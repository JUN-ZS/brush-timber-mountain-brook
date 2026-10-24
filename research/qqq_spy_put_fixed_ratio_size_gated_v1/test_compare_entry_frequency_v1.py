#!/usr/bin/env python3
from __future__ import annotations
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import compare_entry_frequency_v1 as comp

def row(eid,day,policy,status,pnl="",lq="1",sq="3"):
    return {"episode_id":str(eid),"signal_date":day,"policy":policy,"status":status,
            "net_pnl_usd":str(pnl),"long_qqq_qty":lq,"short_spy_qty":sq}

class FrequencyComparisonTests(unittest.TestCase):
    def test_duplicate_policy_rows_count_as_one_cohort(self):
        ds={"trades":[row(1,"2025-03-01","HOLD_5_SESSIONS","RESOLVED",100),
                      row(1,"2025-03-01","HOLD_10_SESSIONS","RESOLVED",80)],"skips":[]}
        selected,entered,skipped=comp.episode_map(ds)
        self.assertEqual((len(selected),len(entered),len(skipped)),(1,1,0))

    def test_unresolved_not_zero_filled_and_stress_visible(self):
        ds={"trades":[row(1,"2025-03-01","HOLD_20_SESSIONS","RESOLVED",100,"1","3"),
                      row(2,"2025-03-15","HOLD_20_SESSIONS","UNRESOLVED_SOURCE_END","","1","3")],"skips":[]}
        r=comp.summarize_period(ds,"1:3","none","1Y",comp.date(2024,7,23),comp.date(2025,7,23),1.0,"HOLD_20_SESSIONS")
        self.assertEqual((r["entered_cohorts"],r["resolved"],r["unresolved"]),(2,1,1))
        self.assertEqual(r["mean_net_pnl_resolved_usd"],100.0)
        self.assertEqual(r["stress_mean_net_pnl_usd"],60.0)
        self.assertEqual(r["stress_total_net_pnl_usd"],60.0)

    def test_skipped_entry_separate(self):
        ds={"trades":[row(1,"2025-03-01","HOLD_20_SESSIONS","RESOLVED",100)],
            "skips":[{"episode_id":"2","signal_date":"2025-04-01","status":"ENTRY_SKIPPED"}]}
        selected,entered,skipped=comp.episode_map(ds)
        self.assertEqual((len(selected),len(entered),len(skipped)),(2,1,1))

    def test_windows_frozen(self):
        self.assertEqual(comp.CUTOFF,comp.date(2025,7,23))
        self.assertEqual(comp.WINDOWS[0][1],comp.date(2024,7,23))

if __name__=="__main__": unittest.main(verbosity=2)
