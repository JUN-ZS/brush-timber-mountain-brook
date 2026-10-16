#!/usr/bin/env python3
"""Direct replay of fixed $800 and $1,000 QQQ put-ratio warning policies."""
from __future__ import annotations

import argparse
import importlib.util
import json
import statistics
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "research" / "qqq_put_ratio_exit_study_v1" / "qqq_put_ratio_exit_study_v1.py"
spec = importlib.util.spec_from_file_location("qqq_put_ratio_exit_study_v1_profit_warning", SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Cannot import replay source: {SOURCE}")
REPLAY = importlib.util.module_from_spec(spec)
spec.loader.exec_module(REPLAY)


def _forward(rows: list[dict[str, Any]], target: int) -> dict[str, Any]:
    result = {}
    for h in (5, 10):
        eligible = [r for r in rows if r.get("signalPnlUsd") is not None and r.get(f"forwardPnlUsd{h}") is not None]
        delta = [float(r[f"forwardPnlUsd{h}"]) - float(r["signalPnlUsd"]) for r in eligible]
        future = [float(r[f"forwardPnlUsd{h}"]) for r in eligible]
        result[str(h)] = {
            "n": len(eligible),
            "medianPnlChangeUsd": round(statistics.median(delta), 2) if delta else None,
            "meanPnlChangeUsd": round(sum(delta) / len(delta), 2) if delta else None,
            "fractionGivebackGeHalfTargetPct": round(100 * sum(x <= -target / 2 for x in delta) / len(delta), 2) if delta else None,
            "fractionFuturePnlNonpositivePct": round(100 * sum(x <= 0 for x in future) / len(future), 2) if future else None,
        }
    return result


def build_threshold_study(trades: list[dict[str, Any]], replay: Any, target: int) -> dict[str, Any]:
    name = f"TP_USD_{target}_CLOSE_SHORT_RISK"
    policy = next((p for p in replay.policy_list() if p.get("name") == name), None)
    if policy is None or policy.get("target") != float(target):
        raise ValueError(f"target {target} is not directly defined in policy_list()")

    actual, counterfactual = [], []
    paths = {}
    for trade in trades:
        trade_id = int(trade["trade_id"])
        marks = replay.mark_unmodified_trade(trade, replay.BASE_EVENT_SLIPPAGE, replay.BASE_EVENT_COMMISSION)
        by_age = {int(m["holding_sessions"]): m for m in marks}
        paths[trade_id] = by_age
        hits = [m for m in marks if int(m["holding_sessions"]) >= 1 and m.get("pnl_usd") is not None and float(m["pnl_usd"]) >= target]
        if hits:
            hit = hits[0]
            row = {"tradeId": trade_id, "date": hit["date"], "ageSessions": int(hit["holding_sessions"]), "signalPnlUsd": float(hit["pnl_usd"])}
            for h in (5, 10):
                future = by_age.get(int(hit["holding_sessions"]) + h)
                row[f"forwardPnlUsd{h}"] = float(future["pnl_usd"]) if future and future.get("pnl_usd") is not None else None
            counterfactual.append(row)

        r = replay.simulate_policy(trade, policy, replay.BASE_EVENT_SLIPPAGE, replay.BASE_EVENT_COMMISSION)
        signal_date = r.get("policy_rule_signal_date")
        if not signal_date:
            continue
        daily = {str(x["date"]): x for x in r.get("daily", [])}
        signal = daily.get(str(signal_date), {})
        age = r.get("policy_rule_signal_holding_sessions")
        attempts = [a for a in r.get("actions", []) if a.get("action") == "CLOSE_SHORT_RISK" and a.get("reason") == name]
        attempt_rows = [{"date": a.get("date"), "status": a.get("status"), "quantity": a.get("quantity")} for a in attempts]
        exit_date = r.get("exit_action_date") if r.get("exit_action") == "CLOSE_SHORT_RISK" else None
        exit_action = next((a for a in attempts if a.get("date") == exit_date and a.get("status") == "OK"), None)
        exit_mark = daily.get(str(exit_date), {}) if exit_date else {}
        row = {
            "tradeId": trade_id, "signalDate": signal_date, "signalAgeSessions": age,
            "signalMarkPnlUsd": signal.get("pnl_before_action_usd"),
            "executionAttemptCount": len(attempt_rows), "firstActionAttemptDate": attempt_rows[0]["date"] if attempt_rows else None,
            "firstActionAttemptStatus": attempt_rows[0]["status"] if attempt_rows else None, "actionAttempts": attempt_rows,
            "executionDate": exit_date, "executionStatus": exit_action.get("status") if exit_action else None,
            "executionAgeSessions": r.get("exit_action_holding_sessions"),
            "signalToExecutionSessions": int(r["exit_action_holding_sessions"]) - int(age)
                if exit_action and r.get("exit_action_holding_sessions") is not None and age is not None else None,
            "executionMarkPnlBeforeActionUsd": exit_mark.get("pnl_before_action_usd") if exit_mark else None,
            "executionMarkPnlAfterActionUsd": exit_mark.get("pnl_after_action_usd") if exit_mark else None,
            "executionDailyStatus": exit_mark.get("action_status") if exit_mark else None,
            "finalNetPnlUsd": r.get("final_pnl_usd"), "finalStatus": r.get("final_status"),
        }
        for h in (5, 10):
            future = paths[trade_id].get(int(age) + h) if age is not None else None
            row[f"forwardPnlUsd{h}"] = float(future["pnl_usd"]) if future and future.get("pnl_usd") is not None else None
        actual.append(row)

    ages = [int(r["signalAgeSessions"]) for r in actual if r.get("signalAgeSessions") is not None]
    delays = [int(r["signalToExecutionSessions"]) for r in actual if r.get("signalToExecutionSessions") is not None]
    successful = [r for r in actual if r.get("executionStatus") == "OK" and r.get("executionDate")]
    return {
        "targetUsd": target, "cohortN": len(trades),
        "counterfactualFirstMarkHitCount": len(counterfactual),
        "counterfactualFirstHitWithin5Sessions": sum(r["ageSessions"] <= 5 for r in counterfactual),
        "counterfactualFirstHitAfter5Sessions": sum(r["ageSessions"] > 5 for r in counterfactual),
        "counterfactualFirstHitForwardIfHeld": _forward(counterfactual, target),
        "counterfactualFirstHitEvents": counterfactual,
        "actualPolicyTriggerCount": len(actual),
        "actualPolicyTriggerPct": round(100 * len(actual) / len(trades), 2) if trades else None,
        "actualPolicyTriggerWithin5Sessions": sum(x <= 5 for x in ages),
        "actualPolicyTriggerAfter5Sessions": sum(x > 5 for x in ages),
        "medianTriggerAgeSessions": statistics.median(ages) if ages else None,
        "executionAttemptCount": sum(int(r["executionAttemptCount"]) for r in actual),
        "successfulExitActionCount": len(successful),
        "successfulActionOnNextObservedSessionCount": sum(r.get("signalToExecutionSessions") == 1 for r in successful),
        "medianSignalToActionSessions": statistics.median(delays) if delays else None,
        "forwardIfOriginal1x5Held": _forward(actual, target),
        "actualEvents": actual,
        "sampleStatus": "INSUFFICIENT_SMALL_TRIGGER_COHORT" if len(actual) < 20 else "DESCRIPTIVE_ONLY_NOT_BLIND_OOS",
    }


def _policy(summary: dict[str, Any], target: int) -> dict[str, Any]:
    name = f"TP_USD_{target}_CLOSE_SHORT_RISK"
    for p in summary.get("policy_summaries_base_cost", []):
        if p.get("policy") == name:
            return p
    raise ValueError(f"missing direct replay policy {name}")


def build_payload(summary: dict[str, Any], curve: dict[str, Any], data: dict[str, Any], trades: list[dict[str, Any]], replay: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    if int(summary.get("generation", {}).get("opened_trade_episodes") or 0) != 62 or len(trades) != 62:
        raise ValueError("expected the frozen 62-episode cohort")
    if int(curve.get("trade_count") or 0) != 62 or curve.get("source_option_end") != "2025-12-15":
        raise ValueError("serial curve does not match the pinned cohort")
    thresholds, outcomes = {}, {}
    for target in (800, 1000):
        e = build_threshold_study(trades, replay, target)
        p = _policy(summary, target)
        c = curve.get("metrics_by_policy_at_80k_nav", {}).get(f"TP_USD_{target}_CLOSE_SHORT_RISK")
        if not c:
            raise ValueError(f"missing serial curve for directly replayed target {target}")
        if int(p.get("policy_rule_triggered_trade_count") or 0) != e["actualPolicyTriggerCount"]:
            raise ValueError(f"policy trigger count disagreement for USD {target}")
        if abs(float(p.get("closed_trade_net_pnl_sum_usd") or 0) - float(c.get("net_pnl_sum_closed_trades_usd") or 0)) > 0.02:
            raise ValueError(f"replay and serial curve P&L mismatch for USD {target}")
        thresholds[str(target)] = e
        outcomes[str(target)] = {
            "policy": p,
            "serialCurve": {k: c.get(k) for k in ("net_pnl_last_observed_usd", "net_pnl_sum_closed_trades_usd",
                "max_drawdown_usd_peak_to_trough", "max_drawdown_pct_of_prior_equity_peak", "max_drawdown_peak_date",
                "max_drawdown_trough_date", "mark_coverage_pct", "missing_marks_not_filled", "drawdown_levels", "status")},
            "thresholdStudy": e,
        }

    compact = {key: {k: v for k, v in value.items() if k not in ("actualEvents", "counterfactualFirstHitEvents")} for key, value in thresholds.items()}
    p = _policy(summary, 800)
    new_row = {
        "id": "TP_USD_800_CLOSE_SHORT_RISK", "n": int(p.get("trade_episodes") or 0),
        "resolved": int(p.get("resolved_trades") or 0), "netPnlUsd": p.get("closed_trade_net_pnl_sum_usd"),
        "expectancyUsd": p.get("expectancy_usd_per_resolved_trade"), "winRatePct": p.get("win_rate_pct"),
        "profitFactor": p.get("profit_factor"), "worstTradeUsd": p.get("worst_trade_usd"),
        "triggerCount": p.get("policy_rule_triggered_trade_count"), "triggerPct": p.get("policy_rule_trigger_rate_pct"),
        "fallbackCount": p.get("mandatory_dte7_fallback_trade_count"),
        "medianResolutionSessions": (p.get("resolved_holding_age_sessions_distribution") or {}).get("median"),
        "markCoveragePct": p.get("trade_mark_coverage_pct"), "missingMarkSessions": p.get("total_missing_mark_sessions"),
    }
    policies = [x for x in data.get("policies", []) if x.get("id") != new_row["id"]]
    pos = next((i + 1 for i, x in enumerate(policies) if x.get("id") == "TP_USD_500_CLOSE_SHORT_RISK"), 2)
    policies.insert(pos, new_row)
    data["policies"] = policies
    data.setdefault("events", {})["profitThresholds"] = compact
    data.setdefault("metadata", {})["profitThresholdReplay"] = {
        "cohortN": 62, "sourceEnd": "2025-12-15", "baseCostSlippagePerLegSideUsd": 0.05,
        "baseCostCommissionPerContractSideUsd": 0.65, "target800IsOnePctOnlyAtNavUsd": 80000,
        "deploymentStatus": "BLOCKED_RESEARCH_ONLY",
    }
    detail = {
        "researchId": "QQQ_PUT_RATIO_PROFIT_WARNING_THRESHOLD_STUDY_V1",
        "status": "RESEARCH_DIAGNOSTIC_ONLY_DEPLOYMENT_BLOCKED",
        "cohort": {"episodes": 62, "start": summary.get("window", {}).get("start"),
            "optionSourceEnd": summary.get("window", {}).get("source_end"),
            "structure": "fixed 1 long / 5 short, non-overlapping episodes"},
        "costConvention": {"slippagePerLegPerSideUsd": 0.05, "commissionPerContractPerSideUsd": 0.65},
        "targetDefinition": "USD 800 is a fixed-dollar policy and equals +1% only at USD 80,000 NAV; the app's current-NAV percentage alert is a separate manual-review alert.",
        "thresholds": outcomes, "deploymentGate": summary.get("performance_gate", "BLOCKED"),
        "limitations": [
            "Public EOD quote marks are not exchange-confirmed fills; exact timestamps and intraday touches are unverified.",
            "First mark hit is counterfactual and distinct from actual policy triggers after DTE7 fallback sequencing.",
            "5/10-session forward marks assume the original 1x5 position remains open after its policy signal; these are not post-exit realized returns.",
            "Close actions occur only on a later observed session and may be deferred for invalid or insufficient option quotes.",
            "The 62 episodes were previously inspected, are not a blind holdout, and do not validate broker margin, assignment or forced liquidation.",
        ],
    }
    return data, detail


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _readme(summary: dict[str, Any], curve: dict[str, Any], thresholds: dict[str, Any]) -> str:
    lines = [
        "## $800 vs $1,000 fixed profit-warning recheck", "",
        "Both targets were directly re-run on the same frozen 62-episode LONG 1 / SHORT 5 cohort with shared DTE <= 7 safety fallback and next-observed-session execution. USD 800 equals +1% only at USD 80,000 NAV; the live app's current-NAV percentage alert is a separate manual-review alert, not a proportional re-run of every historical trade.", "",
        "| Fixed target | Counterfactual first EOD mark hit | Actual policy triggers | Successful close actions | 5-session held-path forward n / median ΔP&L / large giveback | 10-session held-path forward n / median ΔP&L / large giveback | Net P&L | Win rate | Serial quote-mark MaxDD |",
        "|---:|---:|---:|---|---|---|---:|---:|---|",
    ]
    for target in (800, 1000):
        p = _policy(summary, target)
        c = curve["metrics_by_policy_at_80k_nav"][f"TP_USD_{target}_CLOSE_SHORT_RISK"]
        e = thresholds[str(target)]
        bits = []
        for h in ("5", "10"):
            fwd = e["forwardIfOriginal1x5Held"][h]
            med = "—" if fwd["medianPnlChangeUsd"] is None else "USD " + f"{fwd['medianPnlChangeUsd']:,.2f}"
            gb = "—" if fwd["fractionGivebackGeHalfTargetPct"] is None else f"{fwd['fractionGivebackGeHalfTargetPct']:.2f}%"
            bits.append(f"n={fwd['n']}; median {med}; giveback {gb}")
        pnl = p.get("closed_trade_net_pnl_sum_usd")
        pnl_text = "—" if pnl is None else "USD " + f"{float(pnl):,.2f}"
        dd = c.get("max_drawdown_pct_of_prior_equity_peak")
        dd_text = "—" if dd is None else f"{float(dd):.2f}%"
        win = p.get("win_rate_pct")
        win_text = "—" if win is None else f"{float(win):.2f}%"
        lines.append(f"| USD {target:,} | {e['counterfactualFirstMarkHitCount']}/62 | {e['actualPolicyTriggerCount']}/62 ({e['actualPolicyTriggerPct']:.2f}%) | {e['successfulExitActionCount']}/{e['actualPolicyTriggerCount']} | {bits[0]} | {bits[1]} | {pnl_text} | {win_text} | {dd_text} ({c.get('max_drawdown_peak_date')} → {c.get('max_drawdown_trough_date')}) |")
    lines += ["", "The 5/10-session forward metrics are **counterfactual marks for holding the original 1x5** after the warning signal; they are not realized P&L after exiting. Counterfactual first mark hits and actual policy triggers are intentionally separate. With a small trigger/forward sample and previously inspected data, these measurements do not select an optimal target.", "",
        "Public EOD marks are not confirmed fills, action attempts may be deferred, and missing marks are not filled. Deployment remains **BLOCKED** pending blind OOS, verified timestamps/fills, and broker margin/assignment/forced-liquidation evidence."]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("cohort", "summary", "curve", "data", "details", "readme"):
        parser.add_argument("--" + flag, type=Path, required=True)
    args = parser.parse_args()
    trades = json.loads(args.cohort.read_text(encoding="utf-8"))
    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    curve = json.loads(args.curve.read_text(encoding="utf-8"))
    data = json.loads(args.data.read_text(encoding="utf-8"))
    updated, detail = build_payload(summary, curve, data, trades, REPLAY)
    _write(args.data, updated)
    _write(args.details, detail)
    readme = args.readme.read_text(encoding="utf-8")
    start, end = "<!-- PROFIT_WARNING_RESULTS_START -->", "<!-- PROFIT_WARNING_RESULTS_END -->"
    if start not in readme or end not in readme:
        raise ValueError("README threshold-results markers are missing")
    head, tail = readme.split(start, 1)
    _, after = tail.split(end, 1)
    args.readme.write_text(head + start + "\n\n" + _readme(summary, curve, updated["events"]["profitThresholds"]) + "\n\n" + end + after, encoding="utf-8")
    print(json.dumps({
        "researchId": detail["researchId"], "status": detail["status"], "cohortN": detail["cohort"]["episodes"],
        "thresholds": {k: {"actualPolicyTriggers": v["thresholdStudy"]["actualPolicyTriggerCount"],
            "successfulExitActions": v["thresholdStudy"]["successfulExitActionCount"],
            "netPnlUsd": v["policy"]["closed_trade_net_pnl_sum_usd"], "winRatePct": v["policy"]["win_rate_pct"],
            "maxDrawdownPct": v["serialCurve"]["max_drawdown_pct_of_prior_equity_peak"],
            "forward5N": v["thresholdStudy"]["forwardIfOriginal1x5Held"]["5"]["n"],
            "forward10N": v["thresholdStudy"]["forwardIfOriginal1x5Held"]["10"]["n"]}
            for k, v in detail["thresholds"].items()}
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
