(function (root) {
  "use strict";
  const finite = value => value !== null && value !== undefined && value !== "" && Number.isFinite(Number(value));
  const n = value => finite(value) ? Number(value) : null;
  const dateMs = value => {
    if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
    const ms = Date.parse(value + "T00:00:00Z");
    return Number.isFinite(ms) && new Date(ms).toISOString().slice(0, 10) === value ? ms : null;
  };
  const daysBetween = (from, to) => {
    const a = dateMs(from), b = dateMs(to);
    if (a === null || b === null || b < a) return null;
    return Math.floor((b - a) / 86400000);
  };
  function stopRiskFromEntry(row) {
    const entry=n(row.entryPrice), stop=n(row.stopMarkPrice), qty=n(row.qty), mult=n(row.multiplier);
    if (entry===null||stop===null||qty===null||mult===null||qty<=0||mult<=0) return null;
    let perUnit=null;
    if(row.template==="QQQ_CORE"&&stop<entry) perUnit=entry-stop;
    else if(row.template==="VXX_SHORT_STOCK"&&stop>entry) perUnit=stop-entry;
    else if(row.kind==="CREDIT_VERTICAL"&&stop>entry) perUnit=stop-entry;
    return perUnit!==null&&perUnit>0?perUnit*qty*mult:null;
  }
  function stopGapFromMark(row) {
    const mark=n(row.markPrice),stop=n(row.stopMarkPrice),qty=n(row.qty),mult=n(row.multiplier);
    if(mark===null||stop===null||qty===null||mult===null)return null;
    if(row.template==="QQQ_CORE")return Math.max(0,mark-stop)*qty*mult;
    if(row.template==="VXX_SHORT_STOCK"||row.kind==="CREDIT_VERTICAL")return Math.max(0,stop-mark)*qty*mult;
    return null;
  }
  function rewardToTarget(row) {
    const mark=n(row.markPrice),target=n(row.targetMarkPrice),qty=n(row.qty),mult=n(row.multiplier);
    if(mark===null||target===null||qty===null||mult===null)return null;
    if(row.template==="QQQ_CORE")return Math.max(0,target-mark)*qty*mult;
    if(row.template==="VXX_SHORT_STOCK"||row.kind==="CREDIT_VERTICAL")return Math.max(0,mark-target)*qty*mult;
    return null;
  }
  function evaluate(row, context={}) {
    row=row||{};
    const today=context.today||new Date().toISOString().slice(0,10);
    const nav=n(context.nav),pnl=n(row.unrealizedPnl),mark=n(row.markPrice),age=daysBetween(row.entryDate,today);
    const expiryMs=dateMs(row.expiry),todayMs=dateMs(today);
    const dte=row.kind==="CREDIT_VERTICAL"&&expiryMs!==null&&todayMs!==null?Math.floor((expiryMs-todayMs)/86400000):null;
    const configuredRisk=n(row.riskBudgetUsd),stopRisk=stopRiskFromEntry(row);
    const optionExpiryRisk=row.kind==="CREDIT_VERTICAL"&&row.termsComplete===true&&row.adjustedDetected!==true&&n(row.maxLossPerPackage)>0&&n(row.qty)>0
      ?n(row.maxLossPerPackage)*n(row.qty):null;
    const riskBudgetUsd=configuredRisk>0?configuredRisk:stopRisk!==null?stopRisk:optionExpiryRisk;
    const riskBudgetSource=configuredRisk>0?"OPERATOR-ENTERED RISK BUDGET":stopRisk!==null?"DERIVED FROM ENTRY → STOP MARK":optionExpiryRisk!==null?"DERIVED STANDARD VERTICAL EXPIRY MAX LOSS":"UNKNOWN";
    const pnlR=pnl!==null&&riskBudgetUsd!==null&&riskBudgetUsd>0?pnl/riskBudgetUsd:null;
    const pnlPctNav=pnl!==null&&nav!==null&&nav>0?pnl/nav*100:null;
    const riskBudgetPctNav=riskBudgetUsd!==null&&nav!==null&&nav>0?riskBudgetUsd/nav*100:null;
    const elapsed=age!==null&&age>0?age:null;
    const pnlPerCalendarDay=pnl!==null&&elapsed!==null?pnl/elapsed:null;
    const rPerCalendarDay=pnlR!==null&&elapsed!==null?pnlR/elapsed:null;
    const riskToStopUsd=stopGapFromMark(row),targetRewardUsd=rewardToTarget(row);
    const rewardRiskRatio=targetRewardUsd!==null&&riskToStopUsd!==null&&riskToStopUsd>0?targetRewardUsd/riskToStopUsd:null;
    const daysToTimeLimit=n(row.maxHoldDays)!==null&&age!==null?n(row.maxHoldDays)-age:null;
    const rewardPerRemainingDay=targetRewardUsd!==null&&daysToTimeLimit!==null&&daysToTimeLimit>0?targetRewardUsd/daysToTimeLimit:null;
    const lossRiskUsedPct=pnl!==null&&pnl<0&&riskBudgetUsd!==null&&riskBudgetUsd>0?-pnl/riskBudgetUsd*100:0;
    const freshLabel=["LIVE ≤15M","DELAYED ≤72H","EOD ≤96H"].includes(String(row.markFreshness||""));
    const pnlQualityReady=pnl!==null&&mark!==null&&row.staleMark!==true&&row.pnlStatus&&String(row.pnlStatus).startsWith("GROSS UNREALIZED P&L")&&freshLabel;
    const hasPriceRule=n(row.stopMarkPrice)!==null||n(row.targetMarkPrice)!==null||n(row.profitTargetR)!==null;
    const priceRulePending=hasPriceRule&&!pnlQualityReady;
    const stopBreached=pnlQualityReady&&n(row.stopMarkPrice)!==null&&(
      row.template==="QQQ_CORE"?mark<=n(row.stopMarkPrice):
      row.template==="VXX_SHORT_STOCK"||row.kind==="CREDIT_VERTICAL"?mark>=n(row.stopMarkPrice):false);
    const lossBudgetBreached=pnlQualityReady&&riskBudgetUsd!==null&&riskBudgetUsd>0&&pnl<=-riskBudgetUsd;
    const targetPriceReached=pnlQualityReady&&n(row.targetMarkPrice)!==null&&(
      row.template==="QQQ_CORE"?mark>=n(row.targetMarkPrice):
      row.template==="VXX_SHORT_STOCK"||row.kind==="CREDIT_VERTICAL"?mark<=n(row.targetMarkPrice):false);
    const targetR=n(row.profitTargetR);
    const profitTargetRReached=pnlQualityReady&&targetR!==null&&targetR>0&&pnlR!==null&&pnlR>=targetR;
    const timeLimitReached=n(row.maxHoldDays)!==null&&age!==null&&age>=n(row.maxHoldDays);
    const expiryReviewDte=n(row.expiryReviewDte),expired=dte!==null&&dte<0;
    const expiryWindow=dte!==null&&expiryReviewDte!==null&&dte>=0&&dte<=expiryReviewDte;
    const marketState=context.marketState||null;
    const verifiedRiskOff=marketState&&marketState.blocked!==true&&marketState.riskOff===true;
    const riskSensitive=row.template==="VXX_SHORT_STOCK"||row.kind==="CREDIT_VERTICAL";
    const regimeReview=Boolean(verifiedRiskOff&&riskSensitive);
    const stopMissing=n(row.stopMarkPrice)===null;
    const timeRuleMissing=n(row.maxHoldDays)===null&&!(row.kind==="CREDIT_VERTICAL"&&expiryReviewDte!==null);
    const entryDateMissing=age===null,riskUnitMissing=riskBudgetUsd===null||!(riskBudgetUsd>0);
    let action="MONITOR · NO RULE TRIGGERED";
    let reason="Configured rules are not triggered. P&L pace is descriptive; fast profit alone does not force a large trim.";
    if(stopBreached){action="STOP MARK BREACHED · HUMAN REVIEW";reason="The current marked price crossed the configured stop. Verify the live broker quote, fillability and quantity before any manual exit decision.";}
    else if(lossBudgetBreached){action="RISK BUDGET BREACHED · HUMAN REVIEW";reason="Gross unrealized loss has reached or exceeded the configured/derived risk budget. This is a review gate, not an order.";}
    else if(regimeReview){action="REGIME RISK REVIEW · HUMAN REVIEW";reason="The verified market gate is risk-off. Review short-stock / credit-option exposure before treating profit pace or time decay as the primary decision.";}
    else if(timeLimitReached){action="TIME LIMIT REACHED · HUMAN REVIEW";reason="The operator-defined calendar-day holding limit has been reached. Refresh the mark and decide whether to exit, trim, or explicitly reset the thesis/time limit.";}
    else if(expired){action="PAST EXPIRY · ASSIGNMENT / POSITION CHECK";reason="Recorded option expiry is in the past. Reconcile assignment, exercise and any resulting stock position; do not treat the option as an unexpired live mark.";}
    else if(expiryWindow){action="EXPIRY REVIEW WINDOW · HUMAN REVIEW";reason="DTE is at or inside the operator-defined expiry-review threshold. Check assignment, pin and weekend/gap risk.";}
    else if(priceRulePending){action="PENDING · FRESH VERIFIED MARK REQUIRED";reason="A configured price/profit rule cannot be evaluated from this row's current mark quality. Refresh the quote and verify its source before interpreting a trigger.";}
    else if(targetPriceReached||profitTargetRReached){action="PROFIT REVIEW THRESHOLD REACHED";reason="An explicit target mark or target-R threshold has been reached. Compare remaining reward, loss-to-stop, time and market regime; this is not an automatic full close.";}
    else if(riskUnitMissing){action="PLAN INCOMPLETE · RISK UNIT UNKNOWN";reason="Enter a risk budget or valid stop mark. For standard credit verticals, expiry-risk reference is derived only when terms are complete.";}
    else if(stopMissing){action="PLAN INCOMPLETE · STOP MARK NOT SET";reason="Record a stop/exit mark. A dollar risk unit alone does not identify the price where the trade thesis is invalidated.";}
    else if(timeRuleMissing||entryDateMissing){action="PLAN INCOMPLETE · TIME RULE NOT SET";reason="Enter a valid entry date and calendar-day holding limit (and optionally an option expiry-review DTE) so profit can be compared with time consumed.";}
    return {
      action,reason,elapsedCalendarDays:age,dte,daysToTimeLimit,riskBudgetUsd,riskBudgetSource,riskBudgetPctNav,
      pnlPctNav,pnlR,pnlPerCalendarDay,rPerCalendarDay,lossRiskUsedPct,riskToStopUsd,targetRewardUsd,rewardRiskRatio,rewardPerRemainingDay,
      pnlQualityReady,priceRulePending,stopBreached,lossBudgetBreached,targetPriceReached,profitTargetRReached,timeLimitReached,expiryWindow,regimeReview,
      planComplete:!riskUnitMissing&&!stopMissing&&!timeRuleMissing&&!entryDateMissing,
      pacePolicy:"P&L/calendar-day and R/calendar-day are descriptive measures. Fast profit alone does not force a large trim; assess target, stop, time, current reward-vs-risk, quote quality and regime together."
    };
  }
  root.PositionManagementV1={evaluate,stopRiskFromEntry,stopGapFromMark,rewardToTarget};
  if(typeof module!=="undefined"&&module.exports)module.exports=root.PositionManagementV1;
})(typeof globalThis!=="undefined"?globalThis:this);
