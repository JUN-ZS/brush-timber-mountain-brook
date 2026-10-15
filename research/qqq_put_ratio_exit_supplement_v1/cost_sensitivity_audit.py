#!/usr/bin/env python3
"""Audit cross-cost policy results and friction BAR sample sufficiency.

This script does not optimize a strategy. It pairs zero/base/adverse-cost results
for identical cohort, ratio, NAV, risk budget, and exit-policy definitions. It
also checks whether each friction BAR has enough qualifying episodes/marks to
be informative. All outputs remain research-only diagnostics.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

COST_CASES = ("ZERO_FRICTION_BOUND", "BASE_005_065", "ADVERSE_010_065")
POLICY_KEYS = ("direction", "ratio_n", "nav_usd", "tail_risk_budget_pct", "policy")
FRICTION_KEYS = ("direction", "ratio_n", "nav_usd", "tail_risk_budget_pct", "state", "target_pct_nav")
SHOW_POLICIES = {
    "DTE7_CLOSE_SHORT_RISK",
    "TP_1.0PCT_FULL_CLOSE",
    "FAST3_1.0PCT_FULL_CLOSE",
    "FAST5_1.0PCT_FULL_CLOSE",
    "DAY20_NONPOS_FULL_CLOSE",
    "SL_1.0PCT_FULL_CLOSE",
}


def number(value: Any) -> float | None:
    try:
        out = float(value)
        return out if math.isfinite(out) else None
    except (TypeError, ValueError):
        return None


def integer(value: Any) -> int | None:
    v = number(value)
    return int(v) if v is not None else None


def read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def key_of(row: dict[str, Any], keys: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(str(row.get(k, "")) for k in keys)


def triplet(values: dict[str, dict[str, Any]], field: str) -> dict[str, Any]:
    return {cost: number((values.get(cost) or {}).get(field)) for cost in COST_CASES}


def compare_policy_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    grouped: dict[tuple[str, ...], dict[str, dict[str, Any]]] = defaultdict(dict)
    duplicate_cost_rows = 0
    for row in rows:
        key = key_of(row, POLICY_KEYS)
        cost = str(row.get("cost_case", ""))
        if cost not in COST_CASES:
            continue
        if cost in grouped[key]:
            duplicate_cost_rows += 1
        grouped[key][cost] = row

    out = []
    complete = 0
    missing = 0
    for key, values in sorted(grouped.items()):
        if set(values) == set(COST_CASES):
            complete += 1
        else:
            missing += 1
        exemplar = next(iter(values.values()))
        pnl = triplet(values, "net_pnl_sum_usd")
        exp = triplet(values, "expectancy_usd_per_unit")
        pf = triplet(values, "profit_factor")
        worst = triplet(values, "worst_trade_usd")
        win = triplet(values, "win_rate_pct")
        unit_count = integer(exemplar.get("ratio_units"))
        state = str(exemplar.get("sizing_status", ""))
        sample_n = integer(exemplar.get("depth_qualified_episodes")) or 0
        mark_coverage = number(exemplar.get("mark_coverage_pct"))
        median_delay = number(exemplar.get("median_trigger_to_action_delay_sessions"))
        deferred = integer(exemplar.get("deferred_action_sessions"))
        nav = number(exemplar.get("nav_usd"))
        budget_pct = number(exemplar.get("tail_risk_budget_pct"))
        target = nav * budget_pct if nav is not None and budget_pct is not None else None
        if unit_count == 0 or state == "BLOCKED_ZERO_WHOLE_UNITS":
            sample_status = "BLOCKED_ZERO_WHOLE_UNITS"
        elif sample_n < 30:
            sample_status = "PENDING_SMALL_EPISODE_SAMPLE"
        elif mark_coverage is not None and mark_coverage < 95:
            sample_status = "PENDING_MARK_COVERAGE_LT95PCT"
        else:
            sample_status = "DIAGNOSTIC_SAMPLE_ONLY_NOT_FILL_VALIDATION"
        out.append({
            "direction": exemplar.get("direction"),
            "ratio_n": integer(exemplar.get("ratio_n")),
            "n_long": integer(exemplar.get("n_long")),
            "n_short": integer(exemplar.get("n_short")),
            "nav_usd": nav,
            "tail_risk_budget_pct": budget_pct,
            "policy": exemplar.get("policy"),
            "ratio_units": unit_count,
            "sizing_status": state,
            "sample_status": sample_status,
            "cohort_episodes": integer(exemplar.get("cohort_episodes")),
            "depth_qualified_episodes": sample_n,
            "depth_skipped": integer(exemplar.get("depth_skipped")),
            "target_usd_for_budget_pct": target,
            **{f"net_pnl_{k.lower()}_usd": v for k, v in pnl.items()},
            "net_pnl_zero_minus_base_usd": round(pnl["ZERO_FRICTION_BOUND"] - pnl["BASE_005_065"], 2) if pnl["ZERO_FRICTION_BOUND"] is not None and pnl["BASE_005_065"] is not None else None,
            "net_pnl_adverse_minus_base_usd": round(pnl["ADVERSE_010_065"] - pnl["BASE_005_065"], 2) if pnl["ADVERSE_010_065"] is not None and pnl["BASE_005_065"] is not None else None,
            **{f"expectancy_{k.lower()}_usd": v for k, v in exp.items()},
            **{f"profit_factor_{k.lower()}": v for k, v in pf.items()},
            **{f"worst_trade_{k.lower()}_usd": v for k, v in worst.items()},
            **{f"win_rate_{k.lower()}_pct": v for k, v in win.items()},
            **{f"resolved_{k.lower()}": integer((values.get(k) or {}).get("resolved")) for k in COST_CASES},
            "mark_coverage_pct_base": mark_coverage,
            "median_trigger_to_action_delay_sessions_base": median_delay,
            "deferred_action_sessions_base": deferred,
            "all_three_cost_cases_present": set(values) == set(COST_CASES),
        })
    meta = {
        "input_rows": len(rows),
        "unique_policy_comparisons": len(grouped),
        "complete_zero_base_adverse_triplets": complete,
        "incomplete_triplets": missing,
        "duplicate_cost_case_rows": duplicate_cost_rows,
        "expected_cost_cases": list(COST_CASES),
    }
    return out, meta


def compare_friction_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    grouped: dict[tuple[str, ...], dict[str, dict[str, Any]]] = defaultdict(dict)
    duplicate_cost_rows = 0
    for row in rows:
        key = key_of(row, FRICTION_KEYS)
        cost = str(row.get("cost_case", ""))
        if cost not in COST_CASES:
            continue
        if cost in grouped[key]:
            duplicate_cost_rows += 1
        grouped[key][cost] = row

    out = []
    complete = 0
    incomplete = 0
    blocked = 0
    small_sample = 0
    for key, values in sorted(grouped.items()):
        if set(values) == set(COST_CASES):
            complete += 1
        else:
            incomplete += 1
        ex = next(iter(values.values()))
        episodes = {k: integer((values.get(k) or {}).get("episode_count")) for k in COST_CASES}
        marks = {k: integer((values.get(k) or {}).get("mark_observations")) for k in COST_CASES}
        p50 = {k: number((values.get(k) or {}).get("friction_bar_p50_episode_median_usd")) for k in COST_CASES}
        p95 = {k: number((values.get(k) or {}).get("friction_bar_p95_episode_median_usd")) for k in COST_CASES}
        nav = number(ex.get("nav_usd"))
        n = integer(ex.get("ratio_n"))
        units = integer(ex.get("ratio_units"))
        state = str(ex.get("state", ""))
        status = str(ex.get("sizing_status", ""))
        depth_vals = [number((values.get(k) or {}).get("exit_depth_qualified_pct")) for k in COST_CASES]
        worst_depth = min((v for v in depth_vals if v is not None), default=None)
        if units == 0 or status == "BLOCKED_ZERO_WHOLE_UNITS":
            sample_gate = "BLOCKED_ZERO_WHOLE_UNITS"
            blocked += 1
        elif state == "OVERALL":
            if min((v or 0) for v in episodes.values()) >= 30 and min((v or 0) for v in marks.values()) >= 500:
                sample_gate = "BAR_SAMPLE_OK_DIAGNOSTIC_ONLY"
            else:
                sample_gate = "PENDING_INSUFFICIENT_OVERALL_SAMPLES"
                small_sample += 1
        else:
            if min((v or 0) for v in episodes.values()) >= 20 and min((v or 0) for v in marks.values()) >= 100:
                sample_gate = "BAR_REGIME_SAMPLE_OK_DIAGNOSTIC_ONLY"
            else:
                sample_gate = "PENDING_SMALL_REGIME_SAMPLE"
                small_sample += 1
        out.append({
            "direction": ex.get("direction"),
            "ratio_n": n,
            "nav_usd": nav,
            "tail_risk_budget_pct": number(ex.get("tail_risk_budget_pct")),
            "target_pct_nav": number(ex.get("target_pct_nav")),
            "state": state,
            "ratio_units": units,
            "sizing_status": status,
            "bar_sample_status": sample_gate,
            "episodes_zero": episodes["ZERO_FRICTION_BOUND"],
            "episodes_base": episodes["BASE_005_065"],
            "episodes_adverse": episodes["ADVERSE_010_065"],
            "marks_zero": marks["ZERO_FRICTION_BOUND"],
            "marks_base": marks["BASE_005_065"],
            "marks_adverse": marks["ADVERSE_010_065"],
            "friction_p50_zero_usd": p50["ZERO_FRICTION_BOUND"],
            "friction_p50_base_usd": p50["BASE_005_065"],
            "friction_p50_adverse_usd": p50["ADVERSE_010_065"],
            "friction_p95_zero_usd": p95["ZERO_FRICTION_BOUND"],
            "friction_p95_base_usd": p95["BASE_005_065"],
            "friction_p95_adverse_usd": p95["ADVERSE_010_065"],
            "friction_p95_adverse_minus_base_usd": round(p95["ADVERSE_010_065"] - p95["BASE_005_065"], 2) if p95["ADVERSE_010_065"] is not None and p95["BASE_005_065"] is not None else None,
            "friction_p95_base_pct_nav": number((values.get("BASE_005_065") or {}).get("friction_p95_pct_of_nav")),
            "net_target_usd": number(ex.get("net_profit_target_usd")),
            "target_to_friction_p95_zero": number((values.get("ZERO_FRICTION_BOUND") or {}).get("net_target_to_friction_p95_ratio")),
            "target_to_friction_p95_base": number((values.get("BASE_005_065") or {}).get("net_target_to_friction_p95_ratio")),
            "target_to_friction_p95_adverse": number((values.get("ADVERSE_010_065") or {}).get("net_target_to_friction_p95_ratio")),
            "midpoint_profit_needed_p95_zero_usd": number((values.get("ZERO_FRICTION_BOUND") or {}).get("midpoint_profit_needed_p95_usd")),
            "midpoint_profit_needed_p95_base_usd": number((values.get("BASE_005_065") or {}).get("midpoint_profit_needed_p95_usd")),
            "midpoint_profit_needed_p95_adverse_usd": number((values.get("ADVERSE_010_065") or {}).get("midpoint_profit_needed_p95_usd")),
            "exit_depth_qualified_pct_worst_case": worst_depth,
            "all_three_cost_cases_present": set(values) == set(COST_CASES),
        })
    meta = {
        "input_rows": len(rows),
        "unique_friction_comparisons": len(grouped),
        "complete_zero_base_adverse_triplets": complete,
        "incomplete_triplets": incomplete,
        "duplicate_cost_case_rows": duplicate_cost_rows,
        "blocked_zero_unit_comparisons": blocked,
        "small_sample_comparisons": small_sample,
        "minimum_episode_gate_overall": 30,
        "minimum_mark_gate_overall": 500,
        "minimum_episode_gate_regime": 20,
        "minimum_mark_gate_regime": 100,
        "expected_cost_cases": list(COST_CASES),
    }
    return out, meta


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("status,detail\nEMPTY,No observations\n", encoding="utf-8")
        return
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def audit(policy_rows: list[dict[str, Any]], friction_rows: list[dict[str, Any]], out: Path) -> dict[str, Any]:
    policy_comp, policy_meta = compare_policy_rows(policy_rows)
    friction_comp, friction_meta = compare_friction_rows(friction_rows)
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "cost_sensitivity_by_policy.csv", policy_comp)
    write_csv(out / "friction_cost_sensitivity.csv", friction_comp)

    selected = [
        x for x in policy_comp
        if x["ratio_n"] in (1, 2, 5)
        and x["nav_usd"] in (100000.0, 1000000.0)
        and abs((x["tail_risk_budget_pct"] or 0) - 0.01) < 1e-9
        and x["policy"] in SHOW_POLICIES
    ]
    sample_bar_rows = sum(x["bar_sample_status"] in ("BAR_SAMPLE_OK_DIAGNOSTIC_ONLY", "BAR_REGIME_SAMPLE_OK_DIAGNOSTIC_ONLY") for x in friction_comp)
    blocked_bar_rows = sum(x["bar_sample_status"] == "BLOCKED_ZERO_WHOLE_UNITS" for x in friction_comp)
    pending_bar_rows = len(friction_comp) - sample_bar_rows - blocked_bar_rows
    meta = {
        "research_id": "QQQ_PUT_RATIO_COST_SENSITIVITY_AUDIT_V1",
        "status": "DIAGNOSTIC_ONLY_DEPLOYMENT_BLOCKED",
        "cost_cases": {
            "ZERO_FRICTION_BOUND": {"slippage_per_leg_usd": 0.0, "commission_per_contract_per_side_usd": 0.0},
            "BASE_005_065": {"slippage_per_leg_usd": 0.05, "commission_per_contract_per_side_usd": 0.65},
            "ADVERSE_010_065": {"slippage_per_leg_usd": 0.10, "commission_per_contract_per_side_usd": 0.65},
        },
        "policy_comparison": policy_meta,
        "friction_comparison": friction_meta,
        "friction_bar_quality": {
            "rows_with_adequate_minimum_sample_for_diagnostic": sample_bar_rows,
            "blocked_zero_units": blocked_bar_rows,
            "pending_small_or_incomplete_sample": pending_bar_rows,
            "sample_thresholds_are_screening_rules_not_statistical_validation": True,
        },
        "outputs": ["cost_sensitivity_by_policy.csv", "friction_cost_sensitivity.csv", "cost_sensitivity_audit_summary.json", "cost_sensitivity_audit_summary.md"],
        "interpretation": [
            "Cost scenarios are modeled slippage/commission assumptions on historical quote-side marks, not confirmed fills.",
            "Zero friction is a lower-bound comparison only, never the expected executable outcome.",
            "Episode and mark-count gates screen sample sufficiency, but do not correct for overlapping observations, source timing, selection bias, or fills.",
            "Rows with zero sized units have no BAR sample; their null BAR is not zero cost and remains blocked.",
            "No exit policy is promoted based on this audit.",
        ],
    }
    (out / "cost_sensitivity_audit_summary.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    lines = [
        "# QQQ put-ratio cost sensitivity and sample audit",
        "",
        "**Status: diagnostic only; deployment remains BLOCKED.**",
        "",
        "## Scenario coverage",
        "",
        f"- Policy matrix input rows: {len(policy_rows)}; unique cost-paired configurations: {policy_meta['unique_policy_comparisons']}.",
        f"- Full zero/base/adverse policy triplets: {policy_meta['complete_zero_base_adverse_triplets']}; incomplete triplets: {policy_meta['incomplete_triplets']}; duplicate cost rows: {policy_meta['duplicate_cost_case_rows']}.",
        f"- Friction BAR input rows: {len(friction_rows)}; unique cost-paired BAR configurations: {friction_meta['unique_friction_comparisons']}.",
        f"- Full zero/base/adverse BAR triplets: {friction_meta['complete_zero_base_adverse_triplets']}; incomplete triplets: {friction_meta['incomplete_triplets']}; duplicate cost rows: {friction_meta['duplicate_cost_case_rows']}.",
        "",
        "Cost cases: ZERO_FRICTION_BOUND (0 slippage/commission); BASE_005_065 (USD 0.05/leg slippage + USD 0.65/contract/side commission); ADVERSE_010_065 (USD 0.10/leg + USD 0.65/contract/side).",
        "",
        "## Representative 1% NAV tail-budget sensitivity",
        "",
        "| Direction | N | NAV | Policy | Eligible episodes | Zero friction net P&L | Base net P&L | Adverse net P&L | Adverse minus base | Base worst trade | Base win rate | Median trigger-to-action delay (sessions) |",
        "|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for x in selected:
        z, b, a = x.get("net_pnl_zero_friction_bound_usd"), x.get("net_pnl_base_005_065_usd"), x.get("net_pnl_adverse_010_065_usd")
        fmt = lambda v: "—" if v is None else f"{v:,.2f}"
        lines.append(
            f"| {x['direction']} | {x['ratio_n']} | USD {x['nav_usd']:,.0f} | {x['policy']} | "
            f"{x['depth_qualified_episodes']} | {fmt(z)} | {fmt(b)} | {fmt(a)} | "
            f"{fmt(x.get('net_pnl_adverse_minus_base_usd'))} | {fmt(x.get('worst_trade_base_005_065_usd'))} | "
            f"{fmt(x.get('win_rate_base_005_065_pct'))} | {fmt(x.get('median_trigger_to_action_delay_sessions_base'))} |"
        )
    lines += [
        "",
        "## Friction BAR eligibility",
        "",
        f"- BAR rows passing the minimum episode/mark-count screen (diagnostic only): {sample_bar_rows}.",
        f"- BAR rows blocked by zero whole units: {blocked_bar_rows}.",
        f"- BAR rows pending small/incomplete sample: {pending_bar_rows}.",
        "- OVERALL BAR screen: at least 30 qualifying episodes and 500 quote-mark observations in every cost case.",
        "- Regime BAR screen: at least 20 qualifying episodes and 100 quote-mark observations in every cost case.",
        "- Meeting the screen does not establish fill realism, independent observations, statistical significance, or a profitable exit rule.",
        "",
        "## Required interpretation",
        "",
        "- Compare net P&L, worst observed trade, win rate, profit factor, and trigger-to-action delay together. A lower-cost scenario is not evidence that the modeled costs will be achievable.",
        "- The policy matrix holds the same risk-budget sizing inputs constant while varying slippage/commission; capacity remains driven by worst observed terminal payoff and displayed entry depth.",
        "- Quote-side EOD marks remain unverified fills. All prior 2018–2025 observations remain development/revisit data, not blind final OOS.",
        "- No policy is promoted; unresolved margin, assignment, forced liquidation, decision-time marks and unseen OOS keep deployment BLOCKED.",
    ]
    (out / "cost_sensitivity_audit_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return meta


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--policy-matrix", type=Path, required=True)
    parser.add_argument("--friction-matrix", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    policy_rows = read_csv(args.policy_matrix)
    friction_rows = read_csv(args.friction_matrix)
    result = audit(policy_rows, friction_rows, args.out)
    print(json.dumps(result, indent=2))
    print((args.out / "cost_sensitivity_audit_summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
