from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any


class Lifecycle(str, Enum):
    QUIET = "QUIET"
    STATE_TRANSITION = "STATE_TRANSITION"
    PULSE_EVENT = "PULSE_EVENT"
    ASYMMETRY_SCORE = "ASYMMETRY_SCORE"
    ENTRY_ELIGIBLE = "ENTRY_ELIGIBLE"
    REJECTED = "REJECTED"
    NO_TRADE = "NO_TRADE"
    ACTIVE = "ACTIVE"
    HARVESTING = "HARVESTING"
    RUNNER = "RUNNER"
    DECAY = "DECAY"
    EXIT = "EXIT"
    JOURNALED = "JOURNALED"
    ATTACKED = "ATTACKED"


class Verdict(str, Enum):
    UNTESTED = "UNTESTED"
    FALSE_PULSE = "FALSE_PULSE"
    FRAGILE = "FRAGILE"
    INSUFFICIENT_SAMPLE = "INSUFFICIENT_SAMPLE"
    HARD_FAIL = "HARD_FAIL"
    SURVIVING_EVENT = "SURVIVING_EVENT"
    RECURRING_CLASS = "RECURRING_CLASS"


MUST_ANSWER = (
    "what_changed",
    "why_unusual",
    "transition_strength",
    "typical_duration",
    "invalidation",
    "pre_confirmation_loss",
    "harvest_zones",
    "runner_rule",
    "death_rule",
)


@dataclass
class PulseEvent:
    event_id: str
    bar_date: str
    split: str
    search_level: str
    direction: str
    skeleton: str
    regime: str
    family_id: str
    what_changed: str
    why_unusual: str
    transition_strength: float
    states: dict[str, str]
    observed_fields: list[str]
    missing_fields: list[str]
    protocol_id: str = "pulse_capture.v2"
    protocol_hash: str | None = None
    seen_by_tuning: bool = False
    lifecycle: str = Lifecycle.PULSE_EVENT.value
    verdict: str = Verdict.UNTESTED.value
    typical_duration: str | None = None
    invalidation: str | None = None
    pre_confirmation_loss: float | None = None
    harvest_zones: list[float] = field(default_factory=list)
    runner_rule: str | None = None
    death_rule: str | None = None
    asymmetry: float | None = None
    evidence_tag: str = "Observed"
    notes: dict[str, Any] = field(default_factory=dict)

    def unanswered(self) -> list[str]:
        missing = []
        for k in MUST_ANSWER:
            v = getattr(self, k, None)
            if v is None or v == "" or v == []:
                missing.append(k)
        return missing

    def may_enter(self) -> tuple[bool, str]:
        if self.split in {"LIVE"}:
            return False, "LIVE_LOCKED"
        gaps = self.unanswered()
        if gaps:
            return False, "UNANSWERED:" + ",".join(gaps)
        if self.asymmetry is None or self.asymmetry < 1.6:
            return False, "ASYMMETRY_BELOW_GATE"
        if self.lifecycle in {Lifecycle.REJECTED.value, Lifecycle.NO_TRADE.value}:
            return False, self.lifecycle
        return True, "ENTRY_ELIGIBLE"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
