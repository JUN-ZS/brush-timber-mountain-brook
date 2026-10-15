#!/usr/bin/env python3
"""Reproducible QQQ Hybrid Generality Auditor.

Computes paired after-cost daily NAV/return series from a traceable CSV ledger
and a pinned expected-session calendar. It cannot authenticate broker fills,
prove a holdout was untouched, or turn model replay into real-execution evidence.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

AUDITOR_VERSION = "QQQ_HYBRID_GENERALITY_AUDITOR_V1"
REQUIRED_REGIMES = ("CARRY", "WEAKENING", "PRE-SHOCK", "SHOCK_BACKWARDATION")
ALLOWED_SOURCE_CLASSES = {"OBSERVED", "DERIVED", "ESTIMATED", "UNKNOWN"}
ALLOWED_OUTCOME_CLASSES = {"REAL_EXECUTION", "REAL_MARKED_PORTFOLIO", "MODEL_REPLAY", "SYNTHETIC"}
REQUIRED_COLUMNS = {
    "date", "baseline_gross_pnl_usd", "candidate_gross_pnl_usd",
    "baseline_cost_usd", "candidate_cost_usd",
    "baseline_adverse_cost_usd", "candidate_adverse_cost_usd",
    "external_flow_usd", "regime", "source_class", "source_ref",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def valid_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def numeric(value: Any, label: str, *, nonnegative: bool = False) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be numeric and explicitly present")
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite")
    if nonnegative and result < 0:
        raise ValueError(f"{label} cannot be negative")
    return result


def load_calendar(path: Path) -> tuple[list[str], str]:
    raw = path.read_text(encoding="utf-8-sig")
    if path.suffix.lower() == ".json":
        parsed = json.loads(raw)
        values = parsed.get("dates") if isinstance(parsed, dict) else None
        if not isinstance(values, list):
            raise ValueError("Calendar JSON must contain a dates array")
    else:
        values = []
        for line in raw.splitlines():
            item = line.strip()
            if item and item.lower() != "date":
                values.append(item.split(",")[0].strip())
    dates = [str(value) for value in values]
    if not dates or any(not valid_date(value) for value in dates):
        raise ValueError("Calendar contains no dates or contains an invalid YYYY-MM-DD date")
    if dates != sorted(dates) or len(dates) != len(set(dates)):
        raise ValueError("Calendar dates must be strictly sorted and unique")
    return dates, sha256_file(path)


def load_spec(path: Path) -> tuple[dict[str, Any], str]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("Spec must be a JSON object")
    if payload.get("schema") != "QQQ_HYBRID_GENERALITY_SPEC_V1":
        raise ValueError("Unsupported spec schema; expected QQQ_HYBRID_GENERALITY_SPEC_V1")
    return payload, sha256_file(path)


def load_observations(path: Path) -> tuple[list[dict[str, Any]], str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = set(reader.fieldnames or [])
        missing = sorted(REQUIRED_COLUMNS - headers)
        if missing:
            raise ValueError("Observation CSV missing required columns: " + ", ".join(missing))
        rows: list[dict[str, Any]] = []
        for line_number, row in enumerate(reader, start=2):
            day = str(row.get("date", "")).strip()
            if not valid_date(day):
                raise ValueError(f"CSV line {line_number}: invalid date")
            normalized: dict[str, Any] = {
                "date": day,
                "baseline_gross_pnl_usd": numeric(row.get("baseline_gross_pnl_usd"), f"line {line_number} baseline gross P&L"),
                "candidate_gross_pnl_usd": numeric(row.get("candidate_gross_pnl_usd"), f"line {line_number} candidate gross P&L"),
                "baseline_cost_usd": numeric(row.get("baseline_cost_usd"), f"line {line_number} baseline costs", nonnegative=True),
                "candidate_cost_usd": numeric(row.get("candidate_cost_usd"), f"line {line_number} candidate costs", nonnegative=True),
                "baseline_adverse_cost_usd": numeric(row.get("baseline_adverse_cost_usd"), f"line {line_number} baseline adverse cost", nonnegative=True),
                "candidate_adverse_cost_usd": numeric(row.get("candidate_adverse_cost_usd"), f"line {line_number} candidate adverse cost", nonnegative=True),
                "external_flow_usd": numeric(row.get("external_flow_usd"), f"line {line_number} common external flow"),
                "regime": str(row.get("regime", "")).strip().upper(),
                "source_class": str(row.get("source_class", "")).strip().upper(),
                "source_ref": str(row.get("source_ref", "")).strip(),
            }
            if normalized["regime"] not in set(REQUIRED_REGIMES) | {"UNKNOWN"}:
                raise ValueError(f"CSV line {line_number}: unsupported regime {normalized['regime']!r}")
            if normalized["source_class"] not in ALLOWED_SOURCE_CLASSES:
                raise ValueError(f"CSV line {line_number}: unsupported source_class")
            if not normalized["source_ref"]:
                raise ValueError(f"CSV line {line_number}: source_ref must be explicit")
            rows.append(normalized)
    if not rows:
        raise ValueError("Observation CSV has no rows")
    dates = [row["date"] for row in rows]
    if dates != sorted(dates):
        raise ValueError("Observation rows must be in ascending date order")
    if len(dates) != len(set(dates)):
        raise ValueError("Observation dates must be unique; duplicate dates are never silently averaged")
    return rows, sha256_file(path)


def objective_metric(returns: list[float], objective: str) -> float:
    """Higher is always better; result unit is percentage points."""
    if not returns:
        raise ValueError("Cannot measure an empty return window")
    wealth = 1.0
    path = [1.0]
    for value in returns:
        if not math.isfinite(value) or value <= -1:
            raise ValueError("Daily return implies non-positive wealth; block the replay")
        wealth *= 1.0 + value
        path.append(wealth)
    if objective == "CAGR":
        return (wealth ** (252.0 / len(returns)) - 1.0) * 100.0
    peak = path[0]
    drawdowns = []
    for point in path[1:]:
        peak = max(peak, point)
        drawdowns.append(point / peak - 1.0)
    if objective == "MAX_DRAWDOWN_MAGNITUDE":
        return min(drawdowns, default=0.0) * 100.0
    if objective == "ES95_MAGNITUDE":
        count = max(1, math.ceil(len(returns) * 0.05))
        worst = sorted(returns)[:count]
        es = sum(worst) / len(worst)
        return -max(0.0, -es) * 100.0
    raise ValueError("primaryObjective must be CAGR, MAX_DRAWDOWN_MAGNITUDE, or ES95_MAGNITUDE")


def risk_metrics(returns: list[float]) -> dict[str, float | int]:
    if not returns:
        raise ValueError("No daily returns for risk metrics")
    wealth = 1.0
    path = [1.0]
    for value in returns:
        if not math.isfinite(value) or value <= -1:
            raise ValueError("Daily return implies non-positive wealth; block the replay")
        wealth *= 1.0 + value
        path.append(wealth)
    peak = path[0]
    drawdowns = []
    for value in path[1:]:
        peak = max(peak, value)
        drawdowns.append(value / peak - 1.0)
    count = max(1, math.ceil(len(returns) * 0.05))
    worst = sorted(returns)[:count]
    es_mean = sum(worst) / len(worst)
    stdev = statistics.stdev(returns) if len(returns) > 1 else 0.0
    mean_return = statistics.mean(returns)
    return {
        "observationCount": len(returns),
        "totalReturnPct": (wealth - 1.0) * 100.0,
        "cagrPct": (wealth ** (252.0 / len(returns)) - 1.0) * 100.0,
        "maxDrawdownPct": min(drawdowns, default=0.0) * 100.0,
        "annualizedVolatilityPct": stdev * math.sqrt(252.0) * 100.0,
        "sharpeRf0": mean_return / stdev * math.sqrt(252.0) if stdev > 0 else 0.0,
        "worstDayPct": min(returns) * 100.0,
        "es95MagnitudePct": max(0.0, -es_mean) * 100.0,
    }


def _base_report() -> dict[str, Any]:
    return {
        "auditorVersion": AUDITOR_VERSION, "auditStatus": "NOT_PASS",
        "operatorAttested": True, "sourceAuthenticated": False,
        "canCountAsRealExecutionProbability": False,
        "realExecutionProbabilityGate": "BLOCKED_SOURCE_AUTHENTICATION",
        "evidenceClass": "UNKNOWN", "outcomeClass": "UNKNOWN",
        "inputIntegrity": {}, "dataQuality": {},
        "rollingWindows": [],
        "regimeObservations": {key: 0 for key in REQUIRED_REGIMES},
        "issues": [],
        "limitations": [
            "Input hashes are reproducibility fingerprints, not a digital signature or source authentication.",
            "The auditor computes the supplied ledger; it cannot prove quote-side realism, fills, licensing, or that a final lockbox was never inspected.",
            "Derived/model/synthetic outcomes never qualify as real-execution probability.",
        ],
    }


def audit_daily_series(observation_path: Path, calendar_path: Path, spec_path: Path) -> dict[str, Any]:
    report = _base_report()
    try:
        spec, spec_hash = load_spec(spec_path)
        calendar, calendar_hash = load_calendar(calendar_path)
        rows, observations_hash = load_observations(observation_path)
        report.update({
            "baselineId": str(spec.get("baselineId", "")).strip(),
            "candidateId": str(spec.get("candidateId", "")).strip(),
            "sourceRef": str(spec.get("sourceRef", "")).strip(),
            "evidenceClass": str(spec.get("evidenceClass", "UNKNOWN")).upper(),
            "outcomeClass": str(spec.get("outcomeClass", "UNKNOWN")).upper(),
            "primaryObjective": str(spec.get("primaryObjective", "CAGR")).upper(),
            "inputIntegrity": {
                "observationsSha256": observations_hash,
                "calendarSha256": calendar_hash,
                "specSha256": spec_hash,
            },
        })
        for key in ("trainStart", "trainEnd", "validationStart", "validationEnd", "finalStart", "finalEnd"):
            report[key] = spec.get(key)
        required_dates = [report[key] for key in ("trainStart", "trainEnd", "validationStart", "validationEnd", "finalStart", "finalEnd")]
        if not report["baselineId"] or not report["candidateId"] or not report["sourceRef"]:
            report["issues"].append("baselineId, candidateId, and sourceRef are required")
        if report["evidenceClass"] not in ALLOWED_SOURCE_CLASSES:
            report["issues"].append("evidenceClass must be OBSERVED, DERIVED, ESTIMATED, or UNKNOWN")
        if report["outcomeClass"] not in ALLOWED_OUTCOME_CLASSES:
            report["issues"].append("outcomeClass must be REAL_EXECUTION, REAL_MARKED_PORTFOLIO, MODEL_REPLAY, or SYNTHETIC")
        if report["primaryObjective"] not in {"CAGR", "MAX_DRAWDOWN_MAGNITUDE", "ES95_MAGNITUDE"}:
            report["issues"].append("Unsupported primaryObjective")
        if any(not valid_date(value) for value in required_dates):
            report["issues"].append("All train/validation/final dates must be valid YYYY-MM-DD dates")
        elif not (report["trainStart"] <= report["trainEnd"] < report["validationStart"] <= report["validationEnd"] < report["finalStart"] <= report["finalEnd"]):
            report["issues"].append("Train, validation, and final OOS dates must be chronological and non-overlapping")
        initial_nav = numeric(spec.get("initialNavUsd"), "initialNavUsd", nonnegative=True)
        if initial_nav <= 0:
            report["issues"].append("initialNavUsd must be positive")
        for key in ("finalUntouched", "finalEvaluatedOnce", "designFrozenBeforeFinal", "noLookahead", "trialLedgerComplete"):
            if spec.get(key) is not True:
                report["issues"].append(key + " must be explicitly true")
        if report["issues"]:
            report["auditStatus"] = "INVALID_SPEC"
            return report

        starts, ends = report["trainStart"], report["finalEnd"]
        calendar_set = set(calendar)
        split_boundaries = [report[key] for key in ("trainStart", "trainEnd", "validationStart", "validationEnd", "finalStart", "finalEnd")]
        if any(day not in calendar_set for day in split_boundaries):
            report["issues"].append("Every train/validation/final split boundary must be an expected calendar session")
            report["auditStatus"] = "INVALID_SPEC"
            return report
        selected_rows = [row for row in rows if starts <= row["date"] <= ends]
        expected = [day for day in calendar if starts <= day <= ends]
        row_by_date = {row["date"]: row for row in selected_rows}
        missing_dates = [day for day in expected if day not in row_by_date]
        extra_dates = [row["date"] for row in selected_rows if row["date"] not in calendar_set]
        coverage = 100.0 * (len(expected) - len(missing_dates)) / len(expected) if expected else 0.0
        report["dataQuality"] = {
            "calendarExpectedCount": len(expected),
            "sourceRowCount": len(selected_rows),
            "expectedObservationCoveragePct": round(coverage, 6),
            "missingExpectedDates": missing_dates,
            "extraNonCalendarDates": extra_dates,
            "duplicateSourceDates": [],
            "calendarSource": str(calendar_path),
            "observationsSource": str(observation_path),
        }
        if not expected:
            report["issues"].append("No expected calendar sessions inside the evaluation window")
        if missing_dates:
            report["issues"].append(f"{len(missing_dates)} expected sessions are missing; complete performance metrics are blocked")
        if extra_dates:
            report["issues"].append("Source includes observations outside the pinned expected-session calendar")
        if any(row["source_class"] == "UNKNOWN" for row in selected_rows):
            report["issues"].append("At least one source row has UNKNOWN evidence class")
        if len(selected_rows) != len(expected) or missing_dates or extra_dates:
            report["auditStatus"] = "BLOCKED_SOURCE_COVERAGE"
            report["finalCoveragePct"] = round(coverage, 6)
            report["finalObservationCount"] = sum(report["finalStart"] <= row["date"] <= report["finalEnd"] for row in selected_rows)
            return report

        source_classes = sorted({row["source_class"] for row in selected_rows})
        report["rowSourceClasses"] = source_classes
        report["rowSourceReferenceCount"] = len({row["source_ref"] for row in selected_rows})
        report["sourceReferencesSample"] = sorted({row["source_ref"] for row in selected_rows})[:20]
        source_rank = {"OBSERVED": 0, "DERIVED": 1, "ESTIMATED": 2, "UNKNOWN": 3}
        worst_row_source_rank = max(source_rank[value] for value in source_classes)
        if source_rank[report["evidenceClass"]] < worst_row_source_rank:
            report["issues"].append("Spec evidenceClass overstates the weakest row-level source class")
        report["sourceReferencesSample"] = sorted({row["source_ref"] for row in selected_rows})[:20]

        # Same initial NAV and one shared external-flow path. Cash flow is end-of-day.
        base_nav = cand_nav = base_stress_nav = cand_stress_nav = initial_nav
        daily: list[dict[str, Any]] = []
        for row in selected_rows:
            base_net = row["baseline_gross_pnl_usd"] - row["baseline_cost_usd"]
            cand_net = row["candidate_gross_pnl_usd"] - row["candidate_cost_usd"]
            base_stress_net = base_net - row["baseline_adverse_cost_usd"]
            cand_stress_net = cand_net - row["candidate_adverse_cost_usd"]
            if min(base_nav, cand_nav, base_stress_nav, cand_stress_nav) <= 0:
                raise ValueError("A portfolio NAV reached zero or below; stop before computing return metrics")
            base_return, cand_return = base_net / base_nav, cand_net / cand_nav
            base_stress_return, cand_stress_return = base_stress_net / base_stress_nav, cand_stress_net / cand_stress_nav
            flow = row["external_flow_usd"]
            base_nav += base_net + flow
            cand_nav += cand_net + flow
            base_stress_nav += base_stress_net + flow
            cand_stress_nav += cand_stress_net + flow
            if min(base_nav, cand_nav, base_stress_nav, cand_stress_nav) <= 0:
                raise ValueError("A portfolio NAV reached zero or below; stop before computing return metrics")
            daily.append({
                **row, "baselineReturn": base_return, "candidateReturn": cand_return,
                "baselineStressReturn": base_stress_return, "candidateStressReturn": cand_stress_return,
                "baselineNav": base_nav, "candidateNav": cand_nav,
                "baselineStressNav": base_stress_nav, "candidateStressNav": cand_stress_nav,
            })

        def segment(start: str, end: str) -> list[dict[str, Any]]:
            return [item for item in daily if start <= item["date"] <= end]

        def evaluate_segment(items: list[dict[str, Any]]) -> dict[str, Any]:
            if not items:
                raise ValueError("Empty train/validation/final or rolling segment")
            base = [item["baselineReturn"] for item in items]
            cand = [item["candidateReturn"] for item in items]
            base_stress = [item["baselineStressReturn"] for item in items]
            cand_stress = [item["candidateStressReturn"] for item in items]
            objective = report["primaryObjective"]
            effect = objective_metric(cand, objective) - objective_metric(base, objective)
            adverse_effect = objective_metric(cand_stress, objective) - objective_metric(base_stress, objective)
            return {
                "baseline": risk_metrics(base), "candidate": risk_metrics(cand),
                "effectDeltaPct": effect, "adverseCostEffectDeltaPct": adverse_effect,
                "costStressPass": adverse_effect > 0,
                "catastrophicFailure": any(item["candidateNav"] <= 0 or item["candidateStressNav"] <= 0 for item in items),
                "observations": len(items),
            }

        spec_windows = spec.get("rollingWindows")
        if not isinstance(spec_windows, list) or len(spec_windows) < 5:
            report["issues"].append("At least five pre-registered rollingWindows are required in the spec")
            report["auditStatus"] = "NOT_PASS"
            return report
        rolling: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        seen_ranges: set[tuple[str, str]] = set()
        previous_start = ""
        for item in spec_windows:
            if not isinstance(item, dict):
                report["issues"].append("Every rolling window must be an object")
                continue
            window_id, start, end = str(item.get("id", "")).strip(), item.get("start"), item.get("end")
            if not window_id or window_id in seen_ids:
                report["issues"].append("Rolling window IDs must be present and unique")
                continue
            seen_ids.add(window_id)
            if not valid_date(start) or not valid_date(end) or start > end:
                report["issues"].append("Rolling window " + window_id + " has invalid dates")
                continue
            if (start, end) in seen_ranges:
                report["issues"].append("Duplicate rolling date range: " + window_id)
                continue
            seen_ranges.add((start, end))
            if previous_start and start < previous_start:
                report["issues"].append("Rolling windows must be ordered by start date")
            previous_start = start
            if start < report["trainStart"] or end > report["validationEnd"]:
                report["issues"].append("Rolling window " + window_id + " must lie before final OOS")
                continue
            if start not in calendar_set or end not in calendar_set:
                report["issues"].append("Rolling window " + window_id + " boundaries must be expected calendar sessions")
                continue
            expected_window = [day for day in expected if start <= day <= end]
            window_rows = segment(start, end)
            window_coverage = 100.0 * len(window_rows) / len(expected_window) if expected_window else 0.0
            if len(window_rows) < 100:
                report["issues"].append("Rolling window " + window_id + " has fewer than 100 observations")
            measured = evaluate_segment(window_rows)
            rolling.append({
                "id": window_id, "start": start, "end": end,
                "observations": len(window_rows), "coveragePct": round(window_coverage, 6),
                "missingDatesReviewed": True, "sameCapitalAndCosts": True,
                "lookaheadFree": spec["noLookahead"], "costStressPass": measured["costStressPass"],
                "catastrophicFailure": measured["catastrophicFailure"],
                "effectDeltaPct": round(measured["effectDeltaPct"], 8),
                "adverseCostEffectDeltaPct": round(measured["adverseCostEffectDeltaPct"], 8),
                "baseline": measured["baseline"], "candidate": measured["candidate"],
            })
        if len(rolling) < 5:
            report["issues"].append("Fewer than five valid rolling windows were measured")
        for regime in REQUIRED_REGIMES:
            report["regimeObservations"][regime] = sum(1 for item in daily if item["regime"] == regime)
            if report["regimeObservations"][regime] < 100:
                report["issues"].append(regime + " has fewer than 100 daily observations")
        positive = sum(1 for item in rolling if item["effectDeltaPct"] > 0)
        required_positive = math.ceil(len(rolling) * 0.8)
        if len(rolling) >= 5 and positive < required_positive:
            report["issues"].append(f"Pre-selected objective improves in {positive}/{len(rolling)} windows; requires {required_positive}")
        if any(not item["costStressPass"] for item in rolling):
            report["issues"].append("At least one rolling window fails the adverse-cost objective-direction check")
        if any(item["catastrophicFailure"] for item in rolling):
            report["issues"].append("At least one rolling window reports a non-positive portfolio NAV")
        train_rows = segment(report["trainStart"], report["trainEnd"])
        validation_rows = segment(report["validationStart"], report["validationEnd"])
        if len(train_rows) < 100:
            report["issues"].append("Training segment has fewer than 100 daily observations")
        if len(validation_rows) < 100:
            report["issues"].append("Validation segment has fewer than 100 daily observations")
        train = evaluate_segment(train_rows)
        validation = evaluate_segment(validation_rows)
        final = evaluate_segment(segment(report["finalStart"], report["finalEnd"]))
        final_rows = segment(report["finalStart"], report["finalEnd"])
        final_expected = [day for day in expected if report["finalStart"] <= day <= report["finalEnd"]]
        final_coverage = 100.0 * len(final_rows) / len(final_expected) if final_expected else 0.0
        if len(final_rows) < 100:
            report["issues"].append("Final OOS has fewer than 100 daily observations")
        if final_coverage != 100:
            report["issues"].append("Final OOS does not have 100% expected-session coverage")
        report.update({
            "finalCoveragePct": round(final_coverage, 6),
            "finalObservationCount": len(final_rows),
            "rollingWindows": rolling,
            "positiveEffectWindows": positive,
            "requiredPositiveWindows": required_positive,
            "trainMetrics": train, "validationMetrics": validation, "finalMetrics": final,
            "finalUntouched": spec["finalUntouched"], "finalEvaluatedOnce": spec["finalEvaluatedOnce"],
            "designFrozenBeforeFinal": spec["designFrozenBeforeFinal"], "noLookahead": spec["noLookahead"],
            "trialLedgerComplete": spec["trialLedgerComplete"],
            "canCountAsRealExecutionProbability": False,
        })
        report["auditStatus"] = "PASS_OPERATOR_ATTESTED" if not report["issues"] else "NOT_PASS"
        # This program has no independent source-authentication mechanism. Do not
        # let caller-controlled evidenceClass/outcomeClass labels unlock empirical
        # execution probabilities, even when arithmetic/coverage rules pass.
        report["canCountAsRealExecutionProbability"] = False
        report["realExecutionProbabilityGate"] = "BLOCKED_SOURCE_AUTHENTICATION"
        report["limitations"].append(
            "Real-execution probability is disabled until independent source authentication is implemented; row labels, source references and SHA-256 fingerprints alone do not authenticate observed fills."
        )
        return report
    except (OSError, UnicodeError, json.JSONDecodeError, csv.Error, ValueError, TypeError) as exc:
        report["auditStatus"] = "INVALID_INPUT"
        report["issues"].append(str(exc))
        return report


def audit_alignment_diagnostic(path: Path) -> dict[str, Any]:
    report = _base_report()
    raw = path.read_bytes()
    report["inputIntegrity"] = {"alignmentDiagnosticSha256": hashlib.sha256(raw).hexdigest()}
    try:
        payload = json.loads(raw.decode("utf-8-sig"))
        coverage = payload.get("coverage", {})
        report.update({
            "auditStatus": "SOURCE_DIAGNOSTIC_ONLY",
            "researchId": payload.get("research_id"),
            "diagnosticStatus": payload.get("status"),
            "integrityOk": payload.get("integrity_ok") is True,
            "notAStrategyBacktest": payload.get("not_a_strategy_backtest") is True,
            "tradeReplayApproved": payload.get("trade_replay_approved") is True,
            "requestedWindow": payload.get("window"),
            "sourceDateBounds": coverage.get("source_date_bounds", {}),
            "expectedTradingDates": coverage.get("expected_trading_dates_from_repo_universe"),
            "datesWithOptions": coverage.get("dates_with_qqq_option_rows"),
            "datesWithRawTargetPairs": coverage.get("dates_with_raw_target_pairs"),
            "rawTargetPairCoveragePct": coverage.get("raw_target_pair_coverage_pct_of_expected_dates"),
            "optionDateCoveragePct": coverage.get("option_date_coverage_pct"),
            "rawUnderlyingDateCoveragePct": coverage.get("raw_underlying_price_date_coverage_pct"),
            "missingOptionDates": coverage.get("expected_dates_missing_option_rows", []),
            "missingRawUnderlyingDates": coverage.get("expected_dates_missing_raw_underlying_price", []),
            "interpretation": payload.get("interpretation"),
            "limitations": payload.get("limitations", []),
        })
        report["issues"] = [
            "This is source-coverage diagnostic data, not a paired strategy-return series.",
            "It cannot support a Generality PASS, CAGR/MaxDD/ES95, or real-execution probability.",
        ]
        if payload.get("integrity_ok") is not True:
            report["issues"].append("Alignment diagnostic does not report verified file integrity")
        if payload.get("not_a_strategy_backtest") is not True or payload.get("trade_replay_approved") is True:
            report["issues"].append("Diagnostic classification is inconsistent with the no-strategy-performance boundary")
    except (UnicodeError, json.JSONDecodeError, AttributeError, TypeError) as exc:
        report["auditStatus"] = "INVALID_INPUT"
        report["issues"].append(str(exc))
    return report


def markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# QQQ Hybrid Generality Audit", "",
        f"- Auditor: {report.get('auditorVersion', AUDITOR_VERSION)}",
        f"- Audit status: {report.get('auditStatus', 'UNKNOWN')}",
        f"- Baseline / candidate: {report.get('baselineId', 'N/A')} / {report.get('candidateId', 'N/A')}",
        f"- Objective: {report.get('primaryObjective', 'N/A')}",
        f"- Final coverage: {report.get('finalCoveragePct', report.get('rawTargetPairCoveragePct', 'N/A'))}",
        f"- Final observations: {report.get('finalObservationCount', 'N/A')}",
        f"- Source authenticated: {report.get('sourceAuthenticated', False)}", "",
        "## Input fingerprints", "",
    ]
    for key, value in report.get("inputIntegrity", {}).items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Issues / limits", ""])
    for issue in report.get("issues", []):
        lines.append(f"- {issue}")
    if report.get("missingExpectedDates"):
        lines.extend(["", "## Missing expected dates", ""])
        for missing in report["missingExpectedDates"][:100]:
            lines.append(f"- {missing}")
        if len(report["missingExpectedDates"]) > 100:
            lines.append(f"- … plus {len(report['missingExpectedDates']) - 100} additional dates")
    if report.get("rollingWindows"):
        lines.extend(["", "## Rolling windows", "", "| ID | Window | N | Coverage | Objective delta (pp) | Adverse-cost pass |", "|---|---|---:|---:|---:|---|"])
        for window in report["rollingWindows"]:
            lines.append(f"| {window['id']} | {window['start']} → {window['end']} | {window['observations']} | {window['coveragePct']:.2f}% | {window['effectDeltaPct']:.4f} | {window['costStressPass']} |")
    if report.get("finalMetrics"):
        lines.extend(["", "## Final OOS metrics", "", "| Metric | Baseline | Candidate |", "|---|---:|---:|"])
        for key, label in (("totalReturnPct", "Total return %"), ("cagrPct", "CAGR %"), ("maxDrawdownPct", "Daily marked MaxDD %"), ("annualizedVolatilityPct", "Annualized volatility %"), ("sharpeRf0", "Sharpe (rf=0)"), ("worstDayPct", "Worst day %"), ("es95MagnitudePct", "ES95 loss magnitude %")):
            base = report["finalMetrics"]["baseline"][key]
            cand = report["finalMetrics"]["candidate"][key]
            lines.append(f"| {label} | {base:.4f} | {cand:.4f} |")
    lines.extend(["", "## Non-negotiable limitation", "", "PASS_OPERATOR_ATTESTED validates the entered fingerprints, arithmetic path and pre-registered acceptance rules, but not source authenticity or whether final dates were truly untouched. Derived/model/synthetic outcomes never qualify as real-execution probability.", ""])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observations", type=Path)
    parser.add_argument("--calendar", type=Path)
    parser.add_argument("--spec", type=Path)
    parser.add_argument("--source-alignment-json", type=Path)
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-md", type=Path)
    args = parser.parse_args(argv)
    if args.source_alignment_json:
        report = audit_alignment_diagnostic(args.source_alignment_json)
    elif args.observations and args.calendar and args.spec:
        report = audit_daily_series(args.observations, args.calendar, args.spec)
    else:
        parser.error("Use --source-alignment-json or provide --observations, --calendar, and --spec")
    report["generatedAtUtc"] = datetime.now(timezone.utc).isoformat()
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.out_md:
        args.out_md.parent.mkdir(parents=True, exist_ok=True)
        args.out_md.write_text(markdown_report(report) + "\n", encoding="utf-8")
    print(f"generality_audit_status={report.get('auditStatus', 'UNKNOWN')}")
    print(f"source_authenticated={str(report.get('sourceAuthenticated', False)).upper()}")
    print(f"issues={len(report.get('issues', []))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
