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
from .engine import N_SHORT, Contract, Order, Position, plan, select_far, select_near
from .futu_reader import LiveFutuReader
from .futu_trade_reader import FutuTradeReader
from .state import StateStore
from ..evidence_v1.family_snapshot import build_family_snapshot
from ..evidence_v1.identity import runtime_identity
from ..evidence_v1.ledger import EvidenceLedger
from ..evidence_v1.snapshot import write_snapshot
from ..evidence_v1.lock_guard import StrategyLockViolation, assert_runtime_lock


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


def _position_dicts(items):
    """Normalize engine Position objects to the dict shape used by campaign.py."""
    out = []
    for p in items:
        if hasattr(p, "__dict__"):
            p = p.__dict__
        out.append(dict(p))
    return out


def _evidence_positions(items):
    out = []
    for p in items:
        if hasattr(p, "__dict__"):
            p = p.__dict__
        out.append({
            k: p.get(k)
            for k in ("code", "side", "qty", "avg_cost", "strike", "expiry", "dte")
        })
    return out


def _evidence_orders(items):
    out = []
    for o in items:
        if hasattr(o, "__dict__"):
            o = o.__dict__
        out.append({
            k: o.get(k)
            for k in (
                "order_id", "code", "side", "qty", "price", "status",
                "created_at", "updated_at", "dealt_qty", "dealt_avg_price"
            )
        })
    return out


def _evidence_deals(items):
    return [
        {k: d.get(k) for k in ("deal_id", "code", "side", "qty", "price", "created_at")}
        for d in items
    ]


def _ticket_baseline_positions(current_positions):
    # A newly issued ticket freezes the account as seen at issuance.
    # Never reuse the previous cycle snapshot as the new ticket baseline.
    return position_snapshot(current_positions)


def _format_price(v):
    return "NA" if v is None else f"{float(v):.4f}"


def _fill_lots(state, ticket):
    state.setdefault("lots", [])

    for fill in ticket.get("fill", []) or []:
        code = str(fill.get("code", ""))
        qty = _safe_int(fill.get("qty"))
        side = str(fill.get("side", "")).upper()
        expected_side = str(fill.get("expected_side", "")).upper()
        price = fill.get("avg_price")
        source = fill.get("price_source", "NOT_OBSERVED")
        if qty <= 0 or not is_qqq_option_code(code):
            continue

        # Only a BUY that establishes/increases a LONG near position creates a strategy lot.
        if side == "BUY" and expected_side == "LONG":
            lot_id = f'LOT-{ticket["ticket_id"]}-{code}'
            state["lots"].append({
                "lot_id": lot_id,
                "ticket_id": ticket["ticket_id"],
                "code": code,
                "qty": qty,
                "avg_cost": price,
                "opened_at": ticket.get("filled_at", ticket.get("issued_at")),
                "status": "OPEN",
                "price_source": source,
            })
            continue

        if side != "SELL" or expected_side != "LONG":
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
    match = next(
        (o for o in acct_orders if str(o.get("order_id")) == order_id),
        None,
    )
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


def _human_ticket(ticket):
    if not ticket:
        return "HOLD — no primary ticket"
    action = ticket.get("action", "")
    legs = ticket.get("legs", [])
    if action == "ROLL_NEAR" and len(legs) >= 2:
        a, b = legs[0], legs[1]
        return (
            f"ROLL {a.get('qty', 0)} {a.get('code')} SELL @{_format_price(a.get('price'))} "
            f"→ BUY {b.get('code')} @{_format_price(b.get('price'))}"
        )
    if action == "CLOSE_CAMPAIGN_EMERGENCY":
        return (
            "EMERGENCY CLOSE — "
            + " ; ".join(
                f"{x.get('side')} {x.get('qty')} {x.get('code')} @{_format_price(x.get('price'))}"
                for x in legs
            )
        )
    if len(legs) == 1:
        x = legs[0]
        return (
            f"{action} {x.get('qty', 0)} {x.get('code')} "
            f"{x.get('side')} @{_format_price(x.get('price'))}"
        )
    return action


def _filled_summary(events):
    for event in events:
        if event.get("type") == "TICKET_FILLED":
            fills = event.get("payload", {}).get("fill", [])
            if fills:
                parts = []
                for fill in fills:
                    parts.append(
                        f"FILLED {fill.get('qty')} {fill.get('code')} "
                        f"@ { _format_price(fill.get('avg_price')) } "
                        f"[{fill.get('price_source')}]"
                    )
                return " ; ".join(parts)
            return f"FILLED {event.get('payload', {}).get('action', '')}"
    return None


def _mark_position_summary(positions, quotes, contracts_by_code=None):
    rows=[]; unrealized=0.0
    for p in positions:
        q=quotes.get(p.code,{})
        mid=q.get("mid")
        bid=q.get("bid"); ask=q.get("ask")
        if mid is None and bid is not None and ask is not None and float(ask)>=float(bid):
            mid=(float(bid)+float(ask))/2
        if mid is None:
            rows.append({"code":p.code,"side":p.side,"qty":p.qty,"avg_cost":p.avg_cost,"status":"NO_MARK"})
            continue
        meta=(contracts_by_code or {}).get(p.code)
        size=max(1, _safe_int(getattr(meta, "lot_size", 100)) or 100)
        qty=_safe_int(p.qty); avg=_safe_float(p.avg_cost); side=str(p.side).upper()
        u=((float(mid)-avg) if side=="LONG" else (avg-float(mid)))*qty*size
        unrealized += u
        rows.append({"code":p.code,"side":side,"qty":qty,"avg_cost":avg,"mid":float(mid),"unrealized_pnl":u,"status":"MARKED"})
    return {
        "status":"OK" if rows and all(x["status"]=="MARKED" for x in rows) else ("PARTIAL" if rows else "EMPTY"),
        "unrealized_pnl":unrealized,
        "rows":rows,
        "realized_pnl":"NOT_TRACKED_BY_LIVE_DESK",
        "total_pnl":"NOT_TRACKED_BY_LIVE_DESK",
    }

def _action_card(ticket):
    if not ticket:
        return {"status":"NO_PRIMARY_TICKET","action":"HOLD","legs":[]}
    legs=[]
    for leg in ticket.get("legs",[]) or []:
        before=_safe_int(leg.get("before_qty"))
        target=_safe_int(leg.get("target_qty"))
        legs.append({
            "code":leg.get("code"),
            "side":leg.get("side"),
            "qty":_safe_int(leg.get("qty")),
            "before_qty":before,
            "target_qty":target,
            "delta_qty":target-before,
            "price":leg.get("price"),
            "expected_side":leg.get("expected_side"),
        })
    return {
        "status":ticket.get("status"),
        "action":ticket.get("action"),
        "ticket_id":ticket.get("ticket_id"),
        "campaign_id":ticket.get("campaign_id"),
        "reason":ticket.get("reason"),
        "issued_at":ticket.get("issued_at"),
        "legs":legs,
        "manual_execution_only":True,
    }

def _strategy_positions_for_plan(positions, spot, contracts_by_code):
    """
    Restrict the planner's LONG side to the strategy-managed near CALL universe.
    Unrelated QQQ long options (for example PUTs or longer-dated CALLs) must remain
    visible in broker exposure but must not be harvested/reduced by the V22 desk.
    FAR SHORTs remain available to the planner; it already matches the anchored far code.
    """
    out = []
    for p in positions:
        if p.side == "SHORT":
            out.append(p)
            continue
        if p.side != "LONG" or p.qty <= 0:
            continue
        meta = contracts_by_code.get(p.code)
        right = str(getattr(meta, "right", "")).upper()
        if (
            right == "CALL"
            and p.strike is not None
            and spot > 0
            and p.strike <= spot * 1.01
            and p.dte is not None
            and 0 <= int(p.dte) <= 35
        ):
            out.append(p)
    return out


def _strategy_position_analysis(positions, market, far, near, risk_state, contracts_by_code):
    spot = _safe_float((market or {}).get("spot"))
    qqq = [
        p for p in positions
        if is_qqq_option_code(p.code) and p.qty > 0 and p.side in {"LONG", "SHORT"}
    ]
    far_code = getattr(far, "code", None)
    far_shorts = [
        p for p in qqq
        if p.side == "SHORT"
        and (far_code is None or p.code == far_code)
        and str(getattr(contracts_by_code.get(p.code), "right", "")).upper() == "CALL"
    ]
    all_qqq_shorts = [p for p in qqq if p.side == "SHORT"]
    unmanaged_shorts = [
        p for p in all_qqq_shorts
        if far_code is None or p.code != far_code
    ]
    near_longs = [
        p for p in qqq
        if p.side == "LONG"
        and str(getattr(contracts_by_code.get(p.code), "right", "")).upper() == "CALL"
        and p.strike is not None
        and spot > 0
        and p.strike <= spot * 1.01
        and p.dte is not None
        and 0 <= int(p.dte) <= 35
    ]
    desired_near = _safe_int(risk_state.get("desired_stack")) if risk_state else None
    actual_far = sum(_safe_int(p.qty) for p in far_shorts)
    actual_near = sum(_safe_int(p.qty) for p in near_longs)
    return {
        "definition": {
            "far_short": "QQQ CALL; fixed 10 contracts at campaign entry",
            "near_call": "QQQ CALL; 0-35 DTE including roll window; strike <= 1.01×spot; selected around 0.50 delta",
        },
        "far_short_contracts": actual_far,
        "far_short_target_contracts": N_SHORT,
        "far_short_gap_contracts": N_SHORT - actual_far,
        "far_short_positions": [
            {"code": p.code, "qty": p.qty, "avg_cost": p.avg_cost, "strike": p.strike, "dte": p.dte}
            for p in far_shorts
        ],
        "unmanaged_qqq_short_contracts": sum(_safe_int(p.qty) for p in unmanaged_shorts),
        "unmanaged_qqq_short_positions": [
            {"code": p.code, "qty": p.qty, "avg_cost": p.avg_cost, "strike": p.strike, "dte": p.dte}
            for p in unmanaged_shorts
        ],
        "near_call_contracts": actual_near,
        "near_call_target_contracts": desired_near,
        "near_call_gap_contracts": None if desired_near is None else desired_near - actual_near,
        "near_call_positions": [
            {"code": p.code, "qty": p.qty, "avg_cost": p.avg_cost, "strike": p.strike, "dte": p.dte}
            for p in near_longs
        ],
        "all_qqq_long_option_contracts": sum(_safe_int(p.qty) for p in qqq if p.side == "LONG"),
        "selected_near_candidate": near.__dict__ if near else None,
    }


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
    repo = Path(__file__).resolve().parents[2]
    out_path = Path(args.out)
    store = StateStore(
        out_path.with_name("state.json"),
        out_path.with_name("events.jsonl"),
    )
    state = store.load()
    state["_now"] = now
    cycle_id = f"QQQ_DESK_{now.replace(':','').replace('-','').replace('.','').replace('+00:00','Z')}"
    evidence = EvidenceLedger(
        repo / "research/evidence_v1/evidence.jsonl",
        identity=runtime_identity(repo),
    )
    try:
        lock_status = assert_runtime_lock(
            repo,
            far_dte=args.far_dte,
            far_delta=args.far_delta,
            near_dte=args.near_dte,
        )
    except StrategyLockViolation as exc:
        evidence.append(
            "DATA_GAP",
            cycle_id=cycle_id,
            campaign_id=(state.get("campaign") or {}).get("id"),
            timestamp_utc=now,
            evidence_grade="DATA_GAP",
            payload={"stage": "STRATEGY_LOCK", "error": str(exc)},
        )
        evidence.append(
            "CYCLE_FINALIZED",
            cycle_id=cycle_id,
            campaign_id=(state.get("campaign") or {}).get("id"),
            timestamp_utc=now,
            evidence_grade="DATA_GAP",
            payload={"status": "BLOCKED_STRATEGY_LOCK"},
        )
        print(json.dumps({
            "status": "BLOCKED_STRATEGY_LOCK",
            "timestamp": now,
            "error": str(exc),
        }, ensure_ascii=False, indent=2))
        return 4

    evidence.append(
        "CYCLE_STARTED",
        cycle_id=cycle_id,
        campaign_id=(state.get("campaign") or {}).get("id"),
        timestamp_utc=now,
        payload={
            "cli": {
                "far_dte": args.far_dte,
                "far_delta": args.far_delta,
                "near_dte": args.near_dte,
                "simulate_account": args.simulate_account,
                "adopt_existing_far": args.adopt_existing_far,
            },
            "state_before": state.get("campaign"),
        },
    )
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
        evidence.append(
            "DATA_GAP",
            cycle_id=cycle_id,
            campaign_id=(state.get("campaign") or {}).get("id"),
            timestamp_utc=now,
            evidence_grade="DATA_GAP",
            payload={
                "stage": "MARKET_READER",
                "status": snap.get("status"),
                "reason": snap.get("reason") or snap.get("error") or "market snapshot unavailable",
                "connection_status": (snap.get("connection") or {}).get("status"),
            },
        )
        evidence.append(
            "CYCLE_FINALIZED",
            cycle_id=cycle_id,
            campaign_id=(state.get("campaign") or {}).get("id"),
            timestamp_utc=now,
            evidence_grade="DATA_GAP",
            payload={"status": "BLOCKED_MARKET_READER"},
        )
        output = {
            "status": "BLOCKED_MARKET_READER",
            "timestamp": now,
            "manual_execution_only": True,
            "positions_source": acct.get("source"),
            "account": acct,
            "market": snap,
        }
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(output, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return 2

    market = snap["market"]
    contracts = [C(x) for x in snap["contracts"]]
    quotes = snap.get("quotes", {})
    by = {c.code: c for c in contracts}

    positions = []
    unknown_qqq_positions = []
    for p in acct.get("positions", []):
        side = str(p.get("side", "")).upper()
        if is_qqq_option_code(p.get("code", "")) and side == "UNKNOWN":
            unknown_qqq_positions.append(p)
            continue
        if side not in {"LONG", "SHORT"}:
            continue
        meta = by.get(p["code"])
        q = quotes.get(p["code"], {})
        positions.append(
            Position(
                p["code"],
                side,
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

    if unknown_qqq_positions:
        evidence.append(
            "DATA_GAP",
            cycle_id=cycle_id,
            campaign_id=(state.get("campaign") or {}).get("id"),
            timestamp_utc=now,
            evidence_grade="DATA_GAP",
            payload={
                "stage": "POSITION_RECONCILIATION",
                "reason": "QQQ option position_side is missing or unrecognized",
                "unknown_count": len(unknown_qqq_positions),
            },
        )
        evidence.append(
            "CYCLE_FINALIZED",
            cycle_id=cycle_id,
            campaign_id=(state.get("campaign") or {}).get("id"),
            timestamp_utc=now,
            evidence_grade="DATA_GAP",
            payload={"status": "BLOCKED_UNKNOWN_POSITION_SIDE"},
        )
        output = {
            "status": "BLOCKED_UNKNOWN_POSITION_SIDE",
            "timestamp": now,
            "manual_execution_only": True,
            "unknown_qqq_positions": unknown_qqq_positions,
            "reasons": [
                "QQQ option position_side is missing/unrecognized",
                "desk refuses to infer LONG/SHORT",
            ],
        }
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(output, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return 3

    if campaign.get("state") == STATE_IDLE and args.adopt_existing_far:
        if len(qqq_shorts) != 1:
            raise RuntimeError(
                "--adopt-existing-far requires exactly one QQQ option short; "
                f"found {len(qqq_shorts)}"
            )
        campaign["id"] = make_campaign_id(
            now,
            store.next_campaign_sequence(state),
        )
        campaign["state"] = STATE_OPEN
        campaign["far_code"] = qqq_shorts[0].code
        campaign["started_at"] = now
        campaign["last_transition_at"] = now
        store.emit(
            state,
            "CAMPAIGN_ADOPTED_EXISTING_FAR",
            now=now,
            payload={
                "far_code": qqq_shorts[0].code,
                "qty": qqq_shorts[0].qty,
            },
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

    if far is None and campaign.get("state") == STATE_IDLE and not qqq_shorts:
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

    near = select_near(
        contracts,
        float(market["spot"]),
        args.near_dte,
    )
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

    planner_positions = _strategy_positions_for_plan(
        positions,
        float(market["spot"]),
        by,
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

    reconcile_events = []
    reconcile = reconcile_ticket(
        state,
        _position_dicts(positions),
        [o.__dict__ for o in acct_orders],
        acct.get("deals", []),
    )
    for event in reconcile.get("events", []):
        event_type = event.pop("type")
        reconcile_events.append(
            store.emit(
                state,
                event_type,
                now=now,
                payload=event,
            )
        )

    rp_done, rp_terminal, rp_events = _reconcile_order_ticket(
        state,
        [o.__dict__ for o in acct_orders],
        store,
        now,
    )
    reconcile_events.extend(rp_events)

    just_filled = bool(
        reconcile.get("filled")
        or rp_terminal
        or reconcile.get("superseded")
    )

    if reconcile_events:
        evidence.append(
            "EXECUTION_OBSERVED",
            cycle_id=cycle_id,
            campaign_id=(state.get("campaign") or {}).get("id"),
            timestamp_utc=now,
            evidence_grade="BROKER_OBSERVED",
            payload={
                "reconcile_events": reconcile_events,
                "ticket_after_reconcile": state.get("active_ticket"),
                "broker_source": acct.get("source"),
                "deal_warning": acct.get("deal_warning"),
            },
        )
        manual_events = [
            e for e in reconcile_events
            if str(e.get("type", "")).upper() in {
                "MANUAL_POSITION_CHANGE",
                "TICKET_SUPERSEDED_MANUAL_CHANGE",
                "MANUAL_RECONCILE",
            }
        ]
        if manual_events:
            evidence.append(
                "HUMAN_INTERVENTION",
                cycle_id=cycle_id,
                campaign_id=(state.get("campaign") or {}).get("id"),
                timestamp_utc=now,
                evidence_grade="HUMAN_REPORTED",
                payload={
                    "events": manual_events,
                    "note": "Manual intervention/change is preserved separately from strategy outcome.",
                },
            )

    if reconcile.get("filled"):
        filled_ticket = reconcile.get("ticket") or {}
        _fill_lots(state, filled_ticket)

        action = filled_ticket.get("action")
        if action == "SELL_FAR":
            _transition(state, STATE_OPEN, now, store)
        elif action == "CLOSE_CAMPAIGN_EMERGENCY":
            if not any(
                is_qqq_option_code(p.code) and p.qty > 0
                for p in positions
            ):
                campaign["far_code"] = None
                campaign["id"] = None
                _transition(state, STATE_IDLE, now, store)
            else:
                _transition(state, STATE_RECONCILE_WAIT, now, store)
        elif campaign.get("state") != STATE_IDLE:
            _transition(state, STATE_OPEN, now, store)

    campaign_active = campaign.get("state") != STATE_IDLE
    signal_active = bool(market.get("signal_active"))

    # A campaign cannot remain logically active after every managed QQQ option is gone.
    if campaign_active and not strict_positions and state.get("active_ticket") is None and not just_filled:
        campaign["id"] = None
        campaign["far_code"] = None
        _transition(state, STATE_IDLE, now, store)
        campaign_active = False

    unmanaged_short_block = (
        campaign.get("state") == STATE_IDLE and bool(qqq_shorts)
    )

    gamma_history = state.get("gamma_history") or []
    gamma_baseline = (
        sum(gamma_history[-20:]) / len(gamma_history[-20:])
        if len(gamma_history) >= 3 else None
    )
    previous_delta = state.get("far_delta")

    family_observation = build_family_snapshot(
        contracts,
        spot=float(market["spot"]),
        signal_active=signal_active and not unmanaged_short_block,
        campaign_active=campaign_active,
        active_far_code=far.code if far else None,
    )
    snapshot_payload = {
        "cycle_id": cycle_id,
        "captured_at_utc": now,
        "market": market,
        "contracts": [x.__dict__ for x in contracts],
        "quotes": quotes,
        "account": {
            "positions": _evidence_positions(positions),
            "orders": _evidence_orders(acct_orders),
            "deals": _evidence_deals(acct.get("deals", [])),
            "source": acct.get("source"),
            "deal_warning": acct.get("deal_warning"),
        },
        "campaign": campaign,
        "family_observation": family_observation,
        "engine_inputs": {
            "gamma_baseline": gamma_baseline,
            "previous_far_delta_abs": previous_delta,
            "signal_active": signal_active,
            "signal_active_for_plan": signal_active and not unmanaged_short_block,
            "planner_position_scope": "QQQ SHORTs + strategy-managed near CALL LONGs only",
            "planner_long_positions": _evidence_positions(
                [p for p in planner_positions if p.side == "LONG"]
            ),
        },
    }
    snapshot_ref = write_snapshot(repo, cycle_id, snapshot_payload)
    available_family_count = sum(
        1 for row in family_observation["rows"] if row["status"] == "AVAILABLE"
    )
    if available_family_count < family_observation["family_count_expected"]:
        evidence.append(
            "DATA_GAP",
            cycle_id=cycle_id,
            campaign_id=campaign.get("id"),
            timestamp_utc=now,
            evidence_grade="DATA_GAP",
            payload={
                "stage": "FAMILY_OBSERVATION",
                "expected_family_members": family_observation["family_count_expected"],
                "available_family_members": available_family_count,
                "missing_family_members": family_observation["family_count_expected"] - available_family_count,
                "note": "Unavailable family members remain explicit; no substitution or inference.",
            },
        )
    evidence.append(
        "PRE_DECISION_OBSERVATION",
        cycle_id=cycle_id,
        campaign_id=campaign.get("id"),
        timestamp_utc=now,
        payload={
            "snapshot": snapshot_ref,
            "market": market,
            "campaign_state": campaign.get("state"),
            "positions": _evidence_positions(positions),
            "far_candidate": far.__dict__ if far else None,
            "near_candidate": near.__dict__ if near else None,
            "family_observation_count": family_observation["config_count"],
            "active_family_count": sum(
                1 for x in family_observation["rows"] if x["active_family"]
            ),
            "engine_inputs": snapshot_payload["engine_inputs"],
            "observation_is_pre_decision": True,
        },
    )

    p = plan(
        market=market,
        far=far,
        near=near,
        positions=planner_positions,
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
            "use --adopt-existing-far only after verifying ownership",
        ] + list(p.get("reasons", []))

    primary = None
    if (
        not just_filled
        and state.get("active_ticket") is None
        and campaign.get("state") != STATE_EMERGENCY_CLOSE
    ):
        primary = choose_primary_action(p.get("candidate_actions", []))

    if primary:
        action_name = str(primary.get("action"))

        if campaign.get("state") == STATE_IDLE and action_name == "SELL_FAR":
            campaign["id"] = make_campaign_id(
                now,
                store.next_campaign_sequence(state),
            )
            campaign["far_code"] = primary["code"]
            campaign["started_at"] = now

        new_state = transition_for_action(
            campaign.get("state", STATE_IDLE),
            action_name,
        )
        _transition(state, new_state, now, store)

        ticket = build_ticket(
            action=primary,
            campaign_id=campaign.get("id"),
            before_positions=_ticket_baseline_positions(positions),
            now=now,
            sequence=store.next_ticket_sequence(state),
        )
        if action_name == "REPRICE_OR_CANCEL":
            ticket["legs"][0]["order_id"] = primary.get("order_id")
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

    if far:
        state["far_code"] = far.code
        if far.delta is not None:
            state["far_delta"] = abs(float(far.delta))
        if far.gamma is not None:
            hist = state.setdefault("gamma_history", [])
            hist.append(abs(float(far.gamma)))
            state["gamma_history"] = hist[-20:]

    if p.get("risk_state"):
        new_target = p["risk_state"].get("desired_stack")
        new_risk = p["risk_state"].get("risk_score")
        old_target = state.get("last_target_stack")
        if old_target is not None and new_target != old_target:
            store.emit(
                state,
                "TARGET_STACK_CHANGE",
                now=now,
                payload={
                    "from": old_target,
                    "to": new_target,
                    "risk_score": new_risk,
                },
            )
        state["last_target_stack"] = new_target
        state["last_risk_score"] = new_risk
        campaign["target_stack"] = new_target

    store.record_position_snapshot(state, positions)
    state.pop("_now", None)
    store.save(state)

    filled_message = _filled_summary(reconcile_events)
    primary_ticket = state.get("active_ticket")

    if primary_ticket:
        status = "WAITING_MANUAL_TICKET"
        instruction = _human_ticket(primary_ticket)
    elif filled_message:
        status = "RECONCILED_FILL"
        instruction = filled_message
    elif reconcile.get("superseded"):
        status = "MANUAL_CHANGE_RECONCILE"
        instruction = "Manual position change detected; ticket superseded. Recompute on next cycle."
    elif p.get("status", "").startswith("BLOCKED"):
        status = p.get("status")
        instruction = "BLOCK — no new order should be issued."
    else:
        status = p.get("status", "HOLD")
        instruction = "HOLD — no primary ticket."

    mark_summary = _mark_position_summary(strict_positions, quotes, by)
    position_analysis = _strategy_position_analysis(
        strict_positions,
        market,
        far,
        near,
        p.get("risk_state"),
        by,
    )
    action_card = _action_card(primary_ticket)

    evidence.append(
        "DECISION_EMITTED",
        cycle_id=cycle_id,
        campaign_id=campaign.get("id"),
        timestamp_utc=now,
        payload={
            "status": status,
            "signal_active": signal_active,
            "plan_status": p.get("status"),
            "risk_state": p.get("risk_state"),
            "candidate_actions": p.get("candidate_actions", []),
            "primary": primary,
            "ticket": primary_ticket,
            "next_triggers": p.get("next_triggers", []),
            "reasons": p.get("reasons", []),
            "family_observation_count": family_observation["config_count"],
            "snapshot_sha256": snapshot_ref["snapshot_sha256"],
        },
    )

    evidence.append(
        "CYCLE_FINALIZED",
        cycle_id=cycle_id,
        campaign_id=campaign.get("id"),
        timestamp_utc=now,
        payload={
            "status": status,
            "instruction": instruction,
            "campaign": campaign,
            "active_ticket": state.get("active_ticket"),
            "reconcile_event_count": len(reconcile_events),
            "candidate_action_count": len(p.get("candidate_actions", [])),
            "snapshot_sha256": snapshot_ref["snapshot_sha256"],
        },
    )

    output = {
        "status": status,
        "instruction": instruction,
        "timestamp": now,
        "signal_active": signal_active,
        "campaign": campaign,
        "active_ticket": state.get("active_ticket"),
        "primary_ticket": primary_ticket,
        "action_card": action_card,
        "position_mark": mark_summary,
        "position_analysis": position_analysis,
        "one_primary_ticket_per_cycle": True,
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
        "unknown_qqq_positions": unknown_qqq_positions,
        "account_source": acct.get("source"),
        "deal_warning": acct.get("deal_warning"),
        "source": "FUTU_OPEND_READ_ONLY",
        "manual_execution_only": True,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
