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


class PutRatioDynamicBarApiContractTests(unittest.TestCase):
    def test_pinned_dynamic_snapshot_is_budget_gated(self):
        payload = server.load_put_ratio_dynamic_bar()
        meta = payload["metadata"]
        self.assertEqual(payload["schemaVersion"], "QQQ_PUT_RATIO_DYNAMIC_BAR_SNAPSHOT_V1")
        self.assertEqual((meta["start"], meta["end"], meta["episodes"]), ("2018-03-01", "2025-12-15", 62))
        self.assertEqual((meta["long"], meta["short"]), (1, 5))
        self.assertEqual(meta["allowedUnits"], 0)
        self.assertEqual(meta["budgetBreachEpisodes"], 62)
        self.assertGreater(meta["oneUnitWorstTerminalLossUsd"], meta["budgetUsd"])
        self.assertEqual(payload["status"], "RESEARCH_DIAGNOSTIC_ONLY_BUDGET_BYPASS")
        self.assertEqual(len(payload["barRows"]), 162)
        self.assertEqual(len(payload["drawdownRows"]), 14)
        levels = {row[3] for row in payload["barRows"]}
        self.assertEqual(levels, {0.5, 1.0, 2.0})

    def test_missing_dynamic_snapshot_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            missing = Path(td) / "missing.json"
            with patch.object(server, "PUT_RATIO_DYNAMIC_BAR_SNAPSHOT", missing):
                with self.assertRaises(FileNotFoundError):
                    server.load_put_ratio_dynamic_bar()

    def test_wrong_dynamic_schema_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            wrong = Path(td) / "wrong.json"
            wrong.write_text(json.dumps({"schemaVersion": "OTHER"}), encoding="utf-8")
            with patch.object(server, "PUT_RATIO_DYNAMIC_BAR_SNAPSHOT", wrong):
                with self.assertRaisesRegex(ValueError, "schema"):
                    server.load_put_ratio_dynamic_bar()

    def test_budget_bypass_label_cannot_be_removed(self):
        payload = json.loads(server.PUT_RATIO_DYNAMIC_BAR_SNAPSHOT.read_text(encoding="utf-8"))
        payload["metadata"]["allowedUnits"] = 1
        with tempfile.TemporaryDirectory() as td:
            candidate = Path(td) / "wrong_budget.json"
            candidate.write_text(json.dumps(payload), encoding="utf-8")
            with patch.object(server, "PUT_RATIO_DYNAMIC_BAR_SNAPSHOT", candidate):
                with self.assertRaisesRegex(ValueError, "budget-bypass"):
                    server.load_put_ratio_dynamic_bar()


if __name__ == "__main__":
    unittest.main(verbosity=2)
