window.PortfolioCampaignTimelineV1 = (() => {
  const EPS = 1e-12;

  function campaignKey(row) {
    const id = row?.campaignId;
    return id ? String(id) : "UNASSIGNED";
  }

  function finite(v) {
    if (v === null || v === undefined || v === "") return null;
    return Number.isFinite(Number(v)) ? Number(v) : null;
  }

  function normalizeMarksSeries(series) {
    return (Array.isArray(series) ? series : [])
      .map((row) => {
        const timestamp = row && row.timestamp ? new Date(row.timestamp) : null;
        if (!timestamp || !Number.isFinite(timestamp.getTime())) return null;
        const marks = row && row.marks && typeof row.marks === "object" && !Array.isArray(row.marks)
          ? row.marks
          : {};
        const normalized = {};
        for (const [symbol, value] of Object.entries(marks)) {
          const px = finite(value);
          if (px !== null) normalized[String(symbol).toUpperCase()] = px;
        }
        return { timestamp: timestamp.toISOString(), marks: normalized };
      })
      .filter(Boolean)
      .sort((a, b) => a.timestamp.localeCompare(b.timestamp));
  }

  function marksAt(series, timestamp) {
    const marks = {};
    let foundTimestamp = null;
    for (const row of series) {
      if (row.timestamp > timestamp) break;
      Object.assign(marks, row.marks);
      foundTimestamp = row.timestamp;
    }
    return foundTimestamp ? { timestamp: foundTimestamp, marks } : null;
  }

  function ensureSpread(state, identity) {
    if (!state.has(identity.spreadId)) {
      state.set(identity.spreadId, {
        spreadId: identity.spreadId,
        campaignId: identity.campaignId || null,
        strategyRole: identity.strategyRole || null,
        legs: { LONG: {}, SHORT: {} },
        seenRoles: { LONG: false, SHORT: false }
      });
    }
    const group = state.get(identity.spreadId);
    if (identity.campaignId && !group.campaignId) group.campaignId = identity.campaignId;
    if (identity.strategyRole && !group.strategyRole) group.strategyRole = identity.strategyRole;
    group.seenRoles[identity.legRole] = true;
    return group;
  }

  function activeLegs(group, role) {
    return Object.entries(group.legs[role])
      .filter(([, qty]) => Math.abs(qty) > EPS)
      .map(([symbol, qty]) => ({ symbol, quantity: qty }))
      .sort((a, b) => a.symbol.localeCompare(b.symbol));
  }

  function snapshot(group) {
    if (!group) {
      return {
        status: "UNSEEN",
        units: null,
        signature: null,
        long: [],
        short: []
      };
    }

    const long = activeLegs(group, "LONG");
    const short = activeLegs(group, "SHORT");
    const hasHistory = group.seenRoles.LONG && group.seenRoles.SHORT;
    let status = "INCOMPLETE";
    let units = null;

    if (hasHistory && long.length === 0 && short.length === 0) {
      status = "CLOSED";
    } else if (long.length === 1 && short.length === 1) {
      const longQty = Math.abs(long[0].quantity);
      const shortQty = Math.abs(short[0].quantity);
      if (Math.abs(longQty - shortQty) <= EPS && long[0].quantity > EPS && short[0].quantity < -EPS) {
        status = "PAIRED";
        units = longQty;
      } else if (Math.abs(longQty - shortQty) > EPS) {
        status = "IMBALANCED";
      }
    } else if (long.length > 1 || short.length > 1) {
      status = "MULTI_CONTRACT";
    }

    const signature = status === "PAIRED"
      ? long[0].symbol + " | " + short[0].symbol
      : null;

    return { status, units, signature, long, short };
  }

  function applyEvent(group, event) {
    const identity = event.positionIdentity;
    const signedQty = event.side === "BUY" ? event.quantity : -event.quantity;
    const role = identity.legRole;
    group.legs[role][event.symbol] = (group.legs[role][event.symbol] || 0) + signedQty;
  }

  function classify(before, after, lastPairedSignature, lastPairedUnits, wasEverPaired) {
    if (after.status === "CLOSED") return wasEverPaired ? "FULL_CLOSE" : "INCOMPLETE";

    if (after.status === "PAIRED") {
      if (!lastPairedSignature) return "OPEN";
      if (after.signature !== lastPairedSignature) return "ROLL_COMPLETE";
      if (lastPairedUnits !== null && after.units < lastPairedUnits - EPS) return "PARTIAL_CLOSE";
      if (lastPairedUnits !== null && after.units > lastPairedUnits + EPS) return "ADD";
      return "UPDATE";
    }

    if (before.status === "PAIRED" && after.status === "MULTI_CONTRACT") return "ROLL_START";
    if (before.status === "PAIRED" && after.status === "INCOMPLETE") return "LEG_ADJUST";
    if (after.status === "IMBALANCED") return "IMBALANCE";
    if (after.status === "MULTI_CONTRACT") return "MULTI_CONTRACT";
    return "INCOMPLETE";
  }

  function rowFor(attrRows, spreadId) {
    return (attrRows || []).find((row) => row.spreadId === spreadId) || null;
  }

  function realizedNet(row) {
    if (!row) return null;
    const realized = finite(row.realizedPnl);
    const fees = finite(row.fees);
    if (realized === null || fees === null) return null;
    return realized - fees;
  }

  function cumulativeCampaignRealized(rows, key) {
    let total = 0;
    for (const row of rows || []) {
      if (campaignKey(row) !== key) continue;
      const value = realizedNet(row);
      if (value === null) return null;
      total += value;
    }
    return total;
  }

  function campaignRole(rows, key) {
    const roles = new Set();
    for (const row of rows || []) {
      if (campaignKey(row) === key && row.strategyRole) roles.add(row.strategyRole);
    }
    if (!roles.size) return null;
    return roles.size === 1 ? [...roles][0] : "MIXED";
  }

  function timeline(events, marksSeries = []) {
    const ordered = window.PortfolioLedgerV1.sortEvents(events || []);
    const series = normalizeMarksSeries(marksSeries);
    const state = new Map();
    const lastPairedSignature = new Map();
    const lastPairedUnits = new Map();
    const hadPaired = new Set();
    const histories = [];
    const prefix = [];

    for (const event of ordered) {
      const beforePrefix = prefix.slice();
      prefix.push(event);

      if (event.type !== "FILL" || event.assetType !== "OPTION" || !event.positionIdentity) continue;

      const identity = event.positionIdentity;
      const group = ensureSpread(state, identity);
      const before = snapshot(group);
      applyEvent(group, event);
      const after = snapshot(group);
      const eventKind = classify(
        before,
        after,
        lastPairedSignature.get(identity.spreadId) || null,
        lastPairedUnits.has(identity.spreadId) ? lastPairedUnits.get(identity.spreadId) : null,
        hadPaired.has(identity.spreadId)
      );

      if (after.status === "PAIRED") {
        hadPaired.add(identity.spreadId);

        lastPairedSignature.set(identity.spreadId, after.signature);
        lastPairedUnits.set(identity.spreadId, after.units);
      }

      const point = marksAt(series, event.timestamp);
      const marks = point ? point.marks : {};
      const afterAttr = window.PortfolioSpreadPnlV1.attribute(prefix, marks);
      const afterRow = rowFor(afterAttr.rows, identity.spreadId);
      const realizedNetPnl = realizedNet(afterRow);
      const totalPnl = afterRow ? finite(afterRow.totalPnl) : null;
      const unrealizedPnl = afterRow ? finite(afterRow.unrealizedPnl) : null;
      const campaignId = afterRow?.campaignId || group.campaignId || null;
      const campaignKeyValue = campaignId ? String(campaignId) : "UNASSIGNED";
      const campaignCumulativeRealizedNetPnl = cumulativeCampaignRealized(afterAttr.rows, campaignKeyValue);

      histories.push({
        timestamp: event.timestamp,
        eventId: event.id,
        spreadId: identity.spreadId,
        campaignId,
        campaignKey: campaignKeyValue,
        strategyRole: afterRow?.strategyRole || group.strategyRole || null,
        eventKind,
        beforeStatus: before.status,
        afterStatus: after.status,
        units: after.units,
        longContracts: after.long.map((x) => x.symbol),
        shortContracts: after.short.map((x) => x.symbol),
        realizedPnl: afterRow ? finite(afterRow.realizedPnl) : null,
        fees: afterRow ? finite(afterRow.fees) : null,
        realizedNetPnl,
        unrealizedPnl,
        totalPnl,
        pnlBasis: totalPnl !== null
          ? "MARKED_TOTAL"
          : (realizedNetPnl !== null ? "REALIZED_ONLY" : "NONE"),
        markTimestamp: point ? point.timestamp : null,
        campaignCumulativeRealizedNetPnl,
        completeness: after.status,
        attributionStatus: afterRow?.status || after.status
      });
    }

    const campaignsMap = new Map();
    for (const row of histories) {
      if (!campaignsMap.has(row.campaignKey)) {
        campaignsMap.set(row.campaignKey, {
          campaignId: row.campaignId,
          campaignKey: row.campaignKey,
          strategyRole: row.strategyRole || null,
          events: [],
          finalRealizedNetPnl: null
        });
      }
      const campaign = campaignsMap.get(row.campaignKey);
      if (!campaign.strategyRole && row.strategyRole) campaign.strategyRole = row.strategyRole;
      else if (campaign.strategyRole && row.strategyRole && campaign.strategyRole !== row.strategyRole) campaign.strategyRole = "MIXED";
      campaign.events.push(row);
      if (row.campaignCumulativeRealizedNetPnl !== null) {
        campaign.finalRealizedNetPnl = row.campaignCumulativeRealizedNetPnl;
      }
    }

    const campaigns = [...campaignsMap.values()]
      .sort((a, b) => a.campaignKey.localeCompare(b.campaignKey));

    return {
      rows: histories,
      campaigns,
      summary: {
        campaigns: campaigns.length,
        timelineEvents: histories.length,
        opens: histories.filter((x) => x.eventKind === "OPEN").length,
        rolls: histories.filter((x) => x.eventKind === "ROLL_COMPLETE").length,
        partialCloses: histories.filter((x) => x.eventKind === "PARTIAL_CLOSE").length,
        fullCloses: histories.filter((x) => x.eventKind === "FULL_CLOSE").length,
        incomplete: histories.filter((x) => x.eventKind === "INCOMPLETE" || x.completeness === "IMBALANCED" || x.completeness === "MULTI_CONTRACT").length,
        markedEvents: histories.filter((x) => x.pnlBasis === "MARKED_TOTAL").length,
        realizedOnlyEvents: histories.filter((x) => x.pnlBasis === "REALIZED_ONLY").length,
        scope: "IDENTIFIED_OPTION_SPREADS_ONLY"
      },
      contract: "PORTFOLIO_CAMPAIGN_TIMELINE_V1",
      rules: {
        historySource: "EXPLICIT_OPTION_FILL_EVENT_ORDER",
        realizedNetPnl: "SPREAD_REALIZED_PNL_MINUS_FEES",
        totalPnl: "ONLY_WHEN_POINT_IN_TIME_MARKS_EXIST",
        markLookahead: "LATEST_MARK_AT_OR_BEFORE_EVENT_TIMESTAMP",
        currentLiveMarksReuse: false,
        unpaired: "NO_FABRICATED_TOTAL_PNL",
        scope: "IDENTIFIED_OPTION_SPREADS_ONLY",
        strategyMutation: false,
        brokerOrders: false
      }
    };
  }

  return { timeline };
})();
