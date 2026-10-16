window.HybridEngineV3 = (() => {
  const POLICY = Object.freeze({
    engineVersion: "V3-FREE-VX-PROVENANCE-2",
    policyVersion: "ORIGINAL_HYBRID_BASELINE_FROZEN",
    corePct: 42, vxxNormalPct: 18, vxxHighPct: 10, vxxCallBudgetPct: 2, qqqCallBudgetPct: 1.2,
    vixHigh: 28, termSafe: 5, maxTermAgeDays: 4, qqqRollDte: 14, qqqRollDelta: 0.16, vxxRollDte: 14, vxxRollDelta: 0.20,
    optionTargetDte: 45, maxOptionQuoteAgeDays: 1,
  });
  const num=(v,d=null)=>{if(v===null||v===undefined||v==="")return d;const x=parseFloat(String(v).replace(/,/g,""));return Number.isFinite(x)?x:d;};
  function term(m1,m2){return Number.isFinite(m1)&&Number.isFinite(m2)&&m1!==0?((m2-m1)/m1)*100:null;}
  function parseDay(v){
    if(typeof v!=="string"||!/^\d{4}-\d{2}-\d{2}$/.test(v))return null;
    const ms=Date.parse(v+"T00:00:00Z");
    return Number.isFinite(ms)&&new Date(ms).toISOString().slice(0,10)===v?ms:null;
  }
  function daysBetween(a,b){const x=parseDay(a),y=parseDay(b);if(x===null||y===null)return null;return Math.abs(y-x)/86400000;}
  function dataHealth(d){
    const hasSpot=[d.qqq,d.vxx,d.vix].every(Number.isFinite),hasTerm=Number.isFinite(d.m1)&&Number.isFinite(d.m2)&&Number.isFinite(d.s);
    if(!hasSpot||!hasTerm)return{status:"BLOCKED",label:"DATA BLOCKED",reason:"Required spot or VX term field missing."};
    const todayMs=parseDay(d.today),termMs=parseDay(d.termAsOf),spotMs=parseDay(d.spotAsOf);
    if(todayMs===null||termMs===null||spotMs===null)return{status:"PENDING",label:"TIMESTAMP PENDING",reason:"Required today, term as-of, and spot as-of dates must be valid ISO calendar dates; missing/invalid time is not fresh."};
    if(termMs>todayMs||spotMs>todayMs)return{status:"PENDING",label:"TIMESTAMP PENDING",reason:"A source as-of date is in the future relative to the decision date."};
    const age=(todayMs-termMs)/86400000,asofGap=Math.abs(spotMs-termMs)/86400000;
    if(age>POLICY.maxTermAgeDays)return{status:"STALE",label:"DATA STALE",ageDays:age,reason:"VX term source is older than the permitted operator cadence."};
    if(asofGap>2)return{status:"MIXED",label:"AS-OF MIXED",ageDays:asofGap,reason:"Spot and term inputs are materially out of sync; review before acting."};
    return{status:"FRESH",label:"DATA FRESH",ageDays:age,reason:"Required fields are present and within the configured cadence."};
  }
  function derive(d){
    const health=dataHealth(d);
    if(health.status==="BLOCKED")return{state:"DATA BLOCKED",action:"HOLD",gate:"BLOCKED",targets:null,blocked:true,health,reason:"Data incomplete: preserve current position and do not invent a risk action."};
    if(health.status==="PENDING")return{state:"TIMESTAMP PENDING",action:"HOLD",gate:"PENDING",targets:null,blocked:true,health,reason:health.reason};
    if(health.status==="STALE"||health.status==="MIXED")return{state:health.status==="STALE"?"DATA STALE":"AS-OF MIXED",action:"HOLD",gate:health.status,targets:null,blocked:true,health,reason:health.reason};
    const high=d.vix>=POLICY.vixHigh,back=d.s<=0,thin=d.s<=POLICY.termSafe;let state,action,gate,reason;
    if(high&&back){state="SHOCK";action="REDUCE";gate="CUT";reason="High VIX + VX backwardation: cut VXX seller risk first; preserve QQQ core.";}
    else if(back){state="PRE-SHOCK";action="REDUCE";gate="CUT";reason="VX backwardation: carry gate is broken; no new short-vol deployment.";}
    else if(high){state="PRE-SHOCK";action="REDUCE";gate="CAP";reason="VIX is high: cap seller exposure and stop adding new carry.";}
    else if(thin){state="WEAKENING";action="HOLD";gate="WATCH";reason="Contango is positive but thin: keep core, do not add short-vol carry.";}
    else{state="CARRY";action="BUY";gate="OPEN";reason="Contango is healthy and VIX is below the high threshold: restore carry legs toward baseline target.";}
    const vxxBase=high?POLICY.vxxHighPct:POLICY.vxxNormalPct;
    return{state,action,gate,reason,blocked:false,health,targets:{qqqCorePct:POLICY.corePct,vxxPct:back?0:vxxBase,vxxCallBudgetPct:back||high?0:POLICY.vxxCallBudgetPct,qqqCallBudgetPct:back||high?0:POLICY.qqqCallBudgetPct},reasons:{"VIX":high?">= 28":"< 28","S":back?"<= 0":(thin?"<= 5%":"> 5%")}};
  }
  function optionQty(nav,budgetPct,credit){return nav>0&&budgetPct>0&&Number.isFinite(credit)&&credit>0?Math.max(0,Math.floor(nav*(budgetPct/100)/(credit*100))):0;}
  function bsCallDelta(spot,strike,dte,iv,rate=0){
    if(![spot,strike,dte,iv].every(Number.isFinite)||spot<=0||strike<=0||dte<=0||iv<=0)return null;
    const t=dte/365,sigma=Math.max(1e-9,iv),d1=(Math.log(spot/strike)+(rate+0.5*sigma*sigma)*t)/(sigma*Math.sqrt(t));
    const erf=x=>{const sign=x<0?-1:1,ax=Math.abs(x),a1=0.254829592,a2=-0.284496736,a3=1.421413741,a4=-1.453152027,a5=1.061405429,p=0.3275911,tt=1/(1+p*ax);return sign*(1-(((((a5*tt+a4)*tt)+a3)*tt+a2)*tt+a1)*tt*Math.exp(-ax*ax));};
    return 0.5*(1+erf(d1/Math.sqrt(2)));
  }
  function expiryMs(v){if(typeof v==="number"&&Number.isFinite(v))return v<1e12?v*1000:v;if(typeof v==="string"&&/^\\s*\\d+(?:\\.\\d+)?\\s*$/.test(v)){const nval=Number(v);return nval<1e12?nval*1000:nval;}if(v instanceof Date)return v.getTime();if(typeof v==="string"&&v.trim()){const x=Date.parse(v);return Number.isFinite(x)?x:null;}return null;}
  function normalizeOptionChain(payload){if(Array.isArray(payload))return payload;if(payload&&Array.isArray(payload.calls))return payload.calls;const result=payload?.optionChain?.result?.[0],opts=result?.options?.[0];return Array.isArray(opts?.calls)?opts.calls:[];}
  function candidateFromChain(payload,spot,targetDelta=0.10,targetDte=POLICY.optionTargetDte,asOf=null,quoteMeta={}){
    if(!Number.isFinite(spot)||spot<=0)return null;
    const chain=normalizeOptionChain(payload);
    if(!chain.length)return null;
    const asOfMs=parseDay(asOf),quoteStamp=typeof quoteMeta?.retrievedAt==="string"?Date.parse(quoteMeta.retrievedAt):null;
    const quoteDay=typeof quoteMeta?.retrievedAt==="string"?parseDay(quoteMeta.retrievedAt.slice(0,10)):null;
    const root=String(quoteMeta?.symbol||"").trim().toUpperCase(),source=String(quoteMeta?.source||"").trim();
    if(asOfMs===null||!Number.isFinite(quoteStamp)||quoteDay===null||!root||!source)return null;
    const quoteAgeDays=(asOfMs-quoteDay)/86400000;
    if(quoteAgeDays<0||quoteAgeDays>POLICY.maxOptionQuoteAgeDays)return null;
    const identity=(symbol,strike,expiry)=>{
      const m=/^([A-Z]{1,6})(\d{6})([CP])(\d{8})$/.exec(String(symbol||"").trim().toUpperCase());
      if(!m||m[1]!==root)return false;
      const yy=Number(m[2].slice(0,2)),year=yy>=80?1900+yy:2000+yy,month=Number(m[2].slice(2,4)),day=Number(m[2].slice(4,6));
      const symbolExpiry=Date.UTC(year,month-1,day),expiryDay=new Date(expiry).toISOString().slice(0,10);
      const encodedStrike=Number(m[4])/1000;
      return Number.isFinite(symbolExpiry)&&new Date(symbolExpiry).toISOString().slice(0,10)===expiryDay&&Math.abs(encodedStrike-strike)<1e-6;
    };
    const rows=chain.map(x=>{
      const exp=expiryMs(x.expiration??x.expiry??x.expirationDate),dteDate=Number.isFinite(exp)?Math.max(0,(exp-asOfMs)/86400000):null;
      const dte=Number.isFinite(num(x.days))?num(x.days):dteDate,strike=num(x.strike),bid=num(x.bid),ask=num(x.ask);
      const bidSize=num(x.bidSize),askSize=num(x.askSize),iv=num(x.impliedVolatility),rawDelta=num(x.delta);
      const delta=Number.isFinite(rawDelta)?rawDelta:bsCallDelta(spot,strike,dte,iv);
      const contractSymbol=String(x.contractSymbol??x.symbol??"").trim().toUpperCase();
      const identityValid=Number.isFinite(exp)&&Number.isFinite(strike)&&identity(contractSymbol,strike,exp);
      const quoteValid=Number.isFinite(bid)&&Number.isFinite(ask)&&bid>=0&&ask>0&&bid<=ask&&Number.isFinite(bidSize)&&bidSize>0&&Number.isFinite(askSize)&&askSize>0;
      return{...x,contractSymbol,strike,bid,ask,bidSize,askSize,dte,delta,expiryMs:exp,identityValid,quoteValid,deltaSource:Number.isFinite(rawDelta)?"INPUT":"BS_ESTIMATE"};
    }).filter(x=>x.identityValid&&x.quoteValid&&Number.isFinite(x.dte)&&x.dte>=14&&x.dte<=120&&Number.isFinite(x.delta)&&x.delta>0&&x.delta<=0.25&&x.strike>spot);
    if(!rows.length)return null;
    const expiries=[...new Set(rows.map(x=>x.expiryMs))].sort((a,b)=>Math.abs((a-asOfMs)/86400000-targetDte)-Math.abs((b-asOfMs)/86400000-targetDte));
    if(!expiries.length)return null;
    const pool=rows.filter(x=>x.expiryMs===expiries[0]);
    pool.sort((a,b)=>Math.abs(a.delta-targetDelta)-Math.abs(b.delta-targetDelta));
    const short=pool[0];
    if(!short)return null;
    const longs=pool.filter(x=>x.expiryMs===short.expiryMs&&x.strike>short.strike).sort((a,b)=>Math.abs(a.strike-short.strike*1.015)-Math.abs(b.strike-short.strike*1.015));
    if(!longs.length)return null;
    const long=longs[0],credit=short.bid-long.ask,width=long.strike-short.strike,multiplier=100;
    if(short.expiryMs!==long.expiryMs||short.contractSymbol===long.contractSymbol||!Number.isFinite(credit)||credit<=0||!Number.isFinite(width)||width<=credit)return null;
    return{
      shortContractSymbol:short.contractSymbol,longContractSymbol:long.contractSymbol,
      shortStrike:short.strike,longStrike:long.strike,dte:short.dte,delta:short.delta,deltaSource:short.deltaSource,
      credit,shortBid:short.bid,shortAsk:short.ask,longBid:long.bid,longAsk:long.ask,
      shortBidSize:short.bidSize,shortAskSize:short.askSize,longBidSize:long.bidSize,longAskSize:long.askSize,
      width,contractMultiplier:multiplier,maxLossPerSpread:(width-credit)*multiplier,
      expiration:new Date(short.expiryMs).toISOString().slice(0,10),quoteAsOf:quoteMeta.retrievedAt,
      quoteAgeDays,source,contractIdentityValidated:true,quoteValidated:true,sizingAvailable:true
    };
  }
  function optionSizing(nav,budgetPct,candidate,constraints={}){
    const n=num(nav),pct=num(budgetPct),credit=num(candidate?.credit),width=num(candidate?.width),multiplier=num(candidate?.contractMultiplier);
    const creditBudget=Number.isFinite(n)&&Number.isFinite(pct)&&n>=0&&pct>=0?n*pct/100:null;
    const creditQty=Number.isFinite(creditBudget)?optionQty(n,pct,credit):null;
    const maxLossPerSpread=Number.isFinite(width)&&Number.isFinite(credit)&&Number.isFinite(multiplier)&&width>credit&&credit>0&&multiplier>0?(width-credit)*multiplier:null;
    const base={
      budgetSemantics:"UNRESOLVED_FOR_DEPLOYMENT",
      legacyFormulaSemantics:"PREMIUM_CREDIT_CAP_ONLY",
      creditBudgetAmount:creditBudget,
      creditBudgetQuantity:creditQty,
      maxLossPerSpread,
      maxLossBudgetAmount:null,
      maxLossBudgetQuantity:null,
      interimStressBudgetAmount:null,
      interimStressLossPerSpread:null,
      quantity:null,
      recommendedQuantity:null,
      executable:false,
      reason:"Credit-derived quantity is theoretical only; a separate expiry-loss/interim-stress budget and verified cash, margin, quote depth, and assignment constraints are required."
    };
    if(Number.isFinite(pct)&&pct===0)return{...base,status:"POLICY_TARGET_ZERO",budgetSemantics:"ZERO_BY_FROZEN_POLICY",quantity:0,recommendedQuantity:0,reason:"Frozen regime explicitly sets this option sleeve target to zero; executable exit capacity remains a separate quote/margin question."};
    if(!Number.isFinite(n)||n<=0||!Number.isFinite(pct)||pct<0)return{...base,status:"BLOCKED_BUDGET_INPUT",reason:"NAV and the configured premium-credit budget percent must be valid."};
    if(!candidate||candidate.contractIdentityValidated!==true||candidate.quoteValidated!==true||candidate.sizingAvailable!==true)return{...base,status:"PENDING_CANDIDATE",reason:"No fully identified same-expiry spread with valid bid/ask and quote sizes; retain current position target."};
    if(maxLossPerSpread===null)return{...base,status:"BLOCKED_MAX_LOSS_UNKNOWN",reason:"Spread width, net credit, or contract multiplier is invalid; maximum expiry loss is unknown."};
    const riskPct=num(constraints.maxLossBudgetPct),stressPct=num(constraints.interimStressBudgetPct),stressLoss=num(constraints.interimStressLossPerSpread);
    if(constraints.budgetSemantics!=="MAX_EXPIRY_LOSS"||!Number.isFinite(riskPct)||riskPct<0)return{...base,status:"PENDING_RISK_BUDGET",reason:"The legacy percent only sizes premium credit. Explicit MAX_EXPIRY_LOSS budget semantics and percentage are required before recommending a quantity."};
    const maxLossBudgetAmount=n*riskPct/100,maxLossBudgetQuantity=Math.floor(maxLossBudgetAmount/maxLossPerSpread);
    const stressBudgetAmount=Number.isFinite(stressPct)&&stressPct>=0?n*stressPct/100:null;
    const baseWithRisk={...base,budgetSemantics:"MAX_EXPIRY_LOSS",maxLossBudgetAmount,maxLossBudgetQuantity,interimStressBudgetAmount:stressBudgetAmount,interimStressLossPerSpread:stressLoss};
    if(!Number.isFinite(stressPct)||stressPct<0||!Number.isFinite(stressLoss)||stressLoss<=0||constraints.interimStressVerified!==true)return{...baseWithRisk,status:"PENDING_INTERIM_STRESS",reason:"Interim mark-to-market stress budget and loss-per-spread are not verified; expiry loss alone is insufficient."};
    const interimStressQuantity=Math.floor(stressBudgetAmount/stressLoss);
    if(!Number.isInteger(constraints.cashMaxQty)||constraints.cashMaxQty<0)return{...baseWithRisk,status:"BLOCKED_CASH_CAP",interimStressQuantity,reason:"A verified available-cash / buying-power quantity cap is required."};
    if(!Number.isInteger(constraints.brokerMarginMaxQty)||constraints.brokerMarginMaxQty<0||constraints.marginVerified!==true)return{...baseWithRisk,status:"BLOCKED_MARGIN_UNKNOWN",interimStressQuantity,reason:"Broker margin capacity is missing or unverified; theoretical quantity is not executable capacity."};
    if(constraints.assignmentVerified!==true)return{...baseWithRisk,status:"BLOCKED_ASSIGNMENT_UNKNOWN",interimStressQuantity,reason:"Short-option assignment/exercise handling is not verified."};
    if(constraints.quoteExecutionVerified!==true)return{...baseWithRisk,status:"BLOCKED_EXECUTION_QUOTE_UNVERIFIED",interimStressQuantity,reason:"Quote sides and sizes are recorded, but executable quote evidence is not explicitly verified."};
    const entryDepthQuantity=Math.floor(Math.min(candidate.shortBidSize,candidate.longAskSize));
    const exitDepthQuantity=Math.floor(Math.min(candidate.shortAskSize,candidate.longBidSize));
    const caps={expiryLoss:maxLossBudgetQuantity,interimStress:interimStressQuantity,cash:constraints.cashMaxQty,brokerMargin:constraints.brokerMarginMaxQty,entryDepth:entryDepthQuantity};
    const quantity=Math.max(0,Math.min(...Object.values(caps)));
    return{...baseWithRisk,status:quantity>0?"READY":"CAPACITY_ZERO",maxLossBudgetQuantity,interimStressQuantity,entryDepthQuantity,exitDepthQuantity,caps,quantity,recommendedQuantity:quantity,executable:quantity>0,reason:quantity>0?"Quantity is capped by the strictest verified risk/cash/margin/depth limit; human review still required.":"At least one verified capacity limit allows zero complete spreads."};
  }
  function targetLedger(d,e,ledger,candidates={},constraints={}){
    const cur={qqqShares:num(ledger.qqqShares,0),vxxPct:num(ledger.vxxPct,0),qqqCalls:num(ledger.qqqCalls,0),vxxCalls:num(ledger.vxxCalls,0)};
    if(e.blocked){
      const unresolvedRisk=[
        {leg:"QQQ CORE",current:cur.qqqShares,unit:"shares"},
        {leg:"VXX UNDERLYING SHORT",current:cur.vxxPct,unit:"% NAV"},
        {leg:"QQQ FAR CALL",current:cur.qqqCalls,unit:"spreads"},
        {leg:"VXX CALL CREDIT SPREAD",current:cur.vxxCalls,unit:"spreads"}
      ].filter(x=>Number.isFinite(x.current)&&x.current>0);
      return{current:cur,target:{...cur},deltas:{qqqShares:0,vxxPct:0,qqqCalls:0,vxxCalls:0},blocked:true,riskStatus:unresolvedRisk.length?"UNRESOLVED_CURRENT_EXPOSURE":"NO_RECORDED_OPEN_EXPOSURE",unresolvedRisk,executionAllowed:false,reason:"Data/capacity gate is blocked. Current positions are preserved, not risk-cleared; no automatic reduction is permitted." ,sizing:{qqqCalls:{status:"BLOCKED_DATA_GATE",quantity:null,executable:false},vxxCalls:{status:"BLOCKED_DATA_GATE",quantity:null,executable:false}}};
    }
    const nav=num(ledger.nav,0),qqqPrice=num(d.qqq,0),rawShares=nav>0&&qqqPrice>0?(nav*e.targets.qqqCorePct/100)/qqqPrice:cur.qqqShares,buyAllowed=e.action==="BUY";
    const qs=optionSizing(nav,e.targets.qqqCallBudgetPct,candidates.qqq||null,constraints.qqq||{});
    const vs=optionSizing(nav,e.targets.vxxCallBudgetPct,candidates.vxx||null,constraints.vxx||{});
    const qTarget=e.targets.qqqCallBudgetPct===0?0:(buyAllowed&&qs.status==="READY"?qs.quantity:cur.qqqCalls);
    const vTarget=e.targets.vxxCallBudgetPct===0?0:(buyAllowed&&vs.status==="READY"?vs.quantity:cur.vxxCalls);
    const target={qqqShares:buyAllowed?Math.floor(rawShares):cur.qqqShares,vxxPct:buyAllowed?e.targets.vxxPct:Math.min(cur.vxxPct,e.targets.vxxPct),qqqCalls:qTarget,vxxCalls:vTarget};
    const deltas={qqqShares:target.qqqShares-cur.qqqShares,vxxPct:target.vxxPct-cur.vxxPct,qqqCalls:target.qqqCalls-cur.qqqCalls,vxxCalls:target.vxxCalls-cur.vxxCalls};
    const unresolvedTargets=[];
    if(e.targets.qqqCallBudgetPct>0&&qs.status!=="READY")unresolvedTargets.push({leg:"QQQ FAR CALL",current:cur.qqqCalls,status:qs.status,reason:qs.reason});
    if(e.targets.vxxCallBudgetPct>0&&vs.status!=="READY")unresolvedTargets.push({leg:"VXX CALL CREDIT SPREAD",current:cur.vxxCalls,status:vs.status,reason:vs.reason});
    return{current:cur,target,deltas,blocked:false,riskStatus:unresolvedTargets.length?"OPTION_TARGET_PENDING":"TARGETS_CALCULATED",unresolvedTargets,executionAllowed:false,reason:unresolvedTargets.length?"Current option quantities are preserved where the desired quantity is not defensible; theoretical credit sizing is not a deployable target.":"Targets are calculated from verified capacity inputs and still require human review.",sizing:{qqqCalls:qs,vxxCalls:vs}};
  }
  function actionRows(book){return Object.entries(book.deltas).map(([key,diff])=>({key,diff,kind:Math.abs(diff)<1e-9?"HOLD":diff>0?"ADD":"REDUCE"}));}
  function triggers(d,e,opt={}){
    const rows=[];
    if(Number.isFinite(d.s)){rows.push({id:"S_ZERO",label:"VX term to zero",value:d.s<=0?"TRIGGERED":d.s.toFixed(2)+"% → 0",fire:d.s<=0,priority:"HIGH"});rows.push({id:"S_SAFE",label:"VX carry line",value:d.s<=POLICY.termSafe?d.s.toFixed(2)+"% ≤ 5%":(d.s-POLICY.termSafe).toFixed(2)+"% above",fire:d.s<=POLICY.termSafe,priority:"MED"});}
    if(Number.isFinite(d.vix))rows.push({id:"VIX_28",label:"VIX high line",value:d.vix>=POLICY.vixHigh?"TRIGGERED":(POLICY.vixHigh-d.vix).toFixed(2)+" away",fire:d.vix>=POLICY.vixHigh,priority:"HIGH"});
    const qdte=num(opt.qqqDte),qdelta=num(opt.qqqDelta),vdte=num(opt.vxxDte),vdelta=num(opt.vxxDelta);
    rows.push({id:"QQQ_ROLL",label:"QQQ far call roll",value:"DTE "+(Number.isFinite(qdte)?qdte:"—")+" · Δ "+(Number.isFinite(qdelta)?qdelta.toFixed(2):"—"),fire:(Number.isFinite(qdte)&&qdte<=POLICY.qqqRollDte)||(Number.isFinite(qdelta)&&qdelta>=POLICY.qqqRollDelta),priority:"MED"});
    rows.push({id:"VXX_ROLL",label:"VXX call roll",value:"DTE "+(Number.isFinite(vdte)?vdte:"—")+" · Δ "+(Number.isFinite(vdelta)?vdelta.toFixed(2):"—"),fire:(Number.isFinite(vdte)&&vdte<=POLICY.vxxRollDte)||(Number.isFinite(vdelta)&&vdelta>=POLICY.vxxRollDelta)||e.state==="SHOCK",priority:"HIGH"});
    return rows;
  }
  return{POLICY,num,term,parseDay,dataHealth,derive,optionQty,normalizeOptionChain,candidateFromChain,optionSizing,targetLedger,actionRows,triggers};
})();