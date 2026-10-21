#!/usr/bin/env python3
"""Build entry-defined terminal max-loss proxies for frozen real-chain strategy ledgers.

No future prices/quotes are used for risk. For each observed entry date in the
frozen State Adaptive or Staggered 1-layer trade ledger, the original entry
selection is reconstructed from the canonical QQQ chain and the entry
Bid/Ask is used to compute the terminal-payoff max-loss proxy for:
  +1 ATM Call -2 Short 20Δ Call +2 8Δ Call Wing
  +1 Long 25Δ Put -1 Short 10Δ Put

This is an entry-time risk definition, not a realized drawdown measurement.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from qqq_ratio_call_harvest_v1 import ensure_data
from qqq_state_adaptive_geometry_v1 import select_entry


def entry_quotes(con, opt_path, dt, ids):
    q = con.execute(
        """
        SELECT CAST(date AS DATE) AS date,
               CAST(contract_id AS VARCHAR) AS contract_id,
               CAST(strike AS DOUBLE) AS strike,
               CAST(bid AS DOUBLE) AS bid,
               CAST(ask AS DOUBLE) AS ask
        FROM read_parquet(?)
        WHERE CAST(date AS DATE)=?
          AND CAST(contract_id AS VARCHAR) IN (SELECT * FROM UNNEST(?))
          AND bid IS NOT NULL AND ask IS NOT NULL
          AND ask >= bid AND bid >= 0
        """,
        [str(opt_path), pd.Timestamp(dt).date(), [str(x) for x in ids]],
    ).df()
    if q.empty:
        return {}
    q["contract_id"] = q["contract_id"].astype(str)
    return {str(r.contract_id): r for _, r in q.iterrows()}


def max_loss_proxy(legs, quotes, spot):
    ids = {
        "atm": str(legs["atm"]["id"]),
        "sc": str(legs["sc20"]["id"]),
        "wing": str(legs["wing"]["id"]),
        "lp": str(legs["lp"]["id"]),
        "sp": str(legs["sp10"]["id"]),
    }
    if any(x not in quotes for x in ids.values()):
        return None

    q = {k: quotes[v] for k, v in ids.items()}
    initial = (
        float(q["atm"].ask)
        - 2.0 * float(q["sc"].bid)
        + 2.0 * float(q["wing"].ask)
        + float(q["lp"].ask)
        - float(q["sp"].bid)
    ) * 100.0

    grid = np.linspace(
        max(1.0, float(spot) * 0.20),
        max(float(spot) * 2.5, float(legs["wing"]["k"]) * 1.25),
        1200,
    )

    payoff = (
        np.maximum(grid - float(legs["atm"]["k"]), 0.0)
        - 2.0 * np.maximum(grid - float(legs["sc20"]["k"]), 0.0)
        + 2.0 * np.maximum(grid - float(legs["wing"]["k"]), 0.0)
        + np.maximum(float(legs["lp"]["k"]) - grid, 0.0)
        - np.maximum(float(legs["sp10"]["k"]) - grid, 0.0)
    ) * 100.0

    return max(0.0, -float(np.min(payoff - initial)))


def ledger(path, strategy):
    x = pd.read_csv(path)
    x["entry"] = pd.to_datetime(x["entry"])
    x["exit"] = pd.to_datetime(x["exit"])
    if "pnl_usd" not in x.columns:
        if "pnl_usd_100k_unit" in x.columns:
            x["pnl_usd"] = x["pnl_usd_100k_unit"].astype(float)
        else:
            raise ValueError(f"{path}: missing pnl")
    return x[["entry", "exit", "pnl_usd"]].drop_duplicates("entry").assign(strategy=strategy)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--state-ledger", required=True)
    ap.add_argument("--staggered-ledger", required=True)
    ap.add_argument("--out", default="artifacts")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    opt_path, up_path = ensure_data(Path(args.data_dir))
    underlying = pd.read_parquet(up_path)
    underlying.columns = [c.lower() for c in underlying.columns]
    underlying["date"] = pd.to_datetime(underlying["date"]).dt.tz_localize(None).dt.normalize()
    price_col = "adjclose" if "adjclose" in underlying.columns else ("adj_close" if "adj_close" in underlying.columns else "close")
    prices = underlying.set_index("date")[price_col].astype(float)

    ledgers = pd.concat(
        [
            ledger(args.state_ledger, "STATE_ADAPTIVE_GEOMETRY"),
            ledger(args.staggered_ledger, "STAGGERED_1LAYER"),
        ],
        ignore_index=True,
    )

    con = duckdb.connect()
    rows = []
    rejects = {}

    for _, row in ledgers.sort_values(["entry", "strategy"]).iterrows():
        dt = pd.Timestamp(row["entry"])
        spot = float(prices.loc[dt])
        legs = select_entry(con, opt_path, dt)
        if legs is None:
            rejects["NO_ENTRY_LEGS"] = rejects.get("NO_ENTRY_LEGS", 0) + 1
            continue

        ids = [legs[k]["id"] for k in ("atm", "sc20", "wing", "lp", "sp10")]
        q = entry_quotes(con, opt_path, dt, ids)
        risk = max_loss_proxy(legs, q, spot)
        if risk is None:
            rejects["NO_ENTRY_QUOTES"] = rejects.get("NO_ENTRY_QUOTES", 0) + 1
            continue

        rows.append(
            {
                "strategy": row["strategy"],
                "entry": str(dt.date()),
                "exit": str(pd.Timestamp(row["exit"]).date()),
                "pnl_usd": float(row["pnl_usd"]),
                "entry_terminal_max_loss_proxy_usd": float(risk),
                "spot": spot,
                "expiry": str(pd.Timestamp(legs["expiry"]).date()),
                "atm_strike": float(legs["atm"]["k"]),
                "short_call_strike": float(legs["sc20"]["k"]),
                "wing_strike": float(legs["wing"]["k"]),
                "long_put_strike": float(legs["lp"]["k"]),
                "short_put_strike": float(legs["sp10"]["k"]),
            }
        )

    df = pd.DataFrame(rows).sort_values(["entry", "strategy"])
    df.to_csv(out / "all_realchain_entry_risk.csv", index=False)

    print(
        {
            "rows": int(len(df)),
            "strategies": sorted(df.strategy.unique().tolist()) if not df.empty else [],
            "rejects": rejects,
            "risk_min": float(df.entry_terminal_max_loss_proxy_usd.min()) if not df.empty else None,
            "risk_median": float(df.entry_terminal_max_loss_proxy_usd.median()) if not df.empty else None,
            "risk_p95": float(df.entry_terminal_max_loss_proxy_usd.quantile(0.95)) if not df.empty else None,
            "risk_max": float(df.entry_terminal_max_loss_proxy_usd.max()) if not df.empty else None,
        }
    )


if __name__ == "__main__":
    main()
