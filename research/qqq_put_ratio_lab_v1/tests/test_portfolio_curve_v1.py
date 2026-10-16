from __future__ import annotations
import sys
import unittest
from pathlib import Path

LAB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB))
import build_portfolio_curve as curve


class SerialPortfolioCurveTests(unittest.TestCase):
    def test_realized_pnl_accumulates_across_sequential_episodes(self):
        sessions = [f"2024-01-0{i}" for i in range(1, 7)]
        results = [
            {
                "trade_id": 1, "entry_date": "2024-01-02", "final_pnl_usd": -500.0,
                "daily": [
                    {"date":"2024-01-02","pnl_after_action_usd":-100.0},
                    {"date":"2024-01-03","pnl_after_action_usd":-500.0},
                ],
            },
            {
                "trade_id": 2, "entry_date": "2024-01-05", "final_pnl_usd": 200.0,
                "daily": [
                    {"date":"2024-01-05","pnl_after_action_usd":100.0},
                    {"date":"2024-01-06","pnl_after_action_usd":200.0},
                ],
            },
        ]
        self.assertEqual(curve.combine_episode_daily(sessions, results), [0.0, -100.0, -500.0, -500.0, -400.0, -300.0])

    def test_missing_mark_is_null_and_unresolved_blocks_future_equity(self):
        sessions = [f"2024-01-0{i}" for i in range(1, 6)]
        results = [{
            "trade_id": 1, "entry_date": "2024-01-02", "final_pnl_usd": None,
            "daily": [
                {"date":"2024-01-02","pnl_after_action_usd":-10.0},
                {"date":"2024-01-03","pnl_after_action_usd":None},
            ],
        }]
        result = curve.combine_episode_daily(sessions, results)
        self.assertEqual(result, [0.0, -10.0, None, None, None])

    def test_overlapping_episodes_are_rejected(self):
        sessions = [f"2024-01-0{i}" for i in range(1, 6)]
        results = [
            {"trade_id":1,"entry_date":"2024-01-02","final_pnl_usd":10,"daily":[{"date":"2024-01-02","pnl_after_action_usd":10},{"date":"2024-01-03","pnl_after_action_usd":10}]},
            {"trade_id":2,"entry_date":"2024-01-03","final_pnl_usd":20,"daily":[{"date":"2024-01-03","pnl_after_action_usd":20},{"date":"2024-01-04","pnl_after_action_usd":20}]},
        ]
        with self.assertRaises(ValueError):
            curve.combine_episode_daily(sessions, results)

    def test_drawdown_and_threshold_rates_are_measured_from_nav_curve(self):
        sessions = [f"2024-01-0{i}" for i in range(1, 7)]
        pnl = [0.0, -100.0, -500.0, -500.0, -300.0, 100.0]
        m = curve.curve_metrics(sessions, pnl, 80000.0)
        self.assertEqual(m["max_drawdown_usd_peak_to_trough"], 500.0)
        self.assertLess(m["max_drawdown_pct_of_prior_equity_peak"], 0.0)
        self.assertEqual(m["drawdown_levels"][0]["level_pct"], 3)
        self.assertEqual(m["drawdown_levels"][-1]["level_pct"], 30)
        self.assertEqual(m["known_marks"], 6)
        self.assertEqual(m["missing_marks_not_filled"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
