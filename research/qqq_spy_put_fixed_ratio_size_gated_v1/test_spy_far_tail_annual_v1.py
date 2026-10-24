#!/usr/bin/env python3
import unittest
from summarize_spy_far_tail_annual_v1 import build_annual_rows, build_robustness


def row(phase, episode, exit_date, base, tail, hedged, paired=True, label="TAIL_025_DELTA", qty=1, policy="HOLD_10_OR_DTE_LE_7"):
    return {
        "arm": "DTE45", "phase": str(phase), "episode_id": episode, "policy": policy,
        "entry_date": "2020-12-20", "exit_date": exit_date,
        "base_net_pnl_usd": str(base), "tail_net_pnl_usd": str(tail),
        "hedged_net_pnl_usd": str(hedged),
        "paired_realized_comparison": str(paired), "tail_label": label, "tail_quantity": str(qty),
    }


class AnnualSummaryTests(unittest.TestCase):
    def test_same_paired_subset_and_baseline_deduplicated(self):
        rows = [
            row(0, "a", "2021-01-05", -100, -20, -120),
            row(0, "a", "2021-01-05", -100, -20, -120, label="TAIL_05_DELTA"),
            row(0, "b", "2021-02-05", 200, 50, 250),
            row(1, "a", "2021-01-05", -100, -10, -110),
        ]
        annual = build_annual_rows(rows)
        self.assertEqual(len(annual), 3)
        phase0 = next(r for r in annual if r["phase"] == 0 and r["tail_label"] == "TAIL_025_DELTA")
        self.assertEqual(phase0["base_resolved_n_all"], 2)
        self.assertEqual(phase0["paired_n"], 2)
        self.assertEqual(phase0["no_hedge_mean_paired_usd"], 50.0)
        self.assertEqual(phase0["hedged_mean_paired_usd"], 65.0)
        self.assertEqual(phase0["mean_incremental_hedge_usd"], 15.0)
        self.assertEqual(phase0["no_hedge_win_rate_all_resolved_pct"], 50.0)

    def test_unpaired_rows_not_misreported_as_realized_hedged(self):
        rows = [
            row(0, "a", "2021-01-05", -100, -20, -120, paired=True),
            row(0, "b", "2021-02-05", 200, "", "", paired=False),
        ]
        annual = build_annual_rows(rows)
        self.assertEqual(len(annual), 1)
        self.assertEqual(annual[0]["base_resolved_n_all"], 2)
        self.assertEqual(annual[0]["paired_n"], 1)
        self.assertEqual(annual[0]["paired_coverage_pct_of_base_resolved"], 50.0)

    def test_robustness_uses_phase_range_not_pooled_rows(self):
        rows = build_annual_rows([
            row(0, "a", "2022-01-05", 100, -20, 80),
            row(1, "b", "2022-02-05", 200, -10, 190),
        ])
        robust = build_robustness(rows)
        self.assertEqual(len(robust), 1)
        self.assertEqual(robust[0]["paired_n_min"], 1)
        self.assertEqual(robust[0]["paired_n_max"], 1)
        self.assertEqual(robust[0]["no_hedge_mean_paired_phase_min"], 100.0)
        self.assertEqual(robust[0]["no_hedge_mean_paired_phase_max"], 200.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
