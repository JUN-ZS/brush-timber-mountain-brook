#!/usr/bin/env python3
"""Unit checks for the single-account NAV replay."""
from __future__ import annotations

import unittest

import run_spy_far_tail_nav_account_v1 as nav


class NavAccountTests(unittest.TestCase):
    def sample_trade(self):
        return {
            "trade_key": "sample",
            "long_qqq_qty": "1",
            "short_spy_qty": "3",
            "qqq_entry_ask": "2.00",
            "spy_entry_bid": "1.00",
            "base_slippage_per_share": "0.05",
            "base_commission_per_contract_per_side": "0.65",
            "spy_strike": "500",
            "qqq_contract_id": "QQQID",
            "spy_contract_id": "SPYID",
        }

    def test_open_cashflow_includes_both_leg_entry_costs(self):
        self.assertAlmostEqual(nav.base_open_cashflow(self.sample_trade()), 77.40, places=2)

    def test_close_cashflow_uses_liquidation_sides_and_exit_costs(self):
        trade = self.sample_trade()
        qrow = {"bid": "3.00"}
        srow = {"ask": "2.00"}
        self.assertAlmostEqual(nav.base_close_cashflow(trade, qrow, srow), -322.60, places=2)

    def test_cash_only_account_nav_equals_cash_when_flat(self):
        account = nav.make_account(10_000.0, 0, "NO_HEDGE", 0)
        row = nav.account_nav(account, "2020-01-02", {}, {})
        self.assertEqual(row["nav_usd"], 10_000.0)
        self.assertTrue(row["mark_complete"])
        self.assertEqual(row["open_base_positions_n"], 0)

    def test_missing_exact_contract_mark_is_blank_not_forward_filled(self):
        account = nav.make_account(10_000.0, 0, "NO_HEDGE", 0)
        account["positions"]["sample"] = {
            "trade": self.sample_trade(),
            "tail_open": False,
            "base_closed": False,
            "tail_qty": 0,
        }
        row = nav.account_nav(account, "2020-01-03", {}, {})
        self.assertIsNone(row["nav_usd"])
        self.assertFalse(row["mark_complete"])
        self.assertEqual(row["unmarked_position_n"], 1)
        self.assertEqual(account["mark_gap_dates"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
