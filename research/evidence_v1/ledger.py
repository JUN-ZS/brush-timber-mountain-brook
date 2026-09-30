from __future__ import annotations

import hashlib
import json
import os
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

    def validate(self) -> dict[str, Any]:
        rows = self._rows()
        previous = GENESIS
        for idx, row in enumerate(rows, 1):
            if row.get("schema") != SCHEMA:
                raise LedgerError(f"LEDGER_BAD_SCHEMA:seq={idx}")
            if int(row.get("evidence_seq", -1)) != idx:
                raise LedgerError(f"LEDGER_BAD_SEQUENCE:seq={idx}")
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

    def last(self) -> dict[str, Any] | None:
        rows = self._rows()
        return rows[-1] if rows else None

    def append(
        self,
        event_type: str,
        *,
        cycle_id: str,
        timestamp_utc: str,
        payload: dict[str, Any],
        campaign_id: str | None = None,
        evidence_id: str | None = None,
        evidence_grade: str = "PROSPECTIVE_OBSERVED",
    ) -> dict[str, Any]:
        if event_type not in EVENT_TYPES:
            raise LedgerError(f"UNKNOWN_EVENT_TYPE:{event_type}")

        validation = self.validate()
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
        validation = self.validate()
        last = self.last()
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
        target.write_text(json.dumps(seal, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return seal
