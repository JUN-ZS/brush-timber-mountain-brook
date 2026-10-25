#!/usr/bin/env python3
import datetime
import unittest

import qqq_spy_put_premium_matched_phase_v1 as engine

class WeeklyDropFilterTests(unittest.TestCase):
    def make_prices(self):
        dates=[]
        qqq={}
        spy={}
        q=s=100.0
        returns=(-0.001,0.0015,0.002,-0.0007,0.0003,-0.0012,0.001)
        for i in range(67):
            dates.append((datetime.date(2026,1,1)+datetime.timedelta(days=i)).isoformat())
            if i > 0 and i <= 59:
                r=returns[(i-1)%len(returns)]
                q *= 1+r
                s *= 1+r
            # Hold both underlying closes steady from index 59 to 64.
            if i == 65:
                s *= 0.97
            qqq[dates[-1]]=q
            spy[dates[-1]]=s
        return dates,qqq,spy

    def test_only_first_crossing_of_weekly_minus_two_percent_triggers(self):
        dates,qqq,spy=self.make_prices()
        passed,metrics=engine.evaluate_entry_filter(
            "spy_weekly_drop_2pct_corr60_pos",65,dates,qqq,spy)
        self.assertTrue(passed,metrics)
        self.assertLessEqual(metrics["spy_trailing_return_pct"],-2.0)
        self.assertGreater(metrics["spy_previous_trailing_return_pct"],-2.0)
        self.assertGreater(metrics["qqq_spy_corr_60d"],0)

        # Next session remains below the rolling threshold, but no new crossing.
        passed_next,metrics_next=engine.evaluate_entry_filter(
            "spy_weekly_drop_2pct_corr60_pos",66,dates,qqq,spy)
        self.assertFalse(passed_next)
        self.assertEqual(metrics_next["filter_pass_reason"],"NO_NEW_SPY_5D_MINUS_2PCT_CROSSING")

    def test_weekly_minus_one_percent_crossing_triggers_without_correlation_gate(self):
        dates,qqq,spy=self.make_prices()
        passed,metrics=engine.evaluate_entry_filter("spy_weekly_drop_1pct",65,dates,qqq,spy)
        self.assertTrue(passed,metrics)
        self.assertLessEqual(metrics["spy_trailing_return_pct"],-1.0)
        self.assertGreater(metrics["spy_previous_trailing_return_pct"],-1.0)
        self.assertIsNone(metrics["qqq_spy_corr_60d"])
        self.assertEqual(metrics["filter_pass_reason"],"SPY_5D_DROPPED_THROUGH_MINUS_1PCT")

        # The rolling return remains below threshold, so it does not repeat every day.
        passed_next,metrics_next=engine.evaluate_entry_filter("spy_weekly_drop_1pct",66,dates,qqq,spy)
        self.assertFalse(passed_next)
        self.assertEqual(metrics_next["filter_pass_reason"],"NO_NEW_SPY_5D_MINUS_1PCT_CROSSING")

    def test_weekly_minus_one_percent_needs_only_six_common_sessions(self):
        dates,qqq,spy=self.make_prices()
        passed,metrics=engine.evaluate_entry_filter("spy_weekly_drop_1pct",5,dates,qqq,spy)
        self.assertFalse(passed)
        self.assertEqual(metrics["filter_pass_reason"],"INSUFFICIENT_LOOKBACK")

    def test_insufficient_history_never_triggers(self):
        dates,qqq,spy=self.make_prices()
        passed,metrics=engine.evaluate_entry_filter(
            "spy_weekly_drop_2pct_corr60_pos",30,dates,qqq,spy)
        self.assertFalse(passed)
        self.assertEqual(metrics["filter_pass_reason"],"INSUFFICIENT_LOOKBACK")

class HalfPremiumQQQSelectionTests(unittest.TestCase):
    @staticmethod
    def option(symbol, strike, delta, bid, ask, size, expiry="2026-01-16"):
        day = "2026-01-02"
        expiry_code = datetime.datetime.strptime(expiry, "%Y-%m-%d").strftime("%y%m%d")
        cid = f"{symbol}{expiry_code}P{int(strike * 1000):08d}"
        return {
            "contract_id": cid, "symbol": symbol, "expiration": expiry,
            "strike": strike, "type": "put", "bid": bid, "ask": ask,
            "bid_size": size, "ask_size": size, "volume": 100,
            "open_interest": 1000, "date": day,
            "implied_volatility": 0.3, "delta": delta,
        }

    def test_two_lower_premium_puts_target_half_reference_ask_and_require_size_two(self):
        day = "2026-01-02"
        qqq = [
            self.option("QQQ", 500, -0.65, 19.0, 20.0, 10),
            self.option("QQQ", 490, -0.61, 16.5, 17.0, 10),
            # This is exactly at the half-price target but cannot support two contracts.
            self.option("QQQ", 470, -0.25, 8.3, 8.5, 1),
            self.option("QQQ", 465, -0.20, 8.4, 8.75, 3),
        ]
        spy = [self.option("SPY", 590, -0.25, 3.0, 3.2, 10)]
        pair = engine.choose_pair_by_premium(
            qqq, spy, day, 500.0, 600.0,
            target_delta=0.25, dte_min=7, dte_max=21, dte_target=14,
            premium_match_short_qty=6, qqq_target_abs_delta=0.65,
            qqq_delta_tolerance=0.05, qqq_reference_premium_fraction=0.5,
            qqq_required_size=2,
        )
        self.assertIsNotNone(pair)
        self.assertEqual(pair["qqq_premium_reference_contract_id"], "QQQ260116P00490000")
        self.assertAlmostEqual(pair["qqq_premium_reference_ask_signal"], 17.0)
        self.assertAlmostEqual(pair["qqq_target_ask_signal"], 8.5)
        self.assertEqual(pair["qqq_contract_id"], "QQQ260116P00465000")
        self.assertAlmostEqual(pair["qqq_signal_ask"], 8.75)
        self.assertAlmostEqual(pair["qqq_abs_delta"], 0.20)
        self.assertAlmostEqual(pair["qqq_reference_premium_fraction"], 0.5)
        self.assertEqual(pair["spy_contract_id"], "SPY260116P00590000")

    def test_half_premium_selector_locks_baseline_expiry_and_spy_contract(self):
        day = "2026-01-02"
        expiry_near = "2026-01-14"  # 12 DTE
        expiry_far = "2026-01-18"   # 16 DTE; equally far from target DTE14

        qqq = [
            # Reference candidates: baseline uses 6x SPY Bid = $18 target.
            self.option("QQQ", 500, -0.65, 16.0, 17.0, 10, expiry_near),
            self.option("QQQ", 510, -0.65, 19.0, 20.0, 10, expiry_far),
            # Half-premium alternatives. The farther expiry has an exact half-ask match,
            # but must not pull the baseline SPY leg/expiry away from expiry_near.
            self.option("QQQ", 470, -0.25, 8.3, 8.5, 3, expiry_near),
            self.option("QQQ", 465, -0.20, 9.8, 10.0, 3, expiry_far),
            # A cheaper near-expiry contract with an ideal half price, but no size for 2.
            self.option("QQQ", 460, -0.15, 8.3, 8.5, 1, expiry_near),
        ]
        spy = [
            self.option("SPY", 590, -0.25, 3.0, 3.2, 10, expiry_near),
            self.option("SPY", 585, -0.25, 3.0, 3.2, 10, expiry_far),
        ]

        baseline = engine.choose_pair_by_premium(
            qqq, spy, day, 500.0, 600.0,
            target_delta=0.25, dte_min=7, dte_max=21, dte_target=14,
            premium_match_short_qty=6, qqq_target_abs_delta=0.65,
            qqq_delta_tolerance=0.05,
        )
        half = engine.choose_pair_by_premium(
            qqq, spy, day, 500.0, 600.0,
            target_delta=0.25, dte_min=7, dte_max=21, dte_target=14,
            premium_match_short_qty=6, qqq_target_abs_delta=0.65,
            qqq_delta_tolerance=0.05, qqq_reference_premium_fraction=0.5,
            qqq_required_size=2,
        )
        self.assertIsNotNone(baseline)
        self.assertIsNotNone(half)
        self.assertEqual(baseline["expiry"], expiry_near)
        self.assertEqual(half["expiry"], baseline["expiry"])
        self.assertEqual(half["spy_contract_id"], baseline["spy_contract_id"])
        self.assertEqual(half["qqq_premium_reference_contract_id"], baseline["qqq_contract_id"])
        self.assertEqual(half["qqq_contract_id"], "QQQ260114P00470000")
        self.assertAlmostEqual(half["qqq_target_ask_signal"], 8.5)
        self.assertAlmostEqual(half["qqq_signal_ask"], 8.5)
        self.assertEqual(half["qqq_abs_delta"], 0.25)
        self.assertTrue(half["qqq_reference_expiry_locked_to_reference"])

if __name__ == "__main__":
    unittest.main(verbosity=2)
