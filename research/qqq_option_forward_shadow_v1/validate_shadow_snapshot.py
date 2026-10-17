#!/usr/bin/env python3
"""Validate append-only QQQ option shadow snapshots; never executes orders."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
SIGNAL_RULE_ID = "QQQ_REVERSAL_2P1_MA20_VIX5D_V1"
EVENT_TYPES = {"SIGNAL", "ENTRY", "MARK", "EXIT", "BLOCKED_ENTRY", "BLOCKED_EXIT", "MISSING_MARK", "CENSORED"}
SOURCE_TYPES = {"MANUAL_SCREEN_CAPTURE", "BROKER_EXPORT", "LICENSED_HISTORICAL_DATA"}
ID_RE = re.compile(r"QQQ(\d{6})([CP])(\d{8})")
SHA256_RE = re.compile(r"[0-9a-f]{64}")


class SnapshotValidationError(ValueError):
    pass


def _num(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        n = float(value)
        return n if math.isfinite(n) else None
    except (TypeError, ValueError):
        return None


def _aware_datetime(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise SnapshotValidationError(f"{field}: ISO-8601 timestamp with UTC offset required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SnapshotValidationError(f"{field}: invalid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise SnapshotValidationError(f"{field}: naive timestamp is forbidden")
    return parsed


def _required_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SnapshotValidationError(f"{field}: non-empty string required")
    return value.strip()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_evidence_path(root: Path, relative: str) -> Path:
    rel = Path(relative)
    if rel.is_absolute():
        raise SnapshotValidationError("source.evidence_file: relative path required")
    root_resolved = root.resolve()
    resolved = (root_resolved / rel).resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise SnapshotValidationError("source.evidence_file: path traversal outside shadow root is forbidden") from exc
    return resolved


def _validate_evidence(snapshot: dict[str, Any], root: Path) -> dict[str, str]:
    source = snapshot.get("source")
    if not isinstance(source, dict):
        raise SnapshotValidationError("source: object required")
    source_type = _required_text(source.get("source_type"), "source.source_type")
    if source_type not in SOURCE_TYPES:
        raise SnapshotValidationError(f"source.source_type: unsupported value {source_type!r}")
    provider = _required_text(source.get("provider"), "source.provider")
    evidence_file = _required_text(source.get("evidence_file"), "source.evidence_file")
    expected_sha = str(source.get("evidence_sha256", "")).lower()
    if not SHA256_RE.fullmatch(expected_sha):
        raise SnapshotValidationError("source.evidence_sha256: 64-hex SHA-256 required")
    path = _safe_evidence_path(root, evidence_file)
    if not path.is_file():
        raise SnapshotValidationError(f"source.evidence_file: missing file {evidence_file}")
    actual_sha = _sha256(path)
    if actual_sha != expected_sha:
        raise SnapshotValidationError(f"source.evidence_sha256 mismatch: expected {expected_sha}, actual {actual_sha}")
    return {"source_type": source_type, "provider": provider, "evidence_file": evidence_file,
            "evidence_sha256": actual_sha}


def _validate_leg(leg: Any, snapshot_date: str, event_type: str, index: int) -> dict[str, Any]:
    prefix = f"legs[{index}]"
    if not isinstance(leg, dict):
        raise SnapshotValidationError(f"{prefix}: object required")
    contract_id = re.sub(r"\s+", "", _required_text(leg.get("contract_id"), f"{prefix}.contract_id").upper())
    if contract_id.startswith("O:"):
        contract_id = contract_id[2:]
    match = ID_RE.fullmatch(contract_id)
    if not match:
        raise SnapshotValidationError(f"{prefix}.contract_id: standard QQQ OCC root/expiry/right/strike required")
    if str(leg.get("symbol", "")).upper() != "QQQ":
        raise SnapshotValidationError(f"{prefix}.symbol: must be QQQ")
    right = str(leg.get("right", "")).upper()
    if right not in {"C", "P"} or right != match.group(2):
        raise SnapshotValidationError(f"{prefix}.right: mismatch with contract ID")
    try:
        encoded_expiry = datetime.strptime(match.group(1), "%y%m%d").date().isoformat()
    except ValueError as exc:
        raise SnapshotValidationError(f"{prefix}.contract_id: invalid expiry") from exc
    expiry = str(leg.get("expiry", ""))[:10]
    if expiry != encoded_expiry:
        raise SnapshotValidationError(f"{prefix}.expiry: mismatch with contract ID")
    strike = _num(leg.get("strike"))
    encoded_strike = int(match.group(3)) / 1000.0
    if strike is None or strike <= 0 or abs(strike - encoded_strike) >= 0.00051:
        raise SnapshotValidationError(f"{prefix}.strike: mismatch with contract ID")
    try:
        if date.fromisoformat(expiry) < date.fromisoformat(snapshot_date):
            raise SnapshotValidationError(f"{prefix}.expiry: an expired contract cannot be a live mark")
    except ValueError as exc:
        if isinstance(exc, SnapshotValidationError):
            raise
        raise SnapshotValidationError(f"{prefix}: invalid ISO date") from exc
    side = str(leg.get("position_side", "")).upper()
    if side not in {"LONG", "SHORT"}:
        raise SnapshotValidationError(f"{prefix}.position_side: must be LONG or SHORT")
    qty = leg.get("qty")
    if isinstance(qty, bool) or not isinstance(qty, int) or qty < 1:
        raise SnapshotValidationError(f"{prefix}.qty: positive whole-contract count required")
    quote_status = str(leg.get("quote_status", "")).upper()
    if quote_status not in {"OBSERVED", "MISSING"}:
        raise SnapshotValidationError(f"{prefix}.quote_status: must be OBSERVED or MISSING")
    if str(leg.get("quote_date", ""))[:10] != snapshot_date:
        raise SnapshotValidationError(f"{prefix}.quote_date: must equal snapshot_date; stale/forward-filled quotes forbidden")
    bid, ask = _num(leg.get("bid")), _num(leg.get("ask"))
    bid_size, ask_size = _num(leg.get("bid_size")), _num(leg.get("ask_size"))
    delta = _num(leg.get("delta"))
    if quote_status == "MISSING":
        if any(v is not None for v in (bid, ask, bid_size, ask_size, delta)):
            raise SnapshotValidationError(f"{prefix}: MISSING quote must use null price/size/Delta values")
        _required_text(leg.get("missing_reason"), f"{prefix}.missing_reason")
        return {"contract_id": contract_id, "right": right, "expiry": expiry, "strike": strike,
                "position_side": side, "qty": qty, "quote_status": "MISSING",
                "executable_at_visible_size": False}
    if bid is None or bid < 0 or ask is None or ask <= 0 or bid > ask:
        raise SnapshotValidationError(f"{prefix}: invalid or crossed Bid/Ask")
    if bid_size is None or bid_size < 0 or ask_size is None or ask_size < 0:
        raise SnapshotValidationError(f"{prefix}: non-negative displayed bid_size and ask_size required")
    if delta is None or abs(delta) >= 1 or delta == 0:
        raise SnapshotValidationError(f"{prefix}.delta: finite non-zero Delta with abs(value)<1 required")
    qtime = _aware_datetime(leg.get("quote_captured_at"), f"{prefix}.quote_captured_at")
    if qtime.date().isoformat() != snapshot_date:
        raise SnapshotValidationError(f"{prefix}.quote_captured_at: local date must equal snapshot_date")
    if event_type in {"ENTRY", "EXIT"}:
        if event_type == "ENTRY":
            price, size = (ask, ask_size) if side == "LONG" else (bid, bid_size)
        else:
            price, size = (bid, bid_size) if side == "LONG" else (ask, ask_size)
        if price <= 0 or size < qty:
            raise SnapshotValidationError(f"{prefix}: insufficient side-correct displayed size; record BLOCKED_{event_type}")
    if event_type == "SIGNAL":
        executable = ((ask_size >= qty and ask > 0) if side == "LONG" else (bid_size >= qty and bid > 0))
    else:
        executable = True
    return {"contract_id": contract_id, "right": right, "expiry": expiry, "strike": strike,
            "position_side": side, "qty": qty, "quote_status": "OBSERVED",
            "executable_at_visible_size": executable}


def validate_snapshot(snapshot: Any, shadow_root: Path) -> dict[str, Any]:
    if not isinstance(snapshot, dict):
        raise SnapshotValidationError("top-level JSON object required")
    if snapshot.get("schema_version") != SCHEMA_VERSION:
        raise SnapshotValidationError(f"schema_version must be {SCHEMA_VERSION}")
    snapshot_id = _required_text(snapshot.get("snapshot_id"), "snapshot_id")
    event_id = _required_text(snapshot.get("event_id"), "event_id")
    strategy_id = _required_text(snapshot.get("strategy_id"), "strategy_id")
    event_type = str(snapshot.get("event_type", "")).upper()
    if event_type not in EVENT_TYPES:
        raise SnapshotValidationError(f"unsupported event_type {event_type!r}")
    snapshot_date = str(snapshot.get("snapshot_date", ""))
    try:
        date.fromisoformat(snapshot_date)
    except ValueError as exc:
        raise SnapshotValidationError("snapshot_date must be ISO YYYY-MM-DD") from exc
    captured_at = _aware_datetime(snapshot.get("captured_at"), "captured_at")
    if captured_at.date().isoformat() != snapshot_date:
        raise SnapshotValidationError("captured_at date must equal snapshot_date")
    nav = _num(snapshot.get("nav_usd"))
    if nav is None or nav <= 0:
        raise SnapshotValidationError("nav_usd must be a positive finite value")
    if snapshot.get("execution_enabled") is not False or snapshot.get("order_placed") is not False:
        raise SnapshotValidationError("execution_enabled and order_placed must both be false")
    evidence = _validate_evidence(snapshot, shadow_root)
    market = snapshot.get("market")
    if not isinstance(market, dict) or str(market.get("symbol", "")).upper() != "QQQ":
        raise SnapshotValidationError("market must contain a QQQ observation")
    spot = _num(market.get("qqq_price"))
    vix = _num(market.get("vix"))
    if spot is None or spot <= 0:
        raise SnapshotValidationError("market.qqq_price must be positive")
    if vix is None or vix <= 0:
        raise SnapshotValidationError("market.vix must be positive; missing VIX is not inferred")
    for field in ("qqq_observed_at", "vix_observed_at"):
        dt = _aware_datetime(market.get(field), f"market.{field}")
        if dt.date().isoformat() != snapshot_date:
            raise SnapshotValidationError(f"market.{field} date must equal snapshot_date")
    signal = snapshot.get("signal")
    if event_type == "SIGNAL":
        if not isinstance(signal, dict):
            raise SnapshotValidationError("SIGNAL snapshot requires signal evidence")
        if signal.get("rule_id") != SIGNAL_RULE_ID:
            raise SnapshotValidationError(f"signal.rule_id must be frozen as {SIGNAL_RULE_ID}")
        state = str(signal.get("state", "")).upper()
        if state not in {"TRIGGERED", "NOT_TRIGGERED", "INCOMPLETE"}:
            raise SnapshotValidationError("signal.state must be TRIGGERED, NOT_TRIGGERED or INCOMPLETE")
        if state == "TRIGGERED":
            current = _num(signal.get("qqq_close_vs_ma20_pct"))
            previous = _num(signal.get("previous_close_vs_ma20_pct"))
            vix_change = _num(signal.get("vix_5_session_change_pct"))
            if current is None or current > -2.1:
                raise SnapshotValidationError("TRIGGERED requires QQQ <= -2.1% below MA20 today")
            if previous is None or previous > -2.1:
                raise SnapshotValidationError("TRIGGERED requires QQQ <= -2.1% below MA20 on prior session")
            if signal.get("qqq_up_day") is not True:
                raise SnapshotValidationError("TRIGGERED requires a positive QQQ day")
            if vix_change is None or vix_change >= 0:
                raise SnapshotValidationError("TRIGGERED requires VIX below its level five observed sessions earlier")
    legs = snapshot.get("legs")
    if not isinstance(legs, list):
        raise SnapshotValidationError("legs must be a list; use [] when no contracts were selected")
    if event_type in {"ENTRY", "EXIT"} and not legs:
        raise SnapshotValidationError(f"{event_type} requires exact contract legs")
    normalized = [_validate_leg(leg, snapshot_date, event_type, i) for i, leg in enumerate(legs)]
    quantities = [int(leg["qty"]) for leg in normalized]
    common = math.gcd(*quantities) if quantities else 1
    signature = [
        {**{k: leg[k] for k in ("contract_id", "right", "expiry", "strike", "position_side")},
         "ratio_qty": int(leg["qty"]) // common}
        for leg in normalized
    ]
    return {
        "status": "VALID_RESEARCH_SNAPSHOT",
        "snapshot_id": snapshot_id, "event_id": event_id, "strategy_id": strategy_id,
        "event_type": event_type, "snapshot_date": snapshot_date, "evidence": evidence,
        "contract_signature": signature, "leg_quote_statuses": [leg["quote_status"] for leg in normalized],
        "leg_count": len(normalized),
        "execution_enabled": False, "order_placed": False,
        "note": "Checks identity/provenance/field consistency; does not prove a fill or strategy edge.",
    }


def validate_directory(snapshot_dir: Path, shadow_root: Path) -> dict[str, Any]:
    files = sorted(snapshot_dir.rglob("*.json"))
    seen: dict[str, Path] = {}
    by_event: dict[tuple[str, str], list[tuple[dict[str, Any], Path]]] = {}
    records = []
    for path in files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise SnapshotValidationError(f"{path}: invalid JSON/UTF-8") from exc
        record = validate_snapshot(payload, shadow_root)
        if record["snapshot_id"] in seen:
            raise SnapshotValidationError(f"duplicate snapshot_id {record['snapshot_id']}: {seen[record['snapshot_id']]} and {path}")
        if path.stem != record["snapshot_id"]:
            raise SnapshotValidationError(f"{path}: filename stem must equal snapshot_id (immutable append-only file)")
        seen[record["snapshot_id"]] = path
        records.append(record)
        by_event.setdefault((record["event_id"], record["strategy_id"]), []).append((record, path))

    checks = 0
    for key, items in by_event.items():
        items.sort(key=lambda item: (item[0]["snapshot_date"], item[0]["snapshot_id"]))
        signal_date = None
        entry_date = None
        exit_date = None
        signature = None
        for record, _path in items:
            kind = record["event_type"]
            if kind == "SIGNAL":
                if signal_date is not None:
                    raise SnapshotValidationError(f"{key}: duplicate SIGNAL record")
                signal_date = record["snapshot_date"]
                signature = record["contract_signature"]
            elif kind == "ENTRY":
                if signal_date is None:
                    raise SnapshotValidationError(f"{key}: ENTRY requires a preceding frozen SIGNAL record")
                if entry_date is not None:
                    raise SnapshotValidationError(f"{key}: duplicate ENTRY record")
                if record["snapshot_date"] <= signal_date:
                    raise SnapshotValidationError(f"{key}: ENTRY must occur after signal date; no same-close fills")
                entry_date = record["snapshot_date"]
            elif kind == "BLOCKED_ENTRY":
                if signal_date is None:
                    raise SnapshotValidationError(f"{key}: BLOCKED_ENTRY requires a preceding SIGNAL record")
                if record["snapshot_date"] <= signal_date:
                    raise SnapshotValidationError(f"{key}: entry attempt must occur after signal date")
            elif kind in {"MARK", "MISSING_MARK", "EXIT", "BLOCKED_EXIT", "CENSORED"}:
                if entry_date is None:
                    raise SnapshotValidationError(f"{key}: {kind} cannot precede ENTRY")
            if kind == "EXIT":
                if exit_date is not None:
                    raise SnapshotValidationError(f"{key}: duplicate EXIT record")
                if record["snapshot_date"] < entry_date:
                    raise SnapshotValidationError(f"{key}: EXIT precedes ENTRY")
                exit_date = record["snapshot_date"]
            if kind in {"ENTRY", "MARK", "MISSING_MARK", "EXIT", "BLOCKED_EXIT", "CENSORED"}:
                current_signature = record["contract_signature"]
                if signature is None:
                    signature = current_signature
                elif signature != current_signature:
                    raise SnapshotValidationError(f"{key}: contract IDs/legs changed; silent substitution is forbidden")
            checks += 1
    return {
        "status": "VALID_APPEND_ONLY_SHADOW_LEDGER", "snapshots_validated": len(records),
        "event_strategy_pairs": len(by_event), "unique_snapshot_ids": len(seen),
        "event_records_checked": checks, "order_execution_count": 0,
        "note": "Missing quotes remain explicit; no interpolation, order placement or execution is performed.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--snapshot-dir", type=Path)
    parser.add_argument("--root", type=Path, required=True, help="Shadow-test root; evidence paths resolve relative to it.")
    args = parser.parse_args()
    if bool(args.snapshot) == bool(args.snapshot_dir):
        parser.error("provide exactly one of --snapshot or --snapshot-dir")
    if args.snapshot:
        payload = json.loads(args.snapshot.read_text(encoding="utf-8"))
        result = validate_snapshot(payload, args.root)
    else:
        result = validate_directory(args.snapshot_dir, args.root)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
