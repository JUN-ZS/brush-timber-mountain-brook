const fs = require("fs");
const path = require("path");
const vm = require("vm");

const ledgerSource = fs.readFileSync(path.join(__dirname, "..", "ledger_engine.js"), "utf8");
const identitySource = fs.readFileSync(path.join(__dirname, "..", "position_identity.js"), "utf8");
const pnlSource = fs.readFileSync(path.join(__dirname, "..", "spread_pnl.js"), "utf8");

const ctx = { window: {} };
vm.createContext(ctx);
vm.runInContext(ledgerSource, ctx);
vm.runInContext(identitySource, ctx);
vm.runInContext(pnlSource, ctx);
const S = ctx.window.PortfolioSpreadPnlV1;

function near(actual, expected, eps, label) {
  if (Math.abs(actual - expected) > eps) throw new Error(label + ": expected " + expected + ", got " + actual);
}
function eq(actual, expected, label) {
  if (actual !== expected) throw new Error(label + ": expected " + expected + ", got " + actual);
}

const base = [
  { id:"short-open", timestamp:"2026-10-01T10:00:00Z", symbol:"QQQ261218C00700000", assetType:"OPTION", side:"SELL", quantity:3, price:8, fees:3,
    positionIdentity:{campaignId:"C1",spreadId:"QSP1",legRole:"SHORT",strategyRole:"QQQ_CALL_CREDIT_SPREAD"} },
  { id:"long-open", timestamp:"2026-10-01T10:01:00Z", symbol:"QQQ261218C00750000", assetType:"OPTION", side:"BUY", quantity:3, price:2, fees:3,
    positionIdentity:{campaignId:"C1",spreadId:"QSP1",legRole:"LONG",strategyRole:"QQQ_CALL_CREDIT_SPREAD"} }
];

let r = S.attribute(base, {
  QQQ261218C00700000:5,
  QQQ261218C00750000:3
});
eq(r.summary.paired, 1, "paired");
const row = r.rows[0];
eq(row.status, "PAIRED", "status");
near(row.units, 3, 1e-12, "units");
near(row.entryDebit, 600, 1e-9, "entry debit");
near(row.entryCredit, 2400, 1e-9, "entry credit");
near(row.netEntryCredit, 1800, 1e-9, "net entry credit");
near(row.currentValue, -600, 1e-9, "current value");
near(row.realizedPnl, 0, 1e-9, "realized");
near(row.unrealizedPnl, 1200, 1e-9, "unrealized");
near(row.fees, 6, 1e-9, "fees");
near(row.totalPnl, 1194, 1e-9, "total pnl");
near(row.longLeg.unrealizedPnl, 300, 1e-9, "long unrealized");
near(row.shortLeg.unrealizedPnl, 900, 1e-9, "short unrealized");

const partial = base.concat([
  { id:"short-close", timestamp:"2026-10-02T10:00:00Z", symbol:"QQQ261218C00700000", assetType:"OPTION", side:"BUY", quantity:1, price:6, fees:2,
    positionIdentity:{spreadId:"QSP1",legRole:"SHORT"} },
  { id:"long-close", timestamp:"2026-10-02T10:01:00Z", symbol:"QQQ261218C00750000", assetType:"OPTION", side:"SELL", quantity:1, price:4, fees:2,
    positionIdentity:{spreadId:"QSP1",legRole:"LONG"} }
]);
r = S.attribute(partial, {
  QQQ261218C00700000:5,
  QQQ261218C00750000:3
});
const p = r.rows[0];
eq(p.status, "PAIRED", "partial close status");
near(p.units, 2, 1e-12, "partial units");
near(p.longLeg.realizedPnl, 200, 1e-9, "long realized");
near(p.shortLeg.realizedPnl, 200, 1e-9, "short realized");
near(p.longLeg.unrealizedPnl, 200, 1e-9, "long open unrealized");
near(p.shortLeg.unrealizedPnl, 600, 1e-9, "short open unrealized");
near(p.realizedPnl, 400, 1e-9, "spread realized");
near(p.unrealizedPnl, 800, 1e-9, "spread unrealized");
near(p.fees, 10, 1e-9, "spread fees");
near(p.totalPnl, 1190, 1e-9, "spread total");
near(p.entryDebit, 400, 1e-9, "active entry debit");
near(p.entryCredit, 1600, 1e-9, "active entry credit");
near(p.currentValue, -400, 1e-9, "active current value");
near(p.netEntryCredit + p.currentValue, p.unrealizedPnl, 1e-9, "unrealized consistency");

const missingMark = S.attribute(base, {QQQ261218C00700000:5});
eq(missingMark.rows[0].status, "INCOMPLETE", "missing mark blocked");
eq(missingMark.rows[0].reason, "MISSING_CURRENT_MARK", "missing mark reason");

const incomplete = S.attribute([
  base[0]
], {QQQ261218C00700000:5});
eq(incomplete.rows[0].status, "INCOMPLETE", "unpaired blocked");
eq(incomplete.rows[0].reason, "POSITION_IDENTITY_INCOMPLETE", "unpaired reason");

const imbalanced = S.attribute(base.concat([
  { id:"short-extra", timestamp:"2026-10-03T10:00:00Z", symbol:"QQQ261218C00700000", assetType:"OPTION", side:"SELL", quantity:1, price:7, fees:0,
    positionIdentity:{spreadId:"QSP1",legRole:"SHORT"} }
]), {
  QQQ261218C00700000:5,
  QQQ261218C00750000:3
});
eq(imbalanced.rows[0].status, "INCOMPLETE", "imbalanced blocked");
eq(imbalanced.rows[0].reason, "POSITION_IDENTITY_IMBALANCED", "imbalanced reason");


const closed = base.concat([
  { id:"short-close", timestamp:"2026-10-02T10:00:00Z", symbol:"QQQ261218C00700000", assetType:"OPTION", side:"BUY", quantity:3, price:6, fees:1,
    positionIdentity:{spreadId:"QSP1",legRole:"SHORT"} },
  { id:"long-close", timestamp:"2026-10-02T10:01:00Z", symbol:"QQQ261218C00750000", assetType:"OPTION", side:"SELL", quantity:3, price:4, fees:1,
    positionIdentity:{spreadId:"QSP1",legRole:"LONG"} }
]);
const closedResult = S.attribute(closed, {});
eq(closedResult.summary.closed, 1, "closed count");
eq(closedResult.rows[0].status, "CLOSED", "closed status");
near(closedResult.rows[0].realizedPnl, 1200, 1e-9, "closed realized");
near(closedResult.rows[0].unrealizedPnl, 0, 1e-9, "closed unrealized");
near(closedResult.rows[0].fees, 8, 1e-9, "closed fees");
near(closedResult.rows[0].totalPnl, 1192, 1e-9, "closed total pnl");


const rolled = base.concat([
  { id:"short-roll-open", timestamp:"2026-10-02T10:00:00Z", symbol:"QQQ261218C00800000", assetType:"OPTION", side:"SELL", quantity:3, price:5, fees:1,
    positionIdentity:{campaignId:"C1",spreadId:"QSP1",legRole:"SHORT"} },
  { id:"short-old-close", timestamp:"2026-10-02T10:01:00Z", symbol:"QQQ261218C00700000", assetType:"OPTION", side:"BUY", quantity:3, price:6, fees:1,
    positionIdentity:{campaignId:"C1",spreadId:"QSP1",legRole:"SHORT"} }
]);
const rolledNoMarks = S.attribute(rolled, {});
eq(rolledNoMarks.rows[0].status, "INCOMPLETE", "rolled spread remains structurally paired without marks but attribution is incomplete");
near(rolledNoMarks.rows[0].realizedPnl, 600, 1e-9, "rolled realized retained without marks");
near(rolledNoMarks.rows[0].fees, 8, 1e-9, "rolled fees retained without marks");
eq(rolledNoMarks.rows[0].totalPnl, null, "rolled total blocked without marks");

const rolledResult = S.attribute(rolled, {
  QQQ261218C00750000:3,
  QQQ261218C00800000:4
});
eq(rolledResult.rows[0].status, "PAIRED", "rolled spread remains paired");
near(rolledResult.rows[0].realizedPnl, 600, 1e-9, "rolled historical realized retained");
near(rolledResult.rows[0].fees, 8, 1e-9, "rolled historical fees retained");
near(rolledResult.rows[0].unrealizedPnl, 600, 1e-9, "rolled active unrealized only");
near(rolledResult.rows[0].totalPnl, 1192, 1e-9, "rolled total includes historical realized and all fees");


const neverPaired = [
  { id:"np-short-open", timestamp:"2026-10-06T10:00:00Z", symbol:"QQQ261218C00900000", assetType:"OPTION", side:"SELL", quantity:1, price:8, fees:1,
    positionIdentity:{campaignId:"C3",spreadId:"QSP3",legRole:"SHORT"} },
  { id:"np-long-open", timestamp:"2026-10-06T10:01:00Z", symbol:"QQQ261218C00950000", assetType:"OPTION", side:"BUY", quantity:2, price:2, fees:1,
    positionIdentity:{campaignId:"C3",spreadId:"QSP3",legRole:"LONG"} },
  { id:"np-short-close", timestamp:"2026-10-06T10:02:00Z", symbol:"QQQ261218C00900000", assetType:"OPTION", side:"BUY", quantity:1, price:7, fees:1,
    positionIdentity:{campaignId:"C3",spreadId:"QSP3",legRole:"SHORT"} },
  { id:"np-long-close", timestamp:"2026-10-06T10:03:00Z", symbol:"QQQ261218C00950000", assetType:"OPTION", side:"SELL", quantity:2, price:3, fees:1,
    positionIdentity:{campaignId:"C3",spreadId:"QSP3",legRole:"LONG"} }
];
const np = S.attribute(neverPaired, {});
eq(np.rows[0].status, "INCOMPLETE", "never-paired history is not CLOSED");
eq(np.rows[0].reason, "POSITION_IDENTITY_INCOMPLETE", "never-paired reason");
eq(np.rows[0].totalPnl, null, "never-paired pnl blocked");


const unorderedSpread = S.attribute([
  base[1],
  base[0]
], {
  QQQ261218C00700000:5,
  QQQ261218C00750000:3
});
eq(unorderedSpread.rows[0].status, "PAIRED", "unordered spread stays paired");
near(unorderedSpread.rows[0].totalPnl, 1194, 1e-9, "unordered spread FIFO attribution");


// BLOCKER B: null/blank marks must NOT coerce to 0 and invent P&L
const nullMarkEvents = [
  { id:"nb-short", timestamp:"2026-10-01T10:00:00Z", symbol:"QQQ261218C00700000", assetType:"OPTION", side:"SELL", quantity:1, price:5, fees:0,
    positionIdentity:{campaignId:"CA",spreadId:"SPB",legRole:"SHORT",strategyRole:"ROLE"} },
  { id:"nb-long", timestamp:"2026-10-01T10:01:00Z", symbol:"QQQ261218C00750000", assetType:"OPTION", side:"BUY", quantity:1, price:2, fees:0,
    positionIdentity:{campaignId:"CA",spreadId:"SPB",legRole:"LONG",strategyRole:"ROLE"} }
];
const nullMark = S.attribute(nullMarkEvents, { QQQ261218C00750000: null, QQQ261218C00700000: 5 });
eq(nullMark.rows[0].status, "INCOMPLETE", "null mark blocked");
eq(nullMark.rows[0].reason, "MISSING_CURRENT_MARK", "null mark reason");
eq(nullMark.rows[0].totalPnl, null, "null mark no fabricated pnl");
eq(nullMark.rows[0].longLeg.mark, null, "null mark stays null not 0");

const blankMark = S.attribute(nullMarkEvents, { QQQ261218C00750000: "", QQQ261218C00700000: 5 });
eq(blankMark.rows[0].status, "INCOMPLETE", "blank mark blocked");
eq(blankMark.rows[0].reason, "MISSING_CURRENT_MARK", "blank mark reason");
eq(blankMark.rows[0].totalPnl, null, "blank mark no fabricated pnl");

// RISK A: campaignId conflict blocks attribution (no first-seen wins)
const conflictEvents = [
  { id:"cf-long", timestamp:"2026-10-01T10:00:00Z", symbol:"QQQ261218C00750000", assetType:"OPTION", side:"BUY", quantity:1, price:2, fees:0,
    positionIdentity:{campaignId:"CA",spreadId:"SPC",legRole:"LONG",strategyRole:"ROLE_A"} },
  { id:"cf-short", timestamp:"2026-10-01T10:01:00Z", symbol:"QQQ261218C00700000", assetType:"OPTION", side:"SELL", quantity:1, price:5, fees:0,
    positionIdentity:{campaignId:"CB",spreadId:"SPC",legRole:"SHORT",strategyRole:"ROLE_B"} }
];
const conflict = S.attribute(conflictEvents, { QQQ261218C00750000: 3, QQQ261218C00700000: 4 });
eq(conflict.rows[0].status, "INCOMPLETE", "campaign conflict blocked");
eq(conflict.rows[0].reason, "POSITION_IDENTITY_METADATA_CONFLICT", "campaign conflict reason");
eq(conflict.rows[0].campaignId, null, "campaign conflict clears campaignId");
eq(conflict.rows[0].totalPnl, null, "campaign conflict no pnl");

console.log("SPREAD PNL ATTRIBUTION GOLDEN TEST: PASS");