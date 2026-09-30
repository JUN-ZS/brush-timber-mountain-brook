from __future__ import annotations

import unittest
from pathlib import Path

from research.evidence_v1.lock_guard import (
    StrategyLockViolation,
    assert_cli_member,
    assert_runtime_lock,
)


ROOT = Path(__file__).resolve().parents[2]


class LockGuardTest(unittest.TestCase):
    def test_all_72_member_parameter_axes_are_allowed(self):
        for dte in (90, 120, 180):
            for delta in (0.05, 0.08, 0.10):
                assert_cli_member(far_dte=dte, far_delta=delta, near_dte=30)

    def test_near_dte_mutation_is_rejected(self):
        with self.assertRaises(StrategyLockViolation):
            assert_cli_member(far_dte=120, far_delta=0.08, near_dte=21)

    def test_far_axis_mutation_is_rejected(self):
        with self.assertRaises(StrategyLockViolation):
            assert_cli_member(far_dte=60, far_delta=0.08, near_dte=30)
        with self.assertRaises(StrategyLockViolation):
            assert_cli_member(far_dte=120, far_delta=0.07, near_dte=30)

    def test_live_engine_constants_match_locked_core(self):
        out = assert_runtime_lock(ROOT, far_dte=120, far_delta=0.08, near_dte=30)
        self.assertEqual(out["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
