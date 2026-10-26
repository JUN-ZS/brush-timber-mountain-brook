#!/usr/bin/env python3
from __future__ import annotations
import unittest

import qqq_spy_call_premium_matched_phase_v1 as engine


class CallRatioEngineTests(unittest.TestCase):
    def test_standard_call_identity_and_put_rejection(self):
        call = {
            "contract_id": "QQQ260115C00500000", "symbol": "QQQ", "type": "call",
            "expiration": "2026-01-15", "strike": 500.0,
        }
        self.assertTrue(engine.standard_call_identity(call, "QQQ"))
        put = dict(call, contract_id="QQQ260115P00500000", type="put")
        self.assertFalse(engine.standard_call_identity(put, "QQQ"))

    def test_call_moneyness_direction(self):
        self.assertEqual(engine.call_moneyness(100, 110)["status"], "OTM")
        self.assertEqual(engine.call_moneyness(110, 100)["status"], "ITM")
        self.assertAlmostEqual(engine.call_moneyness(100, 110)["otm_pct"], 10.0)

    def test_delta_020_prefers_nearest_call(self):
        base = {
            "symbol": "QQQ", "type": "call", "expiration": "2026-01-15",
            "date": "2025-12-30", "bid": 1.0, "ask": 1.1,
            "bid_size": 5, "ask_size": 5, "open_interest": 100,
        }
        rows = [
            dict(base, contract_id="QQQ260115C00510000", strike=510, delta=0.24),
            dict(base, contract_id="QQQ260115C00500000", strike=500, delta=0.205),
            dict(base, contract_id="QQQ260115C00490000", strike=490, delta=0.31),
        ]
        selected = engine.choose_leg(rows, "QQQ", "2025-12-30", "2026-01-15", 0.20)
        self.assertIsNotNone(selected)
        self.assertEqual(selected["id"], "QQQ260115C00500000")
        self.assertAlmostEqual(selected["abs_delta"], 0.205)

    def test_1_to_6_call_leg_pnl_signs(self):
        episode = {
            "long_qqq_qty": 1, "short_spy_qty": 6,
            "qqq_entry_ask": 2.0, "spy_entry_bid": 1.0,
        }
        result = engine.episode_pnl(episode, qqq_exit_bid=3.0, spy_exit_ask=2.0,
                                    slippage_per_share=0.0, commission_per_contract_side=0.0)
        self.assertAlmostEqual(result["qqq_long_gross_pnl_usd"], 100.0)
        self.assertAlmostEqual(result["spy_short_gross_pnl_usd"], -600.0)
        self.assertAlmostEqual(result["net_pnl_usd"], -500.0)

    def test_fixed_schedule_anchor(self):
        self.assertEqual(list(engine.fixed_schedule_indices(26, 0, 10)), [0, 10, 20])
        self.assertEqual(list(engine.fixed_schedule_indices(26, 2, 10)), [2, 12, 22])


if __name__ == "__main__":
    unittest.main(verbosity=2)
