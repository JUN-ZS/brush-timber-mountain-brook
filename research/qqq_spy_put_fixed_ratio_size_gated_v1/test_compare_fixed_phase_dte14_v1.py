#!/usr/bin/env python3
from __future__ import annotations
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import compare_fixed_phase_dte14_v1 as compare
import audit_fixed_phase_schedule_v1 as schedule_audit


class Dte14ComparisonTests(unittest.TestCase):
    def test_performance_pair_is_keyed_by_phase_window_policy(self):
        base = {"phase": 0, "window": "5Y", "policy": "HOLD_20_SESSIONS",
                "opened": 250, "resolved": 245, "unresolved": 5,
                "win_rate_pct": 80.0, "mean_net_pnl_usd": 300.0,
                "median_net_pnl_usd": 250.0, "total_resolved_net_pnl_usd": 73500.0,
                "annualized_resolved_net_pnl_usd": 14700.0, "worst_resolved_trade_usd": -5000.0,
                "profit_factor": 1.3, "stress_annualized_net_pnl_usd": 12500.0,
                "peak_concurrent_cohorts": 7, "peak_short_assignment_obligation_usd": 900000.0}
        test = dict(base, opened=250, resolved=240, unresolved=10, win_rate_pct=75.0,
                    mean_net_pnl_usd=200.0, total_resolved_net_pnl_usd=48000.0,
                    annualized_resolved_net_pnl_usd=9600.0, worst_resolved_trade_usd=-7000.0,
                    peak_concurrent_cohorts=5, peak_short_assignment_obligation_usd=650000.0)
        result = compare.join_performance([base], [test])
        self.assertEqual(len(result), 1)
        row = result[0]
        self.assertEqual(row["delta_dte14_minus_dte45_win_rate_pct"], -5.0)
        self.assertEqual(row["delta_dte14_minus_dte45_mean_net_pnl_usd"], -100.0)
        self.assertEqual(row["delta_dte14_minus_dte45_peak_short_assignment_obligation_usd"], -250000.0)

    def test_missing_paired_case_is_rejected(self):
        row = {"phase": 0, "window": "5Y", "policy": "HOLD_20_SESSIONS"}
        with self.assertRaisesRegex(ValueError, "do not reconcile"):
            compare.join_performance([row], [])

    def test_phase_report_displays_actual_dte_selection(self):
        report = schedule_audit.make_report([], [], [], {
            "dte_min": 7, "dte_max": 21, "dte_target": 14, "target_abs_delta": 0.25,
        })
        self.assertIn("DTE 7–21 targeting 14", report)
        self.assertIn("target absolute Delta 0.25", report)
        self.assertNotIn("DTE 30–60 targeting 45", report)

    def test_otm_delta_is_points_not_relative_percent(self):
        a = {"phase": "1", "leg": "QQQ", "reference_time": "entry",
             "n": "100", "otm_n": "99", "atm_n": "0", "itm_n": "1", "non_otm_pct": "1.0",
             "mean_signed_otm_pct": "5.0", "median_signed_otm_pct": "4.5",
             "min_signed_otm_pct": "-0.2", "max_signed_otm_pct": "10.0",
             "mean_otm_pct_when_otm": "5.1", "median_otm_pct_when_otm": "4.6"}
        b = dict(a, mean_signed_otm_pct="3.0", median_signed_otm_pct="2.5", non_otm_pct="3.0")
        row = compare.join_otm([a], [b])[0]
        self.assertAlmostEqual(row["delta_dte14_minus_dte45_median_signed_otm_pct"], -2.0)
        self.assertEqual(row["dte14_itm_n"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
