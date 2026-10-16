import importlib.util
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
PATH = HERE / "qqq_put_ratio_dynamic_nav_bar_v1.py"
SPEC = importlib.util.spec_from_file_location("qqq_dynamic_nav_bar", PATH)
M = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(M)


def qr(bid, ask, bs=20, ass=20):
    return {"bid": bid, "ask": ask, "bid_size": bs, "ask_size": ass}


def simple_trade():
    return {
        "trade_id": "synthetic-1",
        "entry_date": "2024-01-03",
        "expiry": "2024-01-05",
        "long_strike": 100.0,
        "short_strike": 90.0,
        "spot_entry": 105.0,
        "entry_quotes": {"long": qr(4.5, 5.0), "short": qr(2.0, 2.5)},
        "path": [
            {"date": "2024-01-03", "spot": 105.0, "long": qr(4.5, 5.0), "short": qr(2.0, 2.5), "vix": 18.0},
            {"date": "2024-01-04", "spot": 104.0, "long": qr(4.7, 5.1), "short": qr(1.0, 1.4), "vix": 22.0},
            {"date": "2024-01-05", "spot": 105.0, "long": qr(0.0, 0.01), "short": qr(0.0, 0.01), "vix": 20.0},
        ],
    }


class DynamicNavBarTests(unittest.TestCase):
    def test_mark_path_is_optional_and_does_not_change_pnl(self):
        trade = simple_trade()
        policy = {"name": "DTE7_CLOSE_SHORT_RISK", "kind": "DTE7"}
        base = M.core.simulate(trade, M.core.SHORT_HEAVY, 1, 100000, policy, .05, .65)
        tracked = M.core.simulate(trade, M.core.SHORT_HEAVY, 1, 100000, policy, .05, .65, include_mark_path=True)
        self.assertIsNone(base["mark_curve"])
        self.assertEqual(len(tracked["mark_curve"]), 3)
        self.assertEqual(tracked["mark_curve"][-1]["status"], "EXPIRY_INTRINSIC_PROXY_NOT_BROKER_SETTLEMENT")
        self.assertEqual(base["final_pnl_usd"], tracked["final_pnl_usd"])

    def test_whole_units_follow_budget_and_depth(self):
        blocked = M.choose_units(100000, .01, 3000, 0, 20, "PER_TRADE_TERMINAL_BUDGET")
        self.assertEqual(blocked["planned_units"], 0)
        self.assertEqual(blocked["actual_units"], 0)
        fixed = M.choose_units(100000, .01, 3000, 0, 20, "FIXED_1_UNIT_BUDGET_BYPASS")
        self.assertEqual(fixed["actual_units"], 1)
        self.assertTrue(fixed["breaches_tail_budget"])
        fixed12 = M.choose_units(100000, .01, 3000, 0, 20, "FIXED_12_UNIT_BUDGET_BYPASS")
        self.assertEqual(fixed12["actual_units"], 12)
        self.assertTrue(fixed12["breaches_tail_budget"])

    def test_bar_occurrence_reports_episode_and_mark_rates(self):
        episodes = [
            {"nav_before": 100000, "mark_curve": [
                {"pnl_usd": -200, "vix": 18, "dte": 30},
                {"pnl_usd": 800, "vix": 28, "dte": 15},
            ], "friction_observations": [
                {"friction_drag_usd": 600, "state_labels": ("OVERALL", "VIX_25_35", "DTE_8_20")},
                {"friction_drag_usd": 200, "state_labels": ("OVERALL", "VIX_15_25", "DTE_21_40")},
            ]},
            {"nav_before": 100000, "mark_curve": [
                {"pnl_usd": 100, "vix": 18, "dte": 30},
                {"pnl_usd": -1200, "vix": 22, "dte": 25},
            ], "friction_observations": [
                {"friction_drag_usd": 100, "state_labels": ("OVERALL", "VIX_15_25", "DTE_21_40")},
            ]},
        ]
        config = {"direction": "SHORT_HEAVY_1_LONG_N_SHORT", "ratio_n": 1, "tail_budget_pct": .01,
                  "policy": "synthetic", "cost_case": "BASE_005_065", "sizing_mode": "PER_TRADE_TERMINAL_BUDGET"}
        rows = M.build_bar_rows(episodes, config)
        profit_05 = next(x for x in rows if x["bar_type"] == "NET_PROFIT_BAR" and x["bar_level_pct_nav"] == .5)
        loss_1 = next(x for x in rows if x["bar_type"] == "NET_LOSS_BAR" and x["bar_level_pct_nav"] == 1.0)
        friction_05 = next(x for x in rows if x["bar_type"] == "FRICTION_COST_BAR" and x["bar_level_pct_nav"] == .5)
        self.assertEqual((profit_05["episode_denominator"], profit_05["episode_hit_count"]), (2, 1))
        self.assertAlmostEqual(profit_05["episode_hit_pct"], 50.0)
        self.assertEqual((loss_1["episode_denominator"], loss_1["episode_hit_count"]), (2, 1))
        self.assertEqual((friction_05["episode_denominator"], friction_05["episode_hit_count"]), (2, 1))
        self.assertEqual((friction_05["mark_observation_denominator"], friction_05["mark_hit_count"]), (3, 1))

    def test_drawdown_tiers_include_cycles_year_incidence_and_days(self):
        prices = [{"date": (date(2024, 1, 1) + timedelta(days=i)).isoformat(), "close": 100, "vix": 20} for i in range(5)]
        daily = [
            {"date": prices[0]["date"], "nav_usd": 100000.0},
            {"date": prices[1]["date"], "nav_usd": 96000.0},
            {"date": prices[2]["date"], "nav_usd": 94000.0},
            {"date": prices[3]["date"], "nav_usd": 100000.0},
            {"date": prices[4]["date"], "nav_usd": 105000.0},
        ]
        _, tiers = M.drawdown_tiers(daily, prices)
        three = next(x for x in tiers if x["drawdown_level_pct"] == 3)
        five = next(x for x in tiers if x["drawdown_level_pct"] == 5)
        self.assertEqual(three["cycle_count"], 1)
        self.assertEqual(three["event_year_incidence_pct"], 100.0)
        self.assertEqual(five["cycle_count"], 1)
        self.assertEqual(three["valid_day_incidence_pct"], 40.0)

    def test_nonpositive_nav_is_capital_failure_not_missing_data(self):
        prices = [{"date": (date(2024, 1, 1) + timedelta(days=i)).isoformat(), "close": 100, "vix": 20}
                  for i in range(5)]
        daily = [
            {"date": prices[0]["date"], "nav_usd": 100000.0},
            {"date": prices[1]["date"], "nav_usd": 1000.0},
            {"date": prices[2]["date"], "nav_usd": 0.0},
            {"date": prices[3]["date"], "nav_usd": -100.0},
            {"date": prices[4]["date"], "nav_usd": 900.0},
        ]
        meta, tiers = M.drawdown_tiers(daily, prices)
        self.assertEqual(meta["valid_marks"], 5)
        self.assertEqual(meta["missing_marks"], 0)
        self.assertEqual(meta["nonpositive_nav_marks"], 2)
        self.assertEqual(meta["max_drawdown_pct"], -100.0)

    def test_one_episode_dynamic_replay_outputs_nav_curve(self):
        trade = simple_trade()
        prices = [
            {"date": "2024-01-03", "close": 105, "vix": 18},
            {"date": "2024-01-04", "close": 104, "vix": 22},
            {"date": "2024-01-05", "close": 105, "vix": 20},
        ]
        summary, episodes, daily = M.replay_scenario(
            [trade], prices, 100000, 214012, M.core.SHORT_HEAVY, 1, .02,
            {"name": "DTE7_CLOSE_SHORT_RISK", "kind": "DTE7"},
            next(cost for cost in M.core.COSTS if cost["name"] == "BASE_005_065"), "PER_TRADE_TERMINAL_BUDGET"
        )
        self.assertEqual(summary["executed_episodes"], 1)
        self.assertEqual(len(episodes), 1)
        self.assertEqual(len(daily), 3)
        self.assertIsNotNone(summary["final_nav_usd"])
        self.assertEqual(episodes[0]["ratio_units"], 6, "2% of $100k divided by the one-unit terminal envelope should size six contracts, within displayed depth")


if __name__ == "__main__":
    unittest.main(verbosity=2)
