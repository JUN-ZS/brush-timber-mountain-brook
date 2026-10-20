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
          badAttributes.push({tag: element.tagName, name: attribute.name, value: attribute.value});
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
  const summaryPlacement = await page.evaluate(() => ({
    summaryBeforeControls: document.querySelector("#decisionSummary").compareDocumentPosition(document.querySelector(".controls")) & Node.DOCUMENT_POSITION_FOLLOWING ? true : false,
    metricsBeforeControls: document.querySelector("#metrics").compareDocumentPosition(document.querySelector(".controls")) & Node.DOCUMENT_POSITION_FOLLOWING ? true : false,
    initialLead: document.querySelector("#decisionLead").innerText,
    initialValue: document.querySelector("#decisionPrimaryValue").innerText,
    initialBehavior: document.querySelector("#decisionBehaviorHeadline").innerText,
    initialAllocation: document.querySelector("#decisionAllocationHeadline").innerText,
    initialAllocationDetail: document.querySelector("#decisionAllocationDetail").innerText,
    initialFlow: document.querySelector("#decisionFlowHeadline").innerText,
    initialFloor: document.querySelector("#decisionFloorHeadline").innerText
  }));
  need(summaryPlacement.summaryBeforeControls && summaryPlacement.metricsBeforeControls, "decision outputs are not positioned ahead of controls");
  need(summaryPlacement.initialLead.includes("AGG") && summaryPlacement.initialLead.includes("60%") && summaryPlacement.initialLead.includes("第5年"), "initial decision summary does not state the selected strategy/year");
  need(summaryPlacement.initialValue.startsWith("$") && summaryPlacement.initialBehavior.length > 0 && summaryPlacement.initialAllocation.includes("股票") && summaryPlacement.initialFlow.includes("不提款") && summaryPlacement.initialFloor.includes("$"), "initial decision summary is missing amount/behavior/data fields");
  need(summaryPlacement.initialAllocationDetail.includes("按主結果 $167,812") && summaryPlacement.initialAllocationDetail.includes("股票約 $98,590") && summaryPlacement.initialAllocationDetail.includes("AGG 約 $69,222"), "initial allocation dollar split must reconcile to the displayed NAV and allocation percentages");
  result.frontloaded_decision_summary = { ...summaryPlacement, passed: true };

  await page.locator("#decisionTrajectory[data-state]").waitFor({state: "visible", timeout: 5000});
  const readTrajectory = () => page.evaluate(() => {
    const root = document.querySelector("#decisionTrajectory");
    const values = series => Array.from(root.querySelectorAll('[data-series="' + series + '"] td[data-year]'));
    const stocks = values("stock").map(cell => Number(cell.dataset.stockPct));
    const bonds = values("bond").map(cell => Number(cell.dataset.bondPct));
    const years = Array.from(root.querySelectorAll("[data-trajectory-year]")).map(button => Number(button.getAttribute("data-trajectory-year")));
    const idValues = Array.from(document.querySelectorAll("[id]")).map(node => node.id);
    const duplicates = Array.from(new Set(idValues.filter((id, index) => idValues.indexOf(id) !== index)));
    return {
      state: root.dataset.state,
      panel_after_summary: !!(document.querySelector("#decisionSummary").compareDocumentPosition(root) & Node.DOCUMENT_POSITION_FOLLOWING),
      panel_before_controls: !!(root.compareDocumentPosition(document.querySelector(".controls")) & Node.DOCUMENT_POSITION_FOLLOWING),
      selected_year: root.dataset.year,
      target: Number(root.dataset.target),
      timing: root.dataset.timing,
      endpoint_bond_pct: Number(root.dataset.endpointBondPct),
      year_buttons: years,
      selected_button_count: root.querySelectorAll('[data-trajectory-year][aria-pressed="true"]').length,
      selected_button_year: Number(root.querySelector('[data-trajectory-year][aria-pressed="true"]')?.getAttribute("data-trajectory-year")),
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
  need(initialTrajectory.year_buttons.length === 11 && initialTrajectory.year_buttons.every((year, index) => year === index), "trajectory panel does not expose years 0-10: " + JSON.stringify(initialTrajectory.year_buttons));
  need(initialTrajectory.stock_pcts.length === 11 && initialTrajectory.bond_pcts.length === 11, "trajectory panel is missing annual stock/bond rows");
  need(initialTrajectory.selected_year === "5" && initialTrajectory.selected_button_count === 1 && initialTrajectory.selected_button_year === 5, "trajectory panel did not highlight the selected year 5");
  need(Math.abs(initialTrajectory.endpoint_bond_pct - initialTrajectory.target) <= 0.75, "year-10 bond target does not match selected target: " + JSON.stringify(initialTrajectory));
  need(initialTrajectory.stock_bond_sums.every(value => Math.abs(value - 100) <= 0.02), "trajectory stock and bond percentages do not sum to 100: " + JSON.stringify(initialTrajectory.stock_bond_sums));
  need(initialTrajectory.crosscheck_text.includes("歷史回測摘要") && initialTrajectory.crosscheck_text.includes("差異"), "trajectory does not compare rule path with historical backtest allocation");
  need(initialTrajectory.rendered_duplicate_ids.length === 0, "trajectory panel caused duplicate rendered IDs: " + JSON.stringify(initialTrajectory.rendered_duplicate_ids));
  result.glidepath_decision_trajectory = {initial: initialTrajectory, passed: true};

  await page.locator('#decisionTrajectory button[data-trajectory-year="9"]').click({timeout: 5000});
  await page.waitForTimeout(150);
  const year9State = await page.evaluate(() => ({
    controlValue: document.querySelector("#year")?.value ?? null,
    panelYear: document.querySelector("#decisionTrajectory")?.dataset.year ?? null,
    selectedYearButtons: Array.from(document.querySelectorAll("#decisionTrajectory [data-trajectory-year][aria-pressed='true']")).map(node => node.getAttribute("data-trajectory-year")),
    summaryLead: document.querySelector("#decisionLead")?.innerText ?? "",
    buttonCount: document.querySelectorAll('#decisionTrajectory button[data-trajectory-year="9"]').length
  }));
  result.glidepath_decision_trajectory.year9_click_state = year9State;
  need(year9State.controlValue === "9" && year9State.panelYear === "9" && year9State.selectedYearButtons.join(",") === "9", "trajectory year click did not synchronize source control and panel state: " + JSON.stringify(year9State));
  need(year9State.summaryLead.includes("第9年"), "trajectory year click did not update the frontloaded decision summary: " + JSON.stringify(year9State));
  need(await page.locator('#decisionTrajectory button[data-trajectory-year="9"]').getAttribute("aria-pressed") === "true", "trajectory year-9 click did not highlight year 9");
  await page.locator('#decisionTrajectory button[data-trajectory-year="5"]').click({timeout: 5000});
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
  result.frontloaded_decision_summary.updated_state = {...changedSummary, passed:true};

  await page.waitForFunction(() => {
    const root = document.querySelector("#decisionTrajectory");
    return root && root.dataset.target === "80" &&
      root.dataset.timing === "front_fast" && root.dataset.year === "5";
  }, null, {timeout: 5000});
  const changedTrajectory = await readTrajectory();
  need(changedTrajectory.state === "ready" && changedTrajectory.target === 80 && changedTrajectory.timing === "front_fast", "trajectory panel did not follow target/timing control changes: " + JSON.stringify(changedTrajectory));
  need(Math.abs(changedTrajectory.endpoint_bond_pct - 80) <= 0.75, "trajectory endpoint failed to update to 80% TLT target: " + JSON.stringify(changedTrajectory));
  need(changedTrajectory.selected_year === "5" && changedTrajectory.selected_button_year === 5, "trajectory selected-year highlight did not persist when strategy changed");
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
        need(bad.badAttributes.length === 0, "invalid SVG attribute appeared for year=" + year + ", inflation=" + inflation + ", stat=" + stat);
        result.state_matrix_combinations.push({year, inflation, stat});
        result.state_matrix_sweeps++;
      }
    }
  }
  result.rendered_dom_guard_passed = true;
  need(result.state_matrix_sweeps === 45, "state matrix did not complete 45 combinations");

  const geometry = await page.locator("#glide circle").evaluateAll(nodes => {
    const vals = nodes.map(node => Number(node.getAttribute("cy")));
    return {count: vals.length, min: Math.min(...vals), max: Math.max(...vals), non_finite: vals.filter(value => !Number.isFinite(value)).length};
  });
  need(geometry.count === 66, "expected 66 glidepath circle nodes, got " + geometry.count);
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
    return [0.0235, 0.035].map(cpi => {
      const threshold = 100000 * Math.pow(1 + cpi, 10);
      return {
        annualized_inflation_assumption: cpi,
        year10_nominal_principal_threshold_usd: threshold,
        year10_strategies: rows.length,
        provable_zero_real_breach_strategies: rows.filter(row => Number(row[8]) >= threshold).length
      };
    });
  });
  need(proof.length === 2 && proof[0].year10_strategies === 768, "could not reproduce year-10 strategy proof counts from embedded RAW_PACK data");
  need(proof[0].provable_zero_real_breach_strategies === 363, "2.35% zero-breach proof count differs: " + JSON.stringify(proof[0]));
  need(proof[1].provable_zero_real_breach_strategies === 329, "3.50% zero-breach proof count differs: " + JSON.stringify(proof[1]));
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

  result.csv_exports_verified.matrix = await saveCsv(page, "exportMatrix", 48, 23);
  result.csv_exports_verified.trajectory = await saveCsv(page, "exportTrajectory", 11, 23);
  result.csv_exports_verified.cohorts = await saveCsv(page, "exportCohort", 14, 19);
  result.csv_exports_verified.annual = await saveCsv(page, "exportAnnual", 8448, 23);

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
