from __future__ import annotations

import unittest

from .run_instance import manual_apply_trade, manual_position_snapshot, summarize_strategy_pnl


class SingleStrategyPnlTests(unittest.TestCase):
    def test_same_code_isolated_by_strategy_id(self):
        lots = []
        manual_apply_trade(lots, action="ADD", code="US.QQQ.CALL_A", qty=2, price=5.0,
                           lot_size=100, trade_id="A1", timestamp="2026-10-01T00:00:00Z",
                           strategy_id="STRAT_A")
        manual_apply_trade(lots, action="ADD", code="US.QQQ.CALL_A", qty=3, price=7.0,
                           lot_size=100, trade_id="B1", timestamp="2026-10-01T00:01:00Z",
                           strategy_id="STRAT_B")
        pnl, _ = manual_apply_trade(lots, action="REDUCE", code="US.QQQ.CALL_A", qty=1, price=8.0,
                                    lot_size=100, trade_id="A2", timestamp="2026-10-01T00:02:00Z",
                                    strategy_id="STRAT_A")
        self.assertEqual(pnl, 300.0)
        positions = {p["strategy_id"]: p for p in manual_position_snapshot(lots)}
        self.assertEqual(positions["STRAT_A"]["qty"], 1)
        self.assertEqual(positions["STRAT_B"]["qty"], 3)
        self.assertEqual(positions["STRAT_A"]["avg_cost"], 5.0)
        self.assertEqual(positions["STRAT_B"]["avg_cost"], 7.0)

    def test_cannot_close_another_strategy_lots_by_shared_option_code(self):
        lots = []
        manual_apply_trade(lots, action="ADD", code="US.QQQ.CALL_A", qty=2, price=5.0,
                           lot_size=100, trade_id="B1", timestamp="2026-10-01T00:00:00Z",
                           strategy_id="STRAT_B")
        with self.assertRaisesRegex(SystemExit, "MANUAL_REDUCE_EXCEEDS_POSITION"):
            manual_apply_trade(lots, action="REDUCE", code="US.QQQ.CALL_A", qty=1, price=8.0,
                               lot_size=100, trade_id="A1", timestamp="2026-10-01T00:01:00Z",
                               strategy_id="STRAT_A")

    def test_missing_mark_is_pending_not_zero(self):
        lots = [
            {"lot_id":"A1", "strategy_id":"STRAT_A", "code":"US.QQQ.CALL_A", "side":"LONG",
             "qty":1, "avg_price":5.0, "lot_size":100, "status":"OPEN"},
            {"lot_id":"B1", "strategy_id":"STRAT_B", "code":"US.QQQ.PUT_B", "side":"SHORT",
             "qty":1, "avg_price":2.0, "lot_size":100, "status":"OPEN"},
        ]
        mark = {"status":"PARTIAL", "unrealized_pnl":50.0, "rows":[
            {"lot_id":"A1", "strategy_id":"STRAT_A", "status":"MARKED", "unrealized_pnl":50.0},
            {"lot_id":"B1", "strategy_id":"STRAT_B", "status":"NO_MARK"},
        ]}
        out = summarize_strategy_pnl(lots, mark, [
            {"strategy_id":"STRAT_A","realized_pnl_delta":150.0},
            {"strategy_id":"STRAT_B","realized_pnl_delta":-25.0},
        ], expected_realized_pnl=125.0)
        self.assertEqual(out["by_strategy"]["STRAT_A"]["total_pnl"], 200.0)
        self.assertIsNone(out["by_strategy"]["STRAT_B"]["unrealized_pnl"])
        self.assertEqual(out["by_strategy"]["STRAT_B"]["mark_status"], "PENDING")
        self.assertEqual(out["reconciliation"]["status"], "PENDING_MARKS")
        self.assertIsNone(out["reconciliation"]["total_delta"])

    def test_total_strategy_pnl_reconciles_to_manual_book_when_all_marks_exist(self):
        lots = [
            {"lot_id":"A1", "strategy_id":"STRAT_A", "code":"US.QQQ.CALL_A", "side":"LONG",
             "qty":1, "avg_price":5.0, "lot_size":100, "status":"OPEN"},
            {"lot_id":"B1", "strategy_id":"STRAT_B", "code":"US.QQQ.PUT_B", "side":"SHORT",
             "qty":2, "avg_price":3.0, "lot_size":100, "status":"OPEN"},
        ]
        mark = {"status":"OK", "unrealized_pnl":30.0, "rows":[
            {"lot_id":"A1", "strategy_id":"STRAT_A", "status":"MARKED", "unrealized_pnl":50.0},
            {"lot_id":"B1", "strategy_id":"STRAT_B", "status":"MARKED", "unrealized_pnl":-20.0},
        ]}
        trades = [
            {"strategy_id":"STRAT_A","realized_pnl_delta":200.0},
            {"strategy_id":"STRAT_B","realized_pnl_delta":-50.0},
        ]
        out = summarize_strategy_pnl(lots, mark, trades, expected_realized_pnl=150.0)
        self.assertEqual(out["reconciliation"]["status"], "RECONCILED")
        self.assertAlmostEqual(out["reconciliation"]["realized_delta"], 0.0)
        self.assertAlmostEqual(out["reconciliation"]["unrealized_delta"], 0.0)
        self.assertAlmostEqual(out["reconciliation"]["total_delta"], 0.0)
        self.assertEqual(sum(x["total_pnl"] for x in out["by_strategy"].values()), 180.0)

    def test_ledger_realized_mismatch_is_not_passed(self):
        out = summarize_strategy_pnl([], {"status":"EMPTY", "rows":[]}, [
            {"strategy_id":"STRAT_A","realized_pnl_delta":100.0}
        ], expected_realized_pnl=99.0)
        self.assertEqual(out["reconciliation"]["status"], "CHECK_REQUIRED")
        self.assertAlmostEqual(out["reconciliation"]["realized_delta"], 1.0)


if __name__ == "__main__":
    unittest.main()
