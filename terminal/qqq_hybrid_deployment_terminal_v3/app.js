
const E=HybridEngineV3;
const $=id=>document.getElementById(id);
let live=null;
const candidates={qqq:null,vxx:null};
let journalRows=[];
let putRatioSnapshot=null;
let putRatioCurrentOutput=null;
let putRatioLoadError=null;

const fmt=(v,d=2)=>Number.isFinite(Number(v))?Number(v).toFixed(d):"—";
const pct=(v,d=2)=>Number.isFinite(Number(v))?((Number(v)>=0?"+":"")+Number(v).toFixed(d)+"%"):"—";

function ledger(){
  return {
    nav:Number($("nav").value)||0,
    qqqShares:Number($("qqqShares").value)||0,
    vxxPct:Number($("vxxPct").value)||0,
    qqqCalls:Number($("qqqCalls").value)||0,
    vxxCalls:Number($("vxxCalls").value)||0
  };
}

function inputRow(){
  if(!live) return {qqq:null,vxx:null,vix:null,m1:null,m2:null,s:null,termAsOf:null,spotAsOf:null,today:new Date().toISOString().slice(0,10)};
  return {
    ...live,
    s:Number.isFinite(Number(live.term_slope))?Number(live.term_slope):E.term(Number(live.m1),Number(live.m2)),
    termAsOf:live.term_asof,
    spotAsOf:live.spot_asof,
    today:new Date().toISOString().slice(0,10)
  };
}

function renderFlow(d,e,book){
  const ids=["flowData","flowDecision","flowBuild","flowWatch","flowJournal"];
  ids.forEach(id=>{const el=$(id);if(el)el.className="flow-step";});
  let active="flowWatch",tone="active",next="NEXT: REFRESH";
  const hasPosition=book.current.qqqShares>0||book.current.vxxPct>0||book.current.qqqCalls>0||book.current.vxxCalls>0;
  const changed=($("sinceJournal")?.className||"").includes("changed");
  if(e.blocked){active="flowData";tone="danger";next="NEXT: GET FRESH, COMPLETE DATA";}
  else if(e.action==="BUY" && !hasPosition){active="flowBuild";next="NEXT: REVIEW TARGET → BUILD POSITION";}
  else if(e.action==="BUY"){active="flowBuild";next="NEXT: EXECUTE DELTAS → JOURNAL";}
  else if(e.action==="REDUCE"){active="flowDecision";tone="danger";next="NEXT: REDUCE SELLER RISK → JOURNAL";}
  else if(changed){active="flowWatch";tone="warn";next="NEXT: REVIEW WHAT CHANGED";}
  else {active="flowWatch";next="NEXT: REFRESH ON 1–2 DAY CADENCE";}
  const el=$(active);if(el)el.classList.add(tone);
  if($("flowJournal")&&journalRows.length) $("flowJournal").classList.add(changed?"warn":"active");
  if($("nextStep")) $("nextStep").textContent=next;
  $("gateData").textContent=e.health.status;
  $("gateTerm").textContent=Number.isFinite(d.s)?(d.s>5?"OPEN":d.s>0?"THIN":"CUT"):"BLOCK";
  $("gateVix").textContent=Number.isFinite(d.vix)?(d.vix>=E.POLICY.vixHigh?"HIGH":"OK"):"—";
  $("gateSpot").textContent=[d.qqq,d.vxx,d.vix].every(Number.isFinite)?"OK":"MISSING";
  $("gateReason").textContent=e.health.reason+" · "+e.reason;
  if($("watchSummary")){
    const opt={qqqDte:Number($("qqqDte").value),qqqDelta:Number($("qqqDelta").value),vxxDte:Number($("vxxDte").value),vxxDelta:Number($("vxxDelta").value)};
    const fires=E.triggers(d,e,opt).filter(x=>x.fire).length;
    $("watchSummary").textContent=fires?fires+" TRIGGER"+(fires===1?"":"S"):"WATCHING";
  }
}

function render(d,e,book){
  renderFlow(d,e,book);
  $("qqq").textContent=fmt(d.qqq);
  $("vxx").textContent=fmt(d.vxx);
  $("vix").textContent=fmt(d.vix);
  $("term").textContent=pct(d.s);
  $("m1").textContent="M1 "+fmt(d.m1);
  $("m2").textContent="M2 "+fmt(d.m2);
  $("termMeta").textContent=(live?.m1_code||live?.m1?.symbol||"—")+" → "+(live?.m2_code||live?.m2?.symbol||"—")+" · "+(live?.term_source||"BLOCKED");
  $("sourceMeta").textContent=(live?.source_chain||[]).join(" → ")||"NO SOURCE";
  $("asof").textContent="term as-of "+(d.termAsOf||"—")+" · spot as-of "+(d.spotAsOf||"—");
  $("action").textContent=e.blocked?"HOLD / BLOCKED":e.action;
  $("reason").textContent=e.reason;
  $("stateBadge").textContent=e.state;
  $("dataBadge").textContent=e.health.label;
  $("dataBadge").className="badge "+(e.health.status==="FRESH"?"ok":e.blocked?"block":"warn");
  $("stateBadge").className="badge "+(e.state==="CARRY"?"ok":e.state==="SHOCK"||e.state==="PRE-SHOCK"?"block":"warn");
  $("monitorTag").textContent=e.blocked?"NO ACTION":e.gate;
  if($("qqqSize")) $("qqqSize").textContent=optionSizingText(book.sizing?.qqqCalls);
  if($("vxxSize")) $("vxxSize").textContent=optionSizingText(book.sizing?.vxxCalls);
  if($("qqqCandidate")) $("qqqCandidate").textContent=candidates.qqq?candidateText(candidates.qqq):"No QQQ candidate";
  if($("vxxCandidate")) $("vxxCandidate").textContent=candidates.vxx?candidateText(candidates.vxx):"No VXX candidate";
  if($("candidateSource")) $("candidateSource").textContent=[candidates.qqq?.source,candidates.vxx?.source].filter(Boolean).join(" / ")||"NONE";

  const rows=[
    ["QQQ CORE",book.current.qqqShares,book.target.qqqShares,book.deltas.qqqShares,"shares"],
    ["VXX SHORT",book.current.vxxPct,book.target.vxxPct,book.deltas.vxxPct,"% NAV"],
    ["QQQ CALL",book.current.qqqCalls,book.target.qqqCalls,book.deltas.qqqCalls,"spreads"],
    ["VXX CALL",book.current.vxxCalls,book.target.vxxCalls,book.deltas.vxxCalls,"spreads"],
  ];
  $("ledgerRows").innerHTML=rows.map(r=>{
    const kind=Math.abs(r[3])<1e-9?"HOLD":r[3]>0?"ADD":"REDUCE";
    return '<div class="ledger-row"><span>'+r[0]+'</span><span>'+fmt(r[1])+'</span><span>'+fmt(r[2])+'</span><span class="'+kind+'">'+kind+" "+(Math.abs(r[3])<1e-9?"":(r[3]>0?"+":"")+fmt(r[3])+" "+r[4])+'</span></div>';
  }).join("");

  const acts=E.actionRows(book).filter(x=>Math.abs(x.diff)>1e-9);
  const queueRows=[];
  if(e.blocked){
    queueRows.push('<div class="queue-item HOLD"><b>DATA GATE</b><span>BLOCKED · CURRENT KEPT; RISK NOT CLEARED</span></div>');
  }else{
    if(acts.length) queueRows.push(acts.map(x=>'<div class="queue-item '+x.kind+'"><b>'+x.key+'</b><span>'+x.kind+' · '+fmt(x.diff)+'</span></div>').join(""));
    if(book.unresolvedTargets?.length) queueRows.push('<div class="queue-item HOLD"><b>OPTION TARGET PENDING</b><span>CURRENT QUANTITY RETAINED · CAPACITY NOT VERIFIED</span></div>');
    if(!acts.length&&!book.unresolvedTargets?.length) queueRows.push('<div class="queue-item HOLD"><b>NO POSITION CHANGE</b><span>WAIT / HOLD</span></div>');
  }
  $("queue").innerHTML=queueRows.join("");

  const opts={
    qqqDte:Number($("qqqDte").value),
    qqqDelta:Number($("qqqDelta").value),
    vxxDte:Number($("vxxDte").value),
    vxxDelta:Number($("vxxDelta").value)
  };
  const tr=E.triggers(d,e,opts);
  $("triggerRows").innerHTML=tr.map(x=>'<div class="trigger '+(x.fire?"fire":"")+'"><span><b>'+x.label+'</b><small> '+x.priority+'</small></span><span>'+x.value+'</span><strong>'+(x.fire?"TRIGGER":"WATCH")+'</strong></div>').join("");

  $("prov").innerHTML=[
    ["QQQ/VXX/VIX",(live?.provenance?Object.entries(live.provenance).filter(([k])=>["qqq","vxx","vix"].includes(k)).map(([,v])=>v).join(" / "):"—"),"OBSERVED"],
    ["VX M1",live?.m1_code||"—",live?.term_source?"OBSERVED":"BLOCKED"],
    ["VX M2",live?.m2_code||"—",live?.term_source?"OBSERVED":"BLOCKED"],
    ["S_t","(M2-M1)/M1","DERIVED"],
    ["Target","frozen policy + ledger","DERIVED"]
  ].map(r=>'<div class="prov-row"><span>'+r[0]+' · '+r[1]+'</span><span class="tag '+r[2].toLowerCase()+'">'+r[2]+'</span></div>').join("");
  renderPutRatioEvidence();
}

function putRatioMoney(value){
  const x=Number(value);
  if(!Number.isFinite(x))return "—";
  return (x<0?"−$":"$")+Math.abs(x).toLocaleString("en-US",{minimumFractionDigits:0,maximumFractionDigits:2});
}
function putRatioPercent(value){
  const x=Number(value);
  return Number.isFinite(x)?x.toFixed(2)+"%":"—";
}
function putRatioInput(id){const el=$(id);return el?el.value:"";}
function makePutRatioMetric(host,label,value,detail){
  const card=document.createElement("div");card.className="put-ratio-metric";
  const l=document.createElement("span");l.textContent=label;
  const v=document.createElement("b");v.textContent=value;
  const d=document.createElement("small");d.textContent=detail||"";
  card.append(l,v,d);host.appendChild(card);
}
function makePutRatioAlert(host,tone,title,text){
  const card=document.createElement("div");card.className="put-ratio-alert "+(tone||"");
  const h=document.createElement("b");h.textContent=title;
  const p=document.createElement("div");p.textContent=text;
  card.append(h,p);host.appendChild(card);
}
function putRatioInputs(){
  return {
    nav:ledger().nav,
    direction:putRatioInput("putRatioDirection"),
    n:putRatioInput("putRatioN"),
    policyId:putRatioInput("putRatioPolicy"),
    riskPct:putRatioInput("putRatioRiskPct"),
    profitPct:putRatioInput("putRatioProfitPct"),
    currentPnl:putRatioInput("putRatioCurrentPnl"),
    age:putRatioInput("putRatioAge"),
    dte:putRatioInput("putRatioDte"),
    rv20:putRatioInput("putRatioRv20"),
    horizon:putRatioInput("putRatioHorizon"),
    combinedReview:!!$("putRatioCombined")?.checked
  };
}
function renderPutRatioEvidence(){
  const badge=$("putRatioEvidenceBadge"),metrics=$("putRatioMetrics"),status=$("putRatioOverlayStatus"),alerts=$("putRatioAlerts"),ddRows=$("putRatioDdRows"),prov=$("putRatioProvenance"),gate=$("putRatioDecisionGate");
  if(!badge||!metrics||!status||!alerts||!ddRows||!prov)return;
  metrics.textContent="";alerts.textContent="";
  const combined=!!$("putRatioCombined")?.checked;
  if(!putRatioSnapshot||!window.PutRatioEvidenceV1){
    badge.textContent=putRatioLoadError?"EVIDENCE BLOCKED":"EVIDENCE PENDING";
    badge.className="tag research";
    makePutRatioMetric(metrics,"歷史 WIN","PENDING","固定來源證據尚未載入");
    makePutRatioMetric(metrics,"尾部風險","PENDING","不假設零損失");
    status.className="put-ratio-overlay-status";
    status.textContent=(combined?"COMBINED REVIEW":"ISOLATED EVIDENCE")+" · PENDING · "+(putRatioLoadError||"等待 read-only evidence API");
    ddRows.innerHTML='<tr><td colspan="6">PENDING · 沒有回填或虛構 MaxDD</td></tr>';
    makePutRatioAlert(alerts,"warn","研究證據未載入",putRatioLoadError||"固定 SHA 來源證據尚未讀取；Hybrid 原政策照常獨立運行。");
    prov.textContent="Evidence API: /api/research/put-ratio-evidence";
    if(gate){gate.textContent="PUT RATIO EVIDENCE · PENDING · PRIMARY FROZEN ACTION UNCHANGED";gate.className="put-ratio-decision-line off";}
    putRatioCurrentOutput=null;
    return;
  }
  const out=window.PutRatioEvidenceV1.evaluate(putRatioSnapshot,putRatioInputs());
  putRatioCurrentOutput=out;
  const matched=out.history;
  const curve=out.serialCurve;
  badge.textContent=out.evidenceStatus==="AVAILABLE_RESEARCH_ONLY"?"PINNED · 62 HISTORICAL EPISODES":"EVIDENCE BLOCKED";
  badge.className="tag "+(out.evidenceStatus==="AVAILABLE_RESEARCH_ONLY"?"research":"retired");
  makePutRatioMetric(metrics,"歷史 WIN",matched?putRatioPercent(matched.winRatePct):"NO MATCH",matched?matched.resolved+"/62 組已結算 · "+matched.policyId:"此方向／N 沒有直接歷史勝率");
  makePutRatioMetric(metrics,"累計淨損益",matched?putRatioMoney(matched.netPnlUsd):"—",matched?"固定一組一組、不複利": "不沿用 1:5 結果");
  makePutRatioMetric(metrics,"策略 MaxDD",curve?pct(curve.maxPct):"NO MATCH",curve?curve.maxPeakDate+" → "+curve.maxTroughDate:"沒有同結構逐日曲線");
  makePutRatioMetric(metrics,"最差觀察尾部損失",out.tail.worstUsd===null?"PENDING":putRatioMoney(out.tail.worstUsd),out.tail.lossPctOfNav===null?"NAV 未知":pct(out.tail.lossPctOfNav)+" of current NAV");
  makePutRatioMetric(metrics,"尾部預算整組數",out.tail.wholeUnits===null?"PENDING":String(out.tail.wholeUnits),putRatioMoney(out.tail.budgetUsd)+" budget · theoretical only");
  makePutRatioMetric(metrics,"目前獲利線",putRatioMoney(out.profitTarget.navTargetUsd),out.profitTarget.directFixedTargetUsd!==null&&matched?"直接匹配 +$"+out.profitTarget.directFixedTargetUsd+" 歷史政策":"無同額直接回測，不能插值");
  const vol=out.volatility,sv=vol?.selected,av=vol?.all;
  makePutRatioMetric(metrics,"QQQ 跌 ≥5% 頻率",sv?pct(sv.down5Pct):"—",sv?"N="+sv.n+" · "+vol.horizon+" sessions": "RV20 / horizon data pending");
  makePutRatioMetric(metrics,"QQQ 跌 ≥10% 頻率",sv?pct(sv.down10Pct):"—",sv&&av?"ALL 基準 "+pct(av.down10Pct):"Underlying-only");
  status.className="put-ratio-overlay-status "+(combined&&out.combinedReview.status==="BLOCK_PUT_RATIO_ADDITION"?"block":combined&&out.combinedReview.status==="REVIEW_PUT_RATIO_SCENARIO"?"review":"");
  status.textContent=(combined?"COMBINED REVIEW":"ISOLATED EVIDENCE")+" · "+out.combinedReview.status+" · "+out.combinedReview.reason+" Frozen Hybrid action/target unchanged; no broker order.";
  ddRows.innerHTML=curve?curve.levels.map(x=>{
    const years=x.eventYears.length?x.eventYears.map(y=>y+" ("+x.yearCounts[y]+")").join(", "):"無觀察事件";
    const incidence=x.yearIncidencePct===null?"—":x.yearIncidencePct.toFixed(1)+"% ("+x.years+"/"+x.allYears+")";
    const gap=x.medianGap===null?"—":Math.round(x.medianGap);
    return '<tr><td>−'+x.level+'%</td><td>'+x.count+'</td><td>'+x.perYear.toFixed(2)+'</td><td>'+incidence+'</td><td>'+years+'</td><td>'+gap+'</td></tr>';
  }).join(""):'<tr><td colspan="6">NO MATCHED HISTORY · 不會把 1:5 的曲線套用到其他比例</td></tr>';
  if(!matched)makePutRatioAlert(alerts,"warn","沒有直接匹配的期權策略歷史","目前選擇 "+(out.inputs.direction==="SHORT_HEAVY"?"LONG 1 : SHORT "+out.inputs.n:"LONG "+out.inputs.n+" : SHORT 1")+"。只有 LONG 1 : SHORT 5 具備這份 62 組直接歷史樣本；不複製其他比例的 WIN／MaxDD。");
  (out.alerts||[]).forEach(a=>makePutRatioAlert(alerts,a.tone,a.title,a.text));
  if(!out.alerts.length&&matched)makePutRatioAlert(alerts,"good","沒有額外條件觸發","不代表可部署；歷史資料、尾部預算及實際成交限制仍須人工核對。");
  prov.textContent=[
    "研究 ID: "+(putRatioSnapshot.metadata?.researchId||"—")+" · study SHA: "+(out.manifest?.sourceStudyCommit||"—"),
    "Data SHA: "+(out.manifest?.dataJsonBlobSha||"—"),
    "Curve SHA: "+(out.manifest?.portfolioCurveBlobSha||"—"),
    "Profit-trigger SHA: "+(out.manifest?.profitWarningAnalysisBlobSha||"—"),
    "Option source: "+(putRatioSnapshot.metadata?.optionSource||"—")+" · cutoff "+(putRatioSnapshot.metadata?.optionSourceEnd||"—")+" · N="+(putRatioSnapshot.metadata?.optionEpisodes||"—"),
    "Cost: $"+putRatioSnapshot.metadata?.costCase?.slippagePerLegSideUsd+"/leg/side slippage + $"+putRatioSnapshot.metadata?.costCase?.commissionPerContractSideUsd+"/contract/side commission.",
    "Missing daily marks remain null. QQQ price-path frequencies are not Put Ratio loss probabilities. Margin, assignment, interim liquidation and confirmed fills remain unknown."
  ].join("\n");
  if(gate){
    if(!combined){gate.textContent="PUT RATIO EVIDENCE · ISOLATED · "+(matched?"62-EPISODE HISTORY AVAILABLE":"NO MATCHED STRATEGY HISTORY")+" · PRIMARY FROZEN ACTION UNCHANGED";gate.className="put-ratio-decision-line off";}
    else if(out.combinedReview.status==="BLOCK_PUT_RATIO_ADDITION"){gate.textContent="COMBINED REVIEW · BLOCK NEW PUT RATIO ADDITIONS (TAIL BUDGET) · EXISTING HYBRID TARGETS UNCHANGED";gate.className="put-ratio-decision-line block";}
    else if(out.combinedReview.status==="REVIEW_PUT_RATIO_SCENARIO"){gate.textContent="COMBINED REVIEW · MANUAL PUT RATIO RISK REVIEW REQUIRED · EXISTING HYBRID TARGETS UNCHANGED";gate.className="put-ratio-decision-line review";}
    else{gate.textContent="COMBINED REVIEW · RESEARCH CONTEXT ONLY · NO NEW PUT RATIO AUTHORITY";gate.className="put-ratio-decision-line off";}
  }
}
async function loadPutRatioEvidence(){
  try{
    const r=await fetch("/api/research/put-ratio-evidence?ts="+Date.now(),{cache:"no-store"});
    const j=await r.json();
    if(!r.ok||!j.ok)throw new Error(j.error||"Put Ratio evidence source unavailable");
    putRatioSnapshot=j.evidence;putRatioLoadError=null;
  }catch(err){putRatioSnapshot=null;putRatioLoadError=String(err.message||err);}
  renderPutRatioEvidence();
}
function putRatioPolicySummary(){
  renderPutRatioEvidence();
  const o=putRatioCurrentOutput;
  if(!o)return {status:"PENDING",combinedReview:!!$("putRatioCombined")?.checked,executionEnabled:false};
  return {status:o.combinedReview.status,scenarioId:o.scenarioId,evidenceStatus:o.evidenceStatus,history:o.history?{policyId:o.history.policyId,winRatePct:o.history.winRatePct,netPnlUsd:o.history.netPnlUsd,episodes:o.history.episodes}:null,
    tail:{worstUsd:o.tail.worstUsd,lossPctOfNav:o.tail.lossPctOfNav,budgetUsd:o.tail.budgetUsd,wholeUnits:o.tail.wholeUnits,status:o.tail.status},
    profitTarget:{navTargetUsd:o.profitTarget.navTargetUsd,directFixedTargetUsd:o.profitTarget.directFixedTargetUsd,directPolicyId:o.history?o.profitTarget.directPolicy?.id||null:null},
    volatility:{state:o.volatility?.state,horizon:o.volatility?.horizon,elevated:o.volatility?.elevated},
    alerts:o.alerts.map(a=>({code:a.code,tone:a.tone,title:a.title})),primaryHybridActionMutation:false,primaryHybridTargetMutation:false,executionEnabled:false,
    sourceStudyCommit:o.manifest?.sourceStudyCommit||null,dataBlobSha:o.manifest?.dataJsonBlobSha||null,curveBlobSha:o.manifest?.portfolioCurveBlobSha||null};
}

function optionSizingText(s){
  if(!s) return "PENDING";
  if(s.status==="READY") return "CAP VERIFIED · "+fmt(s.quantity,0)+" spreads · human review required";
  if(s.status==="POLICY_TARGET_ZERO") return "POLICY TARGET 0 · exit capacity separate";
  const theoretical=s.creditBudgetQuantity!==null&&s.creditBudgetQuantity!==undefined&&Number.isFinite(Number(s.creditBudgetQuantity))?" · credit-only "+fmt(s.creditBudgetQuantity,0)+" theoretical":"";
  return String(s.status||"PENDING").replaceAll("_"," ")+theoretical;
}

function candidateText(c){
  if(!c) return "—";
  const credit=Number.isFinite(Number(c.credit))?Number(c.credit).toFixed(2):"—";
  const quoteTime=c.quoteTimestampVerified?"SOURCE QUOTE TIME VERIFIED":"SOURCE QUOTE TIME UNVERIFIED (retrieval time only)";
  return "short "+fmt(c.shortStrike)+" / long "+fmt(c.longStrike)+" · DTE "+fmt(c.dte,0)+" · Δ "+fmt(c.delta,2)+" · credit "+credit+" · "+(c.deltaSource||"ESTIMATE")+" · "+quoteTime;
}

function applyCandidate(sym,c){
  candidates[sym]=c;
  const dteId=sym==="qqq"?"qqqDte":"vxxDte",deltaId=sym==="qqq"?"qqqDelta":"vxxDelta";
  if(c && $(dteId)) $(dteId).value=Number.isFinite(Number(c.dte))?Math.round(Number(c.dte)):"";
  if(c && $(deltaId)) $(deltaId).value=Number.isFinite(Number(c.delta))?Number(c.delta).toFixed(2):"";
  const d=inputRow(),e=E.derive(d),book=E.targetLedger(d,e,ledger(),candidates);
  render(d,e,book);
}

async function loadCandidate(sym){
  if(!live || !Number.isFinite(Number(live[sym]))) return;
  try{
    const r=await fetch("/api/options?symbol="+encodeURIComponent(sym.toUpperCase())+"&targetDte="+E.POLICY.optionTargetDte,{cache:"no-store"});
    const j=await r.json();
    if(!r.ok || !j.ok) throw new Error(j.error||"option source unavailable");
    const asOf=String(live.today||live.captured_at||"").slice(0,10);
    const c=E.candidateFromChain(j.calls,Number(live[sym]),0.10,E.POLICY.optionTargetDte,asOf,{retrievedAt:j.retrieved_at,source:j.source,symbol:sym.toUpperCase()});
    if(!c) throw new Error("no qualifying call spread candidate");
    c.apiExpiry=j.expiry||c.expiration;
    applyCandidate(sym,c);
  }catch(err){
    candidates[sym]=null;
    const d=inputRow(),e=E.derive(d),book=E.targetLedger(d,e,ledger(),candidates);
    render(d,e,book);
    if($("candidateSource")) $("candidateSource").textContent=sym.toUpperCase()+" unavailable: "+err.message;
  }
}

function renderChangeSinceJournal(){
  const el=$("sinceJournal");
  if(!el) return;
  if(!journalRows.length){el.textContent="No prior journal baseline.";el.className="meta";return;}
  const last=journalRows[journalRows.length-1],d=inputRow(),e=E.derive(d),book=E.targetLedger(d,e,ledger(),candidates);
  const changed=last.engine_action!==e.action || last.state!==e.state || JSON.stringify(last.target_position||{})!==JSON.stringify(book.target||{});
  el.textContent=changed?"CHANGED SINCE LAST JOURNAL · "+(last.state||"—")+" / "+(last.engine_action||"—")+" → "+e.state+" / "+e.action:"NO CHANGE SINCE LAST JOURNAL";
  el.className="meta "+(changed?"changed":"stable");
}

async function refresh(){
  $("refreshBtn").disabled=true;
  try{
    const res=await fetch("/api/snapshot?ts="+Date.now(),{cache:"no-store"});
    live=await res.json();
    await loadPutRatioEvidence();
    const d=inputRow();
    const e=E.derive(d);
    const book=E.targetLedger(d,e,ledger(),candidates);
    render(d,e,book);
    await loadJournal();
  }catch(err){
    $("reason").textContent="SNAPSHOT ERROR: "+err;
    $("dataBadge").textContent="ERROR";
    $("dataBadge").className="badge block";
  }finally{
    $("refreshBtn").disabled=false;
  }
}

async function journalDecision(){
  if(!live) return;
  const d=inputRow(), e=E.derive(d), book=E.targetLedger(d,e,ledger(),candidates);
  const researchEvidence=putRatioPolicySummary();
  const human=($("humanAction").value||"").trim().toUpperCase();
  const conflict=human && human!==e.action ? "CONFLICT":"NONE";
  const payload={
    event_id:"QHV3-"+Date.now(),
    snapshot:{
      captured_at:live.captured_at,
      data_asof:live.term_asof,
      qqq:live.qqq,vxx:live.vxx,vix:live.vix,
      m1:live.m1,m2:live.m2,m1_code:live.m1_code,m2_code:live.m2_code,
      m1_expiry:live.m1_expiry,m2_expiry:live.m2_expiry,
      term_slope:d.s,term_source:live.term_source,
      provenance:live.provenance
    },
    policy_version:E.POLICY.policyVersion,
    engine_version:E.POLICY.engineVersion,
    state:e.state,
    gate:e.gate,
    engine_action:e.action,
    reason:e.reason,
    current_position:book.current,
    target_position:book.target,
    deltas:book.deltas,
    human_action:human||null,
    research_evidence:{...researchEvidence,mode:$("putRatioCombined")?.checked?"COMBINED_REVIEW":"ISOLATED"},
    conflict,
  };
  const r=await fetch("/api/journal",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
  if(!r.ok) throw new Error("journal failed");
  $("humanAction").value="";
  await loadJournal();
}

async function loadJournal(){
  const r=await fetch("/api/journal",{cache:"no-store"});
  const j=await r.json();
  journalRows=j.rows||[];
  $("journalCount").textContent=journalRows.length;
  $("journalRows").innerHTML=journalRows.slice().reverse().map(x=>{
    const s=x.snapshot||{};
    const ov=x.research_evidence?.combinedReview||x.research_evidence?.status;
    return '<div class="journal-row"><b>'+((x.journaled_at||"").slice(0,19).replace("T"," "))+'</b> · '+(x.engine_action||"—")+' · '+(x.state||"—")+' · M1/M2 '+fmt(s.m1)+'/'+fmt(s.m2)+' · PUT RATIO '+(ov||"—")+' · '+(x.conflict||"NONE")+'</div>';
  }).join("") || '<div class="meta">No decisions journaled yet.</div>';
  renderChangeSinceJournal();
}

$("refreshBtn").addEventListener("click",refresh);
if($("findQQQ")) $("findQQQ").addEventListener("click",()=>loadCandidate("qqq"));
if($("findVXX")) $("findVXX").addEventListener("click",()=>loadCandidate("vxx"));
$("journalBtn").addEventListener("click",journalDecision);
["nav","qqqShares","vxxPct","qqqCalls","vxxCalls","qqqDte","qqqDelta","vxxDte","vxxDelta"].forEach(id=>$(id).addEventListener("input",()=>{if(live){const d=inputRow(),e=E.derive(d),book=E.targetLedger(d,e,ledger(),candidates);render(d,e,book)}}));
["putRatioDirection","putRatioN","putRatioPolicy","putRatioRiskPct","putRatioProfitPct","putRatioCurrentPnl","putRatioAge","putRatioDte","putRatioRv20","putRatioHorizon","putRatioCombined"].forEach(id=>{const el=$(id);if(el)el.addEventListener("input",renderPutRatioEvidence);});
if($("putRatioCombined"))$("putRatioCombined").addEventListener("change",renderPutRatioEvidence);
refresh();
