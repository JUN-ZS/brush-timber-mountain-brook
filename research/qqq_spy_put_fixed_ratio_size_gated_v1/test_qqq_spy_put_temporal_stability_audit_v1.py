#!/usr/bin/env python3
from __future__ import annotations
import csv, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import qqq_spy_put_temporal_stability_audit_v1 as audit

def row(eid,day,policy,status,pnl="",qqq="",spy="",adverse=""):
    return {"episode_id":str(eid),"signal_date":day,"policy":policy,"status":status,
      "net_pnl_usd":str(pnl),"qqq_long_gross_pnl_usd":str(qqq),
      "spy_short_gross_pnl_usd":str(spy),"max_adverse_mark_pnl_usd":str(adverse)}

class TemporalAuditTests(unittest.TestCase):
    def test_unresolved_counted_but_never_zero_filled(self):
        rows=[row(1,"2022-01-10","HOLD_10_SESSIONS","RESOLVED",100,-20,130,-25),
          row(2,"2022-06-10","HOLD_10_SESSIONS","UNRESOLVED_SOURCE_END","",5,70,-80)]
        r=audit.summarize(rows,"1:3","era","2022-2023","HOLD_10_SESSIONS")
        self.assertEqual((r["opened"],r["resolved"],r["unresolved"]),(2,1,1))
        self.assertEqual(r["mean_net_pnl_usd"],100.0)
        self.assertEqual(r["total_resolved_net_pnl_usd"],100.0)
        self.assertEqual(r["worst_adverse_mark_usd"],-80.0)

    def test_win_loss_flat_and_profit_factor(self):
        rows=[row(1,"2020-02-01","HOLD_5_SESSIONS","RESOLVED",100),
          row(2,"2020-03-01","HOLD_5_SESSIONS","RESOLVED",-25),
          row(3,"2020-04-01","HOLD_5_SESSIONS","RESOLVED",0)]
        r=audit.summarize(rows,"2:4","year","2020","HOLD_5_SESSIONS")
        self.assertEqual((r["wins"],r["losses"],r["flat"]),(1,1,1))
        self.assertEqual(r["profit_factor"],4.0)
        self.assertEqual(r["mean_net_pnl_usd"],25.0)

    def test_inconsistent_episode_dates_rejected(self):
        rows=[row(1,"2018-01-01","HOLD_5_SESSIONS","RESOLVED",10),
          row(1,"2018-01-02","HOLD_10_SESSIONS","RESOLVED",20)]
        with self.assertRaises(ValueError): audit.signature(rows)

    def test_wilson_interval(self):
        lo,hi=audit.wilson95(8,10)
        self.assertLess(lo,80); self.assertGreater(hi,80)
        self.assertEqual(audit.wilson95(0,0),(None,None))

    def test_all_ratios_must_share_same_cohort(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            fields=["episode_id","signal_date","policy","status","net_pnl_usd",
              "qqq_long_gross_pnl_usd","spy_short_gross_pnl_usd","max_adverse_mark_pnl_usd"]
            for folder in audit.RATIO_DIRS.values():
                path=root/folder/"trade_episodes.csv"; path.parent.mkdir(parents=True)
                with path.open("w",newline="",encoding="utf-8") as f:
                    w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
                    for policy in audit.POLICIES: w.writerow(row(1,"2018-03-01",policy,"RESOLVED",5,2,4,-1))
            audit.build_records(root)
            path=root/audit.RATIO_DIRS["1:3"]/"trade_episodes.csv"
            with path.open("w",newline="",encoding="utf-8") as f:
                w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
                for policy in audit.POLICIES: w.writerow(row(2,"2018-04-01",policy,"RESOLVED",5,2,4,-1))
            with self.assertRaises(ValueError): audit.build_records(root)

if __name__=="__main__": unittest.main(verbosity=2)
