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
for (const timing of ["front_fast", "front_loaded", "linear", "mid_loaded", "back_loaded", "back_late"]) {
  assert(html.includes('value="' + timing + '"'), "missing selectable timing option: " + timing);
}
for (const token of ["__DATA__", "__ANNUAL__"]) assert(!html.includes(token), "unexpanded data placeholder " + token);

const defaults = {bond:"AGG", timing:"linear", flow:"no_withdrawals", target:"60", year:"5", heatMetric:"median_nav_usd"};
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
const initialMetrics = getElementById("metrics").innerHTML;
const initialValues = metricValues(initialMetrics);
assert(initialMetrics.includes("第5年中位資產"), "initial metrics should identify year 5");
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
assert(getElementById("shares").innerHTML.includes("46.0%"), "year 9 at 60% linear target should show 46% stock target");
assert(getElementById("shares").innerHTML.includes("54.0%"), "year 9 at 60% linear target should show 54% bond target");

year.value = "10";
fire("year");
const year10Values = metricValues(getElementById("metrics").innerHTML);
assert.notStrictEqual(year10Values[0], year9Values[0], "year 10 and year 9 should use different historical NAV summaries");
assert(getElementById("shares").innerHTML.includes("40.0%"), "year 10 should show 40% stocks for a 60% target");
assert(getElementById("shares").innerHTML.includes("60.0%"), "year 10 should show 60% bonds for a 60% target");

target.value = "80";
timing.value = "back_late";
year.value = "9";
fire("year");
assert(getElementById("shares").innerHTML.includes("53.3%"), "year 9 late conversion should show 53.3% bonds for an 80% target");
assert(getElementById("shares").innerHTML.includes("46.7%"), "year 9 late conversion should show 46.7% stocks for an 80% target");
assert((getElementById("fan").innerHTML.match(/data-year=/g) || []).length === 11, "fan chart should expose all 11 historical-year selection points");
assert(getElementById("fan").innerHTML.includes("P05") && getElementById("fan").innerHTML.includes("P95"), "fan chart must expose historical quantiles");
assert((getElementById("drawdownPath").innerHTML.match(/data-year=/g) || []).length === 11, "underwater path should expose all 11 year points");
assert((getElementById("heatmap").innerHTML.match(/data-target=/g) || []).length === 48, "heatmap should include all 8 targets x 6 timing rules");
const heatMetric = getElementById("heatMetric");
heatMetric.value = "windows_with_withdrawal_shortfall";
fire("heatMetric");
assert(getElementById("heatmap").innerHTML.includes("提款缺口窗口"), "heatmap metric selector should change the displayed metric");
flow.value = "monthly_withdrawal_1000_usd_stress";
fire("flow");
assert(getElementById("label").textContent.includes("每月$1,000"), "cash-flow selector should update the chosen scenario");
assert(getElementById("flows").innerHTML.includes("每月$1,000"), "cash-flow comparison should highlight the chosen mode");

const clickHandler = documentHandlers.click;
assert(clickHandler, "delegated chart-click listener must be installed");
const heatCell = {dataset:{bond:"IEF",target:"70",timing:"mid_loaded",year:"4"}};
clickHandler({target:{closest(selector) { return selector === "[data-target]" ? heatCell : null; }}});
assert.strictEqual(bond.value, "IEF", "heatmap selection should update bond proxy");
assert.strictEqual(target.value, "70", "heatmap selection should update target");
assert.strictEqual(timing.value, "mid_loaded", "heatmap selection should update timing");
assert.strictEqual(year.value, "4", "heatmap selection should update selected year");
assert(getElementById("label").textContent.includes("第4年"), "linked chart state should move to the selected year");
const point = {dataset:{bond:"TLT",target:"90",timing:"front_fast",flow:"monthly_withdrawal_1000_usd_stress"}};
clickHandler({target:{closest(selector) { return selector === "[data-target]" ? point : null; }}});
assert.strictEqual(bond.value, "TLT", "clicking a scatter point must update bond proxy");
assert.strictEqual(target.value, "90", "clicking a scatter point must update target percentage");
assert.strictEqual(timing.value, "front_fast", "clicking a scatter point must update timing rule");
assert(getElementById("label").textContent.includes("加速前置"), "scenario title must follow the clicked point");
const pickCount = (getElementById("frontier").innerHTML.match(/data-pick=/g) || []).length;
assert(pickCount > 0 && pickCount <= 48, "frontier should contain only the selected-year, selected-flow comparison");
getElementById("exportMatrix").listeners.click();
assert(downloads.at(-1).filename.includes("glidepath-year-4-matrix.csv"), "matrix export should reflect the selected year");
assert(downloads.at(-1).contents.split("\\r\\n").length === 49, "matrix export must include 48 strategy rows plus header");
getElementById("exportAnnual").listeners.click();
assert(downloads.at(-1).filename === "glidepath-all-annual-summaries.csv", "annual summary export name should be stable");
assert(downloads.at(-1).contents.split("\\r\\n").length === 8449, "annual export must include 8,448 records plus header");

console.log(JSON.stringify({
  status:"PASS",
  annualYearSwitches:[5,9,10],
  timingsTested:["linear","back_late","front_fast"],
  flowModeTested:"monthly_withdrawal_1000_usd_stress",
  clickSelectTested:true,
  interactiveFrontierPoints:pickCount,
  historicalFanPoints:11,
  underwaterPoints:11,
  heatmapCells:48,
  csvExports:downloads.map(x=>({filename:x.filename,rows:x.contents.split("\\r\\n").length-1})),
  dashboardBytes:Buffer.byteLength(html),
}, null, 2));
