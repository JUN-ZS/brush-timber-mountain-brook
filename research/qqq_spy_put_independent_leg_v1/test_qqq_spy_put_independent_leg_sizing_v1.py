#!/usr/bin/env python3
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import qqq_spy_put_independent_leg_sizing_v1 as s

def row(symbol,expiry,strike,delta,bid,ask,bid_size=5,ask_size=5):
    code=f"{int(round(strike*1000)):08d}";ymd=expiry[2:4]+expiry[5:7]+expiry[8:10]
    return {"contract_id":f"{symbol}{ymd}P{code}","symbol":symbol,"expiration":expiry,"strike":strike,"type":"put",
      "bid":bid,"ask":ask,"bid_size":bid_size,"ask_size":ask_size,"date":"2024-01-02","delta":delta,
      "volume":10,"open_interest":100,"implied_volatility":0.25}

class IndependentSideTests(unittest.TestCase):
    def test_qqq_standalone_does_not_require_spy(self):
        q=row("QQQ","2024-02-16",400,-.25,4.0,4.2,3,2)
        self.assertEqual(s.validate_entry(s.LEG_Q,q,None,2,0),(True,"OK"))
        self.assertEqual(s.validate_entry(s.LEG_Q,q,None,3,0),(False,"QQQ_LONG_ASK_SIZE_INSUFFICIENT"))
    def test_spy_standalone_does_not_require_qqq(self):
        p=row("SPY","2024-02-16",480,-.25,5.0,5.2,2,3)
        self.assertEqual(s.validate_entry(s.LEG_S,None,p,0,2),(True,"OK"))
        self.assertEqual(s.validate_entry(s.LEG_S,None,p,0,3),(False,"SPY_SHORT_BID_SIZE_INSUFFICIENT"))
    def test_each_leg_has_its_own_exit_depth(self):
        q=row("QQQ","2024-02-16",400,-.25,4.0,4.2,2,9)
        p=row("SPY","2024-02-16",480,-.25,5.0,5.2,9,1)
        self.assertEqual(s.validate_exit(s.LEG_Q,q,None,2,0),(True,"OK"))
        self.assertEqual(s.validate_exit(s.LEG_Q,q,None,3,0),(False,"QQQ_LONG_BID_SIZE_INSUFFICIENT"))
        self.assertEqual(s.validate_exit(s.LEG_S,None,p,0,1),(True,"OK"))
        self.assertEqual(s.validate_exit(s.LEG_S,None,p,0,2),(False,"SPY_SHORT_ASK_SIZE_INSUFFICIENT"))
    def test_pair_requires_both_legs(self):
        q=row("QQQ","2024-02-16",400,-.25,4.0,4.2);p=row("SPY","2024-02-16",480,-.25,5.0,5.2)
        self.assertEqual(s.validate_entry(s.PAIR,q,p,4,5),(True,"OK"))
        self.assertFalse(s.validate_entry(s.PAIR,q,None,4,5)[0])
        self.assertFalse(s.validate_exit(s.PAIR,q,None,4,5)[0])
    def test_pnl_and_cost(self):
        qg,sg,g=s.raw_pnl(2,3,4.0,5.0,5.0,6.0)
        self.assertEqual((qg,sg,g),(200.0,-300.0,-100.0))
        self.assertAlmostEqual(s.rt_cost(.05,.65),11.30)
        self.assertAlmostEqual(g-s.rt_cost(.05,.65)*5,-156.5)
    def test_cap_nine_has_36_pair_cells(self):
        cells=[(q,p) for q in range(1,10) for p in range(1,10) if q+p<=9]
        self.assertEqual(len(cells),36);self.assertIn((1,5),cells);self.assertIn((4,5),cells);self.assertNotIn((5,5),cells)
    def test_premium_match_is_cashflow_not_risk(self):
        self.assertEqual(s.match_pct(600,600),100)
        self.assertAlmostEqual(s.match_pct(500,600),83.3333333,places=5)
        self.assertIsNone(s.match_pct(0,0))

if __name__=="__main__":unittest.main(verbosity=2)
