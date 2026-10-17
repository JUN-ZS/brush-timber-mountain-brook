#!/usr/bin/env python3
import json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import validate_qqq_option_shortlist_v1 as v

class AuditTests(unittest.TestCase):
 def test_contract_count_includes_ratio_multiplicity(self):
  self.assertEqual(v.ncontracts({"contract_legs":json.dumps([{"qty":1},{"qty":5}])}),6)
 def test_cost_cases(self):
  self.assertAlmostEqual(v.pnl_cost(100,2,"ZERO_FRICTION"),122.6)
  self.assertAlmostEqual(v.pnl_cost(100,2,"BASE"),100)
  self.assertAlmostEqual(v.pnl_cost(100,2,"STRESS"),80)
 def test_entry_only_terminal_risk_adjustment(self):
  self.assertAlmostEqual(v.terminal_loss_cost(1000,2,"ZERO_FRICTION"),988.7)
  self.assertAlmostEqual(v.terminal_loss_cost(1000,2,"BASE"),1000)
  self.assertAlmostEqual(v.terminal_loss_cost(1000,2,"STRESS"),1010)
 def test_capacity_respects_risk_and_depth(self):
  self.assertEqual(v.risk_units(80000,.01,600,3),1)
  self.assertEqual(v.risk_units(80000,.01,600,0),0)
  self.assertEqual(v.risk_units(80000,.01,10000,5),0)
 def test_wilson_bounds_observed_rate(self):
  lo,hi=v.wilson(16,28);self.assertLess(lo,16/28);self.assertGreater(hi,16/28)
  lo2,hi2=v.wilson(5,9);self.assertLessEqual(lo2,lo);self.assertGreaterEqual(hi2,hi)
 def test_unresolved_not_in_win_rate(self):
  rows=[v.norm({"status":"RESOLVED","strategy_id":"X","signal_date":"2024-01-01","net_pnl_usd":"10","terminal_worst_loss_usd":"100","depth_units_at_entry":"2","mae_one_unit_usd":"-5","contract_legs":'[{"qty":1}]'}),
        v.norm({"status":"UNRESOLVED_EXIT_QUOTE","strategy_id":"X","signal_date":"2024-01-02","net_pnl_usd":"","terminal_worst_loss_usd":"100","depth_units_at_entry":"2","mae_one_unit_usd":"","contract_legs":'[{"qty":1}]'})]
  out=v.summarize(rows,"BASE");self.assertEqual(out["resolved"],1);self.assertEqual(out["wins"],1);self.assertEqual(out["unresolved"],1)
 def test_git_blob_hash(self):
  self.assertEqual(v.git_blob_sha_bytes(b"abc"),"f2ba8f84ab5c1bce84a7b441cb1959cfc7093b7f")
if __name__=="__main__":unittest.main(verbosity=2)
