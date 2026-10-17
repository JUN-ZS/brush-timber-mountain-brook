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
                   "observation_timezone":"America/New_York",
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



def write_snapshot(root: Path, snap: dict):
    snapshot_dir = root / "snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    path = snapshot_dir / f"{snap['snapshot_id']}.json"
    path.write_text(json.dumps(snap, indent=2), encoding="utf-8")
    return path


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
            self.assertEqual(result["leg_quote_statuses"][0],"MISSING")

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


    def test_scaled_positions_change_frozen_signature(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            signal=make_snapshot(root,event_type="SIGNAL")
            signal["signal"]={"rule_id":shadow.SIGNAL_RULE_ID,"state":"TRIGGERED",
                              "qqq_close_vs_ma20_pct":-2.4,"previous_close_vs_ma20_pct":-2.3,
                              "qqq_up_day":True,"vix_5_session_change_pct":-4.0}
            entry=make_snapshot(root)
            entry["snapshot_id"]="SNAP_20261021_155500_001"
            entry["snapshot_date"]="2026-10-21"
            entry["captured_at"]="2026-10-21T15:55:00-04:00"
            entry["event_type"]="ENTRY"
            entry["market"]["qqq_observed_at"]="2026-10-21T15:55:00-04:00"
            entry["market"]["vix_observed_at"]="2026-10-21T15:55:00-04:00"
            for leg in entry["legs"]:
                leg["qty"]=2
                leg["quote_date"]="2026-10-21"
                leg["quote_captured_at"]="2026-10-21T15:55:00-04:00"
            a=shadow.validate_snapshot(signal,root)
            b=shadow.validate_snapshot(entry,root)
            self.assertNotEqual(a["contract_signature"],b["contract_signature"])


    def test_manila_capture_after_et_close_validates_against_market_date(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            snap=make_snapshot(root)
            # 03:55 in Manila on Oct 21 is 15:55 EDT on the prior U.S. market date.
            local_ts="2026-10-21T03:55:00+08:00"
            snap["captured_at"]=local_ts
            snap["market"]["qqq_observed_at"]=local_ts
            snap["market"]["vix_observed_at"]=local_ts
            for leg in snap["legs"]:
                leg["quote_captured_at"]=local_ts
            result=shadow.validate_snapshot(snap,root)
            self.assertEqual(result["snapshot_date"],"2026-10-20")
            self.assertEqual(result["evidence"]["observation_timezone"],"America/New_York")

    def test_timestamp_on_next_market_date_is_rejected_after_timezone_conversion(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            snap=make_snapshot(root)
            next_market_day="2026-10-21T17:00:00+08:00"
            snap["captured_at"]=next_market_day
            with self.assertRaises(shadow.SnapshotValidationError):
                shadow.validate_snapshot(snap,root)

    def test_invalid_observation_timezone_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            snap=make_snapshot(root)
            snap["source"]["observation_timezone"]="Mars/Olympus"
            with self.assertRaises(shadow.SnapshotValidationError):
                shadow.validate_snapshot(snap,root)

    def test_automatic_execution_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            snap=make_snapshot(root,execution_enabled=True)
            with self.assertRaises(shadow.SnapshotValidationError):
                shadow.validate_snapshot(snap,root)


    def test_daily_not_triggered_signal_status_allows_zero_option_legs(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            snap = make_snapshot(
                root,
                event_type="SIGNAL",
                strategy_id="QQQ_REVERSAL_SIGNAL_ONLY",
                legs=[],
            )
            snap["signal"] = {
                "rule_id": shadow.SIGNAL_RULE_ID,
                "state": "NOT_TRIGGERED",
                "qqq_close_vs_ma20_pct": -1.2,
                "previous_close_vs_ma20_pct": -0.8,
                "qqq_up_day": False,
                "vix_5_session_change_pct": 2.4,
            }
            result = shadow.validate_snapshot(snap, root)
            self.assertEqual(result["status"], "VALID_RESEARCH_SNAPSHOT")
            self.assertEqual(result["leg_count"], 0)
            self.assertEqual(result["contract_signature"], [])
            self.assertFalse(result["execution_enabled"])
            self.assertFalse(result["order_placed"])


    def test_entry_rejects_a_missing_leg_quote(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            snap = make_snapshot(root, event_type="ENTRY")
            snap["legs"][0].update({
                "quote_status": "MISSING", "bid": None, "ask": None,
                "bid_size": None, "ask_size": None, "delta": None,
                "missing_reason": "Exact contract quote absent",
            })
            with self.assertRaises(shadow.SnapshotValidationError):
                shadow.validate_snapshot(snap, root)

    def test_mark_with_missing_quote_must_be_recorded_as_missing_mark(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            snap = make_snapshot(root, event_type="MARK")
            snap["legs"][1].update({
                "quote_status": "MISSING", "bid": None, "ask": None,
                "bid_size": None, "ask_size": None, "delta": None,
                "missing_reason": "Exact contract quote absent",
            })
            with self.assertRaises(shadow.SnapshotValidationError):
                shadow.validate_snapshot(snap, root)

    def test_missing_mark_requires_at_least_one_missing_leg(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            snap = make_snapshot(root, event_type="MISSING_MARK")
            with self.assertRaises(shadow.SnapshotValidationError):
                shadow.validate_snapshot(snap, root)

    def test_non_triggered_or_incomplete_signal_cannot_enter(self):
        for signal_state in ("NOT_TRIGGERED", "INCOMPLETE"):
            with self.subTest(signal_state=signal_state), tempfile.TemporaryDirectory() as d:
                root = Path(d)
                signal = make_snapshot(root, event_type="SIGNAL", legs=[])
                signal["snapshot_id"] = "SIGNAL_20261020"
                signal["signal"] = {
                    "rule_id": shadow.SIGNAL_RULE_ID,
                    "state": signal_state,
                    "qqq_close_vs_ma20_pct": -1.2,
                    "previous_close_vs_ma20_pct": -0.8,
                    "qqq_up_day": False,
                    "vix_5_session_change_pct": 2.4,
                }
                entry = make_snapshot(root, event_type="ENTRY")
                entry["snapshot_id"] = "ENTRY_20261021"
                entry["event_id"] = signal["event_id"]
                entry["strategy_id"] = signal["strategy_id"]
                entry["snapshot_date"] = "2026-10-21"
                entry["captured_at"] = "2026-10-21T15:55:00-04:00"
                entry["market"]["qqq_observed_at"] = entry["captured_at"]
                entry["market"]["vix_observed_at"] = entry["captured_at"]
                for leg in entry["legs"]:
                    leg["quote_date"] = entry["snapshot_date"]
                    leg["quote_captured_at"] = entry["captured_at"]
                write_snapshot(root, signal)
                write_snapshot(root, entry)
                with self.assertRaises(shadow.SnapshotValidationError):
                    shadow.validate_directory(root / "snapshots", root)

    def test_blocked_entry_cannot_later_become_a_fill(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            signal = make_snapshot(root, event_type="SIGNAL")
            signal["snapshot_id"] = "SIGNAL_20261020"
            signal["signal"] = {
                "rule_id": shadow.SIGNAL_RULE_ID,
                "state": "TRIGGERED",
                "qqq_close_vs_ma20_pct": -2.4,
                "previous_close_vs_ma20_pct": -2.3,
                "qqq_up_day": True,
                "vix_5_session_change_pct": -4.0,
            }
            blocked = make_snapshot(root, event_type="BLOCKED_ENTRY")
            blocked["snapshot_id"] = "BLOCKED_20261021"
            blocked["event_id"] = signal["event_id"]
            blocked["strategy_id"] = signal["strategy_id"]
            blocked["snapshot_date"] = "2026-10-21"
            blocked["captured_at"] = "2026-10-21T15:55:00-04:00"
            blocked["market"]["qqq_observed_at"] = blocked["captured_at"]
            blocked["market"]["vix_observed_at"] = blocked["captured_at"]
            blocked["legs"][0]["quote_date"] = blocked["snapshot_date"]
            blocked["legs"][0]["quote_captured_at"] = blocked["captured_at"]
            blocked["legs"][0]["ask_size"] = 0
            for leg in blocked["legs"][1:]:
                leg["quote_date"] = blocked["snapshot_date"]
                leg["quote_captured_at"] = blocked["captured_at"]

            entry = make_snapshot(root, event_type="ENTRY")
            entry["snapshot_id"] = "ENTRY_20261022"
            entry["event_id"] = signal["event_id"]
            entry["strategy_id"] = signal["strategy_id"]
            entry["snapshot_date"] = "2026-10-22"
            entry["captured_at"] = "2026-10-22T15:55:00-04:00"
            entry["market"]["qqq_observed_at"] = entry["captured_at"]
            entry["market"]["vix_observed_at"] = entry["captured_at"]
            for leg in entry["legs"]:
                leg["quote_date"] = entry["snapshot_date"]
                leg["quote_captured_at"] = entry["captured_at"]

            write_snapshot(root, signal)
            write_snapshot(root, blocked)
            write_snapshot(root, entry)
            with self.assertRaises(shadow.SnapshotValidationError):
                shadow.validate_directory(root / "snapshots", root)

    def test_position_quantity_cannot_change_between_signal_and_entry(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            signal = make_snapshot(root, event_type="SIGNAL")
            signal["snapshot_id"] = "SIGNAL_20261020"
            signal["signal"] = {
                "rule_id": shadow.SIGNAL_RULE_ID,
                "state": "TRIGGERED",
                "qqq_close_vs_ma20_pct": -2.4,
                "previous_close_vs_ma20_pct": -2.3,
                "qqq_up_day": True,
                "vix_5_session_change_pct": -4.0,
            }
            entry = make_snapshot(root, event_type="ENTRY")
            entry["snapshot_id"] = "ENTRY_20261021"
            entry["event_id"] = signal["event_id"]
            entry["strategy_id"] = signal["strategy_id"]
            entry["snapshot_date"] = "2026-10-21"
            entry["captured_at"] = "2026-10-21T15:55:00-04:00"
            entry["market"]["qqq_observed_at"] = entry["captured_at"]
            entry["market"]["vix_observed_at"] = entry["captured_at"]
            for leg in entry["legs"]:
                leg["qty"] = 2
                leg["quote_date"] = entry["snapshot_date"]
                leg["quote_captured_at"] = entry["captured_at"]
            write_snapshot(root, signal)
            write_snapshot(root, entry)
            with self.assertRaises(shadow.SnapshotValidationError):
                shadow.validate_directory(root / "snapshots", root)

    def test_terminal_exit_rejects_later_marks(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            signal = make_snapshot(root, event_type="SIGNAL")
            signal["snapshot_id"] = "SIGNAL_20261020"
            signal["signal"] = {
                "rule_id": shadow.SIGNAL_RULE_ID,
                "state": "TRIGGERED",
                "qqq_close_vs_ma20_pct": -2.4,
                "previous_close_vs_ma20_pct": -2.3,
                "qqq_up_day": True,
                "vix_5_session_change_pct": -4.0,
            }
            entry = make_snapshot(root, event_type="ENTRY")
            exit_record = make_snapshot(root, event_type="EXIT")
            mark = make_snapshot(root, event_type="MARK")
            for snap, sid, day in (
                (entry, "ENTRY_20261021", "2026-10-21"),
                (exit_record, "EXIT_20261022", "2026-10-22"),
                (mark, "MARK_20261023", "2026-10-23"),
            ):
                snap["snapshot_id"] = sid
                snap["event_id"] = signal["event_id"]
                snap["strategy_id"] = signal["strategy_id"]
                snap["snapshot_date"] = day
                snap["captured_at"] = f"{day}T15:55:00-04:00"
                snap["market"]["qqq_observed_at"] = snap["captured_at"]
                snap["market"]["vix_observed_at"] = snap["captured_at"]
                for leg in snap["legs"]:
                    leg["quote_date"] = day
                    leg["quote_captured_at"] = snap["captured_at"]
            write_snapshot(root, signal)
            write_snapshot(root, entry)
            write_snapshot(root, exit_record)
            write_snapshot(root, mark)
            with self.assertRaises(shadow.SnapshotValidationError):
                shadow.validate_directory(root / "snapshots", root)

if __name__ == "__main__":
    unittest.main(verbosity=2)
