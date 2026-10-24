#!/usr/bin/env python3
import sys, unittest
from pathlib import Path
from datetime import date

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import audit_fixed_phase_capacity_v1 as audit

def row(eid, entry, exit_day, obligation, pnl=10, status="RESOLVED", last=""):
    return {"episode_id":str(eid),"policy":"HOLD_20_SESSIONS","entry_date":entry,
      "exit_date":exit_day,"last_observed_date":last,"spy_put_strike_assignment_obligation_usd":str(obligation),
      "net_pnl_usd":str(pnl),"status":status}

class CapacitySweepTests(unittest.TestCase):
    def test_overlapping_assignment_obligations_are_summed_by_day(self):
        rows=[row(1,"2025-01-01","2025-01-03",50000),
              row(2,"2025-01-02","2025-01-04",75000)]
        s=audit.sweep(rows)
        self.assertEqual(s["peak_n"],2)
        self.assertEqual(s["peak"],125000)
        # Obligation exceeds $100k from Jan 2 through Jan 3 inclusive.
        over=sum(length for a,b,length,n,value in s["periods"] if value>100000)
        self.assertEqual(over,2)

    def test_unresolved_position_is_counted_to_last_observed_date(self):
        rows=[row(1,"2025-01-01","",60000,status="UNRESOLVED_SOURCE_END",last="2025-01-04")]
        s=audit.sweep(rows)
        self.assertEqual(s["peak"],60000)
        self.assertEqual(s["span"],("2025-01-01","2025-01-04"))
        self.assertEqual(s["observed_calendar_days"] if "observed_calendar_days" in s else sum(p[2] for p in s["periods"]),4)

    def test_empty_rows_have_zero_exposure(self):
        s=audit.sweep([])
        self.assertEqual((s["positions"],s["peak_n"],s["peak"]),(0,0,0.0))

if __name__=="__main__":
    unittest.main(verbosity=2)
