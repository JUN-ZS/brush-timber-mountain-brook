"""Offline unit tests for QQQ FAR CALL causal decomposition V2."""
import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qqq_far_call_incremental_decomposition as study


def trade(pnl=10.0, exit_reason="DTE_LE_7", scenario=None):
    row = {
        "entry_gross_credit_cash_usd": "200.00",
        "entry_execution_costs_usd": "10.00",
        "exit_gross_debit_cash_usd": "160.00",
        "exit_execution_costs_usd": "20.00",
        "recomputed_net_pnl_usd": str(pnl),
        "realized_pnl_after_scenario_costs": str(pnl),
        "attribution_status": "PASS_CASH_FLOW_RECONCILIATION",
        "exit_reason": exit_reason,
        "holding_calendar_days": "10",
        "exit_quote_missing_sessions": "2",
        "exit_debit_basis": "OBSERVED_EOD_SHORT_ASK_MINUS_WING_BID",
        "entry_gross_credit_per_share": "1.00",
        "entry_net_credit_ps": "0.95",
        "entry_quote_quality_bucket": "TIGHT_LE_10PCT_MID",
    }
    if scenario:
        row.update(scenario)
    return row


def event(event_name, reason="", scenario_id=None):
    return {
        "event": event_name,
        "reason": reason,
        "scenario_id": scenario_id or "SOURCE_MAX_LOSS_0P8PCT_NAV|SLIP_PER_LEG_0.000|COMM_PER_CONTRACT_SIDE_0.00",
        "scenario": "SOURCE_MAX_LOSS_0P8PCT_NAV",
        "slippage_per_leg_usd": "0.0",
        "commission_per_contract_per_side_usd": "0.0",
        "gross_credit_per_share": "1.0",
        "net_credit_per_share": "0.95",
        "quantity": "2",
    }


def daily(day, nav, baseline, open_flag="False"):
    return {
        "date": day,
        "nav_eod_marked": "" if nav is None else str(nav),
        "no_call_baseline_nav": "" if baseline is None else str(baseline),
        "nav_mark_status": "MISSING_MARK" if nav is None else "OK",
        "position_open": open_flag,
        "pending_close": "False",
        "pending_open": "False",
        "scenario_id": "SOURCE_MAX_LOSS_0P8PCT_NAV|SLIP_PER_LEG_0.000|COMM_PER_CONTRACT_SIDE_0.00",
        "scenario": "SOURCE_MAX_LOSS_0P8PCT_NAV",
        "slippage_per_leg_usd": "0.0",
        "commission_per_contract_per_side_usd": "0.0",
    }


class IncrementalDecompositionTests(unittest.TestCase):
    def test_cashflow_waterfall_independently_reconciles_to_cent(self):
        result = study.independently_reconcile([trade()])
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["independently_rechecked_rows"], 1)
        self.assertEqual(result["max_abs_independent_reconciliation_error_usd"], 0.0)

    def test_cashflow_waterfall_flags_mismatch_above_one_cent(self):
        row = trade()
        row["realized_pnl_after_scenario_costs"] = "10.02"
        result = study.independently_reconcile([row])
        self.assertEqual(result["status"], "FAIL_INDEPENDENT_CASHFLOW_RECONCILIATION")
        self.assertEqual(result["independent_failures_over_1cent"], 1)

    def test_missing_cashflow_component_blocks_reconciliation(self):
        row = trade()
        row["exit_execution_costs_usd"] = ""
        result = study.independently_reconcile([row])
        self.assertEqual(result["status"], "BLOCKED_INDEPENDENT_CASHFLOW_RECONCILIATION")
        self.assertEqual(result["blocked_rows"], 1)

    def test_paired_nav_excludes_unmarked_dates_without_interpolation(self):
        rows = [
            daily("2024-01-02", 100200, 100000),
            daily("2024-01-03", None, 100100, "True"),
            daily("2024-01-04", 99950, 100000),
        ]
        result = study.summarize_path(rows, 3)
        self.assertEqual(result["matched_nav_sessions"], 2)
        self.assertEqual(result["unmatched_nav_sessions"], 1)
        self.assertEqual(result["last_observed_incremental_nav_usd"], -50)
        self.assertEqual(result["minimum_observed_incremental_nav_usd"], -50)
        self.assertEqual(result["maximum_observed_incremental_nav_usd"], 200)
        self.assertEqual(result["position_open_but_unmarked_days"], 1)
        self.assertEqual(result["daily_row_count_matches_expected"], True)

    def test_exit_attribution_keeps_existing_reason_groups_separate(self):
        rows = [
            trade(-20, "DTE_LE_7"),
            trade(40, "DTE_LE_7"),
            trade(-30, "PNL_OVER_MAXLOSS_LE_NEG_0P55"),
        ]
        result = study.summarize_exits(rows)
        self.assertEqual(result["DTE_LE_7"]["closed_trade_count"], 2)
        self.assertEqual(result["DTE_LE_7"]["net_pnl_usd"], 20)
        self.assertEqual(result["PNL_OVER_MAXLOSS_LE_NEG_0P55"]["net_pnl_usd"], -30)
        self.assertEqual(result["DTE_LE_7"]["exit_quote_missing_sessions"], 4)

    def test_cost_scenario_ids_do_not_collapse_different_assumptions(self):
        rows = [
            {"scenario": "BASE", "slippage_per_leg_usd": "0", "commission_per_contract_per_side_usd": "0"},
            {"scenario": "BASE", "slippage_per_leg_usd": "0.05", "commission_per_contract_per_side_usd": "0.65"},
        ]
        groups = study.group_scenarios(rows)
        self.assertEqual(len(groups), 2)
        self.assertIn("BASE|SLIP_PER_LEG_0.000|COMM_PER_CONTRACT_SIDE_0.00", groups)
        self.assertIn("BASE|SLIP_PER_LEG_0.050|COMM_PER_CONTRACT_SIDE_0.65", groups)

    def test_negative_base_screen_does_not_authorize_integration(self):
        key = "SOURCE_MAX_LOSS_0P8PCT_NAV|SLIP_PER_LEG_0.000|COMM_PER_CONTRACT_SIDE_0.00"
        scenario = {
            "scenario": "SOURCE_MAX_LOSS_0P8PCT_NAV",
            "budget_kind": "max_loss",
            "budget_pct_nav": 0.008,
            "slippage_per_leg_usd": 0.0,
            "commission_per_contract_per_side_usd": 0.0,
            "opened_spreads": 1,
            "closed_spreads": 1,
            "unresolved_or_open_position_at_end": 0,
            "missing_position_mark_sessions": 1,
            "closed_trade_net_pnl_sum_usd": -10,
            "paired_nav_diagnostic": {"last_incremental_nav_vs_no_call_usd": -5},
            "nav_path_complete": False,
        }
        summary = {
            "coverage": {
                "expected_sessions": 2,
                "chain_sessions": 2,
                "first_expected_date": "2024-01-02",
                "last_expected_date": "2024-01-03",
                "last_source_observation": "2024-01-03",
                "terminal_missing_sessions": [],
            },
            "scenarios": [scenario],
        }
        t = trade(-10)
        t["exit_gross_debit_cash_usd"] = "180.00"
        t["recomputed_net_pnl_usd"] = "-10.00"
        t["scenario_id"] = key
        t["scenario"] = scenario["scenario"]
        t["slippage_per_leg_usd"] = "0.0"
        t["commission_per_contract_per_side_usd"] = "0.0"
        e = event("OPEN")
        d = [daily("2024-01-02", 99990, 100000), daily("2024-01-03", 99995, 100000)]
        report = study.build_report(summary, [t], [e], d)
        self.assertEqual(report["decision"]["base_screen"], "FAILS_CURRENT_BASE_SCREEN")
        self.assertFalse(report["decision"]["integration_eligible"])
        self.assertFalse(report["decision"]["main_changed"])
        self.assertFalse(report["decision"]["broker_orders_enabled"])

    def test_output_writer_creates_json_markdown_and_csv(self):
        report = {
            "study_id": study.STUDY_ID,
            "status": study.REPORT_STATUS,
            "decision": {"base_screen": "NOT_ESTABLISHED", "integration_eligible": False,
                         "frozen_original_hybrid_changed": False, "main_changed": False,
                         "broker_orders_enabled": False},
            "global_ledger_quality": {
                "status": "PASS", "independently_rechecked_rows": 0, "closed_trade_rows": 0,
                "max_abs_independent_reconciliation_error_usd": 0.0,
            },
            "evidence_limits": {"terminal_source_gap_sessions": 0, "source_last_observation": None},
            "coverage": {"expected_sessions": 0, "chain_sessions": 0, "first_expected_date": None,
                         "last_expected_date": None, "last_source_observation": None,
                         "terminal_missing_sessions": []},
            "scenario_decompositions": {},
            "cost_scenario_comparisons": [],
            "exit_mechanism_csv_rows": [],
        }
        with tempfile.TemporaryDirectory() as temp:
            paths = study.write_outputs(report, temp)
            self.assertTrue(Path(paths["json"]).is_file())
            self.assertTrue(Path(paths["markdown"]).is_file())
            self.assertTrue(Path(paths["csv"]).is_file())
            self.assertEqual(json.loads(Path(paths["json"]).read_text(encoding="utf-8"))["study_id"],
                             study.STUDY_ID)
            with Path(paths["csv"]).open("r", encoding="utf-8") as handle:
                self.assertTrue(next(csv.reader(handle)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
