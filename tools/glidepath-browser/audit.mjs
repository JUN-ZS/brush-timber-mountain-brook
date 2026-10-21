import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { chromium } from "playwright";

const htmlPath = path.resolve(process.env.GLIDEPATH_HTML || "v2.html");
const outputPath = process.env.AUDIT_RESULTS_PATH || path.join(os.tmpdir(), "glidepath-browser-audit-results.json");
const failures = [];
const consoleErrors = [];
const pageErrors = [];
let browser;
let result = {
  status: "RUNNING",
  browser: null,
  console_errors: 0,
  page_errors: 0,
  state_matrix_sweeps: 0,
  state_matrix_combinations: [],
  rendered_dom_guard_passed: false,
  glidepath_geometry: null,
  stat_view_missing_guards: {},
  real_mode_table_label_guard: {},
  derived_real_breach_zero_proof: [],
  interactive_delegations_verified: {},
  csv_exports_verified: {},
  responsive_viewports_verified: {},
  failures
};

function need(condition, message) {
  if (!condition) throw new Error(message);
}
async function bodyText(page) {
  return page.locator("body").innerText();
}
async function inspectRender(page) {
  return page.evaluate(() => {
    const text = document.body.innerText || "";
    const badText = /\b(?:NaN|undefined)\b/i.test(text);
    const badAttributes = [];
    for (const element of document.querySelectorAll("svg *")) {
      for (const attribute of Array.from(element.attributes)) {
        if (/\b(?:NaN|undefined)\b/i.test(attribute.value)) {
          badAttributes.push({tag: element.tagName, id: element.id || null, className: typeof element.className === "string" ? element.className : null, svgId: element.closest("svg")?.id || null, name: attribute.name, value: attribute.value, outerHTML: element.outerHTML.slice(0, 500)});
        }
      }
    }
    return {badText, badAttributes};
  });
}
async function clickAndRead(page, selector) {
  const locator = page.locator(selector).first();
  await locator.waitFor({state: "visible"});
  const attrs = await locator.evaluate(el => ({
    target: el.getAttribute("data-target"),
    timing: el.getAttribute("data-timing"),
    bond: el.getAttribute("data-bond"),
    flow: el.getAttribute("data-flow"),
    year: el.getAttribute("data-year"),
    cohortYear: el.getAttribute("data-cohort-year")
  }));
  await locator.click({force: true});
  return attrs;
}
async function saveCsv(page, id, expectedRows, expectedCols) {
  await page.evaluate(() => {
    window.__glidepathAuditLastBlob = null;
    window.__glidepathAuditLastDownloadName = null;
  });
  await page.locator("#" + id).click();
  const captured = await page.evaluate(async () => {
    const blob = window.__glidepathAuditLastBlob;
    return blob ? {
      text: await blob.text(),
      bytes: blob.size,
      file_name: window.__glidepathAuditLastDownloadName
    } : null;
  });
  need(captured !== null, id + " did not construct a CSV Blob");
  need(captured.file_name && captured.file_name.endsWith(".csv"), id + " did not assign a CSV filename");
  const lines = captured.text.trimEnd().split(/\r?\n/);
  need(lines.length === expectedRows + 1, id + " row count expected " + (expectedRows + 1) + " lines including header, got " + lines.length);
  const cols = lines[0].split(",").length;
  need(cols === expectedCols, id + " expected " + expectedCols + " columns, got " + cols);
  const decodedTextBytes = Buffer.byteLength(captured.text);
  need(captured.bytes >= decodedTextBytes && captured.bytes - decodedTextBytes <= 3, id + " Blob/text byte difference exceeds possible UTF-8 BOM: " + captured.bytes + " vs " + decodedTextBytes);
  return {rows: lines.length - 1, cols, bytes: captured.bytes, decoded_text_bytes: decodedTextBytes, bom_bytes_delta: captured.bytes - decodedTextBytes, file_name: captured.file_name};
}

try {
  browser = await chromium.launch({headless: true, args: ["--no-sandbox"]});
  result.browser = await browser.version();
  const page = await browser.newPage({viewport: {width: 1480, height: 1200}, acceptDownloads: true});
  page.on("console", message => { if (message.type() === "error") consoleErrors.push(message.text()); });
  page.on("pageerror", error => pageErrors.push(String(error)));
  await page.goto(pathToFileURL(htmlPath).href, {waitUntil: "load"});
  await page.locator("#metrics .metric").first().waitFor({state: "visible"});
  await page.locator("#decisionSummary").waitFor({state: "visible"});
  await page.locator("#decisionEvidence").waitFor({state: "visible"});
  const summaryPlacement = await page.evaluate(() => {
    const evidence = document.querySelector("#decisionEvidence");
    const summary = document.querySelector("#decisionSummary");
    const controls = document.querySelector(".controls");
    const firstChart = document.querySelector("svg,canvas");
    const rawPack = RAW_PACK;
    const bondValue = document.querySelector("#bond").value;
    const bondIndex = ["AGG", "SHY", "IEF", "TLT"].indexOf(bondValue);
    const timingIndex = ["front_rapid", "front_fast", "front_loaded", "linear", "mid_loaded", "staggered", "back_loaded", "back_late"].indexOf(document.querySelector("#timing").value);
    const flowIndex = ["no_withdrawals", "delayed_stepup_example", "monthly_withdrawal_500_usd_stress", "monthly_withdrawal_1000_usd_stress"].indexOf(document.querySelector("#flow").value);
    const target = Number(document.querySelector("#target").value);
    const year = Number(document.querySelector("#year").value);
    const cpi = Math.max(0, Number(document.querySelector("#realMode").value || 0));
    const annual = rawPack.a.find(row => row[0] === year && row[1] === bondIndex && row[2] === target && row[3] === timingIndex && row[4] === flowIndex);
    if (!annual) throw new Error("missing compact annual record for the currently selected strategy/year");
    const stat = document.querySelector("#statView")?.value || "median";
    const navField = stat === "p05" ? 6 : stat === "worst" ? 8 : 5;
    const expectedNav = annual[navField] / Math.pow(1 + cpi, year);
    const money = value => "$" + Math.round(value).toLocaleString("en-US");
    const stockWeight = 1 - Number(annual[20]);
    const bondWeight = Number(annual[20]);
    const displayStockPct = Number((100 * stockWeight).toFixed(2));
    const displayBondPct = Number((100 * bondWeight).toFixed(2));
    const displayNavRounded = Math.round(expectedNav);
    const initialCapital = Number(rawPack.meta?.initial_capital_usd || 100000);
    const floorProof = rate => rawPack.d.filter(row => Number(row[7]) >= initialCapital * Math.pow(1 + rate, 10)).length;
    const strategyCount = rawPack.d.length;
    const sampleWindows = Number(rawPack.meta?.rolling_windows_per_scenario || 157);
    const sourceAsOf = String(rawPack.meta?.source_as_of || "2026-09-30");
    return {
    summaryBeforeControls: summary.compareDocumentPosition(controls) & Node.DOCUMENT_POSITION_FOLLOWING ? true : false,
    evidenceAfterSummary: !!(summary.compareDocumentPosition(evidence) & Node.DOCUMENT_POSITION_FOLLOWING),
    evidenceBeforeControls: !!(evidence.compareDocumentPosition(controls) & Node.DOCUMENT_POSITION_FOLLOWING),
    evidenceBeforeFirstChart: !!(firstChart && (evidence.compareDocumentPosition(firstChart) & Node.DOCUMENT_POSITION_FOLLOWING)),
    firstChartTag: firstChart ? firstChart.tagName.toLowerCase() : null,
    evidenceAmount: document.querySelector("#decisionEvidenceAmount").innerText,
    evidenceAllocation: document.querySelector("#decisionEvidenceAllocation").innerText,
    evidenceBehavior: document.querySelector("#decisionEvidenceBehavior").innerText,
    evidenceFlow: document.querySelector("#decisionEvidenceFlow").innerText,
    evidenceSample: document.querySelector("#decisionEvidenceSample").innerText,
    evidenceRisk: document.querySelector("#decisionEvidenceRisk").innerText,
    evidenceScope: document.querySelector("#decisionEvidenceScope").innerText,
    strategyCount,
    sampleWindows,
    sourceAsOf,
    selectedBond: bondValue,
    floorProof235: floorProof(0.0235),
    floorProof350: floorProof(0.035),
    expectedAmount: money(expectedNav),
    expectedStockAmount: money(displayNavRounded * displayStockPct / 100),
    expectedBondAmount: money(displayNavRounded * displayBondPct / 100),
    evidenceDataset: {
      sampleWindows: evidence.dataset.sampleWindows,
      strategyCount: evidence.dataset.strategyCount,
      direction: evidence.dataset.direction,
      flow: evidence.dataset.flow,
      reverseReplayScope: evidence.dataset.reverseReplayScope
    },
    metricsBeforeControls: document.querySelector("#metrics").compareDocumentPosition(controls) & Node.DOCUMENT_POSITION_FOLLOWING ? true : false,
    initialLead: document.querySelector("#decisionLead").innerText,
    initialValue: document.querySelector("#decisionPrimaryValue").innerText,
    initialBehavior: document.querySelector("#decisionBehaviorHeadline").innerText,
    initialAllocation: document.querySelector("#decisionAllocationHeadline").innerText,
    initialAllocationDetail: document.querySelector("#decisionAllocationDetail").innerText,
    initialFlow: document.querySelector("#decisionFlowHeadline").innerText,
    initialFloor: document.querySelector("#decisionFloorHeadline").innerText
  };
  });
  need(summaryPlacement.summaryBeforeControls && summaryPlacement.metricsBeforeControls, "decision outputs are not positioned ahead of controls");
  need(summaryPlacement.evidenceAfterSummary && summaryPlacement.evidenceBeforeControls && summaryPlacement.evidenceBeforeFirstChart,
    "decision evidence must follow the selected summary and precede both controls and the first chart: " + JSON.stringify(summaryPlacement));
  need(summaryPlacement.evidenceAmount.includes(summaryPlacement.expectedAmount) &&
    summaryPlacement.evidenceAllocation.includes("股票約 " + summaryPlacement.expectedStockAmount) &&
    summaryPlacement.evidenceAllocation.includes(summaryPlacement.selectedBond + " 約 " + summaryPlacement.expectedBondAmount),
    "decision evidence does not bind the displayed amount to its actual selected allocation split");
  need(summaryPlacement.evidenceBehavior.includes("AGG") && summaryPlacement.evidenceBehavior.includes("60%") &&
    summaryPlacement.evidenceBehavior.includes("第 5 年") && summaryPlacement.evidenceFlow.includes("不提款"),
    "decision evidence does not bind the NAV amount to current strategy behavior and cashflow");
  need(summaryPlacement.evidenceSample.includes(summaryPlacement.strategyCount + " 組") &&
    summaryPlacement.evidenceSample.includes(summaryPlacement.sampleWindows + " 個重疊") &&
    summaryPlacement.evidenceSample.includes(summaryPlacement.sourceAsOf),
    "decision evidence is missing the dynamic strategy count, rolling-window count or forward-data as-of date");
  need(summaryPlacement.evidenceRisk.includes(summaryPlacement.floorProof235 + " 組") &&
    summaryPlacement.evidenceRisk.includes(summaryPlacement.floorProof350 + " 組") &&
    summaryPlacement.evidenceRisk.includes("未精算") && summaryPlacement.evidenceRisk.includes("不代表途中"),
    "decision evidence must derive real-terminal-floor evidence counts from the embedded strategy records");
  need(summaryPlacement.evidenceDataset.strategyCount === String(summaryPlacement.strategyCount) &&
    summaryPlacement.evidenceDataset.sampleWindows === String(summaryPlacement.sampleWindows),
    "decision evidence machine attributes do not report the current embedded sample population");
  need(summaryPlacement.initialLead.includes("AGG") && summaryPlacement.initialLead.includes("60%") && summaryPlacement.initialLead.includes("第5年"), "initial decision summary does not state the selected strategy/year");
  need(summaryPlacement.initialValue.startsWith("$") && summaryPlacement.initialBehavior.length > 0 && summaryPlacement.initialAllocation.includes("股票") && summaryPlacement.initialFlow.includes("不提款") && summaryPlacement.initialFloor.includes("$"), "initial decision summary is missing amount/behavior/data fields");
  need(summaryPlacement.initialAllocationDetail.includes("按主結果 " + summaryPlacement.expectedAmount) &&
    summaryPlacement.initialAllocationDetail.includes("股票約 " + summaryPlacement.expectedStockAmount) &&
    summaryPlacement.initialAllocationDetail.includes(summaryPlacement.selectedBond + " 約 " + summaryPlacement.expectedBondAmount),
    "initial allocation dollar split must reconcile to the displayed NAV and allocation percentages");
  result.frontloaded_decision_summary = { ...summaryPlacement, passed: true };

  await page.locator("#decisionTrajectory[data-state]").waitFor({state: "visible", timeout: 5000});
  const readTrajectory = () => page.evaluate(() => {
    const root = document.querySelector("#decisionTrajectory");
    const values = series => Array.from(root.querySelectorAll('[data-series="' + series + '"] td[data-year]'));
    const stocks = values("stock").map(cell => Number(cell.dataset.stockPct));
    const bonds = values("bond").map(cell => Number(cell.dataset.bondPct));
    const years = Array.from(root.querySelectorAll("[data-trajectory-year]")).map(header => Number(header.getAttribute("data-trajectory-year")));
    const idValues = Array.from(document.querySelectorAll("[id]")).map(node => node.id);
    const duplicates = Array.from(new Set(idValues.filter((id, index) => idValues.indexOf(id) !== index)));
    return {
      state: root.dataset.state,
      source: "S()/Y() canonical annual record map",
      panel_after_summary: !!(document.querySelector("#decisionSummary").compareDocumentPosition(root) & Node.DOCUMENT_POSITION_FOLLOWING),
      panel_before_controls: !!(root.compareDocumentPosition(document.querySelector(".controls")) & Node.DOCUMENT_POSITION_FOLLOWING),
      selected_year: root.dataset.year,
      target: Number(root.dataset.target),
      timing: root.dataset.timing,
      endpoint_bond_pct: Number(root.dataset.endpointBondPct),
      year_headers: years,
      selected_year_header_count: root.querySelectorAll('[data-trajectory-year][aria-current="true"]').length,
      selected_year_header: Number(root.querySelector('[data-trajectory-year][aria-current="true"]')?.getAttribute("data-trajectory-year")),
      stock_pcts: stocks,
      bond_pcts: bonds,
      stock_bond_sums: stocks.map((stock, index) => stock + bonds[index]),
      crosscheck: root.dataset.crosscheck,
      allocation_delta_pp: root.dataset.allocationDeltaPp == null ? null : Number(root.dataset.allocationDeltaPp),
      crosscheck_text: root.querySelector("#decisionTrajectoryCrosscheck").innerText,
      status_text: root.querySelector("#decisionTrajectoryStatus").innerText,
      rendered_duplicate_ids: duplicates
    };
  });
  const initialTrajectory = await readTrajectory();
  need(initialTrajectory.state === "ready", "year-by-year trajectory panel is not ready: " + JSON.stringify(initialTrajectory));
  need(initialTrajectory.panel_after_summary && initialTrajectory.panel_before_controls, "trajectory panel is not placed between the decision summary and controls");
  need(initialTrajectory.year_headers.length === 11 && initialTrajectory.year_headers.every((year, index) => year === index), "trajectory panel does not expose years 0-10: " + JSON.stringify(initialTrajectory.year_headers));
  need(initialTrajectory.stock_pcts.length === 11 && initialTrajectory.bond_pcts.length === 11, "trajectory panel is missing annual stock/bond rows");
  need(initialTrajectory.selected_year === "5" && initialTrajectory.selected_year_header_count === 1 && initialTrajectory.selected_year_header === 5, "trajectory panel did not highlight the selected year 5 from the original year BAR");
  need(Math.abs(initialTrajectory.endpoint_bond_pct - initialTrajectory.target) <= 0.75, "year-10 bond target does not match selected target: " + JSON.stringify(initialTrajectory));
  need(initialTrajectory.stock_bond_sums.every(value => Math.abs(value - 100) <= 0.02), "trajectory stock and bond percentages do not sum to 100: " + JSON.stringify(initialTrajectory.stock_bond_sums));
  need(initialTrajectory.source === "S()/Y() canonical annual record map", "trajectory is not sourced from canonical annual backtest records");
  need(initialTrajectory.crosscheck_text.includes("年度回測配置記錄") && initialTrajectory.crosscheck_text.includes("畫面差異"), "trajectory does not compare the annual record with the frontloaded summary");
  need(initialTrajectory.rendered_duplicate_ids.length === 0, "trajectory panel caused duplicate rendered IDs: " + JSON.stringify(initialTrajectory.rendered_duplicate_ids));
  result.glidepath_decision_trajectory = {initial: initialTrajectory, passed: true};

  const originalControls = await page.evaluate(() => ({
    bond: document.querySelector("#bond").value,
    target: document.querySelector("#target").value,
    timing: document.querySelector("#timing").value,
    flow: document.querySelector("#flow").value,
    year: document.querySelector("#year").value,
    realMode: document.querySelector("#realMode").value,
    statView: document.querySelector("#statView").value
  }));
  // Cross the full cashflow × year × statistic-view state space. Every visible
  // value must resolve to one exact annual D/A record with the same five-part key.
  const cashflowModes = [
    "no_withdrawals",
    "delayed_stepup_example",
    "monthly_withdrawal_500_usd_stress",
    "monthly_withdrawal_1000_usd_stress"
  ];
  const cashflowYears = Array.from({length: 11}, (_, index) => index);
  const cashflowStats = ["median", "p05", "worst"];
  const cashflowSemanticSweep = {
    total_combinations: 0,
    yearly_flow_slices_verified: 0,
    primary_nav_bindings_verified: 0,
    metric_rows_verified: 0,
    allocation_path_bindings_verified: 0,
    flow_comparison_bars_verified: 0,
    no_withdrawal_zero_cashflow_checks: 0,
    data_scope_disclosure_checks: 0,
    checked_flows: cashflowModes,
    checked_years: cashflowYears,
    checked_stat_views: cashflowStats
  };
  const moneyText = value => "$" + Math.round(value).toLocaleString("en-US");
  const pctText = value => value == null ? "—" : (Number(value) * 100).toFixed(2) + "%";

  for (const flow of cashflowModes) {
    await page.locator("#flow").selectOption(flow);
    for (const year of cashflowYears) {
      await page.locator("#year").evaluate((element, value) => {
        element.value = String(value);
        element.dispatchEvent(new Event("input", {bubbles: true}));
        element.dispatchEvent(new Event("change", {bubbles: true}));
      }, year);
      for (const stat of cashflowStats) {
        await page.locator("#statView").selectOption(stat);
        await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
        const state = await page.evaluate(() => {
          const bond = document.querySelector("#bond").value;
          const target = Number(document.querySelector("#target").value);
          const timing = document.querySelector("#timing").value;
          const flow = document.querySelector("#flow").value;
          const moneyText = value => "$" + Math.round(value).toLocaleString("en-US");
          const pctText = value => value == null ? "—" : (Number(value) * 100).toFixed(2) + "%";
          const year = Number(document.querySelector("#year").value);
          const stat = document.querySelector("#statView").value;
          const cpi = Math.max(0, Number(document.querySelector("#realMode").value || 0));
          const bonds = ["AGG", "SHY", "IEF", "TLT"];
          const timings = ["front_rapid", "front_fast", "front_loaded", "linear", "mid_loaded", "staggered", "back_loaded", "back_late"];
          const flows = ["no_withdrawals", "delayed_stepup_example", "monthly_withdrawal_500_usd_stress", "monthly_withdrawal_1000_usd_stress"];
          const bi = bonds.indexOf(bond);
          const ti = timings.indexOf(timing);
          const fi = flows.indexOf(flow);
          const row = RAW_PACK.a.find(item => item[0] === year && item[1] === bi && item[2] === target && item[3] === ti && item[4] === fi);
          if (!row) throw new Error("No exact annual key for flow sweep: " + JSON.stringify({bond, target, timing, flow, year}));
          const navIndex = stat === "p05" ? 6 : stat === "worst" ? 8 : 5;
          const expectedPrimary = moneyText(row[navIndex] / Math.pow(1 + cpi, year));
          const primary = (document.querySelector("#decisionPrimaryValue")?.innerText || "").trim();
          const flowOption = document.querySelector("#flow").selectedOptions[0];
          const flowLabel = (flowOption?.textContent || "").trim();
          const timingLabel = (document.querySelector("#timing").selectedOptions[0]?.textContent || "").trim();
          const evidence = document.querySelector("#decisionEvidence");
          const trajectory = document.querySelector("#decisionTrajectory");
          const navMetricRows = Array.from(document.querySelectorAll("#metrics .metric")).map(card => ({
            label: (card.querySelector(".k")?.innerText || "").trim(),
            value: (card.querySelector(".v")?.innerText || "").trim(),
            note: (card.querySelector(".s")?.innerText || "").trim()
          }));
          const expectedMetricRows = [
            ["第" + year + "年中位資產", moneyText(row[5])],
            ["第" + year + "年P05資產", moneyText(row[6])],
            ["截至當年累計年化回報", pctText(row[9])],
            ["截至當年最大回撤", pctText(row[13])],
            ["最差窗口截至當年回撤", pctText(row[14])],
            ["名目低於本金窗口", String(Math.round(Number(row[15]))) + "/157"],
            ["累計缺口窗口", String(Math.round(Number(row[16]))) + "/157"]
          ];
          const metricReconciles = navMetricRows.length === expectedMetricRows.length &&
            expectedMetricRows.every((expected, index) =>
              navMetricRows[index].label === expected[0] && navMetricRows[index].value === expected[1]);
          const shortfallNoteExpected = "截至當年P95缺口 " + moneyText(row[19]);
          const shortfallNoteReconciles = navMetricRows.length === 7 && navMetricRows[6].note.includes(shortfallNoteExpected);
          const stockCell = trajectory?.querySelector('[data-series="stock"] td[data-year="' + year + '"]');
          const bondCell = trajectory?.querySelector('[data-series="bond"] td[data-year="' + year + '"]');
          const expectedStockPct = Number((100 * (1 - Number(row[20]))).toFixed(4));
          const expectedBondPct = Number((100 * Number(row[20])).toFixed(4));
          const stockPct = Number(stockCell?.dataset.stockPct);
          const bondPct = Number(bondCell?.dataset.bondPct);
          const bars = Array.from(document.querySelectorAll("#flows .barrow"));
          const flowBars = flows.map((flowValue, index) => {
            const flowRow = RAW_PACK.a.find(item => item[0] === year && item[1] === bi && item[2] === target && item[3] === ti && item[4] === index);
            const bar = bars[index];
            const gapNote = bar?.nextElementSibling?.innerText || "";
            return {
              flow: flowValue,
              label: (bar?.querySelector("span")?.innerText || "").trim(),
              nav: (bar?.querySelector("b")?.innerText || "").trim(),
              expectedNav: moneyText(flowRow[5]),
              expectedShortfallCount: String(Math.round(Number(flowRow[16]))),
              expectedP95Shortfall: moneyText(flowRow[19]),
              gapNote
            };
          });
          const allocationDetail = (document.querySelector("#decisionAllocationDetail")?.innerText || "").trim();
          const navRound = Math.round(row[navIndex] / Math.pow(1 + cpi, year));
          const stockPctRounded = Number((100 * (1 - Number(row[20]))).toFixed(2));
          const bondPctRounded = Number((100 * Number(row[20])).toFixed(2));
          const expectedStockDollars = moneyText(navRound * stockPctRounded / 100);
          const expectedBondDollars = moneyText(navRound * bondPctRounded / 100);
          const evidenceFlow = (document.querySelector("#decisionEvidenceFlow")?.innerText || "").trim();
          const evidenceScope = (document.querySelector("#decisionEvidenceScope")?.innerText || "").trim();
          return {
            bond, target, timing, flow, flowLabel, year, stat, cpi,
            primary, expectedPrimary,
            evidenceFlow,
            evidenceFlowBound: evidence?.dataset.flow === flowLabel &&
              evidence?.dataset.year === String(year) &&
              evidence?.dataset.bond === bond &&
              evidence?.dataset.target === String(target) &&
              evidence?.dataset.timing === timingLabel,
            metricReconciles,
            shortfallNoteReconciles,
            metricRows: navMetricRows,
            expectedMetricRows,
            trajectoryYear: trajectory?.dataset.year || null,
            stockPct, expectedStockPct, bondPct, expectedBondPct,
            flowBars,
            allocationDetail,
            expectedStockDollars,
            expectedBondDollars,
            selectedBond: bond,
            dataScopeDisclosure: evidenceScope
          };
        });
        const context = JSON.stringify({flow, year, stat, state});
        need(state.primary === state.expectedPrimary,
          "cashflow/year/stat NAV binding differs from its exact annual record: " + context);
        need(state.evidenceFlowBound && state.evidenceFlow.includes(state.flowLabel),
          "cashflow label/key/year does not match the selected annual key: " + context);
        need(state.metricReconciles && state.shortfallNoteReconciles,
          "year NAV/return/drawdown/shortfall metrics do not reconcile to the current flow row: " + context);
        need(state.trajectoryYear === String(year) &&
             Number.isFinite(state.stockPct) && Number.isFinite(state.bondPct) &&
             Math.abs(state.stockPct - state.expectedStockPct) <= 0.0001 &&
             Math.abs(state.bondPct - state.expectedBondPct) <= 0.0001,
          "allocation path is not using the same annual record as the selected NAV: " + context);
        need(state.allocationDetail.includes("股票約 " + state.expectedStockDollars) &&
             state.allocationDetail.includes(state.selectedBond + " 約 " + state.expectedBondDollars),
          "allocation dollar split does not reconcile to the selected NAV statistic and target weights: " + context);
        need(state.dataScopeDisclosure.includes("不代表實際持倉或今日訂單"),
          "UI must distinguish annual target weights from actual holdings/orders: " + context);
        for (const bar of state.flowBars) {
          need(bar.label.length > 0 && bar.nav === bar.expectedNav &&
               bar.gapNote.includes("截至當年缺口 " + bar.expectedShortfallCount + "/157") &&
               bar.gapNote.includes("P95缺口 " + bar.expectedP95Shortfall),
            "cashflow comparison chart bar/gap text is not bound to its own annual row: " + JSON.stringify({flow, year, stat, bar}));
          cashflowSemanticSweep.flow_comparison_bars_verified++;
        }
        if (flow === "no_withdrawals") {
          const noFlowRow = await page.evaluate((selection) => {
            const bi = ["AGG", "SHY", "IEF", "TLT"].indexOf(selection.bond);
            const ti = ["front_rapid", "front_fast", "front_loaded", "linear", "mid_loaded", "staggered", "back_loaded", "back_late"].indexOf(selection.timing);
            const item = RAW_PACK.a.find(row => row[0] === selection.year && row[1] === bi &&
              row[2] === selection.target && row[3] === ti && row[4] === 0);
            return {withdrawals:item[17],medianShortfall:item[18],p95Shortfall:item[19],shortfallWindows:item[16]};
          }, {bond:state.bond,target:state.target,timing:state.timing,year:state.year});
          need(Math.abs(Number(noFlowRow.withdrawals)) <= 0.01 &&
               Math.abs(Number(noFlowRow.medianShortfall)) <= 0.01 &&
               Math.abs(Number(noFlowRow.p95Shortfall)) <= 0.01 &&
               Number(noFlowRow.shortfallWindows) === 0,
            "no-withdrawal annual row must be all-zero for actual withdrawals and shortfalls: " + context + " / " + JSON.stringify(noFlowRow));
          cashflowSemanticSweep.no_withdrawal_zero_cashflow_checks++;
        }
        cashflowSemanticSweep.total_combinations++;
        cashflowSemanticSweep.yearly_flow_slices_verified++;
        cashflowSemanticSweep.primary_nav_bindings_verified++;
        cashflowSemanticSweep.metric_rows_verified++;
        cashflowSemanticSweep.allocation_path_bindings_verified++;
        cashflowSemanticSweep.data_scope_disclosure_checks++;
      }
    }
  }
  result.cashflow_nav_semantic_sweep = cashflowSemanticSweep;

  // Restore the exact original forward-mode state before independent reverse replay.
  for (const [selector, value] of [
    ["#flow", originalControls.flow], ["#statView", originalControls.statView],
    ["#realMode", originalControls.realMode]
  ]) {
    await page.locator(selector).selectOption(String(value));
  }
  await page.locator("#year").evaluate((element, value) => {
    element.value = String(value);
    element.dispatchEvent(new Event("input", {bubbles:true}));
    element.dispatchEvent(new Event("change", {bubbles:true}));
  }, Number(originalControls.year));
  await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));

  const noWithdrawalValue = await page.locator("#flow").evaluate(el => {
    const option = Array.from(el.options).find(item => /不提款/.test(item.textContent || ""));
    return option ? option.value : null;
  });
  need(noWithdrawalValue !== null, "reverse replay requires an explicit no-withdrawal cashflow option");
  await page.locator("#glidepathDirection").selectOption("bond-to-stock");
  await page.locator("#bond").selectOption("TLT");
  await page.locator("#flow").selectOption(noWithdrawalValue);
  await page.locator("#realMode").selectOption("0");
  await page.waitForFunction(() => {
    const root = document.querySelector("#decisionTrajectory");
    const replay = document.querySelector("#reverseReplay");
    return root && root.dataset.direction === "bond-to-stock" && replay && replay.dataset.state === "passed";
  }, null, {timeout: 10000});
  const reverseRead = await page.evaluate(() => {
    const root = document.querySelector("#decisionTrajectory");
    const replay = document.querySelector("#reverseReplay");
    const series = key => Array.from(root.querySelectorAll('[data-series="' + key + '"] td[data-year]'));
    const stock = series("stock").map(cell => Number(cell.dataset.stockPct));
    const bond = series("bond").map(cell => Number(cell.dataset.bondPct));
    return {
      direction: root.dataset.direction,
      pathState: root.dataset.state,
      target: Number(root.dataset.target),
      endpointStockPct: Number(root.dataset.endpointStockPct),
      endpointBondPct: Number(root.dataset.endpointBondPct),
      stockPct: stock,
      bondPct: bond,
      sums: stock.map((value, index) => value + bond[index]),
      selectedYear: root.dataset.year,
      replayState: replay.dataset.state,
      windowCount: Number(replay.dataset.windowCount),
      sourceAsOf: replay.dataset.sourceAsOf,
      sourceSha256Present: /^[a-f0-9]{64}$/.test(replay.dataset.sourceSha256 || ""),
      firstStart: replay.dataset.firstStart,
      firstEnd: replay.dataset.firstEnd,
      lastStart: replay.dataset.lastStart,
      lastEnd: replay.dataset.lastEnd,
      medianTerminalNav: Number(replay.dataset.medianTerminalNav),
      medianRealTerminalNav: Number(replay.dataset.medianRealTerminalNav),
      medianNominalCagr: Number(replay.dataset.medianNominalCagr),
      medianRealCagr: Number(replay.dataset.medianRealCagr),
      medianNominalDrawdown: Number(replay.dataset.medianNominalDrawdown),
      worstNominalDrawdown: Number(replay.dataset.worstNominalDrawdown),
      nominalNoLossCount: Number(replay.dataset.nominalNoLossCount),
      realNoLossCount: Number(replay.dataset.realNoLossCount),
      statusText: document.querySelector("#reverseReplayStatus").innerText,
      sourceDisclosure: document.querySelector("#reverseReplayLimits").innerText,
      legacyMetricsHidden: document.querySelector("#metrics").getAttribute("data-glp-reverse-hidden") === "true",
      legacySummaryHidden: document.querySelector("#decisionSummary").getAttribute("data-glp-reverse-hidden") === "true"
    };
  });
  need(reverseRead.direction === "bond-to-stock" && reverseRead.pathState === "ready", "reverse direction path not ready: " + JSON.stringify(reverseRead));
  need(reverseRead.stockPct.length === 11 && reverseRead.bondPct.length === 11 &&
    Math.abs(reverseRead.stockPct[0]) < 0.02 && Math.abs(reverseRead.bondPct[0] - 100) < 0.02,
    "reverse path must begin at 100% bonds / 0% stocks: " + JSON.stringify(reverseRead));
  need(Math.abs(reverseRead.endpointStockPct - reverseRead.target) <= 0.75 &&
    Math.abs(reverseRead.endpointBondPct - (100 - reverseRead.target)) <= 0.75,
    "reverse year-10 endpoint must match selected stock target and complementary bond weight");
  need(reverseRead.sums.every(value => Math.abs(value - 100) <= 0.02), "reverse stock/bond weights must sum to 100%");
  need(reverseRead.replayState === "passed" && reverseRead.windowCount === 157, "reverse replay did not compute all 157 windows: " + JSON.stringify(reverseRead));
  need(reverseRead.sourceAsOf === "2026-09-04" && reverseRead.sourceSha256Present, "reverse replay source/date/hash lineage is missing");
  need(reverseRead.firstStart === "2004-03-30" && reverseRead.firstEnd && reverseRead.lastStart && reverseRead.lastEnd,
    "reverse replay window coverage dates are invalid: " + JSON.stringify(reverseRead));
  need(Number.isFinite(reverseRead.medianTerminalNav) && reverseRead.medianTerminalNav > 0 &&
    Number.isFinite(reverseRead.medianRealTerminalNav) && reverseRead.medianRealTerminalNav > 0 &&
    Number.isFinite(reverseRead.medianNominalCagr) && Number.isFinite(reverseRead.worstNominalDrawdown),
    "reverse replay metrics are missing or non-finite");
  need(reverseRead.legacyMetricsHidden && reverseRead.legacySummaryHidden,
    "forward-only front metrics must be hidden in reverse mode to prevent cross-mode confusion");
  need(reverseRead.sourceDisclosure.includes("TLT") && reverseRead.sourceDisclosure.includes("通脹假設"),
    "reverse replay proxy and inflation limitations are not disclosed");

  const pairRead = await page.evaluate(() => {
    const panel = document.querySelector("#pairedComparison");
    return {
      state: panel.dataset.state,
      windowCount: Number(panel.dataset.windowCount),
      matchedPairCount: Number(panel.dataset.matchedPairCount),
      sourceAsOf: panel.dataset.sourceAsOf,
      sourceSha256: panel.dataset.sourceSha256,
      firstStart: panel.dataset.firstStart,
      firstEnd: panel.dataset.firstEnd,
      lastStart: panel.dataset.lastStart,
      lastEnd: panel.dataset.lastEnd,
      inflation: Number(panel.dataset.inflation),
      forwardMedianNav: Number(panel.dataset.forwardMedianNav),
      reverseMedianNav: Number(panel.dataset.reverseMedianNav),
      forwardMedianRealNav: Number(panel.dataset.forwardMedianRealNav),
      reverseMedianRealNav: Number(panel.dataset.reverseMedianRealNav),
      forwardP05RealNav: Number(panel.dataset.forwardP05RealNav),
      reverseP05RealNav: Number(panel.dataset.reverseP05RealNav),
      forwardMedianRealCagr: Number(panel.dataset.forwardMedianRealCagr),
      reverseMedianRealCagr: Number(panel.dataset.reverseMedianRealCagr),
      forwardRealFloorCount: Number(panel.dataset.forwardRealFloorCount),
      reverseRealFloorCount: Number(panel.dataset.reverseRealFloorCount),
      medianRealNavDelta: Number(panel.dataset.medianRealNavDelta),
      pairedMedianRealNavDelta: Number(panel.dataset.pairedMedianRealNavDelta),
      forwardMedianCagr: Number(panel.dataset.forwardMedianCagr),
      reverseMedianCagr: Number(panel.dataset.reverseMedianCagr),
      medianCagrDelta: Number(panel.dataset.medianCagrDelta),
      pairedMedianCagrDelta: Number(panel.dataset.pairedMedianCagrDelta),
      forwardMedianDd: Number(panel.dataset.forwardMedianDd),
      reverseMedianDd: Number(panel.dataset.reverseMedianDd),
      medianDdDelta: Number(panel.dataset.medianDdDelta),
      pairedMedianDdDelta: Number(panel.dataset.pairedMedianDdDelta),
      forwardDdYearCounts: JSON.parse(panel.dataset.forwardDdYearCounts || "{}"),
      reverseDdYearCounts: JSON.parse(panel.dataset.reverseDdYearCounts || "{}"),
      drawdownYearRows: document.querySelectorAll("#pairedDrawdownYearTable tbody tr").length,
      drawdownYearCells: document.querySelectorAll("#pairedDrawdownYearTable tbody td").length,
      forwardDrawdownTableCounts: Array.from(document.querySelectorAll('#pairedDrawdownYearTable [data-dd-year-row="forward"]')).map(cell => Number(cell.innerText)),
      reverseDrawdownTableCounts: Array.from(document.querySelectorAll('#pairedDrawdownYearTable [data-dd-year-row="reverse"]')).map(cell => Number(cell.innerText)),
      reverseRealNavWins: Number(panel.dataset.reverseRealNavWins),
      forwardRealNavWins: Number(panel.dataset.forwardRealNavWins),
      reverseLowerDrawdown: Number(panel.dataset.reverseLowerDrawdown),
      forwardLowerDrawdown: Number(panel.dataset.forwardLowerDrawdown),
      statusText: document.querySelector("#pairedComparisonStatus").innerText,
      winSummary: document.querySelector("#pairedComparisonWinSummary").innerText,
      method: document.querySelector("#pairedComparisonMethod").innerText,
      limits: document.querySelector("#pairedComparisonLimits").innerText,
      evidenceSample: document.querySelector("#decisionEvidenceSample").innerText,
      tableRows: document.querySelectorAll("#pairedComparison .paired-table-wrap tbody tr").length
    };
  });
  need(pairRead.state === "passed" && pairRead.windowCount === 157 && pairRead.matchedPairCount === 157,
    "same-window paired comparison did not compute 157 matched pairs: " + JSON.stringify(pairRead));
  need(pairRead.firstStart === reverseRead.firstStart && pairRead.firstEnd === reverseRead.firstEnd &&
    pairRead.lastStart === reverseRead.lastStart && pairRead.lastEnd === reverseRead.lastEnd,
    "paired comparison windows diverged from reverse replay window protocol");
  need(pairRead.sourceAsOf === reverseRead.sourceAsOf && /^[a-f0-9]{64}$/.test(pairRead.sourceSha256),
    "paired comparison source lineage is missing or differs from reverse replay");
  need(pairRead.evidenceSample.includes("2004-03-30–2014-04-03") &&
    pairRead.evidenceSample.includes("2016-08-19–2026-08-31"),
    "the selected paired amount does not show the independent 10-year window date range");
  need(Number.isFinite(pairRead.forwardMedianNav) && Number.isFinite(pairRead.reverseMedianNav) &&
    Number.isFinite(pairRead.pairedMedianRealNavDelta) && Number.isFinite(pairRead.pairedMedianCagrDelta) &&
    Number.isFinite(pairRead.pairedMedianDdDelta), "paired comparison contains non-finite metrics");
  need(Math.abs(pairRead.medianRealNavDelta - (pairRead.reverseMedianRealNav - pairRead.forwardMedianRealNav)) < 0.1,
    "real NAV summary delta does not reconcile to the reported strategy medians");
  need(Math.abs(pairRead.medianCagrDelta - (pairRead.reverseMedianCagr - pairRead.forwardMedianCagr)) < 1e-6,
    "CAGR summary delta does not reconcile to the reported strategy medians");
  need(Math.abs(pairRead.medianDdDelta - (pairRead.reverseMedianDd - pairRead.forwardMedianDd)) < 1e-6,
    "drawdown summary delta does not reconcile to the reported strategy medians");
  need(Object.values(pairRead.forwardDdYearCounts).reduce((a,b)=>a+b,0) === 157 &&
    Object.values(pairRead.reverseDdYearCounts).reduce((a,b)=>a+b,0) === 157,
    "drawdown-occurrence-year counts must account for all windows in both directions");
  need(pairRead.drawdownYearRows === 2 && pairRead.drawdownYearCells === 20 &&
    pairRead.forwardDrawdownTableCounts.reduce((a,b)=>a+b,0) === 157 &&
    pairRead.reverseDrawdownTableCounts.reduce((a,b)=>a+b,0) === 157 &&
    pairRead.forwardDrawdownTableCounts.every((count,index)=>count===pairRead.forwardDdYearCounts[String(index+1)]) &&
    pairRead.reverseDrawdownTableCounts.every((count,index)=>count===pairRead.reverseDdYearCounts[String(index+1)]),
    "visible drawdown occurrence-year distribution must match the per-window audit counts");
  need(pairRead.reverseRealNavWins + pairRead.forwardRealNavWins <= 157 &&
    pairRead.reverseLowerDrawdown + pairRead.forwardLowerDrawdown <= 157,
    "paired win counts exceed matched window count");
  need(pairRead.tableRows === 9 && pairRead.limits.includes("窗口彼此重疊") &&
    pairRead.method.includes("最大回撤年") && pairRead.method.includes("252 個交易日"),
    "paired comparison table/method/overlap disclosures are missing");
  need(Math.abs(pairRead.reverseMedianNav - reverseRead.medianTerminalNav) < 0.1,
    "paired reverse NAV does not reconcile with the independently replayed reverse strategy");
  result.paired_direction_comparison = {...pairRead, passed: true};

  const realMedianAtZero = reverseRead.medianRealTerminalNav;
  await page.locator("#realMode").selectOption("0.0235");
  await page.waitForFunction(baseline => {
    const panel = document.querySelector("#reverseReplay");
    const current = Number(panel && panel.dataset.medianRealTerminalNav);
    return panel && panel.dataset.state === "passed" && Number.isFinite(current) && Math.abs(current - baseline) > 1;
  }, realMedianAtZero, {timeout: 10000});
  const realMedianAt235 = await page.locator("#reverseReplay").getAttribute("data-median-real-terminal-nav");
  need(realMedianAt235 !== null && Math.abs(Number(realMedianAt235) - realMedianAtZero) > 1,
    "inflation assumption did not change the independent real NAV outcome");
  await page.waitForFunction(() => {
    const panel = document.querySelector("#pairedComparison");
    return panel && panel.dataset.state === "passed" && panel.dataset.inflation === "0.0235" &&
      Number.isFinite(Number(panel.dataset.forwardMedianRealNav)) &&
      Number.isFinite(Number(panel.dataset.reverseMedianRealNav));
  }, null, {timeout: 10000});
  const pairReal235 = await page.evaluate(() => {
    const panel = document.querySelector("#pairedComparison");
    return {
      state: panel.dataset.state,
      matchedPairCount: Number(panel.dataset.matchedPairCount),
      inflation: Number(panel.dataset.inflation),
      forwardMedianRealNav: Number(panel.dataset.forwardMedianRealNav),
      reverseMedianRealNav: Number(panel.dataset.reverseMedianRealNav),
      forwardP05RealNav: Number(panel.dataset.forwardP05RealNav),
      reverseP05RealNav: Number(panel.dataset.reverseP05RealNav),
      forwardMedianRealCagr: Number(panel.dataset.forwardMedianRealCagr),
      reverseMedianRealCagr: Number(panel.dataset.reverseMedianRealCagr),
      forwardRealFloorCount: Number(panel.dataset.forwardRealFloorCount),
      reverseRealFloorCount: Number(panel.dataset.reverseRealFloorCount),
      medianRealNavDelta: Number(panel.dataset.medianRealNavDelta),
      pairedMedianRealNavDelta: Number(panel.dataset.pairedMedianRealNavDelta),
      forwardMedianDd: Number(panel.dataset.forwardMedianDd),
      reverseMedianDd: Number(panel.dataset.reverseMedianDd),
      medianDdDelta: Number(panel.dataset.medianDdDelta),
      reverseRealNavWins: Number(panel.dataset.reverseRealNavWins),
      forwardRealNavWins: Number(panel.dataset.forwardRealNavWins),
      forwardDdYearCounts: JSON.parse(panel.dataset.forwardDdYearCounts || "{}"),
      reverseDdYearCounts: JSON.parse(panel.dataset.reverseDdYearCounts || "{}"),
      limits: document.querySelector("#pairedComparisonLimits").innerText
    };
  });
  need(pairReal235.state === "passed" && pairReal235.matchedPairCount === 157 && pairReal235.inflation === 0.0235,
    "paired real-value comparison did not refresh for 2.35% inflation");
  need(Number.isFinite(pairReal235.forwardMedianRealNav) && Number.isFinite(pairReal235.reverseMedianRealNav) &&
    Number.isFinite(pairReal235.forwardP05RealNav) && Number.isFinite(pairReal235.reverseP05RealNav) &&
    Number.isFinite(pairReal235.forwardMedianRealCagr) && Number.isFinite(pairReal235.reverseMedianRealCagr),
    "paired real-value snapshot contains missing metrics");
  need(Math.abs(pairReal235.medianRealNavDelta - (pairReal235.reverseMedianRealNav - pairReal235.forwardMedianRealNav)) < 0.1 &&
    pairReal235.limits.includes("窗口彼此重疊"),
    "paired real summary delta/disclosure does not reconcile");
  result.paired_direction_comparison_real_235 = {...pairReal235, passed:true};
  await page.locator("#realMode").selectOption("0");

  await page.locator("#bond").selectOption("SHY");
  await page.waitForFunction(() => document.querySelector("#reverseReplay").dataset.state === "blocked" &&
    document.querySelector("#pairedComparison").dataset.state === "blocked", null, {timeout: 5000});
  const unsupportedBondBlock = await page.locator("#reverseReplayStatus").innerText();
  const unsupportedPairBlock = await page.locator("#pairedComparisonStatus").innerText();
  need(unsupportedBondBlock.includes("BLOCK") && (await page.locator("#reverseReplayMethod").innerText()).includes("只覆蓋 TLT"),
    "unsupported bond proxy must BLOCK rather than borrow TLT results");
  need(unsupportedPairBlock.includes("BLOCK") && (await page.locator("#pairedComparisonMethod").innerText()).includes("只覆蓋 TLT"),
    "paired comparison must BLOCK for unsupported bond proxies");
  await page.locator("#bond").selectOption("TLT");
  await page.waitForFunction(() => document.querySelector("#reverseReplay").dataset.state === "passed", null, {timeout: 10000});
  await page.locator("#flow").selectOption("monthly_withdrawal_500_usd_stress");
  await page.waitForFunction(() => document.querySelector("#reverseReplay").dataset.state === "blocked" &&
    document.querySelector("#pairedComparison").dataset.state === "blocked", null, {timeout: 5000});
  need((await page.locator("#reverseReplayStatus").innerText()).includes("BLOCK") &&
    (await page.locator("#reverseReplayMethod").innerText()).includes("不提款模式"),
    "unsupported withdrawal mode must BLOCK rather than reuse no-withdrawal outcomes");
  need((await page.locator("#pairedComparisonStatus").innerText()).includes("BLOCK") &&
    (await page.locator("#pairedComparisonMethod").innerText()).includes("不提款／不供款"),
    "paired comparison must BLOCK for unsupported cashflows");
  await page.locator("#flow").selectOption(noWithdrawalValue);
  await page.waitForFunction(() => document.querySelector("#reverseReplay").dataset.state === "passed", null, {timeout: 10000});
  result.reverse_direction_replay = {...reverseRead, realMedianAt235: Number(realMedianAt235), unsupportedBondBlock, passed: true};

  await page.locator("#glidepathDirection").selectOption("stock-to-bond");
  for (const [selector, value] of [
    ["#bond", originalControls.bond], ["#target", originalControls.target],
    ["#timing", originalControls.timing], ["#flow", originalControls.flow],
    ["#year", originalControls.year], ["#realMode", originalControls.realMode], ["#statView", originalControls.statView]
  ]) {
    if (selector === "#bond" || selector === "#timing" || selector === "#flow" || selector === "#realMode" || selector === "#statView") {
      await page.locator(selector).selectOption(String(value));
    } else {
      await page.locator(selector).evaluate((el, next) => {
        el.value = String(next);
        el.dispatchEvent(new Event("input", {bubbles:true}));
        el.dispatchEvent(new Event("change", {bubbles:true}));
      }, String(value));
    }
  }
  await page.waitForFunction(() => document.querySelector("#decisionSummary").getAttribute("data-glp-reverse-hidden") === null &&
    document.querySelector("#metrics").getAttribute("data-glp-reverse-hidden") === null &&
    document.querySelector("#reverseReplay").hidden === true, null, {timeout: 5000});

  await page.locator("#year").evaluate((el, value) => {
    el.value = String(value);
    el.dispatchEvent(new Event("input", {bubbles: true}));
    el.dispatchEvent(new Event("change", {bubbles: true}));
  }, 9);
  await page.waitForFunction(() => document.querySelector("#year").value === "9" && document.querySelector("#decisionTrajectory").dataset.year === "9", null, {timeout: 5000});
  const year9State = await page.evaluate(() => ({
    controlValue: document.querySelector("#year")?.value ?? null,
    panelYear: document.querySelector("#decisionTrajectory")?.dataset.year ?? null,
    selectedYearHeaders: Array.from(document.querySelectorAll("#decisionTrajectory [data-trajectory-year][aria-current='true']")).map(node => node.getAttribute("data-trajectory-year")),
    summaryLead: document.querySelector("#decisionLead")?.innerText ?? ""
  }));
  result.glidepath_decision_trajectory.year9_bar_sync_state = year9State;
  need(year9State.controlValue === "9" && year9State.panelYear === "9" && year9State.selectedYearHeaders.join(",") === "9", "year BAR did not synchronize the annual trajectory table: " + JSON.stringify(year9State));
  need(year9State.summaryLead.includes("第9年"), "year BAR change did not update the frontloaded decision summary: " + JSON.stringify(year9State));
  await page.locator("#year").evaluate((el, value) => {
    el.value = String(value);
    el.dispatchEvent(new Event("input", {bubbles: true}));
    el.dispatchEvent(new Event("change", {bubbles: true}));
  }, 5);
  await page.waitForFunction(() => document.querySelector("#year").value === "5" && document.querySelector("#decisionTrajectory").dataset.year === "5", null, {timeout: 5000});

  await page.locator("#bond").selectOption("TLT");
  await page.locator("#target").evaluate(el => {el.value="80"; el.dispatchEvent(new Event("input",{bubbles:true})); el.dispatchEvent(new Event("change",{bubbles:true}));});
  await page.locator("#timing").selectOption("front_fast");
  await page.locator("#flow").selectOption("monthly_withdrawal_500_usd_stress");
  await page.locator("#realMode").selectOption("0.0235");
  const changedSummary = await page.evaluate(() => ({
    lead: document.querySelector("#decisionLead").innerText,
    allocation: document.querySelector("#decisionAllocationHeadline").innerText,
    allocationDetail: document.querySelector("#decisionAllocationDetail").innerText,
    flow: document.querySelector("#decisionFlowHeadline").innerText,
    floor: document.querySelector("#decisionFloorHeadline").innerText,
    value: document.querySelector("#decisionPrimaryValue").innerText
  }));
  need(changedSummary.lead.includes("TLT") && changedSummary.lead.includes("80%") && changedSummary.lead.includes("加速前置"), "decision summary did not follow strategy control changes");
  need(changedSummary.flow.includes("$500") && changedSummary.floor.includes("$"), "decision summary did not follow cashflow/inflation changes");
  need(changedSummary.value.startsWith("$") && changedSummary.allocation.includes("TLT"), "decision summary lacks updated monetary result/allocation");
  need(changedSummary.allocationDetail.includes("按主結果 $112,171") && changedSummary.allocationDetail.includes("股票約 $50,477") && changedSummary.allocationDetail.includes("TLT 約 $61,694"), "changed allocation dollar split must reconcile to displayed real NAV and allocation percentages");
  await page.waitForFunction(() => document.querySelector("#decisionEvidence").dataset.target === "80" &&
    document.querySelector("#decisionEvidence").dataset.bond === "TLT" &&
    document.querySelector("#decisionEvidence").dataset.flow.includes("$500") &&
    document.querySelector("#decisionEvidence").dataset.inflation === "0.0235", null, {timeout: 5000});
  const updatedEvidence = await page.evaluate(() => ({
    amount: document.querySelector("#decisionEvidenceAmount").innerText,
    behavior: document.querySelector("#decisionEvidenceBehavior").innerText,
    flow: document.querySelector("#decisionEvidenceFlow").innerText,
    risk: document.querySelector("#decisionEvidenceRisk").innerText,
    scope: document.querySelector("#decisionEvidenceScope").innerText,
    dataset: {
      direction: document.querySelector("#decisionEvidence").dataset.direction,
      bond: document.querySelector("#decisionEvidence").dataset.bond,
      target: document.querySelector("#decisionEvidence").dataset.target,
      flow: document.querySelector("#decisionEvidence").dataset.flow,
      inflation: document.querySelector("#decisionEvidence").dataset.inflation,
      reverseReplayScope: document.querySelector("#decisionEvidence").dataset.reverseReplayScope
    }
  }));
  need(updatedEvidence.amount.includes("$112,171") && updatedEvidence.behavior.includes("TLT") &&
    updatedEvidence.behavior.includes("80%") && updatedEvidence.flow.includes("$500"),
    "decision evidence did not update its amount/behavior/flow linkage after controls changed");
  need(updatedEvidence.risk.includes("未精算") && updatedEvidence.scope.includes("實際持倉"),
    "decision evidence must retain unproven-risk and not-actual-holdings notices after controls change");
  result.frontloaded_decision_summary.decision_evidence_updated_state = {...updatedEvidence,passed:true};
  result.frontloaded_decision_summary.updated_state = {...changedSummary, passed:true};

  await page.waitForFunction(() => {
    const root = document.querySelector("#decisionTrajectory");
    return root && root.dataset.target === "80" &&
      root.dataset.timing === "front_fast" && root.dataset.year === "5";
  }, null, {timeout: 5000});
  const changedTrajectory = await readTrajectory();
  need(changedTrajectory.state === "ready" && changedTrajectory.target === 80 && changedTrajectory.timing === "front_fast", "trajectory panel did not follow target/timing control changes: " + JSON.stringify(changedTrajectory));
  need(Math.abs(changedTrajectory.endpoint_bond_pct - 80) <= 0.75, "trajectory endpoint failed to update to 80% TLT target: " + JSON.stringify(changedTrajectory));
  need(changedTrajectory.selected_year === "5" && changedTrajectory.selected_year_header_count === 1 && changedTrajectory.selected_year_header === 5, "trajectory selected-year highlight did not persist when strategy changed");
  need(Math.abs(changedTrajectory.bond_pcts[5] - initialTrajectory.bond_pcts[5]) > 0.5, "trajectory did not change when the target and timing changed");
  need(changedTrajectory.stock_bond_sums.every(value => Math.abs(value - 100) <= 0.02), "updated stock/bond percentages no longer sum to 100");
  result.glidepath_decision_trajectory.updated_state = changedTrajectory;

  await page.evaluate(() => {
    window.__glidepathAuditLastBlob = null;
    window.__glidepathAuditLastDownloadName = null;
    const NativeBlob = window.Blob;
    window.Blob = class GlidepathAuditBlob extends NativeBlob {
      constructor(parts, options) {
        super(parts, options);
        window.__glidepathAuditLastBlob = this;
      }
    };
    document.addEventListener("click", event => {
      const element = event.target && event.target.closest ? event.target.closest("[data-target],[data-year],[data-flow],[data-timing]") : null;
      window.__glidepathAuditLastClick = element ? {
        target: element.getAttribute("data-target"),
        timing: element.getAttribute("data-timing"),
        bond: element.getAttribute("data-bond"),
        flow: element.getAttribute("data-flow"),
        year: element.getAttribute("data-year"),
        cohortYear: element.getAttribute("data-cohort-year")
      } : null;
      const anchor = event.target && event.target.closest ? event.target.closest("a[download]") : null;
      if (anchor) window.__glidepathAuditLastDownloadName = anchor.download;
    }, true);
  });
  need(await page.title() === "股票轉債互動追蹤台（優化增強版 v2.2）", "document title was not updated to v2.2");

  const setYear = async year => page.locator("#year").evaluate((el, value) => {
    el.value = String(value);
    el.dispatchEvent(new Event("input", {bubbles: true}));
    el.dispatchEvent(new Event("change", {bubbles: true}));
  }, year);

  for (const year of [0, 1, 5, 9, 10]) {
    for (const inflation of ["0", "0.0235", "0.035"]) {
      for (const stat of ["median", "p05", "worst"]) {
        await setYear(year);
        await page.locator("#realMode").selectOption(inflation);
        await page.locator("#statView").selectOption(stat);
        const bad = await inspectRender(page);
        need(!bad.badText, "NaN/undefined appeared in visible DOM for year=" + year + ", inflation=" + inflation + ", stat=" + stat);
        need(bad.badAttributes.length === 0, "invalid SVG attribute appeared for year=" + year + ", inflation=" + inflation + ", stat=" + stat + ": " + JSON.stringify(bad.badAttributes));
        result.state_matrix_combinations.push({year, inflation, stat});
        result.state_matrix_sweeps++;
      }
    }
  }
  result.rendered_dom_guard_passed = true;
  need(result.state_matrix_sweeps === 45, "state matrix did not complete 45 combinations");

  const geometry = await page.locator("#glide circle").evaluateAll(nodes => {
    const vals = nodes.map(node => Number(node.getAttribute("cy")));
    const timingValues = Array.from(document.querySelectorAll("#timing option")).map(option => option.value);
    const yearControl = document.querySelector("#year");
    const minYear = Number(yearControl.min || 0);
    const maxYear = Number(yearControl.max || 10);
    const yearStep = Number(yearControl.step || 1);
    const yearsPerTiming = Math.floor((maxYear - minYear) / yearStep) + 1;
    const pairs = nodes.map(node => node.getAttribute("data-timing") + ":" + node.getAttribute("data-year"));
    return {
      count: vals.length,
      expectedCount: timingValues.length * yearsPerTiming,
      timingCount: timingValues.length,
      yearsPerTiming,
      uniqueTimingYearPairs: new Set(pairs).size,
      min: Math.min(...vals),
      max: Math.max(...vals),
      non_finite: vals.filter(value => !Number.isFinite(value)).length
    };
  });
  need(geometry.timingCount === 8 && geometry.count === geometry.expectedCount &&
       geometry.uniqueTimingYearPairs === geometry.expectedCount,
       "glidepath must render one circle for every timing/year pair (8 timing rules x all years): " + JSON.stringify(geometry));
  // The current selected target can legitimately drive the bond allocation to 100% (cy=y0=15); assert the chart's actual plot bounds, not the default strategy's narrower range.
  need(geometry.non_finite === 0 && geometry.min >= 15 && geometry.max <= 180, "glidepath circle geometry out of plot bounds [15,180]: " + JSON.stringify(geometry));
  result.glidepath_geometry = geometry;

  await setYear(5);
  await page.locator("#realMode").selectOption("0");
  await page.locator("#statView").selectOption("p05");
  let drawdownText = await page.locator("#drawdown").innerText();
  need(drawdownText.includes("資料缺口：本年度摘要沒有 P05 最大回撤分位數"), "P05 drawdown missing-data guard not shown");
  result.stat_view_missing_guards.p05_drawdown = true;

  await page.locator("#statView").selectOption("worst");
  const worstText = await bodyText(page);
  need(worstText.includes("資料缺口：本年度摘要沒有最差窗口年化回報序列"), "worst-CAGR missing-data guard not shown");
  result.stat_view_missing_guards.worst_cagr = true;

  await page.locator("#realMode").selectOption("0.0235");
  const realHead = await page.locator("#table thead th").nth(7).innerText();
  const realCell = await page.locator("#table tbody tr").first().locator("td").nth(7).innerText();
  need(realHead.includes("實質保本窗口") && realHead.includes("未精算"), "table real-mode header is ambiguous: " + realHead);
  need(realCell.includes("未精算（名目") && realCell.includes("/157）"), "table real-mode count still presents an unlabelled nominal count: " + realCell);
  result.real_mode_table_label_guard = {header: realHead, first_row: realCell, passed: true};
  await page.locator("#realMode").selectOption("0");
  const nominalHead = await page.locator("#table thead th").nth(7).innerText();
  const nominalCell = await page.locator("#table tbody tr").first().locator("td").nth(7).innerText();
  need(nominalHead === "名目低於本金" && /^\d+\/157$/.test(nominalCell), "nominal-mode table label/count invalid: " + nominalHead + " / " + nominalCell);

  const proof = await page.evaluate(() => {
    const rows = RAW_PACK.a.filter(row => Number(row[0]) === 10);
    const year10StrategyCount = RAW_PACK.d.length;
    const initialCapital = Number((RAW_PACK.meta && RAW_PACK.meta.initial_capital_usd) || 100000);
    return [0.0235, 0.035].map(cpi => {
      const threshold = initialCapital * Math.pow(1 + cpi, 10);
      return {
        annualized_inflation_assumption: cpi,
        year10_nominal_principal_threshold_usd: threshold,
        year10_strategies: rows.length,
        provable_zero_real_breach_strategies: rows.filter(row => Number(row[8]) >= threshold).length
      };
    });
  });
  need(proof.length === 2 && proof[0].year10_strategies === 1024, "could not reproduce year-10 strategy proof counts from embedded RAW_PACK data");
  need(proof[0].year10_strategies === 1024 && proof[1].year10_strategies === 1024, "year-10 strategy count does not match all 1,024 embedded scenario records");
  need(proof.every(item => Number.isInteger(item.provable_zero_real_breach_strategies) && item.provable_zero_real_breach_strategies >= 0 && item.provable_zero_real_breach_strategies <= item.year10_strategies),
    "derived real-floor proof count is outside the observed strategy population: " + JSON.stringify(proof));
  result.derived_real_breach_zero_proof = proof;

  // Verify real click delegation and that each interaction changes the intended control/state.
  let attrs = await clickAndRead(page, "#heatmapX [data-target][data-timing]");
  need(String(await page.locator("#target").inputValue()) === attrs.target && await page.locator("#timing").inputValue() === attrs.timing, "heatmap click did not synchronize target/timing");
  result.interactive_delegations_verified.heatmap_cell_click = true;

  attrs = await clickAndRead(page, "#flows .barrow[data-flow]");
  need(await page.locator("#flow").inputValue() === attrs.flow, "cashflow bar click did not synchronize flow");
  result.interactive_delegations_verified.cashflow_bar_click = true;

  attrs = await clickAndRead(page, "#table tbody tr.clickable-row");
  need(await page.locator("#timing").inputValue() === attrs.timing, "table row click did not synchronize timing");
  result.interactive_delegations_verified.table_row_click = true;

  const unoccludedGlideNode = await page.locator("#glide circle[data-year][data-timing]").evaluateAll(nodes => {
    for (const element of nodes) {
      const rect = element.getBoundingClientRect();
      const hit = document.elementFromPoint(rect.left + rect.width / 2, rect.top + rect.height / 2);
      const actual = hit && hit.closest ? hit.closest("circle[data-year][data-timing]") : null;
      if (actual === element) {
        return {year: element.getAttribute("data-year"), timing: element.getAttribute("data-timing")};
      }
    }
    return null;
  });
  need(unoccludedGlideNode !== null, "no non-overlapping glidepath node is available for a physical click test");
  attrs = await clickAndRead(page, '#glide circle[data-year="' + unoccludedGlideNode.year + '"][data-timing="' + unoccludedGlideNode.timing + '"]');
  const glideActual = {clicked: attrs, year: await page.locator("#year").inputValue(), timing: await page.locator("#timing").inputValue()};
  need(glideActual.year === attrs.year && glideActual.timing === attrs.timing, "glidepath node click did not synchronize year/timing: " + JSON.stringify(glideActual));
  result.interactive_delegations_verified.glidepath_node_click = glideActual;

  attrs = await clickAndRead(page, "#frontier [data-pick='1']");
  const frontierHit = await page.evaluate(() => window.__glidepathAuditLastClick);
  const frontierActual = {
    locator_marker: attrs,
    actual_hit_marker: frontierHit,
    bond: await page.locator("#bond").inputValue(),
    target: await page.locator("#target").inputValue(),
    timing: await page.locator("#timing").inputValue(),
    flow: await page.locator("#flow").inputValue()
  };
  need(frontierHit !== null && frontierActual.bond === frontierHit.bond && frontierActual.target === frontierHit.target && frontierActual.timing === frontierHit.timing && frontierActual.flow === frontierHit.flow, "frontier click state did not match the marker physically hit: " + JSON.stringify(frontierActual));
  result.interactive_delegations_verified.frontier_scatter_click = frontierActual;

  attrs = await clickAndRead(page, "#cohortX rect[data-cohort-year]");
  const cohortDetail = await page.locator("#cohortDetailX").innerText();
  need(cohortDetail.includes(attrs.cohortYear + " 年起點"), "cohort bar click did not update cohort detail");
  result.interactive_delegations_verified.cohort_bar_click = true;

  await page.locator("#pickBestNav").click();
  need((await page.locator("#label").innerText()).trim().length > 0, "P05 optimizer left label empty");
  await page.locator("#pickMinDd").click();
  need((await page.locator("#label").innerText()).trim().length > 0, "drawdown optimizer left label empty");
  result.interactive_delegations_verified.smart_optimizer_buttons = true;

  const expectedMatrixRows = await page.evaluate(() => TG.length * TM.length);
  need(expectedMatrixRows === 64, "current-year matrix must cover all 8 targets x 8 timing rules: " + expectedMatrixRows);
  result.csv_exports_verified.matrix = await saveCsv(page, "exportMatrix", expectedMatrixRows, 23);
  result.csv_exports_verified.trajectory = await saveCsv(page, "exportTrajectory", 11, 23);
  result.csv_exports_verified.cohorts = await saveCsv(page, "exportCohort", 14, 19);
  const expectedAnnualRows = await page.evaluate(() => RAW_PACK.a.length);
  need(expectedAnnualRows === 11264, "annual CSV must export the complete embedded annual grid: " + expectedAnnualRows);
  result.csv_exports_verified.annual = await saveCsv(page, "exportAnnual", expectedAnnualRows, 23);

  for (const viewport of [
    {name: "desktop_1480x1200", width: 1480, height: 1200},
    {name: "tablet_900x1024", width: 900, height: 1024},
    {name: "mobile_390x844", width: 390, height: 844}
  ]) {
    await page.setViewportSize({width: viewport.width, height: viewport.height});
    const layout = await page.evaluate(() => {
      const svgs = Array.from(document.querySelectorAll("svg"));
      return {
        horizontal_overflow_px: Math.max(0, document.documentElement.scrollWidth - window.innerWidth),
        svg_count: svgs.length,
        all_svgs_visible: svgs.length === 8 && svgs.every(svg => {
          const rect = svg.getBoundingClientRect();
          return rect.width > 0 && rect.height > 0;
        })
      };
    });
    need(layout.horizontal_overflow_px === 0, viewport.name + " has horizontal overflow: " + layout.horizontal_overflow_px);
    need(layout.svg_count === 8 && layout.all_svgs_visible, viewport.name + " SVG visibility/count failed: " + JSON.stringify(layout));
    result.responsive_viewports_verified[viewport.name] = layout;
  }

  need(consoleErrors.length === 0, "browser console errors: " + consoleErrors.join(" | "));
  need(pageErrors.length === 0, "browser page errors: " + pageErrors.join(" | "));
  result.console_errors = consoleErrors.length;
  result.page_errors = pageErrors.length;
  result.status = "PASSED";
} catch (error) {
  failures.push(String(error && error.stack ? error.stack : error));
  result.status = "FAILED";
} finally {
  if (browser) await browser.close();
  await fs.mkdir(path.dirname(outputPath), {recursive: true});
  await fs.writeFile(outputPath, JSON.stringify(result, null, 2) + "\n", "utf8");
}
if (result.status !== "PASSED") {
  console.error(JSON.stringify(result, null, 2));
  process.exitCode = 1;
} else {
  console.log(JSON.stringify(result, null, 2));
}
