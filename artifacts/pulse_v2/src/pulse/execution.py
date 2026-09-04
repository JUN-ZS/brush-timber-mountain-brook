from __future__ import annotations

"""Execution families are hypotheses. NEXT_OPEN is not the system default."""

from dataclasses import dataclass

import pandas as pd


FAMILIES = ("IMMEDIATE", "DELAYED", "NEXT_OPEN", "PULLBACK", "CONFIRMATION")


@dataclass
class Fill:
    family: str
    fill_date: str | None
    fill_price: float | None
    missed_move: float | None
    status: str
    honesty: str


def _px(row: pd.Series, field: str) -> float | None:
    v = row.get(field)
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    return float(v)


def propose_fills(df: pd.DataFrame, event_i: int) -> list[Fill]:
    """Daily bar honesty:

    If the transition uses same-day close features, same-day close fill is
    lookahead. Honest immediate = next session open.
    """
    n = len(df)
    ev = df.iloc[event_i]
    close = _px(ev, "QQQ")
    out: list[Fill] = []

    # IMMEDIATE: next bar open (honest). Same-day close would be leak.
    if event_i + 1 < n:
        nxt = df.iloc[event_i + 1]
        px = _px(nxt, "QQQ_Open")
        missed = None if close is None or px is None else (px / close - 1.0)
        out.append(Fill("IMMEDIATE", str(nxt["Date"])[:10], px, missed, "HYPOTHESIS", "next_open_is_honest_immediate"))
    else:
        out.append(Fill("IMMEDIATE", None, None, None, "NO_FILL", "end_of_panel"))

    # NEXT_OPEN: same as honest immediate on this panel — keep distinct label
    # so later intraday data can split them. Do not treat as champion.
    out.append(
        Fill(
            "NEXT_OPEN",
            out[-1].fill_date if out else None,
            out[-1].fill_price if out else None,
            out[-1].missed_move if out else None,
            "EXECUTION_HYPOTHESIS",
            "not_system_default",
        )
    )

    # DELAYED: wait one extra session, fill at that open
    if event_i + 2 < n:
        d = df.iloc[event_i + 2]
        px = _px(d, "QQQ_Open")
        missed = None if close is None or px is None else (px / close - 1.0)
        out.append(Fill("DELAYED", str(d["Date"])[:10], px, missed, "HYPOTHESIS", "wait_one_session"))
    else:
        out.append(Fill("DELAYED", None, None, None, "NO_FILL", "end_of_panel"))

    # PULLBACK: next 3 sessions, fill if low revisits event close * 0.997
    filled = None
    if close is not None:
        for j in range(1, 4):
            if event_i + j >= n:
                break
            row = df.iloc[event_i + j]
            lo = _px(row, "QQQ_Low")
            if lo is not None and lo <= close * 0.997:
                px = min(close * 0.997, _px(row, "QQQ_Open") or lo)
                filled = Fill("PULLBACK", str(row["Date"])[:10], px, px / close - 1.0, "HYPOTHESIS", "limit_near_event_close")
                break
    out.append(filled or Fill("PULLBACK", None, None, None, "NO_FILL", "no_pullback_in_3"))

    # CONFIRMATION: require next day continuation then fill following open
    if event_i + 2 < n:
        d1 = df.iloc[event_i + 1]
        d2 = df.iloc[event_i + 2]
        ok = False
        if ev.get("price_state") == "ACCEL_UP" and float(d1["QQQ"]) > float(ev["QQQ"]):
            ok = True
        if ev.get("price_state") == "ACCEL_DOWN" and float(d1["QQQ"]) < float(ev["QQQ"]):
            ok = True
        if ok:
            px = _px(d2, "QQQ_Open")
            missed = None if close is None or px is None else px / close - 1.0
            out.append(Fill("CONFIRMATION", str(d2["Date"])[:10], px, missed, "HYPOTHESIS", "wait_continuation"))
        else:
            out.append(Fill("CONFIRMATION", None, None, None, "NO_FILL", "no_confirmation"))
    else:
        out.append(Fill("CONFIRMATION", None, None, None, "NO_FILL", "end_of_panel"))
    return out
