/** Tiny harness: load engine.js candidateFromChain for Cell 10.
 * Usage: node cell10_select_candidate.js <payload.json>
 * payload: { calls:[...], spot:number, targetDelta?:number, targetDte?:number, asOf?:string|null }
 * Prints JSON candidate or {"candidate":null}.
 */
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
globalThis.window = {};
vm.runInThisContext(fs.readFileSync(path.join(here, "..", "engine.js"), "utf8"));
const E = globalThis.window.HybridEngineV3;

const file = process.argv[2];
if (!file) {
  console.error("usage: node cell10_select_candidate.js <payload.json>");
  process.exit(2);
}
const payload = JSON.parse(fs.readFileSync(file, "utf8"));
const spot = Number(payload.spot);
const targetDelta = payload.targetDelta != null ? Number(payload.targetDelta) : 0.10;
const targetDte = payload.targetDte != null ? Number(payload.targetDte) : E.POLICY.optionTargetDte;
const asOf = payload.asOf != null ? payload.asOf : null;
const cand = E.candidateFromChain(payload.calls || payload, spot, targetDelta, targetDte, asOf);
process.stdout.write(JSON.stringify({ candidate: cand == null ? null : cand }) + "\n");
