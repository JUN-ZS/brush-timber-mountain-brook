"""Offline regression tests for the QQQ option price-basis audit."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit_qqq_public_eod_options as audit


class PriceBasisAuditTests(unittest.TestCase):
    def test_strike_targets_scale_with_nominal_spot(self):
        adjusted = audit.model_qqq_quote(162.9786, 82.69)
        raw = audit.model_qqq_quote(169.30, 82.69)
        self.assertLess(adjusted["short_target_strike"], raw["short_target_strike"])
        self.assertLess(adjusted["long_target_strike"], raw["long_target_strike"])
        self.assertAlmostEqual(
            raw["short_target_strike"] / adjusted["short_target_strike"],
            169.30 / 162.9786,
            places=5,
        )

    def test_same_expiry_pair_uses_valid_quotes_and_reports_executable_credit(self):
        day = "2020-03-16"
        rows = []
        for strike, bid, ask, delta in [
            (215.0, 0.50, 0.56, 0.155),
            (220.0, 0.28, 0.34, 0.115),
            (230.0, 0.12, 0.18, 0.075),
            (240.0, 0.05, 0.10, 0.040),
        ]:
            rows.append({
                "type": "call", "date": day, "expiration": "2020-04-17",
                "strike": strike, "bid": bid, "ask": ask, "delta": delta,
                "contract_id": f"QQQTESTC{int(strike*1000):08d}",
                "volume": 10, "open_interest": 100,
            })
        rows.append({
            "type": "call", "date": day, "expiration": "2020-04-17",
            "strike": 214.5, "bid": 0.0, "ask": 0.0, "delta": 0.16,
            "contract_id": "INVALID", "volume": 0, "open_interest": 0,
        })
        geometry = {
            "repo_adjusted_spot": audit.model_qqq_quote(162.9786, 82.69),
            "raw_close_spot": audit.model_qqq_quote(169.30, 82.69),
        }
        matched = audit.nearest_quote_model_pairs(
            rows, day, geometry, 169.30, 162.9786, 82.69
        )
        self.assertEqual(matched["status"], "MATCHED_NEAREST_20_40_DTE_EXPIRY")
        self.assertEqual(matched["selected_expiry"], "2020-04-17")
        for label in geometry:
            pair = matched["model_target_nearest_pairs"][label]
            self.assertIsNotNone(pair)
            self.assertNotEqual(pair["short_contract_id"], "INVALID")
            self.assertAlmostEqual(
                pair["observed_credit_bid_minus_wing_ask"],
                pair["short_bid"] - pair["wing_ask"],
                places=9,
            )
            self.assertGreater(pair["wing_strike"], pair["short_strike"])

    def test_no_same_expiry_quote_is_invented(self):
        result = audit.nearest_quote_model_pairs(
            [], "2020-03-16",
            {"adjusted": audit.model_qqq_quote(162.9786, 82.69)},
            169.30, 162.9786, 82.69,
        )
        self.assertEqual(result["status"], "NO_VALID_STANDARD_GRID_CALLS_WITH_20_40_DTE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
