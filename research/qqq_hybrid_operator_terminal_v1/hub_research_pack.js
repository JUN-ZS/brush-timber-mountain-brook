(function (root) {
  "use strict";

  const MULTIPLIER = 100;
  const EPS = 1e-9;

  function num(value, fallback = null) {
    if (value === null || value === undefined || value === "") return fallback;
    const parsed = Number(String(value).replace(/,/g, ""));
    return Number.isFinite(parsed) ? parsed : fallback;
  }

  function calculateNavExitReferences(navValue) {
    const nav = num(navValue);
    if (!(nav > 0)) return { ready: false, nav: null, targets: [], error: "NAV must be positive to normalize exit thresholds." };
    const targets = [0.5, 1, 2].map(percentNav => ({
      percentNav,
      usd: Math.round(nav * percentNav) / 100
    }));
    return { ready: true, nav, targets };
  }

  function whole(value, fallback = 0) {
    const n = num(value, fallback);
    return Number.isFinite(n) ? Math.max(0, Math.floor(n)) : fallback;
  }

  function clamp(value, low, high) {
    return Math.max(low, Math.min(high, value));
  }

  function intrinsic(right, strike, spot) {
    return right === "call" ? Math.max(0, spot - strike) : Math.max(0, strike - spot);
  }

  function validateLegs(legs) {
    if (!Array.isArray(legs) || !legs.length) return "No option legs supplied.";
    for (const leg of legs) {
      if (!["call", "put"].includes(leg.right) || !["BUY", "SELL"].includes(leg.side)) return "Invalid option side or right.";
      if (!(num(leg.strike, 0) > 0) || !(num(leg.qty, 0) > 0)) return "Every leg needs a positive strike and quantity.";
      if (num(leg.price) === null || num(leg.price) < 0) return "Every leg needs a non-negative observed entry price.";
    }
    return null;
  }

  // Entry cash debit can be negative (a net credit). Risk is the worst
  // expiry payoff loss on the package's listed strikes, not an intraday loss cap.
  function terminalMaxLoss(legs, spot) {
    const error = validateLegs(legs);
    if (error) return { ready: false, riskUsd: null, debitUsd: null, error, source: "MISSING_OR_INVALID_INPUT" };
    const s0 = num(spot);
    if (!(s0 > 0)) return { ready: false, riskUsd: null, debitUsd: null, error: "Enter a verified QQQ spot.", source: "MISSING_SPOT" };

    let debitUsd = 0;
    let callTailSlope = 0;
    const points = new Set([0, s0]);
    for (const leg of legs) {
      const qty = num(leg.qty);
      const strike = num(leg.strike);
      const price = num(leg.price);
      const signedQty = leg.side === "BUY" ? qty : -qty;
      debitUsd += signedQty * price * MULTIPLIER;
      points.add(strike);
      if (leg.right === "call") callTailSlope += signedQty;
    }
    if (callTailSlope < -EPS) {
      return { ready: false, riskUsd: null, debitUsd, error: "Call-side tail has net short exposure and no finite upside loss cap.", source: "UNBOUNDED_TAIL" };
    }

    const values = [...points].filter(Number.isFinite).sort((a, b) => a - b);
    let worstPnl = Infinity;
    for (const priceAtExpiry of values) {
      let payoff = 0;
      for (const leg of legs) {
        const signedQty = leg.side === "BUY" ? num(leg.qty) : -num(leg.qty);
        payoff += signedQty * intrinsic(leg.right, num(leg.strike), priceAtExpiry) * MULTIPLIER;
      }
      worstPnl = Math.min(worstPnl, payoff - debitUsd);
    }
    const riskUsd = Math.max(0, -worstPnl);
    return { ready: true, riskUsd, debitUsd, worstExpiryPnlUsd: worstPnl, source: "ENTRY_BID_ASK_TERMINAL_PAYOFF_PROXY" };
  }

  function ratioCallLegs(inputs, n) {
    return [
      { name: "ATM long call", right: "call", side: "BUY", qty: 1, strike: num(inputs.atmStrike), price: num(inputs.atmAsk) },
      { name: "OTM short calls", right: "call", side: "SELL", qty: n, strike: num(inputs.shortStrike), price: num(inputs.shortBid) },
      { name: "Far OTM long wings", right: "call", side: "BUY", qty: n, strike: num(inputs.wingStrike), price: num(inputs.wingAsk) }
    ];
  }

  function ratioGeometryError(inputs) {
    const values = [inputs.atmStrike, inputs.shortStrike, inputs.wingStrike].map(v => num(v));
    const prices = [inputs.atmAsk, inputs.shortBid, inputs.wingAsk].map(v => num(v));
    if (values.some(v => !(v > 0)) || prices.some(v => v === null || v < 0) || !(prices[0] > 0) || !(prices[2] > 0)) return "ATM/wing Ask must be positive; all strikes and observed Bid/Ask prices are required.";
    if (!(values[0] < values[1] && values[1] < values[2])) return "Call geometry must satisfy ATM strike < short-call strike < farther-OTM wing strike.";
    return null;
  }

  function calculateRatioCall(input) {
    const d = input || {};
    const geomError = ratioGeometryError(d);
    const nav = num(d.nav, 0);
    const budgetUsd = Math.max(0, num(d.budgetUsd, 0));
    const cap = clamp(whole(d.maxN, 4), 1, 6);
    if (geomError || !(nav > 0) || !(budgetUsd > 0)) {
      return { ready: false, status: "PENDING", error: geomError || "NAV and remaining option-risk budget must be positive.", budgetUsd, riskByN: [] };
    }
    const riskByN = [];
    for (let n = 1; n <= cap; n += 1) {
      const risk = terminalMaxLoss(ratioCallLegs(d, n), d.spot);
      riskByN.push({ n, riskUsd: risk.riskUsd, debitUsd: risk.debitUsd, ready: risk.ready, error: risk.error });
    }
    const feasible = riskByN.filter(x => x.ready && x.riskUsd <= budgetUsd + EPS);
    const maxAffordableN = feasible.length ? Math.max(...feasible.map(x => x.n)) : 0;
    const mode = d.mode || "ratio-dynamic-v2";
    let entryN = 0;
    if (mode === "ratio-harvest50") {
      const requested = clamp(whole(d.requestedN, 2), 1, cap);
      const picked = riskByN.find(x => x.n === requested);
      entryN = picked && picked.ready && picked.riskUsd <= budgetUsd + EPS ? requested : 0;
    } else if (mode === "ratio-fresh-v7") {
      const picked = riskByN.find(x => x.n === 2);
      entryN = picked && picked.ready && picked.riskUsd <= budgetUsd + EPS ? 2 : 0;
    } else {
      entryN = riskByN.filter(x => x.n <= 4 && x.ready && x.riskUsd <= budgetUsd + EPS).reduce((max, x) => Math.max(max, x.n), 0);
    }
    const entry = riskByN.find(x => x.n === entryN) || null;
    const currentN = clamp(whole(d.currentN, entryN || 0), 0, 6);
    const currentShorts = clamp(whole(d.currentShorts, currentN), 0, 1000);
    const currentWings = clamp(whole(d.currentWings, currentN), 0, 1000);
    const delta = num(d.currentShortDelta, 0.20);
    const packagePnl = num(d.packagePnlUsd, 0);
    const riskAtEntry = entry ? entry.riskUsd : 0;
    const lossFraction = riskAtEntry > 0 ? Math.max(0, -packagePnl) / riskAtEntry : 0;
    let targetPairs = currentN;
    let targetShorts = currentShorts;
    let targetWings = currentWings;
    let action = entryN ? "ENTRY ELIGIBLE / REVIEW" : "BLOCKED BY RISK GATE";
    let reason = entryN ? "The selected entry structure fits the current risk budget; actual fills and position state still require manual verification." : "Chosen N does not fit the risk budget, or a required quote/geometry is missing.";
    let harvestedPairs = 0;

    if (entryN && currentN === 0) {
      action = "NEW ENTRY ELIGIBLE / REVIEW";
      reason = "No current position quantity was entered. Entry N and risk fit are shown above; position-management actions wait until the actual open legs are entered.";
    } else if (entryN && mode === "ratio-harvest50") {
      const pairQuotes = [num(d.shortBid), num(d.wingAsk), num(d.currentShortAsk), num(d.currentWingBid)];
      const pairPnl = pairQuotes.every(Number.isFinite)
        ? ((pairQuotes[0] - pairQuotes[1]) - (pairQuotes[2] - pairQuotes[3])) * MULTIPLIER
        : null;
      if (d.approachTouched && d.nextDayReversal && pairPnl !== null && pairPnl > 0 && currentN > 0) {
        harvestedPairs = Math.ceil(currentN / 2);
        targetPairs = Math.max(0, currentN - harvestedPairs);
        targetShorts = targetPairs;
        targetWings = targetPairs;
        action = "HARVEST 50%+ PAIRS";
        reason = "HARVEST50 V1: after an approach/reversal, close at least half of the profitable short+wing pairs; keep the ATM long.";
      } else {
        action = "HOLD / WAIT FOR HARVEST TRIGGER";
        reason = "HARVEST50 V1 is event-driven. A short-strike touch alone is not an exit; the next-day reversal and profitable executable pair are required.";
      }
    } else if (entryN && mode === "ratio-dynamic-v2") {
      const deltaReductions = Number.isFinite(delta) ? Math.max(0, Math.floor((delta - 0.20) / 0.15 + 1e-9)) : 0;
      targetPairs = Math.max(0, entryN - deltaReductions);
      if (lossFraction >= 0.25 && riskAtEntry > 0) targetPairs = Math.min(targetPairs, Math.max(0, Math.ceil(entryN * Math.max(0, 1 - lossFraction))));
      targetPairs = Math.min(currentN, targetPairs);
      targetShorts = targetPairs;
      targetWings = targetPairs;
      action = targetPairs < currentN ? "REDUCE SHORT+WING PAIRS" : "HOLD / MONITOR";
      reason = "Dynamic-N V2: reduce one pair per +0.15 short-delta step from 0.20; at 25%+ package-risk consumption, also apply the frozen package-DD target.";
      if (d.approachTouched && d.nextDayContinuation) {
        targetPairs = 0;
        targetShorts = 0;
        targetWings = currentWings;
        action = "CLOSE ALL SHORTS; KEEP WINGS + ATM";
        reason = "Dynamic-N V2 breakout continuation: buy back all remaining short calls while keeping the ATM long and remaining wings.";
      } else if (d.approachTouched && d.nextDayReversal && num(d.currentShortAsk, Infinity) <= 0.5 * num(d.shortBid, 0) && currentShorts > 0) {
        targetShorts = Math.max(0, currentShorts - Math.ceil(currentShorts / 2));
        targetWings = currentWings;
        action = "HARVEST SHORTS ONLY";
        reason = "Dynamic-N V2 reversal harvest: if the short buyback Ask is no more than 50% of entry short Bid, buy back at least half the remaining shorts and retain wings/ATM.";
      }
    } else if (entryN && mode === "ratio-fresh-v7") {
      targetPairs = currentN;
      targetShorts = currentShorts;
      targetWings = currentWings;
      action = "HOLD / MONITOR";
      reason = "Fresh-Pair V7 starts at N=2, caps N at 4, and requires quote-confirmed state transitions.";
      if (d.approachTouched && d.nextDayContinuation && currentN > 0) {
        if (currentN > 1) {
          targetPairs = currentN - 1;
          targetShorts = Math.min(currentShorts, targetPairs);
          targetWings = Math.min(currentWings, targetPairs);
          action = "CONTINUATION: CLOSE ONE PAIR";
        } else {
          targetPairs = 0;
          targetShorts = Math.max(0, currentShorts - 1);
          targetWings = currentWings;
          action = "CONTINUATION: CLOSE LAST SHORT ONLY";
        }
        reason = "Fresh-Pair V7 continuation closes one short+wing pair; when one pair remains, it removes the last short and keeps the wing.";
      } else if (d.approachTouched && d.nextDayReversal && num(d.currentShortAsk, Infinity) <= 0.5 * num(d.shortBid, 0) && currentShorts > 0) {
        targetShorts = Math.max(0, currentShorts - 1);
        action = "REVERSAL: CLOSE ONE LEAD SHORT";
        reason = "Fresh-Pair V7 reversal harvest buys back one lead short only when its Ask is no more than half the entry short Bid.";
      } else if (lossFraction >= 0.25 && riskAtEntry > 0 && num(d.currentShortAsk, Infinity) <= num(d.shortBid, 0)) {
        targetShorts = Math.min(currentShorts, Math.max(0, Math.ceil(2 * Math.max(0, 1 - lossFraction))));
        action = targetShorts < currentShorts ? "DOWNSIDE DD: REDUCE SHORTS ONLY" : "HOLD: DD CUT PRICE NOT MET";
        reason = "Fresh-Pair V7 downside governor reduces short-only inventory from the entry risk fraction; wing inventory remains. Buyback must be no dearer than entry short Bid.";
      } else if (delta <= 0.10 && whole(d.lowDeltaStreak, 0) >= 2 && whole(d.sessionsSinceChange, 99) >= 5 && currentN < 4) {
        const nextRisk = riskByN.find(x => x.n === currentN + 1);
        if (nextRisk && nextRisk.ready && nextRisk.riskUsd <= budgetUsd + EPS) {
          targetPairs = currentN + 1;
          targetShorts = currentShorts + 1;
          targetWings = currentWings + 1;
          action = "ADD ONE FRESH SHORT+WING PAIR";
          reason = "Fresh-Pair V7 add gate passes: short delta <=0.10 for two sessions, five-session cooldown, N<=4 and resulting entry-risk proxy within budget.";
        } else {
          action = "HOLD: NEXT N FAILS RISK GATE";
        }
      } else if (delta >= 0.35 && currentN > 0) {
        targetPairs = currentN - 1;
        targetShorts = Math.max(0, currentShorts - 1);
        targetWings = Math.max(0, currentWings - 1);
        action = "REDUCE ONE SHORT+WING PAIR";
        reason = "Fresh-Pair V7 reduces one short+wing pair when an open short delta reaches 0.35 or higher.";
      }
    }

    return {
      ready: true, status: entryN ? "RISK_GATE_PASS" : "RISK_GATE_BLOCK",
      mode, budgetUsd, maxAffordableN, entryN, currentN, riskUsd: entry ? entry.riskUsd : null,
      debitUsd: entry ? entry.debitUsd : null, targetPairs, targetShorts, targetWings,
      currentShorts, currentWings, harvestedPairs, lossFraction, action, reason, riskByN,
      legs: entryN ? ratioCallLegs(d, entryN) : [],
      source: "HUB_RATIO_CALL_RESEARCH_TEMPLATE"
    };
  }

  function stateAdaptiveLegs(d) {
    return [
      { name: "ATM long call", right: "call", side: "BUY", qty: 1, strike: num(d.atmStrike), price: num(d.atmAsk) },
      { name: "Short calls", right: "call", side: "SELL", qty: 2, strike: num(d.shortStrike), price: num(d.shortBid) },
      { name: "Far call wings", right: "call", side: "BUY", qty: 2, strike: num(d.wingStrike), price: num(d.wingAsk) },
      { name: "Long put", right: "put", side: "BUY", qty: 1, strike: num(d.longPutStrike), price: num(d.longPutAsk) },
      { name: "Short put", right: "put", side: "SELL", qty: 1, strike: num(d.shortPutStrike), price: num(d.shortPutBid) }
    ];
  }

  function calculateStateAdaptive(input) {
    const d = input || {};
    const callError = ratioGeometryError(d);
    const putValues = [num(d.longPutStrike), num(d.shortPutStrike), num(d.longPutAsk), num(d.shortPutBid)];
    const putError = putValues.some(v => v === null || v < 0) || !(putValues[0] > putValues[1] && putValues[1] > 0 && putValues[2] > 0)
      ? "Put geometry requires Long Put strike > Short Put strike > 0 and observed Ask/Bid prices."
      : null;
    if (callError || putError) return { ready: false, status: "PENDING", error: callError || putError };
    const legs = stateAdaptiveLegs(d);
    const risk = terminalMaxLoss(legs, d.spot);
    if (!risk.ready) return { ready: false, status: "PENDING", error: risk.error, risk };
    const budgetUsd = Math.max(0, num(d.budgetUsd, 0));
    const maxPackages = risk.riskUsd > 0 ? Math.floor((budgetUsd + EPS) / risk.riskUsd) : 0;
    const wave = clamp(whole(d.wave, 0), 0, 2);
    const prevClose = num(d.prevClose);
    const anchorClose = num(d.anchorClose);
    const atr20 = num(d.atr20);
    const waveTrigger = wave < 2 && [prevClose, anchorClose, atr20].every(Number.isFinite) && atr20 > 0 && prevClose >= anchorClose + atr20;
    const nextWave = waveTrigger ? wave + 1 : wave;
    return {
      ready: true, status: risk.riskUsd <= budgetUsd && budgetUsd > 0 ? "RISK_GATE_PASS" : "RISK_GATE_BLOCK",
      budgetUsd, riskUsd: risk.riskUsd, debitUsd: risk.debitUsd, maxPackages,
      targetPackages: Math.max(0, maxPackages), legs,
      wave, waveTrigger, nextWave,
      nextCallShortDelta: waveTrigger ? (nextWave === 1 ? 0.30 : 0.40) : null,
      nextPutShortAbsDelta: waveTrigger ? 0.05 : null,
      reason: waveTrigger
        ? "State-Adaptive Geometry wave trigger passed: the previous close is at least 1 ATR20 above the anchor. The next wave targets a closer OTM call short and a farther-OTM put short; ATM call, wings, long put, N=2 and expiry stay fixed."
        : (wave >= 2 ? "Maximum two migrations reached; keep the remaining entry geometry." : "No migration signal from the supplied prior-close / anchor / ATR20 inputs."),
      source: "HUB_STATE_ADAPTIVE_GEOMETRY_REAL_CHAIN_TEMPLATE"
    };
  }

  function calculateStaggered(input) {
    const d = input || {};
    const base = calculateStateAdaptive(d);
    if (!base.ready) return base;
    const cap = [1, 2, 4].includes(whole(d.layerCap, 1)) ? whole(d.layerCap, 1) : 1;
    const currentLayers = whole(d.currentLayers, 0);
    const affordableLayers = base.riskUsd > 0 ? Math.floor((Math.max(0, base.budgetUsd) + EPS) / base.riskUsd) : 0;
    const targetLayers = Math.min(cap, affordableLayers);
    return {
      ...base, status: targetLayers > 0 ? "RISK_GATE_PASS" : "RISK_GATE_BLOCK",
      layerCap: cap, currentLayers, targetLayers,
      reserveAtTargetUsd: targetLayers * base.riskUsd,
      remainingRiskUsd: Math.max(0, base.budgetUsd - targetLayers * base.riskUsd),
      action: currentLayers > targetLayers ? "REDUCE VINTAGES" : currentLayers < targetLayers ? "ADD VINTAGES WHEN SIGNALS QUALIFY" : "HOLD / WAIT FOR A FREE SLOT",
      reason: "Staggered Stack is a separate cross-date-vintage profile using the frozen static State-Adaptive entry package. Only 1/2/4 layers are supported; existing vintages keep their original expiry/geometry."
    };
  }

  function calculateShockGatedPut(input) {
    const d = input || {};
    const longK = num(d.longPutStrike), shortK = num(d.shortPutStrike);
    const longAsk = num(d.longPutAsk), shortBid = num(d.shortPutBid);
    const spot = num(d.spot);
    if (!(spot > 0) || !(longK > shortK && shortK > 0) || !(longAsk > 0) || !(shortBid >= 0)) {
      return { ready: false, status: "PENDING", error: "Need QQQ spot, Long Put strike > Short Put strike, positive Long Put Ask and valid Short Put Bid." };
    }
    const risk = terminalMaxLoss([
      { name: "Long protective put", right: "put", side: "BUY", qty: 1, strike: longK, price: longAsk },
      { name: "Short farther-OTM put", right: "put", side: "SELL", qty: 1, strike: shortK, price: shortBid }
    ], spot);
    if (!risk.ready) return { ready: false, status: "PENDING", error: risk.error };
    if (!(risk.debitUsd > 0)) return { ready: false, status: "PENDING", error: "This SHOCK-GATED template is a debit spread; observed Long Put Ask minus Short Put Bid must be positive." };
    const budgetUsd = Math.max(0, num(d.budgetUsd, 0));
    const capacity = risk.riskUsd > 0 ? Math.floor((budgetUsd + EPS) / risk.riskUsd) : 0;
    const drawdown = num(d.drawdown252Pct, 0);
    const ret5 = num(d.return5dPct, 0);
    const triggered = Number.isFinite(drawdown) && drawdown <= -8 || Number.isFinite(ret5) && ret5 <= -4;
    return {
      ready: true, status: !triggered ? "WAITING_FOR_SHOCK_GATE" : capacity > 0 ? "SHOCK_GATE_PASS" : "RISK_GATE_BLOCK",
      triggered, budgetUsd, riskUsd: risk.riskUsd, debitUsd: risk.debitUsd,
      maxContracts: capacity, targetContracts: triggered ? capacity : 0,
      drawdown252Pct: drawdown, return5dPct: ret5,
      reason: triggered
        ? "Shock gate passed: trailing 252-day drawdown <= -8% OR trailing 5-session return <= -4%. Long-put debit defines the spread's maximum expiry loss."
        : "No entry: frozen shock condition is not met. The spread remains a research candidate and uses no risk budget at target.",
      source: "HUB_SHOCK_GATED_PUT_DEBIT_REAL_CHAIN_TEMPLATE"
    };
  }

  function calculatePutRatio(input) {
    const d = input || {};
    const n = num(d.putRatioN);
    const direction = d.putRatioDirection === "long-heavy" ? "long-heavy" : "short-heavy";
    const expiry = String(d.putRatioExpiry || "").trim();
    if (!Number.isInteger(n) || n < 1 || n > 6) {
      return { ready: false, status: "PENDING", error: "N must be a whole number from 1 to 6." };
    }
    if (!/^\d{4}-\d{2}-\d{2}$/.test(expiry) || !Number.isFinite(Date.parse(expiry + "T00:00:00Z")) ||
        new Date(expiry + "T00:00:00Z").toISOString().slice(0, 10) !== expiry) {
      return { ready: false, status: "PENDING", error: "Enter the exact shared QQQ put expiry (YYYY-MM-DD); do not calculate a package with an unknown expiry." };
    }
    if (expiry < new Date().toISOString().slice(0, 10)) {
      return { ready: false, status: "PENDING", error: "This expiry is already past. Load a current chain or enter a valid future expiry." };
    }
    if (d.putRatioQuoteConfirmed !== true) {
      return { ready: false, status: "PENDING", error: "Manually compare both legs with the current broker chain, including quote timestamp, Bid/Ask and size, then confirm the quote check." };
    }
    if (d.putRatioStandardContractConfirmed !== true) {
      return { ready: false, status: "PENDING", error: "Confirm both legs use the standard QQQ 100-share deliverable. Adjusted or unknown contract terms are not supported by this multiplier." };
    }
    const budgetRaw = num(d.budgetUsd);
    if (budgetRaw === null || budgetRaw < 0) {
      return { ready: false, status: "PENDING", error: "Remaining Hub risk budget is unknown; first resolve the existing Hybrid reservation. Unknown is not zero." };
    }
    const spot = num(d.spot);
    const longK = num(d.longPutStrike);
    const shortK = num(d.shortPutStrike);
    const longAsk = num(d.longPutAsk);
    const shortBid = num(d.shortPutBid);
    const correctGeometry = direction === "short-heavy"
      ? longK > shortK && shortK > 0
      : shortK > longK && longK > 0;
    if (!(spot > 0) || !correctGeometry || !(longAsk > 0) || !(shortBid >= 0)) {
      return {
        ready: false, status: "PENDING",
        error: direction === "short-heavy"
          ? "N SHORT : 1 LONG needs the higher-strike Long Put (Long K > Short K > 0), a valid Long Ask, QQQ spot and exact expiry."
          : "N LONG : 1 SHORT needs the higher-strike Short Put (Short K > Long K > 0), a valid Long Ask, QQQ spot and exact expiry."
      };
    }
    const longPutQtyPerPackage = direction === "long-heavy" ? n : 1;
    const shortPutQtyPerPackage = direction === "short-heavy" ? n : 1;
    const legs = [
      { name: "Long QQQ put", right: "put", side: "BUY", qty: longPutQtyPerPackage, strike: longK, price: longAsk },
      { name: "Short QQQ put", right: "put", side: "SELL", qty: shortPutQtyPerPackage, strike: shortK, price: shortBid }
    ];
    const risk = terminalMaxLoss(legs, spot);
    if (!risk.ready) return { ...risk, status: "PENDING" };
    if (!(risk.riskUsd > 0)) {
      return {
        ready: false, status: "PENDING", debitUsd: risk.debitUsd, riskUsd: risk.riskUsd,
        error: "No positive finite expiry-loss amount was measured. Do not infer infinite capacity; verify quotes, multiplier and contract terms."
      };
    }
    const budgetUsd = Math.max(0, budgetRaw);
    const maxPackages = Math.floor((budgetUsd + EPS) / risk.riskUsd);
    let zeroSpotPnlUsd = -risk.debitUsd;
    for (const leg of legs) {
      zeroSpotPnlUsd += (leg.side === "BUY" ? 1 : -1) * num(leg.qty) * num(leg.strike) * MULTIPLIER;
    }
    const orientation = direction === "short-heavy" ? "N SHORT : 1 LONG" : "N LONG : 1 SHORT";
    return {
      ready: true,
      status: budgetUsd > 0 && maxPackages > 0 ? "RISK_GATE_PASS" : "RISK_GATE_BLOCK",
      putRatioN: n,
      putRatioDirection: direction,
      orientation,
      expiry,
      ratioLabel: orientation,
      longPutQtyPerPackage,
      shortPutQtyPerPackage,
      budgetUsd,
      riskUsd: risk.riskUsd,
      debitUsd: risk.debitUsd,
      zeroSpotPnlUsd,
      maxPackages,
      longPutContracts: longPutQtyPerPackage * maxPackages,
      shortPutContracts: shortPutQtyPerPackage * maxPackages,
      legs,
      worstExpiryPnlUsd: risk.worstExpiryPnlUsd,
      source: "HUB_QQQ_PUT_RATIO_DIRECTIONAL_BID_ASK_TERMINAL_PAYOFF_PROXY",
      reason: maxPackages > 0
        ? (direction === "short-heavy"
          ? "Research capacity only. N short puts against one long put leaves (N−1) net short puts below the lower strike when N>1. Loss can be substantial if QQQ falls toward zero."
          : "Research capacity only. The long-put backspread may benefit from a sharp fall, but can lose around the lower long strike and has time/volatility/assignment risks.")
          + " It is not included in the primary risk pool and does not authorize an order."
        : "RISK_GATE_BLOCK: the remaining research risk budget cannot cover one complete package at the observed-side expiry-loss estimate."
    };
  }

  function calculateRiskBank(input) {
    const d = input || {};
    const seed = Math.max(0, num(d.seedWinUsd, 0));
    const losses = Math.max(0, num(d.laterLossesUsd, 0));
    const netPnl = num(d.laterNetPnlUsd, 0);
    const mode = d.mode === "replenish-comparator" ? "REPLENISH_COMPARATOR" : "ISOLATED";
    const available = mode === "ISOLATED" ? Math.max(0, seed - losses) : Math.max(0, seed + netPnl);
    const candidateRisk = num(d.candidateRiskUsd);
    const eligible = candidateRisk !== null && candidateRisk >= 0 && available > 0 && candidateRisk <= available + EPS;
    return {
      mode, seedWinUsd: seed, laterLossesUsd: losses, laterNetPnlUsd: netPnl,
      availableRiskRightsUsd: available, candidateRiskUsd: candidateRisk,
      eligible, status: !available ? "NO_RISK_BANK" : eligible ? "RIGHTS_GATE_PASS" : "RIGHTS_GATE_BLOCK",
      isCash: false, isCollateral: false,
      reason: mode === "ISOLATED"
        ? "Isolated Universal Bank: start from one realized positive N>2 Risk-WIN; ignore later wins and let only subsequent losses consume the risk-right balance."
        : "REPLENISH is a contamination comparator, not the authoritative isolated rule. Bank dollars are research risk currency, not NAV, cash, margin or broker collateral."
    };
  }

  function blackScholesDelta(spot, strike, dte, iv, right) {
    if (![spot, strike, dte, iv].every(Number.isFinite) || spot <= 0 || strike <= 0 || dte <= 0 || iv <= 0) return null;
    const t = dte / 365;
    const sigma = iv > 2 ? iv / 100 : iv;
    const d1 = (Math.log(spot / strike) + (0.03 + 0.5 * sigma * sigma) * t) / (sigma * Math.sqrt(t));
    // Abramowitz-Stegun erf approximation, sufficient only for candidate ranking.
    const sign = d1 < 0 ? -1 : 1;
    const x = Math.abs(d1), a1 = 0.254829592, a2 = -0.284496736, a3 = 1.421413741, a4 = -1.453152027, a5 = 1.061405429, p = 0.3275911;
    const t0 = 1 / (1 + p * x);
    const erf = sign * (1 - (((((a5 * t0 + a4) * t0) + a3) * t0 + a2) * t0 + a1) * t0 * Math.exp(-x * x));
    const call = 0.5 * (1 + erf);
    return right === "put" ? call - 1 : call;
  }

  function normalizeRows(rows, right, spot, asOf, fallbackExpiry) {
    return (Array.isArray(rows) ? rows : []).map(row => {
      const rawExpiry = row.expiration ?? row.expiry ?? row.expirationDate ?? fallbackExpiry;
      const expiryMs = typeof rawExpiry === "number" ? (rawExpiry > 1e12 ? rawExpiry : rawExpiry * 1000) : Date.parse(rawExpiry || "");
      const dte = Number.isFinite(expiryMs) ? (expiryMs - Date.parse(String(asOf || new Date().toISOString()).slice(0, 10) + "T00:00:00Z")) / 86400000 : null;
      const strike = num(row.strike);
      const bid = num(row.bid);
      const ask = num(row.ask);
      const iv = num(row.impliedVolatility ?? row.iv);
      const rawDelta = num(row.delta);
      const delta = rawDelta !== null ? rawDelta : blackScholesDelta(spot, strike, dte, iv, right);
      return {
        right, strike, bid, ask, iv, dte, delta,
        deltaSource: rawDelta !== null ? "PROVIDER_DELTA" : delta !== null ? "BS_ESTIMATE" : "DELTA_UNAVAILABLE",
        expiry: Number.isFinite(expiryMs) ? new Date(expiryMs).toISOString().slice(0, 10) : null,
        contractSymbol: row.contractSymbol || row.contractSymbol || ""
      };
    }).filter(row => row.strike > 0 && Number.isFinite(row.bid) && Number.isFinite(row.ask) && row.bid >= 0 && row.ask >= row.bid);
  }

  function chooseChainLegs(payload, spot, asOf, targetDte = 45, putRatioDirection = "short-heavy") {
    const calls = normalizeRows(payload && payload.calls, "call", spot, asOf, payload && payload.expiry);
    const puts = normalizeRows(payload && payload.puts, "put", spot, asOf, payload && payload.expiry);
    const all = calls.concat(puts).filter(x => x.expiry && x.delta !== null);
    if (!(spot > 0) || !all.length) return { ready: false, error: "No usable current chain with strike, Bid/Ask, expiry and IV/Delta. Manual verification is required." };
    const expiries = [...new Set(all.map(x => x.expiry))].sort((a, b) => Math.abs((Date.parse(a) - Date.parse(String(asOf).slice(0, 10))) / 86400000 - targetDte) - Math.abs((Date.parse(b) - Date.parse(String(asOf).slice(0, 10))) / 86400000 - targetDte));
    const expiry = payload && payload.expiry ? String(payload.expiry).slice(0, 10) : expiries[0];
    const c = calls.filter(x => x.expiry === expiry && x.ask > 0 && x.delta > 0);
    const p = puts.filter(x => x.expiry === expiry && x.ask > 0 && x.delta < 0);
    function closest(rows, score, extra) {
      const pool = rows.filter(x => extra(x) && Number.isFinite(score(x)));
      pool.sort((a, b) => score(a) - score(b));
      return pool[0] || null;
    }
    const atm = closest(c, x => Math.abs(x.strike - spot), x => x.strike > 0);
    const short = atm && closest(c, x => Math.abs(Math.abs(x.delta) - 0.20), x => x.strike > atm.strike && x.delta <= 0.35);
    const wing = short && closest(c, x => Math.abs(Math.abs(x.delta) - 0.08), x => x.strike > short.strike && x.delta <= 0.18);
    let longPut;
    let shortPut;
    if (putRatioDirection === "long-heavy") {
      // Backspread: sell one higher-strike put, buy N lower-strike puts.
      shortPut = closest(p, x => Math.abs(Math.abs(x.delta) - 0.25), x => x.strike < spot && x.delta <= -0.10);
      longPut = shortPut && closest(p, x => Math.abs(Math.abs(x.delta) - 0.10), x => x.strike < shortPut.strike && x.delta >= -0.20);
    } else {
      // Short-heavy: buy one higher-strike put, sell N lower-strike puts.
      longPut = closest(p, x => Math.abs(Math.abs(x.delta) - 0.25), x => x.strike < spot && x.delta <= -0.10);
      shortPut = longPut && closest(p, x => Math.abs(Math.abs(x.delta) - 0.10), x => x.strike < longPut.strike && x.delta >= -0.20);
    }
    if (!atm || !short || !wing || !longPut || !shortPut) {
      return { ready: false, error: "Could not build every researched leg from this expiry's observable chain. Check quotes/IV and select manually; no substitute quote is fabricated.", expiry, deltaSource: [...c, ...p].some(x => x.deltaSource === "BS_ESTIMATE") ? "BS_ESTIMATE" : "PROVIDER_DELTA" };
    }
    return {
      ready: true, expiry,
      deltaSource: [atm, short, wing, longPut, shortPut].some(x => x.deltaSource === "BS_ESTIMATE") ? "BS_ESTIMATE" : "PROVIDER_DELTA",
      atm, short, wing, longPut, shortPut,
      warning: "Public-chain prices may be delayed/incomplete; Greek targets may be Black-Scholes estimates. Review every contract in the broker chain."
    };
  }

  root.HubOptionPackV1 = {
    MULTIPLIER, num, whole, calculateNavExitReferences, terminalMaxLoss, calculateRatioCall,
    calculateStateAdaptive, calculateStaggered, calculateShockGatedPut, calculatePutRatio,
    calculateRiskBank, blackScholesDelta, chooseChainLegs, ratioCallLegs, stateAdaptiveLegs
  };
  if (typeof module !== "undefined" && module.exports) module.exports = root.HubOptionPackV1;
})(typeof globalThis !== "undefined" ? globalThis : this);
