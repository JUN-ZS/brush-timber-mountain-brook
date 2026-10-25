#!/usr/bin/env python3
"""Aggregate predeclared DTE45 cadence/phase replay outputs without pooling phases."""
from __future__ import annotations

import csv
import json
import statistics
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

START = date(2018, 3, 1)
END = date(2025, 12, 15)
YEARS = (END - START).days / 365.25
ROOT = Path("research/qqq_spy_put_fixed_ratio_size_gated_v1/results/dte45_cadence_grid_v1")
CONFIGS = {
    5: [0, 1, 2, 3, 4],
    7: [0, 1, 3, 4, 6],
    10: [0, 2, 4, 6, 8],
    15: [0, 3, 6, 9, 12],
    20: [0, 4, 8, 12, 16],
}
POLICY = "HOLD_20_OR_DTE_LE_7"


def concurrency_from_csv(path: Path) -> tuple[int, float]:
    """Conservative inclusive daily interval count; obligation is not broker margin."""
    events: dict[date, list[float]] = defaultdict(lambda: [0.0, 0.0])
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            entry_s = row.get("entry_date") or ""
            if not entry_s:
                continue
            entry = date.fromisoformat(entry_s[:10])
            exit_s = row.get("exit_date") or ""
            status = (row.get("status") or "").upper()
            last_s = row.get("last_observed_date") or ""
            if status == "RESOLVED" and exit_s:
                end = date.fromisoformat(exit_s[:10])
            elif last_s:
                end = date.fromisoformat(last_s[:10])
            else:
                end = END
            if end < entry:
                end = entry
            obligation = float(row.get("spy_put_strike_assignment_obligation_usd") or 0)
            events[entry][0] += 1
            events[entry][1] += obligation
            after_end = end + timedelta(days=1)
            events[after_end][0] -= 1
            events[after_end][1] -= obligation

    active_n = 0.0
    active_obligation = 0.0
    peak_n = 0
    peak_obligation = 0.0
    for day in sorted(events):
        active_n += events[day][0]
        active_obligation += events[day][1]
        peak_n = max(peak_n, round(active_n))
        peak_obligation = max(peak_obligation, active_obligation)
    return peak_n, round(peak_obligation, 2)


def main() -> int:
    rows: list[dict] = []
    for stride, phases in CONFIGS.items():
        for phase in phases:
            out = ROOT / f"stride_{stride}" / f"phase_{phase}"
            summary_path = out / "summary.json"
            trades_path = out / "trade_episodes.csv"
            report_path = out / "CADENCE_REPORT.md"
            for required in (summary_path, trades_path, report_path):
                if not required.is_file() or required.stat().st_size == 0:
                    raise SystemExit(f"missing/empty output: {required}")
            data = json.loads(summary_path.read_text(encoding="utf-8"))
            if not str(data.get("status", "")).startswith("COMPLETED"):
                raise SystemExit(f"run not complete: stride={stride} phase={phase}: {data.get('status')}")
            selection = data["selection"]
            if (
                selection["dte_target"] != 45
                or selection["dte_min"] != 30
                or selection["dte_max"] != 60
                or selection["allow_overlapping_cohorts"] is not True
                or selection["cohort_stride_sessions"] != stride
                or selection["initial_phase_sessions"] != phase
            ):
                raise SystemExit(f"configuration mismatch: stride={stride} phase={phase}")
            if data["ratio"]["fixed_long_qqq_contracts"] != 1 or data["ratio"]["fixed_short_spy_contracts"] != 6:
                raise SystemExit(f"ratio mismatch: stride={stride} phase={phase}")
            policy = data["policies"][POLICY]
            annual = policy["total_net_pnl_usd"] / YEARS if policy["total_net_pnl_usd"] is not None else None
            peak_n, peak_obligation = concurrency_from_csv(trades_path)
            rows.append({
                "stride_sessions": stride,
                "phase_sessions": phase,
                "entries": data["cohort"]["entered_cohorts"],
                "resolved": policy["resolved"],
                "unresolved": policy["unresolved"],
                "win_rate_resolved_pct": policy["win_rate_pct"],
                "mean_net_pnl_per_resolved_usd": policy["expectancy_net_usd"],
                "median_net_pnl_per_resolved_usd": policy["median_net_usd"],
                "total_resolved_net_pnl_usd": policy["total_net_pnl_usd"],
                "annual_avg_resolved_trade_pnl_usd": round(annual, 2) if annual is not None else "",
                "worst_resolved_trade_usd": policy["worst_net_usd"],
                "profit_factor": policy["profit_factor"],
                "peak_concurrent_cohorts_est": peak_n,
                "peak_gross_spy_assignment_obligation_usd_est": peak_obligation,
                "mean_spy_assignment_obligation_per_cohort_usd": data["ratio"]["mean_spy_put_assignment_obligation_usd"],
                "unresolved_fraction_of_entries_pct": round(100 * policy["unresolved"] / max(data["cohort"]["entered_cohorts"], 1), 2),
                "run_status": data["status"],
            })

    matrix = ROOT / "cadence_phase_matrix.csv"
    with matrix.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    grouped: dict[int, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[int(row["stride_sessions"])].append(row)
    report_lines = [
        "# DTE45 cadence grid — overlapping 1:6 replay",
        "",
        f"- Frozen window: {START.isoformat()} to {END.isoformat()} ({YEARS:.3f} calendar years).",
        "- Fixed legs: QQQ LONG PUT 1 : SPY SHORT PUT 6; DTE 30–60, target 45; both legs abs Delta target 0.25; no entry filter.",
        "- Exit: hold up to 20 sessions, or exit when remaining DTE <= 7, whichever comes first.",
        "- Costs: USD 0.05 per option-share per side + USD 0.65 per contract per side.",
        "- Cadence grid: every 5, 7, 10, 15 or 20 common sessions; five predeclared phase starts per stride. The stride-5 set covers every phase; longer strides use five spread phases, not exhaustive phase enumeration.",
        "- Phase accounts are separate schedules. They are summarized by median and range; their P&L is not pooled as if independent.",
        "",
        "## Annual additive trade-P&L by cadence",
        "",
        "| Entry stride | Phase runs | Median annual resolved-trade P&L | Min–max annual P&L | Phases >= $12k/year | Median entries | Median unresolved | Median peak concurrent cohorts | Median peak gross SPY assignment obligation |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for stride in sorted(grouped):
        group = grouped[stride]
        annuals = [float(r["annual_avg_resolved_trade_pnl_usd"]) for r in group]
        phase_hit = sum(v >= 12000 for v in annuals)
        entry_med = statistics.median(int(r["entries"]) for r in group)
        unresolved_med = statistics.median(int(r["unresolved"]) for r in group)
        peak_n_med = statistics.median(int(r["peak_concurrent_cohorts_est"]) for r in group)
        peak_ob_med = statistics.median(float(r["peak_gross_spy_assignment_obligation_usd_est"]) for r in group)
        report_lines.append(
            f"| {stride} sessions | {len(group)} | ${statistics.median(annuals):,.0f} | "
            f"${min(annuals):,.0f} to ${max(annuals):,.0f} | {phase_hit}/{len(group)} | "
            f"{entry_med:,.0f} | {unresolved_med:,.0f} | {peak_n_med:,.0f} | ${peak_ob_med:,.0f} |"
        )
    report_lines += [
        "",
        "## All phase results",
        "",
        "| Stride | Phase | Entries | Resolved | Unresolved | Win rate | Mean P&L/trade | Total resolved P&L | Annual average | Worst trade | Profit factor | Peak concurrent | Peak gross SPY assignment obligation |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in sorted(rows, key=lambda x: (x["stride_sessions"], x["phase_sessions"])):
        report_lines.append(
            f"| {r['stride_sessions']} | {r['phase_sessions']} | {r['entries']} | {r['resolved']} | {r['unresolved']} | "
            f"{float(r['win_rate_resolved_pct']):.2f}% | ${float(r['mean_net_pnl_per_resolved_usd']):,.2f} | "
            f"${float(r['total_resolved_net_pnl_usd']):,.2f} | ${float(r['annual_avg_resolved_trade_pnl_usd']):,.2f} | "
            f"${float(r['worst_resolved_trade_usd']):,.2f} | {float(r['profit_factor']):.3f} | "
            f"{r['peak_concurrent_cohorts_est']} | ${float(r['peak_gross_spy_assignment_obligation_usd_est']):,.0f} |"
        )
    report_lines += [
        "",
        "## Interpretation limits",
        "",
        "The $12,000/year marker refers only to the additive sum of resolved episode P&L divided by calendar years. It is not account annual profit, CAGR, or a guarantee that a $100,000 NAV can support the strategy. Unresolved trade P&L is excluded from the sum and reported separately.",
        "",
        "Overlapping gross assignment obligations must not be read as broker margin, but they expose why cadence alone does not prove account feasibility. The replay has no integrated cash, margin, assignment funding, forced-liquidation, financing, tax, or compounding engine. Far-OTM TAIL premiums are excluded. EOD quote-side prices are not verified executions.",
        "",
        "Select a cadence only if its phase median and range are both acceptable; do not pick the single best phase. The five phases for strides above 5 are a robustness sample, not a full enumeration of all possible anchors.",
        "",
        f"Outputs: {matrix.name} and per-run stride/phase summary.json, trade_episodes.csv, and CADENCE_REPORT.md files.",
        "",
    ]
    report = ROOT / "DTE45_CADENCE_GRID_REPORT.md"
    report.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"wrote {report} and {matrix}; runs={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
