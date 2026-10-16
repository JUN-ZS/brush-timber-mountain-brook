import importlib.util
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
SPEC = importlib.util.spec_from_file_location(
    "qqq_policy_mae_reversal",
    HERE / "qqq_put_ratio_policy_mae_reversal_v1.py",
)
M = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(M)


def qr(bid, ask, bid_size=20, ask_size=20):
    return {"bid": bid, "ask": ask, "bid_size": bid_size, "ask_size": ask_size}


def sample_trade():
    return {
        "trade_id": "synthetic-exact-pair",
        "entry_date": "2024-01-03",
        "expiry": "2024-01-10",
        "long_id": "QQQ240110P00100000",
        "short_id": "QQQ240110P00090000",
        "long_strike": 100.0,
        "short_strike": 90.0,
        "spot_entry": 105.0,
        "entry_quotes": {
            "long": qr(4.5, 5.0, 10, 12),
            "short": qr(2.0, 2.5, 30, 35),
        },
        "path": [
            {"date": "2024-01-03", "spot": 105, "long": qr(4.5, 5.0), "short": qr(2.0, 2.5)},
            {"date": "2024-01-04", "spot": 104, "long": qr(4.7, 5.1), "short": qr(2.3, 2.7)},
            {"date": "2024-01-05", "spot": 103, "long": qr(4.9, 5.2), "short": qr(2.5, 3.0)},
            {"date": "2024-01-08", "spot": 101, "long": qr(5.2, 5.6), "short": qr(3.0, 3.6)},
            {"date": "2024-01-09", "spot": 100, "long": qr(5.5, 6.0), "short": qr(3.5, 4.0)},
            {"date": "2024-01-10", "spot": 99, "long": qr(6.0, 6.5), "short": qr(4.0, 4.5)},
        ],
    }


class PolicyMaeStrictReversalTests(unittest.TestCase):
    def test_inversion_swaps_exact_same_contracts_strikes_and_quotes(self):
        original = sample_trade()
        inverted = M.invert_same_contract_trade(original)
        self.assertEqual(inverted["long_strike"], 90.0)
        self.assertEqual(inverted["short_strike"], 100.0)
        self.assertEqual(inverted["long_id"], original["short_id"])
        self.assertEqual(inverted["short_id"], original["long_id"])
        self.assertEqual(inverted["entry_quotes"]["long"], original["entry_quotes"]["short"])
        self.assertEqual(inverted["entry_quotes"]["short"], original["entry_quotes"]["long"])
        self.assertEqual(inverted["path"][1]["long"], original["path"][1]["short"])
        self.assertEqual(inverted["path"][1]["short"], original["path"][1]["long"])
        self.assertTrue(inverted["strict_sign_reversal_same_contract_ids"])
        self.assertEqual(M.core.quantities(M.core.SHORT_HEAVY, 5), (1, 5))
        self.assertEqual(M.core.quantities(M.core.LONG_HEAVY, 5), (5, 1))

    def test_forced_delay_blocks_short_close_size_but_not_quote_price(self):
        original = sample_trade()
        delayed, touched = M.apply_delay(original, 2)
        self.assertEqual(touched, 2)
        self.assertEqual(delayed["path"][1]["short"]["ask"], original["path"][1]["short"]["ask"])
        self.assertEqual(delayed["path"][1]["short"]["ask_size"], 0)
        self.assertEqual(delayed["path"][2]["short"]["ask_size"], 0)
        self.assertEqual(delayed["path"][3]["short"]["ask_size"], original["path"][3]["short"]["ask_size"])

    def test_walk_forward_training_excludes_same_day_future_and_unclean_samples(self):
        refs = [
            {"training_eligible": True, "exit_date": "2024-01-02", "trade_id": "prior"},
            {"training_eligible": True, "exit_date": "2024-01-03", "trade_id": "same-day"},
            {"training_eligible": True, "exit_date": "2024-01-04", "trade_id": "future"},
            {"training_eligible": False, "exit_date": "2024-01-01", "trade_id": "unclean"},
        ]
        eligible = M.clean_prior(refs, "2024-01-03")
        self.assertEqual([x["trade_id"] for x in eligible], ["prior"])

    def test_mae_budget_uses_current_nav_and_depth_caps_whole_units(self):
        result = M.size_mae(100_000, 0.10, 2_000, 1.5, 4)
        self.assertEqual(result["budget_usd"], 10_000)
        self.assertEqual(result["denominator_usd"], 3_000)
        self.assertEqual(result["planned"], 3)
        self.assertEqual(result["units"], 3)
        capped = M.size_mae(1_000_000, 0.50, 2_000, 1.0, 4)
        self.assertEqual(capped["planned"], 250)
        self.assertEqual(capped["units"], 4)
        self.assertEqual(capped["status"], "DEPTH_CAPPED")

    def test_no_prior_mae_is_pending_not_a_zero_risk_estimate(self):
        result = M.size_mae(100_000, 0.10, None, 1.0, 20)
        self.assertEqual(result["units"], 0)
        self.assertEqual(result["status"], "PENDING_NO_PRIOR_MAE")

    def test_unexecutable_inverse_entry_cannot_train_mae(self):
        original = sample_trade()
        original["entry_quotes"]["long"]["bid_size"] = 0
        transformed = M.invert_same_contract_trade(original)
        result = M.reference(transformed, 0, M.ORIENTATIONS[1], M.core.LONG_HEAVY, 5,
                             M.POLICIES[0], 0)
        self.assertFalse(result["entry_capacity_eligible"])
        self.assertFalse(result["training_eligible"])
        self.assertEqual(result["training_exclusion_reason"], "ENTRY_DEPTH_INSUFFICIENT")

    def test_target_is_normalized_to_starting_nav(self):
        self.assertAlmostEqual(100_000 * M.TARGET_MULTIPLE, 314_012)
        self.assertAlmostEqual(1_000_000 * M.TARGET_MULTIPLE, 3_140_120)


if __name__ == "__main__":
    unittest.main(verbosity=2)
