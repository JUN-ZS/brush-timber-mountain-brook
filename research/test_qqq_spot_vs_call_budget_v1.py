import unittest
import pandas as pd

from qqq_spot_vs_call_budget_v1 import pick_candidate, size_contracts, xirr


class QQQSpotVsCallBudgetTests(unittest.TestCase):
    def test_weekly_call_selects_nearest_five_delta_otm_contract(self):
        d = pd.Timestamp("2020-01-03")
        chain = pd.DataFrame([
            {"date": d, "expiration": pd.Timestamp("2020-01-10"), "contract_id": "A",
             "strike": 101.0, "bid": 0.10, "ask": 0.12, "delta": 0.051, "volume": 2, "dte": 7},
            {"date": d, "expiration": pd.Timestamp("2020-01-10"), "contract_id": "B",
             "strike": 102.0, "bid": 0.09, "ask": 0.11, "delta": 0.050, "volume": 20, "dte": 7},
            {"date": d, "expiration": pd.Timestamp("2020-01-10"), "contract_id": "ITM",
             "strike": 99.0, "bid": 0.20, "ask": 0.22, "delta": 0.90, "volume": 100, "dte": 7},
        ])
        picked = pick_candidate(chain, d, 100.0, "weekly")
        self.assertIsNotNone(picked)
        self.assertEqual(picked["contract_id"], "B")
        self.assertEqual(picked["dte"], 7)
        self.assertGreater(picked["strike"], 100.0)

    def test_annual_call_obeys_dte_band_and_delta_band(self):
        d = pd.Timestamp("2020-01-03")
        chain = pd.DataFrame([
            {"date": d, "expiration": pd.Timestamp("2021-01-02"), "contract_id": "Y",
             "strike": 150.0, "bid": 4.0, "ask": 4.2, "delta": 0.05, "volume": 1, "dte": 365},
            {"date": d, "expiration": pd.Timestamp("2021-01-02"), "contract_id": "BAD_DELTA",
             "strike": 151.0, "bid": 1.0, "ask": 1.1, "delta": 0.15, "volume": 10, "dte": 365},
        ])
        picked = pick_candidate(chain, d, 100.0, "annual")
        self.assertEqual(picked["contract_id"], "Y")

    def test_whole_contract_sizing_never_overspends(self):
        self.assertEqual(size_contracts(13.46, 0.13), 1)
        self.assertEqual(size_contracts(13.46, 0.14), 0)
        self.assertEqual(size_contracts(700.0, 7.0), 1)
        self.assertEqual(size_contracts(699.0, 7.0), 0)

    def test_xirr_uses_actual_start_and_terminal_dates(self):
        start = pd.Timestamp("2010-01-01")
        end = pd.Timestamp("2020-01-01")
        rate = xirr([(start, -7000.0), (end, 14000.0)])
        self.assertIsNotNone(rate)
        self.assertAlmostEqual(rate, 2 ** (365.25 / (end - start).days) - 1, places=6)

    def test_xirr_for_cash_only_with_even_yearly_contributions_is_zero(self):
        flows = [(pd.Timestamp(f"{year}-01-01"), -700.0) for year in range(2010, 2020)]
        flows.append((pd.Timestamp("2020-01-01"), 7000.0))
        rate = xirr(flows)
        self.assertIsNotNone(rate)
        self.assertAlmostEqual(rate, 0.0, places=6)


if __name__ == "__main__":
    unittest.main()
