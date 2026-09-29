#!/usr/bin/env python3
"""QQQ Universal Harvest NAV V19.

Adds official step-NAV, total return, CAGR and max drawdown on top of the
V18 isolated / replenish harvest bank. Research only. Not a live signal.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd

from qqq_universal_harvest_bank_v18 import (
    load_seed, ratio_pool, conv_pool, simulate_seed, GLOBAL_GAP_DAYS,
)

CAPITAL = 100000.0


def _to_ts(x):
    return pd.Timestamp(x)


def step_equity(flows, capital=CAPITAL):
    if not flows:
        return pd.DataFrame(columns=["date", "nav", "peak", "dd", "pnl_usd"])
    rows = []
    nav = float(capital)
    peak = float(capital)
    for dt, pnl, src in sorted(flows, key=lambda x: (_to_ts(x[0]), x[2])):
        nav = nav + float(pnl)
        peak = max(peak, nav)
        rows.append({
            "date": _to_ts(dt), "nav": float(nav), "peak": float(peak),
            "dd": float(nav / peak - 1.0) if peak else 0.0,
            "pnl_usd": float(pnl), "source": src,
        })
    return pd.DataFrame(rows)


def summarize_equity(eq, label, extra=None):
    extra = extra or {}
    if eq is None or eq.empty:
        out = {"book": label, "trades": 0, "total_return_pct": 0.0,
               "cagr": 0.0, "maxdd": 0.0, "final_nav": CAPITAL}
        out.update(extra)
        return out
    start = _to_ts(eq.date.iloc[0])
    end = _to_ts(eq.date.iloc[-1])
    yrs = max((end - start).days / 365.25, 1.0 / 365.25)
    final = float(eq.nav.iloc[-1])
    pnls = [float(x) for x in eq.pnl_usd.tolist()]
    out = {
        "book": label,
        "start": str(start.date()),
        "end": str(end.date()),
        "days": int((end - start).days),
        "years": float(yrs),
        "trades": int(len(eq)),
        "win_rate": float(np.mean([p > 0 for p in pnls])) if pnls else 0.0,
        "avg_trade_usd": float(np.mean(pnls)) if pnls else 0.0,
        "total_pnl_usd": float(sum(pnls)),
        "total_return_pct": float(100.0 * (final / CAPITAL - 1.0)),
        "cagr": float((final / CAPITAL) ** (1.0 / yrs) - 1.0),
        "maxdd": float(eq.dd.min()),
        "final_nav": final,
        "capital_usd": CAPITAL,
    }
    out.update(extra)
    return out


def book_flows(seed_row, accepted):
    flows = [(_to_ts(seed_row["exit"]), float(seed_row["pnl_usd"]), "SEED")]
    for ev in accepted:
        flows.append((_to_ts(ev["exit"]), float(ev["pnl"]), str(ev["strategy"])))
    return flows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed-ledger", required=True)
    ap.add_argument("--ratio-ledger", required=True)
    ap.add_argument("--convexity-ledger", required=True)
    ap.add_argument("--out", default="artifacts")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    seeds = load_seed(a.seed_ledger)
    ratio = ratio_pool(a.ratio_ledger)
    conv = conv_pool(a.convexity_ledger)
    ratio["priority"] = 1
    conv["priority"] = 0
    pool = pd.concat([conv, ratio], ignore_index=True).sort_values(["entry", "priority"]).reset_index(drop=True)

    summaries = []
    event_rows = []
    equity_rows = []
    per_seed = []

    for _, seed in seeds.iterrows():
        seed_id = str(pd.Timestamp(seed["entry"]).date())
        for replenish in (False, True):
            mode = "REPLENISH" if replenish else "ISOLATED"
            accepted, bank, summary = simulate_seed(seed, pool.copy(), replenish)
            flows = book_flows(seed, accepted)
            eq = step_equity(flows)
            stats = summarize_equity(
                eq, f"{mode}:{seed_id}",
                extra={
                    "mode": mode,
                    "seed_entry": seed_id,
                    "seed_n": int(seed["n"]),
                    "seed_pnl_usd": float(seed["pnl_usd"]),
                    "future_opportunities": int(len(accepted)),
                    "ratio_count": int(sum(x["strategy"] == "RATIO_HARVEST_N2" for x in accepted)),
                    "convexity_count": int(sum(x["strategy"] == "CONVEXITY_SHOCK" for x in accepted)),
                    "final_bank_usd": float(bank),
                    "rights_win_rate": float(np.mean([float(x["pnl"]) > 0 for x in accepted])) if accepted else None,
                    "rights_pnl_usd": float(sum(float(x["pnl"]) for x in accepted)) if accepted else 0.0,
                },
            )
            per_seed.append(stats)
            summaries.append(summary)
            eq2 = eq.copy()
            eq2["mode"] = mode
            eq2["seed_entry"] = seed_id
            equity_rows.append(eq2)
            for ev in accepted:
                e2 = dict(ev)
                e2["seed_entry"] = seed_id
                e2["seed_n"] = int(seed["n"])
                e2["mode"] = mode
                event_rows.append(e2)

    per_seed_df = pd.DataFrame(per_seed)
    eq_all = pd.concat(equity_rows, ignore_index=True) if equity_rows else pd.DataFrame()
    ev_df = pd.DataFrame(event_rows)
    per_seed_df.to_csv(out / "v19_per_seed_nav_stats.csv", index=False)
    ev_df.to_csv(out / "v19_events.csv", index=False)
    eq_all.to_csv(out / "v19_all_step_equity.csv", index=False)

    first = seeds.iloc[0]
    first_acc, first_bank, _ = simulate_seed(first, pool.copy(), False)
    first_eq = step_equity(book_flows(first, first_acc))
    first_eq.to_csv(out / "v19_first_seed_isolated_equity.csv", index=False)
    first_stats = summarize_equity(
        first_eq, "FIRST_SEED_ONLY_ISOLATED",
        extra={
            "mode": "ISOLATED",
            "seed_entry": str(pd.Timestamp(first["entry"]).date()),
            "seed_n": int(first["n"]),
            "seed_pnl_usd": float(first["pnl_usd"]),
            "future_opportunities": int(len(first_acc)),
            "final_bank_usd": float(first_bank),
            "official_single_curve": True,
        },
    )

    def pack_mode(mode):
        z = per_seed_df[per_seed_df["mode"] == mode]
        if z.empty:
            return {"mode": mode, "books": 0}
        return {
            "mode": mode,
            "books": int(len(z)),
            "median_total_return_pct": float(z.total_return_pct.median()),
            "mean_total_return_pct": float(z.total_return_pct.mean()),
            "min_total_return_pct": float(z.total_return_pct.min()),
            "max_total_return_pct": float(z.total_return_pct.max()),
            "median_cagr": float(z.cagr.median()),
            "mean_cagr": float(z.cagr.mean()),
            "median_maxdd": float(z.maxdd.median()),
            "min_maxdd": float(z.maxdd.min()),
            "mean_win_rate": float(z.win_rate.mean()),
            "median_future_opportunities": float(z.future_opportunities.median()),
        }

    report = {
        "research_id": "QQQ_UNIVERSAL_HARVEST_NAV_V19",
        "status": "REAL_CHAIN_STEP_NAV_ON_V18_BANK",
        "capital_usd": CAPITAL,
        "nav_note": "NAV marks realized cashflows. Bank isolation unchanged. Per-seed books overlap and must not be summed.",
        "contract": {
            "authoritative_mode": "ISOLATED",
            "official_single_curve": "FIRST_SEED_ONLY_ISOLATED",
            "replenish": "contamination comparator",
            "gap_days": GLOBAL_GAP_DAYS,
            "hybrid_dynamic": "excluded",
            "optimization": False,
            "black_scholes": False,
        },
        "data": {
            "options_sha256": "1f831556cd87ec9d7af43d3b47a69a829ffb2fb199cfcef4ff55d289badf8734",
            "underlying_sha256": "78c015fd7fa9d493cd798d5ae81b3c2ae6dc3b8176e25e7bb90cd4114b103351",
            "seed_count": int(len(seeds)),
        },
        "results": {
            "first_seed_only_isolated": first_stats,
            "per_seed_isolated": per_seed_df[per_seed_df["mode"] == "ISOLATED"].to_dict(orient="records"),
            "aggregate": [pack_mode("ISOLATED"), pack_mode("REPLENISH")],
        },
    }
    (out / "qqq_universal_harvest_nav_v19_result.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
