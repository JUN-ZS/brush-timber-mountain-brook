#!/usr/bin/env python3
"""Offline contract tests for independent fixed-N leg attribution."""
import unittest
from independent_leg_n_sweep_v1 import (
    COSTS, round_trip_cost, gross_scaled, leg_net, pair_net, stats, valid_pairs,
)

class IndependentLegSweepTests(unittest.TestCase):
    def setUp(self):
        self.row = {
            "status": "RESOLVED",
            "long_qqq_qty": "3", "short_spy_qty": "2",
            "qqq_long_gross_pnl_usd": "-12.0", "spy_short_gross_pnl_usd": "6.0",
            "base_slippage_per_share": "0.05",
            "base_commission_per_contract_per_side": "0.65",
        }

    def test_round_trip_cost_is_open_plus_close(self):
        self.assertAlmostEqual(round_trip_cost(1, 0.05, 0.65), 11.30, places=8)
        self.assertAlmostEqual(round_trip_cost(2, 0.05, 0.65), 22.60, places=8)

    def test_each_leg_scales_from_its_own_parent_quantity(self):
        self.assertAlmostEqual(gross_scaled(self.row, "QQQ_LONG_PUT", 2), -8.0)
        self.assertAlmostEqual(gross_scaled(self.row, "SPY_SHORT_PUT", 3), 9.0)

    def test_standalone_net_recalculates_costs_for_hypothetical_n(self):
        self.assertAlmostEqual(leg_net(self.row, "QQQ_LONG_PUT", 2, COSTS[1]), -30.60)
        self.assertAlmostEqual(leg_net(self.row, "SPY_SHORT_PUT", 3, COSTS[1]), -24.90)
        self.assertAlmostEqual(leg_net(self.row, "QQQ_LONG_PUT", 2, COSTS[0]), -8.0)

    def test_pair_charges_both_legs(self):
        self.assertAlmostEqual(pair_net(self.row, 1, 1, COSTS[1]), -23.60)

    def test_unresolved_episode_is_not_imputed_as_zero(self):
        unresolved = dict(self.row, status="UNRESOLVED_SOURCE_END")
        self.assertIsNone(gross_scaled(unresolved, "QQQ_LONG_PUT", 1))
        result = stats([3.0, -1.0, None])
        self.assertEqual(result["opened_n"], 3)
        self.assertEqual(result["resolved_n"], 2)
        self.assertEqual(result["unresolved_n"], 1)
        self.assertEqual(result["wins"], 1)
        self.assertEqual(result["losses"], 1)
        self.assertEqual(result["win_rate_pct"], 50.0)

    def test_pair_grid_obeys_cap(self):
        pairs = valid_pairs(9)
        self.assertEqual(len(pairs), 30)
        self.assertTrue(all(q + s <= 9 for q, s in pairs))
        self.assertNotIn((4, 6), pairs)
        self.assertIn((4, 5), pairs)

    def test_nonpositive_fixed_n_is_rejected(self):
        with self.assertRaises(ValueError):
            gross_scaled(self.row, "QQQ_LONG_PUT", 0)

if __name__ == "__main__":
    unittest.main(verbosity=2)
