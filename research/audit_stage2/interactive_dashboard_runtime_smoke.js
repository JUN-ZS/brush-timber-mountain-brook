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

const defaults = {bond:"AGG", timing:"linear", flow:"no_withdrawals", target:"60", year:"5"};
const nodes = new Map();
const documentHandlers = {};
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
  getElementById,
  addEventListener(type, fn) { documentHandlers[type] = fn; },
};
const context = vm.createContext({document, console});
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
flow.value = "monthly_withdrawal_1000_usd_stress";
fire("flow");
assert(getElementById("label").textContent.includes("每月$1,000"), "cash-flow selector should update the chosen scenario");
assert(getElementById("flows").innerHTML.includes("每月$1,000"), "cash-flow comparison should highlight the chosen mode");

const clickHandler = documentHandlers.click;
assert(clickHandler, "delegated chart-click listener must be installed");
const point = {dataset:{bond:"TLT",target:"90",timing:"front_fast"}};
clickHandler({target:{closest(selector) { return selector === "[data-target]" ? point : null; }}});
assert.strictEqual(bond.value, "TLT", "clicking a scatter point must update bond proxy");
assert.strictEqual(target.value, "90", "clicking a scatter point must update target percentage");
assert.strictEqual(timing.value, "front_fast", "clicking a scatter point must update timing rule");
assert(getElementById("label").textContent.includes("加速前置"), "scenario title must follow the clicked point");
const pickCount = (getElementById("frontier").innerHTML.match(/data-pick=/g) || []).length;
assert(pickCount >= 100, "frontier should contain the complete year-specific no-flow comparison");

console.log(JSON.stringify({
  status:"PASS",
  annualYearSwitches:[5,9,10],
  timingsTested:["linear","back_late","front_fast"],
  flowModeTested:"monthly_withdrawal_1000_usd_stress",
  clickSelectTested:true,
  interactiveFrontierPoints:pickCount,
  dashboardBytes:Buffer.byteLength(html),
}, null, 2));
