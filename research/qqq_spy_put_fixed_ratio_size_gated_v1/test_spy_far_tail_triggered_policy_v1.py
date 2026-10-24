#!/usr/bin/env python3
import unittest
from summarize_spy_far_tail_triggered_policy_v1 import policy_row_metrics, summarize


def base_row(key, base, triggered=False, entry=False, paired=False, hedged=None, premium=None, exit_year=2020):
    return {
        "trade_key": key, "arm": "DTE45", "phase": "0", "policy": "HOLD_20_OR_DTE_LE_7",
        "episode_id": key, "trigger_label": "ENTRY_SPOT_DRAWDOWN_3PCT", "trigger_drop_pct": "3.0",
        "tail_label": "TAIL_025_DELTA", "tail_quantity": "1", "trigger_fired": str(triggered),
        "base_net_pnl_usd": str(base), "base_resolved": "True", "tail_entry_executable": str(entry),
        "paired_realized_comparison": str(paired), "hedged_net_pnl_usd": "" if hedged is None else str(hedged),
        "tail_entry_gross_premium_usd": "" if premium is None else str(premium),
        "exit_date": f"{exit_year}-12-01", "target_observation_date": f"{exit_year}-12-01",
    }


class PolicyEvaluationTests(unittest.TestCase):
    def test_untriggered_and_blocked_trades_stay_at_base_pnl(self):
        rows = [
            base_row("a", 100, triggered=False, entry=False),
            base_row("b", -50, triggered=True, entry=False),
            base_row("c", -100, triggered=True, entry=True, paired=True, hedged=-60, premium=20),
        ]
        metrics, eval_map = policy_row_metrics(rows)
        self.assertEqual(metrics["base_resolved_n"], 3)
        self.assertEqual(metrics["policy_evaluable_n"], 3)
        self.assertEqual(metrics["trigger_signal_n_resolved"], 2)
        self.assertEqual(metrics["conditional_increment_mean_policy_evaluable_usd"], 13.33)
        self.assertEqual(metrics["conditional_strategy_mean_policy_evaluable_usd"], -3.33)

    def test_entered_but_unpriced_is_unknown_not_zero(self):
        rows = [
            base_row("a", 100, triggered=False, entry=False),
            base_row("b", -100, triggered=True, entry=True, paired=False, premium=15),
        ]
        metrics, eval_map = policy_row_metrics(rows)
        self.assertEqual(metrics["base_resolved_n"], 2)
        self.assertEqual(metrics["unknown_entered_hedge_n_resolved"], 1)
        self.assertEqual(metrics["policy_evaluable_n"], 1)
        self.assertEqual(metrics["policy_evaluable_coverage_pct_of_base_resolved"], 50.0)
        self.assertEqual(metrics["conditional_strategy_mean_policy_evaluable_usd"], 100.0)

    def test_build_summary_compares_qty_on_common_policy_sample(self):
        rows = [
            base_row("a", -100, triggered=True, entry=True, paired=True, hedged=-120, premium=20),
            base_row("a", -100, triggered=True, entry=True, paired=True, hedged=-140, premium=60),
        ]
        rows[0]["tail_quantity"] = "1"
        rows[1]["tail_quantity"] = "3"
        summary, annual = summarize(rows)
        one = next(r for r in summary if r["tail_quantity"] == 1)
        three = next(r for r in summary if r["tail_quantity"] == 3)
        self.assertEqual(three["common_policy_evaluable_1x3_n"], 1)
        self.assertEqual(three["common_3x_extra_drag_per_trade_usd"], -20.0)
        self.assertEqual(len(annual), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
