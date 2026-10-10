"""Offline checks for the full-history QQQ option quote audit."""
import sys
import unittest
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import full_history_qqq_quote_audit as audit

class FullHistoryAuditTests(unittest.TestCase):
    def test_vix_regime_labels(self):
        self.assertEqual(audit.vix_bucket(14.99),"LOW_LT15")
        self.assertEqual(audit.vix_bucket(15),"NORMAL_15_25")
        self.assertEqual(audit.vix_bucket(25),"ELEVATED_25_35")
        self.assertEqual(audit.vix_bucket(35),"HIGH_GTE35")
        self.assertEqual(audit.vix_bucket(None),"UNKNOWN")

    def test_numeric_summary(self):
        result=audit.summarize_numbers([1,2,3,4,5])
        self.assertEqual(result["n"],5)
        self.assertEqual(result["median"],3)
        self.assertEqual(result["mean"],3)
        self.assertEqual(result["p90"],4)

    def test_spread_metrics(self):
        self.assertAlmostEqual(audit.spread_pct_mid(1.0,1.2),18.1818181818,places=6)
        self.assertIsNone(audit.spread_pct_mid(1.2,1.0))
        self.assertIsNone(audit.spread_pct_mid(0,0.1))

    def test_model_half_spread_matches_preserved_proxy_formula(self):
        self.assertAlmostEqual(audit.model_half_spread_fraction(82.69), 0.078352, places=6)
        self.assertAlmostEqual(audit.model_half_spread_fraction(12.42), 0.025, places=6)
        self.assertAlmostEqual(audit.model_half_spread_fraction(1000), 0.1, places=6)
        self.assertIsNone(audit.model_half_spread_fraction(None))

    def test_coverage_denominator_includes_dates_after_source_cutoff(self):
        expected=["2025-12-29","2025-12-30","2025-12-31"]
        spots={"2025-12-29":{},"2025-12-30":{}}
        daily=[
            {"date":"2025-12-29","option_rows":10,"raw_target_pair":{"observed_executable_side_credit":0.2}},
            {"date":"2025-12-30","option_rows":10,"raw_target_pair":None},
        ]
        result=audit.build_coverage_summary(expected,spots,daily,"2025-12-29","2025-12-31")
        self.assertEqual(result["expected_trading_dates_from_repo_universe"],3)
        self.assertEqual(result["expected_dates_with_raw_underlying_price"],2)
        self.assertAlmostEqual(result["raw_underlying_price_date_coverage_pct"],200/3)
        self.assertEqual(result["dates_with_qqq_option_rows"],2)
        self.assertAlmostEqual(result["option_date_coverage_pct"],200/3)
        self.assertEqual(result["dates_with_raw_target_pairs"],1)
        self.assertAlmostEqual(result["raw_target_pair_coverage_pct_of_expected_dates"],100/3)
        self.assertEqual(result["expected_dates_missing_raw_underlying_price"],["2025-12-31"])
        self.assertEqual(result["expected_dates_missing_option_rows"],["2025-12-31"])
        self.assertEqual(result["last_expected_trading_date"],"2025-12-31")
        self.assertFalse(result["source_date_bounds"]["source_window_complete_through_last_expected_session"])

    def test_finalize_day_uses_helper_metric_keys(self):
        quotes={
            "row_count":50,"valid_two_sided_quote_pct":88.0,"call_rows":25,"put_rows":25,
            "call_candidates_30_60_dte_abs_delta_0p03_0p10":7,
        }
        geom={"short_target_strike":100.0,"long_target_strike":110.0}
        match={
            "status":"MATCHED_NEAREST_20_40_DTE_EXPIRY","selected_expiry":"2026-01-16",
            "calendar_dte":17,"eligible_standard_grid_call_rows_in_expiry":42,
            "model_target_nearest_pairs":{"raw_close_spot":None,"repo_adjusted_spot":None},
        }
        with patch.object(audit.base,"inspect_day",return_value=quotes), \
             patch.object(audit.base,"model_qqq_quote",return_value=geom), \
             patch.object(audit.base,"nearest_quote_model_pairs",return_value=match):
            result=audit.finalize_day("2025-12-30",[{}],
                {"2025-12-30":{"repo_qqq_input":99.0,"vix":18.0}},
                {"2025-12-30":{"raw_close":100.0,"adjusted_close":99.0,"split_coefficient":1.0}})
        self.assertEqual(result["candidate_calls_30_60_dte_abs_delta_003_010"],7)
        self.assertEqual(result["eligible_rows_in_expiry"],42)

    def test_annual_file_manifest(self):
        self.assertEqual([x["year"] for x in audit.ANNUAL_FILES],list(range(2018,2026)))
        self.assertTrue(all(len(x["sha"])==40 and x["bytes"]>0 for x in audit.ANNUAL_FILES))
        self.assertEqual(audit.START_DATE,"2018-03-01")
        self.assertEqual(audit.END_DATE,"2025-12-31")

if __name__=="__main__":unittest.main(verbosity=2)
