import importlib.util
import unittest
from datetime import date, timedelta
from pathlib import Path

SCRIPT = Path(__file__).with_name("qqq_public_price_proxy.py")
SPEC = importlib.util.spec_from_file_location("qqq_public_price_proxy", SCRIPT)
M = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(M)


def rows(n=55):
    start = date(2026, 1, 2)
    out = []
    px = 100.0
    for i in range(n):
        px *= 1.004 if i % 4 else 0.997
        out.append({
            "date": (start + timedelta(days=i)).isoformat(),
            "raw_close": px,
            "adj_close": px,
            "vix": 20.0,
            "price_source": "fixture",
        })
    return out


class PublicPriceProxyTests(unittest.TestCase):
    def test_vix_and_rv_buckets_have_known_boundaries(self):
        self.assertEqual(M.rv_label(0.1499), "RV20_LT15")
        self.assertEqual(M.rv_label(0.15), "RV20_15_25")
        self.assertEqual(M.rv_label(0.25), "RV20_25_35")
        self.assertEqual(M.rv_label(0.35), "RV20_GTE35")
        self.assertEqual(M.vix_label(14.9), "VIX_LT15")
        self.assertEqual(M.vix_label(15.0), "VIX_15_25")
        self.assertEqual(M.vix_label(25.0), "VIX_25_35")
        self.assertEqual(M.vix_label(35.0), "VIX_GTE35")

    def test_probability_sample_is_censored_at_window_end(self):
        rs = rows(55)
        rv = M.rv_buckets(rs)
        begin = date.fromisoformat(rs[0]["date"])
        end = date.fromisoformat(rs[30]["date"])
        out = M.price_stats(rs, rv, begin, end, "bounded")
        row = next(x for x in out if x["state"] == "ALL" and x["horizon_sessions"] == 5)
        # Starting rows 0 through 25 have a complete five-session outcome by row 30.
        self.assertEqual(row["n"], 26)

    def test_post_source_extension_is_distinct_and_price_only(self):
        rs = rows(80)
        rv = M.rv_buckets(rs)
        start = date.fromisoformat(rs[55]["date"])
        end = date.fromisoformat(rs[-1]["date"])
        out = M.price_stats(rs, rv, start, end, "external_extension")
        five = next(x for x in out if x["state"] == "ALL" and x["horizon_sessions"] == 5)
        self.assertEqual(five["n"], 20)
        self.assertIn("window", five)
        self.assertEqual(five["window"], "external_extension")

    def test_invalid_price_gap_is_not_silently_forward_filled(self):
        session = date(2026, 1, 5)
        for value in (None, "not-a-price", float("nan"), 0.0, -1.0):
            with self.subTest(value=value):
                with self.assertRaises(RuntimeError):
                    M.validate_close(value, session)
        self.assertEqual(M.validate_close("123.456789", session), 123.456789)


if __name__ == "__main__":
    unittest.main(verbosity=2)
