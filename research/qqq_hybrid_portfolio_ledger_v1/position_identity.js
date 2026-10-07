window.PortfolioPositionIdentityV1 = (() => {
  const EPS = 1e-12;
  const norm = (event) => {
    if (window.PortfolioLedgerV1 && window.PortfolioLedgerV1.normalizeEvent) {
      return window.PortfolioLedgerV1.normalizeEvent(event);
    }
    return event;
  };

  function build(events, asOf = null) {
    const cutoff = asOf ? new Date(asOf).getTime() : Infinity;
    if (asOf && !Number.isFinite(cutoff)) throw new Error("invalid asOf");

    const groups = {};
    let optionFills = 0;
    let unmappedOptionFills = 0;

    const ordered = window.PortfolioLedgerV1.sortEvents ? window.PortfolioLedgerV1.sortEvents(events || []) : (events || []).map(norm);
    for (const event of ordered) {
      if (event.type !== "FILL" || event.assetType !== "OPTION") continue;
      const t = new Date(event.timestamp).getTime();
      if (t > cutoff) continue;

      optionFills += 1;
      const identity = event.positionIdentity;
      if (!identity) {
        unmappedOptionFills += 1;
        continue;
      }

      const spreadId = identity.spreadId;
      const legRole = identity.legRole;
      const signedQty = event.side === "BUY" ? event.quantity : -event.quantity;

      if (!groups[spreadId]) {
        groups[spreadId] = {
          spreadId,
          campaignId: identity.campaignId || null,
          strategyRoles: new Set(),
          legs: { LONG: {}, SHORT: {} },
          everPaired: false,
          metadataConflict: false,
          campaignIdsSeen: new Set(identity.campaignId ? [identity.campaignId] : [])
        };
      }

      const group = groups[spreadId];
      // campaignId must be consistent for the same spreadId (no first-seen wins).
      if (identity.campaignId) {
        group.campaignIdsSeen.add(identity.campaignId);
        if (!group.campaignId) {
          group.campaignId = identity.campaignId;
        } else if (group.campaignId !== identity.campaignId) {
          group.metadataConflict = true;
        }
      }
      if (identity.strategyRole) group.strategyRoles.add(identity.strategyRole);

      const bySymbol = group.legs[legRole];
      if (!bySymbol[event.symbol]) bySymbol[event.symbol] = 0;
      bySymbol[event.symbol] += signedQty;

      const activeLong = Object.values(group.legs.LONG).filter(q => Math.abs(q) > EPS);
      const activeShort = Object.values(group.legs.SHORT).filter(q => Math.abs(q) > EPS);
      if (activeLong.length === 1 && activeShort.length === 1) {
        const lq = activeLong[0];
        const sq = activeShort[0];
        if (lq > EPS && sq < -EPS && Math.abs(Math.abs(lq) - Math.abs(sq)) <= EPS) {
          group.everPaired = true;
        }
      }
    }

    const rows = Object.values(groups).map(group => {
      const activeLegs = {};
      for (const role of ["LONG", "SHORT"]) {
        activeLegs[role] = Object.entries(group.legs[role])
          .filter(([, q]) => Math.abs(q) > EPS)
          .map(([symbol, q]) => ({ symbol, quantity: q }));
      }

      const longLegs = activeLegs.LONG;
      const shortLegs = activeLegs.SHORT;
      let status = "INCOMPLETE";
      let units = null;

      if (group.metadataConflict) {
        status = "METADATA_CONFLICT";
        units = null;
      } else if (longLegs.length === 1 && shortLegs.length === 1) {
        const longQty = Math.abs(longLegs[0].quantity);
        const shortQty = Math.abs(shortLegs[0].quantity);
        if (Math.abs(longQty - shortQty) <= EPS) {
          status = "PAIRED";
          units = longQty;
        } else {
          status = "IMBALANCED";
        }
      } else if (longLegs.length > 1 || shortLegs.length > 1) {
        status = "MULTI_CONTRACT";
      }

      return {
        spreadId: group.spreadId,
        campaignId: group.metadataConflict ? null : group.campaignId,
        campaignIds: [...group.campaignIdsSeen].sort(),
        strategyRole: group.strategyRoles.size === 1 ? [...group.strategyRoles][0] : (group.strategyRoles.size ? "MIXED" : null),
        status,
        units,
        everPaired: Boolean(group.everPaired),
        legs: activeLegs
      };
    }).sort((a, b) => a.spreadId.localeCompare(b.spreadId));

    return {
      rows,
      summary: {
        optionFills,
        identifiedOptionFills: optionFills - unmappedOptionFills,
        unmappedOptionFills,
        paired: rows.filter(r => r.status === "PAIRED").length,
        incomplete: rows.filter(r => r.status === "INCOMPLETE").length,
        imbalanced: rows.filter(r => r.status === "IMBALANCED").length,
        multiContract: rows.filter(r => r.status === "MULTI_CONTRACT").length,
        metadataConflict: rows.filter(r => r.status === "METADATA_CONFLICT").length
      },
      contract: "POSITION_IDENTITY_V1"
    };
  }

  return { build };
})();