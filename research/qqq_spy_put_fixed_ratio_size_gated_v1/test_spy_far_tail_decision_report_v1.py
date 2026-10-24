#!/usr/bin/env python3
import unittest
from build_spy_far_tail_decision_report_v1 import median, money, config_summary, annual_summary, stress_summary


class ReportSummaryTests(unittest.TestCase):
    def test_median_and_currency(self):
        self.assertEqual(median([1, 3]), 2.0)
        self.assertEqual(money(-12.5), "−$12.50")
        self.assertEqual(money(0), "$0.00")

    def test_config_summary_uses_same_pair(self):
        rows = [
            {"joint_resolved_paired_n":"8","paired_coverage_pct_of_base_resolved":"80",
             "paired_baseline_mean_net_usd":"-100","paired_hedged_mean_net_usd":"-120",
             "paired_mean_incremental_hedge_usd":"-20","paired_baseline_win_rate_pct":"60",
             "paired_hedged_win_rate_pct":"55","paired_baseline_worst_trade_usd":"-500",
             "paired_hedged_worst_trade_usd":"-400","baseline_losses_improved_n":"2",
             "baseline_losses_turned_positive_n":"0"},
            {"joint_resolved_paired_n":"10","paired_coverage_pct_of_base_resolved":"90",
             "paired_baseline_mean_net_usd":"-80","paired_hedged_mean_net_usd":"-110",
             "paired_mean_incremental_hedge_usd":"-30","paired_baseline_win_rate_pct":"62",
             "paired_hedged_win_rate_pct":"54","paired_baseline_worst_trade_usd":"-600",
             "paired_hedged_worst_trade_usd":"-350","baseline_losses_improved_n":"4",
             "baseline_losses_turned_positive_n":"1"},
        ]
        out = config_summary(rows)
        self.assertEqual(out["paired_n_min"], 8)
        self.assertEqual(out["paired_n_max"], 10)
        self.assertEqual(out["base_mean_median"], -90)
        self.assertEqual(out["hedged_mean_median"], -115)
        self.assertEqual(out["increment_median"], -25)
        self.assertEqual(out["worst_improvement_median"], 175)

    def test_annual_and_stress_summary(self):
        annual = annual_summary([
            {"paired_n":"10","paired_coverage_pct_of_base_resolved":"80","no_hedge_mean_paired_usd":"-20",
             "hedged_mean_paired_usd":"-30","mean_incremental_hedge_usd":"-10","no_hedge_worst_paired_usd":"-500",
             "hedged_worst_paired_usd":"-400"},
            {"paired_n":"12","paired_coverage_pct_of_base_resolved":"90","no_hedge_mean_paired_usd":"-10",
             "hedged_mean_paired_usd":"-25","mean_incremental_hedge_usd":"-15","no_hedge_worst_paired_usd":"-450",
             "hedged_worst_paired_usd":"-350"},
        ])
        self.assertEqual(annual["increment_median"], -12.5)
        stress = stress_summary([{
            "eligible_entry_cohorts":"100","mean_short_spy_sleeve_net_usd":"-1000",
            "mean_hedged_spy_sleeve_net_usd":"-800","mean_tail_increment_usd":"200",
            "worst_short_spy_sleeve_net_usd":"-2000","worst_hedged_spy_sleeve_net_usd":"-1500",
            "fraction_hedge_improves_short_sleeve_pct":"90"}])
        self.assertEqual(stress["increment_median"], 200)
        self.assertEqual(stress["improved_pct_median"], 90)


if __name__ == "__main__":
    unittest.main(verbosity=2)
