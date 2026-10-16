import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).with_name("sync_profit_warning_results.py")
spec = importlib.util.spec_from_file_location("sync_profit_warning_results", MODULE)
M = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(M)


def fixture():
    expiry = "2024-02-16"
    return {"trade_id": 1, "entry_date": "2024-01-03", "expiry": expiry,
        "long_id": "LONG", "short_id": "SHORT", "long_strike": 480.0,
        "short_strike": 450.0, "spot_entry": 500.0,
        "entry_quotes": {"long": {"ask": 5.0}, "short": {"bid": 4.9}},
        "path": [
            {"date": "2024-01-03", "short": {"bid": 4.9, "ask": 5.1, "ask_size": 10}, "long": {"bid": 4.8, "ask": 5.0, "bid_size": 10}, "spot": 500.0},
            {"date": "2024-01-04", "short": {"bid": .8, "ask": 1.0, "ask_size": 10}, "long": {"bid": 15.0, "ask": 15.2, "bid_size": 10}, "spot": 500.0},
            {"date": "2024-01-05", "short": {"bid": .05, "ask": .10, "ask_size": 10}, "long": {"bid": .1, "ask": .15, "bid_size": 10}, "spot": 500.0},
            {"date": expiry, "short": {"bid": .01, "ask": .02, "ask_size": 10}, "long": {"bid": .1, "ask": .2, "bid_size": 10}, "spot": 500.0},
        ]}


class ThresholdEventTests(unittest.TestCase):
    def test_actual_signal_and_next_observed_action_are_separate_from_held_path(self):
        event = M.build_threshold_study([fixture()], M.REPLAY, 800)
        self.assertEqual(event["actualPolicyTriggerCount"], 1)
        self.assertEqual(event["successfulExitActionCount"], 1)
        self.assertEqual(event["actualEvents"][0]["signalDate"], "2024-01-04")
        self.assertEqual(event["actualEvents"][0]["executionDate"], "2024-01-05")
        self.assertEqual(event["actualEvents"][0]["signalToExecutionSessions"], 1)
        self.assertEqual(event["counterfactualFirstMarkHitCount"], 1)
        self.assertEqual(event["sampleStatus"], "INSUFFICIENT_SMALL_TRIGGER_COHORT")

    def test_unknown_target_is_not_interpolated(self):
        with self.assertRaisesRegex(ValueError, "not directly defined"):
            M.build_threshold_study([fixture()], M.REPLAY, 900)


if __name__ == "__main__":
    unittest.main()
