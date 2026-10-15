import importlib.util
import unittest
from datetime import date,timedelta
from pathlib import Path

MODULE=Path(__file__).with_name("qqq_put_iv_realized_vol_study_v1.py")
SPEC=importlib.util.spec_from_file_location("qqq_iv_rv_v1",MODULE)
M=importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(M)

class QQQIVRVTests(unittest.TestCase):
    def quote(self,day,days=30,delta=-.5,iv=.24,bid=2.0,ask=2.2,quote_day=None):
        expiry=(date.fromisoformat(day)+timedelta(days=days)).isoformat()
        ymd=expiry[2:4]+expiry[5:7]+expiry[8:10]
        strike=100.0
        code=f"{int(round(strike*1000)):08d}"
        return {"contract_id":f"QQQ{ymd}P{code}","symbol":"QQQ","expiration":expiry,"strike":strike,"type":"put",
                "bid":bid,"ask":ask,"bid_size":10,"ask_size":10,"open_interest":1000,"volume":20,
                "date":quote_day or day,"delta":delta,"implied_volatility":iv}

    def test_selection_requires_same_day_standard_quote_dte_and_delta(self):
        day="2024-01-03"
        a=self.quote(day,30,-.49,.24)
        b=self.quote(day,35,-.50,.28)
        selected=M.select_atm_put_iv([a,b],day,100.0)
        self.assertIsNotNone(selected)
        self.assertEqual(selected["dte"],30)
        self.assertAlmostEqual(selected["iv_pct"],24.0)
        self.assertEqual(selected["iv_source_format"],"DECIMAL")
        normalized=M.select_atm_put_iv([self.quote(day,30,-.51,24.0)],day,100.0)
        self.assertEqual(normalized["iv_pct"],24.0)
        self.assertEqual(normalized["iv_source_format"],"PERCENT_POINTS_NORMALIZED")
        self.assertIsNone(M.select_atm_put_iv([self.quote(day,30,-.5,.24,quote_day="2024-01-02")],day,100.0))
        self.assertIsNone(M.select_atm_put_iv([self.quote(day,30,-.8,.24)],day,100.0))
        self.assertIsNone(M.select_atm_put_iv([self.quote(day,30,-.5,.24,bid=3.0,ask=2.2)],day,100.0))
        self.assertIsNone(M.select_atm_put_iv([],day,100.0))
        self.assertIsNone(M.select_atm_put_iv([a],day,None))

    def test_missing_iv_is_not_filled_and_forward_horizons_are_separate(self):
        start=date(2020,1,2)
        days=[];spots={};ivs={};price=100.0
        for i in range(120):
            day=(start+timedelta(days=i)).isoformat()
            days.append(day)
            price*=1.01 if i%2 else .99
            spots[day]={"raw_close":price}
            if i%8:
                iv=18.0 if i%3 else 35.0
                ivs[day]={"date":day,"contract_id":"SYNTHETIC_FIXTURE","iv_pct":iv,"iv_decimal":iv/100,
                    "iv_source_format":"DECIMAL","expiry":(date.fromisoformat(day)+timedelta(days=30)).isoformat(),
                    "dte":30,"strike":price,"abs_delta":.5,"bid":1.0,"ask":1.1,"bid_size":10,"ask_size":10,
                    "spread_pct":9.5,"spot":price}
        report=M.build_profile(days,spots,ivs)
        self.assertEqual(report["selected_iv_sessions"],len(days)-len(days[::8]))
        self.assertNotIn(days[0],{x["date"] for x in report["daily_selected_quote_audit_rows"]})
        self.assertEqual({x["horizon_sessions"] for x in report["conditional_forward_results"]},{3,5,10,20,30})
        self.assertTrue(any(x["observations"]>0 for x in report["conditional_forward_results"]))
        self.assertIn("not option-package win probability"," ".join(report["limitations"]))

if __name__=="__main__":unittest.main(verbosity=2)
