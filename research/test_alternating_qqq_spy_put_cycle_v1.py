import unittest
from alternating_qqq_spy_put_cycle_v1 import (
    choose_contract_pair, direction_for, trade_pnl, premium_cashflow_usd,
    LONG_QTY, SHORT_QTY,
)


class AlternatingPutCycleTests(unittest.TestCase):
    def test_weekly_directions_alternate_even_if_signal_skipped(self):
        self.assertEqual([direction_for("alternate", i) for i in range(6)], ["A", "B", "A", "B", "A", "B"])

    def test_fixed_direction_controls(self):
        self.assertEqual(direction_for("fixed_A", 7), "A")
        self.assertEqual(direction_for("fixed_B", 8), "B")

    def test_pair_selector_requires_exact_zero_premium_and_delta_band(self):
        d, exp = "2022-01-03", "2022-01-24"
        short_rows = [
            {"contract_id":"SPY220124P00450000","symbol":"SPY","expiration":exp,"strike":450.0,
             "type":"put","bid":4.0,"ask":4.1,"bid_size":10,"ask_size":10,"open_interest":100,
             "date":d,"delta":-0.25},
            {"contract_id":"SPY220124P00440000","symbol":"SPY","expiration":exp,"strike":440.0,
             "type":"put","bid":2.0,"ask":2.1,"bid_size":10,"ask_size":10,"open_interest":100,
             "date":d,"delta":-0.15},
        ]
        long_rows = [
            {"contract_id":"QQQ220124P00350000","symbol":"QQQ","expiration":exp,"strike":350.0,
             "type":"put","bid":23.9,"ask":24.0,"bid_size":5,"ask_size":5,"open_interest":50,
             "date":d,"delta":-0.65},
            {"contract_id":"QQQ220124P00360000","symbol":"QQQ","expiration":exp,"strike":360.0,
             "type":"put","bid":27.0,"ask":28.0,"bid_size":5,"ask_size":5,"open_interest":50,
             "date":d,"delta":-0.85},
        ]
        pair = choose_contract_pair(short_rows, long_rows, "SPY", "QQQ", d, 470.0, 370.0)
        self.assertIsNotNone(pair)
        self.assertEqual(pair["short_contract_id"], "SPY220124P00450000")
        self.assertEqual(pair["long_contract_id"], "QQQ220124P00350000")
        self.assertEqual(pair["long_premium_error_signal"], 0.0)
        self.assertEqual(pair["long_premium_match_pct_signal"], 100.0)
        self.assertEqual(pair["opening_premium_cashflow_signal_usd"], 0.0)
        self.assertAlmostEqual(pair["long_abs_delta"], 0.65)

    def test_near_match_is_rejected_not_called_zero(self):
        d, exp = "2022-01-03", "2022-01-24"
        short_rows = [
            {"contract_id":"SPY220124P00450000","symbol":"SPY","expiration":exp,"strike":450.0,
             "type":"put","bid":4.0,"ask":4.1,"bid_size":10,"ask_size":10,"open_interest":100,
             "date":d,"delta":-0.25},
        ]
        long_rows = [
            {"contract_id":"QQQ220124P00350000","symbol":"QQQ","expiration":exp,"strike":350.0,
             "type":"put","bid":23.89,"ask":23.99,"bid_size":5,"ask_size":5,"open_interest":50,
             "date":d,"delta":-0.65},
        ]
        self.assertIsNone(choose_contract_pair(short_rows, long_rows, "SPY", "QQQ", d, 470.0, 370.0))

    def test_reversed_direction_also_requires_exact_zero_premium(self):
        d, exp = "2022-01-03", "2022-01-24"
        short_rows = [
            {"contract_id":"QQQ220124P00350000","symbol":"QQQ","expiration":exp,"strike":350.0,
             "type":"put","bid":4.0,"ask":4.1,"bid_size":10,"ask_size":10,"open_interest":100,
             "date":d,"delta":-0.25},
        ]
        long_rows = [
            {"contract_id":"SPY220124P00450000","symbol":"SPY","expiration":exp,"strike":450.0,
             "type":"put","bid":23.9,"ask":24.0,"bid_size":5,"ask_size":5,"open_interest":50,
             "date":d,"delta":-0.65},
        ]
        pair = choose_contract_pair(short_rows, long_rows, "QQQ", "SPY", d, 370.0, 470.0)
        self.assertIsNotNone(pair)
        self.assertEqual(pair["short_symbol"], "QQQ")
        self.assertEqual(pair["long_symbol"], "SPY")
        self.assertEqual(premium_cashflow_usd(24.0, 4.0), 0.0)

    def test_premium_cashflow_is_zero_only_when_exactly_equal(self):
        self.assertEqual(premium_cashflow_usd(24.0, 4.0), 0.0)
        self.assertEqual(premium_cashflow_usd(23.99, 4.0), 1.0)
        self.assertEqual(premium_cashflow_usd(24.01, 4.0), -1.0)

    def test_trade_pnl_prices_long_and_short_legs_correctly(self):
        result = trade_pnl({"long_entry_ask":10.0,"short_entry_bid":2.0}, 15.0, 5.0)
        self.assertEqual(result["long_gross_pnl_usd"], 500.0)
        self.assertEqual(result["short_gross_pnl_usd"], -1800.0)
        self.assertLess(result["net_pnl_usd"], -1300.0)
        self.assertEqual((LONG_QTY, SHORT_QTY), (1, 6))


if __name__ == "__main__":
    unittest.main()
