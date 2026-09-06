import unittest

from backtest.engines import classify_state, run_state_risk, suggested_risk
from backtest.paper import empty_book
from backtest.scenario import run_scenarios
from backtest.types import OptionContract


class EngineTests(unittest.TestCase):
    def test_calm_path(self):
        prices = [100 + i * 0.05 for i in range(80)]
        st = classify_state(prices, vix=14.0, vix_prev5=14.0)
        self.assertEqual(st["regime"], "CALM")
        self.assertFalse(st["building"])

    def test_tail_vix(self):
        prices = [100 for _ in range(80)]
        st = classify_state(prices, vix=35.0)
        self.assertEqual(st["regime"], "TAIL")

    def test_risk_building_raises_put(self):
        r = suggested_risk({"regime": "CALM", "building": True})
        self.assertGreaterEqual(r["put_hedge"], 0.75)
        self.assertEqual(r["qqq_exposure"], 1.0)
        self.assertEqual(r["source"], "DERIVED")

    def test_state_from_universe_is_derived_without_live(self):
        out = run_state_risk()
        self.assertIn(out["state"]["regime"], {"CALM", "UNSTABLE", "TAIL", "RECOVERY"})
        self.assertEqual(out["state"]["source"], "DERIVED")

    def test_paper_forbids_trade_context(self):
        b = empty_book()
        self.assertEqual(b["orders"], "NONE")
        self.assertEqual(b["trade_context"], "FORBIDDEN")
        self.assertEqual(b["source"], "SIMULATED")

    def test_scenario_labels_derived(self):
        s = run_scenarios(spot=500.0, iv=0.18, iv_source="DERIVED", spot_source="DERIVED")
        self.assertEqual(s["status"], "PASS")
        self.assertTrue(s["rows"])
        shocked = [r for r in s["rows"] if r["structure"] != "QQQ_ONLY"]
        self.assertTrue(all(r["shocked_option_source"] == "DERIVED" for r in shocked))

    def test_scenario_refuses_silent_iv(self):
        s = run_scenarios(spot=500.0, iv=None, iv_source="UNAVAILABLE", spot_source="DERIVED")
        self.assertEqual(s["status"], "UNAVAILABLE")
        self.assertEqual(s["rows"], [])

    def test_live_entry_still_derived_exit(self):
        live = OptionContract(
            code="US.QQQ_P",
            underlying="US.QQQ",
            right="PUT",
            strike=475.0,
            expiry="2099-01-01",
            dte=30,
            lot_size=100,
            bid=8.0,
            ask=8.2,
            last=8.1,
            iv=0.2,
            delta=-0.25,
            gamma=None,
            theta=None,
            vega=None,
            oi=None,
            volume=None,
            source="LIVE QUOTE",
            field_sources={"bid": "LIVE QUOTE", "ask": "LIVE QUOTE"},
        )
        s = run_scenarios(spot=500.0, iv=0.2, iv_source="LIVE QUOTE", spot_source="LIVE QUOTE", live_puts=[live])
        otm = [r for r in s["rows"] if r["structure"] == "OTM5_PUT" and r["shock"] == -0.05][0]
        self.assertEqual(otm["entry_source"], "LIVE QUOTE")
        self.assertEqual(otm["shocked_option_source"], "DERIVED")


if __name__ == "__main__":
    unittest.main()
