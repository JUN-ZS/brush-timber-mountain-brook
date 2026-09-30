from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .campaign import (
    STATE_ARMING,
    STATE_EMERGENCY_CLOSE,
    STATE_HARVESTING,
    STATE_IDLE,
    STATE_OPEN,
    STATE_RECONCILE_WAIT,
    STATE_REDUCING,
    STATE_ROLLING,
    build_ticket,
    choose_primary_action,
    is_qqq_option_code,
    make_campaign_id,
    position_snapshot,
    reconcile_ticket,
    transition_for_action,
)
from .engine import Contract, Order, Position, plan
from .futu_reader import LiveFutuReader
from .futu_trade_reader import FutuTradeReader
from .state import StateStore


def C(x):
    return Contract(
        code=str(x["code"]),
        right=str(x.get("right", "CALL")).upper(),
        strike=float(x["strike"]),
        expiry=str(x["expiry"]),
        dte=int(x["dte"]),
        bid=x.get("bid"),
        ask=x.get("ask"),
        delta=x.get("delta"),
        gamma=x.get("gamma"),
        iv=x.get("iv"),
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_int(v) -> int:
    try:
        return int(float(v or 0))
    except Exception:
        return 0


def _safe_float(v) -> float:
    try:
        return float(v or 0)
    except Exception:
        return 0.0


def _fill_lots(state, ticket):
    state.setdefault("lots", [])
    fills = ticket.get("fill", []) or []

    for fill in fills:
        code = str(fill.get("code", ""))
        qty = _safe_int(fill.get("qty"))
        side = str(fill.get("side", "")).upper()
        price = fill.get("avg_price")
        source = fill.get("price_source", "NOT_OBSERVED")
        if qty <= 0 or not is_qqq_option_code(code):
            continue

        if side == "BUY":
            lot_id = f'LOT-{ticket["ticket_id"]}-{code}'
            state["lots"].append(
                {
                    "lot_id": lot_id,
                    "ticket_id": ticket["ticket_id"],
                    "code": code,
                    "qty": qty,
                    "avg_cost": price,
                    "opened_at": ticket.get("filled_at", ticket.get("issued_at")),
                    "status": "OPEN",
                    "price_source": source,
                }
            )
            continue

        if side != "SELL":
            continue

        remaining = qty
        preferred = ticket.get("lot_id")
        candidates = [
            lot for lot in state["lots"]
            if lot.get("status") == "OPEN"
            and lot.get("code") == code
            and (preferred is None or lot.get("lot_id") == preferred)
        ]
        if not preferred:
            candidates = [
                lot for lot in state["lots"]
                if lot.get("status") == "OPEN" and lot.get("code") == code
            ]
            candidates.sort(key=lambda x: str(x.get("opened_at", "")))

        for lot in candidates:
            if remaining <= 0:
                break
            take = min(remaining, _safe_int(lot.get("qty")))
            lot["qty"] = _safe_int(lot.get("qty")) - take
            remaining -= take
            if lot["qty"] <= 0:
                lot["qty"] = 0
                lot["status"] = "CLOSED"

    # A full emergency close supersedes all remaining campaign accounting lots.
    if ticket.get("action") == "CLOSE_CAMPAIGN_EMERGENCY":
        for lot in state["lots"]:
            if lot.get("status") == "OPEN":
                lot["qty"] = 0
                lot["status"] = "CLOSED"

    state["lots"] = [lot for lot in state["lots"] if lot.get("status") == "OPEN"]


def _transition(state, new_state, now, store):
    camp = state.setdefault("campaign", {})
    old_state = camp.get("state", STATE_IDLE)
    if old_state == new_state:
        return None
    camp["state"] = new_state
    camp["last_transition_at"] = now
    return store.emit(
        state,
        "CAMPAIGN_TRANSITION",
        now=now,
        payload={"from": old_state, "to": new_state},
    )


def _reconcile_order_ticket(state, acct_orders, store, now):
    ticket = state.get("active_ticket")
    if not ticket or ticket.get("action") != "REPRICE_OR_CANCEL":
        return False, False, []

    order_id = str(ticket.get("legs", [{}])[0].get("order_id", ""))
    match = next((o for o in acct_orders if str(o.get("order_id")) == order_id), None)
    if match is None:
        ticket["status"] = "SUPERSEDED"
        event = store.emit(
            state,
            "REPRICE_TICKET_SUPERSEDED",
            now=now,
            payload={"ticket_id": ticket["ticket_id"], "order_id": order_id},
        )
        state["active_ticket"] = None
        return True, False, [event]

    status = str(match.get("status", "")).upper()
    if status in {"FILLED", "FILLED_ALL"}:
        ticket["status"] = "FILLED"
        ticket["filled_at"] = now
        ticket["broker_order"] = match
        event = store.emit(
            state,
            "REPRICE_ORDER_TERMINAL",
            now=now,
            payload={"ticket_id": ticket["ticket_id"], "order": match},
        )
        state["active_ticket"] = None
        return True, True, [event]

    if status in {"CANCELLED", "CANCELLED_ALL", "REJECTED", "FAILED"}:
        ticket["status"] = "SUPERSEDED"
        ticket["terminal_status"] = status
        event = store.emit(
            state,
            "REPRICE_ORDER_CANCELLED",
            now=now,
            payload={"ticket_id": ticket["ticket_id"], "order": match},
        )
        state["active_ticket"] = None
        return True, False, [event]

    return False, False, []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--far-dte", type=int, default=120)
    ap.add_argument("--far-delta", type=float, default=0.08)
    ap.add_argument("--near-dte", type=int, default=30)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=11111)
    ap.add_argument("--simulate-account", action="store_true")
    ap.add_argument(
        "--adopt-existing-far",
        action="store_true",
        help="adopt exactly one existing QQQ option short as the campaign far; never auto-adopt by default",
    )
    ap.add_argument("--out", default="research/live_hedge_v1/live_state.json")
    args = ap.parse_args()

    now = _now()
    out_path = Path(args.out)
    store = StateStore(out_path.with_name("state.json"), out_path.with_name("events.jsonl"))
    state = store.load()
    state["_now"] = now
    state.setdefault("lots", [])

    campaign = state.setdefault(
        "campaign",
        {
            "id": None,
            "state": STATE_IDLE,
            "far_code": None,
            "started_at": None,
            "last_transition_at": None,
            "target_stack": None,
        },
    )
    active_ticket = state.get("active_ticket")

    extra = []
    if campaign.get("far_code"):
        extra.append(campaign["far_code"])
    for leg in (active_ticket or {}).get("legs", []):
        if leg.get("code"):
            extra.append(leg["code"])
    for lot in state.get("lots", []):
        if lot.get("code"):
            extra.append(lot["code"])

    acct = FutuTradeReader(
        args.host,
        args.port,
        real=not args.simulate_account,
    ).read()

    snap = LiveFutuReader(args.host, args.port).snapshot(sorted(set(extra)))
    if snap.get("status") != "OK":
        output = {
            "status": "BLOCKED_MARKET_READER",
            "timestamp": now,
            "manual_execution_only": True,
            "positions_source": acct.get("source"),
            "account": acct,
            "market": snap,
        }
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return 2

    market = snap["market"]
    contracts = [C(x) for x in snap["contracts"]]
    quotes = snap.get("quotes", {})
    by = {c.code: c for c in contracts}

    positions = []
    for p in acct.get("positions", []):
        if str(p.get("side", "")).upper() not in {"LONG", "SHORT"}:
            continue
        meta = by.get(p["code"])
        q = quotes.get(p["code"], {})
        positions.append(
            Position(
                p["code"],
                p["side"],
                _safe_int(p.get("qty")),
                _safe_float(p.get("avg_cost")),
                meta.strike if meta else q.get("strike"),
                meta.expiry if meta else q.get("expiry"),
                meta.dte if meta else q.get("dte"),
                q.get("delta"),
                q.get("gamma"),
            )
        )

    strict_positions = [
        p for p in positions
        if is_qqq_option_code(p.code) and p.qty > 0
    ]
    qqq_shorts = [p for p in strict_positions if p.side == "SHORT"]

    if campaign.get("state") == STATE_IDLE and args.adopt_existing_far:
        if len(qqq_shorts) != 1:
            raise RuntimeError(
                f"--adopt-existing-far requires exactly one QQQ option short; found {len(qqq_shorts)}"
            )
        campaign["id"] = make_campaign_id(now, store.next_campaign_sequence(state))
        campaign["state"] = STATE_OPEN
        campaign["far_code"] = qqq_shorts[0].code
        campaign["started_at"] = now
        campaign["last_transition_at"] = now
        store.emit(
            state,
            "CAMPAIGN_ADOPTED_EXISTING_FAR",
            now=now,
            payload={"far_code": qqq_shorts[0].code, "qty": qqq_shorts[0].qty},
        )

    far_position = None
    far_code = campaign.get("far_code")
    if far_code:
        far_position = next(
            (
                p for p in strict_positions
                if p.side == "SHORT" and p.code == far_code
            ),
            None,
        )

    far = None
    if far_code:
        z = quotes.get(far_code)
        if z and z.get("strike") is not None and z.get("expiry"):
            far = Contract(
                far_code,
                "CALL",
                float(z["strike"]),
                str(z["expiry"]),
                int(z.get("dte") or 0),
                z.get("bid"),
                z.get("ask"),
                z.get("delta"),
                z.get("gamma"),
                z.get("iv"),
            )

    if far is None and campaign.get("state") == STATE_IDLE:
        # Only select a fresh far when there is no unmanaged QQQ option short.
        if not qqq_shorts:
            candidate = next(
                (
                    c for c in contracts
                    if c.right == "CALL"
                    and c.bid is not None
                    and c.ask is not None
                ),
                None,
            )
            if candidate:
                from .engine import select_far
                far = select_far(
                    contracts,
                    float(market["spot"]),
                    args.far_dte,
                    args.far_delta,
                )

    if far is None and far_position is not None:
        z = quotes.get(far_position.code)
        if z:
            far = Contract(
                far_position.code,
                "CALL",
                float(z.get("strike") or far_position.strike or 0),
                str(z.get("expiry") or far_position.expiry or ""),
                int(z.get("dte") or far_position.dte or 0),
                z.get("bid"),
                z.get("ask"),
                z.get("delta"),
                z.get("gamma"),
                z.get("iv"),
            )

    near = None
    from .engine import select_near
    if market.get("spot"):
        near = select_near(contracts, float(market["spot"]), args.near_dte)
        if near is not None and near.code in quotes:
            z = quotes[near.code]
            near = Contract(
                near.code,
                near.right,
                near.strike,
                near.expiry,
                near.dte,
                z.get("bid"),
                z.get("ask"),
                z.get("delta"),
                z.get("gamma"),
                z.get("iv"),
            )

    acct_orders = [
        Order(
            order_id=str(o.get("order_id", "")),
            code=str(o.get("code", "")),
            side=str(o.get("side", "")).upper(),
            qty=_safe_int(o.get("qty")),
            price=o.get("price"),
            status=str(o.get("status", "")).upper(),
            updated_at=str(o.get("updated_at", "")),
            created_at=str(o.get("created_at", "")),
            dealt_qty=_safe_int(o.get("dealt_qty")),
            dealt_avg_price=o.get("dealt_avg_price"),
        )
        for o in acct.get("orders", [])
    ]

    prev = position_snapshot(positions)
    reconcile = reconcile_ticket(
        state,
        positions,
        [o.__dict__ for o in acct_orders],
        acct.get("deals", []),
    )
    reconcile_events = []
    for event in reconcile.get("events", []):
        reconcile_events.append(store.emit(
            state,
            event.pop("type"),
            now=now,
            payload=event,
        ))

    rp_done, rp_terminal, rp_events = _reconcile_order_ticket(
        state,
        [o.__dict__ for o in acct_orders],
        store,
        now,
    )
    reconcile_events.extend(rp_events)

    just_filled = bool(reconcile.get("filled") or rp_terminal)
    if reconcile.get("filled"):
        filled_ticket = reconcile.get("ticket") or {}
        _fill_lots(state, filled_ticket)

        action = filled_ticket.get("action")
        if action == "SELL_FAR":
            _transition(state, STATE_OPEN, now, store)
        elif action == "CLOSE_CAMPAIGN_EMERGENCY":
            if not any(is_qqq_option_code(p.code) and p.qty > 0 for p in positions):
                campaign["far_code"] = None
                campaign["id"] = None
                _transition(state, STATE_IDLE, now, store)
            else:
                _transition(state, STATE_RECONCILE_WAIT, now, store)
        elif campaign.get("state") != STATE_IDLE:
            _transition(state, STATE_OPEN, now, store)

    # Do not issue a second command in the same cycle in which the previous command filled.
    campaign_active = campaign.get("state") != STATE_IDLE
    signal_active = bool(market.get("signal_active"))
    unmanaged_short_block = campaign.get("state") == STATE_IDLE and bool(qqq_shorts)

    gamma_history = state.get("gamma_history") or []
    gamma_baseline = (
        sum(gamma_history[-20:]) / len(gamma_history[-20:])
        if len(gamma_history) >= 3 else None
    )
    previous_delta = state.get("far_delta")

    p = plan(
        market=market,
        far=far,
        near=near,
        positions=positions,
        orders=acct_orders,
        signal_active=(signal_active and not unmanaged_short_block),
        far_campaign_active=campaign_active,
        quotes_by_code=quotes,
        gamma_baseline=gamma_baseline,
        previous_far_delta_abs=previous_delta,
        near_lots=state.get("lots", []),
        now=datetime.fromisoformat(now),
    )

    if unmanaged_short_block and not campaign_active:
        p["status"] = "BLOCKED_UNMANAGED_QQQ_SHORT"
        p["candidate_actions"] = []
        p["reasons"] = [
            "unmanaged QQQ option short exists while campaign state is IDLE",
            "use --adopt-existing-far only after verifying that short belongs to this desk",
        ] + list(p.get("reasons", []))

    # A just-filled cycle only records the fill and next triggers. It does not stack a new order immediately.
    primary = None
    if not just_filled and state.get("active_ticket") is None and campaign.get("state") != STATE_EMERGENCY_CLOSE:
        primary = choose_primary_action(p.get("candidate_actions", []))

    if primary:
        if campaign.get("state") == STATE_IDLE and primary.get("action") == "SELL_FAR":
            campaign["id"] = make_campaign_id(now, store.next_campaign_sequence(state))
            campaign["far_code"] = primary["code"]
            campaign["started_at"] = now
            campaign["last_transition_at"] = now
            _transition(state, STATE_ARMING, now, store)

        action_name = str(primary.get("action"))
        new_state = transition_for_action(campaign.get("state", STATE_IDLE), action_name)
        if campaign.get("state") == STATE_IDLE and action_name == "SELL_FAR":
            new_state = STATE_ARMING
        if new_state != campaign.get("state"):
            _transition(state, new_state, now, store)

        ticket = build_ticket(
            action=primary,
            campaign_id=campaign.get("id"),
            before_positions=state.get("last_positions") or prev,
            now=now,
            sequence=store.next_ticket_sequence(state),
        )
        if action_name == "REPRICE_OR_CANCEL":
            leg = ticket["legs"][0]
            leg["order_id"] = primary.get("order_id")
        state["active_ticket"] = ticket

        store.emit(
            state,
            "TICKET_ISSUED",
            now=now,
            payload={
                "ticket": ticket,
                "primary_reason": primary.get("why"),
            },
        )

    # Persist the state observed at the end of this cycle; next cycle uses it as the reconcile baseline.
    if far:
        state["far_code"] = far.code
        if far.delta is not None:
            state["far_delta"] = abs(float(far.delta))
        if far.gamma is not None:
            hist = state.setdefault("gamma_history", [])
            hist.append(abs(float(far.gamma)))
            state["gamma_history"] = hist[-20:]

    if p.get("risk_state"):
        state["last_target_stack"] = p["risk_state"].get("desired_stack")
        state["last_risk_score"] = p["risk_state"].get("risk_score")
        campaign["target_stack"] = p["risk_state"].get("desired_stack")

    old_target = state.get("_previous_target_stack")
    new_target = state.get("last_target_stack")
    if new_target is not None and old_target is not None and new_target != old_target:
        store.emit(
            state,
            "TARGET_STACK_CHANGE",
            now=now,
            payload={
                "from": old_target,
                "to": new_target,
                "risk_score": state.get("last_risk_score"),
            },
        )
    state["_previous_target_stack"] = new_target
    store.record_position_snapshot(state, positions)
    state.pop("_now", None)
    store.save(state)

    output = {
        "status": "RECONCILED_FILL" if just_filled else (
            "WAITING_MANUAL_TICKET" if state.get("active_ticket") else p.get("status")
        ),
        "timestamp": now,
        "signal_active": signal_active,
        "campaign": campaign,
        "active_ticket": state.get("active_ticket"),
        "primary_ticket": state.get("active_ticket") if primary else None,
        "market": market,
        "far": p.get("far"),
        "near_candidate": p.get("near_candidate"),
        "risk_state": p.get("risk_state"),
        "positions": [
            {
                "code": x.code,
                "side": x.side,
                "qty": x.qty,
                "avg_cost": x.avg_cost,
                "dte": x.dte,
                "strike": x.strike,
            }
            for x in strict_positions
        ],
        "lots": state.get("lots", []),
        "candidate_actions": p.get("candidate_actions", []),
        "next_triggers": p.get("next_triggers", []),
        "reasons": p.get("reasons", []),
        "reconcile_events": reconcile_events,
        "account_source": acct.get("source"),
        "deal_warning": acct.get("deal_warning"),
        "source": "FUTU_OPEND_READ_ONLY",
        "manual_execution_only": True,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
