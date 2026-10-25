#!/usr/bin/env python3
"""Condition weekly SPY -2% trigger cohorts on realized SPY drawdown paths."""
import argparse, csv, json, statistics
from collections import defaultdict
from datetime import date
from pathlib import Path
import qqq_spy_premium_matched_phase_v1 as eng

START, END = "2018-03-01", "2025-12-15"
YEARS = (date.fromisoformat(END)-date.fromisoformat(START)).days / 365.2425
POLICY = "HOLD_20_OR_DTE_LE_7"

def load_csv(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def read_prices(path, symbol):
    return eng.load_spots(path, symbol)

def summarize(rows, name, ratio):
    vals = [float(r["net_pnl_usd"]) for r in rows]
    annual_by_entry_year = defaultdict(float)
    for r in rows:
        annual_by_entry_year[str(r["entry_date"])[:4]] += float(r["net_pnl_usd"])
    return {
        "ratio": ratio, "condition": name, "resolved_n": len(vals),
        "cumulative_episode_pnl_usd": round(sum(vals), 2),
        "mean_per_episode_usd": round(statistics.mean(vals), 2) if vals else None,
        "median_per_episode_usd": round(statistics.median(vals), 2) if vals else None,
        "win_rate_pct": round(100 * sum(x > 0.005 for x in vals) / len(vals), 2) if vals else None,
        "worst_episode_usd": round(min(vals), 2) if vals else None,
        "best_episode_usd": round(max(vals), 2) if vals else None,
        "annual_average_episode_sum_usd": round(sum(vals) / YEARS, 2),
        "entry_year_pnl_usd": {k: round(v, 2) for k, v in sorted(annual_by_entry_year.items())},
        "CAGR": None,
        "CAGR_note": "Not calculated: episodes overlap and no capital-constrained account NAV is modeled."
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base", required=True, help="Parent folder containing ratio_1x3 and ratio_1x6")
    p.add_argument("--qqq-cache", required=True)
    p.add_argument("--spy-cache", required=True)
    args = p.parse_args()
    base = Path(args.base)
    out = base / "weekly_drop_2pct_path_conditioned"
    out.mkdir(parents=True, exist_ok=True)

    qspots = read_prices(Path(args.qqq_cache) / "underlying_prices.parquet", "QQQ")
    sspots = read_prices(Path(args.spy_cache) / "underlying_prices.parquet", "SPY")
    common = sorted(set(qspots) & set(sspots))
    peak, ath_dd = -float("inf"), {}
    for day in sorted(sspots):
        peak = max(peak, sspots[day])
        ath_dd[day] = sspots[day] / peak - 1.0

    detail, summaries, run_stats = [], [], {}
    for ratio in ("1x3", "1x6"):
        arm = base / ("ratio_" + ratio)
        run_summary = json.loads((arm / "summary.json").read_text(encoding="utf-8"))
        entries = {str(r["episode_id"]): r for r in load_csv(arm / "entry_cohort.csv")}
        trades = [r for r in load_csv(arm / "trade_episodes.csv") if r.get("policy") == POLICY]
        if not entries:
            run_stats[ratio] = {
                "scheduled_opportunities": run_summary.get("fixed_entry_schedule", {}).get("scheduled_opportunities"),
                "filter_qualified_sessions": run_summary.get("entry_filter", {}).get("qualified_sessions"),
                "selected_signals": run_summary.get("cohort", {}).get("selected_signals"),
                "entered_cohorts": run_summary.get("cohort", {}).get("entered_cohorts"),
                "entry_skipped": run_summary.get("cohort", {}).get("entry_skipped"),
                "resolved": 0, "unresolved": 0
            }
        else:
            run_stats[ratio] = {
                "scheduled_opportunities": run_summary.get("fixed_entry_schedule", {}).get("scheduled_opportunities"),
                "filter_qualified_sessions": run_summary.get("entry_filter", {}).get("qualified_sessions"),
                "selected_signals": run_summary.get("cohort", {}).get("selected_signals"),
                "entered_cohorts": run_summary.get("cohort", {}).get("entered_cohorts"),
                "entry_skipped": run_summary.get("cohort", {}).get("entry_skipped"),
                "resolved": sum(r.get("status") == "RESOLVED" for r in trades),
                "unresolved": sum(str(r.get("status", "")).startswith("UNRESOLVED") for r in trades)
            }
        if abs(float(run_summary["costs"]["base_slippage_per_option_share_usd"]) - 0.05) > 1e-9:
            raise ValueError("Unexpected slippage assumption")
        if abs(float(run_summary["costs"]["base_commission_per_contract_per_side_usd"]) - 0.65) > 1e-9:
            raise ValueError("Unexpected commission assumption")

        classified = []
        seen = set()
        for trade in trades:
            eid = str(trade.get("episode_id"))
            if eid in seen:
                raise ValueError(f"Duplicate selected-policy trade row {ratio}/{eid}")
            seen.add(eid)
            if trade.get("status") != "RESOLVED" or trade.get("net_pnl_usd") in (None, ""):
                continue
            entry = entries.get(eid)
            if entry is None:
                raise ValueError(f"Resolved episode missing entry metadata {ratio}/{eid}")
            start, end = entry.get("entry_date"), trade.get("exit_date")
            if not start or not end or start not in ath_dd or end not in ath_dd:
                raise ValueError(f"Missing path dates {ratio}/{eid}: {start}->{end}")
            path = [d for d in common if start <= d <= end]
            if not path:
                raise ValueError(f"Empty SPY path {ratio}/{eid}: {start}->{end}")
            max_dd_path = min(ath_dd[d] for d in path)
            min_return_entry = min(sspots[d] / sspots[start] - 1 for d in path)
            row = {
                "ratio": ratio, "episode_id": eid,
                "signal_date": entry.get("signal_date"), "entry_date": start, "exit_date": end,
                "spy_5d_return_at_signal_pct": entry.get("spy_trailing_return_pct"),
                "spy_previous_5d_return_pct": entry.get("spy_previous_trailing_return_pct"),
                "qqq_5d_return_at_signal_pct": entry.get("qqq_trailing_return_pct"),
                "qqq_spy_corr_prior_60d": entry.get("qqq_spy_corr_60d"),
                "spy_ath_drawdown_at_entry_pct": round(100 * ath_dd[start], 4),
                "spy_worst_ath_drawdown_during_episode_pct": round(100 * max_dd_path, 4),
                "spy_worst_return_from_entry_during_episode_pct": round(100 * min_return_entry, 4),
                "status": trade["status"], "net_pnl_usd": round(float(trade["net_pnl_usd"]), 2),
                "no_ath_breach_minus_10pct": bool(max_dd_path >= -0.10),
                "no_ath_breach_minus_15pct": bool(max_dd_path >= -0.15),
                "no_entry_loss_breach_minus_10pct": bool(min_return_entry >= -0.10),
                "no_entry_loss_breach_minus_15pct": bool(min_return_entry >= -0.15),
            }
            detail.append(row)
            classified.append(row)
        sums = [
            ("all_resolved_weekly_trigger_trades", lambda r: True),
            ("whole_holding_period_SPY_ATH_drawdown_not_below_minus_10pct", lambda r: r["no_ath_breach_minus_10pct"]),
            ("whole_holding_period_SPY_ATH_drawdown_not_below_minus_15pct", lambda r: r["no_ath_breach_minus_15pct"]),
            ("whole_holding_period_SPY_return_from_entry_not_below_minus_10pct", lambda r: r["no_entry_loss_breach_minus_10pct"]),
            ("whole_holding_period_SPY_return_from_entry_not_below_minus_15pct", lambda r: r["no_entry_loss_breach_minus_15pct"]),
        ]
        for label, pred in sums:
            summaries.append(summarize([r for r in classified if pred(r)], label, ratio))

    # Ensure summary contains all ratio/condition pairs even when no episodes passed a condition.
    with (out / "episode_classification.csv").open("w", newline="", encoding="utf-8") as f:
        fields = list(detail[0].keys()) if detail else [
            "ratio","episode_id","signal_date","entry_date","exit_date","spy_5d_return_at_signal_pct",
            "spy_previous_5d_return_pct","qqq_5d_return_at_signal_pct","qqq_spy_corr_prior_60d",
            "spy_ath_drawdown_at_entry_pct","spy_worst_ath_drawdown_during_episode_pct",
            "spy_worst_return_from_entry_during_episode_pct","status","net_pnl_usd",
            "no_ath_breach_minus_10pct","no_ath_breach_minus_15pct",
            "no_entry_loss_breach_minus_10pct","no_entry_loss_breach_minus_15pct"]
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(detail)

    result = {
        "schema": "weekly-spy-drop-2pct-conditioned-path-replay.v1",
        "status": "COMPLETED",
        "window": {"start": START, "end": END, "elapsed_years": round(YEARS, 6)},
        "trigger_definition": {
            "signal": "SPY close-to-close rolling 5-common-session return crosses from above -2.00% to <= -2.00%",
            "deduplication": "Only the first threshold-crossing day is a signal; no repeated entries while rolling 5-session return stays <= -2%. A later new signal requires the rolling return to recover above -2% and cross down again.",
            "entry": "Select option contracts at signal close, enter on the next common session when exact contract quotes and displayed size validate.",
            "correlation_filter": "Pearson correlation of prior 60 common-session daily close returns must be > 0; excludes signal-day return.",
            "same_contract_selector_as_REF": "Same expiry DTE 7-21, target 14; SPY short put abs Delta nearest 0.25; QQQ long put abs Delta 0.60-0.70 with Ask closest to 6x SPY Bid; use identical QQQ contract for 1:3 and 1:6.",
            "exit_policy": POLICY,
            "costs": "$0.05 per option-share per side plus $0.65 per contract per side"
        },
        "path_condition_definitions": {
            "no_ath_breach_minus_10pct": "From entry to exit every SPY close is at least 90% of SPY's running all-history close high; ex-post hypothetical condition",
            "no_ath_breach_minus_15pct": "From entry to exit every SPY close is at least 85% of SPY's running all-history close; ex-post hypothetical condition",
            "no_entry_loss_breach_minus_10pct": "From entry to exit SPY never closes 10% below its entry close; ex-post diagnostic",
            "no_entry_loss_breach_minus_15pct": "From entry to exit SPY never closes 15% below its entry close; ex-post diagnostic"
        },
        "correlation": {"full_period_daily_return_pearson": 0.935952,
                        "rolling_entry_correlation_is_lagged": True},
        "run_stats": run_stats, "condition_summary": summaries,
        "source": {"repository": "anahatsingh-ui/options-dataset-hist",
                   "tree_commit": "37f6c456fe1a4775c875673fb8ef907d5cd2fd66",
                   "qqq_underlying_file": "qqq/underlying_prices.parquet",
                   "spy_underlying_file": "spy/underlying_prices.parquet"},
        "limitations": [
            "Whole-holding-period path conditions use future prices and answer the requested counterfactual only; they are not implementable entry filters.",
            "P&L is the existing EOD quote-side replay, not verified fills.",
            "Cohorts overlap and capital is unconstrained. Cumulative episode P&L and the annualized episode sum are not an account NAV return or CAGR.",
            "SPY drawdown is close-based, not intraday; price closes are not dividend-total-return series.",
            "Unresolved cohorts are reported separately and excluded from resolved P&L statistics.",
            "No assignment cash, broker margin, forced liquidation, financing, tax, or portfolio NAV model."
        ]
    }
    (out / "summary.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    lines = [
        "# Weekly SPY -2% drop trigger + QQQ positive correlation — conditional path REF",
        "",
        f"Window {START} to {END}; {YEARS:.3f} years. Trigger: SPY rolling 5-session close return crosses from above -2% to <= -2%, and prior 60-session QQQ/SPY daily-return Pearson correlation is positive.",
        "",
        "Entry contracts are selected at the signal close; entry is next common session subject to exact-contract quote and displayed-size gates. Same DTE14 premium-matched contract selector and base costs as the existing REF. Exit: HOLD_20_OR_DTE_LE_7.",
        "",
        "## Trigger/run coverage",
        "",
        "| Ratio | Scheduled daily opportunities | Qualified signals | Entered cohorts | Entry skips | Resolved | Unresolved |",
        "|---|---:|---:|---:|---:|---:|---:|"
    ]
    for ratio in ("1x3", "1x6"):
        z=run_stats[ratio]
        lines.append(f"| {ratio.replace('x',':')} | {z.get('scheduled_opportunities')} | {z.get('selected_signals')} | {z.get('entered_cohorts')} | {z.get('entry_skipped')} | {z.get('resolved')} | {z.get('unresolved')} |")
    lines += [
        "",
        "## Conditional P&L (base strategy, no TAIL)",
        "",
        "Annual-average episode sum = each group's episode P&L / the full 7.792-year study window. This is explicitly not account CAGR. The whole-period no-breach groups are hindsight counterfactual subsets, as requested.",
        "",
        "| Ratio | Condition | N resolved | Sum episode P&L | Mean / episode | Median / episode | Win rate | Worst episode | Annual-average episode sum |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|"
    ]
    for z in summaries:
        def usd(v): return "n/a" if v is None else "USD "+format(v,",.2f")
        win="n/a" if z["win_rate_pct"] is None else format(z["win_rate_pct"],".2f")+"%"
        lines.append(f"| {z['ratio'].replace('x',':')} | {z['condition']} | {z['resolved_n']} | {usd(z['cumulative_episode_pnl_usd'])} | {usd(z['mean_per_episode_usd'])} | {usd(z['median_per_episode_usd'])} | {win} | {usd(z['worst_episode_usd'])} | {usd(z['annual_average_episode_sum_usd'])} |")
    lines += [
        "",
        "## Interpretation",
        "",
        "- The weekly 2% drop is an implementable event trigger with positive lagged QQQ/SPY correlation; the whole-period no-breach rule is NOT available at entry.",
        "- SPY ATH drawdown uses a running close high-water mark from the earliest source date (1999), avoiding a reset at 2018. Intraday breaches may be missed.",
        "- Episodes overlap and portfolio capital/margin are not constrained; these metrics cannot be converted to compound account CAGR.",
        "- Daily close return correlation was 0.935952 in the full historical period; this descriptive full-period result is not used as a look-ahead gate.",
        "",
        "Artifacts: episode_classification.csv, summary.json. No orders or main-branch changes."
    ]
    (out / "REF_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status":"COMPLETED","summary_rows":len(summaries),"classified_resolved":len(detail),
                      "run_stats":run_stats},indent=2))

if __name__ == "__main__":
    main()
