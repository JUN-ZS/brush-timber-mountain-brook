#!/usr/bin/env python3
"""Post-replay causal decomposition for QQQ FAR CALL; descriptive only."""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median

STUDY_ID = "QQQ_FAR_CALL_INCREMENTAL_VALUE_V2"
REPORT_STATUS = "DESCRIPTIVE_DECOMPOSITION_ONLY_NOT_PERFORMANCE_APPROVED"
BASE_BUDGET = "SOURCE_MAX_LOSS_0P8PCT_NAV"


def number(value):
    if value is None or value == "":
        return None
    if isinstance(value, str) and value.strip().lower() in {"none", "null", "nan", "na"}:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def flag(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def load_csv(path):
    with Path(path).open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def scenario_id(row):
    existing = row.get("scenario_id")
    if existing:
        return str(existing)
    name = row.get("scenario")
    slip = number(row.get("slippage_per_leg_usd"))
    commission = number(row.get("commission_per_contract_per_side_usd"))
    if not name or slip is None or commission is None:
        return None
    return f"{name}|SLIP_PER_LEG_{slip:.3f}|COMM_PER_CONTRACT_SIDE_{commission:.2f}"


def group_scenarios(rows):
    result = defaultdict(list)
    for row in rows:
        key = scenario_id(row)
        if key:
            result[key].append(row)
    return result


def sum_field(rows, key):
    values = [number(row.get(key)) for row in rows]
    usable = [value for value in values if value is not None]
    return round(sum(usable), 6) if usable else 0.0


def stats(rows, key):
    values = [number(row.get(key)) for row in rows]
    values = [value for value in values if value is not None]
    return {
        "n": len(values),
        "mean": round(mean(values), 8) if values else None,
        "median": round(median(values), 8) if values else None,
        "min": round(min(values), 8) if values else None,
        "max": round(max(values), 8) if values else None,
    }


def independently_reconcile(trades):
    checked, errors = 0, []
    blocked_rows = []
    upstream = Counter()
    for row in trades:
        status = str(row.get("attribution_status") or "MISSING")
        upstream[status] += 1
        components = [
            number(row.get("entry_gross_credit_cash_usd")),
            number(row.get("entry_execution_costs_usd")),
            number(row.get("exit_gross_debit_cash_usd")),
            number(row.get("exit_execution_costs_usd")),
            number(row.get("realized_pnl_after_scenario_costs")),
        ]
        if any(value is None for value in components):
            blocked_rows.append(row)
            continue
        entry_gross, entry_cost, exit_gross, exit_cost, ledger = components
        calculated = entry_gross - entry_cost - exit_gross - exit_cost
        checked += 1
        errors.append(calculated - ledger)
    failures = sum(abs(error) > 0.01 for error in errors)
    if failures:
        status = "FAIL_INDEPENDENT_CASHFLOW_RECONCILIATION"
    elif blocked_rows:
        status = "BLOCKED_INDEPENDENT_CASHFLOW_RECONCILIATION"
    else:
        status = "PASS"
    return {
        "closed_trade_rows": len(trades),
        "independently_rechecked_rows": checked,
        "blocked_rows": len(blocked_rows),
        "upstream_attribution_status_counts": dict(upstream),
        "max_abs_independent_reconciliation_error_usd": round(max((abs(x) for x in errors), default=0.0), 8),
        "independent_failures_over_1cent": failures,
        "status": status,
    }


def waterfall(trades):
    fields = [
        "entry_gross_credit_cash_usd", "entry_execution_costs_usd",
        "exit_gross_debit_cash_usd", "exit_execution_costs_usd",
        "recomputed_net_pnl_usd", "realized_pnl_after_scenario_costs",
    ]
    result = {field: sum_field(trades, field) for field in fields}
    calculated = independently_reconcile(trades)
    result.update(calculated)
    return result


def summarize_entry(events, trades):
    event_counts = Counter(str(row.get("event") or "UNKNOWN") for row in events)
    reasons = Counter()
    for row in events:
        event = str(row.get("event") or "")
        if event.startswith("ENTRY_"):
            reasons[f"{event}:{row.get('reason') or 'NO_REASON'}"] += 1
    opens = [row for row in events if row.get("event") == "OPEN"]
    return {
        "event_counts": dict(event_counts),
        "entry_skip_or_block_reasons": dict(reasons),
        "opened_event_rows": len(opens),
        "open_event_gross_credit_per_share": stats(opens, "gross_credit_per_share"),
        "open_event_net_credit_per_share": stats(opens, "net_credit_per_share"),
        "open_event_quantity": stats(opens, "quantity"),
        "closed_trade_entry_gross_credit_per_share": stats(trades, "entry_gross_credit_per_share"),
        "closed_trade_entry_net_credit_per_share": stats(trades, "entry_net_credit_ps"),
        "closed_trade_entry_cost_usd": sum_field(trades, "entry_execution_costs_usd"),
        "closed_trade_entry_quote_quality_counts": dict(Counter(
            str(row.get("entry_quote_quality_bucket") or "UNKNOWN") for row in trades
        )),
        "note": "Trade and event counts are preserved as reported; a higher-cost arm may change selection eligibility, size, and number of trades.",
    }


def summarize_exits(trades):
    groups = defaultdict(list)
    for row in trades:
        groups[str(row.get("exit_reason") or "UNKNOWN_EXIT_REASON")].append(row)
    result = {}
    for reason, rows in sorted(groups.items()):
        result[reason] = {
            "closed_trade_count": len(rows),
            "net_pnl_usd": sum_field(rows, "realized_pnl_after_scenario_costs"),
            "mean_net_pnl_usd": stats(rows, "realized_pnl_after_scenario_costs")["mean"],
            "holding_calendar_days": stats(rows, "holding_calendar_days"),
            "exit_quote_missing_sessions": sum_field(rows, "exit_quote_missing_sessions"),
            "exit_basis_counts": dict(Counter(str(row.get("exit_debit_basis") or "UNKNOWN") for row in rows)),
            "reconciliation_failures": sum(
                row.get("attribution_status") == "FAIL_CASH_FLOW_RECONCILIATION" for row in rows
            ),
        }
    return result


def summarize_path(daily, expected_sessions):
    matches, status_counts = [], Counter()
    open_days = unmarked_open = pending_close = pending_open = 0
    for row in daily:
        status_counts[str(row.get("nav_mark_status") or "UNKNOWN")] += 1
        is_open = flag(row.get("position_open"))
        marked = number(row.get("nav_eod_marked"))
        baseline = number(row.get("no_call_baseline_nav"))
        if is_open:
            open_days += 1
            if marked is None:
                unmarked_open += 1
        pending_close += int(flag(row.get("pending_close")))
        pending_open += int(flag(row.get("pending_open")))
        if marked is not None and baseline is not None:
            matches.append((str(row.get("date") or ""), marked - baseline))
    values = [value for _, value in matches]
    matched_dates = [day for day, _ in matches]
    unmatched = max(0, len(daily) - len(matches))
    return {
        "daily_rows": len(daily),
        "expected_sessions": expected_sessions,
        "daily_row_count_matches_expected": expected_sessions is not None and len(daily) == expected_sessions,
        "matched_nav_sessions": len(matches),
        "unmatched_nav_sessions": unmatched,
        "first_matched_date": matched_dates[0] if matched_dates else None,
        "last_matched_date": matched_dates[-1] if matched_dates else None,
        "last_observed_incremental_nav_usd": round(values[-1], 2) if values else None,
        "minimum_observed_incremental_nav_usd": round(min(values), 2) if values else None,
        "maximum_observed_incremental_nav_usd": round(max(values), 2) if values else None,
        "positive_incremental_mark_days": sum(value > 0 for value in values),
        "positive_incremental_mark_fraction": round(sum(value > 0 for value in values) / len(values), 6) if values else None,
        "position_open_days": open_days,
        "position_open_but_unmarked_days": unmarked_open,
        "pending_close_days": pending_close,
        "pending_open_days": pending_open,
        "mark_status_counts": dict(status_counts),
        "interpretation": "Matched EOD mark differences only; missing dates excluded, never interpolated. Not a complete return series.",
    }


def make_id(name, slip, commission):
    if not name or number(slip) is None or number(commission) is None:
        return None
    return f"{name}|SLIP_PER_LEG_{number(slip):.3f}|COMM_PER_CONTRACT_SIDE_{number(commission):.2f}"


def build_report(summary, trades, events, daily):
    trade_groups, event_groups, daily_groups = map(group_scenarios, (trades, events, daily))
    metadata = {}
    for item in summary.get("scenarios", []):
        key = make_id(item.get("scenario"), item.get("slippage_per_leg_usd"),
                      item.get("commission_per_contract_per_side_usd"))
        if key:
            metadata[key] = item
    coverage = summary.get("coverage") or {}
    expected = number(coverage.get("expected_sessions"))
    if expected is None:
        expected = next((number(item.get("expected_sessions")) for item in metadata.values()
                         if number(item.get("expected_sessions")) is not None), None)
    expected = int(expected) if expected is not None else None
    terminal_gap = coverage.get("terminal_missing_sessions") or []
    source_last = coverage.get("last_source_observation")
    last_expected = coverage.get("last_expected_date")
    all_reconciliation = independently_reconcile(trades)

    scenarios = {}
    exit_rows = []
    keys = sorted(set(metadata) | set(trade_groups) | set(event_groups) | set(daily_groups))
    for key in keys:
        meta = metadata.get(key, {})
        trows, erows, drows = trade_groups.get(key, []), event_groups.get(key, []), daily_groups.get(key, [])
        path = summarize_path(drows, expected)
        cash = waterfall(trows)
        exits = summarize_exits(trows)
        missing_marks = number(meta.get("missing_position_mark_sessions"))
        if missing_marks is None:
            missing_marks = path["position_open_but_unmarked_days"]
        unresolved = int(number(meta.get("unresolved_or_open_position_at_end")) or 0)
        complete_by_rows = (
            path["daily_row_count_matches_expected"] and
            path["unmatched_nav_sessions"] == 0 and
            (missing_marks or 0) == 0 and unresolved == 0 and not terminal_gap
        )
        scenario_name = meta.get("scenario") or (trows[0].get("scenario") if trows else None)
        scenarios[key] = {
            "scenario": scenario_name,
            "budget_kind": meta.get("budget_kind"),
            "budget_pct_nav": number(meta.get("budget_pct_nav")),
            "slippage_per_leg_usd": number(meta.get("slippage_per_leg_usd")),
            "commission_per_contract_per_side_usd": number(meta.get("commission_per_contract_per_side_usd")),
            "opened_spreads": int(number(meta.get("opened_spreads")) or 0),
            "closed_spreads": int(number(meta.get("closed_spreads")) or len(trows)),
            "unresolved_or_open_at_end": unresolved,
            "entry_economics": summarize_entry(erows, trows),
            "cashflow_waterfall": cash,
            "exit_mechanism_attribution": exits,
            "daily_capital_and_mark_path": path,
            "source_and_completeness": {
                "expected_sessions": expected,
                "sessions_with_chain": int(number(coverage.get("chain_sessions")) or 0),
                "chain_coverage_fraction": round(number(coverage.get("chain_sessions")) / expected, 6)
                    if expected and number(coverage.get("chain_sessions")) is not None else None,
                "first_expected_date": coverage.get("first_expected_date"),
                "last_expected_date": last_expected,
                "last_source_observation": source_last,
                "terminal_missing_sessions": terminal_gap,
                "source_rows_cover_requested_end": not bool(terminal_gap) and source_last == last_expected,
                "complete_by_observed_rows": bool(complete_by_rows),
                "reported_missing_position_mark_sessions": int(missing_marks or 0),
                "EOD_quotes_confirm_executable_fills": False,
                "exact_quote_timestamp_verified": False,
                "virgin_holdout": False,
                "performance_gate": "BLOCKED",
            },
            "reported_closed_trade_net_pnl_usd": number(meta.get("closed_trade_net_pnl_sum_usd")),
            "reported_last_incremental_nav_usd": number(
                (meta.get("paired_nav_diagnostic") or {}).get("last_incremental_nav_vs_no_call_usd")
            ),
            "reported_paired_nav_diagnostic": meta.get("paired_nav_diagnostic"),
            "nav_path_complete_claimed_by_replay": bool(meta.get("nav_path_complete")),
        }
        for reason, metrics in exits.items():
            exit_rows.append({
                "row_type": "exit_mechanism", "scenario_id": key, "exit_reason": reason,
                "closed_trade_count": metrics["closed_trade_count"],
                "net_pnl_usd": metrics["net_pnl_usd"],
                "mean_holding_calendar_days": metrics["holding_calendar_days"]["mean"],
                "exit_quote_missing_sessions": metrics["exit_quote_missing_sessions"],
                "exit_basis_counts_json": json.dumps(metrics["exit_basis_counts"], sort_keys=True),
            })

    cost_differences = []
    by_budget = defaultdict(list)
    for key, item in scenarios.items():
        by_budget[item.get("scenario") or "UNKNOWN"].append((key, item))
    for budget_name, items in sorted(by_budget.items()):
        base = next((item for _, item in items
                     if item.get("slippage_per_leg_usd") == 0 and
                     item.get("commission_per_contract_per_side_usd") == 0), None)
        if base is None:
            continue
        base_pnl = number(base.get("reported_closed_trade_net_pnl_usd"))
        base_nav = number(base.get("reported_last_incremental_nav_usd"))
        for key, item in sorted(items, key=lambda pair: (
            number(pair[1].get("slippage_per_leg_usd")) or 0,
            number(pair[1].get("commission_per_contract_per_side_usd")) or 0)):
            pnl = number(item.get("reported_closed_trade_net_pnl_usd"))
            nav = number(item.get("reported_last_incremental_nav_usd"))
            cost_differences.append({
                "budget_scenario": budget_name, "scenario_id": key,
                "slippage_per_leg_usd": item.get("slippage_per_leg_usd"),
                "commission_per_contract_per_side_usd": item.get("commission_per_contract_per_side_usd"),
                "closed_trade_pnl_usd": pnl,
                "closed_trade_pnl_difference_vs_zero_cost_usd": round(pnl - base_pnl, 2)
                    if pnl is not None and base_pnl is not None else None,
                "opened_count_difference_vs_zero_cost": item.get("opened_spreads") - base.get("opened_spreads"),
                "closed_count_difference_vs_zero_cost": item.get("closed_spreads") - base.get("closed_spreads"),
                "last_nav_difference_vs_zero_cost_usd": round(nav - base_nav, 2)
                    if nav is not None and base_nav is not None else None,
                "interpretation": "Independent cost arm, not pure fee subtraction; size, entry eligibility, and trade counts may differ.",
            })

    base_key = make_id(BASE_BUDGET, 0, 0)
    base_result = scenarios.get(base_key, {})
    base_pnl = number(base_result.get("reported_closed_trade_net_pnl_usd"))
    base_nav = number(base_result.get("reported_last_incremental_nav_usd"))
    base_screen = "NOT_ESTABLISHED"
    if base_pnl is not None and base_nav is not None and base_pnl < 0 and base_nav < 0:
        base_screen = "FAILS_CURRENT_BASE_SCREEN"
    ledger_status = all_reconciliation["status"]
    return {
        "study_id": STUDY_ID,
        "status": REPORT_STATUS,
        "decision": {
            "base_screen": base_screen,
            "integration_eligible": False,
            "no_parameter_search": True,
            "reason": "The source max-loss zero-cost arm must show defensible incremental value; the observed base screen is negative and source completeness, timestamp/fill and lockbox gates remain blocked.",
            "frozen_original_hybrid_changed": False,
            "main_changed": False,
            "broker_orders_enabled": False,
        },
        "global_ledger_quality": all_reconciliation,
        "evidence_limits": {
            "quote_evidence": "Public preservation-mirror EOD quote sides; not confirmed fills.",
            "exact_quote_tick_timestamp": "UNVERIFIED",
            "source_last_observation": source_last,
            "requested_last_date": last_expected,
            "terminal_source_gap_sessions": len(terminal_gap),
            "terminal_source_gap_dates": terminal_gap,
            "virgin_holdout": False,
            "CAGR_MaxDD_Sharpe_ES95": "BLOCKED; not calculated or claimed.",
        },
        "coverage": coverage,
        "scenario_decompositions": scenarios,
        "cost_scenario_comparisons": cost_differences,
        "exit_mechanism_csv_rows": exit_rows,
        "methodology": {
            "A_entry_economics": "Summarize the frozen entry selection, observed-side gross/net credits, costs, sizes, and entry skip/block reasons. Do not turn post-hoc quote bins into entry rules.",
            "B_mark_and_capital_occupancy": "Paired overlay-minus-no-call NAV only on dates where both values exist; missing days are excluded and never interpolated.",
            "C_exit_lifecycle": "Group actual existing exit reasons, holding duration, quote-delay counts and settlement basis; do not tune exit thresholds or infer causality from group membership alone.",
            "D_data_integrity_and_incremental_value": "Expose source gaps, missing marks, unresolved positions and paired matched-day values. EOD-only quotes keep performance approval blocked.",
            "costs": "Scenario differences are not isolated cost deductions because sizing and trade counts can differ across independently replayed arms.",
        },
    }


def render_markdown(report):
    coverage = report["coverage"]
    ledger = report["global_ledger_quality"]
    lines = [
        "# QQQ FAR CALL incremental-value decomposition V2",
        "",
        "Status: DESCRIPTIVE DECOMPOSITION ONLY — NOT PERFORMANCE APPROVED.",
        "",
        "This report measures four predeclared dimensions. It does not change strategy rules and does not treat EOD quote sides as confirmed fills.",
        "",
        "## Gate status",
        "",
        f"- Base screen: {report['decision']['base_screen']}",
        f"- Independent cash-flow ledger: {ledger['status']}",
        f"- Independently rechecked trade rows: {ledger['independently_rechecked_rows']} / {ledger['closed_trade_rows']}",
        f"- Maximum absolute independent reconciliation error: USD {ledger['max_abs_independent_reconciliation_error_usd']}",
        f"- Source terminal gap sessions: {report['evidence_limits']['terminal_source_gap_sessions']}",
        f"- Last source date: {report['evidence_limits']['source_last_observation']}",
        "- Frozen Original Hybrid changed: False",
        "- Main changed: False",
        "- Broker orders enabled: False",
        "",
        "## Coverage",
        "",
        f"- Expected sessions: {coverage.get('expected_sessions')}",
        f"- Sessions with QQQ chain rows: {coverage.get('chain_sessions')}",
        f"- Expected date range: {coverage.get('first_expected_date')} to {coverage.get('last_expected_date')}",
        f"- Last source observation: {coverage.get('last_source_observation')}",
        f"- Terminal source gap sessions: {len(coverage.get('terminal_missing_sessions') or [])}",
        "- The inspected 2018–2025 interval is development evidence, not a virgin holdout.",
        "",
        "## Scenario decomposition",
        "",
        "| Budget | Slippage/leg | Commission/contract/side | Opens | Closes | Entry gross credit | Entry costs | Exit gross debit | Exit costs | Closed-trade P&L | Paired NAV days | Unmatched days | Last observed NAV difference | Open but unmarked days |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for key, item in sorted(report["scenario_decompositions"].items()):
        cash = item["cashflow_waterfall"]
        path = item["daily_capital_and_mark_path"]
        def money(value):
            return "—" if value is None else f"USD {value:,.2f}"
        lines.append(
            f"| {item.get('scenario')} | {item.get('slippage_per_leg_usd')} | "
            f"{item.get('commission_per_contract_per_side_usd')} | {item.get('opened_spreads')} | "
            f"{item.get('closed_spreads')} | {money(cash.get('entry_gross_credit_cash_usd'))} | "
            f"{money(cash.get('entry_execution_costs_usd'))} | {money(cash.get('exit_gross_debit_cash_usd'))} | "
            f"{money(cash.get('exit_execution_costs_usd'))} | {money(item.get('reported_closed_trade_net_pnl_usd'))} | "
            f"{path.get('matched_nav_sessions')} | {path.get('unmatched_nav_sessions')} | "
            f"{money(path.get('last_observed_incremental_nav_usd'))} | {path.get('position_open_but_unmarked_days')} |"
        )
    base_key = make_id(BASE_BUDGET, 0, 0)
    base = report["scenario_decompositions"].get(base_key, {})
    lines += [
        "",
        "## Existing exit-mechanism attribution — source budget, zero extra costs",
        "",
        "| Existing exit reason | Trades | Net P&L | Mean holding days | Exit quote-delay sessions | Exit basis counts |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for reason, item in base.get("exit_mechanism_attribution", {}).items():
        mean_days = item["holding_calendar_days"]["mean"]
        lines.append(
            f"| {reason} | {item['closed_trade_count']} | USD {item['net_pnl_usd']:,.2f} | "
            f"{'—' if mean_days is None else round(mean_days, 2)} | "
            f"{item['exit_quote_missing_sessions']} | {json.dumps(item['exit_basis_counts'], sort_keys=True)} |"
        )
    lines += [
        "",
        "## Cost-arm differences",
        "",
        "These are separately sized replay outcomes versus the zero-cost arm, not isolated fee deductions. Entry eligibility and trade counts can change.",
        "",
        "| Budget | Slippage/leg | Commission/side | Closed-trade P&L delta | Open-count delta | Close-count delta | Terminal paired-NAV delta |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for item in report["cost_scenario_comparisons"]:
        fmt = lambda value: "—" if value is None else f"USD {value:,.2f}"
        lines.append(
            f"| {item['budget_scenario']} | {item['slippage_per_leg_usd']} | "
            f"{item['commission_per_contract_per_side_usd']} | "
            f"{fmt(item['closed_trade_pnl_difference_vs_zero_cost_usd'])} | "
            f"{item['opened_count_difference_vs_zero_cost']} | {item['closed_count_difference_vs_zero_cost']} | "
            f"{fmt(item['last_nav_difference_vs_zero_cost_usd'])} |"
        )
    lines += [
        "",
        "## Measurement verdict",
        "",
        "A. Entry economics: report observed-side credit, assumed costs, contract quantity and all entry skips/blocks.",
        "",
        "B. Capital occupancy and marks: use paired dates only. No missing mark is filled and no return-series metrics are inferred from the paired differences.",
        "",
        "C. Exit lifecycle: summarize existing exit groups and quote-delay/settlement bases only. This is not proof that an exit rule caused the loss.",
        "",
        "D. Data completeness and value: source stops before the requested final date, quotes are EOD, and the reviewed period is not an untouched holdout. Integration remains blocked.",
        "",
        "CAGR, daily MTM MaxDD, Sharpe and ES95 are not calculated or claimed. This report does not mutate the Frozen Original Hybrid, main, live sizing, or broker-order permissions.",
        "",
    ]
    return "\n".join(lines)


def write_outputs(report, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "qqq_far_call_incremental_decomposition.json"
    md_path = out_dir / "qqq_far_call_incremental_decomposition.md"
    csv_path = out_dir / "qqq_far_call_incremental_decomposition.csv"
    json_path.write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    rows = []
    for key, item in sorted(report["scenario_decompositions"].items()):
        cash, path = item["cashflow_waterfall"], item["daily_capital_and_mark_path"]
        rows.append({
            "row_type": "scenario", "scenario_id": key, "scenario": item.get("scenario"),
            "budget_kind": item.get("budget_kind"), "slippage_per_leg_usd": item.get("slippage_per_leg_usd"),
            "commission_per_contract_per_side_usd": item.get("commission_per_contract_per_side_usd"),
            "opens": item.get("opened_spreads"), "closes": item.get("closed_spreads"),
            "entry_gross_credit_cash_usd": cash.get("entry_gross_credit_cash_usd"),
            "entry_execution_costs_usd": cash.get("entry_execution_costs_usd"),
            "exit_gross_debit_cash_usd": cash.get("exit_gross_debit_cash_usd"),
            "exit_execution_costs_usd": cash.get("exit_execution_costs_usd"),
            "realized_pnl_usd": item.get("reported_closed_trade_net_pnl_usd"),
            "independent_reconciliation_error_usd": cash.get("max_abs_independent_reconciliation_error_usd"),
            "matched_nav_sessions": path.get("matched_nav_sessions"),
            "unmatched_nav_sessions": path.get("unmatched_nav_sessions"),
            "last_incremental_nav_usd": path.get("last_observed_incremental_nav_usd"),
            "min_incremental_nav_usd": path.get("minimum_observed_incremental_nav_usd"),
            "max_incremental_nav_usd": path.get("maximum_observed_incremental_nav_usd"),
            "open_unmarked_days": path.get("position_open_but_unmarked_days"),
        })
    rows.extend(report.get("exit_mechanism_csv_rows", []))
    rows.extend({"row_type": "cost_comparison", **item} for item in report.get("cost_scenario_comparisons", []))
    fields = sorted({field for row in rows for field in row})
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return {"json": str(json_path), "markdown": str(md_path), "csv": str(csv_path)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", default="artifacts/qqq_far_call_replay")
    parser.add_argument("--out-dir", default="artifacts/qqq_far_call_replay/incremental_decomposition")
    args = parser.parse_args()
    input_dir = Path(args.input_dir)
    required = {
        "summary": input_dir / "qqq_far_call_replay_summary.json",
        "trades": input_dir / "qqq_far_call_replay_trades.csv",
        "events": input_dir / "qqq_far_call_replay_events.csv",
        "daily": input_dir / "qqq_far_call_replay_daily.csv",
    }
    missing = [str(path) for path in required.values() if not path.is_file()]
    if missing:
        raise SystemExit("Required replay output missing: " + ", ".join(missing))
    summary = json.loads(required["summary"].read_text(encoding="utf-8"))
    report = build_report(
        summary, load_csv(required["trades"]),
        load_csv(required["events"]), load_csv(required["daily"]),
    )
    paths = write_outputs(report, args.out_dir)
    print(json.dumps({
        "study_id": report["study_id"], "status": report["status"],
        "decision": report["decision"], "global_ledger_quality": report["global_ledger_quality"],
        "scenario_count": len(report["scenario_decompositions"]),
        "cost_comparison_rows": len(report["cost_scenario_comparisons"]), "outputs": paths,
    }, indent=2))
    if report["global_ledger_quality"]["status"] != "PASS":
        raise SystemExit("Cash-flow ledger hard gate failed; inspect report before interpretation")


if __name__ == "__main__":
    main()
