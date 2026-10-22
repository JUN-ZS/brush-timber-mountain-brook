#!/usr/bin/env python3
"""Offline tests for the independent-leg N sweep."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import qqq_spy_put_independent_leg_sizing_v1 as sizing

def episode(policy="HOLD_5_SESSIONS", status="RESOLVED", qqty=2, sqty=3,
            q_entry=4.0, q_exit=5.0, s_entry=5.0, s_exit=6.0, pnl=None):
    q_gross = (q_exit-q_entry)*100*qqty if status == "RESOLVED" else ""
    s_gross = (s_entry-s_exit)*100*sqty if status == "RESOLVED" else ""
    cost = (qqty+sqty)*sizing.round_trip_cost_per_contract(0.05, 0.65)
    if pnl is None and status == "RESOLVED":
        pnl = q_gross+s_gross-cost
    return {
        "episode_id":"1", "policy":policy, "status":status,
        "long_qqq_qty":str(qqty), "short_spy_qty":str(sqty),
        "qqq_entry_ask":str(q_entry), "spy_entry_bid":str(s_entry),
        "exit_qqq_bid":str(q_exit) if status == "RESOLVED" else "",
        "exit_spy_ask":str(s_exit) if status == "RESOLVED" else "",
        "qqq_long_gross_pnl_usd":str(q_gross), "spy_short_gross_pnl_usd":str(s_gross),
        "net_pnl_usd":str(pnl if pnl is not None else ""),
        "qqq_long_premium_debit_usd":str(q_entry*100*qqty),
        "spy_short_premium_credit_usd":str(s_entry*100*sqty),
        "premium_mismatch_usd":"0", "premium_match_pct":"100",
    }

class IndependentLegSizingTests(unittest.TestCase):
    def test_unit_gross_and_round_trip_cost(self):
        r=episode(qqty=2, sqty=3, q_entry=4, q_exit=5, s_entry=5, s_exit=6)
        self.assertAlmostEqual(sizing.qqq_unit_gross(r),100.0)
        self.assertAlmostEqual(sizing.spy_unit_gross(r),-100.0)
        self.assertAlmostEqual(sizing.round_trip_cost_per_contract(0.05,0.65),11.30)

    def test_independent_leg_isolated_from_other_leg(self):
        r=episode()
        cost={"name":"BASE_COST","slippage":0.05,"commission":0.65}
        q=sizing.measure_strategy([r],"QQQ_LONG_PUT_STANDALONE","HOLD_5_SESSIONS",
            lambda _:1,lambda _:0,cost,"TEST")
        s=sizing.measure_strategy([r],"SPY_SHORT_PUT_STANDALONE","HOLD_5_SESSIONS",
            lambda _:0,lambda _:1,cost,"TEST")
        self.assertAlmostEqual(q["mean_net_pnl_usd"],100-11.3)
        self.assertAlmostEqual(s["mean_net_pnl_usd"],-100-11.3)
        self.assertEqual(q["mean_spy_gross_pnl_usd"],0.0)
        self.assertEqual(s["mean_qqq_gross_pnl_usd"],0.0)

    def test_unresolved_not_assigned_zero(self):
        rows=[episode(),episode(status="UNRESOLVED_SOURCE_END")]
        result=sizing.measure_strategy(rows,"FIXED_PAIR_CROSS_GRID","HOLD_5_SESSIONS",
            lambda r:1,lambda r:1,{"name":"BASE_COST","slippage":0.05,"commission":0.65},"TEST")
        self.assertEqual((result["opened_n"],result["resolved_n"],result["unresolved_n"]),(2,1,1))
        self.assertEqual(result["win_rate_pct"],0.0)

    def test_pair_contract_cap_has_36_cells_at_nine(self):
        cells=[(q,s) for q in range(1,10) for s in range(1,10) if q+s<=9]
        self.assertEqual(len(cells),36)
        self.assertTrue(all(q+s<=9 for q,s in cells))
        self.assertIn((1,5),cells); self.assertIn((4,5),cells)
        self.assertNotIn((5,5),cells)

    def test_premium_match_is_cash_flow_ratio_only(self):
        self.assertEqual(sizing.premium_match_pct(600.0,600.0),100.0)
        self.assertAlmostEqual(sizing.premium_match_pct(500.0,600.0),500/600*100)
        self.assertIsNone(sizing.premium_match_pct(0.0,0.0))

if __name__ == "__main__":
    unittest.main(verbosity=2)
