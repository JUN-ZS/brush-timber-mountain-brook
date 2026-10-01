from __future__ import annotations

import tempfile
from pathlib import Path

from research.evidence_v1.family_snapshot import build_family_snapshot
from research.evidence_v1.ledger import EvidenceLedger, LedgerError
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
