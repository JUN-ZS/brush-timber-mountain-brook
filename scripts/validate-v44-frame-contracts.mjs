import fs from "node:fs";
import vm from "node:vm";
import assert from "node:assert/strict";

const htmlPath = "qqq_hybrid_v4_4_issue_107_frame_vxx_48_golden_tests.html";
const html = fs.readFileSync(htmlPath, "utf8");
const workflow = fs.readFileSync(".github/workflows/rolling-floor.yml", "utf8");
const ledger = fs.readFileSync("docs/QQQ_HYBRID_V44_ASSUMPTION_LEDGER_V1.md", "utf8");

function requireText(source, pattern, message) {
  assert.ok(pattern.test(source), message);
}

let inlineCount = 0;
for (const match of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)) {
  const attrs = match[1] || "";
  const body = match[2] || "";
  if (/\bsrc\s*=/.test(attrs) || !body.trim()) continue;
  assert.doesNotThrow(() => new vm.Script(body, { filename: htmlPath + "#inline-" + inlineCount }), "inline JavaScript syntax failed at block " + inlineCount);
  inlineCount++;
}
assert.ok(inlineCount >= 1, "expected at least one inline JavaScript block");

// Execute the actual SharedContractEngine and its actual 52-case Golden Test function
// in a VM with DOM-ready callbacks deliberately disabled. This does not run browser UI or HUB.
const inlineScripts = [...html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)]
  .filter(m => !/\bsrc\s*=/.test(m[1] || "") && (m[2] || "").includes("const SharedContractEngine = {"));
assert.equal(inlineScripts.length, 1, "expected exactly one core application script");
const coreScript = inlineScripts[0][2];
const fakeDocument = {
  addEventListener() {},
  querySelectorAll() { return []; },
  getElementById() { return { value: "", textContent: "", innerHTML: "", className: "", addEventListener() {} }; }
};
const browserContext = vm.createContext({
  window: { addEventListener() {} },
  document: fakeDocument,
  console,
  setTimeout,
  clearTimeout
});
const exposedScript = coreScript + "\n;globalThis.__v44Harness = { runAutomated52GoldenTests, SharedContractEngine, PRESETS, resolveFrameAssumptions, VerifiedSourceStore };";
assert.doesNotThrow(() => vm.runInContext(exposedScript, browserContext, { timeout: 10000 }), "core app script could not initialize in isolated test VM");
const actualGoldenResults = browserContext.__v44Harness.runAutomated52GoldenTests();
assert.equal(actualGoldenResults.length, 52, "engine's actual Golden Test function must return 52 results");
const actualFailures = actualGoldenResults.filter(r => !r.passed);
if (actualFailures.length) {
  const E0 = browserContext.__v44Harness.SharedContractEngine;
  const P0 = browserContext.__v44Harness.PRESETS;
  const sample = E0.evaluateDecision(P0.live_thin);
  console.log("GOLDEN FAILURE DETAILS:", JSON.stringify(actualFailures.map(r => ({id:r.id, name:r.name, detail:r.detail}))));
  console.log("BASELINE CANDIDATE DIAGNOSTICS:", JSON.stringify({
    preset: Object.fromEntries(["todayDate","quoteAsOf","candidateState","quoteProvenance","candVxxShortAsOf","candVxxLongAsOf","candVxxShortSourceRef","candVxxLongSourceRef","candVxxWidth","candVxxLegStrikes"].map(k => [k, P0.live_thin[k]])),
    qqq: {valid:sample.candEval.qqqCand.valid,status:sample.candEval.qqqCand.status,reason:sample.candEval.qqqCand.reason},
    vxx: {valid:sample.candEval.vxxCand.valid,status:sample.candEval.vxxCand.status,reason:sample.candEval.vxxCand.reason},
    put: {valid:sample.candEval.vxxPutCand.valid,status:sample.candEval.vxxPutCand.status,reason:sample.candEval.vxxPutCand.reason},
    fullQqqCalls:sample.fullQqqCalls,fullVxxCalls:sample.fullVxxCalls,fullVxxPuts:sample.fullVxxPuts,
    frameReady:sample.frameReady,hub:sample.hubEval.status,targetVxxPct:sample.targetVxxPct
  }));
}
assert.equal(actualFailures.length, 0, "actual Golden Tests failed: " + actualFailures.map(r => r.id + " " + r.name + " :: " + r.detail).join(" | "));

// Direct negative tests against actual engine method, not text-only assertions.
const E = browserContext.__v44Harness.SharedContractEngine;
const P = browserContext.__v44Harness.PRESETS;
const validBundle = E.buildContractBundle({
  inputs: { ...P.live_thin },
  barParams: { barNav:"100000", barRiskPct:"1.00", slippage:"0.05", commission:"0.65", spreadMult:"1.00", execLagDays:"1", ratioDir:"SHORT_HEAVY_PUT", ratioN:"5", quoteDepth:"25", marginVerified:"UNVERIFIED", shortStrikeInput:"820", holdingDay:"1", pmCurPnl:"0", pmDaysHeld:"1", pmDteLeft:"20", pmRiskUnitR:"1", pmRemUpside:"0", pmDistToStop:"0" },
  probParams: { regFilter:"ALL", customDrop:"5.0", maxVix:"50" },
  floorAndDveParams: { baseB:"100000", month:"12", actualPct:"12", s20:"15", s30:"14", s50:"14", dveWinProb:"80", dveSampleN:"35", dveGainPerUnit:"2000", dveLossPerUnit:"1000", dveAltName:"WAIT_T_BILL_10D", dveAltEv:"110", dveAltCap:"100000", dveFairMatch:"MATCHED", stressQqqCore:"0", stressVxxShort:"0", stressQqqCall:"0", stressVxxCall:"0", stressVxxPut:"0" },
  sourceState: browserContext.VerifiedSourceStore.exportState()
});
const width = E.evaluateDecision({ ...P.live_thin, candVxxWidth: "1", candVxxLegStrikes: "21/26" });
const type = E.evaluateDecision({ ...P.live_thin, candVxxLongId: "VXX261120P00026000" });
const expiry = E.evaluateDecision({ ...P.live_thin, candVxxLongId: "VXX261218C00026000" });
const strike = E.evaluateDecision({ ...P.live_thin, candVxxLongId: "VXX261120C00025000" });
const missingSource = E.evaluateDecision({ ...P.live_thin, candVxxLongSourceRef: "" });
const placeholderSource = E.evaluateDecision({ ...P.live_thin, candVxxShortSourceRef: "USER_SUPPLIED_UNVERIFIED" });
const engineChecks = {
  width: width.candEval.vxxCand.status,
  type: type.candEval.vxxCand.status,
  expiry: expiry.candEval.vxxCand.status,
  strike: strike.candEval.vxxCand.status,
  missingSource: missingSource.candEval.vxxCand.status,
  placeholderSource: placeholderSource.candEval.vxxCand.status,
  invalidWidthCapacity: width.candEval.vxxCand.fullQty
};
assert.equal(engineChecks.width, "BLOCKED_STRIKE_WIDTH_MISMATCH");
assert.equal(engineChecks.type, "BLOCKED_LEG_OPTION_TYPE_MISMATCH");
assert.equal(engineChecks.expiry, "BLOCKED_LEG_EXPIRY_MISMATCH");
assert.equal(engineChecks.strike, "BLOCKED_LEG_STRIKE_ID_MISMATCH");
assert.equal(engineChecks.missingSource, "PENDING_LEG_SOURCE_REFERENCE");
assert.equal(engineChecks.placeholderSource, "PENDING_LEG_SOURCE_REFERENCE");
assert.equal(engineChecks.invalidWidthCapacity, null);
assert.equal(validBundle.schema, "qqq-hybrid.shared-contract.v4.4");
assert.equal(validBundle.brokerOrdersAllowed, false);
assert.match(validBundle.baseEngineCommitRef, /^[0-9a-f]{40}$/);
assert.equal(E.verifyContractBundle(JSON.parse(JSON.stringify(validBundle))).ok, true);
const forgedBaseRef = JSON.parse(JSON.stringify(validBundle));
forgedBaseRef.baseEngineCommitRef = "0".repeat(40);
const forgedBaseResult = E.verifyContractBundle(forgedBaseRef);
assert.equal(forgedBaseResult.ok, false);
assert.match(forgedBaseResult.error, /BASE_ENGINE_COMMIT_MISMATCH/);

console.log("PASS actual SharedContractEngine Golden Tests:", actualGoldenResults.length + "/" + actualGoldenResults.length);
console.log("PASS direct engine negative contract probes:", JSON.stringify(engineChecks));


const ids = [...html.matchAll(/assertCase\(['"](GT-\d+)['"]/g)].map((m) => m[1]);
assert.equal(ids.length, 52, "Golden Test count must match the user-visible 52-test label");
assert.equal(new Set(ids).size, 52, "Golden Test IDs must be unique");
for (let n = 1; n <= 52; n++) assert.ok(ids.includes("GT-" + String(n).padStart(2, "0")), "missing GT-" + String(n).padStart(2, "0"));

const helperStart = html.indexOf("// Scenario assumptions are explicit hypotheses");
const helperEnd = html.indexOf("const SharedContractEngine = {", helperStart);
assert.ok(helperStart >= 0 && helperEnd > helperStart, "assumption/parser module markers missing");
const helpers = html.slice(helperStart, helperEnd);
const contractChecks = [
  'const qqq = parseOccOptionId("QQQ261120C00820000");',
  'if (!qqq || qqq.root !== "QQQ" || qqq.expiryDate !== "2026-11-20" || qqq.optionType !== "C" || qqq.strike !== 820) throw new Error("QQQ OCC ID parse mismatch");',
  'const vxxPut = parseOccOptionId("VXX261120P00015000");',
  'if (!vxxPut || vxxPut.root !== "VXX" || vxxPut.optionType !== "P" || vxxPut.strike !== 15) throw new Error("VXX put OCC ID parse mismatch");',
  'if (parseOccOptionId("VXX2613320C00021000") !== null) throw new Error("invalid OCC expiry must be rejected");',
  'const b = resolveFrameAssumptions({ assumptionProfile: "BASELINE" });',
  'const c = resolveFrameAssumptions({ assumptionProfile: "CONSERVATIVE" });',
  'const st = resolveFrameAssumptions({ assumptionProfile: "STRESS" });',
  'if (b.qqqCallMaxLossBudgetFraction !== 0.012 || b.vxxCallMaxLossBudgetFraction !== 0.020 || b.vxxPutMaxLossBudgetFraction !== 0.010) throw new Error("baseline changed unexpectedly");',
  'if (!(c.qqqCallMaxLossBudgetFraction < b.qqqCallMaxLossBudgetFraction && st.qqqCallMaxLossBudgetFraction < c.qqqCallMaxLossBudgetFraction)) throw new Error("profiles are not ordered by capacity severity");',
  'if (st.evidenceClass !== "HYPOTHETICAL_SCENARIO_NOT_OBSERVED") throw new Error("profile evidence class missing");',
  'if (isUsableLegSourceReference("USER_SUPPLIED_UNVERIFIED")) throw new Error("provenance placeholder must not count as a source reference");',
  'if (!isUsableLegSourceReference("SCREENSHOT:V44_source.png")) throw new Error("usable evidence pointer was rejected");'
].join("\n");
assert.doesNotThrow(() => vm.runInNewContext(helpers + "\n" + contractChecks, {}), "OCC parser/profile logic failed");

requireText(html, /BLOCKED_STRIKE_WIDTH_MISMATCH/, "strike-width inconsistency guard is missing");
requireText(html, /BLOCKED_LEG_STRIKE_ID_MISMATCH/, "strike encoded in contract ID is not checked");
requireText(html, /BLOCKED_LEG_OPTION_TYPE_MISMATCH/, "option type encoded in contract ID is not checked");
requireText(html, /BLOCKED_LEG_EXPIRY_MISMATCH/, "leg expiry consistency guard is missing");
requireText(html, /PENDING_LEG_QUOTE_TIMESTAMP/, "per-leg quote timestamp gate is missing");
requireText(html, /PENDING_LEG_SOURCE_REFERENCE/, "per-leg source reference gate is missing");
requireText(html, /isUsableLegSourceReference/, "source-ref placeholder validation is missing");
assert.match(html, /id="candVxxShortAsOf" type="text" value="" placeholder=/, "live VXX timestamp must start empty");
assert.match(html, /id="candVxxShortSourceRef" type="text" value="" placeholder=/, "live VXX source reference must start empty");
requireText(html, /USER_ASSERTED_NOT_INDEPENDENTLY_VERIFIED/, "user-supplied evidence class is not labelled");
requireText(html, /HUB_PREFLIGHT_CONFIG_READY/, "HUB label must describe preflight, not actual execution");
requireText(html, /version:\s*'qqq-hybrid\.shared-contract\.v4\.4'/, "shared contract version must be V4.4");
requireText(html, /frozenPolicyTargetVxxPct/, "frozen policy target must be separate from capacity-limited target");
requireText(html, /baseEngineCommitRef/, "V4.4 bundle must label inherited engine ancestry separately");
requireText(html, /BASE_ENGINE_COMMIT_MISMATCH/, "forged inherited-engine ancestry must be rejected");
assert.doesNotMatch(html, /commitRef:\s*this\.commitHash|SharedContractEngine\.commitHash/, "V4.4 must not present the V4.3 ancestry anchor as current commit");
assert.doesNotMatch(html, /status:\s*'VERIFIED_CONTRACT',/, "a user-asserted contract must not be labelled verified");
assert.doesNotMatch(html, /HUB_EXECUTION_VERIFIED_READY|VERIFIED_EXCHANGE_QUOTE|ADJUSTED_VERIFIED_25/, "misleading legacy evidence/status labels remain");

for (const id of [
  "inpAssumptionProfile", "inpVxxDeliverableEvidenceRef", "inpVxxDeliverableEvidenceSha",
  "candQqqShortAsOf", "candQqqLongAsOf", "candQqqShortSourceRef", "candQqqLongSourceRef",
  "candVxxShortAsOf", "candVxxLongAsOf", "candVxxShortSourceRef", "candVxxLongSourceRef",
  "candVxxPutShortAsOf", "candVxxPutLongAsOf", "candVxxPutShortSourceRef", "candVxxPutLongSourceRef"
]) {
  assert.ok(html.includes('id="' + id + '"'), "missing DOM field " + id);
  assert.ok(html.includes("'" + id + "'"), "field not present in PUSH/PULL or DOM mapping: " + id);
}

requireText(workflow, /default:\s*HOLD_AWAITING_USER_FRAME_ACCEPTANCE/, "HUB must default to HOLD");
requireText(workflow, /-\s*hub_only/, "HUB-only mode missing");
requireText(workflow, /if:\s*\$\{\{\s*inputs\.frame_acceptance == 'ACCEPTED_AFTER_FRAME_REVIEW'\s*\}\}/, "explicit user acceptance gate missing");
requireText(workflow, /runs-on:\s*\[self-hosted,\s*linux,\s*x64\]/, "HUB must use self-hosted Linux runner");
requireText(workflow, /grokbot-box-linux-x64/, "approved HUB runner name guard missing");
requireText(workflow, /source\.sha256[\s\S]*output\.sha256[\s\S]*run_manifest\.txt/, "source/output hashes and run manifest missing");
requireText(workflow, /needs\.ndx-linux\.result == 'success'[\s\S]*needs\.hub-web\.result == 'success'/, "bridge is not gated on successful required shards");
requireText(ledger, /HYPOTHETICAL_SCENARIO_NOT_OBSERVED/, "assumption ledger must classify scenario assumptions");
requireText(ledger, /independently verified/i, "assumption ledger must preserve evidence limitation");

console.log("PASS V4.4 static/frame checks");
console.log("inline JS blocks syntax-checked:", inlineCount);
console.log("Golden Tests defined:", ids.length, "(GT-01..GT-52)");
console.log("OCC parser/profile logic: PASS");
console.log("strike/leg/provenance/HUB guards: present");
console.log("NOTE: This is not a browser execution of all 52 Golden Tests and does not run HUB.");
