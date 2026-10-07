
const E=HybridEngineV3;
const $=id=>document.getElementById(id);
let live=null;
const candidates={qqq:null,vxx:null};
let optionsStatus=null; // last /api/options status (LIVE | OPTIONS_SOURCE_DOWN | BLOCKED_NO_OPEND)
let journalRows=[];
const MEMORY_LS_KEY="qhv3.operatorMemory.snapshot";
// Journal↔Memory map stays E.MEMORY_IDS; the local snapshot also keeps the beginner-only fields.
const MEMORY_FIELD_IDS=[...new Set([...(E.MEMORY_IDS||["nav","strategyPool","newCapital","qqqShares","vxxPct","qqqCalls","vxxCalls","qqqShortStrike","qqqLongStrike","qqqExpiry","qqqDte","qqqDelta","qqqEntryCredit","vxxShortStrike","vxxLongStrike","vxxExpiry","vxxDte","vxxDelta","vxxEntryCredit"]),"cash","vxxShortShares"])];
let lastLedger=null;

function readMemoryFields(){
  const out={};
  for(const id of MEMORY_FIELD_IDS){
    const el=$(id);
    out[id]=el?String(el.value):"";
  }
  return out;
}
function saveMemorySnapshot(eventId){
  try{
    const snap={
      event_id:eventId||null,
      saved_at:new Date().toISOString(),
      fields:readMemoryFields()
    };
    localStorage.setItem(MEMORY_LS_KEY,JSON.stringify(snap));
    return snap;
  }catch(err){
    return null;
  }
}
function loadMemorySnapshot(){
  try{
    const raw=localStorage.getItem(MEMORY_LS_KEY);
    if(!raw) return null;
    const j=JSON.parse(raw);
    if(!j||typeof j!=="object"||!j.fields||typeof j.fields!=="object") return null;
    return j;
  }catch(err){
    return null;
  }
}
function flashMemoryIds(ids){
  for(const id of ids){
    const el=$(id);
    if(!el) continue;
    el.classList.add("memory-flash");
    const label=el.closest("label");
    if(label) label.classList.add("memory-flash");
    setTimeout(()=>{
      el.classList.remove("memory-flash");
      if(label) label.classList.remove("memory-flash");
    },1600);
  }
}
function applyMemoryFields(fields,{sourceLabel}={}){
  const updated=[];
  const skipped=[];
  for(const id of MEMORY_FIELD_IDS){
    const v=fields&&Object.prototype.hasOwnProperty.call(fields,id)?fields[id]:null;
    if(v===null||v===undefined){skipped.push(id);continue;}
    const el=$(id);
    if(!el){skipped.push(id);continue;}
    el.value=String(v);
    updated.push(id);
  }
  flashMemoryIds(updated);
  if($("memoryMapPreview")){
    const lines=updated.map(id=>{
      const path=(E.JOURNAL_MEMORY_MAP||[]).find(m=>m.memoryId===id);
      const jp=path?path.journalPath:("memory."+id);
      return jp+" → Memory "+id+" = "+fields[id];
    });
    $("memoryMapPreview").textContent=lines.length
      ?(sourceLabel?sourceLabel+" · ":"")+lines.join(" · ")
      :(sourceLabel||"Restore")+": no fields to write (all blank/missing → left EMPTY)";
  }
  if($("memoryRestoreMeta")){
    $("memoryRestoreMeta").textContent=
      "Restored "+updated.length+" field(s)"+(skipped.length?" · skipped EMPTY "+skipped.length:"");
  }
  return{updated,skipped};
}
function restoreMemoryFromJournalRow(row){
  if(!row){
    if($("memoryMapPreview")) $("memoryMapPreview").textContent="No journal row to restore from.";
    return null;
  }
  const mapped=E.memoryFromJournal(row);
  const preview=E.memoryMapPreview(mapped);
  if($("memoryMapPreview")){
    $("memoryMapPreview").textContent=preview.length
      ?preview.join(" · ")
      :"Map preview: all journal fields blank/missing → Memory left EMPTY (null skip)";
  }
  const applied=applyMemoryFields(mapped.fields,{sourceLabel:"Journal "+(mapped.sourceEventId||"row")});
  // Persist applied memory + event_id for reload restore
  saveMemorySnapshot(mapped.sourceEventId);
  if(live){
    const d=inputRow(),e=E.derive(d),book=E.targetLedger(d,e,ledger(),candidates);
    render(d,e,book);
  }else{
    renderLegIdentity();
  }
  return{mapped,applied,preview};
}
function restoreMemoryFromLastJournal(){
  if(!journalRows.length){
    if($("memoryMapPreview")) $("memoryMapPreview").textContent="No journal rows yet — nothing to restore.";
    if($("memoryRestoreMeta")) $("memoryRestoreMeta").textContent="Restore skipped · empty journal";
    return null;
  }
  const last=journalRows[journalRows.length-1];
  return restoreMemoryFromJournalRow(last);
}
function restoreMemorySnapshotOnLoad(){
  const snap=loadMemorySnapshot();
  if(!snap) return null;
  // Safest: restore last Memory snapshot from localStorage on load if present.
  const applied=applyMemoryFields(snap.fields,{
    sourceLabel:"localStorage snapshot"+(snap.event_id?" · "+snap.event_id:"")
  });
  if($("memoryRestoreMeta")){
    $("memoryRestoreMeta").textContent=
      "Auto-restored Memory snapshot"+(snap.event_id?" · event "+snap.event_id:"")+
      " · "+applied.updated.length+" field(s)";
  }
  return{snap,applied};
}


const fmt=(v,d=2)=>Number.isFinite(Number(v))?Number(v).toFixed(d):"—";
const pct=(v,d=2)=>Number.isFinite(Number(v))?((Number(v)>=0?"+":"")+Number(v).toFixed(d)+"%"):"—";

const val=id=>$(id)?String($(id).value):"";
function ledger(){
  // Cell 18: beginner input → same ledger shape as before. Blank stays EMPTY (→ NEEDS INPUT), never 0.
  const raw={
    cash:val("cash"),
    nav:val("nav"),
    qqqShares:val("qqqShares"),
    vxxPct:val("vxxPct"),
    vxxShortShares:val("vxxShortShares"),
    qqqCalls:val("qqqCalls"),
    vxxCalls:val("vxxCalls")
  };
  const price=k=>live&&Number.isFinite(Number(live[k]))&&live[k]!==null?Number(live[k]):null;
  lastLedger=E.beginnerLedger(raw,{qqqPrice:price("qqq"),vxxPrice:price("vxx")});
  renderBeginnerInput(lastLedger);
  return lastLedger;
}
function effectiveNav(){
  const l=lastLedger||ledger();
  return l&&l.navInfo&&l.navInfo.status==="VALUE"?l.navInfo.value:null;
}
function renderBeginnerInput(l){
  const ni=l.navInfo||{};
  const el=$("navInUse");
  if(el){
    const usd=v=>"USD "+Number(v).toLocaleString("en-US",{maximumFractionDigits:2});
    if(ni.status==="VALUE"&&ni.source==="MANUAL") el.textContent="NAV 使用中：MANUAL override = "+usd(ni.value)+"（自動計已停用；清空 override 就用返 現金 + QQQ）";
    else if(ni.status==="VALUE") el.textContent="NAV 使用中：AUTO = 現金 "+usd(ni.cash)+" + QQQ "+fmt(ni.qqqShares,0)+" × "+(ni.qqqPrice!==null?fmt(ni.qqqPrice):"—")+" = "+usd(ni.value);
    else el.textContent="NAV："+(ni.status==="INVALID"?"INVALID · ":"")+(ni.reason||"未能計");
    el.className="nav-in-use"+(ni.status==="VALUE"?"":ni.status==="INVALID"?" invalid":" empty");
  }
  if($("vxxConvertMeta")){
    const vi=l.vxxInfo||{};
    const c=vi.conversion;
    $("vxxConvertMeta").textContent=
      vi.source==="SHARES"&&c&&c.status==="VALUE"
        ?"VXX short 由股數換算："+Number(c.shares).toLocaleString("en-US")+" 股 × "+fmt(c.price)+" = USD "+Number(c.usd).toLocaleString("en-US",{maximumFractionDigits:0})+" ÷ NAV "+Number(c.nav).toLocaleString("en-US",{maximumFractionDigits:0})+" = "+fmt(c.value)+"% NAV"
        :vi.source==="PCT"?"VXX short 直接用 % NAV："+fmt(l.vxxPct)+"%"+(vi.warning?" · ⚠ "+vi.warning:"")
        :"VXX short："+(vi.reason||"未填")+"（用 % NAV，唔係 option 張數）";
  }
  if($("inputStatusMeta")){
    const gap=E.inputGapText(l.inputStatus);
    $("inputStatusMeta").textContent=l.inputStatus.status==="READY"?"第一步 ✓ 已填齊":"NEEDS INPUT · "+gap;
    $("inputStatusMeta").className="meta"+(l.inputStatus.status==="READY"?"":" changed");
  }
}

function fundingInputs(){
  return {
    strategyPool:$("strategyPool")?$("strategyPool").value:"",
    newCapital:$("newCapital")?$("newCapital").value:""
  };
}
function renderFundingPlan(d,e,book){
  const f=fundingInputs();
  const nv=effectiveNav();
  const plan=E.fundingPlan({d,e,book,strategyPool:f.strategyPool,newCapital:f.newCapital,nav:nv===null?"":String(nv)});
  if($("strategyName"))$("strategyName").textContent=plan.strategyName;
  if($("strategyFormula"))$("strategyFormula").textContent=plan.formula;
  if($("fundingRegime"))$("fundingRegime").textContent=plan.regime+" · "+plan.route;
  if($("fundingMessage"))$("fundingMessage").textContent=plan.message;
  if($("fundingPoolStatus"))$("fundingPoolStatus").textContent=plan.poolStatus==="VALUE"?"READY · "+fmt(plan.strategyPool):plan.poolStatus;
  if($("fundingNewCapital"))$("fundingNewCapital").textContent=plan.newCapitalStatus==="VALUE"?fmt(plan.newCapital):plan.newCapitalStatus;
  if($("qqqFundingCurrent"))$("qqqFundingCurrent").textContent=Number.isFinite(plan.qqqValue)?fmt(plan.qqqValue):"—";
  if($("qqqFundingPct"))$("qqqFundingPct").textContent=Number.isFinite(plan.qqqCurrentPct)?pct(plan.qqqCurrentPct):"—";
  if($("qqqFundingTarget"))$("qqqFundingTarget").textContent=Number.isFinite(plan.qqqTargetValue)?fmt(plan.qqqTargetValue)+" · "+fmt(plan.qqqTargetPct,1)+"% NAV":"—";
  if($("qqqFundingGap"))$("qqqFundingGap").textContent=Number.isFinite(plan.qqqGap)?fmt(plan.qqqGap):"—";
  if($("qqqFundingSuggestion"))$("qqqFundingSuggestion").textContent=Number.isFinite(plan.suggestedQqqFromNewCapital)?fmt(plan.suggestedQqqFromNewCapital):"—";
  if($("fundingReserve"))$("fundingReserve").textContent=Number.isFinite(plan.reserveAfterQqq)?fmt(plan.reserveAfterQqq):"—";
  if($("shortCallFunding"))$("shortCallFunding").textContent=plan.shortCall;
  return plan;
}

function escapeHtml(v){
  return String(v??"").replace(/[&<>"]/g,ch=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;"}[ch]));
}
function renderStrategyBridge(d,e,book,funding){
  const bridge=E.strategyActionBridge({
    d,e,book,funding,
    currentOptionLegs:optionLegs(),
    journalRows
  });
  if($("bridgeAction")){
    $("bridgeAction").textContent=bridge.actionClass;
    $("bridgeAction").className="tag "+(
      bridge.actionClass==="DEFEND"||bridge.actionClass==="PAUSE"||bridge.actionClass==="TRIM"?"retired":
      bridge.actionClass==="BUILD"||bridge.actionClass==="REBALANCE"?"active":"research"
    );
  }
  if($("bridgeInstruction"))$("bridgeInstruction").textContent=bridge.operatorInstruction;
  if($("bridgeReduce"))$("bridgeReduce").textContent=(bridge.reduceLines&&bridge.reduceLines.length)
    ?(bridge.actionClass==="TRIM"?"TRIM（只減、唔加）：":"REDUCE：")+bridge.reduceLines.join(" · ")
    :"";
  if($("bridgeStrategy"))$("bridgeStrategy").textContent=bridge.strategyName+" · "+bridge.regime;
  if($("bridgePosition"))$("bridgePosition").textContent=
    "QQQ "+fmt(bridge.current.qqqShares)+" shares · VXX short "+pct(bridge.current.vxxPct)+
    " NAV · QQQ far "+fmt(bridge.current.qqqCalls,0)+" · VXX call "+fmt(bridge.current.vxxCalls,0);
  if($("bridgeTarget"))$("bridgeTarget").textContent=
    "QQQ "+fmt(bridge.target.qqqShares)+" shares · VXX short "+pct(bridge.target.vxxPct)+
    " · QQQ far "+fmt(bridge.target.qqqCalls,0)+" · VXX call "+fmt(bridge.target.vxxCalls,0);
  if($("bridgeGap"))$("bridgeGap").textContent=Number.isFinite(bridge.qqqGap)
    ?fmt(bridge.qqqGap)+" to "+fmt(bridge.qqqCoreTargetPct,1)+"% core target":"—";
  if($("bridgeFunding"))$("bridgeFunding").textContent=
    bridge.funding.route+" · "+bridge.funding.status+
    (Number.isFinite(bridge.funding.newCapital)? " · new "+fmt(bridge.funding.newCapital):"");
  if($("bridgeNext"))$("bridgeNext").textContent=
    bridge.nextStep==="ROLL_OPTION"?"ROLL OPTION NOW":
    (bridge.transition.length?bridge.transition[0].label:"WATCH NEXT TRANSITION");
  if($("bridgeJournal"))$("bridgeJournal").textContent=
    bridge.journal.eventId
      ?("Last "+bridge.journal.eventId+" · "+(bridge.journal.changed?"CHANGED":"ALIGNED")+" · "+bridge.journal.conflict)
      :"No journal baseline yet";
  if($("bridgeLoop")){
    $("bridgeLoop").innerHTML=bridge.closedLoop.map(x=>
      "<span class='bridge-loop-step'><b>"+escapeHtml(x.stage)+"</b><small>"+escapeHtml(x.status)+"</small></span>"
    ).join("");
  }
  return bridge;
}
function optionLegs(){
  const qqqCalls=$("qqqCalls")?$("qqqCalls").value:"";
  const vxxCalls=$("vxxCalls")?$("vxxCalls").value:"";
  return E.currentOptionLegs({
    qqq:{
      qty:qqqCalls,
      shortStrike:$("qqqShortStrike")?$("qqqShortStrike").value:"",
      longStrike:$("qqqLongStrike")?$("qqqLongStrike").value:"",
      expiry:$("qqqExpiry")?$("qqqExpiry").value:"",
      dte:$("qqqDte")?$("qqqDte").value:"",
      delta:$("qqqDelta")?$("qqqDelta").value:"",
      entryCredit:$("qqqEntryCredit")?$("qqqEntryCredit").value:""
    },
    vxx:{
      qty:vxxCalls,
      shortStrike:$("vxxShortStrike")?$("vxxShortStrike").value:"",
      longStrike:$("vxxLongStrike")?$("vxxLongStrike").value:"",
      expiry:$("vxxExpiry")?$("vxxExpiry").value:"",
      dte:$("vxxDte")?$("vxxDte").value:"",
      delta:$("vxxDelta")?$("vxxDelta").value:"",
      entryCredit:$("vxxEntryCredit")?$("vxxEntryCredit").value:""
    }
  });
}
function renderLegIdentity(){
  const legs=optionLegs();
  const paint=(id,leg)=>{
    const el=$(id); if(!el) return;
    el.textContent=leg.status+(leg.rollReady?" · ROLL-READY":"");
    el.className="tag"+(leg.status==="READY"?" active":leg.status==="INVALID"?" retired":leg.status==="INCOMPLETE"?" research":"");
  };
  paint("qqqLegStatus",legs.qqq);
  paint("vxxLegStatus",legs.vxx);
  if($("legIdentityMeta")){
    const w=x=>Number.isFinite(x.width)?(" width "+x.width):"";
    $("legIdentityMeta").textContent="QQQ "+legs.qqq.status+w(legs.qqq)+" · VXX "+legs.vxx.status+w(legs.vxx)+" · ROLL reads Current Leg (Candidate stays separate; Build uses call counts)";
  }
}

function inputRow(){
  if(!live) return {qqq:null,vxx:null,vix:null,m1:null,m2:null,s:null,termAsOf:null,spotAsOf:null,term_source:null,provenance:{},today:new Date().toISOString().slice(0,10)};
  return {
    ...live,
    s:Number.isFinite(Number(live.term_slope))?Number(live.term_slope):E.term(Number(live.m1),Number(live.m2)),
    termAsOf:live.term_asof,
    spotAsOf:live.spot_asof,
    term_source:live.term_source,
    provenance:live.provenance||{},
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
  else if(book.inputBlocked){active="flowBuild";tone="warn";next="NEXT: 第一步 — 填齊持倉（Operator Memory，留空 ≠ 0）";}
  else if(e.action==="BUY" && !hasPosition){active="flowBuild";next="NEXT: REVIEW TARGET → BUILD POSITION";}
  else if(e.action==="BUY"){active="flowBuild";next="NEXT: EXECUTE DELTAS → JOURNAL";}
  else if(e.action==="REDUCE"){active="flowDecision";tone="danger";next="NEXT: REDUCE SELLER RISK → JOURNAL";}
  else if(e.action==="HOLD"&&Object.values(book.deltas||{}).some(v=>Number(v)<-1e-9)){active="flowBuild";tone="warn";next="NEXT: TRIM 超出目標部分（只減唔加）→ JOURNAL";}
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
    const opt={
      qqqDte:$("qqqDte")?$("qqqDte").value:"",qqqDelta:$("qqqDelta")?$("qqqDelta").value:"",
      vxxDte:$("vxxDte")?$("vxxDte").value:"",vxxDelta:$("vxxDelta")?$("vxxDelta").value:"",
      qqqCalls:$("qqqCalls")?$("qqqCalls").value:"",vxxCalls:$("vxxCalls")?$("vxxCalls").value:"",
      forceFlat:!!($("forceFlat")&&$("forceFlat").checked),currentOptionLegs:optionLegs()
    };
    const fires=E.triggers(d,e,opt).filter(x=>x.fire).length;
    $("watchSummary").textContent=fires?fires+" TRIGGER"+(fires===1?"":"S"):"WATCHING";
  }
}

function renderOperatorSummary(d,e,book){
  const legs=optionLegs();
  // Pass raw strings (blank ≠ 0). ROLL prefers currentOptionLegs; manual DTE/Δ are fallback only.
  const opt={
    qqqDte:$("qqqDte")?$("qqqDte").value:"",qqqDelta:$("qqqDelta")?$("qqqDelta").value:"",
    vxxDte:$("vxxDte")?$("vxxDte").value:"",vxxDelta:$("vxxDelta")?$("vxxDelta").value:"",
    currentOptionLegs:legs,
    forceFlat:!!($("forceFlat")&&$("forceFlat").checked),
    today:d.today||null,
    nav:effectiveNav()
  };
  const s=E.operatorSummary(d,e,book,candidates,opt);
  if($("operatorMode"))$("operatorMode").textContent=s.mode;
  if($("operatorAction"))$("operatorAction").textContent=e.blocked?"HOLD / BLOCKED":e.action;
  if($("operatorPlan"))$("operatorPlan").innerHTML=s.plan.map(x=>"<div class='operator-line'>"+escapeHtml(x)+"</div>").join("");
  if($("operatorThresholds"))$("operatorThresholds").innerHTML=s.thresholds.length?s.thresholds.map((x,i)=>"<div class='operator-line'><b>"+escapeHtml(x.label)+"</b><span>"+escapeHtml(x.text)+"</span></div>").join(""):"<div class='operator-line'>等待有效市場數據</div>";
  if($("operatorRolls"))$("operatorRolls").innerHTML=[s.rolls.qqq,s.rolls.vxx].map(x=>"<div class='operator-line'><b>"+escapeHtml(x.label)+"</b><span>"+escapeHtml(x.text)+"</span></div>").join("");
  if($("operatorBaseline"))$("operatorBaseline").textContent="Baseline · QQQ core "+E.POLICY.corePct+"% NAV · VXX short "+E.POLICY.vxxNormalPct+"% (VIX ≥ "+E.POLICY.vixHigh+" → "+E.POLICY.vxxHighPct+"%) · QQQ far-call budget "+E.POLICY.qqqCallBudgetPct+"% · VXX call budget "+E.POLICY.vxxCallBudgetPct+"%";
}
function render(d,e,book){
  const funding=renderFundingPlan(d,e,book);
  renderStrategyBridge(d,e,book,funding);
  renderOperatorSummary(d,e,book);
  renderLegIdentity();
  renderFlow(d,e,book);
  $("qqq").textContent=fmt(d.qqq);
  $("vxx").textContent=fmt(d.vxx);
  $("vix").textContent=fmt(d.vix);
  $("term").textContent=pct(d.s);
  $("m1").textContent="M1 "+fmt(d.m1);
  $("m2").textContent="M2 "+fmt(d.m2);
  $("termMeta").textContent=(live?.m1_code||live?.m1?.symbol||"—")+" → "+(live?.m2_code||live?.m2?.symbol||"—")+" · "+(live?.term_source||"BLOCKED");
  $("sourceMeta").textContent=(live?.source_chain||[]).join(" → ")||"NO SOURCE";
  // F2: term as-of = Cboe payload date (NY); fetched = when this terminal pulled it (display only).
  const fetchedAt=live&&live.term_fetched_at?new Date(live.term_fetched_at):null;
  const fetchedTxt=fetchedAt&&Number.isFinite(fetchedAt.getTime())?" · term fetched "+fetchedAt.toLocaleString():"";
  const undated=live&&live.term_asof_status&&live.term_asof_status!=="PAYLOAD_LAST_UPDATE"?" · term date "+live.term_asof_status:"";
  $("asof").textContent="term as-of "+(d.termAsOf||"—")+" · spot as-of "+(d.spotAsOf||"—")+fetchedTxt+undated;
  $("action").textContent=e.blocked?"HOLD / BLOCKED":e.action;
  $("reason").textContent=e.reason;
  $("stateBadge").textContent=e.state;
  $("dataBadge").textContent=e.health.label;
  const mixedSrc=e.health.sourceMix==="MIXED_SOURCE";
  $("dataBadge").className="badge "+(e.health.status==="FRESH"&&!mixedSrc?"ok":e.blocked?"block":"warn");
  if($("cadenceBadge")){
    if(mixedSrc||(e.health.badges&&e.health.badges.length)){
      $("cadenceBadge").style.display="";
      $("cadenceBadge").textContent=(e.health.badges&&e.health.badges.length)?e.health.badges.join(" · "):(mixedSrc?"MIXED-SOURCE":"—");
      $("cadenceBadge").className="badge warn";
    }else{
      $("cadenceBadge").style.display="none";
    }
  }
  if($("vxxExposureMeta")){
    const labels=E.exposureLabels();
    const impl=E.impliedVxxShares(effectiveNav(),book.current.vxxPct,d.vxx);
    $("vxxExposureMeta").textContent=labels.vxxShort+" · "+labels.vxxCallSpreads+" = "+labels.vxxCallUnit+(Number.isFinite(impl)?" · implied ≈ "+fmt(impl,1)+" VXX shares":"");
  }
  $("stateBadge").className="badge "+(e.state==="CARRY"?"ok":e.state==="SHOCK"||e.state==="PRE-SHOCK"?"block":"warn");
  $("monitorTag").textContent=e.blocked?"NO ACTION":e.gate;
  if($("qqqSize")) $("qqqSize").textContent=book.sizing?.qqqCalls?.status==="READY"?"READY · "+fmt(book.sizing.qqqCalls.quantity,0)+" spreads":"PENDING";
  if($("vxxSize")) $("vxxSize").textContent=book.sizing?.vxxCalls?.status==="READY"?"READY · "+fmt(book.sizing.vxxCalls.quantity,0)+" spreads":"PENDING";
  if($("qqqCandidate")) $("qqqCandidate").textContent=candidates.qqq?candidateText(candidates.qqq):"No QQQ candidate";
  if($("vxxCandidate")) $("vxxCandidate").textContent=candidates.vxx?candidateText(candidates.vxx):"No VXX candidate";
  if($("candidateSource")) $("candidateSource").textContent=[candidates.qqq?.source,candidates.vxx?.source].filter(Boolean).join(" / ")||"NONE";

  const XL=E.exposureLabels();
  const rows=[
    ["QQQ CORE",book.current.qqqShares,book.target.qqqShares,book.deltas.qqqShares,"shares"],
    ["VXX SHORT EXPOSURE",book.current.vxxPct,book.target.vxxPct,book.deltas.vxxPct,XL.vxxShortUnit],
    ["QQQ FAR CALL SPREADS",book.current.qqqCalls,book.target.qqqCalls,book.deltas.qqqCalls,XL.qqqCallUnit],
    ["VXX CALL SPREADS",book.current.vxxCalls,book.target.vxxCalls,book.deltas.vxxCalls,XL.vxxCallUnit],
  ];
  $("ledgerRows").innerHTML=rows.map(r=>{
    const kind=Math.abs(r[3])<1e-9?"HOLD":r[3]>0?"ADD":"REDUCE";
    return '<div class="ledger-row"><span>'+r[0]+'</span><span>'+fmt(r[1])+'</span><span>'+fmt(r[2])+'</span><span class="'+kind+'">'+kind+" "+(Math.abs(r[3])<1e-9?"":(r[3]>0?"+":"")+fmt(r[3])+" "+r[4])+'</span></div>';
  }).join("");

  const acts=E.actionRows(book).filter(x=>Math.abs(x.diff)>1e-9);
  $("queue").innerHTML=(e.blocked
    ? '<div class="queue-item HOLD"><b>DATA GATE</b><span>BLOCKED · CURRENT = TARGET</span></div>'
    : book.inputBlocked
      ? '<div class="queue-item HOLD"><b>NEEDS INPUT</b><span>'+escapeHtml(E.inputGapText(book.inputStatus)||"第一步未填齊")+' · 留空 ≠ 0</span></div>'
    : acts.length
      ? acts.map(x=>'<div class="queue-item '+x.kind+'"><b>'+x.key+'</b><span>'+x.kind+' · '+fmt(x.diff)+'</span></div>').join("")
      : '<div class="queue-item HOLD"><b>NO POSITION CHANGE</b><span>WAIT / HOLD</span></div>'
  );

  const opts={
    qqqDte:$("qqqDte")?$("qqqDte").value:"",
    qqqDelta:$("qqqDelta")?$("qqqDelta").value:"",
    vxxDte:$("vxxDte")?$("vxxDte").value:"",
    vxxDelta:$("vxxDelta")?$("vxxDelta").value:"",
    qqqCalls:$("qqqCalls")?$("qqqCalls").value:"",
    vxxCalls:$("vxxCalls")?$("vxxCalls").value:"",
    forceFlat:!!($("forceFlat")&&$("forceFlat").checked),
    currentOptionLegs:optionLegs()
  };
  const tr=E.triggers(d,e,opts);
  $("triggerRows").innerHTML=tr.map(x=>'<div class="trigger '+(x.fire?"fire":"")+'"><span><b>'+x.label+'</b><small> '+x.priority+'</small></span><span>'+x.value+'</span><strong>'+(x.fire?"TRIGGER":x.mode==="NO_POSITION"?"OFF":x.mode==="NEEDS_POSITION_DATA"?"INCOMPLETE":x.mode==="WATCH"?"WATCH":"WATCH")+'</strong></div>').join("");

  $("prov").innerHTML=[
    ["QQQ/VXX/VIX",(live?.provenance?Object.entries(live.provenance).filter(([k])=>["qqq","vxx","vix"].includes(k)).map(([,v])=>v).join(" / "):"—"),"OBSERVED"],
    ["VX M1",live?.m1_code||"—",live?.term_source?"OBSERVED":"BLOCKED"],
    ["VX M2",live?.m2_code||"—",live?.term_source?"OBSERVED":"BLOCKED"],
    ["S_t","(M2-M1)/M1","DERIVED"],
    ["Target","frozen policy + ledger","DERIVED"]
  ].map(r=>'<div class="prov-row"><span>'+escapeHtml(r[0])+' · '+escapeHtml(r[1])+'</span><span class="tag '+escapeHtml(r[2].toLowerCase())+'">'+escapeHtml(r[2])+'</span></div>').join("");
}

function candidateText(c){
  if(!c) return "—";
  const credit=Number.isFinite(Number(c.credit))?Number(c.credit).toFixed(2):"—";
  return "short "+fmt(c.shortStrike)+" / long "+fmt(c.longStrike)+" · DTE "+fmt(c.dte,0)+" · Δ "+fmt(c.delta,2)+" · credit "+credit+" · "+(c.deltaSource||"ESTIMATE");
}

function applyCandidate(sym,c){
  // Candidate = next buy only. Do not write into Current Option Leg Watch fields.
  candidates[sym]=c;
  const d=inputRow(),e=E.derive(d),book=E.targetLedger(d,e,ledger(),candidates);
  render(d,e,book);
}

async function loadCandidate(sym){
  if(!live || !Number.isFinite(Number(live[sym]))) return;
  try{
    const r=await fetch("/api/options?symbol="+encodeURIComponent(sym.toUpperCase())+"&targetDte="+E.POLICY.optionTargetDte,{cache:"no-store"});
    const j=await r.json();
    if(!r.ok || !j.ok){
      optionsStatus=j.status||"OPTIONS_SOURCE_DOWN";
      throw new Error(j.error||j.status||"option source unavailable");
    }
    optionsStatus=j.status||"LIVE";
    const c=E.candidateFromChain(j.calls,Number(live[sym]),0.10,E.POLICY.optionTargetDte);
    if(!c) throw new Error("no qualifying call spread candidate");
    c.apiExpiry=j.expiry||c.expiration;
    applyCandidate(sym,c);
  }catch(err){
    candidates[sym]=null;
    if(optionsStatus==null||optionsStatus==="LIVE") optionsStatus="OPTIONS_SOURCE_DOWN";
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
  const d=inputRow(), e=E.derive(d), led=ledger();
  const bookRaw=E.targetLedger(d,e,led,candidates);
  // Attach nav onto current for optional Journal→Memory restore (never invent from candidate).
  const book={...bookRaw,current:{...bookRaw.current,nav:led.nav}};
  const human=($("humanAction").value||"").trim().toUpperCase();
  const funding=renderFundingPlan(d,e,book);
  const currentLegs=optionLegs();
  const bridge=E.strategyActionBridge({
    d,e,book,funding,
    currentOptionLegs:currentLegs,
    journalRows
  });
  const rec=E.journalRecord({
    engine:e,
    book,
    humanAction:human||null,
    optionsStatus,
    candidates,
    currentOptionLegs:currentLegs,
    funding,
    actionBridge:bridge
  });
  const eventId="QHV3-"+Date.now();
  const payload={
    event_id:eventId,
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
    ...rec
  };
  const r=await fetch("/api/journal",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
  if(!r.ok) throw new Error("journal failed");
  $("humanAction").value="";
  // Auto-save Memory snapshot keyed by event_id (counts+legs from UI — not from candidate).
  saveMemorySnapshot(eventId);
  if($("memoryRestoreMeta")) $("memoryRestoreMeta").textContent="Memory snapshot saved · "+eventId;
  await loadJournal();
}

async function loadJournal(){
  const r=await fetch("/api/journal",{cache:"no-store"});
  const j=await r.json();
  journalRows=j.rows||[];
  $("journalCount").textContent=journalRows.length;
  $("journalRows").innerHTML=journalRows.slice().reverse().map(x=>{
    const s=x.snapshot||{};
    return '<div class="journal-row"><b>'+escapeHtml(String(x.journaled_at||"").slice(0,19).replace("T"," "))+'</b> · '+escapeHtml(x.engine_action||"—")+' · '+escapeHtml(x.state||"—")+' · M1/M2 '+fmt(s.m1)+'/'+fmt(s.m2)+' · '+escapeHtml(x.conflict||"NONE")+(x.action_bridge&&x.action_bridge.action_class?' · '+escapeHtml(x.action_bridge.action_class):'')+'</div>';
  }).join("") || '<div class="meta">No decisions journaled yet.</div>';
  renderChangeSinceJournal();
}

$("refreshBtn").addEventListener("click",refresh);
if($("findQQQ")) $("findQQQ").addEventListener("click",()=>loadCandidate("qqq"));
if($("findVXX")) $("findVXX").addEventListener("click",()=>loadCandidate("vxx"));
$("journalBtn").addEventListener("click",journalDecision);
if($("restoreMemoryBtn")) $("restoreMemoryBtn").addEventListener("click",()=>{
  restoreMemoryFromLastJournal();
});
MEMORY_FIELD_IDS.forEach(id=>{const el=$(id);if(el)el.addEventListener("input",()=>{if(live){const d=inputRow(),e=E.derive(d),book=E.targetLedger(d,e,ledger(),candidates);render(d,e,book)}else{ledger();}})});
if($("forceFlat")) $("forceFlat").addEventListener("change",()=>{if(live){const d=inputRow(),e=E.derive(d),book=E.targetLedger(d,e,ledger(),candidates);render(d,e,book)}});
// Prefer explicit button for Journal restore; auto-restore last Memory snapshot on load if present.
restoreMemorySnapshotOnLoad();
ledger();
refresh();
