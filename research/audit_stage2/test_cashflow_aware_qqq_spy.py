import datetime as dt
import unittest

from cashflow_aware_qqq_spy import (
    FlowEvent,
    MonthlyPrice,
    HORIZON_MONTHS,
    fixed_withdrawal_schedule,
    replay_window,
    run_research,
    summarize_capital_floor_scenarios,
    solve_xirr,
)


def points_from_prices(qqq_prices, spy_prices=None, start=dt.date(2020, 1, 31)):
    spy_prices = spy_prices if spy_prices is not None else qqq_prices
    dates = []
    year, month = start.year, start.month
    for index in range(len(qqq_prices)):
        if index == 0:
            date = start
        else:
            month += 1
            if month == 13:
                year += 1
                month = 1
            date = dt.date(year, month, min(start.day, 28))
        dates.append(date)
    return [
        MonthlyPrice(date, float(qqq), float(spy))
        for date, qqq, spy in zip(dates, qqq_prices, spy_prices)
    ]


def flat_prices(first=100.0, count=HORIZON_MONTHS + 1):
    return [first] * count


class CashflowAwareReplayTests(unittest.TestCase):
    def test_no_withdrawal_xirr_matches_underlying_price_return(self):
        prices = [100.0 * (1.01 ** month) for month in range(HORIZON_MONTHS + 1)]
        points = points_from_prices(prices)
        result = replay_window(points, 0, "QQQ", {}, initial_capital_usd=1_000.0)
        self.assertAlmostEqual(
            result["terminal_nav_usd"], 1_000.0 * (1.01 ** HORIZON_MONTHS), places=2
        )
        self.assertEqual(result["investor_xirr_status"], "OK")
        elapsed_years = (points[-1].date - points[0].date).days / 365.25
        expected = (prices[-1] / prices[0]) ** (1.0 / elapsed_years) - 1.0
        self.assertAlmostEqual(result["investor_xirr"], expected, places=6)

    def test_fixed_withdrawal_is_separate_from_ending_nav(self):
        prices = [100.0, 110.0, 121.0] + [121.0] * (HORIZON_MONTHS - 2)
        points = points_from_prices(prices)
        schedule = {
            1: [FlowEvent(1, "withdrawal", 100.0)],
            2: [FlowEvent(2, "withdrawal", 100.0)],
        }
        result = replay_window(points, 0, "QQQ", schedule, initial_capital_usd=1_000.0)
        self.assertAlmostEqual(result["actual_withdrawals_usd"], 200.0, places=6)
        self.assertAlmostEqual(result["terminal_nav_usd"], 1_000.0, places=6)
        self.assertAlmostEqual(
            result["nominal_net_result_vs_initial_capital_usd"], 200.0, places=6
        )
        self.assertAlmostEqual(result["withdrawal_shortfall_usd"], 0.0, places=6)
        self.assertEqual(result["investor_xirr_status"], "OK")

    def test_shortfall_is_not_silently_filled_with_negative_nav(self):
        prices = [100.0, 50.0, 60.0] + [60.0] * (HORIZON_MONTHS - 2)
        points = points_from_prices(prices)
        schedule = {
            1: [FlowEvent(1, "withdrawal", 1_000.0, "overdraw after crash")],
            2: [FlowEvent(2, "deposit", 500.0, "replenish later")],
        }
        result = replay_window(points, 0, "QQQ", schedule, initial_capital_usd=1_000.0)
        self.assertAlmostEqual(result["actual_withdrawals_usd"], 500.0, places=6)
        self.assertAlmostEqual(result["withdrawal_shortfall_usd"], 500.0, places=6)
        self.assertAlmostEqual(result["additional_deposits_usd"], 500.0, places=6)
        self.assertAlmostEqual(result["terminal_nav_usd"], 500.0, places=6)
        self.assertTrue(result["ever_depleted_at_month_end"])
        self.assertEqual(result["first_depletion_month_index"], 1)

    def test_same_month_events_follow_input_order(self):
        points = points_from_prices(flat_prices())
        schedule = {
            1: [
                FlowEvent(1, "deposit", 500.0, "deposit first"),
                FlowEvent(1, "withdrawal", 1_200.0, "withdraw second"),
            ]
        }
        result = replay_window(points, 0, "QQQ", schedule, initial_capital_usd=1_000.0)
        self.assertAlmostEqual(result["additional_deposits_usd"], 500.0, places=6)
        self.assertAlmostEqual(result["actual_withdrawals_usd"], 1_200.0, places=6)
        self.assertAlmostEqual(result["terminal_nav_usd"], 300.0, places=6)
        self.assertAlmostEqual(result["withdrawal_shortfall_usd"], 0.0, places=6)

    def test_daily_drawdown_keeps_intramonth_crash_that_monthly_closes_miss(self):
        prices = flat_prices()
        points = points_from_prices(prices)
        feb_date = points[1].date
        points[1] = MonthlyPrice(
            feb_date,
            100.0,
            100.0,
            (
                (dt.date(feb_date.year, feb_date.month, 3), 100.0, 100.0),
                (dt.date(feb_date.year, feb_date.month, 12), 50.0, 50.0),
                (feb_date, 100.0, 100.0),
            ),
        )
        result = replay_window(points, 0, "QQQ", {}, initial_capital_usd=1_000.0)
        self.assertAlmostEqual(result["underlying_price_max_drawdown"], -0.5, places=6)

    def test_nominal_maturity_floor_survives_a_growth_sleeve_crash(self):
        prices = [100.0] * HORIZON_MONTHS + [1.0]
        spy_prices = [100.0] * HORIZON_MONTHS + [50.0]
        points = points_from_prices(prices, spy_prices)
        summaries, rows = summarize_capital_floor_scenarios(
            points, floor_face_usd=100_000.0, floor_cost_usd=60_000.0
        )
        by_name = {row["scenario"]: row for row in summaries}
        qqq = by_name["FLOOR_PLUS_QQQ"]
        self.assertEqual(qqq["windows_floor_not_met_by_model_before_tax_costs"], 0)
        self.assertAlmostEqual(qqq["growth_sleeve_initial_capital_usd"], 40_000.0, places=6)
        self.assertAlmostEqual(qqq["worst_terminal_nav_usd"], 100_400.0, places=2)
        self.assertTrue(all(row["principal_floor_met_at_maturity_before_tax_costs"] for row in rows))

    def test_floor_withdrawal_can_be_delayed_then_step_up_year_by_year(self):
        points = points_from_prices([100.0] * (HORIZON_MONTHS + 1))
        schedule = {
            13: [FlowEvent(13, "withdrawal", 1_000.0, "after first full year")],
            25: [FlowEvent(25, "withdrawal", 1_250.0, "step up year 3")],
            37: [FlowEvent(37, "withdrawal", 1_500.0, "step up year 4")],
        }
        summaries, rows = summarize_capital_floor_scenarios(
            points,
            floor_face_usd=100_000.0,
            floor_cost_usd=60_000.0,
            custom_schedule=schedule,
        )
        qqq_row = next(
            row for row in rows
            if row["scenario"] == "FLOOR_PLUS_QQQ" and row["window_index"] == 0
        )
        self.assertAlmostEqual(qqq_row["requested_withdrawals_usd"], 3_750.0, places=6)
        self.assertAlmostEqual(qqq_row["actual_withdrawals_usd"], 3_750.0, places=6)
        self.assertAlmostEqual(qqq_row["withdrawal_shortfall_usd"], 0.0, places=6)
        self.assertAlmostEqual(qqq_row["growth_sleeve_terminal_usd"], 36_250.0, places=6)
        self.assertAlmostEqual(qqq_row["protected_maturity_payment_usd"], 100_000.0, places=6)
        self.assertFalse(qqq_row["floor_payment_used_for_spending"])
        self.assertIsNone(qqq_row["terminal_cagr"])
        self.assertEqual(qqq_row["investor_xirr_status"], "OK")

    def test_floor_is_never_used_when_withdrawal_exceeds_growth_sleeve(self):
        points = points_from_prices([100.0] * (HORIZON_MONTHS + 1))
        schedule = {13: [FlowEvent(13, "withdrawal", 50_000.0, "exceeds growth sleeve")]}
        _, rows = summarize_capital_floor_scenarios(
            points,
            floor_face_usd=100_000.0,
            floor_cost_usd=60_000.0,
            custom_schedule=schedule,
        )
        qqq_row = next(
            row for row in rows
            if row["scenario"] == "FLOOR_PLUS_QQQ" and row["window_index"] == 0
        )
        self.assertAlmostEqual(qqq_row["requested_withdrawals_usd"], 50_000.0, places=6)
        self.assertAlmostEqual(qqq_row["actual_withdrawals_usd"], 40_000.0, places=6)
        self.assertAlmostEqual(qqq_row["withdrawal_shortfall_usd"], 10_000.0, places=6)
        self.assertAlmostEqual(qqq_row["growth_sleeve_terminal_usd"], 0.0, places=6)
        self.assertAlmostEqual(qqq_row["terminal_nav_usd"], 100_000.0, places=6)
        self.assertFalse(qqq_row["floor_payment_used_for_spending"])

    def test_no_withdrawals_is_default_and_withdrawal_grid_is_opt_in(self):
        points = points_from_prices([100.0] * (HORIZON_MONTHS + 1))
        default_report, default_rows = run_research(points)
        self.assertEqual(len(default_report["scenario_summaries"]), 2)
        self.assertEqual(len(default_report["capital_floor_summaries"]), 4)
        self.assertFalse(default_report["method"]["withdrawal_grid_enabled"])
        self.assertEqual(
            {row["scenario"] for row in default_report["scenario_summaries"]},
            {"no_withdrawals"},
        )
        grid_report, _ = run_research(points, include_withdrawal_grid=True)
        self.assertEqual(len(grid_report["scenario_summaries"]), 12)
        self.assertTrue(grid_report["method"]["withdrawal_grid_enabled"])

    def test_xirr_does_not_invent_a_return_for_one_sign(self):
        flows = [
            (dt.date(2020, 1, 1), -1_000.0),
            (dt.date(2021, 1, 1), -100.0),
        ]
        value, status = solve_xirr(flows)
        self.assertIsNone(value)
        self.assertEqual(status, "NO_ROOT")

    def test_replay_requires_a_full_120_month_window(self):
        points = points_from_prices(flat_prices())
        result = replay_window(points, 0, "SPY", {}, initial_capital_usd=100_000.0)
        self.assertAlmostEqual(result["terminal_nav_usd"], 100_000.0, places=6)


if __name__ == "__main__":
    unittest.main()
