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

    def test_insufficient_history_never_triggers(self):
        dates,qqq,spy=self.make_prices()
        passed,metrics=engine.evaluate_entry_filter(
            "spy_weekly_drop_2pct_corr60_pos",30,dates,qqq,spy)
        self.assertFalse(passed)
        self.assertEqual(metrics["filter_pass_reason"],"INSUFFICIENT_LOOKBACK")

if __name__ == "__main__":
    unittest.main(verbosity=2)
