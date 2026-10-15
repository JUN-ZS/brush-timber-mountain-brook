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

  const PRIMARY_STRESS_LEGS=Object.freeze(["qqqCore","vxxShort","qqqCallCredit","vxxCallCredit"]);
  const REQUIRED_REGIMES=Object.freeze(["CARRY","WEAKENING","PRE-SHOCK","SHOCK_BACKWARDATION"]);
  function parseObject(value){
    if(value&&typeof value==="object"&&!Array.isArray(value))return value;
    if(typeof value==="string"&&value.trim()){try{const parsed=JSON.parse(value);return parsed&&typeof parsed==="object"&&!Array.isArray(parsed)?parsed:null;}catch(_){return null;}}
    return null;
  }
  function validIsoDate(value){
    const s=String(value||"");
    if(!/^\d{4}-\d{2}-\d{2}$/.test(s))return false;
    const ms=Date.parse(s+"T00:00:00Z");
    return Number.isFinite(ms)&&new Date(ms).toISOString().slice(0,10)===s;
  }
  function evaluateComparator(i,candidateHorizonDays,alternativeEVTotalUsd,alternativeLabel){
    const label=String(alternativeLabel||"").trim();
    if(alternativeEVTotalUsd===null||alternativeEVTotalUsd===undefined||!label||label.length<3)
      return {status:"VALUE_PENDING",comparable:false,reason:"Named alternative EV is missing."};
    const candidateCapital=n(i.candidateCapitalBasisUsd),alternativeCapital=n(i.alternativeCapitalBasisUsd);
    const candidateRisk=n(i.candidateRiskBudgetUsd),alternativeRisk=n(i.alternativeRiskBudgetUsd),alternativeHorizon=n(i.alternativeHorizonDays);
    if(candidateCapital===null||candidateCapital<=0||alternativeCapital===null||alternativeCapital<=0||
       candidateRisk===null||candidateRisk<=0||alternativeRisk===null||alternativeRisk<=0||
       candidateHorizonDays===null||alternativeHorizon===null)
      return {status:"BASIS_PENDING",comparable:false,reason:"Candidate/alternative capital, risk budget, and horizon must be explicit."};
    if(!Number.isInteger(candidateHorizonDays)||candidateHorizonDays<1||candidateHorizonDays>3650||
       !Number.isInteger(alternativeHorizon)||alternativeHorizon<1||alternativeHorizon>3650)
      return {status:"BASIS_PENDING",comparable:false,reason:"Candidate and alternative horizons must be integer calendar days from 1 to 3650."};
    if(Math.abs(candidateCapital-alternativeCapital)>0.01)return {status:"INCOMPARABLE",comparable:false,reason:"Capital basis differs by more than $0.01."};
    if(Math.abs(candidateRisk-alternativeRisk)>0.01)return {status:"INCOMPARABLE",comparable:false,reason:"Risk-budget basis differs by more than $0.01; normalize risk before comparing."};
    if(candidateHorizonDays!==alternativeHorizon)return {status:"INCOMPARABLE",comparable:false,reason:"Candidate and alternative calendar horizons differ."};
    if(i.alternativeCostsIncluded!==true)return {status:"INCOMPARABLE",comparable:false,reason:"Alternative EV is not explicitly confirmed net of all stated costs."};
    return {status:"COMPARABLE",comparable:true,reason:"Same capital, risk budget, calendar horizon, and explicitly after-cost alternative EV.",candidateCapitalBasisUsd:candidateCapital,alternativeCapitalBasisUsd:alternativeCapital,candidateRiskBudgetUsd:candidateRisk,alternativeRiskBudgetUsd:alternativeRisk,horizonDays:candidateHorizonDays,afterCosts:true};
  }
  function evaluatePortfolioStress(raw,nav){
    const b=parseObject(raw);
    if(!b)return {status:"PENDING",complete:false,scenarioName:null,totalLossUsd:null,riskPctNav:null,activeLegs:[],missingLegs:PRIMARY_STRESS_LEGS.slice(),unboundedTail:false,warnings:["Reconcile all four primary exposure categories under one named common stress event."]};
    const scenarioName=String(b.scenarioName||"").trim(),sourceNote=String(b.sourceNote||"").trim(),legs=b.legs&&typeof b.legs==="object"&&!Array.isArray(b.legs)?b.legs:{};
    const missing=[],invalid=[],activeLegs=[];let totalLossUsd=0,unboundedTail=false;
    if(scenarioName.length<3)missing.push("scenarioName");
    if(sourceNote.length<8)missing.push("sourceNote");
    if(b.reconciled!==true)missing.push("explicit reconciliation of all four primary categories");
    for(const key of PRIMARY_STRESS_LEGS){
      const leg=legs[key],state=String(leg&&leg.state||"UNKNOWN").toUpperCase();
      if(!leg){missing.push(key);continue;}
      if(!["ACTIVE","ZERO","UNKNOWN"].includes(state)){invalid.push(key+": state must be ACTIVE, ZERO, or UNKNOWN");continue;}
      if(state==="UNKNOWN"){missing.push(key);continue;}
      if(state==="ZERO")continue;
      const loss=n(leg.stressLossUsd);
      if(loss===null||loss<=0){missing.push(key+": positive same-scenario loss estimate");continue;}
      totalLossUsd+=loss;activeLegs.push({key,stressLossUsd:loss});
      if(key==="vxxShort")unboundedTail=true;
    }
    const navValue=n(nav);
    if(navValue===null||navValue<=0)missing.push("positive NAV denominator");
    const riskPctNav=navValue!==null&&navValue>0&&missing.length===0&&invalid.length===0?totalLossUsd/navValue*100:null;
    let status=invalid.length?"INVALID":missing.length?"PENDING":unboundedTail?"UNBOUNDED_TAIL_SCENARIO":"COMPLETE_SCENARIO_ESTIMATE";
    const warnings=[];
    if(status==="COMPLETE_SCENARIO_ESTIMATE")warnings.push("Loss-only sum for one operator-defined event; not VaR, maximum loss, authenticated evidence, or a correlation/hedge-credit model.");
    if(unboundedTail)warnings.push("VXX short stock has structurally unbounded upside risk; this finite stress estimate is not a cap.");
    if(riskPctNav!==null&&riskPctNav>5)warnings.push("Common-scenario loss sum exceeds 5% NAV; internal review trigger, not a universal law.");
    return {status,complete:status==="COMPLETE_SCENARIO_ESTIMATE"||status==="UNBOUNDED_TAIL_SCENARIO",scenarioName:scenarioName||null,sourceNote:sourceNote||null,totalLossUsd:missing.length||invalid.length?null:totalLossUsd,riskPctNav,activeLegs,missingLegs:missing,invalid,unboundedTail,warnings,reconciled:b.reconciled===true,sourceAuthenticated:false};
  }
  function evaluateGenerality(raw){
    const d=parseObject(raw);
    if(!d)return {status:"MISSING_DOSSIER",pass:false,operatorAttested:false,evidenceAuthenticated:false,issues:["A structured chronological generality dossier is required."]};
    const fingerprintKeys=["observationsSha256","calendarSha256","specSha256"];
    const fingerprints=d.inputIntegrity&&typeof d.inputIntegrity==="object"?d.inputIntegrity:{};
    const dataQuality=d.dataQuality&&typeof d.dataQuality==="object"?d.dataQuality:{};
    const fingerprintsValid=fingerprintKeys.every(key=>typeof fingerprints[key]==="string"&&/^[a-f0-9]{64}$/i.test(fingerprints[key]));
    const missingExpected=Array.isArray(dataQuality.missingExpectedDates)?dataQuality.missingExpectedDates:null;
    const auditReady=d.auditorVersion==="QQQ_HYBRID_GENERALITY_AUDITOR_V1"&&d.auditStatus==="PASS_OPERATOR_ATTESTED"&&fingerprintsValid&&
      n(dataQuality.expectedObservationCoveragePct)===100&&missingExpected!==null&&missingExpected.length===0&&
      Number.isInteger(n(dataQuality.sourceRowCount))&&n(dataQuality.sourceRowCount)>=100;
    if(!auditReady)return {status:"AUDIT_REQUIRED",pass:false,operatorAttested:true,evidenceAuthenticated:false,auditStatus:String(d.auditStatus||"MISSING"),issues:["Paste a completed generality_auditor.py JSON report, not manually entered rolling-window claims. Require three SHA-256 fingerprints, full expected-session coverage and no missing dates."]};
    const issues=[],requiredStrings=["baselineId","candidateId","sourceRef","trainStart","trainEnd","validationStart","validationEnd","finalStart","finalEnd"];
    const missing=requiredStrings.filter(k=>d[k]===undefined||d[k]===null||String(d[k]).trim()==="");
    if(missing.length)issues.push("Missing fields: "+missing.join(", "));
    for(const k of ["trainStart","trainEnd","validationStart","validationEnd","finalStart","finalEnd"])if(d[k]!==undefined&&!validIsoDate(d[k]))issues.push(k+" must be a real YYYY-MM-DD date.");
    if(missing.length||issues.length)return {status:missing.length?"NEEDS_DATA":"INVALID",pass:false,operatorAttested:false,evidenceAuthenticated:false,issues};
    if(!(d.trainStart<=d.trainEnd&&d.trainEnd<d.validationStart&&d.validationStart<=d.validationEnd&&d.validationEnd<d.finalStart&&d.finalStart<=d.finalEnd))issues.push("Train, validation, and final OOS dates must be chronological and non-overlapping.");
    for(const k of ["finalUntouched","finalEvaluatedOnce","designFrozenBeforeFinal","noLookahead","trialLedgerComplete"])if(d[k]!==true)issues.push(k+" must be explicitly true.");
    const finalCoverage=n(d.finalCoveragePct),finalObservations=n(d.finalObservationCount);
    if(finalCoverage===null||finalCoverage<0||finalCoverage>100)issues.push("finalCoveragePct must be within 0–100.");
    if(finalObservations===null||!Number.isInteger(finalObservations)||finalObservations<100)issues.push("Final OOS needs at least 100 observations to publish daily risk/return statistics.");
    if(finalCoverage!==100)issues.push("Final OOS coverage must be 100% for a complete final-window claim; missing sessions cannot be silently dropped.");
    const windows=Array.isArray(d.rollingWindows)?d.rollingWindows:[];
    if(windows.length<5)issues.push("At least five chronological rolling windows are required.");
    const ids=new Set(),dateRanges=new Set();let positive=0,catastrophic=0,windowsValid=true,lastStart="";
    for(let j=0;j<windows.length;j++){
      const w=windows[j]||{},id=String(w.id||"").trim();
      if(!id||ids.has(id))issues.push("Rolling window IDs must be present and unique: index "+j+".");ids.add(id);
      if(!validIsoDate(w.start)||!validIsoDate(w.end)||w.start>w.end){issues.push("Rolling window "+(id||j)+" has invalid dates.");windowsValid=false;}
      if(validIsoDate(w.start)&&validIsoDate(w.end)){const dateKey=w.start+"|"+w.end;if(dateRanges.has(dateKey))issues.push("Duplicate rolling date range cannot count as another window: "+dateKey+".");dateRanges.add(dateKey);}
      if(validIsoDate(w.start)&&lastStart&&w.start<lastStart){issues.push("Rolling windows must be ordered chronologically.");windowsValid=false;}
      if(validIsoDate(w.start))lastStart=w.start;
      const obs=n(w.observations),coverage=n(w.coveragePct),effect=n(w.effectDeltaPct);
      if(obs===null||!Number.isInteger(obs)||obs<100){issues.push("Rolling window "+(id||j)+" has fewer than 100 observations.");windowsValid=false;}
      if(coverage===null||coverage<98||coverage>100||w.missingDatesReviewed!==true){issues.push("Rolling window "+(id||j)+" needs >=98% coverage and missing-date review.");windowsValid=false;}
      if(w.sameCapitalAndCosts!==true||w.lookaheadFree!==true||w.costStressPass!==true||typeof w.catastrophicFailure!=="boolean"){issues.push("Rolling window "+(id||j)+" must document paired capital/costs, no-lookahead, adverse costs and catastrophic-failure status.");windowsValid=false;}
      if(effect===null){issues.push("Rolling window "+(id||j)+" needs a numeric pre-selected-objective effectDeltaPct.");windowsValid=false;}else if(effect>0)positive++;
      if(w.catastrophicFailure===true)catastrophic++;
      if(validIsoDate(w.end)&&validIsoDate(d.validationEnd)&&w.end>d.validationEnd)issues.push("Rolling window "+(id||j)+" overlaps the final OOS lockbox.");
    }
    const rc=d.regimeObservations&&typeof d.regimeObservations==="object"&&!Array.isArray(d.regimeObservations)?d.regimeObservations:{};
    const regimeMissing=REQUIRED_REGIMES.filter(k=>{const v=n(rc[k]);return v===null||!Number.isInteger(v)||v<100;});
    if(regimeMissing.length)issues.push("Regimes need >=100 daily observations: "+regimeMissing.join(", ")+". Otherwise mark INSUFFICIENT_SAMPLE.");
    if(windowsValid&&windows.length>=5&&positive<Math.ceil(windows.length*0.8))issues.push("Positive primary effect is below 80% of rolling windows.");
    if(catastrophic>0)issues.push("A rolling window reports catastrophic failure; Generality cannot pass.");
    const pass=issues.length===0;
    return {status:pass?"PASS_OPERATOR_ATTESTED":"NOT_PASS",pass,operatorAttested:true,evidenceAuthenticated:false,auditorVersion:d.auditorVersion,auditStatus:d.auditStatus,inputIntegrity:fingerprints,dataQuality,baselineId:String(d.baselineId),candidateId:String(d.candidateId),sourceRef:String(d.sourceRef),evidenceClass:String(d.evidenceClass||"UNKNOWN"),outcomeClass:String(d.outcomeClass||"UNKNOWN"),canCountAsRealExecutionProbability:d.canCountAsRealExecutionProbability===true&&d.evidenceClass==="OBSERVED"&&d.outcomeClass==="REAL_EXECUTION",rollingWindowCount:windows.length,positiveEffectWindows:positive,requiredPositiveWindows:Math.ceil(windows.length*0.8),catastrophicFailures:catastrophic,regimesMeasured:REQUIRED_REGIMES.filter(k=>!regimeMissing.includes(k)),finalCoveragePct:finalCoverage,finalObservationCount:finalObservations,issues,limitation:"Input fingerprints and arithmetic are structurally checked, but this APP cannot authenticate source files or prove the lockbox was untouched."};
  }

  function evaluate(input){
    const i=input&&typeof input==="object"?input:{}, candidateKey=String(i.candidateKey||"custom"),candidateLabel=strategyLabel(candidateKey),lens=i.lens==="HOLD"?"HOLD":"ADD";
    const nav=n(i.nav),quantity=n(i.quantity),horizonDays=n(i.horizonDays),reward=n(i.rewardUsd),loss=n(i.lossUsd),cost=n(i.costUsd),costStress=n(i.costStressUsd);
    const alternativeEVTotalUsd=n(i.alternativeEVTotalUsd),alternativeLabel=String(i.alternativeLabel||"").trim();
    const warnings=[],market=i.market&&typeof i.market==="object"?i.market:null,route=mainRoute(i.mainRow,candidateKey);
    const comparator=evaluateComparator(i,horizonDays,alternativeEVTotalUsd,alternativeLabel);
    const portfolioStress=evaluatePortfolioStress(i.portfolioStress,nav);
    const generalityReview=evaluateGenerality(i.generalityDossierJson);
    const primaryCandidate=["qqqShares","vxxShortShares","qqqCallSpreads","vxxCallSpreads"].includes(candidateKey);
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
    const alternativeValuePresent=alternativeEVTotalUsd!==null&&Number.isFinite(alternativeEVTotalUsd)&&alternativeLabel.length>=3;
    const alternativeComplete=comparator.status==="COMPARABLE";
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
    const independentEvidenceOk=probabilityBasis==="INDEPENDENT_OOS"&&probabilityMethod==="EMPIRICAL"&&sampleSize!==null&&sampleSize>=30&&empirical!==null&&evidenceNote.length>=12&&axes.accuracy==="PASS"&&axes.generality==="PASS"&&axes.integration==="PASS"&&generalityReview.status==="PASS_OPERATOR_ATTESTED"&&generalityReview.canCountAsRealExecutionProbability===true;
    let status="BASELINE_PENDING",nextAction="Complete payoff, cost, time and evidence inputs; no default success probability or alternative value is inserted.";
    if(!market||market.blocked===true){status="MARKET_BLOCKED";nextAction="BLOCK: the main market-data gate is blocked or unavailable. Scenario EV cannot authorize deployment.";}
    else if(qqqOverlayLocked){status="QQQ_OVERLAY_LOCKBOX";nextAction="BLOCK promotion of the incremental QQQ FAR CALL overlay. Accuracy / Generality / Integration lockbox failures cannot be overridden by a positive scenario EV.";}
    else if(lens==="ADD"&&floorBreached){status="CLOCK_FLOOR_BREACH";nextAction="BLOCK new deployment while NAV is below the CLOCK Floor. Reconcile NAV, cash flows, holdings and pending orders; the floor is a review trigger, not an automatic sell.";}
    else if(lens==="ADD"&&market.allowNew!==true){status="ADD_NOT_ALLOWED";nextAction="BLOCK new exposure: the current verified market state does not permit new Carry risk. QQQ Core and seller legs cannot use an EV score to bypass this gate.";}
    else if(lens==="ADD"&&(addNotAllowed||qtyOverTarget)){status=qtyOverTarget?"QTY_OVER_TARGET":"ADD_NOT_ALLOWED";nextAction=qtyOverTarget?"BLOCK: proposed units exceed the current main-engine ADD gap. EV does not enlarge capacity.":"NO ADD: the main sizing row is not in ADD state or has no known positive add gap. Respect HOLD / REDUCE / BLOCK / PENDING.";}
    else if(lens==="HOLD"&&heldReviews.length){status="POSITION_REVIEW_PRIORITY";nextAction="The registered position-management meter flags this holding for review before a new hold-vs-exit EV can be actioned: "+heldReviews.map(x=>String(x.label||x.template)+": "+String(x.action||"REVIEW")).join("; ")+". EV remains counterfactual and cannot override the position-specific gate.";}
    else if(holdConflictsWithReduce){status="HOLD_CONFLICTS_WITH_REDUCE";nextAction="The main sizing engine requests REDUCE. A positive forward EV is counterfactual and cannot cancel the current reduction route.";}
    else if(lens==="HOLD"&&!routeCanHold&&!["custom","deploymentTiming","qqqFarCallOverlay"].includes(candidateKey)){status="ADD_NOT_ALLOWED";nextAction="No positive current exposure is available to score as HOLD. Reconcile quantities, or change the lens to ADD.";}
    else if(riskNature==="UNBOUNDED"){status="UNBOUNDED_TAIL";nextAction="This candidate has structurally unbounded/unknown tail risk. Scenario EV can be inspected, but a finite entered stress loss is not a maximum-loss cap.";}
    else if(primaryCandidate&&portfolioStress.status==="PENDING"){status="PORTFOLIO_STRESS_PENDING";nextAction="PENDING: reconcile QQQ Core, VXX short-stock, QQQ call-credit and VXX call-credit under one named common stress event. Unknown categories are not zero.";}
    else if(primaryCandidate&&portfolioStress.status==="INVALID"){status="PORTFOLIO_STRESS_INVALID";nextAction="BLOCK: common portfolio stress inputs contain invalid states or values. Correct the stress ledger before evaluating integration.";}
    else if(primaryCandidate&&portfolioStress.unboundedTail){status="PORTFOLIO_TAIL_REVIEW";nextAction="HUMAN REVIEW: the combined portfolio includes VXX short-stock with unbounded upside risk. The finite common-stress sum is not a loss cap.";}
    else if(lens==="ADD"&&primaryCandidate&&portfolioStress.riskPctNav!==null&&portfolioStress.riskPctNav>5){status="PORTFOLIO_STRESS_REVIEW";nextAction="HUMAN REVIEW: summed loss under the named common stress exceeds 5% NAV. This is an internal materiality gate, not a universal finance law.";}
    else if(noSizingRoute){status="NO_SIZING_ROUTE";nextAction="Scenario only: this candidate has no primary sizing route. It cannot become a portfolio allocation until a capacity model exists.";}
    else if(!payoffComplete||!qtyComplete||!timeComplete){status="NEEDS_PAYOFF";nextAction="Enter positive gain/loss per unit, non-negative base/adverse costs, integer quantity and calendar-day horizon. Missing values remain PENDING.";}
    else if(probabilityMissing){status="NEEDS_PROBABILITY";nextAction="PENDING: enter low / base / high probability, or provide wins and total outcomes. Missing probability evidence is not a 0% probability or an invalid range.";}
    else if(!probComplete||pBase===null){status="INVALID_RANGE";nextAction="Probability inputs must be within [0,100], with low ≤ base ≤ high. Correct the invalid range; do not use a blank as zero.";}
    else if(probabilityBasis==="MODEL_REPLAY"){status="MODEL_ONLY";nextAction=basePass?"Model EV is positive under entered assumptions, but model win frequency is not a real-execution probability. No trade-ready conclusion.":"The model scenario does not pass the entered base-EV screen; keep it research/scenario only.";}
    else if(probabilityBasis!=="INDEPENDENT_OOS"){status="HYPOTHESIS_ONLY";nextAction=basePass?"Base EV is positive under the scenario, but the success probability remains a hypothesis; relative value versus waiting/another strategy is not authenticated.":"Hypothetical base EV is non-positive. Wait or remeasure; no evidence-backed future probability exists.";}
    else if(probabilityBasis==="INDEPENDENT_OOS"&&generalityReview.status!=="PASS_OPERATOR_ATTESTED"){status="GENERALITY_PENDING";nextAction="PENDING: chronological/rolling/regime/final-OOS dossier has not passed structural checks. A UI dropdown alone cannot certify Generality.";}
    else if(!independentEvidenceOk){status="EVIDENCE_INCOMPLETE";nextAction="PENDING: at least 30 counted outcomes, source reference, valid Generality dossier and PASS on Accuracy / Generality / Integration are required.";}
    else if(!basePass){status="NEGATIVE_EXPECTED_VALUE";nextAction="Base expected value is zero or negative after entered costs. Under this payoff/probability specification, do not add exposure.";}
    else if(comparator.status==="VALUE_PENDING"){status="ALTERNATIVE_VALUE_PENDING";nextAction="EV is positive under supplied assumptions, but the named waiting / alternative expected value is missing. Do not silently equate WAIT with $0.";}
    else if(comparator.status==="BASIS_PENDING"){status="COMPARATOR_CONTRACT_PENDING";nextAction="PENDING: enter candidate and alternative capital bases, both risk budgets, same horizon, and after-cost confirmation.";}
    else if(comparator.status==="INCOMPARABLE"){status="ALTERNATIVE_NOT_COMPARABLE";nextAction="Candidate and alternative fail the fair-comparison contract: "+comparator.reason+" Normalize the basis or keep scenario-only.";}
    else if(incrementalEVBase<=0){status="NEGATIVE_INCREMENTAL_VALUE";nextAction="Candidate base EV is no better than the alternative under the validated capital/risk/time/cost basis. Prefer WAIT or a better comparator.";}
    else if(!rangeComplete){status="NEEDS_PROBABILITY";nextAction="PENDING: the low / base / high probability range is incomplete, so robustness versus the comparator cannot be assessed.";}
    else if(!adversePass||incrementalEVAdverse===null||incrementalEVAdverse<=0){status="FRAGILE_EXPECTED_VALUE";nextAction="Base EV beats the comparator, but the low-probability / adverse-cost case fails to beat it. Relative value is fragile; do not call it robust.";}
    else{status="ELIGIBLE_FOR_HUMAN_REVIEW";nextAction="Evidence, current sizing route, explicit alternative and adverse case pass the configured screen. ELIGIBLE FOR HUMAN REVIEW only—not trade approval, strategy promotion or an order.";}
    if(lens==="HOLD"&&heldPositions.length===0&&routeCanHold)warnings.push("No matching registered position row: current units exist in the sizing input, but stop / mark / age / DTE management evidence is not linked for this holding.");
    if(floorBreached&&lens!=="ADD")warnings.push("CLOCK Floor is breached. This EV remains a scenario; the long-horizon controller calls for NAV / cash-flow reconciliation and human review.");
    const candidateEvidence=qqqOverlayLocked?{accuracy:EVIDENCE.qqqFarCallOverlay.accuracy,generality:EVIDENCE.qqqFarCallOverlay.generality,integration:EVIDENCE.qqqFarCallOverlay.integration,sourceId:EVIDENCE.qqqFarCallOverlay.id}
      :probabilityBasis==="MODEL_REPLAY"&&candidateKey==="vxxCallSpreads"?{accuracy:"BLOCKED · MODEL_ONLY / NOT OPRA",generality:"NOT DEMONSTRATED",integration:"NOT PROVEN BY ISOLATED ATTRIBUTION",sourceId:EVIDENCE.vxxCallCredit.id}
      :{...axes,sourceId:evidenceNote||null,operatorAttested:probabilityBasis==="INDEPENDENT_OOS"};
    if(riskNature==="UNBOUNDED")warnings.push("VXX short-stock risk is structurally unbounded; entered stress loss cannot cap the tail.");
    warnings.push(...portfolioStress.warnings);
    if(generalityReview.status!=="PASS_OPERATOR_ATTESTED")warnings.push("Generality dossier status: "+generalityReview.status+". Structural checks do not authenticate source data or prove the final holdout was untouched.");
    else warnings.push("Generality dossier is structurally complete but operator-attested only; source data and holdout independence are not authenticated by the APP.");
    if(candidateKey==="qqqCallSpreads")warnings.push("The isolated incremental FAR CALL overlay failed its current research screen. This is not a full-composite return replay and does not prove primary-leg future probability.");
    if(baseEV!==null&&baseEV>0&&adverseEV!==null&&adverseEV<=0)warnings.push("Base EV is positive but low-probability plus adverse-cost EV is non-positive.");
    if(riskTotal!==null&&nav!==null&&nav>0&&riskTotal/nav>0.05)warnings.push("Entered scenario loss exceeds 5% of NAV; this is a project materiality warning, not a universal finance law.");
    return {
      status,statusLabel:status,nextAction,candidateKey,candidateLabel,lens,navUsd:nav,quantity:qtyComplete?quantity:null,horizonDays:timeComplete?horizonDays:null,
      rewardUsd:reward,lossUsd:loss,costUsd:cost,costStressUsd:costStress,riskNature,riskNatureLabel:riskNature==="UNBOUNDED"?"UNBOUNDED TAIL · stress amount is not a cap":riskNature==="DEFINED"?"DEFINED STOP / MAX-LOSS ASSUMPTION":"STRESS ONLY · not a guaranteed loss cap",
      probabilityMethod,probabilityMethodLabel,probabilityBasis,probabilityBasisLabel,probabilityLowPct:pctRange(pLow)?pLow:null,probabilityBasePct:pctRange(pBase)?pBase:null,probabilityHighPct:pctRange(pHigh)?pHigh:null,
      sampleSize,empiricalInterval:empirical,breakEvenProbabilityPct:breakEven,expectedValueBaseUsd:baseEV,expectedValueAdverseUsd:adverseEV,expectedValueHighUsd:highEV,
      expectedValueBaseTotalUsd:baseTotal,expectedValueAdverseTotalUsd:adverseTotal,expectedValueHighTotalUsd:highTotal,
      alternativeEVTotalUsd:alternativeValuePresent?alternativeEVTotalUsd:null,alternativeLabel:alternativeLabel||null,alternativeComplete,comparatorContract:comparator,
      candidateCapitalBasisUsd:n(i.candidateCapitalBasisUsd),alternativeCapitalBasisUsd:n(i.alternativeCapitalBasisUsd),candidateRiskBudgetUsd:n(i.candidateRiskBudgetUsd),alternativeRiskBudgetUsd:n(i.alternativeRiskBudgetUsd),alternativeHorizonDays:n(i.alternativeHorizonDays),alternativeCostsIncluded:i.alternativeCostsIncluded===true,
      portfolioStress,generalityReview,
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
  const api={evaluate,wilson95,evaluateComparator,evaluatePortfolioStress,evaluateGenerality,EVIDENCE};
  if(typeof module!=="undefined"&&module.exports)module.exports=api;
  if(root)root.DecisionValueEngineV1=api;
})(typeof window!=="undefined"?window:(typeof globalThis!=="undefined"?globalThis:this));
