#!/usr/bin/env python3
"""Mode C capacity-gated portfolio replay from the source-pinned DTE factorial episodes.

Mode C: fixed 10-session signal schedule; cap admitted cohorts at 1 or 2; skip a scheduled
entry when the cap is occupied; do not re-anchor. Each exit policy gets its own independent book.
Entries and exits are quote-side estimates, not verified fills or a broker margin simulation.
"""
from __future__ import annotations

import argparse
import csv
import math
import statistics
from collections import defaultdict
from datetime import date
from pathlib import Path
import json

BASE = Path("research/qqq_spy_call_fixed_ratio_size_gated_v1")
ROOT = BASE / "results/dte_hold_exit_factorial_call_v1"
START, END = date(2018, 3, 1), date(2025, 12, 15)
YEARS = (END - START).days / 365.25
DTE_BANDS = {20: (14, 26), 30: (24, 36), 45: (39, 51), 60: (54, 66)}
PHASES = (0, 2, 4, 6, 8)
HOLDS = (5, 10, 15, 20)
GUARDS = (None, 7, 14)
POLICIES = {
    (hold, guard): (
        f"HOLD_{hold}_SESSIONS" if guard is None
        else f"HOLD_{hold}_OR_DTE_LE_{guard}"
    )
    for hold in HOLDS for guard in GUARDS
}
CAPS = (None, 1, 2)
REQUIRED = {
    "episode_id", "policy", "status", "signal_date", "signal_index",
    "entry_date", "entry_index", "expiry", "signal_dte", "long_qqq_qty",
    "short_spy_qty", "spy_call_strike_delivery_obligation_usd",
    "exit_signal_date", "exit_signal_index", "exit_index", "exit_date",
    "exit_reason", "last_observed_date", "net_pnl_usd"
}

def fnum(value):
    try:
        v = float(value)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None

def med(values):
    clean = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    return statistics.median(clean) if clean else None

def fmt(value, digits=0):
    if value is None or not math.isfinite(float(value)):
        return "n/a"
    return f"{float(value):,.{digits}f}"

def read_csv(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write_csv(path, rows):
    if not rows:
        raise RuntimeError(f"refusing to write empty output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

def exit_release_index(row, source_sessions):
    # If quote-side exit never resolved, retain slot through source end; expiry may imply assignment.
    if (row.get("status") or "").upper() == "RESOLVED":
        i = fnum(row.get("exit_index"))
        if i is None:
            raise RuntimeError(f"resolved row missing exit_index: episode={row.get('episode_id')}")
        return int(i)
    return source_sessions + 1

def gate_candidates(candidates, cap, source_sessions):
    ordered = sorted(candidates, key=lambda r: (
        int(float(r["signal_index"])), int(float(r["entry_index"])), int(float(r["episode_id"]))
    ))
    if cap is None:
        return ordered, []
    selected, blocked = [], []
    for row in ordered:
        signal_idx = int(float(row["signal_index"]))
        active = [s for s in selected if exit_release_index(s, source_sessions) > signal_idx]
        if len(active) < cap:
            selected.append(row)
        else:
            blocked.append(row)
    return selected, blocked

def portfolio_metrics(selected, source_sessions):
    resolved = [r for r in selected if (r.get("status") or "").upper() == "RESOLVED"
                and fnum(r.get("net_pnl_usd")) is not None]
    unresolved = [r for r in selected if (r.get("status") or "").upper() != "RESOLVED"]
    pnls = [float(r["net_pnl_usd"]) for r in resolved]
    wins = [x for x in pnls if x > 0.005]
    losses = [x for x in pnls if x < -0.005]
    total = sum(pnls)
    positive = sum(wins)
    negative = abs(sum(losses))
    # Close events at a session are processed before an entry on that same session.
    events = defaultdict(lambda: [0, 0.0])
    for r in selected:
        start = fnum(r.get("entry_index"))
        if start is None:
            continue
        start = int(start)
        is_resolved = (r.get("status") or "").upper() == "RESOLVED"
        end = int(float(r["exit_index"])) if is_resolved and fnum(r.get("exit_index")) is not None else source_sessions
        obligation = fnum(r.get("spy_call_strike_delivery_obligation_usd")) or 0.0
        events[start][0] += 1
        events[start][1] += obligation
        events[end][0] -= 1
        events[end][1] -= obligation
    live = 0
    obligation_live = 0.0
    peak_live = 0
    peak_obligation = 0.0
    for idx in sorted(events):
        live += events[idx][0]
        obligation_live += events[idx][1]
        peak_live = max(peak_live, live)
        peak_obligation = max(peak_obligation, obligation_live)
    annual = total / YEARS
    year_pnl = {}
    year_count = {}
    for y in range(2018, 2026):
        yr = [r for r in resolved if r.get("exit_date") and int(r["exit_date"][:4]) == y]
        year_pnl[y] = round(sum(float(r["net_pnl_usd"]) for r in yr), 2)
        year_count[y] = len(yr)
    return {
        "entries_admitted": len(selected),
        "resolved": len(resolved),
        "unresolved": len(unresolved),
        "total_resolved_pnl_usd": round(total, 2),
        "annual_resolved_pnl_usd": round(annual, 2),
        "win_rate_pct": round(100 * len(wins) / len(resolved), 4) if resolved else None,
        "expectancy_usd": round(total / len(resolved), 2) if resolved else None,
        "median_trade_usd": round(statistics.median(pnls), 2) if pnls else None,
        "worst_trade_usd": round(min(pnls), 2) if pnls else None,
        "profit_factor": round(positive / negative, 6) if negative else (None if not wins else "INF"),
        "peak_concurrent_cohorts": peak_live,
        "peak_gross_call_delivery_notional_usd": round(peak_obligation, 2),
        "year_pnl": year_pnl,
        "year_count": year_count,
    }

def self_test():
    def row(eid, sig, entry, exit_idx, status="RESOLVED"):
        return {
            "episode_id": str(eid), "signal_index": str(sig), "entry_index": str(entry),
            "exit_index": "" if exit_idx is None else str(exit_idx), "status": status,
        }
    sample = [row(1, 0, 1, 20), row(2, 5, 6, 25), row(3, 10, 11, 30),
              row(4, 20, 21, None, "UNRESOLVED_SOURCE_END")]
    one, blocked_one = gate_candidates(sample, 1, 40)
    assert [int(r["episode_id"]) for r in one] == [1, 4]
    assert [int(r["episode_id"]) for r in blocked_one] == [2, 3]
    two, blocked_two = gate_candidates(sample, 2, 40)
    assert [int(r["episode_id"]) for r in two] == [1, 2, 4]
    assert [int(r["episode_id"]) for r in blocked_two] == [3]
    all_rows, blocked_all = gate_candidates(sample, None, 40)
    assert len(all_rows) == 4 and not blocked_all
    # An unresolved accepted cohort keeps the slot reserved through source end.
    final, blocked_final = gate_candidates([row(1, 0, 1, None, "UNRESOLVED_SOURCE_END"),
                                            row(2, 10, 11, 25)], 1, 40)
    assert [int(r["episode_id"]) for r in final] == [1]
    assert [int(r["episode_id"]) for r in blocked_final] == [2]
    print("MODE-C SELF-TEST PASS: cap=1/cap=2/unlimited; same-day release; unresolved hold-open.")

def load_phase(dte, phase):
    out = ROOT / f"dte_{dte}" / f"phase_{phase}"
    for filename in ("summary.json", "factorial_policy_summary.json", "trade_episodes.csv"):
        path = out / filename
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError(f"missing required replay output: {path}")
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    policy_summary_raw = json.loads((out / "factorial_policy_summary.json").read_text(encoding="utf-8"))
    policy_summary = {p["policy"]: p for p in policy_summary_raw["policies"]}
    trade_rows = read_csv(out / "trade_episodes.csv")
    if not trade_rows:
        raise RuntimeError(f"no trade episodes: {out}")
    missing = REQUIRED - set(trade_rows[0].keys())
    if missing:
        raise RuntimeError(f"trade episode CSV lacks capacity-audit fields {sorted(missing)}: {out}")
    source_sessions = int(summary["coverage"]["common_underlying_sessions"])
    if source_sessions < 1:
        raise RuntimeError(f"invalid common session count: {out}")
    for (hold, guard), policy in POLICIES.items():
        rows = [r for r in trade_rows if r.get("policy") == policy]
        if not rows:
            raise RuntimeError(f"missing policy rows {policy} in {out}")
        expected = policy_summary[policy]
        resolved = [r for r in rows if (r.get("status") or "").upper() == "RESOLVED"]
        unresolved = [r for r in rows if (r.get("status") or "").upper() != "RESOLVED"]
        if len(resolved) != int(expected.get("resolved") or 0) or len(unresolved) != int(expected.get("unresolved") or 0):
            raise RuntimeError(f"resolved/unresolved count mismatch dte={dte} phase={phase} policy={policy}")
        actual_pnl = sum(fnum(r.get("net_pnl_usd")) or 0.0 for r in resolved)
        expected_pnl = fnum(expected.get("total_net_pnl_usd")) or 0.0
        if abs(actual_pnl - expected_pnl) > 0.02:
            raise RuntimeError(f"trade-level P&L doesn't reconcile to replay summary dte={dte} phase={phase} policy={policy} actual={actual_pnl} expected={expected_pnl}")
    return summary, policy_summary, trade_rows, source_sessions

def generate():
    cell_rows = []
    selected_episode_rows = []
    year_rows = []
    config_accum = defaultdict(list)
    phase_data = {}
    for dte in DTE_BANDS:
        for phase in PHASES:
            phase_data[(dte, phase)] = load_phase(dte, phase)
    # Independently gate each policy; exit timing of another policy never controls admissions.
    for dte, (dte_min, dte_max) in DTE_BANDS.items():
        for phase in PHASES:
            summary, policy_summary, all_trades, source_sessions = phase_data[(dte, phase)]
            for (hold, guard), policy in POLICIES.items():
                candidates = sorted(
                    [r for r in all_trades if r.get("policy") == policy and r.get("entry_date")],
                    key=lambda r: (int(float(r["signal_index"])), int(float(r["entry_index"])), int(float(r["episode_id"])))
                )
                expected = policy_summary[policy]
                if len(candidates) != int(expected.get("resolved") or 0) + int(expected.get("unresolved") or 0):
                    raise RuntimeError(f"candidate count differs from replay summary dte={dte} phase={phase} policy={policy} candidates={len(candidates)}")
                for cap in CAPS:
                    selected, blocked = gate_candidates(candidates, cap, source_sessions)
                    metrics = portfolio_metrics(selected, source_sessions)
                    if cap is None:
                        if metrics["resolved"] != int(expected.get("resolved") or 0) or metrics["unresolved"] != int(expected.get("unresolved") or 0):
                            raise RuntimeError(f"uncapped count mismatch dte={dte} phase={phase} policy={policy}")
                        if abs(metrics["total_resolved_pnl_usd"] - (fnum(expected.get("total_net_pnl_usd")) or 0.0)) > 0.02:
                            raise RuntimeError(f"uncapped P&L mismatch dte={dte} phase={phase} policy={policy}")
                    gate_name = "UNLIMITED" if cap is None else str(cap)
                    cell = {
                        "dte_target": dte, "dte_min": dte_min, "dte_max": dte_max,
                        "phase_sessions": phase, "hold_sessions": hold,
                        "expiry_guard_dte": "" if guard is None else guard, "policy": policy,
                        "max_concurrent_cohorts": gate_name,
                        "entry_candidates": len(candidates), "capacity_skipped": len(blocked),
                        "capacity_skip_pct": round(100 * len(blocked) / len(candidates), 2) if candidates else 0.0,
                        **{k: v for k, v in metrics.items() if k not in ("year_pnl", "year_count")},
                    }
                    cell_rows.append(cell)
                    for year in range(2018, 2026):
                        year_rows.append({
                            "dte_target": dte, "phase_sessions": phase, "hold_sessions": hold,
                            "expiry_guard_dte": "" if guard is None else guard, "policy": policy,
                            "max_concurrent_cohorts": gate_name, "exit_year": year,
                            "resolved_trade_pnl_usd": metrics["year_pnl"][year],
                            "resolved_trades": metrics["year_count"][year],
                        })
                    for r in selected:
                        selected_episode_rows.append({
                            "dte_target": dte, "phase_sessions": phase, "hold_sessions": hold,
                            "expiry_guard_dte": "" if guard is None else guard, "policy": policy,
                            "max_concurrent_cohorts": gate_name, "episode_id": r.get("episode_id"),
                            "status": r.get("status"), "signal_date": r.get("signal_date"),
                            "signal_index": r.get("signal_index"), "entry_date": r.get("entry_date"),
                            "entry_index": r.get("entry_index"), "expiry": r.get("expiry"),
                            "signal_dte": r.get("signal_dte"), "exit_signal_date": r.get("exit_signal_date"),
                            "exit_date": r.get("exit_date"), "exit_index": r.get("exit_index"),
                            "exit_delay_sessions": r.get("exit_delay_sessions"), "exit_reason": r.get("exit_reason"),
                            "net_pnl_usd": r.get("net_pnl_usd"), "long_qqq_qty": r.get("long_qqq_qty"),
                            "short_spy_qty": r.get("short_spy_qty"),
                            "spy_call_strike_delivery_obligation_usd": r.get("spy_call_strike_delivery_obligation_usd"),
                        })
    groups = defaultdict(list)
    for r in cell_rows:
        groups[(r["dte_target"], r["max_concurrent_cohorts"], r["hold_sessions"], str(r["expiry_guard_dte"]), r["policy"])].append(r)
    by_phase = {(r["dte_target"], r["phase_sessions"], r["policy"], r["max_concurrent_cohorts"]): r for r in cell_rows}
    configs = []
    for (dte, gate, hold, guard, policy), rows in sorted(groups.items(), key=lambda item: (
        item[0][0], 99 if item[0][1] == "UNLIMITED" else int(item[0][1]),
        item[0][2], 99 if item[0][3] == "" else int(item[0][3])
    )):
        annual = [float(r["annual_resolved_pnl_usd"]) for r in rows]
        base_rows = [by_phase.get((dte, r["phase_sessions"], policy, "UNLIMITED")) for r in rows]
        retained = [
            float(r["annual_resolved_pnl_usd"]) / float(b["annual_resolved_pnl_usd"]) * 100
            for r, b in zip(rows, base_rows)
            if b and float(b["annual_resolved_pnl_usd"]) > 0
        ]
        obligation_reduction = [
            (1 - float(r["peak_gross_call_delivery_notional_usd"]) / float(b["peak_gross_call_delivery_notional_usd"])) * 100
            for r, b in zip(rows, base_rows)
            if b and float(b["peak_gross_call_delivery_notional_usd"]) > 0
        ]
        max_obligation = max(float(r["peak_gross_call_delivery_notional_usd"]) for r in rows)
        worst_values = [float(r["worst_trade_usd"]) for r in rows if r["worst_trade_usd"] is not None]
        pf_values = [r["profit_factor"] for r in rows if fnum(r["profit_factor"]) is not None]
        configs.append({
            "dte_target": dte, "dte_min": DTE_BANDS[dte][0], "dte_max": DTE_BANDS[dte][1],
            "max_concurrent_cohorts": gate, "hold_sessions": hold,
            "expiry_guard_dte": guard, "policy": policy, "phase_count": len(rows),
            "median_annual_resolved_pnl_usd": round(statistics.median(annual), 2),
            "min_phase_annual_pnl_usd": round(min(annual), 2), "max_phase_annual_pnl_usd": round(max(annual), 2),
            "phases_ge_12000_usd": sum(1 for x in annual if x >= 12000),
            "median_entry_candidates": round(statistics.median(float(r["entry_candidates"]) for r in rows), 1),
            "median_entries_admitted": round(statistics.median(float(r["entries_admitted"]) for r in rows), 1),
            "median_capacity_skipped": round(statistics.median(float(r["capacity_skipped"]) for r in rows), 1),
            "median_capacity_skip_pct": round(statistics.median(float(r["capacity_skip_pct"]) for r in rows), 2),
            "median_resolved": round(statistics.median(float(r["resolved"]) for r in rows), 1),
            "median_unresolved": round(statistics.median(float(r["unresolved"]) for r in rows), 1),
            "median_win_rate_pct": round(med([r["win_rate_pct"] for r in rows]) or 0, 2),
            "median_expectancy_usd": round(med([r["expectancy_usd"] for r in rows]) or 0, 2),
            "median_worst_trade_usd": round(med([r["worst_trade_usd"] for r in rows]) or 0, 2),
            "worst_trade_across_phases_usd": round(min(worst_values), 2) if worst_values else None,
            "median_profit_factor": round(med(pf_values) or 0, 4),
            "median_peak_concurrent_cohorts": round(statistics.median(float(r["peak_concurrent_cohorts"]) for r in rows), 1),
            "max_peak_gross_call_delivery_notional_usd": round(max_obligation, 2),
            "median_pnl_retained_pct_vs_unlimited": round(statistics.median(retained), 2) if retained else None,
            "median_peak_delivery_notional_reduction_pct_vs_unlimited": round(statistics.median(obligation_reduction), 2) if obligation_reduction else None,
            "median_annual_pnl_per_100k_delivery_notional_usd": round(statistics.median(annual) /
                (max_obligation / 100000), 2) if max_obligation > 0 else None,
        })
    write_csv(ROOT / "mode_c_capacity_matrix.csv", cell_rows)
    write_csv(ROOT / "mode_c_capacity_config_summary.csv", configs)
    write_csv(ROOT / "mode_c_capacity_calendar_year_pnl.csv", year_rows)
    write_csv(ROOT / "mode_c_selected_episodes.csv", selected_episode_rows)
    make_report(configs)

def make_report(configs):
    lines = [
        "# Mode C: Capacity-gated DTE × holding × exit comparison", "",
        f"- Replay period: {START.isoformat()} through {END.isoformat()} ({YEARS:.3f} calendar years).",
        "- Strategy: QQQ LONG CALL 1 : SPY SHORT CALL 6; same expiry; both legs nearest absolute Delta 0.25; fixed 10-common-session signal cadence; five phase anchors 0, 2, 4, 6, 8.",
        "- Costs: USD 0.05 per option-share per side slippage and USD 0.65 per contract per side commission.",
        "- Mode C semantics: each holding/exit policy owns an independent book; admit a new signal only if live cohort reservations are below cap 1 or 2; skip blocked signals without re-anchoring; unresolved/expired-without-executable-exit cohorts reserve capacity through source end.",
        "- Capacity gating is a chronological admission simulation over the same source-pinned, per-cohort quote-side outcomes. Blocked cohorts contribute no P&L; because positions are separately simulated, their hypothetical paths do not affect later cohorts.",
        "- Annual P&L is resolved episode net P&L summed then divided by 7.792 calendar years; not CAGR, account return, or proof of USD 100,000 buying-power feasibility.",
        "- Peak gross call-delivery notional is the sum of SPY short-call strike × 100 × short contracts across concurrently open admitted cohorts; it is not broker margin or a risk cap. Uncovered short-call losses can exceed this notional and are theoretically unbounded.",
        "- Unresolved episodes are excluded from P&L but keep their capacity slot through source end. EOD quote-side prices are not verified fills.",
        "",
        "## Shortlist across DTE and capacity limits", "",
        "| DTE band | Max cohorts | Hold | Exit guard | Median annual P&L | Phase range | P&L retained vs unlimited | Peak delivery-notional reduction | Median skipped | Worst trade across phases | Peak call delivery notional |",
        "|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    shortlisted = []
    for dte in (20, 30, 45, 60):
        for gate in ("1", "2", "UNLIMITED"):
            rows = [r for r in configs if r["dte_target"] == dte and r["max_concurrent_cohorts"] == gate]
            rows.sort(key=lambda r: (
                -float(r["median_annual_resolved_pnl_usd"]),
                float(r["max_peak_gross_call_delivery_notional_usd"]),
                -float(r["median_pnl_retained_pct_vs_unlimited"] or 0)
            ))
            show = rows[:2]
            shorter = [r for r in rows if r["hold_sessions"] <= 15]
            if shorter:
                eff = max(shorter, key=lambda r: float(r["median_annual_resolved_pnl_usd"]) /
                          max(float(r["max_peak_gross_call_delivery_notional_usd"]), 1))
                if eff not in show:
                    show.append(eff)
            for r in show:
                if r not in shortlisted:
                    shortlisted.append(r)
    for r in shortlisted:
        lines.append(
            f"| {r['dte_target']} ({r['dte_min']}-{r['dte_max']}) | {r['max_concurrent_cohorts']} | {r['hold_sessions']} | "
            f"{'none' if r['expiry_guard_dte']=='' else 'DTE <= '+str(r['expiry_guard_dte'])} | "
            f"{fmt(r['median_annual_resolved_pnl_usd'])} | {fmt(r['min_phase_annual_pnl_usd'])}–{fmt(r['max_phase_annual_pnl_usd'])} | "
            f"{fmt(r['median_pnl_retained_pct_vs_unlimited'],1)}% | "
            f"{fmt(r['median_peak_delivery_notional_reduction_pct_vs_unlimited'],1)}% | "
            f"{r['median_capacity_skipped']} / {r['median_entry_candidates']} ({fmt(r['median_capacity_skip_pct'],1)}%) | "
            f"{fmt(r['worst_trade_across_phases_usd'])} | {fmt(r['max_peak_gross_call_delivery_notional_usd'])} |"
        )
    lines += [
        "", "## How to interpret it", "",
        "- Cap 1 serializes the portfolio; cap 2 allows up to two open/reserved cohorts; UNLIMITED is the control.",
        "- Annual median must be read with phase range, skipped-entry rate, worst trade, unresolved counts, peak simultaneous cohorts and gross call-delivery notional.",
        "- Cap reduces admitted opportunities, so lower total P&L can coexist with similar per-trade expectancy. It is useful only if lower stacked exposure is worth the income surrendered.",
        "- A high win rate does not neutralize the 1:6 structure's short-call tail risk. Account cash, broker margin, forced liquidation, financing, tax, compounding and TAIL cost are not modeled.",
        "- Before choosing any configuration for live use, validate the underlying quote history, fills and the actual broker's assignment/margin treatment.",
        "",
        "Machine-readable outputs: mode_c_capacity_matrix.csv (720 phase cells), mode_c_capacity_config_summary.csv (144 configurations), mode_c_capacity_calendar_year_pnl.csv, and mode_c_selected_episodes.csv.", ""
    ]
    (ROOT / "MODE_C_CAPACITY_GATE_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"MODE-C AUDIT PASS: report has {len(configs)} config rows")

def generate():
    cell_rows = []
    selected_episode_rows = []
    year_rows = []
    phase_data = {}
    for dte in DTE_BANDS:
        for phase in PHASES:
            phase_data[(dte, phase)] = load_phase(dte, phase)
    for dte, (dte_min, dte_max) in DTE_BANDS.items():
        for phase in PHASES:
            summary, policy_summary, all_trades, source_sessions = phase_data[(dte, phase)]
            for (hold, guard), policy in POLICIES.items():
                candidates = sorted(
                    [r for r in all_trades if r.get("policy") == policy and r.get("entry_date")],
                    key=lambda r: (int(float(r["signal_index"])), int(float(r["entry_index"])), int(float(r["episode_id"])))
                )
                expected = policy_summary[policy]
                if len(candidates) != int(expected.get("resolved") or 0) + int(expected.get("unresolved") or 0):
                    raise RuntimeError(f"candidate count differs from replay summary dte={dte} phase={phase} policy={policy} candidates={len(candidates)}")
                for cap in CAPS:
                    selected, blocked = gate_candidates(candidates, cap, source_sessions)
                    metrics = portfolio_metrics(selected, source_sessions)
                    if cap is None:
                        if metrics["resolved"] != int(expected.get("resolved") or 0) or metrics["unresolved"] != int(expected.get("unresolved") or 0):
                            raise RuntimeError(f"uncapped count mismatch dte={dte} phase={phase} policy={policy}")
                        if abs(metrics["total_resolved_pnl_usd"] - (fnum(expected.get("total_net_pnl_usd")) or 0.0)) > 0.02:
                            raise RuntimeError(f"uncapped P&L mismatch dte={dte} phase={phase} policy={policy}")
                    gate_name = "UNLIMITED" if cap is None else str(cap)
                    cell = {
                        "dte_target": dte, "dte_min": dte_min, "dte_max": dte_max,
                        "phase_sessions": phase, "hold_sessions": hold,
                        "expiry_guard_dte": "" if guard is None else guard, "policy": policy,
                        "max_concurrent_cohorts": gate_name,
                        "entry_candidates": len(candidates), "capacity_skipped": len(blocked),
                        "capacity_skip_pct": round(100 * len(blocked) / len(candidates), 2) if candidates else 0.0,
                        **{k: v for k, v in metrics.items() if k not in ("year_pnl", "year_count")},
                    }
                    cell_rows.append(cell)
                    for year in range(2018, 2026):
                        year_rows.append({
                            "dte_target": dte, "phase_sessions": phase, "hold_sessions": hold,
                            "expiry_guard_dte": "" if guard is None else guard, "policy": policy,
                            "max_concurrent_cohorts": gate_name, "exit_year": year,
                            "resolved_trade_pnl_usd": metrics["year_pnl"][year],
                            "resolved_trades": metrics["year_count"][year],
                        })
                    for r in selected:
                        selected_episode_rows.append({
                            "dte_target": dte, "phase_sessions": phase, "hold_sessions": hold,
                            "expiry_guard_dte": "" if guard is None else guard, "policy": policy,
                            "max_concurrent_cohorts": gate_name, "episode_id": r.get("episode_id"),
                            "status": r.get("status"), "signal_date": r.get("signal_date"),
                            "signal_index": r.get("signal_index"), "entry_date": r.get("entry_date"),
                            "entry_index": r.get("entry_index"), "expiry": r.get("expiry"),
                            "signal_dte": r.get("signal_dte"), "exit_signal_date": r.get("exit_signal_date"),
                            "exit_date": r.get("exit_date"), "exit_index": r.get("exit_index"),
                            "exit_delay_sessions": r.get("exit_delay_sessions"), "exit_reason": r.get("exit_reason"),
                            "net_pnl_usd": r.get("net_pnl_usd"), "long_qqq_qty": r.get("long_qqq_qty"),
                            "short_spy_qty": r.get("short_spy_qty"),
                            "spy_call_strike_delivery_obligation_usd": r.get("spy_call_strike_delivery_obligation_usd"),
                        })
    groups = defaultdict(list)
    for r in cell_rows:
        groups[(r["dte_target"], r["max_concurrent_cohorts"], r["hold_sessions"], str(r["expiry_guard_dte"]), r["policy"])].append(r)
    by_phase = {(r["dte_target"], r["phase_sessions"], r["policy"], r["max_concurrent_cohorts"]): r for r in cell_rows}
    configs = []
    for (dte, gate, hold, guard, policy), rows in sorted(groups.items(), key=lambda item: (
        item[0][0], 99 if item[0][1] == "UNLIMITED" else int(item[0][1]),
        item[0][2], 99 if item[0][3] == "" else int(item[0][3])
    )):
        annual = [float(r["annual_resolved_pnl_usd"]) for r in rows]
        base_rows = [by_phase.get((dte, r["phase_sessions"], policy, "UNLIMITED")) for r in rows]
        retained = [
            float(r["annual_resolved_pnl_usd"]) / float(b["annual_resolved_pnl_usd"]) * 100
            for r, b in zip(rows, base_rows)
            if b and float(b["annual_resolved_pnl_usd"]) > 0
        ]
        obligation_reduction = [
            (1 - float(r["peak_gross_call_delivery_notional_usd"]) / float(b["peak_gross_call_delivery_notional_usd"])) * 100
            for r, b in zip(rows, base_rows)
            if b and float(b["peak_gross_call_delivery_notional_usd"]) > 0
        ]
        max_obligation = max(float(r["peak_gross_call_delivery_notional_usd"]) for r in rows)
        worst_values = [float(r["worst_trade_usd"]) for r in rows if r["worst_trade_usd"] is not None]
        pf_values = [r["profit_factor"] for r in rows if fnum(r["profit_factor"]) is not None]
        configs.append({
            "dte_target": dte, "dte_min": DTE_BANDS[dte][0], "dte_max": DTE_BANDS[dte][1],
            "max_concurrent_cohorts": gate, "hold_sessions": hold,
            "expiry_guard_dte": guard, "policy": policy, "phase_count": len(rows),
            "median_annual_resolved_pnl_usd": round(statistics.median(annual), 2),
            "min_phase_annual_pnl_usd": round(min(annual), 2), "max_phase_annual_pnl_usd": round(max(annual), 2),
            "phases_ge_12000_usd": sum(1 for x in annual if x >= 12000),
            "median_entry_candidates": round(statistics.median(float(r["entry_candidates"]) for r in rows), 1),
            "median_entries_admitted": round(statistics.median(float(r["entries_admitted"]) for r in rows), 1),
            "median_capacity_skipped": round(statistics.median(float(r["capacity_skipped"]) for r in rows), 1),
            "median_capacity_skip_pct": round(statistics.median(float(r["capacity_skip_pct"]) for r in rows), 2),
            "median_resolved": round(statistics.median(float(r["resolved"]) for r in rows), 1),
            "median_unresolved": round(statistics.median(float(r["unresolved"]) for r in rows), 1),
            "median_win_rate_pct": round(med([r["win_rate_pct"] for r in rows]) or 0, 2),
            "median_expectancy_usd": round(med([r["expectancy_usd"] for r in rows]) or 0, 2),
            "median_worst_trade_usd": round(med([r["worst_trade_usd"] for r in rows]) or 0, 2),
            "worst_trade_across_phases_usd": round(min(worst_values), 2) if worst_values else None,
            "median_profit_factor": round(med(pf_values) or 0, 4),
            "median_peak_concurrent_cohorts": round(statistics.median(float(r["peak_concurrent_cohorts"]) for r in rows), 1),
            "max_peak_gross_call_delivery_notional_usd": round(max_obligation, 2),
            "median_pnl_retained_pct_vs_unlimited": round(statistics.median(retained), 2) if retained else None,
            "median_peak_delivery_notional_reduction_pct_vs_unlimited": round(statistics.median(obligation_reduction), 2) if obligation_reduction else None,
            "median_annual_pnl_per_100k_delivery_notional_usd": round(statistics.median(annual) /
                (max_obligation / 100000), 2) if max_obligation > 0 else None,
        })
    write_csv(ROOT / "mode_c_capacity_matrix.csv", cell_rows)
    write_csv(ROOT / "mode_c_capacity_config_summary.csv", configs)
    write_csv(ROOT / "mode_c_capacity_calendar_year_pnl.csv", year_rows)
    write_csv(ROOT / "mode_c_selected_episodes.csv", selected_episode_rows)
    make_report(configs)

def make_report(configs):
    lines = [
        "# Mode C: Capacity-gated DTE × holding × exit comparison", "",
        f"- Replay period: {START.isoformat()} through {END.isoformat()} ({YEARS:.3f} calendar years).",
        "- Strategy: QQQ LONG CALL 1 : SPY SHORT CALL 6; same expiry; both legs nearest absolute Delta 0.25; fixed 10-common-session signal cadence; five phase anchors 0, 2, 4, 6, 8.",
        "- Costs: USD 0.05 per option-share per side slippage and USD 0.65 per contract per side commission.",
        "- Mode C semantics: each holding/exit policy owns an independent book; admit a new signal only if live cohort reservations are below cap 1 or 2; skip blocked signals without re-anchoring; unresolved/expired-without-executable-exit cohorts reserve capacity through source end.",
        "- Capacity gating is a chronological admission simulation over the same source-pinned, per-cohort quote-side outcomes. Blocked cohorts contribute no P&L; because positions are separately simulated, their hypothetical paths do not affect later cohorts.",
        "- Annual P&L is resolved episode net P&L summed then divided by 7.792 calendar years; not CAGR, account return, or proof of USD 100,000 buying-power feasibility.",
        "- Peak gross call-delivery notional is the sum of SPY short-call strike × 100 × short contracts across concurrently open admitted cohorts; it is not broker margin or maximum loss.",
        "- Unresolved episodes are excluded from P&L but keep their capacity slot through source end. EOD quote-side prices are not verified fills.",
        "",
        "## Shortlist across DTE and capacity limits", "",
        "| DTE band | Max cohorts | Hold | Exit guard | Median annual P&L | Phase range | P&L retained vs unlimited | Peak delivery-notional reduction | Median skipped | Worst trade across phases | Peak call-delivery notional |",
        "|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    shortlisted = []
    for dte in (20, 30, 45, 60):
        for gate in ("1", "2", "UNLIMITED"):
            rows = [r for r in configs if r["dte_target"] == dte and r["max_concurrent_cohorts"] == gate]
            rows.sort(key=lambda r: (
                -float(r["median_annual_resolved_pnl_usd"]),
                float(r["max_peak_gross_call_delivery_notional_usd"]),
                -float(r["median_pnl_retained_pct_vs_unlimited"] or 0)
            ))
            show = rows[:2]
            shorter = [r for r in rows if r["hold_sessions"] <= 15]
            if shorter:
                eff = max(shorter, key=lambda r: float(r["median_annual_resolved_pnl_usd"]) /
                          max(float(r["max_peak_gross_call_delivery_notional_usd"]), 1))
                if eff not in show:
                    show.append(eff)
            for r in show:
                if r not in shortlisted:
                    shortlisted.append(r)
    for r in shortlisted:
        lines.append(
            f"| {r['dte_target']} ({r['dte_min']}-{r['dte_max']}) | {r['max_concurrent_cohorts']} | {r['hold_sessions']} | "
            f"{'none' if r['expiry_guard_dte']=='' else 'DTE <= '+str(r['expiry_guard_dte'])} | "
            f"{fmt(r['median_annual_resolved_pnl_usd'])} | {fmt(r['min_phase_annual_pnl_usd'])}–{fmt(r['max_phase_annual_pnl_usd'])} | "
            f"{fmt(r['median_pnl_retained_pct_vs_unlimited'],1)}% | "
            f"{fmt(r['median_peak_delivery_notional_reduction_pct_vs_unlimited'],1)}% | "
            f"{r['median_capacity_skipped']} / {r['median_entry_candidates']} ({fmt(r['median_capacity_skip_pct'],1)}%) | "
            f"{fmt(r['worst_trade_across_phases_usd'])} | {fmt(r['max_peak_gross_call_delivery_notional_usd'])} |"
        )
    lines += [
        "", "## How to interpret it", "",
        "- Cap 1 serializes the portfolio; cap 2 allows up to two open/reserved cohorts; UNLIMITED is the control.",
        "- Annual median must be read with phase range, skipped-entry rate, worst trade, unresolved counts, peak simultaneous cohorts and gross call-delivery notional.",
        "- Cap reduces admitted opportunities, so lower total P&L can coexist with similar per-trade expectancy. It is useful only if lower stacked exposure is worth the income surrendered.",
        "- A high win rate does not neutralize the 1:6 structure's short-call tail risk. Account cash, broker margin, forced liquidation, financing, tax, compounding and TAIL cost are not modeled.",
        "- Before choosing any configuration for live use, validate the underlying quote history, fills and the actual broker's assignment/margin treatment.",
        "",
        "Machine-readable outputs: mode_c_capacity_matrix.csv (720 phase cells), mode_c_capacity_config_summary.csv (144 configurations), mode_c_capacity_calendar_year_pnl.csv, and mode_c_selected_episodes.csv.", ""
    ]
    (ROOT / "MODE_C_CAPACITY_GATE_REPORT.md").write_text("\n".join(lines), encoding="utf-8")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    else:
        generate()

if __name__ == "__main__":
    main()
