const L = window.PortfolioLedgerV1;
const P = window.PortfolioPositionIdentityV1;
const R = window.PortfolioReconciliationV1;
let events = [];
let liveMarks = {};
let manualMarks = {};
let strategy = null;

const $ = (id) => document.getElementById(id);
const money = (v) => Number.isFinite(Number(v)) ? Number(v).toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2}) : "—";
const qty = (v) => Number.isFinite(Number(v)) ? Number(v).toLocaleString(undefined,{maximumFractionDigits:6}) : "—";
const signMoney = (v) => Number.isFinite(Number(v)) ? ((Number(v)>=0?"+":"") + money(v)) : "—";
const nowLocalInput = () => {
  const d = new Date();
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
  return d.toISOString().slice(0,16);
};

function mergedMarks(){
  return Object.assign({}, liveMarks, manualMarks);
}

function fillTimestampToIso(v){
  return v ? new Date(v).toISOString() : new Date().toISOString();
}

function prettyError(err){
  return err && err.message ? err.message : String(err);
}

function esc(value){
  return String(value ?? "").replace(/[&<>"']/g, ch => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"
  }[ch]));
}

function fmtSpreadUnits(v){
  return Number.isFinite(Number(v)) ? qty(v) : "—";
}

function renderSpreadIdentity(){
  const identity = P.build(events);
  const s = identity.summary;
  if($("identityStatus")){
    $("identityStatus").textContent = s.paired
      ? ("PAIRED · " + s.paired)
      : (s.optionFills ? ("IDENTIFIED · " + s.identifiedOptionFills) : "NO IDENTIFIED SPREADS");
    $("identityStatus").className = "status " + (s.paired ? "ok" : (s.optionFills ? "warn" : ""));
  }
  if(!$("spreadRows")) return;

  if(!identity.rows.length){
    $("spreadRows").innerHTML = s.unmappedOptionFills
      ? '<div class="hint">No explicit Spread ID yet. '+s.unmappedOptionFills+' option fill(s) remain unmapped.</div>'
      : '<div class="hint">No option fills with explicit spread identity.</div>';
    return;
  }

  $("spreadRows").innerHTML =
    '<div class="spread-summary"><span>PAIRED '+s.paired+'</span><span>INCOMPLETE '+s.incomplete+'</span><span>IMBALANCED '+s.imbalanced+'</span><span>MULTI-CONTRACT '+s.multiContract+'</span><span>UNMAPPED FILLS '+s.unmappedOptionFills+'</span></div>' +
    identity.rows.map(r=>{
      const longLeg = r.legs.LONG.map(x => esc(x.symbol)+" · "+qty(x.quantity)).join("<br>") || "—";
      const shortLeg = r.legs.SHORT.map(x => esc(x.symbol)+" · "+qty(x.quantity)).join("<br>") || "—";
      const cls = r.status === "PAIRED" ? "paired" : "warning";
      return '<div class="spread-row '+cls+'">' +
        '<span><small>SPREAD ID</small><b>'+esc(r.spreadId)+'</b><small>'+esc(r.strategyRole || "—")+'</small></span>' +
        '<span><small>LONG LEG</small><b>'+longLeg+'</b></span>' +
        '<span><small>SHORT LEG</small><b>'+shortLeg+'</b></span>' +
        '<span><small>UNITS</small><b>'+fmtSpreadUnits(r.units)+'</b></span>' +
        '<strong>'+esc(r.status)+'</strong>' +
      '</div>';
    }).join("");
}

async function loadStrategy(){
  try{
    const r=await fetch("/api/strategy-status?ts="+Date.now(),{cache:"no-store"});
    const j=await r.json();
    strategy=j;
    const connected=Boolean(j.available && j.connected);
    $("bridgeStatus").textContent=connected ? "CONNECTED · READ-ONLY" : "OFFLINE / NOT AVAILABLE";
    $("strategyBadge").textContent=connected ? "CONNECTED" : "OFFLINE";
    $("strategyBadge").className="badge "+(connected ? "ok" : "neutral");
    $("strategyState").textContent=connected ? ("V3 · "+(j.state||"—")) : (j.source==="V3_ENGINE_NOT_PRESENT" ? "V3 engine not present" : "V3 bridge not available");
    $("strategyAction").textContent=connected ? (j.action||"—") : "—";
    $("strategyMode").textContent=connected ? (j.state||"—") : "—";
    $("strategyGate").textContent=connected ? (j.gate||"—") : "—";
    $("strategyAsOf").textContent=connected ? (j.snapshot_asof||"—") : "—";
    $("strategyReason").textContent=connected
      ? (j.reason||"V3 recommendation received read-only.")
      : (j.error||"No V3 recommendation is fabricated when the bridge is unavailable.");
    const t=j.targets||null;
    $("strategyTargets").innerHTML=connected && t
      ? '<div><small>QQQ CORE</small><b>'+money(t.qqqCorePct)+'% NAV</b></div>'+
        '<div><small>VXX SHORT</small><b>'+money(t.vxxPct)+'% NAV</b></div>'+
        '<div><small>QQQ CALL BUDGET</small><b>'+money(t.qqqCallBudgetPct)+'%</b></div>'+
        '<div><small>VXX CALL BUDGET</small><b>'+money(t.vxxCallBudgetPct)+'%</b></div>'
      : "";
  }catch(err){
    strategy={ok:false,connected:false,available:false,source:"V3_BRIDGE_ERROR",error:prettyError(err)};
    $("bridgeStatus").textContent="OFFLINE / ERROR";
    $("strategyBadge").textContent="OFFLINE";
    $("strategyBadge").className="badge neutral";
    $("strategyState").textContent="V3 bridge error";
    $("strategyAction").textContent="—";
    $("strategyMode").textContent="—";
    $("strategyGate").textContent="—";
    $("strategyAsOf").textContent="—";
    $("strategyReason").textContent=prettyError(err);
    $("strategyTargets").innerHTML="";
  }
  renderReconciliation();
}


function renderReconciliation(){
  const snapshot = L.snapshot(events, mergedMarks());
  const result = R.reconcile(snapshot, strategy);
  $("reconStatus").textContent =
    result.status === "READY"
      ? ("READY · " + result.summary.comparable + " COMPARABLE")
      : "WAITING FOR V3";
  $("reconStatus").className = "status " + (result.status === "READY" ? "ok" : "warn");
  $("reconReason").textContent = result.reason;
  if(result.status !== "READY"){
    $("reconSummary").innerHTML="";
    $("reconRows").innerHTML='<div class="hint">No V3 target available. No comparison fabricated.</div>';
    return;
  }

  $("reconSummary").innerHTML =
    '<div><small>ALIGNED</small><b>'+result.summary.aligned+'</b></div>'+
    '<div><small>UNDERWEIGHT</small><b>'+result.summary.underweight+'</b></div>'+
    '<div><small>OVERWEIGHT</small><b>'+result.summary.overweight+'</b></div>'+
    '<div><small>UNMAPPED</small><b>'+result.summary.unmapped+'</b></div>';

  $("reconRows").innerHTML = result.rows.map(r=>{
    const cls = r.action === "ALIGNED" ? "aligned" :
      r.action === "UNDERWEIGHT" ? "underweight" :
      r.action === "OVERWEIGHT" ? "overweight" : "unmapped";
    return '<div class="recon-row '+cls+'">'+
      '<span><b>'+r.label+'</b><small>'+r.source+'</small></span>'+
      '<span><small>ACTUAL</small><b>'+fmtRecon(r.actual,r.unit)+'</b></span>'+
      '<span><small>TARGET</small><b>'+fmtRecon(r.target,r.unit)+'</b></span>'+
      '<span><small>GAP</small><b>'+fmtRecon(r.gap,r.unit)+'</b></span>'+
      '<strong>'+r.action+'</strong>'+
    '</div>';
  }).join("");
}

function fmtRecon(value, unit){
  if(!Number.isFinite(Number(value))) return "—";
  return Number(value).toFixed(unit === "% NAV" ? 2 : 0) + (unit === "% NAV" ? "%" : " "+unit);
}

async function loadEvents(){
  const r = await fetch("/api/events?ts=" + Date.now(), {cache:"no-store"});
  const j = await r.json();
  if(!r.ok || !j.ok) throw new Error(j.error || "events unavailable");
  events = Array.isArray(j.events) ? j.events : [];
  $("eventCount").textContent = String(events.length);
  $("ledgerStatus").textContent = "READY";
}

async function fetchMarks(){
  const symbols = [...new Set(events.filter(e => e.type === "FILL").map(e => e.symbol))];
  if(!symbols.length){ liveMarks = {}; renderAll(); return; }
  const r = await fetch("/api/marks?symbols=" + encodeURIComponent(symbols.join(",")) + "&ts=" + Date.now(), {cache:"no-store"});
  const j = await r.json();
  liveMarks = {};
  (j.rows || []).forEach(x => { if(Number.isFinite(Number(x.price))) liveMarks[x.symbol] = Number(x.price); });
  $("markStatus").textContent = (j.source || "NONE") + " · " + (j.asOf || "—");
  $("coverage").textContent = (Object.keys(liveMarks).length) + "/" + symbols.length + " live marks";
  renderAll();
}

function addEventToServer(event){
  return fetch("/api/events", {
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify(event)
  }).then(async r => {
    const j=await r.json();
    if(!r.ok || !j.ok) throw new Error(j.error || "event write failed");
    return j;
  });
}

function renderPositions(){
  const snap = L.snapshot(events, mergedMarks());
  const markedComplete = snap.coverage.allMarksPresent;
  $("equity").textContent = markedComplete ? money(snap.equity) : "PARTIAL · " + money(snap.equity);
  $("netPnl").textContent = markedComplete ? signMoney(snap.netPnl) : "PARTIAL · " + signMoney(snap.netPnl);
  $("realized").textContent = signMoney(snap.realizedPnl);
  $("unrealized").textContent = markedComplete ? signMoney(snap.unrealizedPnl) : "PARTIAL · " + signMoney(snap.unrealizedPnl);
  $("cash").textContent = money(snap.cash);
  $("fees").textContent = money(snap.totalFees);
  $("netPnl").className = snap.netPnl >= 0 ? "positive" : "negative";
  $("coverage").textContent = snap.coverage.totalSymbols === 0
    ? "NO POSITIONS"
    : (snap.coverage.markedSymbols + "/" + snap.coverage.totalSymbols + " live marks" + (markedComplete ? "" : " · NAV/P&L PARTIAL"));
  $("coverage").className = "status " + (markedComplete ? "ok" : "warn");
  $("positions").innerHTML = snap.positions.length
    ? '<table class="table"><thead><tr><th>Position</th><th>Qty</th><th>Avg open</th><th>Mark</th><th>Market value</th><th>Unrealized</th><th>Realized</th></tr></thead><tbody>' +
      snap.positions.map(p => {
        const direction = p.quantity >= 0 ? "LONG" : "SHORT";
        return '<tr><td><b>'+p.symbol+'</b><br><span class="'+(p.quantity>=0?"long":"short")+'">'+direction+' · '+p.assetType+'</span></td>' +
          '<td>'+qty(p.quantity)+'</td><td>'+money(p.averageOpenPrice)+'</td><td>'+money(p.mark)+'</td>' +
          '<td>'+money(p.marketValue)+'</td><td class="'+(Number(p.unrealizedPnl)>=0?"positive":"negative")+'">'+signMoney(p.unrealizedPnl)+'</td>' +
          '<td class="'+(Number(p.realizedPnl)>=0?"positive":"negative")+'">'+signMoney(p.realizedPnl)+'</td></tr>';
      }).join("") + '</tbody></table>'
    : '<div class="hint">No open positions. Add a fill or import your transaction history.</div>';

  $("markRows").innerHTML = snap.positions.map(p =>
    '<div class="mark-row"><b>'+p.symbol+'</b><span>live '+money(liveMarks[p.symbol])+' · manual '+money(manualMarks[p.symbol])+'</span></div>'
  ).join("") || '<div class="hint">No symbols to mark yet.</div>';
}

function renderEvents(){
  $("events").innerHTML = events.slice().reverse().map(e => {
    if(e.type === "CASHFLOW"){
      return '<div class="event"><span>'+e.timestamp.slice(0,19).replace("T"," ")+'</span><b>CASHFLOW</b><span>'+money(e.amount)+'</span><span class="muted">external</span><span>'+ (e.note||"") +'</span></div>';
    }
    return '<div class="event"><span>'+e.timestamp.slice(0,19).replace("T"," ")+'</span><b>'+e.side+'</b><span>'+e.symbol+'</span><span>'+qty(e.quantity)+' × '+money(e.price)+'</span><span>'+money(e.fees)+' fees</span></div>';
  }).join("") || '<div class="hint">No recorded events.</div>';
}

function renderAll(){
  try{
    renderPositions();
    renderSpreadIdentity();
    renderEvents();
    renderReconciliation();
  }catch(err){
    $("ledgerStatus").textContent = "ERROR";
    $("positions").innerHTML = '<div class="danger-text">'+prettyError(err)+'</div>';
  }
}

function manualMarksFromForm(){
  const raw = $("manualMarks").value.trim();
  if(!raw){ manualMarks={}; return; }
  const x = JSON.parse(raw);
  if(!x || typeof x !== "object" || Array.isArray(x)) throw new Error("manual marks must be a JSON object");
  manualMarks={};
  Object.keys(x).forEach(k => {
    const n=Number(x[k]);
    if(Number.isFinite(n)) manualMarks[String(k).toUpperCase()]=n;
  });
}

function setDefaultTimes(){
  $("fillTimestamp").value = nowLocalInput();
  $("cashTimestamp").value = nowLocalInput();
  const now = new Date();
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
  $("periodEnd").value = now.toISOString().slice(0,16);
  now.setDate(now.getDate()-1);
  $("periodStart").value = now.toISOString().slice(0,16);
}

$("fillAsset").addEventListener("change", syncIdentityFields);

function syncIdentityFields(){
  const isOption = $("fillAsset").value === "OPTION";
  ["fillCampaignId","fillSpreadId","fillLegRole","fillStrategyRole"].forEach(id => {
    $(id).disabled = !isOption;
  });
  if(!isOption){
    $("fillCampaignId").value = "";
    $("fillSpreadId").value = "";
    $("fillLegRole").value = "";
    $("fillStrategyRole").value = "";
  }
}

syncIdentityFields();

$("fillForm").addEventListener("submit", async (ev)=>{
  ev.preventDefault();
  try{
    const asset=$("fillAsset").value;
    const event={
      type:"FILL",
      id:"F-"+Date.now(),
      timestamp:fillTimestampToIso($("fillTimestamp").value),
      symbol:$("fillSymbol").value.trim().toUpperCase(),
      assetType:asset,
      side:$("fillSide").value,
      quantity:Number($("fillQty").value),
      price:Number($("fillPrice").value),
      multiplier:$("fillMultiplier").value==="" ? undefined : Number($("fillMultiplier").value),
      fees:Number($("fillFees").value||0),
      note:$("fillNote").value.trim()
    };
    if(asset === "OPTION"){
      const campaignId=$("fillCampaignId").value.trim();
      const spreadId=$("fillSpreadId").value.trim();
      const legRole=$("fillLegRole").value;
      const strategyRole=$("fillStrategyRole").value.trim();
      if(campaignId || spreadId || legRole || strategyRole){
        event.positionIdentity={};
        if(campaignId) event.positionIdentity.campaignId=campaignId;
        if(spreadId) event.positionIdentity.spreadId=spreadId;
        if(legRole) event.positionIdentity.legRole=legRole;
        if(strategyRole) event.positionIdentity.strategyRole=strategyRole;
      }
    }
    L.normalizeEvent(event);
    await addEventToServer(event);
    await loadEvents(); await fetchMarks();
    $("fillForm").reset(); $("fillFees").value="0"; $("fillTimestamp").value=nowLocalInput();
  }catch(err){ alert(prettyError(err)); }
});

$("cashForm").addEventListener("submit", async (ev)=>{
  ev.preventDefault();
  try{
    const event={
      type:"CASHFLOW",
      id:"CF-"+Date.now(),
      timestamp:fillTimestampToIso($("cashTimestamp").value),
      amount:Number($("cashAmount").value),
      note:$("cashNote").value.trim()
    };
    L.normalizeEvent(event);
    await addEventToServer(event);
    await loadEvents(); renderAll();
    $("cashForm").reset(); $("cashTimestamp").value=nowLocalInput();
  }catch(err){ alert(prettyError(err)); }
});

$("markApplyBtn").addEventListener("click",()=>{
  try{ manualMarksFromForm(); renderAll(); }catch(err){ alert(prettyError(err)); }
});

$("refreshBtn").addEventListener("click", async ()=>{
  $("markStatus").textContent="REFRESHING";
  try{ await loadEvents(); await fetchMarks(); await loadStrategy(); }
  catch(err){ $("markStatus").textContent="ERROR"; alert(prettyError(err)); }
});

$("periodBtn").addEventListener("click",()=>{
  try{
    manualMarksFromForm();
    const startRaw=$("periodStart").value, endRaw=$("periodEnd").value;
    const startMarksRaw=$("startMarks").value.trim();
    const startMarks=startMarksRaw?JSON.parse(startMarksRaw):{};
    const result=L.periodMetrics(events, new Date(startRaw).toISOString(), new Date(endRaw).toISOString(), startMarks, mergedMarks());
    $("periodBadge").textContent=result.complete?"COMPLETE":"INCOMPLETE";
    $("periodBadge").className="status "+(result.complete?"ok":"warn");
    $("periodResult").innerHTML =
      '<div><small>START EQUITY</small><strong>'+money(result.startEquity)+'</strong></div>' +
      '<div><small>END EQUITY</small><strong>'+money(result.endEquity)+'</strong></div>' +
      '<div><small>NET EXTERNAL CASHFLOW</small><strong>'+money(result.periodExternalCashFlow)+'</strong></div>' +
      '<div><small>PERIOD P&L / RETURN</small><strong>'+signMoney(result.pnl)+' / '+(result.returnPct===null?"—":result.returnPct.toFixed(2)+"%")+'</strong></div>';
    if(!result.complete) $("periodResult").insertAdjacentHTML("afterbegin",'<div><small>REASON</small><strong>Missing start/end mark</strong></div>');
  }catch(err){ alert(prettyError(err)); }
});

$("exportBtn").addEventListener("click",()=>{
  const blob=new Blob([JSON.stringify(L.exportBundle(events),null,2)],{type:"application/json"});
  const a=document.createElement("a"); a.href=URL.createObjectURL(blob); a.download="qqq-hybrid-portfolio-ledger.json"; a.click(); URL.revokeObjectURL(a.href);
});

$("importFile").addEventListener("change", async (ev)=>{
  const file=ev.target.files && ev.target.files[0];
  if(!file) return;
  try{
    const parsed=JSON.parse(await file.text());
    const incoming=Array.isArray(parsed)?parsed:parsed.events;
    if(!Array.isArray(incoming)) throw new Error("JSON must contain an events array");
    const result=await fetch("/api/import",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({events:incoming})});
    const j=await result.json();
    if(!result.ok || !j.ok) throw new Error(j.error || "import failed");
    await loadEvents(); await fetchMarks();
    alert("Imported "+j.added+" new events; "+j.duplicates+" duplicates ignored.");
  }catch(err){ alert(prettyError(err)); }
  ev.target.value="";
});

setDefaultTimes();
loadEvents().then(fetchMarks).then(loadStrategy).catch(err=>{ $("ledgerStatus").textContent="ERROR"; alert(prettyError(err)); });
