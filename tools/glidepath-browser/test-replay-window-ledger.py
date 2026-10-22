#!/usr/bin/env python3
from __future__ import annotations
import datetime as dt, importlib.util, unittest
from pathlib import Path
import numpy as np
SCRIPT=Path(__file__).with_name("replay-window-ledger.py")
SPEC=importlib.util.spec_from_file_location("replay_window_ledger",SCRIPT)
assert SPEC and SPEC.loader
M=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(M)
def flat_market():
    dates=[(dt.date(2000,1,1)+dt.timedelta(days=15*i)).isoformat() for i in range(241)]
    return dates,np.full((241,6),100.0,dtype=np.float64),[2*i for i in range(121)]
class IndependentLedgerReplayTests(unittest.TestCase):
    def test_real_principal_counts_use_strict_less_than_and_ordered_thresholds(self):
        threshold235 = M.INITIAL * (1.0 + 0.0235) ** 10
        threshold350 = M.INITIAL * (1.0 + 0.035) ** 10
        navs = [200000.0] * 154 + [threshold235, threshold235 - 0.01, threshold350 - 0.01]
        count235, count350 = M.real_principal_breach_counts(navs, 10)
        self.assertEqual(count235, 1)
        self.assertEqual(count350, 3)
        self.assertEqual(M.real_principal_breach_counts([100000.0] * 157, 0), (0, 0))

    def test_daily_real_floor_touch_remains_visible_after_year_end_recovery(self):
        d, p, m = flat_market()
        # A one-session crash then recovery leaves every year-end NAV above the
        # first-year inflation threshold, but the daily account NAV touched below it.
        p[13, :] = 80.0
        p[14:, :] = 110.0
        r, marks = M.replay_window(d, p, m, 0, "AGG", 60, "linear", "no_withdrawals", {})
        threshold235 = M.INITIAL * (1.0 + 0.0235)
        threshold350 = M.INITIAL * (1.0 + 0.035)
        self.assertGreater(marks[1]["nav_usd"], threshold235)
        self.assertGreater(marks[1]["nav_usd"], threshold350)
        self.assertTrue(marks[1]["ever_below_real_principal_235"])
        self.assertTrue(marks[1]["ever_below_real_principal_350"])
        self.assertTrue(marks[10]["ever_below_real_principal_235"])
        self.assertTrue(marks[10]["ever_below_real_principal_350"])
        self.assertEqual(M.real_principal_breach_counts([marks[1]["nav_usd"]] * 157, 1), (0, 0))
        self.assertEqual(r["terminal_nav_usd"], 110000.0)

    def test_flat_unfunded_real_floor_tracks_inflation_touch_even_without_price_loss(self):
        d, p, m = flat_market()
        _, marks = M.replay_window(d, p, m, 0, "AGG", 60, "linear", "no_withdrawals", {})
        self.assertFalse(marks[0]["ever_below_real_principal_235"])
        self.assertFalse(marks[0]["ever_below_real_principal_350"])
        self.assertTrue(marks[1]["ever_below_real_principal_235"])
        self.assertTrue(marks[1]["ever_below_real_principal_350"])
        self.assertTrue(all(mark["ever_below_real_principal_235"] for mark in marks[1:]))
        self.assertTrue(all(mark["ever_below_real_principal_350"] for mark in marks[1:]))

    def test_real_principal_count_rejects_incomplete_or_invalid_nav_samples(self):
        with self.assertRaisesRegex(ValueError, "157 window NAVs"):
            M.real_principal_breach_counts([100000.0] * 156, 10)
        with self.assertRaisesRegex(ValueError, "finite non-negative"):
            M.real_principal_breach_counts([100000.0] * 156 + [float("nan")], 10)

    def test_flat_market_no_flow_conserves_nav_and_zero_return(self):
        d,p,m=flat_market(); r,marks=M.replay_window(d,p,m,0,"AGG",60,"linear","no_withdrawals",{})
        self.assertEqual(r["terminal_nav_usd"],100000.0); self.assertEqual(r["additional_deposits_usd"],0.0)
        self.assertEqual(r["actual_withdrawals_usd"],0.0); self.assertEqual(r["withdrawal_shortfall_usd"],0.0)
        self.assertAlmostEqual(r["time_weighted_cagr"],0.0,places=12); self.assertAlmostEqual(r["daily_max_drawdown"],0.0,places=12)
        self.assertEqual(len(marks),11); self.assertEqual(marks[-1]["target_bond_weight"],.60)
    def test_deposit_and_withdrawal_preserve_time_weighted_return(self):
        d,p,m=flat_market(); ev={1:[("withdrawal",1000.0)],2:[("deposit",500.0)]}
        r,_=M.replay_window(d,p,m,0,"AGG",60,"linear","delayed_stepup_example",ev)
        self.assertEqual(r["requested_withdrawals_usd"],1000.0); self.assertEqual(r["actual_withdrawals_usd"],1000.0)
        self.assertEqual(r["withdrawal_shortfall_usd"],0.0); self.assertEqual(r["additional_deposits_usd"],500.0)
        self.assertEqual(r["terminal_nav_usd"],99500.0); self.assertAlmostEqual(r["time_weighted_cagr"],0.0,places=12)
    def test_comparison_counter_increments_once_per_field(self):
        stats={"fields_compared":0,"max_abs_error":{}}
        M.close_value(100.0,"100","test_numeric",stats,"counter")
        self.assertEqual(stats["fields_compared"],1)
        M.close_value("linear","linear","timing_rule",stats,"counter")
        self.assertEqual(stats["fields_compared"],2)
    def test_depletion_and_unpaid_withdrawals_are_explicit(self):
        d,p,m=flat_market(); ev={k:[("withdrawal",1000.0)] for k in range(1,121)}
        r,_=M.replay_window(d,p,m,0,"AGG",60,"linear","monthly_withdrawal_1000_usd_stress",ev)
        self.assertEqual(r["first_nav_depletion_month"],100); self.assertEqual(r["actual_withdrawals_usd"],100000.0)
        self.assertEqual(r["withdrawal_shortfall_usd"],20000.0); self.assertEqual(r["terminal_nav_usd"],0.0)
        self.assertAlmostEqual(r["requested_withdrawals_usd"],r["actual_withdrawals_usd"]+r["withdrawal_shortfall_usd"],places=8)
if __name__=="__main__": unittest.main()
