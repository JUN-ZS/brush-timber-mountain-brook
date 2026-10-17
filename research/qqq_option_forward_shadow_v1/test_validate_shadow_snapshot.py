#!/usr/bin/env python3
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import validate_shadow_snapshot as shadow


def make_snapshot(root: Path, **overrides):
    ev_dir = root / "evidence"
    ev_dir.mkdir(parents=True, exist_ok=True)
    evidence = ev_dir / "shot.bin"
    evidence.write_bytes(b"immutable test evidence bytes")
    sha = hashlib.sha256(evidence.read_bytes()).hexdigest()
    ts = "2026-10-20T15:55:00-04:00"
    snap = {
        "schema_version": 1,
        "snapshot_id": "SNAP_20261020_155500_001",
        "event_id": "EVT_20261020_01",
        "strategy_id": "CALL_DEBIT_50D_10D",
        "event_type": "ENTRY",
        "snapshot_date": "2026-10-20",
        "captured_at": ts,
        "nav_usd": 80000,
        "market": {"symbol":"QQQ","qqq_price":520.0,"qqq_observed_at":ts,"vix":22.0,"vix_observed_at":ts},
        "signal": None,
        "source": {"source_type":"MANUAL_SCREEN_CAPTURE","provider":"CBOE_DELAYED_SCREEN",
                   "evidence_file":"evidence/shot.bin","evidence_sha256":sha},
        "execution_enabled": False,
        "order_placed": False,
        "legs": [
            {"contract_id":"QQQ261120C00520000","symbol":"QQQ","right":"C","expiry":"2026-11-20","strike":520,
             "position_side":"LONG","qty":1,"quote_status":"OBSERVED","quote_date":"2026-10-20",
             "quote_captured_at":ts,"bid":17.8,"ask":18.1,"bid_size":5,"ask_size":8,"delta":0.50,"missing_reason":None},
            {"contract_id":"QQQ261120C00560000","symbol":"QQQ","right":"C","expiry":"2026-11-20","strike":560,
             "position_side":"SHORT","qty":1,"quote_status":"OBSERVED","quote_date":"2026-10-20",
             "quote_captured_at":ts,"bid":4.2,"ask":4.5,"bid_size":7,"ask_size":9,"delta":0.10,"missing_reason":None},
        ],
    }
    snap.update(overrides)
    return snap


class ShadowSnapshotTests(unittest.TestCase):
    def test_valid_snapshot_requires_hash_verified_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            result=shadow.validate_snapshot(make_snapshot(root),root)
            self.assertEqual(result["status"],"VALID_RESEARCH_SNAPSHOT")
            self.assertEqual(result["leg_count"],2)
            self.assertFalse(result["order_placed"])

    def test_encoded_expiry_and_strike_mismatch_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            snap=make_snapshot(root)
            snap["legs"][0]["strike"]=521
            with self.assertRaises(shadow.SnapshotValidationError):
                shadow.validate_snapshot(snap,root)

    def test_triggered_signal_must_satisfy_frozen_rule(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            snap=make_snapshot(root,event_type="SIGNAL")
            snap["signal"]={"rule_id":shadow.SIGNAL_RULE_ID,"state":"TRIGGERED",
                            "qqq_close_vs_ma20_pct":-2.4,"previous_close_vs_ma20_pct":-2.3,
                            "qqq_up_day":True,"vix_5_session_change_pct":-4.0}
            shadow.validate_snapshot(snap,root)
            snap["signal"]["vix_5_session_change_pct"]=1.0
            with self.assertRaises(shadow.SnapshotValidationError):
                shadow.validate_snapshot(snap,root)

    def test_entry_uses_side_correct_visible_size(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            snap=make_snapshot(root)
            snap["legs"][0]["ask_size"]=0
            with self.assertRaises(shadow.SnapshotValidationError):
                shadow.validate_snapshot(snap,root)
            snap["event_type"]="BLOCKED_ENTRY"
            result=shadow.validate_snapshot(snap,root)
            self.assertEqual(result["status"],"VALID_RESEARCH_SNAPSHOT")

    def test_missing_mark_is_explicit_not_forward_filled(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            snap=make_snapshot(root,event_type="MISSING_MARK")
            snap["legs"][0].update({"quote_status":"MISSING","bid":None,"ask":None,"bid_size":None,
                                    "ask_size":None,"delta":None,"missing_reason":"Contract row absent from source"})
            result=shadow.validate_snapshot(snap,root)
            self.assertEqual(result["contract_signature"][0]["contract_id"],"QQQ261120C00520000")
            self.assertEqual(result["contract_signature"][0]["quote_status"],"MISSING")

    def test_evidence_hash_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            snap=make_snapshot(root)
            snap["source"]["evidence_sha256"]="0"*64
            with self.assertRaises(shadow.SnapshotValidationError):
                shadow.validate_snapshot(snap,root)

    def test_stale_quote_date_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            snap=make_snapshot(root)
            snap["legs"][0]["quote_date"]="2026-10-19"
            with self.assertRaises(shadow.SnapshotValidationError):
                shadow.validate_snapshot(snap,root)

    def test_automatic_execution_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            snap=make_snapshot(root,execution_enabled=True)
            with self.assertRaises(shadow.SnapshotValidationError):
                shadow.validate_snapshot(snap,root)


if __name__ == "__main__":
    unittest.main(verbosity=2)
