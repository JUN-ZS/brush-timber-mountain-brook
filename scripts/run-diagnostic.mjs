#!/usr/bin/env node
/**
 * Cross-platform wrapper: python3 → python → py
 * Always forwards --diagnostic --futu-test unless the user passed flags.
 */
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const extra = process.argv.slice(2);
const flags = extra.length ? extra : ["--diagnostic", "--futu-test"];
const args = ["-m", "backtest.local_diagnostic", ...flags];
const bins =
  process.platform === "win32" ? ["py", "python", "python3"] : ["python3", "python", "py"];

let lastErr = "";
for (const bin of bins) {
  const r = spawnSync(bin, args, { cwd: root, stdio: "inherit", shell: process.platform === "win32" });
  if (r.error && r.error.code === "ENOENT") {
    lastErr = `${bin} not found`;
    continue;
  }
  process.exit(r.status ?? 1);
}
console.error(`No Python interpreter found (${bins.join(", ")}). Install Python 3.10+ then retry.`);
if (lastErr) console.error(lastErr);
process.exit(1);
