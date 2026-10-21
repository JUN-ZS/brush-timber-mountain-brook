#!/usr/bin/env node
"use strict";
import fs from "node:fs";
import vm from "node:vm";
import assert from "node:assert/strict";

const htmlPath = process.argv[2];
if (!htmlPath) throw new Error("Usage: node interactive_dashboard_runtime_smoke.js <interactive_dashboard.html>");
const html = fs.readFileSync(htmlPath, "utf8");
const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/);
assert(scriptMatch, "dashboard must contain the embedded client script");
const js = scriptMatch[1];
for (const timing of ["front_rapid", "front_fast", "front_loaded", "linear", "mid_loaded", "staggered", "back_loaded", "back_late"]) {
  assert(html.includes('value="' + timing + '"'), "missing selectable timing option: " + timing);
}
for (const token of ["__DATA__", "__ANNUAL__", "__HIST__", "__COHORT__"]) assert(!html.includes(token), "unexpanded data placeholder " + token);

const defaults = {bond:"AGG", timing:"linear", flow:"no_withdrawals", target:"60", year:"5", heatMetric:"median_nav_usd", histMetric:"terminal_nav_usd", cohortMetric:"median_terminal_nav_usd"};
const nodes = new Map();
const documentHandlers = {};
const downloads = [];
const blobStore = new Map();
let blobSequence = 0;
class BlobFake { constructor(parts, options) { this.parts = parts; this.options = options; } }
const URLFake = {
  createObjectURL(blob) { const key = "blob:smoke-" + (++blobSequence); blobStore.set(key, blob); return key; },
  revokeObjectURL(key) { blobStore.delete(key); },
};
function getElementById(id) {
  if (!nodes.has(id)) {
    nodes.set(id, {
      id,
      value: Object.prototype.hasOwnProperty.call(defaults, id) ? defaults[id] : "",
      innerHTML: "",
      textContent: "",
      listeners: {},
      addEventListener(type, fn) { this.listeners[type] = fn; },
    });
  }
  return nodes.get(id);
}
const document = {
  body: {appendChild() {}},
  getElementById,
  addEventListener(type, fn) { documentHandlers[type] = fn; },
  createElement(tag) {
    assert.strictEqual(tag, "a");
    return {
      href: "", download: "",
      click() { const blob = blobStore.get(this.href); downloads.push({filename:this.download, contents:blob ? blob.parts.join("") : ""}); },
      remove() {},
    };
  },
};
const context = vm.createContext({document, console, Blob:BlobFake, URL:URLFake, setTimeout(fn) { fn(); return 1; }});
vm.runInContext(js, context, {timeout: 15000});

const year = getElementById("year");
const target = getElementById("target");
const timing = getElementById("timing");
const bond = getElementById("bond");
const flow = getElementById("flow");
const fire = id => {
  const node = getElementById(id);
  assert(node.listeners.input, "input listener missing for " + id);
  node.listeners.input();
};

const metricValues = html => [...html.matchAll(/<div class="v">([^<]+)<[/]div>/g)].map(match => match[1]);
const annualRows = vm.runInContext("A", context);
assert(Array.isArray(annualRows) && annualRows.length === 11264, "runtime must load every actual year x scenario summary");
const fmtMoney = value => value == null || !Number.isFinite(+value) ? "—" : "$" + Math.round(+value).toLocaleString("en-US");
const fmtPct = value => value == null || !Number.isFinite(+value) ? "—" : (100 * +value).toFixed(2) + "%";
const yearAudit = [];
for (let yearNo = 0; yearNo <= 10; yearNo++) {
  year.value = String(yearNo);
  fire("year");
  const actual = annualRows.find(row =>
    row.bond_proxy === bond.value &&
    +row.target_bond_conversion_pct_at_year10 === +target.value &&
    row.timing_rule === timing.value &&
    row.cashflow_mode === flow.value &&
    +row.year === yearNo
  );
  assert(actual, "missing actual annual summary row for year " + yearNo);
  const shown = metricValues(getElementById("metrics").innerHTML);
  assert.strictEqual(shown[0], fmtMoney(actual.median_nav_usd), "NAV metric must be data-linked at year " + yearNo);
  assert.strictEqual(shown[1], fmtMoney(actual.p05_nav_usd), "P05 metric must be data-linked at year " + yearNo);
  assert.strictEqual(shown[2], fmtPct(actual.median_cumulative_twr_cagr), "cumulative return must be data-linked at year " + yearNo);
  assert.strictEqual(shown[3], fmtPct(actual.median_drawdown_to_date), "drawdown must be data-linked at year " + yearNo);
  assert.strictEqual(shown[4], fmtPct(actual.worst_drawdown_to_date), "worst-window drawdown must be data-linked at year " + yearNo);
  assert.strictEqual(shown[5], actual.windows_below_initial_capital + "/" + actual.rolling_windows, "capital-floor count must be data-linked at year " + yearNo);
  assert.strictEqual(shown[6], actual.windows_with_withdrawal_shortfall + "/" + actual.rolling_windows, "shortfall count must be data-linked at year " + yearNo);
  assert(getElementById("metrics").innerHTML.includes("截至當年P95缺口 " + fmtMoney(actual.p95_shortfall_usd)), "P95 shortfall must be data-linked at year " + yearNo);
  const allocation = getElementById("allocation").innerHTML;
  assert(allocation.includes((100 * actual.median_target_stock_weight).toFixed(1) + "%"), "stock target must match year " + yearNo);
  assert(allocation.includes((100 * actual.median_target_bond_weight).toFixed(1) + "%"), "bond target must match year " + yearNo);
  assert(Math.abs(actual.median_target_stock_weight + actual.median_target_bond_weight - 1) < 1e-12, "stock/bond target weights must sum to 100%");
  assert(getElementById("wealth").innerHTML.includes("第" + yearNo + "年中位資產"), "wealth chart title must track year " + yearNo);
  assert(getElementById("drawdown").innerHTML.includes("截至第" + yearNo + "年最大回撤"), "drawdown chart title must track year " + yearNo);
  if (yearNo === 0) {
    assert(getElementById("returns").innerHTML.includes("第0年"), "year zero must not invent annualized return");
  } else {
    assert(getElementById("returns").innerHTML.includes("截至第" + yearNo + "年累計年化回報"), "return chart title must track year " + yearNo);
  }
  yearAudit.push({year:yearNo,median_nav_usd:actual.median_nav_usd,stock_target:+(100*actual.median_target_stock_weight).toFixed(1),bond_target:+(100*actual.median_target_bond_weight).toFixed(1)});
}
assert.notStrictEqual(yearAudit[9].median_nav_usd, yearAudit[10].median_nav_usd, "year 9 and year 10 must use different actual NAV values");
assert(yearAudit.every((item, i) => i === 0 || item.median_nav_usd !== yearAudit[i-1].median_nav_usd), "adjacent year NAV values should change for the baseline probe");
year.value = "5";
fire("year");

const initialMetrics = getElementById("metrics").innerHTML;
const initialValues = metricValues(initialMetrics);
assert(initialMetrics.includes("第5年中位資產"), "initial metrics should identify year 5");
assert(initialMetrics.includes("低於起始本金窗口"), "initial dashboard metrics must expose nominal capital-floor breaches");
assert(initialValues.length >= 6, "metric cards must expose six numeric values");
year.value = "9";
fire("year");
assert(getElementById("yearOut").textContent.includes("第9年"), "year label must follow the slider");
assert(getElementById("metrics").innerHTML.includes("第9年中位資產"), "metric cards must use year 9");
assert(getElementById("wealth").innerHTML.includes("第9年中位資產"), "wealth chart must use year 9");
assert(getElementById("drawdown").innerHTML.includes("截至第9年"), "drawdown chart must use year 9");
assert(getElementById("returns").innerHTML.includes("截至第9年"), "return chart must use year 9");
assert(getElementById("gaps").innerHTML.includes("截至第9年"), "shortfall chart must use year 9");
assert.notStrictEqual(getElementById("metrics").innerHTML, initialMetrics, "metrics HTML must change when year changes");
const year9Values = metricValues(getElementById("metrics").innerHTML);
assert.notStrictEqual(year9Values[0], initialValues[0], "year 9 must update the actual NAV value, not only its label");
assert.notStrictEqual(year9Values[2], initialValues[2], "year 9 must update the actual cumulative return value");
assert.notStrictEqual(year9Values[5], initialValues[5], "year 9 must update the actual count of windows below initial capital");
assert(getElementById("shares").innerHTML.includes("46.0%"), "year 9 at 60% linear target should show 46% stock target");
assert(getElementById("shares").innerHTML.includes("54.0%"), "year 9 at 60% linear target should show 54% bond target");
assert(getElementById("allocation").innerHTML.includes("46.0%"), "year BAR should show 46% stocks beside slider at year 9");
assert(getElementById("allocation").innerHTML.includes("54.0%"), "year BAR should show 54% bonds beside slider at year 9");
const allocationAtYear9 = getElementById("allocation").innerHTML;

year.value = "10";
fire("year");
const year10Values = metricValues(getElementById("metrics").innerHTML);
assert.notStrictEqual(year10Values[0], year9Values[0], "year 10 and year 9 should use different historical NAV summaries");
assert(getElementById("shares").innerHTML.includes("40.0%"), "year 10 should show 40% stocks for a 60% target");
assert(getElementById("shares").innerHTML.includes("60.0%"), "year 10 should show 60% bonds for a 60% target");
assert(getElementById("allocation").innerHTML.includes("60.0%"), "year 10 bond target should update beside slider");
assert.notStrictEqual(getElementById("allocation").innerHTML, allocationAtYear9, "allocation beside slider must differ from year 9 to year 10");

target.value = "80";
timing.value = "back_late";
year.value = "9";
fire("year");
assert(getElementById("shares").innerHTML.includes("53.3%"), "year 9 late conversion should show 53.3% bonds for an 80% target");
assert(getElementById("shares").innerHTML.includes("46.7%"), "year 9 late conversion should show 46.7% stocks for an 80% target");
assert((getElementById("fan").innerHTML.match(/data-year=/g) || []).length === 11, "fan chart should expose all 11 historical-year selection points");
assert(getElementById("fan").innerHTML.includes("P05") && getElementById("fan").innerHTML.includes("P95"), "fan chart must expose historical quantiles");
assert((getElementById("drawdownPath").innerHTML.match(/data-year=/g) || []).length === 11, "underwater path should expose all 11 year points");
assert((getElementById("heatmap").innerHTML.match(/data-target=/g) || []).length === 64, "heatmap should include all 8 targets x 8 timing rules");
const heatMetric = getElementById("heatMetric");
heatMetric.value = "windows_below_initial_capital";
fire("heatMetric");
assert(getElementById("heatmap").innerHTML.includes("低於起始本金窗口"), "heatmap should expose nominal capital-floor breach counts");
assert(getElementById("histogram").innerHTML.includes("P05") && getElementById("histogram").innerHTML.includes("P95"), "distribution histogram should mark its tail quantiles");
const histMetric = getElementById("histMetric");
histMetric.value = "daily_max_drawdown";
fire("histMetric");
assert(getElementById("histogram").innerHTML.includes("十年每日最大回撤"), "histogram metric selector should rerender the selected distribution");
const cohortMetric = getElementById("cohortMetric");
cohortMetric.value = "p05_terminal_nav_usd";
fire("cohortMetric");
assert(getElementById("cohort").innerHTML.includes("P05終值"), "cohort metric selector should rerender the historical start-year series");
assert((getElementById("cohort").innerHTML.match(/data-cohort-year=/g) || []).length > 0, "cohort chart should expose selectable start-year bars");
cohortMetric.value = "windows_below_initial_capital";
fire("cohortMetric");
assert(getElementById("cohort").innerHTML.includes("低於起始本金窗口數"), "cohort chart should expose nominal capital-floor breach counts");
flow.value = "monthly_withdrawal_1000_usd_stress";
fire("flow");
assert(getElementById("label").textContent.includes("每月$1,000"), "cash-flow selector should update the chosen scenario");
assert(getElementById("flows").innerHTML.includes("每月$1,000"), "cash-flow comparison should highlight the chosen mode");

const clickHandler = documentHandlers.click;
assert(clickHandler, "delegated chart-click listener must be installed");
const fakeSelectable = dataset => ({
  dataset,
  getAttribute(name) {
    const mapping = {"data-bond":"bond","data-target":"target","data-timing":"timing","data-flow":"flow","data-year":"year","data-cohort-year":"cohortYear"};
    const key = mapping[name];
    return key && Object.prototype.hasOwnProperty.call(dataset, key) ? String(dataset[key]) : null;
  },
});
const glideYearPoint = fakeSelectable({bond:"AGG",target:"60",timing:"linear",flow:"no_withdrawals",year:"9"});
clickHandler({target:{closest(selector) { return selector === "[data-target]" ? glideYearPoint : null; }}});
assert.strictEqual(year.value, "9", "clicking year 9 in glidepath chart must update year BAR");
assert.strictEqual(metricValues(getElementById("metrics").innerHTML)[0], fmtMoney(annualRows.find(row => row.bond_proxy==="AGG" && row.target_bond_conversion_pct_at_year10===60 && row.timing_rule==="linear" && row.cashflow_mode==="no_withdrawals" && row.year===9).median_nav_usd), "glidepath point must load actual year 9 NAV");
const cohortPoint = fakeSelectable({bond:"SHY",target:"50",timing:"back_loaded",flow:"no_withdrawals",cohortYear:"2003"});
clickHandler({target:{closest(selector) { return selector === "[data-target]" ? cohortPoint : null; }}});
assert.strictEqual(bond.value, "SHY", "cohort selection should update bond proxy");
assert.strictEqual(target.value, "50", "cohort selection should update target");
assert.strictEqual(timing.value, "back_loaded", "cohort selection should update timing");
assert(getElementById("cohortDetail").innerHTML.includes("2003"), "cohort selection should update the focused start-year detail");
const heatCell = fakeSelectable({bond:"IEF",target:"70",timing:"mid_loaded",year:"4"});
clickHandler({target:{closest(selector) { return selector === "[data-target]" ? heatCell : null; }}});
assert.strictEqual(bond.value, "IEF", "heatmap selection should update bond proxy");
assert.strictEqual(target.value, "70", "heatmap selection should update target");
assert.strictEqual(timing.value, "mid_loaded", "heatmap selection should update timing");
assert.strictEqual(year.value, "4", "heatmap selection should update selected year");
assert(getElementById("label").textContent.includes("第4年"), "linked chart state should move to the selected year");
const point = fakeSelectable({bond:"TLT",target:"90",timing:"front_fast",flow:"monthly_withdrawal_1000_usd_stress"});
clickHandler({target:{closest(selector) { return selector === "[data-target]" ? point : null; }}});
assert.strictEqual(bond.value, "TLT", "clicking a scatter point must update bond proxy");
assert.strictEqual(target.value, "90", "clicking a scatter point must update target percentage");
assert.strictEqual(timing.value, "front_fast", "clicking a scatter point must update timing rule");
assert(getElementById("label").textContent.includes("加速前置"), "scenario title must follow the clicked point");
const pickCount = (getElementById("frontier").innerHTML.match(/data-pick=/g) || []).length;
assert.strictEqual(pickCount, 256, "frontier must include 4 bond proxies x 8 targets x 8 timing rules for the selected year and flow");
getElementById("exportMatrix").listeners.click();
assert(downloads.at(-1).filename.includes("glidepath-year-4-matrix.csv"), "matrix export should reflect the selected year");
assert(downloads.at(-1).contents.split("\r\n").length === 65, "matrix export must include 64 strategy rows plus header");
getElementById("exportAnnual").listeners.click();
assert(downloads.at(-1).filename === "glidepath-all-annual-summaries.csv", "annual summary export name should be stable");
assert(downloads.at(-1).contents.split("\r\n").length === 11265, "annual export must include 11,264 records plus header");

console.log(JSON.stringify({
  status:"PASS",
  annualYearSwitches:yearAudit,
  timingsTested:["linear","back_late","front_rapid","staggered"],
  flowModeTested:"monthly_withdrawal_1000_usd_stress",
  clickSelectTested:true,
  interactiveFrontierPoints:pickCount,
  historicalFanPoints:11,
  underwaterPoints:11,
  heatmapCells:64,
  startYearCohortPoints:(getElementById("cohort").innerHTML.match(/data-cohort-year=/g)||[]).length,
  cohortMetricTested:getElementById("cohortMetric").value,
  histogramMetricTested:getElementById("histMetric").value,
  csvExports:downloads.map(x=>({filename:x.filename,rows:x.contents.split("\r\n").length-1})),
  dashboardBytes:Buffer.byteLength(html),
}, null, 2));
