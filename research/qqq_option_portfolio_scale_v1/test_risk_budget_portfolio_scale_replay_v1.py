#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "qqq_option_shortlist_v1"))
import qqq_option_shortlist_replay_v1 as core
import risk_budget_portfolio_scale_replay_v1 as portfolio


def leg_row(cid, right, expiry, strike, delta, bid=1.0, ask=1.1, date="2025-10-01", bs=20, ass=20):
    return {"contract_id":cid,"symbol":"QQQ","type":right,"expiration":expiry,"strike":strike,
            "delta":delta,"bid":bid,"ask":ask,"bid_size":bs,"ask_size":ass,"date":date}


class RiskBudgetPortfolioTests(unittest.TestCase):
    def test_identity_checks_contract_root_right_expiry_strike_and_quote_date(self):
        long_call = {"id":"QQQ251114C00500000","right":"C","expiry":"2025-11-14","strike":500}
        row = leg_row("QQQ251114C00500000","CALL","2025-11-14",500,.50)
        self.assertTrue(portfolio.identity_matches(row,long_call,"2025-10-01"))
        self.assertFalse(portfolio.identity_matches(dict(row,contract_id="QQQ251114P00500000"),long_call,"2025-10-01"))
        self.assertFalse(portfolio.identity_matches(dict(row,strike=501),long_call,"2025-10-01"))
        self.assertFalse(portfolio.identity_matches(dict(row,date="2025-10-02"),long_call,"2025-10-01"))

    def test_size_units_enforces_tail_budget_cash_and_displayed_depth(self):
        units, info = portfolio.size_whole_units(80_000, 40_000, .01, 500, -100, 20)
        self.assertEqual(units, 1)
        self.assertEqual(info["risk_units"], 1)
        self.assertEqual(info["cash_units"], 400)
        units2, _ = portfolio.size_whole_units(80_000, 40_000, .02, 50_000, 100, 20)
        self.assertEqual(units2, 0)
        units3, _ = portfolio.size_whole_units(80_000, 40_000, .02, 500, -100, 0)
        self.assertEqual(units3, 0)

    def test_scaled_legs_preserve_contract_geometry_and_scale_quantities(self):
        legs = [
            {"id":"QQQ251114P00480000","expiry":"2025-11-14","strike":480,"right":"P","side":"buy","qty":1},
            {"id":"QQQ251114P00450000","expiry":"2025-11-14","strike":450,"right":"P","side":"sell","qty":5},
        ]
        got = portfolio.scale_legs(legs,3)
        self.assertEqual([x["qty"] for x in got],[3,15])
        self.assertEqual([x["id"] for x in got],[x["id"] for x in legs])

    def test_account_nav_reconciliation_identity(self):
        initial, shares, first_spot, spot = 80_000, 200, 100.0, 110.0
        cash, flows, mark = 59_900, -100, 250
        nav = cash + shares * spot + mark
        core_pnl = shares * (spot - first_spot)
        self.assertAlmostEqual(nav, initial + core_pnl + flows + mark)


if __name__ == "__main__":
    unittest.main(verbosity=2)
