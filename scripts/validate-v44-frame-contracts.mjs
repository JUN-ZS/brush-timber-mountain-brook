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

const ids = [...html.matchAll(/assertCase\(['"](GT-\d+)['"]/g)].map((m) => m[1]);
assert.equal(ids.length, 52, "Golden Test count must match the user-visible 52-test label");
assert.equal(new Set(ids).size, 52, "Golden Test IDs must be unique");
for (let n = 1; n <= 52; n++) assert.ok(ids.includes("GT-" + String(n).padStart(2, "0")), "missing GT-" + String(n).padStart(2, "0"));

const helperStart = html.indexOf("// Scenario assumptions are explicit hypotheses");
const helperEnd = html.indexOf("const SharedContractEngine = {", helperStart);
assert.ok(helperStart >= 0 && helperEnd > helperStart, "assumption/parser module markers missing");
const helpers = html.slice(helperStart, helperEnd);
const contractChecks = [
  "const qqq = parseOccOptionId(\\"QQQ261120C00820000\\");",
  "if (!qqq || qqq.root !== \\"QQQ\\" || qqq.expiryDate !== \\"2026-11-20\\" || qqq.optionType !== \\"C\\" || qqq.strike !== 820) throw new Error(\\"QQQ OCC ID parse mismatch\\");",
  "const vxxPut = parseOccOptionId(\\"VXX261120P00015000\\");",
  "if (!vxxPut || vxxPut.root !== \\"VXX\\" || vxxPut.optionType !== \\"P\\" || vxxPut.strike !== 15) throw new Error(\\"VXX put OCC ID parse mismatch\\");",
  "if (parseOccOptionId(\\"VXX2613320C00021000\\") !== null) throw new Error(\\"invalid OCC expiry must be rejected\\");",
  "const b = resolveFrameAssumptions({ assumptionProfile: \\"BASELINE\\" });",
  "const c = resolveFrameAssumptions({ assumptionProfile: \\"CONSERVATIVE\\" });",
  "const st = resolveFrameAssumptions({ assumptionProfile: \\"STRESS\\" });",
  "if (b.qqqCallMaxLossBudgetFraction !== 0.012 || b.vxxCallMaxLossBudgetFraction !== 0.020 || b.vxxPutMaxLossBudgetFraction !== 0.010) throw new Error(\\"baseline changed unexpectedly\\");",
  "if (!(c.qqqCallMaxLossBudgetFraction < b.qqqCallMaxLossBudgetFraction && st.qqqCallMaxLossBudgetFraction < c.qqqCallMaxLossBudgetFraction)) throw new Error(\\"profiles are not ordered by capacity severity\\");",
  "if (st.evidenceClass !== \\"HYPOTHETICAL_SCENARIO_NOT_OBSERVED\\") throw new Error(\\"profile evidence class missing\\");"
].join("\\n");
assert.doesNotThrow(() => vm.runInNewContext(helpers + "\\n" + contractChecks, {}), "OCC parser/profile logic failed");

requireText(html, /BLOCKED_STRIKE_WIDTH_MISMATCH/, "strike-width inconsistency guard is missing");
requireText(html, /BLOCKED_LEG_STRIKE_ID_MISMATCH/, "strike encoded in contract ID is not checked");
requireText(html, /BLOCKED_LEG_OPTION_TYPE_MISMATCH/, "option type encoded in contract ID is not checked");
requireText(html, /BLOCKED_LEG_EXPIRY_MISMATCH/, "leg expiry consistency guard is missing");
requireText(html, /PENDING_LEG_QUOTE_TIMESTAMP/, "per-leg quote timestamp gate is missing");
requireText(html, /PENDING_LEG_SOURCE_REFERENCE/, "per-leg source reference gate is missing");
requireText(html, /USER_ASSERTED_NOT_INDEPENDENTLY_VERIFIED/, "user-supplied evidence class is not labelled");
requireText(html, /HUB_PREFLIGHT_CONFIG_READY/, "HUB label must describe preflight, not actual execution");
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
