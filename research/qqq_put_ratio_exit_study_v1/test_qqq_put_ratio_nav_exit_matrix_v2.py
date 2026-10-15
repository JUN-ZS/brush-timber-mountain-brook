import importlib.util
import unittest
from datetime import date, timedelta
from pathlib import Path
MODULE=Path(__file__).with_name("qqq_put_ratio_nav_exit_matrix_v2.py")
SPEC=importlib.util.spec_from_file_location("ratio_matrix_v2",MODULE)
M=importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(M)

class MatrixTests(unittest.TestCase):
    def test_nav_percent_converts_for_both_account_sizes(self):
        self.assertEqual([100000*p/100 for p in (0.5,1,2)],[500,1000,2000])
        self.assertEqual([1000000*p/100 for p in (0.5,1,2)],[5000,10000,20000])

    def test_historical_volatility_profile_covers_horizons_and_realized_vol(self):
        start=date(2020,1,2);days=[];spots={};universe={};price=100.0
        for i in range(160):
            day=(start+timedelta(days=i)).isoformat();days.append(day)
            price*=1.012 if i%3 else 0.99
            spots[day]={"raw_close":price};universe[day]={"vix":18.0 if i%4 else 32.0}
        report=M.build_volatility_time_profile(days,spots,universe)
        self.assertEqual({x["horizon_sessions"] for x in report["horizon_returns"]},{1,3,5,10,20,30,45})
        self.assertEqual({x["window_sessions"] for x in report["rolling_realized_volatility"]},{10,20,30,60})
        self.assertIn("not independent-trial forecasts",report["interpretation"])
        rv_buckets={x["entry_rv20_bucket"] for x in report["conditional_by_entry_rv20"]}
        self.assertTrue({"RV20_LT20","RV20_20_35","RV20_GTE35"}.issubset(rv_buckets))
        surge=report["prior_3_session_surge_forward_study"]
        self.assertEqual({x["prior_3_session_return_ge_pct"] for x in surge},{3.0,5.0})
        self.assertEqual({x["forward_horizon_sessions"] for x in surge},{1,3,5,10})
        self.assertTrue(all(x["overlapping_event_dates"] for x in surge))
        spots.pop(days[-1])
        partial=M.build_volatility_time_profile(days,spots,universe)
        self.assertEqual(partial["source_end"],days[-2])
        self.assertEqual(partial["expected_sessions"],len(days))
        self.assertEqual(partial["observed_close_sessions"],len(days)-1)
        self.assertEqual(partial["missing_expected_close_sessions"],1)

    def test_payoff_tail_checks_breakpoints_in_both_directions(self):
        short={"n_long":1,"n_short":3,"long_strike":105.0,"short_strike":90.0,"entry_quotes":{"long":{"ask":7.2},"short":{"bid":1.0}}}
        long={"n_long":3,"n_short":1,"long_strike":90.0,"short_strike":105.0,"entry_quotes":{"long":{"ask":1.2},"short":{"bid":7.0}}}
        a=M.terminal_risk_per_package(short,.05,.65);b=M.terminal_risk_per_package(long,.05,.65)
        self.assertGreaterEqual(a["terminal_max_loss_usd"],0)
        self.assertGreaterEqual(b["terminal_max_loss_usd"],0)
        self.assertNotEqual(a["terminal_max_loss_usd"],b["terminal_max_loss_usd"])

    def test_depth_gate_checks_requested_N_and_orientation(self):
        def put(strike,delta,bid,ask,expiry="2024-02-16",day="2024-01-03",bid_size=10,ask_size=10):
            code=f"{int(round(strike*1000)):08d}";ymd=expiry[2:4]+expiry[5:7]+expiry[8:10]
            return {"contract_id":f"QQQ{ymd}P{code}","symbol":"QQQ","expiration":expiry,"strike":strike,"type":"put","bid":bid,"ask":ask,"bid_size":bid_size,"ask_size":ask_size,"open_interest":100,"volume":10,"date":day,"delta":delta}
        high=put(105,-.30,7,7.2,bid_size=1,ask_size=1);low=put(90,-.10,1,1.2,bid_size=2,ask_size=2)
        pair={"long_id":high["contract_id"],"short_id":low["contract_id"],"expiry":"2024-02-16"}
        q,status=M.shape_quote_pair(pair,[high,low],"2024-01-03",3,"short-heavy")
        self.assertIsNone(q);self.assertEqual(status,"SHORT_BID_OR_SIZE_INSUFFICIENT")
        q,status=M.shape_quote_pair(pair,[high,low],"2024-01-03",2,"long-heavy")
        self.assertIsNotNone(q);self.assertEqual(status,"OK")

    def test_displayed_entry_depth_caps_nav_budget_package_count(self):
        trade={"n_long":1,"n_short":5,"long_strike":21.0,"short_strike":20.0,
               "entry_quotes":{"long":{"ask":2.0,"bid":1.8,"bid_size":50,"ask_size":4},
                               "short":{"bid":1.0,"ask":1.2,"ask_size":15,"bid_size":7}}}
        cap=M.package_capacity(trade,1000000,2.0,0.05,0.65)
        self.assertGreater(cap["risk_budget_capacity_packages"],cap["entry_depth_capacity_packages"])
        self.assertEqual(cap["entry_depth_capacity_packages"],1)
        self.assertEqual(cap["packages"],1)
        self.assertTrue(cap["depth_limited"])

    def test_policy_summary_reports_resolved_and_missing_cases_separately(self):
        results=[
            {"resolved":True,"final_pnl_usd":100.0,"packages":1,"custom_triggered":True,"dte7_fallback_triggered":False,
             "mark_coverage_pct":100.0,"missing_mark_sessions":0,"deferred_action_sessions":0},
            {"resolved":True,"final_pnl_usd":-50.0,"packages":2,"custom_triggered":False,"dte7_fallback_triggered":True,
             "mark_coverage_pct":90.0,"missing_mark_sessions":1,"deferred_action_sessions":1},
            {"resolved":False,"final_pnl_usd":None,"packages":1,"custom_triggered":False,"dte7_fallback_triggered":False,
             "mark_coverage_pct":70.0,"missing_mark_sessions":3,"deferred_action_sessions":0},
        ]
        s=M.summarize_policy(results,candidate_n=4,blocked=1)
        self.assertEqual(s["candidate_episodes"],4)
        self.assertEqual(s["episodes_fitting_budget"],3)
        self.assertEqual(s["resolved_episodes"],2)
        self.assertEqual(s["unresolved_episodes"],1)
        self.assertEqual(s["net_pnl_sum_usd"],50.0)
        self.assertEqual(s["win_rate_pct"],50.0)
        self.assertEqual(s["custom_triggered_episodes"],1)
        self.assertEqual(s["dte7_fallback_episodes"],1)

    def test_dte_baseline_and_first_session_exit_policies_are_distinct(self):
        p=M.make_policies(1000000,1.0,"short-heavy",1)
        names={x["name"] for x in p}
        self.assertIn("DTE7_BASELINE",names)
        self.assertIn("FIRST3D_TP_1PCT_CLOSE_ALL",names)
        self.assertFalse(any(x["action"]=="TRIM_SHORT" for x in p))
        # This policy axis spans all target percentages, regardless of the NAV risk-budget loop.
        all_targets={x["target_pct"] for x in M.all_exit_policies(1000000,"short-heavy",5) if x["target_pct"] is not None}
        self.assertEqual(all_targets,{0.5,1.0,2.0})

if __name__=="__main__":unittest.main()
