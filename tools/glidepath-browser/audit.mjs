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
  need(geometry.non_finite === 0 && geometry.min >= 81 && geometry.max <= 180, "glidepath circle geometry out of bounds: " + JSON.stringify(geometry));
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
        all_svgs_visible: svgs.length === 9 && svgs.every(svg => {
          const rect = svg.getBoundingClientRect();
          return rect.width > 0 && rect.height > 0;
        })
      };
    });
    need(layout.horizontal_overflow_px === 0, viewport.name + " has horizontal overflow: " + layout.horizontal_overflow_px);
    need(layout.svg_count === 9 && layout.all_svgs_visible, viewport.name + " SVG visibility/count failed: " + JSON.stringify(layout));
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
