#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, json, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import validate_prospective_oos_v1 as validator

class ProspectiveProtocolTests(unittest.TestCase):
    def test_committed_protocol_is_frozen(self):
        p=json.loads(validator.DEFAULT_PROTOCOL.read_text(encoding="utf-8"))
        self.assertEqual(validator.validate_protocol(p),[])
        self.assertEqual(p["primary_candidate"]["ratio"],"1:3")
        self.assertEqual(p["primary_candidate"]["exit_policy"],"HOLD_20_SESSIONS")
        self.assertEqual(p["quantities"]["ratios_in_scope"],["1:3","2:4","4:5","1:6"])

    def test_parameter_mutation_is_rejected(self):
        p=json.loads(validator.DEFAULT_PROTOCOL.read_text(encoding="utf-8"))
        p["entry"]["cohort_stride_common_sessions"]=20
        self.assertTrue(validator.validate_protocol(p))

    def test_missing_fresh_data_stays_blocked_not_passed(self):
        p=json.loads(validator.DEFAULT_PROTOCOL.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as td:
            r=validator.readiness(p,Path(td))
        self.assertEqual(r["status"],"BLOCKED_MISSING_FRESH_QUOTES")
        self.assertFalse(r["replay_performed"])
        self.assertFalse(r["source_manifest_present"])

    def test_quote_schema_requires_sizes_and_post_cutoff_dates(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"options.csv"
            with p.open("w",newline="",encoding="utf-8") as f:
                w=csv.DictWriter(f,fieldnames=["date","contract_id","symbol","expiration","strike","type","bid","ask","bid_size","ask_size","delta"])
                w.writeheader()
                w.writerow({"date":"2026-10-21","contract_id":"QQQ261120P00500000","symbol":"QQQ","expiration":"2026-11-20","strike":500,"type":"put","bid":5.0,"ask":5.2,"bid_size":10,"ask_size":12,"delta":-0.25})
            self.assertEqual(validator.validate_csv(p,validator.REQUIRED_OPTIONS),[])
            with p.open("w",newline="",encoding="utf-8") as f:
                w=csv.DictWriter(f,fieldnames=["date","contract_id","symbol","expiration","strike","type","bid","ask","bid_size","ask_size","delta"])
                w.writeheader()
                w.writerow({"date":"2025-12-15","contract_id":"QQQ251219P00500000","symbol":"QQQ","expiration":"2025-12-19","strike":500,"type":"put","bid":5.0,"ask":5.2,"bid_size":10,"ask_size":12,"delta":-0.25})
            self.assertTrue(validator.validate_csv(p,validator.REQUIRED_OPTIONS))

    def test_bad_quote_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"options.csv"
            with p.open("w",newline="",encoding="utf-8") as f:
                w=csv.DictWriter(f,fieldnames=["date","contract_id","symbol","expiration","strike","type","bid","ask","bid_size","ask_size","delta"])
                w.writeheader()
                w.writerow({"date":"2026-10-21","contract_id":"SPY261120P00600000","symbol":"SPY","expiration":"2026-11-20","strike":600,"type":"put","bid":6.0,"ask":5.5,"bid_size":10,"ask_size":12,"delta":-0.25})
            self.assertTrue(validator.validate_csv(p,validator.REQUIRED_OPTIONS))

if __name__=="__main__": unittest.main(verbosity=2)
