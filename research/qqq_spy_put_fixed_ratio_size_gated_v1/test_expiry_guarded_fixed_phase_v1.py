#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import run_expiry_guarded_fixed_phase_v1 as guarded


class ExpiryGuardedExitTests(unittest.TestCase):
    def test_dte_guard_triggers_before_holding_limit(self):
        self.assertTrue(guarded.expiry_guard_exit_trigger(age_sessions=3, dte=7, hold_sessions=10))
        self.assertEqual(guarded.expiry_guard_exit_reason(3, 7, 10), "DTE_LE_7")

    def test_holding_limit_triggers_while_dte_is_above_guard(self):
        self.assertTrue(guarded.expiry_guard_exit_trigger(age_sessions=10, dte=18, hold_sessions=10))
        self.assertEqual(guarded.expiry_guard_exit_reason(10, 18, 10), "HOLD_10_SESSIONS")

    def test_policy_stays_open_before_both_conditions(self):
        self.assertFalse(guarded.expiry_guard_exit_trigger(age_sessions=9, dte=8, hold_sessions=10))
        self.assertFalse(guarded.expiry_guard_exit_trigger(age_sessions=19, dte=8, hold_sessions=20))

    def test_dte_threshold_is_inclusive(self):
        self.assertTrue(guarded.expiry_guard_exit_trigger(age_sessions=1, dte=7, hold_sessions=20))
        self.assertFalse(guarded.expiry_guard_exit_trigger(age_sessions=1, dte=8, hold_sessions=20))

    def test_invalid_parameters_are_rejected(self):
        with self.assertRaises(ValueError):
            guarded.expiry_guard_exit_trigger(1, 7, 0)
        with self.assertRaises(ValueError):
            guarded.expiry_guard_exit_trigger(1, 7, 10, -1)

    def test_engine_patch_is_exact_and_does_not_mutate_baseline(self):
        namespace, hashes = guarded.load_engine_namespace()
        self.assertEqual(
            [p["policy"] for p in namespace["POLICIES"]],
            ["HOLD_10_OR_DTE_LE_7", "HOLD_20_OR_DTE_LE_7"],
        )
        self.assertEqual([p["dte_guard_days"] for p in namespace["POLICIES"]], [7, 7])
        self.assertEqual(len(hashes["base_engine_sha256"]), 64)
        self.assertEqual(len(hashes["patched_engine_sha256"]), 64)
        source = Path(guarded.ENGINE_PATH).read_text(encoding="utf-8")
        self.assertIn(guarded.TRIGGER_SOURCE, source, "baseline engine must not be modified by wrapper")


if __name__ == "__main__":
    unittest.main(verbosity=2)
