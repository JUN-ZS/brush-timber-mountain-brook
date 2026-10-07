const fs = require("fs");
const path = require("path");
const vm = require("vm");

const ledgerSource = fs.readFileSync(path.join(__dirname, "..", "ledger_engine.js"), "utf8");
const identitySource = fs.readFileSync(path.join(__dirname, "..", "position_identity.js"), "utf8");
const ctx = { window: {} };
vm.createContext(ctx);
vm.runInContext(ledgerSource, ctx);
vm.runInContext(identitySource, ctx);
const P = ctx.window.PortfolioPositionIdentityV1;

function eq(actual, expected, label) {
  if (actual !== expected) throw new Error(label + ": expected " + expected + ", got " + actual);
}
function near(actual, expected, eps, label) {
  if (Math.abs(actual - expected) > eps) throw new Error(label + ": expected " + expected + ", got " + actual);
}

const events = [
  { id:"s1", timestamp:"2026-10-01T10:00:00Z", symbol:"QQQ261218C00700000", assetType:"OPTION", side:"SELL", quantity:3, price:8, positionIdentity:{campaignId:"C1",spreadId:"QSP1",legRole:"SHORT",strategyRole:"QQQ_CALL_CREDIT_SPREAD"} },
  { id:"l1", timestamp:"2026-10-01T10:01:00Z", symbol:"QQQ261218C00750000", assetType:"OPTION", side:"BUY", quantity:3, price:2, positionIdentity:{campaignId:"C1",spreadId:"QSP1",legRole:"LONG",strategyRole:"QQQ_CALL_CREDIT_SPREAD"} }
];
let r = P.build(events);
eq(r.summary.optionFills, 2, "option fills");
eq(r.summary.unmappedOptionFills, 0, "unmapped option fills");
eq(r.summary.paired, 1, "paired count");
near(r.rows[0].units, 3, 1e-12, "paired units");
eq(r.rows[0].status, "PAIRED", "paired status");
eq(r.rows[0].campaignId, "C1", "campaign");
eq(r.rows[0].strategyRole, "QQQ_CALL_CREDIT_SPREAD", "strategy role");

const imbalanced = events.concat([
  { id:"s2", timestamp:"2026-10-02T10:00:00Z", symbol:"QQQ261218C00700000", assetType:"OPTION", side:"SELL", quantity:1, price:7, positionIdentity:{spreadId:"QSP1",legRole:"SHORT"} }
]);
r = P.build(imbalanced);
eq(r.rows[0].status, "IMBALANCED", "imbalanced status");
eq(r.rows[0].units, null, "imbalanced units");

const incomplete = events.concat([
  { id:"l2", timestamp:"2026-10-02T10:00:00Z", symbol:"QQQ261218C00800000", assetType:"OPTION", side:"BUY", quantity:1, price:1, positionIdentity:{spreadId:"QSP2",legRole:"LONG"} }
]);
r = P.build(incomplete);
eq(r.summary.incomplete, 1, "incomplete count");

const multi = events.concat([
  { id:"l3", timestamp:"2026-10-02T11:00:00Z", symbol:"QQQ261218C00760000", assetType:"OPTION", side:"BUY", quantity:1, price:1, positionIdentity:{spreadId:"QSP1",legRole:"LONG"} }
]);
r = P.build(multi);
eq(r.rows[0].status, "MULTI_CONTRACT", "multi-contract status");

const closedRoll = events.concat([
  { id:"lclose", timestamp:"2026-10-03T10:00:00Z", symbol:"QQQ261218C00750000", assetType:"OPTION", side:"SELL", quantity:3, price:3, positionIdentity:{spreadId:"QSP1",legRole:"LONG"} },
  { id:"lnew", timestamp:"2026-10-03T10:01:00Z", symbol:"QQQ261218C00770000", assetType:"OPTION", side:"BUY", quantity:3, price:1, positionIdentity:{spreadId:"QSP1",legRole:"LONG"} }
]);
r = P.build(closedRoll);
eq(r.rows[0].status, "PAIRED", "rolled spread stays paired");
eq(r.rows[0].legs.LONG[0].symbol, "QQQ261218C00770000", "old long fully closed");

const unmapped = events.concat([
  { id:"u1", timestamp:"2026-10-04T10:00:00Z", symbol:"VXX261218C00040000", assetType:"OPTION", side:"BUY", quantity:1, price:2 }
]);
r = P.build(unmapped);
eq(r.summary.unmappedOptionFills, 1, "unmapped count");


const neverPaired = P.build([
  {id:"np-s",timestamp:"2026-10-06T10:00:00Z",symbol:"QQQ261218C00900000",assetType:"OPTION",side:"SELL",quantity:1,price:8,
   positionIdentity:{campaignId:"C3",spreadId:"QSP3",legRole:"SHORT"}},
  {id:"np-l",timestamp:"2026-10-06T10:01:00Z",symbol:"QQQ261218C00950000",assetType:"OPTION",side:"BUY",quantity:2,price:2,
   positionIdentity:{campaignId:"C3",spreadId:"QSP3",legRole:"LONG"}},
  {id:"np-sc",timestamp:"2026-10-06T10:02:00Z",symbol:"QQQ261218C00900000",assetType:"OPTION",side:"BUY",quantity:1,price:7,
   positionIdentity:{campaignId:"C3",spreadId:"QSP3",legRole:"SHORT"}},
  {id:"np-lc",timestamp:"2026-10-06T10:03:00Z",symbol:"QQQ261218C00950000",assetType:"OPTION",side:"SELL",quantity:2,price:3,
   positionIdentity:{campaignId:"C3",spreadId:"QSP3",legRole:"LONG"}}
]);
eq(neverPaired.rows[0].status, "INCOMPLETE", "never-paired final identity incomplete");
eq(neverPaired.rows[0].everPaired, false, "never-paired history flag");

const pairedThenClosed = P.build([
  {id:"pc-s",timestamp:"2026-10-07T10:00:00Z",symbol:"QQQ261218C01100000",assetType:"OPTION",side:"SELL",quantity:1,price:8,positionIdentity:{campaignId:"C5",spreadId:"QSP5",legRole:"SHORT"}},
  {id:"pc-l",timestamp:"2026-10-07T10:01:00Z",symbol:"QQQ261218C01150000",assetType:"OPTION",side:"BUY",quantity:1,price:2,positionIdentity:{campaignId:"C5",spreadId:"QSP5",legRole:"LONG"}},
  {id:"pc-sc",timestamp:"2026-10-07T10:02:00Z",symbol:"QQQ261218C01100000",assetType:"OPTION",side:"BUY",quantity:1,price:7,positionIdentity:{campaignId:"C5",spreadId:"QSP5",legRole:"SHORT"}},
  {id:"pc-lc",timestamp:"2026-10-07T10:03:00Z",symbol:"QQQ261218C01150000",assetType:"OPTION",side:"SELL",quantity:1,price:3,positionIdentity:{campaignId:"C5",spreadId:"QSP5",legRole:"LONG"}}
]);
eq(pairedThenClosed.rows[0].everPaired, true, "paired history flag retained after closure");


console.log("POSITION IDENTITY GOLDEN TEST: PASS");