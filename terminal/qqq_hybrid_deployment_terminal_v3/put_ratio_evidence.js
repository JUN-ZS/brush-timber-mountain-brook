(function(root){
"use strict";
const LEVELS=[3,5,10,15,20,25,30];
const DIRECT_TARGETS=[500,800,1000,2000];
function num(v){if(v===null||v===undefined||v==="")return null;const x=Number(v);return Number.isFinite(x)?x:null;}
function money(v){const x=num(v);return x===null?"—":(x<0?"−$":"$")+Math.abs(x).toLocaleString("en-US",{minimumFractionDigits:0,maximumFractionDigits:2});}
function pct(v,d=2){const x=num(v);return x===null?"—":x.toFixed(d)+"%";}
function validateSnapshot(s){
  const reasons=[];
  if(!s||s.schemaVersion!=="QQQ_PUT_RATIO_EVIDENCE_SNAPSHOT_V1")reasons.push("Evidence snapshot schema is missing or unsupported.");
  if(!s?.metadata||Number(s.metadata.optionEpisodes)!==62||s.metadata.optionSourceEnd!=="2025-12-15")reasons.push("Evidence metadata does not match the pinned 62-episode source window.");
  if(!Array.isArray(s?.policies)||!Array.isArray(s?.probabilities))reasons.push("Policy summaries or price-path frequencies are missing.");
  if(Number(s?.curve?.trade_count)!==62||s?.curve?.source_option_end!==s?.metadata?.optionSourceEnd)reasons.push("Serial curve does not match the 62-episode source.");
  if(!Array.isArray(s?.curve?.session_dates)||!s?.curve?.cumulative_pnl_usd_by_policy)reasons.push("Serial curve dates or policy series are missing.");
  if(!s?.manifest?.dataJsonBlobSha||!s?.manifest?.portfolioCurveBlobSha||!s?.manifest?.profitWarningAnalysisBlobSha)reasons.push("Source blob hashes are missing.");
  return {ok:reasons.length===0,reasons};
}
function policyById(s,id){return (s?.policies||[]).find(p=>p.id===id)||null;}
function selectedHistoryPolicy(s,inputs){
  if(inputs.direction!=="SHORT_HEAVY"||Number(inputs.n)!==5)return null;
  return policyById(s,inputs.policyId)||null;
}
function targetForAmount(amount){
  const a=num(amount);
  if(a===null)return null;
  const rounded=Math.round(a*100)/100;
  const target=DIRECT_TARGETS.find(x=>Math.abs(rounded-x)<0.005);
  return target===undefined?null:target;
}
function drawdownStats(s,nav,policyId){
  const dates=s?.curve?.session_dates||[];
  const series=s?.curve?.cumulative_pnl_usd_by_policy?.[policyId]||[];
  if(!dates.length||series.length!==dates.length||num(nav)===null||num(nav)<=0)return null;
  const pts=[];
  for(let i=0;i<dates.length;i++){
    const pnl=num(series[i]);
    if(pnl!==null)pts.push({i,date:dates[i],pnl,eq:nav+pnl});
  }
  if(!pts.length)return null;
  let peak=pts[0],maxPct=0,maxUsd=0,maxPeakDate=peak.date,maxTroughDate=peak.date;
  for(const p of pts){
    if(p.eq>=peak.eq){peak=p;continue;}
    const drop=peak.eq>0?(p.eq/peak.eq-1)*100:null;
    if(drop!==null&&drop<maxPct){maxPct=drop;maxUsd=peak.eq-p.eq;maxPeakDate=peak.date;maxTroughDate=p.date;}
  }
  const cycles=[];
  let cp=pts[0],worst=0,trough=pts[0];
  for(let i=1;i<pts.length;i++){
    const p=pts[i],d=cp.eq>0?(p.eq/cp.eq-1)*100:0;
    if(p.eq>=cp.eq){cycles.push({worst,trough:trough.date,index:trough.i});cp=p;worst=0;trough=p;}
    else if(d<worst){worst=d;trough=p;}
  }
  cycles.push({worst,trough:trough.date,index:trough.i});
  const first=Date.parse(dates[0]),last=Date.parse(dates[dates.length-1]);
  const spanYears=(last-first)/(365.2425*86400000);
  const allYears=Array.from(new Set(dates.map(x=>String(x).slice(0,4)))).sort();
  const levels=LEVELS.map(level=>{
    const hit=cycles.filter(x=>x.worst<=-level+1e-9).sort((a,b)=>a.index-b.index);
    const gaps=hit.slice(1).map((x,i)=>x.index-hit[i].index).sort((a,b)=>a-b);
    const yearCounts={};
    hit.forEach(x=>{const y=x.trough.slice(0,4);yearCounts[y]=(yearCounts[y]||0)+1;});
    const eventYearCount=Object.keys(yearCounts).length;
    return {level,count:hit.length,perYear:spanYears>0?hit.length/spanYears:0,years:eventYearCount,allYears:allYears.length,yearIncidencePct:allYears.length?100*eventYearCount/allYears.length:null,eventYears:Object.keys(yearCounts).sort(),yearCounts,
      medianGap:gaps.length?(gaps.length%2?gaps[(gaps.length-1)/2]:(gaps[gaps.length/2-1]+gaps[gaps.length/2])/2):null};
  });
  return {maxPct,maxUsd,maxPeakDate,maxTroughDate,levels,coverage:100*pts.length/dates.length,knownMarks:pts.length,expectedMarks:dates.length,missingMarks:dates.length-pts.length,spanYears,finalPnl:pts[pts.length-1].pnl,minimumEquity:Math.min(...pts.map(x=>x.eq))};
}
function rvState(value){const x=num(value);if(x===null)return "ALL";if(x<15)return "RV20_LT15";if(x<25)return "RV20_15_25";if(x<35)return "RV20_25_35";return "RV20_GTE35";}
function volatility(s,rv20,horizon){
  const state=rvState(rv20),h=Number(horizon),rows=s?.probabilities||[];
  const selected=rows.find(x=>x.state===state&&Number(x.horizonSessions)===h)||null;
  const all=rows.find(x=>x.state==="ALL"&&Number(x.horizonSessions)===h)||null;
  const r5=selected&&all&&num(all.down5Pct)>0?num(selected.down5Pct)/num(all.down5Pct):null;
  const r10=selected&&all&&num(all.down10Pct)>0?num(selected.down10Pct)/num(all.down10Pct):null;
  const down5Elevated=num(rv20)!==null&&num(rv20)>=25&&r5!==null&&r5>=1.5;
  const down10Elevated=num(rv20)!==null&&num(rv20)>=25&&r10!==null&&r10>=1.5;
  return {state,horizon:h,selected,all,down5Ratio:r5,down10Ratio:r10,down5Elevated,down10Elevated,elevated:down5Elevated||down10Elevated};
}
function evaluate(s,rawInputs={}){
  const valid=validateSnapshot(s);
  const inputs={
    nav:num(rawInputs.nav),direction:rawInputs.direction==="LONG_HEAVY"?"LONG_HEAVY":"SHORT_HEAVY",
    n:num(rawInputs.n),riskPct:num(rawInputs.riskPct),profitPct:num(rawInputs.profitPct),
    currentPnl:num(rawInputs.currentPnl),age:num(rawInputs.age),dte:num(rawInputs.dte),rv20:num(rawInputs.rv20),
    horizon:num(rawInputs.horizon)||5,policyId:String(rawInputs.policyId||"BASE_DTE7_CLOSE_SHORT_RISK"),
    combinedReview:rawInputs.combinedReview===true
  };
  const directionRows=inputs.direction==="SHORT_HEAVY"?s?.tailLossShortHeavy:s?.tailLossLongHeavy;
  const tailRow=(directionRows||[]).find(x=>Number(x.n)===inputs.n)||null;
  const budget=inputs.nav!==null&&inputs.nav>0&&inputs.riskPct!==null&&inputs.riskPct>=0?inputs.nav*inputs.riskPct/100:null;
  const worst=tailRow?num(tailRow.worstUsd):null;
  const units=budget!==null&&worst!==null&&worst>0?Math.max(0,Math.floor(budget/worst)):null;
  const tail={direction:inputs.direction,n:inputs.n,medianUsd:tailRow?tailRow.medianUsd:null,p95Usd:tailRow?tailRow.p95Usd:null,worstUsd:worst,
    lossPctOfNav:worst!==null&&inputs.nav>0?100*worst/inputs.nav:null,budgetUsd:budget,wholeUnits:units,
    status:units===null?"PENDING":units===0?"BLOCKED_TAIL_BUDGET":"THEORETICAL_ONLY"};
  const matched=valid.ok?selectedHistoryPolicy(s,inputs):null;
  const navTarget=inputs.nav!==null&&inputs.nav>0&&inputs.profitPct!==null&&inputs.profitPct>=0?Math.round(inputs.nav*inputs.profitPct)/100:null;
  const fixedTarget=targetForAmount(navTarget);
  const directTargetPolicy=fixedTarget!==null&&valid.ok?policyById(s,"TP_USD_"+fixedTarget+"_CLOSE_SHORT_RISK"):null;
  const thresholdStudy=fixedTarget!==null?s?.profitThresholds?.[String(fixedTarget)]||null:null;
  const curve=valid.ok&&matched?drawdownStats(s,inputs.nav,inputs.policyId):null;
  const vol=valid.ok?volatility(s,inputs.rv20,inputs.horizon):{state:"PENDING",selected:null,all:null,elevated:false};
  const alerts=[];
  if(!valid.ok)alerts.push({tone:"bad",code:"EVIDENCE_INVALID",title:"Evidence source blocked",text:valid.reasons.join(" ")});
  if(tail.status==="BLOCKED_TAIL_BUDGET")alerts.push({tone:"bad",code:"TAIL_BUDGET_ZERO",title:"Put Ratio addition blocked by terminal-tail budget",text:"The selected NAV tail budget allows zero complete ratio units under the observed worst terminal-loss estimate. This gate applies to the Put Ratio scenario, not to unrelated Frozen Hybrid legs."});
  else if(tail.status==="THEORETICAL_ONLY")alerts.push({tone:"warn",code:"TAIL_BUDGET_THEORETICAL",title:"Tail budget is only a theoretical upper bound",text:"Broker margin, interim stress, quote depth, cash, assignment and forced liquidation are not verified; this count is not executable capacity."});
  if(inputs.currentPnl!==null&&navTarget!==null&&inputs.currentPnl>=navTarget){
    let text="Current net-liquidation P&L estimate reached the NAV-relative warning line "+money(navTarget)+". This is a manual-review alert.";
    if(directTargetPolicy&&matched){text+=" Direct same-dollar replay "+money(fixedTarget)+": WIN "+pct(directTargetPolicy.winRatePct)+", net P&L "+money(directTargetPolicy.netPnlUsd)+", policy triggers "+directTargetPolicy.triggerCount+"/62. "+(thresholdStudy?"First EOD marks hit "+thresholdStudy.counterfactualFirstMarkHitCount+"/62; within five sessions "+thresholdStudy.counterfactualFirstHitWithin5Sessions+"/62.":"First-hit age distribution is not saved for this dollar target.");}
    else if(!matched)text+=" No direct historical option-policy result can be transferred to the selected direction/N.";
    else text+=" This dollar target does not exactly match a directly replayed fixed threshold; no interpolation is used.";
    alerts.push({tone:"warn",code:"PROFIT_TARGET_REACHED",title:"Profit warning line reached — human review",text});
  }
  if(inputs.age!==null&&inputs.age>=20){
    const text=inputs.currentPnl===null?"Position age is at least 20 sessions but current P&L is missing; profitability cannot be inferred.":
      inputs.currentPnl<=0?"Position age is at least 20 sessions and current P&L is non-positive; compare the historical day-20 rule, without treating it as a proven exit optimum.":
      "Position age is at least 20 sessions while P&L remains positive; review short-put gamma/assignment exposure and profit giveback.";
    alerts.push({tone:inputs.currentPnl!==null&&inputs.currentPnl<=0?"bad":"warn",code:"AGE_20",title:"Time warning — age ≥20 sessions",text});
  }
  if(inputs.dte!==null&&inputs.dte<=7)alerts.push({tone:"bad",code:"DTE_7",title:"Short-put expiry warning — DTE ≤7",text:"Review short-put buyback sides, size, assignment and margin now. No automatic close is emitted."});
  if(vol.elevated){
    const reasons=[];
    if(vol.down5Elevated)reasons.push("≥5% drop rate "+vol.down5Ratio.toFixed(2)+"× ALL");
    if(vol.down10Elevated)reasons.push("≥10% drop rate "+vol.down10Ratio.toFixed(2)+"× ALL");
    alerts.push({tone:"warn",code:"VOL_DOWNSIDE_ELEVATED",title:"Time × volatility warning — QQQ downside frequency elevated",text:"RV20 "+pct(inputs.rv20)+" ("+vol.state+"), horizon "+inputs.horizon+" sessions, N="+vol.selected.n+". "+reasons.join("; ")+". This is underlying price-path frequency, not Put Ratio loss probability."});
  }
  const timingPressure=alerts.filter(a=>["PROFIT_TARGET_REACHED","AGE_20","DTE_7"].includes(a.code));
  if(vol.elevated&&timingPressure.length){
    alerts.push({
      tone:"bad",
      code:"TIME_VOL_PRIORITY_REVIEW",
      title:"優先人工覆核：時間／期限 × 高波動下行風險重疊",
      text:"已觸發 "+timingPressure.map(a=>a.title).join("、")+"，且 RV20×觀察期限的 QQQ 下跌頻率高於 ALL 歷史基準。請重新核對整組 Put Ratio 的即時淨清算回補成本、短 Put Gamma／指派風險及尾部壓力；這是人工覆核提示，不是自動平倉指令，也不是 Put Ratio 虧損機率。"
    });
  }
  const timeOrPnl=alerts.some(a=>["PROFIT_TARGET_REACHED","AGE_20","DTE_7","VOL_DOWNSIDE_ELEVATED"].includes(a.code));
  const combinedStatus=!inputs.combinedReview?"ISOLATED_EVIDENCE":tail.status==="BLOCKED_TAIL_BUDGET"?"BLOCK_PUT_RATIO_ADDITION":timeOrPnl?"REVIEW_PUT_RATIO_SCENARIO":"RESEARCH_CONTEXT_ONLY";
  return {
    schemaVersion:"PUT_RATIO_RESEARCH_OVERLAY_OUTPUT_V1",
    evidenceStatus:valid.ok?"AVAILABLE_RESEARCH_ONLY":"PENDING",
    scenarioId:"PUT_RATIO_"+inputs.direction+"_N"+String(inputs.n),
    inputs,history:matched?{policyId:matched.id,episodes:matched.n,resolved:matched.resolved,winRatePct:matched.winRatePct,netPnlUsd:matched.netPnlUsd,expectancyUsd:matched.expectancyUsd,profitFactor:matched.profitFactor,worstTradeUsd:matched.worstTradeUsd,triggerCount:matched.triggerCount,triggerPct:matched.triggerPct,fallbackCount:matched.fallbackCount,markCoveragePct:matched.markCoveragePct,missingMarkSessions:matched.missingMarkSessions}:null,
    serialCurve:curve,tail,profitTarget:{navTargetUsd:navTarget,profitPct:inputs.profitPct,directFixedTargetUsd:fixedTarget,directPolicy:directTargetPolicy?{id:directTargetPolicy.id,winRatePct:directTargetPolicy.winRatePct,netPnlUsd:directTargetPolicy.netPnlUsd,triggerCount:directTargetPolicy.triggerCount,triggerPct:directTargetPolicy.triggerPct,fallbackCount:directTargetPolicy.fallbackCount,worstTradeUsd:directTargetPolicy.worstTradeUsd}:null,thresholdStudy:thresholdStudy?{targetUsd:thresholdStudy.targetUsd,counterfactualFirstMarkHitCount:thresholdStudy.counterfactualFirstMarkHitCount,counterfactualFirstHitWithin5Sessions:thresholdStudy.counterfactualFirstHitWithin5Sessions,counterfactualFirstHitAfter5Sessions:thresholdStudy.counterfactualFirstHitAfter5Sessions,actualPolicyTriggerCount:thresholdStudy.actualPolicyTriggerCount,actualPolicyTriggerPct:thresholdStudy.actualPolicyTriggerPct,medianTriggerAgeSessions:thresholdStudy.medianTriggerAgeSessions,medianSignalToActionSessions:thresholdStudy.medianSignalToActionSessions,forwardIfOriginal1x5Held:thresholdStudy.forwardIfOriginal1x5Held,sampleStatus:thresholdStudy.sampleStatus}:null},
    volatility:vol,alerts,combinedReview:{enabled:inputs.combinedReview,status:combinedStatus,primaryHybridActionMutation:false,primaryHybridTargetMutation:false,executionEnabled:false,reason:!inputs.combinedReview?"Research evidence is displayed separately; it is not included in this round's combined review.":combinedStatus==="BLOCK_PUT_RATIO_ADDITION"?"Do not add this Put Ratio scenario under the selected terminal-tail budget. Existing Frozen Hybrid targets and action are preserved.":combinedStatus==="REVIEW_PUT_RATIO_SCENARIO"?"Add the Put Ratio evidence to human review alongside the Frozen Hybrid decision; no automatic target mutation.":"Evidence is attached to this Hybrid review but does not authorize adding the research scenario."},
    manifest:s?.manifest||null,
    limitations:["Only LONG 1 : SHORT 5 has a directly replayed 62-episode option history; all other direction/N selections have no matched strategy win rate or strategy curve.","The serial equity curve is fixed one-unit, non-compounding, and not NAV-scaled. Missing marks stay unknown; observed MaxDD may understate hidden drawdown.","Option source is an EOD preservation mirror with conservative quote-side marks, not confirmed exchange fills; exact quote times are unverified.","QQQ RV20 downside frequency is underlying-only and is not a Put Ratio loss probability.","Margin, interim liquidation, assignment, forced liquidation, cash and quote-depth constraints are not verified. Deployment remains BLOCKED."]
  };
}
const api={validateSnapshot,evaluate,drawdownStats,volatility,targetForAmount,policyById,money,pct};
if(typeof module!=="undefined"&&module.exports)module.exports=api;else root.PutRatioEvidenceV1=api;
})(typeof window!=="undefined"?window:this);
