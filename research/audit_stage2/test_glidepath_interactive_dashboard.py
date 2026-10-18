import json
import unittest
from pathlib import Path
from glidepath_interactive_dashboard import FIELDS, ANNUAL_FIELDS, render_dashboard
from stock_bond_glidepath_backtest import BOND_TICKERS, TARGET_CONVERSIONS, TIMING_RULES

def sample_rows():
    cases, annual = [], []
    for b in BOND_TICKERS:
        for t in TARGET_CONVERSIONS:
            for m in TIMING_RULES:
                for f in ("no_withdrawals","delayed_stepup_example","monthly_withdrawal_500_usd_stress","monthly_withdrawal_1000_usd_stress"):
                    base={"bond_proxy":b,"target_bond_conversion_pct_at_year10":t,"timing_rule":m,"cashflow_mode":f,"rolling_windows":157}
                    scenario={k:None for k in FIELDS}
                    scenario.update(base)
                    scenario.update({"median_terminal_nav_usd":230000.0,"p05_terminal_nav_usd":120000.0,"p95_terminal_nav_usd":400000.0,"worst_terminal_nav_usd":90000.0,"median_time_weighted_cagr":0.08,"p05_time_weighted_cagr":0.01,"worst_time_weighted_cagr":-0.02,"median_daily_max_drawdown":-0.2,"worst_daily_max_drawdown":-0.55,"windows_below_initial_capital_at_year10":10,"windows_with_withdrawal_shortfall":5 if f=="monthly_withdrawal_1000_usd_stress" else 0,"median_actual_withdrawals_usd":60000,"p95_withdrawal_shortfall_usd":1500,"median_investor_xirr":0.08})
                    cases.append(scenario)
                    for y in range(11):
                        mark={k:None for k in ANNUAL_FIELDS}
                        mark.update(base)
                        mark.update({"year":y,"median_nav_usd":100000+y*(t*100),"p05_nav_usd":90000+y*(t*50),"p95_nav_usd":110000+y*(t*150),"worst_nav_usd":80000+y*(t*25),"median_cumulative_twr_cagr":None if y==0 else 0.05+y*0.003,"p05_cumulative_twr_cagr":None if y==0 else -0.04+y*0.002,"median_year_twr":None if y==0 else 0.04,"p05_year_twr":None if y==0 else -0.12,"median_drawdown_to_date":0.0 if y==0 else -0.10-y*0.01,"worst_drawdown_to_date":0.0 if y==0 else -0.45,"windows_below_initial_capital":0 if y==0 else y,"windows_with_withdrawal_shortfall":0 if f!="monthly_withdrawal_1000_usd_stress" else y,"median_actual_withdrawals_usd":0 if f=="no_withdrawals" else min(y*1000,120000),"median_shortfall_usd":0,"p95_shortfall_usd":0 if f!="monthly_withdrawal_1000_usd_stress" else y*100,"median_target_bond_weight":t/100*(y/10),"median_target_stock_weight":1-t/100*(y/10)})
                        annual.append(mark)
    return cases, annual

class DashboardTests(unittest.TestCase):
    def test_embeds_complete_scenario_grid_and_all_annual_marks(self):
        cases, annual = sample_rows()
        self.assertEqual(len(cases),768)
        self.assertEqual(len(annual),8448)
        page=render_dashboard(cases,annual)
        for token in ('id="target"','id="year"','id="heatMetric"','id="wealth"','id="drawdown"','id="returns"','id="gaps"','id="frontier"','id="flows"','id="glide"','id="table"','id="fan"','id="drawdownPath"','id="heatmap"','id="exportMatrix"','id="exportAnnual"','addEventListener("input",update)','data-pick=','data-year=','拖動 BAR','不是預測','P05–P95','__ANNUAL__'):
            if token=="__ANNUAL__":
                continue
            self.assertIn(token,page)
        payload=page.split("const D=",1)[1].split(",A=",1)[0]
        annual_payload=page.split("const D=",1)[1].split(",A=",1)[1].split(",TG=",1)[0]
        self.assertEqual(len(json.loads(payload)),768)
        self.assertEqual(len(json.loads(annual_payload)),8448)
        self.assertNotIn("__DATA__",page)
        self.assertNotIn("__ANNUAL__",page)

    def test_selected_year_is_read_from_annual_rows_and_all_six_timings_have_paths(self):
        page_template=Path(__import__("glidepath_interactive_dashboard").__file__).read_text(encoding="utf-8")
        self.assertIn('year===s.year',page_template)
        self.assertIn('Y(s.bond,s.target,s.timing,s.flow,s.year)',page_template)
        self.assertIn('100*Y(s.bond,s.target,m,s.flow,y).median_target_bond_weight',page_template)
        self.assertNotIn('W(s.target,y,m)',page_template)
        self.assertIn('median_nav_usd',page_template)
        self.assertIn('median_drawdown_to_date',page_template)
        self.assertIn('back_late',page_template)
        self.assertIn('mid_loaded',page_template)
        self.assertIn('function fan(s)',page_template)
        self.assertIn('function drawdownPath(s)',page_template)
        self.assertIn('function heatmap(s)',page_template)
        self.assertIn('function exportMatrix()',page_template)
        self.assertIn('cashflow_mode===s.flow',page_template)
        self.assertIn('data-year="'+"'"+'+y+',page_template)

if __name__=="__main__":
    unittest.main()
