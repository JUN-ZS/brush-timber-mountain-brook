"""Independent integrity tests for the published compact glidepath v2 preview.

Run from the repository root:
    python -m unittest research.audit_stage2.test_glidepath_v2_preview -v

These tests check the checked-in HTML, embedded data conservation, selector-to-metric
routing and JavaScript syntax. They are not a substitute for a real-browser visual
and interaction test.
"""
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from collections import Counter, defaultdict
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HTML_PATH = ROOT / "v2.html"


class IdAudit(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name == "id" and value:
                self.ids.append(value)


def load_html_and_pack():
    html = HTML_PATH.read_text(encoding="utf-8")
    match = re.search(r"const RAW_PACK=(\{.*?\});\s*const TG=", html, re.S)
    if not match:
        raise AssertionError("Could not locate compact RAW_PACK payload in v2.html")
    return html, json.loads(match.group(1))


class GlidepathV2IndependentAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html, cls.pack = load_html_and_pack()
        cls.script_match = re.search(r"<script>(.*?)</script>", cls.html, re.S)
        if not cls.script_match:
            raise AssertionError("Inline JavaScript block not found")

    def test_html_ids_are_unique(self):
        parser = IdAudit()
        parser.feed(self.html)
        duplicates = sorted(key for key, count in Counter(parser.ids).items() if count > 1)
        self.assertFalse(duplicates, f"Duplicate HTML IDs: {duplicates}")
        self.assertGreaterEqual(len(parser.ids), 40)

    def test_javascript_syntax(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is unavailable; CI workflow checks it separately")
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".js") as handle:
            handle.write(self.script_match.group(1))
            handle.flush()
            proc = subprocess.run([node, "--check", handle.name], text=True,
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        self.assertEqual(proc.returncode, 0, proc.stdout)

    def test_compact_data_counts_and_unique_keys(self):
        p = self.pack
        self.assertEqual(len(p["d"]), 768)
        self.assertEqual(len(p["a"]), 8448)
        self.assertEqual(len(p["h"]), 3072)
        self.assertEqual(len(p["c"]), 10752)
        self.assertEqual(len(p["cm"]), 14)
        self.assertEqual(len({tuple(r[:4]) for r in p["d"]}), 768)
        self.assertEqual(len({tuple(r[:5]) for r in p["a"]}), 8448)
        self.assertEqual(len({tuple(r[:5]) for r in p["c"]}), 10752)

    def test_all_histogram_counts_conserve_157_windows(self):
        for row in self.pack["h"]:
            self.assertEqual(sum(row[10]), 157, f"Histogram failed to conserve windows: {row[:5]}")

    def test_each_scenario_has_14_calendar_start_cohorts(self):
        groups = defaultdict(list)
        for row in self.pack["c"]:
            groups[tuple(row[:4])].append(int(row[4]))
        self.assertEqual(len(groups), 768)
        for key, years in groups.items():
            self.assertEqual(len(years), 14, f"Cohort count mismatch for {key}")
            self.assertEqual(len(set(years)), 14, f"Duplicate cohort year for {key}")

    def test_year_10_annual_rows_match_scenario_summaries(self):
        annual_by_key = {
            (row[1], row[2], row[3], row[4], int(row[0])): row
            for row in self.pack["a"]
        }
        pairs = ((4, 5), (5, 6), (6, 7), (7, 8), (8, 9),
                 (9, 10), (11, 13), (12, 14), (13, 15), (14, 16))
        for scenario in self.pack["d"]:
            annual = annual_by_key.get((scenario[0], scenario[1], scenario[2], scenario[3], 10))
            self.assertIsNotNone(annual, f"Missing year-10 row for {scenario[:4]}")
            for summary_index, annual_index in pairs:
                self.assertAlmostEqual(float(scenario[summary_index]), float(annual[annual_index]),
                                       delta=0.001, msg=f"Mismatch for {scenario[:4]} field {summary_index}")

    def test_statistic_selectors_route_only_to_supported_fields(self):
        self.assertIn('id="navStatView"', self.html)
        self.assertIn('id="ddStatView"', self.html)
        self.assertIn('id="cagrStatView"', self.html)
        self.assertNotIn('id="statView"', self.html)
        self.assertNotIn("s.stat", self.html)
        self.assertIn('const navMetric=s.navStat==="p05"?"p05_nav_usd":s.navStat==="worst"?"worst_nav_usd":"median_nav_usd";', self.html)
        self.assertIn('const ddMetric=s.ddStat==="worst"?"worst_drawdown_to_date":"median_drawdown_to_date";', self.html)
        self.assertIn('const cagrMetric=s.cagrStat==="p05"?"p05_cumulative_twr_cagr":"median_cumulative_twr_cagr";', self.html)

    def test_inflation_mode_does_not_mislabel_nominal_breach_counts(self):
        self.assertIn("年化通膨假設", self.html)
        self.assertIn("T10YIE 代理，2026-10-16", self.html)
        self.assertIn("名目低於本金窗口", self.html)
        self.assertIn("本頁尚未計算實質門檻違約窗口數", self.html)
        self.assertIn("提款／缺口金額仍為名目美元", self.html)
        self.assertNotIn("2.35% CPI", self.html)
        self.assertNotIn("3.50% CPI", self.html)

    def test_unmodeled_STRIPS_baseline_has_no_guaranteed_value_claim(self):
        self.assertIn("STRIPS/TIPS 尚未納入本頁同條件回測", self.html)
        self.assertNotIn("$182,270", self.html)
        self.assertNotIn("$144,475", self.html)
        self.assertNotIn("保證名目底線", self.html)
        self.assertIn("不代表未來最優", self.html)

    def test_audit_and_optional_bundle_match_current_html(self):
        import hashlib
        import zipfile
        audit_path = ROOT / "glidepath_preview_optimized_audit.json"
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        self.assertNotEqual(audit.get("status"), "ALL_CHECKS_PASSED")
        self.assertIn("BROWSER", str(audit.get("status", "")).upper())
        html_bytes = self.html.encode("utf-8")
        expected_sha = hashlib.sha256(html_bytes).hexdigest()
        if audit.get("bundle_status") == "CURRENT_ZIP_BUILT_FROM_VERIFIED_HTML":
            self.assertEqual(audit.get("sha256"), expected_sha)
            bundle_path = ROOT / "glidepath_interactive_preview_optimized_bundle.zip"
            self.assertTrue(bundle_path.exists())
            self.assertEqual(audit.get("bundle_bytes"), bundle_path.stat().st_size)
            with zipfile.ZipFile(bundle_path) as bundle:
                self.assertEqual(bundle.read("v2.html"), html_bytes)
                embedded_audit = json.loads(bundle.read("glidepath_preview_optimized_audit.json"))
                self.assertEqual(embedded_audit, audit)
        else:
            self.assertEqual(audit.get("bundle_status"), "STALE_DO_NOT_USE_UNTIL_REBUILT_FROM_THIS_HTML")
            self.assertIsNone(audit.get("sha256"))


if __name__ == "__main__":
    unittest.main()
