#!/usr/bin/env python3
"""QQQ Universal Harvest Bank V19: ALL verified real-chain nodes.

This is a counterfactual rights-bank experiment.

Seed:
  one independent positive N>2 realized Risk-Win from strict V16.

Pool (real historical chain):
  RATIO_HARVEST_N2
  CONVEXITY_SHOCK_GATED
  STATE_ADAPTIVE_GEOMETRY
  STAGGERED_1LAYER

Each candidate carries an entry-defined terminal max-loss/risk requirement.
A right can be bought only when required risk <= current Bank.

Accounting modes:
  ISOLATED: later positive P&L is ignored; only later losses consume Bank.
  REPLENISH: all later realized P&L changes Bank (contamination comparator).

Rules:
  one active opportunity
  10-calendar-day gap after each realized exit
  fixed strategy priority on same entry date:
    CONVEXITY, STATE_ADAPTIVE, STAGGERED, RATIO
  no optimization, no look-ahead, no BS pricing
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

GLOBAL_GAP_DAYS = 10


def load_seed(path):
    x = pd.read_csv(path)
    x["entry"] = pd.to_datetime(x["entry"])
    x["exit"] = pd.to_datetime(x["exit"])
    return x[(x["n"] > 2) & (x["pnl_usd"] > 0)].sort_values("entry").reset_index(drop=True)


def ratio_pool(path):
    x = pd.read_csv(path)
    x["entry"] = pd.to_datetime(x["entry"])
    x["exit"] = pd.to_datetime(x["exit"])
    return x.assign(
        risk=x["max_loss_proxy_usd"].astype(float),
        pnl=x["pnl_usd"].astype(float),
        strategy="RATIO_HARVEST_N2",
    )[["entry", "exit", "risk", "pnl", "strategy"]]


def convexity_pool(path):
    x = pd.read_csv(path)
    x["entry"] = pd.to_datetime(x["entry_date"])
    x["exit"] = pd.to_datetime(x["exit_date"])
    return x.assign(
        risk=x["debit_usd"].astype(float),
        pnl=x["realized_pnl_usd"].astype(float),
        strategy="CONVEXITY_SHOCK_GATED",
    )[["entry", "exit", "risk", "pnl", "strategy"]]


def realchain_pool(path, risk_path, strategy):
    t = pd.read_csv(path)
    t["entry"] = pd.to_datetime(t["entry"])
    t["exit"] = pd.to_datetime(t["exit"])
    if "pnl_usd" not in t.columns and "pnl_usd_100k_unit" in t.columns:
        t["pnl_usd"] = t["pnl_usd_100k_unit"].astype(float)
    r = pd.read_csv(risk_path)
    r["entry"] = pd.to_datetime(r["entry"])
    r = r[r["strategy"] == strategy][["entry", "entry_terminal_max_loss_proxy_usd"]]
    x = t.merge(r, on="entry", how="inner")
    return x.assign(
        risk=x["entry_terminal_max_loss_proxy_usd"].astype(float),
        pnl=x["pnl_usd"].astype(float),
        strategy=strategy,
    )[["entry", "exit", "risk", "pnl", "strategy"]]


def simulate(seed_row, pool, replenish):
    bank = float(seed_row["pnl_usd"])
    seed_entry = pd.Timestamp(seed_row["entry"])
    last_exit = pd.Timestamp(seed_row["exit"])
    accepted = []
    skipped = []

    while True:
        avail = pool[pool["entry"] > last_exit + pd.Timedelta(days=GLOBAL_GAP_DAYS)].copy()
        if avail.empty or bank <= 0:
            break

        next_date = avail["entry"].min()
        same = avail[avail["entry"] == next_date].sort_values("priority")

        feasible = same[same["risk"] <= bank]
        if feasible.empty:
            skipped.extend(same.to_dict("records"))
            pool = pool[pool["entry"] > next_date].copy()
            continue

        cand = feasible.iloc[0].to_dict()
        accepted.append(cand)

        pnl = float(cand["pnl"])
        if replenish:
            bank = max(0.0, bank + pnl)
        else:
            bank = max(0.0, bank + min(0.0, pnl))

        last_exit = pd.Timestamp(cand["exit"])
        pool = pool[pool["entry"] > last_exit].copy()

    end = pd.Timestamp(accepted[-1]["exit"]) if accepted else last_exit

    summary = {
        "seed_entry": str(seed_entry.date()),
        "seed_exit": str(pd.Timestamp(seed_row["exit"]).date()),
        "seed_n": int(seed_row["n"]),
        "seed_pnl_usd": float(seed_row["pnl_usd"]),
        "mode": "REPLENISH" if replenish else "ISOLATED",
        "future_opportunities": int(len(accepted)),
        "distinct_strategies": int(len({x["strategy"] for x in accepted})),
        "ratio_count": int(sum(x["strategy"] == "RATIO_HARVEST_N2" for x in accepted)),
        "convexity_count": int(sum(x["strategy"] == "CONVEXITY_SHOCK_GATED" for x in accepted)),
        "state_count": int(sum(x["strategy"] == "STATE_ADAPTIVE_GEOMETRY" for x in accepted)),
        "staggered_count": int(sum(x["strategy"] == "STAGGERED_1LAYER" for x in accepted)),
        "gross_risk_traversed_usd": float(sum(float(x["risk"]) for x in accepted)),
        "lifetime_days": int((end - seed_entry).days),
        "final_bank_usd": float(bank),
        "accepted_entries": ";".join(str(pd.Timestamp(x["entry"]).date()) for x in accepted),
    }
    return accepted, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed-ledger", required=True)
    ap.add_argument("--ratio-ledger", required=True)
    ap.add_argument("--convexity-ledger", required=True)
    ap.add_argument("--state-ledger", required=True)
    ap.add_argument("--staggered-ledger", required=True)
    ap.add_argument("--risk-ledger", required=True)
    ap.add_argument("--out", default="artifacts")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    pools = [
        convexity_pool(args.convexity_ledger),
        realchain_pool(args.state_ledger, args.risk_ledger, "STATE_ADAPTIVE_GEOMETRY"),
        realchain_pool(args.staggered_ledger, args.risk_ledger, "STAGGERED_1LAYER"),
        ratio_pool(args.ratio_ledger),
    ]
    priorities = {
        "CONVEXITY_SHOCK_GATED": 0,
        "STATE_ADAPTIVE_GEOMETRY": 1,
        "STAGGERED_1LAYER": 2,
        "RATIO_HARVEST_N2": 3,
    }
    pool = pd.concat(pools, ignore_index=True)
    pool["priority"] = pool["strategy"].map(priorities)
    pool = pool.dropna(subset=["entry", "exit", "risk", "pnl"]).sort_values(
        ["entry", "priority"]
    ).reset_index(drop=True)

    seeds = load_seed(args.seed_ledger)
    rows = []
    events = []

    for _, seed in seeds.iterrows():
        for replenish in (False, True):
            accepted, summary = simulate(seed, pool.copy(), replenish)
            rows.append(summary)
            for x in accepted:
                events.append(
                    {
                        "seed_entry": str(pd.Timestamp(seed["entry"]).date()),
                        "seed_n": int(seed["n"]),
                        "mode": summary["mode"],
                        "entry": str(pd.Timestamp(x["entry"]).date()),
                        "exit": str(pd.Timestamp(x["exit"]).date()),
                        "strategy": x["strategy"],
                        "risk_usd": float(x["risk"]),
                        "pnl_usd": float(x["pnl"]),
                    }
                )

    summary_df = pd.DataFrame(rows)
    events_df = pd.DataFrame(events)
    summary_df.to_csv(out / "universal_harvest_all_seed_summary.csv", index=False)
    events_df.to_csv(out / "universal_harvest_all_events.csv", index=False)

    agg = []
    for mode in ("ISOLATED", "REPLENISH"):
        z = summary_df[summary_df["mode"] == mode]
        if z.empty:
            continue
        agg.append(
            {
                "mode": mode,
                "seeds": int(len(z)),
                "mean_lifetime_days": float(z["lifetime_days"].mean()),
                "median_lifetime_days": float(z["lifetime_days"].median()),
                "max_lifetime_days": int(z["lifetime_days"].max()),
                "mean_future_opportunities": float(z["future_opportunities"].mean()),
                "median_future_opportunities": float(z["future_opportunities"].median()),
                "max_future_opportunities": int(z["future_opportunities"].max()),
                "mean_distinct_strategies": float(z["distinct_strategies"].mean()),
                "seeds_using_both_or_more": int((z["distinct_strategies"] >= 2).sum()),
                "seeds_using_3plus": int((z["distinct_strategies"] >= 3).sum()),
                "seeds_using_4": int((z["distinct_strategies"] >= 4).sum()),
                "ratio_total": int(z["ratio_count"].sum()),
                "convexity_total": int(z["convexity_count"].sum()),
                "state_total": int(z["state_count"].sum()),
                "staggered_total": int(z["staggered_count"].sum()),
                "mean_gross_risk_traversed_usd": float(z["gross_risk_traversed_usd"].mean()),
                "median_gross_risk_traversed_usd": float(z["gross_risk_traversed_usd"].median()),
                "max_gross_risk_traversed_usd": float(z["gross_risk_traversed_usd"].max()),
            }
        )

    report = {
        "research_id": "QQQ_UNIVERSAL_HARVEST_BANK_V19_ALL_REALCHAIN",
        "status": "REAL_QQQ_CHAIN_STRATEGY_POOL_COUNTERFACTUAL",
        "source_runs": {
            "v16_seed": 36560796953,
            "ratio": 36550743553,
            "convexity_shock_gated": 36550732916,
            "state_adaptive": "research/qqq-state-adaptive-geometry-v1-20260929",
            "staggered": 36550743641,
        },
        "strategies": [
            "RATIO_HARVEST_N2",
            "CONVEXITY_SHOCK_GATED",
            "STATE_ADAPTIVE_GEOMETRY",
            "STAGGERED_1LAYER",
        ],
        "risk_definition": "entry-terminal-max-loss proxy from actual entry Bid/Ask and fixed entry geometry; no future quote lookahead",
        "contract": {
            "seed": "positive N>2 V16 Risk-Win, each seed isolated",
            "entry_rule": "candidate risk <= current Bank",
            "update_isolated": "later positive P&L ignored; later losses consume Bank",
            "update_replenish": "Bank=max(0,Bank+all realized strategy P&L)",
            "one_active_opportunity": True,
            "global_gap_days": GLOBAL_GAP_DAYS,
            "same_date_priority": "CONVEXITY, STATE_ADAPTIVE, STAGGERED, RATIO",
            "bank_is_not_nav": True,
            "optimization": False,
            "black_scholes": False,
            "interpolation": False,
        },
        "data": {
            "options_sha256": "1f831556cd87ec9d7af43d3b47a69a829ffb2fb199cfcef4ff55d289badf8734",
            "underlying_sha256": "78c015fd7fa9d493cd798d5ae81b3c2ae6dc3b8176e25e7bb90cd4114b103351",
        },
        "results": {"aggregate": agg},
    }

    (out / "qqq_universal_harvest_bank_v19_all_result.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
