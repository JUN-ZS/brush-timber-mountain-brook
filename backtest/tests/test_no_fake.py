import unittest

from backtest.classify import classify_error, next_action
from backtest.futu_adapter import MockAdapter, UnavailableAdapter, load_futu, make_adapter
from backtest.selector import select_structure
from backtest.types import Check, finite, unavailable_quote
from backtest.types import Quote


class NoFakeLiveTests(unittest.TestCase):
    def test_finite_does_not_turn_missing_into_zero(self):
        self.assertIsNone(finite(None))
        self.assertIsNone(finite(float("nan")))
        self.assertIsNone(finite("N/A"))
        self.assertIsNone(finite(""))
        self.assertEqual(finite(0.0), 0.0)
        self.assertEqual(finite("0.25"), 0.25)

    def test_unavailable_quote_is_not_live(self):
        q = unavailable_quote("US.QQQ", "no opend")
        self.assertEqual(q.source, "UNAVAILABLE")
        self.assertIsNone(q.last)
        self.assertIsNone(q.bid)
        self.assertIsNone(q.ask)

    def test_unavailable_adapter_never_reports_live(self):
        a = UnavailableAdapter(reason="futu-api missing")
        self.assertEqual(a.connect().status, "FAIL")
        self.assertEqual(a.connect().issue_class, "ENVIRONMENT")
        self.assertEqual(a.get_qqq_quote().source, "UNAVAILABLE")
        self.assertEqual(a.get_vix_quote().source, "UNAVAILABLE")
        chain = a.get_qqq_option_chain()
        self.assertEqual(chain["source"], "UNAVAILABLE")
        self.assertEqual(chain["contract_count"], 0)
        self.assertEqual(a.get_option_quote("US.X").source, "UNAVAILABLE")
        self.assertIsNone(a.get_option_quote("US.X").iv)

    def test_mock_is_synthetic_not_live(self):
        a = MockAdapter()
        q = a.get_qqq_quote()
        self.assertEqual(q.source, "SYNTHETIC")
        self.assertNotEqual(q.source, "LIVE QUOTE")
        self.assertEqual(a.get_qqq_option_chain()["source"], "SYNTHETIC")

    def test_selector_refuses_non_live(self):
        a = MockAdapter()
        chain = a.get_qqq_option_chain()
        out = select_structure(chain["contracts"], spot=500.0, regime="UNSTABLE")
        self.assertEqual(out["status"], "NOT_AVAILABLE")

    def test_selector_refuses_without_spot(self):
        out = select_structure([], spot=None)
        self.assertEqual(out["status"], "NOT_AVAILABLE")

    def test_classify_connection_refused(self):
        self.assertEqual(classify_error("ConnectionRefusedError: 127.0.0.1:11111"), "ENVIRONMENT")
        self.assertEqual(classify_error("No module named 'futu'"), "ENVIRONMENT")
        self.assertEqual(classify_error("no permission for US option", connected=True), "PERMISSION")
        self.assertEqual(classify_error("TypeError: bad", connected=False), "CODE")

    def test_next_action_sdk(self):
        txt = next_action({"sdk": Check("sdk", "FAIL", "missing", "ENVIRONMENT"), "environment": Check("environment", "PASS", "ok")})
        self.assertIn("pip install futu-api", txt)

    def test_next_action_connection(self):
        txt = next_action(
            {
                "environment": Check("environment", "PASS", "ok"),
                "sdk": Check("sdk", "PASS", "ok"),
                "connection": Check("connection", "FAIL", "refused", "ENVIRONMENT"),
            }
        )
        self.assertIn("NOT CONNECTED", txt)
        self.assertIn("local environment", txt.lower())

    def test_make_adapter_without_sdk(self):
        futu, _ = load_futu()
        if futu is not None:
            self.skipTest("futu installed in this environment")
        a = make_adapter()
        self.assertEqual(a.get_qqq_quote().source, "UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
