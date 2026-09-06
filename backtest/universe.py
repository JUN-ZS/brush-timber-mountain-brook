"""Read the V2.2 Observed EOD universe. Used only as DERIVED fallback, never as LIVE."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
UNIVERSE_PATH = ROOT / "src" / "data" / "universe.json"

DAYS = 252


def load_universe() -> dict:
    with UNIVERSE_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def last_close(sym: str, u: Optional[dict] = None) -> Optional[float]:
    u = u or load_universe()
    arr = (u.get("c") or {}).get(sym) or []
    for v in reversed(arr):
        if isinstance(v, (int, float)) and v == v and v > 0:
            return float(v)
    return None


def last_date(u: Optional[dict] = None) -> Optional[str]:
    u = u or load_universe()
    dates = u.get("dates") or []
    return dates[-1] if dates else None


def closes(sym: str, n: int = 80, u: Optional[dict] = None) -> list[float]:
    u = u or load_universe()
    arr = (u.get("c") or {}).get(sym) or []
    out: list[float] = []
    for v in arr:
        if isinstance(v, (int, float)) and v == v and v > 0:
            out.append(float(v))
    return out[-n:]


def stdev(xs: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / len(xs))


def realized_vol(prices: list[float], window: int = 20) -> Optional[float]:
    if len(prices) < window + 1:
        return None
    rets = []
    sl = prices[-(window + 1) :]
    for i in range(1, len(sl)):
        if sl[i - 1] > 0:
            rets.append(sl[i] / sl[i - 1] - 1.0)
    if len(rets) < 2:
        return None
    return stdev(rets) * math.sqrt(DAYS)


def momentum(prices: list[float], lookback: int) -> Optional[float]:
    if len(prices) <= lookback or prices[-1 - lookback] <= 0:
        return None
    return prices[-1] / prices[-1 - lookback] - 1.0
