#!/usr/bin/env python3
"""Independent-N QQQ long-put and SPY short-put quote-side counterfactual grid."""
from __future__ import annotations
import argparse, csv, hashlib, json, math, statistics
from pathlib import Path
from typing import Any, Callable

SOURCE_TRADES_SHA = "13b4cf574d24250655d8f9e3d5878e3a4d4f1bd5"
SOURCE_SUMMARY_SHA = "968676c093d48579b516e1b07d4ec55619b90349"
POLICIES = ("HOLD_5_SESSIONS", "HOLD_10_SESSIONS", "HOLD_20_SESSIONS", "EXIT_AT_DTE_LE_7")
COST_SCENARIOS = (
    {"name": "ZERO_COST", "slippage": 0.0, "commission": 0.0},
    {"name": "BASE_COST", "slippage": 0.05, "commission": 0.65},
    {"name": "ADVERSE_COST", "slippage": 0.10, "commission": 0.65},
)
TRADE_PATH = "research/qqq_spy_put_equal_premium_v1/results/latest/trade_episodes.csv"
SUMMARY_PATH = "research/qqq_spy_put_equal_premium_v1/results/latest/summary.json"
FIELDS = [
    "strategy", "policy", "cost_scenario", "slippage_per_option_share_usd",
    "commission_per_contract_per_side_usd", "qqq_long_contracts", "spy_short_contracts",
    "mean_qqq_contracts", "mean_spy_contracts", "opened_n", "resolved_n", "unresolved_n",
    "wins", "losses", "flat", "win_rate_pct", "mean_net_pnl_usd", "median_net_pnl_usd",
    "total_net_pnl_usd", "best_net_pnl_usd", "worst_net_pnl_usd", "profit_factor",
    "mean_qqq_gross_pnl_usd", "mean_spy_gross_pnl_usd",
    "mean_qqq_premium_debit_usd", "mean_spy_premium_credit_usd",
    "mean_abs_premium_mismatch_usd", "mean_premium_match_pct",
    "mean_net_delta_vs_premium_matched_baseline_usd", "execution_depth_status",
]

def git_blob_sha_bytes(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()

def read_verified_inputs(trades_path: Path, summary_path: Path) -> list[dict[str, Any]]:
    for path, expected in ((trades_path, SOURCE_TRADES_SHA), (summary_path, SOURCE_SUMMARY_SHA)):
        actual = git_blob_sha_bytes(path.read_bytes())
        if actual != expected:
            raise ValueError(f"source input pin mismatch for {path}: {actual} != {expected}")
    with trades_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("trade_episodes.csv is empty")
    required = {
        "episode_id", "policy", "status", "long_qqq_qty", "short_spy_qty",
        "qqq_entry_ask", "spy_entry_bid", "exit_qqq_bid", "exit_spy_ask",
        "qqq_long_gross_pnl_usd", "spy_short_gross_pnl_usd", "net_pnl_usd",
        "qqq_long_premium_debit_usd", "spy_short_premium_credit_usd",
    }
    missing = sorted(required - set(rows[0]))
    if missing:
        raise ValueError(f"trade_episodes.csv missing fields: {missing}")
    keys = [(r["episode_id"], r["policy"]) for r in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate (episode_id, policy) records")
    policies_seen = {r["policy"] for r in rows}
    if policies_seen != set(POLICIES):
        raise ValueError(f"unexpected exit-policy coverage: {sorted(policies_seen)}")
    for policy in POLICIES:
        count = sum(r["policy"] == policy for r in rows)
        if count != 44:
            raise ValueError(f"{policy}: expected 44 opened cohorts, got {count}")
    return rows

def number(value: Any) -> float | None:
    try:
        v = float(value)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None

def qqq_unit_gross(row: dict[str, Any]) -> float:
    entry, exit_price = number(row.get("qqq_entry_ask")), number(row.get("exit_qqq_bid"))
    if entry is None or exit_price is None:
        raise ValueError(f"resolved QQQ episode {row.get('episode_id')} lacks entry/exit quote")
    return (exit_price - entry) * 100.0

def spy_unit_gross(row: dict[str, Any]) -> float:
    entry, exit_price = number(row.get("spy_entry_bid")), number(row.get("exit_spy_ask"))
    if entry is None or exit_price is None:
        raise ValueError(f"resolved SPY episode {row.get('episode_id')} lacks entry/exit quote")
    return (entry - exit_price) * 100.0

def round_trip_cost_per_contract(slippage_per_share: float, commission_per_side: float) -> float:
    return slippage_per_share * 100.0 * 2.0 + commission_per_side * 2.0

def premium_match_pct(debit: float, credit: float) -> float | None:
    high = max(debit, credit)
    if high <= 0:
        return None
    return min(debit, credit) / high * 100.0

def _fmt(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        return round(value, 6)
    return value

def measure_strategy(rows: list[dict[str, Any]], strategy: str, policy: str,
                     nq_for_row: Callable[[dict[str, Any]], int],
                     ns_for_row: Callable[[dict[str, Any]], int],
                     cost: dict[str, Any], depth_status: str,
                     baseline_expectancy: float | None = None) -> dict[str, Any]:
    opened = [r for r in rows if r["policy"] == policy]
    if not opened:
        raise ValueError(f"no rows for {policy}")
    pnl_values, q_gross_values, s_gross_values = [], [], []
    q_premiums, s_premiums, mismatches, matches, q_qtys, s_qtys = [], [], [], [], [], []
    unresolved = 0
    per_contract_cost = round_trip_cost_per_contract(cost["slippage"], cost["commission"])
    is_standalone = strategy.endswith("_STANDALONE")
    for r in opened:
        nq, ns = int(nq_for_row(r)), int(ns_for_row(r))
        if nq < 0 or ns < 0:
            raise ValueError("contract quantities cannot be negative")
        q_entry, s_entry = float(r["qqq_entry_ask"]), float(r["spy_entry_bid"])
        q_qtys.append(nq); s_qtys.append(ns)
        q_debit, s_credit = q_entry * 100.0 * nq, s_entry * 100.0 * ns
        q_premiums.append(q_debit); s_premiums.append(s_credit)
        if not is_standalone:
            mismatches.append(abs(q_debit - s_credit))
            match = premium_match_pct(q_debit, s_credit)
            if match is not None:
                matches.append(match)
        if r["status"] != "RESOLVED":
            unresolved += 1
            continue
        q_gross = qqq_unit_gross(r) * nq if nq else 0.0
        s_gross = spy_unit_gross(r) * ns if ns else 0.0
        q_gross_values.append(q_gross); s_gross_values.append(s_gross)
        pnl_values.append(q_gross + s_gross - per_contract_cost * (nq + ns))
    wins = sum(v > 1e-9 for v in pnl_values)
    losses = sum(v < -1e-9 for v in pnl_values)
    flats = len(pnl_values) - wins - losses
    positive_sum = sum(v for v in pnl_values if v > 0)
    negative_sum = -sum(v for v in pnl_values if v < 0)
    expectancy = statistics.mean(pnl_values) if pnl_values else None
    nq0, ns0 = nq_for_row(opened[0]), ns_for_row(opened[0])
    return {
        "strategy": strategy, "policy": policy, "cost_scenario": cost["name"],
        "slippage_per_option_share_usd": cost["slippage"],
        "commission_per_contract_per_side_usd": cost["commission"],
        "qqq_long_contracts": nq0 if all(nq_for_row(x) == nq0 for x in opened) else "VARIABLE",
        "spy_short_contracts": ns0 if all(ns_for_row(x) == ns0 for x in opened) else "VARIABLE",
        "mean_qqq_contracts": statistics.mean(q_qtys) if q_qtys else None,
        "mean_spy_contracts": statistics.mean(s_qtys) if s_qtys else None,
        "opened_n": len(opened), "resolved_n": len(pnl_values), "unresolved_n": unresolved,
        "wins": wins, "losses": losses, "flat": flats,
        "win_rate_pct": wins / len(pnl_values) * 100.0 if pnl_values else None,
        "mean_net_pnl_usd": expectancy,
        "median_net_pnl_usd": statistics.median(pnl_values) if pnl_values else None,
        "total_net_pnl_usd": sum(pnl_values) if pnl_values else None,
        "best_net_pnl_usd": max(pnl_values) if pnl_values else None,
        "worst_net_pnl_usd": min(pnl_values) if pnl_values else None,
        "profit_factor": positive_sum / negative_sum if negative_sum > 0 else (None if not pnl_values else (math.inf if positive_sum > 0 else 0.0)),
        "mean_qqq_gross_pnl_usd": statistics.mean(q_gross_values) if q_gross_values else None,
        "mean_spy_gross_pnl_usd": statistics.mean(s_gross_values) if s_gross_values else None,
        "mean_qqq_premium_debit_usd": statistics.mean(q_premiums) if q_premiums else None,
        "mean_spy_premium_credit_usd": statistics.mean(s_premiums) if s_premiums else None,
        "mean_abs_premium_mismatch_usd": statistics.mean(mismatches) if mismatches else None,
        "mean_premium_match_pct": statistics.mean(matches) if matches else None,
        "mean_net_delta_vs_premium_matched_baseline_usd": expectancy - baseline_expectancy if expectancy is not None and baseline_expectancy is not None else None,
        "execution_depth_status": depth_status,
    }

def build_outputs(trades: list[dict[str, Any]], max_total_contracts: int = 9, max_leg_contracts: int = 9):
    if max_total_contracts < 2 or max_leg_contracts < 1:
        raise ValueError("max_total_contracts must be >=2 and max_leg_contracts >=1")
    outputs, baselines = [], {}
    for cost in COST_SCENARIOS:
        for policy in POLICIES:
            source = [r for r in trades if r["policy"] == policy]
            baseline = measure_strategy(source, "PREMIUM_MATCHED_BASELINE", policy,
                lambda r: int(r["long_qqq_qty"]), lambda r: int(r["short_spy_qty"]),
                cost, "BASE_RUN_ENTRY_AND_EXIT_SIZE_SCREENED")
            if cost["name"] == "BASE_COST":
                for r in source:
                    if r["status"] == "RESOLVED":
                        recalculated = (qqq_unit_gross(r) * int(r["long_qqq_qty"])
                            + spy_unit_gross(r) * int(r["short_spy_qty"])
                            - round_trip_cost_per_contract(cost["slippage"], cost["commission"])
                              * (int(r["long_qqq_qty"]) + int(r["short_spy_qty"])))
                        stored = number(r["net_pnl_usd"])
                        if stored is None or abs(recalculated - stored) > 0.02:
                            raise ValueError(f"base P&L reconciliation failed for {r['episode_id']} {policy}: {recalculated} vs {stored}")
            baselines[(policy, cost["name"])] = baseline
            outputs.append(baseline)
            for leg in ("QQQ_LONG_PUT_STANDALONE", "SPY_SHORT_PUT_STANDALONE"):
                for n in range(1, max_leg_contracts + 1):
                    nqf, nsf = ((lambda r, n=n: n), (lambda r: 0)) if leg.startswith("QQQ") else ((lambda r: 0), (lambda r, n=n: n))
                    outputs.append(measure_strategy(source, leg, policy, nqf, nsf, cost,
                        "COUNTERFACTUAL_ENTRY_AND_EXIT_DEPTH_NOT_STORED_FOR_FIXED_N"))
            for nq in range(1, min(max_leg_contracts, max_total_contracts - 1) + 1):
                for ns in range(1, min(max_leg_contracts, max_total_contracts - nq) + 1):
                    outputs.append(measure_strategy(source, "FIXED_PAIR_CROSS_GRID", policy,
                        lambda r, nq=nq: nq, lambda r, ns=ns: ns, cost,
                        "COUNTERFACTUAL_ENTRY_AND_EXIT_DEPTH_NOT_STORED_FOR_FIXED_N",
                        baseline["mean_net_pnl_usd"]))
    order = {"PREMIUM_MATCHED_BASELINE": 0, "QQQ_LONG_PUT_STANDALONE": 1,
             "SPY_SHORT_PUT_STANDALONE": 2, "FIXED_PAIR_CROSS_GRID": 3}
    cost_index = {c["name"]: i for i, c in enumerate(COST_SCENARIOS)}
    policy_index = {p: i for i, p in enumerate(POLICIES)}
    outputs.sort(key=lambda r: (cost_index[r["cost_scenario"]], policy_index[r["policy"]],
        order[r["strategy"]], str(r["qqq_long_contracts"]).zfill(3), str(r["spy_short_contracts"]).zfill(3)))
    return outputs, baselines

def csv_text(rows: list[dict[str, Any]]) -> str:
    import io
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=FIELDS, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: _fmt(row.get(key)) for key in FIELDS})
    return buffer.getvalue()

def money(value: Any) -> str:
    return "n/a" if value is None else "$" + format(float(value), ",.2f")

def percent(value: Any) -> str:
    return "n/a" if value is None else f"{float(value):.2f}%"

def write_report(outputs, baselines, out: Path, max_total_contracts: int, max_leg_contracts: int):
    base = [baselines[(p, "BASE_COST")] for p in POLICIES]
    lines = [
        "# QQQ LONG PUT / SPY SHORT PUT — Independent-Leg Sizing V1", "",
        "**Status: research-only counterfactual sizing grid. No live sizing, no orders, no merge to main.**", "",
        "## What this answers", "",
        "QQQ LONG PUT and SPY SHORT PUT are first measured separately at fixed N=1 through N=" + str(max_leg_contracts) + ". Every fixed N:M pair under the combined cap is then cross-compared with the original variable-size equal-premium baseline. All rows reuse the frozen V1 selected contracts, entry dates and conservative quote-side exits; this is not a fresh strike selector or a profit-optimized search.", "",
        "## Source freeze and controls", "",
        "- Frozen trade input Git blob SHA: " + SOURCE_TRADES_SHA + "; frozen summary SHA: " + SOURCE_SUMMARY_SHA + ".",
        "- Window, 44 opened cohorts and four exit policies remain those of the equal-premium V1 input (2018-03-01 through 2025-12-15).",
        f"- Standalone N sweep: 1–{max_leg_contracts}; paired cross-grid: each leg N>=1 and QQQ+SPY <= {max_total_contracts} contracts.",
        "- Base costs: $0.05 per option share per side plus $0.65 commission per contract per side. Cost checks include ZERO, BASE and ADVERSE ($0.10/share + $0.65/contract/side).",
        "- Exits use QQQ LONG at displayed Bid and SPY SHORT buyback at displayed Ask. Unresolved episodes remain separate and are excluded from resolved-only P&L / win-rate denominators.",
        "- Fixed-N rows are counterfactual: the source output did not persist every entry/exit displayed-size value needed to verify each fixed N. Do not interpret them as confirmed fills or executable capacities. Only the original premium-matched baseline inherits its source run's entry/exit depth screen.", "",
        "## Existing equal-premium baseline at base assumed costs", "",
        "| Exit policy | Resolved / opened | Win / loss / flat | Win rate | Mean net P&L | Total net P&L | Worst resolved |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in base:
        lines.append(f"| {r['policy']} | {r['resolved_n']} / {r['opened_n']} | {r['wins']} / {r['losses']} / {r['flat']} | {percent(r['win_rate_pct'])} | {money(r['mean_net_pnl_usd'])} | {money(r['total_net_pnl_usd'])} | {money(r['worst_net_pnl_usd'])} |")
    lines += ["", "## Independent single-leg results at base costs", "",
        "Each row below runs one leg alone, with the other leg set to zero. The full N sweep and cost sensitivities are in independent_leg_sizing.csv.", "",
        "| Exit policy | Standalone leg | N | Resolved / opened | Win rate | Mean net P&L | Total net P&L | Worst resolved |",
        "|---|---|---:|---:|---:|---:|---:|---:|"]
    for policy in POLICIES:
        for leg, n in (("QQQ_LONG_PUT_STANDALONE", 1), ("QQQ_LONG_PUT_STANDALONE", 4),
                       ("QQQ_LONG_PUT_STANDALONE", max_leg_contracts),
                       ("SPY_SHORT_PUT_STANDALONE", 1), ("SPY_SHORT_PUT_STANDALONE", 4),
                       ("SPY_SHORT_PUT_STANDALONE", max_leg_contracts)):
            qn, sn = (n, 0) if leg.startswith("QQQ") else (0, n)
            r = next(x for x in outputs if x["strategy"] == leg and x["policy"] == policy
                     and x["cost_scenario"] == "BASE_COST" and x["qqq_long_contracts"] == qn and x["spy_short_contracts"] == sn)
            lines.append(f"| {policy} | {leg.replace('_STANDALONE','').replace('_',' ')} | {n} | {r['resolved_n']} / {r['opened_n']} | {percent(r['win_rate_pct'])} | {money(r['mean_net_pnl_usd'])} | {money(r['total_net_pnl_usd'])} | {money(r['worst_net_pnl_usd'])} |")
    lines += ["", "## Paired fixed-N cross-grid examples at base costs", "",
        "Examples only, not recommendations or optimization winners. The complete pair grid is in fixed_pair_cross_grid.csv and includes expectancy delta versus the equal-premium baseline.", "",
        "| Exit policy | QQQ long : SPY short | Win rate | Mean net P&L | Delta vs matched baseline expectancy | Total net P&L | Worst resolved |",
        "|---|---:|---:|---:|---:|---:|---:|"]
    for policy in POLICIES:
        for nq, ns in ((1, 1), (1, 5), (4, 5), (5, 1)):
            if nq + ns > max_total_contracts:
                continue
            r = next(x for x in outputs if x["strategy"] == "FIXED_PAIR_CROSS_GRID" and x["policy"] == policy
                     and x["cost_scenario"] == "BASE_COST" and x["qqq_long_contracts"] == nq and x["spy_short_contracts"] == ns)
            lines.append(f"| {policy} | {nq} : {ns} | {percent(r['win_rate_pct'])} | {money(r['mean_net_pnl_usd'])} | {money(r['mean_net_delta_vs_premium_matched_baseline_usd'])} | {money(r['total_net_pnl_usd'])} | {money(r['worst_net_pnl_usd'])} |")
    lines += ["", "## Interpretation boundaries", "",
        "- Premium parity is a cash-flow match, not equal underlying notional, Delta-dollar, maximum loss, margin or assignment exposure.",
        "- Fixed-N sweeps separate each leg's mark-to-market contribution from paired outcomes, but they do not re-fetch chains or revalidate displayed-size execution capacity.",
        "- Historical EOD quotes are not verified fills. Cohorts can share market regimes; do not select a strategy based on one apparently best grid cell.",
        "- Early assignment, broker margin, financing, taxes, portfolio compounding, forced liquidation and intraday paths are not modeled.", "",
        "## Files", "",
        "- independent_leg_sizing.csv: standalone QQQ N and standalone SPY N, each isolated.",
        "- fixed_pair_cross_grid.csv: fixed N:M comparisons under aggregate contract cap.",
        "- premium_matched_baseline.csv: original variable-size baseline by exit rule and cost scenario.",
        "- source_manifest.json: source pins and run parameters.", ""]
    (out / "summary.md").write_text("\n".join(lines), encoding="utf-8")

def run(trades_path: Path, summary_path: Path, out: Path, max_total_contracts: int, max_leg_contracts: int):
    trades = read_verified_inputs(trades_path, summary_path)
    outputs, baselines = build_outputs(trades, max_total_contracts, max_leg_contracts)
    out.mkdir(parents=True, exist_ok=True)
    standalone = [r for r in outputs if r["strategy"] in ("QQQ_LONG_PUT_STANDALONE", "SPY_SHORT_PUT_STANDALONE")]
    pairs = [r for r in outputs if r["strategy"] == "FIXED_PAIR_CROSS_GRID"]
    baseline_rows = [r for r in outputs if r["strategy"] == "PREMIUM_MATCHED_BASELINE"]
    (out / "independent_leg_sizing.csv").write_text(csv_text(standalone), encoding="utf-8")
    (out / "fixed_pair_cross_grid.csv").write_text(csv_text(pairs), encoding="utf-8")
    (out / "premium_matched_baseline.csv").write_text(csv_text(baseline_rows), encoding="utf-8")
    write_report(outputs, baselines, out, max_total_contracts, max_leg_contracts)
    manifest = {
        "schema": "qqq-spy-independent-leg-sizing.v1",
        "status": "GENERATED_COUNTERFACTUAL_FIXED_N_GRID",
        "input": {"trade_episodes_path": TRADE_PATH, "trade_episodes_git_blob_sha": SOURCE_TRADES_SHA,
                  "summary_json_path": SUMMARY_PATH, "summary_json_git_blob_sha": SOURCE_SUMMARY_SHA,
                  "source_study": "QQQ LONG PUT / SPY SHORT PUT equal-premium replay V1"},
        "parameters": {"max_total_pair_contracts": max_total_contracts, "max_standalone_leg_contracts": max_leg_contracts,
                       "contract_multiplier": 100, "cost_scenarios": COST_SCENARIOS, "exit_policies": list(POLICIES),
                       "pair_grid_cells_per_policy_cost": sum(1 for nq in range(1, min(max_leg_contracts, max_total_contracts - 1) + 1)
                           for ns in range(1, min(max_leg_contracts, max_total_contracts - nq) + 1))},
        "controls": {"same_selected_contract_ids_and_dates": True, "no_forward_fill_or_contract_substitution": True,
                     "fixed_n_displayed_depth_verified": False,
                     "execution_depth_status": "COUNTERFACTUAL_ENTRY_AND_EXIT_DEPTH_NOT_STORED_FOR_FIXED_N",
                     "resolved_only_pnl_and_win_rate": True, "unresolved": "kept separate; never assigned zero",
                     "real_fills": False},
    }
    (out / "source_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return {"source_rows": len(trades), "standalone_rows": len(standalone), "pair_rows": len(pairs), "baseline_rows": len(baseline_rows)}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trades", default=TRADE_PATH)
    parser.add_argument("--summary-json", default=SUMMARY_PATH)
    parser.add_argument("--out", default="research/qqq_spy_put_independent_leg_v1/results/latest")
    parser.add_argument("--max-total-contracts", type=int, default=9)
    parser.add_argument("--max-leg-contracts", type=int, default=9)
    args = parser.parse_args()
    stats = run(Path(args.trades), Path(args.summary_json), Path(args.out), args.max_total_contracts, args.max_leg_contracts)
    print(json.dumps({"status": "OK", **stats, "out": args.out}, indent=2))

if __name__ == "__main__":
    main()
