import datetime as dt
import unittest

from cashflow_aware_qqq_spy import FlowEvent
from stock_bond_glidepath_backtest import (
    BOND_TICKERS,
    TARGET_CONVERSIONS,
    TIMING_RULES,
    _target_bond_weight,
    summarize_annual_group,
    replay_one_window,
    summarize_group,
)


def market_fixture(months=121):
    dates = []
    year, month = 2020, 1
    for index in range(months):
        dates.append(dt.date(year, month, 28))
        month += 1
        if month == 13:
            year += 1
            month = 1
    prices = {}
    for ticker in ("QQQ", "SPY", "AGG", "SHY", "IEF", "TLT"):
        if ticker in ("QQQ", "SPY"):
            values = [100.0 * (1.01 ** i) for i in range(months)]
        else:
            values = [100.0] * months
        prices[ticker] = values
    return dates, prices, list(range(months))


class StockBondGlidepathTests(unittest.TestCase):
    def test_targets_are_30_to_100_and_weight_steps_are_linear(self):
        self.assertEqual(TARGET_CONVERSIONS, (30, 40, 50, 60, 70, 80, 90, 100))
        self.assertEqual(TIMING_RULES, ("front_fast", "front_loaded", "linear", "mid_loaded", "back_loaded", "back_late"))
        self.assertAlmostEqual(_target_bond_weight(60, 0), 0.0)
        self.assertAlmostEqual(_target_bond_weight(60, 12), 0.06)
        self.assertAlmostEqual(_target_bond_weight(60, 60), 0.30)
        self.assertAlmostEqual(_target_bond_weight(60, 120), 0.60)
        self.assertAlmostEqual(_target_bond_weight(100, 120), 1.0)
        self.assertAlmostEqual(_target_bond_weight(60, 24, "front_fast"), 0.30)
        self.assertAlmostEqual(_target_bond_weight(60, 120, "front_fast"), 0.60)
        self.assertAlmostEqual(_target_bond_weight(60, 36, "front_loaded"), 0.30)
        self.assertAlmostEqual(_target_bond_weight(60, 120, "front_loaded"), 0.60)
        self.assertAlmostEqual(_target_bond_weight(60, 60, "mid_loaded"), 0.30)
        self.assertAlmostEqual(_target_bond_weight(60, 120, "mid_loaded"), 0.60)
        self.assertAlmostEqual(_target_bond_weight(60, 60, "back_loaded"), 0.0)
        self.assertAlmostEqual(_target_bond_weight(60, 72, "back_loaded"), 0.12)
        self.assertAlmostEqual(_target_bond_weight(60, 84, "back_late"), 0.0)
        self.assertAlmostEqual(_target_bond_weight(60, 96, "back_late"), 0.20)
        for timing in TIMING_RULES:
            ws = [_target_bond_weight(60, month, timing) for month in range(0, 121, 12)]
            self.assertAlmostEqual(ws[0], 0.0)
            self.assertAlmostEqual(ws[-1], 0.60)
            self.assertTrue(all(0 <= a <= b <= 0.60 for a,b in zip(ws,ws[1:])))
        self.assertAlmostEqual(_target_bond_weight(60, 120, "back_loaded"), 0.60)

    def test_one_hundred_percent_target_ends_all_bond_and_no_market_loss(self):
        dates, prices, monthly = market_fixture()
        row = replay_one_window(dates, prices, monthly, 0, "IEF", 100)
        self.assertAlmostEqual(row["ending_stock_weight"], 0.0)
        self.assertAlmostEqual(row["ending_bond_weight"], 1.0)
        self.assertGreater(row["terminal_nav_usd"], 0)
        self.assertAlmostEqual(row["daily_max_drawdown"], 0.0, places=6)
        self.assertEqual(row["withdrawal_shortfall_usd"], 0.0)
        self.assertEqual(row["investor_xirr_status"], "OK")

    def test_conversion_timing_changes_returns_but_not_year_ten_target(self):
        dates, prices, monthly = market_fixture()
        front = replay_one_window(dates, prices, monthly, 0, "IEF", 60, timing_rule="front_loaded")
        linear = replay_one_window(dates, prices, monthly, 0, "IEF", 60, timing_rule="linear")
        back = replay_one_window(dates, prices, monthly, 0, "IEF", 60, timing_rule="back_loaded")
        for row in (front, linear, back):
            self.assertAlmostEqual(row["ending_stock_weight"], 0.40)
            self.assertAlmostEqual(row["ending_bond_weight"], 0.60)
        # Fixture has rising stocks and flat bonds; moving out of stocks earlier reduces total return.
        self.assertGreater(back["time_weighted_cagr"], linear["time_weighted_cagr"])
        self.assertGreater(linear["time_weighted_cagr"], front["time_weighted_cagr"])

    def test_custom_withdrawal_is_recorded_and_never_pushes_nav_negative(self):
        dates, prices, monthly = market_fixture()
        schedule = {
            13: [FlowEvent(13, "withdrawal", 1000.0, "after first year")],
            97: [FlowEvent(97, "deposit", 5000.0, "top-up")],
            108: [FlowEvent(108, "withdrawal", 1800.0, "irregular")],
        }
        baseline = replay_one_window(dates, prices, monthly, 0, "AGG", 60)
        row = replay_one_window(dates, prices, monthly, 0, "AGG", 60, schedule)
        self.assertEqual(row["requested_withdrawals_usd"], 2800.0)
        self.assertEqual(row["actual_withdrawals_usd"], 2800.0)
        self.assertEqual(row["additional_deposits_usd"], 5000.0)
        self.assertEqual(row["withdrawal_shortfall_usd"], 0.0)
        self.assertGreaterEqual(row["terminal_nav_usd"], 0.0)
        # Cash flows must change investor terminal wealth, not time-weighted strategy returns,
        # because they are added/removed pro rata instead of changing rebalance timing.
        self.assertAlmostEqual(row["time_weighted_cagr"], baseline["time_weighted_cagr"], places=12)

    def test_scenario_summary_reports_downside_and_withdrawals(self):
        rows = []
        for bond in BOND_TICKERS:
            row = {
                "bond_proxy": bond,
                "target_bond_conversion_pct_at_year10": 30,
                "timing_rule": "linear",
                "cashflow_mode": "no_withdrawals",
                "terminal_nav_usd": 105000.0,
                "time_weighted_cagr": 0.005,
                "daily_max_drawdown": -0.2,
                "investor_xirr": 0.005,
                "actual_withdrawals_usd": 0.0,
                "withdrawal_shortfall_usd": 0.0,
            }
            rows.append(row)
        summary = summarize_group(rows)
        self.assertEqual(summary["rolling_windows"], len(BOND_TICKERS))
        self.assertEqual(summary["windows_below_initial_capital_at_year10"], 0)
        self.assertEqual(summary["windows_with_withdrawal_shortfall"], 0)
        self.assertAlmostEqual(summary["median_daily_max_drawdown"], -0.2)

    def test_each_replay_exposes_selected_year_marks_with_nav_and_weights(self):
        dates, prices, monthly = market_fixture()
        row = replay_one_window(dates, prices, monthly, 0, "AGG", 60, timing_rule="linear")
        self.assertEqual(len(row["yearly_marks"]), 11)
        self.assertEqual(row["yearly_marks"][0]["nav_usd"], 100000.0)
        self.assertAlmostEqual(row["yearly_marks"][0]["target_bond_weight"], 0.0)
        self.assertAlmostEqual(row["yearly_marks"][1]["target_bond_weight"], 0.06)
        self.assertAlmostEqual(row["yearly_marks"][9]["target_bond_weight"], 0.54)
        self.assertAlmostEqual(row["yearly_marks"][10]["target_bond_weight"], 0.60)
        self.assertNotEqual(row["yearly_marks"][1]["nav_usd"], row["yearly_marks"][10]["nav_usd"])

    def test_annual_summary_uses_requested_year_not_terminal_only(self):
        base={"bond_proxy":"AGG","target_bond_conversion_pct_at_year10":60,"timing_rule":"linear","cashflow_mode":"no_withdrawals"}
        rows=[]
        for nav,dd in ((90000.0,-0.25),(120000.0,-0.05)):
            marks=[
                {"year":0,"nav_usd":100000.0,"performance_index":100000.0,"year_twr":None,"cumulative_twr_cagr":None,"max_drawdown_to_date":0.0,"actual_withdrawals_usd":0.0,"withdrawal_shortfall_usd":0.0,"additional_deposits_usd":0.0,"target_bond_weight":0.0,"target_stock_weight":1.0},
                {"year":1,"nav_usd":nav,"performance_index":nav,"year_twr":0.02,"cumulative_twr_cagr":0.02,"max_drawdown_to_date":dd,"actual_withdrawals_usd":0.0,"withdrawal_shortfall_usd":0.0,"additional_deposits_usd":0.0,"target_bond_weight":0.06,"target_stock_weight":0.94},
            ]
            rows.append(dict(base,yearly_marks=marks))
        summary=summarize_annual_group(rows,1)
        self.assertEqual(summary["median_nav_usd"],105000.0)
        self.assertEqual(summary["windows_below_initial_capital"],1)
        self.assertEqual(summary["rolling_windows"],2)


if __name__ == "__main__":
    unittest.main()
