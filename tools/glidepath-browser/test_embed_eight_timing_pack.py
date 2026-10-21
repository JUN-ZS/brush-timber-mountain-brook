from __future__ import annotations

import copy
import importlib.util
import json
import re
from pathlib import Path
import unittest

SCRIPT = Path(__file__).with_name("embed-eight-timing-pack.py")
SPEC = importlib.util.spec_from_file_location("embed_eight_timing_pack", SCRIPT)
assert SPEC and SPEC.loader
PACKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PACKER)

YEARS = list(range(2003, 2017))
COHORT_COUNTS = {year: (4 if year == 2003 else 9 if year == 2016 else 12) for year in YEARS}
BOND_WEIGHT_PATHS = {
    "front_rapid": (0, .50, .56, .62, .67, .72, .77, .82, .87, .93, 1),
    "front_fast": (0, .25, .50, .56, .62, .68, .73, .79, .85, .92, 1),
    "front_loaded": (0, .166667, .333333, .50, .555556, .611111, .666667, .722222, .777778, .888889, 1),
    "linear": (0, .1, .2, .3, .4, .5, .6, .7, .8, .9, 1),
    "mid_loaded": (0, .03, .10, .22, .38, .58, .76, .90, .97, .995, 1),
    "staggered": (0, .125, .25, .333333, .416667, .50, .583333, .666667, .75, .875, 1),
    "back_loaded": (0, 0, 0, 0, 0, 0, .2, .4, .6, .8, 1),
    "back_late": (0, 0, 0, 0, 0, 0, 0, 0, 1/3, 2/3, 1),
}

def _scenario_key(bond, target, timing, flow):
    return (bond, target, timing, flow)

def make_fixture():
    scenarios = []
    annual = []
    hist = []
    cohorts = []
    timings = list(PACKER.TIMINGS)
    flows = list(PACKER.FLOWS)
    for bi, bond in enumerate(PACKER.BONDS):
        for target in PACKER.TARGETS:
            for mi, timing in enumerate(timings):
                for fi, flow in enumerate(flows):
                    terminal = 150000 + bi*1000 + target*10 + mi*100 + fi*25
                    cagr = .04 + target/10000 + mi/1000
                    dd = -.12 - mi/100 - bi/1000
                    shortfall = 0 if fi < 2 else fi + mi
                    scenario = {
                        "bond_proxy": bond,
                        "target_bond_conversion_pct_at_year10": target,
                        "timing_rule": timing,
                        "cashflow_mode": flow,
                        "rolling_windows": 157,
                        "median_terminal_nav_usd": terminal,
                        "p05_terminal_nav_usd": terminal*.8,
                        "p95_terminal_nav_usd": terminal*1.2,
                        "worst_terminal_nav_usd": terminal*.7,
                        "median_time_weighted_cagr": cagr,
                        "p05_time_weighted_cagr": cagr-.03,
                        "worst_time_weighted_cagr": cagr-.08,
                        "median_daily_max_drawdown": dd,
                        "worst_daily_max_drawdown": dd-.2,
                        "windows_below_initial_capital_at_year10": 3,
                        "windows_with_withdrawal_shortfall": shortfall,
                        "median_actual_withdrawals_usd": 0 if fi == 0 else 1000,
                        "p95_withdrawal_shortfall_usd": 0 if fi < 2 else 2500,
                        "median_investor_xirr": None if fi > 1 else cagr,
                    }
                    scenarios.append(scenario)
                    for year in range(11):
                        bond_w = target/100 * BOND_WEIGHT_PATHS[timing][year]
                        year10 = year == 10
                        year0 = year == 0
                        annual.append({
                            "year": year,
                            "bond_proxy": bond,
                            "target_bond_conversion_pct_at_year10": target,
                            "timing_rule": timing,
                            "cashflow_mode": flow,
                            "rolling_windows": 157,
                            "median_nav_usd": 100000 if year0 else (terminal if year10 else 100000 + 1500*year),
                            "p05_nav_usd": 100000 if year0 else (terminal*.8 if year10 else 90000 + year*1000),
                            "p95_nav_usd": 100000 if year0 else (terminal*1.2 if year10 else 110000 + year*2000),
                            "worst_nav_usd": 100000 if year0 else (terminal*.7 if year10 else 80000 + year*500),
                            "median_cumulative_twr_cagr": None if year0 else (cagr if year10 else cagr*year/10),
                            "p05_cumulative_twr_cagr": None if year0 else cagr*year/10-.03,
                            "median_year_twr": None if year0 else .04,
                            "p05_year_twr": None if year0 else -.12,
                            "median_drawdown_to_date": 0 if year0 else (dd if year10 else dd/2),
                            "worst_drawdown_to_date": 0 if year0 else dd-.2,
                            "windows_below_initial_capital": 0 if year0 else (3 if year10 else 2),
                            "windows_with_withdrawal_shortfall": 0 if year0 else shortfall,
                            "median_actual_withdrawals_usd": 0 if year0 or fi == 0 else year*100,
                            "median_shortfall_usd": 0 if fi < 2 else year*20,
                            "p95_shortfall_usd": 0 if fi < 2 else year*250,
                            "median_target_bond_weight": bond_w,
                            "median_target_stock_weight": 1-bond_w,
                        })
                    for metric in PACKER.METRICS:
                        hist.append({
                            "bond_proxy": bond,
                            "target_bond_conversion_pct_at_year10": target,
                            "timing_rule": timing,
                            "cashflow_mode": flow,
                            "metric": metric,
                            "n": 157,
                            "min": -1.0 if metric != "terminal_nav_usd" else 100000,
                            "max": 1.0 if metric != "terminal_nav_usd" else 200000,
                            "p05": -0.8 if metric != "terminal_nav_usd" else 110000,
                            "median": 0.0 if metric != "terminal_nav_usd" else 150000,
                            "p95": .8 if metric != "terminal_nav_usd" else 190000,
                            "bins": [
                                {"low": -1.0 if metric != "terminal_nav_usd" else 100000,
                                 "high": 0.0 if metric != "terminal_nav_usd" else 150000, "count": 78},
                                {"low": 0.0 if metric != "terminal_nav_usd" else 150000,
                                 "high": 1.0 if metric != "terminal_nav_usd" else 200000, "count": 79},
                            ],
                        })
                    for year in YEARS:
                        count = COHORT_COUNTS[year]
                        first = f"{year}-09-30" if year == 2003 else f"{year}-01-31" if year != 2016 else "2016-01-29"
                        last = f"{year}-12-31" if year != 2016 else "2016-09-30"
                        cohorts.append({
                            "bond_proxy": bond,
                            "target_bond_conversion_pct_at_year10": target,
                            "timing_rule": timing,
                            "cashflow_mode": flow,
                            "start_year": year,
                            "window_count": count,
                            "first_window_start": first,
                            "last_window_start": last,
                            "median_terminal_nav_usd": terminal,
                            "p05_terminal_nav_usd": terminal*.8,
                            "p95_terminal_nav_usd": terminal*1.2,
                            "worst_terminal_nav_usd": terminal*.7,
                            "median_time_weighted_cagr": cagr,
                            "p05_time_weighted_cagr": cagr-.03,
                            "worst_time_weighted_cagr": cagr-.08,
                            "median_daily_max_drawdown": dd,
                            "worst_daily_max_drawdown": dd-.2,
                            "windows_with_withdrawal_shortfall": shortfall,
                            "initial_capital_usd": 100000,
                            "windows_below_initial_capital": 2,
                        })
    report = {
        "schema": PACKER.EXPECTED_SCHEMA,
        "method": {"rolling_windows_per_scenario": 157, "initial_capital_usd": 100000,
                   "timing_rules": {timing: timing for timing in timings}},
        "data": {"last_common_date": "2026-09-30",
                 "raw_panel_canonical_sha256": "a"*64,
                 "daily_common_observations": 5788,
                 "common_month_end_observations": 277},
        "scenarios": scenarios,
        "annual_scenarios": annual,
    }
    hist_report = {"schema":"stock-bond-glidepath-window-distributions.v1",
                   "rolling_windows_per_scenario":157, "metric_names":list(PACKER.METRICS),
                   "distributions":hist}
    cohort_report = {"schema":"stock-bond-glidepath-start-cohorts.v1",
                     "rolling_windows_per_scenario":157,"cohorts":cohorts}
    return report, hist_report, cohort_report

def make_ledger_fixture(report):
    counts=[]
    for row in report["annual_scenarios"]:
        year=int(row["year"])
        bond_index=PACKER.BONDS.index(row["bond_proxy"])
        target=int(row["target_bond_conversion_pct_at_year10"])
        timing_index=PACKER.TIMINGS.index(row["timing_rule"])
        flow_index=PACKER.FLOWS.index(row["cashflow_mode"])
        count235=0 if year==0 else (target+timing_index+flow_index+year)%158
        count350=0 if year==0 else (target+2*timing_index+flow_index+year+1)%158
        counts.append([year,bond_index,target,timing_index,flow_index,count235,count350])
    return {
        "schema":"glidepath-window-cashflow-ledger-replay.v1",
        "status":"PASS",
        "source_panel_sha256":report["data"]["raw_panel_canonical_sha256"],
        "source_as_of":"2026-09-30",
        "rolling_windows_per_scenario":157,
        "window_rows_expected":160768,
        "annual_summary_rows_expected":11264,
        "scenario_count":1024,
        "counters":{"window_rows_replayed":160768,"annual_rows_reconciled":11264,
                    "scenario_summaries_reconciled":1024,"real_floor_annual_rows":11264},
        "real_floor_annual_count_rates":[0.0235,0.035],
        "real_floor_annual_counts":counts
    }

def minimal_html():
    return '''<!doctype html><html><body>
<span class="badge ok">✓ 768 組策略 · 8,448 筆年度摘要</span>
<p>拖動查看年份 BAR 或直接點擊圖上第 0–10 年圓點，比較六條轉換曲線在各年度的目標轉債路徑。</p>
<p>固定目標轉債比例，逐行比較六種轉換時間規則。</p>
<p>目標 × 6 規則（共 48 格）</p><p>共 192 點＝4 種債券 × 8 目標 × 6 規則</p>
<div class="legend">○ 線性　□ 加速前置　△ 前置　◇ 中段S曲線　▽ 後置　＋ 延後</div>
<p>本預覽保留 768 組策略、8,448 筆年度摘要、3,072 組分布與 10,752 筆起始年份分組。</p>
<code>8d34a8772fd5c74a7df20957cab971c3c2685963e54b160c3c958c8b9d4b7e70</code>
<select id="timing"><option value="front_fast">old</option></select>
<script>
const RAW_PACK={"cm":{},"d":[],"a":[],"h":[],"c":[]};
const TG=[30],TM=["front_fast"],FL=["no_withdrawals"],BM=["AGG"],MM=["terminal_nav_usd"];
const TN={front_fast:"加速前置"},FN={no_withdrawals:"不提款"},C={front_fast:"#c94c4c"};
const dash={front_fast:"1 3",front_loaded:"6 4",linear:"",mid_loaded:"6 2 1 2",back_loaded:"2 4",back_late:"10 3"};
function scatter() {
let shape=r.timing_rule,mark;
    if(shape==="front_fast")mark='<rect x="'+(x-3.5).toFixed(1)+'" y="'+(y-3.5).toFixed(1)+'" width="7" height="7"';
    else if(shape==="front_loaded")mark='<polygon points="'+x.toFixed(1)+','+(y-4.5).toFixed(1)+' '+(x-4.5).toFixed(1)+','+(y+3.5).toFixed(1)+' '+(x+4.5).toFixed(1)+','+(y+3.5).toFixed(1)+'"';
    else if(shape==="linear")mark='<circle cx="'+x.toFixed(1)+'" cy="'+y.toFixed(1)+'" r="'+(sel?5.2:3.3)+'"';
    else if(shape==="mid_loaded")mark='<polygon points="'+x.toFixed(1)+','+(y-5).toFixed(1)+' '+(x-5).toFixed(1)+','+y.toFixed(1)+' '+x.toFixed(1)+','+(y+5).toFixed(1)+' '+(x+5).toFixed(1)+','+y.toFixed(1)+'"';
    else if(shape==="back_loaded")mark='<polygon points="'+(x-4.5).toFixed(1)+','+(y-3.5).toFixed(1)+' '+(x+4.5).toFixed(1)+','+(y-3.5).toFixed(1)+' '+x.toFixed(1)+','+(y+5).toFixed(1)+'"';
    else mark='<path d="M '+(x-4).toFixed(1)+' '+y.toFixed(1)+' H '+(x+4).toFixed(1)+' M '+x.toFixed(1)+' '+(y-4).toFixed(1)+' V '+(y+4).toFixed(1)+'" ';
    let close=shape==="front_fast"?"</rect>":shape==="front_loaded"||shape==="mid_loaded"||shape==="back_loaded"?"</polygon>":shape==="linear"?"</circle>":"</path>";
}
const dash=(m==="front_loaded"?"6 4":m==="back_loaded"?"2 4":"");
/* real-floor UI contract fragments:
median_target_bond_weight:bw,median_target_stock_weight:sw};
[s.cpi>0?"實質保本窗口（未精算）":"名目低於本金窗口",s.cpi>0?"不可精算":r.windows_below_initial_capital+"/"+r.rolling_windows,s.cpi>0?"缺少逐窗口 NAV，不把名目計數冒充實質計數；"+floorLabel:"名目 NAV 低於起始 $100,000 的歷史窗口數；不是未來機率"],
(s.cpi>0?'實質保本窗口（未精算）':'名目低於本金')
(s.cpi>0?'未精算（名目 '+v.windows_below_initial_capital+'/'+v.rolling_windows+'）':v.windows_below_initial_capital+'/'+v.rolling_windows)
      "年通脹 2.35% 時，768 組第10年策略中有 363 組可由最差窗口期末 NAV 證明「157 個歷史窗口均未跌破實質本金」；年通脹 3.50% 時是 329 組。這只代表第10年期末門檻，不代表途中不回撤或未來保本機率。" +
      " 其餘未獲零跌破證明的策略，不代表已知它們全部跌破；精確實質跌破窗口數尚未全部逐窗口精算，頁面會標「未精算」，不把名目數字假裝成實質風險。";
*/
</script></body></html>'''

class EightTimingPackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report, cls.hist, cls.cohort = make_fixture()
        cls.ledger = make_ledger_fixture(cls.report)

    def test_validates_and_packs_full_eight_timing_grid(self):
        pack = PACKER.validate_and_pack(self.report, self.hist, self.cohort, self.ledger)
        self.assertEqual(len(pack["d"]), 1024)
        self.assertEqual(len(pack["a"]), 11264)
        self.assertEqual(len(pack["h"]), 4096)
        self.assertEqual(len(pack["c"]), 14336)
        self.assertEqual(pack["meta"]["source_as_of"], "2026-09-30")
        self.assertEqual(pack["meta"]["source_sha256"], "a"*64)
        self.assertEqual(sum(meta[0] for meta in pack["cm"].values()), 157)
        self.assertEqual(pack["d"][0][0:4], [0, 30, 0, 0])
        self.assertEqual(pack["a"][0][0:5], [0, 0, 30, 0, 0])
        # The last annual row for the first scenario equals that scenario's terminal NAV.
        first_scenario_terminal = pack["d"][0][4]
        first_scenario_year10 = next(row for row in pack["a"] if row[:5] == [10, 0, 30, 0, 0])
        self.assertAlmostEqual(first_scenario_year10[5], first_scenario_terminal)
        self.assertEqual(first_scenario_year10[21], (30+0+0+10)%158)
        self.assertEqual(first_scenario_year10[22], (30+0+0+11)%158)

    def test_embeds_eight_selectable_timing_options_and_rewrites_copy(self):
        pack = PACKER.validate_and_pack(self.report, self.hist, self.cohort, self.ledger)
        html = PACKER.embed_pack(minimal_html(), pack)
        for timing in PACKER.TIMINGS:
            self.assertIn('value="' + timing + '"', html)
        self.assertIn("TM=[\"front_rapid\",\"front_fast\",\"front_loaded\",\"linear\",\"mid_loaded\",\"staggered\",\"back_loaded\",\"back_late\"]", html)
        self.assertIn("1,024 組策略", html)
        self.assertIn("11,264 筆年度摘要", html)
        self.assertIn("4,096 組分布", html)
        self.assertIn("14,336 筆起始年份分組", html)
        self.assertIn("八條轉換曲線", html)
        self.assertIn("八種轉換時間規則", html)
        self.assertIn("共 256 點", html)
        self.assertIn("windows_below_real_principal_235:r[21]", html)
        self.assertIn("低於實質本金窗口", html)
        self.assertIn("逐窗口核算確認", html)
        for timing in PACKER.TIMINGS:
            self.assertRegex(html, r'const dash=\{[^{}]*\b' + re.escape(timing) + r'\s*:')
        self.assertNotIn('stroke-dasharray="undefined"', html)
        # Running the embedder on its own output must be deterministic and safe.
        repacked_html = PACKER.embed_pack(html, pack)
        self.assertNotIn('stroke-dasharray="undefined"', repacked_html)
        for timing in PACKER.TIMINGS:
            self.assertRegex(repacked_html, r'const dash=\{[^{}]*\b' + re.escape(timing) + r'\s*:')
        packed = json.loads(repacked_html.split("const RAW_PACK=", 1)[1].split(";\nconst TG=", 1)[0])
        self.assertEqual(len(packed["d"]), 1024)

    def test_rejects_incomplete_scenario_grid(self):
        report, hist, cohort = make_fixture()
        report["scenarios"].pop()
        with self.assertRaisesRegex(ValueError, "1,024"):
            PACKER.validate_and_pack(report, hist, cohort, make_ledger_fixture(report))

    def test_rejects_no_withdrawal_cashflow_leakage(self):
        report, hist, cohort = make_fixture()
        row = next(item for item in report["annual_scenarios"]
                   if item["cashflow_mode"] == "no_withdrawals" and item["year"] == 5)
        row["median_actual_withdrawals_usd"] = 25
        with self.assertRaisesRegex(ValueError, "No-withdrawal mode"):
            PACKER.validate_and_pack(report, hist, cohort, make_ledger_fixture(report))

    def test_rejects_year_zero_nav_or_cashflow_that_is_not_at_starting_state(self):
        report, hist, cohort = make_fixture()
        row = next(item for item in report["annual_scenarios"]
                   if item["cashflow_mode"] == "monthly_withdrawal_500_usd_stress"
                   and item["year"] == 0)
        row["p05_nav_usd"] = 99000
        with self.assertRaisesRegex(ValueError, "Year-zero p05_nav_usd"):
            PACKER.validate_and_pack(report, hist, cohort, make_ledger_fixture(report))

    def test_rejects_cashflow_mode_that_changes_target_allocation_schedule(self):
        report, hist, cohort = make_fixture()
        row = next(item for item in report["annual_scenarios"]
                   if item["bond_proxy"] == "AGG" and
                   item["target_bond_conversion_pct_at_year10"] == 30 and
                   item["timing_rule"] == "front_fast" and
                   item["cashflow_mode"] == "no_withdrawals" and
                   item["year"] == 5)
        row["median_target_bond_weight"] += 0.01
        row["median_target_stock_weight"] -= 0.01
        with self.assertRaisesRegex(ValueError, "allocation schedule"):
            PACKER.validate_and_pack(report, hist, cohort, make_ledger_fixture(report))

    def test_rejects_missing_real_principal_count_grid(self):
        report, hist, cohort = make_fixture()
        ledger = make_ledger_fixture(report)
        ledger["real_floor_annual_counts"].pop()
        with self.assertRaisesRegex(ValueError, "real-principal count grid"):
            PACKER.validate_and_pack(report, hist, cohort, ledger)

    def test_rejects_year_zero_real_principal_count_leakage(self):
        report, hist, cohort = make_fixture()
        ledger = make_ledger_fixture(report)
        ledger["real_floor_annual_counts"][0][5] = 1
        with self.assertRaisesRegex(ValueError, "Year-zero real-principal"):
            PACKER.validate_and_pack(report, hist, cohort, ledger)

    def test_rejects_histogram_bins_that_compact_format_would_distort(self):
        report, hist, cohort = make_fixture()
        hist["distributions"][0]["bins"][1]["low"] = 0.1
        with self.assertRaisesRegex(ValueError, "equal-width"):
            PACKER.validate_and_pack(report, hist, cohort, make_ledger_fixture(report))

if __name__ == "__main__":
    unittest.main()
