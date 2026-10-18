import json
import unittest
from glidepath_interactive_dashboard import FIELDS, render_dashboard
from stock_bond_glidepath_backtest import BOND_TICKERS, TARGET_CONVERSIONS, TIMING_RULES

def samples():
    rows=[]
    for b in BOND_TICKERS:
        for t in TARGET_CONVERSIONS:
            for m in TIMING_RULES:
                for f in ("no_withdrawals","delayed_stepup_example","monthly_withdrawal_500_usd_stress","monthly_withdrawal_1000_usd_stress"):
                    r={k:None for k in FIELDS}
                    r.update({"bond_proxy":b,"target_bond_conversion_pct_at_year10":t,"timing_rule":m,"cashflow_mode":f,"rolling_windows":157,"median_terminal_nav_usd":260000,"p05_terminal_nav_usd":120000,"p95_terminal_nav_usd":400000,"worst_terminal_nav_usd":100000,"median_time_weighted_cagr":0.08,"p05_time_weighted_cagr":0.02,"worst_time_weighted_cagr":-0.01,"median_daily_max_drawdown":-0.2,"worst_daily_max_drawdown":-0.5,"windows_below_initial_capital_at_year10":10,"windows_with_withdrawal_shortfall":5 if f=="monthly_withdrawal_1000_usd_stress" else 0,"median_actual_withdrawals_usd":60000,"p95_withdrawal_shortfall_usd":1500,"median_investor_xirr":0.08})
                    rows.append(r)
    return rows

class DashboardTests(unittest.TestCase):
    def test_embeds_complete_grid_and_linked_controls(self):
        page=render_dashboard(samples())
        for token in ('id="target"','id="year"','id="wealth"','id="drawdown"','id="returns"','id="gaps"','id="frontier"','id="flows"','id="glide"','id="table"','data-pick=','拖動 BAR','不是預測'):
            self.assertIn(token,page)
        payload=page.split("const D=",1)[1].split(",TG=",1)[0]
        self.assertEqual(len(json.loads(payload)),384)
        self.assertNotIn("__DATA__",page)

if __name__=="__main__":
    unittest.main()
