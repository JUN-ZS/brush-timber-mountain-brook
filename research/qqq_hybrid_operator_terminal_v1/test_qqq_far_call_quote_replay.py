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
        self.assertEqual(status2, "WING_CONTRACT_ROW_MISSING")

    def test_exit_mark_invalid_quote_reason_identifies_the_bad_leg(self):
        pair = replay.choose_vertical(sample_chain(), DAY)
        pos = {"short_id": pair["short"]["contract_id"], "wing_id": pair["wing"]["contract_id"]}
        quotes = replay.quote_map(sample_chain())
        quotes[pos["short_id"]]["ask"] = None
        debit, status = replay.close_side_debit_per_share(pos, quotes, 0.0, 0.0)
        self.assertIsNone(debit)
        self.assertEqual(status, "SHORT_ASK_MISSING_OR_NONPOSITIVE")

        quotes = replay.quote_map(sample_chain())
        quotes[pos["wing_id"]]["ask"] = -1
        debit, status = replay.close_side_debit_per_share(pos, quotes, 0.0, 0.0)
        self.assertIsNone(debit)
        self.assertEqual(status, "WING_ASK_MISSING_OR_NONPOSITIVE")

    def test_exit_mark_accepts_zero_bid_as_conservative_mark_when_close_sides_are_observed(self):
        pair = replay.choose_vertical(sample_chain(), DAY)
        pos = {"short_id": pair["short"]["contract_id"], "wing_id": pair["wing"]["contract_id"]}
        quotes = replay.quote_map(sample_chain())
        # A zero short Bid is irrelevant when the short Ask is observed.
        quotes[pos["short_id"]]["bid"] = 0.0
        # A zero wing Bid is accepted as a conservative $0 exit value, not as a fill.
        quotes[pos["wing_id"]]["bid"] = 0.0
        close_debit, close_status = replay.close_side_debit_per_share(pos, quotes, 0.0, 0.0)
        self.assertIsNone(close_debit)
        self.assertEqual(close_status, "WING_BID_ZERO_NOT_EXECUTABLE")

        mark_debit, mark_status = replay.close_side_debit_per_share(
            pos, quotes, 0.0, 0.0, allow_zero_wing_bid=True
        )
        self.assertEqual(mark_status, "OK_ZERO_WING_BID_FLOOR")
        self.assertAlmostEqual(mark_debit, quotes[pos["short_id"]]["ask"])

    def test_exit_mark_ignores_missing_short_bid_but_blocks_missing_wing_bid(self):
        pair = replay.choose_vertical(sample_chain(), DAY)
        pos = {"short_id": pair["short"]["contract_id"], "wing_id": pair["wing"]["contract_id"]}
        quotes = replay.quote_map(sample_chain())
        quotes[pos["short_id"]]["bid"] = None
        debit, status = replay.close_side_debit_per_share(pos, quotes, 0.0, 0.0)
        self.assertEqual(status, "OK")
        self.assertAlmostEqual(debit, quotes[pos["short_id"]]["ask"] - quotes[pos["wing_id"]]["bid"])

        quotes = replay.quote_map(sample_chain())
        quotes[pos["wing_id"]]["bid"] = None
        debit2, status2 = replay.close_side_debit_per_share(pos, quotes, 0.0, 0.0)
        self.assertIsNone(debit2)
        self.assertEqual(status2, "WING_BID_MISSING")

    def test_exit_mark_distinguishes_inconsistent_vertical_from_bad_leg_quotes(self):
        pair = replay.choose_vertical(sample_chain(), DAY)
        pos = {"short_id": pair["short"]["contract_id"], "wing_id": pair["wing"]["contract_id"]}
        quotes = replay.quote_map(sample_chain())
        short = quotes[pos["short_id"]]
        wing = quotes[pos["wing_id"]]
        short["ask"] = 1.5
        short["bid"] = 1.4
        wing["bid"] = 1.6
        wing["ask"] = 1.7
        debit, status = replay.close_side_debit_per_share(pos, quotes, 0.0, 0.0)
        self.assertIsNone(debit)
        self.assertEqual(status, "INCONSISTENT_VERTICAL_EXIT_MARK")

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

    def test_expiry_uses_intrinsic_and_closes_open_position(self):
        state = replay.Replay(replay.BUDGET_MODES[0], 0.0, 0.0)
        spot = {"raw_close": 100.0, "adjusted_close": 100.0}
        state.process(DAY, sample_chain(day_key=DAY), spot, 18.0)
        state.process("2026-10-21", sample_chain(day_key="2026-10-21"), spot, 18.0)
        self.assertIsNotNone(state.position)
        state.position["expiry"] = "2026-10-22"
        expiry_spot = {"raw_close": 120.0, "adjusted_close": 120.0}
        state.process("2026-10-22", sample_chain(day_key="2026-10-22"), expiry_spot, 18.0)
        self.assertIsNone(state.position)
        self.assertEqual(state.counters["expiry_settlements"], 1)
        self.assertEqual(state.trades[-1]["settlement_basis"], "OBSERVED_RAW_CLOSE_ON_EXPIRY_DATE")
        self.assertAlmostEqual(state.trades[-1]["exit_intrinsic_debit_per_share"], 10.0)
        self.assertEqual(state.trades[-1]["status"], "SETTLED_INTRINSIC_PROXY_NOT_CONFIRMED_EXERCISE")

    def test_weekend_expiry_uses_tagged_last_pre_expiry_spot_fallback(self):
        state = replay.Replay(replay.BUDGET_MODES[0], 0.0, 0.0)
        spot = {"raw_close": 100.0, "adjusted_close": 100.0}
        state.process(DAY, sample_chain(day_key=DAY), spot, 18.0)
        state.process("2026-10-21", sample_chain(day_key="2026-10-21"), spot, 18.0)
        self.assertIsNotNone(state.position)
        state.position["expiry"] = "2026-10-24"  # Saturday
        friday_spot = {"raw_close": 105.0, "adjusted_close": 105.0}
        state.process("2026-10-23", sample_chain(day_key="2026-10-23"), friday_spot, 18.0)
        monday_spot = {"raw_close": 120.0, "adjusted_close": 120.0}
        state.process("2026-10-26", sample_chain(day_key="2026-10-26"), monday_spot, 18.0)
        self.assertIsNone(state.position)
        self.assertEqual(state.expiry_settlement_fallbacks, 1)
        self.assertEqual(state.trades[-1]["settlement_price_date"], "2026-10-23")
        self.assertEqual(state.trades[-1]["settlement_basis"], "FALLBACK_LAST_OBSERVED_SESSION_BEFORE_EXPIRY")
        self.assertAlmostEqual(state.trades[-1]["settlement_spot"], 105.0)
    def test_quote_side_mtm_does_not_require_displayed_size_but_entry_does(self):
        state = replay.Replay(replay.BUDGET_MODES[0], 0.0, 0.0)
        spot = {"raw_close": 100.0, "adjusted_close": 100.0}
        state.process(DAY, sample_chain(day_key=DAY), spot, 18.0)
        state.process("2026-10-21", sample_chain(day_key="2026-10-21"), spot, 18.0)
        self.assertIsNotNone(state.position)
        no_size = sample_chain(day_key="2026-10-22")
        for row in no_size:
            row["bid_size"] = 0
            row["ask_size"] = 0
        state.process("2026-10-22", no_size, spot, 18.0)
        self.assertIsNotNone(state.daily[-1]["nav_eod_marked"])
        self.assertEqual(state.daily[-1]["nav_mark_status"], "OK")
        self.assertEqual(state.exit_quote_size_missing_sessions, 1)
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


    def test_quote_spread_bins_are_diagnostic_and_explicit(self):
        self.assertEqual(replay.quote_quality_bucket(5.0, 10.0), "TIGHT_LE_10PCT_MID")
        self.assertEqual(replay.quote_quality_bucket(10.01, 25.0), "MODERATE_10_25PCT_MID")
        self.assertEqual(replay.quote_quality_bucket(25.01, 4.0), "WIDE_GT25PCT_MID")
        self.assertEqual(replay.quote_quality_bucket(None, 4.0), "UNKNOWN_QUOTE_SPREAD")

    def test_raw_spot_20_session_momentum_is_asof_and_unknown_when_incomplete(self):
        missing, label = replay.raw_spot_momentum20(103.0, [])
        self.assertIsNone(missing)
        self.assertEqual(label, "UNKNOWN_INSUFFICIENT_20_SESSION_HISTORY")
        prior = [(f"session-{i}", 100.0) for i in range(20)]
        momentum, label = replay.raw_spot_momentum20(103.0, prior)
        self.assertAlmostEqual(momentum, 0.03)
        self.assertEqual(label, "UP_GE_2PCT_20S")
        prior[-20] = ("missing-session", None)
        momentum, label = replay.raw_spot_momentum20(103.0, prior)
        self.assertIsNone(momentum)
        self.assertEqual(label, "UNKNOWN_MISSING_20_SESSION_REFERENCE")

    def _sample_attribution_trade(self):
        return {
            "scenario": "SOURCE_MAX_LOSS_0P8PCT_NAV",
            "scenario_id": "SOURCE_MAX_LOSS_0P8PCT_NAV|SLIP_PER_LEG_0.000|COMM_PER_CONTRACT_SIDE_0.00",
            "quantity": 2,
            "entry_date": "2020-01-10", "exit_date": "2020-01-20",
            "entry_gross_credit_per_share": 1.0, "entry_net_credit_ps": 0.95,
            "exit_short_ask": 1.2, "exit_wing_bid": 0.4,
            "exit_net_debit_per_share": 0.9,
            "realized_pnl_after_scenario_costs": 10.0,
            "entry_total_max_loss_scenario_usd": 800.0,
            "short_delta": 0.16, "wing_delta": 0.08,
            "exit_short_delta": 0.25, "exit_wing_delta": 0.12,
            "entry_short_spread_pct_mid": 20.0, "entry_wing_spread_pct_mid": 10.0,
            "exit_short_spread_pct_mid": 15.0, "exit_wing_spread_pct_mid": 8.0,
            "entry_regime": "NORMAL_15_25", "exit_regime": "ELEVATED_25_35",
            "entry_trend_regime": "UP_GE_2PCT_20S", "exit_trend_regime": "RANGE_ABS_LT2PCT_20S",
            "exit_reason": "PNL_OVER_MAXLOSS_GE_0P50", "holding_calendar_days": 10,
        }

    def test_trade_attribution_cash_flows_reconcile_and_measure_delta_drift(self):
        trade = replay.attribute_closed_trade(self._sample_attribution_trade())
        self.assertEqual(trade["attribution_status"], "PASS_CASH_FLOW_RECONCILIATION")
        self.assertAlmostEqual(trade["entry_gross_credit_cash_usd"], 200.0)
        self.assertAlmostEqual(trade["entry_execution_costs_usd"], 10.0)
        self.assertAlmostEqual(trade["exit_gross_debit_cash_usd"], 160.0)
        self.assertAlmostEqual(trade["exit_execution_costs_usd"], 20.0)
        self.assertAlmostEqual(trade["recomputed_net_pnl_usd"], 10.0)
        self.assertAlmostEqual(trade["pnl_reconciliation_error_usd"], 0.0)
        self.assertAlmostEqual(trade["short_delta_drift"], 0.09)
        self.assertAlmostEqual(trade["wing_delta_drift"], 0.04)
        self.assertEqual(trade["entry_year"], "2020")
        self.assertEqual(trade["entry_quote_quality_bucket"], "MODERATE_10_25PCT_MID")

    def test_expiry_trade_attribution_uses_intrinsic_debit_not_missing_quote_fallback(self):
        trade = self._sample_attribution_trade()
        trade.update({
            "quantity": 1, "entry_gross_credit_per_share": 1.0, "entry_net_credit_ps": 0.95,
            "exit_intrinsic_debit_per_share": 0.5, "exit_net_debit_per_share": 0.55,
            "realized_pnl_after_scenario_costs": 40.0,
        })
        trade.pop("exit_short_ask")
        trade.pop("exit_wing_bid")
        trade.pop("exit_short_delta")
        trade.pop("exit_wing_delta")
        attributed = replay.attribute_closed_trade(trade)
        self.assertEqual(attributed["attribution_status"], "PASS_CASH_FLOW_RECONCILIATION")
        self.assertEqual(attributed["exit_debit_basis"], "INTRINSIC_SETTLEMENT_PROXY")
        self.assertAlmostEqual(attributed["exit_gross_debit_cash_usd"], 50.0)
        self.assertAlmostEqual(attributed["exit_execution_costs_usd"], 5.0)
        self.assertIsNone(attributed["short_delta_drift"])

    def test_trade_attribution_fails_reconciliation_when_cash_flows_do_not_match(self):
        trade = self._sample_attribution_trade()
        trade["realized_pnl_after_scenario_costs"] = 9.98
        attributed = replay.attribute_closed_trade(trade)
        self.assertEqual(attributed["attribution_status"], "FAIL_CASH_FLOW_RECONCILIATION")
        self.assertGreater(abs(attributed["pnl_reconciliation_error_usd"]), 0.01)

    def test_trade_attribution_groups_by_unique_cost_scenario_and_exit_reason(self):
        base = replay.attribute_closed_trade(self._sample_attribution_trade())
        second = dict(base)
        second["scenario_id"] = "SOURCE_MAX_LOSS_0P8PCT_NAV|SLIP_PER_LEG_0.025|COMM_PER_CONTRACT_SIDE_0.00"
        second["realized_pnl_after_scenario_costs"] = -50.0
        # Keep the cash-flow components internally consistent for the loss arm.
        second["exit_net_debit_per_share"] = 1.2
        second["exit_short_ask"] = 1.5
        second["exit_wing_bid"] = 0.3
        second = replay.attribute_closed_trade(second)
        summary, rows = replay.build_trade_attribution([base, second])
        self.assertEqual(summary["closed_trade_rows"], 2)
        self.assertEqual(summary["reconciliation_pass_rows"], 2)
        self.assertEqual(len(summary["scenarios"]), 2)
        self.assertIn("PNL_OVER_MAXLOSS_GE_0P50", summary["scenarios"][base["scenario_id"]]["groups"]["exit_reason"])
        self.assertTrue(any(row["dimension"] == "entry_trend_regime" for row in rows))


    def test_zero_wing_bid_mark_can_trigger_risk_exit_but_cannot_fill_exit(self):
        state = replay.Replay(replay.BUDGET_MODES[0], 0.0, 0.0)
        spot = {"raw_close": 100.0, "adjusted_close": 100.0}
        state.process(DAY, sample_chain(day_key=DAY), spot, 18.0)
        entry_day = "2026-10-21"
        state.process(entry_day, sample_chain(day_key=entry_day), spot, 18.0)
        self.assertIsNotNone(state.position)

        stress_day = "2026-10-22"
        stressed = sample_chain(day_key=stress_day)
        quotes = replay.quote_map(stressed)
        quotes["QQQ261120C00100000"]["ask"] = 9.9
        quotes["QQQ261120C00110000"]["bid"] = 0.0
        state.process(stress_day, stressed, spot, 18.0)

        self.assertIsNotNone(state.position)
        self.assertTrue(state.pending_close)
        self.assertEqual(state.position["exit_reason"], "PNL_OVER_MAXLOSS_LE_NEG_0P55")
        self.assertEqual(state.daily[-1]["nav_mark_status"], "OK_ZERO_WING_BID_FLOOR")

    def test_dte_exit_signal_is_raised_without_chain_and_waits_for_a_later_quote(self):
        state = replay.Replay(replay.BUDGET_MODES[0], 0.0, 0.0)
        spot = {"raw_close": 100.0, "adjusted_close": 100.0}
        state.process(DAY, sample_chain(day_key=DAY), spot, 18.0)
        entry_day = "2026-10-21"
        state.process(entry_day, sample_chain(day_key=entry_day), spot, 18.0)
        self.assertIsNotNone(state.position)

        signal_day = "2026-11-13"  # Seven calendar days to the listed 2026-11-20 expiry.
        state.process(signal_day, [], spot, 18.0)
        self.assertIsNotNone(state.position)
        self.assertTrue(state.pending_close)
        self.assertEqual(state.position["exit_reason"], "DTE_LE_7")
        self.assertEqual(state.position["exit_signal_date"], signal_day)
        self.assertEqual(len(state.trades), 0)

        close_day = "2026-11-14"
        state.process(close_day, sample_chain(day_key=close_day), spot, 18.0)
        self.assertIsNone(state.position)
        self.assertEqual(state.trades[-1]["exit_date"], close_day)
        self.assertEqual(state.trades[-1]["exit_signal_date"], signal_day)
        self.assertEqual(state.trades[-1]["exit_delay_calendar_days"], 1)

    def test_close_signal_waits_for_current_quote_and_records_delay(self):
        state = replay.Replay(replay.BUDGET_MODES[0], 0.0, 0.0)
        spot = {"raw_close": 100.0, "adjusted_close": 100.0}
        state.process(DAY, sample_chain(day_key=DAY), spot, 18.0)
        entry_day = "2026-10-21"
        state.process(entry_day, sample_chain(day_key=entry_day), spot, 18.0)
        self.assertIsNotNone(state.position)

        # Mimic a previously raised exit signal. A missing chain must not fabricate an exit.
        state.pending_close = True
        state.position["exit_reason"] = "TEST_EXIT_SIGNAL"
        state.position["exit_signal_date"] = entry_day
        state.position["exit_signal_vix"] = 18.0
        state.position["exit_signal_regime"] = "NORMAL_15_25"
        state.position["exit_signal_trend_regime"] = "UNKNOWN"
        state.process("2026-10-22", [], spot, 28.0)
        self.assertIsNotNone(state.position)
        self.assertEqual(state.position["exit_quote_missing_sessions"], 1)
        self.assertEqual(state.counters["exit_delayed_missing_chain_sessions"], 1)
        self.assertEqual(len(state.trades), 0)

        # The exit uses the first later current-date quote set for the exact same contract IDs.
        state.process("2026-10-23", sample_chain(day_key="2026-10-23"), spot, 21.0)
        self.assertIsNone(state.position)
        self.assertEqual(len(state.trades), 1)
        self.assertEqual(state.trades[0]["exit_quote_missing_sessions"], 1)
        self.assertEqual(state.trades[0]["exit_signal_date"], entry_day)
        self.assertEqual(state.trades[0]["exit_delay_calendar_days"], 2)
        self.assertEqual(state.trades[0]["exit_regime"], "NORMAL_15_25")
        self.assertEqual(state.trades[0]["exit_signal_regime"], "NORMAL_15_25")

if __name__ == "__main__":
    unittest.main(verbosity=2)
