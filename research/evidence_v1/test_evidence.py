from __future__ import annotations

import json
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


def _write_test_snapshot(root, cycle_id="C1", campaign_id="CAMP1"):
    from research.evidence_v1.snapshot import write_snapshot
    return write_snapshot(
        root,
        cycle_id,
        {"cycle_id": cycle_id, "campaign_id": campaign_id,
         "family_observation": {"rows": []}},
    )


def test_report_reads_only_validated_ledger_and_dedupes_corrections():
    import json
    import tempfile
    from research.evidence_v1.report import main as report_main

    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        ev=root/"research/evidence_v1/evidence.jsonl"
        ledger=EvidenceLedger(ev)
        for et,t in [
            ("CYCLE_STARTED","2026-10-01T00:00:00+00:00"),
            ("PRE_DECISION_OBSERVATION","2026-10-01T00:00:01+00:00"),
            ("DECISION_EMITTED","2026-10-01T00:00:02+00:00"),
        ]:
            payload={"candidate_actions":[],"primary":None} if et=="DECISION_EMITTED" else {}
            ledger.append(et,cycle_id="C1",campaign_id="CAMP1",timestamp_utc=t,payload=payload)
        snap_ref=_write_test_snapshot(root)
        # Attach a real, hash-verified pre-decision snapshot to the first cycle.
        rows_before_outcome=ledger.rows()
        pre=rows_before_outcome[1]
        pre["payload"]["snapshot"]=snap_ref
        # The fixture only needs a valid ledger record for report processing;
        # rebuild that pre-decision row in a dedicated ledger below.
        ev.unlink()
        ledger=EvidenceLedger(ev)
        ledger.append("CYCLE_STARTED",cycle_id="C1",campaign_id="CAMP1",timestamp_utc="2026-10-01T00:00:00+00:00",payload={})
        ledger.append("PRE_DECISION_OBSERVATION",cycle_id="C1",campaign_id="CAMP1",timestamp_utc="2026-10-01T00:00:01+00:00",payload={"snapshot":snap_ref})
        ledger.append("DECISION_EMITTED",cycle_id="C1",campaign_id="CAMP1",timestamp_utc="2026-10-01T00:00:02+00:00",payload={"candidate_actions":[],"primary":None})
        first=ledger.append(
            "OUTCOME_RESOLVED",cycle_id="O1",campaign_id="CAMP1",
            timestamp_utc="2026-10-01T01:00:00+00:00",
            payload={"realized_pnl":100.0,"benchmark_return":0.01},
        )
        second=ledger.append(
            "OUTCOME_RESOLVED",cycle_id="O2",campaign_id="CAMP1",
            timestamp_utc="2026-10-01T02:00:00+00:00",
            payload={"realized_pnl":80.0,"benchmark_return":0.008,
                     "anchor_evidence_id":"DECISION-TEST",
                     "corrects_evidence_id":first["evidence_id"]},
        )
        import sys
        from unittest.mock import patch
        with patch.object(sys,"argv",["report.py","--repo-root",str(root)]):
            assert report_main()==0
        report=json.loads((root/"research/evidence_v1/sealed/LONGITUDINAL_REPORT.json").read_text(encoding="utf-8"))
        assert report["ledger_head_hash"]==ledger.validate()["head_hash"]
        assert report["outcome_metrics"]["resolved_outcomes"]==1
        assert report["outcome_metrics"]["realized_pnl_sum"]==80.0


def test_snapshot_round_trip_hash_and_atomic_publish():
    import json
    import tempfile
    from research.evidence_v1.snapshot import snapshot_sha256, write_snapshot
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        payload={"cycle_id":"C1","family_observation":{"rows":[{"family_id":"F1","status":"AVAILABLE"}]}}
        ref=write_snapshot(root,"C1",payload)
        saved=json.loads((root/ref["snapshot_ref"]).read_text(encoding="utf-8"))
        assert ref["snapshot_sha256"]==snapshot_sha256(saved)
        assert not (root/"research/evidence_v1/snapshots/C1.json.tmp").exists()


def test_report_blocks_snapshot_hash_tamper():
    import json
    import sys
    from unittest.mock import patch
    from research.evidence_v1.report import main as report_main
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        ev=root/"research/evidence_v1/evidence.jsonl"
        ledger=EvidenceLedger(ev)
        snap=root/"research/evidence_v1/snapshots/C1.json"
        snap.parent.mkdir(parents=True)
        obj={"cycle_id":"C1","family_observation":{"rows":[]}}
        snap.write_text(json.dumps(obj),encoding="utf-8")
        from research.evidence_v1.snapshot import snapshot_sha256
        good=snapshot_sha256(obj)
        ledger.append("CYCLE_STARTED",cycle_id="C1",campaign_id="CAMP1",timestamp_utc="2026-10-01T00:00:00+00:00",payload={})
        ledger.append("PRE_DECISION_OBSERVATION",cycle_id="C1",campaign_id="CAMP1",timestamp_utc="2026-10-01T00:00:01+00:00",
                      payload={"snapshot":{"snapshot_ref":"research/evidence_v1/snapshots/C1.json","snapshot_sha256":good}})
        snap.write_text(json.dumps({"cycle_id":"C1","family_observation":{"rows":[{"tampered":True}]}}),encoding="utf-8")
        with patch.object(sys,"argv",["report.py","--repo-root",str(root)]):
            try:
                rc=report_main()
            except SystemExit:
                rc=1
        assert rc==2
        report=json.loads((root/"research/evidence_v1/sealed/LONGITUDINAL_REPORT.json").read_text(encoding="utf-8"))
        assert report["snapshot_integrity"]["status"]=="BLOCKED"


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


def test_broker_reconciled_outcome_requires_source_evidence():
    import json
    import sys
    from research.evidence_v1 import outcome
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        lock=root/"research/evidence_v1/STRATEGY_LOCK.json"
        lock.parent.mkdir(parents=True)
        lock.write_text(json.dumps({
            "strategy_id":"TEST","strategy_version":"V1",
            "selection_cutoff":"2025-12-15",
            "research_engine_commit":"TEST","evidence_policy":{},
        }),encoding="utf-8")
        ledger=EvidenceLedger(root/"research/evidence_v1/evidence.jsonl")
        anchor=ledger.append("DECISION_EMITTED",cycle_id="C1",campaign_id="CAMP1",
                             timestamp_utc="2026-10-01T00:00:00+00:00",
                             payload={"candidate_actions":[],"primary":None})
        with patch.object(sys,"argv",[
            "outcome.py","--repo-root",str(root),
            "--campaign-id","CAMP1","--anchor-evidence-id",anchor["evidence_id"],
            "--realized-pnl","10","--outcome-source","BROKER_RECONCILED",
        ]):
            try:
                outcome.main()
            except SystemExit as exc:
                assert "BROKER_RECONCILED_REQUIRES_SOURCE_EVIDENCE_ID" in str(exc)
            else:
                raise AssertionError("broker outcome without source evidence must fail")


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
        ledger.append(
            "CYCLE_STARTED",
            cycle_id="C1",
            campaign_id="CAMP1",
            timestamp_utc="2026-10-01T00:00:00+00:00",
            payload={},
        )
        ledger.append(
            "PRE_DECISION_OBSERVATION",
            cycle_id="C1",
            campaign_id="CAMP1",
            timestamp_utc="2026-10-01T00:00:01+00:00",
            payload={"observation":"TEST"},
        )
        anchor=ledger.append(
            "DECISION_EMITTED",
            cycle_id="C1",
            campaign_id="CAMP1",
            timestamp_utc="2026-10-01T00:00:02+00:00",
            payload={
                "candidate_actions": [],
                "primary": None,
                "contract": "AS_EMITTED_THEN_POSTHOC",
            },
        )

        def run(*extra):
            argv=[
                "outcome.py","--repo-root",str(root),
                "--campaign-id","CAMP1",
                "--anchor-evidence-id",anchor["evidence_id"],
                "--realized-pnl","100",
                "--outcome-source","USER_REPORTED",
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
            timestamp_utc="2026-10-01T00:00:02+00:00",
            payload={"candidate_actions":[],"primary":None},
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
            "payload":{"candidate_actions":[]},
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
