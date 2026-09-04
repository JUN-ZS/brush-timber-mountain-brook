from __future__ import annotations

"""State-transition radar on the EVB panel.

Does not define 'momentum' as RSI+volume+accel.
It only labels states from Observed lagged fields, then emits transitions.

Lookahead columns fwd* are never inputs.
VXX nulls disable VXX families instead of imputing.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

LOOKAHEAD = ("fwd5", "fwd10", "fwd15", "fwd20")


def assert_no_lookahead(columns: list[str]) -> None:
    bad = [c for c in columns if c in LOOKAHEAD]
    if bad:
        raise ValueError(f"LOOKAHEAD_FORBIDDEN:{bad}")


def _z(s: pd.Series, win: int = 60) -> pd.Series:
    mu = s.rolling(win, min_periods=max(20, win // 3)).mean()
    sd = s.rolling(win, min_periods=max(20, win // 3)).std()
    return (s - mu) / sd.replace(0, np.nan)


def enrich_states(df: pd.DataFrame) -> pd.DataFrame:
    assert_no_lookahead([c for c in df.columns])
    out = df.copy()
    # price state from already-lagged / same-bar derived fields that exist
    ret1 = out["QQQ_ret1"]
    out["price_state"] = np.select(
        [
            (ret1 > 0.012) & (out.get("mom2_improve", 0) == 1),
            (ret1 < -0.012),
            out.get("persist_below_MA20", 0) >= 5,
            out["QQQ_over_MA20"] > 1.0,
        ],
        ["ACCEL_UP", "ACCEL_DOWN", "PERSIST_WEAK", "ABOVE_MA20"],
        default="RANGE",
    )
    rv_z = _z(out["RV20"])
    out["vol_state"] = np.select(
        [rv_z > 1.5, rv_z < -1.0, out.get("backwardation", 0) == 1],
        ["EXPANSION", "COMPRESSION", "BACKWARDATION"],
        default="NORMAL",
    )
    qqq_r = out["QQQ"].pct_change()
    spy_r = out["SPY"].pct_change()
    rel = (qqq_r - spy_r).rolling(5, min_periods=3).sum()
    out["rel_state"] = np.select(
        [rel > 0.015, rel < -0.015],
        ["QQQ_LEAD", "QQQ_LAG"],
        default="IN_LINE",
    )
    tlt = out["TLT"].pct_change(5)
    out["cross_rates"] = np.select(
        [tlt > 0.02, tlt < -0.02],
        ["DURATION_BID", "DURATION_OFF"],
        default="DURATION_FLAT",
    )
    vpz = out.get("VolPremium_z")
    out["cross_vol"] = np.select(
        [vpz > 1.2, vpz < -1.2],
        ["VOL_PREMIUM_RICH", "VOL_PREMIUM_CHEAP"],
        default="VOL_NEUTRAL",
    )
    # liquidity proxy from volume z
    vz = _z(np.log1p(out["QQQ_Volume"]))
    out["liq_state"] = np.select(
        [vz < -1.3, vz > 1.3],
        ["THIN", "HEAVY"],
        default="NORMAL",
    )
    vix = out["VIX"]
    out["regime"] = np.select(
        [vix >= 30, vix >= 20, out["QQQ_over_MA50"] < 1.0],
        ["CRISIS_VOL", "STRESS_VOL", "RISK_OFF_TREND"],
        default="RISK_ON",
    )
    out["vxx_ok"] = out["VXX"].notna()
    return out


@dataclass
class Transition:
    i: int
    bar_date: str
    skeleton: str
    direction: str
    search_level: str
    strength: float
    states: dict
    missing: list[str]
    observed: list[str]
    what_changed: str
    why_unusual: str


def detect_transitions(df: pd.DataFrame) -> list[Transition]:
    """Emit transitions. Thresholds here are RESEARCH HYPOTHESES, not champions.

    Changing them after seeing 2023-2026 marks that window seen_by_tuning.
    """
    rows: list[Transition] = []
    prev = df.shift(1)
    for i in range(1, len(df)):
        r = df.iloc[i]
        p = prev.iloc[i]
        if pd.isna(r["QQQ"]) or pd.isna(p["QQQ"]):
            continue
        changed = []
        if r["price_state"] != p["price_state"]:
            changed.append(f"price:{p['price_state']}->{r['price_state']}")
        if r["vol_state"] != p["vol_state"]:
            changed.append(f"vol:{p['vol_state']}->{r['vol_state']}")
        if r["rel_state"] != p["rel_state"]:
            changed.append(f"rel:{p['rel_state']}->{r['rel_state']}")
        if r["cross_vol"] != p["cross_vol"]:
            changed.append(f"xvol:{p['cross_vol']}->{r['cross_vol']}")
        if not changed:
            continue
        # only keep "sudden" composites — at least price+one other, or vol expansion from compression
        sudden = False
        skeleton = None
        direction = "FLAT"
        level = "SINGLE"
        if r["price_state"] in {"ACCEL_UP", "ACCEL_DOWN"} and (
            r["vol_state"] != p["vol_state"] or r["rel_state"] != p["rel_state"]
        ):
            sudden = True
            direction = "UP" if r["price_state"] == "ACCEL_UP" else "DOWN"
            skeleton = f"PRICE_{r['price_state']}+VOL_{r['vol_state']}+REL_{r['rel_state']}"
            level = "COMPOSITE"
        elif p["vol_state"] == "COMPRESSION" and r["vol_state"] == "EXPANSION":
            sudden = True
            direction = "VOL"
            skeleton = "VOL_COMPRESSION_TO_EXPANSION"
            level = "CROSS"
        elif r["rel_state"] != p["rel_state"] and r["rel_state"] != "IN_LINE":
            sudden = True
            direction = "REL_UP" if r["rel_state"] == "QQQ_LEAD" else "REL_DOWN"
            skeleton = f"PAIR_QQQ_SPY_{r['rel_state']}"
            level = "PAIR"
        if not sudden:
            continue
        missing = []
        if not bool(r["vxx_ok"]):
            missing.append("VXX")
        strength = float(min(3.0, abs(r["QQQ_ret1"]) / 0.01 + (1.0 if r["vol_state"] == "EXPANSION" else 0.0)))
        rows.append(
            Transition(
                i=i,
                bar_date=str(r["Date"])[:10],
                skeleton=skeleton,
                direction=direction,
                search_level=level,
                strength=strength,
                states={
                    "price": r["price_state"],
                    "vol": r["vol_state"],
                    "rel": r["rel_state"],
                    "regime": r["regime"],
                    "liq": r["liq_state"],
                    "cross_vol": r["cross_vol"],
                    "cross_rates": r["cross_rates"],
                },
                missing=missing,
                observed=["QQQ", "SPY", "VIX", "QQQ_Volume", "RV20"],
                what_changed=";".join(changed),
                why_unusual=skeleton,
            )
        )
    return rows
