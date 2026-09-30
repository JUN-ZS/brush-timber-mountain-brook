from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional

STATE_IDLE = "IDLE"
STATE_ARMING = "ARMING"
STATE_OPEN = "OPEN"
STATE_HARVESTING = "HARVESTING"
STATE_REDUCING = "REDUCING"
STATE_ROLLING = "ROLLING"
STATE_RECONCILE_WAIT = "RECONCILE_WAIT"
STATE_EMERGENCY_CLOSE = "EMERGENCY_CLOSE"

ACTIVE_TICKET_STATUSES = {"OPEN", "PARTIAL"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def is_qqq_option_code(code: str) -> bool:
    c = str(code or "").upper()
    return c.startswith("US.QQQ") and c != "US.QQQ"


def strict_option_positions(positions: Iterable[Dict[str, Any]]) -> list[Dict[str, Any]]:
    return [
        dict(p)
        for p in positions
        if is_qqq_option_code(p.get("code", ""))
        and str(p.get("side", "")).upper() in {"LONG", "SHORT"}
        and int(p.get("qty", 0) or 0) > 0
    ]


def position_key(p: Dict[str, Any]) -> str:
    return f'{str(p.get("side","")).upper()}:{str(p.get("code","")).upper()}'


def position_snapshot(positions: Iterable[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for p in strict_option_positions(positions):
        out[position_key(p)] = {
            "code": p["code"],
            "side": str(p["side"]).upper(),
            "qty": int(p.get("qty", 0) or 0),
            "avg_cost": float(p.get("avg_cost", 0) or 0),
        }
    return out


def qty_for(snapshot: Dict[str, Dict[str, Any]], side: str, code: str) -> int:
    return int(snapshot.get(f"{side.upper()}:{code.upper()}", {}).get("qty", 0) or 0)


def _parse_time(s: Any) -> Optional[datetime]:
    if not s:
        return None
    raw = str(s).strip()
    for candidate in (
        raw,
        raw.replace("Z", "+00:00"),
    ):
        try:
            dt = datetime.fromisoformat(candidate)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            continue
    return None


def _is_after(created_at: Any, issued_at: Any) -> bool:
    a = _parse_time(created_at)
    b = _parse_time(issued_at)
    if not b:
        return True
    if not a:
        return False
    return a >= b


def _match_fill_price(
    ticket: Dict[str, Any],
    leg: Dict[str, Any],
    orders: Iterable[Dict[str, Any]],
    deals: Iterable[Dict[str, Any]],
) -> tuple[Optional[float], str]:
    code = str(leg.get("code", "")).upper()
    side = str(leg.get("side", "")).upper()
    want = int(leg.get("qty", 0) or 0)
    candidates = []

    for d in deals:
        if str(d.get("code", "")).upper() != code:
            continue
        if str(d.get("side", "")).upper() != side:
            continue
        if not _is_after(d.get("created_at"), ticket.get("issued_at")):
            continue
        price = float(d.get("price", 0) or 0)
        qty = int(float(d.get("qty", 0) or 0))
        if qty > 0 and price > 0:
            candidates.append(("DEAL", price, qty, d.get("deal_id", "")))

    for o in orders:
        if str(o.get("code", "")).upper() != code:
            continue
        if str(o.get("side", "")).upper() != side:
            continue
        if not _is_after(
            o.get("created_at", o.get("updated_at", "")),
            ticket.get("issued_at"),
        ):
            continue
        dealt = int(float(o.get("dealt_qty", 0) or 0))
        avg = float(o.get("dealt_avg_price", 0) or 0)
        if dealt > 0 and avg > 0:
            candidates.append(("ORDER", avg, dealt, o.get("order_id", "")))

    candidates.sort(key=lambda x: str(x[3]), reverse=True)
    exact = [x for x in candidates if x[2] >= want]
    if exact:
        return exact[0][1], exact[0][0]
    if candidates:
        return candidates[0][1], candidates[0][0]
    return None, "NOT_OBSERVED"


def _derived_fill_price(
    before: Dict[str, Any],
    after: Dict[str, Any],
    delta_qty: int,
) -> Optional[float]:
    if delta_qty <= 0:
        return None
    old_qty = int(before.get("qty", 0) or 0)
    old_avg = float(before.get("avg_cost", 0) or 0)
    new_qty = int(after.get("qty", 0) or 0)
    new_avg = float(after.get("avg_cost", 0) or 0)
    if new_qty <= 0 or new_avg <= 0:
        return None
    if old_qty <= 0 or old_avg <= 0:
        return new_avg
    return (new_qty * new_avg - old_qty * old_avg) / delta_qty


def build_ticket(
    *,
    action: Dict[str, Any],
    campaign_id: str,
    before_positions: Dict[str, Dict[str, Any]],
    now: Optional[str] = None,
    sequence: int = 0,
) -> Dict[str, Any]:
    now = now or utc_now()
    stamp = now.replace("-", "").replace(":", "").replace(".", "").replace("+00:00", "Z")
    ticket_id = f"T-{stamp}-{sequence:04d}"
    act = str(action.get("action", ""))
    legs = []

    if act == "ROLL_NEAR":
        old_code = str(action["code"])
        qty = int(action["qty"])
        new_code = str(action.get("new_code", ""))
        legs = [
            {
                "side": "SELL",
                "code": old_code,
                "qty": qty,
                "price": action.get("price"),
                "expected_side": "LONG",
                "before_qty": qty_for(before_positions, "LONG", old_code),
                "target_qty": max(0, qty_for(before_positions, "LONG", old_code) - qty),
            },
            {
                "side": "BUY",
                "code": new_code,
                "qty": qty,
                "price": action.get("new_price"),
                "expected_side": "LONG",
                "before_qty": qty_for(before_positions, "LONG", new_code),
                "target_qty": qty_for(before_positions, "LONG", new_code) + qty,
            },
        ]
    elif act == "CLOSE_CAMPAIGN_EMERGENCY":
        for leg in action.get("legs", []):
            code = str(leg["code"])
            side = str(leg["side"]).upper()
            expected_side = "SHORT" if side == "BUY" else "LONG"
            legs.append(
                {
                    "side": side,
                    "code": code,
                    "qty": int(leg["qty"]),
                    "price": leg.get("price"),
                    "expected_side": expected_side,
                    "before_qty": qty_for(before_positions, expected_side, code),
                    "target_qty": 0,
                }
            )
    elif act == "REPRICE_OR_CANCEL":
        leg = {
            "side": str(action.get("side", "")).upper(),
            "code": str(action.get("code", "")),
            "qty": int(action.get("qty", 0) or 0),
            "price": action.get("current_price"),
            "order_id": action.get("order_id"),
        }
        legs = [leg]
    else:
        code = str(action.get("code", ""))
        qty = int(action.get("qty", action.get("target_qty", 0)) or 0)
        side = str(action.get("side") or (
            "SELL" if act in {
                "SELL_FAR", "HARVEST_NEAR", "REDUCE_NEAR",
                "CLOSE_FAR_EMERGENCY", "CLOSE_NEAR"
            } else "BUY"
        )).upper()
        expected_side = "SHORT" if act == "SELL_FAR" else (
            "SHORT" if act == "REPAIR_FAR" else "LONG"
        )
        before = qty_for(before_positions, expected_side, code)
        if act == "REPAIR_FAR":
            target = int(action.get("target_qty", 10))
            side = "SELL" if before < target else "BUY"
            qty = abs(target - before)
        else:
            target = before + qty if side == "BUY" else max(0, before - qty)
        legs = [{
            "side": side,
            "code": code,
            "qty": qty,
            "price": action.get("price"),
            "expected_side": expected_side,
            "before_qty": before,
            "target_qty": target,
        }]

    return {
        "ticket_id": ticket_id,
        "campaign_id": campaign_id,
        "action": act,
        "status": "OPEN",
        "issued_at": now,
        "reason": action.get("why"),
        "legs": legs,
        "fill": [],
        "manual_execution_only": True,
    }


def reconcile_ticket(
    state: Dict[str, Any],
    current_positions: Iterable[Dict[str, Any]],
    orders: Iterable[Dict[str, Any]],
    deals: Iterable[Dict[str, Any]],
) -> Dict[str, Any]:
    ticket = state.get("active_ticket")
    events = []
    if not ticket or ticket.get("status") not in ACTIVE_TICKET_STATUSES:
        return {"filled": False, "partial": False, "events": events, "ticket": ticket}

    if ticket.get("action") == "REPRICE_OR_CANCEL":
        return {"filled": False, "partial": False, "events": events, "ticket": ticket}

    before = state.get("last_positions") or {}
    current = position_snapshot(current_positions)
    all_reached = True
    any_progress = False
    unexpected = []

    for leg in ticket.get("legs", []):
        key = f'{leg["expected_side"]}:{str(leg["code"]).upper()}'
        before_qty = int(
            leg.get("before_qty", qty_for(before, leg["expected_side"], leg["code"])) or 0
        )
        now_qty = qty_for(current, leg["expected_side"], leg["code"])
        target_qty = int(leg.get("target_qty", now_qty) or 0)
        expected_delta = target_qty - before_qty
        actual_delta = now_qty - before_qty

        if actual_delta != 0:
            any_progress = True
        if actual_delta != expected_delta:
            if actual_delta != 0:
                unexpected.append({
                    "code": leg["code"],
                    "side": leg["expected_side"],
                    "expected_delta": expected_delta,
                    "actual_delta": actual_delta,
                    "ticket_id": ticket["ticket_id"],
                })
            all_reached = False
        elif now_qty != target_qty:
            all_reached = False

        fill_qty = (
            max(0, actual_delta)
            if expected_delta > 0
            else max(0, -actual_delta)
        )
        if fill_qty > 0:
            price, source = _match_fill_price(ticket, leg, orders, deals)
            if price is None and expected_delta > 0:
                price = _derived_fill_price(
                    before.get(key, {"qty": before_qty, "avg_cost": 0}),
                    current.get(key, {"qty": now_qty, "avg_cost": 0}),
                    fill_qty,
                )
                source = "DERIVED_POSITION_DELTA"
            ticket.setdefault("fill", [])
            ticket["fill"] = [
                f for f in ticket["fill"] if f.get("code") != leg["code"]
            ]
            ticket["fill"].append({
                "code": leg["code"],
                "side": leg["side"],
                "qty": fill_qty,
                "avg_price": price,
                "price_source": source,
                "observed_at": state.get("_now") or utc_now(),
            })

    if unexpected:
        events.append({
            "type": "MANUAL_POSITION_CHANGE",
            "ticket_id": ticket["ticket_id"],
            "changes": unexpected,
        })

    if all_reached:
        ticket["status"] = "FILLED"
        ticket["filled_at"] = state.get("_now") or utc_now()
        events.append({
            "type": "TICKET_FILLED",
            "ticket_id": ticket["ticket_id"],
            "action": ticket.get("action"),
            "fill": deepcopy(ticket.get("fill", [])),
        })
        state["active_ticket"] = None
        return {"filled": True, "partial": False, "events": events, "ticket": ticket}

    if any_progress and not unexpected:
        ticket["status"] = "PARTIAL"
        events.append({
            "type": "TICKET_PARTIAL_PROGRESS",
            "ticket_id": ticket["ticket_id"],
            "fill": deepcopy(ticket.get("fill", [])),
        })

    return {"filled": False, "partial": any_progress, "events": events, "ticket": ticket}


def transition_for_action(state_name: str, action: str) -> str:
    if action == "SELL_FAR":
        return STATE_ARMING
    if action == "HARVEST_NEAR":
        return STATE_HARVESTING
    if action == "REDUCE_NEAR":
        return STATE_REDUCING
    if action == "ROLL_NEAR":
        return STATE_ROLLING
    if action in {"CLOSE_FAR_EMERGENCY", "CLOSE_CAMPAIGN_EMERGENCY"}:
        return STATE_EMERGENCY_CLOSE
    return state_name if state_name != STATE_IDLE else STATE_OPEN


def choose_primary_action(candidates: Iterable[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    actions = list(candidates)
    priority = [
        "CLOSE_CAMPAIGN_EMERGENCY",
        "CLOSE_FAR_EMERGENCY",
        "CLOSE_NEAR",
        "REPAIR_FAR",
        "HARVEST_NEAR",
        "ROLL_NEAR",
        "REPRICE_OR_CANCEL",
        "REDUCE_NEAR",
        "ADD_NEAR",
        "SELL_FAR",
    ]
    for name in priority:
        for action in actions:
            if action.get("action") == name:
                return action
    return None


def make_campaign_id(now: Optional[str] = None, sequence: int = 0) -> str:
    now = now or utc_now()
    stamp = now.replace("-", "").replace(":", "").replace(".", "").replace("+00:00", "Z")
    return f"C-{stamp}-{sequence:04d}"
