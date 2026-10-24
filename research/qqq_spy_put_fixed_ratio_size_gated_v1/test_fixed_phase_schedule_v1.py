#!/usr/bin/env python3
from __future__ import annotations
import sys, unittest
from datetime import date
from pathlib import Path

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import qqq_spy_put_fixed_phase_v1 as engine
import audit_fixed_phase_schedule_v1 as audit

class FixedAnchorCadenceTests(unittest.TestCase):
    def test_slots_are_immutable_even_when_one_slot_cannot_select_a_pair(self):
        slots=list(engine.fixed_schedule_indices(22,2,5))
        missing={7}
        selected=[i for i in slots if i not in missing]
        self.assertEqual(slots,[2,7,12,17])
        self.assertEqual(selected,[2,12,17])
        self.assertNotEqual(selected,[2,12,17,22])

    def test_all_phases_remain_on_phase_plus_k_times_stride(self):
        for phase in range(5):
            slots=list(engine.fixed_schedule_indices(31,phase,5))
            self.assertTrue(slots)
            self.assertTrue(all(i % 5 == phase for i in slots))
            self.assertEqual(slots, list(range(phase,31,5)))

    def test_invalid_schedule_inputs_rejected(self):
        with self.assertRaisesRegex(ValueError,"initial phase"):
            engine.fixed_schedule_indices(20,5,5)
        with self.assertRaisesRegex(ValueError,"stride"):
            engine.fixed_schedule_indices(20,0,0)

class FixedSlotAuditTests(unittest.TestCase):
    def sample(self, selected_indices=(0,5,15,20), missed=(10,)):
        phase=0; stride=5; session_count=22
        slots=list(range(phase,session_count,stride))
        schedule_skips=[{"scheduled_index":i,"scheduled_signal_date":f"2025-01-{i+1:02d}",
                         "status":"SCHEDULE_SKIPPED","reason":"NO_ELIGIBLE_COMMON_EXPIRY_PAIR"} for i in missed]
        summary={
          "coverage":{"common_underlying_sessions":session_count},
          "selection":{"schedule_mode":"FIXED_ANCHOR_NO_REANCHOR","initial_phase_sessions":phase,
                       "cohort_stride_sessions":stride,"allow_overlapping_cohorts":True},
          "fixed_entry_schedule":{"mode":"FIXED_ANCHOR_NO_REANCHOR","phase_sessions":phase,
               "scheduled_opportunities":len(slots),"selected_signals":len(selected_indices),
               "skipped_opportunities":len(missed)},
          "cohort":{"selected_signals":len(selected_indices),"entered_cohorts":len(selected_indices)-1,
                    "entry_skipped":1},
        }
        entry_rows=[{"signal_index":str(i)} for i in selected_indices[:-1]]
        entry_skip_rows=[{"signal_index":str(selected_indices[-1])}]
        return summary,entry_rows,entry_skip_rows,schedule_skips

    def test_slot_accounting_and_signal_anchor_pass(self):
        args=self.sample()
        out=audit.validate_schedule_phase(0,*args)
        self.assertEqual(out["status"],"PASS")
        self.assertEqual(out["scheduled_opportunities"],5)
        self.assertEqual(out["selected_signals"]+out["skipped_opportunities"],5)

    def test_reanchored_signal_is_rejected(self):
        args=self.sample(selected_indices=(0,5,11,20),missed=(10,))
        with self.assertRaisesRegex(ValueError,"off fixed cadence"):
            audit.validate_schedule_phase(0,*args)

    def test_missing_slot_must_be_recorded_on_scheduled_index(self):
        args=self.sample(missed=(11,))
        with self.assertRaisesRegex(ValueError,"skip records off fixed cadence"):
            audit.validate_schedule_phase(0,*args)

if __name__=="__main__":
    unittest.main(verbosity=2)
