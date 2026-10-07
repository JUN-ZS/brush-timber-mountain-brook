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
  function daysBetween(a,b){if(!a||!b)return null;const x=new Date(a+"T00:00:00Z").getTime(),y=new Date(b+"T00:00:00Z").getTime();if(!Number.isFinite(x)||!Number.isFinite(y))return null;return Math.abs(y-x)/86400000;}
  function dataHealth(d){
    const hasSpot=[d.qqq,d.vxx,d.vix].every(Number.isFinite),hasTerm=Number.isFinite(d.m1)&&Number.isFinite(d.m2)&&Number.isFinite(d.s);
    if(!hasSpot||!hasTerm)return{status:"BLOCKED",label:"DATA BLOCKED",reason:"Required spot or VX term field missing."};
    const age=d.termAsOf&&d.today?daysBetween(d.termAsOf,d.today):0,asofGap=d.spotAsOf&&d.termAsOf?daysBetween(d.spotAsOf,d.termAsOf):0;
    if(age!==null&&age>POLICY.maxTermAgeDays)return{status:"STALE",label:"DATA STALE",ageDays:age,reason:"VX term source is older than the permitted operator cadence."};
    if(asofGap!==null&&asofGap>2)return{status:"MIXED",label:"AS-OF MIXED",ageDays:asofGap,reason:"Spot and term inputs are materially out of sync; review before acting."};
    return{status:"FRESH",label:"DATA FRESH",ageDays:age,reason:"Required fields are present and within the configured cadence."};
  }
  function derive(d){
    const health=dataHealth(d);
    if(health.status==="BLOCKED")return{state:"DATA BLOCKED",action:"HOLD",gate:"BLOCKED",targets:null,blocked:true,health,reason:"Data incomplete: preserve current position and do not invent a risk action."};
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
  function triggers(d,e,opt={}){
    const rows=[];
    if(Number.isFinite(d.s)){
      rows.push({id:"S_ZERO",label:"VX term to zero",value:d.s<=0?"TRIGGERED":d.s.toFixed(2)+"% → 0",fire:d.s<=0,mode:d.s<=0?"TRIGGER":"WATCH",priority:"HIGH"});
      rows.push({id:"S_SAFE",label:"VX carry line",value:d.s<=POLICY.termSafe?d.s.toFixed(2)+"% ≤ 5%":"above 5%",fire:false,mode:d.s<=POLICY.termSafe?"WATCH":"NORMAL",priority:"MED"});
    }
    if(Number.isFinite(d.vix))rows.push({id:"VIX_28",label:"VIX high line",value:d.vix>=POLICY.vixHigh?"TRIGGERED":(POLICY.vixHigh-d.vix).toFixed(2)+" away",fire:d.vix>=POLICY.vixHigh,mode:d.vix>=POLICY.vixHigh?"TRIGGER":"WATCH",priority:"HIGH"});
    const qdte=num(opt.qqqDte),qdelta=num(opt.qqqDelta),vdte=num(opt.vxxDte),vdelta=num(opt.vxxDelta);
    const hasQ=opt.hasQQQCall===true,hasV=opt.hasVXXCall===true;
    rows.push({id:"QQQ_ROLL",label:"QQQ far call roll",value:!hasQ?"NO POSITION":"DTE "+(Number.isFinite(qdte)?qdte:"—")+" · Δ "+(Number.isFinite(qdelta)?qdelta.toFixed(2):"—"),fire:hasQ&&((Number.isFinite(qdte)&&qdte<=POLICY.qqqRollDte)||(Number.isFinite(qdelta)&&qdelta>=POLICY.qqqRollDelta)),mode:!hasQ?"NO_POSITION":((Number.isFinite(qdte)||Number.isFinite(qdelta))?"TRIGGERABLE":"NEEDS_POSITION_DATA"),priority:"MED"});
    rows.push({id:"VXX_ROLL",label:"VXX call roll",value:!hasV?"NO POSITION":"DTE "+(Number.isFinite(vdte)?vdte:"—")+" · Δ "+(Number.isFinite(vdelta)?vdelta.toFixed(2):"—"),fire:hasV&&((Number.isFinite(vdte)&&vdte<=POLICY.vxxRollDte)||(Number.isFinite(vdelta)&&vdelta>=POLICY.vxxRollDelta)||e.state==="SHOCK"),mode:!hasV?"NO_POSITION":((Number.isFinite(vdte)||Number.isFinite(vdelta)||e.state==="SHOCK")?"TRIGGERABLE":"NEEDS_POSITION_DATA"),priority:"HIGH"});
    return rows;
  }
  function operatorSummary(d,e,book,candidates={},opt={}){
    const hasPosition=book.current.qqqShares>0||book.current.vxxPct>0||book.current.qqqCalls>0||book.current.vxxCalls>0;
    const acts=Object.entries(book.deltas||{}).filter(([,v])=>Number.isFinite(v)&&Math.abs(v)>1e-9);
    const mode=e.blocked?"PAUSED":e.action==="REDUCE"?"DEFEND":e.action==="HOLD"?"WATCH":acts.length?"BUILD / REBALANCE":hasPosition?"AT TARGET / MONITOR":"EMPTY / READY TO BUILD";
    const plan=[];
    if(e.blocked) plan.push("不新增、不減倉：等待完整新數據");
    else if(e.action==="HOLD") plan.push("不新增 carry：保留現有倉位，等轉態");
    else if(e.action==="REDUCE"){
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
    const rolls={
      qqq:rollDistance("QQQ far",book.current.qqqCalls,opt.qqqDte,opt.qqqDelta,POLICY.qqqRollDte,POLICY.qqqRollDelta),
      vxx:rollDistance("VXX call",book.current.vxxCalls,opt.vxxDte,opt.vxxDelta,POLICY.vxxRollDte,POLICY.vxxRollDelta)
    };
    return{mode,plan,thresholds:thresholds.slice(0,3),rolls,hasPosition};
  }
  function fmtNum(v){return Number.isFinite(Number(v))?Number(v).toLocaleString("en-US",{maximumFractionDigits:2}):"—";}
  function fmtPct(v){return Number.isFinite(Number(v))?fmtNum(v)+"%":"—";}
  function optionPlan(label,c,n){
    if(!c)return label+" +"+fmtNum(n)+" spreads · candidate PENDING";
    return label+" +"+fmtNum(n)+" spreads · "+fmtNum(c.shortStrike)+"/"+fmtNum(c.longStrike)+" · DTE "+fmtNum(c.dte)+" · Δ "+fmtNum(c.delta)+" · credit "+fmtNum(c.credit);
  }
  function rollDistance(label,count,dte,delta,dteLine,deltaLine){
    if(!(count>0))return{label,status:"OFF",text:"NO POSITION"};
    const present=v=>v!==null&&v!==undefined&&String(v).trim()!=="";
    const d=present(dte)?Number(dte):null,del=present(delta)?Number(delta):null;
    if(d===null&&!Number.isFinite(del))return{label,status:"NEEDS_DATA",text:"輸入現有 spread DTE / Δ"};
    const dteLeft=Number.isFinite(d)?d-dteLine:null;
    const deltaLeft=Number.isFinite(del)?deltaLine-del:null;
    const fire=(Number.isFinite(dteLeft)&&dteLeft<=0)||(Number.isFinite(deltaLeft)&&deltaLeft<=0);
    const parts=[];
    if(Number.isFinite(dteLeft))parts.push("DTE "+(dteLeft<=0?"ROLL NOW":fmtNum(dteLeft)+"d"));
    if(Number.isFinite(deltaLeft))parts.push("Δ "+(deltaLeft<=0?"ROLL NOW":fmtNum(deltaLeft)));
    return{label,status:fire?"ROLL_NOW":"WATCH",text:parts.join(" · ")};
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
  return{POLICY,num,operatorNumber,operatorExpiry,parseOptionLeg,currentOptionLegs,term,dataHealth,derive,optionQty,normalizeOptionChain,candidateFromChain,targetLedger,actionRows,triggers,operatorSummary};
})();