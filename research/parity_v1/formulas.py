"""Side-by-side formula mirrors for research vs live parity.

Citations refer to source files at HEAD of feat/operator-desk-v2-20261001.
Do NOT invent alpha — only re-state existing logic for isolated comparison.

Research pick_*/target_* are re-implemented here (byte-logic match) so tests do not
require duckdb (research engine imports duckdb at module import time).

Live gamma baseline mirrors the real engine helper (prefer import over stale copy).
"""
from __future__ import annotations

import math
from typing import Optional, Sequence

import numpy as np
import pandas as pd

from research.live_hedge_v1.engine import gamma_baseline_from_history as live_gamma_baseline_from_history

# Constants from research/qqq_dynamic_near_long_state_engine_v22_930c949.py
N_SHORT = 10
LONG_DELTA = 0.50
MAX_STACK = 5


def research_gamma_baseline_series(gamma_spot: Sequence[float]) -> pd.Series:
    """LOCKED research engine formula.

    Source: research/qqq_dynamic_near_long_state_engine_v22_930c949.py:482
        fqd["gamma_baseline"] = fqd["gamma_spot"].shift(1).rolling(20, min_periods=5).median()
    """
    s = pd.Series(list(gamma_spot), dtype="float64")
    return s.shift(1).rolling(20, min_periods=5).median()


def live_gamma_walk_baselines(values: Sequence[Optional[float]]) -> list[Optional[float]]:
    """Simulate live cycle: baseline from prior history, then append current value.

    History values should be gamma_spot (= abs(gamma)*spot) to match run_live_desk.
    """
    history: list[float] = []
    out: list[Optional[float]] = []
    for v in values:
        out.append(live_gamma_baseline_from_history(history))
        if v is None:
            continue
        try:
            if isinstance(v, float) and math.isnan(v):
                continue
            if pd.isna(v):
                continue
        except (TypeError, ValueError):
            pass
        history.append(abs(float(v)))
        history = history[-20:]
    return out


def research_gamma_spot_from_gamma_and_spot(
    gamma: Sequence[Optional[float]], spot: Sequence[float]
) -> pd.Series:
    """Research gamma_spot construction (has_gamma path). Lines 476-477."""
    g = pd.Series(list(gamma), dtype="float64")
    s = pd.Series(list(spot), dtype="float64")
    return g.abs() * s


def research_pick_far(ch: pd.DataFrame, spot: float, dte_target: int, delta_target: float):
    """Exact logic from qqq_dynamic...py pick_far (lines 94-127)."""
    if ch is None or ch.empty:
        return None
    g = ch[
        (ch.strike > float(spot))
        & ch.bid.notna() & ch.ask.notna() & ch.delta.notna()
        & (ch.ask >= ch.bid) & (ch.bid >= 0)
    ].copy()
    if g.empty:
        return None
    g["dte"] = (g.expiration - g.date).dt.days
    g = g[(g.dte >= 60) & (g.dte <= 210)]
    if g.empty:
        return None
    exp_score = g.groupby("expiration", as_index=False).agg(
        dte=("dte", "first"), volume=("volume", "sum")
    )
    exp_score["err"] = (exp_score.dte - dte_target).abs()
    ex = exp_score.sort_values(["err", "volume"], ascending=[True, False]).iloc[0].expiration
    z = g[g.expiration == ex].copy()
    z["derr"] = (z.delta.abs() - delta_target).abs()
    z = z.sort_values(["derr", "volume", "strike"], ascending=[True, False, True])
    r = z.iloc[0]
    out = {
        "cid": str(r.contract_id),
        "strike": float(r.strike),
        "delta": float(r.delta),
        "expiry": pd.Timestamp(r.expiration),
        "entry_bid": float(r.bid),
        "entry_ask": float(r.ask),
    }
    if "gamma" in r.index and pd.notna(r["gamma"]):
        out["gamma"] = float(r["gamma"])
    return out


def research_pick_near(ch: pd.DataFrame, spot: float, target_dte: int):
    """Exact logic from qqq_dynamic...py pick_near (lines 130-163)."""
    if ch is None or ch.empty:
        return None
    g = ch[
        (ch.strike <= float(spot) * 1.02)
        & ch.bid.notna() & ch.ask.notna() & ch.delta.notna()
        & (ch.ask >= ch.bid) & (ch.bid >= 0)
    ].copy()
    if g.empty:
        return None
    g["dte"] = (g.expiration - g.date).dt.days
    g = g[(g.dte >= 7) & (g.dte <= 35)]
    if g.empty:
        return None

    exp_score = g.groupby("expiration", as_index=False).agg(
        dte=("dte", "first"), volume=("volume", "sum")
    )
    exp_score["err"] = (exp_score.dte - target_dte).abs()
    ex = exp_score.sort_values(["err", "volume"], ascending=[True, False]).iloc[0].expiration

    z = g[(g.expiration == ex) & (g.strike <= float(spot) * 1.01)].copy()
    if z.empty:
        return None
    z["derr"] = (z.delta.abs() - LONG_DELTA).abs()
    z = z.sort_values(["derr", "volume", "strike"], ascending=[True, False, True])
    r = z.iloc[0]
    return {
        "cid": str(r.contract_id),
        "strike": float(r.strike),
        "delta": float(r.delta),
        "expiry": pd.Timestamp(r.expiration),
        "entry_ask": float(r.ask),
    }


def research_target_from_state(
    far_delta_abs: float,
    distance_pct: float,
    gamma_rel: float,
    delta_jump: float,
    coverage_mult: float,
):
    """Exact logic from qqq_dynamic...py target_from_state (lines 272-318)."""
    if far_delta_abs < 0.04:
        dscore = 1
    elif far_delta_abs < 0.06:
        dscore = 2
    elif far_delta_abs < 0.08:
        dscore = 3
    elif far_delta_abs < 0.10:
        dscore = 4
    else:
        dscore = 5

    if distance_pct > 0.10:
        xscore = 1
    elif distance_pct > 0.07:
        xscore = 2
    elif distance_pct > 0.04:
        xscore = 3
    elif distance_pct > 0.02:
        xscore = 4
    else:
        xscore = 5

    if gamma_rel < 1.20 and delta_jump < 0.01:
        gscore = 1
    elif gamma_rel < 1.50 and delta_jump < 0.02:
        gscore = 2
    else:
        gscore = 3

    base = int(math.ceil((coverage_mult * N_SHORT * far_delta_abs) / LONG_DELTA))
    composite = 0.50 * dscore + 0.30 * xscore + 0.20 * gscore
    boost = 2 if composite >= 4.2 else 1 if composite >= 3.2 else 0

    return max(1, min(MAX_STACK, base + boost)), {
        "dscore": dscore,
        "xscore": xscore,
        "gscore": gscore,
        "risk_score": composite,
    }
