#!/usr/bin/env python3
"""QQQ cross-date staggered / stacked real-chain replay V2.

Purpose:
  Test whether the missing dynamic is not within-vintage strike migration,
  but overlapping option vintages opened on different signal dates.

FROZEN CONTRACT PER VINTAGE:
  +1 ~50Δ Call
  -2 ~20Δ Calls
  +2 ~8Δ farther OTM Call Wings
  +1 ~25Δ Long Put
  -1 ~10Δ Short Put

V2 modes:
  1_LAYER: one active vintage at a time (no overlap)
  2_LAYER_HALF_STACK: up to two simultaneous vintages, 50% capital each
  4_LAYER_STACK: up to four simultaneous vintages, 25% capital each

The geometry inside each vintage is STATIC. There are no strike migrations,
no optimization, no Black-Scholes selection, and no interpolation.

Every qualifying signal date is a candidate new vintage. If a slot is free,
a new vintage is opened. Older vintages remain alive until their original
30-day/expiry exit. This creates true cross-date stacking and retains the
Long Put / Short Put tail structure in each live vintage.

P&L accounting:
  Each vintage is a 100,000 USD normalized sub-account. In a K-layer mode,
  each admitted vintage is assigned CAPITAL/K. The rest stays in cash.
  Per-vintage daily MTM is scaled into the portfolio; at exit its realized
  value returns to cash. Thus portfolio NAV is not a concatenation of
  isolated trades and overlapping vintages are explicitly aggregated.

Historical QQQ option-chain Bid/Ask only.
Entry: executable asks/bids.
Daily mark: Mid.
Exit: executable Bid/Ask.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import duckdb

from qqq_ratio_call_harvest_v1 import (
    CAPITAL_USD,
    ensure_data,
    load_underlying,
    sha256_file,
)
from qqq_state_adaptive_geometry_v1 import select_entry, trade


BASE_CAPITAL = 100_000.0
STACKS = {
    "1_LAYER_NO_OVERLAP": 1,
    "2_LAYER_HALF_STACK": 2,
    "4_LAYER_STACK": 4,
}


def build_candidates(con, opt_path, u):
    candidates = []
    rejects = {}

    for _, row in u.iterrows():
        dt = pd.Timestamp(row.date)
        if not bool(row.signal):
            continue

        legs = select_entry(con, opt_path, dt)
        if legs is None:
            rejects["NO_ENTRY_LEGS"] = rejects.get("NO_ENTRY_LEGS", 0) + 1
            continue

        tr, status = trade(con, opt_path, u, row, legs, False)
        if tr is None:
            rejects[status] = rejects.get(status, 0) + 1
            continue

        candidates.append(tr)

    candidates.sort(key=lambda x: pd.Timestamp(x["entry"]))
    return candidates, rejects


def admit_stack(candidates, max_layers):
    """Greedily admit candidate vintages whenever a layer is free.

    Exit is processed before a same-day entry, so an expiring layer can be
    recycled on the same trading date. No global cooldown is applied because
    overlap itself is the tested structural variable.
    """
    selected = []
    active = []

    for tr in candidates:
        entry = pd.Timestamp(tr["entry"])
        active = [x for x in active if pd.Timestamp(x["exit"]) >= entry]

        if len(active) >= max_layers:
            continue

        selected.append(tr)
        active.append(tr)

    return selected


def portfolio_curve(selected, max_layers, dates):
    """Build continuous portfolio NAV from scaled overlapping sub-accounts."""
    if not selected:
        return pd.DataFrame(columns=["date", "nav", "active_layers", "tail_long_puts"])

    alloc = BASE_CAPITAL / max_layers

    starts = {}
    exits = {}
    paths = {}

    for i, tr in enumerate(selected):
        key = f"v{i:04d}"
        entry = pd.Timestamp(tr["entry"])
        exit_ = pd.Timestamp(tr["exit"])
        starts.setdefault(entry, []).append((key, tr))
        exits.setdefault(exit_, []).append((key, tr))
        paths[key] = pd.DataFrame(
            [(pd.Timestamp(dt), float(raw_nav)) for dt, raw_nav in tr["eq"]],
            columns=["date", "raw_nav"],
        ).drop_duplicates("date").set_index("date")

    cash = BASE_CAPITAL
    active = {}
    realized = {}
    rows = []

    for dt in pd.to_datetime(dates):
        # Exits first: free capital before any same-day new entry.
        for key, tr in exits.get(pd.Timestamp(dt), []):
            if key not in active:
                continue
            p = paths[key]
            if dt in p.index:
                final_nav = float(p.loc[dt, "raw_nav"])
            else:
                final_nav = float(p.iloc[-1]["raw_nav"])
            cash += alloc * final_nav / BASE_CAPITAL
            realized[key] = final_nav
            del active[key]

        # New vintages.
        for key, tr in starts.get(pd.Timestamp(dt), []):
            if key in active or key in realized:
                continue
            cash -= alloc
            active[key] = tr

        nav = float(cash)
        tail_count = 0

        for key, tr in active.items():
            p = paths[key]
            if dt not in p.index:
                # No new quote that day; keep the latest known MTM.
                prev = p.loc[p.index <= dt]
                if prev.empty:
                    continue
                raw_nav = float(prev.iloc[-1]["raw_nav"])
            else:
                raw_nav = float(p.loc[dt, "raw_nav"])

            nav += alloc * raw_nav / BASE_CAPITAL
            tail_count += 1

        rows.append(
            {
                "date": pd.Timestamp(dt),
                "nav": nav,
                "active_layers": int(len(active)),
                # Every active vintage contains one retained Long Put.
                "tail_long_puts": int(tail_count),
            }
        )

    out = pd.DataFrame(rows)
    out["peak"] = out.nav.cummax()
    out["dd"] = out.nav / out.peak - 1.0
    return out


def summarize(selected, curve, label, max_layers, candidate_count):
    if curve.empty:
        return {
            "mode": label,
            "stack_layers": max_layers,
            "trades": 0,
            "candidate_signals": candidate_count,
        }

    start_nav = BASE_CAPITAL
    final_nav = float(curve.nav.iloc[-1])
    first = pd.Timestamp(curve.date.iloc[0])
    last = pd.Timestamp(curve.date.iloc[-1])
    years = max((last - first).days / 365.25, 1 / 365.25)

    concurrent = curve.active_layers.astype(float)

    return {
        "mode": label,
        "stack_layers": max_layers,
        "trades": int(len(selected)),
        "candidate_signals": int(candidate_count),
        "entries_skipped_full": int(candidate_count - len(selected)),
        "total_return_pct": float(100.0 * (final_nav / start_nav - 1.0)),
        "cagr": float((final_nav / start_nav) ** (1.0 / years) - 1.0),
        "maxdd_daily_mtm": float(curve.dd.min()),
        "avg_active_layers": float(concurrent.mean()),
        "max_active_layers": int(concurrent.max()),
        "days_with_2plus_layers": int((concurrent >= 2).sum()),
        "days_with_4_layers": int((concurrent >= 4).sum()),
        "data_start": str(first.date()),
        "data_end": str(last.date()),
        "final_nav_usd": final_nav,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--out", default="artifacts")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    opt_path, up_path = ensure_data(Path(args.data_dir))
    u = load_underlying(up_path).copy().reset_index(drop=True)
    con = duckdb.connect()

    candidates, rejects = build_candidates(con, opt_path, u)

    summary_rows = []
    curve_paths = {}
    selected_trades = {}

    trading_dates = u["date"].tolist()

    for label, max_layers in STACKS.items():
        selected = admit_stack(candidates, max_layers)
        curve = portfolio_curve(selected, max_layers, trading_dates)

        summary_rows.append(
            summarize(
                selected,
                curve,
                label,
                max_layers,
                len(candidates),
            )
        )
        curve_paths[label] = curve
        selected_trades[label] = selected

        trade_rows = []
        for i, tr in enumerate(selected):
            trade_rows.append(
                {
                    "vintage_id": f"v{i:04d}",
                    "entry": str(pd.Timestamp(tr["entry"]).date()),
                    "exit": str(pd.Timestamp(tr["exit"]).date()),
                    "pnl_usd_100k_unit": float(tr["pnl_usd"]),
                    "return_pct_unit": float(tr["return_pct"]),
                    "entry_cashflow_usd_100k_unit": float(tr["entry_cashflow_usd"]),
                }
            )

        pd.DataFrame(trade_rows).to_csv(
            out / f"trades_{label}.csv", index=False
        )
        if not curve.empty:
            curve.to_csv(out / f"equity_{label}.csv", index=False)

    pd.DataFrame(summary_rows).to_csv(out / "summary.csv", index=False)

    report = {
        "research_id": "QQQ_STAGGERED_STACK_V2",
        "status": "REAL_QQQ_CHAIN_CROSS_DATE_STACK_TEST",
        "contract": {
            "per_vintage": "+1 ~50Δ Call -2 ~20Δ Calls +2 ~8Δ Call Wings +1 ~25Δ Long Put -1 ~10Δ Short Put",
            "geometry": "STATIC_WITHIN_VINTAGE",
            "cross_date_rule": "every qualifying signal date is a candidate new vintage",
            "stack_modes": STACKS,
            "allocation": "BASE_CAPITAL / stack_layers per admitted vintage",
            "expiry": "fixed from vintage entry",
            "holding": "same original trade lifecycle: max 30 days or expiry",
            "tail": "each live vintage retains its own Long Put and Short Put",
            "migration": False,
            "interpolation": False,
            "black_scholes": False,
            "optimization": False,
            "overlap": True,
            "cooldown": False,
        },
        "data": {
            "options_sha256": sha256_file(opt_path),
            "underlying_sha256": sha256_file(up_path),
            "underlying_range": [
                str(pd.Timestamp(u.date.min()).date()),
                str(pd.Timestamp(u.date.max()).date()),
            ],
        },
        "results": {
            "summary": summary_rows,
            "candidate_rejections": rejects,
        },
    }

    (out / "qqq_staggered_stack_v2_result.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
