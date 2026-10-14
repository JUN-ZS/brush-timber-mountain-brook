(function (root) {
  "use strict";
  const EVIDENCE = Object.freeze({
    rollingFloor:{id:"ROLLING_10Y_FLOOR_REPORT",replayCount:153,nonLossRatePct:100,terminalQ05Multiple:2.0571,worstTerminalMultiple:1.9801,worstMaxDrawdownPct:-32.6,asOf:"2026-09-04",interpretation:"Historical replay output; not a future success probability."},
    qqqFarCallOverlay:{id:"QQQ_FAR_CALL_MEASUREMENT_SCORECARD_RUN148",scenarioPasses:0,scenarioCount:16,baseClosedPnlUsd:-5646,lastPairedNavGapUsd:-5552,sourceEnd:"2025-12-15",missingTerminalSessions:11,accuracy:"BLOCKED",generality:"NOT DEMONSTRATED",integration:"FAILS CURRENT BASE SCREEN"},
    vxxCallCredit:{id:"QQQ_HYBRID_PROFIT_TREND_REPLAY_V1_README",wins:41,closes:49,losses:8,realizedPnlUsd:7178,probabilityClass:"MODEL_ONLY",pricingModel:"DERIVED_BS_VIX",notOpra:true,windowStart:"2018-03-01",windowEnd:"2026-09-04"},
    hybridReplay:{windowStart:"2018-03-01",windowEnd:"2026-09-04",sessions:2141,baselineCagrPct:13.70,baselineMaxDrawdownPct:-23.02,deployV11CagrPct:13.92,deployV11MaxDrawdownPct:-22.85,pricingModel:"DERIVED_BS_VIX",notOpra:true}
  });
  function n(value){if(value===null||value===undefined||value==="")return null;const x=typeof value==="number"?value:Number(String(value).trim());return Number.isFinite(x)?x:null;}
  function clamp(x,lo,hi){return Math.max(lo,Math.min(hi,x));}
  function pctRange(x){return x!==null&&x>=0&&x<=100;}
  function ev(p,gain,loss,cost){if(![p,gain,loss,cost].every(Number.isFinite))return null;return p*gain-(1-p)*loss-cost;}
  function wilson95(wins,trials){
    if(!Number.isInteger(wins)||!Number.isInteger(trials)||trials<1||wins<0||wins>trials)return null;
    const z=1.959963984540054,z2=z*z,phat=wins/trials,denom=1+z2/trials;
    const center=(phat+z2/(2*trials))/denom;
    const radius=z*Math.sqrt((phat*(1-phat)+z2/(4*trials))/trials)/denom;
    return {lowPct:clamp(center-radius,0,1)*100,basePct:phat*100,highPct:clamp(center+radius,0,1)*100,method:"WILSON_95_BINOMIAL_APPROX"};
  }
  function strategyLabel(key){return ({qqqShares:"QQQ CORE shares",vxxShortShares:"VXX SHORT shares",qqqCallSpreads:"QQQ CALL-CREDIT primary leg",vxxCallSpreads:"VXX CALL-CREDIT primary leg",qqqFarCallOverlay:"QQQ FAR CALL incremental research overlay",deploymentTiming:"Rolling 10Y / long-horizon deployment timing",custom:"Other / hypothetical candidate"})[key]||String(key||"UNKNOWN");}
  function mainRoute(row,candidateKey){
    if(!row)return null;
    const current=n(row.current),target=n(row.target),capacity=n(row.capacity),action=String(row.action||row.status||"PENDING").toUpperCase();
    const quantitiesKnown=current!==null&&target!==null;
    const blocked=["BLOCKED","BLOCK","PENDING","WAIT FOR DATA","PLAN INCOMPLETE","INCOMPLETE","UNKNOWN"].some(flag=>action.includes(flag));
    const maxAllowedAdd=!quantitiesKnown||blocked?null:action==="ADD"?Math.max(0,target-current):0;
    const maxAllowedTrim=!quantitiesKnown||blocked?null:action==="REDUCE"?Math.max(0,current-target):0;
    return {candidateKey,current,target,capacity,action,maxAllowedAdd,maxAllowedTrim,status:row.status||null,reason:row.reason||""};
  }
  function evaluate(input){
    const i=input&&typeof input==="object"?input:{}, candidateKey=String(i.candidateKey||"custom"),candidateLabel=strategyLabel(candidateKey),lens=i.lens==="HOLD"?"HOLD":"ADD";
    const nav=n(i.nav),quantity=n(i.quantity),horizonDays=n(i.horizonDays),reward=n(i.rewardUsd),loss=n(i.lossUsd),cost=n(i.costUsd),costStress=n(i.costStressUsd);
    const alternativeEVTotalUsd=n(i.alternativeEVTotalUsd),alternativeLabel=String(i.alternativeLabel||"").trim();
    const warnings=[],market=i.market&&typeof i.market==="object"?i.market:null,route=mainRoute(i.mainRow,candidateKey);
    const roadmap=i.deploymentRoadmap&&typeof i.deploymentRoadmap==="object"?i.deploymentRoadmap:null;
    const positionTemplateFor={qqqShares:"QQQ_CORE",vxxShortShares:"VXX_SHORT_STOCK",qqqCallSpreads:"QQQ_CALL_CREDIT",vxxCallSpreads:"VXX_CALL_CREDIT"};
    const relevantTemplates=positionTemplateFor[candidateKey]?[positionTemplateFor[candidateKey]]:[];
    const heldPositions=Array.isArray(i.positionManagementRows)?i.positionManagementRows.filter(x=>relevantTemplates.includes(x.template)):[];
    const heldReviews=heldPositions.filter(x=>!String(x.action||"").startsWith("MONITOR "));
    const axes={accuracy:String(i.accuracy||"UNREVIEWED"),generality:String(i.generality||"NOT_DEMONSTRATED"),integration:String(i.integration||"NOT_TESTED")};
    const evidenceNote=String(i.evidenceNote||"").trim(),probabilityMethod=String(i.probabilityMethod||"MANUAL"),probabilityBasis=String(i.probabilityBasis||"HYPOTHESIS");
    let pLow=n(i.probabilityLowPct),pBase=n(i.probabilityBasePct),pHigh=n(i.probabilityHighPct),sampleSize=null,empirical=null,probabilityMethodLabel="Manual low/base/high scenario",probabilityBasisLabel="Operator hypothesis";
    if(probabilityMethod==="EMPIRICAL"){
      const wins=n(i.wins),trials=n(i.trials);
      if(wins!==null&&trials!==null&&Number.isInteger(wins)&&Number.isInteger(trials)){
        empirical=wilson95(wins,trials);
        if(empirical){pLow=empirical.lowPct;pBase=empirical.basePct;pHigh=empirical.highPct;sampleSize=trials;probabilityMethodLabel="Observed fraction + nominal 95% Wilson interval";}
        else pLow=pBase=pHigh=null;
      }else pLow=pBase=pHigh=null;
    }else sampleSize=n(i.trials);
    if(probabilityBasis==="MODEL_REPLAY")probabilityBasisLabel="Repository / external model replay";
    else if(probabilityBasis==="INDEPENDENT_OOS")probabilityBasisLabel="Operator-identified independent chronological holdout / real outcomes";
    if(probabilityMethod==="EMPIRICAL"&&empirical&&sampleSize!==null&&sampleSize<30)warnings.push("Sample is below the repo contract's 30-trade descriptive floor; do not claim an edge.");
    if(probabilityMethod==="EMPIRICAL"&&empirical)warnings.push("Wilson interval assumes binomial trials; overlapping positions, model-generated trades and correlated regimes can invalidate its interpretation.");
    if(probabilityMethod==="EMPIRICAL"&&empirical&&probabilityBasis==="MODEL_REPLAY")warnings.push("A model-generated win fraction is not an observed real-execution probability.");
    if(probabilityBasis==="INDEPENDENT_OOS")warnings.push("Holdout provenance, fill quality and independence are operator-attested; the APP does not authenticate them.");

    const payoffComplete=reward!==null&&reward>0&&loss!==null&&loss>0&&cost!==null&&cost>=0&&costStress!==null&&costStress>=0;
    const qtyComplete=quantity!==null&&Number.isInteger(quantity)&&quantity>=1;
    const timeComplete=horizonDays!==null&&Number.isInteger(horizonDays)&&horizonDays>=1&&horizonDays<=3650;
    const probComplete=pBase!==null&&pctRange(pBase)&&(pLow===null||pctRange(pLow))&&(pHigh===null||pctRange(pHigh))&&!(pLow!==null&&pHigh!==null&&(pLow>pBase||pBase>pHigh));
    const breakEven=payoffComplete?(loss+cost)/(reward+loss)*100:null;
    const baseEV=payoffComplete&&pctRange(pBase)?ev(pBase/100,reward,loss,cost):null;
    const adverseEV=payoffComplete&&pctRange(pLow)?ev(pLow/100,reward,loss,cost+costStress):null;
    const highEV=payoffComplete&&pctRange(pHigh)?ev(pHigh/100,reward,loss,cost):null;
    const baseTotal=baseEV!==null&&qtyComplete?baseEV*quantity:null,adverseTotal=adverseEV!==null&&qtyComplete?adverseEV*quantity:null,highTotal=highEV!==null&&qtyComplete?highEV*quantity:null;
    const alternativeComplete=alternativeEVTotalUsd!==null&&Number.isFinite(alternativeEVTotalUsd)&&alternativeLabel.length>=3;
    const incrementalEVBase=baseTotal!==null&&alternativeComplete?baseTotal-alternativeEVTotalUsd:null;
    const incrementalEVAdverse=adverseTotal!==null&&alternativeComplete?adverseTotal-alternativeEVTotalUsd:null;
    const incrementalEVHigh=highTotal!==null&&alternativeComplete?highTotal-alternativeEVTotalUsd:null;
    const incrementalEVPerDay=incrementalEVBase!==null&&timeComplete?incrementalEVBase/horizonDays:null;
    const incrementalEVPctNav=incrementalEVBase!==null&&nav!==null&&nav>0?incrementalEVBase/nav*100:null;
    const perDay=baseTotal!==null&&timeComplete?baseTotal/horizonDays:null,riskTotal=loss!==null&&loss>0&&qtyComplete?loss*quantity:null;
    const riskPctNav=riskTotal!==null&&nav!==null&&nav>0?riskTotal/nav*100:null,evPctNav=baseTotal!==null&&nav!==null&&nav>0?baseTotal/nav*100:null;
    const evPerRisk=baseEV!==null&&loss!==null&&loss>0?baseEV/loss:null,rr=payoffComplete?reward/loss:null,margin=pBase!==null&&breakEven!==null?pBase-breakEven:null;
    const rangeComplete=pctRange(pLow)&&pctRange(pBase)&&pctRange(pHigh),adversePass=adverseEV!==null&&adverseEV>0,basePass=baseEV!==null&&baseEV>0;
    const probabilityMissing=probabilityMethod==="EMPIRICAL"?(n(i.wins)===null||n(i.trials)===null):(pLow===null||pBase===null||pHigh===null);
    const routeAllowsAdd=!!route&&route.action==="ADD"&&route.maxAllowedAdd!==null&&route.maxAllowedAdd>0,routeCanHold=!!route&&route.current!==null&&route.current>0;
    const qtyOverTarget=lens==="ADD"&&routeAllowsAdd&&qtyComplete&&quantity>route.maxAllowedAdd;
    const addNotAllowed=lens==="ADD"&&!["custom","qqqFarCallOverlay","deploymentTiming"].includes(candidateKey)&&(!route||!routeAllowsAdd);
    const holdConflictsWithReduce=lens==="HOLD"&&route&&route.action==="REDUCE";
    const qqqOverlayLocked=candidateKey==="qqqFarCallOverlay",noSizingRoute=!route&&["custom","deploymentTiming"].includes(candidateKey);
    const riskNature=candidateKey==="vxxShortShares"?"UNBOUNDED":String(i.riskNature||"STRESS_ONLY");
    const floorBreached=roadmap&&roadmap.status==="FLOOR_BREACH";
    const independentEvidenceOk=probabilityBasis==="INDEPENDENT_OOS"&&probabilityMethod==="EMPIRICAL"&&sampleSize!==null&&sampleSize>=30&&empirical!==null&&evidenceNote.length>=12&&axes.accuracy==="PASS"&&axes.generality==="PASS"&&axes.integration==="PASS";
    let status="BASELINE_PENDING",nextAction="Complete payoff, cost, time and evidence inputs; no default success probability or alternative value is inserted.";
    if(!market||market.blocked===true){status="MARKET_BLOCKED";nextAction="BLOCK: the main market-data gate is blocked or unavailable. Scenario EV cannot authorize deployment.";}
    else if(qqqOverlayLocked){status="QQQ_OVERLAY_LOCKBOX";nextAction="BLOCK promotion of the incremental QQQ FAR CALL overlay. Accuracy / Generality / Integration lockbox failures cannot be overridden by a positive scenario EV.";}
    else if(lens==="ADD"&&floorBreached){status="CLOCK_FLOOR_BREACH";nextAction="BLOCK new deployment while NAV is below the CLOCK Floor. Reconcile NAV, cash flows, holdings and pending orders; the floor is a review trigger, not an automatic sell.";}
    else if(lens==="ADD"&&market.allowNew!==true){status="ADD_NOT_ALLOWED";nextAction="BLOCK new exposure: the current verified market state does not permit new Carry risk. QQQ Core and seller legs cannot use an EV score to bypass this gate.";}
    else if(lens==="ADD"&&(addNotAllowed||qtyOverTarget)){status=qtyOverTarget?"QTY_OVER_TARGET":"ADD_NOT_ALLOWED";nextAction=qtyOverTarget?"BLOCK: proposed units exceed the current main-engine ADD gap. EV does not enlarge capacity.":"NO ADD: the main sizing row is not in ADD state or has no known positive add gap. Respect HOLD / REDUCE / BLOCK / PENDING.";}
    else if(lens==="HOLD"&&heldReviews.length){status="POSITION_REVIEW_PRIORITY";nextAction="The registered position-management meter flags this holding for review before a new hold-vs-exit EV can be actioned: "+heldReviews.map(x=>String(x.label||x.template)+": "+String(x.action||"REVIEW")).join("; ")+". EV remains counterfactual and cannot override the position-specific gate.";}
    else if(holdConflictsWithReduce){status="HOLD_CONFLICTS_WITH_REDUCE";nextAction="The main sizing engine requests REDUCE. A positive forward EV is counterfactual and cannot cancel the current reduction route.";}
    else if(lens==="HOLD"&&!routeCanHold&&!["custom","deploymentTiming","qqqFarCallOverlay"].includes(candidateKey)){status="ADD_NOT_ALLOWED";nextAction="No positive current exposure is available to score as HOLD. Reconcile quantities, or change the lens to ADD.";}
    else if(!payoffComplete||!qtyComplete||!timeComplete){status="NEEDS_PAYOFF";nextAction="Enter positive gain/loss per unit, non-negative base/adverse costs, integer quantity and calendar-day horizon. Missing values remain PENDING.";}
    else if(probabilityMissing){status="NEEDS_PROBABILITY";nextAction="PENDING: enter low / base / high probability, or provide wins and total outcomes. Missing probability evidence is not a 0% probability or an invalid range.";}
    else if(!probComplete||pBase===null){status="INVALID_RANGE";nextAction="Probability inputs must be within [0,100], with low ≤ base ≤ high. Correct the invalid range; do not use a blank as zero.";}
    else if(riskNature==="UNBOUNDED"){status="UNBOUNDED_TAIL";nextAction="This candidate has structurally unbounded/unknown tail risk. Scenario EV can be inspected, but a finite entered stress loss is not a maximum-loss cap.";}
    else if(noSizingRoute){status="NO_SIZING_ROUTE";nextAction="Scenario only: this candidate has no primary sizing route. It cannot become a portfolio allocation until a capacity model exists.";}
    else if(probabilityBasis==="MODEL_REPLAY"){status="MODEL_ONLY";nextAction=basePass?"Model EV is positive under entered assumptions, but model win frequency is not a real-execution probability. No trade-ready conclusion.":"The model scenario does not pass the entered base-EV screen; keep it research/scenario only.";}
    else if(probabilityBasis!=="INDEPENDENT_OOS"){status="HYPOTHESIS_ONLY";nextAction=basePass?"Base EV is positive under the scenario, but the success probability remains a hypothesis; relative value versus waiting/another strategy is not authenticated.":"Hypothetical base EV is non-positive. Wait or remeasure; no evidence-backed future probability exists.";}
    else if(!independentEvidenceOk){status="EVIDENCE_INCOMPLETE";nextAction="PENDING: at least 30 counted outcomes, a source/reference note and PASS on Accuracy, Generality and Integration are required. UI attestations do not authenticate evidence.";}
    else if(!basePass){status="NEGATIVE_EXPECTED_VALUE";nextAction="Base expected value is zero or negative after entered costs. Under this payoff/probability specification, do not add exposure.";}
    else if(!alternativeComplete){status="ALTERNATIVE_VALUE_PENDING";nextAction="EV is positive under supplied assumptions, but the waiting / alternative path has no priced expected value for the same capital and horizon. Enter a sourced comparator; do not silently equate WAIT with $0.";}
    else if(incrementalEVBase<=0){status="NEGATIVE_INCREMENTAL_VALUE";nextAction="The candidate's base expected value is no better than the named waiting / alternative benchmark. Prefer WAIT / compare another candidate unless other objectives justify review.";}
    else if(!rangeComplete){status="NEEDS_PROBABILITY";nextAction="PENDING: the low / base / high probability range is incomplete, so robustness versus the comparator cannot be assessed.";}
    else if(!adversePass||incrementalEVAdverse===null||incrementalEVAdverse<=0){status="FRAGILE_EXPECTED_VALUE";nextAction="Base EV beats the comparator, but the low-probability / adverse-cost case fails to beat it. Relative value is fragile; do not call it robust.";}
    else{status="ELIGIBLE_FOR_HUMAN_REVIEW";nextAction="Evidence, current sizing route, explicit alternative and adverse case pass the configured screen. ELIGIBLE FOR HUMAN REVIEW only—not trade approval, strategy promotion or an order.";}
    if(lens==="HOLD"&&heldPositions.length===0&&routeCanHold)warnings.push("No matching registered position row: current units exist in the sizing input, but stop / mark / age / DTE management evidence is not linked for this holding.");
    if(floorBreached&&lens!=="ADD")warnings.push("CLOCK Floor is breached. This EV remains a scenario; the long-horizon controller calls for NAV / cash-flow reconciliation and human review.");
    const candidateEvidence=qqqOverlayLocked?{accuracy:EVIDENCE.qqqFarCallOverlay.accuracy,generality:EVIDENCE.qqqFarCallOverlay.generality,integration:EVIDENCE.qqqFarCallOverlay.integration,sourceId:EVIDENCE.qqqFarCallOverlay.id}
      :probabilityBasis==="MODEL_REPLAY"&&candidateKey==="vxxCallSpreads"?{accuracy:"BLOCKED · MODEL_ONLY / NOT OPRA",generality:"NOT DEMONSTRATED",integration:"NOT PROVEN BY ISOLATED ATTRIBUTION",sourceId:EVIDENCE.vxxCallCredit.id}
      :{...axes,sourceId:evidenceNote||null,operatorAttested:probabilityBasis==="INDEPENDENT_OOS"};
    if(riskNature==="UNBOUNDED")warnings.push("VXX short-stock risk is structurally unbounded; entered stress loss cannot cap the tail.");
    if(candidateKey==="qqqCallSpreads")warnings.push("The isolated incremental FAR CALL overlay failed its current research screen. This is not a full-composite return replay and does not prove primary-leg future probability.");
    if(baseEV!==null&&baseEV>0&&adverseEV!==null&&adverseEV<=0)warnings.push("Base EV is positive but low-probability plus adverse-cost EV is non-positive.");
    if(riskTotal!==null&&nav!==null&&nav>0&&riskTotal/nav>0.05)warnings.push("Entered scenario loss exceeds 5% of NAV; this is a project materiality warning, not a universal finance law.");
    return {
      status,statusLabel:status,nextAction,candidateKey,candidateLabel,lens,navUsd:nav,quantity:qtyComplete?quantity:null,horizonDays:timeComplete?horizonDays:null,
      rewardUsd:reward,lossUsd:loss,costUsd:cost,costStressUsd:costStress,riskNature,riskNatureLabel:riskNature==="UNBOUNDED"?"UNBOUNDED TAIL · stress amount is not a cap":riskNature==="DEFINED"?"DEFINED STOP / MAX-LOSS ASSUMPTION":"STRESS ONLY · not a guaranteed loss cap",
      probabilityMethod,probabilityMethodLabel,probabilityBasis,probabilityBasisLabel,probabilityLowPct:pctRange(pLow)?pLow:null,probabilityBasePct:pctRange(pBase)?pBase:null,probabilityHighPct:pctRange(pHigh)?pHigh:null,
      sampleSize,empiricalInterval:empirical,breakEvenProbabilityPct:breakEven,expectedValueBaseUsd:baseEV,expectedValueAdverseUsd:adverseEV,expectedValueHighUsd:highEV,
      expectedValueBaseTotalUsd:baseTotal,expectedValueAdverseTotalUsd:adverseTotal,expectedValueHighTotalUsd:highTotal,
      alternativeEVTotalUsd:alternativeComplete?alternativeEVTotalUsd:null,alternativeLabel:alternativeLabel||null,alternativeComplete,
      incrementalValueBaseUsd:incrementalEVBase,incrementalValueAdverseUsd:incrementalEVAdverse,incrementalValueHighUsd:incrementalEVHigh,
      incrementalValuePerCalendarDayUsd:incrementalEVPerDay,incrementalValuePctNav:incrementalEVPctNav,
      totalCostBaseUsd:cost!==null&&qtyComplete?cost*quantity:null,totalCostAdverseUsd:cost!==null&&costStress!==null&&qtyComplete?(cost+costStress)*quantity:null,
      expectedValuePerCalendarDayUsd:perDay,expectedValueBasePerRisk:evPerRisk,rewardRiskRatio:rr,probabilityMarginPct:margin,
      scenarioLossTotalUsd:riskTotal,scenarioRiskPctNav:riskPctNav,expectedValuePctNav:evPctNav,robustPositive:rangeComplete&&adversePass&&basePass,
      adverseProbabilityPct:pctRange(pLow)?pLow:null,favorableProbabilityPct:pctRange(pHigh)?pHigh:null,mainRoute:route,quantityOverTarget:qtyOverTarget,independentEvidenceOk,axes:candidateEvidence,evidenceNote:evidenceNote||null,warnings,
      researchEvidence:{rollingFloor:EVIDENCE.rollingFloor,qqqFarCallOverlay:EVIDENCE.qqqFarCallOverlay,vxxCallCredit:EVIDENCE.vxxCallCredit,hybridReplay:EVIDENCE.hybridReplay},
      deploymentRoadmap:roadmap?{status:roadmap.status||null,floorUsd:roadmap.floorUsd??null,floorGapUsd:roadmap.floorGapUsd??null,elapsedMonths:roadmap.elapsedMonths??null,remainingMonths:roadmap.remainingMonths??null}:null,
      heldPositions,heldPositionReviewCount:heldReviews.length,
      waitReferenceExpectedValueUsd:null,futureCashYieldIncluded:false,brokerOrders:false
    };
  }
  const api={evaluate,wilson95,EVIDENCE};
  if(typeof module!=="undefined"&&module.exports)module.exports=api;
  if(root)root.DecisionValueEngineV1=api;
})(typeof window!=="undefined"?window:(typeof globalThis!=="undefined"?globalThis:this));
