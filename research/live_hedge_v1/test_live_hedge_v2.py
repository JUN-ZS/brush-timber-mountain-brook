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
    _publish_live_output,
    _ticket_baseline_positions,
)


def now_iso():
    return datetime.now(timezone.utc).isoformat()


class LiveHedgeV2Test(unittest.TestCase):
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


    def test_schema2_gamma_spot_but_raw_scale_resets(self):
        state = {
            "gamma_history": [0.01, 0.012, 0.011, 0.015, 0.02],
            "gamma_history_schema": 2,
            "gamma_history_unit": "gamma_spot",
        }
        hist = ensure_gamma_history_schema(state, spot=500.0)

        self.assertEqual(hist, [])
        self.assertEqual(state["gamma_history"], [])
        self.assertEqual(state["gamma_history_schema"], 2)
        self.assertEqual(state["gamma_history_unit"], "gamma_spot")
        self.assertEqual(
            state.get("gamma_history_reset_reason"),
            "values_look_like_raw_abs_gamma",
        )

if __name__ == "__main__":
    unittest.main()
