#!/usr/bin/env python3
import unittest
from run_spy_far_tail_conditional_v1 import compute_trigger_flags, conditional_result, sleeve_pnl, tail_stress_pnl


def cohort(episode, date, spot, delta=0.20, signal_index=0):
    return {"arm": "DTE45", "phase": 0, "episode_id": episode, "entry_date": date,
            "signal_date": date, "signal_index": signal_index, "spy_spot_entry": str(spot),
            "spy_abs_delta": str(delta)}


class TriggerLogicTests(unittest.TestCase):
    def test_drawdown_trigger_uses_only_past_and_current_observations(self):
        values = [100, 102, 101, 99, 94]
        rows = [cohort(str(i), f"2024-01-{i+1:02d}", value, 0.20, i * 5) for i, value in enumerate(values)]
        flags = compute_trigger_flags({("DTE45", 0, x["episode_id"]): x for x in rows})
        last = flags[("DTE45", 0, "4")]
        self.assertAlmostEqual(last["drawdown_from_5_observation_peak_pct"], 7.8431, places=3)
        self.assertTrue(last["risk_trigger"])
        self.assertTrue(last["drawdown_trigger"])

    def test_delta_can_trigger_before_drawdown_window_is_ready(self):
        row = cohort("a", "2024-01-02", 100, 0.31, 0)
        flags = compute_trigger_flags({("DTE45", 0, "a"): row})
        self.assertTrue(flags[("DTE45", 0, "a")]["risk_trigger"])
        self.assertFalse(flags[("DTE45", 0, "a")]["drawdown_history_ready"])
        self.assertTrue(flags[("DTE45", 0, "a")]["short_delta_trigger"])

    def test_future_drop_does_not_retroactively_trigger_earlier_cohort(self):
        values = [100, 100, 100, 100, 90]
        rows = [cohort(chr(97+i), f"2024-01-{2+7*i:02d}", value, 0.20, i*5) for i,value in enumerate(values)]
        flags = compute_trigger_flags({("DTE45", 0, x["episode_id"]): x for x in rows})
        self.assertFalse(flags[("DTE45", 0, "d")]["risk_trigger"])
        self.assertTrue(flags[("DTE45", 0, "e")]["risk_trigger"])

    def test_missing_exit_is_not_assumed_zero(self):
        self.assertEqual(conditional_result(False, False, False, 100, None), (100, "NO_HEDGE_NOT_TRIGGERED"))
        self.assertEqual(conditional_result(True, False, False, -200, None), (-200, "TRIGGERED_BUT_TAIL_ENTRY_NOT_EXECUTABLE"))
        pnl, _ = conditional_result(True, True, False, -200, None)
        self.assertIsNone(pnl)
        self.assertEqual(conditional_result(True, True, True, -200, 50), (-150, "TRIGGERED_HEDGE_PAIRED_REALIZED"))

    def test_deep_expiry_shock_improves_sleeve_when_tail_is_in_the_money(self):
        base = sleeve_pnl(100, 95, 3, 1.0, -0.50, 0.05, 0.65)
        tail = tail_stress_pnl(80, 3, 0.10, 100, -0.50, 0.05, 0.65)
        self.assertLess(base, 0)
        self.assertGreater(base + tail, base)


if __name__ == "__main__":
    unittest.main(verbosity=2)
