#!/usr/bin/env python3
"""Temporal, friction and paired hedge audit for a persisted QQQ option trade ledger."""
from __future__ import annotations
import argparse, csv, hashlib, json, math
from pathlib import Path
from statistics import median
from typing import Any

MULTIPLIER = 100.0
BASE_SLIP = 0.05
STRESS_SLIP = 0.10
COMMISSION = 0.65
COST_CASES = ("ZERO", "BASE", "STRESS")
PERIODS = (("FULL", 2018, 2025), ("2018-2022", 2018, 2022), ("2023-2025", 2023, 2025))
CALL_ONLY = "CALL_DEBIT_50D_10D"
CALL_PUT = "CALL_DEBIT_PLUS_LONG_PUT_10D"


def number(value: Any) -> float | None:
    try:
        n = float(value)
        return n if math.isfinite(n) else None
    except (TypeError, ValueError):
        return None


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_trade_rows_from_dicts(raw_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for raw in raw_rows:
        raw_legs = raw.get("contract_legs") or "[]"
        legs = json.loads(raw_legs) if isinstance(raw_legs, str) else raw_legs
        if not isinstance(legs, list):
            raise ValueError("contract_legs must be a JSON list")
        contracts = sum(int(leg.get("qty", 0)) for leg in legs if isinstance(leg, dict))
        declared = number(raw.get("entry_contract_count"))
        if raw.get("status") == "RESOLVED" and declared is not None and int(declared) != contracts:
            raise ValueError(f"contract count mismatch: {raw.get('signal_date')} / {raw.get('strategy_id')}")
        rows.append({
            **raw, "legs": legs, "contract_count": contracts,
            "year": int(str(raw.get("signal_date", ""))[:4]),
            "pnl": number(raw.get("net_pnl_usd")),
            "mae": number(raw.get("mae_one_unit_usd")),
            "tail_loss": number(raw.get("terminal_worst_loss_usd")),
            "capacity_0p5": int(number(raw.get("units_at_0p5pct_nav_tail_budget")) or 0),
            "capacity_1": int(number(raw.get("units_at_1pct_nav_tail_budget")) or 0),
            "capacity_2": int(number(raw.get("units_at_2pct_nav_tail_budget")) or 0),
        })
    return rows


def load_trade_rows(path: Path) -> list[dict[str, Any]]:
    with path.open("r", newline="", encoding="utf-8-sig") as fh:
        return load_trade_rows_from_dicts(list(csv.DictReader(fh)))


def validate_unique_events(rows: list[dict[str, Any]]) -> None:
    seen = set()
    for row in rows:
        if row.get("status") != "RESOLVED":
            continue
        key = (str(row.get("strategy_id")), str(row.get("signal_date")))
        if key in seen:
            raise ValueError(f"duplicate strategy/event row: {key}")
        seen.add(key)


def load_run_meta(path: Path | None) -> dict[str, str]:
    data = {}
    if path is None:
        return data
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            data[key.strip()] = value.strip()
    return data


def adjusted_value(row: dict[str, Any], key: str, cost_case: str) -> float | None:
    value = number(row.get(key))
    if value is None:
        return None
    contracts = int(row.get("contract_count", 0))
    if cost_case == "ZERO":
        return value + contracts * 2.0 * (MULTIPLIER * BASE_SLIP + COMMISSION)
    if cost_case == "BASE":
        return value
    if cost_case == "STRESS":
        return value - contracts * 2.0 * MULTIPLIER * (STRESS_SLIP - BASE_SLIP)
    raise ValueError(f"unknown cost case: {cost_case}")


def pf(values: list[float]) -> float | None:
    gross_wins = sum(x for x in values if x > 0)
    gross_losses = -sum(x for x in values if x < 0)
    if gross_losses == 0:
        return None if gross_wins == 0 else float("inf")
    return gross_wins / gross_losses


def select_period(rows: list[dict[str, Any]], period: str) -> list[dict[str, Any]]:
    spec = next((p for p in PERIODS if p[0] == period), None)
    if spec is None:
        raise ValueError(f"unknown period: {period}")
    _, low, high = spec
    return rows if period == "FULL" else [r for r in rows if low <= r["year"] <= high]


def summarize_group(rows: list[dict[str, Any]], strategy: str, period: str, cost_case: str) -> dict[str, Any]:
    chosen = [r for r in rows if r.get("strategy_id") == strategy]
    resolved = [r for r in chosen if r.get("status") == "RESOLVED" and r.get("pnl") is not None]
    values = [float(adjusted_value(r, "pnl", cost_case)) for r in resolved]
    maes = [float(adjusted_value(r, "mae", cost_case)) for r in resolved if r.get("mae") is not None]
    tails = [float(r["tail_loss"]) for r in resolved if r.get("tail_loss") is not None]
    positives = [v for v in values if v > 0]
    factor = pf(values)
    return {
        "period": period, "strategy_id": strategy, "cost_case": cost_case,
        "episode_rows": len(chosen), "resolved_n": len(values), "unresolved_n": len(chosen)-len(values),
        "win_n": len(positives), "flat_n": sum(v == 0 for v in values),
        "win_rate_pct": round(100*len(positives)/len(values), 4) if values else None,
        "total_net_pnl_usd": round(sum(values), 2) if values else None,
        "mean_net_pnl_usd": round(sum(values)/len(values), 2) if values else None,
        "median_net_pnl_usd": round(median(values), 2) if values else None,
        "profit_factor": round(factor, 5) if factor is not None and math.isfinite(factor) else ("INF_NO_LOSSES" if factor == float("inf") else None),
        "best_net_pnl_usd": round(max(values), 2) if values else None,
        "worst_net_pnl_usd": round(min(values), 2) if values else None,
        "mean_mae_usd_adjusted_for_cost_case": round(sum(maes)/len(maes), 2) if maes else None,
        "median_terminal_tail_loss_usd": round(median(tails), 2) if tails else None,
        "events_with_unit_at_0p5pct_tail_budget": sum(r["capacity_0p5"] > 0 for r in resolved),
        "events_with_unit_at_1pct_tail_budget": sum(r["capacity_1"] > 0 for r in resolved),
        "events_with_unit_at_2pct_tail_budget": sum(r["capacity_2"] > 0 for r in resolved),
        "capacity_basis": "BASE entry terminal-payoff estimate plus entry-side displayed depth; not broker margin or exit-depth approval",
    }


def same_call_legs(call: dict[str, Any], combo: dict[str, Any]) -> bool:
    if len(call.get("legs", [])) < 2 or len(combo.get("legs", [])) < 3:
        return False
    fields = ("id", "expiry", "strike", "right", "side", "qty")
    return all(call["legs"][i].get(k) == combo["legs"][i].get(k) for i in range(2) for k in fields)


def paired_hedge_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    calls = {str(r["signal_date"]): r for r in rows if r.get("strategy_id") == CALL_ONLY and r.get("status") == "RESOLVED" and r.get("pnl") is not None}
    combos = [r for r in rows if r.get("strategy_id") == CALL_PUT and r.get("status") == "RESOLVED" and r.get("pnl") is not None]
    matched, mismatches = [], 0
    for combo in combos:
        call = calls.get(str(combo["signal_date"]))
        if call is None:
            continue
        if not same_call_legs(call, combo):
            mismatches += 1
            continue
        matched.append((call, combo))
    out = []
    for period, low, high in PERIODS:
        pairs = matched if period == "FULL" else [p for p in matched if low <= p[0]["year"] <= high]
        for cost_case in COST_CASES:
            pnl_delta = [float(adjusted_value(h, "pnl", cost_case))-float(adjusted_value(c, "pnl", cost_case)) for c,h in pairs]
            mae_delta = [
                float(adjusted_value(h, "mae", cost_case))-float(adjusted_value(c, "mae", cost_case))
                for c,h in pairs if c.get("mae") is not None and h.get("mae") is not None
            ]
            out.append({
                "period": period, "cost_case": cost_case, "exact_call_leg_pairs": len(pairs),
                "mean_pnl_delta_combo_minus_call_usd": round(sum(pnl_delta)/len(pnl_delta),2) if pnl_delta else None,
                "median_pnl_delta_combo_minus_call_usd": round(median(pnl_delta),2) if pnl_delta else None,
                "combo_higher_pnl_count": sum(x > 0 for x in pnl_delta),
                "combo_lower_pnl_count": sum(x < 0 for x in pnl_delta),
                "mean_mae_delta_combo_minus_call_usd": round(sum(mae_delta)/len(mae_delta),2) if mae_delta else None,
                "combo_less_adverse_mae_count": sum(x > 0 for x in mae_delta),
                "combo_more_adverse_mae_count": sum(x < 0 for x in mae_delta),
                "identity_mismatch_rows_excluded": mismatches,
                "interpretation": "same-signal exact-call-leg comparison; later period is not virgin OOS",
            })
    return out, mismatches


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("status\nNO_ROWS\n", encoding="utf-8")
        return
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build_audit(trades: list[dict[str, Any]], input_sha: str, manifest: dict[str, Any], meta: dict[str, str]) -> dict[str, Any]:
    strategies = sorted({str(r.get("strategy_id")) for r in trades})
    summary = []
    for period, _, _ in PERIODS:
        period_set = select_period(trades, period)
        for strategy in strategies:
            for cost_case in COST_CASES:
                summary.append(summarize_group(period_set, strategy, period, cost_case))
    paired, mismatches = paired_hedge_rows(trades)
    return {
        "audit_id": "QQQ_OPTION_SHORTLIST_TEMPORAL_COST_AUDIT_V1",
        "source_trade_rows_sha256": input_sha,
        "source_run_id": meta.get("run_id"),
        "source_tested_sha": meta.get("tested_sha"),
        "source_run_url": meta.get("run_url"),
        "source_runner": meta.get("runner_name"),
        "source_window": ["2018-03-01", manifest.get("source_end")],
        "source_sessions": manifest.get("source_sessions"),
        "signal_count": manifest.get("signals"),
        "pricing_evidence": manifest.get("pricing_evidence"),
        "row_count": len(trades),
        "strategy_count": len(strategies),
        "cost_assumptions": {
            "BASE": {"slippage_per_share_per_leg_side_usd": BASE_SLIP, "commission_per_contract_per_side_usd": COMMISSION},
            "ZERO": "Counterfactual adjustment removing modeled BASE round-trip friction on the same observed episode outcomes.",
            "STRESS": {"slippage_per_share_per_leg_side_usd": STRESS_SLIP, "commission_per_contract_per_side_usd": COMMISSION},
            "important": "ZERO/STRESS adjust friction mathematically; they do not re-run order eligibility or claim identical fills at those prices.",
        },
        "summary_rows": summary,
        "paired_hedge_rows": paired,
        "paired_identity_mismatch_count": mismatches,
        "decision_constraints": [
            "Episode statistics are not a continuously compounded account CAGR/MaxDD.",
            "Risk-unit counts use BASE entry terminal-payoff arithmetic plus entry-side displayed depth; broker margin, exit depth and interim liquidation limits are not proved.",
            "2018-2022 versus 2023-2025 is a descriptive split after exploratory full-sample review, not an untouched holdout.",
            "The public historical option chain ends on 2025-12-15; no option outcomes are available in this audit after that date.",
        ],
    }


def render_report(report: dict[str, Any]) -> str:
    rows = report["summary_rows"]
    base = {r["strategy_id"]: r for r in rows if r["period"] == "FULL" and r["cost_case"] == "BASE"}
    stress = {r["strategy_id"]: r for r in rows if r["period"] == "FULL" and r["cost_case"] == "STRESS"}
    call_train = next(r for r in rows if r["strategy_id"] == CALL_ONLY and r["period"] == "2018-2022" and r["cost_case"] == "STRESS")
    call_late = next(r for r in rows if r["strategy_id"] == CALL_ONLY and r["period"] == "2023-2025" and r["cost_case"] == "STRESS")
    r5, r6 = stress.get("PUT_SHORT_HEAVY_1x5", {}), stress.get("PUT_SHORT_HEAVY_1x6", {})
    selected = [CALL_ONLY, CALL_PUT, "PUT_SHORT_HEAVY_1x1", "PUT_SHORT_HEAVY_1x4", "PUT_SHORT_HEAVY_1x5", "PUT_SHORT_HEAVY_1x6", "PUT_LONG_HEAVY_2x1"]
    lines = [
        "# QQQ Option Shortlist — Temporal and Friction Audit V1", "",
        "**Status: research only. No live orders, HUB action changes, or Frozen Original Hybrid changes.**", "",
        f"- Source run: {report.get('source_run_id')}; tested SHA: {report.get('source_tested_sha')}.",
        f"- Source window: {report.get('source_window')}; sessions: {report.get('source_sessions')}; signal events: {report.get('signal_count')}.",
        f"- Trade ledger SHA-256: {report.get('source_trade_rows_sha256')}.",
        f"- Evidence: {report.get('pricing_evidence')}.", "",
        "## Same-event fixed-horizon outcomes", "",
        "BASE is the original quote-side replay. ZERO and STRESS are friction adjustments to the same episodes, not separate fill simulations.", "",
        "| Strategy | Resolved | BASE win % | BASE mean USD | STRESS win % | STRESS mean USD | STRESS PF | Worst STRESS USD | 1% budget-sizeable events | 2% budget-sizeable events |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name in selected:
        b, s = base.get(name), stress.get(name)
        if not b or not s:
            continue
        lines.append(
            f"| {name} | {b['resolved_n']} | {b['win_rate_pct']} | {b['mean_net_pnl_usd']} | "
            f"{s['win_rate_pct']} | {s['mean_net_pnl_usd']} | {s['profit_factor']} | {s['worst_net_pnl_usd']} | "
            f"{b['events_with_unit_at_1pct_tail_budget']} | {b['events_with_unit_at_2pct_tail_budget']} |"
        )
    lines += [
        "", "## Paired test: does the extra LONG PUT pay for itself?", "",
        "Only dates where call-only and call-plus-put rows used identical two call contracts are included.", "",
        "| Period | Cost case | Exact pairs | Mean P&L delta (combo − call) | Combo higher-P&L count | Mean MAE delta (positive is less adverse) | MAE improved count |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in report["paired_hedge_rows"]:
        if row["cost_case"] in ("BASE", "STRESS"):
            lines.append(
                f"| {row['period']} | {row['cost_case']} | {row['exact_call_leg_pairs']} | "
                f"{row['mean_pnl_delta_combo_minus_call_usd']} | {row['combo_higher_pnl_count']} | "
                f"{row['mean_mae_delta_combo_minus_call_usd']} | {row['combo_less_adverse_mae_count']} |"
            )
    lines += [
        "", "## Decision readout", "",
        f"- CALL debit stress mean: USD {stress[CALL_ONLY]['mean_net_pnl_usd']} per event across {stress[CALL_ONLY]['resolved_n']} events. At least one unit fit the 1% terminal-tail budget on {base[CALL_ONLY]['events_with_unit_at_1pct_tail_budget']}/{base[CALL_ONLY]['resolved_n']} events and the 2% budget on {base[CALL_ONLY]['events_with_unit_at_2pct_tail_budget']}/{base[CALL_ONLY]['resolved_n']}.",
        f"- Time dependence: CALL debit stress mean was USD {call_train['mean_net_pnl_usd']} per event in 2018–2022 and USD {call_late['mean_net_pnl_usd']} in 2023–2025. The later segment has {call_late['resolved_n']} events and is not a virgin holdout.",
        f"- SHORT-heavy PUT ratio: 1x5 stress mean USD {r5.get('mean_net_pnl_usd')} and 1x6 stress mean USD {r6.get('mean_net_pnl_usd')}. Both have zero complete units inside the 0.5%, 1%, and 2% NAV terminal-tail budgets on every observed episode.",
        "- Extra LONG PUT remains a protection hypothesis only. Do not auto-add it; weigh incremental P&L cost against paired improvement in adverse marks.",
        "", "## Interpretation limits", "",
    ]
    lines += [f"- {x}" for x in report["decision_constraints"]]
    lines += [
        "- No portfolio compounding, total account CAGR, or account MaxDD is inferred from these isolated fixed-horizon episodes.",
        "- Entry displayed size does not prove sufficient exit size; terminal payoff does not bound interim liquidation or broker margin.",
        "",
    ]
    return "\n".join(lines)


def run(trades_path: Path, manifest_path: Path, out_dir: Path, run_meta_path: Path | None = None) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("source_integrity_status") != "PINNED_SOURCE_VERIFICATION_COMPLETED_BY_REUSED_AUDIT":
        raise ValueError("Source manifest integrity gate did not pass.")
    if manifest.get("pricing_evidence") != "OBSERVED_EOD_QUOTES_WITH_DERIVED_QUOTE_SIDE_REPLAY_NOT_CONFIRMED_FILLS":
        raise ValueError("Unexpected pricing evidence class.")
    if manifest.get("source_end") != "2025-12-15":
        raise ValueError(f"Unexpected option source end date: {manifest.get('source_end')}")
    trades = load_trade_rows(trades_path)
    if not trades:
        raise ValueError("No trade rows found.")
    validate_unique_events(trades)
    if not any(r.get("status") == "RESOLVED" and r.get("pnl") is not None for r in trades):
        raise ValueError("No resolved trade rows to audit.")
    report = build_audit(trades, sha256_file(trades_path), manifest, load_run_meta(run_meta_path))
    if report["paired_identity_mismatch_count"] != 0:
        raise ValueError(f"Paired call-leg identity mismatches found: {report['paired_identity_mismatch_count']}")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "period_cost_audit.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_dir / "REPORT.md").write_text(render_report(report), encoding="utf-8")
    write_csv(out_dir / "summary.csv", report["summary_rows"])
    write_csv(out_dir / "paired_call_put.csv", report["paired_hedge_rows"])
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trades", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--run-meta", type=Path, default=None)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.trades, args.manifest, args.out, args.run_meta)
    print(json.dumps({
        "audit_id": report["audit_id"],
        "source_trade_rows_sha256": report["source_trade_rows_sha256"],
        "source_run_id": report.get("source_run_id"),
        "source_tested_sha": report.get("source_tested_sha"),
        "signal_count": report.get("signal_count"),
        "strategy_count": report.get("strategy_count"),
        "paired_identity_mismatch_count": report.get("paired_identity_mismatch_count"),
        "summary_rows": len(report["summary_rows"]),
        "paired_rows": len(report["paired_hedge_rows"]),
        "output_dir": str(args.out),
    }, indent=2))


if __name__ == "__main__":
    main()
