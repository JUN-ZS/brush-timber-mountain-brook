const fs = require("fs");
const path = require("path");
const vm = require("vm");

const root = path.join(__dirname, "..");
const ctx = { window: {} };
vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(root, "ledger_engine.js"), "utf8"), ctx);
vm.runInContext(fs.readFileSync(path.join(root, "position_identity.js"), "utf8"), ctx);
vm.runInContext(fs.readFileSync(path.join(root, "spread_pnl.js"), "utf8"), ctx);
vm.runInContext(fs.readFileSync(path.join(root, "portfolio_performance.js"), "utf8"), ctx);

const P = ctx.window.PortfolioCampaignPerformanceV1;
function eq(actual, expected, label) {
  if (actual !== expected) throw new Error(label + ": expected " + expected + ", got " + actual);
}
function near(actual, expected, eps, label) {
  if (Math.abs(actual - expected) > eps) throw new Error(label + ": expected " + expected + ", got " + actual);
}

const opened = [
  {id:"s",timestamp:"2026-10-01T10:00:00Z",symbol:"QQQ261218C00700000",assetType:"OPTION",side:"SELL",quantity:1,price:8,fees:1,
   positionIdentity:{campaignId:"C1",spreadId:"S1",legRole:"SHORT",strategyRole:"QQQ_CALL_CREDIT_SPREAD"}},
  {id:"l",timestamp:"2026-10-01T10:01:00Z",symbol:"QQQ261218C00750000",assetType:"OPTION",side:"BUY",quantity:1,price:2,fees:1,
   positionIdentity:{campaignId:"C1",spreadId:"S1",legRole:"LONG",strategyRole:"QQQ_CALL_CREDIT_SPREAD"}}
];

let r = P.performance(
  opened,
  "2026-10-01T09:00:00Z",
  "2026-10-01T16:00:00Z",
  {},
  {"QQQ261218C00700000":5,"QQQ261218C00750000":3}
);
eq(r.summary.completeSpreads, 1, "open spread complete");
eq(r.campaigns.length, 1, "campaign count");
eq(r.campaigns[0].campaignId, "C1", "campaign id");
near(r.campaigns[0].startPnl, 0, 1e-9, "start pnl");
near(r.campaigns[0].currentPnl, 1198, 1e-9, "current pnl after fees");
near(r.campaigns[0].periodPnl, 1198, 1e-9, "period pnl");

const closed = opened.concat([
  {id:"sc",timestamp:"2026-10-02T10:00:00Z",symbol:"QQQ261218C00700000",assetType:"OPTION",side:"BUY",quantity:1,price:6,fees:1,
   positionIdentity:{campaignId:"C1",spreadId:"S1",legRole:"SHORT"}},
  {id:"lc",timestamp:"2026-10-02T10:01:00Z",symbol:"QQQ261218C00750000",assetType:"OPTION",side:"SELL",quantity:1,price:4,fees:1,
   positionIdentity:{campaignId:"C1",spreadId:"S1",legRole:"LONG"}}
]);
r = P.performance(
  closed,
  "2026-10-01T09:00:00Z",
  "2026-10-02T16:00:00Z",
  {},
  {}
);
eq(r.summary.completeSpreads, 1, "closed spread retained");
eq(r.spreadRows[0].endStatus, "CLOSED", "closed end status");
near(r.spreadRows[0].endPnl, 396, 1e-9, "closed cumulative pnl");
near(r.campaigns[0].periodPnl, 396, 1e-9, "closed campaign period pnl");

const partial = closed.concat([
  {id:"s2",timestamp:"2026-10-03T10:00:00Z",symbol:"QQQ261218C00720000",assetType:"OPTION",side:"SELL",quantity:1,price:6,fees:0,
   positionIdentity:{campaignId:"C2",spreadId:"S2",legRole:"SHORT"}}
]);
r = P.performance(
  partial,
  "2026-10-02T16:00:00Z",
  "2026-10-03T16:00:00Z",
  {},
  {}
);
eq(r.summary.incompleteSpreads, 1, "incomplete campaign spread");
eq(r.campaigns.find(c => c.campaignId === "C2").status, "INCOMPLETE", "incomplete campaign status");
eq(r.campaigns.find(c => c.campaignId === "C2").periodPnl, null, "incomplete campaign pnl blocked");

console.log("PORTFOLIO CAMPAIGN PERFORMANCE GOLDEN TEST: PASS");