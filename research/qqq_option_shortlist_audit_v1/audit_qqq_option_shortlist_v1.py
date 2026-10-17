#!/usr/bin/env python3
"""Independent cost, time-split, and tail-capacity audit for QQQ shortlist replay V1.

Consumes persisted trade rows only. It does not refit the signal or select new thresholds.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from statistics import median
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SOURCE_RUN = ROOT / "research" / "qqq_option_shortlist_results_v1" / "run-39003581461-d2e3d21c54c1e02a11c75218abc588458b59b4d1"
NAV_USD = 80_000.0
BUDGETS = (0.005, 0.01, 0.02)
MULTIPLIER = 100.0
BASE_SLIPPAGE_PER_SHARE = 0.05
STRESS_SLIPPAGE_PER_SHARE = 0.10
COMMISSION_PER_CONTRACT_SIDE = 0.65
COST_CASES = ("ZERO", "BASE", "STRESS")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def n(value: Any) -> float | None:
    try:
        x = float(value)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def wilson_95(wins: int, trials: int) -> list[float | None]:
    """Nominal Wilson binomial interval; does not correct for event clustering."""
    if trials <= 0:
        return [None, None]
    z = 1.959963984540054
    p = wins / trials
    den = 1.0 + z * z / trials
    center = (p + z * z / (2.0 * trials)) / den
    half = z * math.sqrt((p * (1.0 - p) / trials) + z * z / (4.0 * trials * trials)) / den
    return [round(max(0.0, center - half) * 100.0, 4),
            round(min(1.0, center + half) * 100.0, 4)]


def parse_trade(raw: dict[str, str]) -> dict[str, Any]:
    legs = json.loads(raw["contract_legs"])
    contracts = sum(int(leg["qty"]) for leg in legs)
    entry_cf = n(raw.get("entry_cashflow_usd"))
    pnl = n(raw.get("net_pnl_usd"))
    risk = n(raw.get("terminal_worst_loss_usd"))
    parsed = dict(raw)
    parsed.update({
        "legs": legs,
        "contracts": contracts,
        "year": int(str(raw.get("signal_date", ""))[:4]),
        "pnl": pnl,
        "entry_cf": entry_cf,
        "risk": risk,
        "mae": n(raw.get("mae_one_unit_usd")),
        "mfe": n(raw.get("mfe_one_unit_usd")),
        "depth_units": int(n(raw.get("depth_units_at_entry")) or 0),
    })
    return parsed


def scenario_pnl(row: dict[str, Any], case: str) -> float | None:
    pnl = row.get("pnl")
    if pnl is None:
        return None
    contracts = int(row["contracts"])
    if case == "ZERO":
        # Remove both entry and exit: $0.05/share x 100 x 2 sides + $0.65 x 2 sides.
        return float(pnl) + contracts * (2.0 * (BASE_SLIPPAGE_PER_SHARE * MULTIPLIER + COMMISSION_PER_CONTRACT_SIDE))
    if case == "BASE":
        return float(pnl)
    if case == "STRESS":
        # Stress doubles slippage from $0.05 to $0.10; commission remains unchanged.
        return float(pnl) - contracts * (2.0 * ((STRESS_SLIPPAGE_PER_SHARE - BASE_SLIPPAGE_PER_SHARE) * MULTIPLIER))
    raise ValueError(f"Unknown cost case: {case}")


def terminal_worst_loss(row: dict[str, Any], case: str) -> float:
    """Recompute expiry intrinsic worst loss at payoff knots for changed entry friction."""
    contracts = int(row["contracts"])
    entry_cf = float(row["entry_cf"])
    if case == "ZERO":
        entry_cf += contracts * (BASE_SLIPPAGE_PER_SHARE * MULTIPLIER + COMMISSION_PER_CONTRACT_SIDE)
    elif case == "STRESS":
        entry_cf -= contracts * ((STRESS_SLIPPAGE_PER_SHARE - BASE_SLIPPAGE_PER_SHARE) * MULTIPLIER)
    elif case != "BASE":
        raise ValueError(f"Unknown cost case: {case}")

    strikes = {float(leg["strike"]) for leg in row["legs"]}
    knots = sorted({0.0, *strikes, max(strikes) * 2.0 + 1.0})
    pnls = []
    for spot in knots:
        expiry_payoff = 0.0
        for leg in row["legs"]:
            strike = float(leg["strike"])
            right = str(leg["right"])
            side = str(leg["side"])
            qty = int(leg["qty"])
            intrinsic = max(spot - strike, 0.0) if right == "C" else max(strike - spot, 0.0)
            sign = 1.0 if side == "buy" else -1.0
            expiry_payoff += sign * intrinsic * MULTIPLIER * qty
        pnls.append(entry_cf + expiry_payoff)
    return max(0.0, -min(pnls))


def capacity_counts(row: dict[str, Any], case: str) -> dict[str, int]:
    risk = terminal_worst_loss(row, case)
    depth = max(0, int(row["depth_units"]))
    out: dict[str, int] = {}
    for budget in BUDGETS:
        label = str(int(budget * 1000))
        if risk > 0:
            by_risk = math.floor(NAV_USD * budget / risk)
        else:
            by_risk = depth
        out[label] = min(depth, max(0, by_risk))
    return out


def summarize(rows: list[dict[str, Any]], case: str) -> dict[str, Any]:
    usable = [r for r in rows if r.get("status") == "RESOLVED" and scenario_pnl(r, case) is not None]
    unresolved = sum(r.get("status") != "RESOLVED" for r in rows)
    pnls = [float(scenario_pnl(r, case)) for r in usable]
    wins = sum(p > 0 for p in pnls)
    losses = sum(p < 0 for p in pnls)
    positive = sum(p for p in pnls if p > 0)
    negative = -sum(p for p in pnls if p < 0)
    def mean(vals: list[float]) -> float | None:
        return round(sum(vals) / len(vals), 4) if vals else None
    capacity = {
        label: sum(capacity_counts(r, case)[label] > 0 for r in usable)
        for label in ("5", "10", "20")
    }
    risks = [terminal_worst_loss(r, case) for r in usable]
    ci = wilson_95(wins, len(pnls))
    return {
        "cost_case": case,
        "opened_or_recorded": len(rows),
        "resolved": len(usable),
        "unresolved": unresolved,
        "wins": wins,
        "win_rate_pct": round(100.0 * wins / len(pnls), 4) if pnls else None,
        "win_rate_wilson95_low_pct": ci[0],
        "win_rate_wilson95_high_pct": ci[1],
        "mean_net_pnl_usd_per_unit": mean(pnls),
        "median_net_pnl_usd_per_unit": round(median(pnls), 4) if pnls else None,
        "total_noncompounded_net_pnl_usd": round(sum(pnls), 4) if pnls else None,
        "profit_factor": round(positive / negative, 5) if negative > 0 else (None if positive == 0 else "INF_NO_LOSSES_IN_SAMPLE"),
        "worst_net_pnl_usd_per_unit": round(min(pnls), 4) if pnls else None,
        "mean_entry_terminal_worst_loss_usd": mean(risks),
        "episodes_with_at_least_one_unit_under_0p5pct_nav_tail_budget": capacity["5"],
        "episodes_with_at_least_one_unit_under_1pct_nav_tail_budget": capacity["10"],
        "episodes_with_at_least_one_unit_under_2pct_nav_tail_budget": capacity["20"],
        "mean_mae_usd_base_marks": mean([float(r["mae"]) for r in usable if r.get("mae") is not None]),
        "nav_for_capacity_reference_usd": NAV_USD,
        "win_rate_ci_note": "Naive Wilson interval; market-event clustering may make this interval too narrow."
    }


def load_source(source_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any], dict[str, str]]:
    manifest_path = source_dir / "manifest.json"
    summary_path = source_dir / "summary.json"
    trades_path = source_dir / "trades.csv"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    replay_summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if manifest.get("research_id") != "QQQ_OPTION_SHORTLIST_REPLAY_V1":
        raise ValueError("Unexpected replay research_id; refusing to audit.")
    if manifest.get("source_end") != "2025-12-15" or manifest.get("nav_reference_usd") != NAV_USD:
        raise ValueError("Unexpected replay source end or NAV; refusing to audit.")
    if int(manifest.get("source_sessions", -1)) != 1960 or int(manifest.get("signals", -1)) != 28:
        raise ValueError("Replay manifest session/signal counts changed; update audit contract explicitly.")
    if int(replay_summary.get("signal_summary", {}).get("signal_count", -1)) != 28:
        raise ValueError("Replay summary signal count does not match frozen audit contract.")
    expected_files = manifest.get("source_file_git_blob_sha") or {}
    if len(expected_files) != 8 or any(not isinstance(v, str) or len(v) != 40 for v in expected_files.values()):
        raise ValueError("Expected eight SHA-pinned annual option files.")
    with trades_path.open("r", newline="", encoding="utf-8") as f:
        trades = [parse_trade(r) for r in csv.DictReader(f)]
    if len(trades) != int(manifest.get("trade_rows", -1)):
        raise ValueError(f"Trade row count mismatch: {len(trades)} vs {manifest.get('trade_rows')}")
    hashes = {
        "input_manifest_sha256": sha256_file(manifest_path),
        "input_summary_sha256": sha256_file(summary_path),
        "input_trades_sha256": sha256_file(trades_path),
    }
    return trades, manifest, replay_summary, hashes


def run_audit(source_dir: Path, output_dir: Path) -> dict[str, Any]:
    trades, source_manifest, replay_summary, hashes = load_source(source_dir)
    strategies = sorted({str(r["strategy_id"]) for r in trades})
    periods = {
        "ALL_2018_2025": lambda year: 2018 <= year <= 2025,
        "EARLIER_2018_2022": lambda year: 2018 <= year <= 2022,
        "LATER_2023_2025": lambda year: 2023 <= year <= 2025,
    }
    results = []
    lookup: dict[tuple[str, int], dict[str, Any]] = {}
    for strategy in strategies:
        base_rows = [r for r in trades if r["strategy_id"] == strategy]
        for period_name, predicate in periods.items():
            group = [r for r in base_rows if predicate(r["year"])]
            for case in COST_CASES:
                row = {"strategy_id": strategy, "period": period_name, **summarize(group, case)}
                results.append(row)
                lookup[(strategy, len(lookup))] = row

    pair_results = []
    call = {r["signal_date"]: r for r in trades if r["strategy_id"] == "CALL_DEBIT_50D_10D" and r.get("status") == "RESOLVED"}
    hedge = {r["signal_date"]: r for r in trades if r["strategy_id"] == "CALL_DEBIT_PLUS_LONG_PUT_10D" and r.get("status") == "RESOLVED"}
    for period_name, predicate in periods.items():
        dates = sorted(d for d in set(call) & set(hedge) if predicate(int(d[:4])))
        for case in COST_CASES:
            diffs = [float(scenario_pnl(hedge[d], case)) - float(scenario_pnl(call[d], case)) for d in dates]
            mae_diffs = [
                float(hedge[d]["mae"]) - float(call[d]["mae"])
                for d in dates if hedge[d].get("mae") is not None and call[d].get("mae") is not None
            ]
            pair_results.append({
                "period": period_name,
                "cost_case": case,
                "matched_events": len(dates),
                "hedge_beats_call_debit_on_net_pnl": sum(v > 0 for v in diffs),
                "hedge_mean_incremental_net_pnl_usd": round(sum(diffs) / len(diffs), 4) if diffs else None,
                "hedge_median_incremental_net_pnl_usd": round(median(diffs), 4) if diffs else None,
                "hedge_worst_incremental_net_pnl_usd": round(min(diffs), 4) if diffs else None,
                "hedge_improves_base_mark_mae_count": sum(v > 0 for v in mae_diffs),
                "hedge_mean_incremental_mae_usd": round(sum(mae_diffs) / len(mae_diffs), 4) if mae_diffs else None,
                "interpretation": "Positive incremental MAE means less adverse (less negative) observed mark; paired events are not independent market regimes."
            })

    results.sort(key=lambda r: (r["period"], r["strategy_id"], COST_CASES.index(r["cost_case"])))
    pair_results.sort(key=lambda r: (r["period"], COST_CASES.index(r["cost_case"])))
    payload = {
        "audit_id": "QQQ_OPTION_SHORTLIST_COST_AND_HOLDOUT_AUDIT_V1",
        "source_run_id": "39003581461",
        "source_commit_tested": "d2e3d21c54c1e02a11c75218abc588458b59b4d1",
        "source_manifest": {
            "source_end": source_manifest["source_end"],
            "source_sessions": source_manifest["source_sessions"],
            "signals": source_manifest["signals"],
            "trade_rows": source_manifest["trade_rows"],
            "source_file_count": source_manifest["source_file_count"],
            "source_file_git_blob_sha": source_manifest["source_file_git_blob_sha"],
            "evidence_class": source_manifest["pricing_evidence"],
            **hashes
        },
        "cost_cases": {
            "ZERO": "Remove $0.05/share/leg/side slippage and $0.65/contract/leg/side commissions from both entry and exit cashflows; capacity recomputed with friction-free entry cashflow.",
            "BASE": "Original replay: $0.05/share/leg/side slippage and $0.65/contract/leg/side commission.",
            "STRESS": "Increase slippage to $0.10/share/leg/side, commission unchanged; capacity recomputed with stressed entry cashflow."
        },
        "periods": {
            "ALL_2018_2025": "All 28 observed event signals; episode metrics are not compounded portfolio performance.",
            "EARLIER_2018_2022": "Earlier-period directional check; not a separately selected training protocol.",
            "LATER_2023_2025": "Late-period directional check with only 9 call-debit episodes; not labelled a virgin out-of-sample holdout."
        },
        "strategy_results": results,
        "paired_long_put_increment": pair_results,
        "limitations": [
            "Public historical EOD quote snapshots, not authenticated fills; exact tick timestamps, broker margin, exercise/assignment, fill sequencing and market impact are not verified.",
            "Signal episodes and regime windows are not independent random trials. Wilson intervals are descriptive and may be too narrow.",
            "Episode P&L is noncompounded one-unit P&L, not portfolio CAGR, portfolio MaxDD, or a proven NAV allocation result.",
            "The 1xN and Nx1 PUT Ratio candidates share selected strikes but multiply different legs; large entry terminal tail losses can make every full unit infeasible even when short-period P&L is positive.",
            "The latest option chain date is 2025-12-15; no option result after that date is claimed.",
            "The terminal loss used for illustrative capacity is expiry intrinsic payoff at payoff knots; it does not cap interim liquidation, margin expansion, forced liquidation or gap losses."
        ]
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "audit_summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    csv_path = output_dir / "audit_summary.csv"
    flat_fields = [
        "strategy_id", "period", "cost_case", "opened_or_recorded", "resolved", "unresolved",
        "wins", "win_rate_pct", "win_rate_wilson95_low_pct", "win_rate_wilson95_high_pct",
        "mean_net_pnl_usd_per_unit", "median_net_pnl_usd_per_unit", "total_noncompounded_net_pnl_usd",
        "profit_factor", "worst_net_pnl_usd_per_unit",
        "mean_entry_terminal_worst_loss_usd",
        "episodes_with_at_least_one_unit_under_0p5pct_nav_tail_budget",
        "episodes_with_at_least_one_unit_under_1pct_nav_tail_budget",
        "episodes_with_at_least_one_unit_under_2pct_nav_tail_budget",
        "mean_mae_usd_base_marks"
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=flat_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)

    def find_result(strategy: str, period: str, case: str) -> dict[str, Any]:
        return next(r for r in results if r["strategy_id"] == strategy and r["period"] == period and r["cost_case"] == case)

    lines = [
        "# QQQ Option Shortlist V1 — Cost / Time-Split / Tail-Capacity Audit",
        "",
        "## Evidence class",
        "",
        f"- Source run: 39003581461; replay window 2018-03-01 to {source_manifest['source_end']}; 1,960 sessions, 28 signals, {source_manifest['trade_rows']} strategy-episode rows.",
        f"- Input hashes: manifest {hashes['input_manifest_sha256']}; summary {hashes['input_summary_sha256']}; trades {hashes['input_trades_sha256']}.",
        f"- Evidence: {source_manifest['pricing_evidence']}. This is a persisted-data audit, not a fresh quote download or a confirmed-fill replay.",
        "- Scenario arithmetic is applied to the already replayed exact listed-contract rows; it does not reselect contracts or refit the signal.",
        "",
        "## Base-case outcome summary",
        "",
        "| Strategy | Period | n | Wins | Win rate (nominal Wilson 95%) | Mean net P&L/unit | PF | Worst P&L/unit | Fits 0.5% / 1% / 2% NAV tail budget |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|"
    ]
    chosen = [
        ("CALL_DEBIT_50D_10D", "ALL_2018_2025"),
        ("CALL_DEBIT_50D_10D", "EARLIER_2018_2022"),
        ("CALL_DEBIT_50D_10D", "LATER_2023_2025"),
        ("CALL_DEBIT_PLUS_LONG_PUT_10D", "ALL_2018_2025"),
        ("CALL_DEBIT_PLUS_LONG_PUT_10D", "EARLIER_2018_2022"),
        ("CALL_DEBIT_PLUS_LONG_PUT_10D", "LATER_2023_2025"),
        ("PUT_SHORT_HEAVY_1x5", "ALL_2018_2025"),
        ("PUT_SHORT_HEAVY_1x6", "ALL_2018_2025"),
        ("PUT_LONG_HEAVY_2x1", "ALL_2018_2025"),
    ]
    for strategy, period in chosen:
        r = find_result(strategy, period, "BASE")
        ci = f"{r['win_rate_wilson95_low_pct']:.1f}–{r['win_rate_wilson95_high_pct']:.1f}%" if r["win_rate_wilson95_low_pct"] is not None else "n/a"
        fit = f"{r['episodes_with_at_least_one_unit_under_0p5pct_nav_tail_budget']} / {r['episodes_with_at_least_one_unit_under_1pct_nav_tail_budget']} / {r['episodes_with_at_least_one_unit_under_2pct_nav_tail_budget']}"
        lines.append(f"| {strategy} | {period} | {r['resolved']} | {r['wins']} | {r['win_rate_pct']:.1f}% ({ci}) | {r['mean_net_pnl_usd_per_unit']:.2f} | {r['profit_factor']} | {r['worst_net_pnl_usd_per_unit']:.2f} | {fit} |")
    lines += [
        "",
        "## Cost sensitivity: mean net P&L per one structure unit",
        "",
        "| Strategy | Period | Zero friction | Base | Stress slippage |",
        "|---|---|---:|---:|---:|"
    ]
    for strategy, period in chosen:
        vals = [find_result(strategy, period, c)["mean_net_pnl_usd_per_unit"] for c in COST_CASES]
        lines.append(f"| {strategy} | {period} | {vals[0]:.2f} | {vals[1]:.2f} | {vals[2]:.2f} |")
    lines += [
        "",
        "## Paired effect of adding one LONG PUT to the call debit vertical",
        "",
        "| Period | Cost case | Matched events | Put hedge has higher net P&L | Mean incremental P&L | Median incremental P&L | Mean MAE change | MAE improves in pairs |",
        "|---|---|---:|---:|---:|---:|---:|---:|"
    ]
    for r in pair_results:
        lines.append(f"| {r['period']} | {r['cost_case']} | {r['matched_events']} | {r['hedge_beats_call_debit_on_net_pnl']} | {r['hedge_mean_incremental_net_pnl_usd']} | {r['hedge_median_incremental_net_pnl_usd']} | {r['hedge_mean_incremental_mae_usd']} | {r['hedge_improves_base_mark_mae_count']} |")
    lines += [
        "",
        "## Decision, not a winner badge",
        "",
        "- A positive per-unit mean is not sufficient. Capacity must be nonzero at the actual whole-contract tail-risk budget, and it must survive the adverse-cost case.",
        "- The late-period slice contains only nine call-debit events; it is a directional consistency check, not a statistically conclusive or fully untouched holdout.",
        "- The PUT Ratio variants with N short-heavy can show positive event-level P&L while having no full-size capacity under 0.5%/1%/2% of $80k terminal-tail budgets. Do not promote them on win rate.",
        "- The add-on LONG PUT is a paid hedge. Judge it by paired event P&L and adverse mark changes together, not by the name 'protection'.",
        "- No strategy is approved for HUB execution by this audit. The next promotion gate is a predeclared risk-normalized portfolio replay with same NAV, same risk capital, marked option legs, and an untouched later period.",
        "",
        "## Limitations",
        ""
    ]
    lines.extend(f"- {item}" for item in payload["limitations"])
    (output_dir / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    payload["output_files"] = ["audit_summary.json", "audit_summary.csv", "REPORT.md"]
    (output_dir / "audit_summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, default=SOURCE_RUN)
    parser.add_argument("--out", type=Path, default=SOURCE_RUN / "audit_v1")
    args = parser.parse_args()
    report = run_audit(args.source_dir, args.out)
    base = [r for r in report["strategy_results"] if r["period"] == "ALL_2018_2025" and r["cost_case"] == "BASE"]
    print(json.dumps({
        "audit_id": report["audit_id"],
        "source_run_id": report["source_run_id"],
        "input_hashes": report["source_manifest"],
        "all_period_base": [{
            "strategy_id": r["strategy_id"], "n": r["resolved"], "win_rate_pct": r["win_rate_pct"],
            "mean_pnl": r["mean_net_pnl_usd_per_unit"], "profit_factor": r["profit_factor"],
            "fit_1pct_tail_budget": r["episodes_with_at_least_one_unit_under_1pct_nav_tail_budget"]
        } for r in base],
        "paired_long_put_increment": report["paired_long_put_increment"],
        "out_files": report["output_files"]
    }, indent=2))


if __name__ == "__main__":
    main()
