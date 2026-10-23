#!/usr/bin/env python3
from __future__ import annotations
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import qqq_spy_put_fixed_ratio_size_gated_v1 as engine
import compare_cadence_grid_v1 as cadence


def trade(eid, policy, status, pnl="", entry="2025-01-02", exit_day="2025-01-12",
          obligation="76500", longq="1", shortq="3", signal="2025-01-01", last="2025-01-20"):
    return {
        "episode_id": str(eid), "policy": policy, "status": status, "net_pnl_usd": str(pnl),
        "entry_date": entry, "exit_date": exit_day, "last_observed_date": last,
        "spy_put_strike_assignment_obligation_usd": obligation, "long_qqq_qty": longq,
        "short_spy_qty": shortq, "signal_date": signal,
    }


class OverlapGateTests(unittest.TestCase):
    def test_legacy_default_serializes_while_any_policy_is_active(self):
        self.assertFalse(engine.entry_gate_open([{"policy": "HOLD_20_SESSIONS"}], False))
        self.assertTrue(engine.entry_gate_open([], False))

    def test_explicit_overlap_mode_allows_next_cohort_while_prior_is_active(self):
        self.assertTrue(engine.entry_gate_open([{"policy": "HOLD_20_SESSIONS"}], True))

    def test_cli_flag_is_explicit_and_opt_in(self):
        with patch.object(sys, "argv", ["replay"]):
            self.assertFalse(engine.parse_args().allow_overlapping_cohorts)
        with patch.object(sys, "argv", ["replay", "--allow-overlapping-cohorts"]):
            self.assertTrue(engine.parse_args().allow_overlapping_cohorts)


class CadenceAuditTests(unittest.TestCase):
    def test_peak_overlapping_assignment_obligation(self):
        rows = [
            trade("1", "HOLD_20_SESSIONS", "RESOLVED", 100, "2025-01-02", "2025-01-10", "50000"),
            trade("2", "HOLD_20_SESSIONS", "RESOLVED", -50, "2025-01-05", "2025-01-15", "75000"),
        ]
        count, obligation = cadence.peak_overlapping_exposure(rows)
        self.assertEqual(count, 2)
        self.assertEqual(obligation, 125000.0)

    def test_unresolved_not_zero_filled_and_slippage_stress_is_visible(self):
        case = {
            "filter": "none", "stride": 10, "ratio": "1:3",
            "selected": {"1": date(2025, 1, 1), "2": date(2025, 1, 15)},
            "entered": {"1": date(2025, 1, 1), "2": date(2025, 1, 15)},
            "skipped": {},
            "trades": [
                trade("1", "HOLD_20_SESSIONS", "RESOLVED", 100, "2025-01-02", "2025-01-12"),
                trade("2", "HOLD_20_SESSIONS", "UNRESOLVED_SOURCE_END", "", "2025-01-16", "", "76500", "1", "3", "2025-01-15", "2025-01-20"),
            ],
        }
        r = cadence.summarize_period(
            case, "1Y", date(2024, 7, 23), date(2025, 7, 23), 1.0, "HOLD_20_SESSIONS"
        )
        self.assertEqual((r["entered_cohorts"], r["resolved"], r["unresolved"]), (2, 1, 1))
        self.assertEqual(r["mean_net_pnl_usd"], 100.0)
        self.assertEqual(r["stress_mean_net_pnl_usd"], 60.0)
        self.assertEqual(r["peak_concurrent_cohorts"], 2)

    def test_pareto_is_not_a_weighted_score(self):
        rows = [
            {"window":"5Y","filter":"none","ratio":"1:3","policy":"HOLD_20_SESSIONS","stride_sessions":10,
             "annualized_resolved_net_pnl_usd":100,"win_rate_pct":70,"worst_resolved_trade_usd":-1000,
             "peak_short_assignment_obligation_usd":150000},
            {"window":"5Y","filter":"none","ratio":"1:3","policy":"HOLD_20_SESSIONS","stride_sessions":20,
             "annualized_resolved_net_pnl_usd":90,"win_rate_pct":65,"worst_resolved_trade_usd":-1200,
             "peak_short_assignment_obligation_usd":100000},
        ]
        cadence.add_pareto_flags(rows)
        self.assertTrue(all(row["pareto_frontier_cadence"] for row in rows))


if __name__ == "__main__":
    unittest.main(verbosity=2)
