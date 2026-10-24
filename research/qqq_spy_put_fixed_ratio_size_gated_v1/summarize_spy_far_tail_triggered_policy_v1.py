#!/usr/bin/env python3
"""Re-summarize the committed triggered trade ledger as a whole-policy evaluation."""
from __future__ import annotations
import argparse, csv, statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

TRIGGERS = ("ENTRY_SPOT_DRAWDOWN_3PCT", "ENTRY_SPOT_DRAWDOWN_5PCT")
TAILS = ("TAIL_025_DELTA", "TAIL_05_DELTA")
QTY = (1, 3)
TAIL_TEXT = {"TAIL_025_DELTA": "2.5-delta (~−0.025)", "TAIL_05_DELTA": "5-delta (~−0.05)"}
POLICY_TEXT = {"HOLD_10_OR_DTE_LE_7": "Hold 10 / DTE≤7", "HOLD_20_OR_DTE_LE_7": "Hold 20 / DTE≤7"}


def number(row: dict[str, Any], key: str) -> float | None:
    try:
        value = float(row.get(key, ""))
        return value if value == value and abs(value) != float("inf") else None
    except (TypeError, ValueError):
        return None


def yes(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def median(values: Iterable[float | int | None]) -> float | None:
    cleaned = [float(v) for v in values if v is not None]
    return statistics.median(cleaned) if cleaned else None


def range_of(values: Iterable[float | int | None]) -> tuple[float | None, float | None]:
    cleaned = [float(v) for v in values if v is not None]
    return (min(cleaned), max(cleaned)) if cleaned else (None, None)


def money(value: float | int | None) -> str:
    if value is None:
        return "—"
    n = float(value)
    return ("−$" if n < 0 else "$") + f"{abs(n):,.2f}"


def range_text(a: float | int | None, b: float | int | None) -> str:
    return "—" if a is None or b is None else f"{a:g}–{b:g}"


def csv_read(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"empty or missing source file: {path}")
    return rows


def csv_write(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"refusing empty output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fields, seen = [], set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def policy_row_metrics(rows: list[dict[str, str]]) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Keep untriggered/blocked trades at base P&L; exclude entered but unpriced hedges."""
    resolved = [r for r in rows if number(r, "base_net_pnl_usd") is not None]
    unresolved = [r for r in rows if number(r, "base_net_pnl_usd") is None]
    all_base = [float(number(r, "base_net_pnl_usd")) for r in resolved]
    signal_rows = [r for r in resolved if yes(r.get("trigger_fired"))]
    unknown = [r for r in resolved if yes(r.get("tail_entry_executable")) and not yes(r.get("paired_realized_comparison"))]
    evaluable = []
    for row in resolved:
        base_pnl = float(number(row, "base_net_pnl_usd"))
        if yes(row.get("tail_entry_executable")):
            if not yes(row.get("paired_realized_comparison")) or number(row, "hedged_net_pnl_usd") is None:
                continue
            strategy_pnl = float(number(row, "hedged_net_pnl_usd"))
            status = "HEDGED_AND_PRICED"
        else:
            strategy_pnl = base_pnl
            status = "NO_HEDGE_EXECUTED"
        out = dict(row)
        out["_policy_pnl"] = strategy_pnl
        out["_base_pnl"] = base_pnl
        out["_status"] = status
        evaluable.append(out)

    base_eval = [r["_base_pnl"] for r in evaluable]
    policy_eval = [r["_policy_pnl"] for r in evaluable]
    deltas = [p - b for p, b in zip(policy_eval, base_eval)]
    same_worst_improvement = None
    if evaluable:
        worst_base = min(evaluable, key=lambda r: r["_base_pnl"])
        same_worst_improvement = worst_base["_policy_pnl"] - worst_base["_base_pnl"]

    loss_rows = [r for r in evaluable if r["_base_pnl"] < -0.005]
    premium_all = [number(r, "tail_entry_gross_premium_usd") for r in rows]
    premium_paired = [number(r, "tail_entry_gross_premium_usd") for r in evaluable if r["_status"] == "HEDGED_AND_PRICED"]
    signals = sum(yes(r.get("trigger_fired")) for r in resolved)
    entries = sum(yes(r.get("tail_entry_executable")) for r in resolved)
    metrics = {
        "base_resolved_n": len(resolved),
        "base_unresolved_n": len(unresolved),
        "trigger_signal_n_resolved": signals,
        "trigger_rate_pct_of_base_resolved": round(100 * signals / len(resolved), 2) if resolved else None,
        "entry_executable_n_resolved": entries,
        "entry_coverage_pct_of_triggered_resolved": round(100 * entries / signals, 2) if signals else None,
        "unknown_entered_hedge_n_resolved": len(unknown),
        "policy_evaluable_n": len(evaluable),
        "policy_evaluable_coverage_pct_of_base_resolved": round(100 * len(evaluable) / len(resolved), 2) if resolved else None,
        "no_hedge_mean_all_resolved_usd": round(statistics.mean(all_base), 2) if all_base else None,
        "no_hedge_mean_policy_evaluable_usd": round(statistics.mean(base_eval), 2) if base_eval else None,
        "conditional_strategy_mean_policy_evaluable_usd": round(statistics.mean(policy_eval), 2) if policy_eval else None,
        "conditional_increment_mean_policy_evaluable_usd": round(statistics.mean(deltas), 2) if deltas else None,
        "conditional_increment_sum_policy_evaluable_usd": round(sum(deltas), 2) if deltas else None,
        "no_hedge_win_rate_policy_evaluable_pct": round(100 * sum(x > 0.005 for x in base_eval) / len(base_eval), 2) if base_eval else None,
        "conditional_win_rate_policy_evaluable_pct": round(100 * sum(x > 0.005 for x in policy_eval) / len(policy_eval), 2) if policy_eval else None,
        "no_hedge_worst_policy_evaluable_usd": round(min(base_eval), 2) if base_eval else None,
        "conditional_strategy_worst_policy_evaluable_usd": round(min(policy_eval), 2) if policy_eval else None,
        "conditional_pnl_on_worst_base_trade_usd": round(min(evaluable, key=lambda r: r["_base_pnl"])["_policy_pnl"], 2) if evaluable else None,
        "worst_base_trade_improvement_policy_evaluable_usd": round(same_worst_improvement, 2) if same_worst_improvement is not None else None,
        "baseline_losing_trades_n_policy_evaluable": len(loss_rows),
        "baseline_losses_improved_n_policy_evaluable": sum(r["_policy_pnl"] > r["_base_pnl"] for r in loss_rows),
        "baseline_losses_turned_positive_n_policy_evaluable": sum(r["_policy_pnl"] > 0.005 for r in loss_rows),
        "hedged_and_priced_n": sum(r["_status"] == "HEDGED_AND_PRICED" for r in evaluable),
        "unhedged_or_blocked_n_policy_evaluable": sum(r["_status"] == "NO_HEDGE_EXECUTED" for r in evaluable),
        "gross_premium_spend_all_entries_usd": round(sum(x for x in premium_all if x is not None), 2),
        "gross_premium_spend_on_priced_entries_usd": round(sum(x for x in premium_paired if x is not None), 2),
        "gross_premium_per_base_resolved_usd": round(sum(x for x in premium_all if x is not None) / len(resolved), 2) if resolved else None,
    }
    eval_by_trade = {r["trade_key"]: r for r in evaluable}
    return metrics, eval_by_trade


def summarize(trade_rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    config_groups: dict[tuple[Any, ...], list[dict[str, str]]] = defaultdict(list)
    annual_groups: dict[tuple[Any, ...], list[dict[str, str]]] = defaultdict(list)
    for row in trade_rows:
        cfg = (row["arm"], int(float(row["phase"])), row["policy"], row["trigger_label"], row["tail_label"], int(float(row["tail_quantity"])))
        config_groups[cfg].append(row)
        day = row.get("exit_date") or row.get("target_observation_date") or ""
        if day:
            annual_groups[(cfg[0], cfg[1], cfg[2], int(day[:4]), cfg[3], cfg[4], cfg[5])].append(row)

    summary, summary_lookup, eval_lookup = [], {}, {}
    for cfg, rows in sorted(config_groups.items()):
        arm, phase, policy, trigger, tail, qty = cfg
        metrics, eval_by_trade = policy_row_metrics(rows)
        obj = {"arm": arm, "phase": phase, "policy": policy, "trigger_label": trigger,
               "trigger_drop_pct": float(rows[0]["trigger_drop_pct"]), "tail_label": tail,
               "tail_quantity": qty, **metrics}
        summary.append(obj)
        summary_lookup[cfg] = obj
        eval_lookup[cfg] = eval_by_trade

    # Common matched-evaluable set for the whole policy at 1x vs 3x, including untriggered rows.
    for cfg, obj3 in summary_lookup.items():
        arm, phase, policy, trigger, tail, qty = cfg
        if qty != 3:
            continue
        cfg1 = (arm, phase, policy, trigger, tail, 1)
        if cfg1 not in eval_lookup:
            continue
        e1, e3 = eval_lookup[cfg1], eval_lookup[cfg]
        common = sorted(set(e1) & set(e3))
        r1, r3 = [e1[k] for k in common], [e3[k] for k in common]
        base = [float(r["_base_pnl"]) for r in r1]
        p1 = [float(r["_policy_pnl"]) for r in r1]
        p3 = [float(r["_policy_pnl"]) for r in r3]
        def mean(xs):
            return round(statistics.mean(xs), 2) if xs else None
        def worst(xs):
            return round(min(xs), 2) if xs else None
        common_metrics = {
            "common_policy_evaluable_1x3_n": len(common),
            "common_no_hedge_mean_usd": mean(base),
            "common_1x_strategy_mean_usd": mean(p1),
            "common_3x_strategy_mean_usd": mean(p3),
            "common_1x_increment_mean_usd": mean([a-b for a,b in zip(p1,base)]),
            "common_3x_increment_mean_usd": mean([a-b for a,b in zip(p3,base)]),
            "common_3x_extra_drag_per_trade_usd": mean([a-b for a,b in zip(p3,p1)]),
            "common_no_hedge_worst_usd": worst(base),
            "common_1x_strategy_worst_usd": worst(p1),
            "common_3x_strategy_worst_usd": worst(p3),
        }
        obj3.update(common_metrics)
        summary_lookup[cfg1].update(common_metrics)

    annual = []
    for key, rows in sorted(annual_groups.items()):
        arm, phase, policy, year, trigger, tail, qty = key
        metrics, eval_by_trade = policy_row_metrics(rows)
        annual.append({"arm": arm, "phase": phase, "policy": policy, "exit_year": year,
                       "trigger_label": trigger, "trigger_drop_pct": float(rows[0]["trigger_drop_pct"]),
                       "tail_label": tail, "tail_quantity": qty, **metrics})
    return summary, annual


def report(summary: list[dict[str, Any]], annual: list[dict[str, Any]], unconditional: list[dict[str, str]]) -> str:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in summary:
        groups[(row["arm"], row["policy"], row["trigger_label"], row["tail_label"], int(row["tail_quantity"]))].append(row)
    unconditional_groups: dict[tuple[Any, ...], list[dict[str, str]]] = defaultdict(list)
    for row in unconditional:
        unconditional_groups[(row["arm"], row["policy"], row["tail_label"], int(float(row["tail_quantity"])))].append(row)
    rules = [(tr, ta, q) for tr in ("ENTRY_SPOT_DRAWDOWN_3PCT", "ENTRY_SPOT_DRAWDOWN_5PCT") for ta in TAILS for q in QTY]
    lines = [
        "# SPY Far-Tail Triggered Hedge — Whole-Policy Evaluation Addendum V1", "",
        "This addendum uses the saved trade-level replay, and includes untriggered trades as unchanged base P&L. If a trigger fires but no eligible contract/size is available, the policy leaves that trade unchanged. If a hedge was entered but its exit cannot be validly priced, that trade is marked unknown and excluded from the policy-evaluable sample—not set to zero.",
        "",
        "## 1. Whole-policy comparison — DTE45 / Hold-20", "",
        "The primary mean below includes all resolved trades that can be accounted for under the conditional rule: untriggered/blocked trades use the unchanged base P&L; successfully paired hedges use base plus net tail P&L. Unknown entered hedges are excluded and shown separately. The no-hedge mean is recomputed on the exact same policy-evaluable subset.",
        "",
        "| Trigger | Tail | Qty | Trigger rate | Evaluable coverage | Evaluable N range | Base mean on eval set | Conditional policy mean | Incremental mean per eval trade | Worst base→policy | Same worst-base trade improvement | Unknown entered N | Premium spend total / phase median |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for trigger, tail, qty in rules:
        rows = groups[("DTE45", "HOLD_20_OR_DTE_LE_7", trigger, tail, qty)]
        def medf(field):
            return median([number(r, field) for r in rows])
        nlo, nhi = range_of([number(r, "policy_evaluable_n") for r in rows])
        baseworst = medf("no_hedge_worst_policy_evaluable_usd")
        policyworst = medf("conditional_strategy_worst_policy_evaluable_usd")
        uncond = unconditional_groups.get(("DTE45", "HOLD_20_OR_DTE_LE_7", tail, qty), [])
        ucov = median([number(r, "paired_coverage_pct_of_base_resolved") for r in uncond])
        uinc = median([number(r, "paired_mean_incremental_hedge_usd") for r in uncond])
        lines.append(
            f"| {trigger.replace('ENTRY_SPOT_DRAWDOWN_','')} | {TAIL_TEXT[tail]} | {qty} "
            f"| {medf('trigger_rate_pct_of_base_resolved'):.2f}% | {medf('policy_evaluable_coverage_pct_of_base_resolved'):.2f}% "
            f"| {range_text(nlo,nhi)} | {money(medf('no_hedge_mean_policy_evaluable_usd'))} "
            f"| {money(medf('conditional_strategy_mean_policy_evaluable_usd'))} "
            f"| {money(medf('conditional_increment_mean_policy_evaluable_usd'))} "
            f"| {money(baseworst)}→{money(policyworst)} "
            f"| {money(medf('worst_base_trade_improvement_policy_evaluable_usd'))} "
            f"| {medf('unknown_entered_hedge_n_resolved'):.1f} "
            f"| {money(medf('gross_premium_spend_all_entries_usd'))} |"
        )
        # Display unconditional premium drag alongside the matched conditional policy statistic as a separate reference.
        if uncond:
            lines.append(
                f"| Unconditional reference | {TAIL_TEXT[tail]} | {qty} | Every entry scheduled "
                f"| {ucov:.2f}% paired coverage | {range_text(*range_of([number(r,'joint_resolved_paired_n') for r in uncond]))} "
                f"| — | — | {money(uinc)} per paired trade | "
                f"{money(median([number(r,'paired_baseline_worst_trade_usd') for r in uncond]))}→{money(median([number(r,'paired_hedged_worst_trade_usd') for r in uncond]))} "
                f"| — | — | — |"
            )

    lines += [
        "",
        "## 2. Annual whole-policy behavior — DTE45 / Hold-20", "",
        "Calendar year is taken from the frozen base exit date. The five phases are overlapping robustness schedules and are summarized by medians; they are not independent observations.",
        "",
        "| Exit year | Trigger | Tail | Qty | Trigger rate | Evaluable coverage | Eval N range | Base mean on eval set | Conditional strategy mean | Incremental mean | Worst base→policy | Same worst-base trade improvement |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    ag: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in annual:
        if row["arm"] == "DTE45" and row["policy"] == "HOLD_20_OR_DTE_LE_7":
            ag[(int(row["exit_year"]), row["trigger_label"], row["tail_label"], int(row["tail_quantity"]))].append(row)
    for year in sorted({k[0] for k in ag}):
        for trigger, tail, qty in rules:
            rows = ag.get((year, trigger, tail, qty), [])
            if not rows:
                continue
            def mf(field):
                return median([number(r, field) for r in rows])
            nlo, nhi = range_of([number(r, "policy_evaluable_n") for r in rows])
            lines.append(
                f"| {year} | {trigger.replace('ENTRY_SPOT_DRAWDOWN_','')} | {TAIL_TEXT[tail]} | {qty} "
                f"| {mf('trigger_rate_pct_of_base_resolved'):.2f}% | {mf('policy_evaluable_coverage_pct_of_base_resolved'):.2f}% "
                f"| {range_text(nlo,nhi)} | {money(mf('no_hedge_mean_policy_evaluable_usd'))} "
                f"| {money(mf('conditional_strategy_mean_policy_evaluable_usd'))} "
                f"| {money(mf('conditional_increment_mean_policy_evaluable_usd'))} "
                f"| {money(mf('no_hedge_worst_policy_evaluable_usd'))}→{money(mf('conditional_strategy_worst_policy_evaluable_usd'))} "
                f"| {money(mf('worst_base_trade_improvement_policy_evaluable_usd'))} |"
            )

    lines += [
        "",
        "## 3. One vs three contracts on a common whole-policy evaluation set", "",
        "The 1x and 3x comparison is restricted to the same base trades that are policy-evaluable for both quantities. Untriggered or blocked entries stay at base P&L for both; entered but unpriced hedge positions are excluded from both sides of that common-set comparison.",
        "",
        "| Trigger | Tail | Common N range | Base mean | 1x strategy mean | 3x strategy mean | 1x incremental mean | 3x incremental mean | Additional 3x drag/trade | Worst base→1x→3x |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for trigger, tail, qty in rules:
        if qty != 3:
            continue
        rows = groups[("DTE45", "HOLD_20_OR_DTE_LE_7", trigger, tail, qty)]
        def cm(field):
            return median([number(r, field) for r in rows])
        nlo, nhi = range_of([number(r, "common_policy_evaluable_1x3_n") for r in rows])
        lines.append(
            f"| {trigger.replace('ENTRY_SPOT_DRAWDOWN_','')} | {TAIL_TEXT[tail]} | {range_text(nlo,nhi)} "
            f"| {money(cm('common_no_hedge_mean_usd'))} | {money(cm('common_1x_strategy_mean_usd'))} "
            f"| {money(cm('common_3x_strategy_mean_usd'))} | {money(cm('common_1x_increment_mean_usd'))} "
            f"| {money(cm('common_3x_increment_mean_usd'))} | {money(cm('common_3x_extra_drag_per_trade_usd'))} "
            f"| {money(cm('common_no_hedge_worst_usd'))}→{money(cm('common_1x_strategy_worst_usd'))}→{money(cm('common_3x_strategy_worst_usd'))} |"
        )

    lines += [
        "",
        "## 4. Decision readout", "",
        "- The triggered-paired mean answers whether the hedge leg paid on trades it actually covered. The whole-policy mean answers a different question: what happened across all resolved trades that could be evaluated, including trades that never triggered and therefore stayed unhedged. Both are needed.",
        "- The policy-evaluable coverage denominator is all resolved base trades. Unknown entered hedges are excluded rather than guessed; check their count and coverage before drawing a conclusion.",
        "- A trigger may reduce expected insurance spending without improving average return. Treat positive changes in isolated crash years as protection evidence, not proof of a persistent return stream.",
        "- The trigger rule was predeclared, but it was researched on the same historical period. Holdout/forward validation is still required.",
        "- End-of-day quotes and displayed size do not prove actual fills. The five phases overlap. No complete QQQ+SPY NAV, margin, forced liquidation or assignment model is included.",
        "",
        "## 5. Related source artifacts", "",
        "- [Triggered paired analysis](SPY_FAR_TAIL_TRIGGERED_HEDGE_REPORT.md)",
        "- [Triggered phase summary](triggered_summary.csv)",
        "- [Whole-policy phase summary](triggered_policy_summary.csv)",
        "- [Whole-policy annual results](triggered_policy_annual.csv)",
        "- [Full triggered trade ledger](triggered_trade_level.csv)",
        "- [Unconditional hedge baseline report](../spy_far_tail_hedge_v1/SPY_FAR_TAIL_DECISION_REPORT.md)",
        "",
    ]
    return "\n".join(lines)


def run(out: Path) -> dict[str, Any]:
    ledger = csv_read(out / "triggered_trade_level.csv")
    summary, annual = summarize(ledger)
    unconditional = csv_read(out.parent / "spy_far_tail_hedge_v1" / "summary.csv")
    addendum = report(summary, annual, unconditional)
    if not summary or not annual or len(addendum) < 8000:
        raise ValueError("policy evaluation output incomplete")
    csv_write(out / "triggered_policy_summary.csv", summary)
    csv_write(out / "triggered_policy_annual.csv", annual)
    (out / "SPY_FAR_TAIL_TRIGGERED_HEDGE_POLICY_ADDENDUM.md").write_text(addendum, encoding="utf-8")
    return {"status": "COMPLETED", "input_trade_rows": len(ledger), "policy_summary_rows": len(summary),
            "policy_annual_rows": len(annual), "addendum_bytes": len(addendum.encode("utf-8"))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent / "results" / "spy_far_tail_triggered_v1")
    args = parser.parse_args()
    print(run(args.out))


if __name__ == "__main__":
    main()
