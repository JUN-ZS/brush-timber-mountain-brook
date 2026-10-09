from __future__ import annotations

import unittest

from qqq_hybrid_current_capacity_v2 import build_capacity_report, option_spread_capacity
from qqq_hybrid_vxx_short_call_put_strategy_v1 import quote_vxx_put_spread


def trend_fixture():
    return {
        "not_opra": True,
        "current_sizing_contract": {
            "qqq_core_pct": "EXTERNAL_INPUT", "vxx_short_pct": "EXTERNAL_INPUT",
            "qqq_call_contracts": "EXTERNAL_INPUT", "vxx_call_contracts": "EXTERNAL_INPUT",
        },
        "backtest_result": {"final_nav": 298267.22, "cagr": 0.13699, "maxdd_daily_mtm": -0.23021},
    }


def strategy_fixture():
    return {
        "research_id": "QQQ_HYBRID_VXX_SHORT_CALL_PUT_V1",
        "not_opra": True,
        "variants": {"DUAL_CALL_PUT": {"final_nav": 101000.0, "cagr": 0.01}},
    }


class CurrentCapacityTests(unittest.TestCase):
    def test_call_spread_contracts_use_max_loss_not_credit(self):
        got = option_spread_capacity(100000, 2.0, {
            "short_strike": 21, "long_strike": 24, "credit": 0.24,
            "expiry": "2026-11-20", "dte": 42, "short_delta": 0.35,
        }, "call")
        self.assertEqual(got["target_contracts"], 7)
        self.assertAlmostEqual(got["max_loss_per_spread"], 276.0)
        self.assertLessEqual(got["max_loss_at_target"], 2000.0)

    def test_put_spread_ordering_and_risk(self):
        got = option_spread_capacity(100000, 1.0, {
            "short_strike": 21, "long_strike": 18, "credit": 0.24,
            "expiry": "2026-11-20", "dte": 42, "short_delta": -0.35,
        }, "put")
        self.assertEqual(got["target_contracts"], 3)
        self.assertAlmostEqual(got["max_loss_per_spread"], 276.0)
        self.assertLessEqual(got["max_loss_at_target"], 1000.0)

    def test_budget_smaller_than_one_max_loss_returns_zero_contracts(self):
        got = option_spread_capacity(10000, 2.0, {
            "short_strike": 21, "long_strike": 24, "credit": 0.24,
            "expiry": "2026-11-20", "dte": 42, "short_delta": 0.35,
        }, "call")
        self.assertEqual(got["target_contracts"], 0)  # $200 budget < $276 max loss

    def test_invalid_candidate_stays_pending(self):
        got = option_spread_capacity(100000, 2.0, {
            "short_strike": 21, "long_strike": 24, "credit": 0.24,
            "dte": 42, "short_delta": 0.35,
        }, "call")
        self.assertEqual(got["status"], "PENDING")
        self.assertIsNone(got["target_contracts"])

    def test_hold_blocks_add_but_still_trims_over_cap(self):
        current = {
            "nav": 100000, "qqq_price": 750, "vxx_price": 17,
            "current_sizing": {
                "qqq_core_notional_pct": 42, "vxx_short_notional_pct": 18,
                "qqq_call_max_loss_pct": 1.2, "vxx_call_max_loss_pct": 1,
                "vxx_put_max_loss_pct": 1,
            },
            "holdings": {
                "qqq_shares": 1000, "vxx_shares": 2058,
                "qqq_call_spreads": 0, "vxx_call_spreads": 0, "vxx_put_spreads": 0,
            },
            "candidates": {
                "qqq_call": {"short_strike": 799, "long_strike": 810, "credit": 0.76,
                    "expiry": "2026-11-20", "dte": 42, "short_delta": 0.15},
                "vxx_call": {"short_strike": 21, "long_strike": 24, "credit": 0.24,
                    "expiry": "2026-11-20", "dte": 42, "short_delta": 0.35},
                "vxx_put": {"short_strike": 18, "long_strike": 15, "credit": 0.24,
                    "expiry": "2026-11-20", "dte": 42, "short_delta": -0.35},
            },
            "market_state": {
                "label": "WEAKENING/HOLD",
                "allow_new": {
                    "qqq_core": False, "vxx_short": False, "qqq_far_call": False,
                    "vxx_call": False, "vxx_put": False,
                },
            },
        }
        report = build_capacity_report(trend_fixture(), strategy_fixture(), current)
        self.assertEqual(report["current_vs_target"]["vxx_call"]["max_buy"], 0)
        self.assertEqual(report["current_vs_target"]["vxx_put"]["max_buy"], 0)
        self.assertEqual(report["current_vs_target"]["vxx_short"]["status"], "OVER_CAP_TRIM")
        self.assertEqual(report["current_vs_target"]["vxx_short"]["max_sell"], 1000)
        self.assertFalse(report["boundary"]["historical_percentages_promoted_to_current_sizing"])

    def test_put_quote_never_fabricates_nonpositive_credit(self):
        result = quote_vxx_put_spread(17.0, 25.0, 30.0 / 365.0)
        if result is not None:
            self.assertGreater(result["credit"], 0)
            self.assertLess(result["credit"], result["width"])
            self.assertLess(result["long_k"], result["short_k"])


if __name__ == "__main__":
    unittest.main()
