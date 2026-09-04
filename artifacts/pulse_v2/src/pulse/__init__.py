"""PULSE v2 reference implementation.

Not a strategy searcher. Unit = PulseEvent.
Evolution / Capital / FINAL_OOS / LIVE remain locked.
"""

from .gates import GateLockedError, LOCKS
from .splits import Split, assign_split
from .event import PulseEvent, Verdict
from .engine import PulseV2Engine

__all__ = [
    "GateLockedError",
    "LOCKS",
    "Split",
    "assign_split",
    "PulseEvent",
    "Verdict",
    "PulseV2Engine",
]
