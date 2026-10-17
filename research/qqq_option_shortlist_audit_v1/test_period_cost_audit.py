#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path

import period_cost_audit as audit


def row(strategy, date, pnl, mae, legs, risk=500, cap05=1, cap1=1, cap2=1):
    return {
        "strategy_id": strategy,
        "signal_date": date,
        "status": "RESOLVED",
        "net_pnl_usd": pnl,
        "mae_one_unit_usd": mae,
        "terminal_worst_loss_usd": risk,
        "entry_contract_count": sum(x["qty"] for x in legs),
        "contract_legs": json.dumps(legs),
        "units_at_0p5pct_nav_tail_budget": cap05,
        "units_at_1pct_nav_tail_budget": cap1,
        "units_at_2pct_nav_tail_budget": cap2,
    }


CALL_LEGS = [
    {"id":"QQQ251114C00500000","expiry":"2025-11-14","strike":500,"right":"C","side":"buy","qty":1},
    {"id":"QQQ251114C00550000","expiry":"2025-11-14","strike":550,"right":"C","side":"sell","qty":1},
]
HEDGED_LEGS = CALL_LEGS + [
    {"id":"QQQ251114P00450000","expiry":"2025-11-14","strike":450,"right":"P","side":"buy","qty":1}
]


class AuditTests(unittest.TestCase):
    def test_cost_case_adjustments_include_entry_and_exit_friction(self):
        base = row("CALL_DEBIT_50D_10D", "2025-10-01", 100, -200, CALL_LEGS)
        normalized = audit.load_trade_rows_from_dicts([base])[0]
        self.assertAlmostEqual(audit.adjusted_value(normalized, "pnl", "ZERO"), 122.6)
        self.assertAlmostEqual(audit.adjusted_value(normalized, "pnl", "BASE"), 100.0)
        self.assertAlmostEqual(audit.adjusted_value(normalized, "pnl", "STRESS"), 80.0)
        self.assertAlmostEqual(audit.adjusted_value(normalized, "mae", "ZERO"), -177.4)
        self.assertAlmostEqual(audit.adjusted_value(normalized, "mae", "STRESS"), -220.0)

    def test_true_even_median_and_terminal_budget_capacity(self):
        a = audit.load_trade_rows_from_dicts([
            row("S", "2019-01-02", -100, -150, CALL_LEGS, cap05=0, cap1=1, cap2=1),
            row("S", "2024-01-02", 300, -50, CALL_LEGS, cap05=1, cap1=1, cap2=2),
        ])
        full = audit.summarize_group(a, "S", "FULL", "BASE")
        self.assertEqual(full["median_net_pnl_usd"], 100.0)
        self.assertEqual(full["win_rate_pct"], 50.0)
        self.assertEqual(full["events_with_unit_at_0p5pct_tail_budget"], 1)
        self.assertEqual(full["events_with_unit_at_1pct_tail_budget"], 2)

    def test_paired_hedge_requires_identical_call_legs(self):
        call = row("CALL_DEBIT_50D_10D", "2025-10-01", 100, -200, CALL_LEGS)
        hedge = row("CALL_DEBIT_PLUS_LONG_PUT_10D", "2025-10-01", 90, -250, HEDGED_LEGS)
        rows = audit.load_trade_rows_from_dicts([call, hedge])
        paired, mismatch = audit.paired_hedge_rows(rows)
        full_base = next(x for x in paired if x["period"] == "FULL" and x["cost_case"] == "BASE")
        self.assertEqual(mismatch, 0)
        self.assertEqual(full_base["exact_call_leg_pairs"], 1)
        self.assertEqual(full_base["mean_pnl_delta_combo_minus_call_usd"], -10.0)
        self.assertEqual(full_base["mean_mae_delta_combo_minus_call_usd"], -50.0)
        wrong_call = [dict(CALL_LEGS[0], id="QQQ251114C00490000"), CALL_LEGS[1]]
        rows_bad = audit.load_trade_rows_from_dicts([
            row("CALL_DEBIT_50D_10D", "2025-10-01", 100, -200, wrong_call),
            hedge,
        ])
        _, mismatch = audit.paired_hedge_rows(rows_bad)
        self.assertEqual(mismatch, 1)

    def test_duplicate_strategy_event_is_rejected(self):
        items = audit.load_trade_rows_from_dicts([
            row("S", "2024-01-02", 100, -20, CALL_LEGS),
            row("S", "2024-01-02", 200, -10, CALL_LEGS),
        ])
        with self.assertRaises(ValueError):
            audit.validate_unique_events(items)

    def test_source_gate_refuses_unexpected_history_end(self):
        manifest = {
            "source_integrity_status":"PINNED_SOURCE_VERIFICATION_COMPLETED_BY_REUSED_AUDIT",
            "pricing_evidence":"OBSERVED_EOD_QUOTES_WITH_DERIVED_QUOTE_SIDE_REPLAY_NOT_CONFIRMED_FILLS",
            "source_end":"2026-01-01",
        }
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            trades=root/"trades.csv"
            trades.write_text("status\nRESOLVED\n",encoding="utf-8")
            meta=root/"manifest.json"
            meta.write_text(json.dumps(manifest),encoding="utf-8")
            with self.assertRaises(ValueError):
                audit.run(trades, meta, root/"out")


if __name__ == "__main__":
    unittest.main(verbosity=2)
