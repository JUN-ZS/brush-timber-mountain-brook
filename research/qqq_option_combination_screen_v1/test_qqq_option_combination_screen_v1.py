#!/usr/bin/env python3
import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("qqq_option_combination_screen_v1.py")
SPEC = importlib.util.spec_from_file_location("screen", MODULE_PATH)
screen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(screen)


class CombinationScreenTests(unittest.TestCase):
    def test_put_debit_entry_is_net_cash_outflow(self):
        q = {"long": {"ask": 2.00}, "short": {"bid": 0.80}}
        self.assertAlmostEqual(screen.entry_cashflow("PUT_DEBIT", q, 1, 0.05, 0.65), -131.30)

    def test_call_credit_entry_is_net_cash_inflow_after_costs(self):
        q = {"short": {"bid": 1.20}, "wing": {"ask": 0.50}}
        self.assertAlmostEqual(screen.entry_cashflow("CALL_CREDIT", q, 1, 0.05, 0.65), 58.70)

    def test_exit_cashflow_charges_adverse_friction(self):
        q = {"long": {"bid": 1.20}, "short": {"ask": 1.80}}
        self.assertAlmostEqual(screen.exit_cashflow("PUT_DEBIT", q, 1, 0.05, 0.65), -71.30)

    def test_call_risk_uses_width_minus_credit_not_received_credit(self):
        nav = 100_000
        q = {"short": {"bid": 1.50}, "wing": {"ask": 0.50}}
        candidate = {"width": 5.0}
        qty, unit_loss = screen.size_call_credit(nav, q, candidate, 0.05, 0.65)
        self.assertAlmostEqual(unit_loss, 422.60)
        self.assertLessEqual(qty * unit_loss, nav * screen.CALL_MAX_LOSS_BUDGET)

    def test_stress_friction_never_increases_call_capacity(self):
        q = {"short": {"bid": 1.50}, "wing": {"ask": 0.50}}
        candidate = {"width": 5.0}
        base_qty, _ = screen.size_call_credit(100_000, q, candidate, 0.05, 0.65)
        stress_qty, _ = screen.size_call_credit(100_000, q, candidate, 0.10, 0.65)
        self.assertLessEqual(stress_qty, base_qty)

    def test_vertical_mid_marks_have_correct_sign(self):
        put = {"long": {"mid": 2.00}, "short": {"mid": 0.70}}
        call = {"wing": {"mid": 0.20}, "short": {"mid": 1.00}}
        self.assertAlmostEqual(screen.mark_value("PUT_DEBIT", put, 2), 260.0)
        self.assertAlmostEqual(screen.mark_value("CALL_CREDIT", call, 2), -160.0)

    def test_put_selection_obeys_vertical_geometry(self):
        import pandas as pd
        dt = pd.Timestamp("2024-01-02")
        expiry = pd.Timestamp("2024-02-02")
        chain = pd.DataFrame([
            {"date":dt,"expiration":expiry,"contract_id":"P100","type":"PUT","strike":100.0,"bid":1.0,"ask":1.1,"mark":1.05,"delta":-0.25,"volume":100.0},
            {"date":dt,"expiration":expiry,"contract_id":"P95","type":"PUT","strike":95.0,"bid":0.3,"ask":0.4,"mark":0.35,"delta":-0.10,"volume":100.0},
        ])
        selected = screen.select_vertical_for_expiry(chain, 105.0, "PUT_DEBIT")
        self.assertIsNotNone(selected)
        self.assertGreater(selected["long_strike"], selected["short_strike"])
        self.assertEqual(selected["expiry"], expiry)

    def test_crossed_quote_is_rejected_and_locked_quote_is_allowed(self):
        self.assertFalse(screen.good_quote({"bid": 1.0, "ask": 0.9}))
        self.assertTrue(screen.good_quote({"bid": 1.0, "ask": 1.0}))
        self.assertTrue(screen.good_quote({"bid": 0.0, "ask": 0.01}))


if __name__ == "__main__":
    unittest.main(verbosity=2)
