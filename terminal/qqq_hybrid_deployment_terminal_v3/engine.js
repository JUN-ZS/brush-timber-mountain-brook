
window.HybridEngineV3 = (() => {
  const POLICY = Object.freeze({
    engineVersion: "V3-FREE-VX-PROVENANCE-1",
    policyVersion: "ORIGINAL_HYBRID_BASELINE_FROZEN",
    corePct: 42,
    vxxNormalPct: 18,
    vxxHighPct: 10,
    vxxCallBudgetPct: 2,
    qqqCallBudgetPct: 1.2,
    vixHigh: 28,
    termSafe: 5,
    maxTermAgeDays: 4,
    qqqRollDte: 14,
    qqqRollDelta: 0.16,
    vxxRollDte: 14,
    vxxRollDelta: 0.20,
  });

  const num = (v, d = null) => {
    if (v === null || v === undefined || v === "") return d;
    const x = parseFloat(String(v).replace(/,/g, ""));
    return Number.isFinite(x) ? x : d;
  };

  function term(m1, m2) {
    return Number.isFinite(m1) && Number.isFinite(m2) && m1 !== 0
      ? ((m2 - m1) / m1) * 100
      : null;
  }

  function daysBetween(a, b) {
    if (!a || !b) return null;
    const x = new Date(a + "T00:00:00Z").getTime();
    const y = new Date(b + "T00:00:00Z").getTime();
    if (!Number.isFinite(x) || !Number.isFinite(y)) return null;
    return Math.abs(y - x) / 86400000;
  }

  function dataHealth(d) {
    const hasSpot = [d.qqq, d.vxx, d.vix].every(Number.isFinite);
    const hasTerm = Number.isFinite(d.m1) && Number.isFinite(d.m2) && Number.isFinite(d.s);
    if (!hasSpot || !hasTerm) {
      return {status: "BLOCKED", label: "DATA BLOCKED", reason: "Required spot or VX term field missing."};
    }
    const age = d.termAsOf && d.today ? daysBetween(d.termAsOf, d.today) : 0;
    const asofGap = d.spotAsOf && d.termAsOf ? daysBetween(d.spotAsOf, d.termAsOf) : 0;
    if (age !== null && age > POLICY.maxTermAgeDays) {
      return {status: "STALE", label: "DATA STALE", ageDays: age, reason: "VX term source is older than the permitted operator cadence."};
    }
    // Spot and VX timestamps can legitimately differ by one calendar day because
    // the terminal runs in the user's local timezone while Cboe data_asof is New York.
    if (asofGap !== null && asofGap > 2) {
      return {status: "MIXED", label: "AS-OF MIXED", ageDays: asofGap, reason: "Spot and term inputs are materially out of sync; review before acting."};
    }
    return {status: "FRESH", label: "DATA FRESH", ageDays: age, reason: "Required fields are present and within the configured cadence."};
  }

  function derive(d) {
    const health = dataHealth(d);
    if (health.status === "BLOCKED") {
      return {
        state: "DATA BLOCKED",
        action: "HOLD",
        gate: "BLOCKED",
        targetVxx: null,
        targetVxxCall: null,
        targetQqqCall: null,
        blocked: true,
        health,
        reason: "Data incomplete: preserve current position and do not invent a risk action.",
      };
    }
    if (health.status === "STALE" || health.status === "MIXED") {
      return {
        state: health.status === "STALE" ? "DATA STALE" : "AS-OF MIXED",
        action: "HOLD",
        gate: health.status,
        targetVxx: null,
        targetVxxCall: null,
        targetQqqCall: null,
        blocked: true,
        health,
        reason: health.reason,
      };
    }

    const high = d.vix >= POLICY.vixHigh;
    const back = d.s <= 0;
    const thin = d.s <= POLICY.termSafe;
    let state;
    let action;
    let gate;
    let reason;

    if (high && back) {
      state = "SHOCK";
      action = "REDUCE";
      gate = "CUT";
      reason = "High VIX + VX backwardation: cut VXX seller risk first; preserve QQQ core.";
    } else if (back) {
      state = "PRE-SHOCK";
      action = "REDUCE";
      gate = "CUT";
      reason = "VX backwardation: carry gate is broken; no new short-vol deployment.";
    } else if (high) {
      state = "PRE-SHOCK";
      action = "REDUCE";
      gate = "CAP";
      reason = "VIX is high: cap seller exposure and stop adding new carry.";
    } else if (thin) {
      state = "WEAKENING";
      action = "HOLD";
      gate = "WATCH";
      reason = "Contango is positive but thin: keep core, do not add short-vol carry.";
    } else {
      state = "CARRY";
      action = "BUY";
      gate = "OPEN";
      reason = "Contango is healthy and VIX is below the high threshold: restore carry legs toward baseline target.";
    }

    const vxxBase = high ? POLICY.vxxHighPct : POLICY.vxxNormalPct;
    return {
      state,
      action,
      gate,
      reason,
      blocked: false,
      health,
      targets: {
        qqqCorePct: POLICY.corePct,
        vxxPct: back ? 0 : vxxBase,
        vxxCallBudgetPct: back || high ? 0 : POLICY.vxxCallBudgetPct,
        qqqCallBudgetPct: back || high ? 0 : POLICY.qqqCallBudgetPct,
      },
      reasons: {
        "VIX": high ? ">= 28" : "< 28",
        "S": back ? "<= 0" : (thin ? "<= 5%" : "> 5%"),
      },
    };
  }

  function targetLedger(d, e, ledger) {
    const cur = {
      qqqShares: num(ledger.qqqShares, 0),
      vxxPct: num(ledger.vxxPct, 0),
      qqqCalls: num(ledger.qqqCalls, 0),
      vxxCalls: num(ledger.vxxCalls, 0),
    };

    if (e.blocked) {
      return {
        current: cur,
        target: {...cur},
        deltas: {
          qqqShares: 0,
          vxxPct: 0,
          qqqCalls: 0,
          vxxCalls: 0,
        },
        blocked: true,
      };
    }

    const nav = num(ledger.nav, 0);
    const qqqPrice = num(d.qqq, 0);
    const rawShares = nav > 0 && qqqPrice > 0 ? (nav * e.targets.qqqCorePct / 100) / qqqPrice : cur.qqqShares;
    const qCallQty = nav > 0 ? Math.floor(nav * e.targets.qqqCallBudgetPct / 100 / 100) : 0;
    const vCallQty = nav > 0 ? Math.floor(nav * e.targets.vxxCallBudgetPct / 100 / 100) : 0;

    const buyAllowed = e.action === "BUY";
    const target = {
      qqqShares: buyAllowed ? Math.floor(rawShares) : cur.qqqShares,
      vxxPct: buyAllowed ? e.targets.vxxPct : Math.min(cur.vxxPct, e.targets.vxxPct),
      qqqCalls: buyAllowed ? qCallQty : Math.min(cur.qqqCalls, qCallQty),
      vxxCalls: buyAllowed ? vCallQty : Math.min(cur.vxxCalls, vCallQty),
    };

    return {
      current: cur,
      target,
      deltas: {
        qqqShares: target.qqqShares - cur.qqqShares,
        vxxPct: target.vxxPct - cur.vxxPct,
        qqqCalls: target.qqqCalls - cur.qqqCalls,
        vxxCalls: target.vxxCalls - cur.vxxCalls,
      },
      blocked: false,
    };
  }

  function actionRows(book) {
    return Object.entries(book.deltas).map(([key, diff]) => ({
      key,
      diff,
      kind: Math.abs(diff) < 1e-9 ? "HOLD" : diff > 0 ? "ADD" : "REDUCE",
    }));
  }

  function triggers(d, e, opt = {}) {
    const rows = [];
    if (Number.isFinite(d.s)) {
      rows.push({
        id: "S_ZERO",
        label: "VX term to zero",
        value: d.s <= 0 ? "TRIGGERED" : d.s.toFixed(2) + "% → 0",
        fire: d.s <= 0,
        priority: "HIGH",
      });
      rows.push({
        id: "S_SAFE",
        label: "VX carry line",
        value: d.s <= POLICY.termSafe ? d.s.toFixed(2) + "% ≤ 5%" : (d.s - POLICY.termSafe).toFixed(2) + "% above",
        fire: d.s <= POLICY.termSafe,
        priority: "MED",
      });
    }
    if (Number.isFinite(d.vix)) {
      rows.push({
        id: "VIX_28",
        label: "VIX high line",
        value: d.vix >= POLICY.vixHigh ? "TRIGGERED" : (POLICY.vixHigh - d.vix).toFixed(2) + " away",
        fire: d.vix >= POLICY.vixHigh,
        priority: "HIGH",
      });
    }

    const qdte = num(opt.qqqDte), qdelta = num(opt.qqqDelta), vdte = num(opt.vxxDte), vdelta = num(opt.vxxDelta);
    rows.push({
      id: "QQQ_ROLL",
      label: "QQQ far call roll",
      value: "DTE " + (Number.isFinite(qdte) ? qdte : "—") + " · Δ " + (Number.isFinite(qdelta) ? qdelta.toFixed(2) : "—"),
      fire: (Number.isFinite(qdte) && qdte <= POLICY.qqqRollDte) || (Number.isFinite(qdelta) && qdelta >= POLICY.qqqRollDelta),
      priority: "MED",
    });
    rows.push({
      id: "VXX_ROLL",
      label: "VXX call roll",
      value: "DTE " + (Number.isFinite(vdte) ? vdte : "—") + " · Δ " + (Number.isFinite(vdelta) ? vdelta.toFixed(2) : "—"),
      fire: (Number.isFinite(vdte) && vdte <= POLICY.vxxRollDte) || (Number.isFinite(vdelta) && vdelta >= POLICY.vxxRollDelta) || e.state === "SHOCK",
      priority: "HIGH",
    });
    return rows;
  }

  return {POLICY, num, term, dataHealth, derive, targetLedger, actionRows, triggers};
})();
