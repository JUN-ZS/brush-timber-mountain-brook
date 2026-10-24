#!/usr/bin/env python3
import unittest
from unittest.mock import patch

from run_spy_far_tail_holding_trigger_v1 import (
    RULES,
    first_trigger_date,
    outcome_for_hedge,
    sample_period,
    trigger_conditions,
    package_mark_pnl_from_rows,
    iter_merged_symbol_days,
    base_engine,
)


class HoldingTriggerTests(unittest.TestCase):
    def test_delta_trigger_uses_absolute_put_delta_and_frozen_boundary(self):
        self.assertTrue(trigger_conditions(-0.35, 100.0, 100.0, 0.0, 1000.0)["hits"][RULES[0]])
        self.assertFalse(trigger_conditions(-0.3499, 100.0, 100.0, 0.0, 1000.0)["hits"][RULES[0]])

    def test_spy_drawdown_trigger_is_entry_relative(self):
        out = trigger_conditions(0.20, 100.0, 95.0, 0.0, 1000.0)
        self.assertTrue(out["hits"][RULES[1]])
        self.assertAlmostEqual(out["drawdown_pct"], 5.0)
        self.assertFalse(trigger_conditions(0.20, 100.0, 95.01, 0.0, 1000.0)["hits"][RULES[1]])

    def test_package_loss_trigger_scales_with_initial_short_credit(self):
        out = trigger_conditions(0.20, 100.0, 100.0, -500.0, 1000.0)
        self.assertTrue(out["hits"][RULES[2]])
        self.assertFalse(trigger_conditions(0.20, 100.0, 100.0, -499.99, 1000.0)["hits"][RULES[2]])
        self.assertAlmostEqual(out["package_loss_limit_usd"], -500.0)

    def test_or_rule_triggers_on_any_available_component(self):
        out = trigger_conditions(0.40, None, None, None, None)
        self.assertTrue(out["hits"][RULES[0]])
        self.assertTrue(out["hits"][RULES[3]])
        self.assertFalse(out["hits"][RULES[1]])
        self.assertFalse(out["hits"][RULES[2]])

    def test_no_lookahead_first_trigger_date(self):
        rows = [
            ("2023-01-03", {"delta": 0.20, "entry_spot": 100, "spot": 100, "mtm": 0, "credit": 1000}),
            ("2023-01-04", {"delta": 0.25, "entry_spot": 100, "spot": 98, "mtm": -100, "credit": 1000}),
            ("2023-01-05", {"delta": 0.26, "entry_spot": 100, "spot": 94, "mtm": -800, "credit": 1000}),
            ("2023-01-06", {"delta": 0.45, "entry_spot": 100, "spot": 91, "mtm": -1200, "credit": 1000}),
        ]
        self.assertEqual(first_trigger_date(rows, RULES[1]), "2023-01-05")
        self.assertIsNone(first_trigger_date(rows[:2], RULES[1]))
        self.assertEqual(first_trigger_date(rows, RULES[0]), "2023-01-06")

    def test_same_day_delta_and_drawdown_fire_independently(self):
        out = trigger_conditions(0.40, 100.0, 90.0, None, None)
        self.assertTrue(out["hits"][RULES[0]])
        self.assertTrue(out["hits"][RULES[1]])
        self.assertTrue(out["hits"][RULES[3]])
        self.assertEqual(set(out["trigger_reasons"]), {RULES[0], RULES[1]})

    def test_missing_values_do_not_trigger_by_themselves(self):
        out = trigger_conditions(None, 100.0, None, None, 1000.0)
        self.assertFalse(any(out["hits"].values()))
        self.assertIsNone(out["drawdown_pct"])
        self.assertFalse(out["availability"][RULES[0]])
        self.assertFalse(out["availability"][RULES[1]])
        self.assertFalse(out["availability"][RULES[2]])

    def test_missing_exit_never_becomes_zero_or_base_pnl_after_entry(self):
        self.assertEqual(outcome_for_hedge(False, False, -100.0, False, None),
                         (-100.0, "NO_TRIGGER_NO_HEDGE"))
        self.assertEqual(outcome_for_hedge(True, False, -100.0, False, None),
                         (-100.0, "TRIGGERED_BUT_TAIL_ENTRY_UNAVAILABLE"))
        self.assertEqual(outcome_for_hedge(True, True, -100.0, True, 40.0),
                         (-60.0, "HEDGE_PAIRED_REALIZED"))
        pnl, reason = outcome_for_hedge(True, True, -100.0, False, None)
        self.assertIsNone(pnl)
        self.assertEqual(reason, "HEDGE_ENTERED_EXIT_UNAVAILABLE")

    def test_unresolved_base_pnl_stays_missing_even_when_a_tail_mark_exists(self):
        pnl, reason = outcome_for_hedge(True, True, None, True, 999.0)
        self.assertIsNone(pnl)
        self.assertEqual(reason, "BASE_UNRESOLVED_MARK_ONLY")

    def test_underlying_only_close_day_is_retained_without_option_quotes(self):
        snapshots = {
            "QQQ": [
                ("2023-01-03", [{"symbol": "QQQ", "date": "2023-01-03"}]),
                ("2023-01-05", [{"symbol": "QQQ", "date": "2023-01-05"}]),
            ],
            "SPY": [
                ("2023-01-03", [{"symbol": "SPY", "date": "2023-01-03"}]),
                ("2023-01-05", [{"symbol": "SPY", "date": "2023-01-05"}]),
            ],
        }

        def fake_iter(paths, symbol, start_day, end_day, stats):
            for day, rows in snapshots[symbol]:
                stats["chain_dates"] += 1
                stats["put_rows"] += len(rows)
                stats["last_chain_date"] = day
                yield day, rows

        stats = {
            "qqq": {"chain_dates": 0, "put_rows": 0, "first_chain_date": None, "last_chain_date": None},
            "spy": {"chain_dates": 0, "put_rows": 0, "first_chain_date": None, "last_chain_date": None},
        }
        with patch.object(base_engine, "iter_symbol_days", side_effect=fake_iter):
            rows = list(iter_merged_symbol_days(
                ["qqq"], ["spy"], "2023-01-03", "2023-01-05", stats,
                ["2023-01-03", "2023-01-04", "2023-01-05"],
            ))
        self.assertEqual([row[0] for row in rows], ["2023-01-03", "2023-01-04", "2023-01-05"])
        self.assertEqual(rows[1][1:], ([], []))
        self.assertEqual(stats["qqq"]["first_chain_date"], "2023-01-03")
        self.assertEqual(stats["spy"]["last_chain_date"], "2023-01-05")

    def test_locked_chronological_split_is_by_entry_year(self):
        self.assertEqual(sample_period("2018-03-02"), "TRAIN_2018_2022")
        self.assertEqual(sample_period("2022-12-30"), "TRAIN_2018_2022")
        self.assertEqual(sample_period("2023-01-03"), "LOCKED_HOLDOUT_2023_2025")
        self.assertEqual(sample_period("2025-12-12"), "LOCKED_HOLDOUT_2023_2025")
        with self.assertRaises(ValueError):
            sample_period("2026-01-02")


    def test_package_mtm_converts_csv_numeric_strings_before_arithmetic(self):
        trade = {
            "long_qqq_qty": "1",
            "short_spy_qty": "3",
            "qqq_entry_ask": "1.00",
            "spy_entry_bid": "2.00",
            "base_slippage_per_share": "0.05",
            "base_commission_per_contract_per_side": "0.65",
        }
        qrow = {"bid": 1.50}
        srow = {"ask": 1.00}
        self.assertAlmostEqual(package_mark_pnl_from_rows(trade, qrow, srow), 304.80, places=2)

    def test_package_mtm_rejects_missing_entry_cash_fields(self):
        trade = {
            "long_qqq_qty": "1", "short_spy_qty": "3", "qqq_entry_ask": "",
            "spy_entry_bid": "2.00", "base_slippage_per_share": "0.05",
            "base_commission_per_contract_per_side": "0.65",
        }
        with self.assertRaisesRegex(ValueError, "qqq_entry_ask"):
            package_mark_pnl_from_rows(trade, {"bid": 1.50}, {"ask": 1.00})


if __name__ == "__main__":
    unittest.main(verbosity=2)
