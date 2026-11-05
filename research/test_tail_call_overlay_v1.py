import csv
import tempfile
import unittest
from pathlib import Path

from tail_call_overlay_v1 import (
    pick_call, option_mark_pnl, option_closed_pnl, run_arm, write_blocked_status,
    CONTRACTS, MULTIPLIER, TARGET_ASK,
)


def quote(day, expiry, dte, strike=12.0, spot=10.0, ask=0.10, bid=0.0,
          ask_size=10, bid_size=0, oi=20, delta=0.03):
    return {
        "tradeDate": day, "expirDate": expiry, "dte": dte, "strike": strike,
        "spotPrice": spot, "callAskPrice": ask, "callBidPrice": bid,
        "callAskSize": ask_size, "callBidSize": bid_size,
        "callOpenInterest": oi, "callVolume": 5, "delta": delta,
        "callBidIv": 0.5, "callMidIv": 0.55, "callAskIv": 0.6,
        "updatedAt": day + "T19:46:00Z",
    }


def write_rows(path, rows):
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


class TailCallOverlayTests(unittest.TestCase):
    def test_picker_requires_otm_ask_at_or_below_ten_cents_and_six_lot_size(self):
        day = "2025-01-02"
        rows = [
            quote(day, "2025-02-01", 30, ask=0.11, ask_size=20),
            quote(day, "2025-02-01", 30, ask=0.10, ask_size=5),
            quote(day, "2025-02-01", 15, ask=0.10, ask_size=20),
            quote(day, "2025-02-01", 30, strike=9.0, ask=0.10, ask_size=20),
            quote(day, "2025-02-01", 31, ask=0.09, ask_size=20),
            quote(day, "2025-02-01", 30, ask=0.10, ask_size=20),
        ]
        picked = pick_call(rows, day)
        self.assertIsNotNone(picked)
        self.assertEqual(picked["entry_ask"], 0.10)
        self.assertEqual(picked["dte_entry"], 30)
        self.assertEqual(picked["entry_ask_size"], 20)
        self.assertEqual(picked["strike"], 12.0)
        self.assertIsNone(pick_call([quote(day, "2025-02-01", 30, ask=0.11)], day))

    def test_premium_and_commissions_reconcile_to_six_standard_contracts(self):
        self.assertEqual(CONTRACTS * MULTIPLIER * TARGET_ASK, 60.0)
        self.assertAlmostEqual(option_mark_pnl(0.10, 0.00), -63.90, places=6)
        self.assertAlmostEqual(option_closed_pnl(0.10, 0.50), 232.20, places=6)

    def test_daily_nav_uses_bid_and_exit_requires_six_lot_bid(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_rows(root / "testarm_entries.csv", [{
                "episode_id": "testarm-1", "entry_date": "2025-01-02",
            }])
            write_rows(root / "testarm_trades.csv", [{
                "episode_id": "testarm-1", "exit_date": "2025-01-03",
                "net_pnl_usd": "-100.0",
            }])
            write_rows(root / "testarm_daily_nav.csv", [
                {"date": "2025-01-02", "nav_usd": "100000"},
                {"date": "2025-01-03", "nav_usd": "100050"},
                {"date": "2025-01-06", "nav_usd": "100100"},
            ])
            daily_quotes = {
                "2025-01-02": [quote("2025-01-02", "2025-02-01", 30, bid=0.0, bid_size=0)],
                "2025-01-03": [quote("2025-01-03", "2025-02-01", 29, bid=0.50, bid_size=2)],
                "2025-01-06": [quote("2025-01-06", "2025-02-01", 26, bid=0.50, bid_size=6)],
            }
            result = run_arm("testarm", root, daily_quotes)
            self.assertEqual(result["tail_purchased"], 1)
            self.assertEqual(result["tail_entry_blocked"], 0)
            self.assertEqual(result["tail_trade_rows"][0]["status"], "RESOLVED_BID_SIZE_GE_6")
            self.assertEqual(result["tail_trade_rows"][0]["exit_date"], "2025-01-06")
            self.assertEqual(result["tail_trade_rows"][0]["exit_delay_sessions"], 1)
            # The 2-lot positive bid must not mark all six contracts as liquidatable.
            self.assertAlmostEqual(result["tail_daily_rows"][1]["tail_total_pnl_usd"], -63.9, places=5)
            self.assertEqual(result["tail_daily_rows"][1]["positions_with_executable_6_lot_bid"], 0)
            self.assertAlmostEqual(result["tail_trade_rows"][0]["tail_net_pnl_usd"], 232.2, places=5)
            self.assertAlmostEqual(result["tail_daily_rows"][-1]["tail_total_pnl_usd"], 232.2, places=5)
            self.assertAlmostEqual(result["tail_daily_rows"][-1]["combined_nav_usd"], 100332.2, places=5)

    def test_blocked_status_never_substitutes_etf_share_return_for_option_pnl(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "example").mkdir()
            status = write_blocked_status(root / "example", root / "out")
            self.assertEqual(status["status"], "BLOCKED_DATA_ACCESS")
            self.assertEqual(status["maximum_gross_premium_per_cohort_usd"], 60.0)
            text = (root / "out" / "TAIL_CALL_REPORT.md").read_text(encoding="utf-8")
            self.assertIn("No option P&L", text)
            self.assertIn("ORATS_API_TOKEN", text)
            self.assertNotIn("Black-Scholes estimate", text)


if __name__ == "__main__":
    unittest.main()
