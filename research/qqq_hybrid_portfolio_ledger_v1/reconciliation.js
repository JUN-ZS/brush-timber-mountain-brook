window.PortfolioReconciliationV1 = (() => {
  const num = (v, d = null) => {
    if (v === null || v === undefined || v === "") return d;
    const x = Number(v);
    return Number.isFinite(x) ? x : d;
  };

  function positionMap(snapshot) {
    return Object.fromEntries((snapshot?.positions || []).map((p) => [String(p.symbol).toUpperCase(), p]));
  }

  function allocationPct(position, equity, direction = "LONG") {
    if (!position || !Number.isFinite(equity) || equity === 0 || !Number.isFinite(position.marketValue)) {
      return null;
    }
    const value = direction === "SHORT" ? Math.abs(Math.min(0, position.marketValue)) : Math.max(0, position.marketValue);
    return (value / Math.abs(equity)) * 100;
  }

  function gap(actual, target) {
    if (!Number.isFinite(actual) || !Number.isFinite(target)) return null;
    return actual - target;
  }

  function action(gapPct, tolerance = 0.25) {
    if (!Number.isFinite(gapPct)) return "UNMAPPED";
    if (Math.abs(gapPct) <= tolerance) return "ALIGNED";
    return gapPct < 0 ? "UNDERWEIGHT" : "OVERWEIGHT";
  }

  function reconcile(snapshot, strategy) {
    const target = strategy?.targets;
    if (!snapshot || !target || strategy?.available === false || strategy?.connected === false) {
      return {
        status: "UNAVAILABLE",
        reason: "V3 target is unavailable; no reconciliation is fabricated.",
        rows: [],
        summary: { comparable: 0, aligned: 0, underweight: 0, overweight: 0, unmapped: 0 },
      };
    }

    const equity = num(snapshot.equity);
    const positions = positionMap(snapshot);
    const qqqActual = allocationPct(positions.QQQ, equity, "LONG");
    const vxxActual = allocationPct(positions.VXX, equity, "SHORT");
    const rows = [
      {
        key: "QQQ_CORE",
        label: "QQQ CORE",
        actual: qqqActual,
        target: num(target.qqqCorePct),
        gap: gap(qqqActual, num(target.qqqCorePct)),
        unit: "% NAV",
        action: action(gap(qqqActual, num(target.qqqCorePct))),
        source: "LEDGER_QQQ_MARKET_VALUE",
      },
      {
        key: "VXX_SHORT",
        label: "VXX SHORT",
        actual: vxxActual,
        target: num(target.vxxPct),
        gap: gap(vxxActual, num(target.vxxPct)),
        unit: "% NAV",
        action: action(gap(vxxActual, num(target.vxxPct))),
        source: "LEDGER_VXX_SHORT_MARKET_VALUE",
      },
      {
        key: "QQQ_CALL_SPREAD",
        label: "QQQ CALL SPREAD",
        actual: null,
        target: null,
        gap: null,
        unit: "spreads",
        action: "UNMAPPED",
        source: "NOT_ENOUGH_LEG_PAIRING_METADATA",
      },
      {
        key: "VXX_CALL_SPREAD",
        label: "VXX CALL SPREAD",
        actual: null,
        target: null,
        gap: null,
        unit: "spreads",
        action: "UNMAPPED",
        source: "NOT_ENOUGH_LEG_PAIRING_METADATA",
      },
    ];

    const summary = rows.reduce((s, r) => {
      if (r.action === "UNMAPPED") s.unmapped += 1;
      else {
        s.comparable += 1;
        if (r.action === "ALIGNED") s.aligned += 1;
        if (r.action === "UNDERWEIGHT") s.underweight += 1;
        if (r.action === "OVERWEIGHT") s.overweight += 1;
      }
      return s;
    }, { comparable: 0, aligned: 0, underweight: 0, overweight: 0, unmapped: 0 });

    return {
      status: "READY",
      reason: "Only dimensions with a defensible mapping are compared. Option spreads stay unmapped until leg-pair identity is explicit.",
      rows,
      summary,
    };
  }

  return { reconcile };
})();
