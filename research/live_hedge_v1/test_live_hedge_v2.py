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


def now_iso():
    return datetime.now(timezone.utc).isoformat()


class LiveHedgeV2Test(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
