window.HybridEngine = (() => {
  const POLICY = Object.freeze({
    engineVersion: "V2-EVOLVED-GOLDEN-1",
    policyRole: "REFERENCE_BASELINE_PENDING_EXACT_REPLAY_PARITY",
    corePct: 42,
    vxxNormalPct: 18,
    vxxHighPct: 10,
    vxxCallBudgetPct: 2,
    qqqCallBudgetPct: 1.2,
    vixHigh: 28,
    termSafe: 5,
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

  const term = (m1, m2) =>
    Number.isFinite(m1) && Number.isFinite(m2) && m1 !== 0
      ? ((m2 - m1) / m1) * 100
      : null;

  function derive(d) {
    if (![d.qqq, d.vxx, d.vix].every(Number.isFinite)) {
      return {
        state: "DATA INCOMPLETE",
        action: "HOLD",
        conf: 5,
        gate: "BLOCKED",
        why: "Need QQQ + VXX + VIX. / 需要 QQQ、VXX、VIX。",
        vxxTarget: null,
        vxxCalls: null,
        blocked: true,
      };
    }

    if (!Number.isFinite(d.s)) {
      return {
        state: "DATA INCOMPLETE",
        action: "HOLD",
        conf: 35,
        gate: "BLOCKED",
        why: "M1/M2 unavailable. No term-structure guess is permitted. / M1/M2 未有資料，禁止猜期限結構。",
        vxxTarget: null,
        vxxCalls: null,
        blocked: true,
      };
    }

    const high = d.vix >= POLICY.vixHigh;
    const back = d.s <= 0;
    let state, action, conf, why;

    if (high && back) {
      state = "SHOCK";
      action = "REDUCE";
      conf = 97;
      why = "High VIX + backwardation: reduce VXX seller legs first; QQQ core stays intact. / 高 VIX＋倒掛：先減 VXX 賣方，QQQ 核心保持。";
    } else if (back) {
      state = "PRE-SHOCK";
      action = "REDUCE";
      conf = 92;
      why = "Backwardation removes the carry gate; stop adding short-vol carry. / 倒掛令 carry 閘門失效，停止追加 short-vol carry。";
    } else if (high) {
      state = "PRE-SHOCK";
      action = "REDUCE";
      conf = 88;
      why = "VIX is high: cap VXX seller exposure and avoid new carry. / VIX 高，封頂 VXX 空頭並停止新 carry。";
    } else if (d.s <= POLICY.termSafe) {
      state = "WEAKENING";
      action = "HOLD";
      conf = 79;
      why = "Contango is positive but thin: hold QQQ core and wait. / Contango 仍正但變薄，保留 QQQ 核心並等待。";
    } else {
      state = "CARRY";
      action = "BUY";
      conf = 90;
      why = "Supportive contango with VIX below high threshold: restore carry legs toward target. / Contango 充足且 VIX 未過閾值，向目標恢復 carry。";
    }

    const base = high ? POLICY.vxxHighPct : POLICY.vxxNormalPct;
    return {
      state,
      action,
      conf,
      gate: back ? "CUT" : high ? "CAP" : "OPEN",
      why,
      vxxTarget: back ? 0 : base,
      vxxCalls: back || high ? 0 : POLICY.vxxCallBudgetPct,
      reasons: [
        high ? "VIX >= 28" : "VIX < 28",
        back ? "S <= 0" : "S > 0",
        d.s > POLICY.termSafe ? "S > 5%" : "S <= 5%",
      ],
      blocked: false,
    };
  }

  function optionQty(nav, budgetPct, credit) {
    return nav > 0 && credit > 0
      ? Math.max(0, Math.floor(nav * (budgetPct / 100) / (credit * 100)))
      : 0;
  }

  function targets(d, e, ledger, qqqCredit = 0, vxxCredit = 0) {
    const nav = num(ledger.nav, 0);
    const cur = {
      qqq: num(ledger.curQqq, 100),
      vxx: num(ledger.curVxx, 0),
      qcall: num(ledger.curQCall, 0),
      vcall: num(ledger.curVCall, 0),
    };

    if (e.blocked) {
      return {
        QQQ: { current: cur.qqq, target: cur.qqq, unit: "shares" },
        VXX: { current: cur.vxx, target: cur.vxx, unit: "% NAV" },
        QQQ_CALL: { current: cur.qcall, target: cur.qcall, unit: "spreads" },
        VXX_CALL: { current: cur.vcall, target: cur.vcall, unit: "spreads" },
        blocked: true,
      };
    }

    const rawQqq = nav > 0 && Number.isFinite(d.qqq) ? (nav * (POLICY.corePct / 100)) / d.qqq : 100;
    const rawQcall = optionQty(nav, POLICY.qqqCallBudgetPct, qqqCredit);
    const rawVcall = e.vxxCalls > 0 ? optionQty(nav, POLICY.vxxCallBudgetPct, vxxCredit) : 0;
    const allowAdd = e.action === "BUY";

    return {
      QQQ: { current: cur.qqq, target: allowAdd ? rawQqq : cur.qqq, unit: "shares" },
      VXX: { current: cur.vxx, target: allowAdd ? e.vxxTarget : Math.min(cur.vxx, e.vxxTarget), unit: "% NAV" },
      QQQ_CALL: { current: cur.qcall, target: allowAdd ? rawQcall : Math.min(cur.qcall, rawQcall), unit: "spreads" },
      VXX_CALL: { current: cur.vcall, target: allowAdd ? rawVcall : Math.min(cur.vcall, rawVcall), unit: "spreads" },
      blocked: false,
    };
  }

  function delta(cur, tgt) {
    const diff = tgt - cur;
    if (Math.abs(diff) < 1e-9) return { kind: "hold", diff: 0, label: "HOLD / 保持" };
    return diff > 0
      ? { kind: "add", diff, label: "ADD / 加倉" }
      : { kind: "reduce", diff, label: "REDUCE / 減倉" };
  }

  function triggers(d, e, opt = {}) {
    const out = [];
    out.push(
      Number.isFinite(d.s)
        ? { id: "TERM_ZERO", title: "S <= 0 / 倒掛", value: d.s <= 0 ? "BREACHED / 已觸發" : d.s.toFixed(2) + "% -> 0", fire: d.s <= 0, priority: "HIGH" }
        : { id: "TERM_ZERO", title: "M1/M2 / 期限結構", value: "MISSING / 缺失", fire: true, priority: "BLOCK" }
    );
    if (Number.isFinite(d.vix)) {
      out.push({
        id: "VIX_HIGH",
        title: "VIX >= 28 / 高 VIX",
        value: d.vix >= POLICY.vixHigh ? "BREACHED / 已觸發" : (POLICY.vixHigh - d.vix).toFixed(2) + " away",
        fire: d.vix >= POLICY.vixHigh,
        priority: "HIGH",
      });
    }
    const qd = num(opt.qqqDte), qdlt = num(opt.qqqDelta), vd = num(opt.vxxDte), vdlt = num(opt.vxxDelta);
    out.push({
      id: "QQQ_ROLL",
      title: "QQQ Far Call / 遠價 Call",
      value: `DTE ${Number.isFinite(qd) ? qd : "—"} · Δ ${Number.isFinite(qdlt) ? qdlt.toFixed(2) : "—"}`,
      fire: (Number.isFinite(qd) && qd <= POLICY.qqqRollDte) || (Number.isFinite(qdlt) && qdlt >= POLICY.qqqRollDelta),
      priority: "MED",
    });
    out.push({
      id: "VXX_ROLL",
      title: "VXX Call Spread / VXX Call",
      value: `DTE ${Number.isFinite(vd) ? vd : "—"} · Δ ${Number.isFinite(vdlt) ? vdlt.toFixed(2) : "—"}`,
      fire: (Number.isFinite(vd) && vd <= POLICY.vxxRollDte) || (Number.isFinite(vdlt) && vdlt >= POLICY.vxxRollDelta) || e.state === "SHOCK",
      priority: "HIGH",
    });
    return out;
  }

  function candidateFromChain(chain, spot, targetDelta = 0.10) {
    if (!Array.isArray(chain) || !chain.length || !Number.isFinite(spot)) return null;
    const valid = chain.filter(
      (x) =>
        Number.isFinite(num(x.strike)) &&
        Number.isFinite(num(x.delta)) &&
        Number.isFinite(num(x.days)) &&
        num(x.days) > 0 &&
        num(x.delta) > 0 &&
        num(x.delta) <= 0.25
    );
    if (!valid.length) return null;
    valid.sort((a, b) => Math.abs(num(a.delta) - targetDelta) - Math.abs(num(b.delta) - targetDelta));
    const short = valid[0];
    const longs = valid.filter((x) => num(x.strike) > num(short.strike));
    if (!longs.length) return null;
    longs.sort((a, b) => Math.abs(num(a.strike) - num(short.strike) * 1.015) - Math.abs(num(b.strike) - num(short.strike) * 1.015));
    const long = longs[0];
    return { shortStrike: num(short.strike), longStrike: num(long.strike), dte: num(short.days), delta: num(short.delta), credit: null, source: "LIVE CANDIDATE / 即時候選" };
  }

  return { POLICY, term, derive, targets, delta, triggers, candidateFromChain, num };
})();
