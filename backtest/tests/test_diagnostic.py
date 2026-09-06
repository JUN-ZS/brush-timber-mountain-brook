import tempfile
import unittest
from pathlib import Path

from backtest.local_diagnostic import main, run_diagnostic
from backtest.report import render_txt, write_reports


REQUIRED_SECTIONS = [
    "FUTU V2.3 LOCAL RUN RESULT",
    "## ENVIRONMENT",
    "## FUTU OPEND",
    "## QUOTE TEST",
    "## OPTION CHAIN",
    "## OPTION QUOTE",
    "## OPTION SURFACE",
    "## STATE ENGINE",
    "## RISK ENGINE",
    "## PAPER PORTFOLIO",
    "## ERRORS",
    "## WARNINGS",
    "## TESTS",
    "## OVERALL STATUS",
    "## NEXT ACTION",
    "END RESULT",
]


class DiagnosticTests(unittest.TestCase):
    def test_run_without_opend_does_not_crash(self):
        doc = run_diagnostic("127.0.0.1", 11111, True)
        self.assertIn(doc["overall"], {"FAIL", "PARTIAL", "PASS"})
        self.assertEqual(doc["opend"]["connection"], "NOT CONNECTED")
        self.assertNotEqual(doc["qqq"].get("source"), "LIVE QUOTE")
        self.assertTrue(doc["v22_untouched"])
        self.assertFalse(doc["live_orders"])
        self.assertFalse(doc["credentials_used"])
        self.assertIn("NOT CONNECTED", doc["next_action"] + doc["opend"]["connection"])

    def test_txt_has_required_sections(self):
        doc = run_diagnostic("127.0.0.1", 11111, True)
        txt = render_txt(doc)
        for sec in REQUIRED_SECTIONS:
            self.assertIn(sec, txt)
        self.assertIn("connection_test:", txt)
        self.assertIn("quote_test:", txt)
        self.assertIn("chain_test:", txt)
        self.assertIn("option_quote_test:", txt)
        self.assertIn("surface_test:", txt)
        self.assertIn("state_test:", txt)
        self.assertIn("paper_portfolio_test:", txt)

    def test_cli_writes_file_exit_zero(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "local_run_result.txt"
            rc = main(["--diagnostic", "--futu-test", "--out", str(out)])
            self.assertEqual(rc, 0)
            self.assertTrue(out.exists())
            body = out.read_text(encoding="utf-8")
            self.assertIn("FUTU V2.3 LOCAL RUN RESULT", body)
            self.assertTrue(out.with_suffix(".json").exists())

    def test_missing_live_not_filled_with_quarter_iv(self):
        doc = run_diagnostic("127.0.0.1", 11111, True)
        surf = doc.get("surface") or {}
        if not surf.get("available"):
            self.assertTrue(surf.get("iv") in (None, False) or surf.get("iv_source") in (None, "UNAVAILABLE"))
        q = doc.get("qqq") or {}
        if q.get("source") != "LIVE QUOTE":
            self.assertIsNone(q.get("last"))


if __name__ == "__main__":
    unittest.main()
