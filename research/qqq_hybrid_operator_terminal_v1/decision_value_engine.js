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
    const maxAllowedAdd=action==="ADD"&&current!==null&&target!==null?Math.max(0,target-current):0;
    const maxAllowedTrim=action==="REDUCE"&&current!==null&&target!==null?Math.max(0,current-target):(action==="BLOCKED"?null:0);
    return {candidateKey,current,target,capacity,action,maxAllowedAdd,maxAllowedTrim,status:row.status||null,reason:row.reason||""};
  }
  function evaluate(input){
    const i=input&&typeof input==="object"?input:{}, candidateKey=String(i.candidateKey||"custom"),candidateLabel=strategyLabel(candidateKey),lens=i.lens==="HOLD"?"HOLD":"ADD";
    const nav=n(i.nav),quantity=n(i.quantity),horizonDays=n(i.horizonDays),reward=n(i.rewardUsd),loss=n(i.lossUsd),cost=n(i.costUsd),costStress=n(i.costStressUsd);
    const warnings=[],market=i.market&&typeof i.market==="object"?i.market:null,route=mainRoute(i.mainRow,candidateKey);
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
    const perDay=baseTotal!==null&&timeComplete?baseTotal/horizonDays:null,riskTotal=loss!==null&&loss>0&&qtyComplete?loss*quantity:null;
    const riskPctNav=riskTotal!==null&&nav!==null&&nav>0?riskTotal/nav*100:null,evPctNav=baseTotal!==null&&nav!==null&&nav>0?baseTotal/nav*100:null;
    const evPerRisk=baseEV!==null&&loss!==null&&loss>0?baseEV/loss:null,rr=payoffComplete?reward/loss:null,margin=pBase!==null&&breakEven!==null?pBase-breakEven:null;
    const rangeComplete=pctRange(pLow)&&pctRange(pBase)&&pctRange(pHigh),adversePass=adverseEV!==null&&adverseEV>0,basePass=baseEV!==null&&baseEV>0;
    const routeAllowsAdd=!!route&&route.action==="ADD"&&route.maxAllowedAdd>0,routeCanHold=!!route&&route.current!==null&&route.current>0;
    const qtyOverTarget=lens==="ADD"&&routeAllowsAdd&&qtyComplete&&quantity>route.maxAllowedAdd;
    const addNotAllowed=lens==="ADD"&&!["custom","qqqFarCallOverlay","deploymentTiming"].includes(candidateKey)&&(!route||!routeAllowsAdd);
    const holdConflictsWithReduce=lens==="HOLD"&&route&&route.action==="REDUCE";
    const qqqOverlayLocked=candidateKey==="qqqFarCallOverlay",noSizingRoute=!route&&["custom","deploymentTiming"].includes(candidateKey);
    const riskNature=candidateKey==="vxxShortShares"?"UNBOUNDED":String(i.riskNature||"STRESS_ONLY");
    const independentEvidenceOk=probabilityBasis==="INDEPENDENT_OOS"&&probabilityMethod==="EMPIRICAL"&&sampleSize!==null&&sampleSize>=30&&empirical!==null&&evidenceNote.length>=12&&axes.accuracy==="PASS"&&axes.generality==="PASS"&&axes.integration==="PASS";
    let status="BASELINE_PENDING",nextAction="Complete payoff, cost, quantity, horizon and probability; no default success probability is inserted.";
    if(!payoffComplete||!qtyComplete||!timeComplete){status="NEEDS_PAYOFF";nextAction="Enter positive gain/loss per unit, non-negative base/stress costs, integer quantity and calendar-day horizon. Missing values remain PENDING.";}
    else if(!probComplete||pBase===null){status="INVALID_RANGE";nextAction="Probability inputs must be in [0,100], and low ≤ base ≤ high. Provide a base probability.";}
    else if(!market||market.blocked===true){status="MARKET_BLOCKED";nextAction="BLOCK: main market data gate is blocked or unavailable. No deployment may be inferred from scenario EV.";}
    else if(qqqOverlayLocked){status="QQQ_OVERLAY_LOCKBOX";nextAction="BLOCK promotion of incremental QQQ FAR CALL overlay. The current Accuracy / Generality / Integration lockbox fails; positive scenario EV cannot override it.";}
    else if(noSizingRoute){status="NO_SIZING_ROUTE";nextAction="Scenario only: this candidate has no primary sizing row. It cannot turn into an allocation until a mapped capacity model exists.";}
    else if(addNotAllowed||(lens==="ADD"&&qtyOverTarget)){status=qtyOverTarget?"QTY_OVER_TARGET":"ADD_NOT_ALLOWED";nextAction=qtyOverTarget?"BLOCK: proposed units exceed the main engine's current ADD gap. EV does not enlarge capacity.":"NO ADD: the main sizing row is not in ADD state or has no positive add gap. Respect HOLD / REDUCE / BLOCK / PENDING.";}
    else if(lens==="ADD"&&market.allowNew!==true&&candidateKey!=="qqqShares"){status="ADD_NOT_ALLOWED";nextAction="Market state does not permit new exposure for this seller/risk-sensitive lane. Do not bypass the regime gate.";}
    else if(holdConflictsWithReduce){status="HOLD_CONFLICTS_WITH_REDUCE";nextAction="Main sizing engine requests REDUCE. A positive forward EV is counterfactual and cannot cancel the reduction route.";}
    else if(lens==="HOLD"&&!routeCanHold&&!["custom","deploymentTiming","qqqFarCallOverlay"].includes(candidateKey)){status="ADD_NOT_ALLOWED";nextAction="No registered current exposure is available to score as HOLD. Reconcile current units or change the lens to ADD.";}
    else if(probabilityBasis==="MODEL_REPLAY"){status="MODEL_ONLY";nextAction=basePass?"Model EV is positive under entered assumptions, but model probability is not trade-ready evidence.":"Model EV does not pass the entered base scenario; keep it research/scenario only.";}
    else if(probabilityBasis!=="INDEPENDENT_OOS"){status="HYPOTHESIS_ONLY";nextAction=basePass?"Base EV is positive versus $0 direct-P&L WAIT, but success probability remains a hypothesis.":"Hypothetical base EV is non-positive. Wait or remeasure; no evidence-backed probability exists.";}
    else if(!independentEvidenceOk){status="EVIDENCE_INCOMPLETE";nextAction="PENDING: at least 30 counted outcomes, a source/reference note and PASS on Accuracy, Generality and Integration are required. UI attestations do not authenticate evidence.";}
    else if(riskNature==="UNBOUNDED"){status="UNBOUNDED_TAIL";nextAction="Scenario EV may be positive, but this exposure has unbounded/unknown tail risk. Entered stress loss is not a maximum-loss cap.";}
    else if(!basePass){status="NEGATIVE_EXPECTED_VALUE";nextAction="Base expected value is zero or negative after entered costs. Under this payoff/probability specification, do not add exposure.";}
    else if(!rangeComplete||!adversePass){status="FRAGILE_EXPECTED_VALUE";nextAction="Base EV is positive but adverse EV is missing or non-positive. The opportunity is sensitive to probability/costs; do not call it robust.";}
    else{status="ELIGIBLE_FOR_HUMAN_REVIEW";nextAction="Scenario, evidence-axis attestations and sizing route pass. ELIGIBLE FOR HUMAN REVIEW only—not trade approval, strategy promotion or an order.";}
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
      totalCostBaseUsd:cost!==null&&qtyComplete?cost*quantity:null,totalCostAdverseUsd:cost!==null&&costStress!==null&&qtyComplete?(cost+costStress)*quantity:null,
      expectedValuePerCalendarDayUsd:perDay,expectedValueBasePerRisk:evPerRisk,rewardRiskRatio:rr,probabilityMarginPct:margin,
      scenarioLossTotalUsd:riskTotal,scenarioRiskPctNav:riskPctNav,expectedValuePctNav:evPctNav,robustPositive:rangeComplete&&adversePass&&basePass,
      adverseProbabilityPct:pctRange(pLow)?pLow:null,favorableProbabilityPct:pctRange(pHigh)?pHigh:null,mainRoute:route,quantityOverTarget:qtyOverTarget,independentEvidenceOk,axes:candidateEvidence,evidenceNote:evidenceNote||null,warnings,
      researchEvidence:{rollingFloor:EVIDENCE.rollingFloor,qqqFarCallOverlay:EVIDENCE.qqqFarCallOverlay,vxxCallCredit:EVIDENCE.vxxCallCredit,hybridReplay:EVIDENCE.hybridReplay},
      waitReferenceExpectedValueUsd:0,futureCashYieldIncluded:false,brokerOrders:false
    };
  }
  const api={evaluate,wilson95,EVIDENCE};
  if(typeof module!=="undefined"&&module.exports)module.exports=api;
  if(root)root.DecisionValueEngineV1=api;
})(typeof window!=="undefined"?window:(typeof globalThis!=="undefined"?globalThis:this));
