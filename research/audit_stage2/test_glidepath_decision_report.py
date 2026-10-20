import json
import tempfile
import unittest
from pathlib import Path

from glidepath_decision_report import (
    build_decision_summary,
    enhance_report_dir,
    pareto_frontier,
    render_frontier,
)
from stock_bond_glidepath_backtest import BOND_TICKERS, TARGET_CONVERSIONS, TIMING_RULES


def sample_scenarios():
    scenarios = []
    modes = ("no_withdrawals", "delayed_stepup_example", "monthly_withdrawal_500_usd_stress", "monthly_withdrawal_1000_usd_stress")
    timing_risk = {"front_rapid": 0.035, "front_fast": 0.02, "front_loaded": 0.0, "linear": 0.01, "mid_loaded": 0.025, "staggered": 0.015, "back_loaded": 0.07, "back_late": 0.10}
    for mode in modes:
        for bond_index, bond in enumerate(BOND_TICKERS):
            for timing_index, timing in enumerate(TIMING_RULES):
                for target in TARGET_CONVERSIONS:
                    cagr = 0.16 - target * 0.0006 - bond_index * 0.001 + timing_index * 0.0004
                    dd = -(0.12 + target * 0.0008 + timing_risk[timing] + bond_index * 0.002)
                    terminal = 100_000.0 * (1.0 + cagr) ** 10
                    gap = 5 if mode == "monthly_withdrawal_1000_usd_stress" and target >= 60 else 0
                    scenarios.append({
                        "bond_proxy": bond, "target_bond_conversion_pct_at_year10": target,
                        "timing_rule": timing, "cashflow_mode": mode, "rolling_windows": 157,
                        "median_terminal_nav_usd": terminal, "p05_terminal_nav_usd": terminal * 0.55,
                        "p95_terminal_nav_usd": terminal * 1.25, "worst_terminal_nav_usd": terminal * 0.4,
                        "median_time_weighted_cagr": cagr, "p05_time_weighted_cagr": cagr - 0.07,
                        "worst_time_weighted_cagr": cagr - 0.12, "median_daily_max_drawdown": dd,
                        "worst_daily_max_drawdown": min(-0.51, dd - 0.25),
                        "windows_below_initial_capital_at_year10": 12 if target >= 70 else 3,
                        "windows_with_withdrawal_shortfall": gap,
                        "median_actual_withdrawals_usd": 60_000.0 if "500" in mode else 120_000.0 if "1000" in mode else 0.0,
                        "p95_withdrawal_shortfall_usd": 1_000.0 if gap else 0.0,
                        "median_investor_xirr": cagr, "xirr_defined_windows": 157,
                    })
    return scenarios


class GlidepathDecisionReportTests(unittest.TestCase):
    def test_decision_summary_covers_all_targets_and_stresses(self):
        summary = build_decision_summary(sample_scenarios())
        self.assertEqual(summary["no_withdrawal_configurations"], 256)
        self.assertEqual(len(summary["agg_linear_target_scan"]), 8)
        self.assertEqual(len(summary["agg_60_timing_comparison"]), 8)
        self.assertGreater(len(summary["pareto_frontier"]), 0)
        self.assertEqual(summary["withdrawal_stress"]["monthly_withdrawal_1000_usd_stress"]["configurations"], 256)
        self.assertEqual(summary["withdrawal_stress"]["delayed_stepup_example"]["max_windows_with_shortfall"], 0)

    def test_frontier_chart_has_axes_and_non_dominated_points(self):
        noflow = [r for r in sample_scenarios() if r["cashflow_mode"] == "no_withdrawals"]
        frontier = pareto_frontier(noflow)
        svg = render_frontier(noflow)
        self.assertGreater(len(frontier), 0)
        self.assertTrue(svg.startswith("<svg "))
        self.assertIn("歷史回報／回撤取捨前沿", svg)
        self.assertIn("非支配前沿", svg)
        self.assertIn("AGG", svg)

    def test_enhance_report_writes_json_markdown_svg_and_dashboard(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            report = {"scenarios": sample_scenarios()}
            (out / "stock_bond_glidepath_summary.json").write_text(json.dumps(report), encoding="utf-8")
            (out / "index.html").write_text(
                "<html><body><h1>股票逐年轉債券</h1><p class='note'>限制</p>"
                "<section><h2>第10年終值</h2></section></body></html>",
                encoding="utf-8",
            )
            result = enhance_report_dir(out)
            self.assertIn("decision_summary", result)
            self.assertTrue((out / "decision_summary.md").exists())
            self.assertTrue((out / "07_risk_return_frontier.svg").exists())
            html = (out / "index.html").read_text(encoding="utf-8")
            self.assertIn("id='decision-summary'", html)
            self.assertIn("id='risk-return-frontier'", html)
            self.assertGreater(len(html), 10000)


if __name__ == "__main__":
    unittest.main()
