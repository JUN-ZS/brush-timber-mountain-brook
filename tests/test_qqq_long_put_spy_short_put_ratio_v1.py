from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))
import qqq_long_put_spy_short_put_ratio_v1 as replay


class PairedPutReplayTests(unittest.TestCase):
    def test_wilson_interval_is_bounded_and_nonzero(self):
        low, high = replay.wilson_interval(50, 100)
        self.assertGreater(low, 0.0)
        self.assertLess(high, 1.0)
        self.assertLess(low, 0.5)
        self.assertGreater(high, 0.5)

    def test_block_bootstrap_refuses_thin_sample(self):
        self.assertEqual(replay.block_bootstrap_interval([True, False] * 5), (None, None))

    def test_put_value_increases_when_spot_falls_or_iv_rises(self):
        base = replay.bs_put(100, 100, 30 / 365, 0.25)
        lower_spot = replay.bs_put(90, 100, 30 / 365, 0.25)
        higher_iv = replay.bs_put(100, 100, 30 / 365, 0.50)
        self.assertGreater(lower_spot, base)
        self.assertGreater(higher_iv, base)

    def test_expiry_put_intrinsic_uses_last_close_not_future_price(self):
        pair = {
            "qqq_expiry": date(2026, 1, 10),
            "qqq_strike": 95.0,
            "qqq_contract_id": "q1",
        }
        value, settle, method = replay.exit_value(
            "QQQ", pair, date(2026, 1, 12), {}, 
            {date(2026, 1, 9): 90.0, date(2026, 1, 12): 70.0}, True,
        )
        self.assertEqual(value, 5.0)
        self.assertEqual(settle, date(2026, 1, 9))
        self.assertEqual(method, "EXPIRY_INTRINSIC")

    def test_pair_accounting_uses_bid_ask_and_round_trip_commission(self):
        entry = date(2026, 1, 5)
        exit_date = date(2026, 1, 8)
        expiry = date(2026, 2, 6)
        pair = {
            "entry_date": entry, "match_mode": "delta", "match_score": 0.1,
            "qqq_contract_id": "q1", "qqq_expiry": expiry, "qqq_strike": 95.0,
            "qqq_bid": 1.8, "qqq_ask": 2.0, "qqq_delta": -0.25, "qqq_iv": 0.3,
            "qqq_spot": 100.0, "qqq_dte": 32, "qqq_spread_pct": 0.1,
            "spy_contract_id": "s1", "spy_expiry": expiry, "spy_strike": 100.0,
            "spy_bid": 3.0, "spy_ask": 3.2, "spy_delta": -0.25, "spy_iv": 0.2,
            "spy_spot": 105.0, "spy_dte": 32, "spy_spread_pct": 0.1,
            "market_regime": "DOWN_HIGHVOL",
        }
        quotes = {
            ("QQQ", "q1", exit_date): (4.0, 4.2),
            ("SPY", "s1", exit_date): (1.2, 1.4),
        }
        sessions = [entry, date(2026,1,6), date(2026,1,7), exit_date]
        got = replay.outcome(
            pair, "3", (4,5), sessions, {d:i for i,d in enumerate(sessions)},
            quotes, {entry:100, exit_date:90}, {entry:105, exit_date:100}, 0.65,
        )
        self.assertEqual(got["status"], "OK")
        self.assertAlmostEqual(got["pnl_qqq_long_usd"], 794.8, places=6)
        self.assertAlmostEqual(got["pnl_spy_short_usd"], 793.5, places=6)
        self.assertAlmostEqual(got["pnl_net_usd"], 1588.3, places=6)
        self.assertAlmostEqual(got["fees_usd"], 11.7, places=6)

    def test_missing_exit_quote_is_not_fabricated(self):
        pair = {
            "entry_date": date(2026,1,5), "match_mode": "delta", "match_score": 0,
            "qqq_contract_id": "q", "qqq_expiry": date(2026,2,6), "qqq_strike": 95,
            "qqq_bid": 1, "qqq_ask": 2, "qqq_delta": -.25, "qqq_iv": .3, "qqq_spot":100,
            "qqq_dte": 32, "qqq_spread_pct": .1,
            "spy_contract_id": "s", "spy_expiry": date(2026,2,6), "spy_strike":100,
            "spy_bid": 2, "spy_ask": 3, "spy_delta": -.25, "spy_iv": .2, "spy_spot":105,
            "spy_dte":32, "spy_spread_pct":.1, "market_regime":"UP_LOWVOL",
        }
        sessions=[date(2026,1,5),date(2026,1,6)]
        got=replay.outcome(pair,"1",(4,5),sessions,{d:i for i,d in enumerate(sessions)},
            {},{date(2026,1,5):100,date(2026,1,6):99},{date(2026,1,5):105,date(2026,1,6):104},.65)
        self.assertEqual(got["status"],"QQQ_MISSING_EXIT_QUOTE")
        self.assertIsNone(got["pnl_net_usd"])


if __name__ == "__main__":
    unittest.main()
