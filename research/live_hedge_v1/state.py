from __future__ import annotations

import json
import os
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
    "last_positions": {},
    "last_target_stack": None,
    "last_risk_score": None,
}


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
            if "schema_version" not in raw:
                state["schema_version"] = 1
        if state.get("schema_version", 1) < SCHEMA_VERSION:
            state["schema_version"] = SCHEMA_VERSION
            state.setdefault("campaign", json.loads(json.dumps(DEFAULT_STATE["campaign"])))
            state.setdefault("active_ticket", None)
            state.setdefault("ticket_sequence", 0)
            state.setdefault("campaign_sequence", 0)
            state.setdefault("last_positions", {})
            state.setdefault("last_target_stack", None)
            state.setdefault("last_risk_score", None)
        state["schema_version"] = SCHEMA_VERSION
        return state

    def save(self, state: Dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
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
        event = {
            "event_id": f"E-{now.replace(':','').replace('-','').replace('.','')}-{state.get('ticket_sequence',0):04d}",
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
