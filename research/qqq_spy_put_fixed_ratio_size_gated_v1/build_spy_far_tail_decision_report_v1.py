#!/usr/bin/env python3
"""Build a reproducible report comparing SPY far-tail hedge costs and protection."""
from __future__ import annotations
import argparse, csv, json, statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

TAIL = {"TAIL_025_DELTA": "2.5-delta (Put Delta about −0.025)", "TAIL_05_DELTA": "5-delta (about −0.05)", "TAIL_10_DELTA": "10-delta (about −0.10)"}
POLICY = {"HOLD_10_OR_DTE_LE_7": "Hold 10 / DTE≤7", "HOLD_20_OR_DTE_LE_7": "Hold 20 / DTE≤7"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"Missing or empty input: {path}")
    return rows


def num(row: dict[str, Any], key: str) -> float | None:
    try:
        value = float(row.get(key, ""))
        return value if value == value and abs(value) != float("inf") else None
    except (TypeError, ValueError):
        return None


def median(values: Iterable[float | int | None]) -> float | None:
    clean = [float(v) for v in values if v is not None]
    return statistics.median(clean) if clean else None


def bounds(values: Iterable[float | int | None]) -> tuple[float | None, float | None]:
    clean = [float(v) for v in values if v is not None]
    return (min(clean), max(clean)) if clean else (None, None)


def money(value: float | int | None) -> str:
    if value is None:
        return "—"
    value = float(value)
    prefix = "−$" if value < 0 else "$"
    return prefix + f"{abs(value):,.2f}"


def span(lo: float | int | None, hi: float | int | None) -> str:
    return "—" if lo is None or hi is None else f"{lo:g}–{hi:g}"


def summarize(rows: list[dict[str, str]], fields: dict[str, str]) -> dict[str, Any]:
    out: dict[str, Any] = {"n_phases": len(rows)}
    for label, field in fields.items():
        values = [num(row, field) for row in rows]
        lo, hi = bounds(values)
        out[label + "_min"], out[label + "_max"], out[label + "_median"] = lo, hi, median(values)
    return out


def config_summary(rows: list[dict[str, str]]) -> dict[str, Any]:
    result = summarize(rows, {
        "paired_n": "joint_resolved_paired_n",
        "coverage": "paired_coverage_pct_of_base_resolved",
        "base_mean": "paired_baseline_mean_net_usd",
        "hedged_mean": "paired_hedged_mean_net_usd",
        "increment": "paired_mean_incremental_hedge_usd",
        "base_win": "paired_baseline_win_rate_pct",
        "hedged_win": "paired_hedged_win_rate_pct",
        "base_worst": "paired_baseline_worst_trade_usd",
        "hedged_worst": "paired_hedged_worst_trade_usd",
        "loss_improved": "baseline_losses_improved_n",
        "loss_turned_positive": "baseline_losses_turned_positive_n",
    })
    improvements = [
        num(row, "paired_hedged_worst_trade_usd") - num(row, "paired_baseline_worst_trade_usd")
        for row in rows if num(row, "paired_hedged_worst_trade_usd") is not None and num(row, "paired_baseline_worst_trade_usd") is not None
    ]
    result["worst_improvement_median"] = median(improvements)
    return result


def annual_summary(rows: list[dict[str, str]]) -> dict[str, Any]:
    return summarize(rows, {
        "paired_n": "paired_n",
        "coverage": "paired_coverage_pct_of_base_resolved",
        "base_mean": "no_hedge_mean_paired_usd",
        "hedged_mean": "hedged_mean_paired_usd",
        "increment": "mean_incremental_hedge_usd",
        "base_worst": "no_hedge_worst_paired_usd",
        "hedged_worst": "hedged_worst_paired_usd",
    })


def stress_summary(rows: list[dict[str, str]]) -> dict[str, Any]:
    return summarize(rows, {
        "n": "eligible_entry_cohorts",
        "base_mean": "mean_short_spy_sleeve_net_usd",
        "hedged_mean": "mean_hedged_spy_sleeve_net_usd",
        "increment": "mean_tail_increment_usd",
        "base_worst": "worst_short_spy_sleeve_net_usd",
        "hedged_worst": "worst_hedged_spy_sleeve_net_usd",
        "improved_pct": "fraction_hedge_improves_short_sleeve_pct",
    })


def build_report(results: Path) -> str:
    manifest = json.loads((results / "manifest.json").read_text(encoding="utf-8"))
    summary = read_csv(results / "summary.csv")
    annual = read_csv(results / "annual_pnl_by_phase.csv")
    stress = read_csv(results / "stress_grid.csv")
    if manifest.get("status") != "COMPLETED" or manifest.get("summary_rows") != len(summary):
        raise ValueError("Manifest status or summary row count check failed")
    if not any(row.get("tail_label") == "TAIL_025_DELTA" for row in summary):
        raise ValueError("2.5-delta data missing")

    grouped: dict[tuple[str, str, str, int], list[dict[str, str]]] = defaultdict(list)
    for row in summary:
        grouped[(row["arm"], row["policy"], row["tail_label"], int(float(row["tail_quantity"])))].append(row)
    metrics = {key: config_summary(rows) for key, rows in grouped.items()}
    primary = {(delta, qty): metrics[("DTE45", "HOLD_20_OR_DTE_LE_7", delta, qty)]
               for delta in TAIL for qty in (1, 3)}
    annual_groups: dict[tuple[str, str, int], list[dict[str, str]]] = defaultdict(list)
    for row in annual:
        if row["arm"] == "DTE45" and row["policy"] == "HOLD_20_OR_DTE_LE_7" and row["tail_label"] in ("TAIL_025_DELTA", "TAIL_05_DELTA"):
            annual_groups[(row["pnl_year_exit_date"], row["tail_label"], int(float(row["tail_quantity"])))].append(row)
    stress_groups: dict[tuple[str, int, float], list[dict[str, str]]] = defaultdict(list)
    for row in stress:
        shock = float(row["spy_shock_pct"])
        if row["arm"] == "DTE45" and shock in (-10.0, -20.0, -30.0, -50.0, -100.0):
            stress_groups[(row["tail_label"], int(float(row["tail_quantity"])), shock)].append(row)

    base_sha = manifest.get("base_anchor_commit", "unknown")
    source_sha = manifest.get("source_tree_commit", "unknown")
    last_date = manifest.get("stream_stats", {}).get("last_chain_date", "unknown")
    a, b, c = primary[("TAIL_025_DELTA", 1)], primary[("TAIL_05_DELTA", 1)], primary[("TAIL_10_DELTA", 1)]
    a3, b3, c3 = primary[("TAIL_025_DELTA", 3)], primary[("TAIL_05_DELTA", 3)], primary[("TAIL_10_DELTA", 3)]
    lines = [
        "# SPY Far-Tail Hedge — Full Decision Report V1", "",
        "> Research-only report generated from completed, source-pinned replay outputs. Report date: 2026-10-24.", "",
        "## 1. Decision", "",
        "**Do not adopt unconditional far-tail PUT buying as the default entry overlay on current evidence.** It offsets modeled SPY short-put sleeve losses in severe expiry shocks, but recurring hedge cost reduces average realized P&L in most calendar years. The next experiment should test pre-declared, risk-triggered hedging against the frozen baseline; this report does not authorize live execution.", "",
        "### Main findings", "",
        f"- DTE45 / Hold-20 / 2.5-delta / 1x: median incremental P&L {money(a['increment_median'])} per paired trade (phase range {money(a['increment_min'])} to {money(a['increment_max'])}); paired coverage median {a['coverage_median']:.2f}% ({a['coverage_min']:.2f}–{a['coverage_max']:.2f}%).",
        f"- Comparable 5-delta / 1x: median incremental P&L {money(b['increment_median'])}, coverage median {b['coverage_median']:.2f}%. Extra drag relative to 2.5-delta is approximately {money(abs(b['increment_median']) - abs(a['increment_median']))} per paired episode using the phase medians.",
        f"- With 3 contracts, median incremental P&L is {money(a3['increment_median'])} (2.5-delta), {money(b3['increment_median'])} (5-delta), and {money(c3['increment_median'])} (10-delta) per paired episode.",
        f"- Phase-median worst paired-trade improvement is {money(a['worst_improvement_median'])} for 2.5-delta / 1x and {money(a3['worst_improvement_median'])} for 2.5-delta / 3x. This is trade-level evidence, not portfolio maximum drawdown.",
        "- 2020 is the clearest favorable historical year for the hedge; many other years give back P&L through carry cost. Do not extrapolate a crisis year into a stable annual income estimate.",
        "",
        "### Current research status", "",
        "| Candidate | Assessment |",
        "|---|---|",
        "| Unconditional hedge on every base entry | Not supported by average-P&L evidence |",
        "| 2.5-delta, 1 contract | Lower carry among tested DTE45/Hold-20 cases; lower quote coverage; protection concentrated in deeper shocks |",
        "| 5-delta, 1 contract | Better quote coverage and stronger offset in some moderate/deep shocks, at higher carry |",
        "| 3 contracts | Stronger modeled deep-shock offset; materially larger drag and win-rate impact |",
        "| Live orders | Not performed; out of scope |",
        "",
        "## 2. Frozen setup and source lineage", "",
        f"- Baseline anchor commit: [{base_sha}](https://github.com/JUN-ZS/brush-timber-mountain-brook/commit/{base_sha}). Frozen baseline is QQQ LONG PUT 1 : SPY SHORT PUT 3, no entry filter, fixed 5-common-session cadence.",
        "- Arms: DTE14 and DTE45; exits: Hold 10 or Hold 20, with the DTE≤7 guard.",
        f"- Historical SPY chain source: [anahatsingh-ui/options-dataset-hist at {source_sha}](https://github.com/anahatsingh-ui/options-dataset-hist/tree/{source_sha}), with data through {last_date}. Hash pinning proves the file bytes match the referenced Git blobs; it does not independently prove OPRA provenance or executable fills.",
        f"- Replay size: {manifest['base_trade_ledger_count']:,} base ledger rows; {manifest['unique_base_cohort_count']:,} unique cohorts; {manifest['entry_selection_rows']:,} selection rows; {manifest['trade_level_rows']:,} trade-level rows; {manifest['summary_rows']:,} phase/config summary rows; {manifest['stress_grid_rows']:,} expiry stress rows.",
        "- Tail selection: same entry date and expiry as the base SPY short PUT; standard listed PUT; strike strictly below entry spot; valid quote and positive bid. Rank by nearest absolute Delta, then displayed ask size, open interest, relative spread and contract ID.",
        "- 2.5-delta (Put Delta about −0.025) and 5-delta (about −0.05) use the same absolute-Delta band 0.01–0.08. 10-delta (about −0.10) is a reference band 0.05–0.15. Quantities: one or three contracts.",
        "- Modeled friction: $0.05 per option share per side slippage plus $0.65 commission per contract per side. Tail buys enter at ask and exit at bid.",
        "",
        "## 3. All tested configurations", "",
        "Each row reports the median of five phase-level values plus min–max ranges. The shifted entry phases overlap; they are robustness checks, not independent samples. Mean P&L is USD per trade episode, not annual account profit.",
        "",
        "| Arm | Exit | Target | Qty | Paired N range | Coverage median (range) | Base mean median (range) | Hedged mean median (range) | Increment median (range) | Win rate base→hedge | Worst paired trade base→hedge | Losing trades improved / turned positive |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for (arm, policy, delta, qty), m in sorted(metrics.items()):
        lines.append(
            f"| {arm} | {POLICY[policy]} | {TAIL[delta]} | {qty} | {span(m['paired_n_min'], m['paired_n_max'])} "
            f"| {m['coverage_median']:.2f}% ({m['coverage_min']:.2f}–{m['coverage_max']:.2f}%) "
            f"| {money(m['base_mean_median'])} ({money(m['base_mean_min'])} to {money(m['base_mean_max'])}) "
            f"| {money(m['hedged_mean_median'])} ({money(m['hedged_mean_min'])} to {money(m['hedged_mean_max'])}) "
            f"| {money(m['increment_median'])} ({money(m['increment_min'])} to {money(m['increment_max'])}) "
            f"| {m['base_win_median']:.2f}%→{m['hedged_win_median']:.2f}% "
            f"| {money(m['base_worst_median'])}→{money(m['hedged_worst_median'])} "
            f"| {m['loss_improved_median']:.0f} / {m['loss_turned_positive_median']:.0f} |"
        )
    lines += [
        "",
        "Interpretation:", "",
        "- The main average comparison uses only resolved base trades with a quote-valid tail entry and exact-contract exit with sufficient displayed bid size. Coverage is less than 100% in some configurations, so quote-availability selection bias remains possible.",
        "- Base and hedged means in each row use the same paired trades. All-resolved baseline means are shown separately in the annual CSV and must not be compared directly with a paired hedged mean.",
        "- Worst-trade values are minima within the paired sample. A hedge can improve the worst trade while lowering the mean and win rate.",
        "- DTE14 Hold-10 and Hold-20 can produce identical outcomes where the DTE≤7 guard overrides the earlier hold limit.",
        "",
        "## 4. Annual comparison — DTE45 / Hold-20, 2.5-delta vs 5-delta", "",
        "Figures are medians across the five entry phases for each exit year, based on paired realized observations. Delta P&L = hedged minus no-hedge mean; positive is improvement and negative is carry drag.",
        "",
        "| Exit year | Target | Qty | Paired N range | Coverage median | No-hedge mean | Hedged mean | Delta mean P&L | Worst paired trade base→hedge |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for year in sorted({key[0] for key in annual_groups}):
        for delta in ("TAIL_025_DELTA", "TAIL_05_DELTA"):
            for qty in (1, 3):
                rows = annual_groups.get((year, delta, qty), [])
                if not rows:
                    continue
                m = annual_summary(rows)
                lines.append(
                    f"| {year} | {TAIL[delta]} | {qty} | {span(m['paired_n_min'], m['paired_n_max'])} "
                    f"| {m['coverage_median']:.2f}% | {money(m['base_mean_median'])} | {money(m['hedged_mean_median'])} "
                    f"| {money(m['increment_median'])} | {money(m['base_worst_median'])}→{money(m['hedged_worst_median'])} |"
                )
    lines += [
        "",
        "These are per-trade averages grouped by exit year, not total yearly USD, account returns, CAGR or withdrawal capacity. Paired sample sizes vary by target and quantity.",
        "",
        "## 5. Expiry shock grid — SPY short-put sleeve only", "",
        "This is an intrinsic payoff scenario from each entry spot to expiry—not a historical path replay, forecast or probability. It excludes QQQ long-PUT payoff, exit time value, assignment/exercise fees, financing, margin and forced liquidation. Figures are phase medians.",
        "",
        "| SPY shock at expiry | Target | Qty | Mean unhedged sleeve | Mean hedged sleeve | Increment | Worst unhedged→hedged | Phases improved |",
        "|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for shock in (-10.0, -20.0, -30.0, -50.0, -100.0):
        for delta in ("TAIL_025_DELTA", "TAIL_05_DELTA", "TAIL_10_DELTA"):
            for qty in (1, 3):
                rows = stress_groups.get((delta, qty, shock), [])
                if not rows:
                    continue
                m = stress_summary(rows)
                lines.append(
                    f"| {shock:.0f}% | {TAIL[delta]} | {qty} | {money(m['base_mean_median'])} | {money(m['hedged_mean_median'])} "
                    f"| {money(m['increment_median'])} | {money(m['base_worst_median'])}→{money(m['hedged_worst_median'])} "
                    f"| {m['improved_pct_median']:.2f}% |"
                )
    lines += [
        "",
        "The very far-OTM PUT may not offset its carrying cost in a modest decline; its modeled payoff grows only after spot crosses the tail strike. Three long PUTs align with the three short SPY PUTs and have a much larger deep-shock offset, but cost more and do not make the full QQQ/SPY book safe.",
        "",
        "## 6. Findings and next research gate", "",
        "1. **No unconditional hedge default yet.** In DTE45/Hold-20, median incremental P&L across phases is negative for all tested Delta targets at both sizes over the full sample.",
        "2. **2.5-delta / 1x is the lower-carry candidate, not a proven winner.** It generally drags less average P&L but has lower paired coverage and is less effective before a deeper fall.",
        "3. **5-delta / 1x is a reasonable comparator.** Its extra carry should only be accepted if the extra realized or scenario downside offset is worth it to the user’s risk budget.",
        "4. **Three contracts behave more like disaster insurance than return enhancement.** They improve more severe expiry shock results while materially reducing average P&L and, often, win rate.",
        "5. **Next experiment:** evaluate pre-declared risk-triggered hedge rules against no hedge and unconditional 1x candidates. Do not tune on the same years used to claim success; report protected vs unprotected years, hedge spend, quote coverage, worst trade and portfolio NAV/margin before any deployment decision.",
        "",
        "## 7. Limitations", "",
        "- End-of-day quotes and displayed sizes are not verified fills; a size gate is not execution evidence.",
        "- Unresolved base trades remain unresolved; tail marks are not silently counted as realized P&L.",
        "- Hashes prove byte identity against a Git mirror, not OPRA authenticity.",
        "- No shared NAV, concurrent-position allocation, margin calls, forced liquidation or assignment/early-exercise cost is modeled.",
        "- The stress grid covers only the SPY short-put sleeve, not the whole strategy's maximum drawdown.",
        "",
        "## 8. Reproducible artifacts", "",
        "- [Phase-level configuration summary](summary.csv)",
        "- [Matched trade-level ledger](trade_level.csv)",
        "- [Exact selected contracts and quote-size gates](entry_selection.csv)",
        "- [SPY expiry shock grid](stress_grid.csv)",
        "- [Year × phase × configuration values](annual_pnl_by_phase.csv)",
        "- [Annual phase robustness ranges](annual_pnl_robustness.csv)",
        "- [Annual summary report](annual_pnl_report.md)",
        "- [Completed replay Actions run](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/40088228452)",
        "- [Annual summary Actions run](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/40089381454)",
        "",
        "## 9. Core decision table — DTE45 / Hold-20", "",
        "| Target | Qty | Base paired mean | Hedged paired mean | Increment | Coverage median | Worst trade improvement |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for delta in ("TAIL_025_DELTA", "TAIL_05_DELTA", "TAIL_10_DELTA"):
        for qty in (1, 3):
            m = primary[(delta, qty)]
            lines.append(
                f"| {TAIL[delta]} | {qty} | {money(m['base_mean_median'])} | {money(m['hedged_mean_median'])} "
                f"| {money(m['increment_median'])} | {m['coverage_median']:.2f}% | {money(m['worst_improvement_median'])} |"
            )
    lines += ["", f"Frozen replay baseline: {base_sha}. Source chain through {last_date}. This research report does not place or recommend live orders.", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build_report(args.results_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    if len(report) < 10000 or "Annual comparison" not in report or "Expiry shock grid" not in report:
        raise ValueError("Report completeness check failed")
    print(json.dumps({"status": "COMPLETED", "report": str(args.output), "bytes": len(report.encode("utf-8"))}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
