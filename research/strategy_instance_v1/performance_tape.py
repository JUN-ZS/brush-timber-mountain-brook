"""USER_MANUAL performance tape.

Derived from recorded manual trades plus the strategy ticket snapshot stored
with each trade. Not broker evidence. Contracts the operator did not trade
have no observable counterfactual path.
"""
from __future__ import annotations

OPEN_ACTIONS = {"ADD", "SELL_FAR"}
CLOSE_ACTIONS = {"REDUCE", "BUY_BACK_FAR"}
KNOWN = {"FOLLOW_STRATEGY", "ADJUST_SIZE", "OPERATOR_ONLY"}

# Canonical semantic mapping from a live strategy ticket/leg to the
# corresponding manual operator action. A different semantic action is not
# a size adjustment; it is an operator-only execution relative to that ticket.
STRATEGY_TO_MANUAL = {
    "ADD_NEAR": "ADD",
    "HARVEST_NEAR": "REDUCE",
    "REDUCE_NEAR": "REDUCE",
    "SELL_FAR": "SELL_FAR",
    "CLOSE_FAR_EMERGENCY": "BUY_BACK_FAR",
    "CLOSE_NEAR_AFTER_FAR_STRIKE_TOUCH": "REDUCE",
}


def canonical_manual_action(strategy_ref):
    ref = strategy_ref or {}
    leg_action = str(ref.get("strategy_leg_action") or "").upper()
    top_action = str(ref.get("action") or "").upper()
    side = str(ref.get("side") or "").upper()
    if leg_action in STRATEGY_TO_MANUAL:
        return STRATEGY_TO_MANUAL[leg_action]
    if top_action in STRATEGY_TO_MANUAL:
        return STRATEGY_TO_MANUAL[top_action]
    if top_action == "CLOSE_CAMPAIGN_EMERGENCY":
        if side == "BUY":
            return "BUY_BACK_FAR"
        if side == "SELL":
            return "REDUCE"
    return None


def classify_relationship(trade_action, trade_code, trade_qty, strategy_ref):
    ref = strategy_ref or {}
    ticket_id = str(ref.get("ticket_id") or "")
    ref_code = str(ref.get("code") or "").upper()
    if not ticket_id or ref_code != str(trade_code or "").upper():
        return "OPERATOR_ONLY"
    expected = canonical_manual_action(ref)
    if expected != str(trade_action or "").upper():
        return "OPERATOR_ONLY"
    ref_qty = _i(ref.get("qty"))
    return "FOLLOW_STRATEGY" if ref_qty == _i(trade_qty) else "ADJUST_SIZE"


def _f(x):
    try:
        y = float(x)
        return y if y == y else None
    except (TypeError, ValueError):
        return None


def _i(x):
    try:
        return int(float(x or 0))
    except (TypeError, ValueError):
        return 0


def build_performance_tape(trades):
    ordered = sorted(
        trades or [],
        key=lambda r: (str(r.get("timestamp_utc") or ""), _i(r.get("event_seq"))),
    )
    queues = {}
    open_attr = {}
    rows = []
    attributed = {k: 0.0 for k in KNOWN}
    counts = {k: 0 for k in KNOWN}
    opening_counts = {k: 0 for k in KNOWN}
    closing_counts = {k: 0 for k in KNOWN}
    slippage = 0.0
    size_gap = 0
    unmatched_close_qty = 0
    observed_realized = 0.0

    for n, t in enumerate(ordered, 1):
        action = str(t.get("action") or "").upper()
        code = str(t.get("code") or "").upper()
        qty = _i(t.get("qty"))
        price = _f(t.get("price")) or 0.0
        lot = max(1, _i(t.get("lot_size")) or 100)
        ref = t.get("strategy_reference") or {}
        has_ticket = bool(ref.get("ticket_id"))
        s_qty = _i(ref.get("qty")) if has_ticket else None
        s_px = _f(ref.get("price")) if has_ticket else None

        # The relationship is canonicalized from the ticket snapshot and the
        # actual execution. A size gap exists only after semantic action
        # matching; opposite-action executions are operator-only, not
        # "adjusted size".
        rel = classify_relationship(action, code, qty, ref)
        counts[rel] += 1
        expected_action = canonical_manual_action(ref)
        qty_delta = None
        if rel in {"FOLLOW_STRATEGY", "ADJUST_SIZE"} and s_qty is not None:
            qty_delta = qty - s_qty
            if rel == "ADJUST_SIZE":
                size_gap += abs(qty_delta)

        execution_slip = None
        if rel in {"FOLLOW_STRATEGY", "ADJUST_SIZE"} and s_px is not None and qty and price:
            sign = -1 if action in {"ADD", "BUY_BACK_FAR"} else 1
            execution_slip = round((price - s_px) * qty * lot * sign, 4)
            slippage += execution_slip

        realized = round(_f(t.get("realized_pnl_delta")) or 0.0, 4)
        observed_realized = round(observed_realized + realized, 4)
        matched = []
        if action in OPEN_ACTIONS:
            opening_counts[rel] += 1
            side = "LONG" if action == "ADD" else "SHORT"
            queues.setdefault((code, side), []).append({
                "trade_id": t.get("trade_id"),
                "qty": qty,
                "price": price,
                "lot": lot,
                "rel": rel,
            })
        elif action in CLOSE_ACTIONS:
            closing_counts[rel] += 1
            side = "LONG" if action == "REDUCE" else "SHORT"
            q = queues.setdefault((code, side), [])
            rem = qty
            while rem and q:
                sl = q[0]
                take = min(rem, sl["qty"])
                pnl = ((price - sl["price"]) if side == "LONG" else (sl["price"] - price)) * take * sl["lot"]
                pnl = round(pnl, 4)
                attributed[sl["rel"]] = round(attributed.get(sl["rel"], 0.0) + pnl, 4)
                open_attr[sl["trade_id"]] = round(open_attr.get(sl["trade_id"], 0.0) + pnl, 4)
                matched.append({
                    "open_trade_id": sl["trade_id"],
                    "qty": take,
                    "relationship": sl["rel"],
                    "realized": pnl,
                })
                sl["qty"] -= take
                rem -= take
                if sl["qty"] <= 0:
                    q.pop(0)
            unmatched_close_qty += rem

        if rel == "OPERATOR_ONLY":
            read = ("OPERATOR_ONLY: no matching strategy ticket/action at record time."
                    if has_ticket else
                    "OPERATOR_ONLY: no strategy ticket was captured at record time.")
        elif qty_delta == 0:
            read = "FOLLOW_STRATEGY: same code, semantic action and quantity as the ticket. Outcome is the observed fill, not a rewritten strategy path."
        elif qty_delta and qty_delta > 0:
            read = "ADJUST_SIZE up: extra contracts are observed only. The ticket quantity not exceeded has no separate path."
        else:
            read = "ADJUST_SIZE down: skipped contracts have no observable counterfactual. Only the traded quantity has P&L."

        rows.append({
            "seq": n,
            "timestamp_utc": t.get("timestamp_utc"),
            "trade_id": t.get("trade_id"),
            "action": action,
            "code": code,
            "qty": qty,
            "price": price,
            "lot_size": lot,
            "relationship": rel,
            "strategy_ticket_id": ref.get("ticket_id"),
            "strategy_action": ref.get("action"),
            "strategy_expected_manual_action": expected_action,
            "strategy_qty": s_qty,
            "strategy_price": s_px,
            "qty_delta": qty_delta,
            "execution_slippage_estimate": execution_slip,
            "realized_pnl_delta": realized,
            "close_matches": matched,
            "note": t.get("note") or "",
            "read": read,
            "grade": "Derived",
        })

    open_left = {}
    for slices in queues.values():
        for sl in slices:
            if sl["qty"] > 0:
                open_left[sl["trade_id"]] = open_left.get(sl["trade_id"], 0) + sl["qty"]
    for row in rows:
        row["open_qty_remaining"] = open_left.get(row["trade_id"], 0)
        row["attributed_close_pnl"] = open_attr.get(row["trade_id"], 0.0)

    return {
        "schema": "USER_MANUAL_PERFORMANCE_TAPE.v1",
        "grade": "Derived",
        "source": "USER_MANUAL",
        "rule": "Observed fill P&L only. Untraded contracts have no counterfactual. Entry slippage versus the ticket indicative is Estimated, not outcome.",
        "trade_count": len(rows),
        "counts": counts,
        "opening_counts": opening_counts,
        "closing_counts": closing_counts,
        "observed_realized": round(observed_realized, 4),
        "attributed_realized": attributed,
        "attribution_delta": round(observed_realized - sum(attributed.values()), 4),
        "unmatched_close_qty": unmatched_close_qty,
        "attribution_status": "CONSISTENT" if unmatched_close_qty == 0 and abs(observed_realized - sum(attributed.values())) < 0.01 else "CHECK_REQUIRED",
        "execution_slippage_estimate": round(slippage, 4),
        "size_gap_contracts": size_gap,
        "rows": rows,
    }
