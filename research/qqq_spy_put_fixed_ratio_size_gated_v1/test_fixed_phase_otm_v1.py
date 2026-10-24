#!/usr/bin/env python3
from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import audit_fixed_phase_otm_v1 as audit


def sample_row(episode_id="1", qqq_entry_spot="490", spy_entry_spot="555"):
    qqq_strike, spy_strike = 450.0, 550.0
    qqq_signal_spot, spy_signal_spot = 500.0, 520.0
    qsig = audit.put_moneyness(qqq_signal_spot, qqq_strike)
    ssig = audit.put_moneyness(spy_signal_spot, spy_strike)
    qentry = audit.put_moneyness(float(qqq_entry_spot), qqq_strike)
    sentry = audit.put_moneyness(float(spy_entry_spot), spy_strike)
    return {
        "episode_id": episode_id, "signal_date": "2025-01-10", "entry_date": "2025-01-13",
        "expiry": "2025-02-21",
        "qqq_contract_id": "QQQ250221P00450000", "spy_contract_id": "SPY250221P00550000",
        "qqq_strike": str(qqq_strike), "spy_strike": str(spy_strike),
        "qqq_spot_signal": str(qqq_signal_spot), "spy_spot_signal": str(spy_signal_spot),
        "qqq_spot_entry": qqq_entry_spot, "spy_spot_entry": spy_entry_spot,
        "qqq_abs_delta": "0.25", "spy_abs_delta": "0.30",
        "qqq_otm_pct_signal": str(qsig["otm_pct"]), "qqq_moneyness_signal": qsig["status"],
        "spy_otm_pct_signal": str(ssig["otm_pct"]), "spy_moneyness_signal": ssig["status"],
        "qqq_otm_pct_entry": str(qentry["otm_pct"]), "qqq_moneyness_entry": qentry["status"],
        "spy_otm_pct_entry": str(sentry["otm_pct"]), "spy_moneyness_entry": sentry["status"],
        "long_qqq_qty": "1", "short_spy_qty": "3",
    }


class PutMoneynessTests(unittest.TestCase):
    def test_signed_otm_percent_and_status(self):
        self.assertEqual(audit.put_moneyness(100, 95)["status"], "OTM")
        self.assertAlmostEqual(audit.put_moneyness(100, 95)["otm_pct"], 5.0)
        self.assertEqual(audit.put_moneyness(100, 100)["status"], "ATM")
        self.assertAlmostEqual(audit.put_moneyness(100, 105)["otm_pct"], -5.0)
        self.assertEqual(audit.put_moneyness(100, 105)["status"], "ITM")

    def test_bad_spot_rejected(self):
        with self.assertRaisesRegex(ValueError, "must be > 0"):
            audit.put_moneyness(0, 95)


class OtmLedgerAuditTests(unittest.TestCase):
    def test_recomputes_both_legs_at_signal_and_entry(self):
        details, delta = audit.make_detail_rows(2, [sample_row()])
        self.assertEqual(len(details), 2)
        self.assertEqual(len(delta), 2)
        by_leg = {r["leg"]: r for r in details}
        self.assertEqual(by_leg["QQQ"]["moneyness_at_entry"], "OTM")
        self.assertAlmostEqual(by_leg["QQQ"]["otm_pct_at_entry"], (490 - 450) / 490 * 100)
        self.assertEqual(by_leg["SPY"]["moneyness_at_signal"], "ITM")
        self.assertEqual(by_leg["SPY"]["moneyness_at_entry"], "OTM")

    def test_stale_reported_percent_rejected(self):
        row = sample_row()
        row["qqq_otm_pct_entry"] = "3.0"
        with self.assertRaisesRegex(ValueError, "does not reconcile"):
            audit.make_detail_rows(0, [row])

    def test_wrong_contract_identity_rejected(self):
        row = sample_row()
        row["spy_contract_id"] = "QQQ250221P00550000"
        with self.assertRaisesRegex(ValueError, "invalid standard SPY PUT identity"):
            audit.make_detail_rows(0, [row])

    def test_reports_non_otm_warning_without_filtering_sample(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "results"
            out = root / "fixed_phase_otm_audit"
            row = sample_row(qqq_entry_spot="440", spy_entry_spot="540")
            fields = list(row)
            for phase in range(5):
                folder = root / "fixed_phase_sensitivity" / f"phase_{phase}"
                folder.mkdir(parents=True)
                with (folder / "entry_cohort.csv").open("w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=fields)
                    writer.writeheader()
                    writer.writerow(row)
            result = audit.build(root, out)
            self.assertEqual(result["phase_count"], 5)
            self.assertEqual(result["detail_leg_rows"], 10)
            self.assertEqual(result["non_otm_at_entry_leg_rows"], 10)
            self.assertEqual(result["status"], "WARN_NON_OTM_LEGS_FOUND")
            self.assertTrue((out / "report.md").is_file())
            self.assertTrue((out / "phase_leg_otm_summary.csv").is_file())


if __name__ == "__main__":
    unittest.main(verbosity=2)
