#!/usr/bin/env python3
"""Offline tests for QQQ LONG CALL / SPY SHORT PUT equal-premium replay."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qqq_call_spy_put_equal_premium_replay_v1 as replay


def row(symbol, expiry, strike, delta, bid, ask, day="2024-01-02",
        bid_size=50, ask_size=50, option_type="put"):
    yymmdd = expiry[2:4] + expiry[5:7] + expiry[8:10]
    strike_code = f"{int(round(strike * 1000)):08d}"
    right = "C" if option_type.lower() in ("call", "c") else "P"
    return {"contract_id": f"{symbol}{yymmdd}{right}{strike_code}", "symbol": symbol,
            "expiration": expiry, "strike": strike, "type": option_type,
            "bid": bid, "ask": ask, "bid_size": bid_size, "ask_size": ask_size,
            "volume": 20, "open_interest": 100, "date": day, "delta": delta,
            "implied_volatility": 0.25}


class EqualPremiumReplayTests(unittest.TestCase):
    def test_standard_option_identity_checks_right_symbol_expiry_and_strike(self):
        q = row("QQQ", "2024-02-16", 400, 0.25, 4.0, 4.2, option_type="call")
        s = row("SPY", "2024-02-16", 480, -0.25, 5.0, 5.2, option_type="put")
        self.assertTrue(replay.standard_call_identity(q, "QQQ"))
        self.assertTrue(replay.standard_put_identity(s, "SPY"))
        self.assertFalse(replay.standard_call_identity(dict(q, symbol="SPY"), "QQQ"))
        self.assertFalse(replay.standard_call_identity(dict(q, strike=401), "QQQ"))
        self.assertFalse(replay.standard_call_identity(dict(q, type="put"), "QQQ"))
        self.assertFalse(replay.standard_put_identity(dict(s, contract_id=s["contract_id"].replace("P", "C")), "SPY"))

    def test_equal_premium_picker_uses_whole_contracts_and_total_cap(self):
        picked = replay.choose_equal_premium_quantities(4.0, 5.0, 9, 50, 50)
        self.assertEqual((picked["long_qqq_qty"], picked["short_spy_qty"]), (5, 4))
        self.assertAlmostEqual(picked["qqq_call_premium_debit_usd"], 2000.0)
        self.assertAlmostEqual(picked["spy_put_premium_credit_usd"], 2000.0)
        self.assertAlmostEqual(picked["premium_mismatch_usd"], 0.0)
        self.assertAlmostEqual(picked["premium_match_pct"], 100.0)
        self.assertLessEqual(picked["long_qqq_qty"] + picked["short_spy_qty"], 9)

    def test_equal_premium_picker_respects_displayed_size(self):
        picked = replay.choose_equal_premium_quantities(4.0, 5.0, 9, 2, 1)
        self.assertEqual((picked["long_qqq_qty"], picked["short_spy_qty"]), (1, 1))
        self.assertIsNone(replay.choose_equal_premium_quantities(4.0, 5.0, 1, 2, 2))
        self.assertIsNone(replay.choose_equal_premium_quantities(0.0, 5.0, 9, 2, 2))

    def test_entry_and_exit_use_correct_quote_sides_and_depth(self):
        q = row("QQQ", "2024-02-16", 400, 0.25, 4.0, 4.2, option_type="call", ask_size=5, bid_size=5)
        s = row("SPY", "2024-02-16", 480, -0.25, 5.0, 5.2, option_type="put", bid_size=4, ask_size=4)
        self.assertEqual(replay.entry_quotes_valid(q, s, 5, 4), (True, "OK"))
        self.assertEqual(replay.exit_quotes_valid(q, s, 5, 4), (True, "OK"))
        self.assertEqual(replay.entry_quotes_valid(dict(q, ask_size=4), s, 5, 4)[1], "QQQ_CALL_ASK_SIZE_INSUFFICIENT")
        self.assertEqual(replay.exit_quotes_valid(q, dict(s, ask_size=3), 5, 4)[1], "SPY_PUT_ASK_SIZE_INSUFFICIENT")

    def test_five_calls_four_puts_pnl_and_costs_reconcile(self):
        episode = {"long_qqq_qty": 5, "short_spy_qty": 4, "qqq_entry_ask": 3.0, "spy_entry_bid": 2.0}
        no_cost = replay.episode_pnl(episode, 4.0, 1.0, 0.0, 0.0)
        self.assertEqual(no_cost["qqq_long_gross_pnl_usd"], 500.0)
        self.assertEqual(no_cost["spy_short_gross_pnl_usd"], 400.0)
        self.assertEqual(no_cost["gross_pnl_usd"], 900.0)
        base = replay.episode_pnl(episode, 4.0, 1.0, 0.05, 0.65)
        self.assertAlmostEqual(base["cost_usd"], 101.7, places=6)
        self.assertAlmostEqual(base["net_pnl_usd"], 798.3, places=6)

    def test_pair_requires_common_expiry_and_chooses_call_put_rights(self):
        day, expiry = "2024-01-02", "2024-02-16"
        qrows = [row("QQQ", expiry, 400, 0.24, 4.0, 4.2, day, option_type="call"),
                 row("QQQ", expiry, 405, 0.35, 5.0, 5.2, day, option_type="call"),
                 row("QQQ", expiry, 400, -0.25, 4.0, 4.2, day, option_type="put")]
        srows = [row("SPY", expiry, 480, -0.26, 5.0, 5.2, day, option_type="put"),
                 row("SPY", "2024-02-23", 475, -0.25, 5.0, 5.2, day, option_type="put")]
        pair = replay.choose_pair(qrows, srows, day, 400, 480)
        self.assertIsNotNone(pair)
        self.assertEqual(pair["expiry"], expiry)
        self.assertEqual(pair["qqq_contract_id"], qrows[0]["contract_id"])
        self.assertEqual(pair["spy_contract_id"], srows[0]["contract_id"])
        self.assertIsNone(replay.choose_pair(qrows[:1], [srows[1]], day, 400, 480))

    def test_underlying_rows_are_filtered_by_ticker(self):
        dates = ["2024-01-02", "2024-01-02", "2024-01-03", "2024-01-04"]
        symbols = ["QQQ", "SPY", "QQQ", "SPY"]
        closes = [400.0, 480.0, None, 500.0]
        self.assertEqual(replay.spot_rows_to_map(dates, symbols, closes, "QQQ"), {"2024-01-02": 400.0})
        self.assertEqual(replay.spot_rows_to_map(dates, symbols, closes, "SPY"), {"2024-01-02": 480.0, "2024-01-04": 500.0})

    def test_mark_extremes_accept_none_initial_values(self):
        episode = {"max_favorable_mark_pnl_usd": None, "max_adverse_mark_pnl_usd": None}
        replay.update_mark_extremes(episode, -125.0)
        replay.update_mark_extremes(episode, 40.0)
        replay.update_mark_extremes(episode, -200.0)
        self.assertEqual(episode["max_favorable_mark_pnl_usd"], 40.0)
        self.assertEqual(episode["max_adverse_mark_pnl_usd"], -200.0)

    def test_wilson_resolved_only_denominator(self):
        low, high = replay.wilson95(8, 10)
        self.assertLess(low, 80.0)
        self.assertGreater(high, 80.0)
        summary = replay.policy_summary("HOLD_5_SESSIONS", [
            {"episode_id": 1, "policy": "HOLD_5_SESSIONS", "status": "RESOLVED",
             "net_pnl_usd": 10.0, "qqq_long_gross_pnl_usd": 12.0, "spy_short_gross_pnl_usd": -2.0},
            {"episode_id": 2, "policy": "HOLD_5_SESSIONS", "status": "UNRESOLVED_SOURCE_END"},
        ])
        self.assertEqual(summary["resolved"], 1)
        self.assertEqual(summary["unresolved"], 1)
        self.assertEqual(summary["win_rate_pct"], 100.0)
        self.assertEqual(summary["resolved_coverage_pct"], 50.0)

    def test_expiry_grid_uses_call_and_put_intrinsic_payoffs(self):
        entries = [{"qqq_spot_entry": 400.0, "spy_spot_entry": 480.0,
                    "qqq_strike": 410.0, "spy_strike": 470.0,
                    "qqq_entry_ask": 3.0, "spy_entry_bid": 2.0,
                    "long_qqq_qty": 2, "short_spy_qty": 3}]
        zero = replay.build_shock_grid(entries, 0.0, 0.0)
        base = replay.build_shock_grid(entries, 0.05, 0.65)
        zero_flat = next(r for r in zero if r["qqq_pct_move"] == 0 and r["spy_pct_move"] == 0)
        base_flat = next(r for r in base if r["qqq_pct_move"] == 0 and r["spy_pct_move"] == 0)
        self.assertEqual(len(zero), 196)
        self.assertAlmostEqual(zero_flat["mean_expiry_scenario_pnl_usd"], 0.0, places=2)
        self.assertAlmostEqual(base_flat["mean_expiry_scenario_pnl_usd"], -28.25, places=2)

    def test_fixed_ratio_sensitivity_respects_total_contract_cap(self):
        trades = [
            {"policy": "HOLD_5_SESSIONS", "status": "RESOLVED",
             "long_qqq_qty": 5, "short_spy_qty": 4,
             "qqq_long_gross_pnl_usd": 500.0, "spy_short_gross_pnl_usd": 400.0},
            {"policy": "HOLD_5_SESSIONS", "status": "UNRESOLVED_SOURCE_END"},
        ]
        rows = replay.summarize_sizing_sensitivity(trades, 5, 0.05, 0.65)
        self.assertEqual(len(rows), 4 * 10)
        picked = next(r for r in rows if r["policy"] == "HOLD_5_SESSIONS"
                      and r["long_qqq_contracts"] == 4 and r["short_spy_contracts"] == 1)
        self.assertEqual(picked["total_contracts"], 5)
        self.assertEqual((picked["resolved_n"], picked["unresolved_n"]), (1, 1))


if __name__ == "__main__":
    unittest.main(verbosity=2)
