/* GLIDEPATH_TRAJECTORY_PANEL_V1 */
(function () {
  "use strict";

  const summary = document.querySelector("#decisionSummary");
  if (!summary || document.getElementById("decisionTrajectory")) return;

  const years = Array.from({length: 11}, (_, index) => index);
  const section = document.createElement("section");
  section.id = "decisionTrajectory";
  section.className = "decision-trajectory";
  section.setAttribute("aria-live", "polite");

  let html = '<div class="trajectory-heading"><div><h2>第 0–10 年股／債配置路徑</h2><p id="decisionTrajectoryLead" class="trajectory-lead">同步所選轉換規則、債券目標和代理標的。</p></div><div class="trajectory-legend"><span>股票 = 100% − 債券比例</span><span>第 10 年對照目標比例</span></div></div>';
  html += '<div class="trajectory-table-scroll"><table class="trajectory-table" aria-label="第 0 至第 10 年逐年股票和債券目標比例"><thead><tr><th scope="col">配置路徑</th>';
  years.forEach(function (year) {
    html += '<th scope="col"><button type="button" data-trajectory-year="' + year + '" aria-pressed="false">第 ' + year + ' 年</button></th>';
  });
  html += '</tr></thead><tbody>';
  html += '<tr data-series="stock"><th scope="row">股票目標</th>';
  years.forEach(function (year) { html += '<td data-year="' + year + '">—</td>'; });
  html += '</tr><tr data-series="bond"><th scope="row"><span id="decisionTrajectoryBondLabel">債券目標</span></th>';
  years.forEach(function (year) { html += '<td data-year="' + year + '">—</td>'; });
  html += '</tr><tr data-series="change"><th scope="row">債券較上年變化</th>';
  years.forEach(function (year) { html += '<td data-year="' + year + '">—</td>'; });
  html += '</tr></tbody></table></div>';
  html += '<p id="decisionTrajectoryCrosscheck" class="trajectory-crosscheck">正在對照所選年份的路徑與歷史回測摘要……</p>';
  html += '<p id="decisionTrajectoryStatus" class="trajectory-status" role="status" data-state="pending">正在讀取第 7 圖的年份節點……</p>';
  html += '<p class="trajectory-disclaimer">這是所選轉換規則產生的目標配置路徑，不是歷史每日實際持倉或交易紀錄。上方金額仍按所選年份的歷史回測結果拆分；不同年份的 NAV 不可沿用同一金額。</p>';
  section.innerHTML = html;
  summary.insertAdjacentElement("afterend", section);

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
    ".trajectory-table thead button{font:inherit;color:inherit;border:1px solid rgba(127,127,127,.3);background:transparent;border-radius:6px;padding:5px 6px;cursor:pointer;white-space:nowrap}" +
    ".trajectory-table thead button:hover,.trajectory-table thead button:focus-visible{outline:2px solid rgba(59,130,246,.7);outline-offset:1px}" +
    ".trajectory-table .trajectory-selected{background:rgba(59,130,246,.14);font-weight:700;box-shadow:inset 0 0 0 1px rgba(59,130,246,.4)}" +
    ".trajectory-crosscheck{padding:8px 10px;border-left:3px solid rgba(127,127,127,.5);background:rgba(127,127,127,.06);border-radius:4px}" +
    ".trajectory-status[data-state=blocked],.trajectory-status[data-state=pending]{font-weight:600}" +
    ".trajectory-disclaimer{opacity:.75;font-size:.78rem;margin-top:8px}" +
    "@media(max-width:640px){.decision-trajectory{padding:10px}.trajectory-heading{gap:5px}.trajectory-table{min-width:690px}.trajectory-heading h2{font-size:1rem}}";
  document.head.appendChild(style);

  const TOP_Y = 15;
  const BOTTOM_Y = 180;
  let queued = false;

  function one(selector) { return document.querySelector(selector); }
  function selectedText(selector) {
    const element = one(selector);
    if (!element) return "";
    if (element.selectedOptions && element.selectedOptions.length) return element.selectedOptions[0].textContent.trim();
    return String(element.value || "").trim();
  }
  function percentFromNode(node) {
    const explicitNames = ["data-bond-pct", "data-bond-percent", "data-bond-allocation-pct"];
    for (const name of explicitNames) {
      const raw = node.getAttribute(name);
      if (raw !== null && raw.trim() !== "") {
        const parsed = Number(raw.replace("%", ""));
        if (Number.isFinite(parsed)) return Math.max(0, Math.min(100, parsed <= 1 && parsed >= 0 ? parsed * 100 : parsed));
      }
    }
    const cy = Number(node.getAttribute("cy"));
    if (!Number.isFinite(cy) || cy < TOP_Y - 0.5 || cy > BOTTOM_Y + 0.5) return null;
    const pct = (BOTTOM_Y - cy) * 100 / (BOTTOM_Y - TOP_Y);
    if (!Number.isFinite(pct) || pct < -0.5 || pct > 100.5) return null;
    return Math.max(0, Math.min(100, pct));
  }
  function pathForTiming(timing) {
    return Array.from(document.querySelectorAll("#glide circle[data-year][data-timing]"))
      .filter(function (node) { return node.getAttribute("data-timing") === timing; })
      .map(function (node) {
        const year = Number(node.getAttribute("data-year"));
        const bondPct = percentFromNode(node);
        return {year: year, bondPct: bondPct};
      })
      .filter(function (point) { return Number.isInteger(point.year) && point.year >= 0 && point.year <= 10; })
      .sort(function (left, right) { return left.year - right.year; });
  }
  function showUnavailable(message) {
    section.dataset.state = "pending";
    section.dataset.target = String((one("#target") || {}).value || "");
    section.dataset.timing = String((one("#timing") || {}).value || "");
    section.dataset.year = String((one("#year") || {}).value || "");
    section.querySelector("#decisionTrajectoryStatus").dataset.state = "pending";
    section.querySelector("#decisionTrajectoryStatus").textContent = "PENDING · " + message + "；未以估算比例補值。";
    ["stock", "bond", "change"].forEach(function (series) {
      section.querySelectorAll('[data-series="' + series + '"] td[data-year]').forEach(function (cell) { cell.textContent = "—"; });
    });
  }
  function render() {
    const targetElement = one("#target");
    const timingElement = one("#timing");
    const yearElement = one("#year");
    if (!targetElement || !timingElement || !yearElement) return showUnavailable("找不到原有年份、目標或轉換規則控制項");
    const timing = timingElement.value;
    const target = Number(targetElement.value);
    const selectedYear = Number(yearElement.value);
    const points = pathForTiming(timing);
    if (!Number.isFinite(target) || !Number.isInteger(selectedYear)) return showUnavailable("所選控制值不是有效數字");
    if (points.length !== 11 || points.some(function (point, index) { return point.year !== index || !Number.isFinite(point.bondPct); })) {
      return showUnavailable("目前規則沒有完整的第 0 至第 10 年配置節點");
    }
    const endpoint = points[10].bondPct;
    if (Math.abs(endpoint - target) > 0.75) {
      return showUnavailable("第 10 年路徑終點 " + endpoint.toFixed(2) + "% 與目標 " + target.toFixed(2) + "% 不一致");
    }

    const bondName = selectedText("#bond") || "債券代理";
    const timingName = selectedText("#timing") || timing;
    section.querySelector("#decisionTrajectoryBondLabel").textContent = bondName + " 目標";
    section.querySelector("#decisionTrajectoryLead").textContent =
      "規則：" + timingName + " · 第 10 年目標 " + bondName + " " + target.toFixed(2) + "% · 所選年份：" + selectedYear + "。點擊年份可同步切換上方回測摘要和原有年份 BAR。";

    points.forEach(function (point, index) {
      const stockPct = 100 - point.bondPct;
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
      const yearButton = section.querySelector('[data-trajectory-year="' + point.year + '"]');
      yearButton.setAttribute("aria-pressed", point.year === selectedYear ? "true" : "false");
      yearButton.classList.toggle("trajectory-selected", point.year === selectedYear);
    });

    const summaryAllocation = (one("#decisionAllocationHeadline") || {}).textContent || "";
    const rates = Array.from(summaryAllocation.matchAll(/(\d+(?:\.\d+)?)%/g)).map(function (match) { return Number(match[1]); });
    const selectedPoint = points.find(function (point) { return point.year === selectedYear; });
    const crosscheck = section.querySelector("#decisionTrajectoryCrosscheck");
    if (rates.length >= 2 && selectedPoint) {
      const stockDelta = (100 - selectedPoint.bondPct) - rates[0];
      const bondDelta = selectedPoint.bondPct - rates[1];
      crosscheck.textContent = "第 " + selectedYear + " 年對照：規則路徑為股票 " +
        (100 - selectedPoint.bondPct).toFixed(2) + "% / " + bondName + " " +
        selectedPoint.bondPct.toFixed(2) + "%；歷史回測摘要為股票 " + rates[0].toFixed(2) +
        "% / " + bondName + " " + rates[1].toFixed(2) + "%；差異：股票 " +
        (stockDelta > 0 ? "+" : "") + stockDelta.toFixed(2) + ppLabel() + "、債券 " +
        (bondDelta > 0 ? "+" : "") + bondDelta.toFixed(2) + ppLabel() +
        "。金額拆分仍以主摘要的該年回測 NAV 為準。";
      section.dataset.summaryBondPct = rates[1].toFixed(4);
      section.dataset.allocationDeltaPp = bondDelta.toFixed(4);
      section.dataset.crosscheck = Math.abs(bondDelta) <= 0.75 ? "aligned" : "different";
    } else {
      crosscheck.textContent = "所選年份的路徑比例已列出；目前無法從主摘要讀取兩個配置比例，因此不顯示差異值。";
      section.dataset.crosscheck = "unavailable";
    }

    section.dataset.state = "ready";
    section.dataset.target = String(target);
    section.dataset.timing = timing;
    section.dataset.year = String(selectedYear);
    section.dataset.endpointBondPct = endpoint.toFixed(4);
    section.querySelector("#decisionTrajectoryStatus").dataset.state = "ready";
    section.querySelector("#decisionTrajectoryStatus").textContent =
      "已同步 11 個年份節點；第 10 年債券路徑 " + endpoint.toFixed(2) +
      "%，目標 " + target.toFixed(2) + "%。年度差值為規則路徑百分點，不代表當年交易金額或交易紀錄。";
  }
  function ppLabel() { return " 個百分點"; }
  function queueRender() {
    if (queued) return;
    queued = true;
    requestAnimationFrame(function () {
      queued = false;
      render();
    });
  }

  section.querySelectorAll("[data-trajectory-year]").forEach(function (button) {
    button.addEventListener("click", function () {
      const year = Number(button.getAttribute("data-trajectory-year"));
      const yearControl = one("#year");
      if (!yearControl || !Number.isInteger(year)) return;
      yearControl.value = String(year);
      yearControl.dispatchEvent(new Event("input", {bubbles: true}));
      yearControl.dispatchEvent(new Event("change", {bubbles: true}));
      queueRender();
    });
  });

  ["#year", "#target", "#timing", "#bond", "#flow", "#realMode", "#statView"].forEach(function (selector) {
    const control = one(selector);
    if (control) {
      control.addEventListener("input", queueRender);
      control.addEventListener("change", queueRender);
    }
  });
  const glide = one("#glide");
  if (glide && typeof MutationObserver !== "undefined") {
    new MutationObserver(queueRender).observe(glide, {
      subtree: true,
      childList: true,
      attributes: true,
      attributeFilter: ["cy", "data-year", "data-timing"]
    });
  }
  render();
})();