const fs = require("fs");
const path = require("path");

const N = require(path.join(__dirname, "..", "broker_event_normalizer.js"));

function eq(a, b, label) {
  if (a !== b) throw new Error(label + ": expected " + b + ", got " + a);
}
function ok(v, label) {
  if (!v) throw new Error(label + ": expected truthy");
}

const deals = [
  {
    deal_id: "D1",
    order_id: "O1",
    code: "US.QQQ",
    qty: 10,
    price: 700,
    trd_side: "BUY",
    create_time: "2026-10-01 10:00:00",
  },
  {
    deal_id: "D2",
    order_id: "O2",
    code: "US.QQQ261218C00750000",
    qty: 2,
    price: 5,
    trd_side: "SELL",
    create_time: "2026-10-01 10:01:00",
  },
];

const feeRows = [
  { order_id: "O1", fee_amount: 1.25 },
  { order_id: "O2", fee_amount: 3.50 },
];

const normalizedDeals = deals.map(d => N.normalizeDeal(d, {
  sourceTimezone: "-04:00",
  feeByOrderId: { O1: 1.25, O2: 3.50 },
  importedAt: "2026-10-07T01:20:00Z",
}));

eq(normalizedDeals[0].id, "FUTU:FILL:D1", "equity fill id");
eq(normalizedDeals[0].assetType, "EQUITY", "equity classification");
eq(normalizedDeals[0].fees, 1.25, "equity fee enrichment");
eq(normalizedDeals[0].accountingStatus, "READY_FOR_LEDGER", "equity fill ready");
eq(normalizedDeals[0].timestamp, "2026-10-01T14:00:00.000Z", "explicit offset conversion");

eq(normalizedDeals[1].assetType, "OPTION", "option classification");
eq(normalizedDeals[1].multiplier, 100, "option multiplier");
eq(normalizedDeals[1].fees, 3.5, "option fee enrichment");

let caught = false;
try {
  N.normalizeDeal(deals[0], { sourceTimezone: null, feeByOrderId: {} });
} catch (err) {
  caught = /sourceTimezone/.test(String(err));
}
ok(caught, "naive broker timestamp without timezone blocked");



const shortOpen = N.normalizeDeal({
  deal_id:"D-SO", order_id:"O-SO", code:"US.QQQ", qty:2, price:700,
  trd_side:"SELL_SHORT", create_time:"2026-10-01T14:02:00Z"
}, {feeByOrderId:{ "O-SO": 1 }, fillCountByOrderId:{ "O-SO": 1 }});
eq(shortOpen.side, "SELL", "SELL_SHORT maps to opening SELL");
eq(shortOpen.fees, 1, "short-open fee");
eq(shortOpen.provenance.sourceTradeSide, "SELL_SHORT", "raw short-open side preserved");

const buyBack = N.normalizeDeal({
  deal_id:"D-BB", order_id:"O-BB", code:"US.QQQ", qty:2, price:690,
  trd_side:"BUY_BACK", create_time:"2026-10-01T14:03:00Z"
}, {feeByOrderId:{ "O-BB": 1 }, fillCountByOrderId:{ "O-BB": 1 }});
eq(buyBack.side, "BUY", "BUY_BACK maps to closing BUY");
eq(buyBack.provenance.sourceTradeSide, "BUY_BACK", "raw buy-back side preserved");


const flows = [
  {
    cashflow_id: 101,
    clearing_date: "2026-10-02",
    settlement_date: "2026-10-05",
    currency: "USD",
    cashflow_type: "Dividend",
    cashflow_amount: 12.50,
    cashflow_remark: "QQQ dividend",
  },
  {
    cashflow_id: 102,
    clearing_date: "2026-10-02",
    settlement_date: "2026-10-02",
    currency: "USD",
    cashflow_type: "Margin Interest",
    cashflow_amount: -2.20,
    cashflow_remark: "",
  },
  {
    cashflow_id: 103,
    clearing_date: "2026-10-02",
    settlement_date: "2026-10-02",
    currency: "USD",
    cashflow_type: "Securities Lending Interest",
    cashflow_amount: -4.10,
    cashflow_remark: "Borrow fee",
  },
  {
    cashflow_id: 104,
    clearing_date: "2026-10-02",
    settlement_date: "2026-10-02",
    currency: "USD",
    cashflow_type: "External Transfer",
    cashflow_amount: 1000,
    cashflow_remark: "Deposit",
  },
  {
    cashflow_id: 105,
    clearing_date: "2026-10-02",
    settlement_date: "2026-10-02",
    currency: "USD",
    cashflow_type: "Others",
    cashflow_amount: -300,
    cashflow_remark: "Buy QQQ settlement O1",
  },
  {
    cashflow_id: 106,
    clearing_date: "2026-10-02",
    settlement_date: "2026-10-02",
    currency: "USD",
    cashflow_type: "Others",
    cashflow_amount: 0,
    cashflow_remark: "Opt ASS-P-JXC250227P13000-20260210",
  },
  {
    cashflow_id: 107,
    clearing_date: "2026-10-02",
    settlement_date: "2026-10-02",
    currency: "USD",
    cashflow_type: "Mystery",
    cashflow_amount: 1,
    cashflow_remark: "something unknown",
  }
];

const bundle = N.normalizeBundle(
  { deals, cashflows: flows },
  { sourceTimezone: "-04:00", feeRows, importedAt: "2026-10-07T01:20:00Z" }
);

eq(bundle.summary.inputDeals, 2, "deal count");
eq(bundle.summary.inputCashflows, 7, "cashflow count");
eq(bundle.summary.fills, 2, "normalized fills");
eq(bundle.summary.dividends, 1, "dividend count");
eq(bundle.summary.interest, 1, "interest count");
eq(bundle.summary.borrowFees, 1, "borrow fee count");
eq(bundle.summary.externalCashflows, 1, "external cashflow count");
eq(bundle.quarantine.length, 3, "quarantine count");

const byId = Object.fromEntries(bundle.events.map(e => [e.id, e]));
eq(byId["FUTU:DIVIDEND:101"].type, "DIVIDEND", "dividend type");
eq(byId["FUTU:DIVIDEND:101"].accountingStatus, "NORMALIZED_NOT_APPLIED", "dividend not yet applied");

eq(byId["FUTU:INTEREST:102"].type, "INTEREST", "interest type");
eq(byId["FUTU:BORROW_FEE:103"].type, "BORROW_FEE", "borrow type");
eq(byId["FUTU:CASHFLOW:104"].type, "CASHFLOW", "external cashflow type");

const q = Object.fromEntries(bundle.quarantine.map(e => [e.id, e]));
eq(q["FUTU:TRADE_SETTLEMENT_AUDIT:105"].classificationReason, "TRADE_CASHFLOW_MUST_NOT_DOUBLE_COUNT_FILL", "trade settlement anti-double-count");
eq(q["FUTU:ASSIGNMENT:106"].classificationReason, "OPTION_LIFECYCLE_REQUIRES_POSITION_MAPPING", "assignment quarantined");
eq(q["FUTU:TRADE_SETTLEMENT_AUDIT:107"].classificationReason, "UNCLASSIFIED_CASHFLOW", "unknown quarantined");

const all = bundle.events.concat(bundle.quarantine);
ok(all.every(e => e.provenance && e.provenance.broker === "FUTU"), "provenance present");
ok(all.every(e => e.id && String(e.id).startsWith("FUTU:")), "stable source ids");



// One Futu order with multiple fills must not copy the order-level fee to each fill.
const splitOrder = [
  { deal_id:"SD1", order_id:"SO1", code:"US.QQQ", qty:5, price:700, trd_side:"BUY", create_time:"2026-10-01T14:00:00Z" },
  { deal_id:"SD2", order_id:"SO1", code:"US.QQQ", qty:5, price:701, trd_side:"BUY", create_time:"2026-10-01T14:00:01Z" }
];
const splitBundle = N.normalizeBundle(
  { deals: splitOrder, cashflows: [] },
  { feeRows:[{order_id:"SO1",fee_amount:10}], importedAt:"2026-10-07T01:20:00Z" }
);
eq(splitBundle.events.length, 2, "multi-fill deal count");
eq(splitBundle.quarantine.length, 0, "multi-fill fills are retained");
eq(splitBundle.events[0].fees, null, "multi-fill fee not duplicated");
eq(splitBundle.events[1].accountingStatus, "INCOMPLETE_FEE_ALLOCATION", "multi-fill fee allocation incomplete");

console.log("BROKER EVENT NORMALIZER GOLDEN TEST: PASS");