import datetime as dt
import unittest

from cashflow_aware_qqq_spy import (
    FlowEvent,
    MonthlyPrice,
    HORIZON_MONTHS,
    fixed_withdrawal_schedule,
    replay_window,
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
            result["terminal_nav_usd"], 1_000.0 * (1.01 ** HORIZON_MONTHS), places=5
        )
        self.assertEqual(result["investor_xirr_status"], "OK")
        elapsed_years = (points[-1].date - points[0].date).days / 365.25
        expected = (prices[-1] / prices[0]) ** (1.0 / elapsed_years) - 1.0
        self.assertAlmostEqual(result["investor_xirr"], expected, places=6)

    def test_fixed_withdrawal_is_separate_from_ending_nav(self):
        prices = [100.0, 110.0, 121.0] + [121.0] * (HORIZON_MONTHS - 2)
        points = points_from_prices(prices)
        schedule = fixed_withdrawal_schedule(100.0)
        result = replay_window(points, 0, "QQQ", schedule, initial_capital_usd=1_000.0)
        self.assertAlmostEqual(result["actual_withdrawals_usd"], 12_000.0, places=6)
        self.assertAlmostEqual(result["terminal_nav_usd"], 1_000.0, places=6)
        self.assertAlmostEqual(
            result["nominal_net_result_vs_initial_capital_usd"], 12_000.0, places=6
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
