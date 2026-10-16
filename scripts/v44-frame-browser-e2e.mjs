import assert from "node:assert/strict";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { chromium } from "playwright";

const htmlPath = path.resolve("qqq_hybrid_v4_4_issue_107_frame_vxx_48_golden_tests.html");
const url = pathToFileURL(htmlPath).href;
const browser = await chromium.launch({
  headless: true,
  args: ["--no-sandbox", "--disable-dev-shm-usage"]
});
const pageErrors = [];
const failedRequests = [];

try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  page.on("pageerror", e => pageErrors.push(e.stack || e.message));
  page.on("requestfailed", request => failedRequests.push({ url: request.url(), error: request.failure()?.errorText || "failed" }));

  // The tested application logic is local/self-contained. Skip optional CDN styling/chart/font
  // payloads so this acceptance test is deterministic and does not depend on public CDN uptime.
  await page.route("https://**/*", route => route.abort());
  await page.addInitScript(() => {
    window.tailwind = window.tailwind || {};
    window.Chart = class {
      constructor(_context, config = {}) {
        this.config = config;
        this.data = config.data || { labels: [], datasets: [] };
        this.options = config.options || {};
      }
      update() {}
      destroy() {}
      resize() {}
    };
  });

  await page.goto(url, { waitUntil: "load", timeout: 30000 });
  await page.waitForFunction(() => {
    const badge = document.querySelector("#goldenSuiteSummaryBadge");
    return badge && badge.textContent.includes("52 / 52 PASS");
  }, null, { timeout: 30000 });

  // 1. The browser actually loads the HTML, wires events and renders 52 successful tests.
  await page.locator('.nav-tab[data-tab="tab-audit"]').click();
  await page.locator("#btnRunGoldenTests").click();
  const resultRows = await page.locator("#goldenTestsResultList > div").count();
  assert.equal(resultRows, 52, "browser rendered Golden Test rows");
  const failingRows = await page.locator("#goldenTestsResultList").innerText();
  assert.doesNotMatch(failingRows, /\[FAIL\]/, "browser Golden Test results contain a failure");
  assert.match(await page.locator("#goldenSuiteSummaryBadge").innerText(), /52\s*\/\s*52 PASS/);

  // 2. The real UI changes assumptions and refreshes the visible assumptions ledger.
  const assumptions = page.locator("#frameAssumptionLedger");
  await page.locator("#inpAssumptionProfile").selectOption("CONSERVATIVE");
  await page.waitForFunction(() => document.querySelector("#frameAssumptionLedger")?.innerText.includes("CONSERVATIVE"));
  assert.match(await assumptions.innerText(), /FROZEN-VXX-POLICY-TARGET/);
  assert.match(await assumptions.innerText(), /CAPACITY-LIMITED-TARGET/);
  await page.locator("#inpAssumptionProfile").selectOption("STRESS");
  await page.waitForFunction(() => document.querySelector("#frameAssumptionLedger")?.innerText.includes("STRESS"));
  await page.locator("#inpAssumptionProfile").selectOption("BASELINE");
  await page.waitForFunction(() => document.querySelector("#frameAssumptionLedger")?.innerText.includes("BASELINE"));

  // 3. UI-level width mismatch must surface as BLOCKED and must not present a FULL capacity.
  await page.locator('.nav-tab[data-tab="tab-cockpit"]').click();
  await page.locator("#candVxxWidth").fill("1");
  await page.waitForFunction(() => document.querySelector("#aiReviewPackTextarea")?.value.includes("BLOCKED_STRIKE_WIDTH_MISMATCH"));
  const badWidthReport = await page.locator("#aiReviewPackTextarea").inputValue();
  assert.match(badWidthReport, /BLOCKED_STRIKE_WIDTH_MISMATCH/);
  assert.match(badWidthReport, /FULL\s*=\s*null|FULL = null/i);
  await page.locator("#candVxxWidth").fill("5");

  // 4. Export a complete V4.4 bundle, mutate multiple controls, then PULL via the visible modal.
  await page.locator("#inpAssumptionProfile").selectOption("STRESS");
  const originalCash = await page.locator("#inpCash").inputValue();
  const originalProfile = await page.locator("#inpAssumptionProfile").inputValue();
  await page.locator("#btnExportJson").click();
  const exportedJson = await page.locator("#importJsonTextarea").inputValue();
  const bundle = JSON.parse(exportedJson);
  assert.equal(bundle.schema, "qqq-hybrid.shared-contract.v4.4");
  assert.equal(bundle.brokerOrdersAllowed, false);
  assert.match(bundle.hashes.sourceHash, /^[0-9a-f]{64}$/);
  assert.match(bundle.hashes.scenarioHash, /^[0-9a-f]{64}$/);
  assert.match(bundle.hashes.engineOutputHash, /^[0-9a-f]{64}$/);
  assert.equal(bundle.state.inputs.assumptionProfile, "STRESS");

  await page.locator("#inpCash").fill("43210");
  await page.locator("#inpAssumptionProfile").selectOption("BASELINE");
  await page.locator("#btnOpenImportModal").click();
  await page.locator("#importJsonTextarea").fill(JSON.stringify(bundle));
  await page.locator("#btnApplyImportJson").click();
  assert.equal(await page.locator("#inpCash").inputValue(), originalCash, "valid PULL restores original cash");
  assert.equal(await page.locator("#inpAssumptionProfile").inputValue(), originalProfile, "valid PULL restores assumption profile");
  await page.waitForFunction(() => document.querySelector("#importJsonModal")?.classList.contains("hidden"));

  // 5. A deliberately corrupted hash must be rejected transactionally without overwriting current state.
  await page.locator("#inpCash").fill("34567");
  const cashBeforeBadPull = await page.locator("#inpCash").inputValue();
  const badBundle = structuredClone(bundle);
  badBundle.hashes.scenarioHash = "0".repeat(64);
  await page.locator("#btnOpenImportModal").click();
  await page.locator("#importJsonTextarea").fill(JSON.stringify(badBundle));
  await page.locator("#btnApplyImportJson").click();
  assert.equal(await page.locator("#inpCash").inputValue(), cashBeforeBadPull, "failed PULL preserves pre-commit state");
  assert.match(await page.locator("#importJsonTextarea").inputValue(), /PULL.*拒絕|已拒絕提交|SCENARIO_HASH_MISMATCH/i);

  // 6. Exercise the built-in Clear -> PULL -> field/hash comparison from the real DOM.
  await page.locator("#btnCloseImportModal").click();
  await page.locator("#btnRunBrowserRoundTrip").click();
  await page.waitForFunction(() => document.querySelector("#e2eRoundTripBadge")?.textContent.startsWith("PASS"));
  const roundTripBadge = await page.locator("#e2eRoundTripBadge").innerText();
  const roundTripReport = await page.locator("#e2eRoundTripReport").innerText();
  assert.match(roundTripBadge, /PASS/);
  assert.match(roundTripReport, /sourceHashMatch=true/i);
  assert.match(roundTripReport, /完整 VerifiedSourceStore/);

  assert.deepEqual(pageErrors, [], "uncaught browser JavaScript errors");
  console.log("PASS V4.4 Playwright browser E2E");
  console.log("Golden Test rows:", resultRows, "(all PASS)");
  console.log("Assumption profiles: BASELINE / CONSERVATIVE / STRESS UI events PASS");
  console.log("Width mismatch UI gate: BLOCKED, FULL=null");
  console.log("PUSH/PULL schema + three hashes: PASS");
  console.log("Corrupt-hash import rollback: PASS");
  console.log("Browser round-trip:", roundTripBadge);
  console.log("Uncaught browser errors:", pageErrors.length);
  console.log("Optional CDN requests blocked:", failedRequests.length);
} catch (error) {
  console.error("FAIL V4.4 Playwright browser E2E:", error.stack || error);
  if (pageErrors.length) console.error("BROWSER PAGE ERRORS:", JSON.stringify(pageErrors, null, 2));
  throw error;
} finally {
  await browser.close();
}
