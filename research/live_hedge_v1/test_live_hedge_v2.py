from __future__ import annotations

import unittest
from datetime import datetime, timezone

from research.live_hedge_v1.campaign import (
    STATE_OPEN,
    build_ticket,
    choose_primary_action,
    is_qqq_option_code,
    position_snapshot,
    reconcile_ticket,
)
from research.live_hedge_v1.engine import Contract, Order, Position, plan, quote_age_sec
from research.live_hedge_v1.futu_reader import _compute_signal, _enrich_contracts_with_quotes
from research.live_hedge_v1.futu_trade_reader import FutuTradeReader
from research.live_hedge_v1.run_live_desk import (
    _apply_signal_gate,
    _position_dicts,
    _strategy_position_analysis,
    _strategy_positions_for_plan,
    _ticket_baseline_positions,
)


def now_iso():
    return datetime.now(timezone.utc).isoformat()


class LiveHedgeV2Test(unittest.TestCase):
    def test_explicit_account_id_is_required_before_trade_queries(self):
        reader = FutuTradeReader(acc_id=None)
        self.assertIsNone(reader.acc_id)

    def test_account_verification_requires_exact_active_us_account(self):
        class FakeEnv:
            REAL = "REAL"

        class FakeFutu:
            RET_OK = 0
            TrdEnv = FakeEnv

        class FakeCtx:
            def __init__(self, rows):
                self.rows = rows
            def get_acc_list(self):
                return 0, self.rows

        reader = FutuTradeReader(real=True, acc_id=123456)
        reader.futu = FakeFutu
        reader.ctx = FakeCtx([{
            "acc_id": 123456,
            "trd_env": "REAL",
            "acc_status": "ACTIVE",
            "trdmarket_auth": ["US"],
            "card_num": "CARD0007",
            "uni_card_num": "UNI0007",
        }])
        self.assertTrue(reader._verify_account())
        self.assertEqual(reader.account["acc_id"], 123456)
        self.assertEqual(reader.account["card_num_last4"], "0007")

        reader.acc_id = 999999
        self.assertFalse(reader._verify_account())
        self.assertIn("NOT_FOUND", reader.account_error)

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

    def test_incomplete_broker_evidence_does_not_become_full_price(self):
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
        self.assertTrue(result["filled"])
        self.assertEqual(result["ticket"]["fill"][0]["qty"], 2)
        self.assertIsNone(result["ticket"]["fill"][0]["avg_price"])
        self.assertEqual(
            result["ticket"]["fill"][0]["price_source"],
            "BROKER_EVIDENCE_INCOMPLETE",
        )

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


    def test_plan_blocks_stale_source_quote_even_when_read_is_recent(self):
        market = {
            "source": "LIVE QUOTE",
            "timestamp": now_iso(),
            "source_age_sec": 46.0,
            "spot": 500.0,
        }
        far = Contract(
            "US.QQQ261231C00600000", "CALL", 600.0, "2026-12-31", 90,
            2.0, 2.2, 0.08, 0.01
        )
        out = plan(
            market=market,
            far=far,
            near=None,
            positions=[],
            orders=[],
            signal_active=True,
            far_campaign_active=True,
            now=datetime.now(timezone.utc),
        )
        self.assertEqual(out["status"], "BLOCKED_STALE_MARKET")
        self.assertEqual(out["candidate_actions"], [])

    def test_signal_data_gap_never_becomes_inactive_signal(self):
        from research.live_hedge_v1.run_live_desk import _apply_signal_gate

        plan_result = {
            "status": "ACTIONABLE",
            "candidate_actions": [
                {"action": "SELL_FAR", "qty": 10},
            ],
            "reasons": ["NO_ACTIVE_CAMPAIGN_BUT_ENTRY_SIGNAL_ACTIVE"],
        }
        out = _apply_signal_gate(plan_result, None, "DATA_GAP")
        self.assertEqual(out["status"], "BLOCKED_SIGNAL_DATA_GAP")
        self.assertEqual(out["candidate_actions"], [])
        self.assertIn("history/data gap", out["reasons"][0])

    def test_open_ticket_defers_fresh_planner_actions(self):
        from research.live_hedge_v1.run_live_desk import _defer_actions_for_active_ticket

        plan_result = {
            "status": "ACTIONABLE",
            "candidate_actions": [
                {"action": "REPAIR_FAR", "qty": 10},
                {"action": "ADD_NEAR", "qty": 3},
            ],
            "reasons": ["RISK_SCORE=2.50"],
        }
        ticket = {
            "ticket_id": "T-TEST",
            "status": "OPEN",
            "action": "SELL_FAR",
        }
        out = _defer_actions_for_active_ticket(plan_result, ticket)
        self.assertEqual(out["status"], "WAITING_ACTIVE_TICKET")
        self.assertEqual(out["candidate_actions"], [])
        self.assertEqual(
            [x["action"] for x in out["deferred_candidate_actions"]],
            ["REPAIR_FAR", "ADD_NEAR"],
        )
        self.assertTrue(any("ACTIVE_TICKET_OPEN:T-TEST" in r for r in out["reasons"]))

    def test_signal_reports_history_data_gap_instead_of_false(self):
        dates = [f"2026-01-{i:02d}" for i in range(1, 11)]
        history = list(zip(dates, [100.0] * 10))
        out = _compute_signal(110.0, history)
        self.assertEqual(out["status"], "DATA_GAP")
        self.assertIsNone(out["active"])
        self.assertEqual(out["reference_count"], 10)
        self.assertIn("need >=252", out["reason"])

    def test_signal_computes_from_252_reference_closes(self):
        dates = [f"2025-01-{(i % 28)+1:02d} {i//28:02d}" for i in range(252)]
        history = list(zip(dates, [100.0] * 252))
        out = _compute_signal(110.0, history)
        self.assertEqual(out["status"], "OK")
        self.assertTrue(out["active"])
        self.assertAlmostEqual(out["ext200"], 0.1, places=8)
        self.assertAlmostEqual(out["ratio52"], 1.1, places=8)

    def test_live_quote_greeks_enrich_chain_before_selection(self):
        from backtest.types import OptionContract

        raw = OptionContract(
            code="US.QQQ261030C00500000",
            underlying="US.QQQ",
            right="CALL",
            strike=500.0,
            expiry="2026-10-30",
            dte=30,
            lot_size=100,
            bid=None,
            ask=None,
            last=None,
            iv=None,
            delta=None,
            gamma=None,
            theta=None,
            vega=None,
            oi=None,
            volume=None,
            source="LIVE QUOTE",
        )
        quote = OptionContract(
            code="US.QQQ261030C00500000",
            underlying="US.QQQ",
            right="CALL",
            strike=500.0,
            expiry="2026-10-30",
            dte=30,
            lot_size=100,
            bid=8.0,
            ask=8.2,
            last=8.1,
            iv=0.21,
            delta=0.50,
            gamma=0.03,
            theta=-0.1,
            vega=0.2,
            oi=1000,
            volume=50,
            source="LIVE QUOTE",
        )
        out = _enrich_contracts_with_quotes([raw], [quote])
        self.assertEqual(out[0].delta, 0.50)
        self.assertEqual(out[0].gamma, 0.03)
        self.assertEqual(out[0].bid, 8.0)
        self.assertEqual(out[0].ask, 8.2)

    def test_state_snapshot_accepts_position_objects(self):
        import tempfile
        from pathlib import Path
        from research.live_hedge_v1.state import StateStore

        with tempfile.TemporaryDirectory() as td:
            store = StateStore(Path(td) / "state.json", Path(td) / "events.jsonl")
            state = {}
            positions = [
                Position(
                    "US.QQQ261030C00500000",
                    "LONG",
                    2,
                    7.0,
                    500,
                    "2026-10-30",
                    30,
                )
            ]
            store.record_position_snapshot(state, positions)
            self.assertEqual(
                state["last_positions"]["LONG:US.QQQ261030C00500000"]["qty"],
                2,
            )
            self.assertEqual(
                state["last_positions"]["LONG:US.QQQ261030C00500000"]["avg_cost"],
                7.0,
            )

    def test_ticket_baseline_accepts_position_objects(self):
        from research.live_hedge_v1.run_live_desk import _ticket_baseline_positions

        positions = [
            Position(
                "US.QQQ261030C00500000",
                "LONG",
                2,
                7.0,
                500,
                "2026-10-30",
                30,
            )
        ]
        baseline = _ticket_baseline_positions(positions)
        self.assertEqual(
            baseline["LONG:US.QQQ261030C00500000"]["qty"],
            2,
        )
        self.assertEqual(
            baseline["LONG:US.QQQ261030C00500000"]["avg_cost"],
            7.0,
        )

    def test_position_object_normalizes_for_campaign_reconciliation(self):
        from research.live_hedge_v1.run_live_desk import _position_dicts

        positions = [
            Position(
                "US.QQQ261030C00500000",
                "LONG",
                2,
                7.0,
                500,
                "2026-10-30",
                30,
            )
        ]
        self.assertEqual(
            _position_dicts(positions),
            [{
                "code": "US.QQQ261030C00500000",
                "side": "LONG",
                "qty": 2,
                "avg_cost": 7.0,
                "strike": 500,
                "expiry": "2026-10-30",
                "dte": 30,
                "delta": None,
                "gamma": None,
            }],
        )

    def test_position_analysis_counts_call_near_legs_including_roll_window(self):
        from research.live_hedge_v1.run_live_desk import _strategy_position_analysis

        market = {"spot": 500.0}
        far = Contract(
            "US.QQQ261231C00600000", "CALL", 600.0, "2026-12-31", 90,
            2.0, 2.2, 0.08, 0.01
        )
        near = Contract(
            "US.QQQ261030C00500000", "CALL", 500.0, "2026-10-30", 30,
            8.0, 8.2, 0.50, 0.03
        )
        positions = [
            Position("US.QQQ261231C00600000", "SHORT", 10, 2.0, 600, "2026-12-31", 90),
            Position("US.QQQ261003C00500000", "LONG", 2, 6.0, 500, "2026-10-03", 2),
            Position("US.QQQ261030C00500000", "LONG", 1, 7.0, 500, "2026-10-30", 30),
            Position("US.QQQ261030P00500000", "LONG", 9, 7.0, 500, "2026-10-30", 30),
        ]
        contracts_by_code = {
            "US.QQQ261231C00600000": far,
            "US.QQQ261003C00500000": Contract(
                "US.QQQ261003C00500000", "CALL", 500.0, "2026-10-03", 2,
                6.0, 6.2, 0.50, 0.03
            ),
            "US.QQQ261030C00500000": near,
            "US.QQQ261030P00500000": Contract(
                "US.QQQ261030P00500000", "PUT", 500.0, "2026-10-30", 30,
                8.0, 8.2, -0.50, 0.03
            ),
        }
        out = _strategy_position_analysis(
            positions, market, far, near, {"desired_stack": 3}, contracts_by_code
        )
        self.assertEqual(out["far_short_contracts"], 10)
        self.assertEqual(out["near_call_contracts"], 3)
        self.assertEqual(out["near_call_target_contracts"], 3)
        self.assertEqual(len(out["near_call_positions"]), 2)

    def test_planner_excludes_unrelated_long_options(self):
        far = Contract(
            "US.QQQ261231C00600000", "CALL", 600.0, "2026-12-31", 90,
            2.0, 2.2, 0.08, 0.01
        )
        near = Contract(
            "US.QQQ261030C00500000", "CALL", 500.0, "2026-10-30", 30,
            8.0, 8.2, 0.50, 0.03
        )
        put = Contract(
            "US.QQQ261030P00500000", "PUT", 500.0, "2026-10-30", 30,
            8.0, 8.2, -0.50, 0.03
        )
        positions = [
            Position("US.QQQ261231C00600000", "SHORT", 10, 2.0, 600, "2026-12-31", 90),
            Position("US.QQQ261030C00500000", "LONG", 2, 7.0, 500, "2026-10-30", 30),
            Position("US.QQQ261030P00500000", "LONG", 8, 7.0, 500, "2026-10-30", 30),
        ]
        scoped = _strategy_positions_for_plan(
            positions, 500.0, {
                far.code: far,
                near.code: near,
                put.code: put,
            }
        )
        self.assertEqual(
            [(p.code, p.side, p.qty) for p in scoped],
            [
                ("US.QQQ261231C00600000", "SHORT", 10),
                ("US.QQQ261030C00500000", "LONG", 2),
            ],
        )

    def test_naive_broker_timestamp_does_not_crash(self):
        age = quote_age_sec("2026-10-01 00:00:00", datetime.now(timezone.utc), naive_is_local=True)
        self.assertIsNotNone(age)


if __name__ == "__main__":
    unittest.main()
