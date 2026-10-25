from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
import server  # noqa: E402


class PutRatioEvidenceApiContractTests(unittest.TestCase):
    def test_pinned_snapshot_is_loaded_read_only(self):
        payload = server.load_put_ratio_evidence()
        self.assertEqual(payload["schemaVersion"], "QQQ_PUT_RATIO_EVIDENCE_SNAPSHOT_V1")
        self.assertEqual(payload["metadata"]["optionEpisodes"], 62)
        self.assertEqual(payload["metadata"]["optionSourceEnd"], "2025-12-15")
        self.assertEqual(payload["curve"]["source_option_end"], "2025-12-15")
        self.assertEqual(payload["curve"]["trade_count"], 62)
        self.assertEqual(len(payload["curve"]["session_dates"]), 1960)
        self.assertEqual(len(payload["curve"]["cumulative_pnl_usd_by_policy"]), 13)
        manifest = payload["manifest"]
        self.assertTrue(manifest["dataJsonBlobSha"])
        self.assertTrue(manifest["portfolioCurveBlobSha"])
        self.assertTrue(manifest["profitWarningAnalysisBlobSha"])
        self.assertEqual(payload["status"], "RESEARCH_ONLY_DEPLOYMENT_BLOCKED")

    def test_missing_snapshot_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            missing = Path(td) / "missing.json"
            with patch.object(server, "PUT_RATIO_EVIDENCE_SNAPSHOT", missing):
                with self.assertRaises(FileNotFoundError):
                    server.load_put_ratio_evidence()

    def test_wrong_schema_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            wrong = Path(td) / "wrong.json"
            wrong.write_text(json.dumps({"schemaVersion": "OTHER"}), encoding="utf-8")
            with patch.object(server, "PUT_RATIO_EVIDENCE_SNAPSHOT", wrong):
                with self.assertRaisesRegex(ValueError, "schema"):
                    server.load_put_ratio_evidence()

    def test_wrong_source_window_fails_closed(self):
        payload = json.loads(server.PUT_RATIO_EVIDENCE_SNAPSHOT.read_text(encoding="utf-8"))
        payload["curve"]["source_option_end"] = "2026-01-01"
        with tempfile.TemporaryDirectory() as td:
            candidate = Path(td) / "wrong_window.json"
            candidate.write_text(json.dumps(payload), encoding="utf-8")
            with patch.object(server, "PUT_RATIO_EVIDENCE_SNAPSHOT", candidate):
                with self.assertRaisesRegex(ValueError, "source window"):
                    server.load_put_ratio_evidence()


if __name__ == "__main__":
    unittest.main(verbosity=2)
