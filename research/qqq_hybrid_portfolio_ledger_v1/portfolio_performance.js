window.PortfolioCampaignPerformanceV1 = (() => {
  const COMPLETE = new Set(["PAIRED", "CLOSED"]);

  function validPnl(row) {
    return row && COMPLETE.has(row.status) && Number.isFinite(Number(row.totalPnl))
      ? Number(row.totalPnl)
      : null;
  }

  function buildSpreadMap(rows) {
    return new Map((rows || []).map(row => [String(row.spreadId), row]));
  }

  function campaignKey(row) {
    const id = row?.campaignId;
    if (row?.campaignMetadata === "INCOMPLETE") return "CAMPAIGN_METADATA_INCOMPLETE::" + String(row.spreadId);
    if (row?.campaignMetadata === "CONFLICT") return "CAMPAIGN_METADATA_CONFLICT::" + String(row.spreadId);
    return id ? String(id) : "UNASSIGNED";
  }

  function performance(events, startAt, endAt, startMarks = {}, endMarks = {}) {
    const portfolio = window.PortfolioLedgerV1.periodMetrics(
      events, startAt, endAt, startMarks, endMarks
    );
    const startAttr = window.PortfolioSpreadPnlV1.attribute(events, startMarks, startAt);
    const endAttr = window.PortfolioSpreadPnlV1.attribute(events, endMarks, endAt);
    const startMap = buildSpreadMap(startAttr.rows);
    const endMap = buildSpreadMap(endAttr.rows);
    const spreadIds = new Set([...startMap.keys(), ...endMap.keys()]);
    const spreadRows = [];

    for (const spreadId of spreadIds) {
      const startRow = startMap.get(spreadId) || null;
      const endRow = endMap.get(spreadId) || null;
      const startPnl = startRow ? validPnl(startRow) : 0;
      const endPnl = endRow ? validPnl(endRow) : 0;

      let status = "COMPLETE";
      let reason = "START_AND_END_ATTRIBUTION_COMPLETE";
      let periodPnl = null;

      if (startRow && startPnl === null) {
        status = "INCOMPLETE";
        reason = "START_ATTRIBUTION_INCOMPLETE";
      } else if (endRow && endPnl === null) {
        status = "INCOMPLETE";
        reason = "END_ATTRIBUTION_INCOMPLETE";
      } else {
        periodPnl = endPnl - startPnl;
      }

      const ref = endRow || startRow;
      spreadRows.push({
        spreadId,
        campaignId: ref?.campaignId || null,
        campaignMetadata: ref?.campaignMetadata || "UNASSIGNED",
        strategyRole: ref?.strategyRole || null,
        status,
        reason,
        startPnl,
        endPnl: status === "COMPLETE" ? endPnl : null,
        periodPnl,
        endStatus: endRow?.status || null,
        endUnits: endRow?.units ?? null
      });
    }

    const grouped = {};
    for (const row of spreadRows) {
      const key = campaignKey(row);
      if (!grouped[key]) {
        grouped[key] = {
          campaignId: row.campaignId,
          campaignKey: key,
          strategyRoles: new Set(),
          spreadCount: 0,
          pairedEnd: 0,
          closedEnd: 0,
          incomplete: 0,
          startPnl: 0,
          currentPnl: 0,
          periodPnl: 0,
          hasCompletePeriod: true
        };
      }
      const g = grouped[key];
      g.spreadCount += 1;
      if (row.strategyRole) g.strategyRoles.add(row.strategyRole);
      if (row.endStatus === "PAIRED") g.pairedEnd += 1;
      if (row.endStatus === "CLOSED") g.closedEnd += 1;
      if (row.status !== "COMPLETE" || ["INCOMPLETE", "CONFLICT"].includes(row.campaignMetadata)) {
        g.incomplete += 1;
        g.hasCompletePeriod = false;
      } else {
        g.startPnl += row.startPnl;
        g.currentPnl += row.endPnl;
        g.periodPnl += row.periodPnl;
      }
    }

    const campaigns = Object.values(grouped).map(g => ({
      campaignId: g.campaignId,
      campaignKey: g.campaignKey,
      strategyRole: g.strategyRoles.size === 1 ? [...g.strategyRoles][0] : (g.strategyRoles.size ? "MIXED" : null),
      status: g.hasCompletePeriod ? "COMPLETE" : "INCOMPLETE",
      spreadCount: g.spreadCount,
      pairedEnd: g.pairedEnd,
      closedEnd: g.closedEnd,
      incomplete: g.incomplete,
      startPnl: g.hasCompletePeriod ? g.startPnl : null,
      currentPnl: g.hasCompletePeriod ? g.currentPnl : null,
      periodPnl: g.hasCompletePeriod ? g.periodPnl : null
    })).sort((a, b) => a.campaignKey.localeCompare(b.campaignKey));

    const completeCampaigns = campaigns.filter(c => c.status === "COMPLETE");
    return {
      portfolio,
      campaigns,
      spreadRows: spreadRows.sort((a, b) => a.spreadId.localeCompare(b.spreadId)),
      summary: {
        campaigns: campaigns.length,
        completeCampaigns: completeCampaigns.length,
        incompleteCampaigns: campaigns.length - completeCampaigns.length,
        identifiedSpreads: spreadRows.length,
        completeSpreads: spreadRows.filter(r => r.status === "COMPLETE").length,
        incompleteSpreads: spreadRows.filter(r => r.status !== "COMPLETE").length,
        campaignPeriodPnl: completeCampaigns.reduce((s, c) => s + c.periodPnl, 0),
        scope: "IDENTIFIED_OPTION_SPREADS_ONLY"
      },
      contract: "PORTFOLIO_CAMPAIGN_PERFORMANCE_V1",
      rules: {
        periodPnl: "END_CUMULATIVE_SPREAD_PNL_MINUS_START_CUMULATIVE_SPREAD_PNL",
        newSpreadAtPeriodStart: "START_PNL_ZERO_WHEN_NOT_PRESENT",
        closedSpread: "RETAIN_REALIZED_PNL_THROUGH_PERIOD_END",
        incompleteAttribution: "NO_PERIOD_PNL",
        campaignMetadata: "ONLY_COMPLETE_CAMPAIGN_ID_MAY_AGGREGATE",
        portfolioPnlSource: "LEDGER_PERIOD_METRICS",
        strategyMutation: false,
        brokerOrders: false
      }
    };
  }

  return { performance };
})();