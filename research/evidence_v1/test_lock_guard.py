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

    def test_lock_manifest_identity_is_part_of_runtime_fence(self):
        import json
        import tempfile
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            path=root/"research/evidence_v1/STRATEGY_LOCK.json"
            path.parent.mkdir(parents=True)
            lock=json.loads((ROOT/"research/evidence_v1/STRATEGY_LOCK.json").read_text(encoding="utf-8"))
            lock["strategy_id"]="MUTATED"
            path.write_text(json.dumps(lock),encoding="utf-8")
            with self.assertRaises(StrategyLockViolation) as ctx:
                assert_runtime_lock(root, far_dte=120, far_delta=0.08, near_dte=30)
            self.assertIn("MANIFEST", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
