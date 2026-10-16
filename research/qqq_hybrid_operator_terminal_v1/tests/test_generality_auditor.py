#!/usr/bin/env python3
"""Unit tests for generality_auditor.py; all generated rows are synthetic fixtures."""
import csv
import json
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve()
RESEARCH_DIR = HERE.parents[1]
sys.path.insert(0, str(RESEARCH_DIR))
import generality_auditor as auditor  # noqa: E402

FIELDS = [
    "date", "baseline_gross_pnl_usd", "candidate_gross_pnl_usd",
    "baseline_cost_usd", "candidate_cost_usd",
    "baseline_adverse_cost_usd", "candidate_adverse_cost_usd",
    "external_flow_usd", "regime", "source_class", "source_ref",
]


def weekdays(start: date, end: date) -> list[str]:
    output = []
    day = start
    while day <= end:
        if day.weekday() < 5:
            output.append(day.isoformat())
        day += timedelta(days=1)
    return output


class GeneralityAuditorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.start = date(2018, 1, 1)
        self.end = date(2025, 12, 31)
        self.dates = weekdays(self.start, self.end)
        self.calendar = self.root / "calendar.json"
        self.calendar.write_text(json.dumps({"source": "synthetic test calendar", "dates": self.dates}), encoding="utf-8")
        self.observations = self.root / "observations.csv"
        self.write_rows(self.dates)
        self.spec_path = self.root / "spec.json"
        self.write_spec()

    def tearDown(self):
        self.tmp.cleanup()

    def write_rows(self, dates, *, regime_override=None, duplicate_first=False, negative_cost=False):
        with self.observations.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            regimes = list(auditor.REQUIRED_REGIMES)
            rows = []
            for index, day in enumerate(dates):
                regime = regime_override if regime_override else regimes[index % len(regimes)]
                rows.append({
                    "date": day,
                    "baseline_gross_pnl_usd": "2.00",
                    "candidate_gross_pnl_usd": "2.60",
                    "baseline_cost_usd": "-0.01" if negative_cost else "0.20",
                    "candidate_cost_usd": "0.20",
                    "baseline_adverse_cost_usd": "0.03",
                    "candidate_adverse_cost_usd": "0.04",
                    "external_flow_usd": "0.00",
                    "regime": regime,
                    "source_class": "DERIVED",
                    "source_ref": "synthetic-fixture://daily-pnl",
                })
            if duplicate_first and rows:
                rows.insert(1, rows[0].copy())
            writer.writerows(rows)

    def write_spec(self, **overrides):
        spec = {
            "schema": "QQQ_HYBRID_GENERALITY_SPEC_V1",
            "baselineId": "FROZEN_BASELINE_SYNTHETIC_TEST",
            "candidateId": "CANDIDATE_SYNTHETIC_TEST",
            "sourceRef": "synthetic-fixture://spec",
            "evidenceClass": "DERIVED",
            "outcomeClass": "MODEL_REPLAY",
            "primaryObjective": "CAGR",
            "initialNavUsd": 100000,
            "trainStart": "2018-01-01",
            "trainEnd": "2019-12-31",
            "validationStart": "2020-01-01",
            "validationEnd": "2023-12-29",
            "finalStart": "2024-01-01",
            "finalEnd": "2025-12-31",
            "finalUntouched": True,
            "finalEvaluatedOnce": True,
            "designFrozenBeforeFinal": True,
            "noLookahead": True,
            "trialLedgerComplete": True,
            "rollingWindows": [
                {"id": "W1", "start": "2020-01-01", "end": "2020-12-31"},
                {"id": "W2", "start": "2021-01-01", "end": "2021-12-31"},
                {"id": "W3", "start": "2022-01-03", "end": "2022-12-30"},
                {"id": "W4", "start": "2023-01-02", "end": "2023-06-30"},
                {"id": "W5", "start": "2023-07-03", "end": "2023-12-29"},
            ],
        }
        spec.update(overrides)
        self.spec_path.write_text(json.dumps(spec), encoding="utf-8")

    def audit(self):
        return auditor.audit_daily_series(self.observations, self.calendar, self.spec_path)

    def test_full_synthetic_series_is_reproducibly_measured_not_real_execution(self):
        report = self.audit()
        self.assertEqual(report["auditStatus"], "PASS_OPERATOR_ATTESTED", report["issues"])
        self.assertEqual(report["dataQuality"]["expectedObservationCoveragePct"], 100.0)
        self.assertEqual(report["finalCoveragePct"], 100.0)
        self.assertEqual(len(report["rollingWindows"]), 5)
        self.assertEqual(report["positiveEffectWindows"], 5)
        self.assertEqual(report["outcomeClass"], "MODEL_REPLAY")
        self.assertFalse(report["sourceAuthenticated"])
        self.assertFalse(report["canCountAsRealExecutionProbability"])
        self.assertEqual(len(report["inputIntegrity"]["observationsSha256"]), 64)
        self.assertGreater(report["finalMetrics"]["candidate"]["cagrPct"], report["finalMetrics"]["baseline"]["cagrPct"])

    def test_missing_terminal_sessions_block_all_full_window_metrics(self):
        self.write_rows(self.dates[:-5])
        report = self.audit()
        self.assertEqual(report["auditStatus"], "BLOCKED_SOURCE_COVERAGE")
        self.assertEqual(len(report["dataQuality"]["missingExpectedDates"]), 5)
        self.assertNotIn("finalMetrics", report)
        self.assertNotEqual(report["finalCoveragePct"], 100.0)

    def test_duplicate_dates_are_not_silently_averaged(self):
        self.write_rows(self.dates, duplicate_first=True)
        report = self.audit()
        self.assertEqual(report["auditStatus"], "INVALID_INPUT")
        self.assertTrue(any("dates must be unique" in issue for issue in report["issues"]))

    def test_negative_cost_input_is_rejected(self):
        self.write_rows(self.dates, negative_cost=True)
        report = self.audit()
        self.assertEqual(report["auditStatus"], "INVALID_INPUT")
        self.assertTrue(any("cannot be negative" in issue for issue in report["issues"]))

    def test_split_boundaries_must_exist_on_pinned_calendar(self):
        self.write_spec(trainEnd="2019-12-28")
        report = self.audit()
        self.assertEqual(report["auditStatus"], "INVALID_SPEC")
        self.assertTrue(any("split boundary must be an expected calendar session" in issue for issue in report["issues"]))

    def test_final_lockbox_must_be_attested_untouched(self):
        self.write_spec(finalUntouched=False)
        report = self.audit()
        self.assertEqual(report["auditStatus"], "INVALID_SPEC")
        self.assertTrue(any("finalUntouched" in issue for issue in report["issues"]))

    def test_four_regimes_need_minimum_observations(self):
        self.write_rows(self.dates, regime_override="CARRY")
        report = self.audit()
        self.assertEqual(report["auditStatus"], "NOT_PASS")
        self.assertEqual(report["regimeObservations"]["WEAKENING"], 0)
        self.assertTrue(any("fewer than 100 daily observations" in issue for issue in report["issues"]))

    def test_no_result_driven_four_window_shortcut(self):
        spec = json.loads(self.spec_path.read_text(encoding="utf-8"))
        spec["rollingWindows"] = spec["rollingWindows"][:4]
        self.spec_path.write_text(json.dumps(spec), encoding="utf-8")
        report = self.audit()
        self.assertEqual(report["auditStatus"], "NOT_PASS")
        self.assertTrue(any("At least five pre-registered" in issue for issue in report["issues"]))

    def test_duplicate_rolling_ranges_do_not_inflate_generality(self):
        spec = json.loads(self.spec_path.read_text(encoding="utf-8"))
        spec["rollingWindows"][1]["start"] = spec["rollingWindows"][0]["start"]
        spec["rollingWindows"][1]["end"] = spec["rollingWindows"][0]["end"]
        self.spec_path.write_text(json.dumps(spec), encoding="utf-8")
        report = self.audit()
        self.assertEqual(report["auditStatus"], "NOT_PASS")
        self.assertTrue(any("Duplicate rolling date range" in issue for issue in report["issues"]))

    def test_source_alignment_diagnostic_never_becomes_strategy_generality(self):
        path = self.root / "alignment.json"
        path.write_text(json.dumps({
            "research_id": "SOURCE_DIAGNOSTIC_TEST",
            "status": "SOURCE_COVERAGE_DIAGNOSTIC",
            "integrity_ok": True,
            "not_a_strategy_backtest": True,
            "trade_replay_approved": False,
            "window": {"start": "2018-03-01", "end": "2025-12-31"},
            "coverage": {
                "expected_trading_dates_from_repo_universe": 1971,
                "dates_with_qqq_option_rows": 1956,
                "dates_with_raw_target_pairs": 1946,
                "raw_target_pair_coverage_pct_of_expected_dates": 98.7316,
                "option_date_coverage_pct": 99.239,
                "raw_underlying_price_date_coverage_pct": 99.4419,
                "expected_dates_missing_option_rows": ["2025-12-31"],
                "expected_dates_missing_raw_underlying_price": ["2025-12-31"],
                "source_date_bounds": {"last_qqq_option_chain_date": "2025-12-15"},
            },
            "limitations": ["Synthetic test only"],
        }), encoding="utf-8")
        report = auditor.audit_alignment_diagnostic(path)
        self.assertEqual(report["auditStatus"], "SOURCE_DIAGNOSTIC_ONLY")
        self.assertTrue(report["notAStrategyBacktest"])
        self.assertFalse(report["tradeReplayApproved"])
        self.assertEqual(report["rollingWindows"], [])

    def test_nonpositive_daily_wealth_is_blocked(self):
        self.write_rows(self.dates)
        rows = list(csv.DictReader(self.observations.read_text(encoding="utf-8").splitlines()))
        for field in ("baseline_gross_pnl_usd", "candidate_gross_pnl_usd"):
            rows[0][field] = "-200000"
        with self.observations.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        report = self.audit()
        self.assertEqual(report["auditStatus"], "INVALID_INPUT")
        self.assertTrue(any("NAV reached zero or below" in issue for issue in report["issues"]))

    def test_overlapping_rolling_windows_do_not_inflate_generality(self):
        spec = json.loads(self.spec_path.read_text(encoding="utf-8"))
        spec["rollingWindows"][1]["start"] = "2020-07-01"
        self.spec_path.write_text(json.dumps(spec), encoding="utf-8")
        report = self.audit()
        self.assertEqual(report["auditStatus"], "NOT_PASS")
        self.assertTrue(any("overlaps an earlier window" in issue for issue in report["issues"]))

    def test_self_declared_observed_execution_cannot_unlock_probability(self):
        self.write_rows(self.dates)
        rows = list(csv.DictReader(self.observations.read_text(encoding="utf-8").splitlines()))
        for row in rows:
            row["source_class"] = "OBSERVED"
        with self.observations.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        self.write_spec(evidenceClass="OBSERVED", outcomeClass="REAL_EXECUTION")
        report = self.audit()
        self.assertEqual(report["auditStatus"], "PASS_OPERATOR_ATTESTED", report["issues"])
        self.assertFalse(report["sourceAuthenticated"])
        self.assertFalse(report["canCountAsRealExecutionProbability"])
        self.assertEqual(report["realExecutionProbabilityGate"], "BLOCKED_SOURCE_AUTHENTICATION")

    def test_adverse_cost_direction_is_reported_and_gates_pass(self):
        report = self.audit()
        self.assertTrue(all(item["costStressPass"] for item in report["rollingWindows"]))
        self.assertTrue(all(item["adverseCostEffectDeltaPct"] > 0 for item in report["rollingWindows"]))

    def test_all_input_fingerprints_are_stable_hashes(self):
        one = self.audit()
        two = self.audit()
        self.assertEqual(one["inputIntegrity"], two["inputIntegrity"])
        for digest in one["inputIntegrity"].values():
            self.assertRegex(digest, r"^[a-f0-9]{64}$")


if __name__ == "__main__":
    unittest.main(verbosity=2)
