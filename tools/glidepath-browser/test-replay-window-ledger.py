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
    def test_depletion_and_unpaid_withdrawals_are_explicit(self):
        d,p,m=flat_market(); ev={k:[("withdrawal",1000.0)] for k in range(1,121)}
        r,_=M.replay_window(d,p,m,0,"AGG",60,"linear","monthly_withdrawal_1000_usd_stress",ev)
        self.assertEqual(r["first_nav_depletion_month"],100); self.assertEqual(r["actual_withdrawals_usd"],100000.0)
        self.assertEqual(r["withdrawal_shortfall_usd"],20000.0); self.assertEqual(r["terminal_nav_usd"],0.0)
        self.assertAlmostEqual(r["requested_withdrawals_usd"],r["actual_withdrawals_usd"]+r["withdrawal_shortfall_usd"],places=8)
if __name__=="__main__": unittest.main()
