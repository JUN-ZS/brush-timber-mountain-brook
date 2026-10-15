(() => {
  "use strict";
  const E = window.HubOptionPackV1;
  const $ = (id) => document.getElementById(id);
  let lastChain = null;
  let lastCandidates = null;

  const ids = [
    "nav","cashPool","cashReservePct","totalOptionRiskPct","baseRiskReservedUsd","strategyRiskPct","spot","targetDte",
    "strategyMode","putRatioDirection","putRatioExpiry","putRatioQuoteConfirmed","putRatioStandardContractConfirmed","atmStrike","atmAsk","shortStrike","shortBid","wingStrike","wingAsk","longPutStrike","longPutAsk",
    "shortPutStrike","shortPutBid","requestedN","maxN","currentN","currentShorts","currentWings","currentShortDelta",
    "lowDeltaStreak","sessionsSinceChange","packagePnlUsd","currentShortAsk","currentWingBid","approachTouched",
    "nextDayReversal","nextDayContinuation","wave","prevClose","anchorClose","atr20","layerCap","currentLayers",
    "drawdown252Pct","return5dPct","putRatioN","applyRiskBank","bankSeedWinUsd","bankLossesUsd","bankMode","bankNetPnlUsd"
  ];
  const n = (id, fallback = null) => E.num($(id) ? $(id).value : null, fallback);
  const checked = (id) => $(id) && $(id).checked === true;
  const set = (id, value) => { if ($(id) && value !== undefined && value !== null && Number.isFinite(Number(value))) $(id).value = value; };
  const usd = (v) => v === null || v === undefined || v === "" || !Number.isFinite(Number(v)) ? "—" : "$" + Number(v).toLocaleString("en-US", { maximumFractionDigits: 2, minimumFractionDigits: 2 });
  const fmt = (v, d = 0) => v === null || v === undefined || v === "" || !Number.isFinite(Number(v)) ? "—" : Number(v).toLocaleString("en-US", { maximumFractionDigits: d, minimumFractionDigits: d });
  const pct = (v) => Number.isFinite(Number(v)) ? (Number(v) * 100).toFixed(1) + "%" : "—";
  const esc = (value) => String(value === null || value === undefined ? "" : value).replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
  const metric = (label, value) => "<div><small>" + esc(label) + "</small><b>" + esc(value) + "</b></div>";

  function commonBudget() {
    const nav = n("nav", 0);
    const cash = n("cashPool", 0);
    const reservePct = Math.max(0, Math.min(100, n("cashReservePct", 10)));
    const poolPct = Math.max(0, n("totalOptionRiskPct", 3.2));
    const baseReserved = n("baseRiskReservedUsd");
    const baseReservationKnown = baseReserved !== null && baseReserved >= 0;
    const strategyPct = Math.max(0, n("strategyRiskPct", 2));
    const cashAfterReserve = Math.max(0, cash * (1 - reservePct / 100));
    const fullPool = Math.max(0, Math.min(nav * poolPct / 100, cashAfterReserve));
    const remainingPool = baseReservationKnown ? Math.max(0, fullPool - baseReserved) : null;
    const strategyBudget = remainingPool === null ? null : Math.max(0, Math.min(nav * strategyPct / 100, remainingPool));
    const bank = E.calculateRiskBank({
      mode: $("bankMode").value === "replenish-comparator" ? "replenish-comparator" : "isolated",
      seedWinUsd: n("bankSeedWinUsd", 0),
      laterLossesUsd: n("bankLossesUsd", 0),
      laterNetPnlUsd: n("bankNetPnlUsd", 0),
      candidateRiskUsd: 0
    });
    const applyBank = checked("applyRiskBank");
    const effectiveBudget = strategyBudget === null ? null : applyBank ? Math.min(strategyBudget, bank.availableRiskRightsUsd) : strategyBudget;
    return { nav, cash, reservePct, cashAfterReserve, fullPool, baseReserved, baseReservationKnown, remainingPool, strategyBudget, effectiveBudget, applyBank, bank };
  }

  function currentInputs() {
    return {
      spot: n("spot"),
      atmStrike: n("atmStrike"), atmAsk: n("atmAsk"),
      shortStrike: n("shortStrike"), shortBid: n("shortBid"),
      wingStrike: n("wingStrike"), wingAsk: n("wingAsk"),
      longPutStrike: n("longPutStrike"), longPutAsk: n("longPutAsk"),
      shortPutStrike: n("shortPutStrike"), shortPutBid: n("shortPutBid"),
      putRatioDirection: $("putRatioDirection") ? $("putRatioDirection").value : "short-heavy",
      putRatioExpiry: $("putRatioExpiry") ? $("putRatioExpiry").value : "",
      putRatioQuoteConfirmed: $("putRatioQuoteConfirmed") ? $("putRatioQuoteConfirmed").checked === true : false,
      putRatioStandardContractConfirmed: $("putRatioStandardContractConfirmed") ? $("putRatioStandardContractConfirmed").checked === true : false
    };
  }

  function selectVisibleFields() {
    const mode = $("strategyMode").value;
    const ratio = mode.startsWith("ratio-");
    const state = mode === "state-adaptive" || mode === "staggered";
    const shock = mode === "shock-put";
    const putRatio = mode === "put-ratio";
    $("ratioControlGroup").hidden = !ratio;
    $("stateControlGroup").hidden = !state;
    $("shockControlGroup").hidden = !shock;
    $("putRatioControlGroup").hidden = !putRatio;
    $("callLegGroup").hidden = shock || putRatio;
    $("putLegGroup").hidden = !(state || shock || putRatio);
    const longHeavy = $("putRatioDirection") && $("putRatioDirection").value === "long-heavy";
    $("putLegHeading").textContent = putRatio
      ? (longHeavy
        ? "N LONG : 1 SHORT · 買 N 張較低 K Long Put；賣 1 張較高 K Short Put"
        : "N SHORT : 1 LONG · 買 1 張較高 K Long Put；賣 N 張較低 K Short Put")
      : "+1 約 25Δ Long Put −1 約 10Δ farther-OTM Short Put";
    if ($("putRatioNLabel")) $("putRatioNLabel").textContent = longHeavy
      ? "N · 每組買入 Long QQQ Put 張數"
      : "N · 每組賣出 Short QQQ Put 張數";
    if ($("putRatioOneLabel")) $("putRatioOneLabel").textContent = longHeavy
      ? "每組賣出 Short QQQ Put 張數"
      : "每組買入 Long QQQ Put 張數";
    if ($("putRatioRecipe")) $("putRatioRecipe").textContent = longHeavy
      ? "N LONG : 1 SHORT（Put backspread）：BUY TO OPEN N 張較低 K Long Put @ Ask；SELL TO OPEN 1 張較高 K Short Put @ Bid。兩腿必須是 QQQ、同一到期日。急跌時的保護效果不是保證；到期損失低谷可出現在較低的 Long Put 行使價附近，淨 Credit/Debit 依實際報價而定。"
      : "N SHORT : 1 LONG（Short Ratio Put Spread）：BUY TO OPEN 1 張較高 K Long Put @ Ask；SELL TO OPEN N 張較低 K Short Put @ Bid。兩腿必須是 QQQ、同一到期日。N>1 時，QQQ 跌穿較低 K 後仍有 N−1 張淨空頭 Put；不是定義風險保護價差。";
    const captions = {
      "ratio-harvest50": "Ratio-Call HARVEST50 V1",
      "ratio-dynamic-v2": "Ratio-Call Risk-Budget Dynamic-N V2",
      "ratio-fresh-v7": "Ratio-Call Fresh-Pair Dynamic-N V7",
      "state-adaptive": "State-Adaptive Geometry",
      "staggered": "Staggered Stack",
      "shock-put": "SHOCK-GATED Put Debit Spread",
      "put-ratio": "QQQ Put Ratio · both orientations"
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

  function applyPutCandidates(candidates) {
    if (!candidates || !candidates.ready) {
      ["longPutStrike", "longPutAsk", "shortPutStrike", "shortPutBid"].forEach(id => { if ($(id)) $(id).value = ""; });
      if ($("putRatioExpiry")) $("putRatioExpiry").value = candidates && candidates.expiry ? candidates.expiry : "";
      return;
    }
    set("longPutStrike", candidates.longPut.strike);
    set("longPutAsk", candidates.longPut.ask);
    set("shortPutStrike", candidates.shortPut.strike);
    set("shortPutBid", candidates.shortPut.bid);
    if ($("putRatioExpiry")) $("putRatioExpiry").value = candidates.expiry || "";
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
      lastCandidates = E.chooseChainLegs(data, spot, new Date().toISOString().slice(0, 10), targetDte,
        $("putRatioDirection") ? $("putRatioDirection").value : "short-heavy");
      applyPutCandidates(lastCandidates);
      if (!lastCandidates.ready) {
        status.textContent = "到期日 " + esc(lastCandidates.expiry || data.expiry || "unknown") + "，但未能可靠配齊全部 Hub 研究腿：" + lastCandidates.error;
        render();
        return;
      }
      const c = lastCandidates;
      set("atmStrike", c.atm.strike); set("atmAsk", c.atm.ask);
      set("shortStrike", c.short.strike); set("shortBid", c.short.bid);
      set("wingStrike", c.wing.strike); set("wingAsk", c.wing.ask);
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

    if (budget.remainingPool === null) {
      const reason = "原 Hybrid 已佔用期權風險未知。從主操作台重新同步有效情境，或人手輸入已核對的預留額；空白不會當成 $0。";
      return {
        budget, mode, result: { ready: false, status: "PENDING", error: reason },
        riskAtTarget: null, debitAtTarget: null, oneUnitRisk: null,
        title: "需要原 Hybrid 風險預留值",
        rows: [["共享期權風險池", "PENDING"], ["原 Hybrid 預留風險", "UNKNOWN · NOT ZERO"], ["下一步", reason]],
        bank: budget.bank, bankCandidateRisk: null,
        bankMeta: "Hub sizing blocked until the existing Hybrid risk reservation is known."
      };
    }

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
    } else if (mode === "put-ratio") {
      title = "QQQ Put Ratio · " + ($("putRatioDirection").value === "long-heavy" ? "N LONG : 1 SHORT" : "N SHORT : 1 LONG");
      result = E.calculatePutRatio({ ...input, budgetUsd: budget.effectiveBudget,
        putRatioN: n("putRatioN", 2), putRatioDirection: $("putRatioDirection").value,
        putRatioExpiry: $("putRatioExpiry").value,
        putRatioQuoteConfirmed: $("putRatioQuoteConfirmed").checked === true,
        putRatioStandardContractConfirmed: $("putRatioStandardContractConfirmed").checked === true });
      if (result.ready) {
        riskAtTarget = result.riskUsd * result.maxPackages;
        debitAtTarget = result.debitUsd * result.maxPackages;
        oneUnitRisk = result.riskUsd;
      }
      const priceWord = result.ready
        ? (result.debitUsd > 0 ? "NET DEBIT · 約支付 " + usd(result.debitUsd)
          : result.debitUsd < 0 ? "NET CREDIT · 約收取 " + usd(Math.abs(result.debitUsd))
          : "NET EVEN · 約 $0")
        : "PENDING";
      const expiry = result.ready ? result.expiry : ($("putRatioExpiry").value || "未確認");
      rows = result.ready ? [
        ["比例方向", result.orientation],
        ["共同到期日", expiry],
        ["每組 Long Put / Short Put 張數", result.longPutQtyPerPackage + " / " + result.shortPutQtyPerPackage],
        ["買入腿（每組）", "BUY TO OPEN " + result.longPutQtyPerPackage + " × QQQ " + expiry + " $" + fmt(input.longPutStrike, 2) + " PUT · 參考 Ask $" + fmt(input.longPutAsk, 2)],
        ["賣出腿（每組）", "SELL TO OPEN " + result.shortPutQtyPerPackage + " × QQQ " + expiry + " $" + fmt(input.shortPutStrike, 2) + " PUT · 參考 Bid $" + fmt(input.shortPutBid, 2)],
        ["每組開倉淨現金流", priceWord + "（正數為支出 Debit；負數為收入 Credit）"],
        ["每組到期最大虧損估算", usd(result.riskUsd)],
        ["到期 QQQ = $0 時的損益情境", usd(result.zeroSpotPnlUsd)],
        ["每組研究風險預算", usd(result.budgetUsd)],
        ["可負擔最大組數（只按到期虧損）", fmt(result.maxPackages)],
        ["最大容量 Long Put 總張數", fmt(result.longPutContracts)],
        ["最大容量 Short Put 總張數", fmt(result.shortPutContracts)],
        ["最大容量風險儲備估算", usd(result.maxPackages * result.riskUsd)],
        ["怎樣輸入券商單", "人工核對兩腿後，在券商選 QQQ 同到期 PUT ratio 多腿 LIMIT 組合單，一次輸入上列 BUY TO OPEN／SELL TO OPEN 數量。使用淨 Debit/Credit 限價；不要先獨立送出裸 Put。此頁不送單。"],
        ["不可忽略", result.reason]
      ] : [["狀態", result.status || "PENDING"], ["原因", result.error || "報價、到期日、合約乘數或風險額度未核實"]];
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

  function importPrimaryContext() {
    const status = $("primaryContextStatus");
    const bridge = window.HubContextBridgeV1;
    if (!bridge || typeof bridge.validate !== "function") {
      status.textContent = "Context bridge unavailable; refresh the local app files.";
      return;
    }
    let raw;
    try { raw = window.localStorage.getItem(bridge.STORAGE_KEY); }
    catch (_) { status.textContent = "This browser blocks local storage; primary context cannot be imported."; return; }
    if (!raw) {
      status.textContent = "找不到主台快照。先返回主台按「Send capital → Hub」，再回來匯入。";
      return;
    }
    const checked = bridge.validate(raw, Date.now());
    if (!checked.ok) {
      status.textContent = "匯入拒絕：" + checked.error;
      return;
    }
    const c = checked.context;
    set("nav", c.capital.nav);
    set("cashPool", c.capital.cashPool);
    set("cashReservePct", c.capital.cashReservePct);
    set("totalOptionRiskPct", c.capital.totalOptionRiskPct);
    if (c.market.qqqSpot !== null && c.market.qqqSpot > 0) set("spot", c.market.qqqSpot);
    else $("spot").value = "";
    if (c.riskReservationReady) {
      set("baseRiskReservedUsd", c.baseRiskReservedUsd);
      status.textContent = "已匯入主台情境 " + c.generatedAt + " · market gate " + c.market.status +
        " · Hybrid 預留 $" + usd(c.baseRiskReservedUsd) + "。這是 current/target 候選風險估算，非已成交倉位認證。";
    } else {
      $("baseRiskReservedUsd").value = "";
      status.textContent = "已匯入 NAV／現金／比例，但主台 gate=" + c.market.status +
        " 或原 Hybrid 風險估算未通過。預留額保持 UNKNOWN（不是 $0）；Hub 計算維持 PENDING，請更新主台資料後重同步，或先核對實際風險再手動輸入。";
    }
    render();
  }

  function render() {
    selectVisibleFields();
    const budget = commonBudget();
    $("capitalMetrics").innerHTML = [
      metric("Cash after reserve", usd(budget.cashAfterReserve)),
      metric("Total shared option-risk pool", usd(budget.fullPool)),
      metric("Pool after existing Hybrid reservations", budget.remainingPool === null ? "PENDING / UNKNOWN RESERVE" : usd(budget.remainingPool)),
      metric("This strategy budget cap", budget.strategyBudget === null ? "PENDING" : usd(budget.strategyBudget)),
      metric("Effective risk budget after Bank", budget.effectiveBudget === null ? "PENDING" : usd(budget.effectiveBudget)),
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
      metric("Net entry cash flow at preview capacity (debit + / credit −)", usd(out.debitAtTarget)),
      metric("Shared risk pool left after target", out.budget.remainingPool === null || out.riskAtTarget === null ? "PENDING / BLOCKED" : usd(Math.max(0, out.budget.remainingPool - out.riskAtTarget))),
      metric("Bank available rights", usd(out.bank.availableRiskRightsUsd)),
      metric("Bank candidate gate", out.budget.applyBank ? (out.bank.eligible ? "PASS" : "BLOCK / CHECK") : "OFF")
    ].join("");

    $("resultTableWrap").innerHTML = "<table class=\"decision-table\"><thead><tr><th>計算項目</th><th>結果</th></tr></thead><tbody>" +
      out.rows.map(row => "<tr><td>" + esc(row[0]) + "</td><td>" + esc(row[1]) + "</td></tr>").join("") + "</tbody></table>";
    $("riskBoundary").textContent = "風險邊界：" +
      "Entry risk 使用目前輸入的期權 Bid/Ask 與到期 payoff 節點計算；不是日內最大虧損保證、歷史回測結果或建議倉位。" +
      "研究模板只允許目前選取的一種專用結構；Risk-WIN Bank 是研究風險權利，不是現金／NAV／券商抵押品。" +
      "可按「Import main desk capital & risk」帶入同一瀏覽器的主台情境；原 Hybrid 預留額是以主台 primary option current/target 數量乘目前候選每組風險的估算，不是已成交倉位證明。若來源 sizing BLOCKED 或持倉風險未知，預留額留空並令計算 PENDING。Hub 數值仍不能與主台最大容量相加。";
  }

  for (const id of ids) {
    const el = $(id);
    if (!el) continue;
    el.addEventListener("input", render);
    el.addEventListener("change", render);
  }
  $("refreshMarketBtn").addEventListener("click", refreshMarket);
  $("loadChainBtn").addEventListener("click", loadChain);
  $("putRatioDirection").addEventListener("change", () => {
    if (lastChain && n("spot") > 0) {
      const targetDte = Math.max(14, Math.min(120, E.whole(n("targetDte", 45), 45)));
      lastCandidates = E.chooseChainLegs(lastChain, n("spot"), new Date().toISOString().slice(0, 10),
        targetDte, $("putRatioDirection").value);
      applyPutCandidates(lastCandidates);
      $("chainStatus").textContent = lastCandidates.ready
        ? "已按新比例方向重新配對 " + lastCandidates.expiry + " 的 Put 腿；報價可能延遲，請對照券商鏈。"
        : "此到期鏈無法配齊新方向的研究腿：" + (lastCandidates.error || "請手動輸入並核對兩腿。");
    }
    render();
  });
  $("importPrimaryContextBtn").addEventListener("click", importPrimaryContext);
  $("baseRiskReservedUsd").addEventListener("change", () => {
    $("primaryContextStatus").textContent = $("baseRiskReservedUsd").value.trim()
      ? "Hybrid 預留風險已手動填入；請核對它與實際持倉／待成交單一致。手動輸入不是系統認證。"
      : "原 Hybrid 預留風險為 UNKNOWN；此欄空白時 Hub 保持 PENDING，不會當成 $0。";
    render();
  });
  const routeParams = new URLSearchParams(window.location.search);
  const requestedResearchMode = routeParams.get("strategyMode");
  if (requestedResearchMode === "put-ratio" || requestedResearchMode === "shock-put") {
    $("strategyMode").value = requestedResearchMode;
  }
  if (routeParams.get("fromPrimary") === "1") importPrimaryContext();
  render();
})();
