import unittest

import numpy as np

from validate_glidepath_cashflow_ledger import BOND_TICKERS, HORIZON_MONTHS, replay_group, target_bond_weight


class IndependentLedgerReplayTests(unittest.TestCase):
    def test_all_timing_paths_start_equity_only_and_finish_on_target(self):
        timings = ("front_rapid", "front_fast", "front_loaded", "linear", "mid_loaded", "staggered", "back_loaded", "back_late")
        for timing in timings:
            with self.subTest(timing=timing):
                self.assertEqual(target_bond_weight(60, 0, timing), 0.0)
                self.assertAlmostEqual(target_bond_weight(60, 120, timing), 0.60)

    def fixture_prices(self, declining=False):
        n = HORIZON_MONTHS + 1
        if declining:
            qqq = np.asarray([100.0] + [90.0] * (n - 1))
            spy = np.asarray([100.0] + [90.0] * (n - 1))
        else:
            qqq = np.asarray([100.0 * (1.01 ** i) for i in range(n)])
            spy = np.asarray([100.0] * n)
        prices = {ticker: np.asarray([100.0] * n) for ticker in ("QQQ", "SPY", *BOND_TICKERS)}
        prices["QQQ"] = qqq
        prices["SPY"] = spy
        return prices, np.arange(n, dtype=int), np.asarray([0], dtype=int)

    def test_cashflows_reconcile_and_conserve_account_value(self):
        prices, month_indices, starts = self.fixture_prices()
        row = replay_group(
            prices, month_indices, starts, "AGG", 60, "linear",
            {13: [("withdrawal", 1000.0)], 97: [("deposit", 5000.0)], 108: [("withdrawal", 1800.0)]},
        )
        self.assertEqual(float(row["deposits"][0]), 5000.0)
        self.assertEqual(float(row["requested"][0]), 2800.0)
        self.assertEqual(float(row["withdrawals"][0]), 2800.0)
        self.assertEqual(float(row["shortfall"][0]), 0.0)
        self.assertLess(abs(float(row["conservation_error"][0])), 1e-5)
        self.assertEqual(len(row["yearly"]), 11)
        self.assertEqual(float(row["yearly"][0]["nav_usd"][0]), 100000.0)

    def test_unfunded_withdrawal_is_explicit_and_redeposit_restarts_empty_account(self):
        prices, month_indices, starts = self.fixture_prices(declining=True)
        row = replay_group(
            prices, month_indices, starts, "AGG", 60, "linear",
            {1: [("withdrawal", 200000.0)], 3: [("deposit", 5000.0)]},
        )
        self.assertEqual(float(row["requested"][0]), 200000.0)
        self.assertEqual(float(row["withdrawals"][0]), 90000.0)
        self.assertEqual(float(row["shortfall"][0]), 110000.0)
        self.assertEqual(float(row["deposits"][0]), 5000.0)
        self.assertEqual(int(row["first_depletion"][0]), 1)
        self.assertGreaterEqual(float(row["terminal"][0]), 0.0)
        self.assertLess(abs(float(row["conservation_error"][0])), 1e-5)


if __name__ == "__main__":
    unittest.main()
