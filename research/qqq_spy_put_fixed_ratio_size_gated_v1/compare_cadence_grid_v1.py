#!/usr/bin/env python3
"""Audit cadence, overlapping exposure and P&L across fixed QQQ/SPY put ratios."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any

RATIOS = {
    "1:6": ("fixed_1_6", 1, 6),
    "4:5": ("fixed_4_5", 4, 5),
    "2:4": ("fixed_2_4", 2, 4),
    "1:3": ("fixed_1_3", 1, 3),
}
FILTERS = ("none", "qqq_underperforms_spy_20d")
STRIDES = (5, 10, 15, 20, 30, 45)
POLICIES = ("HOLD_5_SESSIONS", "HOLD_10_SESSIONS", "HOLD_20_SESSIONS", "EXIT_AT_DTE_LE_7")
WINDOWS = (
    ("1Y", date(2024, 7, 23), date(2025, 7, 23), 1.0),
    ("3Y", date(2022, 7, 23), date(2025, 7, 23), 3.0),
    ("5Y", date(2020, 7, 23), date(2025, 7, 23), 5.0),
)
CUTOFF = date(2025, 7, 23)
WIN_EPSILON = 0.005
POLICY_LABELS = {
    "HOLD_5_SESSIONS": "5d",
    "HOLD_10_SESSIONS": "10d",
    "HOLD_20_SESSIONS": "20d",
    "EXIT_AT_DTE_LE_7": "DTE<=7",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def number(value: Any) -> float | None:
    try:
        x = float(value)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def as_date(value: Any) -> date | None:
    try:
        return date.fromisoformat(str(value or "")[:10])
    except (TypeError, ValueError):
        return None


def unique_cohorts(rows: list[dict[str, str]], id_field: str = "episode_id",
                   date_field: str = "signal_date") -> dict[str, date]:
    result: dict[str, date] = {}
    for row in rows:
        episode_id = str(row.get(id_field) or "")
        day = as_date(row.get(date_field))
        if not episode_id or day is None:
            continue
        if episode_id in result and result[episode_id] != day:
            raise ValueError(f"cohort {episode_id} has inconsistent signal dates")
        result[episode_id] = day
    return result


def peak_overlapping_exposure(trades: list[dict[str, str]]) -> tuple[int, float]:
    """Sweep daily entry/exit events; assignment obligation is a gross-exposure proxy."""
    events: dict[date, list[float]] = defaultdict(lambda: [0.0, 0.0])
    for row in trades:
        entry_day = as_date(row.get("entry_date")) or as_date(row.get("signal_date"))
        end_day = as_date(row.get("exit_date")) or as_date(row.get("last_observed_date"))
        if entry_day is None or end_day is None or end_day < entry_day:
            continue
        obligation = number(row.get("spy_put_strike_assignment_obligation_usd")) or 0.0
        events[entry_day][0] += 1
        events[entry_day][1] += obligation
        after_end = end_day + timedelta(days=1)
        events[after_end][0] -= 1
        events[after_end][1] -= obligation
    active_count = 0
    active_obligation = 0.0
    peak_count = 0
    peak_obligation = 0.0
    for day in sorted(events):
        delta_count, delta_obligation = events[day]
        active_count += int(delta_count)
        active_obligation += delta_obligation
        peak_count = max(peak_count, active_count)
        peak_obligation = max(peak_obligation, active_obligation)
    return peak_count, round(peak_obligation, 2)


def load_case(root: Path, filter_name: str, stride: int, ratio: str) -> dict[str, Any]:
    folder, long_qty, short_qty = RATIOS[ratio]
    path = root / "cadence_grid" / filter_name / f"stride_{stride}" / folder
    required = ("summary.json", "entry_cohort.csv", "entry_skips.csv", "trade_episodes.csv")
    for name in required:
        if not (path / name).is_file():
            raise FileNotFoundError(f"Missing required cadence replay output: {path / name}")
    summary_path = path / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    selection = summary.get("selection", {})
    if selection.get("cohort_stride_sessions") != stride:
        raise ValueError(f"{path}: requested stride {stride}, found {selection.get('cohort_stride_sessions')}")
    if selection.get("allow_overlapping_cohorts") is not True:
        raise ValueError(f"{path}: overlap mode not enabled; do not use a serialized replay as cadence evidence")
    if summary.get("entry_filter", {}).get("name") != filter_name:
        raise ValueError(f"{path}: entry-filter mismatch")
    actual_long = summary.get("ratio", {}).get("fixed_long_qqq_contracts")
    actual_short = summary.get("ratio", {}).get("fixed_short_spy_contracts")
    if (actual_long, actual_short) != (long_qty, short_qty):
        raise ValueError(f"{path}: fixed ratio mismatch {(actual_long, actual_short)} != {(long_qty, short_qty)}")
    entered_rows = read_csv(path / "entry_cohort.csv")
    skipped_rows = read_csv(path / "entry_skips.csv")
    trades = read_csv(path / "trade_episodes.csv")
    entered = unique_cohorts(entered_rows)
    skipped = unique_cohorts(skipped_rows)
    overlap = set(entered) & set(skipped)
    if overlap:
        raise ValueError(f"{path}: episodes both entered and skipped: {sorted(overlap)}")
    if len(entered) != summary.get("cohort", {}).get("entered_cohorts"):
        raise ValueError(f"{path}: entry-cohort CSV count does not match summary")
    if len(skipped) != summary.get("cohort", {}).get("entry_skipped"):
        raise ValueError(f"{path}: entry-skip CSV count does not match summary")
    selected = {**entered, **skipped}
    sha = hashlib.sha256(summary_path.read_bytes()).hexdigest()
    return {
        "path": str(path), "summary": summary, "entered": entered, "skipped": skipped,
        "selected": selected, "trades": trades, "summary_sha256": sha,
        "ratio": ratio, "filter": filter_name, "stride": stride,
    }


def summarize_period(case: dict[str, Any], window: str, start: date, end: date,
                     years: float, policy: str) -> dict[str, Any]:
    selected = {k: d for k, d in case["selected"].items() if start <= d <= end}
    entered = {k: d for k, d in case["entered"].items() if start <= d <= end}
    skipped = {k: d for k, d in case["skipped"].items() if start <= d <= end}
    episode_rows = [
        row for row in case["trades"]
        if row.get("policy") == policy and str(row.get("episode_id") or "") in entered
    ]
    resolved = [
        row for row in episode_rows
        if row.get("status") == "RESOLVED" and number(row.get("net_pnl_usd")) is not None
    ]
    pnl = [float(number(row.get("net_pnl_usd"))) for row in resolved]
    wins = sum(x > WIN_EPSILON for x in pnl)
    losses = sum(x < -WIN_EPSILON for x in pnl)
    flats = len(pnl) - wins - losses
    gross_positive = sum(x for x in pnl if x > WIN_EPSILON)
    gross_negative = sum(x for x in pnl if x < -WIN_EPSILON)
    stress = []
    for row in resolved:
        value = number(row.get("net_pnl_usd"))
        long_qty = number(row.get("long_qqq_qty"))
        short_qty = number(row.get("short_spy_qty"))
        if value is not None and long_qty is not None and short_qty is not None:
            stress.append(value - 10.0 * (long_qty + short_qty))
    active_episode_ids = set(entered)
    exposure_rows = [
        row for row in episode_rows if str(row.get("episode_id") or "") in active_episode_ids
    ]
    peak_count, peak_obligation = peak_overlapping_exposure(exposure_rows)
    ids_resolved = {str(row.get("episode_id") or "") for row in resolved}
    unresolved = len(active_episode_ids - ids_resolved)
    mean_pnl = statistics.mean(pnl) if pnl else None
    return {
        "window": window, "start": start.isoformat(), "end": end.isoformat(),
        "years": years, "filter": case["filter"], "stride_sessions": case["stride"],
        "ratio": case["ratio"], "policy": policy,
        "selected_cohorts": len(selected), "entered_cohorts": len(entered),
        "entry_skips": len(skipped),
        "selected_cohorts_per_year": round(len(selected) / years, 3),
        "entered_cohorts_per_year": round(len(entered) / years, 3),
        "resolved": len(resolved), "unresolved": unresolved, "wins": wins, "losses": losses,
        "flat": flats, "win_rate_pct": round(100.0 * wins / len(pnl), 2) if pnl else None,
        "mean_net_pnl_usd": round(mean_pnl, 2) if mean_pnl is not None else None,
        "median_net_pnl_usd": round(statistics.median(pnl), 2) if pnl else None,
        "total_resolved_net_pnl_usd": round(sum(pnl), 2),
        "annualized_resolved_net_pnl_usd": round(sum(pnl) / years, 2),
        "worst_resolved_trade_usd": round(min(pnl), 2) if pnl else None,
        "best_resolved_trade_usd": round(max(pnl), 2) if pnl else None,
        "profit_factor": round(gross_positive / abs(gross_negative), 3) if gross_negative < 0 else ("INF" if gross_positive > 0 else None),
        "stress_resolved": len(stress),
        "stress_mean_net_pnl_usd": round(statistics.mean(stress), 2) if stress else None,
        "stress_total_net_pnl_usd": round(sum(stress), 2),
        "stress_annualized_net_pnl_usd": round(sum(stress) / years, 2),
        "stress_worst_trade_usd": round(min(stress), 2) if stress else None,
        "peak_concurrent_cohorts": peak_count,
        "peak_short_assignment_obligation_usd": peak_obligation,
    }


def add_pareto_flags(records: list[dict[str, Any]]) -> None:
    groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        groups[(row["window"], row["filter"], row["ratio"], row["policy"])].append(row)
    for group in groups.values():
        for a in group:
            a["pareto_frontier_cadence"] = True
            for b in group:
                if a is b:
                    continue
                av = (a["annualized_resolved_net_pnl_usd"], a["win_rate_pct"],
                      a["worst_resolved_trade_usd"], a["peak_short_assignment_obligation_usd"])
                bv = (b["annualized_resolved_net_pnl_usd"], b["win_rate_pct"],
                      b["worst_resolved_trade_usd"], b["peak_short_assignment_obligation_usd"])
                if any(x is None for x in av[:3]) or any(x is None for x in bv[:3]):
                    continue
                weak = (bv[0] >= av[0] and bv[1] >= av[1] and bv[2] >= av[2] and bv[3] <= av[3])
                strict = (bv[0] > av[0] or bv[1] > av[1] or bv[2] > av[2] or bv[3] < av[3])
                if weak and strict:
                    a["pareto_frontier_cadence"] = False
                    break


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"Refusing to write empty rows to {path}")
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def money(x: Any) -> str:
    return "—" if x is None else ("USD " + format(float(x), ",.2f"))


def pct(x: Any) -> str:
    return "—" if x is None else format(float(x), ".2f") + "%"


def make_report(records: list[dict[str, Any]], cases: list[dict[str, Any]],
                annual_records: list[dict[str, Any]], metadata: dict[str, Any]) -> str:
    lines = [
        "# QQQ/SPY PUT Cadence Optimization Grid V1", "",
        "- This grid explicitly allows overlapping cohorts; each policy is still measured as its own hypothetical exit path.",
        "- Cadence is a minimum stride after an eligible/selected entry signal; the relative-underperformance filter still must pass when enabled.",
        "- 6 cadence values × 2 filters × 4 fixed ratios = 48 independent replay cases; every case includes 5d, 10d, 20d and DTE<=7 exits.",
        "- Signal-date windows end 2025-07-23 so longer holds have source-history runway. Results are EOD quote-side estimates, not verified fills.",
        "", "## Cohort frequency per year", "",
        "| Window | Filter | Stride (sessions) | Selected/year | Entered/year | 1Y/3Y/5Y window entries |",
        "|---|---|---:|---:|---:|---:|",
    ]
    seen = set()
    for r in sorted(records, key=lambda x: (["1Y","3Y","5Y"].index(x["window"]), x["filter"], x["stride_sessions"] if "stride_sessions" in x else x["stride_sessions"], x["ratio"])):
        pass
    for window in ("1Y", "3Y", "5Y"):
        for filt in FILTERS:
            for stride in STRIDES:
                sample = next(r for r in records if r["window"] == window and r["filter"] == filt and r["stride_sessions"] == stride and r["policy"] == "HOLD_20_SESSIONS")
                key = (window, filt, stride)
                if key in seen:
                    continue
                seen.add(key)
                lines.append(f"| {window} | {filt} | {stride} | {sample['selected_cohorts_per_year']:.2f} | {sample['entered_cohorts_per_year']:.2f} | {sample['entered_cohorts']} |")
    lines += [
        "", "## 1Y / 3Y / 5Y comparison — 20-session exit", "",
        "| Window | Filter | Stride | Ratio | Trades/year | Resolved/opened | Win rate | Mean/trade | Total resolved | Annualized resolved | Worst trade | Peak overlap | Peak SPY assignment obligation | Stress annualized | Pareto cadence |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    focus = [r for r in records if r["policy"] == "HOLD_20_SESSIONS"]
    focus.sort(key=lambda r: (["1Y","3Y","5Y"].index(r["window"]), r["filter"], r["stride_sessions"], r["ratio"]))
    for r in focus:
        lines.append(
            f"| {r['window']} | {r['filter']} | {r['stride_sessions']} | {r['ratio']} | {r['entered_cohorts_per_year']:.2f} | "
            f"{r['resolved']}/{r['entered_cohorts']} | {pct(r['win_rate_pct'])} | {money(r['mean_net_pnl_usd'])} | "
            f"{money(r['total_resolved_net_pnl_usd'])} | {money(r['annualized_resolved_net_pnl_usd'])} | "
            f"{money(r['worst_resolved_trade_usd'])} | {r['peak_concurrent_cohorts']} | "
            f"{money(r['peak_short_assignment_obligation_usd'])} | {money(r['stress_annualized_net_pnl_usd'])} | "
            f"{'YES' if r['pareto_frontier_cadence'] else 'no'} |"
        )
    lines += [
        "", "## Exit-policy comparison — 5Y window", "",
        "| Filter | Stride | Ratio | Exit | Trades/year | Win rate | Mean/trade | Total resolved | Annualized resolved | Worst trade | Peak overlap | Peak SPY assignment obligation | Stress annualized | Pareto cadence |",
        "|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    focus5 = [r for r in records if r["window"] == "5Y"]
    focus5.sort(key=lambda r: (r["filter"], r["stride_sessions"], r["ratio"], POLICIES.index(r["policy"])))
    for r in focus5:
        lines.append(
            f"| {r['filter']} | {r['stride_sessions']} | {r['ratio']} | {POLICY_LABELS[r['policy']]} | {r['entered_cohorts_per_year']:.2f} | "
            f"{pct(r['win_rate_pct'])} | {money(r['mean_net_pnl_usd'])} | {money(r['total_resolved_net_pnl_usd'])} | "
            f"{money(r['annualized_resolved_net_pnl_usd'])} | {money(r['worst_resolved_trade_usd'])} | "
            f"{r['peak_concurrent_cohorts']} | {money(r['peak_short_assignment_obligation_usd'])} | "
            f"{money(r['stress_annualized_net_pnl_usd'])} | {'YES' if r['pareto_frontier_cadence'] else 'no'} |"
        )
    lines += [
        "", "## Calendar-year replay output", "",
        "Per-calendar-year entry counts and P&L for the 20-session exit are in `calendar_year_comparison.csv`; the file preserves years with negative results rather than averaging away regime differences.",
        "", "## Guardrails", "",
        "- The overlap estimate is calculated per exit policy, not by stacking mutually exclusive exit-policy variants against one another.",
        "- Peak SPY assignment obligation sums strike × 100 × short SPY contracts across simultaneously open cohorts. It is a gross assignment proxy, not broker margin or required cash.",
        "- Increasing cadence mechanically increases the number of positions and gross short-put obligations. Summed P&L is not a capital-normalized or compounded account return.",
        "- Slippage stress increases assumed slippage from $0.05 to $0.10 per option share per side; it is a cost sensitivity, not a new order-book fill simulation.",
        "- No fixed PASS threshold or arbitrary weighted score is used. Pareto flags compare cadence choices only within the same window, filter, fixed ratio and exit policy on net P&L, win rate, worst loss and peak assignment obligation.",
        "- Data is historical through 2025-12-12; there is no 2026 option-chain performance here. The test is in-sample, and quote-side displayed sizes do not guarantee actual multi-leg fills.",
        "", "## Reproducibility", "",
        f"- Cases loaded: {metadata['case_count']}; period rows: {len(records)}; calendar-year rows: {len(annual_records)}.",
        f"- Source window: {metadata['source_start']} to {metadata['source_end']}; final signal allowed: {metadata['last_signal_included']}.",
        f"- Ratios: {', '.join(RATIOS)}; filters: {', '.join(FILTERS)}; strides: {', '.join(str(x) for x in STRIDES)}.",
        "",
    ]
    return "\n".join(lines)


def build(root: Path, out_dir: Path) -> dict[str, Any]:
    cases: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    annual_records: list[dict[str, Any]] = []
    for filt in FILTERS:
        for stride in STRIDES:
            for ratio in RATIOS:
                case = load_case(root, filt, stride, ratio)
                cases.append(case)
                for window, start, end, years in WINDOWS:
                    for policy in POLICIES:
                        records.append(summarize_period(case, window, start, end, years, policy))
                for year in range(2018, 2026):
                    start = date(year, 1, 1)
                    end = min(date(year, 12, 31), CUTOFF)
                    if start > CUTOFF:
                        continue
                    for policy in POLICIES:
                        row = summarize_period(case, str(year), start, end,
                                               max(1, (end-start).days+1) / 365.2425, policy)
                        annual_records.append({
                            "year": year, "filter": filt, "stride_sessions": stride,
                            "ratio": ratio, "policy": policy,
                            "selected_cohorts": row["selected_cohorts"],
                            "entered_cohorts": row["entered_cohorts"],
                            "entry_skips": row["entry_skips"],
                            "resolved": row["resolved"], "unresolved": row["unresolved"],
                            "win_rate_pct": row["win_rate_pct"],
                            "mean_net_pnl_usd": row["mean_net_pnl_usd"],
                            "total_resolved_net_pnl_usd": row["total_resolved_net_pnl_usd"],
                            "annualized_resolved_net_pnl_usd": row["annualized_resolved_net_pnl_usd"],
                            "worst_resolved_trade_usd": row["worst_resolved_trade_usd"],
                            "peak_concurrent_cohorts": row["peak_concurrent_cohorts"],
                            "peak_short_assignment_obligation_usd": row["peak_short_assignment_obligation_usd"],
                        })
    add_pareto_flags(records)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_rows(out_dir / "period_comparison.csv", records)
    write_rows(out_dir / "calendar_year_comparison.csv", annual_records)
    metadata = {
        "schema": "qqq-spy-put-cadence-grid.v1",
        "case_count": len(cases),
        "period_record_count": len(records),
        "calendar_year_record_count": len(annual_records),
        "source_start": "2018-03-01",
        "source_end": "2025-12-12",
        "last_signal_included": "2025-07-23",
        "ratios": list(RATIOS),
        "filters": list(FILTERS),
        "strides": list(STRIDES),
        "policies": list(POLICIES),
        "cases": [
            {"filter": c["filter"], "stride_sessions": c["stride"], "ratio": c["ratio"],
             "summary_sha256": c["summary_sha256"], "summary_path": c["path"] + "/summary.json"}
            for c in cases
        ],
        "important_limitations": [
            "Independent cohorts overlap; no portfolio NAV, cash, margin, forced liquidation or financing constraint is modeled.",
            "Short-put assignment obligations can stack; peak obligation is an exposure proxy, not broker margin.",
            "EOD option quote-side results are not verified fills and source data ends in 2025.",
            "In-sample comparison; no automatic best strategy claim is made."
        ],
    }
    (out_dir / "comparison.json").write_text(json.dumps(
        {"metadata": metadata, "period_records": records, "calendar_year_records": annual_records},
        indent=2, allow_nan=False
    ), encoding="utf-8")
    (out_dir / "report.md").write_text(make_report(records, cases, annual_records, metadata), encoding="utf-8")
    return metadata


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-root", type=Path,
                        default=Path("research/qqq_spy_put_fixed_ratio_size_gated_v1/results"))
    parser.add_argument("--out-dir", type=Path,
                        default=Path("research/qqq_spy_put_fixed_ratio_size_gated_v1/results/cadence_grid_audit"))
    args = parser.parse_args()
    metadata = build(args.results_root, args.out_dir)
    print(json.dumps({"status": "COMPLETED", **{k: metadata[k] for k in (
        "case_count", "period_record_count", "calendar_year_record_count", "last_signal_included"
    )}, "out_dir": str(args.out_dir)}, indent=2))


if __name__ == "__main__":
    main()
