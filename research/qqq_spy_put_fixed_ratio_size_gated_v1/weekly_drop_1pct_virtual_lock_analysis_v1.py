#!/usr/bin/env python3
"""Classify SPY 5-session -1% trigger trades by a per-trade -10% SPY entry-price floor."""
import argparse
import csv
import json
import statistics
from datetime import date
from pathlib import Path
from collections import defaultdict

import qqq_spy_put_premium_matched_phase_v1 as eng

START, END = "2018-03-01", "2025-12-15"
YEARS = (date.fromisoformat(END) - date.fromisoformat(START)).days / 365.2425
POLICY = "HOLD_20_OR_DTE_LE_7"
ARMS = ("1x3", "1x6", "2x6", "2x6_samecontract")


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def stats(rows):
    vals = [float(r["net_pnl_usd"]) for r in rows]
    gains = sum(v for v in vals if v > 0)
    losses = -sum(v for v in vals if v < 0)
    return {
        "resolved_n": len(vals),
        "cumulative_episode_pnl_usd": round(sum(vals), 2),
        "mean_per_episode_usd": round(statistics.mean(vals), 2) if vals else None,
        "median_per_episode_usd": round(statistics.median(vals), 2) if vals else None,
        "win_rate_pct": round(100 * sum(v > 0.005 for v in vals) / len(vals), 2) if vals else None,
        "worst_episode_usd": round(min(vals), 2) if vals else None,
        "best_episode_usd": round(max(vals), 2) if vals else None,
        "profit_factor": round(gains / losses, 4) if losses else (None if not gains else "INF"),
        "annual_average_episode_sum_usd": round(sum(vals) / YEARS, 2),
        "CAGR": None,
        "CAGR_note": "Overlapping episode P&L is not a capital-constrained account NAV; CAGR is not calculated."
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base", required=True, help="Directory containing ratio_1x3, ratio_1x6, ratio_2x6 and ratio_2x6_samecontract")
    p.add_argument("--qqq-cache", required=True)
    p.add_argument("--spy-cache", required=True)
    args = p.parse_args()
    base = Path(args.base)
    out = base / "virtual_lock_10pct"
    out.mkdir(parents=True, exist_ok=True)

    qcache, scache = Path(args.qqq_cache), Path(args.spy_cache)
    qcache.mkdir(parents=True, exist_ok=True)
    scache.mkdir(parents=True, exist_ok=True)
    q_path = qcache / "underlying_prices.parquet"
    s_path = scache / "underlying_prices.parquet"
    if not q_path.exists():
        q_path, _ = eng.download_verified("QQQ", None, qcache)
    if not s_path.exists():
        s_path, _ = eng.download_verified("SPY", None, scache)
    qspots = eng.load_spots(q_path, "QQQ")
    sspots = eng.load_spots(s_path, "SPY")
    common = sorted(set(qspots) & set(sspots))

    classifications = []
    summaries = []
    run_stats = {}
    for ratio in ARMS:
        arm = base / ("ratio_" + ratio)
        summary_path = arm / "summary.json"
        entries_path = arm / "entry_cohort.csv"
        trades_path = arm / "trade_episodes.csv"
        if not (summary_path.is_file() and entries_path.is_file() and trades_path.is_file()):
            raise FileNotFoundError(f"Missing replay artifact for {ratio}: {arm}")
        source = json.loads(summary_path.read_text(encoding="utf-8"))
        entries = {str(r["episode_id"]): r for r in read_csv(entries_path)}
        trades = [r for r in read_csv(trades_path) if r.get("policy") == POLICY]
        resolved, accepted = [], []
        breached_n = 0
        missing_path_n = 0
        for trade in trades:
            eid = str(trade.get("episode_id"))
            entry = entries.get(eid)
            if entry is None:
                raise ValueError(f"{ratio}/{eid}: selected-policy trade missing entry metadata")
            status = trade.get("status")
            record = {
                "ratio": ratio,
                "episode_id": eid,
                "signal_date": entry.get("signal_date"),
                "entry_date": entry.get("entry_date"),
                "exit_date": trade.get("exit_date"),
                "status": status,
                "net_pnl_usd": trade.get("net_pnl_usd"),
                "spy_entry_close": entry.get("spy_spot_entry"),
                "spy_worst_close_from_entry_pct": None,
                "spy_floor_90pct_entry_close": None,
                "passed_virtual_lock_10pct": None,
                "path_observations": 0,
                "path_note": None,
            }
            if status != "RESOLVED" or trade.get("net_pnl_usd") in (None, ""):
                record["path_note"] = "UNRESOLVED_EXCLUDED_FROM_PNL"
                classifications.append(record)
                continue
            start, end = str(entry.get("entry_date")), str(trade.get("exit_date"))
            if start not in sspots or end not in sspots:
                missing_path_n += 1
                record["path_note"] = "MISSING_ENTRY_OR_EXIT_SPY_CLOSE"
                classifications.append(record)
                continue
            path = [d for d in common if start <= d <= end]
            if not path or float(sspots[start]) <= 0:
                missing_path_n += 1
                record["path_note"] = "EMPTY_OR_INVALID_SPY_PATH"
                classifications.append(record)
                continue
            worst_return = min(float(sspots[d]) / float(sspots[start]) - 1.0 for d in path)
            passed = worst_return >= -0.10 - 1e-12
            record.update({
                "spy_worst_close_from_entry_pct": round(worst_return * 100, 4),
                "spy_floor_90pct_entry_close": round(float(sspots[start]) * 0.90, 4),
                "passed_virtual_lock_10pct": passed,
                "path_observations": len(path),
                "path_note": "PASS_CLOSES_NEVER_BELOW_90PCT_ENTRY" if passed else "FAIL_CLOSE_BREACHED_10PCT_ENTRY_FLOOR",
            })
            classifications.append(record)
            resolved.append(record)
            if passed:
                accepted.append(record)
            else:
                breached_n += 1

        all_stats = stats(resolved)
        lock_stats = stats(accepted)
        run_stats[ratio] = {
            "entry_filter": source.get("entry_filter"),
            "scheduled_opportunities": source.get("fixed_entry_schedule", {}).get("scheduled_opportunities"),
            "filter_qualified_sessions": source.get("entry_filter", {}).get("qualified_sessions"),
            "selected_signals": source.get("cohort", {}).get("selected_signals"),
            "entered_cohorts": source.get("cohort", {}).get("entered_cohorts"),
            "entry_skipped": source.get("cohort", {}).get("entry_skipped"),
            "opened_selected_policy": len(trades),
            "resolved": len(resolved),
            "unresolved": sum(1 for r in trades if str(r.get("status", "")).startswith("UNRESOLVED")),
            "resolved_missing_path": missing_path_n,
            "resolved_breached_10pct_floor": breached_n,
            "all_resolved": all_stats,
            "virtual_lock_10pct_pass": lock_stats,
        }
        for label, items in (("all_resolved_trades", resolved), ("virtual_lock_10pct_pass", accepted)):
            summaries.append({
                "ratio": ratio, "condition": label,
                "N": len(items),
                **stats(items),
                "breached_10pct_n": sum(r.get("passed_virtual_lock_10pct") is False for r in resolved) if label == "all_resolved_trades" else 0,
            })

    fields = list(classifications[0]) if classifications else []
    with (out / "episode_classification.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(classifications)

    result = {
        "schema": "spy-weekly-drop-1pct-per-trade-virtual-lock-10pct.v1",
        "status": "COMPLETED",
        "window": {"start": START, "end": END, "elapsed_years": round(YEARS, 6)},
        "trigger_definition": {
            "signal": "SPY close-to-close rolling 5-common-session return crosses from above -1.00% to <= -1.00%.",
            "deduplication": "One signal on a downward crossing; while the rolling return remains <= -1%, there is no repeat. A later signal requires a recovery above -1% followed by a new downward crossing.",
            "correlation_gate": "None; no QQQ/SPY correlation filter is applied.",
            "entry_timing": "Select options on the signal-day close and seek entry on the next common session, subject to exact-contract quotes and displayed-size checks.",
            "exit_policy": POLICY,
            "costs": "Existing replay assumptions: $0.05 per option-share per side plus $0.65 per contract per side."
        },
        "virtual_lock_definition": {
            "primary_condition": "After each trade's entry, SPY must never close below 90% of its own entry-date close until the resolved exit date.",
            "mechanism": "Ex-post path conditioning only; trades that breach the floor are excluded from the primary conditional subset rather than liquidated at -10%. No hypothetical stop P&L is applied.",
            "observation": "Daily close prices on common QQQ/SPY sessions; intraday breaches can be missed.",
        },
        "ratio_arms": {
            "1x3": "1 QQQ LONG PUT : 3 SPY SHORT PUTs; QQQ reference abs-Delta 0.60-0.70.",
            "1x6": "1 QQQ LONG PUT : 6 SPY SHORT PUTs; QQQ reference abs-Delta 0.60-0.70.",
            "2x6": "2 same-expiry lower-premium QQQ LONG PUTs targeting 50% of the 1x6 reference unit ask, : 6 SPY SHORT PUTs; reference expiry/SPY selector locked, alternative QQQ Delta unconstrained.",
            "2x6_samecontract": "2 QQQ LONG PUTs of the exact 1x6 reference contract, : 6 SPY SHORT PUTs, only where displayed size permits."
        },
        "source": {
            "repository": "anahatsingh-ui/options-dataset-hist",
            "tree_commit": "37f6c456fe1a4775c875673fb8ef907d5cd2fd66",
            "underlying_prices": "QQQ and SPY underlying_prices.parquet, downloaded/hash-verified by engine when absent"
        },
        "run_stats": run_stats,
        "condition_summary": summaries,
        "limitations": [
            "The 10% entry-price floor is a hindsight filter, not a rule known at entry. This report does not model liquidating any option leg when SPY breaches the floor.",
            "All P&L is a historical end-of-day quote-side estimate, not a verified multi-leg fill.",
            "Cohorts overlap; episode sums and episode-sums-per-year are not account NAV returns or CAGR.",
            "No account capital, assignment cash, margin, forced liquidation, financing, tax or portfolio NAV model.",
            "SPY close data are price closes, not dividend-adjusted total returns; intraday floor breaches can be missed.",
            "Unresolved episodes and resolved episodes with missing path data are not included in P&L summary statistics."
        ]
    }
    (out / "summary.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    lines = [
        "# SPY weekly -1% trigger + per-trade virtual -10% entry-price floor",
        "",
        f"Window: {START} to {END} ({YEARS:.3f} years). Trigger is a downward crossing of SPY rolling 5-common-session close return through -1%; no correlation gate.",
        "",
        "Each primary conditional trade must have SPY remain at or above 90% of its own entry-date close for the whole entry-to-exit path. This is ex-post path conditioning, not an executable stop or an entry filter.",
        "",
        "## Trigger and path coverage",
        "",
        "| Ratio | Signals | Entered | Skipped | Resolved | Unresolved | Breached SPY floor | Pass virtual lock |",
        "|---|---:|---:|---:|---:|---:|---:|---:|"
    ]
    display = {"1x3": "1:3", "1x6": "1:6", "2x6": "2:6 half-premium", "2x6_samecontract": "2:6 same contract"}
    for ratio in ARMS:
        z = run_stats[ratio]
        lines.append(f"| {display[ratio]} | {z.get('selected_signals')} | {z.get('entered_cohorts')} | {z.get('entry_skipped')} | {z.get('resolved')} | {z.get('unresolved')} | {z.get('resolved_breached_10pct_floor')} | {z.get('virtual_lock_10pct_pass', {}).get('resolved_n')} |")
    lines += [
        "",
        "## P&L comparison",
        "",
        "P&L includes the existing replay costs. 'Annual-average episode sum' is conditional episode P&L divided by the complete study period; it is not an account return or CAGR. Because cohorts overlap, sums cannot be compounded as account NAV.",
        "",
        "| Ratio | Condition | N resolved | Sum episode P&L | Mean / episode | Median / episode | Win rate | Profit factor | Worst episode |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|"
    ]
    for z in summaries:
        fmt = lambda v: "n/a" if v is None else "USD " + format(v, ",.2f")
        win = "n/a" if z["win_rate_pct"] is None else f'{z["win_rate_pct"]:.2f}%'
        pf = "n/a" if z["profit_factor"] is None else str(z["profit_factor"])
        lines.append(f"| {display[z['ratio']]} | {z['condition']} | {z['resolved_n']} | {fmt(z['cumulative_episode_pnl_usd'])} | {fmt(z['mean_per_episode_usd'])} | {fmt(z['median_per_episode_usd'])} | {win} | {pf} | {fmt(z['worst_episode_usd'])} |")
    lines += [
        "",
        "## Interpretation constraints",
        "",
        "- The key question is conditional P&L for the trades whose SPY path did not breach -10% from the individual entry close; the 'all resolved' arm is shown only as a baseline.",
        "- The virtual lock excludes paths that breached -10%; it does not simulate a stop-out, and it does not guarantee the option strategy itself loses no more than 10%.",
        "- The option positions are QQQ puts versus SPY short puts; a 10% SPY floor is not a loss cap on the option portfolio.",
        "- Quotes, contract availability and displayed size are historical snapshots, not proof of executable multi-leg fills.",
        "",
        "Artifacts: summary.json and episode_classification.csv."
    ]
    (out / "REF_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": "COMPLETED", "condition_rows": len(summaries), "run_stats": {
        ratio: {k: v for k, v in run_stats[ratio].items() if k not in ("all_resolved", "virtual_lock_10pct_pass")}
        | {"all_resolved": run_stats[ratio]["all_resolved"], "virtual_lock_10pct_pass": run_stats[ratio]["virtual_lock_10pct_pass"]}
        for ratio in ARMS}}, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
