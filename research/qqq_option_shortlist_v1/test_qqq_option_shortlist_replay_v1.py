#!/usr/bin/env python3
import sys
import types
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
# Pure-unit tests do not need to fetch the historical options source.
fake_audit = types.ModuleType("full_history_qqq_quote_audit")
fake_audit.base = types.SimpleNamespace(standard_strike_grid=lambda strike: True)
fake_source = types.ModuleType("qqq_far_call_quote_replay")
fake_source.iter_qqq_chain_days = lambda paths: iter(())
sys.modules.setdefault("full_history_qqq_quote_audit", fake_audit)
sys.modules.setdefault("qqq_far_call_quote_replay", fake_source)
import qqq_option_shortlist_replay_v1 as study


def quote(contract_id, right, expiry, strike, delta, bid, ask, day="2025-10-01", bid_size=20, ask_size=20):
    return {"contract_id": contract_id, "symbol": "QQQ", "type": right,
            "date": day, "expiration": expiry, "strike": strike, "delta": delta,
            "bid": bid, "ask": ask, "bid_size": bid_size, "ask_size": ask_size,
            "volume": 100, "open_interest": 500}


class ShortlistTests(unittest.TestCase):
    def test_standard_identity_rejects_wrong_right_and_encoded_strike(self):
        good = quote("QQQ251114C00500000", "C", "2025-11-14", 500, .50, 4.8, 5.0)
        self.assertTrue(study.standard_identity(good, "C", "2025-10-01"))
        self.assertFalse(study.standard_identity(good, "P", "2025-10-01"))
        self.assertFalse(study.standard_identity(dict(good, strike=501), "C", "2025-10-01"))
        self.assertFalse(study.standard_identity(dict(good, contract_id="QQQ1251114C00500000"), "C", "2025-10-01"))

    def test_buy_call_vertical_and_same_expiry_put_hedge_selected(self):
        rows = [
            quote("QQQ251114C00500000", "C", "2025-11-14", 500, .50, 4.8, 5.0),
            quote("QQQ251114C00550000", "C", "2025-11-14", 550, .10, 1.0, 1.2),
            quote("QQQ251114P00450000", "P", "2025-11-14", 450, -.10, 1.0, 1.1),
            quote("QQQ251114P00480000", "P", "2025-11-14", 480, -.30, 4.0, 4.2),
        ]
        calls = study.choose_call_vertical(rows, "2025-10-01", 520)
        self.assertIsNotNone(calls)
        self.assertEqual(calls["expiry"], "2025-11-14")
        specs, statuses = study.build_candidates(rows, "2025-10-01", 520)
        self.assertEqual(statuses["CALL_DEBIT_50D_10D"], "SELECTED")
        self.assertEqual(statuses["CALL_DEBIT_PLUS_LONG_PUT_10D"], "SELECTED")
        self.assertEqual(len(specs["CALL_DEBIT_PLUS_LONG_PUT_10D"]["legs"]), 3)
        self.assertEqual(specs["CALL_DEBIT_PLUS_LONG_PUT_10D"]["legs"][-1]["right"], "P")
        self.assertIn("PUT_SHORT_HEAVY_1x5", specs)
        self.assertIn("PUT_LONG_HEAVY_5x1", specs)

    def test_entry_and_exit_use_correct_quote_sides_and_costs(self):
        legs = [
            {"id":"LC", "right":"C", "strike":100, "side":"buy", "qty":1},
            {"id":"SC", "right":"C", "strike":110, "side":"sell", "qty":1},
        ]
        qmap = {
            "LC": {"bid":1.5,"ask":1.7,"bid_size":10,"ask_size":10},
            "SC": {"bid":.4,"ask":.6,"bid_size":10,"ask_size":10},
        }
        opened, count, status = study.cashflow(legs, qmap, True, .05, .65)
        self.assertEqual(status,"OK")
        self.assertEqual(count,2)
        self.assertAlmostEqual(opened, -141.30, places=2)
        closed, _, status = study.cashflow(legs, qmap, False, .05, .65)
        self.assertEqual(status,"OK")
        self.assertAlmostEqual(closed, 78.70, places=2)
        self.assertAlmostEqual(opened+closed, -62.60, places=2)

    def test_exit_blocks_insufficient_ask_size_for_short_leg(self):
        legs = [{"id":"SC","right":"C","strike":110,"side":"sell","qty":5}]
        qmap = {"SC":{"bid":1.0,"ask":1.1,"bid_size":10,"ask_size":4}}
        result, _, reason = study.cashflow(legs, qmap, False, .05, .65)
        self.assertIsNone(result)
        self.assertIn("SIZE", reason)

    def test_terminal_risk_checks_strike_knots_and_zero_spot(self):
        legs = [
            {"side":"buy","right":"P","strike":110,"qty":1},
            {"side":"sell","right":"P","strike":100,"qty":5},
        ]
        risk = study.terminal_risk(legs, 400.0)
        self.assertEqual(risk["terminal_pnl_at_zero_usd"], -38600.0)
        self.assertEqual(risk["terminal_worst_loss_usd"], 38600.0)
        self.assertIn(100.0, [x["spot"] for x in risk["terminal_pnl_knots"]])


if __name__ == "__main__":
    unittest.main(verbosity=2)
