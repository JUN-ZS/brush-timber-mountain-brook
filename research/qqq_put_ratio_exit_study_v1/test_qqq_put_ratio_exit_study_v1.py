import importlib.util
from pathlib import Path
from datetime import date
import unittest

MODULE = Path(__file__).with_name('qqq_put_ratio_exit_study_v1.py')
spec = importlib.util.spec_from_file_location('ratio_study', MODULE)
S = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(S)

SIGNAL = '2024-01-02'
EXPIRY = '2024-02-16'
DAY0 = '2024-01-03'
DAY1 = '2024-01-04'
DAY2 = '2024-01-05'


def put(strike, delta, bid, ask, *, expiry=EXPIRY, day=SIGNAL, bid_size=10, ask_size=10, root='QQQ'):
    code = f'{int(round(strike * 1000)):08d}'
    ymd = expiry[2:4] + expiry[5:7] + expiry[8:10]
    ident = f'{root}{ymd}P{code}'
    return {'contract_id': ident, 'symbol': 'QQQ', 'expiration': expiry,
            'strike': strike, 'type': 'put', 'bid': bid, 'ask': ask,
            'bid_size': bid_size, 'ask_size': ask_size, 'open_interest': 1000,
            'volume': 100, 'date': day, 'delta': delta}


def trade_fixture():
    long = put(480, -.30, 4.80, 5.00, day=DAY0)
    short = put(450, -.10, 4.90, 5.10, day=DAY0)
    return {'trade_id': 1, 'signal_date': SIGNAL, 'entry_date': DAY0, 'expiry': EXPIRY,
            'long_id': long['contract_id'], 'short_id': short['contract_id'],
            'long_strike': 480.0, 'short_strike': 450.0, 'width': 30.0,
            'long_abs_delta': .30, 'short_abs_delta': .10, 'signal_dte': 45,
            'spot_entry': 500.0, 'vix_entry': 20.0, 'entry_quotes': {'long': long, 'short': short}, 'path': []}


def step(day, dte, *, short_bid=4.9, short_ask=5.1, short_bid_size=10, short_ask_size=10,
         long_bid=4.8, long_ask=5.0, long_bid_size=10, long_ask_size=10, spot=500.0):
    return {'date': day, 'dte': dte, 'spot': spot, 'vix': 20.0,
            'short': put(450, -.10, short_bid, short_ask, day=day, bid_size=short_bid_size, ask_size=short_ask_size),
            'long': put(480, -.30, long_bid, long_ask, day=day, bid_size=long_bid_size, ask_size=long_ask_size)}


class PutRatioExitStudyTests(unittest.TestCase):
    def test_standard_occ_identity_rejects_adjusted_or_wrong_strike(self):
        good = put(480, -.3, 4.8, 5.0)
        self.assertTrue(S.standard_put_identity(good))
        self.assertFalse(S.standard_put_identity({**good, 'contract_id': good['contract_id'].replace('QQQ', 'QQQ1')}))
        self.assertFalse(S.standard_put_identity({**good, 'strike': 479.0}))

    def test_selection_uses_actual_same_expiry_pair_and_delta_ranges(self):
        rows = [put(480, -.30, 4.8, 5.0), put(450, -.10, 4.9, 5.1),
                put(440, -.08, 4.2, 4.4), put(470, -.40, 7.0, 7.2, expiry='2024-02-23'),
                put(480, -.30, 4.8, 5.0, root='QQQ1')]
        selected = S.choose_ratio_put(rows, SIGNAL, {EXPIRY}, lambda _: True)
        self.assertEqual(selected['status'], 'PAIR_SELECTED')
        self.assertEqual((selected['long_strike'], selected['short_strike'], selected['expiry']), (480, 450, EXPIRY))

    def test_invalid_zero_bid_does_not_create_entry_pair(self):
        rows = [put(480, -.30, 4.8, 5.0), put(450, -.10, 0.0, .1)]
        self.assertNotEqual(S.choose_ratio_put(rows, SIGNAL, {EXPIRY}, lambda _: True)['status'], 'PAIR_SELECTED')

    def test_entry_cashflow_charges_all_six_contracts_and_costs(self):
        expected = 100 * (5 * (4.90 - .05) - (5.00 + .05)) - 6 * .65
        self.assertAlmostEqual(S.entry_cashflow(trade_fixture(), .05, .65), expected)

    def test_terminal_tail_loss_is_measured_not_called_max_loss_cap(self):
        risk = S.terminal_risk(trade_fixture(), 466.10, 100000)
        self.assertAlmostEqual(risk['terminal_pnl_if_qqq_zero_usd'], 466.10 + 100 * (480 - 5 * 450))
        self.assertAlmostEqual(risk['max_terminal_profit_at_short_strike_usd'], 466.10 + 3000)
        self.assertEqual(risk['whole_ratio_units_under_1pct_nav_tail_budget'], 0)
        self.assertGreater(risk['terminal_tail_loss_pct_reference_nav'], 100)

    def test_zero_bid_long_put_mark_is_not_executable_sale(self):
        state = {'cash': 466.10, 'n_short': 5, 'n_long': 1}
        s = step(DAY1, 43, short_bid=1.5, short_ask=2.2, long_bid=0.0)
        pnl, status = S.mark_pnl(state, s, .05, .65)
        self.assertIsNotNone(pnl)
        self.assertEqual(status, 'OK')
        self.assertFalse(S.sell_long_if_executable(state, s, .05, .65)[0])
        self.assertEqual(state['n_long'], 1)

    def test_short_mark_and_close_use_ask_even_if_bid_missing(self):
        state = {'cash': 1000., 'n_short': 5, 'n_long': 0, 'contracts_closed_short': 0}
        s = step(DAY1, 43, short_bid=None, short_ask=1.0, short_ask_size=5)
        pnl, status = S.mark_pnl(state, s, 0., 0.)
        self.assertIsNotNone(pnl)
        self.assertEqual(status, 'OK')
        self.assertTrue(S.close_short_qty(state, s, 5, 0., 0.)[0])
        self.assertEqual(state['n_short'], 0)

    def test_close_requires_sufficient_displayed_ask_size(self):
        state = {'cash': 1000., 'n_short': 5, 'n_long': 1, 'contracts_closed_short': 0}
        before = dict(state)
        ok, status = S.close_short_qty(state, step(DAY1, 43, short_ask_size=4), 5, .05, .65)
        self.assertFalse(ok)
        self.assertEqual(status, 'SHORT_EXIT_ASK_SIZE_INSUFFICIENT')
        self.assertEqual(state, before)

    def test_trim_four_shorts_leaves_one_by_one_vertical(self):
        state = {'cash': 2000., 'n_short': 5, 'n_long': 1, 'contracts_closed_short': 0}
        self.assertTrue(S.close_short_qty(state, step(DAY1, 43), 4, .05, .65)[0])
        self.assertEqual((state['n_short'], state['n_long']), (1, 1))

    def test_policy_matrix_compares_usd_pct_fast_win_and_day20(self):
        names = {x['name'] for x in S.policy_list()}
        for name in ('TP_USD_1000_CLOSE_SHORT_RISK', 'TP_25PCT_MAX_TERMINAL_GAIN',
                     'FAST_1000_WITHIN_5D_TRIM_4_SHORTS', 'DAY20_NONPOSITIVE_CLOSE_SHORT_RISK',
                     'DAY20_NONPOSITIVE_TRIM_4_SHORTS', 'SL_USD_1000_CLOSE_SHORT_RISK'):
            self.assertIn(name, names)

    def test_fast_one_thousand_signals_eod_then_executes_next_session(self):
        trade = trade_fixture()
        trade['entry_quotes']['short']['bid'] = 5.0
        trade['entry_quotes']['long']['ask'] = 5.0
        trade['path'] = [step(DAY0, 44, short_bid=5.0, short_ask=5.1, long_bid=4.8, long_ask=5.0),
                         step(DAY1, 43, short_bid=.05, short_ask=.10, long_bid=0.0, long_ask=.05),
                         step(DAY2, 42, short_bid=.05, short_ask=.10, long_bid=.1, long_ask=.15),
                         step(EXPIRY, 0, short_bid=.0, short_ask=.01, long_bid=0.0, long_ask=.01, spot=500.0)]
        policy = next(x for x in S.policy_list() if x['kind'] == 'fast_trim')
        result = S.simulate_policy(trade, policy, .05, .65)
        trim = next(a for a in result['actions'] if a['action'] == 'TRIM_SHORTS' and a.get('status') == 'OK')
        self.assertEqual(trim['signal_date'], DAY1)
        self.assertEqual(trim['date'], DAY2)
        self.assertEqual(trim['quantity'], 4)
        self.assertEqual(result['policy_rule_signal_date'], DAY1)
        self.assertEqual(result['policy_rule_signal_holding_sessions'], 1)
        self.assertEqual(result['exit_action_holding_sessions'], 2)
        self.assertEqual(result['signal_to_action_delay_sessions'], 1)
        self.assertEqual(result['resolved_holding_sessions'], 3)
        self.assertAlmostEqual(result['short_risk_exposure_session_equivalents'], 3.2)
        summary = S.summarize_policy([result])
        self.assertEqual(summary['policy_rule_triggered_trade_count'], 1)
        self.assertEqual(summary['policy_rule_trigger_rate_pct'], 100.0)
        self.assertEqual(summary['policy_rule_trigger_age_sessions_distribution']['median'], 1.0)
        self.assertEqual(summary['signal_to_first_action_delay_sessions_distribution']['median'], 1.0)
        # Summary publishes this descriptive metric rounded to four decimals.
        self.assertAlmostEqual(
            summary['net_pnl_per_short_risk_equivalent_session_usd'],
            result['final_pnl_usd'] / 3.2,
            delta=0.0001
        )

    def test_dte7_fallback_is_counted_separately_from_policy_trigger(self):
        trade = trade_fixture()
        trade['path'] = [
            step('2024-02-08', 8, short_bid=4.0, short_ask=4.2, long_bid=4.9, long_ask=5.1),
            step('2024-02-09', 7, short_bid=4.0, short_ask=4.2, long_bid=4.9, long_ask=5.1),
            step('2024-02-12', 4, short_bid=4.0, short_ask=4.2, long_bid=4.9, long_ask=5.1),
            step(EXPIRY, 0, short_bid=.01, short_ask=.02, long_bid=.1, long_ask=.2, spot=500.0)
        ]
        policy = next(x for x in S.policy_list() if x['kind'] == 'dte7')
        result = S.simulate_policy(trade, policy, .05, .65)
        self.assertEqual(result['first_signal_reason'], 'DTE7_MANDATORY_CLOSE_SHORT_RISK')
        self.assertEqual(result['first_signal_holding_sessions'], 1)
        self.assertEqual(result['exit_action_holding_sessions'], 2)
        self.assertEqual(result['signal_to_action_delay_sessions'], 1)
        self.assertEqual(result['resolved_holding_sessions'], 2)
        summary = S.summarize_policy([result])
        self.assertEqual(summary['policy_rule_triggered_trade_count'], 0)
        self.assertEqual(summary['policy_rule_trigger_rate_pct'], 0.0)
        self.assertEqual(summary['mandatory_dte7_fallback_trade_count'], 1)
        self.assertIn('DTE7 fallback', S.render_markdown({
            'status': 'TEST', 'generation': {}, 'policy_summaries_base_cost': [summary],
            'risk_summary_base_cost': {}, 'event_study': {}, 'limitations': [], 'performance_gate': 'BLOCKED'
        }))

    def test_fast_trim_is_one_shot(self):
        trade = trade_fixture()
        trade['entry_quotes']['short']['bid'] = 5.0
        trade['entry_quotes']['long']['ask'] = 5.0
        trade['path'] = [step(DAY0, 44, short_bid=5.0, short_ask=5.1, long_bid=4.8, long_ask=5.0),
                         step(DAY1, 43, short_bid=.05, short_ask=.10, long_bid=0.0, long_ask=.05),
                         step(DAY2, 42, short_bid=.05, short_ask=.10, long_bid=.1, long_ask=.15),
                         step('2024-01-08', 39, short_bid=.05, short_ask=.10, long_bid=.2, long_ask=.25),
                         step(EXPIRY, 0, short_bid=.01, short_ask=.02, long_bid=0.0, long_ask=.01, spot=500.0)]
        policy = next(x for x in S.policy_list() if x['kind'] == 'fast_trim')
        result = S.simulate_policy(trade, policy, .05, .65)
        trims = [a for a in result['actions'] if a['action'] == 'TRIM_SHORTS' and a.get('status') == 'OK']
        self.assertEqual(len(trims), 1)
        self.assertEqual(trims[0]['quantity'], 4)

    def test_day20_nonpositive_rule_signals_on_age_20_and_executes_next_observation(self):
        trade = trade_fixture()
        # Valid observed market sessions; skip weekends and the 2024-01-15 market holiday.
        session_dates = [
            '2024-01-03', '2024-01-04', '2024-01-05',
            '2024-01-08', '2024-01-09', '2024-01-10', '2024-01-11', '2024-01-12',
            '2024-01-16', '2024-01-17', '2024-01-18', '2024-01-19',
            '2024-01-22', '2024-01-23', '2024-01-24', '2024-01-25', '2024-01-26',
            '2024-01-29', '2024-01-30', '2024-01-31', '2024-02-01', '2024-02-02'
        ]
        self.assertEqual(len(session_dates), 22)
        trade['path'] = [
            step(day, (date.fromisoformat(EXPIRY) - date.fromisoformat(day)).days,
                 short_bid=4.9, short_ask=5.1, long_bid=4.8, long_ask=5.0, spot=500.)
            for day in session_dates
        ]
        policy = next(x for x in S.policy_list() if x['kind'] == 'day20_close')
        result = S.simulate_policy(trade, policy, .05, .65)
        self.assertEqual(result['policy_rule_signal_date'], session_dates[20])
        self.assertEqual(result['policy_rule_signal_holding_sessions'], 20)
        self.assertEqual(result['exit_signal_date'], session_dates[20])
        self.assertEqual(result['exit_action_date'], session_dates[21])
        self.assertEqual(result['exit_action_holding_sessions'], 21)
        self.assertEqual(result['signal_to_action_delay_sessions'], 1)
        self.assertEqual(result['final_status'], 'CLOSED_AT_OBSERVED_SIDE_QUOTES')
        summary = S.summarize_policy([result])
        self.assertEqual(summary['policy_rule_triggered_trade_count'], 1)
        self.assertEqual(summary['mandatory_dte7_fallback_trade_count'], 0)

    def test_report_has_after_cost_metrics_and_keeps_deployment_blocked(self):
        trade = trade_fixture()
        trade['path'] = [step(DAY0, 44), step(DAY1, 43), step(EXPIRY, 0, spot=500.)]
        report, summaries, per_trade, events = S.build_report([trade], {'opened_trade_episodes': 1}, {'ok': True})
        self.assertEqual(report['status'], 'DEVELOPMENT_DIAGNOSTIC_NOT_LIVE_APPROVAL')
        self.assertTrue(report['performance_gate'].startswith('BLOCKED_FOR_DEPLOYMENT'))
        self.assertGreaterEqual(len(summaries), 12)
        self.assertTrue(per_trade)
        self.assertIn('critical_timing_caveat', events)
        # Win rate is an observed percentage with the resolved-trade denominator, not a fraction mislabeled as a percent.
        for summary in summaries:
            self.assertIn("win_rate_pct", summary)
            self.assertEqual(
                summary["winning_trades"] + summary["losing_trades"] + summary["flat_trades"],
                summary["resolved_trades"],
            )
            if summary["resolved_trades"]:
                expected_pct = round(100 * summary["winning_trades"] / summary["resolved_trades"], 2)
                self.assertEqual(summary["win_rate_pct"], expected_pct)
                self.assertLessEqual(summary["win_rate_wilson95_nominal_low_pct"], expected_pct)
                self.assertGreaterEqual(summary["win_rate_wilson95_nominal_high_pct"], expected_pct)
            else:
                self.assertIsNone(summary["win_rate_pct"])
                self.assertIsNone(summary["win_rate_wilson95_nominal_low_pct"])
                self.assertIsNone(summary["win_rate_wilson95_nominal_high_pct"])
        lo, hi = S._wilson95_pct(59, 62)
        self.assertLess(lo, round(100 * 59 / 62, 2))
        self.assertGreater(hi, round(100 * 59 / 62, 2))


if __name__ == '__main__':
    unittest.main(verbosity=2)
