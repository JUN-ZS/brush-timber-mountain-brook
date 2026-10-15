(function(root){"use strict";
const MULTIPLIER=100;
function num(v){if(v===null||v===undefined||v==="")return null;const n=Number(v);return Number.isFinite(n)?n:null}
function whole(v){const n=num(v);return n!==null&&Number.isInteger(n)?n:null}
function money(v){return Number.isFinite(v)?Math.round((v+Number.EPSILON)*100)/100:null}
function hasZone(v){return typeof v==="string"&&/(?:Z|[+-]\d{2}:\d{2})$/i.test(v.trim())}
function quoteQuality(asOf,nowMs){
 if(!asOf||!hasZone(asOf)||!Number.isFinite(Date.parse(asOf)))return{status:"TIME_UNVERIFIED",ageMs:null,note:"Quote timestamp is absent or lacks explicit timezone; calculation is scenario-only."};
 const ageMs=(Number.isFinite(nowMs)?nowMs:Date.now())-Date.parse(asOf);
 if(ageMs < -300000)return{status:"FUTURE_TIMESTAMP",ageMs,note:"Timestamp is materially in the future; do not treat as current."};
 if(ageMs>900000)return{status:"STALE_OVER_15M",ageMs,note:"Quote is over 15 minutes old; current-exit interpretation is not qualified."};
 return{status:"TIME_WITHIN_15M_UNAUTHENTICATED",ageMs:Math.max(0,ageMs),note:"Timestamp is within 15 minutes, but source, displayed size and executability are not independently authenticated."};
}
function terminalValue(lq,lk,sq,sk,s){return MULTIPLIER*(lq*Math.max(lk-s,0)-sq*Math.max(sk-s,0))}
function evaluate(input,nowMs){
 const d=input||{},nav=num(d.nav),thresholdPct=num(d.thresholdPct);
 const orientation=d.orientation==="long-heavy"?"long-heavy":d.orientation==="short-heavy"?"short-heavy":null;
 const n=whole(d.ratioN),packages=whole(d.packages),lk=num(d.longStrike),sk=num(d.shortStrike);
 const le=num(d.longEntryPrice),se=num(d.shortEntryPrice),lb=num(d.currentLongBid),sa=num(d.currentShortAsk);
 const commission=num(d.commissionPerContractSide),slippage=num(d.closeSlippagePerShare),dte=whole(d.dte),held=whole(d.heldSessions),spot=num(d.spot);
 const thresholds=[0.5,1,2].map(p=>({pct:p,usd:nav>0?money(nav*p/100):null}));
 const targetUsd=nav>0&&thresholdPct>0?money(nav*thresholdPct/100):null;
 const base={ready:false,status:"PENDING",error:"",nav:nav>0?nav:null,thresholdPct,targetUsd,oneThousandPct:nav>0?1000/nav*100:null,thresholds,orientation,ratioN:n,packages,dte,baselineDteActive:dte!==null?dte<=7:null,heldSessions:held,
  timing:held!==null?{first3:held>=0&&held<=3,first5:held>=0&&held<=5,note:"Holding-day window is context only; it does not fire an exit rule or predict future marks."}:null,
  quoteQuality:quoteQuality(d.quoteAsOf,nowMs),disclaimer:"Manual what-if arithmetic only. A recent timestamp does not authenticate the source or prove executable size. No broker order is sent."};
 if(!(nav>0)||!(thresholdPct>0)||thresholdPct>100){base.error="Enter positive NAV and a threshold from >0% through 100% NAV.";return base}
 if(!orientation||!(n>=1&&n<=100)||!(packages>=1&&packages<=100000)||lk===null||sk===null||!(lk>0&&sk>0)||commission===null||commission<0||slippage===null||slippage<0||dte===null||dte<0||dte>1000||held===null||held<0){base.error="Need a valid direction, integer N/package count, positive strikes, non-negative costs, DTE and held-session count.";return base}
 if(!(orientation==="short-heavy"?lk>sk:sk>lk)){base.error=orientation==="short-heavy"?"SHORT-heavy geometry requires Long Put strike > Short Put strike.":"LONG-heavy geometry requires Short Put strike > Long Put strike.";return base}
 if([le,se,lb,sa].some(v=>v===null||v<0)||!(le>0)||!(se>0)){base.error="Enter opening reference/average fill prices plus current Long Put Bid and Short Put Ask. Missing marks stay PENDING.";return base}
 const lp=orientation==="short-heavy"?1:n,sp=orientation==="short-heavy"?n:1,lq=lp*packages,sq=sp*packages,contracts=lq+sq;
 const lpnl=lq*MULTIPLIER*(lb-le),spnl=sq*MULTIPLIER*(se-sa),gross=lpnl+spnl;
 const entryFees=contracts*commission,exitFees=contracts*commission,slipClose=contracts*MULTIPLIER*slippage;
 const full=money(gross-entryFees-exitFees-slipClose),pct=full/nav*100;
 const state=full>=targetUsd?"PROFIT_TARGET_REACHED":full<=-targetUsd?"LOSS_BUDGET_REACHED":"WITHIN_CANDIDATE_BAND";
 const trimEach=orientation==="short-heavy"?Math.max(0,n-1):1,remainSP=orientation==="short-heavy"?Math.min(1,n):0;
 const trimQty=trimEach*packages,rlq=lq,rsq=remainSP*packages,remainContracts=rlq+rsq;
 const trimGross=trimQty*MULTIPLIER*(se-sa),trimNet=money(trimGross-trimQty*2*commission-trimQty*MULTIPLIER*slippage);
 const residualGross=rlq*MULTIPLIER*(lb-le)+rsq*MULTIPLIER*(se-sa);
 const residualNet=money(residualGross-remainContracts*2*commission-remainContracts*MULTIPLIER*slippage);
 const combined=money(trimNet+residualNet),markValue=rlq*MULTIPLIER*lb-rsq*MULTIPLIER*sa,high=Math.max(lk,sk),low=Math.min(lk,sk);
 const settlements=Array.from(new Set([0,low,high,Math.max(spot>0?spot:high,high)*1.25])).sort((a,b)=>a-b);
 const scenarios=settlements.map(s=>({settlement:s,netIntrinsicUsd:money(terminalValue(rlq,lk,rsq,sk,s)),changeFromCurrentMarkUsd:money(terminalValue(rlq,lk,rsq,sk,s)-markValue)}));
 const worst=scenarios.reduce((v,r)=>Math.min(v,r.changeFromCurrentMarkUsd),0),tailLoss=money(Math.max(0,-worst));
 base.ready=true;base.status=state;base.error="";base.longQty=lq;base.shortQty=sq;base.totalContracts=contracts;
 base.grossPnlUsd=money(gross);base.longGrossPnlUsd=money(lpnl);base.shortGrossPnlUsd=money(spnl);base.fullClosePnlUsd=full;base.pnlPctNav=pct;base.pnlVsThresholdPct=pct/thresholdPct*100;base.thresholdState=state;base.thresholdHit=state!=="WITHIN_CANDIDATE_BAND";
 base.entryCommissionUsd=money(entryFees);base.exitCommissionUsd=money(exitFees);base.fullCloseSlippageUsd=money(slipClose);
 base.baselineDteLabel=dte<=7?"DTE≤7 baseline window ACTIVE (comparator only)":"DTE≤7 baseline window not active";
 base.fullClose={action:"CLOSE_ALL",realizedPnlAfterCostsUsd:full,realizedPnlPctNav:pct,remainingLongQty:0,remainingShortQty:0,remainingContracts:0,residualTailLossFromCurrentMarkUsd:0};
 base.trimShort={action:orientation==="short-heavy"?"BUY_TO_CLOSE_EXCESS_SHORTS":"BUY_TO_CLOSE_THE_SHORT",
  description:orientation==="short-heavy"?(n===1?"N=1: no excess SHORT can be reduced; compare CLOSE ALL or DTE≤7 baseline.":"Buy to close "+trimEach+" SHORT per package; retain 1 SHORT + the LONG."):"Buy to close 1 SHORT per package; retain N LONG puts.",
  shortContractsToClose:trimQty,remainingLongQty:rlq,remainingShortQty:rsq,remainingContracts,
  realizedPnlOnTrimmedShortsAfterCostsUsd:trimNet,residualOpenPnlAfterCostsReservedUsd:residualNet,combinedPnlWithResidualExitCostReservedUsd:combined,combinedPnlPctNavWithResidualExitCostReserved:combined/nav*100,
  residualMarkValueUsd:money(markValue),residualWorstExpiryLossFromCurrentMarkUsd:tailLoss,residualWorstExpiryLossPctNav:tailLoss/nav*100,
  riskProfile:orientation==="short-heavy"?(n===1?"N=1: no excess SHORT can be trimmed; both legs remain.":"Retains 1 SHORT + 1 LONG per package; tail risk is reduced, not erased under every path."):"Closes the single SHORT per package and retains N LONG puts; residual risk is long premium exposure.",expiryScenarios:scenarios};
 base.quoteQuality=quoteQuality(d.quoteAsOf,nowMs);base.displayStatus=base.quoteQuality.status==="TIME_WITHIN_15M_UNAUTHENTICATED"?"ARITHMETIC_READY_UNAUTHENTICATED":"SCENARIO_ONLY_TIMESTAMP_GATE_NOT_MET";
 base.purpose="NAV ruler for position P&L, candidate threshold, full close vs short trim, residual contracts and expiry-only tail sensitivity; does not determine an optimum.";
 return base;
}
const API={MULTIPLIER,evaluate,quoteQuality};root.PutRatioExitSensitivityV1=API;if(typeof module!=="undefined"&&module.exports)module.exports=API;
})(typeof globalThis!=="undefined"?globalThis:this);
