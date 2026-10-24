#!/usr/bin/env python3
"""Run a pre-declared entry-time SPY far-tail hedge trigger against a frozen no-hedge baseline."""
from __future__ import annotations
import argparse, csv, hashlib, json, math, statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parent
ARMS = {"DTE45": "expiry_guarded_dte45", "DTE14": "expiry_guarded_dte14"}
PHASES = range(5)
TAILS = ("TAIL_025_DELTA", "TAIL_05_DELTA", "TAIL_10_DELTA")
QUANTITIES = (1, 3)
SHOCKS = (0.0, -0.10, -0.20, -0.30, -0.40, -0.50, -1.0)
LOOKBACK_OBSERVATIONS = 5
DRAWDOWN_THRESHOLD = 0.05
SHORT_DELTA_THRESHOLD = 0.30
MULTIPLIER = 100


def fnum(value: Any) -> float | None:
    try:
        x = float(value)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def num(row: dict[str, Any], key: str) -> float | None:
    return fnum(row.get(key))


def truth(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"Input CSV is empty: {path}")
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"Refusing to write empty output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                fields.append(key)
                seen.add(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def median(values: Iterable[float | int | None]) -> float | None:
    clean = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    return statistics.median(clean) if clean else None


def bounds(values: Iterable[float | int | None]) -> tuple[float | None, float | None]:
    clean = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    return (min(clean), max(clean)) if clean else (None, None)


def money(value: float | int | None) -> str:
    if value is None:
        return "—"
    x = float(value)
    return ("−$" if x < 0 else "$") + f"{abs(x):,.2f}"


def percent(value: float | int | None) -> str:
    return "—" if value is None else f"{float(value):.2f}%"


def span(lo: float | int | None, hi: float | int | None) -> str:
    return "—" if lo is None or hi is None else f"{lo:g}–{hi:g}"


def read_baseline_cohorts(base_root: Path) -> tuple[dict[tuple[str, int, str], dict[str, Any]], dict[str, str]]:
    """Read immutable phase ledgers and collapse policy copies to unique entry cohorts."""
    cohorts: dict[tuple[str, int, str], dict[str, Any]] = {}
    hashes: dict[str, str] = {}
    required = ("entry_date", "episode_id", "spy_spot_entry", "spy_strike", "spy_entry_bid",
                "spy_abs_delta", "short_spy_qty", "signal_date")
    for arm, dirname in ARMS.items():
        for phase in PHASES:
            path = base_root / dirname / "fixed_phase_sensitivity" / f"phase_{phase}" / "trade_episodes.csv"
            if not path.is_file():
                raise FileNotFoundError(f"Required baseline ledger missing: {path}")
            hashes[f"{arm}/phase_{phase}/trade_episodes.csv"] = sha256_file(path)
            for raw in read_csv(path):
                missing = [field for field in required if raw.get(field) in (None, "")]
                if missing:
                    raise ValueError(f"Baseline row missing {missing} in {path}")
                key = (arm, phase, str(raw["episode_id"]))
                row = dict(raw)
                if key in cohorts:
                    old = cohorts[key]
                    for field in ("entry_date", "spy_spot_entry", "spy_strike", "spy_entry_bid", "spy_abs_delta"):
                        try:
                            same = math.isclose(float(old[field]), float(row[field]), rel_tol=1e-8, abs_tol=1e-8)
                        except (TypeError, ValueError):
                            same = str(old.get(field)) == str(row.get(field))
                        if not same:
                            raise ValueError(f"Policy copies disagree for cohort {key} field {field}")
                else:
                    row["arm"], row["phase"] = arm, phase
                    cohorts[key] = row
    return cohorts, hashes


def compute_trigger_flags(cohorts: dict[tuple[str, int, str], dict[str, Any]],
                          lookback: int = LOOKBACK_OBSERVATIONS,
                          drawdown_threshold: float = DRAWDOWN_THRESHOLD,
                          delta_threshold: float = SHORT_DELTA_THRESHOLD) -> dict[tuple[str, int, str], dict[str, Any]]:
    """Use current entry spot and only earlier observations from the same arm/phase."""
    if lookback < 2 or not 0 < drawdown_threshold < 1 or not 0 < delta_threshold < 1:
        raise ValueError("Invalid predeclared trigger parameters")
    groups: dict[tuple[str, int], list[tuple[tuple[str, int, str], dict[str, Any]]]] = defaultdict(list)
    for key, row in cohorts.items():
        groups[(key[0], key[1])].append((key, row))
    flags: dict[tuple[str, int, str], dict[str, Any]] = {}
    for entries in groups.values():
        entries.sort(key=lambda item: (
            str(item[1].get("entry_date", "")),
            int(fnum(item[1].get("signal_index")) or -1),
            item[0][2],
        ))
        for i, (key, row) in enumerate(entries):
            spot = fnum(row.get("spy_spot_entry"))
            window = entries[max(0, i - lookback + 1):i + 1]
            spots = [fnum(item[1].get("spy_spot_entry")) for item in window]
            ready = len(window) == lookback and all(x is not None and x > 0 for x in spots) and spot is not None and spot > 0
            peak = max(float(x) for x in spots) if ready else None
            drawdown = 1.0 - spot / peak if ready and peak else None
            delta = fnum(row.get("spy_abs_delta"))
            delta = abs(delta) if delta is not None else None
            dd_trigger = drawdown is not None and drawdown >= drawdown_threshold
            delta_trigger = delta is not None and delta >= delta_threshold
            reasons = []
            if dd_trigger:
                reasons.append("ENTRY_SPOT_DRAWDOWN_FROM_5_OBSERVATION_HIGH_GE_5PCT")
            if delta_trigger:
                reasons.append("SIGNAL_SHORT_PUT_ABS_DELTA_GE_0.30")
            flags[key] = {
                "arm": key[0], "phase": key[1], "episode_id": key[2],
                "signal_date": row.get("signal_date"), "entry_date": row.get("entry_date"),
                "signal_index": row.get("signal_index"), "spy_spot_entry": spot,
                "spy_abs_delta_at_signal": delta, "lookback_observations": len(window),
                "drawdown_history_ready": ready, "lookback_spy_peak": peak,
                "drawdown_from_5_observation_peak_pct": round(drawdown * 100, 4) if drawdown is not None else None,
                "drawdown_trigger": dd_trigger, "short_delta_trigger": delta_trigger,
                "risk_trigger": bool(dd_trigger or delta_trigger),
                "trigger_reasons": "|".join(reasons) if reasons else "NO_TRIGGER",
                "entry_risk_trigger_rule_version": "SPY_DD5OBS_GE5PCT_OR_SIGNAL_SHORT_ABS_DELTA_GE0.30_V1",
            }
    return flags


def conditional_result(trigger: bool, entry_executable: bool, paired_realized: bool,
                       base_pnl: float | None, tail_pnl: float | None) -> tuple[float | None, str]:
    """Do not invent a realized outcome when a purchased hedge has no valid exit quote."""
    if base_pnl is None:
        return None, "BASE_UNRESOLVED_NOT_IN_REALIZED_PNL"
    if not trigger:
        return base_pnl, "NO_HEDGE_NOT_TRIGGERED"
    if not entry_executable:
        return base_pnl, "TRIGGERED_BUT_TAIL_ENTRY_NOT_EXECUTABLE"
    if paired_realized and tail_pnl is not None:
        return base_pnl + tail_pnl, "TRIGGERED_HEDGE_PAIRED_REALIZED"
    return None, "TRIGGERED_HEDGE_EXIT_NOT_REALIZED_OR_SIZE_GATED"


def build_conditional_trade_rows(trade_rows: list[dict[str, str]],
                                 flags: dict[tuple[str, int, str], dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for raw in trade_rows:
        key = (str(raw["arm"]), int(float(raw["phase"])), str(raw["episode_id"]))
        trigger = flags.get(key)
        if trigger is None:
            raise ValueError(f"No trigger flag for trade row {key}")
        base_pnl, tail_pnl = fnum(raw.get("base_net_pnl_usd")), fnum(raw.get("tail_net_pnl_usd"))
        entry_ok = truth(raw.get("tail_entry_executable"))
        paired = truth(raw.get("paired_realized_comparison")) and tail_pnl is not None
        conditional_pnl, action = conditional_result(bool(trigger["risk_trigger"]), entry_ok, paired, base_pnl, tail_pnl)
        item = dict(raw)
        item.update({
            "entry_risk_trigger_rule_version": trigger["entry_risk_trigger_rule_version"],
            "risk_trigger": trigger["risk_trigger"], "trigger_reasons": trigger["trigger_reasons"],
            "lookback_spy_peak": trigger["lookback_spy_peak"],
            "drawdown_from_5_observation_peak_pct": trigger["drawdown_from_5_observation_peak_pct"],
            "spy_abs_delta_at_signal": trigger["spy_abs_delta_at_signal"],
            "drawdown_trigger": trigger["drawdown_trigger"], "short_delta_trigger": trigger["short_delta_trigger"],
            "conditional_action": action,
            "conditional_strategy_net_pnl_usd": round(conditional_pnl, 2) if conditional_pnl is not None else None,
            "conditional_outcome_known": conditional_pnl is not None,
            "conditional_outcome_definition": "Base PnL if hedge is not bought; base plus paired realized tail PnL if purchased; otherwise missing outcome stays missing.",
        })
        result.append(item)
    return result


def outcome_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    resolved = [r for r in rows if fnum(r.get("base_net_pnl_usd")) is not None]
    known = [r for r in resolved if fnum(r.get("conditional_strategy_net_pnl_usd")) is not None]
    triggered = [r for r in resolved if truth(r.get("risk_trigger"))]
    triggered_entry = [r for r in triggered if truth(r.get("tail_entry_executable"))]
    triggered_paired = [r for r in triggered_entry if truth(r.get("paired_realized_comparison")) and fnum(r.get("tail_net_pnl_usd")) is not None]
    base_all = [float(r["base_net_pnl_usd"]) for r in resolved]
    base_match = [float(r["base_net_pnl_usd"]) for r in known]
    conditional = [float(r["conditional_strategy_net_pnl_usd"]) for r in known]
    increments = [c - b for b, c in zip(base_match, conditional)]
    losing = [(b, c) for b, c in zip(base_match, conditional) if b < -0.005]
    debit_rows = [r for r in rows if truth(r.get("risk_trigger")) and truth(r.get("tail_entry_executable")) and fnum(r.get("tail_entry_ask")) is not None]
    unit_cost = 0.05 * MULTIPLIER + 0.65
    debits = [int(float(r.get("tail_quantity", 0))) * (MULTIPLIER * float(r["tail_entry_ask"]) + unit_cost) for r in debit_rows]
    tail_net = [float(r["tail_net_pnl_usd"]) for r in triggered_paired]
    base_worst = min(base_match) if base_match else None
    conditional_worst = min(conditional) if conditional else None
    return {
        "opened_base_trade_rows": len(rows), "base_resolved_n_all": len(resolved),
        "base_unresolved_n": len(rows) - len(resolved),
        "triggered_base_resolved_n": len(triggered),
        "trigger_rate_pct_of_base_resolved": round(100 * len(triggered) / len(resolved), 2) if resolved else None,
        "trigger_entry_executable_n": len(triggered_entry),
        "trigger_entry_coverage_pct_of_triggered_resolved": round(100 * len(triggered_entry) / len(triggered), 2) if triggered else None,
        "trigger_exit_paired_n": len(triggered_paired),
        "trigger_exit_coverage_pct_of_triggered_entry_eligible": round(100 * len(triggered_paired) / len(triggered_entry), 2) if triggered_entry else None,
        "conditional_outcome_known_n": len(known),
        "conditional_outcome_coverage_pct_of_base_resolved": round(100 * len(known) / len(resolved), 2) if resolved else None,
        "no_hedge_mean_all_resolved_usd": round(statistics.mean(base_all), 2) if base_all else None,
        "no_hedge_mean_matched_usd": round(statistics.mean(base_match), 2) if base_match else None,
        "conditional_mean_matched_usd": round(statistics.mean(conditional), 2) if conditional else None,
        "conditional_mean_increment_vs_no_hedge_usd": round(statistics.mean(increments), 2) if increments else None,
        "no_hedge_win_rate_matched_pct": round(100 * sum(x > 0.005 for x in base_match) / len(base_match), 2) if base_match else None,
        "conditional_win_rate_matched_pct": round(100 * sum(x > 0.005 for x in conditional) / len(conditional), 2) if conditional else None,
        "no_hedge_worst_matched_usd": round(base_worst, 2) if base_worst is not None else None,
        "conditional_worst_matched_usd": round(conditional_worst, 2) if conditional_worst is not None else None,
        "worst_trade_improvement_usd": round(conditional_worst - base_worst, 2) if conditional_worst is not None and base_worst is not None else None,
        "no_hedge_worst_all_resolved_usd": round(min(base_all), 2) if base_all else None,
        "losing_base_trades_improved_n": sum(c > b + 0.005 for b, c in losing),
        "losing_base_trades_turned_positive_n": sum(b < -0.005 and c > 0.005 for b, c in zip(base_match, conditional)),
        "conditional_hedge_purchase_candidates_n": len(debit_rows),
        "modeled_entry_debit_total_usd": round(sum(debits), 2),
        "modeled_entry_debit_mean_per_purchase_usd": round(statistics.mean(debits), 2) if debits else None,
        "mean_realized_tail_net_pnl_when_triggered_and_paired_usd": round(statistics.mean(tail_net), 2) if tail_net else None,
        "realized_tail_net_pnl_triggered_sum_usd": round(sum(tail_net), 2) if tail_net else 0.0,
    }


def aggregate(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row[k] for k in keys)].append(row)
    output = []
    for key, items in sorted(grouped.items(), key=lambda item: tuple(str(v) for v in item[0])):
        result = dict(zip(keys, key))
        result.update(outcome_summary(items))
        output.append(result)
    return output


def build_annual_rows(trade_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in trade_rows:
        if fnum(row.get("base_net_pnl_usd")) is None or not row.get("exit_date"):
            continue
        key = (row["arm"], int(float(row["phase"])), row["policy"], row["tail_label"],
               int(float(row["tail_quantity"])), str(row["exit_date"])[:4])
        groups[key].append(row)
    output = []
    for key, items in sorted(groups.items(), key=lambda item: tuple(str(v) for v in item[0])):
        arm, phase, policy, tail, qty, year = key
        stats = outcome_summary(items)
        output.append({
            "arm": arm, "phase": phase, "policy": policy, "tail_label": tail, "tail_quantity": qty, "exit_year": year,
            "base_resolved_n_all_year": stats["base_resolved_n_all"],
            "conditional_outcome_known_n": stats["conditional_outcome_known_n"],
            "conditional_outcome_coverage_pct": stats["conditional_outcome_coverage_pct_of_base_resolved"],
            "triggered_base_resolved_n": stats["triggered_base_resolved_n"],
            "trigger_rate_pct": stats["trigger_rate_pct_of_base_resolved"],
            "no_hedge_mean_all_resolved_usd": stats["no_hedge_mean_all_resolved_usd"],
            "no_hedge_mean_matched_usd": stats["no_hedge_mean_matched_usd"],
            "conditional_mean_matched_usd": stats["conditional_mean_matched_usd"],
            "conditional_mean_increment_usd": stats["conditional_mean_increment_vs_no_hedge_usd"],
            "no_hedge_worst_matched_usd": stats["no_hedge_worst_matched_usd"],
            "conditional_worst_matched_usd": stats["conditional_worst_matched_usd"],
            "worst_trade_improvement_usd": stats["worst_trade_improvement_usd"],
            "modeled_entry_debit_total_usd": stats["modeled_entry_debit_total_usd"],
            "trigger_entry_coverage_pct": stats["trigger_entry_coverage_pct_of_triggered_resolved"],
            "trigger_exit_coverage_pct": stats["trigger_exit_coverage_pct_of_triggered_entry_eligible"],
        })
    return output


def robust_annual(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keys = ("arm", "exit_year", "policy", "tail_label", "tail_quantity")
    fields = ("conditional_mean_increment_usd", "no_hedge_mean_matched_usd", "conditional_mean_matched_usd",
              "worst_trade_improvement_usd", "conditional_outcome_coverage_pct", "trigger_rate_pct", "modeled_entry_debit_total_usd")
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row[k] for k in keys)].append(row)
    output = []
    for key, items in sorted(grouped.items(), key=lambda item: tuple(str(v) for v in item[0])):
        out = dict(zip(keys, key))
        out["phase_count"] = len(items)
        counts = [int(r["conditional_outcome_known_n"]) for r in items]
        out["paired_n_min"], out["paired_n_max"] = min(counts), max(counts)
        for field in fields:
            lo, hi = bounds(fnum(r.get(field)) for r in items)
            out[field + "_phase_min"], out[field + "_phase_median"], out[field + "_phase_max"] = lo, median(fnum(r.get(field)) for r in items), hi
        output.append(out)
    return output


def read_entry_selection(path: Path) -> dict[tuple[str, int, str, str, int], dict[str, str]]:
    selection = {}
    for row in read_csv(path):
        key = (str(row["arm"]), int(float(row["phase"])), str(row["episode_id"]),
               str(row["tail_label"]), int(float(row["tail_quantity"])))
        selection[key] = row
    return selection


def sleeve_pnl(spot: float, short_strike: float, short_qty: int, short_entry_bid: float,
               shock: float, slippage: float, commission: float) -> float:
    unit = slippage * MULTIPLIER + commission
    stressed_spot = max(0.0, spot * (1.0 + shock))
    intrinsic = max(0.0, short_strike - stressed_spot)
    return short_qty * MULTIPLIER * (short_entry_bid - intrinsic) - short_qty * unit


def tail_stress_pnl(tail_strike: float, tail_qty: int, tail_entry_ask: float,
                    spot: float, shock: float, slippage: float, commission: float) -> float:
    unit = slippage * MULTIPLIER + commission
    stressed_spot = max(0.0, spot * (1.0 + shock))
    intrinsic = max(0.0, tail_strike - stressed_spot)
    return tail_qty * MULTIPLIER * (intrinsic - tail_entry_ask) - tail_qty * unit


def build_stress_rows(cohorts: dict[tuple[str, int, str], dict[str, Any]],
                      flags: dict[tuple[str, int, str], dict[str, Any]],
                      selections: dict[tuple[str, int, str, str, int], dict[str, str]],
                      slippage: float, commission: float) -> list[dict[str, Any]]:
    groups: dict[tuple[str, int, str, int, float], list[dict[str, float]]] = defaultdict(list)
    for key, cohort in cohorts.items():
        trigger = bool(flags[key]["risk_trigger"])
        spot, strike, credit = (fnum(cohort.get("spy_spot_entry")), fnum(cohort.get("spy_strike")), fnum(cohort.get("spy_entry_bid")))
        short_qty = int(float(cohort.get("short_spy_qty", "0")))
        if spot is None or strike is None or credit is None or short_qty < 1:
            raise ValueError(f"Missing stress input for cohort {key}")
        for tail in TAILS:
            for qty in QUANTITIES:
                selected = selections.get((key[0], key[1], key[2], tail, qty), {})
                executable = truth(selected.get("tail_entry_executable_size_gate"))
                tail_strike, tail_ask = fnum(selected.get("tail_strike")), fnum(selected.get("tail_entry_ask"))
                for shock in SHOCKS:
                    base = sleeve_pnl(spot, strike, short_qty, credit, shock, slippage, commission)
                    unconditional, conditional = base, base
                    if executable and tail_strike is not None and tail_ask is not None:
                        pnl = tail_stress_pnl(tail_strike, qty, tail_ask, spot, shock, slippage, commission)
                        unconditional += pnl
                        if trigger:
                            conditional += pnl
                    groups[(key[0], key[1], tail, qty, shock)].append({
                        "base": base, "unconditional": unconditional, "conditional": conditional,
                        "conditional_improved": 1.0 if conditional > base + 0.005 else 0.0,
                        "unconditional_improved": 1.0 if unconditional > base + 0.005 else 0.0,
                        "trigger": 1.0 if trigger else 0.0,
                        "conditional_bought": 1.0 if trigger and executable else 0.0,
                        "unconditional_bought": 1.0 if executable else 0.0,
                        "entry_eligible": 1.0 if executable else 0.0,
                    })
    output = []
    for key, samples in sorted(groups.items()):
        arm, phase, tail, qty, shock = key
        output.append({
            "arm": arm, "phase": phase, "tail_label": tail, "tail_quantity": qty,
            "spy_shock_pct": round(shock * 100, 2), "cohorts_n": len(samples),
            "risk_triggered_cohorts_n": int(sum(s["trigger"] for s in samples)),
            "eligible_tail_entry_cohorts_n": int(sum(s["entry_eligible"] for s in samples)),
            "conditional_hedge_entry_n": int(sum(s["conditional_bought"] for s in samples)),
            "unconditional_hedge_entry_n": int(sum(s["unconditional_bought"] for s in samples)),
            "mean_no_hedge_spy_sleeve_usd": round(statistics.mean(s["base"] for s in samples), 2),
            "mean_unconditional_spy_sleeve_usd": round(statistics.mean(s["unconditional"] for s in samples), 2),
            "mean_conditional_spy_sleeve_usd": round(statistics.mean(s["conditional"] for s in samples), 2),
            "mean_unconditional_increment_usd": round(statistics.mean(s["unconditional"] - s["base"] for s in samples), 2),
            "mean_conditional_increment_usd": round(statistics.mean(s["conditional"] - s["base"] for s in samples), 2),
            "worst_no_hedge_spy_sleeve_usd": round(min(s["base"] for s in samples), 2),
            "worst_unconditional_spy_sleeve_usd": round(min(s["unconditional"] for s in samples), 2),
            "worst_conditional_spy_sleeve_usd": round(min(s["conditional"] for s in samples), 2),
            "conditional_improvement_pct": round(100 * statistics.mean(s["conditional_improved"] for s in samples), 2),
            "unconditional_improvement_pct": round(100 * statistics.mean(s["unconditional_improved"] for s in samples), 2),
        })
    return output


def build_report(results: Path, trigger_rows: list[dict[str, Any]], summaries: list[dict[str, Any]],
                 annual_robust: list[dict[str, Any]], stress_rows: list[dict[str, Any]],
                 manifest: dict[str, Any]) -> str:
    tail_name = {"TAIL_025_DELTA": "2.5-delta (~−0.025)", "TAIL_05_DELTA": "5-delta (~−0.05)", "TAIL_10_DELTA": "10-delta (~−0.10)"}
    policy_name = {"HOLD_10_OR_DTE_LE_7": "Hold-10 / DTE≤7", "HOLD_20_OR_DTE_LE_7": "Hold-20 / DTE≤7"}
    phase_stats = []
    by_phase: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in trigger_rows:
        by_phase[(row["arm"], int(row["phase"]))].append(row)
    for (arm, phase), rows in sorted(by_phase.items()):
        phase_stats.append({
            "arm": arm, "phase": phase, "n": len(rows),
            "trigger_pct": 100 * sum(bool(r["risk_trigger"]) for r in rows) / len(rows),
            "dd_pct": 100 * sum(bool(r["drawdown_trigger"]) for r in rows) / len(rows),
            "delta_pct": 100 * sum(bool(r["short_delta_trigger"]) for r in rows) / len(rows),
            "both_pct": 100 * sum(bool(r["drawdown_trigger"]) and bool(r["short_delta_trigger"]) for r in rows) / len(rows),
        })
    unconditional_rows = read_csv(results.parent / "spy_far_tail_hedge_v1" / "summary.csv")
    unconditional: dict[tuple[str, int], list[dict[str, str]]] = defaultdict(list)
    for row in unconditional_rows:
        if row["arm"] == "DTE45" and row["policy"] == "HOLD_20_OR_DTE_LE_7":
            unconditional[(row["tail_label"], int(float(row["tail_quantity"])))].append(row)
    uncond_metrics = {
        key: median(num(r, "paired_mean_incremental_hedge_usd") for r in rows)
        for key, rows in unconditional.items()
    }
    lines = [
        "# SPY Far-Tail Conditional Risk-Trigger Hedge — Research V1", "",
        "> Source-pinned historical research. No broker orders were placed.", "",
        "## 1. Executive decision", "",
        "**Keep no hedge as the control. Do not enable unconditional tail buying based on the current evidence.** This first trigger rule tests whether premiums can be concentrated in higher-risk entry conditions. It is a pre-declared research candidate, not an optimized or validated trading rule.",
        "",
        "At each base entry, the rule triggers if either (A) SPY is at least 5% below the high among the current and four prior entry observations in the same phase, or (B) the selected base short SPY PUT absolute Delta at signal time is at least 0.30. Five observations proxy about 20 sessions under the fixed five-session cadence. Thresholds are frozen before measuring this experiment's outcomes; they must not be tuned on a claimed holdout.",
        "", 
        "**Critical result:** for DTE45 / Hold-20, median worst-realized-trade improvement is $0.00 for all tested Delta targets at both 1x and 3x. The entry trigger reduces recurring average-P&L drag by buying protection on only about 13.5% of entries, but it did not catch the worst realized trade in the paired samples. Do not adopt this entry-only trigger on the claim that it protects the worst trade.",
        "",
        "## 2. Frozen rule and fair accounting", "",
        "- Baseline remains QQQ LONG PUT 1 : SPY SHORT PUT 3; original entries, quantities, exit policies and cadence are unchanged.",
        "- The hedge is considered at base entry only. No mid-trade additions, rebalancing, stop, roll or future-price trigger is tested.",
        "- Drawdown rule uses current entry spot and earlier observations only; five valid positive spots are required. Missing history cannot trigger the drawdown component. The Delta rule can trigger independently.",
        "- Signal-time Delta is the base selected short put's recorded absolute Delta, not a recalculation at the later entry timestamp.",
        "- Hedge targets: 2.5-delta (~−0.025), 5-delta (~−0.05), 10-delta (~−0.10) reference; quantities 1 and 3. The 2.5/5 targets share the same eligible absolute-Delta band.",
        "- Costs and quote sides match the frozen overlay replay: ask-side buys, bid-side realized exits, $0.05 option-share slippage per side and $0.65 commission per contract per side. Displayed-size checks are not proof of fills.",
        "- No trigger means no tail purchase and conditional P&L equals base P&L. Trigger but entry quote/size gate fails also means no modeled purchase. If the hedge was eligible to enter but lacks a valid size-gated exit quote, the realized conditional result remains missing—not zero, not a mark-to-market profit, and not the base P&L.",
        "- The primary fair comparison is no hedge vs conditional strategy on exactly the same rows where conditional realized outcome is known. All-resolved no-hedge results are provided separately, together with outcome coverage.",
        "",
        "## 3. Trigger frequency by phase", "",
        "| Arm | Phase | Cohorts | Any trigger | Drawdown trigger | Delta trigger | Both |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in phase_stats:
        lines.append(f"| {r['arm']} | {r['phase']} | {r['n']} | {r['trigger_pct']:.2f}% | {r['dd_pct']:.2f}% | {r['delta_pct']:.2f}% | {r['both_pct']:.2f}% |")
    for arm in ("DTE14", "DTE45"):
        values = [r["trigger_pct"] for r in phase_stats if r["arm"] == arm]
        if values:
            lines.append(f"| {arm} phase range | — | — | {min(values):.2f}–{max(values):.2f}% | — | — | — |")
    lines += [
        "",
        "Trigger rate is the fraction of opened base entry cohorts, not the probability of a future loss. Five phases overlap, so phase rates are a robustness range rather than independent evidence.",
        "",
        "## 4. Conditional vs no hedge and unconditional references", "",
        "Median of five phase values is shown for each configuration; the phases overlap. The conditional increment compares the baseline and conditional result on the exact same known-outcome rows. The unconditional figure comes from the earlier overlay's paired sample and has different coverage, so compare it only with the coverage figures alongside it.",
        "",
        "| Arm | Exit | Tail | Qty | Trigger rate median (range) | Entry coverage median (range) | Exit-pair coverage median (range) | Outcome coverage median (range) | No-hedge matched mean median (range) | Conditional matched mean median (range) | Conditional Δ mean median (range) | Unconditional Δ mean median | Worst-trade improvement median (range) | Modeled entry debit median (range) |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    summary_groups = defaultdict(list)
    for summary_row in summaries:
        summary_groups[(summary_row["arm"], summary_row["policy"], summary_row["tail_label"], int(summary_row["tail_quantity"]))].append(summary_row)

    def metric_text(items, field, kind):
        values = [num(item, field) for item in items]
        lo, hi = bounds(values)
        center = median(values)
        fmt = percent if kind == "pct" else money
        return f"{fmt(center)} ({fmt(lo)} to {fmt(hi)})"

    for key, phase_rows in sorted(summary_groups.items(), key=lambda item: item[0]):
        arm, policy, target, quantity = key
        uncond_inc = uncond_metrics.get((target, quantity)) if arm == "DTE45" and policy == "HOLD_20_OR_DTE_LE_7" else None
        lines.append(
            f"| {arm} | {policy_name[policy]} | {tail_name[target]} | {quantity} "
            f"| {metric_text(phase_rows, 'trigger_rate_pct_of_base_resolved', 'pct')} "
            f"| {metric_text(phase_rows, 'trigger_entry_coverage_pct_of_triggered_resolved', 'pct')} "
            f"| {metric_text(phase_rows, 'trigger_exit_coverage_pct_of_triggered_entry_eligible', 'pct')} "
            f"| {metric_text(phase_rows, 'conditional_outcome_coverage_pct_of_base_resolved', 'pct')} "
            f"| {metric_text(phase_rows, 'no_hedge_mean_matched_usd', 'usd')} "
            f"| {metric_text(phase_rows, 'conditional_mean_matched_usd', 'usd')} "
            f"| {metric_text(phase_rows, 'conditional_mean_increment_vs_no_hedge_usd', 'usd')} "
            f"| {money(uncond_inc)} "
            f"| {metric_text(phase_rows, 'worst_trade_improvement_usd', 'usd')} "
            f"| {metric_text(phase_rows, 'modeled_entry_debit_total_usd', 'usd')} |"
        )
    lines += [
        "",
        "Modeled opening debit is the tail ask premium plus opening-side modeled friction for triggered entries that pass the displayed ask-size gate. It assumes a possible ask-side fill and is not a verified cash ledger. Outcome coverage below 100% means the conditional realized average is based on a subset; interpret means only with the coverage columns.",
        "",
        "## 5. Annual results — DTE45 / Hold-20, 2.5-delta and 5-delta", "",
        "Per-trade average P&L by realized exit year; each cell is the median across phases. Δ is conditional minus no-hedge mean on matched known outcomes.",
        "",
        "| Exit year | Tail | Qty | Outcome N range | Outcome coverage median | Trigger rate median | No-hedge mean matched | Conditional mean matched | Δ mean | Worst-trade improvement | Opening debit median across phases |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    annual_primary = [r for r in annual_robust if r["arm"] == "DTE45" and r["policy"] == "HOLD_20_OR_DTE_LE_7" and r["tail_label"] in ("TAIL_025_DELTA", "TAIL_05_DELTA")]
    for row in sorted(annual_primary, key=lambda r: (str(r["exit_year"]), r["tail_label"], int(r["tail_quantity"]))):
        lines.append(
            f"| {row['exit_year']} | {tail_name[row['tail_label']]} | {row['tail_quantity']} | {row['paired_n_min']}–{row['paired_n_max']} "
            f"| {percent(row.get('conditional_outcome_coverage_pct_phase_median'))} | {percent(row.get('trigger_rate_pct_phase_median'))} "
            f"| {money(row.get('no_hedge_mean_matched_usd_phase_median'))} | {money(row.get('conditional_mean_matched_usd_phase_median'))} "
            f"| {money(row.get('conditional_mean_increment_usd_phase_median'))} | {money(row.get('worst_trade_improvement_usd_phase_median'))} "
            f"| {money(row.get('modeled_entry_debit_total_usd_phase_median'))} |"
        )
    lines += [
        "",
        "These figures are not total yearly dollars, CAGR, NAV change or withdrawal capacity. Rows group trade episodes by realized exit year. The trigger may leave catastrophic losses unhedged when neither condition is active.",
        "",
        "## 6. One vs three contracts: expiry stress grid", "",
        "Intrinsic payoff stress on the SPY short-put sleeve only. The conditional tail is added only when the rule triggers and the entry quote/size gate passes. This is not a historical path replay or probability estimate; it excludes the QQQ long PUT, pre-expiry time value, early exercise/assignment, margin, financing and forced liquidation.",
        "",
        "| SPY expiry shock | Tail | Qty | Mean no hedge | Mean unconditional hedge | Mean conditional hedge | Conditional Δ vs no hedge | Worst conditional sleeve | Cohorts improved | Conditional entries median |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for shock in SHOCKS:
        for tail in TAILS:
            for qty in QUANTITIES:
                rr = [r for r in stress_rows if r["arm"] == "DTE45" and float(r["spy_shock_pct"]) == shock * 100 and r["tail_label"] == tail and int(r["tail_quantity"]) == qty]
                if not rr:
                    continue
                lines.append(
                    f"| {shock*100:.0f}% | {tail_name[tail]} | {qty} "
                    f"| {money(median(num(r, 'mean_no_hedge_spy_sleeve_usd') for r in rr))} "
                    f"| {money(median(num(r, 'mean_unconditional_spy_sleeve_usd') for r in rr))} "
                    f"| {money(median(num(r, 'mean_conditional_spy_sleeve_usd') for r in rr))} "
                    f"| {money(median(num(r, 'mean_conditional_increment_usd') for r in rr))} "
                    f"| {money(median(num(r, 'worst_conditional_spy_sleeve_usd') for r in rr))} "
                    f"| {percent(median(num(r, 'conditional_improvement_pct') for r in rr))} "
                    f"| {int(median(num(r, 'conditional_hedge_entry_n') for r in rr) or 0)} |"
                )
    lines += [
        "",
        "Three tail PUTs can offset much more of a very severe expiry loss on the three-short-PUT SPY sleeve, but the rule can leave the book exposed when the pre-entry signal is inactive. No sleeve stress result is a portfolio MaxDD guarantee.",
        "",
        "## 7. Decision and next gate", "",
        "1. Keep no hedge as the control. This run is a test of a frozen candidate trigger—not evidence that the trigger is optimal.",
        "2. Compare 2.5-delta/1x as the low-carry conditional arm with 5-delta/1x as the higher-coverage arm. Treat 3x as higher-cost disaster protection, not a return enhancer.",
        "3. The trigger only has value if it reduces modeled insurance spend while improving worst matched losses or predeclared stress outcomes without leaving unacceptable untriggered losses. Do not judge by total debit alone.",
        "4. Any trigger selection should be frozen and evaluated on a later, untouched chronological holdout. Do not tune thresholds using the same years on which it is reported successful.",
        "5. Before deployment, require full QQQ+SPY path, shared NAV, margin/forced liquidation, actual quote/fill evidence, and assignment/early-exercise accounting. None are part of this overlay.",
        "",
        "## 8. Reproducible artifacts and caveats", "",
        "- trigger_flags.csv — entry-time inputs, rolling high, drawdown/Delta flags and rule reasons.",
        "- conditional_trade_level.csv — every base row with action, missing-exit handling, baseline and conditional outcome.",
        "- conditional_summary.csv — each phase/configuration with trigger and outcome coverage, mean P&L, worst trade and modeled entry debit.",
        "- conditional_annual_by_phase.csv and conditional_annual_robustness.csv — annual behavior and phase ranges.",
        "- conditional_stress_grid.csv — no-hedge, unconditional and conditional SPY-sleeve shock scenarios.",
        "- conditional_manifest.json — source/input hashes, rule thresholds, output counts and caveats.",
        "- Original full decision report: [SPY_FAR_TAIL_DECISION_REPORT.md](../spy_far_tail_hedge_v1/SPY_FAR_TAIL_DECISION_REPORT.md).",
        "- The five fixed phases overlap and are not independent samples. Hash pinning proves byte identity against the public Git mirror, not exchange provenance. EOD quotes and displayed sizes are not verified fills.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-results-root", type=Path, default=ROOT / "results")
    parser.add_argument("--overlay-results", type=Path, default=ROOT / "results" / "spy_far_tail_hedge_v1")
    parser.add_argument("--out", type=Path, default=ROOT / "results" / "spy_far_tail_conditional_v1")
    args = parser.parse_args()
    cohorts, baseline_hashes = read_baseline_cohorts(args.base_results_root)
    flags = compute_trigger_flags(cohorts)
    trade_path = args.overlay_results / "trade_level.csv"
    selection_path = args.overlay_results / "entry_selection.csv"
    replay_manifest_path = args.overlay_results / "manifest.json"
    replay_manifest = json.loads(replay_manifest_path.read_text(encoding="utf-8"))
    if replay_manifest.get("status") != "COMPLETED":
        raise ValueError("Source tail-overlay replay is not complete")
    trade_rows = read_csv(trade_path)
    if len(trade_rows) != int(replay_manifest["trade_level_rows"]):
        raise ValueError("Source trade-level row count differs from manifest")
    selections = read_entry_selection(selection_path)
    conditional_rows = build_conditional_trade_rows(trade_rows, flags)
    summary_rows = aggregate(conditional_rows, ("arm", "phase", "policy", "tail_label", "tail_quantity"))
    annual_rows = build_annual_rows(conditional_rows)
    annual_robustness = robust_annual(annual_rows)
    slippage = float(replay_manifest["costs"]["slippage_per_option_share_per_side_usd"])
    commission = float(replay_manifest["costs"]["commission_per_contract_per_side_usd"])
    stress_rows = build_stress_rows(cohorts, flags, selections, slippage, commission)
    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(args.out / "trigger_flags.csv", list(flags.values()))
    write_csv(args.out / "conditional_trade_level.csv", conditional_rows)
    write_csv(args.out / "conditional_summary.csv", summary_rows)
    write_csv(args.out / "conditional_annual_by_phase.csv", annual_rows)
    write_csv(args.out / "conditional_annual_robustness.csv", annual_robustness)
    write_csv(args.out / "conditional_stress_grid.csv", stress_rows)
    manifest = {
        "schema": "spy-far-tail-conditional-risk-trigger.v1",
        "status": "COMPLETED" if flags and summary_rows and annual_rows and stress_rows else "FAILED_EMPTY_OUTPUT",
        "baseline_anchor_commit": replay_manifest.get("base_anchor_commit"),
        "tail_overlay_replay_source_commit": replay_manifest.get("current_git_sha"),
        "option_chain_source": replay_manifest.get("source_repository"),
        "option_chain_source_commit": replay_manifest.get("source_tree_commit"),
        "chain_last_date": replay_manifest.get("stream_stats", {}).get("last_chain_date"),
        "cohort_count": len(cohorts), "trigger_flag_rows": len(flags),
        "input_trade_level_rows": len(trade_rows), "conditional_trade_level_rows": len(conditional_rows),
        "summary_rows": len(summary_rows), "annual_rows": len(annual_rows),
        "annual_robustness_rows": len(annual_robustness), "stress_rows": len(stress_rows),
        "trigger_rule": {
            "version": "SPY_DD5OBS_GE5PCT_OR_SIGNAL_SHORT_ABS_DELTA_GE0.30_V1",
            "entry_spot_drawdown_observations": LOOKBACK_OBSERVATIONS,
            "entry_spot_drawdown_threshold_pct": 5.0,
            "short_put_signal_abs_delta_threshold": 0.30,
            "combine": "OR",
            "lookahead": "No future observations. Current entry plus up to four prior entries in the same phase; drawdown needs all five valid observations.",
        },
        "tail_targets": [{"label": "TAIL_025_DELTA", "target_abs_delta": 0.025},
                         {"label": "TAIL_05_DELTA", "target_abs_delta": 0.05},
                         {"label": "TAIL_10_DELTA", "target_abs_delta": 0.10}],
        "quantities": list(QUANTITIES), "costs": replay_manifest.get("costs"),
        "input_sha256": {
            "baseline_ledgers": baseline_hashes,
            "overlay_trade_level_csv": sha256_file(trade_path),
            "overlay_entry_selection_csv": sha256_file(selection_path),
            "overlay_manifest_json": sha256_file(replay_manifest_path),
        },
        "warnings": [
            "Five phase schedules overlap and are not independent samples.",
            "EOD quotes/displayed sizes are not verified fills.",
            "Triggered entries with unavailable exits remain missing from realized conditional P&L.",
            "Stress is expiry intrinsic for the SPY short-put sleeve only.",
            "No portfolio NAV, margin, forced liquidation, early exercise or live orders are modeled.",
        ],
    }
    (args.out / "conditional_manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False), encoding="utf-8")
    report = build_report(args.out, list(flags.values()), summary_rows, annual_robustness, stress_rows, manifest)
    report_path = args.out / "SPY_FAR_TAIL_CONDITIONAL_REPORT.md"
    report_path.write_text(report, encoding="utf-8")
    if manifest["status"] != "COMPLETED" or len(report) < 10000:
        raise RuntimeError("Conditional experiment output failed completion checks")
    print(json.dumps({"status": manifest["status"], "cohorts": len(cohorts), "triggers": len(flags),
                      "trade_rows": len(conditional_rows), "summary_rows": len(summary_rows),
                      "annual_rows": len(annual_rows), "stress_rows": len(stress_rows),
                      "report_bytes": len(report.encode("utf-8"))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
