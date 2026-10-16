window.M1M2Lab = (() => {
  const POLICY = Object.freeze({
    version: "M1M2-LAB-V1-POLICY-BASELINE",
    vixHigh: 28,
    termThinPct: 5
  });

  const ARCHIVE_CONTRACT = Object.freeze({
    sourceRepo: "JUN-ZS/timber-blade-kind-dawn",
    sourceRef: "main",
    sourceFiles: Object.freeze({
      radarTs: "8f05a2bbf35ccc136eaab081eadbd52723b50db9",
      policyTs: "6e9a1cab6fdc50c2f025f1c5d0db7a7d1bf97645",
      bookTs: "641dc4b6f8d64d596b00031b00c108f47b3db1d9",
      splitsTs: "7936337677dc402184b68e132b476de184282b1f",
      spotsJson: "2a12ac605cb1bb96522cbd7195fc93e95e1c1fe7"
    }),
    semantics: "SOURCE_CODE_EXACT_PROXY_NOT_TRUE_VX_FUTURES",
    recoveredTerm: "m1_proxy=max(VIX,1e-6); lift=0.10*tanh((VIX_MA20-VIX)/6); m2_proxy=m1_proxy*(1+lift); TS=lift"
  });

  const METHODS = Object.freeze({
    REAL_OBSERVED_CONTROL: Object.freeze({
      id: "REAL_OBSERVED_CONTROL",
      label: "REAL observed M1/M2 — ground-truth control (NOT reconstruction)",
      provenance: "OBSERVED_EXTERNAL",
      status: "CONTROL_ONLY",
      description: "Use observed M1/M2 directly; no inference. This lane establishes the exact term/action state available from the observed dataset."
    }),
    ARCHIVE_V4_PROXY: Object.freeze({
      id: "ARCHIVE_V4_PROXY",
      label: "Archive termSlope — exact source proxy (NOT true VX M1/M2)",
      provenance: "DERIVED_FROM_ARCHIVE_CLUE",
      status: "UNVALIDATED",
      description: "m1_proxy=VIX; lift=0.10*tanh((VIX_MA20-VIX)/6); m2_proxy=m1_proxy*(1+lift)"
    })
  });

  function finite(x) {
    return Number.isFinite(x);
  }

  function num(x, d = null) {
    if (x === null || x === undefined || x === "") return d;
    const v = Number(x);
    return finite(v) ? v : d;
  }

  function pct(x, digits = 2) {
    return finite(x) ? Number((x * 100).toFixed(digits)) : null;
  }

  function rollingMean(values, i, window) {
    const start = Math.max(0, i - window + 1);
    let sum = 0;
    let n = 0;
    for (let j = start; j <= i; j++) {
      const v = num(values[j]);
      if (finite(v)) {
        sum += v;
        n++;
      }
    }
    return n ? sum / n : null;
  }

  function reconstructRow(rows, i, methodId = "ARCHIVE_V4_PROXY") {
    const method = METHODS[methodId];
    if (!method) throw new Error("Unknown reconstruction method: " + methodId);

    const r = rows[i];

    if (methodId === "REAL_OBSERVED_CONTROL") {
      return {
        m1: num(r.M1),
        m2: num(r.M2),
        lift: term(num(r.M1), num(r.M2)),
        ma20: rollingMean(rows.map(x => x.VIX), i, 20),
        source: "OBSERVED",
        method: methodId,
        provenance: "OBSERVED_EXTERNAL",
        role: "GROUND_TRUTH_CONTROL"
      };
    }

    const vix = num(r.VIX);
    const ma20 = rollingMean(rows.map(x => x.VIX), i, 20);

    if (!finite(vix) || !finite(ma20)) {
      return {
        m1: null,
        m2: null,
        lift: null,
        ma20,
        source: "RECONSTRUCTED",
        method: methodId,
        provenance: "DERIVED"
      };
    }

    const lift = 0.10 * Math.tanh((ma20 - vix) / 6.0);
    const m1 = vix;
    const m2 = m1 * (1.0 + lift);

    return {
      m1,
      m2,
      lift,
      ma20,
      source: "RECONSTRUCTED",
      method: methodId,
      provenance: "DERIVED"
    };
  }

  function reconstructSeries(rows, methodId = "ARCHIVE_V4_PROXY") {
    return rows.map((_, i) => reconstructRow(rows, i, methodId));
  }

  function realTermSeries(rows) {
    return rows.map(r => ({
      date: r.Date,
      m1: num(r.M1),
      m2: num(r.M2),
      s: term(num(r.M1), num(r.M2)),
      source: "OBSERVED",
      provenance: "OBSERVED_EXTERNAL"
    }));
  }

    function term(m1, m2) {
    return finite(m1) && finite(m2) && Math.abs(m1) > 1e-12
      ? (m2 - m1) / m1
      : null;
  }

  function regime(s, vix) {
    if (!finite(s) || !finite(vix)) return "DATA INCOMPLETE";
    if (vix >= POLICY.vixHigh && s <= 0) return "SHOCK";
    if (s <= 0 || vix >= POLICY.vixHigh) return "PRE-SHOCK";
    if (s <= POLICY.termThinPct / 100) return "WEAKENING";
    return "CARRY";
  }
  function halfSpreadV(vix) {
    const v = num(vix, 0);
    return Math.min(Math.max(0.035 + 0.14 * Math.max(v / 100 - 0.16, 0), 0.03), 0.16);
  }

  function archiveState(vix, rQ, rV, s) {
    const shock = (finite(rV) && rV > 0.06) || (finite(vix) && vix > 35) || (finite(rQ) && rQ < -0.03);
    if (shock) return "Shock";
    if (halfSpreadV(vix) > 0.14) return "High-Spread";
    if (finite(s) && finite(vix) && s >= 0 && vix < 28) return "Decay-Optimal";
    return "Normal";
  }

  function archiveAction(vix, rQ, rV, s) {
    const shock = (finite(rV) && rV > 0.06) || (finite(vix) && vix > 35) || (finite(rQ) && rQ < -0.03);
    return shock || (finite(s) && s < 0) ? "QQQ_CC_ONLY" : "PAIR";
  }

  function archiveCarry(vix, rQ, rV, s) {
    return archiveAction(vix, rQ, rV, s) === "PAIR";
  }


  function action(s, vix) {
    const r = regime(s, vix);
    if (r === "SHOCK" || r === "PRE-SHOCK") return "REDUCE";
    if (r === "WEAKENING") return "HOLD";
    if (r === "CARRY") return "BUY";
    return "HOLD";
  }

  function mean(xs) {
    const a = xs.filter(finite);
    return a.length ? a.reduce((x, y) => x + y, 0) / a.length : null;
  }

  function mae(xs) {
    return mean(xs.map(Math.abs));
  }

  function rmse(xs) {
    const a = xs.filter(finite);
    return a.length ? Math.sqrt(a.reduce((s, x) => s + x * x, 0) / a.length) : null;
  }

  function bias(xs) {
    return mean(xs);
  }

  function mapePct(truth, pred) {
    const e = [];
    for (let i = 0; i < truth.length; i++) {
      const t = truth[i], p = pred[i];
      if (finite(t) && finite(p) && Math.abs(t) > 1e-12) e.push(Math.abs((p - t) / t) * 100);
    }
    return mean(e);
  }

  function compare(rows, reconstructed, spotsByDate = {}) {
    const out = [];
    let regimeMatches = 0;
    let actionMatches = 0;
    let termSignMatches = 0;
    let archiveStateMatches = 0;
    let archiveActionMatches = 0;
    let archiveCarryMatches = 0;
    let archiveEligible = 0;
    let eligible = 0;

    const m1Err = [];
    const m2Err = [];
    const sErr = [];

    for (let i = 0; i < rows.length; i++) {
      const r = rows[i];
      const tM1 = num(r.M1), tM2 = num(r.M2);
      const pM1 = num(reconstructed[i]?.m1), pM2 = num(reconstructed[i]?.m2);
      const tS = term(tM1, tM2), pS = term(pM1, pM2);

      if (finite(tM1) && finite(pM1)) m1Err.push(pM1 - tM1);
      if (finite(tM2) && finite(pM2)) m2Err.push(pM2 - tM2);
      if (finite(tS) && finite(pS)) sErr.push(pS - tS);

      const tRegime = regime(tS, num(r.VIX));
      const pRegime = regime(pS, num(r.VIX));
      const tAction = action(tS, num(r.VIX));
      const pAction = action(pS, num(r.VIX));

      const spot = spotsByDate[r.Date?.slice(0,10)] || null;
      const prevSpot = spot?.prevDate ? spotsByDate[spot.prevDate] || null : null;
      const rQ = spot && prevSpot ? num(spot.QQQ) / num(prevSpot.QQQ) - 1 : null;
      const rV = spot && prevSpot ? num(spot.VXX) / num(prevSpot.VXX) - 1 : null;
      const taState = archiveState(num(r.VIX), rQ, rV, tS);
      const paState = archiveState(num(r.VIX), rQ, rV, pS);
      const taAction = archiveAction(num(r.VIX), rQ, rV, tS);
      const paAction = archiveAction(num(r.VIX), rQ, rV, pS);
      const taCarry = archiveCarry(num(r.VIX), rQ, rV, tS);
      const paCarry = archiveCarry(num(r.VIX), rQ, rV, pS);

      if (tRegime === pRegime) regimeMatches++;
      if (tAction === pAction) actionMatches++;
      if (taState === paState) archiveStateMatches++;
      if (taAction === paAction) archiveActionMatches++;
      if (taCarry === paCarry) archiveCarryMatches++;
      if (finite(tS) && finite(pS) && (tS > 0) === (pS > 0)) termSignMatches++;
      if (finite(tS) && finite(pS)) eligible++;
      if (spot) archiveEligible++;

      out.push({
        date: r.Date,
        vix: num(r.VIX),
        truth: { m1: tM1, m2: tM2, s: tS, regime: tRegime, action: tAction },
        reconstructed: { m1: pM1, m2: pM2, s: pS, regime: pRegime, action: pAction },
        errors: { m1: finite(tM1) && finite(pM1) ? pM1 - tM1 : null, m2: finite(tM2) && finite(pM2) ? pM2 - tM2 : null, s: finite(tS) && finite(pS) ? pS - tS : null },
        regimeMatch: tRegime === pRegime,
        actionMatch: tAction === pAction,
        archive: {
          rQ, rV,
          truthState: taState, reconState: paState,
          truthAction: taAction, reconAction: paAction,
          truthVxxCarry: taCarry, reconVxxCarry: paCarry,
          stateMatch: taState === paState,
          actionMatch: taAction === paAction,
          carryMatch: taCarry === paCarry,
          eligible: !!spot
        }
      });
    }

    return {
      rows: out,
      metrics: {
        n: rows.length,
        m1: { mae: mae(m1Err), rmse: rmse(m1Err), bias: bias(m1Err), mapePct: mapePct(rows.map(r => num(r.M1)), reconstructed.map(x => x.m1)) },
        m2: { mae: mae(m2Err), rmse: rmse(m2Err), bias: bias(m2Err), mapePct: mapePct(rows.map(r => num(r.M2)), reconstructed.map(x => x.m2)) },
        s: { mae: mae(sErr), rmse: rmse(sErr), bias: bias(sErr) },
        termSignAgreementPct: eligible ? (termSignMatches / eligible) * 100 : null,
        regimeAgreementPct: rows.length ? (regimeMatches / rows.length) * 100 : null,
        actionAgreementPct: rows.length ? (actionMatches / rows.length) * 100 : null,
        archiveStateAgreementPct: archiveEligible ? (archiveStateMatches / archiveEligible) * 100 : null,
        archiveActionAgreementPct: archiveEligible ? (archiveActionMatches / archiveEligible) * 100 : null,
        archiveVxxCarryAgreementPct: archiveEligible ? (archiveCarryMatches / archiveEligible) * 100 : null,
        archiveOverlapRows: archiveEligible
      }
    };
  }

  function topErrors(comparison, key, n = 10) {
    return comparison.rows
      .filter(x => finite(x.errors[key]))
      .slice()
      .sort((a, b) => Math.abs(b.errors[key]) - Math.abs(a.errors[key]))
      .slice(0, n);
  }

  function leakageAudit(rows, methodId = "ARCHIVE_V4_PROXY", cutIndex = null) {
    const n = rows.length;
    const cut = cutIndex === null ? Math.max(0, Math.floor(n * 0.7)) : cutIndex;
    const baseline = reconstructSeries(rows, methodId);
    const altered = rows.map((r, i) => i > cut ? { ...r, M1: 9999, M2: 9999, VIX: num(r.VIX) } : { ...r });
    const replay = reconstructSeries(altered, methodId);
    let priorStable = true;
    for (let i = 0; i <= cut; i++) {
      const a = baseline[i], b = replay[i];
      if ((a.m1 ?? null) !== (b.m1 ?? null) || (a.m2 ?? null) !== (b.m2 ?? null)) {
        priorStable = false;
        break;
      }
    }
    return {
      pass: priorStable,
      cutIndex: cut,
      testedPriorRows: cut + 1,
      rule: "Future truth M1/M2 must not influence earlier reconstruction."
    };
  }

  function buildMaskedInput(rows) {
    return rows.map(r => ({ Date: r.Date, VIX: r.VIX }));
  }

  function csvFromComparison(comparison) {
    const head = [
      "Date","VIX",
      "truth_M1","recon_M1","error_M1",
      "truth_M2","recon_M2","error_M2",
      "truth_S","recon_S","error_S",
      "truth_regime","recon_regime","regime_match",
      "truth_action","recon_action","action_match"
    ];
    const esc = v => {
      const s = v === null || v === undefined ? "" : String(v);
      return /[",\\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
    };
    const lines = [head.join(",")];
    for (const x of comparison.rows) {
      lines.push([
        x.date, x.vix,
        x.truth.m1, x.reconstructed.m1, x.errors.m1,
        x.truth.m2, x.reconstructed.m2, x.errors.m2,
        x.truth.s, x.reconstructed.s, x.errors.s,
        x.truth.regime, x.reconstructed.regime, x.regimeMatch,
        x.truth.action, x.reconstructed.action, x.actionMatch
      ].map(esc).join(","));
    }
    return lines.join("\n");
  }

  return Object.freeze({
    POLICY, ARCHIVE_CONTRACT, METHODS, num, pct, rollingMean, reconstructRow, reconstructSeries, realTermSeries, archiveState, archiveAction, archiveCarry,
    term, regime, action, compare, topErrors, leakageAudit, buildMaskedInput,
    csvFromComparison
  });
})();
