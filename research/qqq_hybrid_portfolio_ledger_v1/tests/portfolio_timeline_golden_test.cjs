const fs = require("fs");
const path = require("path");
const vm = require("vm");

const root = path.join(__dirname, "..");
const ctx = { window: {} };
vm.createContext(ctx);
for (const file of ["ledger_engine.js", "position_identity.js", "spread_pnl.js", "portfolio_timeline.js"]) {
  vm.runInContext(fs.readFileSync(path.join(root, file), "utf8"), ctx);
}

const T = ctx.window.PortfolioCampaignTimelineV1;
function eq(actual, expected, label) {
  if (actual !== expected) throw new Error(label + ": expected " + expected + ", got " + actual);
}
function near(actual, expected, eps, label) {
  if (Math.abs(actual - expected) > eps) throw new Error(label + ": expected " + expected + ", got " + actual);
}

const base = [
  {id:"s-open",timestamp:"2026-10-01T10:00:00Z",symbol:"QQQ261218C00700000",assetType:"OPTION",side:"SELL",quantity:3,price:8,fees:3,
   positionIdentity:{campaignId:"C1",spreadId:"S1",legRole:"SHORT",strategyRole:"QQQ_CALL_CREDIT_SPREAD"}},
  {id:"l-open",timestamp:"2026-10-01T10:01:00Z",symbol:"QQQ261218C00750000",assetType:"OPTION",side:"BUY",quantity:3,price:2,fees:3,
   positionIdentity:{campaignId:"C1",spreadId:"S1",legRole:"LONG",strategyRole:"QQQ_CALL_CREDIT_SPREAD"}}
];

let r = T.timeline(base);
eq(r.contract, "PORTFOLIO_CAMPAIGN_TIMELINE_V1", "contract");
eq(r.summary.opens, 1, "open count");
eq(r.rows.length, 2, "two identity-bearing fills");
eq(r.rows[0].eventKind, "INCOMPLETE", "first leg pending");
eq(r.rows[1].eventKind, "OPEN", "pair opens");
near(r.rows[1].realizedNetPnl, -6, 1e-9, "opening net pnl includes fees");
eq(r.rows[1].pnlBasis, "REALIZED_ONLY", "opening basis");
eq(r.rows[1].totalPnl, null, "no fabricated total pnl");
near(r.rows[1].campaignCumulativeRealizedNetPnl, -6, 1e-9, "campaign cumulative open");

const marks = [
  {timestamp:"2026-10-01T10:01:00Z", marks:{
    QQQ261218C00700000:5,
    QQQ261218C00750000:3
  }},
  {timestamp:"2026-10-02T10:02:00Z", marks:{
    QQQ261218C00800000:1,
    QQQ261218C00750000:3
  }}
];
const withMarks = T.timeline(base, marks);
eq(withMarks.rows[1].pnlBasis, "MARKED_TOTAL", "point-in-time mark used");
near(withMarks.rows[1].totalPnl, 1194, 1e-9, "marked opening total");
eq(withMarks.rows[1].markTimestamp, "2026-10-01T10:01:00.000Z", "mark timestamp");

const rolled = base.concat([
  {id:"new-short",timestamp:"2026-10-02T10:00:00Z",symbol:"QQQ261218C00800000",assetType:"OPTION",side:"SELL",quantity:3,price:5,fees:1,
   positionIdentity:{campaignId:"C1",spreadId:"S1",legRole:"SHORT"}},
  {id:"old-short-close",timestamp:"2026-10-02T10:01:00Z",symbol:"QQQ261218C00700000",assetType:"OPTION",side:"BUY",quantity:3,price:6,fees:1,
   positionIdentity:{campaignId:"C1",spreadId:"S1",legRole:"SHORT"}}
]);
r = T.timeline(rolled);
eq(r.summary.rolls, 1, "roll complete count");
eq(r.rows[2].eventKind, "ROLL_START", "roll starts with second active short");
eq(r.rows[3].eventKind, "ROLL_COMPLETE", "roll completes when old short closes");
eq(r.rows[3].shortContracts[0], "QQQ261218C00800000", "new short remains active");
eq(r.rows[3].afterStatus, "PAIRED", "rolled spread paired");

const partialClose = rolled.concat([
  {id:"short-close-partial",timestamp:"2026-10-03T10:00:00Z",symbol:"QQQ261218C00800000",assetType:"OPTION",side:"BUY",quantity:1,price:4,fees:1,
   positionIdentity:{campaignId:"C1",spreadId:"S1",legRole:"SHORT"}},
  {id:"long-close-partial",timestamp:"2026-10-03T10:01:00Z",symbol:"QQQ261218C00750000",assetType:"OPTION",side:"SELL",quantity:1,price:2,fees:1,
   positionIdentity:{campaignId:"C1",spreadId:"S1",legRole:"LONG"}}
]);
r = T.timeline(partialClose);
eq(r.summary.partialCloses, 1, "partial close count");
eq(r.rows[r.rows.length - 1].eventKind, "PARTIAL_CLOSE", "partial close milestone");
near(r.rows[r.rows.length - 1].realizedNetPnl, 693, 1e-9, "partial realized net after roll"); // 600 short + 100 long - 14 total fees
near(r.rows[r.rows.length - 1].campaignCumulativeRealizedNetPnl, 693, 1e-9, "campaign cumulative partial");

const closed = partialClose.concat([
  {id:"short-close-rest",timestamp:"2026-10-04T10:00:00Z",symbol:"QQQ261218C00800000",assetType:"OPTION",side:"BUY",quantity:2,price:3,fees:1,
   positionIdentity:{campaignId:"C1",spreadId:"S1",legRole:"SHORT"}},
  {id:"long-close-rest",timestamp:"2026-10-04T10:01:00Z",symbol:"QQQ261218C00750000",assetType:"OPTION",side:"SELL",quantity:2,price:1,fees:1,
   positionIdentity:{campaignId:"C1",spreadId:"S1",legRole:"LONG"}}
]);
r = T.timeline(closed);
eq(r.summary.fullCloses, 1, "full close count");
const final = r.rows[r.rows.length - 1];
eq(final.eventKind, "FULL_CLOSE", "full close milestone");
eq(final.afterStatus, "CLOSED", "closed status");
eq(final.totalPnl, final.realizedNetPnl, "closed total equals realized net");
eq(r.campaigns.length, 1, "campaign count");
near(r.campaigns[0].finalRealizedNetPnl, final.realizedNetPnl, 1e-9, "campaign final realized net");

const futureOnly = T.timeline(base, [
  {timestamp:"2026-10-02T10:00:00Z", marks:{
    QQQ261218C00700000:1,
    QQQ261218C00750000:20
  }}
]);
eq(futureOnly.rows[1].totalPnl, null, "future mark never leaks backwards");
eq(futureOnly.rows[1].markTimestamp, null, "no future mark timestamp");

const unpaired = T.timeline([
  {id:"only",timestamp:"2026-10-05T10:00:00Z",symbol:"QQQ261218C00700000",assetType:"OPTION",side:"SELL",quantity:1,price:8,fees:1,
   positionIdentity:{campaignId:"C2",spreadId:"S2",legRole:"SHORT"}}
]);
eq(unpaired.rows[0].eventKind, "INCOMPLETE", "unpaired remains incomplete");
eq(unpaired.rows[0].realizedNetPnl, null, "no fabricated realized pnl for unpaired");
eq(unpaired.campaigns[0].finalRealizedNetPnl, null, "unpaired campaign remains unpriced");

console.log("PORTFOLIO CAMPAIGN TIMELINE GOLDEN TEST: PASS");
