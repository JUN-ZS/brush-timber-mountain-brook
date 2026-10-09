"""Offline checks for the full-history QQQ option quote audit."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import full_history_qqq_quote_audit as audit

class FullHistoryAuditTests(unittest.TestCase):
    def test_vix_regime_labels(self):
        self.assertEqual(audit.vix_bucket(14.99),"LOW_LT15")
        self.assertEqual(audit.vix_bucket(15),"NORMAL_15_25")
        self.assertEqual(audit.vix_bucket(25),"ELEVATED_25_35")
        self.assertEqual(audit.vix_bucket(35),"HIGH_GTE35")
        self.assertEqual(audit.vix_bucket(None),"UNKNOWN")

    def test_numeric_summary(self):
        result=audit.summarize_numbers([1,2,3,4,5])
        self.assertEqual(result["n"],5)
        self.assertEqual(result["median"],3)
        self.assertEqual(result["mean"],3)
        self.assertEqual(result["p90"],4)

    def test_spread_metrics(self):
        self.assertAlmostEqual(audit.spread_pct_mid(1.0,1.2),18.1818181818,places=6)
        self.assertIsNone(audit.spread_pct_mid(1.2,1.0))
        self.assertIsNone(audit.spread_pct_mid(0,0.1))

    def test_model_half_spread_matches_preserved_proxy_formula(self):
        self.assertAlmostEqual(audit.model_half_spread_fraction(82.69), 0.078352, places=6)
        self.assertAlmostEqual(audit.model_half_spread_fraction(12.42), 0.025, places=6)
        self.assertAlmostEqual(audit.model_half_spread_fraction(1000), 0.1, places=6)
        self.assertIsNone(audit.model_half_spread_fraction(None))

    def test_annual_file_manifest(self):
        self.assertEqual([x["year"] for x in audit.ANNUAL_FILES],list(range(2018,2026)))
        self.assertTrue(all(len(x["sha"])==40 and x["bytes"]>0 for x in audit.ANNUAL_FILES))
        self.assertEqual(audit.START_DATE,"2018-03-01")
        self.assertEqual(audit.END_DATE,"2025-12-31")

if __name__=="__main__":unittest.main(verbosity=2)
