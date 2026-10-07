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
near(r.campaigns[0].currentPnl, 398, 1e-9, "current pnl after fees");
near(r.campaigns[0].periodPnl, 398, 1e-9, "period pnl");

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


const multiCampaign = [
  {id:"m1s",timestamp:"2026-10-05T09:00:00Z",symbol:"QQQ261218C00800000",assetType:"OPTION",side:"SELL",quantity:1,price:8,fees:1,
   positionIdentity:{campaignId:"CM","spreadId":"MS1","legRole:"SHORT"}},
  {id:"m1l",timestamp:"2026-10-05T09:01:00Z",symbol:"QQQ261218C00850000",assetType:"OPTION",side:"BUY",quantity:1,price:2,fees:1,
   positionIdentity:{campaignId:"CM","spreadId":"MS1",legRole:"LONG"}},
  {id:"m2s",timestamp:"2026-10-05T09:02:00Z",symbol:"QQQ261218C00900000",assetType:"OPTION",side:"SELL",quantity:1,price:7,fees:1,
   positionIdentity:{campaignId:"CM",spreadId:"MS2",legRole:"SHORT"}},
  {id:"m2l",timestamp:"2026-10-05T09:03:00Z",symbol:"QQQ261218C00950000",assetType:"OPTION",side:"BUY",quantity:1,price:2,fees:1,
   positionIdentity:{campaignId:"CM",spreadId:"MS2",legRole:"LONG"}}
];
r = P.performance(
  multiCampaign,
  "2026-10-05T08:00:00Z",
  "2026-10-05T16:00:00Z",
  {},
  {"QQQ261218C00800000":5,"QQQ261218C00850000":3,"QQQ261218C00900000":4,"QQQ261218C00950000":1}
);
eq(r.campaigns.length, 1, "multi-spread campaign grouped");
eq(r.campaigns[0].spreadCount, 2, "two spreads under one campaign");
eq(r.campaigns[0].status, "COMPLETE", "multi-spread campaign complete");
near(r.campaigns[0].currentPnl, 596, 1e-9, "multi-spread campaign sum");
near(r.campaigns[0].periodPnl, 596, 1e-9, "multi-spread campaign period sum");

const mixedCampaign = multiCampaign.concat([
  {id:"m3s",timestamp:"2026-10-05T09:04:00Z",symbol:"QQQ261218C01000000",assetType:"OPTION",side:"SELL",quantity:1,price:6,fees:1,
   positionIdentity:{campaignId:"CM",spreadId:"MS3",legRole:"SHORT"}}
]);
r = P.performance(
  mixedCampaign,
  "2026-10-05T08:00:00Z",
  "2026-10-05T16:00:00Z",
  {},
  {"QQQ261218C00800000":5,"QQQ261218C00850000":3,"QQQ261218C00900000":4,"QQQ261218C00950000":1}
);
eq(r.campaigns[0].status, "INCOMPLETE", "campaign blocked by incomplete spread");
eq(r.campaigns[0].periodPnl, null, "incomplete campaign aggregate blocked");
eq(r.spreadRows.filter(x => x.status === "COMPLETE").length, 2, "complete spreads retain their own attribution");

console.log("PORTFOLIO CAMPAIGN PERFORMANCE GOLDEN TEST: PASS");