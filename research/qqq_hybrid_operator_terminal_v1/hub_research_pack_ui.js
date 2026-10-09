(() => {
  "use strict";
  const E = window.HubOptionPackV1;
  const $ = (id) => document.getElementById(id);
  let lastChain = null;
  let lastCandidates = null;

  const ids = [
    "nav","cashPool","cashReservePct","totalOptionRiskPct","baseRiskReservedUsd","strategyRiskPct","spot","targetDte",
    "strategyMode","atmStrike","atmAsk","shortStrike","shortBid","wingStrike","wingAsk","longPutStrike","longPutAsk",
    "shortPutStrike","shortPutBid","requestedN","maxN","currentN","currentShorts","currentWings","currentShortDelta",
    "lowDeltaStreak","sessionsSinceChange","packagePnlUsd","currentShortAsk","currentWingBid","approachTouched",
    "nextDayReversal","nextDayContinuation","wave","prevClose","anchorClose","atr20","layerCap","currentLayers",
    "drawdown252Pct","return5dPct","applyRiskBank","bankSeedWinUsd","bankLossesUsd","bankMode","bankNetPnlUsd"
  ];
  const n = (id, fallback = null) => E.num($(id) ? $(id).value : null, fallback);
  const checked = (id) => $(id) && $(id).checked === true;
  const set = (id, value) => { if ($(id) && value !== undefined && value !== null && Number.isFinite(Number(value))) $(id).value = value; };
  const usd = (v) => Number.isFinite(Number(v)) ? "$" + Number(v).toLocaleString("en-US", { maximumFractionDigits: 2, minimumFractionDigits: 2 }) : "—";
  const fmt = (v, d = 0) => Number.isFinite(Number(v)) ? Number(v).toLocaleString("en-US", { maximumFractionDigits: d, minimumFractionDigits: d }) : "—";
  const pct = (v) => Number.isFinite(Number(v)) ? (Number(v) * 100).toFixed(1) + "%" : "—";
  const esc = (value) => String(value === null || value === undefined ? "" : value).replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
  const metric = (label, value) => "<div><small>" + esc(label) + "</small><b>" + esc(value) + "</b></div>";

  function commonBudget() {
    const nav = n("nav", 0);
    const cash = n("cashPool", 0);
    const reservePct = Math.max(0, Math.min(100, n("cashReservePct", 10)));
    const poolPct = Math.max(0, n("totalOptionRiskPct", 3.2));
    const baseReserved = Math.max(0, n("baseRiskReservedUsd", 0));
    const strategyPct = Math.max(0, n("strategyRiskPct", 2));
    const cashAfterReserve = Math.max(0, cash * (1 - reservePct / 100));
    const fullPool = Math.max(0, Math.min(nav * poolPct / 100, cashAfterReserve));
    const remainingPool = Math.max(0, fullPool - baseReserved);
    const strategyBudget = Math.max(0, Math.min(nav * strategyPct / 100, remainingPool));
    const bank = E.calculateRiskBank({
      mode: $("bankMode").value === "replenish-comparator" ? "replenish-comparator" : "isolated",
      seedWinUsd: n("bankSeedWinUsd", 0),
      laterLossesUsd: n("bankLossesUsd", 0),
      laterNetPnlUsd: n("bankNetPnlUsd", 0),
      candidateRiskUsd: 0
    });
    const applyBank = checked("applyRiskBank");
    const effectiveBudget = applyBank ? Math.min(strategyBudget, bank.availableRiskRightsUsd) : strategyBudget;
    return { nav, cash, reservePct, cashAfterReserve, fullPool, baseReserved, remainingPool, strategyBudget, effectiveBudget, applyBank, bank };
  }

  function currentInputs() {
    return {
      spot: n("spot"),
      atmStrike: n("atmStrike"), atmAsk: n("atmAsk"),
      shortStrike: n("shortStrike"), shortBid: n("shortBid"),
      wingStrike: n("wingStrike"), wingAsk: n("wingAsk"),
      longPutStrike: n("longPutStrike"), longPutAsk: n("longPutAsk"),
      shortPutStrike: n("shortPutStrike"), shortPutBid: n("shortPutBid")
    };
  }

  function selectVisibleFields() {
    const mode = $("strategyMode").value;
    const ratio = mode.startsWith("ratio-");
    const state = mode === "state-adaptive" || mode === "staggered";
    const shock = mode === "shock-put";
    $("ratioControlGroup").hidden = !ratio;
    $("stateControlGroup").hidden = !state;
    $("shockControlGroup").hidden = !shock;
    $("callLegGroup").hidden = shock;
    $("putLegGroup").hidden = !(state || mode === "staggered" || shock);
    const captions = {
      "ratio-harvest50": "Ratio-Call HARVEST50 V1",
      "ratio-dynamic-v2": "Ratio-Call Risk-Budget Dynamic-N V2",
      "ratio-fresh-v7": "Ratio-Call Fresh-Pair Dynamic-N V7",
      "state-adaptive": "State-Adaptive Geometry",
      "staggered": "Staggered Stack",
      "shock-put": "SHOCK-GATED Put Debit Spread"
    };
    $("resultStatus").dataset.mode = captions[mode];
  }

  async function refreshMarket() {
    const status = $("chainStatus");
    status.textContent = "正在向本機 V3 只讀 Snapshot 讀取 QQQ 現價…";
    try {
      const response = await fetch("/api/snapshot", { cache: "no-store" });
      const data = await response.json();
      const qqq = E.num(data.qqq ?? data.market?.qqq ?? data.snapshot?.qqq);
      if (!response.ok || !(qqq > 0)) throw new Error(data.message || data.error || "V3 Snapshot 未提供有效 QQQ 現價。");
      set("spot", qqq);
      status.textContent = "已讀取 V3 只讀 QQQ spot = " + usd(qqq) + "；請核對 as-of 時間。";
      render();
    } catch (error) {
      status.textContent = "V3 現價暫不可用：" + error.message + "。可手動輸入已核實價格；不會猜價。";
    }
  }

  function candidatePrice(row) {
    return row ? { strike: row.strike, ask: row.ask, bid: row.bid, delta: row.delta, deltaSource: row.deltaSource } : null;
  }

  async function loadChain() {
    const status = $("chainStatus");
    const spot = n("spot");
    if (!(spot > 0)) {
      status.textContent = "先刷新 V3 spot 或手動輸入已核實的 QQQ 現價。";
      return;
    }
    const targetDte = Math.max(14, Math.min(120, E.whole(n("targetDte", 45), 45)));
    status.textContent = "正在讀取 Yahoo 公開 QQQ option chain…";
    $("loadChainBtn").disabled = true;
    try {
      const response = await fetch("/api/options?symbol=QQQ&right=both&targetDte=" + encodeURIComponent(targetDte), { cache: "no-store" });
      const data = await response.json();
      if (!response.ok || !data.ok) throw new Error(data.error || "option chain not available");
      lastChain = data;
      lastCandidates = E.chooseChainLegs(data, spot, new Date().toISOString().slice(0, 10), targetDte);
      if (!lastCandidates.ready) {
        status.textContent = "到期日 " + esc(data.expiry || "unknown") + "，但未能可靠配齊全部 Hub 研究腿：" + lastCandidates.error;
        render();
        return;
      }
      const c = lastCandidates;
      set("atmStrike", c.atm.strike); set("atmAsk", c.atm.ask);
      set("shortStrike", c.short.strike); set("shortBid", c.short.bid);
      set("wingStrike", c.wing.strike); set("wingAsk", c.wing.ask);
      set("longPutStrike", c.longPut.strike); set("longPutAsk", c.longPut.ask);
      set("shortPutStrike", c.shortPut.strike); set("shortPutBid", c.shortPut.bid);
      const source = c.deltaSource === "BS_ESTIMATE" ? "Delta 由 Black-Scholes 估算" : "採用資料來源提供的 Delta";
      status.textContent = "候選已載入 · " + c.expiry + " · " + source + " · " + (data.source || "public chain") + "。報價可能延遲，不是可成交保證。";
      render();
    } catch (error) {
      lastChain = null; lastCandidates = null;
      status.textContent = "鏈資料載入失敗：" + error.message + "。你仍可手動輸入已核實的 Bid/Ask；缺資料不會補造。";
      render();
    } finally {
      $("loadChainBtn").disabled = false;
    }
  }

  function compute() {
    const budget = commonBudget();
    const input = currentInputs();
    const mode = $("strategyMode").value;
    let result;
    let riskAtTarget = 0;
    let debitAtTarget = 0;
    let oneUnitRisk = null;
    let title = "";
    let rows = [];
    const bankMeta = budget.applyBank
      ? "Bank gate active · " + usd(budget.bank.availableRiskRightsUsd) + " research risk rights"
      : "Bank gate off · capital/risk budget only";

    if (mode.startsWith("ratio-")) {
      title = $("resultStatus").dataset.mode || mode;
      result = E.calculateRatioCall({
        ...input, ...budget,
        budgetUsd: budget.effectiveBudget,
        mode,
        nav: budget.nav,
        requestedN: n("requestedN", 2),
        maxN: n("maxN", 4),
        currentN: n("currentN", 0),
        currentShorts: n("currentShorts", 0),
        currentWings: n("currentWings", 0),
        currentShortDelta: n("currentShortDelta", 0.2),
        lowDeltaStreak: n("lowDeltaStreak", 0),
        sessionsSinceChange: n("sessionsSinceChange", 99),
        packagePnlUsd: n("packagePnlUsd", 0),
        currentShortAsk: n("currentShortAsk"),
        currentWingBid: n("currentWingBid"),
        approachTouched: checked("approachTouched"),
        nextDayReversal: checked("nextDayReversal"),
        nextDayContinuation: checked("nextDayContinuation")
      });
      if (result.ready && result.entryN > 0) {
        riskAtTarget = result.riskUsd;
        debitAtTarget = Math.max(0, result.debitUsd || 0);
        oneUnitRisk = result.riskUsd;
      }
      rows = result.ready ? [
        ["選取 Profile", title],
        ["最大可負擔 N（測試範圍）", fmt(result.maxAffordableN)],
        ["進場 N", fmt(result.entryN)],
        ["ATM Long Call 合約", fmt(result.entryN ? 1 : 0)],
        ["OTM Short Call 合約", fmt(result.entryN ? result.entryN : 0)],
        ["更遠 OTM Long Wing 合約", fmt(result.entryN ? result.entryN : 0)],
        ["該結構 Entry max-loss proxy", usd(result.riskUsd)],
        ["淨 Debit（負數代表淨 Credit）", usd(result.debitUsd)],
        ["目前 Short target", fmt(result.targetShorts)],
        ["目前 Wing target", fmt(result.targetWings)],
        ["管理行動", result.action],
        ["風險估算來源", "同一到期日腿的 Bid/Ask + 到期 payoff proxy"]
      ] : [["狀態", result.status], ["原因", result.error || "報價／結構資料不足"]];
    } else if (mode === "state-adaptive") {
      title = "State-Adaptive Geometry";
      result = E.calculateStateAdaptive({ ...input, nav: budget.nav, budgetUsd: budget.effectiveBudget, wave: n("wave", 0), prevClose: n("prevClose"), anchorClose: n("anchorClose"), atr20: n("atr20") });
      if (result.ready) {
        riskAtTarget = result.riskUsd * result.targetPackages;
        debitAtTarget = Math.max(0, result.debitUsd || 0) * result.targetPackages;
        oneUnitRisk = result.riskUsd;
      }
      rows = result.ready ? [
        ["凍結入場結構", "+1 50Δ Call −2 20Δ Calls +2 8Δ Wings +1 25Δ Put −1 10Δ Put"],
        ["每組 max-loss proxy", usd(result.riskUsd)],
        ["每組淨 Debit（負數代表 Credit）", usd(result.debitUsd)],
        ["風險預算內最大 package units", fmt(result.maxPackages)],
        ["最大 units 使用的風險儲備", usd(riskAtTarget)],
        ["下一 wave 是否觸發", result.waveTrigger ? "YES" : "NO"],
        ["下一 Short Call delta target", result.nextCallShortDelta === null ? "NO MIGRATION" : fmt(result.nextCallShortDelta, 2)],
        ["下一 Short Put abs-delta target", result.nextPutShortAbsDelta === null ? "NO MIGRATION" : fmt(result.nextPutShortAbsDelta, 2)],
        ["研究規則", result.reason]
      ] : [["狀態", result.status], ["原因", result.error || "報價／結構資料不足"]];
    } else if (mode === "staggered") {
      title = "Staggered Stack";
      result = E.calculateStaggered({ ...input, nav: budget.nav, budgetUsd: budget.effectiveBudget, wave: 0, prevClose: null, anchorClose: null, atr20: null, layerCap: n("layerCap", 1), currentLayers: n("currentLayers", 0) });
      if (result.ready) {
        riskAtTarget = result.reserveAtTargetUsd;
        debitAtTarget = Math.max(0, result.debitUsd || 0) * result.targetLayers;
        oneUnitRisk = result.riskUsd;
      }
      rows = result.ready ? [
        ["凍結每個 Vintage", "+1 50Δ Call −2 20Δ Calls +2 8Δ Wings +1 25Δ Put −1 10Δ Put"],
        ["層數模式 / 上限", fmt(result.layerCap)],
        ["每層 max-loss proxy", usd(result.riskUsd)],
        ["目前活躍 Vintage", fmt(result.currentLayers)],
        ["可負擔的目標活躍 Vintage", fmt(result.targetLayers)],
        ["目標層風險儲備", usd(result.reserveAtTargetUsd)],
        ["剩餘研究風險額度", usd(result.remainingRiskUsd)],
        ["Action", result.action]
      ] : [["狀態", result.status], ["原因", result.error || "報價／結構資料不足"]];
    } else {
      title = "SHOCK-GATED Put Debit Spread";
      result = E.calculateShockGatedPut({ ...input, budgetUsd: budget.effectiveBudget, drawdown252Pct: n("drawdown252Pct", 0), return5dPct: n("return5dPct", 0) });
      if (result.ready) {
        riskAtTarget = result.riskUsd * result.targetContracts;
        debitAtTarget = Math.max(0, result.debitUsd || 0) * result.targetContracts;
        oneUnitRisk = result.riskUsd;
      }
      rows = result.ready ? [
        ["結構", "+1 higher-strike Long Put −1 farther-OTM Short Put"],
        ["每張價差的 Debit / max loss", usd(result.riskUsd)],
        ["Shock gate", result.triggered ? "TRIGGERED" : "NOT TRIGGERED"],
        ["最大可負擔張數（只代表容量）", fmt(result.maxContracts)],
        ["現行可新增張數", fmt(result.targetContracts)],
        ["條件", result.reason],
        ["Drawdown 252D / Return 5D", fmt(result.drawdown252Pct, 2) + "% / " + fmt(result.return5dPct, 2) + "%"]
      ] : [["狀態", result.status], ["原因", result.error || "報價／結構資料不足"]];
    }

    const bankCandidateRisk = riskAtTarget > 0 ? riskAtTarget : oneUnitRisk;
    const bank = E.calculateRiskBank({
      mode: $("bankMode").value === "replenish-comparator" ? "replenish-comparator" : "isolated",
      seedWinUsd: n("bankSeedWinUsd", 0),
      laterLossesUsd: n("bankLossesUsd", 0),
      laterNetPnlUsd: n("bankNetPnlUsd", 0),
      candidateRiskUsd: bankCandidateRisk
    });
    return { budget, mode, title, result, rows, riskAtTarget, debitAtTarget, oneUnitRisk, bank, bankCandidateRisk, bankMeta };
  }

  function render() {
    selectVisibleFields();
    const budget = commonBudget();
    $("capitalMetrics").innerHTML = [
      metric("Cash after reserve", usd(budget.cashAfterReserve)),
      metric("Total shared option-risk pool", usd(budget.fullPool)),
      metric("Pool after existing Hybrid reservations", usd(budget.remainingPool)),
      metric("This strategy budget cap", usd(budget.strategyBudget)),
      metric("Effective risk budget after Bank", usd(budget.effectiveBudget)),
      metric("Risk-WIN Bank available", usd(budget.bank.availableRiskRightsUsd))
    ].join("");

    const out = compute();
    const result = out.result;
    let status = result && result.status ? result.status : "PENDING";
    let headline = out.title || "Hub research template";
    let details = [];
    if (result && result.reason) details.push(result.reason);
    if (result && result.error) details.push(result.error);
    details.push(out.bankMeta);
    if (out.budget.applyBank) details.push(out.bank.reason);
    $("resultStatus").innerHTML = "<strong>" + esc(headline) + " · " + esc(status) + "</strong>" +
      details.map(x => "<p>" + esc(x) + "</p>").join("");
    $("resultMetrics").innerHTML = [
      metric("Risk capacity per structure", usd(out.oneUnitRisk)),
      metric("Risk reserved at target", usd(out.riskAtTarget)),
      metric("Positive debit cash requirement (preview)", usd(out.debitAtTarget)),
      metric("Shared risk pool left after target", usd(Math.max(0, out.budget.remainingPool - out.riskAtTarget))),
      metric("Bank available rights", usd(out.bank.availableRiskRightsUsd)),
      metric("Bank candidate gate", out.budget.applyBank ? (out.bank.eligible ? "PASS" : "BLOCK / CHECK") : "OFF")
    ].join("");

    $("resultTableWrap").innerHTML = "<table class=\"decision-table\"><thead><tr><th>計算項目</th><th>結果</th></tr></thead><tbody>" +
      out.rows.map(row => "<tr><td>" + esc(row[0]) + "</td><td>" + esc(row[1]) + "</td></tr>").join("") + "</tbody></table>";
    $("riskBoundary").textContent = "風險邊界：" +
      "Entry risk 使用目前輸入的期權 Bid/Ask 與到期 payoff 節點計算；不是日內最大虧損保證、歷史回測結果或建議倉位。" +
      "研究模板只允許目前選取的一種專用結構；Risk-WIN Bank 是研究風險權利，不是現金／NAV／券商抵押品。" +
      "此頁不與主 Hybrid 頁自動同步持倉或風險使用量，須把既有風險儲備填入上方，否則不得把多個頁面的最大張數相加。";
  }

  for (const id of ids) {
    const el = $(id);
    if (!el) continue;
    el.addEventListener("input", render);
    el.addEventListener("change", render);
  }
  $("refreshMarketBtn").addEventListener("click", refreshMarket);
  $("loadChainBtn").addEventListener("click", loadChain);
  render();
})();
