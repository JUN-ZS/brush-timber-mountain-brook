from __future__ import annotations

import pandas as pd

from research.qqq_v22_locked_oos_family_v2 import (
    clip_quote_maps_to_window,
    mask_campaigns,
)


def test_oos_mask_clips_post_window_data_but_preserves_pre_window_lookback_columns():
    full = pd.DataFrame(
        {
            "date": pd.to_datetime([
                "2025-12-14",
                "2025-12-15",
                "2025-12-16",
            ]),
            "close": [500.0, 501.0, 502.0],
            "dma200": [450.0, 451.0, 452.0],
            "signal": [True, True, True],
        }
    )
    out = mask_campaigns(
        full,
        pd.Timestamp("2025-12-14"),
        pd.Timestamp("2025-12-15"),
    )
    assert list(out["date"].dt.strftime("%Y-%m-%d")) == [
        "2025-12-14", "2025-12-15"
    ]
    assert bool(out["signal"].iloc[-1]) is True
    assert "2025-12-16" not in set(out["date"].dt.strftime("%Y-%m-%d"))




def test_oos_mask_keeps_pre_window_rows_for_lookbacks():
    full = pd.DataFrame(
        {
            "date": pd.to_datetime([
                "2025-12-01",
                "2025-12-13",
                "2025-12-14",
                "2025-12-16",
            ]),
            "close": [490.0, 499.0, 500.0, 502.0],
            "dma200": [440.0, 449.0, 450.0, 452.0],
            "signal": [False, False, True, True],
        }
    )
    out = mask_campaigns(
        full,
        pd.Timestamp("2025-12-14"),
        pd.Timestamp("2025-12-15"),
    )
    assert list(out["date"].dt.strftime("%Y-%m-%d")) == [
        "2025-12-01", "2025-12-13", "2025-12-14"
    ]
    assert out["signal"].tolist() == [False, False, True]


def test_oos_mask_does_not_create_signals_outside_declared_window():
    full = pd.DataFrame(
        {
            "date": pd.to_datetime([
                "2025-12-13",
                "2025-12-14",
                "2025-12-15",
                "2025-12-16",
            ]),
            "close": [499.0, 500.0, 501.0, 502.0],
            "dma200": [449.0, 450.0, 451.0, 452.0],
            "signal": [False, True, True, True],
        }
    )
    out = mask_campaigns(
        full,
        pd.Timestamp("2025-12-14"),
        pd.Timestamp("2025-12-15"),
    )
    assert list(out["date"].dt.strftime("%Y-%m-%d")) == ["2025-12-14", "2025-12-15"]
    assert out["signal"].tolist() == [True, True]


def test_quote_maps_are_clipped_before_oos_replay():
    q = pd.DataFrame(
        {"bid": [1.0, 1.1, 1.2], "ask": [1.1, 1.2, 1.3]},
        index=pd.to_datetime([
            "2025-12-15",
            "2025-12-16",
            "2025-12-20",
        ]),
    )
    out = clip_quote_maps_to_window(
        {"OPT": q},
        pd.Timestamp("2025-12-15"),
    )
    assert list(out["OPT"].index.strftime("%Y-%m-%d")) == ["2025-12-15"]
