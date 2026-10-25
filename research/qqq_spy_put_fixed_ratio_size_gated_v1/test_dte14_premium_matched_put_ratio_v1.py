#!/usr/bin/env python3
"""Deterministic tests for the premium-matched DTE14 option selector."""
from __future__ import annotations
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qqq_spy_put_premium_matched_phase_v1 as eng


def put(symbol: str, strike: float, delta: float, bid: float, ask: float,
        *, day: str = "2026-10-23", expiry: str = "2026-11-06",
        bid_size: int = 10, ask_size: int = 10, oi: int = 1000) -> dict:
    ident = f"{symbol}261106P{int(round(strike*1000)):08d}"
    return {
        "contract_id": ident, "symbol": symbol, "expiration": expiry,
        "strike": strike, "type": "put", "bid": bid, "ask": ask,
        "bid_size": bid_size, "ask_size": ask_size, "volume": 10,
        "open_interest": oi, "date": day, "implied_volatility": 0.2,
        "delta": delta,
    }


class PremiumMatchedSelectorTests(unittest.TestCase):
    def test_qqq_put_ask_matches_six_times_spy_put_bid(self):
        day = "2026-10-23"
        qqq = [
            put("QQQ", 710, -0.40, 25.50, 25.80),
            put("QQQ", 715, -0.50, 26.20, 26.34),
            put("QQQ", 720, -0.60, 26.70, 26.80),
            put("QQQ", 730, -0.70, 26.28, 26.34),
        ]
        spy = [
            put("SPY", 740, -0.21, 3.80, 3.90),
            put("SPY", 745, -0.25, 4.39, 4.46),
            put("SPY", 750, -0.30, 4.90, 4.98),
        ]
        result = eng.choose_pair_by_premium(
            qqq, spy, day, 706.36, 760.19,
            target_delta=0.25, dte_min=7, dte_max=21,
            dte_target=14, premium_match_short_qty=6,
            qqq_target_abs_delta=0.50, qqq_delta_tolerance=0.10,
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["qqq_strike"], 715)
        self.assertEqual(result["spy_strike"], 745)
        self.assertAlmostEqual(result["qqq_target_ask_signal"], 26.34, places=6)
        self.assertAlmostEqual(result["qqq_signal_ask"], 26.34, places=6)
        self.assertAlmostEqual(result["qqq_premium_match_error_signal"], 0.0, places=6)
        self.assertAlmostEqual(result["qqq_abs_delta"], 0.50, places=6)
        self.assertEqual(result["qqq_delta_band_low"], 0.40)
        self.assertEqual(result["qqq_delta_band_high"], 0.60)
        self.assertAlmostEqual(result["spy_abs_delta"], 0.25, places=6)
        self.assertEqual(result["expiry"], "2026-11-06")
        self.assertEqual(result["signal_dte"], 14)


    def test_no_near_atm_candidate_does_not_fall_back_to_deep_itm(self):
        qqq = [put("QQQ", 730, -0.70, 26.28, 26.34), put("QQQ", 735, -0.80, 31.10, 31.25)]
        spy = [put("SPY", 745, -0.25, 4.39, 4.46)]
        result = eng.choose_pair_by_premium(
            qqq, spy, "2026-10-23", 706.36, 760.19, target_delta=0.25,
            dte_min=7, dte_max=21, dte_target=14, premium_match_short_qty=6,
            qqq_target_abs_delta=0.50, qqq_delta_tolerance=0.10,
        )
        self.assertIsNone(result)

    def test_intrinsic_extrinsic_residual_decomposition_is_exact(self):
        ep = {"qqq_strike":710.0,"qqq_spot_entry":706.0,"qqq_entry_ask":8.0,"long_qqq_qty":1}
        result = eng.qqq_value_decomposition(ep,12.0,701.0,{"delta":-0.8})
        self.assertAlmostEqual(result["qqq_intrinsic_pnl_usd"],500.0)
        self.assertAlmostEqual(result["qqq_extrinsic_change_proxy_usd"],-100.0)
        self.assertAlmostEqual(result["qqq_intrinsic_pnl_usd"]+result["qqq_extrinsic_change_proxy_usd"],400.0)
        self.assertAlmostEqual(result["qqq_decomposition_check_usd"],0.0)
        self.assertEqual(result["qqq_moneyness_exit"],"ITM")

    def test_combined_exit_policy_is_frozen(self):
        policies = {p["policy"]: p for p in eng.POLICIES}
        self.assertIn("HOLD_20_OR_DTE_LE_7", policies)
        self.assertEqual(policies["HOLD_20_OR_DTE_LE_7"]["hold_sessions"], 20)
        self.assertEqual(policies["HOLD_20_OR_DTE_LE_7"]["expiry_guard_dte"], 7)

    def test_premium_target_must_be_positive(self):
        with self.assertRaises(ValueError):
            eng.choose_pair_by_premium([], [], "2026-10-23", 706.36, 760.19,
                                       premium_match_short_qty=0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
