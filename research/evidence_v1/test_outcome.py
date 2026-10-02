from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from research.evidence_v1.ledger import EvidenceLedger
from research.evidence_v1 import outcome


def _seed_campaign(repo: Path, campaign_id: str = "C1"):
    path = repo / "research/evidence_v1/evidence.jsonl"
    ledger = EvidenceLedger(path, identity={
        "strategy_id": "TEST",
        "strategy_version": "V1",
        "research_engine_commit": "ENG1",
        "strategy_lock_hash": "LOCK1",
    })
    ledger.append(
        "CYCLE_STARTED",
        cycle_id="CYCLE1",
        campaign_id=campaign_id,
        timestamp_utc="2026-10-01T20:00:00+00:00",
        payload={},
    )
    pre = ledger.append(
        "PRE_DECISION_OBSERVATION",
        cycle_id="CYCLE1",
        campaign_id=campaign_id,
        timestamp_utc="2026-10-01T20:00:01+00:00",
        payload={},
    )
    return ledger, pre["evidence_id"]


TEST_IDENTITY = {
    "strategy_id": "TEST",
    "strategy_version": "V1",
    "selection_cutoff": "2025-12-15",
    "research_engine_commit": "ENG1",
    "strategy_lock_hash": "LOCK1",
    "code_hashes": {},
    "evidence_policy": "TEST",
}


class OutcomeTests(unittest.TestCase):
    def test_outcome_requires_benchmark_scope_when_return_is_present(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _, anchor = _seed_campaign(repo)
            with patch.object(outcome, "runtime_identity", lambda repo_root: TEST_IDENTITY):
                argv = sys.argv
                try:
                    sys.argv = [
                        "outcome.py",
                        "--repo-root", str(repo),
                        "--campaign-id", "C1",
                        "--anchor-evidence-id", anchor,
                        "--realized-pnl", "10",
                        "--benchmark-return", "0.05",
                    ]
                    with self.assertRaises(SystemExit) as exc:
                        outcome.main()
                    self.assertIn(
                        "BENCHMARK_REQUIRED_WHEN_RETURN_SUPPLIED",
                        str(exc.exception),
                    )
                finally:
                    sys.argv = argv

    def test_outcome_rejects_cross_lineage_anchor(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            ledger, _ = _seed_campaign(repo)
            # Rebuild the anchor as a second lineage only for this test.
            ledger.append(
                "CYCLE_STARTED",
                cycle_id="CROSS",
                campaign_id="CROSS",
                timestamp_utc="2026-10-01T20:01:00+00:00",
                payload={},
            )
            ledger.append(
                "PRE_DECISION_OBSERVATION",
                cycle_id="CROSS",
                campaign_id="CROSS",
                timestamp_utc="2026-10-01T20:01:00+00:00",
                payload={},
            )
            anchor = ledger.append(
                "DECISION_EMITTED",
                cycle_id="CROSS",
                campaign_id="CROSS",
                timestamp_utc="2026-10-01T20:01:01+00:00",
                payload={"candidate_actions":[], "candidate_journal":[], "primary":None,
                         "contract":"AS_EMITTED_THEN_POSTHOC"},
            )
            rows = ledger.rows()
            # Replace only the anchor identity in a controlled malformed ledger
            # would invalidate its record hash; instead mock the runtime lineage.
            cross_runtime = dict(TEST_IDENTITY)
            cross_runtime["research_engine_commit"] = "ENG2"
            with patch.object(outcome, "runtime_identity", lambda repo_root: cross_runtime):
                argv = sys.argv
                try:
                    sys.argv = [
                        "outcome.py", "--repo-root", str(repo),
                        "--campaign-id", "CROSS",
                        "--anchor-evidence-id", anchor["evidence_id"],
                        "--realized-pnl", "1",
                    ]
                    with self.assertRaises(SystemExit) as exc:
                        outcome.main()
                    self.assertIn("OUTCOME_ANCHOR_LINEAGE_MISMATCH:research_engine_commit", str(exc.exception))
                finally:
                    sys.argv = argv


    def test_valid_benchmark_outcome_persists_benchmark_and_horizon(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _, anchor = _seed_campaign(repo)
            with patch.object(outcome, "runtime_identity", lambda repo_root: TEST_IDENTITY):
                argv = sys.argv
                try:
                    sys.argv = [
                        "outcome.py",
                        "--repo-root", str(repo),
                        "--campaign-id", "C1",
                        "--anchor-evidence-id", anchor,
                        "--realized-pnl", "10",
                        "--benchmark", "QQQ",
                        "--horizon-trading-days", "21",
                        "--benchmark-return", "0.05",
                    ]
                    self.assertEqual(outcome.main(), 0)
                finally:
                    sys.argv = argv
            rows = EvidenceLedger(repo/"research/evidence_v1/evidence.jsonl").rows()
            payload = rows[-1]["payload"]
            self.assertEqual(payload["benchmark"], "QQQ")
            self.assertEqual(payload["horizon_trading_days"], 21)
            self.assertEqual(payload["benchmark_return"], 0.05)

    def test_report_refuses_to_average_mixed_benchmark_scopes(self):
        from research.evidence_v1 import report

        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            ledger = EvidenceLedger(repo/"research/evidence_v1/evidence.jsonl")
            for i, (campaign, benchmark, horizon, ret) in enumerate([
                ("C1", "QQQ", 21, 0.05),
                ("C2", "SPY", 63, 0.10),
            ]):
                ledger.append(
                    "OUTCOME_RESOLVED",
                    cycle_id=f"O{i}",
                    campaign_id=campaign,
                    timestamp_utc=f"2026-10-01T20:0{i}:00+00:00",
                    payload={
                        "campaign_id": campaign,
                        "realized_pnl": 10.0,
                        "benchmark": benchmark,
                        "horizon_trading_days": horizon,
                        "benchmark_return": ret,
                        "outcome_source": "USER_REPORTED",
                    },
                    evidence_grade="HUMAN_REPORTED",
                )

            argv = sys.argv
            try:
                sys.argv = ["report.py", "--repo-root", str(repo)]
                self.assertEqual(report.main(), 0)
            finally:
                sys.argv = argv
            obj = json.loads(
                (repo/"research/evidence_v1/sealed/LONGITUDINAL_REPORT.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(obj["outcome_metrics"]["benchmark_observations"], 2)
            self.assertIsNone(obj["outcome_metrics"]["mean_benchmark_return"])
            self.assertEqual(
                set(obj["outcome_metrics"]["benchmark_groups"]),
                {"QQQ|21D", "SPY|63D"},
            )


if __name__ == "__main__":
    unittest.main()
