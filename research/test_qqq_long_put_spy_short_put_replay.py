import unittest

import numpy as np
import pandas as pd

from qqq_long_put_spy_short_put_replay import (
    _basic_stats, _day, _exit_mark, _regime_for, _select, leg_pnl_per_contract, package_pnl,
)


class PairedPutReplayTests(unittest.TestCase):
    def test_long_put_uses_ask_to_enter_and_bid_to_exit(self):
        long_pnl, short_pnl = leg_pnl_per_contract(4.00, 3.00, 2.00, 4.00)
        self.assertEqual(long_pnl, -100.0)
        self.assertEqual(short_pnl, -200.0)

    def test_package_costs_scale_with_contract_count(self):
        pnl = package_pnl(0.0, 0.0, 4, 5, commission_per_side=0.65, slippage_per_share_per_side=0.0)
        self.assertAlmostEqual(pnl, -11.7, places=8)

    def test_stats_include_breakeven_in_denominator(self):
        stats = _basic_stats(np.asarray([100.0, -50.0, 0.0]))
        self.assertEqual((stats["n"], stats["wins"], stats["losses"], stats["breakeven"]), (3, 1, 1, 1))
        self.assertAlmostEqual(stats["win_rate_pct"], 100.0 / 3.0, places=8)

    def test_delta_match_selects_candidate_closest_to_target(self):
        candidates = pd.DataFrame([
            {"strike": 95.0, "strike_key": 95000, "dte": 30, "delta": -0.24, "bid": 1.80, "ask": 1.90},
            {"strike": 90.0, "strike_key": 90000, "dte": 30, "delta": -0.12, "bid": 0.70, "ask": 0.80},
        ]).set_index("strike_key", drop=False)
        selected = _select(candidates, 100.0, "DELTA_MATCHED", 30, 0.25, 0.05)
        self.assertEqual(int(selected["strike_key"]), 95000)

    def test_premium_match_selects_closest_bid_to_reference(self):
        candidates = pd.DataFrame([
            {"strike": 95.0, "strike_key": 95000, "dte": 30, "delta": -0.24, "bid": 1.80, "ask": 1.90},
            {"strike": 90.0, "strike_key": 90000, "dte": 30, "delta": -0.12, "bid": 0.70, "ask": 0.80},
        ])
        selected = _select(candidates, 100.0, "PREMIUM_MATCHED", 30, 0.25, 0.05, premium_reference=0.75)
        self.assertEqual(int(selected["strike_key"]), 90000)

    def test_single_quote_day_is_normalized_to_dataframe(self):
        day = pd.Timestamp("2024-01-02")
        index = pd.MultiIndex.from_tuples(
            [(day, pd.Timestamp("2024-02-01"), 95000)],
            names=["quote_date", "expiration", "strike_key"],
        )
        frame = pd.DataFrame([{
            "quote_date": day, "expiration": pd.Timestamp("2024-02-01"), "strike_key": 95000,
            "strike": 95.0, "dte": 30, "bid": 1.0, "ask": 1.1, "delta": -0.25,
        }], index=index)
        result = _day(frame, day)
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 1)

    def test_expired_put_uses_intrinsic_at_expiration_close(self):
        expiry = pd.Timestamp("2024-01-19")
        exit_date = pd.Timestamp("2024-02-16")
        underlying = {expiry: 90.0, exit_date: 80.0}
        empty_quotes = pd.DataFrame()
        long_mark, long_kind, long_settled = _exit_mark(
            empty_quotes, underlying, exit_date, expiry, 95000, 100.0, is_long=True
        )
        short_mark, short_kind, short_settled = _exit_mark(
            empty_quotes, underlying, exit_date, expiry, 95000, 100.0, is_long=False
        )
        self.assertEqual(long_mark, 10.0)
        self.assertEqual(short_mark, 10.0)
        self.assertEqual(long_kind, "EXPIRY_INTRINSIC")
        self.assertEqual(short_kind, "EXPIRY_INTRINSIC")
        self.assertTrue(long_settled)
        self.assertTrue(short_settled)

    def test_live_missing_exit_quote_is_not_filled_from_underlying(self):
        expiry = pd.Timestamp("2024-02-16")
        exit_date = pd.Timestamp("2024-01-19")
        mark, kind, settled = _exit_mark(
            pd.DataFrame(), {exit_date: 80.0}, exit_date, expiry, 95000, 100.0, is_long=True
        )
        self.assertIsNone(mark)
        self.assertEqual(kind, "MISSING_EXIT_QUOTE")
        self.assertFalse(settled)

    def test_regime_names_track_relative_realized_returns(self):
        self.assertEqual(_regime_for(-0.10, -0.04), "BOTH_DOWN_QQQ_WEAKER")
        self.assertEqual(_regime_for(-0.03, -0.08), "BOTH_DOWN_SPY_WEAKER")
        self.assertEqual(_regime_for(0.02, 0.00), "BOTH_UP")
        self.assertEqual(_regime_for(-0.01, 0.02), "MIXED")


if __name__ == "__main__":
    unittest.main()
