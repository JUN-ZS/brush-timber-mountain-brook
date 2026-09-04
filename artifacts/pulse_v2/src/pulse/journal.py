from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class JournalRow:
    event_id: str
    event_class: str
    signal_fingerprint: str
    market_state_snapshot: dict
    entry_reason: str
    expected_continuation: str
    expected_duration: str
    expected_upside: float | None
    expected_downside: float | None
    execution_family: str
    instrument: str
    fill: dict
    actual_path: dict
    MAE: float | None
    MFE: float | None
    harvest_actions: list[dict] = field(default_factory=list)
    runner_duration: int | None = None
    exit_reason: str | None = None
    slippage: float | None = None
    liquidity: str | None = None
    prediction_error: float | None = None
    data_split: str = ""
    protocol_hash: str | None = None
    evidence_tag: str = "Hypothetical"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def prediction_error(expected_upside: float | None, mfe: float | None) -> float | None:
    if expected_upside is None or mfe is None:
        return None
    return float(mfe - expected_upside)
