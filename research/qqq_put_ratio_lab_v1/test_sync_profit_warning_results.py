import importlib.util
from pathlib import Path
import unittest

LAB = Path(__file__).resolve().parent
TEST_SOURCE = LAB.parent / "qqq_put_ratio_exit_study_v1" / "test_qqq_put_ratio_exit_study_v1.py"
REPLAY_SOURCE = LAB / "sync_profit_warning_results.py"

spec = importlib.util.spec_from_file_location("sync_profit_warning_results", REPLAY_SOURCE)
M = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(M)

fixture_spec = importlib.util.spec_from_file_location("original_replay_fixtures", TEST_SOURCE)
T = importlib.util.module_from_spec(fixture_spec)
assert fixture_spec and fixture_spec.loader
fixture_spec.loader.exec_module(T)


def fixture():
    trade = T.trade_fixture()
    trade["path"] = [
        T.step(T.DAY0, 44, short_bid=4.9, short_ask=5.1, long_bid=4.8, long_ask=5.0),
        T.step(T.DAY1, 43, short_bid=.8, short_ask=1.0, long_bid=15.0, long_ask=15.2),
        T.step(T.DAY2, 42, short_bid=.05, short_ask=.10, long_bid=.1, long_ask=.15),
        T.step(T.EXPIRY, 0, short_bid=.01, short_ask=.02, long_bid=.1, long_ask=.2, spot=500.0),
    ]
    return trade


class ThresholdEventTests(unittest.TestCase):
    def test_actual_signal_and_next_observed_action_are_separate_from_held_path(self):
        event = M.build_threshold_study([fixture()], M.REPLAY, 800)
        self.assertEqual(event["actualPolicyTriggerCount"], 1)
        self.assertEqual(event["successfulExitActionCount"], 1)
        self.assertEqual(event["actualEvents"][0]["signalDate"], T.DAY1)
        self.assertEqual(event["actualEvents"][0]["executionDate"], T.DAY2)
        self.assertEqual(event["actualEvents"][0]["signalToExecutionSessions"], 1)
        self.assertEqual(event["counterfactualFirstMarkHitCount"], 1)
        self.assertEqual(event["sampleStatus"], "INSUFFICIENT_SMALL_TRIGGER_COHORT")

    def test_unknown_target_is_not_interpolated(self):
        with self.assertRaisesRegex(ValueError, "not directly defined"):
            M.build_threshold_study([fixture()], M.REPLAY, 900)


if __name__ == "__main__":
    unittest.main()
