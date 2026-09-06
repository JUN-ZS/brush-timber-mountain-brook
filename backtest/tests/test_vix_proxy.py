import unittest

from backtest.classify import classify_error, next_action
from backtest.engines import run_state_risk
from backtest.types import Check, OptionContract, VIX_CODE
from backtest.vix_proxy import (
    iv_to_vix_units,
    qqq_atm_iv_proxy,
    resolve_vix_input,
)


def _put(code: str, strike: float, dte: int, iv: float) -> OptionContract:
    return OptionContract(
        code=code,
        underlying="US.QQQ",
        right="PUT",
        strike=strike,
        expiry="2099-01-01",
        dte=dte,
        lot_size=100,
        bid=1.0,
        ask=1.1,
        last=1.05,
        iv=iv,
        delta=-0.5,
        gamma=None,
        theta=None,
        vega=None,
        oi=None,
        volume=None,
        source="LIVE QUOTE",
        field_sources={"iv": "LIVE QUOTE", "bid": "LIVE QUOTE"},
    )


class VixProxyTests(unittest.TestCase):
    def test_vix_code_is_futu_index(self):
        self.assertEqual(VIX_CODE, "US..VIX")

    def test_iv_to_vix_units(self):
        self.assertAlmostEqual(iv_to_vix_units(0.18019), 18.019)
        self.assertAlmostEqual(iv_to_vix_units(18.0), 18.0)
        with self.assertRaises(ValueError):
            iv_to_vix_units(0.0)

    def test_qqq_atm_iv_prefers_near_30d(self):
        rows = [
            _put("US.QQQ_W", 500.0, 2, 0.10),
            _put("US.QQQ_M", 500.0, 33, 0.18),
            _put("US.QQQ_F", 500.0, 60, 0.22),
        ]
        proxy = qqq_atm_iv_proxy(rows, spot=500.0)
        self.assertIsNotNone(proxy)
        assert proxy is not None
        self.assertEqual(proxy["method"], "QQQ_ATM_IV")
        self.assertEqual(proxy["source"], "DERIVED")
        self.assertEqual(proxy["code"], "US.QQQ_M")
        self.assertAlmostEqual(proxy["level"], 18.0)
        self.assertNotEqual(proxy["source"], "LIVE QUOTE")

    def test_resolve_prefers_live_index(self):
        out = resolve_vix_input(
            live_vix=16.5,
            live_vix_source="LIVE QUOTE",
            live_vix_closes=[15, 15, 15, 15, 15, 15.2, 16.5],
            option_rows=[_put("US.QQQ_M", 500.0, 30, 0.25)],
            spot=500.0,
            live_qqq_closes=None,
            adapter=None,
        )
        self.assertTrue(out["index_quote_ok"])
        self.assertEqual(out["method"], "US_INDEX_VIX")
        self.assertEqual(out["source"], "LIVE QUOTE")
        self.assertAlmostEqual(out["value"], 16.5)

    def test_resolve_uses_atm_iv_when_index_missing(self):
        out = resolve_vix_input(
            live_vix=None,
            live_vix_source="UNAVAILABLE",
            live_vix_closes=None,
            option_rows=[_put("US.QQQ_M", 719.0, 33, 0.18019)],
            spot=718.96,
            live_qqq_closes=None,
            adapter=None,
        )
        self.assertFalse(out["index_quote_ok"])
        self.assertEqual(out["method"], "QQQ_ATM_IV")
        self.assertEqual(out["source"], "DERIVED")
        self.assertAlmostEqual(out["value"], 18.019)

    def test_classify_us_index_unsupported_is_permission(self):
        self.assertEqual(classify_error("暂不支持美股指数", connected=True), "PERMISSION")

    def test_next_action_with_proxy_pass(self):
        checks = {
            "environment": Check("environment", "PASS", "ok"),
            "sdk": Check("sdk", "PASS", "ok"),
            "connection": Check("connection", "PASS", "ok"),
            "quote": Check("quote", "PASS", "ok"),
            "chain": Check("chain", "PASS", "ok"),
            "option_quote": Check("option_quote", "PASS", "ok"),
            "surface": Check("surface", "PASS", "ok"),
            "vix": Check("vix", "FAIL", "暂不支持美股指数", "PERMISSION"),
            "vix_proxy": Check("vix_proxy", "PASS", "QQQ_ATM_IV=18.02 source=DERIVED"),
        }
        msg = next_action(checks)
        self.assertIn("DERIVED", msg)
        self.assertIn("QQQ", msg)
        self.assertNotIn("enable Futu US index quote permission for this account, then re-run", msg)

    def test_state_engine_accepts_proxy_metadata(self):
        prices = [100 + i * 0.05 for i in range(80)]
        out = run_state_risk(
            live_qqq_closes=prices,
            live_vix=18.019,
            live_vix_source="DERIVED",
            live_qqq_source="LIVE QUOTE",
            vix_method="QQQ_ATM_IV",
            vix_prev5_override=18.3,
            vix_reason="proxy",
        )
        self.assertEqual(out["state"]["vix_method"], "QQQ_ATM_IV")
        self.assertEqual(out["state"]["vix_source"], "DERIVED")
        self.assertEqual(out["state"]["vix_reason"], "proxy")
        self.assertAlmostEqual(out["state"]["vix"], 18.019)


if __name__ == "__main__":
    unittest.main()
