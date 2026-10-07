window.PortfolioSpreadPnlV1 = (() => {
  const EPS = 1e-12;
  const norm = (event) => window.PortfolioLedgerV1.normalizeEvent(event);

  function addLot(lots, qty, price, multiplier, timestamp, id) {
    if (Math.abs(qty) <= EPS) return;
    lots.push({ qty, price, multiplier, timestamp, id });
  }

  function applyFill(book, event) {
    let remaining = event.side === "BUY" ? event.quantity : -event.quantity;
    while (Math.abs(remaining) > EPS && book.lots.length) {
      const lot = book.lots[0];
      if (Math.sign(lot.qty) === Math.sign(remaining)) break;

      const closingQty = Math.min(Math.abs(lot.qty), Math.abs(remaining));
      if (lot.qty > 0 && remaining < 0) {
        book.realizedPnl += (event.price - lot.price) * closingQty * lot.multiplier;
      } else {
        book.realizedPnl += (lot.price - event.price) * closingQty * lot.multiplier;
      }

      lot.qty += Math.sign(lot.qty) * -closingQty;
      remaining -= Math.sign(remaining) * closingQty;
      if (Math.abs(lot.qty) <= EPS) book.lots.shift();
    }

    if (Math.abs(remaining) > EPS) {
      addLot(book.lots, remaining, event.price, event.multiplier, event.timestamp, event.id);
    }
    book.fees += event.fees;
  }

  function buildBooks(events, asOf = null) {
    const cutoff = asOf ? new Date(asOf).getTime() : Infinity;
    if (asOf && !Number.isFinite(cutoff)) throw new Error("invalid asOf");

    const books = {};
    const ordered = window.PortfolioLedgerV1.sortEvents ? window.PortfolioLedgerV1.sortEvents(events || []) : (events || []).map(norm);
    for (const event of ordered) {
      if (event.type !== "FILL" || event.assetType !== "OPTION" || !event.positionIdentity) continue;
      const t = new Date(event.timestamp).getTime();
      if (t > cutoff) continue;

      const id = event.positionIdentity;
      const key = id.spreadId + "::" + id.legRole + "::" + event.symbol;
      if (!books[key]) {
        books[key] = {
          spreadId: id.spreadId,
          campaignId: id.campaignId || null,
          strategyRole: id.strategyRole || null,
          legRole: id.legRole,
          symbol: event.symbol,
          multiplier: event.multiplier,
          lots: [],
          realizedPnl: 0,
          fees: 0
        };
      }
      const book = books[key];
      if (book.multiplier !== event.multiplier) {
        throw new Error("multiplier mismatch for " + event.symbol + " in spread " + id.spreadId);
      }
      applyFill(book, event);
      if (id.campaignId && !book.campaignId) book.campaignId = id.campaignId;
      if (id.strategyRole && !book.strategyRole) book.strategyRole = id.strategyRole;
    }
    return books;
  }

  function openQuantity(book) {
    return book.lots.reduce((sum, lot) => sum + lot.qty, 0);
  }

  function parseMark(mark) {
    // Never coerce null/undefined/""/non-finite to 0 (Number(null)===0 would invent P&L).
    if (mark === null || mark === undefined || mark === "") return null;
    const n = typeof mark === "number" ? mark : Number(mark);
    return Number.isFinite(n) && n >= 0 ? n : null;
  }

  function legSnapshot(book, mark) {
    const quantity = openQuantity(book);
    const parsedMark = parseMark(mark);
    const hasMark = parsedMark !== null;
    let currentValue = null;
    let unrealizedPnl = null;
    let entryDebit = 0;
    let entryCredit = 0;

    for (const lot of book.lots) {
      if (lot.qty > 0) entryDebit += lot.qty * lot.price * lot.multiplier;
      if (lot.qty < 0) entryCredit += Math.abs(lot.qty) * lot.price * lot.multiplier;
      if (hasMark) {
        currentValue = (currentValue || 0) + lot.qty * parsedMark * lot.multiplier;
        if (lot.qty > 0) unrealizedPnl = (unrealizedPnl || 0) + (parsedMark - lot.price) * lot.qty * lot.multiplier;
        if (lot.qty < 0) unrealizedPnl = (unrealizedPnl || 0) + (lot.price - parsedMark) * Math.abs(lot.qty) * lot.multiplier;
      }
    }

    return {
      symbol: book.symbol,
      legRole: book.legRole,
      quantity,
      multiplier: book.multiplier,
      entryDebit,
      entryCredit,
      mark: hasMark ? parsedMark : null,
      currentValue,
      realizedPnl: book.realizedPnl,
      unrealizedPnl,
      fees: book.fees,
      totalPnl: unrealizedPnl === null ? null : book.realizedPnl + unrealizedPnl - book.fees,
      openLots: book.lots.map(lot => ({
        qty: lot.qty,
        price: lot.price,
        timestamp: lot.timestamp,
        id: lot.id
      }))
    };
  }

  function attribute(events, marks = {}, asOf = null) {
    const identity = window.PortfolioPositionIdentityV1.build(events, asOf);
    const books = buildBooks(events, asOf);
    const rows = [];

    for (const paired of identity.rows) {
      if (paired.status !== "PAIRED") {
        if (paired.status === "METADATA_CONFLICT") {
          rows.push({
            spreadId: paired.spreadId,
            campaignId: null,
            strategyRole: paired.strategyRole,
            status: "INCOMPLETE",
            reason: "POSITION_IDENTITY_METADATA_CONFLICT",
            units: null,
            longLeg: null,
            shortLeg: null,
            entryDebit: null,
            entryCredit: null,
            netEntryCredit: null,
            currentValue: null,
            realizedPnl: null,
            unrealizedPnl: null,
            fees: null,
            totalPnl: null
          });
          continue;
        }

        const spreadBooks = Object.values(books).filter(b => b.spreadId === paired.spreadId);
        const roleBooks = {
          LONG: spreadBooks.filter(b => b.legRole === "LONG"),
          SHORT: spreadBooks.filter(b => b.legRole === "SHORT")
        };
        const longQty = roleBooks.LONG.reduce((s, b) => s + openQuantity(b), 0);
        const shortQty = roleBooks.SHORT.reduce((s, b) => s + openQuantity(b), 0);
        const fullyClosed =
          paired.everPaired === true &&
          roleBooks.LONG.length > 0 &&
          roleBooks.SHORT.length > 0 &&
          Math.abs(longQty) <= EPS &&
          Math.abs(shortQty) <= EPS;

        if (fullyClosed) {
          const realizedPnl = spreadBooks.reduce((s, b) => s + b.realizedPnl, 0);
          const fees = spreadBooks.reduce((s, b) => s + b.fees, 0);
          rows.push({
            spreadId: paired.spreadId,
            campaignId: paired.campaignId,
            strategyRole: paired.strategyRole,
            status: "CLOSED",
            reason: "PAIR_HISTORY_CLOSED",
            units: null,
            longLeg: null,
            shortLeg: null,
            entryDebit: 0,
            entryCredit: 0,
            netEntryCredit: 0,
            currentValue: 0,
            realizedPnl,
            unrealizedPnl: 0,
            fees,
            totalPnl: realizedPnl - fees
          });
          continue;
        }

        rows.push({
          spreadId: paired.spreadId,
          campaignId: paired.campaignId,
          strategyRole: paired.strategyRole,
          status: "INCOMPLETE",
          reason: "POSITION_IDENTITY_" + paired.status,
          units: null,
          longLeg: null,
          shortLeg: null,
          entryDebit: null,
          entryCredit: null,
          netEntryCredit: null,
          currentValue: null,
          realizedPnl: null,
          unrealizedPnl: null,
          fees: null,
          totalPnl: null
        });
        continue;
      }

      const longMeta = paired.legs.LONG[0];
      const shortMeta = paired.legs.SHORT[0];
      const longBook = books[paired.spreadId + "::LONG::" + longMeta.symbol];
      const shortBook = books[paired.spreadId + "::SHORT::" + shortMeta.symbol];
      const longLeg = legSnapshot(longBook, marks[longMeta.symbol]);
      const shortLeg = legSnapshot(shortBook, marks[shortMeta.symbol]);

      if (!(longLeg.quantity > EPS) || !(shortLeg.quantity < -EPS)) {
        rows.push({
          spreadId: paired.spreadId,
          campaignId: paired.campaignId,
          strategyRole: paired.strategyRole,
          status: "INCOMPLETE",
          reason: "LEG_DIRECTION_MISMATCH",
          units: null,
          longLeg,
          shortLeg,
          entryDebit: null,
          entryCredit: null,
          netEntryCredit: null,
          currentValue: null,
          realizedPnl: null,
          unrealizedPnl: null,
          fees: null,
          totalPnl: null
        });
        continue;
      }

      const spreadBooks = Object.values(books).filter(b => b.spreadId === paired.spreadId);
      const realizedPnl = spreadBooks.reduce((s, b) => s + b.realizedPnl, 0);
      const fees = spreadBooks.reduce((s, b) => s + b.fees, 0);

      if (longLeg.mark === null || shortLeg.mark === null || longLeg.unrealizedPnl === null || shortLeg.unrealizedPnl === null) {
        rows.push({
          spreadId: paired.spreadId,
          campaignId: paired.campaignId,
          campaignMetadata: paired.campaignMetadata || "UNASSIGNED",
          strategyRole: paired.strategyRole,
          status: "INCOMPLETE",
          reason: "MISSING_CURRENT_MARK",
          units: paired.units,
          longLeg,
          shortLeg,
          entryDebit: longLeg.entryDebit + shortLeg.entryDebit,
          entryCredit: longLeg.entryCredit + shortLeg.entryCredit,
          netEntryCredit: longLeg.entryCredit + shortLeg.entryCredit - longLeg.entryDebit - shortLeg.entryDebit,
          currentValue: null,
          realizedPnl,
          unrealizedPnl: null,
          fees,
          totalPnl: null
        });
        continue;
      }

      const entryDebit = longLeg.entryDebit + shortLeg.entryDebit;
      const entryCredit = longLeg.entryCredit + shortLeg.entryCredit;
      const currentValue = longLeg.currentValue + shortLeg.currentValue;
      const unrealizedPnl = longLeg.unrealizedPnl + shortLeg.unrealizedPnl;

      rows.push({
        spreadId: paired.spreadId,
        campaignId: paired.campaignId,
        strategyRole: paired.strategyRole,
        status: "PAIRED",
        reason: "PAIR_AND_MARKS_COMPLETE",
        units: paired.units,
        longLeg,
        shortLeg,
        entryDebit,
        entryCredit,
        netEntryCredit: entryCredit - entryDebit,
        currentValue,
        realizedPnl,
        unrealizedPnl,
        fees,
        totalPnl: realizedPnl + unrealizedPnl - fees
      });
    }

    return {
      rows,
      summary: {
        total: rows.length,
        paired: rows.filter(r => r.status === "PAIRED").length,
        closed: rows.filter(r => r.status === "CLOSED").length,
        incomplete: rows.filter(r => r.status === "INCOMPLETE").length
      },
      contract: "SPREAD_PNL_ATTRIBUTION_V1",
      rules: {
        pAndLSource: "LEG_FIFO_REALIZED_PLUS_LEG_MARK_UNREALIZED_MINUS_FEES",
        marketValueRole: "DISPLAY_ONLY_NOT_PNL",
        unpaired: "INCOMPLETE",
        strategyMutation: false,
        brokerOrders: false
      }
    };
  }

  return { attribute };
})();