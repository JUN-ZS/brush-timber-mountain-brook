"""Unit tests for drawdown_alert + DD_EPISODES cache preference."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from backtest.drawdown_alert import (
    PINNED_FEATURE_HASH,
    PINNED_PACK_HASH,
    alert_report,
    find_drawdown_episodes,
    index_episodes,
    load_dd_episodes,
)


ROOT = Path(__file__).resolve().parents[2]
FEATURE = ROOT / "data/features/DD_EPISODES" / f"dd_episodes.v1_{PINNED_PACK_HASH}" / "dd_episodes.json"


class TestDrawdownAlert(unittest.TestCase):
    def test_feature_file_pinned(self):
        self.assertTrue(FEATURE.is_file(), f"missing pinned feature: {FEATURE}")
        doc = json.loads(FEATURE.read_text(encoding="utf-8"))
        self.assertEqual(doc.get("algorithm_version"), "dd_episodes.v1")
        self.assertEqual(doc.get("feature_hash"), PINNED_FEATURE_HASH)
        self.assertEqual(doc.get("manifest_hash"), PINNED_PACK_HASH)
        self.assertIn("QQQ", doc.get("symbols") or {})

    def test_load_prefers_cache(self):
        eps, meta = load_dd_episodes(FEATURE, symbol="QQQ", repo_root=ROOT)
        self.assertEqual(meta["source"], "DD_EPISODES_CACHE")
        self.assertIsNotNone(eps)
        self.assertGreaterEqual(len(eps or []), 5)
        self.assertEqual(meta["feature_hash"], PINNED_FEATURE_HASH)

    def test_hash_mismatch_falls_back_meta(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "dd.json"
            p.write_text(
                json.dumps(
                    {
                        "algorithm_version": "dd_episodes.v1",
                        "feature_hash": "deadbeef",
                        "manifest_hash": "WRONG",
                        "symbols": {"QQQ": {"episodes": []}},
                    }
                ),
                encoding="utf-8",
            )
            eps, meta = load_dd_episodes(p, symbol="QQQ", expect_pack_hash=PINNED_PACK_HASH)
            self.assertIsNone(eps)
            self.assertEqual(meta["source"], "HASH_MISMATCH")

    def test_index_and_alert_report_uses_cache(self):
        u = json.loads((ROOT / "src/data/universe.json").read_text(encoding="utf-8"))
        dates = u["dates"]
        raw = u["c"]["QQQ"]
        last = None
        prices = []
        for x in raw:
            if isinstance(x, (int, float)) and x == x and x > 0:
                last = float(x)
            prices.append(last if last is not None else float("nan"))
        start = next(i for i, x in enumerate(prices) if x == x)
        rep = alert_report(dates[start:], prices[start:], repo_root=ROOT, symbol="QQQ")
        self.assertEqual(rep["episodes_source"]["source"], "DD_EPISODES_CACHE")
        self.assertFalse(rep["looks_like_historical_max_dd"])
        self.assertIn("worst_episodes", rep)
        self.assertTrue(rep["worst_episodes"])

    def test_scanner_fallback_still_works(self):
        dates = [f"2020-01-{i:02d}" for i in range(1, 21)]
        prices = [100.0] * 5 + [90.0, 85.0, 80.0] + [82.0, 88.0, 100.0] + [101.0] * 9
        eps = find_drawdown_episodes(dates, prices, min_dd=-0.05)
        self.assertTrue(eps)
        self.assertLess(eps[0]["dd"], -0.1)


if __name__ == "__main__":
    unittest.main()
