from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from research.evidence_v1 import checkpoint
from research.evidence_v1.ledger import EvidenceLedger, sha256_json

RUNTIME_IDENTITY={
    "strategy_id":"TEST","strategy_version":"V1",
    "selection_cutoff":"2025-12-15","research_engine_commit":"ENG1",
    "strategy_lock_hash":"LOCK1","code_hashes":{},"evidence_policy":{},
}


def _seed():
    actions = [
        {"action":"ADD_NEAR","code":"US.QQQ.TEST","qty":2,"price":8.5},
        {"action":"REDUCE_NEAR","code":"US.QQQ.TEST","qty":1,"price":12.0},
    ]
    journal = [
        {
            "candidate_index":i,
            "candidate_sha256":sha256_json(a),
            "raw_candidate":a,
            "observed_at_utc":"2026-10-01T20:00:02+00:00",
        }
        for i,a in enumerate(actions)
    ]
    return actions, journal


def test_forward_checkpoint_requires_exact_candidate_identity():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        ledger=EvidenceLedger(root/"research/evidence_v1/evidence.jsonl",identity={
            "strategy_id":"TEST","strategy_version":"V1",
            "research_engine_commit":"ENG1","strategy_lock_hash":"LOCK1",
        })
        actions,journal=_seed()
        ledger.append("CYCLE_STARTED",cycle_id="C1",campaign_id="CAMP1",
                      timestamp_utc="2026-10-01T20:00:00+00:00",payload={})
        anchor=ledger.append(
            "DECISION_EMITTED",cycle_id="C1",campaign_id="CAMP1",
            timestamp_utc="2026-10-01T20:00:02+00:00",
            payload={
                "contract":"AS_EMITTED_THEN_POSTHOC",
                "candidate_actions":actions,
                "candidate_journal":journal,
                "primary":actions[0],
            },
        )
        with patch.object(checkpoint, "runtime_identity", lambda repo_root: RUNTIME_IDENTITY):
            argv=sys.argv
            try:
                sys.argv=[
                    "checkpoint.py","--repo-root",str(root),
                    "--campaign-id","CAMP1",
                    "--anchor-evidence-id",anchor["evidence_id"],
                    "--candidate-index","0",
                    "--candidate-sha256","bad",
                    "--benchmark","QQQ",
                    "--horizon-trading-days","5",
                    "--benchmark-return","0.10",
                ]
            try:
                checkpoint.main()
            except SystemExit as exc:
                assert "CANDIDATE_SHA256_MISMATCH_AT_ANCHOR" in str(exc)
            else:
                raise AssertionError("forged candidate identity was accepted")
                finally:
                    sys.argv=argv


def test_forward_checkpoint_persists_scope_and_candidate_identity():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        ledger=EvidenceLedger(root/"research/evidence_v1/evidence.jsonl",identity={
            "strategy_id":"TEST","strategy_version":"V1",
            "research_engine_commit":"ENG1","strategy_lock_hash":"LOCK1",
        })
        actions,journal=_seed()
        ledger.append("CYCLE_STARTED",cycle_id="C1",campaign_id="CAMP1",
                      timestamp_utc="2026-10-01T20:00:00+00:00",payload={})
        anchor=ledger.append(
            "DECISION_EMITTED",cycle_id="C1",campaign_id="CAMP1",
            timestamp_utc="2026-10-01T20:00:02+00:00",
            payload={
                "contract":"AS_EMITTED_THEN_POSTHOC",
                "candidate_actions":actions,
                "candidate_journal":journal,
                "primary":actions[0],
            },
        )
        with patch.object(checkpoint, "runtime_identity", lambda repo_root: RUNTIME_IDENTITY):
            argv=sys.argv
            try:
                sys.argv=[
                    "checkpoint.py","--repo-root",str(root),
                    "--campaign-id","CAMP1",
                    "--anchor-evidence-id",anchor["evidence_id"],
                    "--candidate-index","1",
                    "--candidate-sha256",sha256_json(actions[1]),
                    "--benchmark","SPY",
                    "--horizon-trading-days","21",
                    "--benchmark-return","0.12",
                    "--candidate-return","0.18",
                ]
            assert checkpoint.main()==0
                finally:
                    sys.argv=argv
        rows=EvidenceLedger(root/"research/evidence_v1/evidence.jsonl").rows()
        payload=rows[-1]["payload"]
        assert rows[-1]["event_type"]=="FORWARD_CHECKPOINT_OBSERVED"
        assert payload["candidate_index"]==1
        assert payload["candidate_sha256"]==sha256_json(actions[1])
        assert payload["benchmark"]=="SPY"
        assert payload["horizon_trading_days"]==21
        assert payload["benchmark_return"]==0.12
        assert payload["candidate_return"]==0.18


def test_forward_checkpoint_rejects_duplicate_scope():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        ledger=EvidenceLedger(root/"research/evidence_v1/evidence.jsonl",identity={
            "strategy_id":"TEST","strategy_version":"V1",
            "research_engine_commit":"ENG1","strategy_lock_hash":"LOCK1",
        })
        actions,journal=_seed()
        ledger.append("CYCLE_STARTED",cycle_id="C1",campaign_id="CAMP1",
                      timestamp_utc="2026-10-01T20:00:00+00:00",payload={})
        anchor=ledger.append(
            "DECISION_EMITTED",cycle_id="C1",campaign_id="CAMP1",
            timestamp_utc="2026-10-01T20:00:02+00:00",
            payload={
                "contract":"AS_EMITTED_THEN_POSTHOC",
                "candidate_actions":actions,
                "candidate_journal":journal,
                "primary":actions[0],
            },
        )
        args=[
            "checkpoint.py","--repo-root",str(root),
            "--campaign-id","CAMP1",
            "--anchor-evidence-id",anchor["evidence_id"],
            "--candidate-index","0",
            "--candidate-sha256",sha256_json(actions[0]),
            "--benchmark","QQQ",
            "--horizon-trading-days","5",
            "--benchmark-return","0.10",
        ]
        with patch.object(checkpoint, "runtime_identity", lambda repo_root: RUNTIME_IDENTITY):
            with patch.object(sys,"argv",args):
                assert checkpoint.main()==0
            with patch.object(sys,"argv",args):
                try:
                checkpoint.main()
                except SystemExit as exc:
                    assert "FORWARD_CHECKPOINT_ALREADY_RECORDED" in str(exc)
                else:
                    raise AssertionError("duplicate checkpoint was accepted")


def test_report_groups_forward_checkpoints_by_candidate_benchmark_and_horizon():
    from research.evidence_v1 import report

    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        path=root/"research/evidence_v1/evidence.jsonl"
        ledger=EvidenceLedger(path)
        for i,payload in enumerate([
            {
                "campaign_id":"C1",
                "anchor_evidence_id":"A1",
                "candidate_sha256":"HASH-A",
                "candidate_index":0,
                "benchmark":"QQQ",
                "horizon_trading_days":5,
                "benchmark_return":0.05,
                "candidate_return":0.08,
            },
            {
                "campaign_id":"C1",
                "anchor_evidence_id":"A1",
                "candidate_sha256":"HASH-A",
                "candidate_index":0,
                "benchmark":"QQQ",
                "horizon_trading_days":21,
                "benchmark_return":0.10,
                "candidate_return":0.15,
            },
        ]):
            ledger.append(
                "FORWARD_CHECKPOINT_OBSERVED",
                cycle_id=f"CHK{i}",
                campaign_id="C1",
                timestamp_utc=f"2026-10-02T00:0{i}:00+00:00",
                payload=payload,
                evidence_grade="HUMAN_REPORTED",
            )
        import sys
        argv=sys.argv
        try:
            sys.argv=["report.py","--repo-root",str(root)]
            assert report.main()==0
        finally:
            sys.argv=argv
        obj=json.loads(
            (root/"research/evidence_v1/sealed/LONGITUDINAL_REPORT.json").read_text(
                encoding="utf-8"
            )
        )
        groups=obj["forward_checkpoint_observation"]["groups"]
        assert set(groups)=={"HASH-A|QQQ|5D","HASH-A|QQQ|21D"}
        assert groups["HASH-A|QQQ|5D"]["mean_benchmark_return"]==0.05
        assert groups["HASH-A|QQQ|21D"]["mean_candidate_return"]==0.15
