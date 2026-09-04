from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Union


DateLike = Union[str, date, datetime]


def _to_date(x: DateLike) -> date:
    if isinstance(x, datetime):
        return x.date()
    if isinstance(x, date):
        return x
    return date.fromisoformat(str(x)[:10])


@dataclass(frozen=True)
class Split:
    name: str
    may_tune: bool
    may_claim_oos: bool
    evidence_tag: str


TRAIN = Split("TRAIN", True, False, "Observed")
VALIDATION = Split("VALIDATION", True, False, "Observed")
CRISIS_STUDY = Split("CRISIS_STUDY", False, False, "Observed")
UNPROVEN_OOS = Split("UNPROVEN_OOS", False, False, "Unproven")
FROZEN_OOS = Split("FROZEN_OOS", False, True, "Frozen")
SHADOW = Split("SHADOW", False, False, "Hypothetical")
LIVE = Split("LIVE", False, False, "LiveLocked")


def assign_split(d: DateLike, *, seen_by_tuning: bool = False) -> Split:
    """OOS is not OOS because it is named OOS.

    2023-2026 stays UNPROVEN_OOS until a protocol_hash is proven locked
    before 2023-01-01 with no post-hoc threshold edits.
    """
    x = _to_date(d)
    if seen_by_tuning and x >= date(2023, 1, 1):
        return UNPROVEN_OOS
    if x <= date(2015, 12, 31):
        return TRAIN
    if x <= date(2019, 12, 31):
        return VALIDATION
    if x <= date(2022, 12, 31):
        return CRISIS_STUDY
    if x <= date(2026, 9, 3):
        return UNPROVEN_OOS
    return UNPROVEN_OOS


def assert_not_frozen(split: Split) -> None:
    if split.name == "FROZEN_OOS":
        raise AssertionError("FROZEN_OOS does not exist until protocol lock proof")
