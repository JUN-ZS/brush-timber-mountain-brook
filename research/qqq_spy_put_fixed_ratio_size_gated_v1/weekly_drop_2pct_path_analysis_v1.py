#!/usr/bin/env python3
"""Condition weekly SPY -2% trigger cohorts on realized SPY drawdown paths."""
import argparse, csv, json, statistics
from collections import defaultdict
from datetime import date
from pathlib import Path
import qqq_spy_put_premium_matched_phase_v1 as eng

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
    # Baseline prices are paired by signal date, so the 2:6 arm can show whether
    # the lower-premium QQQ contract actually achieved the intended half-price.
    reference_unit_ask_by_signal = {}
    ref_entry_path = base / "ratio_1x6" / "entry_cohort.csv"
    if ref_entry_path.exists():
        for ref_row in load_csv(ref_entry_path):
            try:
                reference_unit_ask_by_signal[str(ref_row["signal_date"])] = float(ref_row["qqq_entry_ask"]) * 100
            except (KeyError, TypeError, ValueError):
                continue

    for ratio in ("1x3", "1x6", "2x6"):
        arm = base / ("ratio_" + ratio)
        run_summary = json.loads((arm / "summary.json").read_text(encoding="utf-8"))
        entry_rows = load_csv(arm / "entry_cohort.csv")
        entries = {str(r["episode_id"]): r for r in entry_rows}
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

        q_unit_prices = []
        q_total_debits = []
        spy_total_credits = []
        entry_deltas = []
        unit_reductions_vs_baseline = []
        for e in entry_rows:
            try:
                q_unit = float(e["qqq_entry_ask"]) * 100
                q_qty = int(e["long_qqq_qty"])
                s_qty = int(e["short_spy_qty"])
                spy_bid = float(e["spy_entry_bid"])
                q_unit_prices.append(q_unit)
                q_total_debits.append(q_unit * q_qty)
                spy_total_credits.append(spy_bid * 100 * s_qty)
                delta = float(e.get("qqq_abs_delta_entry") or e.get("qqq_abs_delta") or "")
                if 0 <= delta <= 1:
                    entry_deltas.append(delta)
                ref_price = reference_unit_ask_by_signal.get(str(e.get("signal_date")))
                if ref_price and ref_price > 0:
                    unit_reductions_vs_baseline.append(100 * (1 - q_unit / ref_price))
            except (KeyError, TypeError, ValueError):
                continue
        settings = run_summary.get("ratio", {})
        selector = run_summary.get("selection", {})
        run_stats[ratio].update({
            "qqq_long_contracts": settings.get("fixed_long_qqq_contracts"),
            "spy_short_contracts": settings.get("fixed_short_spy_contracts"),
            "qqq_reference_selector_spy_bid_multiple": selector.get("qqq_premium_match_short_qty"),
            "qqq_reference_premium_fraction": selector.get("qqq_reference_premium_fraction"),
            "qqq_entry_unit_premium_mean_usd": round(statistics.mean(q_unit_prices), 2) if q_unit_prices else None,
            "qqq_entry_unit_premium_median_usd": round(statistics.median(q_unit_prices), 2) if q_unit_prices else None,
            "qqq_total_entry_debit_mean_usd": round(statistics.mean(q_total_debits), 2) if q_total_debits else None,
            "spy_total_entry_credit_mean_usd": round(statistics.mean(spy_total_credits), 2) if spy_total_credits else None,
            "qqq_abs_delta_entry_mean": round(statistics.mean(entry_deltas), 4) if entry_deltas else None,
            "qqq_unit_premium_reduction_vs_1x6_mean_pct": round(statistics.mean(unit_reductions_vs_baseline), 2) if unit_reductions_vs_baseline else None,
            "price_comparison_n": len(unit_reductions_vs_baseline)
        })
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
            q_entry_unit_usd = float(entry.get("qqq_entry_ask") or 0) * 100
            q_qty = int(entry.get("long_qqq_qty") or 1)
            ref_unit_usd = reference_unit_ask_by_signal.get(str(entry.get("signal_date")))
            q_signal_unit_usd = float(entry.get("qqq_signal_ask") or 0) * 100
            q_ref_signal_unit_usd = float(entry.get("qqq_premium_reference_ask_signal") or 0) * 100
            q_entry_delta = entry.get("qqq_abs_delta_entry") or entry.get("qqq_abs_delta")
            row = {
                "ratio": ratio, "episode_id": eid,
                "signal_date": entry.get("signal_date"), "entry_date": start, "exit_date": end,
                "qqq_contract_id": entry.get("qqq_contract_id"),
                "qqq_strike": entry.get("qqq_strike"),
                "qqq_abs_delta_at_signal": entry.get("qqq_abs_delta"),
                "qqq_abs_delta_at_entry": q_entry_delta,
                "qqq_unit_ask_at_signal_usd": round(q_signal_unit_usd, 2),
                "qqq_reference_unit_ask_at_signal_usd": round(q_ref_signal_unit_usd, 2) if q_ref_signal_unit_usd else None,
                "qqq_unit_ask_at_entry_usd": round(q_entry_unit_usd, 2),
                "qqq_total_long_put_debit_at_entry_usd": round(q_entry_unit_usd * q_qty, 2),
                "qqq_reference_1x6_unit_ask_at_entry_usd": round(ref_unit_usd, 2) if ref_unit_usd else None,
                "qqq_unit_premium_reduction_vs_1x6_pct": round(100 * (1 - q_entry_unit_usd / ref_unit_usd), 2) if ref_unit_usd else None,
                "qqq_half_premium_target_usd": round(q_ref_signal_unit_usd * float(entry.get("qqq_reference_premium_fraction") or 1), 2) if q_ref_signal_unit_usd else None,
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
        "run_stats": run_stats,
        "condition_summary": summaries,
        "premium_and_sizing_diagnostics": {
            "reference_arm": "1x6",
            "paired_by": "signal_date",
            "purpose": "Check whether two lower-premium QQQ contracts approximate the single baseline QQQ put premium debit while exposing any Delta/price mismatch."
        },
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
    for ratio in ("1x3", "1x6", "2x6"):
        z=run_stats[ratio]
        lines.append(f"| {ratio.replace('x',':')} | {z.get('scheduled_opportunities')} | {z.get('selected_signals')} | {z.get('entered_cohorts')} | {z.get('entry_skipped')} | {z.get('resolved')} | {z.get('unresolved')} |")
    lines += [
        "",
        "## QQQ unit premium and hedge sizing",
        "",
        "The 2:6 arm selects an alternative same-expiry QQQ put at approximately half the signal-time Ask of the existing 1:6 reference contract, then buys two contracts. The alternative QQQ Delta is intentionally unconstrained, because cheaper contracts generally change hedge sensitivity. Entry unit premium and total debit are measured from next-session entry Ask quotes.",
        "",
        "| Ratio | QQQ long : SPY short | QQQ reference multiple | Mean QQQ premium / contract | Median QQQ premium / contract | Mean total QQQ debit | Mean SPY short credit | Mean QQQ |Delta| at entry | Mean unit-premium reduction vs 1:6 | Paired N |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
    ]
    for ratio in ("1x3", "1x6", "2x6"):
        z = run_stats[ratio]
        def usd2(v): return "n/a" if v is None else "USD " + format(v, ",.2f")
        reduction = "n/a" if z.get("qqq_unit_premium_reduction_vs_1x6_mean_pct") is None else f"{z['qqq_unit_premium_reduction_vs_1x6_mean_pct']:.2f}%"
        multiple = "n/a" if z.get("qqq_reference_selector_spy_bid_multiple") is None else str(z["qqq_reference_selector_spy_bid_multiple"])
        delta = "n/a" if z.get("qqq_abs_delta_entry_mean") is None else f"{z['qqq_abs_delta_entry_mean']:.3f}"
        lines.append(f"| {ratio.replace('x',':')} | {z.get('qqq_long_contracts')} : {z.get('spy_short_contracts')} | {multiple}x | {usd2(z.get('qqq_entry_unit_premium_mean_usd'))} | {usd2(z.get('qqq_entry_unit_premium_median_usd'))} | {usd2(z.get('qqq_total_entry_debit_mean_usd'))} | {usd2(z.get('spy_total_entry_credit_mean_usd'))} | {delta} | {reduction} | {z.get('price_comparison_n')} |")
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
        "Artifacts: episode_classification.csv, summary.json. The 2:6 arm is compared with the original 1:6 arm on the same signal dates; no orders or main-branch changes."
    ]
    (out / "REF_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status":"COMPLETED","summary_rows":len(summaries),"classified_resolved":len(detail),
                      "run_stats":run_stats},indent=2))

if __name__ == "__main__":
    main()
