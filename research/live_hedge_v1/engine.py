from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from math import ceil, isfinite
from zoneinfo import ZoneInfo
from statistics import median
from typing import Any, Optional, Sequence

from .campaign import is_qqq_option_code

N_SHORT = 10
LONG_DELTA = 0.50
MAX_STACK = 5
COVERAGE_MULT = 1.50
NEAR_TP = 0.50
NEAR_ROLL_DTE = 2
SIGNAL_RATIO52_GTE = 0.98
SIGNAL_EXT200_GTE = 0.08
STALE_ORDER_SEC = 120
MAX_QUOTE_AGE_SEC = 45


@dataclass
class Contract:
    code: str
    right: str
    strike: float
    expiry: str
    dte: int
    bid: Optional[float]
    ask: Optional[float]
    delta: Optional[float]
    gamma: Optional[float]
    iv: Optional[float] = None
    lot_size: int = 100
    volume: Optional[float] = None
    quote_timestamp: Optional[str] = None

    @property
    def mid(self):
        if self.bid is not None and self.ask is not None and self.ask >= self.bid:
            return (self.bid + self.ask) / 2
        return self.bid if self.bid is not None else self.ask


@dataclass
class Position:
    code: str
    side: str
    qty: int
    avg_cost: float
    strike: Optional[float] = None
    expiry: Optional[str] = None
    dte: Optional[int] = None
    delta: Optional[float] = None
    gamma: Optional[float] = None


@dataclass
class Order:
    order_id: str
    code: str
    side: str
    qty: int
    price: Optional[float]
    status: str
    updated_at: str
    created_at: str = ""
    dealt_qty: int = 0
    dealt_avg_price: Optional[float] = None


_US_EXCHANGE_TZ = ZoneInfo("America/New_York")


def _dt(s):
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except Exception:
        return None


def quote_age_sec(s, now=None, naive_is_local=False, max_future_sec=5):
    t = _dt(s)
    if t is None:
        return None
    now = now or datetime.now(timezone.utc)
    if t.tzinfo is None:
        if naive_is_local:
            # Futu US-trading timestamps are exchange-local wall-clock values.
            t = t.replace(tzinfo=_US_EXCHANGE_TZ)
        else:
            t = t.replace(tzinfo=timezone.utc)
    age = (now - t).total_seconds()
    if age < -float(max_future_sec):
        return None
    return max(0, age)


def gamma_baseline_from_history(history: Sequence[float]) -> Optional[float]:
    """Match research: shift(1).rolling(20, min_periods=5).median() on gamma_spot.

    Call with history that does NOT yet include the current bar (shift-1 semantics).
    Values in history should be gamma_spot = abs(gamma) * spot.
    """
    hist = []
    for value in history or []:
        try:
            fv = float(value)
        except (TypeError, ValueError):
            continue
        if isfinite(fv):
            hist.append(fv)
    if len(hist) < 5:
        return None
    window = hist[-20:]
    return float(median(window))



# Persisted gamma_history must be gamma_spot only (never mix with legacy raw |γ|).
GAMMA_HISTORY_SCHEMA = 2
GAMMA_HISTORY_UNIT = "gamma_spot"


def ensure_gamma_history_schema(
    state: dict,
    *,
    spot: Optional[float] = None,
) -> list[float]:
    """Ensure gamma_history is gamma_spot-only with explicit schema markers.

    Unit is determined by the persisted schema marker, never guessed from the
    magnitude of the numbers. Missing/wrong markers are treated as
    untrusted legacy state and the warm-up is discarded. Once schema=2 and
    unit=gamma_spot are present, finite observations are retained (last 20).
    Fresh baseline requires >=5 prior observations via
    gamma_baseline_from_history (shift-1 semantics).
    """
    schema = state.get("gamma_history_schema")
    unit = state.get("gamma_history_unit")
    hist: list[float] = []
    for v in state.get("gamma_history") or []:
        try:
            fv = float(v)
        except (TypeError, ValueError):
            continue
        if not isfinite(fv):
            continue
        hist.append(fv)

    markers_ok = schema == GAMMA_HISTORY_SCHEMA and unit == GAMMA_HISTORY_UNIT
    if not markers_ok:
        hist = []
        state["gamma_history"] = hist
        state["gamma_history_reset_reason"] = "missing_or_wrong_markers"
    else:
        hist = hist[-20:]
        state["gamma_history"] = hist
        state.pop("gamma_history_reset_reason", None)

    state["gamma_history_schema"] = GAMMA_HISTORY_SCHEMA
    state["gamma_history_unit"] = GAMMA_HISTORY_UNIT
    return hist


def risk_state(far, spot, gamma_baseline=None, prev_delta=None):
    da = abs(float(far.delta or 0))
    dist = (far.strike - spot) / spot if spot > 0 else 0
    ds = 1 if da < 0.04 else 2 if da < 0.06 else 3 if da < 0.08 else 4 if da < 0.10 else 5
    xs = 1 if dist > 0.10 else 2 if dist > 0.07 else 3 if dist > 0.04 else 4 if dist > 0.02 else 5
    # gamma_rel uses gamma_spot / baseline (research parity); baseline is median of prior gamma_spot.
    if gamma_baseline and far.gamma is not None:
        gamma_spot = abs(float(far.gamma)) * float(spot)
        gr = gamma_spot / gamma_baseline if gamma_baseline else 1.0
    else:
        gr = 1.0
    dj = 0 if prev_delta is None else abs(da - prev_delta)
    gs = 1 if gr < 1.20 and dj < 0.01 else 2 if gr < 1.50 and dj < 0.02 else 3
    score = 0.50 * ds + 0.30 * xs + 0.20 * gs
    target = max(1, min(MAX_STACK, ceil((COVERAGE_MULT * N_SHORT * da) / LONG_DELTA)))
    if score >= 4.2:
        target = min(MAX_STACK, target + 2)
    elif score >= 3.2:
        target = min(MAX_STACK, target + 1)
    return {
        "far_delta_abs": da,
        "distance_pct": dist,
        "gamma_rel": gr,
        "delta_jump": dj,
        "dscore": ds,
        "xscore": xs,
        "gscore": gs,
        "risk_score": score,
        "desired_stack": target,
    }


def _volume_or_zero(c) -> float:
    try:
        if c.volume is None:
            return 0.0
        return float(c.volume)
    except (TypeError, ValueError):
        return 0.0


def select_far(cs, spot, dte_target, delta_target):
    """Two-stage far selection matching research pick_far."""
    xs = [
        c for c in cs
        if c.right == "CALL"
        and c.strike > spot
        and 60 <= c.dte <= 210
        and c.bid is not None
        and c.ask is not None
        and c.ask >= c.bid
        and c.bid >= 0
        and c.delta is not None
    ]
    if not xs:
        return None
    by_exp: dict[str, list] = {}
    for c in xs:
        by_exp.setdefault(c.expiry, []).append(c)

    def exp_sort_key(exp: str):
        group = by_exp[exp]
        dte = group[0].dte
        vol = sum(_volume_or_zero(c) for c in group)
        return (abs(dte - dte_target), -vol)

    best_exp = min(by_exp.keys(), key=exp_sort_key)
    z = list(by_exp[best_exp])
    z.sort(
        key=lambda c: (
            abs(abs(c.delta) - delta_target),
            -_volume_or_zero(c),
            c.strike,
        )
    )
    return z[0]


def select_near(cs, spot, dte_target):
    """Two-stage near selection matching research pick_near (1.02 pool then 1.01)."""
    xs = [
        c for c in cs
        if c.right == "CALL"
        and c.strike <= spot * 1.02
        and 7 <= c.dte <= 35
        and c.bid is not None
        and c.ask is not None
        and c.ask >= c.bid
        and c.bid >= 0
        and c.delta is not None
    ]
    if not xs:
        return None
    by_exp: dict[str, list] = {}
    for c in xs:
        by_exp.setdefault(c.expiry, []).append(c)

    def exp_sort_key(exp: str):
        group = by_exp[exp]
        dte = group[0].dte
        vol = sum(_volume_or_zero(c) for c in group)
        return (abs(dte - dte_target), -vol)

    best_exp = min(by_exp.keys(), key=exp_sort_key)
    z = [c for c in by_exp[best_exp] if c.strike <= spot * 1.01]
    if not z:
        return None
    z.sort(
        key=lambda c: (
            abs(abs(c.delta) - LONG_DELTA),
            -_volume_or_zero(c),
            c.strike,
        )
    )
    return z[0]


def _safe_positive_qty(value) -> bool:
    try:
        return int(float(value or 0)) > 0
    except (TypeError, ValueError):
        return False


def plan(
    *,
    market,
    far,
    near,
    positions,
    orders,
    signal_active,
    far_campaign_active,
    quotes_by_code=None,
    gamma_baseline=None,
    previous_far_delta_abs=None,
    near_lots=None,
    far_ownership_enforced=False,
    managed_far_qty=None,
    managed_far_code=None,
    now=None,
):
    now = now or datetime.now(timezone.utc)
    qage = quote_age_sec(market.get("timestamp"), now)
    if (
        market.get("source") != "LIVE QUOTE"
        or not market.get("spot")
        or qage is None
        or qage > MAX_QUOTE_AGE_SEC
    ):
        return {
            "status": "BLOCKED_STALE_MARKET",
            "timestamp": now.isoformat(),
            "candidate_actions": [],
            "next_triggers": [],
            "market": market,
        }

    spot = float(market["spot"])
    quotes_by_code = quotes_by_code or {}
    near_lots = near_lots or []
    option_freshness = {}

    # Validate every LIVE QUOTE code that can become an actionable strategy leg,
    # including already-owned near lots. Do not use account-wide unrelated QQQ
    # positions as freshness obligations.
    required_codes = set()
    if far is not None:
        required_codes.add(far.code)
    if near is not None:
        required_codes.add(near.code)
    for lot in near_lots:
        if str(lot.get("status", "OPEN")).upper() == "OPEN" and _safe_positive_qty(lot.get("qty")):
            code = str(lot.get("code", "")).upper()
            if is_qqq_option_code(code):
                required_codes.add(code)

    for code in sorted(required_codes):
        quote = quotes_by_code.get(code) or {}
        contract = far if far is not None and far.code == code else (near if near is not None and near.code == code else None)
        live_expected = (
            str(quote.get("source") or "").upper() == "LIVE QUOTE"
            or (contract is not None and contract.quote_timestamp is not None)
        )
        if not live_expected:
            continue
        ts = quote.get("timestamp", contract.quote_timestamp if contract is not None else None)
        age = quote_age_sec(ts, now, naive_is_local=True)
        option_freshness[code] = age
        if age is None or age > MAX_QUOTE_AGE_SEC:
            return {
                "status": "BLOCKED_STALE_OPTION_QUOTE",
                "timestamp": now.isoformat(),
                "candidate_actions": [],
                "next_triggers": [],
                "reasons": [
                    f"strategy option quote {code} is missing, invalid, stale, or materially future-dated"
                ],
                "option_freshness": option_freshness,
                "market": market,
            }

    option_positions = [
        p for p in positions
        if is_qqq_option_code(p.code) and p.side in {"LONG", "SHORT"} and p.qty > 0
    ]
    near_pos_all = [p for p in option_positions if p.side == "LONG"]
    managed_near_by_code = {}
    for lot in near_lots:
        if (
            str(lot.get("status", "OPEN")).upper() != "OPEN"
            or str(lot.get("side", "LONG")).upper() != "LONG"
            or not _safe_positive_qty(lot.get("qty"))
            or not is_qqq_option_code(lot.get("code", ""))
        ):
            continue
        code = str(lot.get("code", "")).upper()
        managed_near_by_code[code] = managed_near_by_code.get(code, 0) + int(lot.get("qty", 0) or 0)
    observed_near_by_code = {}
    for p in near_pos_all:
        code = p.code.upper()
        observed_near_by_code[code] = observed_near_by_code.get(code, 0) + int(p.qty)
    near_mismatches = {
        code: {"position_qty": observed_near_by_code.get(code, 0), "tracked_lot_qty": managed_near_by_code.get(code, 0)}
        for code in set(observed_near_by_code) | set(managed_near_by_code)
        if observed_near_by_code.get(code, 0) != managed_near_by_code.get(code, 0)
    }
    if far_campaign_active and near_mismatches:
        return {
            "status": "BLOCKED_NEAR_OWNERSHIP_MISMATCH",
            "timestamp": now.isoformat(),
            "candidate_actions": [],
            "next_triggers": [],
            "reasons": [
                "observed QQQ LONG inventory does not match tracked strategy near lots",
                "desk refuses to attribute or modify unmatched LONG inventory",
                "resolve manual/out-of-band/state mismatch before campaign management continues",
            ],
            "near_ownership_mismatches": near_mismatches,
            "market": market,
        }
    near_pos = [p for p in near_pos_all if p.code.upper() in managed_near_by_code]
    far_positions = [p for p in option_positions if p.side == "SHORT"]

    if far_campaign_active and far_ownership_enforced:
        managed_code = str(managed_far_code or "").upper()
        observed_far_by_code = {}
        for p in far_positions:
            code = p.code.upper()
            observed_far_by_code[code] = observed_far_by_code.get(code, 0) + int(p.qty)
        extra_far_codes = sorted(
            code for code in observed_far_by_code
            if managed_code and code != managed_code
        )
        if managed_code == "" or managed_far_qty is None:
            return {
                "status": "BLOCKED_FAR_OWNERSHIP_UNBASELINED",
                "timestamp": now.isoformat(),
                "candidate_actions": [],
                "next_triggers": [],
                "reasons": [
                    "active campaign has no explicit managed far ownership baseline",
                    "desk refuses to infer far ownership from current broker position",
                    "explicit rebaseline is required before campaign management continues",
                ],
                "far_ownership": {
                    "status": "UNBASELINED",
                    "managed_far_code": managed_code or None,
                    "managed_far_qty": None,
                    "observed_far_by_code": observed_far_by_code,
                },
                "market": market,
            }
        expected_far_qty = max(0, int(managed_far_qty))
        observed_far_qty = observed_far_by_code.get(managed_code, 0)
        if extra_far_codes or observed_far_qty != expected_far_qty:
            return {
                "status": "BLOCKED_FAR_OWNERSHIP_MISMATCH",
                "timestamp": now.isoformat(),
                "candidate_actions": [],
                "next_triggers": [],
                "reasons": [
                    "observed QQQ SHORT inventory does not match tracked strategy far ownership",
                    "desk refuses to attribute or modify unmatched SHORT inventory",
                    "resolve manual/out-of-band/state mismatch before campaign management continues",
                ],
                "far_ownership": {
                    "status": "MISMATCH",
                    "managed_far_code": managed_code,
                    "managed_far_qty": expected_far_qty,
                    "observed_far_qty": observed_far_qty,
                    "observed_far_by_code": observed_far_by_code,
                    "extra_far_codes": extra_far_codes,
                },
                "market": market,
            }
    terminal_statuses = {"FILLED", "FILLED_ALL", "CANCELLED", "CANCELLED_ALL", "REJECTED", "FAILED"}
    pending_codes = {
        o.code
        for o in orders
        if is_qqq_option_code(o.code)
        and o.status.upper() not in terminal_statuses
        and max(0, int(o.qty) - max(0, int(o.dealt_qty))) > 0
    }

    actions = []
    reasons = []
    next_triggers = [
        {
            "type": "EMERGENCY_CLOSE",
            "when": "spot >= far strike",
            "effect": "close far short and all tracked campaign near longs",
        },
    ]

    if not far_campaign_active:
        if signal_active and far:
            actions.append({
                "action": "SELL_FAR",
                "code": far.code,
                "qty": N_SHORT,
                "side": "SELL",
                "price": far.bid,
                "why": "EXTREME_HIGH_SIGNAL_ACTIVE",
            })
            reasons.append("NO_ACTIVE_CAMPAIGN_BUT_ENTRY_SIGNAL_ACTIVE")
        else:
            reasons.append("NO_NEW_CAMPAIGN")
        next_triggers.append({
            "type": "ARM",
            "when": "extreme-high signal becomes active",
            "effect": f"SELL_FAR {N_SHORT} contracts",
        })
    else:
        if far is None:
            return {
                "status": "BLOCKED_NO_FAR_QUOTE",
                "timestamp": now.isoformat(),
                "candidate_actions": [],
                "next_triggers": next_triggers,
                "reasons": ["active campaign far quote unavailable"],
                "market": market,
            }

        state = risk_state(far, spot, gamma_baseline, previous_far_delta_abs)
        active_near = sum(max(0, int(p.qty)) for p in near_pos)
        far_qty = sum(abs(int(p.qty)) for p in far_positions if p.code == far.code)

        reasons += [
            f"RISK_SCORE={state['risk_score']:.2f}",
            f"TARGET_NEAR={state['desired_stack']}",
            f"ACTIVE_NEAR={active_near}",
        ]

        next_triggers += [
            {"type": "ADD_NEXT", "when": "desired_stack > active_near", "current": active_near, "target": state["desired_stack"], "effect": "ADD_NEAR up to target"},
            {"type": "REDUCE_NOW", "when": "active_near > desired_stack", "current": active_near, "target": state["desired_stack"], "effect": "REDUCE_NEAR excess"},
            {"type": "HARVEST", "when": "near bid / recorded fill cost - 1 >= 50%", "effect": "HARVEST_NEAR eligible lot"},
            {"type": "ROLL", "when": "near DTE <= 2", "effect": "ROLL_NEAR into selected near contract"},
            {"type": "SIGNAL_OFF", "when": "entry signal becomes inactive", "effect": "no automatic campaign close; keep managing until exit condition"},
        ]

        if spot >= far.strike:
            legs = []
            if far_qty > 0:
                legs.append({
                    "code": far.code,
                    "side": "BUY",
                    "qty": far_qty,
                    "price": far.ask,
                    "why": "CLOSE_FAR_EMERGENCY",
                })
            for p in near_pos:
                q = quotes_by_code.get(p.code, {})
                legs.append({
                    "code": p.code,
                    "side": "SELL",
                    "qty": p.qty,
                    "price": q.get("bid"),
                    "why": "CLOSE_NEAR_AFTER_FAR_STRIKE_TOUCH",
                })
            actions.append({
                "action": "CLOSE_CAMPAIGN_EMERGENCY",
                "legs": legs,
                "why": "spot at/above far short strike",
            })
        else:
            if far_qty != N_SHORT:
                direction = "ADD" if far_qty < N_SHORT else "REDUCE"
                actions.append({
                    "action": "REPAIR_FAR",
                    "code": far.code,
                    "target_qty": N_SHORT,
                    "current_qty": far_qty,
                    "direction": direction,
                    "side": "SELL" if direction == "ADD" else "BUY",
                    "qty": abs(N_SHORT - far_qty),
                    "price": far.bid if direction == "ADD" else far.ask,
                    "why": "fixed 10-contract far short invariant",
                })

            eligible_harvest = []
            for lot in near_lots:
                if str(lot.get("status", "OPEN")).upper() != "OPEN":
                    continue
                q = quotes_by_code.get(lot.get("code"), {})
                bid = q.get("bid")
                cost = float(lot.get("avg_cost", 0) or 0)
                if bid is not None and cost > 0 and bid / cost - 1 >= NEAR_TP:
                    eligible_harvest.append((str(lot.get("opened_at", "")), lot))
            if eligible_harvest:
                eligible_harvest.sort(key=lambda x: x[0])
                lot = eligible_harvest[0][1]
                q = quotes_by_code.get(lot["code"], {})
                actions.append({
                    "action": "HARVEST_NEAR",
                    "code": lot["code"],
                    "qty": min(
                        int(lot["qty"]),
                        next((p.qty for p in near_pos if p.code == lot["code"]), int(lot["qty"])),
                    ),
                    "price": q.get("bid"),
                    "return_pct": q["bid"] / float(lot["avg_cost"]) - 1,
                    "lot_id": lot.get("lot_id"),
                    "avg_cost": float(lot["avg_cost"]),
                    "why": "recorded near lot reached +50% profit target",
                })

            for p in near_pos:
                if p.dte is not None and p.dte <= NEAR_ROLL_DTE:
                    if near is not None and near.code != p.code:
                        actions.append({
                            "action": "ROLL_NEAR",
                            "code": p.code,
                            "qty": p.qty,
                            "price": quotes_by_code.get(p.code, {}).get("bid"),
                            "new_code": near.code,
                            "new_price": near.ask,
                            "new_dte": near.dte,
                            "new_delta": near.delta,
                            "why": "near expiry risk",
                        })
                    else:
                        reasons.append(f"ROLL_BLOCKED_NO_NEW_NEAR_QUOTE:{p.code}")

            if active_near > state["desired_stack"]:
                excess = active_near - state["desired_stack"]
                for p in sorted(near_pos, key=lambda z: (z.avg_cost, z.dte if z.dte is not None else 999, z.code)):
                    if excess <= 0:
                        break
                    q = min(excess, p.qty)
                    excess -= q
                    actions.append({
                        "action": "REDUCE_NEAR",
                        "code": p.code,
                        "qty": q,
                        "price": quotes_by_code.get(p.code, {}).get("bid"),
                        "why": "dynamic target stack below current inventory",
                    })

            if active_near < state["desired_stack"] and near and near.code not in pending_codes:
                actions.append({
                    "action": "ADD_NEAR",
                    "code": near.code,
                    "qty": state["desired_stack"] - active_near,
                    "price": near.ask,
                    "dte": near.dte,
                    "delta": near.delta,
                    "why": "dynamic risk coverage below target",
                })

            if not actions:
                reasons.append("NO_PRIMARY_ACTION")

    for o in orders:
        if not is_qqq_option_code(o.code):
            continue
        remaining_qty = max(0, int(o.qty) - max(0, int(o.dealt_qty)))
        if remaining_qty <= 0:
            continue
        age = quote_age_sec(o.updated_at, now, naive_is_local=True)
        q = quotes_by_code.get(o.code, {})
        if (
            age is not None
            and age >= STALE_ORDER_SEC
            and o.status.upper() not in terminal_statuses
        ):
            actions.append({
                "action": "REPRICE_OR_CANCEL",
                "order_id": o.order_id,
                "code": o.code,
                "qty": remaining_qty,
                "side": o.side,
                "current_price": o.price,
                "suggested_price": q.get("mid"),
                "why": f"pending order stale {age:.0f}s; manual requote or cancel required",
            })

    return {
        "status": "ACTIONABLE" if actions else "HOLD",
        "timestamp": now.isoformat(),
        "signal_active": signal_active,
        "far_campaign_active": far_campaign_active,
        "market": market,
        "market_quote_age_sec": qage,
        "option_freshness": option_freshness,
        "far": asdict(far) if far else None,
        "near_candidate": asdict(near) if near else None,
        "candidate_actions": actions,
        "reasons": reasons,
        "next_triggers": next_triggers,
        "risk_state": (
            risk_state(far, spot, gamma_baseline, previous_far_delta_abs)
            if far_campaign_active and far else None
        ),
    }
