import unittest
import pandas as pd
from qqq_atm_weekly_vs_3y_call_v1 import pick_atm_candidate, size_contracts


class QQQATMWeeklyThreeYearTests(unittest.TestCase):
    def test_weekly_selection_uses_nearest_expiry_then_atm_not_delta(self):
        d = pd.Timestamp("2020-01-03")
        chain = pd.DataFrame([
            {"date": d, "expiration": pd.Timestamp("2020-01-10"), "contract_id": "FAR",
             "strike": 120.0, "bid": 0.2, "ask": 0.3, "delta": 0.02, "volume": 100, "dte": 7},
            {"date": d, "expiration": pd.Timestamp("2020-01-10"), "contract_id": "ATM",
             "strike": 100.0, "bid": 2.0, "ask": 2.1, "delta": 0.51, "volume": 1, "dte": 7},
            {"date": d, "expiration": pd.Timestamp("2020-01-09"), "contract_id": "NEARER_DTE",
             "strike": 101.0, "bid": 1.5, "ask": 1.6, "delta": 0.45, "volume": 2, "dte": 6},
        ])
        # The DTE target is prioritized; among equal-DTE candidates, nearest moneyness wins.
        picked = pick_atm_candidate(chain, d, 100.0, "weekly")
        self.assertEqual(picked["contract_id"], "ATM")
        self.assertNotEqual(picked["contract_id"], "FAR")
        self.assertEqual(picked["dte"], 7)

    def test_three_year_selection_requires_actual_long_dte_quote_and_no_delta_band(self):
        d = pd.Timestamp("2020-01-03")
        chain = pd.DataFrame([
            {"date": d, "expiration": pd.Timestamp("2022-01-03"), "contract_id": "TWOY",
             "strike": 100.0, "bid": 10.0, "ask": 10.5, "delta": 0.6, "volume": 1, "dte": 731},
            {"date": d, "expiration": pd.Timestamp("2023-01-02"), "contract_id": "THREEY",
             "strike": 101.0, "bid": 12.0, "ask": 12.5, "delta": 0.7, "volume": 0, "dte": 1095},
        ])
        picked = pick_atm_candidate(chain, d, 100.0, "three_year")
        self.assertEqual(picked["contract_id"], "THREEY")
        self.assertEqual(picked["dte"], 1095)

    def test_no_three_year_contract_returns_no_candidate(self):
        d = pd.Timestamp("2020-01-03")
        chain = pd.DataFrame([
            {"date": d, "expiration": pd.Timestamp("2022-01-03"), "contract_id": "TWOY",
             "strike": 100.0, "bid": 10.0, "ask": 10.5, "delta": 0.6, "volume": 1, "dte": 731},
        ])
        self.assertIsNone(pick_atm_candidate(chain, d, 100.0, "three_year"))

    def test_whole_contracts_never_overspend(self):
        self.assertEqual(size_contracts(700.0, 7.0), 1)
        self.assertEqual(size_contracts(699.0, 7.0), 0)
        self.assertEqual(size_contracts(701.0, 7.0), 1)


if __name__ == "__main__":
    unittest.main()
