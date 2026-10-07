/**
 * Broker Event Normalizer V1
 *
 * Converts Futu OpenD historical deal / fee / account-cash-flow records
 * into source-neutral canonical events.
 *
 * IMPORTANT:
 * - This layer normalizes and classifies; it does not append to the Ledger.
 * - Unknown / ambiguous cash-flow records are quarantined.
 * - Fee data is attached only when explicitly supplied by Futu order-fee data.
 * - Cash-flow rows representing trades are audit-only to avoid double-counting
 *   the same economic movement already represented by canonical FILL events.
 */
(() => {
  const EVENT_TYPES = Object.freeze({
    FILL: "FILL",
    CASHFLOW: "CASHFLOW",
    DIVIDEND: "DIVIDEND",
    INTEREST: "INTEREST",
    BORROW_FEE: "BORROW_FEE",
    FEE: "FEE",
    CORPORATE_ACTION: "CORPORATE_ACTION",
    OPTION_EXPIRY: "OPTION_EXPIRY",
    ASSIGNMENT: "ASSIGNMENT",
    FX_CONVERSION: "FX_CONVERSION",
    TRADE_SETTLEMENT_AUDIT: "TRADE_SETTLEMENT_AUDIT",
    ACCOUNT_TRANSFER: "ACCOUNT_TRANSFER"
  });

  const QUARANTINE = "QUARANTINE";
  const READY = "READY";
  const INCOMPLETE = "INCOMPLETE";

  function requiredString(value, field) {
    const s = String(value ?? "").trim();
    if (!s) throw new Error(field + " is required");
    return s;
  }

  function finiteNumber(value, field, { allowZero = true } = {}) {
    const n = typeof value === "number" ? value : Number(String(value ?? "").replace(/,/g, ""));
    if (!Number.isFinite(n) || (!allowZero && n === 0)) {
      throw new Error(field + " must be finite");
    }
    return n;
  }

  function normalizeCode(code) {
    const raw = requiredString(code, "code").toUpperCase();
    return raw.replace(/^[A-Z]+\./, "");
  }

  function looksLikeOption(code) {
    return /^[A-Z.]+\d{6}[CP]\d{8}$/.test(String(code).toUpperCase());
  }

  function parseTimezoneTimestamp(value, timezone) {
    const s = requiredString(value, "timestamp");
    if (/[zZ]|[+-]\d{2}:?\d{2}$/.test(s)) return new Date(s).toISOString();
    const tz = requiredString(timezone, "sourceTimezone");
    const m = tz.match(/^([+-])(\d{2}):(\d{2})$/);
    if (!m) {
      throw new Error("sourceTimezone must be an explicit offset such as -05:00");
    }
    const normalized = s.replace(" ", "T") + m[1] + m[2] + ":" + m[3];
    const d = new Date(normalized);
    if (!Number.isFinite(d.getTime())) throw new Error("timestamp is invalid");
    return d.toISOString();
  }

  function dealSide(raw) {
    const v = String(raw?.trd_side ?? raw?.trdSide ?? raw?.side ?? "").trim().toUpperCase();
    if (v === "BUY" || v === "1") return "BUY";
    if (v === "SELL" || v === "2") return "SELL";
    throw new Error("unsupported Futu deal side: " + v);
  }

  function feeMap(rows) {
    const out = {};
    for (const row of rows || []) {
      const id = String(row?.order_id ?? row?.orderIDEx ?? "").trim();
      if (!id) continue;
      const amount = row?.fee_amount ?? row?.feeAmount;
      if (amount === null || amount === undefined || amount === "") continue;
      out[id] = finiteNumber(amount, "feeAmount");
    }
    return out;
  }

  function normalizeDeal(raw, { sourceTimezone = null, feeByOrderId = {}, fillCountByOrderId = {}, importedAt = null } = {}) {
    const dealId = requiredString(raw?.deal_id ?? raw?.dealID, "deal_id");
    const code = normalizeCode(raw?.code);
    const orderId = String(raw?.order_id ?? raw?.orderID ?? "").trim() || null;
    const qty = finiteNumber(raw?.qty ?? raw?.quantity, "qty", { allowZero: false });
    const price = finiteNumber(raw?.price, "price");
    const timestamp = parseTimezoneTimestamp(raw?.create_time ?? raw?.createTime, sourceTimezone);
    const side = dealSide(raw);
    const assetType = looksLikeOption(code) ? "OPTION" : "EQUITY";
    const orderFillCount = orderId ? (Number(fillCountByOrderId[orderId]) || 0) : 0;
    const hasOrderFee = orderId && Object.prototype.hasOwnProperty.call(feeByOrderId, orderId);
    const fee = hasOrderFee && orderFillCount === 1 ? feeByOrderId[orderId] : null;
    const accountingStatus = fee !== null
      ? READY
      : (hasOrderFee && orderFillCount > 1 ? "INCOMPLETE_FEE_ALLOCATION" : INCOMPLETE);

    return {
      id: "FUTU:FILL:" + dealId,
      type: EVENT_TYPES.FILL,
      timestamp,
      symbol: code,
      assetType,
      side,
      quantity: qty,
      price,
      multiplier: assetType === "OPTION" ? 100 : 1,
      fees: fee,
      currency: null,
      accountingStatus,
      provenance: {
        broker: "FUTU",
        source: "history_deal_list_query",
        sourceRecordId: dealId,
        sourceOrderId: orderId,
        importedAt: importedAt || null,
        sourceTimezone: sourceTimezone || null
      }
    };
  }

  function normalizeCashflow(raw, { sourceTimezone = null, importedAt = null, tradeOrderIds = new Set() } = {}) {
    const flowId = requiredString(raw?.cashflow_id ?? raw?.cashFlowID, "cashflow_id");
    const type = String(raw?.cashflow_type ?? raw?.cashFlowType ?? "").trim();
    const remark = String(raw?.cashflow_remark ?? raw?.cashFlowRemark ?? "").trim();
    const amount = finiteNumber(raw?.cashflow_amount ?? raw?.cashFlowAmount, "cashflow_amount");
    const currency = String(raw?.currency ?? "").trim().toUpperCase() || null;
    const clearingDate = requiredString(raw?.clearing_date ?? raw?.clearingDate, "clearing_date");
    const settlementDate = String(raw?.settlement_date ?? raw?.settlementDate ?? "").trim() || null;
    const hay = (type + " " + remark).toLowerCase();

    let eventType = null;
    let accountingStatus = READY;
    let classificationReason = null;

    if (/withholding tax|dividend tax|tax withheld|預扣稅|股息稅/.test(hay)) {
      eventType = EVENT_TYPES.FEE;
      accountingStatus = QUARANTINE;
      classificationReason = "WITHHOLDING_TAX_DEDUP_LINK_REQUIRED";
    } else if (/\bdividend\b|股息|分紅/.test(hay)) {
      eventType = EVENT_TYPES.DIVIDEND;
      classificationReason = "DIVIDEND_KEYWORD";
    } else if (/margin interest|interest|融資利息|利息/.test(hay) && !/borrow|securities lending/.test(hay)) {
      eventType = EVENT_TYPES.INTEREST;
      classificationReason = "INTEREST_KEYWORD";
    } else if (/borrow fee|securities lending|borrow interest|借券/.test(hay)) {
      eventType = EVENT_TYPES.BORROW_FEE;
      classificationReason = "BORROW_KEYWORD";
    } else if (/\bassignment\b|\bassign\b|\bexercise\b|opt\s*ass[-_/]/i.test(hay)) {
      eventType = EVENT_TYPES.ASSIGNMENT;
      accountingStatus = QUARANTINE;
      classificationReason = "OPTION_LIFECYCLE_REQUIRES_POSITION_MAPPING";
    } else if (/option expiry|option expiration|expired option|期權到期|到期/.test(hay)) {
      eventType = EVENT_TYPES.OPTION_EXPIRY;
      accountingStatus = QUARANTINE;
      classificationReason = "OPTION_EXPIRY_REQUIRES_CONTRACT_OUTCOME";
    } else if (/stock split|split|reverse split|merger|spinoff|spin-off|corporate action|股份分拆|合併/.test(hay)) {
      eventType = EVENT_TYPES.CORPORATE_ACTION;
      accountingStatus = QUARANTINE;
      classificationReason = "CORPORATE_ACTION_REQUIRES_SECURITY_MAPPING";
    } else if (/currency exchange|fx conversion|foreign exchange|貨幣兌換|匯兌/.test(hay)) {
      eventType = EVENT_TYPES.FX_CONVERSION;
      accountingStatus = QUARANTINE;
      classificationReason = "FX_REQUIRES_CURRENCY_PAIR_ACCOUNTING";
    } else if (/deposit|withdrawal|cash deposit|cash withdrawal|入金|出金/.test(hay)) {
      eventType = EVENT_TYPES.CASHFLOW;
      classificationReason = "EXPLICIT_EXTERNAL_CASHFLOW_KEYWORD";
    } else if (/fund transfer|cash transfer|transfer|調撥|轉賬/.test(hay)) {
      eventType = EVENT_TYPES.ACCOUNT_TRANSFER;
      accountingStatus = QUARANTINE;
      classificationReason = "TRANSFER_EXTERNALITY_REQUIRES_ACCOUNT_MAPPING";
    } else if (/commission|fee|platform fee|trading fee|settlement fee|sec fee|taf|tax|stamp duty|費用|稅/.test(hay)) {
      eventType = EVENT_TYPES.FEE;
      accountingStatus = QUARANTINE;
      classificationReason = "FEE_DEDUP_LINK_REQUIRED";
    } else if (tradeOrderIds.size && [...tradeOrderIds].some(id => hay.includes(String(id).toLowerCase()))) {
      eventType = EVENT_TYPES.TRADE_SETTLEMENT_AUDIT;
      accountingStatus = QUARANTINE;
      classificationReason = "TRADE_CASHFLOW_MUST_NOT_DOUBLE_COUNT_FILL";
    } else {
      eventType = EVENT_TYPES.TRADE_SETTLEMENT_AUDIT;
      accountingStatus = QUARANTINE;
      classificationReason = "UNCLASSIFIED_CASHFLOW";
    }

    return {
      id: "FUTU:" + eventType + ":" + flowId,
      type: eventType,
      effectiveDate: clearingDate,
      settlementDate,
      amount,
      currency,
      accountingStatus,
      classificationReason,
      provenance: {
        broker: "FUTU",
        source: "get_acc_cash_flow",
        sourceRecordId: String(flowId),
        importedAt: importedAt || null
      },
      sourceDetail: {
        cashflowType: type || null,
        cashflowRemark: remark || null
      }
    };
  }

  function normalizeBundle(raw, { sourceTimezone = null, feeRows = [], importedAt = null } = {}) {
    const deals = Array.isArray(raw?.deals) ? raw.deals : [];
    const cashflows = Array.isArray(raw?.cashflows) ? raw.cashflows : [];
    const fees = feeMap(feeRows);
    const orderIds = new Set(deals.map(x => String(x?.order_id ?? x?.orderID ?? "").trim()).filter(Boolean));
    const fillCountByOrderId = {};
    for (const deal of deals) {
      const orderId = String(deal?.order_id ?? deal?.orderID ?? "").trim();
      if (orderId) fillCountByOrderId[orderId] = (fillCountByOrderId[orderId] || 0) + 1;
    }
    const events = [];
    const quarantine = [];

    for (const deal of deals) {
      try {
        events.push(normalizeDeal(deal, { sourceTimezone, feeByOrderId: fees, fillCountByOrderId, importedAt }));
      } catch (err) {
        quarantine.push({
          broker: "FUTU",
          source: "history_deal_list_query",
          sourceRecordId: String(deal?.deal_id ?? deal?.dealID ?? ""),
          status: QUARANTINE,
          reason: String(err?.message || err)
        });
      }
    }

    for (const flow of cashflows) {
      try {
        const event = normalizeCashflow(flow, { sourceTimezone, importedAt, tradeOrderIds: orderIds });
        (event.accountingStatus === QUARANTINE ? quarantine : events).push(event);
      } catch (err) {
        quarantine.push({
          broker: "FUTU",
          source: "get_acc_cash_flow",
          sourceRecordId: String(flow?.cashflow_id ?? flow?.cashFlowID ?? ""),
          status: QUARANTINE,
          reason: String(err?.message || err)
        });
      }
    }

    events.sort((a, b) =>
      String(a.timestamp || a.effectiveDate || "").localeCompare(String(b.timestamp || b.effectiveDate || "")) ||
      a.id.localeCompare(b.id)
    );

    return {
      schemaVersion: 1,
      source: "FUTU",
      generatedAt: importedAt || new Date().toISOString(),
      sourceTimezone: sourceTimezone || null,
      events,
      quarantine,
      summary: {
        inputDeals: deals.length,
        inputCashflows: cashflows.length,
        normalizedEvents: events.length,
        quarantined: quarantine.length,
        fills: events.filter(e => e.type === EVENT_TYPES.FILL).length,
        externalCashflows: events.filter(e => e.type === EVENT_TYPES.CASHFLOW).length,
        dividends: events.filter(e => e.type === EVENT_TYPES.DIVIDEND).length,
        interest: events.filter(e => e.type === EVENT_TYPES.INTEREST).length,
        borrowFees: events.filter(e => e.type === EVENT_TYPES.BORROW_FEE).length,
        fees: events.filter(e => e.type === EVENT_TYPES.FEE).length
      },
      contract: "BROKER_EVENT_NORMALIZER_V1"
    };
  }

  const API = {
    EVENT_TYPES,
    QUARANTINE,
    READY,
    INCOMPLETE,
    normalizeDeal,
    normalizeCashflow,
    normalizeBundle,
    feeMap
  };

  if (typeof window !== "undefined") window.BrokerEventNormalizerV1 = API;
  if (typeof module !== "undefined") module.exports = API;
})();