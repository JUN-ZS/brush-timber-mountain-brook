#!/usr/bin/env python3
import unittest
from spy_far_tail_triggered_hedge_v1 import trigger_condition_met, trigger_tail_expiry_pnl, median, bounds


class TriggeredHedgeTests(unittest.TestCase):
    def test_trigger_threshold_is_fixed_entry_spot_and_inclusive(self):
        self.assertTrue(trigger_condition_met(97.0, 100.0, 0.03))
        self.assertFalse(trigger_condition_met(97.01, 100.0, 0.03))
        self.assertTrue(trigger_condition_met(95.0, 100.0, 0.05))
        self.assertFalse(trigger_condition_met(95.01, 100.0, 0.05))
        self.assertFalse(trigger_condition_met(None, 100.0, 0.03))

    def test_tail_expiry_pnl_charges_both_sides_and_deep_shock_pays(self):
        pnl = trigger_tail_expiry_pnl(1.0, 90.0, 100.0, -0.20, 1, 0.05, 0.65)
        self.assertAlmostEqual(pnl, 100 * (10.0 - 1.0) - 2 * (5.0 + 0.65), places=6)
        no_intrinsic = trigger_tail_expiry_pnl(1.0, 90.0, 100.0, -0.05, 1, 0.05, 0.65)
        self.assertLess(no_intrinsic, 0.0)
        self.assertGreater(pnl, no_intrinsic)

    def test_summary_helpers(self):
        self.assertEqual(median([1, 3]), 2.0)
        self.assertEqual(bounds([5, -2, 3]), (-2.0, 5.0))


if __name__ == "__main__":
    unittest.main(verbosity=2)
