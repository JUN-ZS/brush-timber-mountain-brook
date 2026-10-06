
const E=HybridEngineV3;
const $=id=>document.getElementById(id);
let live=null;

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

function render(d,e,book){
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
  $("queue").innerHTML=(e.blocked
    ? '<div class="queue-item HOLD"><b>DATA GATE</b><span>BLOCKED · CURRENT = TARGET</span></div>'
    : acts.length
      ? acts.map(x=>'<div class="queue-item '+x.kind+'"><b>'+x.key+'</b><span>'+x.kind+' · '+fmt(x.diff)+'</span></div>').join("")
      : '<div class="queue-item HOLD"><b>NO POSITION CHANGE</b><span>WAIT / HOLD</span></div>'
  );

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
}

async function refresh(){
  $("refreshBtn").disabled=true;
  try{
    const res=await fetch("/api/snapshot?ts="+Date.now(),{cache:"no-store"});
    live=await res.json();
    const d=inputRow();
    const e=E.derive(d);
    const book=E.targetLedger(d,e,ledger());
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
  const d=inputRow(), e=E.derive(d), book=E.targetLedger(d,e,ledger());
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
  $("journalCount").textContent=j.rows.length;
  $("journalRows").innerHTML=j.rows.slice().reverse().map(x=>{
    const s=x.snapshot||{};
    return '<div class="journal-row"><b>'+((x.journaled_at||"").slice(0,19).replace("T"," "))+'</b> · '+(x.engine_action||"—")+' · '+(x.state||"—")+' · M1/M2 '+fmt(s.m1)+'/'+fmt(s.m2)+' · '+(x.conflict||"NONE")+'</div>';
  }).join("") || '<div class="meta">No decisions journaled yet.</div>';
}

$("refreshBtn").addEventListener("click",refresh);
$("journalBtn").addEventListener("click",journalDecision);
["nav","qqqShares","vxxPct","qqqCalls","vxxCalls","qqqDte","qqqDelta","vxxDte","vxxDelta"].forEach(id=>$(id).addEventListener("input",()=>{if(live){const d=inputRow(),e=E.derive(d),book=E.targetLedger(d,e,ledger());render(d,e,book)}}));
refresh();
