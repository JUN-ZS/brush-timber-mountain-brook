from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class PathStats:
    holding_bars: int
    mae: float
    mfe: float
    time_to_mae: int | None
    time_to_mfe: int | None
    time_to_failure: int | None
    end_ret: float
    decayed: bool


def path_stats(df: pd.DataFrame, fill_i: int, direction: str, horizon: int = 10) -> PathStats | None:
    if fill_i < 0 or fill_i >= len(df):
        return None
    entry = float(df.iloc[fill_i]["QQQ_Open"] if pd.notna(df.iloc[fill_i]["QQQ_Open"]) else df.iloc[fill_i]["QQQ"])
    sign = 1.0 if direction in {"UP", "REL_UP"} else -1.0 if direction in {"DOWN", "REL_DOWN"} else 1.0
    mae = 0.0
    mfe = 0.0
    t_mae = None
    t_mfe = None
    t_fail = None
    end = 0.0
    decayed = False
    last_exc = 0.0
    bars = 0
    for k in range(0, horizon + 1):
        j = fill_i + k
        if j >= len(df):
            break
        hi = float(df.iloc[j]["QQQ_High"])
        lo = float(df.iloc[j]["QQQ_Low"])
        cl = float(df.iloc[j]["QQQ"])
        ret = (cl / entry - 1.0) * sign
        if sign > 0:
            fav = hi / entry - 1.0
            adv = lo / entry - 1.0
        else:
            fav = -(lo / entry - 1.0)
            adv = -(hi / entry - 1.0)
        if fav > mfe:
            mfe = fav
            t_mfe = k
        if adv < mae:
            mae = adv
            t_mae = k
        if t_fail is None and adv <= -0.02:
            t_fail = k
        if k >= 2 and fav < last_exc * 0.5 and last_exc > 0.01:
            decayed = True
        last_exc = fav
        end = ret
        bars = k
    return PathStats(bars, float(mae), float(mfe), t_mae, t_mfe, t_fail, float(end), decayed)


def harvest_plan(stats: PathStats, cost: float) -> dict:
    """Dynamic harvest. Fixed 25% is forbidden without path evidence."""
    if stats.mfe <= cost:
        return {
            "harvest_fraction": 1.0,
            "runner_allowed": False,
            "reason": "MFE_NOT_ABOVE_COST",
            "invalidation": "mfe<=cost",
        }
    r = stats.mfe / max(1e-6, abs(stats.mae) + cost)
    if stats.decayed:
        return {
            "harvest_fraction": 1.0,
            "runner_allowed": False,
            "reason": "DECAY",
            "invalidation": "excursion_gave_back_half",
        }
    if r >= 2.5 and stats.mfe >= 0.03:
        return {
            "harvest_fraction": 0.4,
            "runner_allowed": True,
            "reason": "STRONG_EXCURSION",
            "invalidation": "giveback_half_mfe",
        }
    if r >= 1.6:
        return {
            "harvest_fraction": 0.6,
            "runner_allowed": True,
            "reason": "ADEQUATE_ASYMMETRY",
            "invalidation": "mae_hits_-1R",
        }
    return {
        "harvest_fraction": 0.8,
        "runner_allowed": False,
        "reason": "WEAK_PATH",
        "invalidation": "no_runner_on_weak_path",
    }
