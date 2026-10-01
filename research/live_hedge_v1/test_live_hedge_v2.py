from __future__ import annotations

import unittest
from pathlib import Path
from datetime import datetime, timezone

from research.live_hedge_v1.campaign import (
    STATE_OPEN,
    build_ticket,
    choose_primary_action,
    is_qqq_option_code,
    position_snapshot,
    reconcile_ticket,
)
from research.live_hedge_v1.engine import (
    Contract,
    Order,
    Position,
    GAMMA_HISTORY_SCHEMA,
    GAMMA_HISTORY_UNIT,
    ensure_gamma_history_schema,
    gamma_baseline_from_history,
    plan,
    quote_age_sec,
)
from research.live_hedge_v1.state import live_desk_mutation_lock
from research.live_hedge_v1.run_live_desk import (
    _action_card,
    _fill_lots,
    _publish_live_output,
    _sync_managed_far_ownership,
    _ticket_baseline_positions,
)


def now_iso():
    return datetime.now(timezone.utc).isoformat()


class LiveHedgeV2Test(unittest.TestCase):
    def test_futu_naive_us_timestamp_is_interpreted_as_exchange_local(self):
        from research.live_hedge_v1.campaign import _is_after, _parse_time
        # 17:00 New York on 2026-10-01 is 21:00 UTC (EDT).
        parsed = _parse_time("2026-10-01 17:00:00")
        self.assertEqual(parsed.utcoffset().total_seconds(), 0)
        self.assertEqual(parsed.hour, 21)
        self.assertTrue(_is_after("2026-10-01 17:00:00", "2026-10-01T18:00:00+00:00"))

    def test_stale_order_age_uses_us_exchange_timezone(self):
        from research.live_hedge_v1.engine import quote_age_sec
        now = datetime.fromisoformat("2026-10-01T21:02:00+00:00")
        age = quote_age_sec(
            "2026-10-01 17:00:00",
            now=now,
            naive_is_local=True,
        )
        # 17:00 New York = 21:00 UTC on this date.
        self.assertAlmostEqual(age, 120.0, places=6)

    def test_trade_reader_does_not_fallback_deal_id_to_order_id(self):
        from research.live_hedge_v1.futu_trade_reader import FutuTradeReader
        class Row:
            def __init__(self, value):
                self.value = value
            def get(self, key, default=None):
                return self.value if key == "code" else {
                    "orderIDEx": "ORDER-123",
                    "code": "US.QQQ260116C00600000",
                    "trd_side": "SELL_SHORT",
                    "qty": 1,
                    "price": 2.0,
                    "create_time": "2026-10-01 17:00:00",
                }.get(key, default)
        class DF:
            def iterrows(self):
                yield 0, Row(None)
        parsed = FutuTradeReader()._parse_deals(DF())
        self.assertEqual(parsed[0]["deal_id"], "")

    def test_position_side_does_not_infer_from_trade_words(self):
        from research.live_hedge_v1.futu_trade_reader import FutuTradeReader
        self.assertEqual(FutuTradeReader._position_side("BUY"), "UNKNOWN")
        self.assertEqual(FutuTradeReader._position_side("SELL"), "UNKNOWN")


    def test_live_desk_mutation_lock_serializes_threads(self):
        import tempfile
        import threading
        with tempfile.TemporaryDirectory() as td:
            active = [0]
            peak = [0]
            guard = threading.Lock()

            def worker():
                with live_desk_mutation_lock(Path(td) / "state.json"):
                    with guard:
                        active[0] += 1
                        peak[0] = max(peak[0], active[0])
                    import time
                    time.sleep(0.02)
                    with guard:
                        active[0] -= 1

            a = threading.Thread(target=worker)
            b = threading.Thread(target=worker)
            a.start(); b.start(); a.join(); b.join()
            self.assertEqual(peak[0], 1)


    def test_action_card_preserves_explicit_roll_leg_semantics(self):
        ticket = {
            "status": "OPEN",
            "action": "ROLL_NEAR",
            "ticket_id": "T-ROLL",
            "legs": [
                {"code": "US.QQQ.OLD", "side": "SELL", "qty": 2, "before_qty": 2, "target_qty": 0,
                 "strategy_leg_action": "REDUCE_NEAR", "why": "near expiry risk"},
                {"code": "US.QQQ.NEW", "side": "BUY", "qty": 2, "before_qty": 0, "target_qty": 2,
                 "strategy_leg_action": "ADD_NEAR"},
            ],
        }
        card = _action_card(ticket)
        self.assertEqual(card["legs"][0]["strategy_leg_action"], "REDUCE_NEAR")
        self.assertEqual(card["legs"][1]["strategy_leg_action"], "ADD_NEAR")


    def test_reader_expiry_universe_includes_all_research_windows(self):
        from research.live_hedge_v1.futu_reader import LiveFutuReader
        reader = object.__new__(LiveFutuReader)
        class FakeFutu:
            RET_OK = 0
        class FakeCtx:
            def get_option_expiration_date(self, code):
                class Column(list):
                    def tolist(self):
                        return list(self)

                class D:
                    columns = ["strike_time"]
                    def __init__(self):
                        self.data = {
                            "strike_time": Column([
                                "2026-10-08", "2026-10-15", "2026-10-22",
                                "2026-10-29", "2026-11-30", "2026-12-30"
                            ])
                        }
                    def __getitem__(self, key):
                        return self.data[key]
                return 0, D()
        class FakeAdapter:
            futu = FakeFutu()
            ctx = FakeCtx()
        reader.a = FakeAdapter()
        got = reader._expiry_targets(asof_date=datetime.strptime("2026-10-01", "%Y-%m-%d").date())
        self.assertEqual(
            got,
            ["2026-10-08","2026-10-15","2026-10-22","2026-10-29","2026-11-30","2026-12-30"],
        )


    def test_quote_date_is_used_as_live_asof_date(self):
        from research.live_hedge_v1.futu_reader import LiveFutuReader
        reader = object.__new__(LiveFutuReader)
        self.assertEqual(
            reader._quote_date("2026-10-01 21:30:00"),
            datetime.strptime("2026-10-01", "%Y-%m-%d").date(),
        )
        self.assertIsNone(reader._quote_date("not-a-date"))


    def test_strict_qqq_universe(self):
        self.assertTrue(is_qqq_option_code("US.QQQ260116C00700000"))
        self.assertFalse(is_qqq_option_code("US.QQQ"))
        self.assertFalse(is_qqq_option_code("US.QCOM260116C00200000"))

    def test_one_primary_priority(self):
        candidates = [
            {"action": "ADD_NEAR", "qty": 2},
            {"action": "REDUCE_NEAR", "qty": 1},
            {"action": "HARVEST_NEAR", "qty": 1},
            {"action": "ROLL_NEAR", "qty": 1},
        ]
        self.assertEqual(choose_primary_action(candidates)["action"], "HARVEST_NEAR")

    def test_plan_can_emit_candidates_but_wrapper_selects_one(self):
        market = {
            "source": "LIVE QUOTE",
            "timestamp": now_iso(),
            "spot": 500.0,
            "signal_active": True,
        }
        far = Contract(
            "US.QQQ260116C00600000", "CALL", 600.0, "2026-01-16", 100,
            2.0, 2.5, 0.08, 0.01
        )
        near = Contract(
            "US.QQQ261030C00500000", "CALL", 500.0, "2026-10-30", 30,
            8.0, 8.5, 0.50, 0.03
        )
        positions = [
            Position("US.QQQ260116C00600000", "SHORT", 10, 2.0, 600, "2026-01-16", 100),
            Position("US.QQQ261003C00500000", "LONG", 5, 4.0, 500, "2026-10-03", 2),
        ]
        out = plan(
            market=market,
            far=far,
            near=near,
            positions=positions,
            orders=[],
            signal_active=True,
            far_campaign_active=True,
            quotes_by_code={
                "US.QQQ261003C00500000": {"bid": 7.0},
                "US.QQQ260116C00600000": {"bid": 2.0, "ask": 2.5},
            },
            previous_far_delta_abs=0.08,
            near_lots=[{
                "lot_id": "LOT-TEST",
                "code": "US.QQQ261003C00500000",
                "qty": 5,
                "status": "OPEN",
            }],
        )
        self.assertIn("candidate_actions", out)
        self.assertTrue(out["next_triggers"])
        self.assertIn(choose_primary_action(out["candidate_actions"])["action"],
                      {"HARVEST_NEAR", "ROLL_NEAR", "REDUCE_NEAR", "REPRICE_OR_CANCEL", "ADD_NEAR", "REPAIR_FAR"})

    def test_ticket_exact_fill_records_fill(self):
        before = position_snapshot([
            {"code": "US.QQQ260116C00600000", "side": "SHORT", "qty": 10, "avg_cost": 2.0},
        ])
        ticket = build_ticket(
            action={"action": "ADD_NEAR", "code": "US.QQQ261030C00500000", "qty": 2, "side": "BUY", "price": 8.5, "why": "test"},
            campaign_id="C-TEST",
            before_positions=before,
            now="2026-10-01T00:00:00+00:00",
            sequence=1,
        )
        state = {
            "_now": "2026-10-01T00:01:00+00:00",
            "active_ticket": ticket,
            "last_positions": before,
        }
        result = reconcile_ticket(
            state,
            [
                {"code": "US.QQQ260116C00600000", "side": "SHORT", "qty": 10, "avg_cost": 2.0},
                {"code": "US.QQQ261030C00500000", "side": "LONG", "qty": 2, "avg_cost": 8.4},
            ],
            [],
            [{
                "deal_id": "D1",
                "code": "US.QQQ261030C00500000",
                "side": "BUY",
                "qty": 2,
                "price": 8.4,
                "created_at": "2026-10-01T00:00:30+00:00",
            }],
        )
        self.assertTrue(result["filled"])
        self.assertIsNone(state["active_ticket"])
        self.assertEqual(result["ticket"]["fill"][0]["avg_price"], 8.4)


    def test_sell_far_builds_short_delta_and_matches_sell_short(self):
        before = position_snapshot([])
        ticket = build_ticket(
            action={"action":"SELL_FAR","code":"US.QQQ260116C00600000","qty":10,"side":"SELL","price":2.0,"why":"entry"},
            campaign_id="C-TEST", before_positions=before,
            now="2026-10-01T00:00:00+00:00", sequence=3,
        )
        leg = ticket["legs"][0]
        self.assertEqual(leg["expected_side"], "SHORT")
        self.assertEqual(leg["before_qty"], 0)
        self.assertEqual(leg["target_qty"], 10)
        self.assertIn("SELL_SHORT", leg["broker_sides"])
        state={"_now":"2026-10-01T00:01:00+00:00","active_ticket":ticket,"last_positions":before}
        result=reconcile_ticket(
            state,
            [{"code":"US.QQQ260116C00600000","side":"SHORT","qty":10,"avg_cost":2.0}],
            [],
            [{"deal_id":"D-FAR","code":"US.QQQ260116C00600000","side":"SELL_SHORT","qty":10,"price":2.0,"created_at":"2026-10-01T00:00:30+00:00"}],
        )
        self.assertTrue(result["filled"])
        self.assertEqual(result["ticket"]["fill"][0]["avg_price"], 2.0)

    def test_far_close_accepts_buy_back_direction(self):
        before = position_snapshot([
            {"code":"US.QQQ260116C00600000","side":"SHORT","qty":10,"avg_cost":2.0},
        ])
        ticket = build_ticket(
            action={"action":"CLOSE_CAMPAIGN_EMERGENCY","legs":[{"code":"US.QQQ260116C00600000","side":"BUY","qty":10,"price":3.0}],"why":"far strike touch"},
            campaign_id="C-TEST", before_positions=before,
            now="2026-10-01T00:00:00+00:00", sequence=5,
        )
        leg = ticket["legs"][0]
        self.assertEqual(leg["target_qty"], 0)
        self.assertIn("BUY_BACK", leg["broker_sides"])
        state={"_now":"2026-10-01T00:01:00+00:00","active_ticket":ticket,"last_positions":before}
        result=reconcile_ticket(
            state, [], [],
            [{"deal_id":"D-CLOSE","code":"US.QQQ260116C00600000","side":"BUY_BACK","qty":10,"price":3.0,"created_at":"2026-10-01T00:00:30+00:00"}],
        )
        self.assertTrue(result["filled"])
        self.assertEqual(result["ticket"]["fill"][0]["avg_price"], 3.0)
    def test_partial_fill_is_partial_not_superseded(self):
        before=position_snapshot([{"code":"US.QQQ261030C00500000","side":"LONG","qty":1,"avg_cost":4.0}])
        ticket=build_ticket(
            action={"action":"ADD_NEAR","code":"US.QQQ261030C00500000","qty":2,"side":"BUY","price":5.0,"why":"partial"},
            campaign_id="C-TEST", before_positions=before,
            now="2026-10-01T00:00:00+00:00", sequence=4,
        )
        state={"_now":"2026-10-01T00:01:00+00:00","active_ticket":ticket,"last_positions":before}
        result=reconcile_ticket(
            state,
            [{"code":"US.QQQ261030C00500000","side":"LONG","qty":2,"avg_cost":4.5}],
            [],
            [{"deal_id":"D-PART","code":"US.QQQ261030C00500000","side":"BUY","qty":1,"price":5.0,"created_at":"2026-10-01T00:00:30+00:00"}],
        )
        self.assertFalse(result["filled"])
        self.assertTrue(result["partial"])
        self.assertFalse(result["superseded"])
        self.assertEqual(state["active_ticket"]["status"], "PARTIAL")

    def test_multi_cycle_fill_price_is_cumulative_from_ticket_baseline(self):
        before = position_snapshot([])
        ticket = build_ticket(
            action={
                "action": "ADD_NEAR",
                "code": "US.QQQ261030C00500000",
                "qty": 2,
                "side": "BUY",
                "price": 8.0,
                "why": "multi-cycle",
            },
            campaign_id="C-TEST",
            before_positions=before,
            now="2026-10-01T00:00:00+00:00",
            sequence=10,
        )
        state = {
            "_now": "2026-10-01T00:01:00+00:00",
            "active_ticket": ticket,
            "last_positions": before,
        }

        cycle1 = reconcile_ticket(
            state,
            [{
                "code": "US.QQQ261030C00500000",
                "side": "LONG",
                "qty": 1,
                "avg_cost": 8.0,
            }],
            [],
            [{
                "deal_id": "D1",
                "code": "US.QQQ261030C00500000",
                "side": "BUY",
                "qty": 1,
                "price": 8.0,
                "created_at": "2026-10-01T00:00:30+00:00",
            }],
        )
        self.assertTrue(cycle1["partial"])
        self.assertEqual(cycle1["ticket"]["fill"][0]["qty"], 1)
        self.assertEqual(cycle1["ticket"]["fill"][0]["avg_price"], 8.0)

        # Desk advances last_positions, but the ticket baseline remains frozen
        # at issuance. An empty deal read must not turn the fill price into 0.
        state["last_positions"] = position_snapshot([{
            "code": "US.QQQ261030C00500000",
            "side": "LONG",
            "qty": 1,
            "avg_cost": 8.0,
        }])
        state["_now"] = "2026-10-01T00:02:00+00:00"
        cycle2 = reconcile_ticket(
            state,
            [{
                "code": "US.QQQ261030C00500000",
                "side": "LONG",
                "qty": 1,
                "avg_cost": 8.0,
            }],
            [],
            [],
        )
        self.assertTrue(cycle2["partial"])
        self.assertEqual(cycle2["ticket"]["fill"][0]["qty"], 1)
        self.assertEqual(cycle2["ticket"]["fill"][0]["avg_price"], 8.0)
        self.assertEqual(
            cycle2["events"][0]["fill_semantics"],
            "CUMULATIVE_SINCE_TICKET_ISSUE",
        )

        state["last_positions"] = position_snapshot([{
            "code": "US.QQQ261030C00500000",
            "side": "LONG",
            "qty": 1,
            "avg_cost": 8.0,
        }])
        state["_now"] = "2026-10-01T00:03:00+00:00"
        cycle3 = reconcile_ticket(
            state,
            [{
                "code": "US.QQQ261030C00500000",
                "side": "LONG",
                "qty": 2,
                "avg_cost": 9.0,
            }],
            [],
            [
                {
                    "deal_id": "D1",
                    "code": "US.QQQ261030C00500000",
                    "side": "BUY",
                    "qty": 1,
                    "price": 8.0,
                    "created_at": "2026-10-01T00:00:30+00:00",
                },
                {
                    "deal_id": "D2",
                    "code": "US.QQQ261030C00500000",
                    "side": "BUY",
                    "qty": 1,
                    "price": 10.0,
                    "created_at": "2026-10-01T00:02:30+00:00",
                },
            ],
        )
        self.assertTrue(cycle3["filled"])
        self.assertEqual(cycle3["ticket"]["fill"][0]["qty"], 2)
        self.assertEqual(cycle3["ticket"]["fill"][0]["avg_price"], 9.0)
        self.assertIsNone(state["active_ticket"])

    def test_position_target_without_complete_broker_evidence_stays_partial(self):
        before = position_snapshot([])
        ticket = build_ticket(
            action={
                "action": "ADD_NEAR",
                "code": "US.QQQ261030C00500000",
                "qty": 2,
                "side": "BUY",
                "price": 8.0,
                "why": "incomplete evidence",
            },
            campaign_id="C-TEST",
            before_positions=before,
            now="2026-10-01T00:05:00+00:00",
            sequence=13,
        )
        state = {
            "_now": "2026-10-01T00:06:00+00:00",
            "active_ticket": ticket,
            "last_positions": before,
        }
        result = reconcile_ticket(
            state,
            [{
                "code": "US.QQQ261030C00500000",
                "side": "LONG",
                "qty": 2,
                "avg_cost": 0,
            }],
            [],
            [{
                "deal_id": "D1",
                "code": "US.QQQ261030C00500000",
                "side": "BUY",
                "qty": 1,
                "price": 8.0,
                "created_at": "2026-10-01T00:05:30+00:00",
            }],
        )
        self.assertFalse(result["filled"])
        self.assertTrue(result["partial"])
        self.assertFalse(result["broker_execution_complete"])
        self.assertEqual(state["active_ticket"]["status"], "PARTIAL")
        self.assertFalse(result["ticket"]["fill"])
        self.assertTrue(
            any(
                e["type"] == "TICKET_WAITING_EXECUTION_EVIDENCE"
                for e in result["events"]
            )
        )
        self.assertFalse(result["ticket"]["fill"])


    def test_deal_and_order_evidence_are_not_double_counted(self):
        before = position_snapshot([{
            "code": "US.QQQ261030C00500000",
            "side": "LONG",
            "qty": 2,
            "avg_cost": 7.0,
        }])
        ticket = build_ticket(
            action={
                "action": "CLOSE_NEAR",
                "code": "US.QQQ261030C00500000",
                "qty": 2,
                "side": "SELL",
                "price": 9.0,
                "why": "close",
            },
            campaign_id="C-TEST",
            before_positions=before,
            now="2026-10-01T00:00:00+00:00",
            sequence=11,
        )
        state = {
            "_now": "2026-10-01T00:01:00+00:00",
            "active_ticket": ticket,
            "last_positions": before,
        }
        result = reconcile_ticket(
            state,
            [],
            [{
                "order_id": "O1",
                "code": "US.QQQ261030C00500000",
                "side": "SELL",
                "qty": 2,
                "price": 9.0,
                "status": "FILLED",
                "created_at": "2026-10-01T00:00:30+00:00",
                "dealt_qty": 2,
                "dealt_avg_price": 10.0,
            }],
            [{
                "deal_id": "D1",
                "code": "US.QQQ261030C00500000",
                "side": "SELL",
                "qty": 2,
                "price": 9.0,
                "created_at": "2026-10-01T00:00:30+00:00",
            }],
        )
        self.assertTrue(result["filled"])
        self.assertEqual(result["ticket"]["fill"][0]["avg_price"], 9.0)

    def test_new_ticket_baseline_uses_current_positions(self):
        stale_last = position_snapshot([{
            "code": "US.QQQ261030C00500000",
            "side": "LONG",
            "qty": 1,
            "avg_cost": 4.0,
        }])
        current = [{
            "code": "US.QQQ261030C00500000",
            "side": "LONG",
            "qty": 5,
            "avg_cost": 9.0,
        }]

        baseline = _ticket_baseline_positions(current)
        ticket = build_ticket(
            action={
                "action": "ADD_NEAR",
                "code": "US.QQQ261030C00500000",
                "qty": 2,
                "side": "BUY",
                "price": 10.0,
                "why": "new ticket baseline",
            },
            campaign_id="C-TEST",
            before_positions=baseline,
            now="2026-10-01T00:04:00+00:00",
            sequence=12,
        )
        leg = ticket["legs"][0]

        # A manual position change between cycles must be absorbed into the
        # new ticket's frozen baseline; the prior cycle snapshot is stale.
        self.assertNotEqual(stale_last["LONG:US.QQQ261030C00500000"]["qty"], leg["before_qty"])
        self.assertEqual(leg["before_qty"], 5)
        self.assertEqual(leg["before_avg_cost"], 9.0)
        self.assertEqual(leg["target_qty"], 7)

    def test_broker_complete_ticket_becomes_filled_after_manual_offset(self):
        before = position_snapshot([])
        ticket = build_ticket(
            action={
                "action": "ADD_NEAR",
                "code": "US.QQQ261030C00500000",
                "qty": 5,
                "side": "BUY",
                "price": 8.5,
            },
            campaign_id="C-TEST",
            before_positions=before,
            now="2026-10-01T00:00:00+00:00",
            sequence=1,
        )
        state = {
            "_now": "2026-10-01T00:03:00+00:00",
            "active_ticket": ticket,
            "last_positions": before,
        }
        result = reconcile_ticket(
            state,
            [{
                "code": "US.QQQ261030C00500000",
                "side": "LONG",
                "qty": 3,
                "avg_cost": 8.5,
            }],
            [],
            [{
                "deal_id": "D1",
                "code": "US.QQQ261030C00500000",
                "side": "BUY",
                "qty": 5,
                "price": 8.5,
                "created_at": "2026-10-01T00:01:00+00:00",
            }],
        )
        self.assertTrue(result["filled"])
        self.assertTrue(result["superseded"])
        self.assertTrue(result["broker_execution_complete"])
        self.assertIsNone(state["active_ticket"])
        self.assertEqual(result["ticket"]["fill"][0]["qty"], 5)
        self.assertEqual(
            result["ticket"]["fill"][0]["price_source"],
            "BROKER_EVIDENCE_CUMULATIVE",
        )
        self.assertEqual(result["events"][0]["type"], "MANUAL_POSITION_CHANGE")
        self.assertEqual(result["events"][1]["type"], "TICKET_SUPERSEDED")

    def test_manual_change_supersedes_ticket(self):
        before = position_snapshot([
            {"code": "US.QQQ261030C00500000", "side": "LONG", "qty": 1, "avg_cost": 4.0},
        ])
        ticket = build_ticket(
            action={"action": "ADD_NEAR", "code": "US.QQQ261030C00500000", "qty": 2, "side": "BUY", "price": 5.0, "why": "test"},
            campaign_id="C-TEST",
            before_positions=before,
            now="2026-10-01T00:00:00+00:00",
            sequence=2,
        )
        state = {
            "_now": "2026-10-01T00:01:00+00:00",
            "active_ticket": ticket,
            "last_positions": before,
        }
        result = reconcile_ticket(
            state,
            [{"code": "US.QQQ261030C00500000", "side": "LONG", "qty": 4, "avg_cost": 4.5}],
            [],
            [],
        )
        self.assertTrue(result["superseded"])
        self.assertIsNone(state["active_ticket"])
        self.assertTrue(any(e["type"] == "MANUAL_POSITION_CHANGE" for e in result["events"]))

    def test_naive_broker_timestamp_does_not_crash(self):
        age = quote_age_sec("2026-10-01 00:00:00", datetime.now(timezone.utc), naive_is_local=True)
        self.assertIsNotNone(age)




    def test_plan_blocks_near_ownership_mismatch(self):
        market = {
            "source": "LIVE QUOTE",
            "timestamp": now_iso(),
            "spot": 500.0,
            "signal_active": True,
        }
        far = Contract(
            "US.QQQ260116C00600000", "CALL", 600.0, "2026-01-16", 100,
            2.0, 2.5, 0.08, 0.01
        )
        near = Contract(
            "US.QQQ261030C00500000", "CALL", 500.0, "2026-10-30", 30,
            8.0, 8.5, 0.50, 0.03
        )
        positions = [
            Position("US.QQQ260116C00600000", "SHORT", 10, 2.0, 600, "2026-01-16", 100),
            Position("US.QQQ261003C00500000", "LONG", 5, 4.0, 500, "2026-10-03", 2),
        ]
        out = plan(
            market=market, far=far, near=near, positions=positions, orders=[],
            signal_active=True, far_campaign_active=True,
            quotes_by_code={
                "US.QQQ261003C00500000": {"bid": 7.0},
                "US.QQQ260116C00600000": {"bid": 2.0, "ask": 2.5},
            },
            previous_far_delta_abs=0.08,
            near_lots=[{
                "lot_id": "LOT-TEST",
                "code": "US.QQQ261003C00500000",
                "qty": 4,
                "status": "OPEN",
            }],
        )
        self.assertEqual(out["status"], "BLOCKED_NEAR_OWNERSHIP_MISMATCH")
        self.assertEqual(out["candidate_actions"], [])
        self.assertEqual(
            out["near_ownership_mismatches"]["US.QQQ261003C00500000"]["position_qty"],
            5,
        )
        self.assertEqual(
            out["near_ownership_mismatches"]["US.QQQ261003C00500000"]["tracked_lot_qty"],
            4,
        )


    def test_state_store_recovers_unsaved_active_ticket_from_event_log(self):
        import tempfile
        from research.live_hedge_v1.state import StateStore
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "live_state.json"
            store = StateStore(out.with_name("state.json"), out.with_name("events.jsonl"))
            state = store.load()
            state["campaign"] = {
                "id": "C-RECOVER-0001",
                "state": "ARMING",
                "far_code": "US.QQQ260116C00600000",
                "managed_far_qty": 0,
            }
            ticket = build_ticket(
                action={
                    "action": "SELL_FAR",
                    "code": "US.QQQ260116C00600000",
                    "qty": 10,
                    "side": "SELL",
                    "price": 2.0,
                },
                campaign_id="C-RECOVER-0001",
                before_positions={},
                now="2026-10-01T00:00:00+00:00",
                sequence=1,
            )
            store.emit(
                state,
                "TICKET_ISSUED",
                now="2026-10-01T00:00:00+00:00",
                payload={"ticket": ticket},
            )
            # Simulate a crash before state.save(): disk state has no ticket.
            recovered = store.load()
            self.assertIsNotNone(recovered["active_ticket"])
            self.assertEqual(recovered["active_ticket"]["ticket_id"], ticket["ticket_id"])
            self.assertEqual(recovered["campaign"]["id"], "C-RECOVER-0001")
            self.assertEqual(recovered["campaign"]["far_code"], "US.QQQ260116C00600000")
            self.assertEqual(recovered["campaign"]["managed_far_qty"], 0)

    def test_state_store_recovery_advances_far_ownership_from_fill_event(self):
        import tempfile
        from research.live_hedge_v1.state import StateStore
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "live_state.json"
            store = StateStore(out.with_name("state.json"), out.with_name("events.jsonl"))
            state = store.load()
            state["campaign"] = {
                "id": "C-RECOVER-0003",
                "state": "ARMING",
                "far_code": "US.QQQ260116C00600000",
                "managed_far_qty": 0,
            }
            ticket = build_ticket(
                action={
                    "action": "SELL_FAR",
                    "code": "US.QQQ260116C00600000",
                    "qty": 10,
                    "side": "SELL",
                    "price": 2.0,
                },
                campaign_id="C-RECOVER-0003",
                before_positions={},
                now="2026-10-01T00:00:00+00:00",
                sequence=3,
            )
            store.emit(
                state,
                "TICKET_ISSUED",
                now="2026-10-01T00:00:00+00:00",
                payload={"ticket": ticket},
            )
            store.emit(
                state,
                "TICKET_FILLED",
                now="2026-10-01T00:01:00+00:00",
                payload={
                    "ticket_id": ticket["ticket_id"],
                    "action": "SELL_FAR",
                    "fill": [{
                        "code": "US.QQQ260116C00600000",
                        "side": "SELL",
                        "expected_side": "SHORT",
                        "qty": 10,
                        "avg_price": 2.1,
                        "price_source": "BROKER_EVIDENCE_CUMULATIVE",
                    }],
                },
            )
            recovered = store.load()
            self.assertIsNone(recovered["active_ticket"])
            self.assertEqual(recovered["campaign"]["managed_far_qty"], 10)
            self.assertEqual(recovered["campaign"]["far_ownership_source"], "BROKER_EXECUTION_EVIDENCE")

    def test_state_store_replays_strategy_near_lots_after_state_crash(self):
        import tempfile
        from research.live_hedge_v1.state import StateStore
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "live_state.json"
            store = StateStore(out.with_name("state.json"), out.with_name("events.jsonl"))
            state = store.load()
            state["campaign"] = {
                "id": "C-RECOVER-LOT",
                "state": "HARVESTING",
                "far_code": "US.QQQ260116C00600000",
                "managed_far_qty": 10,
            }
            ticket = build_ticket(
                action={
                    "action": "ADD_NEAR",
                    "code": "US.QQQ261030C00500000",
                    "qty": 2,
                    "side": "BUY",
                    "price": 8.0,
                },
                campaign_id="C-RECOVER-LOT",
                before_positions={},
                now="2026-10-01T00:00:00+00:00",
                sequence=4,
            )
            store.emit(
                state,
                "TICKET_ISSUED",
                now="2026-10-01T00:00:00+00:00",
                payload={"ticket": ticket},
            )
            store.emit(
                state,
                "TICKET_FILLED",
                now="2026-10-01T00:01:00+00:00",
                payload={
                    "ticket_id": ticket["ticket_id"],
                    "action": "ADD_NEAR",
                    "fill": [{
                        "code": "US.QQQ261030C00500000",
                        "side": "BUY",
                        "expected_side": "LONG",
                        "qty": 2,
                        "avg_price": 8.25,
                        "price_source": "BROKER_EVIDENCE_CUMULATIVE",
                    }],
                },
            )
            recovered = store.load()
            assert len(recovered["lots"]) == 1
            assert recovered["lots"][0]["code"] == "US.QQQ261030C00500000"
            assert recovered["lots"][0]["qty"] == 2
            assert recovered["lots"][0]["avg_cost"] == 8.25

    def test_state_store_terminal_event_clears_stale_ticket_on_recovery(self):
        import tempfile
        from research.live_hedge_v1.state import StateStore
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "live_state.json"
            store = StateStore(out.with_name("state.json"), out.with_name("events.jsonl"))
            state = store.load()
            state["campaign"] = {
                "id": "C-RECOVER-0002",
                "state": "OPEN",
                "far_code": "US.QQQ260116C00600000",
                "managed_far_qty": 10,
            }
            ticket = build_ticket(
                action={
                    "action": "REPAIR_FAR",
                    "code": "US.QQQ260116C00600000",
                    "target_qty": 10,
                    "current_qty": 9,
                    "side": "SELL",
                    "qty": 1,
                    "price": 2.0,
                },
                campaign_id="C-RECOVER-0002",
                before_positions={
                    "SHORT:US.QQQ260116C00600000": {
                        "code": "US.QQQ260116C00600000",
                        "side": "SHORT",
                        "qty": 9,
                        "avg_cost": 2.0,
                    }
                },
                now="2026-10-01T00:00:00+00:00",
                sequence=2,
            )
            state["active_ticket"] = ticket
            store.save(state)
            store.emit(
                state,
                "TICKET_FILLED",
                now="2026-10-01T00:01:00+00:00",
                payload={"ticket_id": ticket["ticket_id"], "action": ticket["action"], "fill": []},
            )
            recovered = store.load()
            self.assertIsNone(recovered["active_ticket"])

    def test_live_state_publisher_writes_valid_json_atomically(self):
        import json
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "live_state.json"
            _publish_live_output(out, {"status": "HOLD", "manual_execution_only": True})
            self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["status"], "HOLD")
            self.assertFalse((Path(str(out) + ".tmp")).exists())

    def test_near_ownership_ignores_short_strategy_lots(self):
        market = {
            "source": "LIVE QUOTE",
            "timestamp": now_iso(),
            "spot": 500.0,
            "signal_active": True,
        }
        far = Contract(
            "US.QQQ260116C00600000", "CALL", 600.0, "2026-01-16", 100,
            2.0, 2.5, 0.08, 0.01,
        )
        near = Contract(
            "US.QQQ261030C00500000", "CALL", 500.0, "2026-10-30", 30,
            8.0, 8.5, 0.50, 0.03,
        )
        positions = [
            Position("US.QQQ260116C00600000", "SHORT", 10, 2.0, 600, "2026-01-16", 100),
            Position("US.QQQ261003C00500000", "LONG", 5, 4.0, 500, "2026-10-03", 2),
        ]
        out = plan(
            market=market, far=far, near=near, positions=positions, orders=[],
            signal_active=True, far_campaign_active=True,
            quotes_by_code={
                "US.QQQ261003C00500000": {"bid": 7.0},
                "US.QQQ260116C00600000": {"bid": 2.0, "ask": 2.5},
            },
            previous_far_delta_abs=0.08,
            near_lots=[{
                "lot_id": "FAR-SAME-CODE",
                "code": "US.QQQ261003C00500000",
                "side": "SHORT",
                "qty": 5,
                "status": "OPEN",
            }],
        )
        self.assertEqual(out["status"], "BLOCKED_NEAR_OWNERSHIP_MISMATCH")
        self.assertEqual(
            out["near_ownership_mismatches"]["US.QQQ261003C00500000"]["tracked_lot_qty"],
            0,
        )

    def test_far_ownership_requires_explicit_baseline(self):
        market = {
            "source": "LIVE QUOTE",
            "timestamp": now_iso(),
            "spot": 500.0,
            "signal_active": True,
        }
        far = Contract(
            "US.QQQ260116C00600000", "CALL", 600.0, "2026-01-16", 100,
            2.0, 2.5, 0.08, 0.01,
        )
        out = plan(
            market=market, far=far, near=None,
            positions=[
                Position("US.QQQ260116C00600000", "SHORT", 10, 2.0, 600, "2026-01-16", 100),
            ],
            orders=[],
            signal_active=True,
            far_campaign_active=True,
            far_ownership_enforced=True,
            managed_far_qty=None,
            managed_far_code=far.code,
            quotes_by_code={far.code: {"bid": 2.0, "ask": 2.5}},
        )
        self.assertEqual(out["status"], "BLOCKED_FAR_OWNERSHIP_UNBASELINED")
        self.assertEqual(out["candidate_actions"], [])

    def test_far_ownership_blocks_same_code_and_extra_short_mismatch(self):
        market = {
            "source": "LIVE QUOTE",
            "timestamp": now_iso(),
            "spot": 500.0,
            "signal_active": False,
        }
        far = Contract(
            "US.QQQ260116C00600000", "CALL", 600.0, "2026-01-16", 100,
            2.0, 2.5, 0.08, 0.01,
        )
        out = plan(
            market=market, far=far, near=None,
            positions=[
                Position("US.QQQ260116C00600000", "SHORT", 12, 2.0, 600, "2026-01-16", 100),
                Position("US.QQQ261030C00700000", "SHORT", 1, 1.0, 700, "2026-10-30", 120),
            ],
            orders=[],
            signal_active=False,
            far_campaign_active=True,
            far_ownership_enforced=True,
            managed_far_qty=10,
            managed_far_code=far.code,
            quotes_by_code={
                far.code: {"bid": 2.0, "ask": 2.5},
                "US.QQQ261030C00700000": {"bid": 1.0, "ask": 1.2},
            },
        )
        self.assertEqual(out["status"], "BLOCKED_FAR_OWNERSHIP_MISMATCH")
        self.assertEqual(out["candidate_actions"], [])

    def test_stale_partial_order_uses_remaining_quantity(self):
        market = {
            "source": "LIVE QUOTE",
            "timestamp": now_iso(),
            "spot": 500.0,
            "signal_active": True,
        }
        far = Contract(
            "US.QQQ260116C00600000", "CALL", 600.0, "2026-01-16", 100,
            2.0, 2.5, 0.08, 0.01,
        )
        near = Contract(
            "US.QQQ261030C00500000", "CALL", 500.0, "2026-10-30", 30,
            8.0, 8.5, 0.50, 0.03,
        )
        stale = Order(
            "O-PARTIAL", "US.QQQ261030C00500000", "BUY", 10, 8.5, "SUBMITTED",
            "2026-10-01T00:00:00+00:00",
            "2026-10-01T00:00:00+00:00",
            dealt_qty=7,
            dealt_avg_price=8.4,
        )
        out = plan(
            market=market, far=far, near=near,
            positions=[
                Position("US.QQQ260116C00600000", "SHORT", 10, 2.0, 600, "2026-01-16", 100),
            ],
            orders=[stale],
            signal_active=True, far_campaign_active=True,
            quotes_by_code={
                "US.QQQ260116C00600000": {"bid": 2.0, "ask": 2.5},
                "US.QQQ261030C00500000": {"bid": 8.0, "ask": 8.5},
            },
            previous_far_delta_abs=0.08,
            near_lots=[],
            now=datetime.fromisoformat("2026-10-01T00:05:00+00:00"),
        )
        reprice = next(x for x in out["candidate_actions"] if x["action"] == "REPRICE_OR_CANCEL")
        self.assertEqual(reprice["qty"], 3)

    def test_strategy_lot_application_is_idempotent_after_retry(self):
        state = {"lots": []}
        ticket = build_ticket(
            action={
                "action": "ADD_NEAR",
                "code": "US.QQQ261030C00500000",
                "qty": 2,
                "side": "BUY",
                "price": 8.5,
            },
            campaign_id="C-IDEM",
            before_positions={},
            now="2026-10-01T00:00:00+00:00",
            sequence=21,
        )
        ticket["status"] = "FILLED"
        ticket["filled_at"] = "2026-10-01T00:01:00+00:00"
        ticket["fill"] = [{
            "code": "US.QQQ261030C00500000",
            "side": "BUY",
            "expected_side": "LONG",
            "qty": 2,
            "avg_price": 8.4,
            "price_source": "BROKER_EVIDENCE_CUMULATIVE",
        }]
        _fill_lots(state, ticket)
        _fill_lots(state, ticket)
        self.assertEqual(len(state["lots"]), 1)
        self.assertEqual(state["lots"][0]["qty"], 2)
        self.assertEqual(state["lots"][0]["avg_cost"], 8.4)

    def test_roll_reduction_is_idempotent_after_retry(self):
        state = {
            "lots": [{
                "lot_id": "OLD",
                "ticket_id": "T0",
                "code": "US.QQQ261030C00500000",
                "qty": 2,
                "avg_cost": 5.0,
                "opened_at": "2026-10-01T00:00:00+00:00",
                "status": "OPEN",
            }]
        }
        ticket = build_ticket(
            action={
                "action": "ROLL_NEAR",
                "code": "US.QQQ261030C00500000",
                "qty": 2,
                "price": 7.0,
                "new_code": "US.QQQ261100C00505000",
                "new_price": 8.0,
            },
            campaign_id="C-ROLL-IDEM",
            before_positions=position_snapshot([{
                "code": "US.QQQ261030C00500000",
                "side": "LONG",
                "qty": 2,
                "avg_cost": 5.0,
            }]),
            now="2026-10-01T00:00:00+00:00",
            sequence=22,
        )
        ticket["fill"] = [
            {
                "code": "US.QQQ261030C00500000",
                "side": "SELL",
                "expected_side": "LONG",
                "qty": 2,
                "avg_price": 7.0,
                "price_source": "BROKER_EVIDENCE_CUMULATIVE",
            },
            {
                "code": "US.QQQ261100C00505000",
                "side": "BUY",
                "expected_side": "LONG",
                "qty": 2,
                "avg_price": 8.0,
                "price_source": "BROKER_EVIDENCE_CUMULATIVE",
            },
        ]
        _fill_lots(state, ticket)
        _fill_lots(state, ticket)
        self.assertFalse(any(
            x["status"] == "OPEN" and x["code"] == "US.QQQ261030C00500000"
            for x in state["lots"]
        ))
        new_lots = [x for x in state["lots"] if x["code"] == "US.QQQ261100C00505000"]
        self.assertEqual(len(new_lots), 1)
        self.assertEqual(new_lots[0]["qty"], 2)

    def test_far_ownership_sync_uses_broker_evidence_not_position(self):
        from research.live_hedge_v1.run_live_desk import _sync_managed_far_ownership
        campaign = {"far_code": "US.QQQ260116C00600000", "managed_far_qty": 10}
        ticket = build_ticket(
            action={
                "action": "REPAIR_FAR",
                "code": "US.QQQ260116C00600000",
                "target_qty": 10,
                "current_qty": 7,
                "direction": "ADD",
                "side": "SELL",
                "qty": 3,
                "price": 2.0,
            },
            campaign_id="C-OWN",
            before_positions={
                "SHORT:US.QQQ260116C00600000": {
                    "code": "US.QQQ260116C00600000",
                    "side": "SHORT",
                    "qty": 7,
                    "avg_cost": 2.0,
                }
            },
            now="2026-10-01T00:00:00+00:00",
            sequence=20,
        )
        reconcile = {
            "evidence_by_leg": {
                "SHORT:US.QQQ260116C00600000": {
                    "required_qty": 3,
                    "evidence_qty": 3,
                }
            }
        }
        _sync_managed_far_ownership(campaign, ticket, reconcile)
        self.assertEqual(campaign["managed_far_qty"], 10)
        self.assertEqual(campaign["far_ownership_source"], "BROKER_EXECUTION_EVIDENCE")

class GammaHistoryMigrationTests(unittest.TestCase):
    """Legacy raw |γ| must not mix with gamma_spot; schema markers gate warm-up."""

    def test_old_schema_resets_history(self):
        state = {
            "gamma_history": [0.01, 0.012, 0.011, 0.015, 0.02, 0.018],
            "gamma_history_schema": 1,
            "gamma_history_unit": "raw_abs_gamma",
        }
        hist = ensure_gamma_history_schema(state, spot=500.0)
        self.assertEqual(hist, [])
        self.assertEqual(state["gamma_history"], [])
        self.assertEqual(state["gamma_history_schema"], GAMMA_HISTORY_SCHEMA)
        self.assertEqual(state["gamma_history_unit"], GAMMA_HISTORY_UNIT)
        self.assertEqual(state.get("gamma_history_reset_reason"), "missing_or_wrong_markers")
        self.assertIsNone(gamma_baseline_from_history(hist))

    def test_schema2_gamma_spot_keeps_history(self):
        vals = [5.0, 5.2, 4.8, 5.1, 5.3, 5.0]
        state = {
            "gamma_history": list(vals),
            "gamma_history_schema": 2,
            "gamma_history_unit": "gamma_spot",
        }
        hist = ensure_gamma_history_schema(state, spot=500.0)
        self.assertEqual(hist, vals)
        self.assertIsNone(state.get("gamma_history_reset_reason"))
        self.assertIsNotNone(gamma_baseline_from_history(hist))
        self.assertAlmostEqual(gamma_baseline_from_history(hist), 5.05, places=6)

    def test_missing_unit_resets_even_if_schema2(self):
        state = {
            "gamma_history": [5.0, 5.2, 4.8, 5.1, 5.3],
            "gamma_history_schema": 2,
        }
        hist = ensure_gamma_history_schema(state, spot=500.0)
        self.assertEqual(hist, [])
        self.assertEqual(state["gamma_history_unit"], GAMMA_HISTORY_UNIT)
        self.assertEqual(state.get("gamma_history_reset_reason"), "missing_or_wrong_markers")

    def test_mixed_or_wrong_unit_resets(self):
        state = {
            "gamma_history": [0.01, 5.0, 0.02],
            "gamma_history_schema": 2,
            "gamma_history_unit": "abs_gamma",
        }
        hist = ensure_gamma_history_schema(state, spot=500.0)
        self.assertEqual(hist, [])
        self.assertEqual(state["gamma_history_schema"], 2)
        self.assertEqual(state["gamma_history_unit"], "gamma_spot")

    def test_fresh_baseline_only_after_five_observations(self):
        state = {
            "gamma_history": [0.01, 0.012, 0.011, 0.015, 0.02],
            # no schema markers -> legacy reset
        }
        ensure_gamma_history_schema(state, spot=500.0)
        self.assertEqual(state["gamma_history"], [])
        for i in range(4):
            state["gamma_history"].append(4.0 + 0.1 * i)
            self.assertIsNone(
                gamma_baseline_from_history(state["gamma_history"]),
                msg=f"baseline must stay None while fresh_count={i+1} < 5",
            )
        state["gamma_history"].append(4.5)
        base = gamma_baseline_from_history(state["gamma_history"])
        self.assertIsNotNone(base)
        self.assertAlmostEqual(base, 4.2, places=6)


    def test_non_finite_gamma_history_is_discarded_not_used(self):
        state = {
            "gamma_history": [5.0, float("inf"), 5.2, float("-inf"), 5.1],
            "gamma_history_schema": 2,
            "gamma_history_unit": "gamma_spot",
        }
        hist = ensure_gamma_history_schema(state, spot=500.0)
        self.assertEqual(hist, [5.0, 5.2, 5.1])
        self.assertTrue(all(v == v and abs(v) < float("inf") for v in hist))
        self.assertIsNone(gamma_baseline_from_history([1, 2, 3, 4, float("inf")]))

    def test_state_store_does_not_trust_unmarked_legacy_gamma_history(self):
        import json
        import tempfile
        from research.live_hedge_v1.state import StateStore
        with tempfile.TemporaryDirectory() as td:
            state_path = Path(td) / "state.json"
            state_path.write_text(
                json.dumps({"schema_version": 1, "gamma_history": [5.0, 5.1, 5.2]}),
                encoding="utf-8",
            )
            store = StateStore(state_path, Path(td) / "events.jsonl")
            state = store.load()
            self.assertEqual(state["gamma_history"], [5.0, 5.1, 5.2])
            hist = ensure_gamma_history_schema(state, spot=500.0)
            self.assertEqual(hist, [])
            self.assertEqual(state["gamma_history"], [])

    def test_schema2_gamma_spot_marker_is_authoritative(self):
        state = {
            "gamma_history": [0.01, 0.012, 0.011, 0.015, 0.02],
            "gamma_history_schema": 2,
            "gamma_history_unit": "gamma_spot",
        }
        hist = ensure_gamma_history_schema(state, spot=500.0)

        # Numeric magnitude is not provenance. Once the explicit schema marker
        # says gamma_spot, the engine keeps the observations instead of guessing
        # their unit from scale.
        self.assertEqual(hist, state["gamma_history"])
        self.assertEqual(state["gamma_history_schema"], 2)
        self.assertEqual(state["gamma_history_unit"], "gamma_spot")
        self.assertNotIn("gamma_history_reset_reason", state)

if __name__ == "__main__":
    unittest.main()
