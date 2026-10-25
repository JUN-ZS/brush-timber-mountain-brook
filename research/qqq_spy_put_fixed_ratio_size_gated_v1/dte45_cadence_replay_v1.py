#!/usr/bin/env python3
"""Source-pinned overlapping-cadence replay for DTE45 QQQ/SPY PUT 1:6.

The cadence and phase are fixed before looking at results. This wrapper runs one
exit policy in isolation, preserving exact contract identity and quote-side
costing in the shared replay engine. It is not an account margin simulation.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import qqq_spy_put_premium_matched_phase_v1 as engine


RULES = {
    "20": {"policy": "HOLD_20_SESSIONS", "hold_sessions": 20},
    "20_or_dte_le_7": {
        "policy": "HOLD_20_OR_DTE_LE_7",
        "hold_sessions": 20,
        "expiry_guard_dte": 7,
    },
}
ALLOWED_PHASES = {
    5: {0, 1, 2, 3, 4},
    7: {0, 1, 3, 4, 6},
    10: {0, 2, 4, 6, 8},
    15: {0, 3, 6, 9, 12},
    20: {0, 4, 8, 12, 16},
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exit-rule", choices=tuple(RULES), required=True)
    wrapper, engine_argv = parser.parse_known_args()

    if "--allow-overlapping-cohorts" not in engine_argv:
        parser.error("this cadence study explicitly requires --allow-overlapping-cohorts")

    engine.POLICIES = (dict(RULES[wrapper.exit_rule]),)
    sys.argv = [sys.argv[0], *engine_argv]
    args = engine.parse_args()

    if args.entry_filter != "none":
        parser.error("cadence study is locked to entry-filter=none")
    if args.sizing_mode != "fixed_ratio" or args.fixed_long_qty != 1 or args.fixed_short_qty != 6:
        parser.error("cadence study is locked to QQQ LONG PUT 1 : SPY SHORT PUT 6")
    if (args.dte_min, args.dte_max, args.dte_target) != (30, 60, 45):
        parser.error("cadence study is locked to DTE 30–60, target 45")
    if abs(args.target_delta - 0.25) > 1e-12:
        parser.error("cadence study is locked to abs Delta target 0.25 on both legs")
    if not args.allow_overlapping_cohorts:
        parser.error("overlapping cohorts are required for this cadence study")
    if args.cohort_stride_sessions not in ALLOWED_PHASES:
        parser.error(f"unsupported cadence stride: {args.cohort_stride_sessions}")
    if args.initial_phase_sessions not in ALLOWED_PHASES[args.cohort_stride_sessions]:
        parser.error("phase is not in the predeclared phase set for this stride")

    report = engine.run_replay(args)
    out = Path(args.out)
    key = RULES[wrapper.exit_rule]["policy"]
    stats = report["policies"][key]
    years = (date.fromisoformat(args.end) - date.fromisoformat(args.start)).days / 365.25
    total = stats.get("total_net_pnl_usd")
    annual = total / years if total is not None and years > 0 else None

    lines = [
        f"# DTE45 overlapping cadence replay — stride {args.cohort_stride_sessions}, phase {args.initial_phase_sessions}",
        "",
        f"- Window: {args.start} to {args.end} ({years:.3f} calendar years).",
        f"- Fixed cadence: one entry opportunity every {args.cohort_stride_sessions} common sessions, phase {args.initial_phase_sessions}.",
        "- Overlapping cohorts: enabled; the historical engine does not impose an account-level maximum-active-position or buying-power limit.",
        "- Legs: QQQ LONG PUT 1 : SPY SHORT PUT 6; same expiry required; each leg selected nearest abs Delta 0.25.",
        "- Expiry selection: DTE 30–60, target 45; no market entry filter.",
        f"- Exit policy: {key}.",
        f"- Costs: USD {args.slippage_per_share:.2f}/option-share/side slippage + USD {args.commission_per_contract_per_side:.2f}/contract/side commission.",
        "",
        "## Historical quote-side results",
        "",
        "| Metric | Result |",
        "|---|---:|",
        f"| Entered cohorts | {report['cohort']['entered_cohorts']:,} |",
        f"| Resolved episodes | {stats['resolved']:,} |",
        f"| Unresolved episodes | {stats['unresolved']:,} |",
        f"| Win rate (resolved only) | {stats['win_rate_pct']:.2f}% |" if stats.get("win_rate_pct") is not None else "| Win rate (resolved only) | unavailable |",
        f"| Mean net P&L per resolved trade | USD {stats['expectancy_net_usd']:,.2f} |" if stats.get("expectancy_net_usd") is not None else "| Mean net P&L per resolved trade | unavailable |",
        f"| Median net P&L per resolved trade | USD {stats['median_net_usd']:,.2f} |" if stats.get("median_net_usd") is not None else "| Median net P&L per resolved trade | unavailable |",
        f"| Cumulative net P&L of resolved trades | USD {total:,.2f} |" if total is not None else "| Cumulative net P&L of resolved trades | unavailable |",
        f"| Annual average of resolved-trade P&L sum | USD {annual:,.2f}/year |" if annual is not None else "| Annual average of resolved-trade P&L sum | unavailable |",
        f"| Worst resolved trade | USD {stats['worst_net_usd']:,.2f} |" if stats.get("worst_net_usd") is not None else "| Worst resolved trade | unavailable |",
        f"| Profit factor | {stats['profit_factor']} |",
        f"| Mean SPY short-put assignment obligation per cohort | USD {report['ratio']['mean_spy_put_assignment_obligation_usd']:,.2f} |",
        "",
        "## Interpretation limits",
        "",
        "This is an additive sum of resolved trade P&L divided by calendar years, not account profit, CAGR, or a $100,000 NAV feasibility result. Unresolved trades are excluded from the reported P&L and separately counted.",
        "",
        "The run does not simulate account cash, margin, broker buying power, assignment funding, forced liquidation, financing, taxes, dividends, or compounding. Concurrent gross SPY assignment obligations can exceed NAV substantially; they are not the same as broker margin.",
        "",
        "Far-OTM TAIL is excluded. Historical EOD displayed-side quotes are not verified fills, and displayed-size gates do not guarantee multi-leg execution. Results must be compared across the predeclared phase matrix, not selected by the best phase.",
        "",
    ]
    out.mkdir(parents=True, exist_ok=True)
    (out / "CADENCE_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(
        f"stride={args.cohort_stride_sessions} phase={args.initial_phase_sessions} "
        f"exit={key} opened={report['cohort']['entered_cohorts']} "
        f"resolved={stats['resolved']} unresolved={stats['unresolved']} "
        f"total_net={total} annual_avg={annual} worst={stats['worst_net_usd']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
