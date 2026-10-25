#!/usr/bin/env python3
"""Isolated single-position DTE45 QQQ LONG PUT 1 : SPY SHORT PUT 6 historical replay.

Each exit policy runs in its own process so the entry gate represents one open
strategy position, not the union of concurrent policies. This is a historical
quote-side replay, not a broker-margin or portfolio-account simulator.
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
    "5": {"policy": "HOLD_5_SESSIONS", "hold_sessions": 5},
    "10": {"policy": "HOLD_10_SESSIONS", "hold_sessions": 10},
    "20": {"policy": "HOLD_20_SESSIONS", "hold_sessions": 20},
    "20_or_dte_le_7": {
        "policy": "HOLD_20_OR_DTE_LE_7",
        "hold_sessions": 20,
        "expiry_guard_dte": 7,
    },
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exit-rule", choices=tuple(RULES), required=True)
    wrapper, engine_argv = parser.parse_known_args()

    if "--allow-overlapping-cohorts" in engine_argv:
        parser.error("single-position replay forbids --allow-overlapping-cohorts")

    rule = RULES[wrapper.exit_rule]
    # Simulate only this exit policy. Otherwise multiple policies share the
    # engine's active list and would hold the entry gate closed for the longest.
    engine.POLICIES = (dict(rule),)
    sys.argv = [sys.argv[0], *engine_argv]
    args = engine.parse_args()

    if args.entry_filter != "none":
        parser.error("this unfiltered cadence comparison requires --entry-filter none")
    if args.sizing_mode != "fixed_ratio" or args.fixed_long_qty != 1 or args.fixed_short_qty != 6:
        parser.error("this study is locked to QQQ LONG PUT 1 : SPY SHORT PUT 6")
    if args.allow_overlapping_cohorts:
        parser.error("single-position replay forbids overlapping cohorts")
    if (args.dte_min, args.dte_max, args.dte_target) != (30, 60, 45):
        parser.error("this study is locked to DTE 30–60, target 45")

    report = engine.run_replay(args)
    out = Path(args.out)
    key = rule["policy"]
    stats = report["policies"][key]
    years = (date.fromisoformat(args.end) - date.fromisoformat(args.start)).days / 365.25
    total = stats.get("total_net_pnl_usd")
    annual = total / years if total is not None and years > 0 else None
    initial_nav = 100_000.0

    exit_text = {
        "5": "Exit after 5 trading sessions",
        "10": "Exit after 10 trading sessions",
        "20": "Exit after 20 trading sessions; if executable quotes are absent, exit is deferred and unresolved items are retained",
        "20_or_dte_le_7": "Exit after 20 trading sessions OR when DTE reaches 7 or less, whichever comes first; if quotes are absent, exit is deferred and unresolved items are retained",
    }[wrapper.exit_rule]

    lines = [
        f"# DTE45 single-position replay — {wrapper.exit_rule}",
        "",
        f"- Period requested: {args.start} to {args.end} ({years:.3f} calendar years).",
        "- Entries: check every common underlying session; no market signal filter; a new cohort is blocked while the previous cohort is active.",
        "- Legs: QQQ LONG PUT 1 : SPY SHORT PUT 6; same expiry required.",
        "- Selection: expiry DTE 30–60, target 45; both puts selected nearest absolute Delta 0.25 among eligible contracts.",
        f"- Exit rule: {exit_text}.",
        f"- Costs: slippage USD {args.slippage_per_share:.2f} per option-share per side; commission USD {args.commission_per_contract_per_side:.2f} per contract per side.",
        "",
        "## Historical quote-side results",
        "",
        "| Metric | Result |",
        "|---|---:|",
        f"| Eligible daily opportunities | {report['fixed_entry_schedule']['scheduled_opportunities']:,} |",
        f"| Entered cohorts | {report['cohort']['entered_cohorts']:,} |",
        f"| Resolved episodes | {stats['resolved']:,} |",
        f"| Unresolved episodes | {stats['unresolved']:,} |",
        f"| Win rate (resolved only) | {stats['win_rate_pct']:.2f}% |" if stats.get("win_rate_pct") is not None else "| Win rate (resolved only) | unavailable |",
        f"| Mean net P&L per resolved trade | USD {stats['expectancy_net_usd']:,.2f} |" if stats.get("expectancy_net_usd") is not None else "| Mean net P&L per resolved trade | unavailable |",
        f"| Median net P&L per resolved trade | USD {stats['median_net_usd']:,.2f} |" if stats.get("median_net_usd") is not None else "| Median net P&L per resolved trade | unavailable |",
        f"| Cumulative net P&L across resolved trades | USD {total:,.2f} |" if total is not None else "| Cumulative net P&L across resolved trades | unavailable |",
        f"| Annual average of resolved trade P&L sum | USD {annual:,.2f}/year |" if annual is not None else "| Annual average of resolved trade P&L sum | unavailable |",
        f"| Worst resolved trade | USD {stats['worst_net_usd']:,.2f} ({stats['worst_net_usd']/initial_nav*100:.2f}% of USD 100k reference NAV) |" if stats.get("worst_net_usd") is not None else "| Worst resolved trade | unavailable |",
        f"| Profit factor | {stats['profit_factor']} |",
        f"| Average SPY short-put assignment obligation per cohort | USD {report['ratio']['mean_spy_put_assignment_obligation_usd']:,.2f} |",
        "",
        "## Limits and interpretation",
        "",
        "This is a sequential, one-open-cohort replay of the QQQ/SPY option legs. It deliberately does not import P&L from the overlapping cadence grid.",
        "",
        "USD 100,000 is only a reference NAV for displaying the worst resolved trade as a percentage; this run does not constrain buying power, margin, assignment funding, forced liquidation, financing, tax, or compounding. The annual average above is an additive resolved-trade P&L sum divided by calendar years, not account annual profit or CAGR.",
        "",
        "**Far-OTM TAIL insurance is not priced in these baseline runs.** No tail contract quantity, DTE/Delta rule, or roll policy is assumed. The results must not be read as net of TAIL premiums.",
        "",
        "Historical EOD displayed bid/ask quotes are conservative quote-side estimates, not verified fills. If the exact selected contract cannot be closed with eligible displayed size, the engine defers the close and records unresolved cases rather than inventing a fill. Source integrity is recorded in source_manifest.json.",
        "",
    ]
    (out / "SINGLE_POSITION_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(
        f"exit_rule={wrapper.exit_rule} entered={report['cohort']['entered_cohorts']} "
        f"resolved={stats['resolved']} unresolved={stats['unresolved']} "
        f"total_net_pnl={total} annual_average={annual} "
        f"worst={stats['worst_net_usd']} win_rate={stats['win_rate_pct']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
