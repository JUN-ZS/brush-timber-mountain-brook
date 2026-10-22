#!/usr/bin/env python3
"""Offline contract tests for the QQQ LONG / SPY SHORT paired replay."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qqq_spy_put_equal_premium_replay_v1 as replay


def row(symbol, expiry, strike, delta, bid, ask, day="2024-01-02",
        bid_size=50, ask_size=50, option_type="put"):
    yymmdd = expiry[2:4] + expiry[5:7] + expiry[8:10]
    strike_code = f"{int(round(strike * 1000)):08d}"
    return {"contract_id": f"{symbol}{yymmdd}P{strike_code}", "symbol": symbol,
            "expiration": expiry, "strike": strike, "type": option_type,
            "bid": bid, "ask": ask, "bid_size": bid_size, "ask_size": ask_size,
            "volume": 20, "open_interest": 100, "date": day, "delta": delta,
            "implied_volatility": 0.25}


class CrossPutReplayTests(unittest.TestCase):
    def test_underlying_rows_are_filtered_by_ticker(self):
        dates = ["2024-01-02", "2024-01-02", "2024-01-03", "2024-01-04"]
        symbols = ["QQQ", "SPY", "QQQ", "SPY"]
        closes = [400.0, 480.0, None, 500.0]
        self.assertEqual(replay.spot_rows_to_map(dates, symbols, closes, "QQQ"), {"2024-01-02": 400.0})
        self.assertEqual(replay.spot_rows_to_map(dates, symbols, closes, "SPY"), {"2024-01-02": 480.0, "2024-01-04": 500.0})
    def test_contract_identity_checks_symbol_right_expiry_and_strike(self):
        q = row("QQQ", "2024-02-16", 400, -0.25, 4.0, 4.2)
        s = row("SPY", "2024-02-16", 480, -0.25, 5.0, 5.2)
        self.assertTrue(replay.standard_put_identity(q, "QQQ"))
        self.assertTrue(replay.standard_put_identity(s, "SPY"))
        self.assertFalse(replay.standard_put_identity(dict(q, symbol="SPY"), "QQQ"))
        self.assertFalse(replay.standard_put_identity(dict(q, strike=401), "QQQ"))
        self.assertFalse(replay.standard_put_identity(dict(q, type="call"), "QQQ"))

    def test_entry_and_exit_side_depth_are_directional(self):
        q = row("QQQ", "2024-02-16", 400, -0.25, 4.0, 4.2, ask_size=4, bid_size=4)
        s = row("SPY", "2024-02-16", 480, -0.25, 5.0, 5.2, bid_size=5, ask_size=5)
        self.assertEqual(replay.entry_quotes_valid(q, s, 4, 5), (True, "OK"))
        self.assertEqual(replay.exit_quotes_valid(q, s, 4, 5), (True, "OK"))
        self.assertEqual(replay.entry_quotes_valid(dict(q, ask_size=3), s, 4, 5)[1], "QQQ_LONG_ASK_SIZE_INSUFFICIENT")
        self.assertEqual(replay.exit_quotes_valid(q, dict(s, ask_size=4), 4, 5)[1], "SPY_SHORT_ASK_SIZE_INSUFFICIENT")

    def test_equal_premium_contract_matching_is_integer_bounded_and_depth_aware(self):
        exact = replay.choose_equal_premium_quantities(2.0, 3.0, 9, 6, 6)
        self.assertIsNotNone(exact)
        self.assertEqual((exact["long_qqq_qty"], exact["short_spy_qty"]), (3, 2))
        self.assertEqual(exact["qqq_long_premium_debit_usd"], 600.0)
        self.assertEqual(exact["spy_short_premium_credit_usd"], 600.0)
        self.assertEqual(exact["premium_mismatch_usd"], 0.0)
        self.assertEqual(exact["premium_match_pct"], 100.0)
        depth_limited = replay.choose_equal_premium_quantities(2.0, 3.0, 9, 2, 2)
        self.assertLessEqual(depth_limited["long_qqq_qty"], 2)
        self.assertLessEqual(depth_limited["short_spy_qty"], 2)
        self.assertLessEqual(depth_limited["long_qqq_qty"] + depth_limited["short_spy_qty"], 9)
        self.assertIsNone(replay.choose_equal_premium_quantities(2.0, 3.0, 1, 6, 6))

    def test_per_cohort_premium_match_summary_records_selected_ratios(self):
        entries = [
            {"long_qqq_qty": 3, "short_spy_qty": 2, "qqq_long_premium_debit_usd": 600,
             "spy_short_premium_credit_usd": 600, "premium_mismatch_usd": 0, "premium_match_pct": 100},
            {"long_qqq_qty": 4, "short_spy_qty": 3, "qqq_long_premium_debit_usd": 800,
             "spy_short_premium_credit_usd": 810, "premium_mismatch_usd": 10, "premium_match_pct": 98.765432},
        ]
        summary = replay.summarize_premium_matching(entries)
        self.assertEqual(summary["cohort_n"], 2)
        self.assertEqual(summary["mean_qqq_premium_debit_usd"], 700.0)
        self.assertEqual(summary["mean_spy_premium_credit_usd"], 705.0)
        self.assertEqual(summary["mean_abs_mismatch_usd"], 5.0)
        self.assertIn("3:2", summary["ratio_counts"])
        self.assertIn("4:3", summary["ratio_counts"])

    def test_four_by_five_pnl_and_costs_reconcile(self):
        episode = {"long_qqq_qty": 4, "short_spy_qty": 5, "qqq_entry_ask": 3.0, "spy_entry_bid": 2.0}
        no_cost = replay.episode_pnl(episode, 4.0, 1.0, 0.0, 0.0)
        self.assertEqual(no_cost["qqq_long_gross_pnl_usd"], 400.0)
        self.assertEqual(no_cost["spy_short_gross_pnl_usd"], 500.0)
        self.assertEqual(no_cost["gross_pnl_usd"], 900.0)
        base = replay.episode_pnl(episode, 4.0, 1.0, 0.05, 0.65)
        self.assertAlmostEqual(base["cost_usd"], 101.7, places=6)
        self.assertAlmostEqual(base["net_pnl_usd"], 798.3, places=6)

    def test_pair_requires_common_expiry_and_uses_delta_target(self):
        day, expiry = "2024-01-02", "2024-02-16"
        qrows = [row("QQQ", expiry, 400, -0.24, 4.0, 4.2, day),
                 row("QQQ", expiry, 405, -0.35, 5.0, 5.2, day),
                 row("QQQ", "2024-02-23", 400, -0.25, 4.0, 4.2, day)]
        srows = [row("SPY", expiry, 480, -0.26, 5.0, 5.2, day),
                 row("SPY", "2024-02-23", 475, -0.25, 5.0, 5.2, day)]
        pair = replay.choose_pair(qrows, srows, day, 400, 480)
        self.assertIsNotNone(pair)
        self.assertEqual(pair["expiry"], expiry)
        self.assertEqual(pair["qqq_contract_id"], qrows[0]["contract_id"])
        self.assertEqual(pair["spy_contract_id"], srows[0]["contract_id"])
        self.assertIsNone(replay.choose_pair(qrows[:1], [srows[1]], day, 400, 480))

    def test_mark_extremes_accept_none_initial_values_and_track_later_marks(self):
        episode = {"max_favorable_mark_pnl_usd": None, "max_adverse_mark_pnl_usd": None}
        replay.update_mark_extremes(episode, -125.0)
        self.assertEqual(episode["max_favorable_mark_pnl_usd"], -125.0)
        self.assertEqual(episode["max_adverse_mark_pnl_usd"], -125.0)
        replay.update_mark_extremes(episode, 40.0)
        self.assertEqual(episode["max_favorable_mark_pnl_usd"], 40.0)
        self.assertEqual(episode["max_adverse_mark_pnl_usd"], -125.0)
        replay.update_mark_extremes(episode, -200.0)
        self.assertEqual(episode["max_favorable_mark_pnl_usd"], 40.0)
        self.assertEqual(episode["max_adverse_mark_pnl_usd"], -200.0)

    def test_wilson_and_resolved_only_win_rate_denominator(self):
        low, high = replay.wilson95(8, 10)
        self.assertIsNotNone(low)
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

    def test_shock_grid_is_196_explicit_hypothetical_scenarios(self):
        entries = [{"episode_id": 1, "qqq_spot_entry": 400.0, "spy_spot_entry": 480.0,
                    "qqq_strike": 390.0, "spy_strike": 460.0,
                    "qqq_entry_ask": 4.0, "spy_entry_bid": 3.0}]
        grid = replay.build_shock_grid(entries, 4, 5, 0.0, 0.0)
        diagonal = [r for r in grid if r["same_pct_move_diagonal"]]
        self.assertEqual(len(grid), 196)
        self.assertEqual(len(diagonal), 14)
        self.assertTrue(all("HYPOTHETICAL" in r["classification"] for r in grid))


    def test_expiry_shock_grid_charges_entry_cost_once_not_round_trip(self):
        entries = [{"episode_id": 1, "qqq_spot_entry": 400.0, "spy_spot_entry": 480.0,
                    "qqq_strike": 390.0, "spy_strike": 460.0,
                    "qqq_entry_ask": 4.0, "spy_entry_bid": 3.0}]
        zero_cost = replay.build_shock_grid(entries, 4, 5, 0.0, 0.0)
        base_cost = replay.build_shock_grid(entries, 4, 5, 0.05, 0.65)
        zero_flat = next(r for r in zero_cost if r["qqq_pct_move"] == 0 and r["spy_pct_move"] == 0)
        base_flat = next(r for r in base_cost if r["qqq_pct_move"] == 0 and r["spy_pct_move"] == 0)
        # Both puts expire OTM at unchanged spots: credit less entry costs only.
        self.assertAlmostEqual(zero_flat["mean_expiry_scenario_pnl_usd"], -100.0, places=2)
        self.assertAlmostEqual(base_flat["mean_expiry_scenario_pnl_usd"], -150.85, places=2)
        self.assertAlmostEqual(
            zero_flat["mean_expiry_scenario_pnl_usd"] - base_flat["mean_expiry_scenario_pnl_usd"],
            50.85, places=2)

    def test_sizing_sensitivity_scales_leg_pnl_and_keeps_unresolved_separate(self):
        trades = [
            {"policy": "HOLD_5_SESSIONS", "status": "RESOLVED",
             "long_qqq_qty": 4, "short_spy_qty": 5,
             "qqq_long_gross_pnl_usd": 400.0, "spy_short_gross_pnl_usd": 500.0},
            {"policy": "HOLD_5_SESSIONS", "status": "UNRESOLVED_SOURCE_END"},
        ]
        rows = replay.summarize_sizing_sensitivity(trades, 4, 5, 0.05, 0.65)
        one_one = next(r for r in rows if r["policy"] == "HOLD_5_SESSIONS"
                       and r["long_qqq_contracts"] == 1 and r["short_spy_contracts"] == 1)
        four_five = next(r for r in rows if r["policy"] == "HOLD_5_SESSIONS"
                         and r["long_qqq_contracts"] == 4 and r["short_spy_contracts"] == 5)
        self.assertEqual(len(rows), 4 * 4 * 5)
        self.assertEqual((one_one["resolved_n"], one_one["unresolved_n"]), (1, 1))
        self.assertAlmostEqual(one_one["expectancy_net_usd"], 177.4, places=2)
        self.assertAlmostEqual(four_five["expectancy_net_usd"], 798.3, places=2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
