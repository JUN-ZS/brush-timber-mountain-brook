#!/usr/bin/env python3
import importlib.util
import unittest
from pathlib import Path

MODULE = Path(__file__).with_name("audit_qqq_option_shortlist_v1.py")
SPEC = importlib.util.spec_from_file_location("audit", MODULE)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class AuditTests(unittest.TestCase):
    def test_wilson_interval_has_bounds_and_width(self):
        low, high = audit.wilson_95(16, 28)
        self.assertLess(low, 16 / 28 * 100)
        self.assertGreater(high, 16 / 28 * 100)
        self.assertTrue(0 <= low <= high <= 100)

    def test_friction_scenarios_are_monotonic_for_long_debit_cost_example(self):
        row = {"pnl": 100.0, "contracts": 2}
        self.assertGreater(audit.scenario_pnl(row, "ZERO"), audit.scenario_pnl(row, "BASE"))
        self.assertGreater(audit.scenario_pnl(row, "BASE"), audit.scenario_pnl(row, "STRESS"))

    def test_terminal_risk_is_recomputed_by_cost_case(self):
        row = {
            "entry_cf": -500.0,
            "contracts": 2,
            "legs": [
                {"strike": 100.0, "right": "P", "side": "buy", "qty": 1},
                {"strike": 90.0, "right": "P", "side": "sell", "qty": 1}
            ],
            "depth_units": 20
        }
        zero = audit.terminal_worst_loss(row, "ZERO")
        base = audit.terminal_worst_loss(row, "BASE")
        stress = audit.terminal_worst_loss(row, "STRESS")
        self.assertLess(zero, base)
        self.assertLess(base, stress)

    def test_no_capacity_when_tail_loss_exceeds_budget(self):
        row = {
            "entry_cf": 100.0,
            "contracts": 6,
            "legs": [
                {"strike": 100.0, "right": "P", "side": "buy", "qty": 1},
                {"strike": 90.0, "right": "P", "side": "sell", "qty": 6}
            ],
            "depth_units": 100
        }
        counts = audit.capacity_counts(row, "BASE")
        self.assertEqual(counts["5"], 0)
        self.assertEqual(counts["10"], 0)
        self.assertEqual(counts["20"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
