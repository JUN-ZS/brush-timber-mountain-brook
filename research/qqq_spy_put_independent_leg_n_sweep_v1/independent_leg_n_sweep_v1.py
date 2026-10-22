#!/usr/bin/env python3
"""Fixed-N independent QQQ LONG PUT / SPY SHORT PUT attribution on exact parent replay contracts.

This is deterministic post-analysis, not a new raw-option replay. Fixed N is not re-gated
against historical displayed depth, so results are quote-price counterfactuals, not fills.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, statistics
from pathlib import Path
from typing import Any, Iterable

MULTIPLIER = 100
POLICIES = ("HOLD_5_SESSIONS", "HOLD_10_SESSIONS", "HOLD_20_SESSIONS", "EXIT_AT_DTE_LE_7")
LEGS = ("QQQ_LONG_PUT", "SPY_SHORT_PUT")
FIXED_N = tuple(range(1, 7))
COSTS = (
    {"name": "ZERO_COST", "slippage": 0.0, "commission": 0.0},
    {"name": "BASE_COST", "slippage": 0.05, "commission": 0.65},
    {"name": "STRESS_COST", "slippage": 0.10, "commission": 0.65},
)

def fnum(v: Any) -> float | None:
    if v is None or str(v).strip() == "":
        return None
    try:
        n = float(v)
        return n if math.isfinite(n) else None
    except (TypeError, ValueError):
        return None

def inum(v: Any) -> int | None:
    n = fnum(v)
    return int(n) if n is not None else None

def rnd(v: float | None) -> float | str:
    return round(v, 6) if v is not None and math.isfinite(v) else ""

def fmt(v: Any) -> str:
    n = fnum(v)
    return "—" if n is None else "USD " + format(n, ",.2f")

def pct(v: Any) -> str:
    n = fnum(v)
    return "—" if n is None else format(n, ".2f") + "%"

def round_trip_cost(n: int, slip: float, commission: float) -> float:
    if n < 0 or slip < 0 or commission < 0:
        raise ValueError("contract counts and costs must be non-negative")
    return 2.0 * n * (slip * MULTIPLIER + commission)

def valid_pairs(cap: int = 9) -> list[tuple[int, int]]:
    if cap < 2:
        raise ValueError("combined contract cap must be at least 2")
    return [(q, s) for q in FIXED_N for s in FIXED_N if q + s <= cap]

def stats(values: Iterable[float | None]) -> dict[str, Any]:
    all_values = list(values)
    v = [float(x) for x in all_values if x is not None]
    wins = sum(x > 0.005 for x in v)
    losses = sum(x < -0.005 for x in v)
    return {
        "opened_n": len(all_values), "resolved_n": len(v), "unresolved_n": len(all_values) - len(v),
        "wins": wins, "losses": losses, "flat": len(v) - wins - losses,
        "win_rate_pct": round(100 * wins / len(v), 4) if v else "",
        "expectancy_net_usd": rnd(statistics.mean(v)) if v else "",
        "median_net_usd": rnd(statistics.median(v)) if v else "",
        "total_net_pnl_usd": rnd(sum(v)) if v else "",
        "best_net_usd": rnd(max(v)) if v else "", "worst_net_usd": rnd(min(v)) if v else "",
    }

def read_trades(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(f"missing parent replay CSV: {path}")
    with path.open(encoding="utf-8-sig", newline="") as h:
        rows = list(csv.DictReader(h))
    required = {
        "policy", "episode_id", "status", "long_qqq_qty", "short_spy_qty",
        "qqq_long_gross_pnl_usd", "spy_short_gross_pnl_usd", "net_pnl_usd",
        "qqq_entry_ask", "spy_entry_bid", "exit_qqq_bid", "exit_spy_ask",
        "qqq_contract_id", "spy_contract_id", "qqq_strike", "spy_strike",
        "base_slippage_per_share", "base_commission_per_contract_per_side",
    }
    if not rows:
        raise ValueError(f"empty parent replay CSV: {path}")
    missing = required - set(rows[0])
    if missing:
        raise ValueError(f"source schema missing columns: {sorted(missing)}")
    keys = [(r.get("policy"), r.get("episode_id")) for r in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate policy/episode key in input")
    if set(r.get("policy", "") for r in rows) != set(POLICIES):
        raise ValueError("source exit-policy set differs from frozen expected set")
    return rows

def gross_scaled(row: dict[str, Any], leg: str, n: int) -> float | None:
    if n < 1:
        raise ValueError("N must be positive")
    if row.get("status") != "RESOLVED":
        return None
    if leg == "QQQ_LONG_PUT":
        q, gross = inum(row.get("long_qqq_qty")), fnum(row.get("qqq_long_gross_pnl_usd"))
    elif leg == "SPY_SHORT_PUT":
        q, gross = inum(row.get("short_spy_qty")), fnum(row.get("spy_short_gross_pnl_usd"))
    else:
        raise ValueError(f"unknown leg {leg}")
    if not q or q < 1 or gross is None:
        return None
    return gross / q * n

def cost_params(row: dict[str, Any], scenario: dict[str, Any]) -> tuple[float, float]:
    if scenario["name"] == "BASE_COST":
        return (fnum(row.get("base_slippage_per_share")) or 0.0,
                fnum(row.get("base_commission_per_contract_per_side")) or 0.0)
    return float(scenario["slippage"]), float(scenario["commission"])

def leg_net(row: dict[str, Any], leg: str, n: int, scenario: dict[str, Any]) -> float | None:
    gross = gross_scaled(row, leg, n)
    if gross is None:
        return None
    slip, commission = cost_params(row, scenario)
    return gross - round_trip_cost(n, slip, commission)

def pair_net(row: dict[str, Any], qn: int, sn: int, scenario: dict[str, Any]) -> float | None:
    qg, sg = gross_scaled(row, "QQQ_LONG_PUT", qn), gross_scaled(row, "SPY_SHORT_PUT", sn)
    if qg is None or sg is None:
        return None
    slip, commission = cost_params(row, scenario)
    return qg + sg - round_trip_cost(qn, slip, commission) - round_trip_cost(sn, slip, commission)

def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    cols: list[str] = []
    for r in rows:
        for k in r:
            if k not in cols:
                cols.append(k)
    with path.open("w", encoding="utf-8", newline="") as h:
        w = csv.DictWriter(h, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

def base_leg_records(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    output, scenario = [], COSTS[1]
    for r in rows:
        for leg in LEGS:
            for n in FIXED_N:
                is_q = leg == "QQQ_LONG_PUT"
                base_n = inum(r.get("long_qqq_qty" if is_q else "short_spy_qty"))
                gross, net = gross_scaled(r, leg, n), leg_net(r, leg, n, scenario)
                slip, commission = cost_params(r, scenario)
                entry = fnum(r.get("qqq_entry_ask" if is_q else "spy_entry_bid"))
                exit_px = fnum(r.get("exit_qqq_bid" if is_q else "exit_spy_ask")) if r.get("status") == "RESOLVED" else None
                strike = fnum(r.get("qqq_strike" if is_q else "spy_strike"))
                prem = entry * MULTIPLIER * n if entry is not None else None
                assignment = strike * MULTIPLIER * n if (not is_q and strike is not None) else 0.0
                output.append({
                    "policy": r.get("policy"), "episode_id": r.get("episode_id"),
                    "signal_date": r.get("signal_date"), "entry_date": r.get("entry_date"),
                    "exit_date": r.get("exit_date"), "expiry": r.get("expiry"),
                    "leg": leg, "fixed_contracts": n, "status": r.get("status"),
                    "contract_id": r.get("qqq_contract_id" if is_q else "spy_contract_id"),
                    "strike": strike if strike is not None else "",
                    "entry_price": entry if entry is not None else "", "exit_price": exit_px if exit_px is not None else "",
                    "entry_premium_or_credit_usd": rnd(prem),
                    "spy_put_strike_assignment_obligation_usd": rnd(assignment),
                    "gross_pnl_usd": rnd(gross), "round_trip_cost_usd": rnd(round_trip_cost(n, slip, commission)),
                    "net_pnl_usd": rnd(net), "win": (net > 0.005) if net is not None else "",
                    "parent_dynamic_qty": base_n if base_n is not None else "",
                    "base_slippage_per_share_usd": slip, "base_commission_per_contract_per_side_usd": commission,
                    "quote_note": "Fixed-N quote-price counterfactual; displayed size not revalidated for hypothetical N.",
                })
    return output

def mean_field(rows: list[dict[str, Any]], field: str) -> float | None:
    vals = [fnum(r.get(field)) for r in rows]
    vals = [v for v in vals if v is not None]
    return statistics.mean(vals) if vals else None

def make_leg_summary(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for p in POLICIES:
        for leg in LEGS:
            for n in FIXED_N:
                subset = [r for r in records if r["policy"] == p and r["leg"] == leg and r["fixed_contracts"] == n]
                item = {"policy": p, "leg": leg, "fixed_contracts": n}
                item.update(stats([fnum(r.get("net_pnl_usd")) for r in subset]))
                item["mean_entry_premium_or_credit_usd"] = rnd(mean_field(subset, "entry_premium_or_credit_usd"))
                item["mean_spy_assignment_obligation_usd"] = rnd(mean_field(subset, "spy_put_strike_assignment_obligation_usd"))
                result.append(item)
    return result

def make_pair_summary(rows: list[dict[str, str]], cap: int) -> list[dict[str, Any]]:
    output, base_cost = [], COSTS[1]
    for p in POLICIES:
        subset = [r for r in rows if r.get("policy") == p]
        dynamic = {"comparison_kind": "DYNAMIC_PREMIUM_MATCHED_BASE", "policy": p,
                   "qqq_long_n": "VARIABLE", "spy_short_n": "VARIABLE", "total_contracts": "VARIABLE"}
        dynamic.update(stats([fnum(r.get("net_pnl_usd")) if r.get("status") == "RESOLVED" else None for r in subset]))
        dynamic["mean_qqq_premium_debit_usd"] = rnd(mean_field(subset, "qqq_long_premium_debit_usd"))
        dynamic["mean_spy_premium_credit_usd"] = rnd(mean_field(subset, "spy_short_premium_credit_usd"))
        dynamic["mean_abs_premium_mismatch_usd"] = rnd(mean_field(subset, "premium_mismatch_usd"))
        dynamic["mean_spy_assignment_obligation_usd"] = rnd(statistics.mean(
            (fnum(r.get("spy_strike")) or 0.0) * MULTIPLIER * (inum(r.get("short_spy_qty")) or 0) for r in subset
        )) if subset else ""
        output.append(dynamic)
        for qn, sn in valid_pairs(cap):
            item = {"comparison_kind": "FIXED_N_PAIR", "policy": p, "qqq_long_n": qn,
                    "spy_short_n": sn, "total_contracts": qn + sn}
            item.update(stats([pair_net(r, qn, sn, base_cost) for r in subset]))
            debits = [(fnum(r.get("qqq_entry_ask")) or 0.0) * MULTIPLIER * qn for r in subset]
            credits = [(fnum(r.get("spy_entry_bid")) or 0.0) * MULTIPLIER * sn for r in subset]
            item["mean_qqq_premium_debit_usd"] = rnd(statistics.mean(debits)) if debits else ""
            item["mean_spy_premium_credit_usd"] = rnd(statistics.mean(credits)) if credits else ""
            item["mean_abs_premium_mismatch_usd"] = rnd(statistics.mean(abs(a-b) for a,b in zip(debits, credits))) if debits else ""
            item["mean_spy_assignment_obligation_usd"] = rnd(statistics.mean(
                (fnum(r.get("spy_strike")) or 0.0) * MULTIPLIER * sn for r in subset
            )) if subset else ""
            output.append(item)
    return output

def make_cost_sensitivity(rows: list[dict[str, str]], cap: int) -> list[dict[str, Any]]:
    output = []
    for p in POLICIES:
        subset = [r for r in rows if r.get("policy") == p]
        for scenario in COSTS:
            for leg in LEGS:
                for n in FIXED_N:
                    item = {"policy": p, "comparison_kind": "STANDALONE_LEG", "leg": leg,
                            "qqq_long_n": n if leg == LEGS[0] else "", "spy_short_n": n if leg == LEGS[1] else "",
                            "cost_scenario": scenario["name"], "slippage_per_option_share_usd": scenario["slippage"],
                            "commission_per_contract_per_side_usd": scenario["commission"]}
                    item.update(stats([leg_net(r, leg, n, scenario) for r in subset]))
                    output.append(item)
            for qn, sn in valid_pairs(cap):
                item = {"policy": p, "comparison_kind": "FIXED_N_PAIR", "leg": "BOTH",
                        "qqq_long_n": qn, "spy_short_n": sn, "cost_scenario": scenario["name"],
                        "slippage_per_option_share_usd": scenario["slippage"],
                        "commission_per_contract_per_side_usd": scenario["commission"]}
                item.update(stats([pair_net(r, qn, sn, scenario) for r in subset]))
                output.append(item)
            dyn_vals = []
            for r in subset:
                if r.get("status") != "RESOLVED":
                    dyn_vals.append(None)
                    continue
                qn, sn = inum(r.get("long_qqq_qty")) or 0, inum(r.get("short_spy_qty")) or 0
                qg, sg = (gross_scaled(r, LEGS[0], qn) if qn else None), (gross_scaled(r, LEGS[1], sn) if sn else None)
                dyn_vals.append(None if qg is None or sg is None else qg + sg
                                - round_trip_cost(qn, scenario["slippage"], scenario["commission"])
                                - round_trip_cost(sn, scenario["slippage"], scenario["commission"]))
            item = {"policy": p, "comparison_kind": "DYNAMIC_PREMIUM_MATCHED_BASE", "leg": "BOTH",
                    "qqq_long_n": "VARIABLE", "spy_short_n": "VARIABLE", "cost_scenario": scenario["name"],
                    "slippage_per_option_share_usd": scenario["slippage"],
                    "commission_per_contract_per_side_usd": scenario["commission"]}
            item.update(stats(dyn_vals))
            output.append(item)
    return output

def render_summary(rows: list[dict[str, str]], legs: list[dict[str, Any]], pairs: list[dict[str, Any]], cap: int, input_path: Path) -> str:
    dates = sorted({r.get("signal_date", "") for r in rows if r.get("signal_date")})
    cohorts = {p: len({r.get("episode_id") for r in rows if r.get("policy") == p}) for p in POLICIES}
    lines = [
        "# Independent QQQ LONG PUT / SPY SHORT PUT Fixed-N Sweep V1", "",
        "**Completed post-analysis of committed EOD quote-side outputs; not actual fills or a new raw-option replay.**", "",
        f"- Input: {input_path.as_posix()}; input SHA-256 is recorded in source_manifest.json.",
        f"- Signal dates: {dates[0] if dates else '—'} through {dates[-1] if dates else '—'}; signal cohorts per exit policy: {cohorts}.",
        f"- Independently fixed N=1–6 per leg. Paired grid allows QQQ N + SPY N ≤ {cap}.",
        "- Contract IDs, entry dates, option entry quotes, and exit policies are held constant from the parent replay; no P&L-selected strikes.",
        "- Fixed-N gross P&L scales each leg's own recorded quote-side result by N / parent variable quantity; costs are recalculated for each hypothetical N.",
        "- Hypothetical fixed N is NOT re-gated against historical displayed bid/ask size. These are quote-price counterfactuals, not execution-verified sizes.",
        "- EOD quotes are not confirmed fills. Base costs: USD 0.05 per option share per side + USD 0.65 commission per contract per side. Sensitivity includes zero cost and USD 0.10/share slippage.",
        "- Resolved-only win rates/P&L; unresolved cases are counted separately. This is a sparse sample (44 signals), not a stable probability estimate.", "",
        "## Original dynamic premium-matched pair (reference)", "",
        "| Policy | Resolved/opened (unresolved) | Win rate | Mean net | Total net | Worst | Mean QQQ debit | Mean SPY credit | Mean abs mismatch | Mean SPY assignment obligation |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for p in POLICIES:
        r = next(x for x in pairs if x["policy"] == p and x["comparison_kind"] == "DYNAMIC_PREMIUM_MATCHED_BASE")
        lines.append(f"| {p} | {r['resolved_n']}/{r['opened_n']} ({r['unresolved_n']}) | {pct(r['win_rate_pct'])} | {fmt(r['expectancy_net_usd'])} | {fmt(r['total_net_pnl_usd'])} | {fmt(r['worst_net_usd'])} | {fmt(r['mean_qqq_premium_debit_usd'])} | {fmt(r['mean_spy_premium_credit_usd'])} | {fmt(r['mean_abs_premium_mismatch_usd'])} | {fmt(r['mean_spy_assignment_obligation_usd'])} |")
    lines += ["", "## Independent standalone legs (base costs)", ""]
    for p in POLICIES:
        lines += [f"### {p}", "",
                  "| Leg | N | Resolved/opened | Wins/losses/flat | Win rate | Mean net | Total net | Worst | Mean entry premium/credit | Mean SPY assignment obligation |",
                  "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for leg in LEGS:
            for n in FIXED_N:
                r = next(x for x in legs if x["policy"] == p and x["leg"] == leg and x["fixed_contracts"] == n)
                lines.append(f"| {leg} | {n} | {r['resolved_n']}/{r['opened_n']} ({r['unresolved_n']}) | {r['wins']}/{r['losses']}/{r['flat']} | {pct(r['win_rate_pct'])} | {fmt(r['expectancy_net_usd'])} | {fmt(r['total_net_pnl_usd'])} | {fmt(r['worst_net_usd'])} | {fmt(r['mean_entry_premium_or_credit_usd'])} | {fmt(r['mean_spy_assignment_obligation_usd'])} |")
        lines.append("")
    lines += ["## Paired fixed-N matrix: mean net P&L per resolved cohort (base costs)", ""]
    for p in POLICIES:
        lines += [f"### {p}", "",
                  "| QQQ LONG N / SPY SHORT N | 1 | 2 | 3 | 4 | 5 | 6 |",
                  "|---:|---:|---:|---:|---:|---:|---:|"]
        for qn in FIXED_N:
            cells = []
            for sn in FIXED_N:
                if qn + sn > cap:
                    cells.append("—")
                else:
                    r = next(x for x in pairs if x["policy"] == p and x["comparison_kind"] == "FIXED_N_PAIR" and x["qqq_long_n"] == qn and x["spy_short_n"] == sn)
                    cells.append(fmt(r["expectancy_net_usd"]))
            lines.append(f"| {qn} | " + " | ".join(cells) + " |")
        lines.append("")
    lines += [
        "## Risk / execution guardrails", "",
        "- QQQ LONG PUT expiry loss is limited to premium paid before costs, but interim liquidation and fills are not guaranteed.",
        "- SPY SHORT PUT premium credit does not cap loss; its strike-based assignment obligation is reported separately and can be much larger than the credit.",
        "- Equal premium is not equal Delta, notional, margin, assignment obligation, or tail risk. Fixed N changes exposure and cash flow together.",
        "- Standalone results keep each selected contract fixed to isolate leg contribution. They are not a separate strategy that reselects strikes for only one ETF.",
        "- No app sizing changes, broker connections, or live orders are authorized by this analysis.", "",
        "Files: independent_leg_trade_episodes.csv, independent_leg_sizing_summary.csv, independent_leg_pair_matrix.csv, cost_sensitivity.csv, source_manifest.json.", ""
    ]
    return "\n".join(lines)

def run(input_path: Path, out: Path, cap: int = 9) -> dict[str, Any]:
    rows = read_trades(input_path)
    leg_records = base_leg_records(rows)
    legs = make_leg_summary(leg_records)
    pairs = make_pair_summary(rows, cap)
    costs = make_cost_sensitivity(rows, cap)
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "independent_leg_trade_episodes.csv", leg_records)
    write_csv(out / "independent_leg_sizing_summary.csv", legs)
    write_csv(out / "independent_leg_pair_matrix.csv", pairs)
    write_csv(out / "cost_sensitivity.csv", costs)
    manifest = {
        "study": "independent_qqq_long_put_spy_short_put_fixed_n_sweep_v1",
        "input_path": input_path.as_posix(), "input_sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(),
        "input_rows": len(rows),
        "signal_cohorts_by_policy": {p: len({r.get("episode_id") for r in rows if r.get("policy") == p}) for p in POLICIES},
        "exit_policies": list(POLICIES), "fixed_standalone_N": list(FIXED_N),
        "paired_combined_contract_cap": cap, "paired_combinations_per_policy": len(valid_pairs(cap)),
        "cost_scenarios": COSTS, "multiplier": MULTIPLIER,
        "pnl_formula": "parent leg gross P&L / parent variable quantity * fixed N; recompute round-trip costs",
        "quotes": {"QQQ_LONG_PUT": "enter Ask / exit Bid", "SPY_SHORT_PUT": "enter Bid / exit Ask"},
        "fixed_N_depth_gate": "not rechecked for hypothetical N; quote-price counterfactual, not execution-verified",
        "unresolved_handling": "preserve source unresolved statuses; exclude unresolved P&L from expectancy but report count",
        "source_caution": "SHA/byte-pinned mirror proves file identity, not OPRA/exchange authenticity or actual fills",
    }
    (out / "source_manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (out / "summary.md").write_text(render_summary(rows, legs, pairs, cap, input_path), encoding="utf-8")
    return manifest

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("research/qqq_spy_put_equal_premium_v1/results/latest/trade_episodes.csv"))
    parser.add_argument("--out", type=Path, default=Path("research/qqq_spy_put_independent_leg_n_sweep_v1/results/latest"))
    parser.add_argument("--max-total-contracts", type=int, default=9)
    args = parser.parse_args()
    print(json.dumps({"status": "COMPLETED", **run(args.input, args.out, args.max_total_contracts)}, indent=2))

if __name__ == "__main__":
    main()
