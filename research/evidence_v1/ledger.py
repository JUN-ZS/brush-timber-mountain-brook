from __future__ import annotations

import hashlib
import json
import os
import tempfile
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any


SCHEMA = "STRATEGY_EVIDENCE.v1"
GENESIS = "0" * 64
EVENT_TYPES = {
    "CYCLE_STARTED",
    "PRE_DECISION_OBSERVATION",
    "DECISION_EMITTED",
    "EXECUTION_OBSERVED",
    "OUTCOME_RESOLVED",
    "DATA_GAP",
    "HUMAN_INTERVENTION",
    "CYCLE_FINALIZED",
}
EVIDENCE_GRADES = {
    "PROSPECTIVE_OBSERVED",
    "BROKER_OBSERVED",
    "PROSPECTIVE_OUTCOME",
    "DATA_GAP",
    "HUMAN_REPORTED",
    "EXTERNAL_RESEARCH",
}


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


class LedgerError(RuntimeError):
    pass


_EVIDENCE_THREAD_LOCKS = {}
_EVIDENCE_THREAD_LOCKS_GUARD = threading.Lock()


def _evidence_lock_path(path: Path) -> Path:
    key = hashlib.sha256(str(path.resolve()).encode("utf-8")).hexdigest()
    return Path(tempfile.gettempdir()) / f"qqq-evidence-ledger-{key}.lock"


@contextmanager
def evidence_ledger_lock(path: str | Path):
    """Serialize append/seal operations on one shared evidence ledger."""
    lock_path = _evidence_lock_path(Path(path))
    key = str(lock_path)
    with _EVIDENCE_THREAD_LOCKS_GUARD:
        thread_lock = _EVIDENCE_THREAD_LOCKS.setdefault(key, threading.Lock())
    with thread_lock:
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with lock_path.open("a+b") as fh:
            fh.seek(0, os.SEEK_END)
            if fh.tell() == 0:
                fh.write(b"0")
                fh.flush()
            fh.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(fh.fileno(), msvcrt.LK_LOCK, 1)
            else:
                import fcntl
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fh.seek(0)
                if os.name == "nt":
                    msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


class EvidenceLedger:
    """Append-only hash-chained evidence ledger.

    Historical rows are never edited. Any correction is a new event that
    references the earlier evidence_id. The ledger refuses to append after a
    malformed/corrupt tail, because silent repair would destroy provenance.
    """

    def __init__(self, path: str | Path, identity: dict[str, Any] | None = None):
        self.path = Path(path)
        self.identity = identity or {}
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _rows(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        rows: list[dict[str, Any]] = []
        for n, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise LedgerError(f"LEDGER_CORRUPT_JSON:line={n}") from exc
        return rows

    @staticmethod
    def _validate_cycle_semantics(rows: list[dict[str, Any]]) -> None:
        cycles: dict[str, dict[str, int]] = {}
        for idx, row in enumerate(rows, 1):
            cycle_id = str(row.get("cycle_id") or "")
            et = str(row.get("event_type") or "").upper()
            if not cycle_id:
                continue
            state = cycles.setdefault(cycle_id, {})
            if state.get("finalized") is not None and idx > state["finalized"]:
                raise LedgerError(f"LEDGER_EVENT_AFTER_FINALIZED:cycle={cycle_id}:seq={idx}")
            if et == "CYCLE_STARTED":
                if "started" in state:
                    raise LedgerError(f"LEDGER_DUPLICATE_CYCLE_STARTED:cycle={cycle_id}")
                state["started"] = idx
            elif et == "PRE_DECISION_OBSERVATION":
                if "pre_decision" in state:
                    raise LedgerError(f"LEDGER_DUPLICATE_PRE_DECISION:cycle={cycle_id}")
                if "started" not in state:
                    raise LedgerError(f"LEDGER_PRE_DECISION_WITHOUT_START:cycle={cycle_id}")
                state["pre_decision"] = idx
            elif et == "DECISION_EMITTED":
                if "decision" in state:
                    raise LedgerError(f"LEDGER_DUPLICATE_DECISION:cycle={cycle_id}")
                if "pre_decision" not in state:
                    raise LedgerError(f"LEDGER_DECISION_BEFORE_PRE_DECISION:cycle={cycle_id}")
                payload = row.get("payload") or {}
                # Backward compatibility: pre-hardening historical decisions may
                # lack the explicit AS_EMITTED_THEN_POSTHOC contract. New records
                # opt into strict capture and must retain the full candidate set.
                if payload.get("contract") == "AS_EMITTED_THEN_POSTHOC":
                    actions = payload.get("candidate_actions")
                    journal = payload.get("candidate_journal")
                    if not isinstance(actions, list):
                        raise LedgerError(f"LEDGER_DECISION_MISSING_CANDIDATE_ACTIONS:cycle={cycle_id}")
                    if "primary" not in payload:
                        raise LedgerError(f"LEDGER_DECISION_MISSING_PRIMARY:cycle={cycle_id}")
                    if not isinstance(journal, list):
                        raise LedgerError(f"LEDGER_DECISION_MISSING_CANDIDATE_JOURNAL:cycle={cycle_id}")
                    for j in journal:
                        if not isinstance(j, dict):
                            raise LedgerError(f"LEDGER_BAD_CANDIDATE_JOURNAL_ROW:cycle={cycle_id}")
                        raw = j.get("raw_candidate")
                        if not isinstance(raw, dict):
                            raise LedgerError(f"LEDGER_CANDIDATE_RAW_MISSING:cycle={cycle_id}")
                        digest = j.get("candidate_sha256")
                        if not digest or sha256_json(raw) != digest:
                            raise LedgerError(f"LEDGER_CANDIDATE_DIGEST_MISMATCH:cycle={cycle_id}")
                        cidx = j.get("candidate_index")
                        if cidx is not None:
                            try:
                                if int(cidx) < 0 or int(cidx) >= len(actions):
                                    raise LedgerError(f"LEDGER_CANDIDATE_INDEX_INVALID:cycle={cycle_id}")
                                if sha256_json(actions[int(cidx)]) != digest:
                                    raise LedgerError(f"LEDGER_CANDIDATE_EMIT_MISMATCH:cycle={cycle_id}")
                            except (TypeError, ValueError) as exc:
                                raise LedgerError(f"LEDGER_CANDIDATE_INDEX_INVALID:cycle={cycle_id}") from exc
                state["decision"] = idx
            elif et == "CYCLE_FINALIZED":
                if "finalized" in state:
                    raise LedgerError(f"LEDGER_DUPLICATE_CYCLE_FINALIZED:cycle={cycle_id}")
                if "started" not in state:
                    raise LedgerError(f"LEDGER_FINALIZED_WITHOUT_START:cycle={cycle_id}")
                state["finalized"] = idx

    def _validate_unlocked(self) -> dict[str, Any]:
        rows = self._rows()
        self._validate_cycle_semantics(rows)
        previous = GENESIS
        for idx, row in enumerate(rows, 1):
            if row.get("schema") != SCHEMA:
                raise LedgerError(f"LEDGER_BAD_SCHEMA:seq={idx}")
            if int(row.get("evidence_seq", -1)) != idx:
                raise LedgerError(f"LEDGER_BAD_SEQUENCE:seq={idx}")
            grade = str(row.get("evidence_grade") or "")
            if grade not in EVIDENCE_GRADES:
                raise LedgerError(f"LEDGER_BAD_EVIDENCE_GRADE:seq={idx}")
            timestamp = row.get("timestamp_utc")
            try:
                from datetime import datetime
                parsed_time = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
            except (TypeError, ValueError) as exc:
                raise LedgerError(f"LEDGER_BAD_TIMESTAMP:seq={idx}") from exc
            if parsed_time.tzinfo is None:
                raise LedgerError(f"LEDGER_NAIVE_TIMESTAMP:seq={idx}")
            if row.get("previous_hash") != previous:
                raise LedgerError(f"LEDGER_CHAIN_BREAK:seq={idx}")
            record_hash = row.get("record_hash")
            if not record_hash:
                raise LedgerError(f"LEDGER_MISSING_HASH:seq={idx}")
            body = dict(row)
            body.pop("record_hash", None)
            expected = sha256_json(body)
            if record_hash != expected:
                raise LedgerError(f"LEDGER_HASH_MISMATCH:seq={idx}")
            previous = record_hash
        return {
            "valid": True,
            "schema": SCHEMA,
            "records": len(rows),
            "head_hash": previous,
            "path": str(self.path),
        }

    def validate(self) -> dict[str, Any]:
        with evidence_ledger_lock(self.path):
            return self._validate_unlocked()

    def _last_unlocked(self) -> dict[str, Any] | None:
        rows = self._rows()
        return rows[-1] if rows else None

    def rows(self) -> list[dict[str, Any]]:
        """Return a locked snapshot of the immutable ledger rows for posthoc analysis."""
        with evidence_ledger_lock(self.path):
            return self._rows()

    def last(self) -> dict[str, Any] | None:
        with evidence_ledger_lock(self.path):
            return self._last_unlocked()

    def append(
        self,
        event_type: str,
        *,
        cycle_id: str,
        timestamp_utc: str,
        payload: dict[str, Any],
        campaign_id: str | None = None,
        instance_id: str | None = None,
        evidence_id: str | None = None,
        evidence_grade: str = "PROSPECTIVE_OBSERVED",
    ) -> dict[str, Any]:
        if event_type not in EVENT_TYPES:
            raise LedgerError(f"UNKNOWN_EVENT_TYPE:{event_type}")

        with evidence_ledger_lock(self.path):
            return self._append_unlocked(
                event_type,
                cycle_id=cycle_id,
                timestamp_utc=timestamp_utc,
                payload=payload,
                campaign_id=campaign_id,
                instance_id=instance_id,
                evidence_id=evidence_id,
                evidence_grade=evidence_grade,
            )

    def _append_unlocked(
        self,
        event_type: str,
        *,
        cycle_id: str,
        timestamp_utc: str,
        payload: dict[str, Any],
        campaign_id: str | None = None,
        instance_id: str | None = None,
        evidence_id: str | None = None,
        evidence_grade: str = "PROSPECTIVE_OBSERVED",
    ) -> dict[str, Any]:
        validation = self._validate_unlocked()
        seq = int(validation["records"]) + 1
        previous_hash = str(validation["head_hash"])
        eid = evidence_id or f"EV-{timestamp_utc.replace(':','').replace('-','').replace('.','')}-{seq:06d}"

        row: dict[str, Any] = {
            "schema": SCHEMA,
            "schema_version": 1,
            "evidence_seq": seq,
            "evidence_id": eid,
            "cycle_id": cycle_id,
            "campaign_id": campaign_id,
            "instance_id": instance_id,
            "timestamp_utc": timestamp_utc,
            "event_type": event_type,
            "evidence_grade": evidence_grade,
            "identity": self.identity,
            "previous_hash": previous_hash,
            "payload": payload,
        }
        row["record_hash"] = sha256_json(row)

        with self.path.open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(canonical_json(row) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        return row

    def seal(self, seal_path: str | Path | None = None, *, note: str = "") -> dict[str, Any]:
        with evidence_ledger_lock(self.path):
            validation = self._validate_unlocked()
            rows = self._rows()
            last = rows[-1] if rows else None
            seal = {
                "schema": "STRATEGY_EVIDENCE_SEAL.v1",
                "sealed_at_utc": last.get("timestamp_utc") if last else None,
                "ledger": str(self.path),
                "records": validation["records"],
                "head_hash": validation["head_hash"],
                "strategy_lock_hash": self.identity.get("strategy_lock_hash"),
                "code_hashes": self.identity.get("code_hashes", {}),
                "note": note,
            }
            target = Path(seal_path) if seal_path else self.path.with_suffix(".seal.json")
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp = target.with_suffix(target.suffix + ".tmp")
            tmp.write_text(
                json.dumps(seal, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            with tmp.open("r+b") as fh:
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, target)
        return seal
