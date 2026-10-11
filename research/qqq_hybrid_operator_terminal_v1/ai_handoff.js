(function (root) {
  "use strict";

  function text(value) {
    if (value === null || value === undefined || value === "") return "—";
    if (typeof value === "object") return JSON.stringify(value);
    return String(value);
  }

  function cell(value) {
    return text(value).replace(/\|/g, "\\|").replace(/\r?\n/g, " ");
  }

  function serialize(plan, candidates, marketMeta) {
    const p = plan || {};
    const input = p.input || {};
    const result = p.result || {};
    const market = result.market || {};
    const rows = Array.isArray(result.rows) ? result.rows : [];
    const generatedAt = p.generatedAt || new Date().toISOString();
    const optionCandidates = candidates || {};
    const snapshot = input.market || {};
    const toUsd = value => Number.isFinite(Number(value)) && value !== null ? "$" + Number(value).toFixed(2) : "PENDING";
    const resultRows = rows.map(row => ({
      key: row.key,
      label: row.label,
      current: row.current,
      capacity: row.capacity,
      target: row.target,
      delta: row.delta,
      action: row.action,
      status: row.status,
      riskPerUnit: row.riskPerUnit,
      allocatedRiskBudgetUsd: row.allocatedRiskBudgetUsd,
      targetRiskReserveUsd: row.targetRiskReserveUsd,
      incrementalCapitalUsd: row.incrementalCapitalUsd,
      targetNotionalUsd: row.targetNotionalUsd,
      reason: row.reason
    }));
    const rowTable = resultRows.length
      ? ["| Position | Current | Capacity | Target | Action | Status / reason |",
         "|---|---:|---:|---:|---|---|"]
          .concat(resultRows.map(row => "| " + [
            cell(row.label || row.key), cell(row.current), cell(row.capacity),
            cell(row.target), cell(row.action),
            cell((row.status || "") + (row.reason ? " — " + row.reason : ""))
          ].join(" | ") + " |")).join("\n")
      : "No calculated position rows were included.";
    const candidateLines = [
      ["QQQ far call-credit", optionCandidates.qqqCall],
      ["VXX call-credit", optionCandidates.vxxCall],
      ["QQQ bear-call (research-only)", optionCandidates.qqqBearCall],
      ["QQQ put (outside primary budget)", optionCandidates.qqqPut],
      ["Other candidates", optionCandidates]
    ];
    const candidateSummary = candidateLines.map(pair =>
      "- **" + pair[0] + ":** " + (pair[1] ? cell(pair[1]) : "not present in this export")
    ).join("\n");
    const payload = {
      schema: "QQQ_HYBRID_AI_REVIEW_PACK_V1",
      generatedAt,
      operatorTerminalSchema: "QQQ_HYBRID_OPERATOR_TERMINAL_V1",
      marketMeta: marketMeta || "",
      input: input,
      result: result,
      candidates: optionCandidates,
      guardrails: {
        role: "Independent manual review; not an order instruction",
        brokerOrders: false,
        automaticMutation: false,
        historicalSizingPromotedToLive: false,
        missingDataPolicy: "BLOCK or WAIT; do not impute, infer, or silently use stale values",
        separateResearchAxes: ["ACCURACY", "GENERALITY", "INTEGRATION"],
        currentFarCallOverlayDisposition: "RESEARCH ONLY; not approved for Frozen Original Hybrid integration"
      }
    };
    const currentGate = (market.status || "UNKNOWN") + " / " +
      (market.state || "STATE UNKNOWN") + " / action=" + (market.action || "UNKNOWN");
    return [
      "# QQQ Hybrid — Manual AI Review Pack",
      "",
      "**Generated (UTC if ISO timestamp):** " + generatedAt,
      "**Pack schema:** QQQ_HYBRID_AI_REVIEW_PACK_V1",
      "**Market gate:** " + currentGate,
      "**APP sizing result:** " + (result.ok ? "CALCULATED — HUMAN REVIEW REQUIRED" : "BLOCKED / INCOMPLETE — no sizing approval"),
      "**Broker orders:** disabled. This packet cannot place, modify, or cancel an order.",
      "",
      "## How to use this packet",
      "Attach this Markdown file to the current ChatGPT conversation. Also provide a fresh broker option-chain screenshot or broker CSV for the exact candidate contracts, showing observation time and timezone. Tell the AI about any current holdings or pending orders not represented in the APP inputs. Never include passwords, account IDs, access tokens, or other secrets.",
      "",
      "## Data and source boundary",
      "- APP snapshot metadata: " + cell(marketMeta || "No source metadata recorded"),
      "- QQQ spot as-of: " + cell(snapshot.spot_asof),
      "- VX M1/M2 as-of: " + cell(snapshot.term_asof),
      "- Snapshot date: " + cell(snapshot.today),
      "- M1: " + cell(snapshot.m1) + "; M2: " + cell(snapshot.m2) + "; supplied/computed slope: " + cell(market.slope),
      "- Market gate reason: " + cell(market.reason),
      "- Missing/stale/mixed required market data means BLOCK. Public option-chain results can be delayed or estimated and are not proof of executable prices.",
      "",
      "## APP-computed positions (capacity is not permission to trade)",
      rowTable,
      "",
      "### Available capital / risk reconciliation",
      "- NAV: " + toUsd(result.nav) + "; truly uncommitted cash: " + toUsd(result.cashPool),
      "- Cash reserve: " + toUsd(result.cashReserveUsd),
      "- Shared option max-loss pool: " + toUsd(result.totalOptionRiskPool),
      "- QQQ incremental capital: " + toUsd(result.qqqAdditionalCapitalUsd),
      "- VXX incremental margin estimate: " + toUsd(result.vxxAdditionalMarginUsd),
      "- Planned required capital: " + toUsd(result.plannedCapitalRequiredUsd),
      "- Unallocated cash after plan: " + toUsd(result.remainingUnallocatedCashUsd),
      "- APP calculation status: " + (result.ok ? "CALCULATED / REVIEW" : "BLOCKED"),
      "",
      "### Candidate status",
      candidateSummary,
      "",
      "## Non-negotiable measurement gates",
      "Report each axis separately. Do not average the axes into a single score; a critical hard-gate failure overrides other passes.",
      "",
      "1. **Accuracy:** verify timestamps, source type and exact contract identity; recompute all price/quantity arithmetic independently; require quoted legs from the same expiry; verify bid/ask side, multiplier, adjusted deliverable, fees/slippage and fill assumptions. Cash-flow reconciliation tolerance is USD 0.01. Missing data stays missing; never forward-fill or invent fills.",
      "2. **Generality:** identify whether the sample is development data or a genuinely untouched holdout. Previously inspected 2018–2025 data cannot be relabelled virgin OOS. Report coverage numerator/denominator, terminal source date, unmatched dates and each regime/rolling window where sample size permits. Require at least five chronological windows where possible, and disclose cost stress of at least 1.5× where relevant.",
      "3. **Integration / incremental value:** compare against a clearly identified matched baseline on identical dates, capital flows, marks and costs. Use the pre-registered objective bars in RESEARCH_MEASUREMENT_CONTRACT.md; do not change thresholds after seeing outcomes. CAGR, daily MTM MaxDD, Sharpe and ES95 must be UNAVAILABLE when the paired mark path is incomplete.",
      "4. **Capital and risk:** shared risk pool includes only QQQ far call-credit and VXX call-credit; never double-count reserve, stock purchases, option loss budget or short-stock margin. VXX short margin is not a maximum-loss cap. Verify contract root/deliverable, especially any adjusted VXX option.",
      "5. **Execution readiness:** APP ADD / BUY is only a sizing preview. No order-ready status unless all market, quote, contract, cash, risk and human-confirmation gates pass. Otherwise output BLOCK or WAIT and name the exact missing evidence.",
      "",
      "## Current research lockbox (do not conceal)",
      "- Accuracy for trade-performance use: BLOCKED. The accounting sub-gate reconciled 1,688 / 1,688 closed rows to USD 0.00 maximum error, but quote/source/fill accuracy is still blocked.",
      "- Generality: NOT DEMONSTRATED. The previously examined 2018–2025 sample is not an untouched final holdout; the pinned option source ends 2025-12-15, with 11 expected terminal sessions missing and 24 unmatched NAV dates.",
      "- Integration: FAILS_CURRENT_BASE_SCREEN for the isolated FAR CALL overlay. Its zero-cost 0.8% NAV max-loss arm reported -USD 5,646 closed-trade P&L and -USD 5,552 last paired-date NAV gap versus the no-call control.",
      "- Important scope: that negative result is an isolated overlay versus a 42% QQQ total-return proxy plus static 58% cash; it is NOT a complete performance result for the full Frozen Original Hybrid. It nevertheless does not approve the incremental overlay.",
      "- No new strategy tuning or integration until the accuracy and generality hard gates pass and the pre-registered integration bar is satisfied.",
      "",
      "## Required AI response format",
      "Return these sections in order:",
      "1. **Gate verdict:** DATA (PASS / BLOCK / WAIT), CONTRACT (PASS / BLOCK / WAIT), CAPITAL (PASS / BLOCK / WAIT), EXECUTION EVIDENCE (PASS / BLOCK / WAIT), STRATEGY EVIDENCE (PASS / NOT DEMONSTRATED / FAIL). Give evidence for every verdict.",
      "2. **Market state:** as-of timestamps, M1/M2 slope calculation, VIX regime, source mismatches and freshness.",
      "3. **Position table:** current → target → proposed delta, exact symbol/side/strike/expiry/quantity when supported, otherwise UNKNOWN/PENDING.",
      "4. **Per-trade arithmetic:** bid/ask used, net credit/debit, spread width, verified multiplier/deliverable, max profit, max loss, breakeven, fees/slippage assumption, total risk consumed.",
      "5. **Capital reconciliation:** NAV, uncommitted cash, reserve, incremental QQQ cash, VXX margin estimate, shared option risk, planned capital, residual cash; explicitly show any discrepancy above USD 0.01.",
      "6. **Counter-evidence / failure modes:** which input could reverse the decision, price-basis issue, quote gaps, execution realism, unmatched marks and model assumptions.",
      "7. **Human action:** only one of BLOCK, WAIT FOR DATA, or ELIGIBLE FOR HUMAN REVIEW. Do not claim an order was placed or use an unqualified BUY signal.",
      "",
      "## Raw machine-readable snapshot",
      "The JSON below is the machine-readable companion to the human summary. Inspect it rather than inferring values from this text alone.",
      "",
      "~~~~json",
      JSON.stringify(payload, null, 2),
      "~~~~",
      "",
      "No broker order is placed by this packet — manual review only."
    ].join("\n") + "\n";
  }

  const api = { serialize: serialize };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (root) root.AiHandoffV1 = api;
})(typeof window !== "undefined" ? window : (typeof globalThis !== "undefined" ? globalThis : this));
