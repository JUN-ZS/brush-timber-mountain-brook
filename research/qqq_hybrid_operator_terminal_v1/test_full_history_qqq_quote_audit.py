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


    def test_spot_basis_comparison_flags_adjusted_geometry_delta_drift(self):
        daily=[{
            "raw_target_geometry":{"short":100.0,"wing":120.0},
            "adjusted_target_geometry":{"short":95.0,"wing":114.0},
            "raw_target_pair":{
                "short_delta":0.16,"wing_delta":0.08,
                "short_contract_id":"RAW_SHORT","wing_contract_id":"RAW_WING",
            },
            "adjusted_target_pair":{
                "short_delta":0.30,"wing_delta":0.15,
                "short_contract_id":"REPO_SHORT","wing_contract_id":"REPO_WING",
            },
        }]
        result=audit.summarize_basis_comparison(daily)
        self.assertEqual(result["days_with_both_target_pairs"],1)
        self.assertEqual(result["raw_target_pair_days"],1)
        self.assertEqual(result["repo_input_target_pair_days"],1)
        self.assertAlmostEqual(result["raw_spot_target_pair_delta_error"]["short_abs_error_vs_0p16"]["median"],0.0)
        self.assertAlmostEqual(result["repo_input_target_pair_delta_error"]["short_abs_error_vs_0p16"]["median"],0.14)
        self.assertAlmostEqual(result["repo_input_target_pair_delta_error"]["wing_abs_error_vs_0p08"]["median"],0.07)
        self.assertAlmostEqual(result["repo_input_geometry_shift_pct_vs_raw_target"]["short_target_strike"]["median"],-5.0)
        self.assertAlmostEqual(result["repo_input_geometry_shift_pct_vs_raw_target"]["wing_target_strike"]["median"],-5.0)
        self.assertEqual(result["fraction_repo_input_short_delta_gt_0p16"],1.0)
        self.assertEqual(result["fraction_repo_input_wing_delta_gt_0p08"],1.0)
        self.assertEqual(result["fraction_selected_short_contract_differs"],1.0)
        self.assertEqual(result["fraction_selected_wing_contract_differs"],1.0)

    def test_spot_basis_comparison_handles_no_matched_pairs(self):
        result=audit.summarize_basis_comparison([{"raw_target_pair":None,"adjusted_target_pair":None}])
        self.assertEqual(result["days_with_both_target_pairs"],0)
        self.assertEqual(result["raw_spot_target_pair_delta_error"]["short_abs_error_vs_0p16"]["n"],0)
        self.assertIsNone(result["fraction_repo_input_short_delta_gt_0p16"])


    def test_adverse_fill_sensitivity_charges_both_legs_and_keeps_quote_only_label(self):
        daily=[
            {"raw_target_pair":{
                "observed_executable_side_credit":0.30,
                "proxy_model_credit_raw_spot":0.35,
                "chain_iv_model_credit_raw_spot":0.32,
            }},
            {"raw_target_pair":{
                "observed_executable_side_credit":0.02,
                "proxy_model_credit_raw_spot":0.01,
                "chain_iv_model_credit_raw_spot":0.03,
            }},
            {"raw_target_pair":None},
        ]
        result=audit.summarize_adverse_fill_sensitivity(daily)
        self.assertTrue(result["not_a_fill_or_strategy_backtest"])
        self.assertEqual(result["pairs"],2)
        baseline=result["scenarios"][0]
        stress=result["scenarios"][2]  # $0.025 per leg => $0.05/share total
        self.assertAlmostEqual(baseline["observed_side_credit_after_slippage"]["median"],0.16)
        self.assertAlmostEqual(stress["extra_two_leg_cost_per_share_usd"],0.05)
        self.assertAlmostEqual(stress["observed_side_credit_after_slippage"]["median"],0.11)
        self.assertAlmostEqual(stress["fraction_credit_nonpositive"],0.5)
        self.assertAlmostEqual(stress["proxy_model_minus_stressed_side_credit"]["median"],0.07)
        self.assertAlmostEqual(stress["source_iv_model_minus_stressed_side_credit"]["median"],0.065)

    def test_adverse_fill_sensitivity_handles_missing_pairs(self):
        result=audit.summarize_adverse_fill_sensitivity([{"raw_target_pair":None}])
        self.assertEqual(result["pairs"],0)
        self.assertIsNone(result["scenarios"][0]["fraction_credit_nonpositive"])
        self.assertEqual(result["scenarios"][0]["observed_side_credit_after_slippage"]["n"],0)

    def test_annual_file_manifest(self):
        self.assertEqual([x["year"] for x in audit.ANNUAL_FILES],list(range(2018,2026)))
        self.assertTrue(all(len(x["sha"])==40 and x["bytes"]>0 for x in audit.ANNUAL_FILES))
        self.assertEqual(audit.START_DATE,"2018-03-01")
        self.assertEqual(audit.END_DATE,"2025-12-31")

if __name__=="__main__":unittest.main(verbosity=2)
