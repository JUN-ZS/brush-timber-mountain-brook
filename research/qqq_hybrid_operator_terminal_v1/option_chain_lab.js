(function(root,factory){"use strict";var api=factory();if(typeof module!=="undefined"&&module.exports)module.exports=api;if(root&&root.document)api.init(root,root.document);})(typeof window!=="undefined"?window:null,function(){"use strict";
var SAMPLE={
expiration:"2026-11-20",
source:"USER_UPLOADED_SCREENSHOT",
originalFile:"未命名.png",
uploadedOn:"2026-10-08",
observationDate:null,
observationTimeVerified:false,
multiplier:100,
note:"Transcribed from the canonical screenshot fixture. Only QQQ CALL and VXX CALL are visible; QQQ PUT and VXX PUT are intentionally empty. Quote time and contract deliverables remain unverified.",
chains:{
QQQ_CALL:[
{strike:799,bid:3.16,ask:3.18,delta:0.1456},
{strike:805,bid:2.37,ask:2.40,delta:0.1161},
{strike:810,bid:1.87,ask:1.89,delta:0.0954}
],
QQQ_PUT:[],
VXX_CALL:[
{strike:21,bid:0.58,ask:0.72,delta:0.2698},
{strike:22,bid:0.49,ask:0.60,delta:0.2280},
{strike:23,bid:0.43,ask:0.51,delta:0.1963},
{strike:24,bid:0.24,ask:0.34,delta:0.1731},
{strike:25,bid:0.35,ask:0.40,delta:0.1532},
{strike:26,bid:0.24,ask:0.36,delta:0.1269}
],
VXX_PUT:[]
}};
function num(x){if(x===null||x===undefined||String(x).trim()==="")return null;var n=Number(String(x).replace(/,/g,""));return Number.isFinite(n)?n:null}
function money(n){return Number.isFinite(n)?"$"+n.toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2}):"—"}
function px(n){return Number.isFinite(n)?n.toFixed(2):"—"}
function esc(x){return String(x===null||x===undefined?"":x).replace(/[&<>"']/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]})}
function sorted(rows){return (rows||[]).map(r=>({strike:num(r.strike),bid:num(r.bid),ask:num(r.ask),delta:num(r.delta)})).filter(r=>r.strike!==null).sort((a,b)=>a.strike-b.strike)}
function quoteState(r){
if(r.bid===null||r.ask===null)return{ok:false,label:"缺雙邊報價",bad:true,spreadPctMid:null,band:"INVALID"};
if(r.bid<0||r.ask<0||r.bid>r.ask)return{ok:false,label:"倒掛／無效",bad:true,spreadPctMid:null,band:"INVALID"};
if(r.bid===0||r.ask===0)return{ok:false,label:"零價待核實",bad:true,spreadPctMid:null,band:"INVALID"};
var w=r.ask-r.bid,m=(r.ask+r.bid)/2,pct=m>0?w/m*100:null,band=pct<=10?"TIGHT":pct<=25?"MODERATE":"WIDE";
return{ok:true,label:band==="TIGHT"?"窄價差 ≤10% mid":band==="MODERATE"?"中等 10–25% mid":"偏闊 >25% mid",wide:band==="WIDE",spread:w,mid:m,spreadPctMid:pct,band:band};
}
function executionStress(width,credit,mult,budget){
return[0,0.025,0.05,0.10].map(function(extraPerLeg){
var stressedCredit=credit-2*extraPerLeg,viable=stressedCredit>0&&stressedCredit<width,maxLoss=viable?(width-stressedCredit)*mult:null;
return{extraSlippagePerLeg:extraPerLeg,creditPerShare:viable?stressedCredit:null,maxProfit:viable?stressedCredit*mult:null,maxLoss:maxLoss,maxQty:viable&&budget>0?Math.floor((budget+1e-9)/maxLoss):0,viable:viable,status:viable?"SCENARIO ONLY":"NO TRADE · NON-POSITIVE CREDIT"};
});
}
function calculateVerticals(key,rows,multiplier,budget,contractStatus){
var data=sorted(rows),mult=num(multiplier),budInput=num(budget),call=String(key).endsWith("_CALL"),valid=[],excluded=0,wide=0,totalPairs=data.length*(data.length-1)/2;
if(contractStatus==="ADJUSTED_TERMS_RECORDED")return{candidates:[],excluded:totalPairs,wide:0,totalPairs:totalPairs,validQuotes:data.filter(r=>quoteState(r).ok).length,error:"調整合約的交割單位／標的價格刻度尚未正規化；此 Lab 封鎖容量計算。"};
if(mult===null||mult<=0)return{candidates:[],excluded:totalPairs,wide:0,totalPairs:totalPairs,validQuotes:data.filter(r=>quoteState(r).ok).length,error:"合約乘數必須是有效正數；空白或 0 不可自動代入 100。"};
if(budInput===null||budInput<0)return{candidates:[],excluded:totalPairs,wide:0,totalPairs:totalPairs,validQuotes:data.filter(r=>quoteState(r).ok).length,error:"風險預算必須是有效的非負數；空白或負數不會自動代入預算。"};
var bud=budInput;
for(var i=0;i<data.length;i++)for(var j=i+1;j<data.length;j++){
var low=data[i],high=data[j],s=call?low:high,l=call?high:low,qs=quoteState(s),ql=quoteState(l);
if(!qs.ok||!ql.ok){excluded++;continue}
var credit=s.bid-l.ask,width=Math.abs(s.strike-l.strike);
if(!(credit>0)||!(width>credit)){excluded++;continue}
var loss=(width-credit)*mult;
if(!(loss>0)){excluded++;continue}
var maxLegSpreadPctMid=Math.max(qs.spreadPctMid,ql.spreadPctMid);
var spreadBand=maxLegSpreadPctMid<=10?"≤10% MID":maxLegSpreadPctMid<=25?"10–25% MID":">25% MID";
var c={key:s.strike+(call?"C":"P")+"/"+l.strike+(call?"C":"P"),shortStrike:s.strike,longStrike:l.strike,width:width,shortBid:s.bid,shortAsk:s.ask,longBid:l.bid,longAsk:l.ask,shortDelta:s.delta,longDelta:l.delta,credit:credit,maxProfit:credit*mult,maxLoss:loss,rewardRisk:credit/(width-credit),breakEven:call?s.strike+credit:s.strike-credit,maxQty:bud>0?Math.floor((bud+1e-9)/loss):0,shortSpreadPctMid:qs.spreadPctMid,wingSpreadPctMid:ql.spreadPctMid,shortQuoteQuality:qs.band,longQuoteQuality:ql.band,maxLegSpreadPctMid:maxLegSpreadPctMid,spreadBand:spreadBand,wide:maxLegSpreadPctMid>25,isCall:call,executionStress:executionStress(width,credit,mult,bud)};
if(c.wide)wide++;
valid.push(c);
}
return{candidates:valid,excluded:excluded,wide:wide,totalPairs:totalPairs,validQuotes:data.filter(r=>quoteState(r).ok).length};
}
function expiryPnl(c,spot,mult,qty){var s=num(spot),m=num(mult),n=num(qty);if(!c||s===null||m===null||m<=0||n===null||n<1||Math.floor(n)!==n)return null;var si,li;if(c.isCall){si=Math.max(s-c.shortStrike,0);li=Math.max(s-c.longStrike,0)}else{si=Math.max(c.shortStrike-s,0);li=Math.max(c.longStrike-s,0)}return(c.credit-si+li)*m*n}
function splitCsvRow(line){var out=[],cur="",quoted=false;for(var i=0;i<line.length;i++){var ch=line[i];if(ch==='"'){if(quoted&&line[i+1]==='"'){cur+='"';i++}else quoted=!quoted}else if(ch===","&&!quoted){out.push(cur);cur=""}else cur+=ch}out.push(cur);return out}
function validHttpUrl(value){return /^https?:\/\/[^\s]+$/i.test(String(value||"").trim())}
function isAdjustedRoot(value){return /^(?:1?VXX[12])/i.test(String(value||"").trim())}
function assessQuoteFreshness(observedAt,nowMs){
var stamp=String(observedAt||"").trim();
if(!stamp)return{status:"AS-OF MISSING",ok:false,ageMinutes:null,reason:"報價觀察時間缺失；仍可看情景算術，但不可當作可執行報價。"};
if(!/(?:Z|[+-][0-9]{2}:[0-9]{2})$/i.test(stamp))return{status:"TIMEZONE OFFSET UNKNOWN",ok:false,ageMinutes:null,reason:"報價時間沒有明確 Z／±HH:MM offset；不會使用瀏覽器本機時區猜測。"};
var stampMs=Date.parse(stamp);
if(!Number.isFinite(stampMs))return{status:"AS-OF INVALID",ok:false,ageMinutes:null,reason:"報價觀察時間無效。"};
var ageMinutes=(nowMs-stampMs)/60000;
if(ageMinutes < 0)return{status:"FUTURE TIMESTAMP",ok:false,ageMinutes:ageMinutes,reason:"報價時間在未來；時鐘／時區需核實。"};
if(ageMinutes>15)return{status:"STALE >15M",ok:false,ageMinutes:ageMinutes,reason:"報價時間已超過 15 分鐘；刷新報價後才可進行手動執行審查。"};
return{status:"AS-OF ≤15M",ok:true,ageMinutes:ageMinutes,reason:"時間新鮮度門檻通過，但不代表有成交或可成交。"};
}
function assessProvenance(meta,expiration,quoteCount,manuallyEdited,nowMs){
var m=meta||{},reasons=[],sourceType=String(m.sourceType||"UNKNOWN"),sourceName=String(m.sourceName||"").trim(),sourceUrl=String(m.sourceUrl||"").trim(),observedAt=String(m.observedAt||"").trim(),timezone=String(m.timezone||"").trim(),contractSymbol=String(m.contractSymbol||"").trim(),contractStatus=String(m.contractStatus||"UNKNOWN"),deliverableNote=String(m.deliverableNote||"").trim(),contractEvidenceUrl=String(m.contractEvidenceUrl||"").trim();
if(!(quoteCount>0))reasons.push("此鏈沒有報價列");
if(!/^\d{4}-\d{2}-\d{2}$/.test(String(expiration||""))||!Number.isFinite(Date.parse(expiration+"T00:00:00Z")))reasons.push("到期日缺失或無效");
if(sourceType==="UNKNOWN")reasons.push("資料來源類型未確認");
if(sourceType==="MODEL_DERIVED")reasons.push("模型衍生數值不是實測來源報價，不能通過 metadata／freshness 合格門檻。");
if(!sourceName)reasons.push("來源名稱缺失");
if(sourceType==="PUBLIC_DATA"&&!validHttpUrl(sourceUrl))reasons.push("公開資料必須提供可追溯來源網址");
if(!timezone||timezone.toUpperCase()==="UNKNOWN")reasons.push("報價時區標籤未記錄");
if(!contractSymbol)reasons.push("Option root／contract symbol 未記錄");
if(contractStatus==="UNKNOWN")reasons.push("標準或調整合約狀態未記錄");
if(!deliverableNote)reasons.push("每張合約交割單位未記錄");
if(contractStatus!=="UNKNOWN"&&!validHttpUrl(contractEvidenceUrl))reasons.push("合約條款證據網址缺失／無效");
var freshness=assessQuoteFreshness(observedAt,nowMs===undefined?Date.now():nowMs);
var metadataComplete=reasons.length===0&&!manuallyEdited;
if(manuallyEdited)reasons.push("報價格已手動修改；需重新對照來源");
if(!freshness.ok)reasons.push(freshness.reason);
var status="INCOMPLETE",complete=metadataComplete&&freshness.ok&&!manuallyEdited;
if(sourceType==="MODEL_DERIVED")status="MODEL_ONLY";
else if(isAdjustedRoot(contractSymbol)&&contractStatus!=="ADJUSTED_TERMS_RECORDED"){
reasons.push("合約根顯示疑似 VXX 調整合約，但條款狀態未標記為調整合約；停止計算。");
status="CONTRACT_STATUS_CONFLICT";complete=false;metadataComplete=false;
}else if(contractStatus==="ADJUSTED_TERMS_RECORDED"){
reasons.push("此版本未正規化調整合約的交割／價格刻度；最大虧損與容量已封鎖。");
status="ADJUSTED_CONTRACT_SCENARIO_ONLY";complete=false;metadataComplete=false;
}else if(manuallyEdited)status="MANUAL_EDIT_RECHECK";
else if(freshness.status==="AS-OF MISSING")status="QUOTE_TIME_MISSING";
else if(freshness.status==="TIMEZONE OFFSET UNKNOWN")status="QUOTE_TIMEZONE_UNKNOWN";
else if(freshness.status==="AS-OF INVALID")status="INVALID_QUOTE_TIMESTAMP";
else if(freshness.status==="FUTURE TIMESTAMP")status="FUTURE_QUOTE_TIMESTAMP";
else if(freshness.status==="STALE >15M")status="STALE_QUOTE";
else if(!metadataComplete)status="INCOMPLETE";
else status="RECORDED_REVIEW_REQUIRED";
return{status:status,complete:complete,metadataComplete:metadataComplete,freshnessStatus:freshness.status,quoteAgeMinutes:freshness.ageMinutes,ordersAuthorized:false,reasons:reasons};
}
function buildPrimaryPlannerHandoff(meta,expiration,chainKey,candidate,multiplier,quoteCount,manuallyEdited,attested,nowMs){
var fail=function(reason){return{ok:false,reason:reason}},m=meta||{},root=chainKey==="QQQ_CALL"?"QQQ":chainKey==="VXX_CALL"?"VXX":null,mult=num(multiplier),clock=nowMs===undefined?Date.now():nowMs;
if(!root)return fail("只可把 QQQ CALL／VXX CALL 送進主風險池；Put 和其他研究組合保持隔離。");
if(!candidate||candidate.isCall!==true)return fail("先選取一組有效 Call-Credit 價差。");
if(!attested)return fail("請先勾選人工覆核聲明：確認來源、報價、到期日、每條腿和標準 100 股交割單位。");
if(!["USER_SCREENSHOT_TRANSCRIPTION","BROKER_EXPORT"].includes(String(m.sourceType||"")))return fail("主風險池只接受使用者截圖轉錄或券商匯出；公開／模型資料只作情景分析。");
if(String(m.contractSymbol||"").trim()!==root)return fail("合約 root 必須與主策略候選完全一致（"+root+"），不可用 VXX1／VXX2 或其他調整合約。");
if(String(m.contractStatus||"")!=="STANDARD_TERMS_RECORDED")return fail("只支援已記錄並由操作員核對的標準合約條款；調整／未知條款封鎖。");
if(mult!==100)return fail("主策略候選目前只接受已明確核對的 100 股標準乘數。");
if(!/(100.{0,30}(shares?|股)|(shares?|股).{0,30}100)/i.test(String(m.deliverableNote||"")))return fail("請在每張實際交割單位記錄中明確寫出標準 100 股。");
if(!validHttpUrl(m.contractEvidenceUrl))return fail("必須填寫 OCC／券商合約條款證據網址。");
var provenanceResult=assessProvenance(m,expiration,quoteCount,manuallyEdited,clock);
if(!provenanceResult.complete)return fail("來源／時間資料未過檢查："+provenanceResult.status+"；"+provenanceResult.reasons.join("；"));
if(provenanceResult.freshnessStatus!=="AS-OF ≤15M")return fail("操作員記錄的觀察時間須在 15 分鐘內；這不會認證資料供應商時間戳。");
var expiryMs=Date.parse(String(expiration||"")+"T00:00:00Z");
if(!Number.isFinite(expiryMs)||new Date(expiryMs).toISOString().slice(0,10)!==expiration)return fail("到期日無效。");
var todayMs=Date.parse(new Date(clock).toISOString().slice(0,10)+"T00:00:00Z"),dte=(expiryMs-todayMs)/86400000;
if(dte<14||dte>120)return fail("主操作台支援 14–120 個日曆日 DTE；目前到期日不在這個範圍。");
var shortQ=quoteState({bid:candidate.shortBid,ask:candidate.shortAsk}),longQ=quoteState({bid:candidate.longBid,ask:candidate.longAsk});
if(!shortQ.ok||!longQ.ok)return fail("兩條腿都必須有有效正數 Bid／Ask。");
var credit=candidate.shortBid-candidate.longAsk,width=candidate.longStrike-candidate.shortStrike;
if(!(credit>0&&width>credit)||Math.abs(credit-candidate.credit)>1e-6||Math.abs(width-candidate.width)>1e-6)return fail("腿位、Bid／Ask、淨 credit 或最大虧損無法互相核對。");
function occ(k){var ymd=expiration.slice(2,4)+expiration.slice(5,7)+expiration.slice(8,10),milli=Math.round(k*1000);if(Math.abs(milli/1000-k)>1e-8||milli<0||milli>99999999)return null;return root+ymd+"C"+String(milli).padStart(8,"0")}
var shortSymbol=occ(candidate.shortStrike),longSymbol=occ(candidate.longStrike);
if(!shortSymbol||!longSymbol)return fail("無法生成精確標準合約識別碼。");
var maxLoss=(width-credit)*100;
return{ok:true,candidate:{
handoffSchema:"QQQ_HYBRID_PRIMARY_OPTION_CANDIDATE_V1",chainKey:chainKey,contractRoot:root,right:"call",
expiry:expiration,dte:dte,shortStrike:candidate.shortStrike,longStrike:candidate.longStrike,
shortContractSymbol:shortSymbol,longContractSymbol:longSymbol,
shortBid:candidate.shortBid,shortAsk:candidate.shortAsk,longBid:candidate.longBid,longAsk:candidate.longAsk,
shortDelta:candidate.shortDelta,longDelta:candidate.longDelta,
shortQuoteWidthPctMid:shortQ.spreadPctMid,longQuoteWidthPctMid:longQ.spreadPctMid,
shortQuoteQuality:shortQ.label,longQuoteQuality:longQ.label,credit:credit,width:width,
maxLossPerSpread:maxLoss,maxProfitPerSpread:credit*100,multiplierAssumption:100,multiplierVerified:true,
contractTermsStatus:"STANDARD_TERMS_RECORDED",adjustedContractSymbols:[],
source:"MANUAL_LAB_OPTION_EVIDENCE",sourceType:m.sourceType,sourceName:String(m.sourceName||"").trim(),
sourceUrl:String(m.sourceUrl||"").trim(),quoteObservedAt:String(m.observedAt||"").trim(),timezone:String(m.timezone||"").trim(),
quoteTimestampStatus:"USER_RECORDED_ASOF_UNVERIFIED_BY_SOURCE",
contractEvidenceUrl:String(m.contractEvidenceUrl||"").trim(),deliverableNote:String(m.deliverableNote||"").trim(),
manualAttestation:true,sizingEvidence:"LAB_HUMAN_ATTESTED_STANDARD_TERMS",candidateStatus:"HUMAN_REVIEW_REQUIRED",
issuedAt:new Date(clock).toISOString(),operatorObservationAgeMinutes:provenanceResult.quoteAgeMinutes,
dataAuthentication:"NOT_INDEPENDENTLY_VERIFIED",ordersAuthorized:false
},reason:"通過格式／算術／人工聲明檢查；來源真實性與實際成交仍未經程式驗證。"};
}
function parseCsv(text){var out={QQQ_CALL:[],QQQ_PUT:[],VXX_CALL:[],VXX_PUT:[]},errors=[],conflicts=[],lines=String(text||"").split(/\r?\n/).filter(x=>x.trim()!==""),idx={},start=0,hasHeader=false,hasMetaColumns=false,metadata={sourceType:"UNKNOWN",sourceName:"",sourceUrl:"",observedAt:"",timezone:""},chainMetadata={},expiryValues=[],commonValues={},commonMissing={},parsedDataRows=0;var commonCols={source_type:"sourceType",source_name:"sourceName",source_url:"sourceUrl",observed_at:"observedAt",timezone:"timezone"};var chainCols={contract_symbol:"contractSymbol",contract_status:"contractStatus",deliverable_note:"deliverableNote",contract_evidence_url:"contractEvidenceUrl"};if(!lines.length)return{chains:out,errors:errors,total:0,expiration:"",metadata:metadata,chainMetadata:chainMetadata,metadataConflicts:conflicts,hasMetadataColumns:false};var first=splitCsvRow(lines[0]).map(x=>x.trim().toLowerCase());if(first.indexOf("symbol")>=0&&first.indexOf("side")>=0&&first.indexOf("strike")>=0){hasHeader=true;first.forEach((x,i)=>idx[x]=i);start=1}else{idx={symbol:0,side:1,strike:2,bid:3,ask:4,delta:5};}hasMetaColumns=hasHeader&&["expiration","source_type","source_name","source_url","observed_at","timezone","contract_symbol","contract_status","deliverable_note","contract_evidence_url"].some(k=>idx[k]!==undefined);function field(a,key){return idx[key]===undefined?"":String(a[idx[key]]===undefined?"":a[idx[key]]).trim()}function addCommon(key,value){if(!value)return;if(!commonValues[key])commonValues[key]=[];if(commonValues[key].indexOf(value)<0)commonValues[key].push(value)}function addChain(k,key,value){if(!value)return;if(!chainMetadata[k])chainMetadata[k]={contractSymbol:"",contractStatus:"",deliverableNote:"",contractEvidenceUrl:""};var existing=chainMetadata[k][key];if(existing&&existing!==value)conflicts.push(k+" 的 "+key+" 值不一致");else chainMetadata[k][key]=value}for(var i=start;i<lines.length;i++){var a=splitCsvRow(lines[i]),sym=field(a,"symbol").toUpperCase(),side=field(a,"side").toUpperCase(),k=sym+"_"+side,st=num(field(a,"strike")),bid=num(field(a,"bid")),ask=num(field(a,"ask")),delta=num(field(a,"delta"));if(!out[k]||st===null){errors.push("第"+(i+1)+"行格式錯誤");continue}if((bid!==null&&bid<0)||(ask!==null&&ask<0)||(bid!==null&&ask!==null&&bid>ask)){errors.push("第"+(i+1)+"行 Bid／Ask 無效");continue}out[k].push({strike:st,bid:bid,ask:ask,delta:delta});parsedDataRows++;var exp=field(a,"expiration");if(exp)expiryValues.push(exp);for(var col in commonCols){var cv=field(a,col);if(cv)addCommon(col,cv);else commonMissing[col]=(commonMissing[col]||0)+1}for(var col2 in chainCols)addChain(k,chainCols[col2],field(a,col2));}for(var c in commonValues){if(commonValues[c].length>1)conflicts.push("跨資料列的 "+c+" 不一致");else metadata[commonCols[c]]=commonValues[c][0];if(commonMissing[c])conflicts.push("部分資料列缺少 "+c)}var uniqueExp=Array.from(new Set(expiryValues));if(uniqueExp.length>1)conflicts.push("同一 Lab 不可混合多個到期日");if(expiryValues.length>0&&expiryValues.length!==parsedDataRows)conflicts.push("部分資料列缺少到期日");Object.keys(out).forEach(k=>out[k]=sorted(out[k]));return{chains:out,errors:errors,total:Object.keys(out).reduce((n,k)=>n+out[k].length,0),expiration:uniqueExp.length===1?uniqueExp[0]:"",metadata:metadata,chainMetadata:chainMetadata,metadataConflicts:Array.from(new Set(conflicts)),hasMetadataColumns:hasMetaColumns}}
function csvCell(value){var s=value===null||value===undefined?"":String(value);return /[",\r\n]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s}
function init(win,doc){var chains={QQQ_CALL:[],QQQ_PUT:[],VXX_CALL:[],VXX_PUT:[]},active="QQQ_CALL",selected=null,loaded=false,manuallyEdited=false,provenance={sourceType:"UNKNOWN",sourceName:"",sourceUrl:"",observedAt:"",timezone:"",chainMetadata:{}};var PaperJournal=win.PaperObservationJournal||null,paperEnvelope=null,paperJournalLoadError="",paperJournalStorageOK=true;var $=id=>doc.getElementById(id),label=k=>k.replace("_"," ");function val(id,fb){var n=num($(id).value);return n===null?fb:n}
function commonFromInputs(){provenance.sourceType=$("sourceType").value||"UNKNOWN";provenance.sourceName=$("sourceName").value.trim();provenance.sourceUrl=$("sourceUrl").value.trim();provenance.observedAt=$("asof").value.trim();provenance.timezone=$("timezone").value.trim()}
function activeChainMetaFromInputs(){provenance.chainMetadata[active]={contractSymbol:$("contractSymbol").value.trim(),contractStatus:$("contractStatus").value||"UNKNOWN",deliverableNote:$("deliverableNote").value.trim(),contractEvidenceUrl:$("contractEvidenceUrl").value.trim()}}
function currentMeta(){return Object.assign({},provenance,provenance.chainMetadata[active]||{contractSymbol:"",contractStatus:"UNKNOWN",deliverableNote:"",contractEvidenceUrl:""})}
function writeCommonInputs(){["sourceType","sourceName","sourceUrl","asof","timezone"].forEach(k=>{$(k).value=provenance[k]||(k==="sourceType"?"UNKNOWN":"")})}
function writeChainInputs(){var m=provenance.chainMetadata[active]||{};$("contractSymbol").value=m.contractSymbol||"";$("contractStatus").value=m.contractStatus||"UNKNOWN";$("deliverableNote").value=m.deliverableNote||"";$("contractEvidenceUrl").value=m.contractEvidenceUrl||""}
function resetProvenance(){provenance={sourceType:"UNKNOWN",sourceName:"",sourceUrl:"",observedAt:"",timezone:"",chainMetadata:{}};manuallyEdited=false;writeCommonInputs();writeChainInputs()}
function result(){var m=currentMeta(),status=m.contractStatus||"UNKNOWN";if(isAdjustedRoot(m.contractSymbol)&&status!=="ADJUSTED_TERMS_RECORDED")status="ADJUSTED_TERMS_RECORDED";return calculateVerticals(active,chains[active],val("mult",null),val("budget",null),status)}
function selectedC(r){if(!r.candidates.length)return null;if(selected){var found=r.candidates.find(c=>c.key===selected);if(found)return found}return r.candidates[0]}
function renderTabs(){doc.querySelectorAll("[data-key]").forEach(b=>b.classList.toggle("active",b.dataset.key===active))}
function renderQuotes(){
var rows=sorted(chains[active]),states=rows.map(quoteState);
$("quotes").innerHTML=rows.length?rows.map(function(r,i){
var q=quoteState(r),w=r.bid!==null&&r.ask!==null?r.ask-r.bid:null;
return "<tr><td><input class='st' type='number' step='.5' data-i='"+i+"' data-f='strike' value='"+esc(r.strike)+"'></td><td><input type='number' min='0' step='.01' data-i='"+i+"' data-f='bid' value='"+(r.bid===null?"":esc(r.bid))+"'></td><td><input type='number' min='0' step='.01' data-i='"+i+"' data-f='ask' value='"+(r.ask===null?"":esc(r.ask))+"'></td><td><input class='de' type='number' step='.0001' data-i='"+i+"' data-f='delta' value='"+(r.delta===null?"":esc(r.delta))+"'></td><td>"+(w===null?"—":px(w))+"</td><td>"+(q.spreadPctMid===null?"—":q.spreadPctMid.toFixed(1)+"%")+"</td><td><span class='quality "+(q.bad?"bad":q.wide?"":"good")+"'>"+q.label+"</span></td></tr>";
}).join(""):"<tr><td colspan='7' class='empty'>此鏈尚未載入報價。</td></tr>";
$("qualitySummary").textContent=loaded?rows.length+" 個履約價；雙邊有效 "+states.filter(q=>q.ok).length+"；缺價／無效 "+states.filter(q=>!q.ok).length+"；窄價差 ≤10% mid "+states.filter(q=>q.ok&&q.band==="TIGHT").length+"；10–25% mid "+states.filter(q=>q.ok&&q.band==="MODERATE").length+"；偏闊 >25% mid "+states.filter(q=>q.wide).length+"。":"請先載入截圖樣本或匯入已核對 CSV。";
$("chainMeta").textContent=loaded?label(active)+" · "+($("expiry").value||"到期日未記錄"):"尚未載入";
}
function draw(c){if(!c){$("graph").innerHTML="<div class='empty'>沒有可繪製的有效價差。</div>";return}var mult=val("mult",null),qty=val("qty",null);if(mult===null||mult<=0||qty===null||qty<1||Math.floor(qty)!==qty){$("graph").innerHTML="<div class='empty'>乘數須為正數，組數須為正整數；參數無效，暫不繪圖。</div>";return}var W=700,H=265,L=58,R=14,T=20,B=38,lo=Math.max(0,Math.min(c.shortStrike,c.longStrike)-c.width*1.2),hi=Math.max(c.shortStrike,c.longStrike)+c.width*1.2,pts=[];for(var i=0;i<=40;i++){var p=lo+(hi-lo)*i/40;pts.push({x:p,y:expiryPnl(c,p,mult,qty)})}var ymin=Math.min(0,...pts.map(p=>p.y)),ymax=Math.max(0,...pts.map(p=>p.y));if(ymax-ymin<1){ymax+=1;ymin-=1}var X=p=>L+(p-lo)/(hi-lo)*(W-L-R),Y=p=>T+(ymax-p)/(ymax-ymin)*(H-T-B),points=pts.map(p=>X(p.x).toFixed(1)+","+Y(p.y).toFixed(1)).join(" "),z=Y(0),lbl=[lo,(lo+hi)/2,hi].map(p=>"<text x='"+X(p)+"' y='"+(H-12)+"' text-anchor='middle' fill='#9baabd' font-size='10'>"+p.toFixed(2)+"</text>").join("");$("graph").innerHTML="<svg viewBox='0 0 "+W+" "+H+"' aria-label='到期損益圖'><line x1='"+L+"' y1='"+z+"' x2='"+(W-R)+"' y2='"+z+"' stroke='#75849a' stroke-dasharray='4 4'/><line x1='"+L+"' y1='"+T+"' x2='"+L+"' y2='"+(H-B)+"' stroke='#566578'/><polyline points='"+points+"' fill='none' stroke='#42d6a0' stroke-width='3' stroke-linejoin='round'/><text x='7' y='15' fill='#9baabd' font-size='10'>P&amp;L ($)</text><text x='"+(W-R)+"' y='"+(H-1)+"' text-anchor='end' fill='#9baabd' font-size='10'>到期標的價格</text><text x='"+(L-7)+"' y='"+(T+4)+"' text-anchor='end' fill='#9baabd' font-size='10'>"+ymax.toFixed(0)+"</text><text x='"+(L-7)+"' y='"+(H-B)+"' text-anchor='end' fill='#9baabd' font-size='10'>"+ymin.toFixed(0)+"</text>"+lbl+"</svg>";$("graphNote").textContent="組數 "+qty+"。只顯示到期損益，不含到期前 Greeks、波動率、時間值、佣金與滑價。"}
function renderStressTable(c){
var rows=c.executionStress.map(function(s){return "<tr><td>$"+s.extraSlippagePerLeg.toFixed(3)+"</td><td>"+(s.viable?px(s.creditPerShare):"NO TRADE")+"</td><td>"+(s.viable?money(s.maxLoss):"—")+"</td><td>"+(s.viable?String(s.maxQty):"0")+"</td></tr>"}).join("");
return "<div class='sensitivity-wrap'><p class='tiny'><b>額外執行成本敏感度（假設值，不是實測滑價）</b><br>每腿額外逆向滑價套用於 short Bid − wing Ask：淨 credit 再減 2 × 每腿滑價。credit ≤ 0 即 NO TRADE。</p><div class='wrap'><table class='quote'><thead><tr><th>額外滑價／腿</th><th>淨 credit／股</th><th>最大虧損／組</th><th>此候選預算組數</th></tr></thead><tbody>"+rows+"</tbody></table></div><p class='tiny'>價差品質以最大單腿 (Ask−Bid)/mid 分級：≤10%、10–25%、>25%。這是容量與報價品質敏感度，不是成交機率、勝率、回測結果或下單授權。</p></div>";
}
function renderSelected(r){
var c=selectedC(r);
if(!c){$("maxLoss").textContent="—";$("maxProfit").textContent="—";$("capacity").textContent=r.error?"PENDING":"0";$("selectedBadge").textContent=r.error?"輸入無效":"沒有有效組合";$("detail").innerHTML="<div class='empty'>"+esc(r.error||"沒有有效價差：檢查 Bid／Ask 是否完整，以及賣出 Bid 是否大於保護 Ask。")+"</div>";$("copy").disabled=true;draw(null);return;}
selected=c.key;$("maxLoss").textContent=money(c.maxLoss);$("maxProfit").textContent=money(c.maxProfit);$("capacity").textContent=String(c.maxQty);$("selectedBadge").textContent=c.key;
var q=c.maxQty,m=val("mult",null);
$("detail").innerHTML="<div class='stats' style='grid-template-columns:repeat(2,minmax(0,1fr))'><div class='stat'><small>淨權利金／組</small><b class='positive'>"+money(c.maxProfit)+"</b><span>"+px(c.credit)+" 每股</span></div><div class='stat'><small>最大虧損／組</small><b class='negative'>"+money(c.maxLoss)+"</b><span>未扣費用</span></div><div class='stat'><small>損益平衡價</small><b>"+px(c.breakEven)+"</b><span>到期值</span></div><div class='stat'><small>預算可開組數</small><b>"+q+"</b><span>風險預算 "+money(val("budget",null))+"</span></div></div><p><b>賣出腿：</b>"+c.shortStrike+(c.isCall?"C":"P")+" @ Bid "+px(c.shortBid)+"；腿價差／mid "+c.shortSpreadPctMid.toFixed(1)+"%</p><p><b>保護腿：</b>"+c.longStrike+(c.isCall?"C":"P")+" @ Ask "+px(c.longAsk)+"；腿價差／mid "+c.wingSpreadPctMid.toFixed(1)+"%</p><p><b>最大單腿價差分級：</b>"+c.spreadBand+"；<b>履約價寬度：</b>"+px(c.width)+" × <b>乘數：</b>"+m+"</p><p><b>權利金／最大虧損：</b>"+(c.rewardRisk*100).toFixed(2)+"%</p><p><b>預算內合計最大盈利／虧損：</b>"+money(c.maxProfit*q)+" / "+money(c.maxLoss*q)+"</p><p class='tiny'>基準 credit 是 short Bid − protective Ask；仍非交易所複合單的成交證明。</p>"+renderStressTable(c);
$("copy").disabled=false;draw(c);
}
function renderMatrix(){
var r=result(),rows=r.candidates.slice(),sort=$("sort").value;
rows.sort((a,b)=>sort==="credit"?b.credit-a.credit:sort==="loss"?a.maxLoss-b.maxLoss:sort==="capacity"?b.maxQty-a.maxQty:b.rewardRisk-a.rewardRisk);
$("candidates").textContent=String(rows.length);$("matrixMeta").textContent=r.error?"BLOCKED · 輸入無效":rows.length+" 有效 · "+r.excluded+" 排除；偏闊候選 "+r.wide+"（>25% MID）";
$("matrix").innerHTML=rows.length?rows.map(function(c){return "<tr class='cand "+(c.key===selected?"selected":"")+"' data-c='"+esc(c.key)+"'><td>"+c.shortStrike+(c.isCall?"C":"P")+" / "+c.longStrike+(c.isCall?"C":"P")+"</td><td>"+px(c.width)+"</td><td>"+px(c.shortBid)+" − "+px(c.longAsk)+"</td><td class='positive'>"+money(c.maxProfit)+"</td><td>"+money(c.maxProfit)+"</td><td class='negative'>"+money(c.maxLoss)+"</td><td>"+(c.rewardRisk*100).toFixed(2)+"%</td><td>"+px(c.breakEven)+"</td><td>"+c.maxQty+"</td><td><span class='quality "+(c.wide?"":"good")+"'>"+c.spreadBand+" · S "+c.shortSpreadPctMid.toFixed(1)+"% / W "+c.wingSpreadPctMid.toFixed(1)+"%</span></td></tr>"}).join(""):"<tr><td colspan='10' class='empty'>沒有有效信用價差。請確認 Bid／Ask 雙邊完整並且賣出 Bid 高於保護 Ask。</td></tr>";
$("matrix").querySelectorAll("[data-c]").forEach(tr=>tr.addEventListener("click",()=>{selected=tr.dataset.c;renderAll()}));renderSelected(r);$("matrix").querySelectorAll("[data-c]").forEach(tr=>tr.classList.toggle("selected",tr.dataset.c===selected));
}
function renderProvenance(){
commonFromInputs();activeChainMetaFromInputs();
var m=currentMeta(),p=assessProvenance(m,$("expiry").value,sorted(chains[active]).length,manuallyEdited),age=p.quoteAgeMinutes===null?"":" · "+Math.round(p.quoteAgeMinutes)+" 分鐘";
var handoffGate=buildPrimaryPlannerHandoff(m,$("expiry").value,active,selectedC(result()),val("mult",null),sorted(chains[active]).length,manuallyEdited,$("attestStandard").checked,Date.now());
$("sendToMain").disabled=!handoffGate.ok;
$("handoffStatus").textContent=handoffGate.ok?"可送入主操作台：人工記錄欄位與標準合約已通過結構檢查；仍須人工覆核，不代表可成交。":handoffGate.reason;
var labelText=p.status==="NOT_LOADED"?"NO QUOTES":p.status==="MODEL_ONLY"?"MODEL ONLY · NOT HISTORICAL":p.status==="ADJUSTED_CONTRACT_SCENARIO_ONLY"?"ADJUSTED CONTRACT · CAPACITY BLOCKED":p.status==="CONTRACT_STATUS_CONFLICT"?"CONTRACT STATUS CONFLICT · BLOCKED":p.status==="MANUAL_EDIT_RECHECK"?"MANUAL EDIT · RECHECK SOURCE":p.status==="QUOTE_TIME_MISSING"?"QUOTE TIME MISSING · SCENARIO ONLY":p.status==="QUOTE_TIMEZONE_UNKNOWN"?"TIMEZONE OFFSET UNKNOWN · SCENARIO ONLY":p.status==="INVALID_QUOTE_TIMESTAMP"?"QUOTE TIMESTAMP INVALID · BLOCKED":p.status==="FUTURE_QUOTE_TIMESTAMP"?"FUTURE QUOTE TIMESTAMP · BLOCKED":p.status==="STALE_QUOTE"?"STALE QUOTE >15M · REFRESH REQUIRED":p.complete?"AS-OF + METADATA PASS · HUMAN REVIEW ONLY":"SCENARIO ONLY · PROVENANCE INCOMPLETE";
$("provenanceStatus").textContent=labelText;
$("provenanceDetail").textContent="報價時效："+p.freshnessStatus+age+"；"+(p.reasons.length?p.reasons.join("；"):"來源欄位已填，但本工具沒有獨立驗證資料供應商、成交可執行性或券商交割記錄。")+"；時間門檻通過仍不代表即時報價、可成交或實際成交；本工具永不授權下單。";
$("sourceBadge").textContent=labelText;$("sourceBadge").className="tag "+(p.complete?"warn":"bad");
}

function initPaperJournal(){if(!PaperJournal){paperJournalLoadError="Paper journal module did not load; no event was stored.";return}paperEnvelope=PaperJournal.emptyEnvelope(new Date().toISOString());try{if(!win.localStorage)throw new Error("localStorage unavailable");var raw=win.localStorage.getItem(PaperJournal.STORAGE_KEY);if(raw){var parsed=PaperJournal.parseEnvelope(raw);if(parsed.ok)paperEnvelope=parsed.envelope;else paperJournalLoadError="Saved journal validation failed; it was not overwritten. Import a valid backup JSON to recover."}}catch(err){paperJournalStorageOK=false;paperJournalLoadError="Browser local storage is unavailable; journal writes are blocked."}}
function paperSaveEnvelope(next,message,allowRecovery){if(paperJournalLoadError.indexOf("Saved journal validation failed")===0&&!allowRecovery)return{ok:false,error:paperJournalLoadError};try{if(!win.localStorage)throw new Error("localStorage unavailable");win.localStorage.setItem(PaperJournal.STORAGE_KEY,JSON.stringify(next));paperEnvelope=next;paperJournalLoadError="";paperJournalStorageOK=true;renderPaperJournal();$("paperJournalStatus").textContent=message;return{ok:true}}catch(err){paperJournalStorageOK=false;var reason="本機儲存失敗，沒有確認保存；請先匯出／清理儲存空間。 "+(err&&err.message?err.message:String(err));$("paperJournalStatus").textContent=reason;return{ok:false,error:reason}}}
function paperAppend(event){if(!PaperJournal||!paperEnvelope||!paperJournalStorageOK){$("paperJournalStatus").textContent=paperJournalLoadError||"Journal storage unavailable; no event saved.";return}var appended=PaperJournal.appendEvent(paperEnvelope,event);if(!appended.ok){$("paperJournalStatus").textContent="拒絕追加："+appended.error;return}paperSaveEnvelope(appended.envelope,"已追加 "+event.eventType+"；原有事件未修改。")}
function downloadPaperJson(){if(!PaperJournal||!paperEnvelope)return;var exported=PaperJournal.exportJson(paperEnvelope,new Date().toISOString());if(!exported.ok){$("paperJournalStatus").textContent="匯出失敗："+exported.error;return}var url=win.URL.createObjectURL(new win.Blob([exported.text],{type:"application/json;charset=utf-8"})),a=doc.createElement("a");a.href=url;a.download="qqq_hybrid_paper_observations_"+new Date().toISOString().slice(0,10)+".json";doc.body.appendChild(a);a.click();a.remove();win.URL.revokeObjectURL(url);$("paperJournalStatus").textContent="已匯出 "+paperEnvelope.events.length+" 個追加式事件；備份內容仍未獨立認證。"}
function recordPaperObservation(){if(!PaperJournal||!paperEnvelope||!loaded){$("paperJournalStatus").textContent="先載入或匯入有效報價鏈，再記錄觀察。";return}commonFromInputs();activeChainMetaFromInputs();var now=Date.now(),meta=currentMeta(),p=assessProvenance(meta,$("expiry").value,sorted(chains[active]).length,manuallyEdited,now),c=selectedC(result());var created=PaperJournal.createQuoteObservation({eventId:PaperJournal.nextEventId("QUOTE",paperEnvelope.events.length,now),recordedAt:new Date(now).toISOString(),chainKey:active,expiration:$("expiry").value,sourceMeta:meta,provenanceStatus:p.status,freshnessStatus:p.freshnessStatus,quoteAgeMinutes:p.quoteAgeMinutes,provenanceComplete:p.complete,manuallyEdited:manuallyEdited,multiplier:val("mult",null),riskBudgetUsd:val("budget",null),plannedQuantity:val("qty",null),intendedLimitCreditPerShare:val("paperLimitCredit",null),candidate:c,chainRows:sorted(chains[active]),note:$("paperQuoteNote").value.trim()});if(!created.ok){$("paperJournalStatus").textContent="未記錄："+created.error;return}paperAppend(created.event)}
function recordPaperOutcome(){if(!PaperJournal||!paperEnvelope){$("paperJournalStatus").textContent="Journal 模組未載入。";return}var observation=paperEnvelope.events.find(function(e){return e.eventType==="QUOTE_OBSERVATION"&&e.eventId===$("paperOutcomeObservation").value});if(!observation){$("paperJournalStatus").textContent="請先選擇已記錄的報價觀察。";return}var now=Date.now(),created=PaperJournal.createOutcomeEvent({eventId:PaperJournal.nextEventId("OUTCOME",paperEnvelope.events.length,now),recordedAt:new Date(now).toISOString(),outcomeType:$("paperOutcomeType").value,fillCreditPerShare:num($("paperOutcomeCredit").value),filledQuantity:num($("paperOutcomeQty").value),outcomeAt:$("paperOutcomeAt").value.trim(),outcomeReference:$("paperOutcomeRef").value.trim(),filledShortSymbol:$("paperOutcomeShortSymbol").value.trim(),filledLongSymbol:$("paperOutcomeLongSymbol").value.trim(),note:$("paperOutcomeNote").value.trim()},observation);if(!created.ok){$("paperJournalStatus").textContent="未記錄結果："+created.error;return}paperAppend(created.event)}
function importPaperJournalFile(){var input=$("paperJournalFile"),file=input.files&&input.files[0];if(!file)return;var reader=new win.FileReader();reader.onload=function(){var raw=String(reader.result||""),merged;if(paperJournalLoadError.indexOf("Saved journal validation failed")===0){merged=PaperJournal.parseEnvelope(raw)}else{merged=PaperJournal.mergeEnvelopes(paperEnvelope,raw)}if(!merged.ok){$("paperJournalStatus").textContent="匯入拒絕；現有有效紀錄未更改："+merged.error;input.value="";return}var next=merged.envelope||merged;var added=typeof merged.added==="number"?merged.added:next.events.length;var saved=paperSaveEnvelope(next,"已合併備份："+added+" 個新增事件；相同事件 ID 已去重。",true);input.value=""};reader.onerror=function(){$("paperJournalStatus").textContent="讀取備份失敗；現有紀錄未更改。";input.value=""};reader.readAsText(file)}
function renderPaperJournal(){
if(!PaperJournal||!paperEnvelope||!$("paperJournalSummary"))return;
var s=PaperJournal.summarize(paperEnvelope);
if(!s.valid){$("paperJournalStatus").textContent="Journal validation error: "+s.error;return}
var gap=s.meanReportedFillCreditGapPerShare===null?"—":(s.meanReportedFillCreditGapPerShare>=0?"+":"")+"$"+s.meanReportedFillCreditGapPerShare.toFixed(4)+"/share";
var excluded=s.nonComparableReportedFillCount||0;
var comparisonSummary=s.eligibleReportedFillComparisons+" comparable row(s) of "+s.operatorReportedFillCount+" operator-reported fill(s); "+excluded+" retained but excluded for missing/mismatched contracts or invalid/backwards/>15m timing. Operator-entered only; not authenticated.";
$("paperJournalSummary").innerHTML=
'<div class="stat"><small>QUOTE SNAPSHOTS</small><b>'+s.quoteObservations+'</b><span>只記錄報價，不代表成交</span></div>'+
'<div class="stat"><small>METADATA + TIME PASS</small><b>'+s.metadataAndFreshnessPassAtCapture+'</b><span>仍未獨立驗證來源</span></div>'+
'<div class="stat"><small>OUTCOME EVENTS</small><b>'+s.outcomeEvents+'</b><span>假設 '+s.hypotheticalFillCount+' · 回報 fill '+s.operatorReportedFillCount+' · 回報 no-fill '+s.operatorReportedNoFillCount+'</span></div>'+
'<div class="stat"><small>TIME + CONTRACT MATCHED FILL − QUOTE SIDE</small><b>'+esc(gap)+'</b><span>'+esc(comparisonSummary)+'</span></div>';
var selected=$("paperOutcomeObservation").value;
var quoteEvents=paperEnvelope.events.filter(function(e){return e.eventType==="QUOTE_OBSERVATION"});
$("paperOutcomeObservation").innerHTML='<option value="">選擇報價觀察…</option>'+quoteEvents.slice().reverse().map(function(q){return'<option value="'+esc(q.eventId)+'">'+esc(q.eventId)+' · '+esc(q.chainKey)+' · '+esc(q.expiration||"到期日未知")+' · '+esc(q.candidate?q.candidate.key:"無有效 spread")+'</option>'}).join("");
if(quoteEvents.some(function(q){return q.eventId===selected}))$("paperOutcomeObservation").value=selected;
var rows=paperEnvelope.events.slice().reverse().slice(0,20).map(function(e){
var q=e.eventType==="QUOTE_OBSERVATION"?e:quoteEvents.find(function(x){return x.eventId===e.observationId});
var chain=q?q.chainKey:"UNKNOWN",expiry=q?q.expiration:"",candidate=q&&q.candidate?q.candidate.key:"—";
var quality=q?((q.provenanceCompleteAtCapture?"METADATA + TIME PASS":"SCENARIO ONLY")+" · "+q.provenanceAtCapture):"OUTCOME";
if(e.eventType==="OUTCOME_RECORDED"&&e.outcomeType==="OPERATOR_REPORTED_FILL"){
var eligible=(s.fillComparisons||[]).find(function(x){return x.eventId===e.eventId});
var excludedRow=(s.fillComparisonExclusions||[]).find(function(x){return x.eventId===e.eventId});
quality+=eligible?" · COMPARABLE: EXACT SYMBOLS + ≤15M":excludedRow?" · NOT COMPARABLE: "+excludedRow.reason:"";
}
var outcome=e.eventType==="QUOTE_OBSERVATION"?"QUOTE ONLY · NOT A FILL":e.outcomeType;
if(e.eventType==="OUTCOME_RECORDED"&&e.outcomeType==="OPERATOR_REPORTED_FILL"&&q&&q.candidate&&Number.isFinite(Number(e.fillCreditPerShare)))outcome+=" · $"+Number(e.fillCreditPerShare).toFixed(4)+"/share";
return'<tr><td>'+esc(e.eventId)+'</td><td>'+esc(e.eventType==="QUOTE_OBSERVATION"?"QUOTE SNAPSHOT":"OUTCOME")+'<small>'+esc(e.outcomeType||"")+'</small></td><td>'+esc(e.recordedAt)+'<small>device clock; not authenticated</small></td><td>'+esc(chain)+' · '+esc(expiry)+'<small>'+esc(candidate)+'</small></td><td>'+esc(quality)+'<small>'+esc(e.status||e.dataAuthentication||"")+'</small></td><td>'+esc(outcome)+'<small>'+esc(e.operatorNote||e.note||e.outcomeReference||"")+'</small></td></tr>';
}).join("");
$("paperJournalRows").innerHTML=rows||'<tr><td colspan="6" class="empty">尚無觀察紀錄。</td></tr>';
if(paperJournalLoadError)$("paperJournalStatus").textContent=paperJournalLoadError;
}

function renderAll(){renderTabs();renderQuotes();renderMatrix();renderProvenance();renderPaperJournal()}
function loadSample(){$("attestStandard").checked=false;chains={};Object.keys(SAMPLE.chains).forEach(k=>chains[k]=sorted(SAMPLE.chains[k]));$("expiry").value=SAMPLE.expiration;active="QQQ_CALL";selected=null;loaded=true;provenance={sourceType:"USER_SCREENSHOT_TRANSCRIPTION",sourceName:"User-uploaded screenshot (conversation attachment)",sourceUrl:"",observedAt:"",timezone:"",chainMetadata:{}};manuallyEdited=false;writeCommonInputs();writeChainInputs();$("importStatus").textContent="已載入正式截圖 fixture：只有 QQQ CALL／VXX CALL；Put 鏈保持空白。觀察時間、合約 root 與交割條款未核實，因此只作情景算術。";renderAll()}
function clear(){chains={QQQ_CALL:[],QQQ_PUT:[],VXX_CALL:[],VXX_PUT:[]};loaded=false;selected=null;resetProvenance();$("expiry").value="";$("importStatus").textContent="已清空；來源、到期日與合約交割欄位均重置。";renderAll()}
function importCsv(){var p=parseCsv($("csv").value);if(!p.total){$("importStatus").textContent="沒有有效列。"+p.errors.join("；");return}if(p.metadataConflicts.length){$("importStatus").textContent="拒絕匯入：CSV metadata 衝突。"+p.metadataConflicts.join("；");return}chains=p.chains;loaded=true;selected=null;manuallyEdited=false;$("attestStandard").checked=false;provenance=Object.assign({},p.metadata,{chainMetadata:p.chainMetadata});$("expiry").value=p.expiration||"";writeCommonInputs();writeChainInputs();$("importStatus").textContent="匯入 "+p.total+" 列。"+(p.errors.length?" 已忽略無效列："+p.errors.join("；"):"")+(p.expiration?" 到期日已明確記錄。":" CSV 未帶到期日，已清空原日期，須自行核實。")+(p.hasMetadataColumns?"":" CSV 未帶來源／合約 metadata，狀態會維持 SCENARIO ONLY。");renderAll()}
function exportCsv(){commonFromInputs();activeChainMetaFromInputs();var lines=["symbol,side,strike,bid,ask,delta,expiration,source_type,source_name,source_url,observed_at,timezone,contract_symbol,contract_status,deliverable_note,contract_evidence_url"];Object.keys(chains).forEach(k=>sorted(chains[k]).forEach(r=>{var m=provenance.chainMetadata[k]||{};lines.push([k.split("_")[0],k.split("_")[1],r.strike,r.bid===null?"":r.bid,r.ask===null?"":r.ask,r.delta===null?"":r.delta,$("expiry").value,provenance.sourceType,provenance.sourceName,provenance.sourceUrl,provenance.observedAt,provenance.timezone,m.contractSymbol||"",m.contractStatus||"UNKNOWN",m.deliverableNote||"",m.contractEvidenceUrl||""].map(csvCell).join(","))}));var url=URL.createObjectURL(new Blob([lines.join("\r\n")],{type:"text/csv;charset=utf-8"})),a=doc.createElement("a");a.href=url;a.download="qqq_vxx_option_chain_"+($("expiry").value||"unknown")+".csv";doc.body.appendChild(a);a.click();a.remove();URL.revokeObjectURL(url)}
function publishToMain(){
commonFromInputs();activeChainMetaFromInputs();
var gate=buildPrimaryPlannerHandoff(currentMeta(),$("expiry").value,active,selectedC(result()),val("mult",null),sorted(chains[active]).length,manuallyEdited,$("attestStandard").checked,Date.now());
if(!gate.ok){$("handoffStatus").textContent=gate.reason;renderAll();return}
try{
win.localStorage.setItem("QQQ_HYBRID_PRIMARY_OPTION_CANDIDATE_V1:"+active,JSON.stringify(gate.candidate));
$("handoffStatus").textContent="已寫入同源瀏覽器儲存；切回主操作台覆核。此時間是操作員記錄，並非供應商認證時間戳，不會下單。";
$("importStatus").textContent="已送出 "+active+" 候選；主操作台仍標記 HUMAN REVIEW REQUIRED。";
}catch(err){$("handoffStatus").textContent="本機交接失敗（儲存不可用）："+(err&&err.message?err.message:String(err))}
}
function copy(){
var c=selectedC(result());if(!c)return;
var m=currentMeta(),p=assessProvenance(m,$("expiry").value,sorted(chains[active]).length,manuallyEdited);
var lines=[
"Scenario arithmetic; no order authorization","Provenance="+p.status,
"Quote freshness="+p.freshnessStatus+"; age minutes="+(p.quoteAgeMinutes===null?"UNKNOWN":p.quoteAgeMinutes.toFixed(1)),
"Source type="+m.sourceType,"Source name="+m.sourceName,"Source URL="+m.sourceUrl,
"Observed at="+m.observedAt+" "+m.timezone,"Contract symbol="+m.contractSymbol,"Contract status="+m.contractStatus,
"Deliverable="+m.deliverableNote,"Contract evidence="+m.contractEvidenceUrl,"Expiry="+$("expiry").value,"Chain="+label(active),
"Short="+c.shortStrike+(c.isCall?"C":"P")+" Bid="+px(c.shortBid)+"; spread/mid="+c.shortSpreadPctMid.toFixed(2)+"%",
"Long="+c.longStrike+(c.isCall?"C":"P")+" Ask="+px(c.longAsk)+"; spread/mid="+c.wingSpreadPctMid.toFixed(2)+"%",
"Maximum leg spread/mid band="+c.spreadBand,"Net credit/share="+px(c.credit),"Max profit/contract="+money(c.maxProfit),
"Max loss/contract="+money(c.maxLoss),"Breakeven="+px(c.breakEven),"Budget="+money(val("budget",null)),"Base max quantity="+c.maxQty,
"Extra slippage sensitivity per leg="+c.executionStress.map(function(x){return "$"+x.extraSlippagePerLeg.toFixed(3)+": "+(x.viable?"credit/share "+px(x.creditPerShare)+", max loss "+money(x.maxLoss)+", maxQty "+x.maxQty:"NO TRADE")}).join(" | "),
"No broker orders; timestamp freshness and spread metrics do not prove execution."
];
var summary=lines.join("\n");
if(win.navigator&&win.navigator.clipboard&&win.navigator.clipboard.writeText)win.navigator.clipboard.writeText(summary).then(()=>{$("importStatus").textContent="摘要已複製。"}).catch(()=>{$("importStatus").textContent=summary});else $("importStatus").textContent=summary;
}
doc.querySelectorAll("[data-key]").forEach(b=>b.addEventListener("click",()=>{commonFromInputs();activeChainMetaFromInputs();active=b.dataset.key;selected=null;$("attestStandard").checked=false;writeChainInputs();renderAll()}));$("loadSample").addEventListener("click",loadSample);$("clear").addEventListener("click",clear);$("import").addEventListener("click",importCsv);$("export").addEventListener("click",exportCsv);$("copy").addEventListener("click",copy);$("sendToMain").addEventListener("click",publishToMain);$("attestStandard").addEventListener("change",renderAll);["sourceType","sourceName","sourceUrl","asof","timezone"].forEach(k=>$(k).addEventListener("change",()=>{commonFromInputs();$("attestStandard").checked=false;renderAll()}));["contractSymbol","contractStatus","deliverableNote","contractEvidenceUrl"].forEach(k=>$(k).addEventListener("change",()=>{activeChainMetaFromInputs();$("attestStandard").checked=false;renderAll()}));["expiry","mult","budget","qty","sort"].forEach(k=>$(k).addEventListener("change",()=>{if(k==="expiry"||k==="mult")$("attestStandard").checked=false;renderAll()}));$("quotes").addEventListener("change",ev=>{var e=ev.target;if(!e.hasAttribute("data-i"))return;var rs=sorted(chains[active]),i=Number(e.dataset.i),f=e.dataset.f;if(!rs[i]||["strike","bid","ask","delta"].indexOf(f)<0)return;rs[i][f]=num(e.value);chains[active]=sorted(rs);selected=null;manuallyEdited=true;$("attestStandard").checked=false;renderAll()});$("recordPaperObservation").addEventListener("click",recordPaperObservation);$("recordPaperOutcome").addEventListener("click",recordPaperOutcome);$("exportPaperJournal").addEventListener("click",downloadPaperJson);$("importPaperJournal").addEventListener("click",function(){$("paperJournalFile").click()});$("paperJournalFile").addEventListener("change",importPaperJournalFile);initPaperJournal();renderAll()}
return{SAMPLE:SAMPLE,sorted:sorted,quoteState:quoteState,calculateVerticals:calculateVerticals,expiryPnl:expiryPnl,parseCsv:parseCsv,splitCsvRow:splitCsvRow,assessProvenance:assessProvenance,buildPrimaryPlannerHandoff:buildPrimaryPlannerHandoff,num:num,init:init,csvCell:csvCell}});