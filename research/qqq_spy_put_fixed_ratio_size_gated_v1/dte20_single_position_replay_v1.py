#!/usr/bin/env python3
"""Isolated single-position DTE20 replay for 5- or 10-session exits.

This runner reuses the audited historical QQQ/SPY option replay engine, but runs
one exit policy per process. That separation is necessary: running several exit
policies together would keep the shared entry gate blocked until the longest
policy exits and would not model independent single-position strategies.
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hold-sessions", type=int, choices=(5, 10), required=True)
    wrapper, engine_argv = parser.parse_known_args()

    if "--allow-overlapping-cohorts" in engine_argv:
        parser.error("single-position replay forbids --allow-overlapping-cohorts")

    # Run just one policy at a time so the entry gate truly means one open
    # strategy position, rather than the union of concurrently simulated exits.
    engine.POLICIES = ({
        "policy": f"HOLD_{wrapper.hold_sessions}_SESSIONS",
        "hold_sessions": wrapper.hold_sessions,
    },)
    sys.argv = [sys.argv[0], *engine_argv]
    args = engine.parse_args()

    if args.entry_filter != "none":
        parser.error("this comparison is intentionally unfiltered (entry-filter=none)")
    if args.sizing_mode != "fixed_ratio" or args.fixed_long_qty != 1 or args.fixed_short_qty != 6:
        parser.error("this run is locked to fixed QQQ LONG PUT 1 : SPY SHORT PUT 6")
    if args.allow_overlapping_cohorts:
        parser.error("single-position replay forbids overlapping cohorts")
    if args.dte_target != 20:
        parser.error("this study is locked to target DTE 20")

    report = engine.run_replay(args)
    out = Path(args.out)
    stats = report["policies"][f"HOLD_{wrapper.hold_sessions}_SESSIONS"]
    years = (date.fromisoformat(args.end) - date.fromisoformat(args.start)).days / 365.25
    total = stats.get("total_net_pnl_usd")
    annual = total / years if total is not None and years > 0 else None
    initial_nav = 100_000.0
    qqq_delta_band = report["selection"].get("qqq_delta_band")
    text = [
        f"# DTE20 single-position replay — exit after {wrapper.hold_sessions} sessions",
        "",
        f"- Period requested: {args.start} to {args.end} ({years:.3f} calendar years).",
        "- Entry schedule: every common-session opportunity; no entry filter; new entry blocked while this policy's position remains open.",
        f"- Option legs: QQQ LONG PUT 1 : SPY SHORT PUT 6; shared expiry; selected expiry DTE {args.dte_min}–{args.dte_max}, target {args.dte_target}.",
        f"- QQQ selection: absolute Delta target {args.qqq_target_abs_delta} ± {args.qqq_delta_tolerance}; within-band QQQ ask matched nearest to 6 × selected SPY put bid.",
        f"- Exit rule: signal exit at holding age {wrapper.hold_sessions} trading sessions, then close only when exact selected contracts have executable displayed-side quotes; missing exits are reported unresolved.",
        f"- Costs: slippage USD {args.slippage_per_share:.2f} per option-share per side; commission USD {args.commission_per_contract_per_side:.2f} per contract per side.",
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
        f"| Cumulative net P&L across resolved trades | USD {total:,.2f} |" if total is not None else "| Cumulative net P&L across resolved trades | unavailable |",
        f"| Annual average of resolved trade P&L sum | USD {annual:,.2f}/year |" if annual is not None else "| Annual average of resolved trade P&L sum | unavailable |",
        f"| Worst resolved trade | USD {stats['worst_net_usd']:,.2f} ({stats['worst_net_usd']/initial_nav*100:.2f}% of USD 100k reference NAV) |" if stats.get("worst_net_usd") is not None else "| Worst resolved trade | unavailable |",
        f"| Profit factor | {stats['profit_factor']} |",
        "",
        "## Interpretation and exclusions",
        "",
        "This is a sequential single-position replay of the QQQ/SPY option legs, not a portfolio-account simulation. The USD 100,000 NAV is a reference denominator only; the engine does not impose buying-power, margin, assignment-funding, forced-liquidation, financing, tax, or compounding constraints, so the annual average above is not CAGR or a verified account return.",
        "",
        "**Far-OTM TAIL insurance is not priced in this base run.** No tail option quantity, expiry/Delta rule, or roll/hold policy is encoded in this isolated timing comparison. Do not read these figures as the net result after paying for tail insurance.",
        "",
        "Historical EOD displayed bid/ask quotes are conservative quote-side marks, not verified fills. The exact contract IDs, quote-size gate, unresolved trades, entry skips, and source-integrity manifest are retained in the sibling CSV/JSON outputs.",
        "",
        "## DTE20 configuration",
        "",
        f"- Requested DTE window: {args.dte_min}–{args.dte_max}, target {args.dte_target}; one common expiry required.",
        f"- Overlapping cohorts enabled: {report['selection']['allow_overlapping_cohorts']}.",
        f"- QQQ Delta band: {qqq_delta_band}.",
    ]
    (out / "SINGLE_POSITION_REPORT.md").write_text("\n".join(text) + "\n", encoding="utf-8")
    print(f"Single-position DTE20 hold-{wrapper.hold_sessions} report: {out / 'SINGLE_POSITION_REPORT.md'}")
    print(f"Entered={report['cohort']['entered_cohorts']} resolved={stats['resolved']} "
          f"unresolved={stats['unresolved']} total_net_pnl={total} annual_avg={annual}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
