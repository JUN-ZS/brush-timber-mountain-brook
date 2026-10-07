window.PortfolioLedgerV1 = (() => {
  const ASSET_TYPES = Object.freeze({ EQUITY: "EQUITY", OPTION: "OPTION" });
  const SIDES = Object.freeze({ BUY: "BUY", SELL: "SELL" });
  const EVENT_TYPES = Object.freeze({ FILL: "FILL", CASHFLOW: "CASHFLOW" });

  const num = (v, d = null) => {
    if (v === null || v === undefined || v === "") return d;
    if (typeof v === "boolean") return d;
    const x = Number(String(v).replace(/,/g, ""));
    return Number.isFinite(x) ? x : d;
  };

  const hasExplicitTimezone = (v) =>
    typeof v === "string" && /(?:Z|[+-]\d{2}:\d{2})$/i.test(v.trim());

  const iso = (v) => {
    if (!v || !hasExplicitTimezone(v)) return null;
    const x = new Date(v);
    return Number.isFinite(x.getTime()) ? x.toISOString() : null;
  };

  function multiplierFor(assetType, value) {
    if (value === null || value === undefined || value === "") {
      return assetType === ASSET_TYPES.OPTION ? 100 : 1;
    }
    const n = num(value);
    if (n === null || n <= 0) throw new Error("multiplier must be > 0");
    return n;
  }

  function normalizePositionIdentity(raw, assetType) {
    if (raw === null || raw === undefined || raw === "") return null;
    if (assetType !== ASSET_TYPES.OPTION) throw new Error("positionIdentity is only valid for OPTION fills");
    if (typeof raw !== "object" || Array.isArray(raw)) throw new Error("positionIdentity must be an object");

    const campaignId = String(raw.campaignId || "").trim();
    const spreadId = String(raw.spreadId || "").trim();
    const legRole = String(raw.legRole || "").trim().toUpperCase();
    const strategyRole = String(raw.strategyRole || "").trim();

    if (!spreadId) throw new Error("positionIdentity.spreadId is required");
    if (!["LONG", "SHORT"].includes(legRole)) {
      throw new Error("positionIdentity.legRole must be LONG or SHORT");
    }

    const out = { spreadId, legRole };
    if (campaignId) out.campaignId = campaignId;
    if (strategyRole) out.strategyRole = strategyRole;
    return out;
  }

  function normalizeEvent(raw) {
    if (!raw || typeof raw !== "object") throw new Error("event must be an object");
    const rawId = raw.id;
    if (typeof rawId !== "string" || !rawId.trim()) {
      throw new Error("event id is required and must be a non-empty string");
    }
    const type = String(raw.type || EVENT_TYPES.FILL).toUpperCase();

    if (type === EVENT_TYPES.CASHFLOW) {
      const amount = num(raw.amount);
      if (!Number.isFinite(amount) || amount === 0) throw new Error("cashflow amount must be non-zero");
      const timestamp = iso(raw.timestamp);
      if (!timestamp) throw new Error("cashflow timestamp is invalid");
      return {
        id: rawId.trim(),
        type,
        timestamp,
        amount,
        note: String(raw.note || ""),
      };
    }

    if (type !== EVENT_TYPES.FILL) throw new Error("unsupported event type: " + type);

    const timestamp = iso(raw.timestamp);
    const symbol = String(raw.symbol || "").trim().toUpperCase();
    const assetType = String(raw.assetType || ASSET_TYPES.EQUITY).toUpperCase();
    const side = String(raw.side || "").toUpperCase();
    const quantity = num(raw.quantity);
    const price = num(raw.price);
    const multiplier = multiplierFor(assetType, raw.multiplier);
    const fees = raw.fees === null || raw.fees === undefined || raw.fees === ""
      ? 0
      : num(raw.fees);
    if (fees === null || fees < 0) throw new Error("fees must be >= 0");
    const positionIdentity = normalizePositionIdentity(raw.positionIdentity, assetType);

    if (!timestamp) throw new Error("fill timestamp is invalid");
    if (!symbol) throw new Error("symbol is required");
    if (![ASSET_TYPES.EQUITY, ASSET_TYPES.OPTION].includes(assetType)) throw new Error("assetType must be EQUITY or OPTION");
    if (![SIDES.BUY, SIDES.SELL].includes(side)) throw new Error("side must be BUY or SELL");
    if (!Number.isFinite(quantity) || quantity <= 0) throw new Error("quantity must be > 0");
    if (!Number.isFinite(price) || price < 0) throw new Error("price must be >= 0");

    return {
      id: rawId.trim(),
      type,
      timestamp,
      symbol,
      assetType,
      side,
      quantity,
      price,
      multiplier,
      fees,
      note: String(raw.note || ""),
      ...(positionIdentity ? { positionIdentity } : {}),
    };
  }

  function sortEvents(events) {
    return events
      .map(normalizeEvent)
      .sort((a, b) => a.timestamp.localeCompare(b.timestamp) || a.id.localeCompare(b.id));
  }

  function ensureSymbolBook(books, event) {
    let book = books[event.symbol];
    if (!book) {
      book = {
        symbol: event.symbol,
        assetType: event.assetType,
        multiplier: event.multiplier,
        lots: [],
        realizedPnl: 0,
        fees: 0,
      };
      books[event.symbol] = book;
      return book;
    }
    if (book.assetType !== event.assetType) throw new Error("asset type mismatch for " + event.symbol);
    if (book.multiplier !== event.multiplier) throw new Error("multiplier mismatch for " + event.symbol);
    return book;
  }

  function applyFill(books, cashState, event) {
    const book = ensureSymbolBook(books, event);
    let remaining = event.side === SIDES.BUY ? event.quantity : -event.quantity;

    while (Math.abs(remaining) > 1e-12 && book.lots.length) {
      const lot = book.lots[0];
      const sameDirection = Math.sign(lot.qty) === Math.sign(remaining);

      if (sameDirection) {
        break;
      }

      const closingQty = Math.min(Math.abs(lot.qty), Math.abs(remaining));
      if (lot.qty > 0 && remaining < 0) {
        book.realizedPnl += (event.price - lot.price) * closingQty * book.multiplier;
      } else {
        book.realizedPnl += (lot.price - event.price) * closingQty * book.multiplier;
      }

      lot.qty += Math.sign(lot.qty) * -closingQty;
      remaining -= Math.sign(remaining) * closingQty;
      if (Math.abs(lot.qty) <= 1e-12) book.lots.shift();
    }

    if (Math.abs(remaining) > 1e-12) {
      book.lots.push({
        qty: remaining,
        price: event.price,
        timestamp: event.timestamp,
        id: event.id,
      });
    }

    const gross = event.price * event.quantity * event.multiplier;
    cashState.cash += event.side === SIDES.BUY ? -gross - event.fees : gross - event.fees;
    book.fees += event.fees;
    cashState.totalFees += event.fees;
  }

  function buildState(events, asOf = null) {
    const normalized = sortEvents(events);
    const cutoff = asOf ? new Date(asOf).getTime() : Infinity;
    if (asOf && !Number.isFinite(cutoff)) throw new Error("invalid asOf");

    const books = {};
    const cashState = { cash: 0, externalCashFlow: 0, totalFees: 0 };

    for (const event of normalized) {
      if (new Date(event.timestamp).getTime() > cutoff) continue;
      if (event.type === EVENT_TYPES.CASHFLOW) {
        cashState.cash += event.amount;
        cashState.externalCashFlow += event.amount;
      } else {
        applyFill(books, cashState, event);
      }
    }

    return {
      books,
      cashState,
      events: normalized.filter((e) => new Date(e.timestamp).getTime() <= cutoff),
    };
  }

  function positionSummary(book) {
    const qty = book.lots.reduce((s, lot) => s + lot.qty, 0);
    const grossUnits = book.lots.reduce((s, lot) => s + Math.abs(lot.qty), 0);
    return { qty, openLots: book.lots.length, grossUnits };
  }

  function markValue(book, mark) {
    if (!Number.isFinite(mark)) return null;
    return positionSummary(book).qty * mark * book.multiplier;
  }

  function snapshot(events, marks = {}, asOf = null) {
    const state = buildState(events, asOf);
    let marketValue = 0;
    let unrealizedPnl = 0;
    const positions = [];

    for (const book of Object.values(state.books)) {
      const p = positionSummary(book);
      if (Math.abs(p.qty) <= 1e-12) continue;
      const rawMark = marks[book.symbol];
      const mark = num(rawMark);
      const usableMark = Number.isFinite(mark) && mark >= 0 ? mark : null;
      const mv = markValue(book, usableMark);
      let upnl = null;

      if (usableMark !== null) {
        upnl = book.lots.reduce((s, lot) => {
          if (lot.qty > 0) return s + (usableMark - lot.price) * lot.qty * book.multiplier;
          return s + (lot.price - usableMark) * Math.abs(lot.qty) * book.multiplier;
        }, 0);
        unrealizedPnl += upnl;
        marketValue += mv;
      }

      positions.push({
        symbol: book.symbol,
        assetType: book.assetType,
        quantity: p.qty,
        multiplier: book.multiplier,
        averageOpenPrice: p.grossUnits > 0
          ? book.lots.reduce((s, lot) => s + Math.abs(lot.qty) * lot.price, 0) / p.grossUnits
          : null,
        openLots: book.lots.map((l) => ({
          qty: l.qty,
          price: l.price,
          timestamp: l.timestamp,
          id: l.id,
        })),
        mark: usableMark,
        marketValue: mv,
        unrealizedPnl: upnl,
        realizedPnl: book.realizedPnl,
      });
    }

    const realizedPnl = Object.values(state.books).reduce((s, b) => s + b.realizedPnl, 0);
    const netPnl = realizedPnl + unrealizedPnl - state.cashState.totalFees;
    const equity = state.cashState.cash + marketValue;

    return {
      asOf: asOf || null,
      cash: state.cashState.cash,
      marketValue,
      equity,
      realizedPnl,
      unrealizedPnl,
      totalFees: state.cashState.totalFees,
      netPnl,
      externalCashFlow: state.cashState.externalCashFlow,
      positions,
      coverage: {
        allMarksPresent: positions.every((p) => Number.isFinite(p.mark)),
        markedSymbols: positions.filter((p) => Number.isFinite(p.mark)).length,
        totalSymbols: positions.length,
      },
    };
  }

  function periodMetrics(events, startAt, endAt, startMarks = {}, endMarks = {}) {
    const startMs = new Date(startAt).getTime();
    const endMs = new Date(endAt).getTime();
    if (!Number.isFinite(startMs) || !Number.isFinite(endMs) || endMs < startMs) {
      throw new Error("period dates invalid");
    }

    const startState = snapshot(events, startMarks, startAt);
    const endState = snapshot(events, endMarks, endAt);
    const sorted = sortEvents(events);

    const periodExternalCashFlow = sorted
      .filter((e) => e.type === EVENT_TYPES.CASHFLOW)
      .filter((e) => {
        const t = new Date(e.timestamp).getTime();
        return t > startMs && t <= endMs;
      })
      .reduce((s, e) => s + e.amount, 0);

    const complete = startState.coverage.allMarksPresent && endState.coverage.allMarksPresent;
    const pnl = complete
      ? endState.equity - startState.equity - periodExternalCashFlow
      : null;
    const returnPct = Number.isFinite(pnl) && Math.abs(startState.equity) > 1e-12
      ? (pnl / startState.equity) * 100
      : null;

    return {
      startAt,
      endAt,
      startEquity: startState.equity,
      endEquity: endState.equity,
      periodExternalCashFlow,
      pnl,
      returnPct,
      complete,
      reason: complete ? "START_AND_END_MARKS_COMPLETE" : "MISSING_START_OR_END_MARK",
      start: startState,
      end: endState,
    };
  }

  function exportBundle(events) {
    return {
      schemaVersion: 1,
      exportedAt: new Date().toISOString(),
      events: sortEvents(events),
    };
  }

  /** Reject null/undefined/""/non-finite — never coerce Number(null)===0 into a mark. */
  function parseMarksObject(x, label = "marks") {
    if (!x || typeof x !== "object" || Array.isArray(x)) {
      throw new Error(label + " must be a JSON object");
    }
    const out = {};
    for (const k of Object.keys(x)) {
      const v = x[k];
      if (v === null || v === undefined || v === "") {
        throw new Error(
          label + ": mark for " + k + " is missing (null/blank); omit the key or provide a finite number"
        );
      }
      const n = num(v);
      if (n === null || n < 0) throw new Error(label + ": mark for " + k + " must be a finite non-negative number");
      out[String(k).toUpperCase()] = n;
    }
    return out;
  }

  /**
   * Historical period queries must use explicit endMarks only.
   * Live marks are allowed only when endAt is effectively "now" and endMarks JSON is empty.
   */
  function resolvePeriodEndMarks(endAt, endMarksFromForm = {}, liveMerged = {}, nowMs = Date.now()) {
    const explicit = endMarksFromForm && typeof endMarksFromForm === "object" ? endMarksFromForm : {};
    if (Object.keys(explicit).length) {
      return { endMarks: explicit, usedLiveEnd: false };
    }
    const endMs = new Date(endAt).getTime();
    const now = Number.isFinite(nowMs) ? nowMs : Date.now();
    const isLiveEnd = Number.isFinite(endMs) && Math.abs(endMs - now) <= 2 * 60 * 1000;
    if (isLiveEnd) {
      return { endMarks: liveMerged || {}, usedLiveEnd: true };
    }
    return { endMarks: {}, usedLiveEnd: false };
  }

  return {
    ASSET_TYPES,
    SIDES,
    EVENT_TYPES,
    normalizePositionIdentity,
    normalizeEvent,
    sortEvents,
    buildState,
    snapshot,
    periodMetrics,
    exportBundle,
    parseMarksObject,
    resolvePeriodEndMarks,
    num,
  };
})();
