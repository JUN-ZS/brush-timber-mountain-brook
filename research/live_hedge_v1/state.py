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
    "campaign": {
        "id": None,
        "state": "IDLE",
        "far_code": None,
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
        return state

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
        with self.events_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")

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
