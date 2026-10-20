/* GLIDEPATH_TRAJECTORY_PANEL_V1 */
/* GLIDEPATH_REVERSE_REPLAY_V1 */
/* GLIDEPATH_PAIRED_COMPARISON_V1 */
(function () {
  "use strict";

  const summary = document.querySelector("#decisionSummary");
  if (!summary || document.getElementById("decisionTrajectory")) return;

  const years = Array.from({length: 11}, (_, index) => index);
  const directionControl = document.createElement("section");
  directionControl.id = "glidepathDirectionControl";
  directionControl.className = "glidepath-direction-control";
  directionControl.innerHTML =
    '<label for="glidepathDirection">轉換方向</label>' +
    '<select id="glidepathDirection" aria-describedby="glidepathDirectionHelp">' +
      '<option value="stock-to-bond">先股後債（原有回測摘要）</option>' +
      '<option value="bond-to-stock">先債後股（獨立歷史回放）</option>' +
    '</select>' +
    '<p id="glidepathDirectionHelp">方向切換會同步配置路徑。先債後股的績效由獨立價格回放計算，不沿用先股後債的歷史績效。</p>';
  const section = document.createElement("section");
  section.id = "decisionTrajectory";
  section.className = "decision-trajectory";
  section.setAttribute("aria-live", "polite");

  let html = '<div class="trajectory-heading"><div><h2>第 0–10 年股／債配置路徑</h2><p id="decisionTrajectoryLead" class="trajectory-lead">同步所選轉換規則、債券目標和代理標的。</p></div><div class="trajectory-legend"><span>股票 = 100% − 債券比例</span><span>第 10 年對照目標比例</span></div></div>';
  html += '<div class="trajectory-table-scroll"><table class="trajectory-table" aria-label="第 0 至第 10 年逐年股票和債券目標比例"><thead><tr><th scope="col">配置路徑</th>';
  years.forEach(function (year) {
    html += '<th scope="col" data-trajectory-year="' + year + '" aria-current="false">第 ' + year + ' 年</th>';
  });
  html += '</tr></thead><tbody>';
  html += '<tr data-series="stock"><th scope="row">股票目標</th>';
  years.forEach(function (year) { html += '<td data-year="' + year + '">—</td>'; });
  html += '</tr><tr data-series="bond"><th scope="row"><span id="decisionTrajectoryBondLabel">債券目標</span></th>';
  years.forEach(function (year) { html += '<td data-year="' + year + '">—</td>'; });
  html += '</tr><tr data-series="change"><th scope="row">債券較上年變化</th>';
  years.forEach(function (year) { html += '<td data-year="' + year + '">—</td>'; });
  html += '</tr></tbody></table></div>';
  html += '<p id="decisionTrajectoryCrosscheck" class="trajectory-crosscheck">正在對照所選年份的年度回測配置記錄與前置摘要……</p>';
  html += '<p id="decisionTrajectoryStatus" class="trajectory-status" role="status" data-state="pending">正在讀取第 7 圖的年份節點……</p>';
  html += '<p class="trajectory-disclaimer">每年股／債比例直接取自所選債券代理、目標、轉換規則與現金流的年度回測配置記錄（median_target_stock_weight／median_target_bond_weight）。這是每年再平衡目標，不等於歷史每一天實際持倉或已執行交易；上方美元拆分採所選年份的 NAV，不能沿用到其他年份，也不代表目前持倉或今日下單金額。</p>';
  section.innerHTML = html;
  const reversePanel = document.createElement("section");
  reversePanel.id = "reverseReplay";
  reversePanel.className = "reverse-replay";
  reversePanel.hidden = true;
  reversePanel.innerHTML =
    '<div class="reverse-replay-heading"><div><h2>先債後股：獨立 10 年歷史回放</h2>' +
    '<p>只在 TLT + 不提款條件下計算；其他狀態顯示 BLOCK，不借用原模式績效。</p></div>' +
    '<span id="reverseReplayStatus" role="status" data-state="pending">PENDING</span></div>' +
    '<div class="reverse-replay-grid">' +
      '<div><span>第 10 年 NAV 中位數（名目）</span><strong data-reverse-value="medianNav">—</strong></div>' +
      '<div><span>第 10 年 NAV 中位數（實質）</span><strong data-reverse-value="medianRealNav">—</strong></div>' +
      '<div><span>10 年 CAGR 中位數（名目）</span><strong data-reverse-value="medianCagr">—</strong></div>' +
      '<div><span>10 年 CAGR 中位數（實質）</span><strong data-reverse-value="medianRealCagr">—</strong></div>' +
      '<div><span>第 10 年 NAV P05（名目）</span><strong data-reverse-value="p05Nav">—</strong></div>' +
      '<div><span>最差窗口第 10 年 NAV（名目）</span><strong data-reverse-value="worstNav">—</strong></div>' +
      '<div><span>中位數最大回撤（名目）</span><strong data-reverse-value="medianDd">—</strong></div>' +
      '<div><span>最差窗口最大回撤（名目）</span><strong data-reverse-value="worstDd">—</strong></div>' +
      '<div><span>名目期末 NAV ≥ 起始本金</span><strong data-reverse-value="nominalFloor">—</strong></div>' +
      '<div><span>實質期末 NAV ≥ 起始本金</span><strong data-reverse-value="realFloor">—</strong></div>' +
    '</div>' +
    '<p id="reverseReplayMethod" class="reverse-replay-method">等待獨立回放條件……</p>' +
    '<p id="reverseReplayLimits" class="reverse-replay-limits">回測是歷史樣本，不是收益保證。</p>';
  const pairedComparison = document.createElement("section");
  pairedComparison.id = "pairedComparison";
  pairedComparison.className = "paired-comparison";
  pairedComparison.innerHTML =
    '<div class="paired-comparison-heading"><div><h2>同窗配對比較：先股後債 vs 先債後股</h2>' +
    '<p>兩邊使用相同 157 個窗口、同一份 SPY/TLT 價格、同一起點本金、每年再平衡與通脹假設。</p></div>' +
    '<span id="pairedComparisonStatus" role="status" data-state="pending">PENDING</span></div>' +
    '<div class="paired-table-wrap"><table class="paired-table" aria-label="先股後債和先債後股同窗配對比較">' +
    '<thead><tr><th scope="col">指標</th><th scope="col">先股後債</th><th scope="col">先債後股</th><th scope="col">摘要差值<br>（先債後股−先股後債）</th></tr></thead><tbody>' +
    '<tr><th scope="row">期末 NAV 中位數（名目）</th><td data-pair-value="forward.medianNav">—</td><td data-pair-value="reverse.medianNav">—</td><td data-pair-delta="medianNav">—</td></tr>' +
    '<tr><th scope="row">期末 NAV P05（實質）</th><td data-pair-value="forward.p05RealNav">—</td><td data-pair-value="reverse.p05RealNav">—</td><td data-pair-delta="p05RealNav">—</td></tr>' +
    '<tr><th scope="row">期末 NAV 中位數（實質）</th><td data-pair-value="forward.medianRealNav">—</td><td data-pair-value="reverse.medianRealNav">—</td><td data-pair-delta="medianRealNav">—</td></tr>' +
    '<tr><th scope="row">CAGR 中位數（名目）</th><td data-pair-value="forward.medianCagr">—</td><td data-pair-value="reverse.medianCagr">—</td><td data-pair-delta="medianCagr">—</td></tr>' +
    '<tr><th scope="row">CAGR 中位數（實質）</th><td data-pair-value="forward.medianRealCagr">—</td><td data-pair-value="reverse.medianRealCagr">—</td><td data-pair-delta="medianRealCagr">—</td></tr>' +
    '<tr><th scope="row">最大回撤中位數</th><td data-pair-value="forward.medianDd">—</td><td data-pair-value="reverse.medianDd">—</td><td data-pair-delta="medianDd">—</td></tr>' +
    '<tr><th scope="row">最差窗口最大回撤</th><td data-pair-value="forward.worstDd">—</td><td data-pair-value="reverse.worstDd">—</td><td data-pair-delta="worstDd">—</td></tr>' +
    '<tr><th scope="row">最大回撤發生年（中位數）</th><td data-pair-value="forward.ddYearMedian">—</td><td data-pair-value="reverse.ddYearMedian">—</td><td data-pair-delta="ddYearMedian">—</td></tr>' +
    '<tr><th scope="row">期末實質 NAV ≥ 本金</th><td data-pair-value="forward.realFloor">—</td><td data-pair-value="reverse.realFloor">—</td><td data-pair-delta="realFloor">—</td></tr>' +
    '</tbody></table></div>' +
    '<p id="pairedComparisonWinSummary" class="paired-comparison-note">配對勝出窗口：—</p>' +
    '<p id="pairedComparisonMethod" class="paired-comparison-note">等待相同日期窗口的成對回放……</p>' +
    '<p id="pairedComparisonLimits" class="paired-comparison-limits">歷史重疊窗口不是獨立未來機率；無法匹配的價格／現金流不會補值。</p>';
  summary.insertAdjacentElement("afterend", directionControl);
  directionControl.insertAdjacentElement("afterend", section);
  section.insertAdjacentElement("afterend", reversePanel);
  reversePanel.insertAdjacentElement("afterend", pairedComparison);

  const style = document.createElement("style");
  style.id = "decisionTrajectoryStyles";
  style.textContent =
    ".decision-trajectory{margin:12px 0 18px;padding:14px;border:1px solid rgba(127,127,127,.3);border-radius:12px;background:rgba(127,127,127,.035);color:inherit}" +
    ".trajectory-heading{display:flex;justify-content:space-between;align-items:flex-start;gap:14px;flex-wrap:wrap}" +
    ".trajectory-heading h2{font-size:1.05rem;line-height:1.35;margin:0 0 5px;font-weight:700}" +
    ".trajectory-lead,.trajectory-crosscheck,.trajectory-status,.trajectory-disclaimer{font-size:.86rem;line-height:1.5;margin:5px 0;color:inherit}" +
    ".trajectory-legend{display:flex;gap:7px;flex-wrap:wrap;font-size:.77rem;opacity:.82}" +
    ".trajectory-legend span{padding:3px 7px;border:1px solid rgba(127,127,127,.25);border-radius:6px}" +
    ".trajectory-table-scroll{width:100%;overflow-x:auto;margin:10px 0 7px}" +
    ".trajectory-table{width:100%;min-width:720px;border-collapse:separate;border-spacing:2px;font-variant-numeric:tabular-nums;font-size:.82rem}" +
    ".trajectory-table th,.trajectory-table td{padding:6px 5px;text-align:center;white-space:nowrap;border-radius:5px}" +
    ".trajectory-table thead th:first-child,.trajectory-table tbody th{position:sticky;left:0;text-align:left;background:rgba(127,127,127,.1);z-index:1}" +
    ".trajectory-table thead th[data-trajectory-year]{border:1px solid rgba(127,127,127,.22);border-radius:6px;padding:7px 5px;white-space:nowrap}" +
    ".trajectory-table thead th[data-trajectory-year][aria-current=true]{background:rgba(59,130,246,.14);font-weight:800;box-shadow:inset 0 0 0 1px rgba(59,130,246,.4)}" +
    ".trajectory-table .trajectory-selected{background:rgba(59,130,246,.14);font-weight:700;box-shadow:inset 0 0 0 1px rgba(59,130,246,.4)}" +
    ".trajectory-crosscheck{padding:8px 10px;border-left:3px solid rgba(127,127,127,.5);background:rgba(127,127,127,.06);border-radius:4px}" +
    ".trajectory-status[data-state=blocked],.trajectory-status[data-state=pending]{font-weight:600}" +
    ".trajectory-disclaimer{opacity:.75;font-size:.78rem;margin-top:8px}" +
    ".glidepath-direction-control{margin:12px 0;padding:12px 14px;border:1px solid rgba(127,127,127,.35);border-radius:10px;display:grid;grid-template-columns:auto minmax(210px,340px);gap:7px 12px;align-items:center}" +
    ".glidepath-direction-control label{font-weight:700}" +
    ".glidepath-direction-control select{font:inherit;padding:8px 10px;border:1px solid rgba(127,127,127,.4);border-radius:7px;background:Canvas;color:CanvasText;max-width:100%}" +
    ".glidepath-direction-control p{grid-column:1/-1;margin:0;font-size:.8rem;line-height:1.45;opacity:.78}" +
    ".reverse-replay{margin:12px 0 18px;padding:14px;border:1px solid rgba(127,127,127,.35);border-radius:12px;background:rgba(127,127,127,.035);color:inherit}" +
    ".reverse-replay[hidden]{display:none!important}" +
    ".reverse-replay-heading{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;flex-wrap:wrap}" +
    ".reverse-replay h2{font-size:1.05rem;line-height:1.35;margin:0 0 5px;font-weight:700}" +
    ".reverse-replay-heading p,.reverse-replay-method,.reverse-replay-limits{font-size:.82rem;line-height:1.5;margin:5px 0;color:inherit}" +
    "#reverseReplayStatus{font-size:.78rem;font-weight:800;border:1px solid rgba(127,127,127,.45);border-radius:6px;padding:4px 8px;white-space:nowrap}" +
    "#reverseReplayStatus[data-state=blocked]{border-color:#b45309;color:#b45309}" +
    "#reverseReplayStatus[data-state=passed]{border-color:#15803d;color:#15803d}" +
    ".reverse-replay-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:8px;margin:12px 0}" +
    ".reverse-replay-grid>div{padding:10px;border:1px solid rgba(127,127,127,.25);border-radius:8px;display:flex;flex-direction:column;gap:5px;min-width:0}" +
    ".reverse-replay-grid span{font-size:.78rem;opacity:.8;line-height:1.35}" +
    ".reverse-replay-grid strong{font-size:1.12rem;font-variant-numeric:tabular-nums;overflow-wrap:anywhere}" +
    ".reverse-replay-method{padding:9px 10px;background:rgba(127,127,127,.07);border-radius:6px}" +
    ".reverse-replay-limits{font-size:.77rem;opacity:.75}" +
    ".paired-comparison{margin:12px 0 18px;padding:14px;border:1px solid rgba(127,127,127,.35);border-radius:12px;background:rgba(127,127,127,.025);color:inherit}" +
    ".paired-comparison-heading{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;flex-wrap:wrap}" +
    ".paired-comparison h2{font-size:1.05rem;line-height:1.35;margin:0 0 5px;font-weight:700}" +
    ".paired-comparison-heading p,.paired-comparison-note,.paired-comparison-limits{font-size:.82rem;line-height:1.5;margin:5px 0;color:inherit}" +
    "#pairedComparisonStatus{font-size:.78rem;font-weight:800;border:1px solid rgba(127,127,127,.45);border-radius:6px;padding:4px 8px;white-space:nowrap}" +
    "#pairedComparisonStatus[data-state=blocked]{border-color:#b45309;color:#b45309}" +
    "#pairedComparisonStatus[data-state=passed]{border-color:#15803d;color:#15803d}" +
    ".paired-table-wrap{width:100%;overflow-x:auto;margin:10px 0 7px}" +
    ".paired-table{width:100%;min-width:760px;border-collapse:separate;border-spacing:0;font-size:.82rem;font-variant-numeric:tabular-nums}" +
    ".paired-table th,.paired-table td{padding:8px 9px;border-bottom:1px solid rgba(127,127,127,.22);text-align:right;white-space:nowrap}" +
    ".paired-table thead th{font-weight:750;background:rgba(127,127,127,.07);text-align:right}" +
    ".paired-table th:first-child{text-align:left;white-space:normal;min-width:190px}" +
    ".paired-table tbody th{font-weight:600}" +
    ".paired-comparison-note{padding:9px 10px;background:rgba(127,127,127,.06);border-radius:6px}" +
    ".paired-comparison-limits{font-size:.77rem;opacity:.75}" +
    "[data-glp-reverse-hidden=true]{display:none!important}" +
    "@media(max-width:640px){.decision-trajectory{padding:10px}.trajectory-heading{gap:5px}.trajectory-table{min-width:690px}.trajectory-heading h2{font-size:1rem}.glidepath-direction-control{grid-template-columns:1fr}.glidepath-direction-control p{grid-column:1}.reverse-replay{padding:10px}}";
  document.head.appendChild(style);

  let queued = false;
  const reverseDataNode = document.getElementById("glidepath-reverse-data");
  let reverseData = null;
  try {
    reverseData = reverseDataNode ? JSON.parse(reverseDataNode.textContent) : null;
  } catch (_) {
    reverseData = null;
  }
  const targetLabel = document.querySelector('label[for="target"]');
  const targetLabelOriginal = targetLabel ? targetLabel.textContent : "第10年目標轉債比例";
  const reverseHideSelectors = ["#metrics", "#decisionSummary", "#heatmapX", "#glide", "#frontier", "#table", "#cohortX", "#cohortDetailX", "#drawdown", "#flows"];

  function one(selector) { return document.querySelector(selector); }
  function currentDirection() {
    return (one("#glidepathDirection") || {}).value || "stock-to-bond";
  }
  function setModeVisibility(reverse) {
    document.body.classList.toggle("glidepath-reverse-mode", reverse);
    reversePanel.hidden = !reverse;
    reverseHideSelectors.forEach(function (selector) {
      const element = one(selector);
      if (!element) return;
      const panel = element.closest("section,article,figure,.panel,.card") || element;
      if (panel.contains(directionControl) || panel.contains(section) || panel.contains(reversePanel) ||
          panel.contains(one(".controls"))) return;
      if (reverse) panel.setAttribute("data-glp-reverse-hidden", "true");
      else panel.removeAttribute("data-glp-reverse-hidden");
    });
  }
  function updateTargetLabel(reverse) {
    if (targetLabel) targetLabel.textContent = reverse ? "第10年目標轉股比例（先債後股）" : targetLabelOriginal;
  }
  function selectedText(selector) {
    const element = one(selector);
    if (!element) return "";
    if (element.selectedOptions && element.selectedOptions.length) return element.selectedOptions[0].textContent.trim();
    return String(element.value || "").trim();
  }
  function pathForTiming(state) {
    // The forward allocation curve is read from the canonical annual record map.
    // Reverse direction changes the allocation schedule only; performance is replayed separately from SPY/TLT prices.
    if (typeof S !== "function" || typeof Y !== "function") return [];
    const reverse = currentDirection() === "bond-to-stock";
    return years.map(function (year) {
      const record = Y(state.bond, state.target, state.timing, state.flow, year);
      if (!record) return {year: year, bondPct: null, stockPct: null};
      const sourceBondPct = 100 * Number(record.median_target_bond_weight);
      const sourceStockPct = 100 * Number(record.median_target_stock_weight);
      const stockPct = reverse ? sourceBondPct : sourceStockPct;
      const bondPct = reverse ? 100 - sourceBondPct : sourceBondPct;
      return {
        year: year,
        bondPct: Number.isFinite(bondPct) ? bondPct : null,
        stockPct: Number.isFinite(stockPct) ? stockPct : null
      };
    });
  }
  function showUnavailable(message) {
    section.dataset.state = "pending";
    section.dataset.direction = currentDirection();
    section.dataset.target = String((one("#target") || {}).value || "");
    section.dataset.timing = String((one("#timing") || {}).value || "");
    section.dataset.year = String((one("#year") || {}).value || "");
    section.querySelector("#decisionTrajectoryStatus").dataset.state = "pending";
    section.querySelector("#decisionTrajectoryStatus").textContent = "PENDING · " + message + "；未以估算比例補值。";
    ["stock", "bond", "change"].forEach(function (series) {
      section.querySelectorAll('[data-series="' + series + '"] td[data-year]').forEach(function (cell) { cell.textContent = "—"; });
    });
    const reverse = currentDirection() === "bond-to-stock";
    setModeVisibility(reverse);
    updateTargetLabel(reverse);
    renderReverseReplay(reverse, []);
    renderPairedComparison(reverse, []);
  }
  function render() {
    const targetElement = one("#target");
    const timingElement = one("#timing");
    const yearElement = one("#year");
    const reverse = currentDirection() === "bond-to-stock";
    setModeVisibility(reverse);
    updateTargetLabel(reverse);
    if (!targetElement || !timingElement || !yearElement) return showUnavailable("找不到原有年份、目標或轉換規則控制項");
    if (typeof S !== "function" || typeof Y !== "function") return showUnavailable("年度回測記錄介面尚未就緒");
    const currentState = S();
    const timing = timingElement.value;
    const target = Number(targetElement.value);
    const selectedYear = Number(yearElement.value);
    const points = pathForTiming(currentState);
    if (!Number.isFinite(target) || !Number.isInteger(selectedYear)) return showUnavailable("所選控制值不是有效數字");
    if (points.length !== 11 || points.some(function (point, index) {
      return point.year !== index || !Number.isFinite(point.bondPct) || !Number.isFinite(point.stockPct);
    })) {
      return showUnavailable("目前策略沒有完整的第 0 至第 10 年年度回測配置記錄");
    }
    const endpoint = reverse ? points[10].stockPct : points[10].bondPct;
    if (Math.abs(endpoint - target) > 0.75) {
      return showUnavailable("第 10 年路徑終點 " + endpoint.toFixed(2) + "% 與目標 " + target.toFixed(2) + "% 不一致");
    }

    const bondName = selectedText("#bond") || "債券代理";
    const timingName = selectedText("#timing") || timing;
    section.querySelector(".trajectory-heading h2").textContent = reverse ? "第 0–10 年債轉股配置路徑" : "第 0–10 年股／債配置路徑";
    section.querySelector("#decisionTrajectoryBondLabel").textContent = bondName + " 目標";
    section.querySelector("#decisionTrajectoryLead").textContent = reverse
      ? "方向：先債後股 · 規則：" + timingName + " · 第 10 年目標股票 " + target.toFixed(2) + "% · 所選年份：" + selectedYear + "。比例列出反向配置目標；績效只採下方獨立 SPY/TLT 歷史回放。"
      : "規則：" + timingName + " · 第 10 年目標 " + bondName + " " + target.toFixed(2) + "% · 所選年份：" + selectedYear + "。比例取自同一策略的年度回測配置記錄；拖動原有年份 BAR 即可切換高亮年份。";

    points.forEach(function (point, index) {
      const stockPct = point.stockPct;
      const stockCell = section.querySelector('[data-series="stock"] [data-year="' + point.year + '"]');
      const bondCell = section.querySelector('[data-series="bond"] [data-year="' + point.year + '"]');
      const changeCell = section.querySelector('[data-series="change"] [data-year="' + point.year + '"]');
      stockCell.textContent = stockPct.toFixed(2) + "%";
      bondCell.textContent = point.bondPct.toFixed(2) + "%";
      stockCell.dataset.stockPct = stockPct.toFixed(4);
      bondCell.dataset.bondPct = point.bondPct.toFixed(4);
      if (index === 0) {
        changeCell.textContent = "起點";
      } else {
        const change = point.bondPct - points[index - 1].bondPct;
        changeCell.textContent = (change > 0 ? "+" : "") + change.toFixed(2) + " pp";
      }
      [stockCell, bondCell, changeCell].forEach(function (cell) {
        cell.classList.toggle("trajectory-selected", point.year === selectedYear);
        cell.setAttribute("aria-label", "第 " + point.year + " 年：" + cell.textContent);
      });
      const yearHeader = section.querySelector('[data-trajectory-year="' + point.year + '"]');
      yearHeader.setAttribute("aria-current", point.year === selectedYear ? "true" : "false");
      yearHeader.classList.toggle("trajectory-selected", point.year === selectedYear);
    });

    const summaryAllocation = (one("#decisionAllocationHeadline") || {}).textContent || "";
    const rates = Array.from(summaryAllocation.matchAll(/(\d+(?:\.\d+)?)%/g)).map(function (match) { return Number(match[1]); });
    const selectedPoint = points.find(function (point) { return point.year === selectedYear; });
    const crosscheck = section.querySelector("#decisionTrajectoryCrosscheck");
    if (reverse) {
      crosscheck.textContent = "反向配置：第 0 年債券 100%／股票 0%，依相同時間曲線把股票比例逐年增加到第 10 年目標；這是新的配置路徑，不是把舊回測績效倒轉。";
      section.dataset.crosscheck = "reverse-direction-independent";
      section.dataset.allocationDeltaPp = "";
    } else if (rates.length >= 2 && selectedPoint) {
      const stockDelta = selectedPoint.stockPct - rates[0];
      const bondDelta = selectedPoint.bondPct - rates[1];
      crosscheck.textContent = "第 " + selectedYear + " 年對照：年度回測配置記錄為股票 " +
        stockPctAt(selectedPoint) + "% / " + bondName + " " +
        selectedPoint.bondPct.toFixed(2) + "%；前置摘要為股票 " + rates[0].toFixed(2) +
        "% / " + bondName + " " + rates[1].toFixed(2) + "%；畫面差異：股票 " +
        (stockDelta > 0 ? "+" : "") + stockDelta.toFixed(2) + ppLabel() + "、債券 " +
        (bondDelta > 0 ? "+" : "") + bondDelta.toFixed(2) + ppLabel() +
        "。這是同一年度記錄的畫面一致性核對，不是獨立回測驗證；金額依主摘要該年 NAV 拆分。";
      section.dataset.summaryBondPct = rates[1].toFixed(4);
      section.dataset.allocationDeltaPp = bondDelta.toFixed(4);
      section.dataset.crosscheck = Math.abs(bondDelta) <= 0.75 ? "aligned" : "different";
    } else {
      crosscheck.textContent = "所選年份的路徑比例已列出；目前無法從主摘要讀取兩個配置比例，因此不顯示差異值。";
      section.dataset.crosscheck = "unavailable";
    }

    section.dataset.state = "ready";
    section.dataset.direction = reverse ? "bond-to-stock" : "stock-to-bond";
    section.dataset.target = String(target);
    section.dataset.timing = timing;
    section.dataset.year = String(selectedYear);
    section.dataset.endpointBondPct = points[10].bondPct.toFixed(4);
    section.dataset.endpointStockPct = points[10].stockPct.toFixed(4);
    section.querySelector("#decisionTrajectoryStatus").dataset.state = "ready";
    section.querySelector("#decisionTrajectoryStatus").textContent = reverse
      ? "已顯示 11 個反向配置目標；第 10 年股票配置 " + endpoint.toFixed(2) + "%，目標 " + target.toFixed(2) + "%。績效由獨立歷史價格回放計算。"
      : "已同步 11 個年度回測配置記錄；第 10 年債券配置 " + endpoint.toFixed(2) +
        "%，目標 " + target.toFixed(2) + "%。年度差值是相鄰年度配置百分點，不代表當年交易金額或每日實際持倉。";
    renderReverseReplay(reverse, points);
    renderPairedComparison(reverse, points);
  }
  function stockPctAt(point) { return point.stockPct.toFixed(2); }
  function ppLabel() { return " 個百分點"; }
  function usd(value) {
    return Number.isFinite(value) ? new Intl.NumberFormat("en-US", {style: "currency", currency: "USD", maximumFractionDigits: 0}).format(value) : "—";
  }
  function pct(value) {
    return Number.isFinite(value) ? (value * 100).toFixed(2) + "%" : "—";
  }
  function quantile(values, q) {
    if (!values.length) return NaN;
    const sorted = values.slice().sort(function (a, b) { return a - b; });
    const p = (sorted.length - 1) * q;
    const lo = Math.floor(p), hi = Math.ceil(p);
    return sorted[lo] + (sorted[hi] - sorted[lo]) * (p - lo);
  }
  function setReplayValue(key, value) {
    const element = reversePanel.querySelector('[data-reverse-value="' + key + '"]');
    if (element) element.textContent = value;
  }
  function clearReplayValues() {
    reversePanel.querySelectorAll("[data-reverse-value]").forEach(function (element) { element.textContent = "—"; });
    ["windowCount", "sourceAsOf", "sourceSha256", "firstStart", "firstEnd", "lastStart", "lastEnd",
      "medianTerminalNav", "medianRealTerminalNav", "medianNominalCagr", "medianRealCagr",
      "medianNominalDrawdown", "worstNominalDrawdown", "nominalNoLossCount", "realNoLossCount"].forEach(function (key) {
      delete reversePanel.dataset[key];
    });
  }
  function blockReplay(message, status) {
    clearReplayValues();
    reversePanel.dataset.state = status || "blocked";
    reversePanel.querySelector("#reverseReplayStatus").dataset.state = status || "blocked";
    reversePanel.querySelector("#reverseReplayStatus").textContent = status === "pending" ? "PENDING" : "BLOCK";
    reversePanel.querySelector("#reverseReplayMethod").textContent = (status === "pending" ? "PENDING · " : "BLOCK · ") + message + "；未以估算或原模式績效補值。";
  }
  function renderReverseReplay(reverse, points) {
    reversePanel.hidden = !reverse;
    if (!reverse) return;
    clearReplayValues();
    const bondValue = (one("#bond") || {}).value || "";
    const flowName = selectedText("#flow");
    const flowValue = (one("#flow") || {}).value || "";
    const noWithdrawal = /不提款/.test(flowName) || /^(none|no_withdrawal|no-withdrawal|no_cashflow)$/.test(flowValue);
    if (!reverseData || reverseData.marker !== "GLIDEPATH_REVERSE_DATA_V1") {
      return blockReplay("反向回放價格包缺失或版本不符", "pending");
    }
    if (bondValue !== "TLT") {
      return blockReplay("目前獨立歷史價格包只覆蓋 TLT；請選擇 TLT 後才可計算先債後股績效");
    }
    if (!noWithdrawal) {
      return blockReplay("此回放只驗證不提款模式；目前現金流設定為「" + flowName + "」。提款／供款版本尚未重播");
    }
    if (!Array.isArray(points) || points.length !== 11 ||
        points.slice(0, 10).some(function (point) { return !Number.isFinite(point.stockPct) || !Number.isFinite(point.bondPct); })) {
      return blockReplay("缺少完整的 0–9 年反向年度配置，無法重播");
    }
    const dates = reverseData.dates || [];
    const spy = reverseData.prices && reverseData.prices.SPY;
    const tlt = reverseData.prices && reverseData.prices.TLT;
    const protocol = reverseData.windowProtocol || {};
    const windows = Number(protocol.nWindows);
    const startIndex = Number(protocol.startIndex);
    const stride = Number(protocol.stride);
    const horizon = Number(protocol.horizonTradingDays);
    const tradingDaysPerYear = Number(protocol.tradingDaysPerYear);
    if (!Array.isArray(spy) || !Array.isArray(tlt) || spy.length !== dates.length || tlt.length !== dates.length ||
        dates.length < 1 || !Number.isInteger(windows) || windows < 1 || !Number.isInteger(horizon) ||
        !Number.isInteger(startIndex) || !Number.isInteger(stride) || !Number.isInteger(tradingDaysPerYear)) {
      return blockReplay("價格序列或窗口契約不完整，無法計算");
    }
    const stockWeights = points.slice(0, 10).map(function (point) { return point.stockPct / 100; });
    if (stockWeights.some(function (weight) { return !Number.isFinite(weight) || weight < 0 || weight > 1; })) {
      return blockReplay("年度股票權重超出 0–100%，拒絕計算");
    }
    const starts = Array.from({length: windows}, function (_, index) { return startIndex + index * stride; });
    if (starts.some(function (start) { return start < 0 || start + horizon >= dates.length; })) {
      return blockReplay("窗口起點超出可用價格範圍；不縮短窗口也不補零");
    }
    for (let i = 0; i < dates.length; i++) {
      if (!(Number.isFinite(spy[i]) && spy[i] > 0 && Number.isFinite(tlt[i]) && tlt[i] > 0)) {
        return blockReplay("價格序列第 " + i + " 行存在缺值／非正價格；不以零收益填補");
      }
    }
    const initialNav = 100000;
    const cpiElement = one("#realMode");
    const inflation = Math.max(0, Number(cpiElement ? cpiElement.value : 0) || 0);
    const results = [];
    for (const start of starts) {
      const firstSpy = spy[start], firstTlt = tlt[start];
      let spyShares = initialNav * stockWeights[0] / firstSpy;
      let tltShares = initialNav * (1 - stockWeights[0]) / firstTlt;
      let peakNominal = initialNav, peakReal = initialNav;
      let maxDdNominal = 0, maxDdReal = 0, terminalNav = initialNav, terminalRealNav = initialNav;
      for (let day = 1; day <= horizon; day++) {
        const idx = start + day;
        terminalNav = spyShares * spy[idx] + tltShares * tlt[idx];
        const realNav = terminalNav / Math.pow(1 + inflation, day / tradingDaysPerYear);
        if (!Number.isFinite(terminalNav) || terminalNav <= 0 || !Number.isFinite(realNav) || realNav <= 0) {
          return blockReplay("窗口 " + dates[start] + " 出現無效 NAV；不略過失敗窗口");
        }
        peakNominal = Math.max(peakNominal, terminalNav);
        peakReal = Math.max(peakReal, realNav);
        maxDdNominal = Math.min(maxDdNominal, terminalNav / peakNominal - 1);
        maxDdReal = Math.min(maxDdReal, realNav / peakReal - 1);
        if (day < horizon && day % tradingDaysPerYear === 0) {
          const targetYear = Math.min(9, day / tradingDaysPerYear);
          spyShares = terminalNav * stockWeights[targetYear] / spy[idx];
          tltShares = terminalNav * (1 - stockWeights[targetYear]) / tlt[idx];
        }
        if (day === horizon) terminalRealNav = realNav;
      }
      results.push({
        start: dates[start],
        end: dates[start + horizon],
        terminalNav: terminalNav,
        realTerminalNav: terminalRealNav,
        nominalCagr: Math.pow(terminalNav / initialNav, 1 / 10) - 1,
        realCagr: Math.pow(terminalRealNav / initialNav, 1 / 10) - 1,
        maxDdNominal: maxDdNominal,
        maxDdReal: maxDdReal
      });
    }
    if (results.length !== 157) return blockReplay("完整窗口數應為 157，實際只有 " + results.length);
    const navs = results.map(function (item) { return item.terminalNav; });
    const realNavs = results.map(function (item) { return item.realTerminalNav; });
    const cagr = results.map(function (item) { return item.nominalCagr; });
    const realCagr = results.map(function (item) { return item.realCagr; });
    const drawdowns = results.map(function (item) { return item.maxDdNominal; });
    const nominalNoLoss = results.filter(function (item) { return item.terminalNav >= initialNav; }).length;
    const realNoLoss = results.filter(function (item) { return item.realTerminalNav >= initialNav; }).length;
    const summary = {
      windowCount: results.length,
      firstStart: results[0].start,
      firstEnd: results[0].end,
      lastStart: results[results.length - 1].start,
      lastEnd: results[results.length - 1].end,
      medianTerminalNav: quantile(navs, 0.5),
      p05TerminalNav: quantile(navs, 0.05),
      worstTerminalNav: Math.min.apply(null, navs),
      medianRealTerminalNav: quantile(realNavs, 0.5),
      p05RealTerminalNav: quantile(realNavs, 0.05),
      medianNominalCagr: quantile(cagr, 0.5),
      medianRealCagr: quantile(realCagr, 0.5),
      medianNominalDrawdown: quantile(drawdowns, 0.5),
      worstNominalDrawdown: Math.min.apply(null, drawdowns),
      nominalNoLossCount: nominalNoLoss,
      realNoLossCount: realNoLoss,
      nominalNoLossRate: nominalNoLoss / results.length,
      realNoLossRate: realNoLoss / results.length,
      annualInflationAssumption: inflation
    };
    setReplayValue("medianNav", usd(summary.medianTerminalNav));
    setReplayValue("medianRealNav", usd(summary.medianRealTerminalNav));
    setReplayValue("medianCagr", pct(summary.medianNominalCagr));
    setReplayValue("medianRealCagr", pct(summary.medianRealCagr));
    setReplayValue("p05Nav", usd(summary.p05TerminalNav));
    setReplayValue("worstNav", usd(summary.worstTerminalNav));
    setReplayValue("medianDd", pct(summary.medianNominalDrawdown));
    setReplayValue("worstDd", pct(summary.worstNominalDrawdown));
    setReplayValue("nominalFloor", nominalNoLoss + "/157 (" + pct(summary.nominalNoLossRate) + ")");
    setReplayValue("realFloor", realNoLoss + "/157 (" + pct(summary.realNoLossRate) + ")");
    reversePanel.dataset.state = "passed";
    reversePanel.dataset.windowCount = String(summary.windowCount);
    reversePanel.dataset.sourceAsOf = String(reverseData.sourceAsOf || "");
    reversePanel.dataset.sourceSha256 = String(reverseData.sourceFileSha256 || "");
    reversePanel.dataset.firstStart = summary.firstStart;
    reversePanel.dataset.firstEnd = summary.firstEnd;
    reversePanel.dataset.lastStart = summary.lastStart;
    reversePanel.dataset.lastEnd = summary.lastEnd;
    reversePanel.dataset.medianTerminalNav = summary.medianTerminalNav.toFixed(4);
    reversePanel.dataset.medianRealTerminalNav = summary.medianRealTerminalNav.toFixed(4);
    reversePanel.dataset.medianNominalCagr = summary.medianNominalCagr.toFixed(8);
    reversePanel.dataset.medianRealCagr = summary.medianRealCagr.toFixed(8);
    reversePanel.dataset.medianNominalDrawdown = summary.medianNominalDrawdown.toFixed(8);
    reversePanel.dataset.worstNominalDrawdown = summary.worstNominalDrawdown.toFixed(8);
    reversePanel.dataset.nominalNoLossCount = String(summary.nominalNoLossCount);
    reversePanel.dataset.realNoLossCount = String(summary.realNoLossCount);
    const badge = reversePanel.querySelector("#reverseReplayStatus");
    badge.dataset.state = "passed";
    badge.textContent = "REPLAY PASSED · " + summary.windowCount + " 窗口";
    reversePanel.querySelector("#reverseReplayMethod").textContent =
      "方法：SPY（股票）＋ TLT（長天期美國公債 ETF）調整收盤價；" + summary.windowCount +
      " 個重疊 10 年窗口，起點從第 " + startIndex + " 個有效交易列開始、每 " + stride +
      " 列一個窗口；每年 " + tradingDaysPerYear + " 個交易日並按年再平衡；起始 NAV $100,000；不提款／不供款；未扣交易成本、稅費或滑點。";
    reversePanel.querySelector("#reverseReplayLimits").textContent =
      "來源：" + (reverseData.datasetSource || "src/data/universe.json") + "（" + (reverseData.sourceAsOf || "日期未知") +
      " 截止，" + dates.length + " 個有效同步價格列；來源檔 SHA-256 " + String(reverseData.sourceFileSha256 || "").slice(0, 16) +
      "…）。實質 NAV 使用年通脹假設 " + (inflation * 100).toFixed(2) +
      "%。TLT 只代表長天期美國公債，不可視為 AGG／SHY／IEF；歷史樣本不保證未來結果。";
  }
  function summarizeReplay(rows, initialNav) {
    const nav = rows.map(function (row) { return row.terminalNav; });
    const realNav = rows.map(function (row) { return row.realTerminalNav; });
    const cagr = rows.map(function (row) { return row.nominalCagr; });
    const realCagr = rows.map(function (row) { return row.realCagr; });
    const dd = rows.map(function (row) { return row.maxDdNominal; });
    const ddYears = rows.map(function (row) { return row.maxDdYear; });
    const realFloor = rows.filter(function (row) { return row.realTerminalNav >= initialNav; }).length;
    return {
      n: rows.length, medianNav: median(nav), p05Nav: quantile(nav, 0.05),
      medianRealNav: median(realNav), p05RealNav: quantile(realNav, 0.05),
      medianCagr: median(cagr), medianRealCagr: median(realCagr),
      medianDd: median(dd), worstDd: Math.min.apply(null, dd),
      ddYearMedian: median(ddYears), realFloorCount: realFloor,
      realFloorRate: realFloor / rows.length,
      minNav: Math.min.apply(null, nav), minRealNav: Math.min.apply(null, realNav),
      ddYearCounts: Object.fromEntries(Array.from({length: 10}, function (_, index) {
        const year = index + 1;
        return [String(year), rows.filter(function (row) { return row.maxDdYear === year; }).length];
      }))
    };
  }
  function median(values) { return quantile(values, 0.5); }
  function replaySchedule(stockWeights, dates, spy, tlt, starts, horizon, tradingDaysPerYear, inflation, initialNav) {
    const rows = [];
    for (const start of starts) {
      let spyShares = initialNav * stockWeights[0] / spy[start];
      let tltShares = initialNav * (1 - stockWeights[0]) / tlt[start];
      let peak = initialNav, maxDd = 0, maxDdDay = 0, maxDdYear = 1, terminalNav = initialNav;
      for (let day = 1; day <= horizon; day++) {
        const idx = start + day;
        terminalNav = spyShares * spy[idx] + tltShares * tlt[idx];
        if (!Number.isFinite(terminalNav) || terminalNav <= 0) return null;
        peak = Math.max(peak, terminalNav);
        const drawdown = terminalNav / peak - 1;
        if (drawdown < maxDd) {
          maxDd = drawdown;
          maxDdDay = day;
          maxDdYear = Math.min(10, Math.ceil(day / tradingDaysPerYear));
        }
        if (day < horizon && day % tradingDaysPerYear === 0) {
          const targetYear = Math.min(stockWeights.length - 1, day / tradingDaysPerYear);
          spyShares = terminalNav * stockWeights[targetYear] / spy[idx];
          tltShares = terminalNav * (1 - stockWeights[targetYear]) / tlt[idx];
        }
      }
      const realTerminalNav = terminalNav / Math.pow(1 + inflation, horizon / tradingDaysPerYear);
      rows.push({
        start: dates[start], end: dates[start + horizon], terminalNav, realTerminalNav,
        nominalCagr: Math.pow(terminalNav / initialNav, 0.1) - 1,
        realCagr: Math.pow(realTerminalNav / initialNav, 0.1) - 1,
        maxDdNominal: maxDd, maxDdYear, maxDdDay
      });
    }
    return rows;
  }
  function renderPairedComparison(reverse, points) {
    pairedComparison.querySelectorAll("[data-pair-value],[data-pair-delta]").forEach(function (node) { node.textContent = "—"; });
    pairedComparison.dataset.state = "pending";
    const badge = pairedComparison.querySelector("#pairedComparisonStatus");
    const bondValue = (one("#bond") || {}).value || "";
    const flowName = selectedText("#flow");
    const flowValue = (one("#flow") || {}).value || "";
    const noWithdrawal = /不提款/.test(flowName) || /^(none|no_withdrawal|no-withdrawal|no_cashflow)$/.test(flowValue);
    function block(message) {
      pairedComparison.dataset.state = "blocked";
      badge.dataset.state = "blocked";
      badge.textContent = "BLOCK";
      pairedComparison.querySelector("#pairedComparisonMethod").textContent = "BLOCK · " + message + "；未用不同樣本或舊摘要填補。";
    }
    if (!reverseData || reverseData.marker !== "GLIDEPATH_REVERSE_DATA_V1") return block("缺少獨立 SPY/TLT 回放價格包");
    if (bondValue !== "TLT") return block("同窗配對回放目前只覆蓋 TLT；請把債券代理選為 TLT");
    if (!noWithdrawal) return block("同窗配對目前只覆蓋不提款／不供款；目前現金流為「" + flowName + "」");
    if (!Array.isArray(points) || points.length !== 11 ||
        points.slice(0, 10).some(function (point) { return !Number.isFinite(point.stockPct) || point.stockPct < 0 || point.stockPct > 100; })) {
      return block("年度配置路徑不完整或超出 0–100%");
    }
    const dates = reverseData.dates || [];
    const spy = reverseData.prices && reverseData.prices.SPY;
    const tlt = reverseData.prices && reverseData.prices.TLT;
    const protocol = reverseData.windowProtocol || {};
    const windows = Number(protocol.nWindows), startIndex = Number(protocol.startIndex);
    const stride = Number(protocol.stride), horizon = Number(protocol.horizonTradingDays);
    const tradingDaysPerYear = Number(protocol.tradingDaysPerYear);
    if (!Array.isArray(spy) || !Array.isArray(tlt) || spy.length !== dates.length || tlt.length !== dates.length ||
        !Number.isInteger(windows) || !Number.isInteger(startIndex) || !Number.isInteger(stride) ||
        !Number.isInteger(horizon) || !Number.isInteger(tradingDaysPerYear)) return block("價格序列與窗口契約不完整");
    const starts = Array.from({length: windows}, function (_, index) { return startIndex + index * stride; });
    if (starts.some(function (start) { return start < 0 || start + horizon >= dates.length; })) return block("窗口超出可用價格範圍；不縮短窗口、不補零");
    for (let i = 0; i < dates.length; i++) {
      if (!(Number.isFinite(spy[i]) && spy[i] > 0 && Number.isFinite(tlt[i]) && tlt[i] > 0)) return block("價格列 " + i + " 存在缺值／非正值");
    }
    const currentStock = points.slice(0, 10).map(function (point) { return point.stockPct / 100; });
    // Compare both mirrored annual target paths on the same starts, irrespective of selected UI direction.
    const reverseStocks = reverse ? currentStock : currentStock.map(function (weight) { return 1 - weight; });
    const forwardStocks = reverseStocks.map(function (weight) { return 1 - weight; });
    const inflation = Math.max(0, Number((one("#realMode") || {}).value || 0));
    const initialNav = 100000;
    const forwardRows = replaySchedule(forwardStocks, dates, spy, tlt, starts, horizon, tradingDaysPerYear, inflation, initialNav);
    const reverseRows = replaySchedule(reverseStocks, dates, spy, tlt, starts, horizon, tradingDaysPerYear, inflation, initialNav);
    if (!forwardRows || !reverseRows || forwardRows.length !== windows || reverseRows.length !== windows) return block("其中一個方向產生無效 NAV；不刪除失敗窗口");
    if (!forwardRows.every(function (row, index) { return row.start === reverseRows[index].start && row.end === reverseRows[index].end; })) return block("兩個方向的窗口起訖日期不一致");
    const forward = summarizeReplay(forwardRows, initialNav);
    const reversed = summarizeReplay(reverseRows, initialNav);
    const pairedDiff = reverseRows.map(function (row, index) {
      return {
        start: row.start, end: row.end,
        realNav: row.realTerminalNav - forwardRows[index].realTerminalNav,
        nominalCagr: row.nominalCagr - forwardRows[index].nominalCagr,
        maxDd: row.maxDdNominal - forwardRows[index].maxDdNominal
      };
    });
    const paired = {
      n: pairedDiff.length,
      medianRealNavDelta: median(pairedDiff.map(function (row) { return row.realNav; })),
      medianNominalCagrDelta: median(pairedDiff.map(function (row) { return row.nominalCagr; })),
      medianMaxDdDelta: median(pairedDiff.map(function (row) { return row.maxDd; })),
      reverseRealNavWins: pairedDiff.filter(function (row) { return row.realNav > 0; }).length,
      forwardRealNavWins: pairedDiff.filter(function (row) { return row.realNav < 0; }).length,
      tiesRealNav: pairedDiff.filter(function (row) { return row.realNav === 0; }).length,
      reverseLowerDrawdown: pairedDiff.filter(function (row) { return row.maxDd > 0; }).length,
      forwardLowerDrawdown: pairedDiff.filter(function (row) { return row.maxDd < 0; }).length,
      tiesDrawdown: pairedDiff.filter(function (row) { return row.maxDd === 0; }).length
    };
    const money = function (value) { return usd(value); };
    const per = function (value) { return pct(value); };
    const renderValues = {
      "forward.medianNav": money(forward.medianNav), "reverse.medianNav": money(reversed.medianNav),
      "forward.p05RealNav": money(forward.p05RealNav), "reverse.p05RealNav": money(reversed.p05RealNav),
      "forward.medianRealNav": money(forward.medianRealNav), "reverse.medianRealNav": money(reversed.medianRealNav),
      "forward.medianCagr": per(forward.medianCagr), "reverse.medianCagr": per(reversed.medianCagr),
      "forward.medianRealCagr": per(forward.medianRealCagr), "reverse.medianRealCagr": per(reversed.medianRealCagr),
      "forward.medianDd": per(forward.medianDd), "reverse.medianDd": per(reversed.medianDd),
      "forward.worstDd": per(forward.worstDd), "reverse.worstDd": per(reversed.worstDd),
      "forward.ddYearMedian": "第 " + forward.ddYearMedian.toFixed(1) + " 年",
      "reverse.ddYearMedian": "第 " + reversed.ddYearMedian.toFixed(1) + " 年",
      "forward.realFloor": forward.realFloorCount + "/" + forward.n + " (" + per(forward.realFloorRate) + ")",
      "reverse.realFloor": reversed.realFloorCount + "/" + reversed.n + " (" + per(reversed.realFloorRate) + ")"
    };
    Object.entries(renderValues).forEach(function (entry) {
      const node = pairedComparison.querySelector('[data-pair-value="' + entry[0] + '"]');
      if (node) node.textContent = entry[1];
    });
    const deltas = {
      medianNav: reversed.medianNav - forward.medianNav,
      p05RealNav: reversed.p05RealNav - forward.p05RealNav,
      medianRealNav: reversed.medianRealNav - forward.medianRealNav,
      medianCagr: reversed.medianCagr - forward.medianCagr,
      medianRealCagr: reversed.medianRealCagr - forward.medianRealCagr,
      medianDd: reversed.medianDd - forward.medianDd,
      worstDd: reversed.worstDd - forward.worstDd,
      ddYearMedian: reversed.ddYearMedian - forward.ddYearMedian,
      realFloor: reversed.realFloorCount - forward.realFloorCount
    };
    Object.entries(deltas).forEach(function (entry) {
      const node = pairedComparison.querySelector('[data-pair-delta="' + entry[0] + '"]');
      if (!node) return;
      if (entry[0] === "medianNav" || entry[0] === "p05RealNav" || entry[0] === "medianRealNav") node.textContent = (entry[1] > 0 ? "+" : "") + money(entry[1]);
      else if (entry[0] === "realFloor") node.textContent = (entry[1] > 0 ? "+" : "") + entry[1] + " 窗口";
      else if (entry[0] === "ddYearMedian") node.textContent = (entry[1] > 0 ? "+" : "") + entry[1].toFixed(1) + " 年";
      else node.textContent = (entry[1] > 0 ? "+" : "") + per(entry[1]);
    });
    pairedComparison.dataset.state = "passed";
    pairedComparison.dataset.windowCount = String(windows);
    pairedComparison.dataset.sourceAsOf = String(reverseData.sourceAsOf || "");
    pairedComparison.dataset.sourceSha256 = String(reverseData.sourceFileSha256 || "");
    pairedComparison.dataset.inflation = String(inflation);
    pairedComparison.dataset.target = String((one("#target") || {}).value || "");
    pairedComparison.dataset.timing = String((one("#timing") || {}).value || "");
    pairedComparison.dataset.firstStart = forwardRows[0].start;
    pairedComparison.dataset.firstEnd = forwardRows[0].end;
    pairedComparison.dataset.lastStart = forwardRows[windows - 1].start;
    pairedComparison.dataset.lastEnd = forwardRows[windows - 1].end;
    pairedComparison.dataset.matchedPairCount = String(paired.n);
    pairedComparison.dataset.forwardMedianNav = forward.medianNav.toFixed(4);
    pairedComparison.dataset.reverseMedianNav = reversed.medianNav.toFixed(4);
    pairedComparison.dataset.forwardMedianRealNav = forward.medianRealNav.toFixed(4);
    pairedComparison.dataset.reverseMedianRealNav = reversed.medianRealNav.toFixed(4);
    pairedComparison.dataset.medianRealNavDelta = deltas.medianRealNav.toFixed(4);
    pairedComparison.dataset.pairedMedianRealNavDelta = paired.medianRealNavDelta.toFixed(4);
    pairedComparison.dataset.forwardMedianCagr = forward.medianCagr.toFixed(8);
    pairedComparison.dataset.reverseMedianCagr = reversed.medianCagr.toFixed(8);
    pairedComparison.dataset.medianCagrDelta = deltas.medianCagr.toFixed(8);
    pairedComparison.dataset.pairedMedianCagrDelta = paired.medianNominalCagrDelta.toFixed(8);
    pairedComparison.dataset.forwardMedianDd = forward.medianDd.toFixed(8);
    pairedComparison.dataset.reverseMedianDd = reversed.medianDd.toFixed(8);
    pairedComparison.dataset.medianDdDelta = deltas.medianDd.toFixed(8);
    pairedComparison.dataset.pairedMedianDdDelta = paired.medianMaxDdDelta.toFixed(8);
    pairedComparison.dataset.forwardDdYearCounts = JSON.stringify(forward.ddYearCounts);
    pairedComparison.dataset.reverseDdYearCounts = JSON.stringify(reversed.ddYearCounts);
    pairedComparison.dataset.reverseRealNavWins = String(paired.reverseRealNavWins);
    pairedComparison.dataset.forwardRealNavWins = String(paired.forwardRealNavWins);
    pairedComparison.dataset.reverseLowerDrawdown = String(paired.reverseLowerDrawdown);
    pairedComparison.dataset.forwardLowerDrawdown = String(paired.forwardLowerDrawdown);
    badge.dataset.state = "passed";
    badge.textContent = "PAIRED PASS · " + windows + " 對";
    pairedComparison.querySelector("#pairedComparisonWinSummary").textContent =
      "同一窗口比較（先債後股勝出／先股後債勝出／平手）：實質期末 NAV " +
      paired.reverseRealNavWins + " / " + paired.forwardRealNavWins + " / " + paired.tiesRealNav +
      " 對；最大回撤較低（較不負） " + paired.reverseLowerDrawdown + " / " + paired.forwardLowerDrawdown +
      " / " + paired.tiesDrawdown + " 對。勝出數依逐窗差計算，不代表獨立未來機率。";
    pairedComparison.querySelector("#pairedComparisonMethod").textContent =
      "方法：兩邊各 " + windows + " 個相同起訖日期的重疊 10 年窗口（首窗 " +
      forwardRows[0].start + "–" + forwardRows[0].end + "；末窗 " +
      forwardRows[windows - 1].start + "–" + forwardRows[windows - 1].end +
      "）；每年 " + tradingDaysPerYear + " 個交易日再平衡、起始 NAV $100,000、不提款／不供款；目標 " +
      (one("#target") || {}).value + "%，轉換規則 " + selectedText("#timing") +
      "，實質值使用 " + (inflation * 100).toFixed(2) + "% 通脹假設。最大回撤年為每窗首次觸及該窗最大回撤的交易年（第 1–10 年）。";
    pairedComparison.querySelector("#pairedComparisonLimits").textContent =
      "價格來源：" + (reverseData.datasetSource || "src/data/universe.json") + "，截至 " +
      (reverseData.sourceAsOf || "unknown") + "，來源 SHA-256 " + String(reverseData.sourceFileSha256 || "").slice(0,16) +
      "…；僅限 SPY/TLT、不提款。未扣交易成本、稅費、滑點；窗口彼此重疊，不是 157 次獨立試驗，也不保證未來表現。";
    pairedComparison._pairedData = {protocol:{nWindows:windows,startIndex,stride,horizonTradingDays:horizon,tradingDaysPerYear},forward,reverse:reversed,paired,forwardRows,reverseRows};
  }
  function queueRender() {
    if (queued) return;
    queued = true;
    requestAnimationFrame(function () {
      queued = false;
      render();
    });
  }

  ["#year", "#target", "#timing", "#bond", "#flow", "#realMode", "#statView", "#glidepathDirection"].forEach(function (selector) {
    const control = one(selector);
    if (control) {
      control.addEventListener("input", queueRender);
      control.addEventListener("change", queueRender);
    }
  });
  render();
})();