import json
import unittest
import csv
import tempfile
from html.parser import HTMLParser
from pathlib import Path

class MarkupIDAudit(HTMLParser):
    def __init__(self):
        super().__init__()
        self.id_to_tag = {}
        self.duplicates = set()
    def handle_starttag(self, tag, attrs):
        element_id = dict(attrs).get("id")
        if not element_id:
            return
        if element_id in self.id_to_tag:
            self.duplicates.add(element_id)
        self.id_to_tag[element_id] = tag
from glidepath_interactive_dashboard import FIELDS, ANNUAL_FIELDS, HISTOGRAM_METRICS, render_dashboard, summarize_histogram, build_cohort_profiles
from stock_bond_glidepath_backtest import BOND_TICKERS, TARGET_CONVERSIONS, TIMING_RULES

def sample_histograms():
    rows=[]
    flow_modes=("no_withdrawals","delayed_stepup_example","monthly_withdrawal_500_usd_stress","monthly_withdrawal_1000_usd_stress")
    counts=[5,10,15,20,30,25,22,30]
    for bi,bond in enumerate(BOND_TICKERS):
        for target in TARGET_CONVERSIONS:
            for ti,timing in enumerate(TIMING_RULES):
                for fi,flow in enumerate(flow_modes):
                    for metric in HISTOGRAM_METRICS:
                        if metric=="terminal_nav_usd":
                            low=90000+target*300+bi*2000+ti*500+fi*1000
                            width=5000.0
                        elif metric=="time_weighted_cagr":
                            low=-0.18+target/1000+bi*.005+ti*.002
                            width=.04
                        elif metric=="daily_max_drawdown":
                            low=-.75+target/1000+bi*.005+ti*.002
                            width=.03
                        else:
                            low=fi*100.0
                            width=100.0
                        bins=[{"low":low+i*width,"high":low+(i+1)*width,"count":n} for i,n in enumerate(counts)]
                        rows.append({
                            "bond_proxy":bond,"target_bond_conversion_pct_at_year10":target,
                            "timing_rule":timing,"cashflow_mode":flow,"metric":metric,"n":157,
                            "min":low,"max":low+8*width,"p05":low+.4*width,
                            "median":low+4*width,"p95":low+7.6*width,"bins":bins,
                        })
    return rows


def sample_cohorts():
    rows=[]
    flow_modes=("no_withdrawals","delayed_stepup_example","monthly_withdrawal_500_usd_stress","monthly_withdrawal_1000_usd_stress")
    for bi,bond in enumerate(BOND_TICKERS):
        for target in TARGET_CONVERSIONS:
            for ti,timing in enumerate(TIMING_RULES):
                for fi,flow in enumerate(flow_modes):
                    for cohort_year in (2003,2004):
                        base=100000+target*100+bi*1000+ti*250+fi*500+(cohort_year-2003)*3000
                        rows.append({
                            "bond_proxy":bond,"target_bond_conversion_pct_at_year10":target,"timing_rule":timing,
                            "cashflow_mode":flow,"start_year":cohort_year,"window_count":6,
                            "first_window_start":f"{cohort_year}-01-31","last_window_start":f"{cohort_year}-06-30",
                            "median_terminal_nav_usd":base,"p05_terminal_nav_usd":base*.8,"p95_terminal_nav_usd":base*1.2,
                            "worst_terminal_nav_usd":base*.5,"median_time_weighted_cagr":.06+ti*.002,
                            "p05_time_weighted_cagr":-.08+ti*.002,"worst_time_weighted_cagr":-.2,
                            "median_daily_max_drawdown":-.2,"worst_daily_max_drawdown":-.55,
                            "windows_with_withdrawal_shortfall":fi*2,"windows_below_initial_capital":2 if cohort_year==2003 else 0,"initial_capital_usd":100000.0,
                        })
    return rows


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
    def test_start_year_cohorts_preserve_all_real_window_rows(self):
        fields=["window_start","initial_capital_usd","bond_proxy","target_bond_conversion_pct_at_year10","timing_rule","cashflow_mode","terminal_nav_usd","time_weighted_cagr","daily_max_drawdown","withdrawal_shortfall_usd"]
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"windows.csv"
            with path.open("w",newline="",encoding="utf-8") as handle:
                writer=csv.DictWriter(handle,fieldnames=fields)
                writer.writeheader()
                for i,date in enumerate(("2003-01-31","2003-02-28","2003-03-31","2004-01-31","2004-02-29","2004-03-31")):
                    writer.writerow({"window_start":date,"initial_capital_usd":100000.0,"bond_proxy":"AGG","target_bond_conversion_pct_at_year10":60,"timing_rule":"linear","cashflow_mode":"no_withdrawals","terminal_nav_usd":90000.0 if i==0 else 100000+i*1000,"time_weighted_cagr":.04+i*.005,"daily_max_drawdown":-.1-i*.02,"withdrawal_shortfall_usd":100.0 if i==5 else 0.0})
            result=build_cohort_profiles(path,expected_scenarios=1,expected_windows=6)
        self.assertEqual({r["start_year"] for r in result},{2003,2004})
        self.assertEqual(sum(r["window_count"] for r in result),6)
        self.assertEqual(next(r for r in result if r["start_year"]==2003)["window_count"],3)
        self.assertEqual(next(r for r in result if r["start_year"]==2004)["windows_with_withdrawal_shortfall"],1)
        self.assertEqual(next(r for r in result if r["start_year"]==2003)["windows_below_initial_capital"],1)
        self.assertEqual(next(r for r in result if r["start_year"]==2004)["windows_below_initial_capital"],0)
    def test_histogram_summary_conserves_samples_and_orders_percentiles(self):
        values=[float(i*i%97) for i in range(157)]
        summary=summarize_histogram(values)
        self.assertEqual(summary["n"],157)
        self.assertEqual(sum(b["count"] for b in summary["bins"]),157)
        self.assertLessEqual(summary["min"],summary["p05"])
        self.assertLessEqual(summary["p05"],summary["median"])
        self.assertLessEqual(summary["median"],summary["p95"])
        self.assertLessEqual(summary["p95"],summary["max"])
        flat=summarize_histogram([0.0]*15)
        self.assertEqual(flat["bins"],[{"low":0.0,"high":0.0,"count":15}])
    def test_embeds_complete_scenario_grid_and_all_annual_marks(self):
        cases, annual = sample_rows()
        self.assertEqual(len(cases),768)
        self.assertEqual(len(annual),8448)
        page=render_dashboard(cases,annual,sample_histograms(),sample_cohorts())
        for token in ('id="target"','id="year"','id="heatMetric"','id="histMetric"','id="cohortMetric"','id="cohort"','id="cohortDetail"','id="wealth"','id="drawdown"','id="returns"','id="gaps"','id="frontier"','id="flows"','id="glide"','id="table"','id="fan"','id="drawdownPath"','id="heatmap"','id="histogram"','id="exportMatrix"','id="exportAnnual"','addEventListener("input",update)','data-pick=','data-year=','拖動 BAR','不是預測','P05–P95','__ANNUAL__'):
            if token=="__ANNUAL__":
                continue
            self.assertIn(token,page)
        payload=page.split("const D=",1)[1].split(",A=",1)[0]
        annual_payload=page.split("const D=",1)[1].split(",A=",1)[1].split(",HIST=",1)[0]
        histogram_payload=page.split(",HIST=",1)[1].split(",COHORT=",1)[0]
        cohort_payload=page.split(",COHORT=",1)[1].split(",TG=",1)[0]
        self.assertEqual(len(json.loads(payload)),768)
        self.assertEqual(len(json.loads(annual_payload)),8448)
        self.assertEqual(len(json.loads(histogram_payload)),768*len(HISTOGRAM_METRICS))
        self.assertEqual(len(json.loads(cohort_payload)),768*2)
        self.assertNotIn("__DATA__",page)
        self.assertNotIn("__ANNUAL__",page)
        self.assertNotIn("__HIST__",page)
        self.assertNotIn("__COHORT__",page)
        markup=MarkupIDAudit()
        markup.feed(page)
        self.assertFalse(markup.duplicates, f"duplicate element IDs: {sorted(markup.duplicates)}")
        self.assertEqual(markup.id_to_tag.get("year"),"input", "year BAR must parse as a real range input")
        self.assertEqual(markup.id_to_tag.get("heatMetric"),"select", "heatmap metric selector must parse as a real select")
        self.assertEqual(markup.id_to_tag.get("histMetric"),"select", "distribution selector must parse as a real select")
        self.assertEqual(markup.id_to_tag.get("cohortMetric"),"select", "start-cohort metric selector must parse as a real select")
        self.assertEqual(markup.id_to_tag.get("fan"),"div")
        self.assertEqual(markup.id_to_tag.get("drawdownPath"),"div")
        self.assertEqual(markup.id_to_tag.get("heatmap"),"div")
        self.assertEqual(markup.id_to_tag.get("histogram"),"div")
        self.assertEqual(markup.id_to_tag.get("cohort"),"div")
        self.assertEqual(markup.id_to_tag.get("cohortDetail"),"div")
        self.assertEqual(markup.id_to_tag.get("exportMatrix"),"button")
        self.assertEqual(markup.id_to_tag.get("exportAnnual"),"button")

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
        self.assertIn('function histogram(s)',page_template)
        self.assertIn('HIST.find(',page_template)
        self.assertIn('function cohortChart(s)',page_template)
        self.assertIn('windows_below_initial_capital',page_template)
        self.assertIn('低於起始本金窗口',page_template)
        self.assertIn('COHORT.filter(',page_template)
        self.assertIn('def build_cohort_profiles(',page_template)
        self.assertIn('function build_window_histograms(',page_template)
        self.assertIn('function summarize_histogram(',page_template)
        self.assertIn('cashflow_mode===s.flow',page_template)
        self.assertIn('data-year="'+"'"+'+y+',page_template)

if __name__=="__main__":
    unittest.main()
