#!/usr/bin/env python3
"""Unit tests for the episode-level TAIL hedge overlay."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tail_overlay_episode_replay_v1 as tail


class TailOverlayTests(unittest.TestCase):
    def test_tail_pair_requires_exact_entry_and_exit_dates(self):
        prices = {"2020-01-02": 10.0, "2020-01-10": 12.0}
        trades = [
            {"ratio": "1:3", "episode_id": "a", "entry_date": "2020-01-02",
             "exit_date": "2020-01-10", "hold_calendar_days": 8, "base_net_pnl_usd": -100.0},
            {"ratio": "1:3", "episode_id": "b", "entry_date": "2020-01-03",
             "exit_date": "2020-01-10", "hold_calendar_days": 7, "base_net_pnl_usd": 50.0},
        ]
        paired, coverage = tail.pair_tail_returns(trades, prices)
        self.assertEqual(len(paired), 1)
        self.assertAlmostEqual(paired[0]["tail_total_return"], 0.20)
        self.assertEqual(coverage["missing_tail_entry_price"], 1)
        self.assertEqual(coverage["missing_tail_exit_price"], 0)

    def test_tail_hedge_offsets_base_loss_net_of_cost(self):
        paired = [
            {"base_net_pnl_usd": -100.0, "tail_total_return": 0.20, "tail_total_return_pct": 20.0,
             "hold_calendar_days": 8},
            {"base_net_pnl_usd": 100.0, "tail_total_return": -0.10, "tail_total_return_pct": -10.0,
             "hold_calendar_days": 8},
        ]
        result = tail.make_scenario(paired, allocation=500.0, cost_rate=0.001)
        self.assertAlmostEqual(result["tail_overlay"]["gross_total_pnl_usd"], 50.0)
        self.assertAlmostEqual(result["tail_overlay"]["assumed_round_trip_cost_usd"], 1.0)
        self.assertAlmostEqual(result["tail_overlay"]["total_net_pnl_usd"], 49.0)
        self.assertAlmostEqual(result["combined"]["total_net_pnl_usd"], 49.0)
        self.assertEqual(result["base_loss_cohorts"], 1)
        self.assertEqual(result["base_loss_cohorts_with_positive_tail_net_pnl"], 1)
        self.assertAlmostEqual(result["worst_trade_loss_reduction_usd"], 99.5)

    def test_zero_allocation_preserves_base_pnl(self):
        paired = [
            {"base_net_pnl_usd": -123.45, "tail_total_return": 0.7, "tail_total_return_pct": 70.0,
             "hold_calendar_days": 9},
            {"base_net_pnl_usd": 25.0, "tail_total_return": -0.2, "tail_total_return_pct": -20.0,
             "hold_calendar_days": 9},
        ]
        result = tail.make_scenario(paired, allocation=0.0, cost_rate=0.0)
        self.assertAlmostEqual(result["combined"]["total_net_pnl_usd"], -98.45)
        self.assertAlmostEqual(result["combined"]["worst_trade_usd"], -123.45)
        self.assertEqual(result["tail_overlay"]["total_net_pnl_usd"], 0.0)

    def test_csv_hash_changes_when_snapshot_changes(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "data.csv"
            path.write_text("date,adj_close\n2020-01-02,10\n", encoding="utf-8")
            first = tail.sha256_file(path)
            path.write_text("date,adj_close\n2020-01-02,11\n", encoding="utf-8")
            second = tail.sha256_file(path)
            self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main(verbosity=2)
