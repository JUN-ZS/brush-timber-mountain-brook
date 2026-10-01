from __future__ import annotations

import json
import os
import tempfile
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Optional

SCHEMA_VERSION = 2

DEFAULT_STATE: Dict[str, Any] = {
    "schema_version": SCHEMA_VERSION,
    "far_code": None,
    "far_delta": None,
    "gamma_history": [],
    "gamma_history_schema": 2,
    "gamma_history_unit": "gamma_spot",
    "campaign": {
        "id": None,
        "state": "IDLE",
        "far_code": None,
        "managed_far_qty": None,
        "far_ownership_source": None,
        "far_ownership_ticket_id": None,
        "started_at": None,
        "last_transition_at": None,
        "target_stack": None,
    },
    "active_ticket": None,
    "ticket_sequence": 0,
    "campaign_sequence": 0,
    "event_sequence": 0,
    "last_positions": {},
    "last_target_stack": None,
    "last_risk_score": None,
    "lots": [],
}


_LIVE_THREAD_LOCKS = {}
_LIVE_THREAD_LOCKS_GUARD = threading.Lock()


def _live_lock_path(path: Path) -> Path:
    key = __import__("hashlib").sha256(str(path.resolve()).encode("utf-8")).hexdigest()
    return Path(tempfile.gettempdir()) / f"qqq-live-desk-{key}.lock"


@contextmanager
def live_desk_mutation_lock(path: str | Path):
    """Serialize one live desk state across duplicate watcher processes."""
    lock_path = _live_lock_path(Path(path))
    key = str(lock_path)
    with _LIVE_THREAD_LOCKS_GUARD:
        thread_lock = _LIVE_THREAD_LOCKS.setdefault(key, threading.Lock())
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


class StateStore:
    def __init__(self, path="research/live_hedge_v1/state.json", events_path=None):
        self.path = Path(path)
        self.events_path = Path(events_path) if events_path else self.path.with_name("events.jsonl")

    def load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return json.loads(json.dumps(DEFAULT_STATE))
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        state = json.loads(json.dumps(DEFAULT_STATE))
        if isinstance(raw, dict):
            state.update(raw)
        if state.get("schema_version", 1) < SCHEMA_VERSION:
            state["schema_version"] = SCHEMA_VERSION
        state.setdefault("campaign", json.loads(json.dumps(DEFAULT_STATE["campaign"])))
        state.setdefault("active_ticket", None)
        state.setdefault("ticket_sequence", 0)
        state.setdefault("campaign_sequence", 0)
        state.setdefault("event_sequence", 0)
        state.setdefault("last_positions", {})
        state.setdefault("last_target_stack", None)
        state.setdefault("last_risk_score", None)
        state.setdefault("lots", [])
        state["schema_version"] = SCHEMA_VERSION
        self._recover_from_events(state)
        return state

    def _read_events(self) -> list[dict[str, Any]]:
        if not self.events_path.exists():
            return []
        rows = []
        lines = self.events_path.read_text(encoding="utf-8").splitlines()
        for idx, line in enumerate(lines):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                # A crash can leave only the final append partially written.
                # Earlier complete events remain usable for deterministic recovery.
                if idx == len(lines) - 1:
                    break
                raise

        return [row for row in rows if isinstance(row, dict)]

    @staticmethod
    def _numeric_suffix(value: Any, width: int = 0) -> int:
        raw = str(value or "")
        if width:
            tail = raw[-width:]
            return int(tail) if tail.isdigit() else 0
        digits = ""
        for ch in reversed(raw):
            if ch.isdigit():
                digits = ch + digits
            elif digits:
                break
        return int(digits) if digits else 0

    @staticmethod
    def _apply_far_execution_evidence(campaign: Dict[str, Any], ticket: Dict[str, Any], fill_rows) -> None:
        """Update managed far qty from cumulative broker-confirmed ticket fills."""
        if not campaign or not ticket:
            return
        far_code = str(campaign.get("far_code") or "").upper()
        if not far_code:
            return
        for fill in fill_rows or []:
            code = str(fill.get("code") or "").upper()
            if code != far_code:
                continue
            if str(fill.get("expected_side") or "").upper() != "SHORT":
                continue
            qty = int(float(fill.get("qty") or 0))
            if qty <= 0:
                continue
            side = str(fill.get("side") or "").upper()
            leg = next(
                (
                    x for x in ticket.get("legs", []) or []
                    if str(x.get("code") or "").upper() == code
                    and str(x.get("side") or "").upper() == side
                    and str(x.get("expected_side") or "").upper() == "SHORT"
                ),
                None,
            )
            if leg is None:
                continue
            before = int(float(leg.get("before_qty") or 0))
            if side == "SELL":
                campaign["managed_far_qty"] = before + qty
            elif side == "BUY":
                campaign["managed_far_qty"] = max(0, before - qty)
            else:
                continue
            campaign["far_ownership_source"] = "BROKER_EXECUTION_EVIDENCE"
            campaign["far_ownership_ticket_id"] = ticket.get("ticket_id")

    def _recover_from_events(self, state: Dict[str, Any]) -> None:
        """Repair an unsaved state cache from the durable live event stream."""
        events = self._read_events()
        if not events:
            return

        latest_ticket = None
        ticket_terminal = None
        campaign = state.setdefault("campaign", {})

        for event in events:
            et = str(event.get("type", "")).upper()
            payload = event.get("payload") or {}

            if et == "CAMPAIGN_TRANSITION":
                to_state = payload.get("to")
                campaign["state"] = to_state
                campaign["last_transition_at"] = event.get("timestamp")
                if to_state == "IDLE":
                    campaign["id"] = None
                    campaign["far_code"] = None
                    campaign["managed_far_qty"] = None
                    campaign["far_ownership_source"] = None
                    campaign["far_ownership_ticket_id"] = None
                    campaign["far_ownership_source"] = None
                    campaign["far_ownership_ticket_id"] = None

            elif et == "CAMPAIGN_ADOPTED_EXISTING_FAR":
                if event.get("campaign_id"):
                    campaign["id"] = event.get("campaign_id")
                campaign["state"] = "OPEN"
                campaign["started_at"] = campaign.get("started_at") or event.get("timestamp")
                if payload.get("far_code"):
                    campaign["far_code"] = payload["far_code"]
                if payload.get("managed_far_qty") is not None:
                    campaign["managed_far_qty"] = payload["managed_far_qty"]
                elif payload.get("qty") is not None:
                    campaign["managed_far_qty"] = payload["qty"]
                campaign["far_ownership_source"] = payload.get("ownership_source") or "EXPLICIT_ADOPTION"
                campaign["far_ownership_ticket_id"] = None

            elif et == "FAR_OWNERSHIP_REBASELINED":
                if event.get("campaign_id"):
                    campaign["id"] = event.get("campaign_id")
                if payload.get("far_code"):
                    campaign["far_code"] = payload["far_code"]
                if payload.get("managed_far_qty") is not None:
                    campaign["managed_far_qty"] = payload["managed_far_qty"]
                campaign["far_ownership_source"] = payload.get("ownership_source") or "EXPLICIT_REBASELINE"
                campaign["far_ownership_ticket_id"] = None

            elif et == "TICKET_ISSUED":
                latest_ticket = payload.get("ticket")
                ticket_terminal = None
                ticket = latest_ticket or {}
                if event.get("campaign_id"):
                    campaign["id"] = event.get("campaign_id")
                legs = ticket.get("legs", []) or []
                far_leg = next(
                    (
                        leg for leg in legs
                        if str(leg.get("expected_side", "")).upper() == "SHORT"
                        and leg.get("code")
                    ),
                    None,
                )
                if far_leg is not None:
                    campaign["far_code"] = far_leg.get("code")
                    if campaign.get("managed_far_qty") is None:
                        campaign["managed_far_qty"] = int(far_leg.get("before_qty", 0) or 0)
                        campaign["far_ownership_source"] = "TICKET_BASELINE"
                    campaign["far_ownership_ticket_id"] = ticket.get("ticket_id")
                if campaign.get("state") == "IDLE":
                    campaign["state"] = "OPEN"
                campaign["started_at"] = campaign.get("started_at") or ticket.get("issued_at")

            elif et in {"TICKET_PARTIAL_PROGRESS", "TICKET_WAITING_EXECUTION_EVIDENCE"}:
                if latest_ticket is not None:
                    latest_ticket = json.loads(json.dumps(latest_ticket))
                    latest_ticket["status"] = "PARTIAL"
                    if et == "TICKET_PARTIAL_PROGRESS" and payload.get("fill") is not None:
                        latest_ticket["fill"] = payload.get("fill")
                        self._apply_far_execution_evidence(
                            campaign,
                            latest_ticket,
                            payload.get("fill"),
                        )

            elif et == "MANUAL_POSITION_CHANGE":
                if latest_ticket is not None:
                    evidence = payload.get("broker_execution_evidence") or {}
                    fills = []
                    for key, row in evidence.items():
                        if not isinstance(row, dict) or ":" not in str(key):
                            continue
                        qty = int(float(row.get("evidence_qty") or 0))
                        if qty <= 0:
                            continue
                        side, code = str(key).split(":", 1)
                        side = side.upper()
                        code = code.upper()
                        fills.append({
                            "code": code,
                            "side": side,
                            "expected_side": next(
                                (
                                    leg.get("expected_side")
                                    for leg in latest_ticket.get("legs", []) or []
                                    if str(leg.get("code") or "").upper() == code
                                    and str(leg.get("side") or "").upper() == side
                                ),
                                None,
                            ),
                            "qty": qty,
                        })
                    self._apply_far_execution_evidence(campaign, latest_ticket, fills)

            elif et == "TICKET_FILLED":
                if latest_ticket is not None:
                    fills = payload.get("fill") or latest_ticket.get("fill") or []
                    self._apply_far_execution_evidence(campaign, latest_ticket, fills)
                ticket_terminal = et
                latest_ticket = None

            elif et in {
                "TICKET_SUPERSEDED",
                "REPRICE_TICKET_SUPERSEDED",
                "REPRICE_ORDER_TERMINAL",
                "REPRICE_ORDER_CANCELLED",
            }:
                ticket_terminal = et
                latest_ticket = None

        if latest_ticket is not None:
            current = state.get("active_ticket")
            if current is None or current.get("ticket_id") == latest_ticket.get("ticket_id"):
                state["active_ticket"] = latest_ticket
        elif ticket_terminal is not None:
            current = state.get("active_ticket")
            if current is not None:
                state["active_ticket"] = None

        state["campaign"] = campaign

        max_event_seq = max(
            (self._numeric_suffix(e.get("event_id"), 6) for e in events),
            default=0,
        )
        state["event_sequence"] = max(int(state.get("event_sequence", 0) or 0), max_event_seq)

        max_ticket_seq = max(
            (
                self._numeric_suffix(
                    e.get("payload", {}).get("ticket", {}).get("ticket_id"),
                    4,
                )
                for e in events
                if e.get("type") == "TICKET_ISSUED"
            ),
            default=0,
        )
        state["ticket_sequence"] = max(int(state.get("ticket_sequence", 0) or 0), max_ticket_seq)

        max_campaign_seq = max(
            (
                self._numeric_suffix(e.get("campaign_id"), 4)
                for e in events
                if e.get("campaign_id")
            ),
            default=0,
        )
        state["campaign_sequence"] = max(int(state.get("campaign_sequence", 0) or 0), max_campaign_seq)

    def save(self, state: Dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(state, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        os.replace(tmp, self.path)

    def append_event(self, event: Dict[str, Any]) -> None:
        self.events_path.parent.mkdir(parents=True, exist_ok=True)
        with self.events_path.open("a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")
            f.flush()
            os.fsync(f.fileno())

    def next_ticket_sequence(self, state: Dict[str, Any]) -> int:
        n = int(state.get("ticket_sequence", 0) or 0) + 1
        state["ticket_sequence"] = n
        return n

    def next_campaign_sequence(self, state: Dict[str, Any]) -> int:
        n = int(state.get("campaign_sequence", 0) or 0) + 1
        state["campaign_sequence"] = n
        return n

    def emit(
        self,
        state: Dict[str, Any],
        event_type: str,
        *,
        now: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        n = int(state.get("event_sequence", 0) or 0) + 1
        state["event_sequence"] = n
        event = {
            "event_id": f"E-{now.replace(':','').replace('-','').replace('.','')}-{n:06d}",
            "timestamp": now,
            "type": event_type,
            "campaign_id": (state.get("campaign") or {}).get("id"),
            "payload": payload or {},
        }
        self.append_event(event)
        return event

    def record_position_snapshot(self, state: Dict[str, Any], positions: Any) -> None:
        from .campaign import position_snapshot
        state["last_positions"] = position_snapshot(positions)
