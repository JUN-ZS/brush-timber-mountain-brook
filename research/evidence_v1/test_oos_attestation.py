from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from .ledger import sha256_json


EXPECTED_ENGINE_COMMIT = "930c949ec5260865f2bf3ee1c6e030dab7b8e4c4"
EXPECTED_ENGINE_SHA256 = "56bff3fc5240871df7dff010c55a8f01f1fe8ac22d6f45036958723a68e3e15e"
EXPECTED_LOCK_HASH = "26adeb6f55149c367903af27b953dafeb657d1470455b8f7c42e99a63c3d8460"
EXPECTED_LOCK_BLOB_SHA = "1ba879f24e367570c3a4e3b04bca607450dc2b8d"
EXPECTED_DATA = {
    "QQQ_options.parquet": "1f831556cd87ec9d7af43d3b47a69a829ffb2fb199cfcef4ff55d289badf8734",
    "QQQ_underlying.parquet": "78c015fd7fa9d493cd798d5ae81b3c2ae6dc3b8176e25e7bb90cd4114b103351",
}


class LockedOOSAttestationTest(unittest.TestCase):
    def setUp(self):
        self.repo = Path(__file__).resolve().parents[2]
        self.path = self.repo / "research" / "evidence_v1" / "LOCKED_OOS_ATTESTATION.json"
        self.obj = json.loads(self.path.read_text(encoding="utf-8"))

    def test_attestation_schema_and_immutable_inputs(self):
        self.assertEqual(self.obj["schema"], "QQQ_LOCKED_OOS_ATTESTATION.v1")
        imm = self.obj["immutable_inputs"]
        self.assertEqual(imm["engine_commit"], EXPECTED_ENGINE_COMMIT)
        self.assertEqual(imm["strategy_lock_hash"], EXPECTED_LOCK_HASH)
        self.assertEqual(imm["strategy_lock_blob_sha"], EXPECTED_LOCK_BLOB_SHA)
        self.assertEqual(imm["canonical_data_sha256"], EXPECTED_DATA)
        self.assertEqual(self.obj["replay_definition"]["candidate_family_configs"], 72)
        self.assertFalse(self.obj["replay_definition"]["post_window_data_used"])
        self.assertEqual(
            self.obj["replay_definition"]["selection_status"],
            "LOCKED_FROM_PRIOR_FULL_SAMPLE_V22_AUDIT",
        )
        self.assertEqual(
            self.obj["replay_definition"]["virgin_oos_status"],
            "NOT_VIRGIN_BECAUSE_PRIOR_SELECTION_USED_FULL_V22_SAMPLE",
        )

    def test_current_lock_matches_attestation(self):
        lock_path = self.repo / "research" / "evidence_v1" / "STRATEGY_LOCK.json"
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        self.assertEqual(sha256_json(lock), EXPECTED_LOCK_HASH)
        self.assertEqual(lock["research_engine_commit"], EXPECTED_ENGINE_COMMIT)
        self.assertEqual(lock["strategy_id"], "QQQ_DYNAMIC_NEAR_LONG_V22_CANDIDATE_FAMILY")
        self.assertEqual(lock["strategy_version"], "V22-family-30D-1.5x")

    def test_current_frozen_engine_matches_attestation(self):
        engine_path = self.repo / "research" / "qqq_dynamic_near_long_state_engine_v22_930c949.py"
        digest = hashlib.sha256(engine_path.read_bytes()).hexdigest()
        self.assertEqual(digest, EXPECTED_ENGINE_SHA256)

    def test_attestation_requires_manual_replay_after_immutable_drift(self):
        self.assertEqual(self.obj["status"], "ARCHIVED_INPUT_MATCH_REQUIRED")
        self.assertIn("Any alpha/lock/frozen-engine change invalidates it", self.obj["rule"])


if __name__ == "__main__":
    unittest.main()
