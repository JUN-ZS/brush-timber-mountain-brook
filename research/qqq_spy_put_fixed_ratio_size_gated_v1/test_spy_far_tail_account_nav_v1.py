#!/usr/bin/env python3
import unittest
from run_spy_far_tail_account_nav_v1 import allow_base, allow_tail, cagr, maxdd, pnl_tail

class Tests(unittest.TestCase):
    def test_cash_secured_short_put_gate(self):
        self.assertTrue(allow_base(110000,-1000,0,100000))
        self.assertFalse(allow_base(99000,-1000,0,100000))
        self.assertFalse(allow_base(250000,-1000,175000,80000))
    def test_hedge_cannot_consume_collateral(self):
        self.assertTrue(allow_tail(180000,1000,175000))
        self.assertFalse(allow_tail(175500,1000,175000))
    def test_tail_pnl_includes_both_sides_costs(self):
        self.assertAlmostEqual(pnl_tail(1,2,3,.05,.65),88.7,places=6)
    def test_observed_drawdown(self):
        self.assertAlmostEqual(maxdd([100,80,110,90]),20.0,places=6)
    def test_cagr(self):
        self.assertGreater(cagr(100,110,"2020-01-01","2021-01-01"),9)
        self.assertLess(cagr(100,110,"2020-01-01","2021-01-01"),11)
        self.assertIsNone(cagr(100,0,"2020-01-01","2021-01-01"))
if __name__=="__main__":unittest.main(verbosity=2)
