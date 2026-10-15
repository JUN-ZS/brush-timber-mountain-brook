import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("cost_sensitivity_audit.py")
SPEC = importlib.util.spec_from_file_location("cost_sensitivity_audit", SCRIPT)
M = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(M)


def policy_rows():
    base = {
        "direction": "LONG_HEAVY_N_LONG_1_SHORT", "ratio_n": "1",
        "n_long": "1", "n_short": "1", "nav_usd": "100000",
        "tail_risk_budget_pct": "0.01", "policy": "TP_1.0PCT_FULL_CLOSE",
        "ratio_units": "1", "sizing_status": "SIZED_WITH_OBSERVED_DEPTH",
        "cohort_episodes": "62", "depth_qualified_episodes": "40", "depth_skipped": "22",
        "mark_coverage_pct": "99.0", "median_trigger_to_action_delay_sessions": "1",
        "deferred_action_sessions": "4", "resolved": "40", "expectancy_usd_per_unit": "20",
        "profit_factor": "1.2", "worst_trade_usd": "-100", "win_rate_pct": "60",
    }
    out = []
    for cost, pnl in (("ZERO_FRICTION_BOUND", 1200), ("BASE_005_065", 800), ("ADVERSE_010_065", 300)):
        out.append({**base, "cost_case": cost, "net_pnl_sum_usd": str(pnl)})
    return out


def friction_rows():
    base = {
        "direction": "LONG_HEAVY_N_LONG_1_SHORT", "ratio_n": "1",
        "nav_usd": "100000", "tail_risk_budget_pct": "0.01",
        "target_pct_nav": "0.01", "state": "OVERALL", "ratio_units": "1",
        "sizing_status": "SIZED_WITH_OBSERVED_DEPTH", "episode_count": "40",
        "mark_observations": "1200", "net_profit_target_usd": "1000",
        "friction_p50_episode_median_usd": "0", "exit_depth_qualified_pct": "95",
        "friction_p95_pct_of_nav": "0.0",
    }
    out = []
    for cost, p95, ratio, gross in (
        ("ZERO_FRICTION_BOUND", 0, "", 1000),
        ("BASE_005_065", 25, 40, 1025),
        ("ADVERSE_010_065", 60, 16.6667, 1060),
    ):
        out.append({
            **base, "cost_case": cost,
            "friction_bar_p95_episode_median_usd": str(p95),
            "net_target_to_friction_p95_ratio": str(ratio),
            "midpoint_profit_needed_p95_usd": str(gross),
        })
    return out


class CostSensitivityAuditTests(unittest.TestCase):
    def test_policy_triplet_pairs_same_strategy_configuration(self):
        rows, meta = M.compare_policy_rows(policy_rows())
        self.assertEqual(len(rows), 1)
        self.assertEqual(meta["complete_zero_base_adverse_triplets"], 1)
        self.assertEqual(meta["incomplete_triplets"], 0)
        row = rows[0]
        self.assertEqual(row["net_pnl_zero_friction_bound_usd"], 1200)
        self.assertEqual(row["net_pnl_base_005_065_usd"], 800)
        self.assertEqual(row["net_pnl_adverse_010_065_usd"], 300)
        self.assertEqual(row["net_pnl_adverse_minus_base_usd"], -500)
        self.assertEqual(row["sample_status"], "DIAGNOSTIC_SAMPLE_ONLY_NOT_FILL_VALIDATION")

    def test_missing_cost_case_is_not_misreported_complete(self):
        rows, meta = M.compare_policy_rows(policy_rows()[:2])
        self.assertEqual(len(rows), 1)
        self.assertEqual(meta["complete_zero_base_adverse_triplets"], 0)
        self.assertEqual(meta["incomplete_triplets"], 1)
        self.assertFalse(rows[0]["all_three_cost_cases_present"])
        self.assertIsNone(rows[0]["net_pnl_adverse_minus_base_usd"])

    def test_friction_bar_requires_episode_and_mark_counts_for_all_costs(self):
        rows, meta = M.compare_friction_rows(friction_rows())
        self.assertEqual(len(rows), 1)
        self.assertEqual(meta["complete_zero_base_adverse_triplets"], 1)
        row = rows[0]
        self.assertEqual(row["bar_sample_status"], "BAR_SAMPLE_OK_DIAGNOSTIC_ONLY")
        self.assertEqual(row["friction_p95_base_usd"], 25)
        self.assertEqual(row["friction_p95_adverse_usd"], 60)
        self.assertEqual(row["friction_p95_adverse_minus_base_usd"], 35)

    def test_zero_units_block_bar_even_with_fictitious_sample_counts(self):
        sample = []
        for x in friction_rows():
            sample.append({**x, "ratio_units": "0", "sizing_status": "BLOCKED_ZERO_WHOLE_UNITS"})
        rows, _ = M.compare_friction_rows(sample)
        self.assertEqual(rows[0]["bar_sample_status"], "BLOCKED_ZERO_WHOLE_UNITS")

    def test_small_regime_is_pending_not_zero_friction(self):
        sample = []
        for x in friction_rows():
            sample.append({**x, "state": "VXN_GTE40", "episode_count": "3", "mark_observations": "15"})
        rows, _ = M.compare_friction_rows(sample)
        self.assertEqual(rows[0]["bar_sample_status"], "PENDING_SMALL_REGIME_SAMPLE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
