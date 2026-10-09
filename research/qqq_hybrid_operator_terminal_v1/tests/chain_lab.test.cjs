"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const sandbox = { module: { exports: {} } };
vm.runInNewContext(fs.readFileSync(require.resolve("../option_chain_lab.js"), "utf8"), sandbox, { filename: "option_chain_lab.js" });
const Lab = sandbox.module.exports;
const s = Lab.SAMPLE;
function near(a,b,label){assert.ok(Math.abs(a-b)<1e-8,label+": expected "+b+", got "+a);}

// Screenshot sample must match the canonical repository fixture.
// QQQ CALL: 799 bid $3.16; 810 protective wing ask $1.89.
const call = Lab.calculateVerticals("QQQ_CALL",s.chains.QQQ_CALL,100,3200);
const q1=call.candidates.find(x=>x.key==="799C/805C");
const q2=call.candidates.find(x=>x.key==="799C/810C");
assert.ok(q1 && q2);
near(q1.credit,.76,"QQQ 799/805 net credit per share");
near(q1.maxProfit,76,"QQQ 799/805 max profit");
near(q1.maxLoss,524,"QQQ 799/805 max loss");
near(q1.breakEven,799.76,"QQQ 799/805 breakeven");
near(q2.credit,1.27,"QQQ 799/810 net credit per share");
near(q2.maxLoss,973,"QQQ 799/810 max loss");
assert.equal(q2.maxQty,3);

// VXX CALL values and sizing must follow the same uploaded fixture.
const vcall = Lab.calculateVerticals("VXX_CALL",s.chains.VXX_CALL,100,3200);
const vc = vcall.candidates.find(x=>x.key==="21C/24C");
assert.ok(vc);
near(vc.credit,.24,"VXX 21/24 net credit per share");
near(vc.maxProfit,24,"VXX 21/24 max profit");
near(vc.maxLoss,276,"VXX 21/24 max loss");
near(vc.breakEven,21.24,"VXX 21/24 breakeven");

// Do not fabricate puts absent from the screenshot. They remain importable separately.
assert.equal(s.chains.QQQ_PUT.length,0,"screenshot QQQ put chain must remain empty");
assert.equal(s.chains.VXX_PUT.length,0,"screenshot VXX put chain must remain empty");
assert.equal(Lab.calculateVerticals("VXX_PUT",s.chains.VXX_PUT,100,3200).candidates.length,0);

const csv=Lab.parseCsv("symbol,side,strike,bid,ask,delta\nQQQ,CALL,799,3.16,3.18,0.1456\nVXX,PUT,16,0.65,0.77,-0.3264");
assert.equal(csv.total,2);
assert.equal(csv.chains.QQQ_CALL[0].strike,799);
assert.equal(csv.chains.VXX_PUT[0].bid,.65);

// A separately supplied manual put chain still computes correctly; it is not part of the screenshot sample.
const manualPut = Lab.calculateVerticals("VXX_PUT",[
  {strike:15,bid:.30,ask:.37,delta:-.1964},
  {strike:16,bid:.65,ask:.77,delta:-.3264}
],100,3200);
const vp=manualPut.candidates.find(x=>x.key==="16P/15P");
assert.ok(vp);
near(vp.credit,.28,"manual VXX 16/15 put credit");
near(vp.maxProfit,28,"manual VXX put max profit");
near(vp.maxLoss,72,"manual VXX put max loss");
near(vp.breakEven,15.72,"manual VXX put breakeven");
near(Lab.expiryPnl(vp,15,100,1),-72,"manual VXX put max loss at expiry");

const missing=Lab.calculateVerticals("VXX_PUT",[
  {strike:16,bid:null,ask:.77},
  {strike:15,bid:.30,ask:.37}
],100,3200);
assert.equal(missing.candidates.length,0);
console.log("option_chain_lab=PASS");
