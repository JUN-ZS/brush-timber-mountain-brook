#!/usr/bin/env python3
"""Summarize realized no-hedge vs SPY far-tail hedge P&L by exit calendar year."""
from __future__ import annotations
import argparse
import csv
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

TRUE = {"1", "true", "yes", "y"}
KEY = ("arm", "phase", "pnl_year", "policy", "tail_label", "tail_quantity")


def fnum(value: Any) -> float | None:
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (TypeError, ValueError):
        return None


def truth(value: Any) -> bool:
    return str(value).strip().lower() in TRUE


def pct(n: int, d: int) -> float | None:
    return round(100.0 * n / d, 2) if d else None


def stats(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        return {"n": 0, "sum": None, "mean": None, "median": None,
                "win_pct": None, "worst": None, "best": None, "loss_n": 0}
    return {
        "n": len(values),
        "sum": round(sum(values), 2),
        "mean": round(statistics.mean(values), 2),
        "median": round(statistics.median(values), 2),
        "win_pct": round(100.0 * sum(v > 0.005 for v in values) / len(values), 2),
        "worst": round(min(values), 2),
        "best": round(max(values), 2),
        "loss_n": sum(v < -0.005 for v in values),
    }


def build_annual_rows(source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Deduplicate tail/quantity copies before calculating the no-hedge all-resolved baseline.
    base_by_trade: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    paired_by_key: dict[tuple[str, int, int, str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in source_rows:
        exit_date = str(row.get("exit_date") or "").strip()
        base_pnl = fnum(row.get("base_net_pnl_usd"))
        if not exit_date or len(exit_date) < 4 or base_pnl is None:
            continue
        identity = (str(row.get("arm", "")), str(row.get("phase", "")),
                    str(row.get("episode_id", "")), str(row.get("policy", "")))
        base_entry = {"arm": identity[0], "phase": int(identity[1]),
                      "episode_id": identity[2], "policy": identity[3],
                      "pnl_year": int(exit_date[:4]), "base_pnl": base_pnl}
        previous = base_by_trade.get(identity)
        if previous and (previous["base_pnl"] != base_pnl or previous["pnl_year"] != base_entry["pnl_year"]):
            raise ValueError(f"inconsistent duplicated baseline trade: {identity}")
        base_by_trade[identity] = base_entry
        tail_pnl = fnum(row.get("tail_net_pnl_usd"))
        hedged_pnl = fnum(row.get("hedged_net_pnl_usd"))
        if truth(row.get("paired_realized_comparison")) and tail_pnl is not None and hedged_pnl is not None:
            key = (identity[0], int(identity[1]), int(exit_date[:4]), identity[3],
                   str(row.get("tail_label", "")), int(row.get("tail_quantity") or 0))
            item = dict(row)
            item["_base_pnl"] = base_pnl
            item["_tail_pnl"] = tail_pnl
            item["_hedged_pnl"] = hedged_pnl
            paired_by_key[key].append(item)

    baseline_by_key: dict[tuple[str, int, int, str], list[float]] = defaultdict(list)
    for row in base_by_trade.values():
        baseline_by_key[(row["arm"], row["phase"], row["pnl_year"], row["policy"])].append(row["base_pnl"])

    result = []
    keys = sorted(paired_by_key)
    for arm, phase, year, policy, label, qty in keys:
        paired = paired_by_key[(arm, phase, year, policy, label, qty)]
        baseline_all = baseline_by_key[(arm, phase, year, policy)]
        base_values = [float(r["_base_pnl"]) for r in paired]
        hedge_values = [float(r["_hedged_pnl"]) for r in paired]
        tail_values = [float(r["_tail_pnl"]) for r in paired]
        all_s = stats(baseline_all)
        paired_base_s, hedged_s, tail_s = stats(base_values), stats(hedge_values), stats(tail_values)
        improved = sum(h > b + 0.005 for b, h in zip(base_values, hedge_values))
        turned_positive = sum(b < -0.005 and h > 0.005 for b, h in zip(base_values, hedge_values))
        result.append({
            "arm": arm, "phase": phase, "pnl_year_exit_date": year, "policy": policy,
            "tail_label": label, "tail_target_abs_delta": {"TAIL_025_DELTA": 0.025, "TAIL_05_DELTA": 0.05,
                                                             "TAIL_10_DELTA": 0.10}.get(label),
            "tail_quantity": qty,
            "base_resolved_n_all": all_s["n"],
            "no_hedge_mean_all_resolved_usd": all_s["mean"],
            "no_hedge_median_all_resolved_usd": all_s["median"],
            "no_hedge_win_rate_all_resolved_pct": all_s["win_pct"],
            "no_hedge_worst_all_resolved_usd": all_s["worst"],
            "paired_n": paired_base_s["n"],
            "paired_coverage_pct_of_base_resolved": pct(int(paired_base_s["n"]), int(all_s["n"])),
            "no_hedge_mean_paired_usd": paired_base_s["mean"],
            "no_hedge_median_paired_usd": paired_base_s["median"],
            "no_hedge_win_rate_paired_pct": paired_base_s["win_pct"],
            "no_hedge_worst_paired_usd": paired_base_s["worst"],
            "hedged_mean_paired_usd": hedged_s["mean"],
            "hedged_median_paired_usd": hedged_s["median"],
            "hedged_win_rate_paired_pct": hedged_s["win_pct"],
            "hedged_worst_paired_usd": hedged_s["worst"],
            "mean_incremental_hedge_usd": round(statistics.mean(h - b for b, h in zip(base_values, hedge_values)), 2),
            "mean_tail_net_pnl_usd": tail_s["mean"],
            "paired_no_hedge_sum_usd": paired_base_s["sum"],
            "paired_hedged_sum_usd": hedged_s["sum"],
            "paired_sum_increment_usd": round(sum(hedge_values) - sum(base_values), 2),
            "paired_baseline_losses_improved_n": improved,
            "paired_baseline_losses_turned_positive_n": turned_positive,
        })
    return result


def build_robustness(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Each phase is a shifted entry schedule; summarize phase ranges/medians, never pool as independent samples.
    buckets: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (row["arm"], row["pnl_year_exit_date"], row["policy"], row["tail_label"], row["tail_quantity"])
        buckets[key].append(row)
    numeric_fields = (
        "no_hedge_mean_all_resolved_usd", "no_hedge_mean_paired_usd", "hedged_mean_paired_usd",
        "mean_incremental_hedge_usd", "no_hedge_worst_paired_usd", "hedged_worst_paired_usd",
        "paired_coverage_pct_of_base_resolved",
    )
    output = []
    for key, items in sorted(buckets.items()):
        arm, year, policy, label, qty = key
        entry = {"arm": arm, "pnl_year_exit_date": year, "policy": policy,
                 "tail_label": label, "tail_quantity": qty, "phase_count": len(items),
                 "paired_n_min": min(int(r["paired_n"]) for r in items),
                 "paired_n_max": max(int(r["paired_n"]) for r in items)}
        for field in numeric_fields:
            vals = [float(r[field]) for r in items if r.get(field) not in ("", None)]
            prefix = field.replace("_usd", "").replace("_pct_of_base_resolved", "")
            entry[prefix + "_phase_min"] = round(min(vals), 2) if vals else None
            entry[prefix + "_phase_median"] = round(statistics.median(vals), 2) if vals else None
            entry[prefix + "_phase_max"] = round(max(vals), 2) if vals else None
        output.append(entry)
    return output


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty results: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(key for row in rows for key in row.keys()))
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_report(path: Path, annual: list[dict[str, Any]], robustness: list[dict[str, Any]]) -> None:
    lines = [
        "# SPY Far-Tail Hedge — Annual Realized P&L Comparison",
        "",
        "## Reading this report",
        "",
        "- Calendar year is assigned by the base trade's realized exit date; unresolved trades without a realized exit are not counted as realized P&L.",
        "- Primary comparison is **no-hedge vs hedged mean P&L on the exact same paired trades** with eligible entry and sufficient exit displayed size. All-resolved no-hedge mean is shown separately as context because hedge quote coverage is not 100%.",
        "- P&L amounts are USD per trade episode, net of the frozen baseline costs and modeled hedge round-trip costs. EOD quotes and displayed sizes are not verified fills.",
        "- The five phases are shifted entry schedules that overlap; they are robustness checks, not independent samples. The robustness table shows phase min/median/max rather than pooling trades across phases.",
        "- Summed episode P&L is not account-level annual profit or annual return: this replay does not model a shared NAV, concurrent-position capital allocation, margin, or forced liquidation.",
        "",
        "## Year-by-year robustness ranges (USD per trade episode)",
        "",
        "| Exit year | Arm | Policy | Tail | Qty | Paired N range | No-hedge mean range | Hedged mean range | Incremental mean range | Worst no-hedge range | Worst hedged range |",
        "|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in robustness:
        if r["tail_label"] not in ("TAIL_025_DELTA", "TAIL_05_DELTA"):
            continue
        def fmt(v):
            return "—" if v is None else f"{float(v):,.2f}"
        lines.append(
            f"| {r['pnl_year_exit_date']} | {r['arm']} | {r['policy']} | {r['tail_label']} | {r['tail_quantity']} "
            f"| {r['paired_n_min']}–{r['paired_n_max']} "
            f"| {fmt(r.get('no_hedge_mean_paired_phase_min'))}–{fmt(r.get('no_hedge_mean_paired_phase_max'))} "
            f"| {fmt(r.get('hedged_mean_paired_phase_min'))}–{fmt(r.get('hedged_mean_paired_phase_max'))} "
            f"| {fmt(r.get('mean_incremental_hedge_phase_min'))}–{fmt(r.get('mean_incremental_hedge_phase_max'))} "
            f"| {fmt(r.get('no_hedge_worst_paired_phase_min'))}–{fmt(r.get('no_hedge_worst_paired_phase_max'))} "
            f"| {fmt(r.get('hedged_worst_paired_phase_min'))}–{fmt(r.get('hedged_worst_paired_phase_max'))} |"
        )
    lines += ["", "## All phase-level yearly values", "",
              "See annual_pnl_by_phase.csv for each phase, entry policy, Delta target, quantity, sample size, paired means, win rate and worst trade.",
              "",
              "## Source and scope", "",
              "Frozen base anchor: c0cc1de3f196a312c00582d9ee9600c689c388d9. This summary reads the completed source-pinned hedge ledger; it does not rerun or alter strategy entries/exits.",
              ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    with args.input.open("r", encoding="utf-8", newline="") as f:
        source_rows = list(csv.DictReader(f))
    if not source_rows:
        raise ValueError("trade-level ledger is empty")
    annual = build_annual_rows(source_rows)
    if not annual:
        raise ValueError("no realized/paired annual observations found")
    robustness = build_robustness(annual)
    write_csv(args.out / "annual_pnl_by_phase.csv", annual)
    write_csv(args.out / "annual_pnl_robustness.csv", robustness)
    write_report(args.out / "annual_pnl_report.md", annual, robustness)
    print({"status": "COMPLETED", "source_rows": len(source_rows), "annual_rows": len(annual),
           "robustness_rows": len(robustness), "exit_years": sorted({r["pnl_year_exit_date"] for r in annual})})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
