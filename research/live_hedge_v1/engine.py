from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from math import ceil
from typing import Any, Optional

from .campaign import is_qqq_option_code

N_SHORT = 10
LONG_DELTA = 0.50
MAX_STACK = 5
COVERAGE_MULT = 1.50
NEAR_TP = 0.50
NEAR_ROLL_DTE = 2
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


def _dt(s):
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except Exception:
        return None


def quote_age_sec(s, now=None, naive_is_local=False):
    t = _dt(s)
    if t is None:
        return None
    now = now or datetime.now(timezone.utc)
    if t.tzinfo is None:
        if naive_is_local:
            local_tz = datetime.now().astimezone().tzinfo or timezone.utc
            t = t.replace(tzinfo=local_tz)
        else:
            t = t.replace(tzinfo=timezone.utc)
    return max(0, (now - t).total_seconds())


def risk_state(far, spot, gamma_baseline=None, prev_delta=None):
    da = abs(float(far.delta or 0))
    dist = (far.strike - spot) / spot if spot > 0 else 0
    ds = 1 if da < 0.04 else 2 if da < 0.06 else 3 if da < 0.08 else 4 if da < 0.10 else 5
    xs = 1 if dist > 0.10 else 2 if dist > 0.07 else 3 if dist > 0.04 else 4 if dist > 0.02 else 5
    gr = 1.0 if not gamma_baseline or not far.gamma else abs(float(far.gamma)) / gamma_baseline
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


def select_far(cs, spot, dte_target, delta_target):
    xs = [
        c for c in cs
        if c.right == "CALL"
        and c.strike > spot
        and 60 <= c.dte <= 210
        and c.bid is not None
        and c.ask is not None
        and c.ask >= c.bid
        and c.delta is not None
    ]
    if not xs:
        return None
    xs.sort(key=lambda c: (abs(c.dte - dte_target), abs(abs(c.delta) - delta_target), c.strike))
    return xs[0]


def select_near(cs, spot, dte_target):
    xs = [
        c for c in cs
        if c.right == "CALL"
        and c.strike <= spot * 1.01
        and 7 <= c.dte <= 35
        and c.bid is not None
        and c.ask is not None
        and c.ask >= c.bid
        and c.delta is not None
    ]
    if not xs:
        return None
    xs.sort(key=lambda c: (abs(c.dte - dte_target), abs(abs(c.delta) - LONG_DELTA), c.strike))
    return xs[0]


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

    option_positions = [
        p for p in positions
        if is_qqq_option_code(p.code) and p.side in {"LONG", "SHORT"} and p.qty > 0
    ]
    near_pos = [p for p in option_positions if p.side == "LONG"]
    far_positions = [p for p in option_positions if p.side == "SHORT"]
    terminal_statuses = {"FILLED", "FILLED_ALL", "CANCELLED", "CANCELLED_ALL", "REJECTED", "FAILED"}
    pending_codes = {
        o.code for o in orders
        if is_qqq_option_code(o.code) and o.status.upper() not in terminal_statuses
    }

    actions = []
    reasons = []
    next_triggers = [
        {
            "type": "EMERGENCY_CLOSE",
            "when": "spot >= far strike",
            "effect": "close far short and all campaign near longs",
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
            legs = [{
                "code": far.code,
                "side": "BUY",
                "qty": max(N_SHORT, far_qty),
                "price": far.ask,
                "why": "CLOSE_FAR_EMERGENCY",
            }]
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
            for p in near_pos:
                q = quotes_by_code.get(p.code, {})
                bid = q.get("bid")
                cost = float(p.avg_cost or 0)
                if bid is not None and cost > 0 and bid / cost - 1 >= NEAR_TP and not any(l.get("code") == p.code for _, l in eligible_harvest):
                    eligible_harvest.append((str(p.code), {
                        "lot_id": f"POSITION:{p.code}",
                        "code": p.code,
                        "qty": p.qty,
                        "avg_cost": cost,
                        "status": "OPEN",
                        "source": "POSITION_FALLBACK",
                    }))
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
                "qty": o.qty,
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
