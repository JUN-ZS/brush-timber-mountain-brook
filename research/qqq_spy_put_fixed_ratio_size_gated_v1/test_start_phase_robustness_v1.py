#!/usr/bin/env python3
from __future__ import annotations
import sys, unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import qqq_spy_put_fixed_ratio_size_gated_v1 as engine
import audit_start_phase_robustness_v1 as audit

def trade(eid,policy,status,pnl="",signal="2025-01-01",entry="2025-01-02",
          exit_day="2025-01-12",last="2025-01-20",obligation="76500",lq="1",sq="3"):
    return {"episode_id":str(eid),"policy":policy,"status":status,"net_pnl_usd":str(pnl),
      "signal_date":signal,"entry_date":entry,"exit_date":exit_day,"last_observed_date":last,
      "spy_put_strike_assignment_obligation_usd":obligation,"long_qqq_qty":lq,"short_spy_qty":sq}

class StartPhaseOptionTests(unittest.TestCase):
    def test_phase_defaults_to_zero(self):
        with patch.object(sys,"argv",["replay"]):
            self.assertEqual(engine.parse_args().initial_phase_sessions,0)

    def test_phase_is_explicitly_selected(self):
        with patch.object(sys,"argv",["replay","--cohort-stride-sessions","5","--initial-phase-sessions","3"]):
            args=engine.parse_args()
        self.assertEqual(args.cohort_stride_sessions,5)
        self.assertEqual(args.initial_phase_sessions,3)

    def test_phase_must_be_less_than_stride_and_rejected_before_data_download(self):
        with patch.object(sys,"argv",["replay","--cohort-stride-sessions","5","--initial-phase-sessions","5"]):
            args=engine.parse_args()
        with self.assertRaisesRegex(ValueError,"initial phase"):
            engine.run_replay(args)

class PhaseAuditTests(unittest.TestCase):
    def test_unresolved_not_zero_filled_and_stress_cost_applied(self):
        rows=[trade(1,"HOLD_20_SESSIONS","RESOLVED",100),
              trade(2,"HOLD_20_SESSIONS","UNRESOLVED_SOURCE_END","",signal="2025-01-15",
                    entry="2025-01-16",exit_day="",last="2025-01-20")]
        r=audit.summarize(rows,2,"1Y",date(2024,7,23),date(2025,7,23),1.0,"HOLD_20_SESSIONS")
        self.assertEqual((r["opened"],r["resolved"],r["unresolved"]),(2,1,1))
        self.assertEqual(r["mean_net_pnl_usd"],100.0)
        self.assertEqual(r["stress_annualized_net_pnl_usd"],60.0)

    def test_peak_exposure_includes_positions_open_before_window(self):
        rows=[trade(1,"HOLD_20_SESSIONS","RESOLVED",100,signal="2024-07-20",
                    entry="2024-07-22",exit_day="2024-07-25",obligation="50000"),
              trade(2,"HOLD_20_SESSIONS","RESOLVED",-50,signal="2024-07-24",
                    entry="2024-07-24",exit_day="2024-07-27",obligation="75000")]
        n,cash=audit.peak_exposure(rows,date(2024,7,23),date(2024,7,31))
        self.assertEqual((n,cash),(2,125000.0))

if __name__=="__main__":
    unittest.main(verbosity=2)
