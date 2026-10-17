#!/usr/bin/env python3
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import aggregate_portfolio_scale_v1 as a

class ScaleAggregateTests(unittest.TestCase):
 def test_core_relative_deltas_preserve_sign(self):
  core={"final_nav_usd":"100000","cagr_pct":"10.0","maxdd_observed_quote_side_marks_pct":"-20.0","worst_observed_calendar_year_pct":"-15.0"}
  cand={"final_nav_usd":"101000","cagr_pct":"10.2","maxdd_observed_quote_side_marks_pct":"-19.0","worst_observed_calendar_year_pct":"-14.0"}
  got=a.compare_to_core(cand,core)
  self.assertEqual(got["delta_final_nav_usd"],1000)
  self.assertAlmostEqual(got["delta_cagr_pp"],0.2)
  self.assertEqual(got["delta_maxdd_pp"],1.0)
  self.assertEqual(got["delta_worst_year_pp"],1.0)
 def test_manifests_require_identical_pinned_sources(self):
  common={"source_window":["2018-03-01","2025-12-15"],"source_sessions":1960,"signal_count":28,"source_option_terminal_date":"2025-12-15","options_source_files":{"a":{"sha":"abc"}},"underlying_and_repo_source_integrity":{"sha":"def"},"max_abs_nav_reconciliation_error_usd":0}
  ms={nav:{**common,"initial_nav_usd":nav} for nav in a.NAVS}
  self.assertEqual(a.validate_manifests(ms)["signal_count"],28)
  ms[1000000]={**ms[1000000],"options_source_files":{"a":{"sha":"different"}}}
  with self.assertRaises(ValueError):a.validate_manifests(ms)
 def test_manifest_rejects_bad_reconciliation(self):
  common={"source_window":["2018-03-01","2025-12-15"],"source_sessions":1960,"signal_count":28,"source_option_terminal_date":"2025-12-15","options_source_files":{"a":{"sha":"abc"}},"underlying_and_repo_source_integrity":{"sha":"def"},"max_abs_nav_reconciliation_error_usd":0}
  ms={nav:{**common,"initial_nav_usd":nav} for nav in a.NAVS}
  ms[100000]={**ms[100000],"max_abs_nav_reconciliation_error_usd":0.02}
  with self.assertRaises(ValueError):a.validate_manifests(ms)
if __name__=="__main__":unittest.main(verbosity=2)
