#!/usr/bin/env python3
import unittest
from run_dte14_ratio_spreads_nav_v1 import spread_collateral

class Tests(unittest.TestCase):
    def test_full_coverage_reserves_vertical_width_not_short_notional(self):
        self.assertEqual(spread_collateral(500,450,3,3),15000)
        self.assertLess(spread_collateral(500,450,3,3),500*100*3)

    def test_half_coverage_keeps_uncovered_short_notional(self):
        self.assertEqual(spread_collateral(500,450,6,3),165000)
        self.assertEqual(spread_collateral(500,450,6,6),30000)

    def test_no_tail_is_fully_cash_secured(self):
        self.assertEqual(spread_collateral(500,None,3,0),150000)
        self.assertEqual(spread_collateral(500,None,6,0),300000)

    def test_tail_must_be_lower_strike(self):
        with self.assertRaises(ValueError):
            spread_collateral(500,500,3,3)
        with self.assertRaises(ValueError):
            spread_collateral(500,510,3,3)

    def test_tail_cannot_cover_more_than_short_quantity(self):
        with self.assertRaises(ValueError):
            spread_collateral(500,450,3,6)

if __name__=="__main__": unittest.main(verbosity=2)
