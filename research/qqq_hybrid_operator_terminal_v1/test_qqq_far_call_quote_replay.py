"""Offline tests for the listed-contract QQQ far-call quote replay."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qqq_far_call_quote_replay as replay


DAY = "2026-10-20"
EXPIRY = "2026-11-20"


def call(strike, delta, bid, ask, expiry=EXPIRY, bid_size=10, ask_size=10, day_key=DAY):
    # OCC identifier: root + YYMMDD + C + strike * 1000, zero-padded to 8 digits.
    strike_code = f"{int(round(strike * 1000)):08d}"
    return {
        "contract_id": f"QQQ261120C{strike_code}",
        "symbol": "QQQ", "expiration": expiry, "strike": strike,
        "type": "call", "bid": bid, "ask": ask,
        "bid_size": bid_size, "ask_size": ask_size,
        "volume": 100, "open_interest": 1000, "date": day_key,
        "implied_volatility": 0.30, "delta": delta,
    }


def sample_chain(day_key=DAY):
    return [
        call(100, 0.16, 5.0, 5.2, day_key=day_key),
        call(105, 0.12, 3.5, 3.7, day_key=day_key),
        call(110, 0.08, 2.0, 2.2, day_key=day_key),
        call(115, 0.04, 0.9, 1.1, day_key=day_key),
    ]


class QqqFarCallReplayTests(unittest.TestCase):
    def test_contract_id_root_requires_full_occ_shape(self):
        self.assertEqual(replay.contract_root("QQQ   261120C00100000"), "QQQ")
        self.assertEqual(replay.contract_root("O:QQQ261120C00100000"), "QQQ")
        self.assertEqual(replay.contract_root("QQQ1261120C00100000"), "QQQ1")
        self.assertIsNone(replay.contract_root("QQQ-contract-123"))

    def test_picker_uses_actual_same_expiry_listed_calls_and_source_deltas(self):
        pair = replay.choose_vertical(sample_chain(), DAY)
        self.assertEqual(pair["status"], "PAIR_SELECTED")
        self.assertEqual(pair["short"]["contract_id"], "QQQ261120C00100000")
        self.assertEqual(pair["wing"]["contract_id"], "QQQ261120C00110000")
        self.assertEqual(pair["expiry"], EXPIRY)
        self.assertEqual(pair["dte"], 31)
        self.assertAlmostEqual(pair["gross_observed_side_credit_per_share"], 2.8)
        self.assertAlmostEqual(pair["width"], 10.0)

    def test_picker_blocks_unverified_root_and_quotes_without_size(self):
        rows = sample_chain()
        for row in rows:
            row["contract_id"] = "QQQ-contract-" + str(row["strike"])
        pair = replay.choose_vertical(rows, DAY)
        self.assertNotEqual(pair["status"], "PAIR_SELECTED")
        no_size = sample_chain()
        for row in no_size:
            row["bid_size"] = 0
            row["ask_size"] = 0
        pair2 = replay.choose_vertical(no_size, DAY)
        self.assertNotEqual(pair2["status"], "PAIR_SELECTED")

    def test_credit_and_max_loss_budgets_are_not_equivalent(self):
        pair = replay.choose_vertical(sample_chain(), DAY)
        net_credit = replay.entry_net_credit_per_share(pair, 0.025, 0.0)
        self.assertAlmostEqual(net_credit, 2.75)
        n_risk, per_spread_risk = replay.pick_quantity(
            100_000, pair, replay.BUDGET_MODES[0], net_credit, 0.025, 0.0
        )
        n_credit, _ = replay.pick_quantity(
            100_000, pair, replay.BUDGET_MODES[1], net_credit, 0.025, 0.0
        )
        self.assertEqual(n_risk, 1)
        self.assertEqual(n_credit, 4)
        self.assertAlmostEqual(per_spread_risk, 730.0)

    def test_nonpositive_net_credit_cannot_be_sized(self):
        pair = replay.choose_vertical(sample_chain(), DAY)
        net_credit = replay.entry_net_credit_per_share(pair, 2.0, 0.0)
        self.assertLessEqual(net_credit, 0)
        quantity, _ = replay.pick_quantity(100_000, pair, replay.BUDGET_MODES[0],
                                           net_credit, 2.0, 0.0)
        self.assertEqual(quantity, 0)

    def test_exit_uses_short_ask_minus_wing_bid_and_exit_costs(self):
        pair = replay.choose_vertical(sample_chain(), DAY)
        pos = {"short_id": pair["short"]["contract_id"], "wing_id": pair["wing"]["contract_id"],
               "expiry": EXPIRY}
        quotes = replay.quote_map(sample_chain())
        debit, status = replay.close_side_debit_per_share(pos, quotes, 0.025, 0.65)
        self.assertEqual(status, "OK")
        self.assertAlmostEqual(debit, 3.263)
        del quotes[pos["wing_id"]]
        debit2, status2 = replay.close_side_debit_per_share(pos, quotes, 0.0, 0.0)
        self.assertIsNone(debit2)
        self.assertEqual(status2, "CONTRACT_ROW_MISSING")

    def test_missing_chain_is_not_forward_filled_for_existing_position_mark(self):
        state = replay.Replay(replay.BUDGET_MODES[0], 0.0, 0.0)
        spot = {"raw_close": 100.0, "adjusted_close": 100.0}
        state.process(DAY, sample_chain(), spot, 18.0)
        self.assertTrue(state.pending_open)
        state.process("2026-10-21", sample_chain(day_key="2026-10-21"), spot, 18.0)
        self.assertIsNotNone(state.position)
        state.process("2026-10-22", [], spot, 18.0)
        self.assertIsNone(state.daily[-1]["nav_eod_marked"])
        self.assertIn("MISSING", state.daily[-1]["nav_mark_status"])
        self.assertEqual(state.counters["missing_position_mark_sessions"], 1)
        self.assertTrue(state.position)

    def test_stale_chain_date_is_rejected_not_used_for_next_session_entry(self):
        state = replay.Replay(replay.BUDGET_MODES[0], 0.0, 0.0)
        spot = {"raw_close": 100.0, "adjusted_close": 100.0}
        state.process(DAY, sample_chain(day_key=DAY), spot, 18.0)
        self.assertTrue(state.pending_open)
        state.process("2026-10-21", sample_chain(day_key=DAY), spot, 18.0)
        self.assertIsNone(state.position)
        self.assertFalse(state.pending_open)
        self.assertEqual(state.counters["stale_or_mixed_chain_dates"], 1)
        self.assertEqual(state.counters["entry_skipped_missing_next_session_chain"], 1)

    def test_missing_signal_day_contract_skips_instead_of_reselecting_new_pair(self):
        state = replay.Replay(replay.BUDGET_MODES[0], 0.0, 0.0)
        spot = {"raw_close": 100.0, "adjusted_close": 100.0}
        state.process(DAY, sample_chain(day_key=DAY), spot, 18.0)
        next_chain = [x for x in sample_chain(day_key="2026-10-21")
                      if x["strike"] not in (100, 110)]
        state.process("2026-10-21", next_chain, spot, 18.0)
        self.assertIsNone(state.position)
        self.assertEqual(state.counters["entry_no_valid_pair"], 1)
        self.assertTrue(any(e.get("reason") == "SIGNAL_CONTRACT_MISSING_NEXT_SESSION"
                            for e in state.events))

    def test_signal_date_selection_is_pinned_for_next_session_entry(self):
        state = replay.Replay(replay.BUDGET_MODES[0], 0.0, 0.0)
        spot = {"raw_close": 100.0, "adjusted_close": 100.0}
        state.process(DAY, sample_chain(day_key=DAY), spot, 18.0)
        self.assertIsNone(state.position)
        self.assertTrue(state.pending_open)
        entry_day = "2026-10-21"
        next_chain = sample_chain(day_key=entry_day)
        # Entry-day deltas now favour 105C/115C; signal-day contract IDs must remain fixed.
        next_chain[0]["delta"] = 0.28
        next_chain[1]["delta"] = 0.16
        next_chain[2]["delta"] = 0.12
        next_chain[3]["delta"] = 0.08
        state.process(entry_day, next_chain, spot, 18.0)
        self.assertIsNotNone(state.position)
        self.assertEqual(state.position["signal_date"], DAY)
        self.assertEqual(state.position["entry_date"], entry_day)
        self.assertEqual(state.position["short_id"], "QQQ261120C00100000")
        self.assertEqual(state.position["wing_id"], "QQQ261120C00110000")
        self.assertAlmostEqual(state.position["entry_gross_credit_per_share"], 2.8)

if __name__ == "__main__":
    unittest.main(verbosity=2)
