"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const root = path.join(__dirname, "..");
const terminal = fs.readFileSync(path.join(root, "index.html"), "utf8");
const lab = fs.readFileSync(path.join(root, "option_chain_lab.html"), "utf8");

// Keep the measured overlay result visible in both operator surfaces.
// The NAV gap is a matched-date overlay/control difference, never a full strategy return.
for (const [name, html] of [["terminal", terminal], ["option-chain lab", lab]]) {
  assert.ok(html.includes("−$5,552"), name + ": last paired-date NAV gap must be disclosed");
  assert.ok(html.includes("32 / 1,947"), name + ": positive paired-day count must be disclosed");
  assert.ok(html.includes("24 unmatched"), name + ": unmatched sessions must not be hidden");
  assert.match(html, /not the full Frozen Original Hybrid composite/i,
    name + ": isolated control must not be conflated with the full hybrid");
  assert.match(html, /not confirmed fills/i,
    name + ": EOD quote-side replay must not be presented as confirmed fills");
  assert.ok(html.includes("42% QQQ core total-return proxy plus static 58% cash"),
    name + ": no-call control definition must remain explicit");
}
assert.ok(terminal.includes("−$5,646 closed-trade P&amp;L"),
  "terminal: zero-cost closed-trade economics must remain visible");

console.log("research_lockbox=PASS");
