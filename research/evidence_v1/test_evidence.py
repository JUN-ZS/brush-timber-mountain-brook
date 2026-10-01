from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from research.evidence_v1.family_snapshot import build_family_snapshot
from research.evidence_v1.ledger import EvidenceLedger, LedgerError, sha256_json
from research.live_hedge_v1.engine import Contract


def test_evidence_ledger_concurrent_appends():
    import threading
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "evidence.jsonl"
        errors = []

        def worker(i):
            try:
                ledger = EvidenceLedger(path, identity={"strategy_id": f"T{i}"})
                ledger.append(
                    "DATA_GAP",
                    cycle_id=f"C{i}",
                    timestamp_utc=f"2026-10-01T00:00:{i:02d}+00:00",
                    payload={"i": i},
                )
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert not errors
        result = EvidenceLedger(path).validate()
        assert result["valid"] is True
        assert result["records"] == 8


def test_last_is_consistent_with_append():
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "evidence.jsonl"
        ledger = EvidenceLedger(path)
        ledger.append(
            "DATA_GAP",
            cycle_id="C1",
            timestamp_utc="2026-10-01T00:00:00+00:00",
            payload={"n": 1},
        )
        last = ledger.last()
        assert last is not None
        assert last["evidence_seq"] == 1
        assert last["event_type"] == "DATA_GAP"


def test_outcome_rows_api_is_locked_snapshot():
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "evidence.jsonl"
        ledger = EvidenceLedger(path)
        ledger.append(
            "CYCLE_STARTED",
            cycle_id="C1",
            campaign_id="CAMP1",
            timestamp_utc="2026-10-01T00:00:00+00:00",
            payload={},
        )
        rows = ledger.rows()
        assert len(rows) == 1
        assert rows[0]["campaign_id"] == "CAMP1"


def test_outcome_requires_anchor_and_rejects_duplicate_without_correction():
    import json
    import sys
    from research.evidence_v1 import outcome

    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        lock=root/"research/evidence_v1/STRATEGY_LOCK.json"
        lock.parent.mkdir(parents=True)
        lock.write_text(json.dumps({
            "strategy_id":"TEST",
            "strategy_version":"V1",
            "selection_cutoff":"2025-12-15",
            "research_engine_commit":"TEST",
            "evidence_policy":{},
        }),encoding="utf-8")
        path=root/"research/evidence_v1/evidence.jsonl"
        ledger=EvidenceLedger(path)
        anchor=ledger.append(
            "DECISION_EMITTED",
            cycle_id="C1",
            campaign_id="CAMP1",
            timestamp_utc="2026-10-01T00:00:00+00:00",
            payload={"decision":"TEST"},
        )

        def run(*extra):
            argv=[
                "outcome.py","--repo-root",str(root),
                "--campaign-id","CAMP1",
                "--anchor-evidence-id",anchor["evidence_id"],
                "--realized-pnl","100",
            ]+list(extra)
            with patch.object(sys,"argv",argv):
                return outcome.main()

        assert run()==0
        try:
            run()
        except SystemExit as exc:
            assert "OUTCOME_ALREADY_RESOLVED" in str(exc)
        else:
            raise AssertionError("duplicate outcome must be rejected")

        rows=ledger.rows()
        prior_outcome=next(r for r in rows if r["event_type"]=="OUTCOME_RESOLVED")
        assert prior_outcome["payload"]["anchor_evidence_id"]==anchor["evidence_id"]

        assert run("--corrects-evidence-id",prior_outcome["evidence_id"])==0


def test_seal_publishes_without_leaving_partial_file():
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "evidence.jsonl"
        seal_path = Path(td) / "evidence.seal.json"
        ledger = EvidenceLedger(path)
        ledger.append(
            "DATA_GAP",
            cycle_id="C1",
            timestamp_utc="2026-10-01T00:00:00+00:00",
            payload={"n": 1},
        )
        seal = ledger.seal(seal_path)
        assert seal_path.exists()
        assert not Path(str(seal_path) + ".tmp").exists()
        assert json.loads(seal_path.read_text(encoding="utf-8"))["records"] == 1


def test_hash_chain_and_tamper_detection():
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "evidence.jsonl"
        ledger = EvidenceLedger(path, identity={"strategy_id": "TEST"})
        ledger.append(
            "CYCLE_STARTED",
            cycle_id="C1",
            timestamp_utc="2026-10-01T00:00:00+00:00",
            payload={"a": 1},
        )
        ledger.append(
            "PRE_DECISION_OBSERVATION",
            cycle_id="C1",
            timestamp_utc="2026-10-01T00:00:01+00:00",
            payload={"spot": 600},
        )
        assert ledger.validate()["records"] == 2
        original = path.read_text(encoding="utf-8")
        path.write_text(original.replace('"spot":600', '"spot":601'), encoding="utf-8")
        try:
            ledger.validate()
        except LedgerError as exc:
            assert "HASH_MISMATCH" in str(exc)
        else:
            raise AssertionError("tampering must be detected")


def test_cycle_semantics_require_predecision_before_decision_and_finalize_last():
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/"evidence.jsonl"
        ledger=EvidenceLedger(path)
        ledger.append(
            "CYCLE_STARTED",cycle_id="C1",
            timestamp_utc="2026-10-01T00:00:00+00:00",payload={},
        )
        ledger.append(
            "PRE_DECISION_OBSERVATION",cycle_id="C1",
            timestamp_utc="2026-10-01T00:00:01+00:00",payload={},
        )
        ledger.append(
            "DECISION_EMITTED",cycle_id="C1",
            timestamp_utc="2026-10-01T00:00:02+00:00",payload={},
        )
        ledger.append(
            "CYCLE_FINALIZED",cycle_id="C1",
            timestamp_utc="2026-10-01T00:00:03+00:00",payload={},
        )
        assert ledger.validate()["records"]==4

        bad_path=Path(td)/"bad.jsonl"
        bad=EvidenceLedger(bad_path)
        bad.append(
            "CYCLE_STARTED",cycle_id="C2",
            timestamp_utc="2026-10-01T00:01:00+00:00",payload={},
        )
        row={
            "schema":"STRATEGY_EVIDENCE.v1","schema_version":1,
            "evidence_seq":2,"evidence_id":"EV-BAD-000002",
            "cycle_id":"C2","campaign_id":None,
            "timestamp_utc":"2026-10-01T00:01:01+00:00",
            "event_type":"DECISION_EMITTED",
            "evidence_grade":"PROSPECTIVE_OBSERVED",
            "identity":{},
            "previous_hash":bad.last()["record_hash"],
            "payload":{},
        }
        row["record_hash"]=sha256_json(row)
        with bad_path.open("a",encoding="utf-8") as fh:
            import json
            fh.write(json.dumps(row,separators=(",",":"))+"\n")
        try:
            bad.validate()
        except LedgerError as exc:
            assert "DECISION_BEFORE_PRE_DECISION" in str(exc)
        else:
            raise AssertionError("cycle chronology violation must be detected")


def test_family_snapshot_is_exactly_72():
    contracts = []
    for dte in (90, 120, 180):
        for delta in (0.05, 0.08, 0.10):
            contracts.append(
                Contract(
                    code=f"US.QQQ.TEST{dte}{int(delta*100):02d}",
                    right="CALL",
                    strike=700 + dte / 20,
                    expiry=f"2027-01-{min(dte,28):02d}",
                    dte=dte,
                    bid=1.0,
                    ask=1.2,
                    delta=delta,
                    gamma=0.01,
                )
            )
    obs = build_family_snapshot(
        contracts,
        spot=650,
        signal_active=True,
        campaign_active=False,
    )
    assert obs["config_count"] == 72
    assert obs["family_count_expected"] == 72
    assert len({r["family_id"] for r in obs["rows"]}) == 72
    assert all(r["status"] == "AVAILABLE" for r in obs["rows"])


if __name__ == "__main__":
    test_hash_chain_and_tamper_detection()
    test_family_snapshot_is_exactly_72()
    print("PASS")



def load_tests(loader, tests, pattern):
    """Allow unittest CI to execute this module's top-level test functions."""
    suite = unittest.TestSuite(tests)
    for name, obj in sorted(globals().items()):
        if name.startswith("test_") and callable(obj):
            suite.addTest(unittest.FunctionTestCase(obj, description=name))
    return suite
