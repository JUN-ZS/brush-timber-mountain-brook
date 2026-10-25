from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT / "qqq_hybrid_tail_triggered_nav_v1.py"
SPEC = importlib.util.spec_from_file_location("hybrid_tail_replay", SCRIPT)
ENGINE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(ENGINE)


class TailOverlayContractTests(unittest.TestCase):
    def test_tail_market_value_is_adjusted_close_return_on_funded_notional(self):
        position = {"entry_notional": 1000.0, "entry_adj_close": 10.0}
        self.assertAlmostEqual(ENGINE.tail_mark_value(position, 12.5), 1250.0, places=8)
        self.assertEqual(ENGINE.tail_mark_value(None, 12.5), 0.0)

    def test_trigger_uses_frozen_hybrid_risk_conditions(self):
        from types import SimpleNamespace
        quiet = SimpleNamespace(rV=0.0, vix=18.0, ts=0.02, rQ=0.001)
        self.assertFalse(ENGINE.tail_trigger(quiet))
        for field, value in (("rV", 0.061), ("vix", 35.1), ("ts", -0.001), ("rQ", -0.031)):
            row = SimpleNamespace(rV=0.0, vix=18.0, ts=0.02, rQ=0.001)
            setattr(row, field, value)
            self.assertTrue(ENGINE.tail_trigger(row), field)

    def test_triggered_entry_and_exit_execute_after_the_signal_close(self):
        dates = pd.bdate_range("2020-01-02", periods=15)
        qqq = [100.0 * (1.001 ** i) for i in range(len(dates))]
        vxx = [20.0] * len(dates)
        vxx[5:] = [21.5] * (len(dates) - 5)  # >6% rise known only at date index 5 close
        vix = [18.0] * len(dates)
        tail = [10.0 + 0.2 * i for i in range(len(dates))]
        data = {
            "dates": [d.strftime("%Y-%m-%d") for d in dates],
            "qqq": qqq, "vxx": vxx, "vix": vix,
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            spot_file = root / "spots.json"
            tail_file = root / "tail.csv"
            spot_file.write_text(json.dumps(data), encoding="utf-8")
            pd.DataFrame({"date": dates, "adj_close": tail}).to_csv(tail_file, index=False)
            result = ENGINE.simulate(
                str(spot_file), False, str(tail_file), "TRIGGERED", 0.02, 0.0
            )
        eq = result[6]
        trades = result[7]
        self.assertEqual(len(eq), len(dates))
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0]["entry_date"], dates[6].strftime("%Y-%m-%d"))
        self.assertEqual(trades[0]["exit_date"], dates[8].strftime("%Y-%m-%d"))
        self.assertEqual(trades[0]["status"], "CLOSED")
        self.assertGreater(trades[0]["net_pnl_usd"], 0.0)
        self.assertTrue(eq["nav"].gt(0).all())
        # The entry itself is funded out of account cash and marks the same value into NAV.
        self.assertAlmostEqual(
            float(eq.loc[eq.date == dates[6], "tail_market_value"].iloc[0]),
            float(trades[0]["entry_notional_usd"]),
            places=6
        )
        self.assertFalse(bool(eq.loc[eq.date == dates[8], "tail_open"].iloc[0]))

    def test_always_on_is_one_non_overlapping_position(self):
        dates = pd.bdate_range("2021-01-04", periods=12)
        data = {
            "dates": [d.strftime("%Y-%m-%d") for d in dates],
            "qqq": [100.0 + i for i in range(len(dates))],
            "vxx": [20.0] * len(dates),
            "vix": [18.0] * len(dates),
        }
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            spot_file = root / "spots.json"
            tail_file = root / "tail.csv"
            spot_file.write_text(json.dumps(data), encoding="utf-8")
            pd.DataFrame({"date": dates, "adj_close": [20.0 + i for i in range(len(dates))]}).to_csv(tail_file, index=False)
            result = ENGINE.simulate(
                str(spot_file), False, str(tail_file), "ALWAYS_ON", 0.02, 10.0
            )
        trades = result[7]
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0]["status"], "MARKED_OPEN_AT_END")
        self.assertAlmostEqual(trades[0]["entry_notional_usd"], 2000.0, delta=2.0)
        self.assertTrue(result[6]["tail_open"].all())


if __name__ == "__main__":
    unittest.main()
