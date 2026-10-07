window.HybridEngineV3 = (() => {
  const POLICY = Object.freeze({
    engineVersion: "V3-FREE-VX-PROVENANCE-2",
    policyVersion: "ORIGINAL_HYBRID_BASELINE_FROZEN",
    corePct: 42, vxxNormalPct: 18, vxxHighPct: 10, vxxCallBudgetPct: 2, qqqCallBudgetPct: 1.2,
    vixHigh: 28, termSafe: 5, maxTermAgeDays: 4, qqqRollDte: 14, qqqRollDelta: 0.16, vxxRollDte: 14, vxxRollDelta: 0.20,
    optionTargetDte: 45,
  });
  const num=(v,d=null)=>{if(v===null||v===undefined||v==="")return d;const x=parseFloat(String(v).replace(/,/g,""));return Number.isFinite(x)?x:d;};
  function operatorNumber(v,{allowZero=true,min=0}={}){
    if(v===null||v===undefined||String(v).trim()==="")return{status:"EMPTY",value:null};
    const n=Number(String(v).replace(/,/g,""));
    if(!Number.isFinite(n))return{status:"INVALID",value:null};
    if((!allowZero&&n===0)||n<min)return{status:"INVALID",value:null};
    return{status:"VALUE",value:n};
  }
  function term(m1,m2){return Number.isFinite(m1)&&Number.isFinite(m2)&&m1!==0?((m2-m1)/m1)*100:null;}
  // F1 — dates are proof of freshness. Only real YYYY-MM-DD calendar days are accepted.
  function isoDay(v){
    if(typeof v!=="string")return null;
    const s=v.trim();
    if(!/^\d{4}-\d{2}-\d{2}$/.test(s))return null;
    const t=Date.parse(s+"T00:00:00Z");
    if(!Number.isFinite(t)||new Date(t).toISOString().slice(0,10)!==s)return null;
    return s;
  }
  function daysBetween(a,b){if(!a||!b)return null;const x=new Date(a+"T00:00:00Z").getTime(),y=new Date(b+"T00:00:00Z").getTime();if(!Number.isFinite(x)||!Number.isFinite(y))return null;return Math.abs(y-x)/86400000;}
  // Calendar days remaining from today → expiry (UTC YYYY-MM-DD). Past expiry → 0. Missing/invalid → null.
  function dteFromExpiry(expiry,today){
    if(expiry===null||expiry===undefined||today===null||today===undefined)return null;
    const exp=String(expiry).trim(),tod=String(today).trim();
    if(!/^\d{4}-\d{2}-\d{2}$/.test(exp)||!/^\d{4}-\d{2}-\d{2}$/.test(tod))return null;
    const x=new Date(exp+"T00:00:00Z").getTime(),y=new Date(tod+"T00:00:00Z").getTime();
    if(!Number.isFinite(x)||!Number.isFinite(y))return null;
    const days=Math.round((x-y)/86400000);
    return days<0?0:days;
  }
  // Cell 13 A — cadence mix: delayed settlement term + live last spot is not silently plain FRESH.
  function classifyTermCadence(d){
    const src=String(d.term_source||d.termSource||"").toUpperCase();
    const prov=d.provenance&&typeof d.provenance==="object"?d.provenance:{};
    const blob=[src,prov.m1,prov.m2,prov.term_slope].map(x=>String(x||"").toUpperCase()).join(" ");
    if(blob.includes("CBOE")||blob.includes("DELAYED"))return"DELAYED_SETTLEMENT";
    if(blob.includes("OPEND")||blob.includes("LIVE"))return"LIVE";
    if(src.trim())return"LIVE";
    return null;
  }
  function classifySpotCadence(d){
    const prov=d.provenance&&typeof d.provenance==="object"?d.provenance:{};
    const spotSrc=String(d.spot_source||d.spotSource||"").toUpperCase();
    const blob=["qqq","vxx","vix"].map(k=>String(prov[k]||"").toUpperCase()).concat(spotSrc).join(" ");
    if(blob.includes("OPEND")||blob.includes("YAHOO")||blob.includes("LAST"))return"LAST";
    return null;
  }
  function sourceCadence(d){
    const termCadence=classifyTermCadence(d);
    const spotCadence=classifySpotCadence(d);
    // Pain #7: MIXED_SOURCE is delayed settlement term vs live last spot (not live-vs-live).
    const sourceMix=(termCadence==="DELAYED_SETTLEMENT"&&spotCadence==="LAST")?"MIXED_SOURCE":(termCadence&&spotCadence?"ALIGNED":null);
    const badges=[];
    if(sourceMix==="MIXED_SOURCE")badges.push("MIXED-SOURCE");
    if(termCadence==="DELAYED_SETTLEMENT"&&spotCadence==="LAST")badges.push("DELAYED SETTLEMENT vs LAST");
    else{
      if(termCadence==="DELAYED_SETTLEMENT")badges.push("DELAYED SETTLEMENT");
      if(spotCadence==="LAST")badges.push("LAST");
    }
    return{termCadence,spotCadence,sourceMix,badges};
  }
  function dataHealth(d){
    const cadence=sourceCadence(d);
    const hasSpot=[d.qqq,d.vxx,d.vix].every(Number.isFinite),hasTerm=Number.isFinite(d.m1)&&Number.isFinite(d.m2)&&Number.isFinite(d.s);
    if(!hasSpot||!hasTerm)return{status:"BLOCKED",label:"DATA BLOCKED",reason:"Required spot or VX term field missing.",...cadence};
    // F1: freshness is fail-closed. Missing or unparseable dates never become age 0.
    const today=isoDay(d.today),termDay=isoDay(d.termAsOf),spotDay=isoDay(d.spotAsOf);
    const dateBlock=(code,reason)=>({status:"BLOCKED",code,label:"DATA BLOCKED · "+code.replace(/_/g," "),reason,...cadence});
    if(!today)return dateBlock("NO_CLOCK","NO CLOCK: no valid today (YYYY-MM-DD) was supplied, so data age cannot be proven. Preserve current position.");
    if(!termDay)return dateBlock("TERM_DATE_INVALID","TERM DATE INVALID: VX term values are present but their as-of date is missing or invalid. Preserve current position.");
    if(!spotDay)return dateBlock("SPOT_DATE_INVALID","SPOT DATE INVALID: QQQ/VXX/VIX as-of date is missing or invalid. Preserve current position.");

    const todayMs=Date.parse(today+"T00:00:00Z"),termMs=Date.parse(termDay+"T00:00:00Z"),spotMs=Date.parse(spotDay+"T00:00:00Z");
    // F1: future as-of is impossible to prove and must block rather than produce a negative age.
    if(termMs>todayMs)return dateBlock("TERM_DATE_FUTURE","TERM DATE FUTURE: VX term as-of date is later than the operator clock. Preserve current position.");
    if(spotMs>todayMs)return dateBlock("SPOT_DATE_FUTURE","SPOT DATE FUTURE: spot as-of date is later than the operator clock. Preserve current position.");

    const age=(todayMs-termMs)/86400000,asofGap=Math.abs(spotMs-termMs)/86400000;
    if(age>POLICY.maxTermAgeDays)return{status:"STALE",label:"DATA STALE",ageDays:age,reason:"VX term source is older than the permitted operator cadence.",...cadence};
    // Date-gap MIXED (>2d) still blocks. Same-day MIXED_SOURCE is warn/badge only (status stays FRESH).
    if(asofGap>2)return{status:"MIXED",label:"AS-OF MIXED",ageDays:asofGap,reason:"Spot and term inputs are materially out of sync; review before acting.",...cadence};
    if(cadence.sourceMix==="MIXED_SOURCE"){
      return{status:"FRESH",label:"DATA FRESH · MIXED-SOURCE",ageDays:age,warnOnly:true,reason:"Same-calendar-day mix of delayed settlement term and live last spot; badge/warn only — regime still drives action.",...cadence};
    }
    return{status:"FRESH",label:"DATA FRESH",ageDays:age,reason:"Required fields are present and within the configured cadence.",...cadence};
  }
  function derive(d){
    const health=dataHealth(d);
    if(health.status==="BLOCKED")return{state:"DATA BLOCKED",action:"HOLD",gate:"BLOCKED",targets:null,blocked:true,health,reason:health.code&&health.code!=="MISSING_FIELD"?"Data date unproven: preserve current position and do not invent a risk action.":"Data incomplete: preserve current position and do not invent a risk action."};
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
  function candidateFromChain(payload,spot,targetDelta=0.10,targetDte=POLICY.optionTargetDte,asOf=null){
    if(!Number.isFinite(spot)||spot<=0)return null;const chain=normalizeOptionChain(payload);if(!chain.length)return null;
    const nowMs=asOf?Date.parse(String(asOf)+"T00:00:00Z"):Date.now();
    const rows=chain.map(x=>{const exp=expiryMs(x.expiration??x.expiry??x.expirationDate),dteDate=Number.isFinite(exp)?Math.max(0,(exp-nowMs)/86400000):null,dte=Number.isFinite(num(x.days))?num(x.days):dteDate,strike=num(x.strike),bid=num(x.bid),ask=num(x.ask),iv=num(x.impliedVolatility),rawDelta=num(x.delta),delta=Number.isFinite(rawDelta)?rawDelta:bsCallDelta(spot,strike,dte,iv);return{...x,strike,bid,ask,dte,delta,expiryMs:exp,deltaSource:Number.isFinite(rawDelta)?"INPUT":"BS_ESTIMATE"};}).filter(x=>Number.isFinite(x.strike)&&Number.isFinite(x.dte)&&x.dte>=14&&x.dte<=120&&Number.isFinite(x.delta)&&x.delta>0&&x.delta<=0.25&&x.strike>spot);
    if(!rows.length)return null;const expiries=[...new Set(rows.map(x=>x.expiryMs).filter(Number.isFinite))].sort((a,b)=>Math.abs((a-nowMs)/86400000-targetDte)-Math.abs((b-nowMs)/86400000-targetDte));
    const pool=expiries.length?rows.filter(x=>x.expiryMs===expiries[0]):rows;pool.sort((a,b)=>Math.abs(a.delta-targetDelta)-Math.abs(b.delta-targetDelta));const short=pool[0];
    const longs=pool.filter(x=>x.strike>short.strike).sort((a,b)=>Math.abs(a.strike-short.strike*1.015)-Math.abs(b.strike-short.strike*1.015));if(!longs.length)return null;const long=longs[0];
    const credit=Number.isFinite(short.bid)&&Number.isFinite(long.ask)?short.bid-long.ask:null;
    return{shortStrike:short.strike,longStrike:long.strike,dte:short.dte,delta:short.delta,deltaSource:short.deltaSource,credit:Number.isFinite(credit)&&credit>0?credit:null,shortBid:short.bid,longAsk:long.ask,width:long.strike-short.strike,expiration:Number.isFinite(short.expiryMs)?new Date(short.expiryMs).toISOString().slice(0,10):null,source:"YAHOO_OPTIONS_ESTIMATE",sizingAvailable:Number.isFinite(credit)&&credit>0};
  }
  function targetLedger(d,e,ledger,candidates={}){
    const cur={qqqShares:num(ledger.qqqShares,0),vxxPct:num(ledger.vxxPct,0),qqqCalls:num(ledger.qqqCalls,0),vxxCalls:num(ledger.vxxCalls,0)};
    if(e.blocked)return{current:cur,target:{...cur},deltas:{qqqShares:0,vxxPct:0,qqqCalls:0,vxxCalls:0},blocked:true,inputBlocked:false,sizing:{qqqCalls:{status:"BLOCKED"},vxxCalls:{status:"BLOCKED"}}};
    if(ledger.inputStatus&&ledger.inputStatus.status!=="READY"){
      return{current:cur,target:{...cur},deltas:{qqqShares:0,vxxPct:0,qqqCalls:0,vxxCalls:0},blocked:false,inputBlocked:true,inputStatus:ledger.inputStatus,sizing:{qqqCalls:{status:"INPUT_INCOMPLETE"},vxxCalls:{status:"INPUT_INCOMPLETE"}}};
    }
    const nav=num(ledger.nav,0),qqqPrice=num(d.qqq,0),rawShares=nav>0&&qqqPrice>0?(nav*e.targets.qqqCorePct/100)/qqqPrice:cur.qqqShares,buyAllowed=e.action==="BUY";
    const qc=candidates.qqq||null,vc=candidates.vxx||null,qQty=optionQty(nav,e.targets.qqqCallBudgetPct,qc?.credit),vQty=optionQty(nav,e.targets.vxxCallBudgetPct,vc?.credit);
    const qqqCallsTarget=e.action==="HOLD"?cur.qqqCalls:(buyAllowed?(qc?.sizingAvailable?qQty:cur.qqqCalls):Math.min(cur.qqqCalls,qQty));
    const vxxCallsTarget=e.action==="HOLD"?cur.vxxCalls:(buyAllowed?(vc?.sizingAvailable?vQty:cur.vxxCalls):Math.min(cur.vxxCalls,vQty));
    const target={qqqShares:buyAllowed?Math.floor(rawShares):cur.qqqShares,vxxPct:buyAllowed?e.targets.vxxPct:Math.min(cur.vxxPct,e.targets.vxxPct),qqqCalls:qqqCallsTarget,vxxCalls:vxxCallsTarget};
    return{current:cur,target,deltas:{qqqShares:target.qqqShares-cur.qqqShares,vxxPct:target.vxxPct-cur.vxxPct,qqqCalls:target.qqqCalls-cur.qqqCalls,vxxCalls:target.vxxCalls-cur.vxxCalls},blocked:false,inputBlocked:false,sizing:{qqqCalls:qc?.sizingAvailable?{status:"READY",credit:qc.credit,quantity:qQty,source:qc.source}:{status:"PENDING_CANDIDATE"},vxxCalls:vc?.sizingAvailable?{status:"READY",credit:vc.credit,quantity:vQty,source:vc.source}:{status:"PENDING_CANDIDATE"}}};
  }
  function actionRows(book){return Object.entries(book.deltas).map(([key,diff])=>({key,diff,kind:Math.abs(diff)<1e-9?"HOLD":diff>0?"ADD":"REDUCE"}));}
  // Cell 13 C — flat-book / no-option-legs silence (suppress ROLL fire from blank DTE).
  function flatBookSilence({qqqCalls,vxxCalls,forceFlat,currentOptionLegs}={}){
    if(forceFlat===true)return{silent:true,qqqSilent:true,vxxSilent:true,reason:"FORCE_FLAT"};
    const qOp=operatorNumber(qqqCalls,{allowZero:true,min:0});
    const vOp=operatorNumber(vxxCalls,{allowZero:true,min:0});
    const qZero=qOp.status==="VALUE"&&qOp.value===0;
    const vZero=vOp.status==="VALUE"&&vOp.value===0;
    const bothZero=qZero&&vZero;
    const legs=currentOptionLegs&&typeof currentOptionLegs==="object"?currentOptionLegs:null;
    const qFlat=!!(legs&&legs.qqq&&legs.qqq.status==="FLAT");
    const vFlat=!!(legs&&legs.vxx&&legs.vxx.status==="FLAT");
    const bothFlat=qFlat&&vFlat;
    const qqqSilent=bothZero||bothFlat||qZero||qFlat;
    const vxxSilent=bothZero||bothFlat||vZero||vFlat;
    return{
      silent:qqqSilent&&vxxSilent,
      qqqSilent,vxxSilent,
      reason:bothFlat?"LEGS_FLAT":bothZero?"CALLS_ZERO":(qqqSilent||vxxSilent)?"PARTIAL_FLAT":"ACTIVE"
    };
  }
  function triggers(d,e,opt={}){
    const rows=[];
    if(Number.isFinite(d.s)){
      rows.push({id:"S_ZERO",label:"VX term to zero",value:d.s<=0?"TRIGGERED":d.s.toFixed(2)+"% → 0",fire:d.s<=0,mode:d.s<=0?"TRIGGER":"WATCH",priority:"HIGH"});
      rows.push({id:"S_SAFE",label:"VX carry line",value:d.s<=POLICY.termSafe?d.s.toFixed(2)+"% ≤ 5%":"above 5%",fire:false,mode:d.s<=POLICY.termSafe?"WATCH":"NORMAL",priority:"MED"});
    }
    if(Number.isFinite(d.vix))rows.push({id:"VIX_28",label:"VIX high line",value:d.vix>=POLICY.vixHigh?"TRIGGERED":(POLICY.vixHigh-d.vix).toFixed(2)+" away",fire:d.vix>=POLICY.vixHigh,mode:d.vix>=POLICY.vixHigh?"TRIGGER":"WATCH",priority:"HIGH"});
    const qdte=num(opt.qqqDte),qdelta=num(opt.qqqDelta),vdte=num(opt.vxxDte),vdelta=num(opt.vxxDelta);
    const silence=flatBookSilence({qqqCalls:opt.qqqCalls,vxxCalls:opt.vxxCalls,forceFlat:opt.forceFlat,currentOptionLegs:opt.currentOptionLegs});
    let hasQ=opt.hasQQQCall===true,hasV=opt.hasVXXCall===true;
    // Auto derive presence from call counts when has* not explicit (Cell 13 strengthen).
    if(opt.hasQQQCall===undefined&&opt.qqqCalls!==undefined){
      const q=operatorNumber(opt.qqqCalls,{allowZero:true,min:0});
      hasQ=q.status==="VALUE"&&q.value>0;
    }
    if(opt.hasVXXCall===undefined&&opt.vxxCalls!==undefined){
      const v=operatorNumber(opt.vxxCalls,{allowZero:true,min:0});
      hasV=v.status==="VALUE"&&v.value>0;
    }
    if(silence.qqqSilent)hasQ=false;
    if(silence.vxxSilent)hasV=false;
    rows.push({id:"QQQ_ROLL",label:"QQQ far call roll",value:!hasQ?"NO POSITION":"DTE "+(Number.isFinite(qdte)?qdte:"—")+" · Δ "+(Number.isFinite(qdelta)?qdelta.toFixed(2):"—"),fire:hasQ&&((Number.isFinite(qdte)&&qdte<=POLICY.qqqRollDte)||(Number.isFinite(qdelta)&&qdelta>=POLICY.qqqRollDelta)),mode:!hasQ?"NO_POSITION":((Number.isFinite(qdte)||Number.isFinite(qdelta))?"TRIGGERABLE":"NEEDS_POSITION_DATA"),priority:"MED"});
    rows.push({id:"VXX_ROLL",label:"VXX call roll",value:!hasV?"NO POSITION":"DTE "+(Number.isFinite(vdte)?vdte:"—")+" · Δ "+(Number.isFinite(vdelta)?vdelta.toFixed(2):"—"),fire:hasV&&((Number.isFinite(vdte)&&vdte<=POLICY.vxxRollDte)||(Number.isFinite(vdelta)&&vdelta>=POLICY.vxxRollDelta)||e.state==="SHOCK"),mode:!hasV?"NO_POSITION":((Number.isFinite(vdte)||Number.isFinite(vdelta)||e.state==="SHOCK")?"TRIGGERABLE":"NEEDS_POSITION_DATA"),priority:"HIGH"});
    return rows;
  }
  function operatorSummary(d,e,book,candidates={},opt={}){
    const hasPosition=book.current.qqqShares>0||book.current.vxxPct>0||book.current.qqqCalls>0||book.current.vxxCalls>0;
    const acts=Object.entries(book.deltas||{}).filter(([,v])=>Number.isFinite(v)&&Math.abs(v)>1e-9);
    const holdTrims=(!e.blocked&&e.action==="HOLD")?reductionLines(book,"TRIM"):[];
    const mode=e.blocked?"PAUSED":e.action==="REDUCE"?"DEFEND":e.action==="HOLD"?(holdTrims.length?"WATCH / TRIM":"WATCH"):acts.length?"BUILD / REBALANCE":hasPosition?"AT TARGET / MONITOR":"EMPTY / READY TO BUILD";
    const plan=[];
    if(e.blocked) plan.push("不新增、不減倉：等待完整新數據");
    else if(e.action==="HOLD"){
      plan.push("不新增 carry：保留現有倉位，等轉態");
      plan.push(...carryInventoryLines(book,d,opt));
      if(holdTrims.length){
        plan.push("超出 frozen target → TRIM（只減、唔加）：");
        plan.push(...holdTrims);
      }
    }
    else if(e.action==="REDUCE"){
      plan.push(...carryInventoryLines(book,d,opt));
      plan.push("減風險：VXX seller → "+fmtPct(book.target.vxxPct)+"；QQQ core 保留");
      if(book.target.qqqCalls<book.current.qqqCalls)plan.push("QQQ far call → 減至 "+fmtNum(book.target.qqqCalls)+" spreads");
      if(book.target.vxxCalls<book.current.vxxCalls)plan.push("VXX call → 減至 "+fmtNum(book.target.vxxCalls)+" spreads");
    }else{
      if(book.deltas.qqqShares>0)plan.push("QQQ core +"+fmtNum(book.deltas.qqqShares)+" shares → "+fmtPct(e.targets.qqqCorePct));
      if(book.deltas.vxxPct>0)plan.push("VXX short +"+fmtPct(book.deltas.vxxPct)+" NAV → "+fmtPct(e.targets.vxxPct));
      if(book.deltas.qqqCalls>0)plan.push(optionPlan("QQQ far",candidates.qqq,book.deltas.qqqCalls));
      if(book.deltas.vxxCalls>0)plan.push(optionPlan("VXX call",candidates.vxx,book.deltas.vxxCalls));
      if(!plan.length)plan.push("已在目標附近：不追買，只監察 / 轉倉");
    }
    const thresholds=[];
    if(Number.isFinite(d.s)){
      if(d.s>POLICY.termSafe) thresholds.push({id:"S_5",label:"S → 5% · WEAKENING",distance:d.s-POLICY.termSafe,text:fmtNum(d.s-POLICY.termSafe)+" pp"});
      else if(d.s>0) thresholds.push({id:"S_0",label:"S → 0% · CUT",distance:d.s,text:fmtNum(d.s)+" pp"});
      else thresholds.push({id:"S_POS",label:"S back > 0% · exit CUT",distance:-d.s,text:fmtNum(-d.s)+" pp"});
    }
    if(Number.isFinite(d.vix)){
      if(d.vix<28) thresholds.push({id:"VIX_28",label:"VIX → 28 · PRE-SHOCK",distance:28-d.vix,text:fmtNum(28-d.vix)+" pts"});
      else thresholds.push({id:"VIX_DOWN",label:"VIX back < 28 · remove CAP",distance:d.vix-28,text:fmtNum(d.vix-28)+" pts"});
    }
    thresholds.sort((a,b)=>Math.abs(a.distance)-Math.abs(b.distance));
    // ROLL prefers Cell 08 currentOptionLegs when provided; else book counts + manual opt DTE/Δ.
    // Cell 13 C: flat-book silence / forceFlat → OFF / NO POSITION (never ROLL_NOW from blank DTE).
    const legs=opt.currentOptionLegs||null;
    const today=opt.today||d.today||null;
    const silence=flatBookSilence({qqqCalls:book.current.qqqCalls,vxxCalls:book.current.vxxCalls,forceFlat:opt.forceFlat,currentOptionLegs:legs});
    const offRoll=(label)=>({label,status:"OFF",text:"NO POSITION"});
    const rolls={
      qqq:silence.qqqSilent?offRoll("QQQ far"):rollForUnderlying("QQQ far",legs&&legs.qqq,book.current.qqqCalls,opt.qqqDte,opt.qqqDelta,POLICY.qqqRollDte,POLICY.qqqRollDelta,today),
      vxx:silence.vxxSilent?offRoll("VXX call"):rollForUnderlying("VXX call",legs&&legs.vxx,book.current.vxxCalls,opt.vxxDte,opt.vxxDelta,POLICY.vxxRollDte,POLICY.vxxRollDelta,today)
    };
    return{mode,plan,thresholds:thresholds.slice(0,3),rolls,hasPosition,flatBookSilence:silence};
  }
  function fmtNum(v){return Number.isFinite(Number(v))?Number(v).toLocaleString("en-US",{maximumFractionDigits:2}):"—";}
  function fmtPct(v){return Number.isFinite(Number(v))?fmtNum(v)+"%":"—";}
  // F4 — human-readable REDUCE/TRIM lines from book deltas (display only; never changes targets).
  function reductionLines(book,tag="REDUCE"){
    const cur=book&&book.current||{},tgt=book&&book.target||{},dl=book&&book.deltas||{};
    const rows=[
      ["qqqShares","QQQ core",v=>fmtNum(v),v=>" shares",v=>fmtNum(v)],
      ["vxxPct","VXX short",v=>fmtPct(v),v=>" NAV",v=>fmtPct(v)],
      ["qqqCalls","QQQ far call",v=>fmtNum(v),v=>" spreads",v=>fmtNum(v)],
      ["vxxCalls","VXX call",v=>fmtNum(v),v=>" spreads",v=>fmtNum(v)]
    ];
    const out=[];
    for(const [k,label,f,unit,fd] of rows){
      const dv=Number(dl[k]);
      if(!(Number.isFinite(dv)&&dv<-1e-9))continue;
      out.push(label+" "+f(cur[k])+" → "+f(tgt[k])+unit()+" ("+tag+" − "+fd(-dv)+")");
    }
    return out;
  }
  function carryInventoryLines(book,d,opt={}){
    const cur=book.current||{};
    const legs=(opt&&opt.currentOptionLegs)||null;
    const lines=[];
    const qShares=num(cur.qqqShares,0), vPct=num(cur.vxxPct,0), qCalls=num(cur.qqqCalls,0), vCalls=num(cur.vxxCalls,0);
    const any=qShares>0||vPct>0||qCalls>0||vCalls>0;
    if(!any){
      lines.push("現有 carry：Memory 未填／空倉 — 填 Operator Memory 或「從 Journal 還原」先睇到你持有乜");
      return lines;
    }
    lines.push("現有 carry（唔再增）：");
    if(qShares>0) lines.push("· QQQ core "+fmtNum(qShares)+" shares");
    else lines.push("· QQQ core：0");
    if(vPct>0){
      const implied=impliedVxxShares(num(opt.nav,num(book.nav,null)),vPct,num(d&&d.vxx,null));
      lines.push("· VXX short exposure "+fmtPct(vPct)+(Number.isFinite(implied)?" ≈ "+fmtNum(implied)+" shares":""));
    } else lines.push("· VXX short exposure：0% NAV");
    lines.push("· "+heldOptionLine("QQQ far",qCalls,legs&&legs.qqq));
    lines.push("· "+heldOptionLine("VXX call",vCalls,legs&&legs.vxx));
    return lines;
  }
  function heldOptionLine(label,count,leg){
    if(!(count>0)) return label+"：0 spreads";
    if(leg&&leg.status==="READY"){
      const ss=leg.shortStrike&&leg.shortStrike.status==="VALUE"?fmtNum(leg.shortStrike.value):"—";
      const ls=leg.longStrike&&leg.longStrike.status==="VALUE"?fmtNum(leg.longStrike.value):"—";
      const exp=leg.expiry&&leg.expiry.status==="VALUE"?String(leg.expiry.value):"—";
      const dte=leg.dte&&leg.dte.status==="VALUE"?fmtNum(leg.dte.value):(leg.expiry&&leg.expiry.status==="VALUE"?"(from expiry)":"—");
      const delta=leg.delta&&leg.delta.status==="VALUE"?fmtNum(leg.delta.value):"—";
      const cr=leg.entryCredit&&leg.entryCredit.status==="VALUE"?fmtNum(leg.entryCredit.value):"—";
      return label+"：持有 "+fmtNum(count)+" spreads · "+ss+"/"+ls+" · exp "+exp+" · DTE "+dte+" · Δ "+delta+" · entry "+cr;
    }
    if(leg&&(leg.status==="INCOMPLETE"||leg.status==="INVALID"))
      return label+"：持有 "+fmtNum(count)+" spreads · 腿身份 "+leg.status+"（補 short/long/expiry）";
    return label+"：持有 "+fmtNum(count)+" spreads · 未填腿身份（Qty only）";
  }
  // Cell 15 — funding/context layer. Advisory only: does NOT alter targetLedger or frozen policy math.
  function fundingPlan({d={},e={},book={},strategyPool="",newCapital="",nav:navInput}={}){
    const pool=operatorNumber(strategyPool,{allowZero:true,min:0});
    const added=operatorNumber(newCapital,{allowZero:true,min:0});
    const navSrc=navInput!==undefined&&navInput!==null&&String(navInput).trim()!==""?navInput:(book&&book.current?book.current.nav:undefined);
    const navValue=operatorNumber(navSrc,{allowZero:true,min:0});
    const nav=navValue.status==="VALUE"?navValue.value:(book&&book.nav!==undefined?num(book.nav,null):null);
    const qqqPrice=Number.isFinite(Number(d.qqq))?Number(d.qqq):null;
    const qqqShares=book&&book.current?num(book.current.qqqShares,null):null;
    const qqqValue=Number.isFinite(qqqShares)&&Number.isFinite(qqqPrice)?qqqShares*qqqPrice:null;
    const navBase=Number.isFinite(nav)?nav:null;
    const contribution=added.status==="VALUE"?added.value:0;
    const projectedNav=Number.isFinite(navBase)?navBase+contribution:null;
    const targetPct=POLICY.corePct;
    const targetValue=Number.isFinite(projectedNav)?projectedNav*(targetPct/100):null;
    const gap=Number.isFinite(targetValue)&&Number.isFinite(qqqValue)?Math.max(0,targetValue-qqqValue):null;
    const state=e.state||"UNKNOWN";
    const blocked=e.blocked===true;
    let route,shortCall;
    if(blocked){route="PAUSED";shortCall="NO NEW"; }
    else if(state==="CARRY"){route="FULL HYBRID";shortCall="ELIGIBLE";}
    else if(state==="WEAKENING"){route="QQQ CORE ONLY";shortCall="MAINTAIN EXISTING · NO NEW";}
    else if(state==="PRE-SHOCK"||state==="SHOCK"){route="DEFENSIVE / RESERVE";shortCall="NO NEW · REDUCE IF TRIGGERED";}
    else{route="REVIEW";shortCall="REVIEW";}
    // Only CARRY / WEAKENING lanes may route new money into QQQ core; PAUSED / DEFENSIVE / REVIEW → all reserve.
    const coreLaneOpen=route==="FULL HYBRID"||route==="QQQ CORE ONLY";
    const qqqTo=coreLaneOpen&&Number.isFinite(gap)?Math.min(contribution,gap):0;
    const reserve=Math.max(0,contribution-qqqTo);
    let message;
    if(blocked) message="策略仍存在，但 DATA gate 未開：新資金先不部署。";
    else if(added.status==="EMPTY") message="未輸入本輪新資金；策略仍照當前 regime 運作。";
    else if(added.status==="INVALID") message="本輪新資金輸入無效；先修正本金資料，唔改策略。";
    else if(state==="CARRY") message="正常 carry：可由新資金補 QQQ core；QQQ far-call credit spread 同 VXX carry 依 frozen target/候選再 build。";
    else if(state==="WEAKENING") message="現時仍有策略：持有 QQQ core＋已有 carry；新資金只作 QQQ core／reserve，唔新增 short-vol carry。";
    else message="現時係防守策略：保留 QQQ core／降低 seller risk；新資金暫作 reserve，唔追新 carry。";
    return{
      strategyName:"ORIGINAL HYBRID BASELINE",
      formula:"QQQ core + QQQ far-call credit spreads + VXX short carry + VXX call hedge",
      regime:state,
      engineAction:e.action||null,
      route,shortCall,
      poolStatus:pool.status,
      newCapitalStatus:added.status,
      strategyPool:pool.value,
      newCapital:added.value,
      nav:navBase,
      projectedNav,
      qqqPrice,
      qqqShares,
      qqqValue,
      qqqCurrentPct:Number.isFinite(qqqValue)&&Number.isFinite(navBase)&&navBase>0?qqqValue/navBase*100:null,
      qqqTargetPct:targetPct,
      qqqTargetValue:targetValue,
      qqqGap:gap,
      suggestedQqqFromNewCapital:qqqTo,
      reserveAfterQqq:reserve,
      message
    };
  }
  // Cell 16 — frozen strategy state -> funding context -> operator action bridge (read-only).
  // This is an interpretation/hand-off layer only. It never mutates targetLedger or emits broker orders.
  function strategyActionBridge({d={},e={},book={},funding={},currentOptionLegs=null,journalRows=[]}={}){
    const cur=book&&book.current&&typeof book.current==="object"?book.current:{};
    const tgt=book&&book.target&&typeof book.target==="object"?book.target:{};
    const delta=book&&book.deltas&&typeof book.deltas==="object"?book.deltas:{};
    const hasPosition=Number(cur.qqqShares||0)>0||Number(cur.vxxPct||0)>0||Number(cur.qqqCalls||0)>0||Number(cur.vxxCalls||0)>0;
    const hasBuild=Object.values(delta).some(v=>Number.isFinite(Number(v))&&Number(v)>1e-9);
    const hasReduction=Object.values(delta).some(v=>Number.isFinite(Number(v))&&Number(v)<-1e-9);
    let actionClass,operatorInstruction;
    if(e.blocked){
      actionClass="PAUSE";
      operatorInstruction="DATA 未通過：不新增、不減倉；先取得完整/較新資料。";
    }else if(e.action==="REDUCE"){
      actionClass="DEFEND";
      operatorInstruction="按 frozen target 檢查減風險項；完成實際人工動作後 JOURNAL。";
    }else if(e.action==="BUY"){
      actionClass=hasBuild&&hasReduction?"REBALANCE":hasBuild?"BUILD":hasPosition?"MAINTAIN":"READY";
      operatorInstruction=actionClass==="REBALANCE"
        ?"按 frozen target 同時檢查新增與縮減項；逐項人工處理後 JOURNAL。"
        :actionClass==="BUILD"
          ?"按 Current → Target 檢查新增項；候選只作參考，不自動下單；完成後 JOURNAL。"
          :actionClass==="MAINTAIN"
            ?"維持現有倉位，等待 NEXT regime / ROLL transition。"
            :"目前無倉位：等待有效 BUILD 條件；不因空倉自行創造目標。";
    }else if(e.action==="HOLD"){
      // F4: HOLD never adds; a position above its frozen target is trimmed down to target.
      actionClass=hasPosition?(hasReduction?"TRIM":"MAINTAIN"):"READY";
      operatorInstruction=actionClass==="TRIM"
        ?"不新增 carry；只將超出 frozen target 嘅部分減返落目標（TRIM）；逐項人工處理後 JOURNAL。"
        :hasPosition
          ?"維持現有倉位，等待 NEXT regime / ROLL transition；不新增 carry。"
          :"目前無倉位：保持觀察，等待有效 BUILD 條件。";
    }else if(hasPosition){
      actionClass="MAINTAIN";
      operatorInstruction="維持現有倉位，等待下一個有效狀態。";
    }else{
      actionClass="READY";
      operatorInstruction="目前無倉位：等待有效 BUILD 條件；不因空倉自行創造目標。";
    }

    const summary=operatorSummary(
      d,
      e,
      book,
      {},
      {currentOptionLegs:currentOptionLegs||null,today:d.today||null}
    );
    const transition=(summary.thresholds||[]).map(x=>({id:x.id,label:x.label,distance:x.distance,text:x.text}));
    const roll={
      qqq:summary.rolls&&summary.rolls.qqq?summary.rolls.qqq:{label:"QQQ far",status:"OFF",text:"NO POSITION"},
      vxx:summary.rolls&&summary.rolls.vxx?summary.rolls.vxx:{label:"VXX call",status:"OFF",text:"NO POSITION"}
    };
    const rollNow=[roll.qqq,roll.vxx].filter(x=>x.status==="ROLL_NOW");
    const fundingView={
      strategyPool:funding.strategyPool??null,
      newCapital:funding.newCapital??null,
      route:funding.route||"REVIEW",
      qqqGap:Number.isFinite(Number(funding.qqqGap))?Number(funding.qqqGap):null,
      suggestedQqqFromNewCapital:Number.isFinite(Number(funding.suggestedQqqFromNewCapital))?Number(funding.suggestedQqqFromNewCapital):null,
      reserveAfterQqq:Number.isFinite(Number(funding.reserveAfterQqq))?Number(funding.reserveAfterQqq):null,
      status:"CONTEXT_ONLY",
      promotion:"RESEARCH_ONLY_NOT_EXECUTION"
    };
    const last=Array.isArray(journalRows)&&journalRows.length?journalRows[journalRows.length-1]:null;
    const journalState=last?{
      eventId:last.event_id??null,
      state:last.state??null,
      action:last.engine_action??null,
      conflict:last.conflict??"NONE"
    }:{eventId:null,state:null,action:null,conflict:null};
    const journalChanged=!!last&&(
      String(last.state??"")!==String(e.state??"") ||
      String(last.engine_action??"")!==String(e.action??"") ||
      JSON.stringify(last.target_position||{})!==JSON.stringify(tgt||{})
    );
    const closedLoop=[
      {stage:"DATA",status:e.health&&e.health.status||"UNKNOWN"},
      {stage:"DECISION",status:e.action||"—"},
      {stage:"CURRENT",status:hasPosition?"LOADED":"EMPTY"},
      {stage:"TARGET",status:e.blocked?"PRESERVE CURRENT":"FROZEN POLICY"},
      {stage:"FUNDING",status:"CONTEXT ONLY"},
      {stage:"WATCH",status:rollNow.length?"ROLL NOW":"MONITOR"},
      {stage:"JOURNAL",status:last?(journalChanged?"CHANGED":"ALIGNED"):"READY"}
    ];
    return{
      version:"CELL16-V1",
      strategyName:"ORIGINAL HYBRID BASELINE",
      policyVersion:POLICY.policyVersion,
      engineVersion:POLICY.engineVersion,
      regime:e.state||"UNKNOWN",
      engineAction:e.action||null,
      actionClass,
      operatorInstruction,
      reduceLines:reductionLines(book,actionClass==="TRIM"?"TRIM":"REDUCE"),
      current:{
        qqqShares:num(cur.qqqShares,0),
        vxxPct:num(cur.vxxPct,0),
        qqqCalls:num(cur.qqqCalls,0),
        vxxCalls:num(cur.vxxCalls,0)
      },
      target:{
        qqqShares:num(tgt.qqqShares,num(cur.qqqShares,0)),
        vxxPct:num(tgt.vxxPct,num(cur.vxxPct,0)),
        qqqCalls:num(tgt.qqqCalls,num(cur.qqqCalls,0)),
        vxxCalls:num(tgt.vxxCalls,num(cur.vxxCalls,0))
      },
      deltas:{
        qqqShares:num(delta.qqqShares,0),
        vxxPct:num(delta.vxxPct,0),
        qqqCalls:num(delta.qqqCalls,0),
        vxxCalls:num(delta.vxxCalls,0)
      },
      qqqCoreTargetPct:POLICY.corePct,
      qqqGap:fundingView.qqqGap,
      funding:fundingView,
      transition,
      roll,
      rollNow,
      nextStep:rollNow.length?"ROLL_OPTION":"WATCH_NEXT_TRANSITION",
      journal:{...journalState,changed:journalChanged},
      closedLoop,
      noBrokerOrder:true
    };
  }

  function optionPlan(label,c,n){
    if(!c)return label+" +"+fmtNum(n)+" spreads · candidate PENDING";
    return label+" +"+fmtNum(n)+" spreads · "+fmtNum(c.shortStrike)+"/"+fmtNum(c.longStrike)+" · DTE "+fmtNum(c.dte)+" · Δ "+fmtNum(c.delta)+" · credit "+fmtNum(c.credit);
  }
  function rollDistance(label,count,dte,delta,dteLine,deltaLine){
    if(!(count>0))return{label,status:"OFF",text:"NO POSITION"};
    const present=v=>v!==null&&v!==undefined&&String(v).trim()!=="";
    const d=present(dte)?Number(dte):null,del=present(delta)?Number(delta):null;
    // blank ≠ 0: missing both → NEEDS_DATA, never invent a roll distance
    if((d===null||!Number.isFinite(d))&&(del===null||!Number.isFinite(del)))return{label,status:"NEEDS_DATA",text:"輸入現有 spread DTE / Δ"};
    const dSafe=Number.isFinite(d)?d:null,delSafe=Number.isFinite(del)?del:null;
    const dteLeft=dSafe!==null?dSafe-dteLine:null;
    const deltaLeft=delSafe!==null?deltaLine-delSafe:null;
    const fire=(Number.isFinite(dteLeft)&&dteLeft<=0)||(Number.isFinite(deltaLeft)&&deltaLeft<=0);
    const parts=[];
    if(Number.isFinite(dteLeft))parts.push("DTE "+(dteLeft<=0?"ROLL NOW":fmtNum(dteLeft)+"d"));
    if(Number.isFinite(deltaLeft))parts.push("Δ "+(deltaLeft<=0?"ROLL NOW":fmtNum(deltaLeft)));
    return{label,status:fire?"ROLL_NOW":"WATCH",text:parts.join(" · ")};
  }
  // Prefer Cell 08 leg identity for ROLL. Candidate (next buy) stays separate.
  // Priority: FLAT→NO POSITION; INCOMPLETE/INVALID→NEEDS_POSITION_DATA;
  // DTE: leg.dte VALUE else dteFromExpiry(leg.expiry, today); Delta: leg.delta VALUE else manual opt.
  function rollForUnderlying(label,leg,fallbackCount,manualDte,manualDelta,dteLine,deltaLine,today){
    if(leg){
      if(leg.status==="FLAT")return{label,status:"OFF",text:"NO POSITION"};
      if(leg.status==="INCOMPLETE"||leg.status==="INVALID")
        return{label,status:"NEEDS_DATA",text:"NEEDS_POSITION_DATA · 輸入現有 spread 身分"};
      // READY (qty>0 + short/long/expiry)
      let dteVal=null;
      if(leg.dte&&leg.dte.status==="VALUE")dteVal=leg.dte.value;
      else if(leg.expiry&&leg.expiry.status==="VALUE")dteVal=dteFromExpiry(leg.expiry.value,today);
      let deltaVal=null;
      if(leg.delta&&leg.delta.status==="VALUE")deltaVal=leg.delta.value;
      else{
        const present=v=>v!==null&&v!==undefined&&String(v).trim()!=="";
        if(present(manualDelta)){const n=Number(manualDelta);if(Number.isFinite(n))deltaVal=n;}
      }
      return rollDistance(label,1,dteVal,deltaVal,dteLine,deltaLine);
    }
    return rollDistance(label,fallbackCount,manualDte,manualDelta,dteLine,deltaLine);
  }
  // Cell 08 — current credit-spread leg identity (display/parse only; does not change Decision/Candidate/Build).
  // entryCredit: credit is positive; a debit may be negative.
  function operatorExpiry(v){
    if(v===null||v===undefined||String(v).trim()==="")return{status:"EMPTY",value:null};
    const s=String(v).trim();
    if(!/^\d{4}-\d{2}-\d{2}$/.test(s))return{status:"INVALID",value:null};
    const t=Date.parse(s+"T00:00:00Z");
    if(!Number.isFinite(t))return{status:"INVALID",value:null};
    return{status:"VALUE",value:s};
  }
  function parseOptionLeg(raw={}){
    const src=raw&&typeof raw==="object"?raw:{};
    const qty=operatorNumber(src.qty,{allowZero:true,min:0});
    const shortStrike=operatorNumber(src.shortStrike,{allowZero:false,min:0});
    const longStrike=operatorNumber(src.longStrike,{allowZero:false,min:0});
    const expiry=operatorExpiry(src.expiry);
    const dte=operatorNumber(src.dte,{allowZero:true,min:0});
    const delta=operatorNumber(src.delta,{allowZero:true,min:0});
    const entryCredit=operatorNumber(src.entryCredit,{allowZero:true,min:Number.NEGATIVE_INFINITY});
    const fields={qty,shortStrike,longStrike,expiry,dte,delta,entryCredit};
    const width=(shortStrike.status==="VALUE"&&longStrike.status==="VALUE")?longStrike.value-shortStrike.value:null;
    const anyInvalid=Object.values(fields).some(f=>f.status==="INVALID");
    const identityReady=shortStrike.status==="VALUE"&&longStrike.status==="VALUE"&&expiry.status==="VALUE";
    const othersEmpty=[shortStrike,longStrike,expiry,dte,delta,entryCredit].every(f=>f.status==="EMPTY");
    let status;
    if(anyInvalid) status="INVALID";
    else if((qty.status==="VALUE"&&qty.value===0)||(qty.status==="EMPTY"&&othersEmpty)) status="FLAT";
    else if(qty.status==="VALUE"&&qty.value>0&&identityReady) status="READY";
    else status="INCOMPLETE";
    const rollReady=status==="READY"&&dte.status==="VALUE"&&delta.status==="VALUE";
    return{...fields,width,status,rollReady};
  }
  function currentOptionLegs(input={}){
    const src=input&&typeof input==="object"?input:{};
    return{qqq:parseOptionLeg(src.qqq||{}),vxx:parseOptionLeg(src.vxx||{})};
  }
  // Cell 13 B — VXX naming / exposure units (short = % NAV; call spreads = contracts).
  const EXPOSURE_LABELS=Object.freeze({
    vxxShort:"VXX short exposure (% NAV)",
    vxxShortUnit:"% NAV",
    vxxCallSpreads:"VXX call credit spreads",
    vxxCallUnit:"contracts",
    qqqCallSpreads:"QQQ far call credit spreads",
    qqqCallUnit:"contracts"
  });
  function exposureLabels(){return EXPOSURE_LABELS;}
  function impliedVxxShares(nav,vxxPct,vxxPrice){
    const n=num(nav),p=num(vxxPct),px=num(vxxPrice);
    if(![n,p,px].every(Number.isFinite)||px<=0)return null;
    return(n*(p/100))/px;
  }
  // Cell 12 — journal payload construction (pure; no I/O). Conflict + option-delta guard.
  // Never copy Candidate strikes into current_position / Current Leg fields.
  function journalRecord({engine,book,humanAction,optionsStatus,candidates,currentOptionLegs,funding,actionBridge}={}){
    const e=engine&&typeof engine==="object"?engine:{};
    const b=book&&typeof book==="object"?book:{};
    const cand=candidates&&typeof candidates==="object"?candidates:{};
    const candidate_present={qqq:!!cand.qqq,vxx:!!cand.vxx};
    const human=(humanAction===null||humanAction===undefined||String(humanAction).trim()==="")?null:String(humanAction).trim().toUpperCase();
    let conflict="NONE";
    const bridgeClass=actionBridge&&actionBridge.actionClass?String(actionBridge.actionClass).toUpperCase():null;
    if(human&&human!==e.action&&human!==bridgeClass) conflict="CONFLICT";
    // Identity counts only — never candidate strikes
    const curSrc=b.current&&typeof b.current==="object"?b.current:{};
    const current_position={
      qqqShares:num(curSrc.qqqShares,0),
      vxxPct:num(curSrc.vxxPct,0),
      qqqCalls:num(curSrc.qqqCalls,0),
      vxxCalls:num(curSrc.vxxCalls,0)
    };
    // Optional nav for Journal→Memory restore (only when explicitly present; never invent 0 from blank).
    if(curSrc.nav!==undefined&&curSrc.nav!==null&&String(curSrc.nav).trim()!==""){
      const nNav=num(curSrc.nav,null);
      if(nNav!==null) current_position.nav=nNav;
    }
    const tgtSrc=b.target&&typeof b.target==="object"?b.target:{};
    const target_position={
      qqqShares:num(tgtSrc.qqqShares,current_position.qqqShares),
      vxxPct:num(tgtSrc.vxxPct,current_position.vxxPct),
      qqqCalls:num(tgtSrc.qqqCalls,current_position.qqqCalls),
      vxxCalls:num(tgtSrc.vxxCalls,current_position.vxxCalls)
    };
    const dSrc=b.deltas&&typeof b.deltas==="object"?b.deltas:{};
    const deltas={
      qqqShares:num(dSrc.qqqShares,0),
      vxxPct:num(dSrc.vxxPct,0),
      qqqCalls:num(dSrc.qqqCalls,0),
      vxxCalls:num(dSrc.vxxCalls,0)
    };
    const holdOrBuy=e.action==="HOLD"||e.action==="BUY";
    const statusDown=optionsStatus==="OPTIONS_SOURCE_DOWN"||optionsStatus==="BLOCKED_NO_OPEND";
    let deltas_guarded=false;
    // HOLD/BUY must not journal false REDUCE option legs when candidate missing or source down/blocked.
    if(holdOrBuy){
      const guardQ=(!candidate_present.qqq)||statusDown;
      const guardV=(!candidate_present.vxx)||statusDown;
      if(deltas.qqqCalls<0&&guardQ){
        if(conflict==="NONE") conflict="DELTA_ACTION_MISMATCH";
        deltas.qqqCalls=0;
        target_position.qqqCalls=current_position.qqqCalls;
        deltas_guarded=true;
      }
      if(deltas.vxxCalls<0&&guardV){
        if(conflict==="NONE") conflict="DELTA_ACTION_MISMATCH";
        deltas.vxxCalls=0;
        target_position.vxxCalls=current_position.vxxCalls;
        deltas_guarded=true;
      }
    }
    const record={
      state:e.state??null,
      gate:e.gate??null,
      engine_action:e.action??null,
      reason:e.reason??null,
      current_position,
      target_position,
      deltas,
      human_action:human,
      conflict,
      options_status:optionsStatus===undefined?null:optionsStatus,
      candidate_present,
      deltas_guarded
    };
    if(currentOptionLegs!==undefined) record.current_option_legs=currentOptionLegs;
    if(funding!==undefined) record.funding_context={
      strategy_pool:funding.strategyPool,
      new_capital:funding.newCapital,
      route:funding.route,
      strategy_name:funding.strategyName,
      regime:funding.regime
    };
    if(actionBridge!==undefined) record.action_bridge={
      version:actionBridge.version,
      action_class:actionBridge.actionClass,
      reduce_lines:Array.isArray(actionBridge.reduceLines)?actionBridge.reduceLines.slice():[],
      operator_instruction:actionBridge.operatorInstruction,
      next_step:actionBridge.nextStep,
      no_broker_order:actionBridge.noBrokerOrder===true
    };
    return record;
  }
  // Cell 14 — Journal → Operator Memory write-back (pure; 1:1 field map; never Candidate).
  // null in fields[id] means SKIP write (blank/missing). Explicit journal 0 → "0".
  const MEMORY_IDS=Object.freeze([
    "nav","strategyPool","newCapital","qqqShares","vxxPct","qqqCalls","vxxCalls",
    "qqqShortStrike","qqqLongStrike","qqqExpiry","qqqDte","qqqDelta","qqqEntryCredit",
    "vxxShortStrike","vxxLongStrike","vxxExpiry","vxxDte","vxxDelta","vxxEntryCredit"
  ]);
  // Easy 1:1 map (Journal path → Memory UI id). Documented in README + UI help.
  const JOURNAL_MEMORY_MAP=Object.freeze([
    {journalPath:"current_position.nav",memoryId:"nav"},
    {journalPath:"funding_context.strategy_pool",memoryId:"strategyPool"},
    {journalPath:"funding_context.new_capital",memoryId:"newCapital"},
    {journalPath:"current_position.qqqShares",memoryId:"qqqShares"},
    {journalPath:"current_position.vxxPct",memoryId:"vxxPct"},
    {journalPath:"current_position.qqqCalls",memoryId:"qqqCalls"},
    {journalPath:"current_position.vxxCalls",memoryId:"vxxCalls"},
    {journalPath:"current_option_legs.qqq.shortStrike",memoryId:"qqqShortStrike"},
    {journalPath:"current_option_legs.qqq.longStrike",memoryId:"qqqLongStrike"},
    {journalPath:"current_option_legs.qqq.expiry",memoryId:"qqqExpiry"},
    {journalPath:"current_option_legs.qqq.dte",memoryId:"qqqDte"},
    {journalPath:"current_option_legs.qqq.delta",memoryId:"qqqDelta"},
    {journalPath:"current_option_legs.qqq.entryCredit",memoryId:"qqqEntryCredit"},
    {journalPath:"current_option_legs.vxx.shortStrike",memoryId:"vxxShortStrike"},
    {journalPath:"current_option_legs.vxx.longStrike",memoryId:"vxxLongStrike"},
    {journalPath:"current_option_legs.vxx.expiry",memoryId:"vxxExpiry"},
    {journalPath:"current_option_legs.vxx.dte",memoryId:"vxxDte"},
    {journalPath:"current_option_legs.vxx.delta",memoryId:"vxxDelta"},
    {journalPath:"current_option_legs.vxx.entryCredit",memoryId:"vxxEntryCredit"}
  ]);
  function pathGet(obj,path){
    if(obj===null||obj===undefined)return undefined;
    const parts=String(path).split(".");
    let cur=obj;
    for(const p of parts){
      if(cur===null||cur===undefined||typeof cur!=="object")return undefined;
      cur=cur[p];
    }
    return cur;
  }
  // Extract a Memory UI string from a journal scalar or {status,value} wrapper.
  // EMPTY / missing / blank → null (skip). Explicit 0 → "0". Never invent from candidates.
  function journalScalarToMemory(raw,warnings,journalPath){
    if(raw===null||raw===undefined)return null;
    if(typeof raw==="object"){
      // Prefer .value when status is VALUE; raw number properties are not walked here.
      if("status" in raw){
        const st=String(raw.status||"").toUpperCase();
        if(st==="EMPTY")return null;
        if(st==="INVALID"){
          if(Array.isArray(warnings))warnings.push(journalPath+": INVALID — skipped");
          return null;
        }
        if(st==="VALUE"){
          const v=raw.value;
          if(v===null||v===undefined||v==="")return null;
          if(typeof v==="number")return Number.isFinite(v)?String(v):null;
          return String(v).trim()===""?null:String(v).trim();
        }
        // Unknown status — try .value then give up
        if(raw.value!==undefined)return journalScalarToMemory(raw.value,warnings,journalPath);
        return null;
      }
      // Unexpected object without status — do not invent
      if(Array.isArray(warnings))warnings.push(journalPath+": non-scalar object — skipped");
      return null;
    }
    if(typeof raw==="number")return Number.isFinite(raw)?String(raw):null;
    if(typeof raw==="boolean")return raw?"1":"0";
    const s=String(raw).trim();
    return s===""?null:s;
  }
  function memoryFromJournal(row){
    const src=row&&typeof row==="object"?row:{};
    const fields=Object.create(null);
    const skipped=[];
    const warnings=[];
    // Explicitly refuse candidate / NOW-plan keys — never map into Memory Current Leg.
    if(src.candidates!==undefined||src.candidate!==undefined||(src.snapshot&&src.snapshot.candidates)){
      warnings.push("candidates present on row but never mapped into Memory Current Leg fields");
    }
    for(const id of MEMORY_IDS) fields[id]=null;
    for(const {journalPath,memoryId} of JOURNAL_MEMORY_MAP){
      const raw=pathGet(src,journalPath);
      // Also accept bare .value sibling already handled inside journalScalarToMemory
      const mem=journalScalarToMemory(raw,warnings,journalPath);
      fields[memoryId]=mem;
      if(mem===null) skipped.push(memoryId);
    }
    const sourceEventId=src.event_id!==undefined&&src.event_id!==null?String(src.event_id):null;
    return{fields,skipped,sourceEventId,warnings,map:JOURNAL_MEMORY_MAP};
  }
  function memoryMapPreview(mapped){
    const m=mapped&&typeof mapped==="object"?mapped:{};
    const fields=m.fields&&typeof m.fields==="object"?m.fields:{};
    const lines=[];
    for(const {journalPath,memoryId} of JOURNAL_MEMORY_MAP){
      const v=fields[memoryId];
      if(v===null||v===undefined) continue;
      lines.push(journalPath+" → Memory "+memoryId+" = "+v);
    }
    return lines;
  }
  return{POLICY,num,operatorNumber,operatorExpiry,parseOptionLeg,currentOptionLegs,dteFromExpiry,term,sourceCadence,dataHealth,derive,optionQty,normalizeOptionChain,candidateFromChain,targetLedger,actionRows,flatBookSilence,triggers,operatorSummary,fundingPlan,strategyActionBridge,exposureLabels,impliedVxxShares,journalRecord,MEMORY_IDS,JOURNAL_MEMORY_MAP,memoryFromJournal,memoryMapPreview};
})();