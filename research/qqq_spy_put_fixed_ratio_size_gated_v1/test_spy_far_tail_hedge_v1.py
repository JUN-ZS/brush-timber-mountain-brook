#!/usr/bin/env python3
import unittest
import qqq_spy_put_fixed_phase_v1 as engine
import spy_far_tail_hedge_v1 as hedge


def option(contract_id, strike, delta, bid=0.12, ask=0.18, bid_size=2, ask_size=3,
           expiry="2024-06-21", day="2024-06-03", oi=1000):
    return {"contract_id": contract_id, "symbol": "SPY", "expiration": expiry, "strike": strike,
        "type": "put", "bid": bid, "ask": ask, "bid_size": bid_size, "ask_size": ask_size,
        "volume": 10, "open_interest": oi, "date": day, "implied_volatility": 0.45, "delta": delta}


class FarTailSelectionTests(unittest.TestCase):
    def test_picks_nearest_delta_same_expiry_strictly_otm(self):
        candidates = [
            option("SPY240621P00380000", 380, -0.052),
            option("SPY240621P00390000", 390, -0.071, oi=9000),
            option("SPY240621P00410000", 410, -0.045),  # ITM must be excluded
            option("SPY240628P00380000", 380, -0.050, expiry="2024-06-28"),
            option("SPY240621P00370000", 370, -0.110),
            option("SPY240621P00360000", 360, -0.040, bid=0),
        ]
        chosen = hedge.select_far_tail(candidates, "2024-06-03", "2024-06-21", 400, 0.05, 0.01, 0.08)
        self.assertIsNotNone(chosen)
        self.assertEqual(chosen["contract_id"], "SPY240621P00380000")
        self.assertAlmostEqual(chosen["abs_delta"], 0.052)
        self.assertGreater(chosen["otm_pct_entry"], 0)

    def test_no_eligible_contract_returns_none(self):
        rows = [option("SPY240621P00410000", 410, -0.05)]
        self.assertIsNone(hedge.select_far_tail(rows, "2024-06-03", "2024-06-21", 400, 0.05, 0.01, 0.08))

    def test_same_contract_quantity_dependent_entry_gate(self):
        pick = {"ask_size": 2}
        self.assertTrue(hedge.entry_size_ok(pick, 1))
        self.assertFalse(hedge.entry_size_ok(pick, 3))
        self.assertFalse(hedge.entry_size_ok(None, 1))

    def test_exit_quote_requires_displayed_bid_size(self):
        row = option("SPY240621P00380000", 380, -0.05, bid_size=2, ask_size=10)
        self.assertTrue(hedge.exit_size_ok(row, 1))
        self.assertFalse(hedge.exit_size_ok(row, 3))
        row["bid"] = None
        self.assertFalse(hedge.exit_size_ok(row, 1))


class AccountingTests(unittest.TestCase):
    def test_tail_round_trip_charges_both_sides(self):
        self.assertAlmostEqual(hedge.tail_net_pnl(0.20, 0.50, 1, 0.05, 0.65), 18.70, places=6)

    def test_deep_shock_tail_improves_short_spy_sleeve(self):
        out = hedge.expiry_spy_sleeve_pnl(400, 380, 3, 2.0, 340, 3, 0.20, -0.50)
        self.assertEqual(out["stressed_spy_spot"], 200)
        self.assertLess(out["short_put_sleeve_net_usd"], 0)
        self.assertGreater(out["tail_put_net_usd"], 0)
        self.assertGreater(out["hedged_spy_sleeve_net_usd"], out["short_put_sleeve_net_usd"])

    def test_three_tail_contracts_offset_more_at_deep_shock_than_one(self):
        one = hedge.expiry_spy_sleeve_pnl(400, 380, 3, 2.0, 340, 1, 0.20, -0.50)
        three = hedge.expiry_spy_sleeve_pnl(400, 380, 3, 2.0, 340, 3, 0.20, -0.50)
        self.assertGreater(three["hedged_spy_sleeve_net_usd"], one["hedged_spy_sleeve_net_usd"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
