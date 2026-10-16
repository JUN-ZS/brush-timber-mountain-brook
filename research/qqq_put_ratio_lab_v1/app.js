(async function(){
"use strict";
const $=id=>document.getElementById(id), L=window.PutRatioLogic;
const labels={
 BASE_DTE7_CLOSE_SHORT_RISK:"基準：DTE ≤ 7 短倉風險處理",
 TP_USD_500_CLOSE_SHORT_RISK:"獲利 +$500：全平短倉風險",
 TP_USD_800_CLOSE_SHORT_RISK:"獲利 +$800（$80k NAV 的 +1%）：全平短倉風險",
 TP_USD_1000_CLOSE_SHORT_RISK:"獲利 +$1,000：全平短倉風險",
 TP_USD_2000_CLOSE_SHORT_RISK:"獲利 +$2,000：全平短倉風險",
 TP_25PCT_MAX_TERMINAL_GAIN:"達終端最大收益的 25%",
 TP_50PCT_MAX_TERMINAL_GAIN:"達終端最大收益的 50%",
 FAST_1000_WITHIN_5D_TRIM_4_SHORTS:"5 日內達 +$1,000：減少 4 張 Short",
 DAY20_NONPOSITIVE_CLOSE_SHORT_RISK:"第 20 日 P&L ≤ 0：全平短倉風險",
 DAY20_NONPOSITIVE_TRIM_4_SHORTS:"第 20 日 P&L ≤ 0：減少 4 張 Short",
 SL_USD_500_CLOSE_SHORT_RISK:"止損 −$500：全平短倉風險",
 SL_USD_1000_CLOSE_SHORT_RISK:"止損 −$1,000：全平短倉風險",
 SL_USD_2000_CLOSE_SHORT_RISK:"止損 −$2,000：全平短倉風險"
};
let data, curveData=null;
const money=L.money,pct=L.pct;
function input(id){return L.num($(id).value);}
function stateName(s){return ({ALL:"全部歷史樣本",RV20_LT15:"RV20 < 15%",RV20_15_25:"RV20 15–25%",RV20_25_35:"RV20 25–35%",RV20_GTE35:"RV20 ≥ 35%"}[s]||s);}

function portfolioStats(nav,policy){
 const dates=curveData?.session_dates||[],series=curveData?.cumulative_pnl_usd_by_policy?.[policy]||[];
 if(!dates.length||series.length!==dates.length)return null;
 const pts=[];
 for(let i=0;i<dates.length;i++)if(series[i]!==null&&series[i]!==undefined&&Number.isFinite(Number(series[i])))pts.push({i,date:dates[i],pnl:Number(series[i]),eq:nav+Number(series[i])});
 if(!pts.length)return null;
 let peak=pts[0],maxUsd=0,maxPct=0,maxPeakDate=peak.date,maxTroughDate=peak.date;
 for(const p of pts){
  if(p.eq>=peak.eq){peak=p;continue;}
  const usd=peak.eq-p.eq,pctDrop=peak.eq>0?(p.eq/peak.eq-1)*100:null;
  if(pctDrop!==null&&pctDrop<maxPct){maxPct=pctDrop;maxUsd=usd;maxPeakDate=peak.date;maxTroughDate=p.date;}
 }
 const dd=L.drawdownCycleStats(dates,pts);
 const levels=dd.levels;
 const span=dd.spanYears;
 return {dates,series,pts,maxUsd,maxPct,maxPeakDate,maxTroughDate,levels,coverage:100*pts.length/dates.length,missing:dates.length-pts.length,spanYears:span,finalPnl:pts[pts.length-1].pnl,minEquity:Math.min(...pts.map(x=>x.eq)),summary:curveData.metrics_by_policy_at_80k_nav?.[policy]||{}};
}
function renderPortfolio(nav){
 const policy=$("curvePolicy")?.value||"BASE_DTE7_CLOSE_SHORT_RISK";
 const status=$("portfolioState"),cards=$("portfolioMetrics"),rows=$("strategyDdRows"),chart=$("equityChart"),note=$("portfolioCaveat");
 if(!curveData){
  status.textContent="PENDING";
  cards.innerHTML='<div class="empty">逐日組合回放尚未保存；未完成真實歷史重算前不會顯示策略 MaxDD。</div>';
  rows.innerHTML='<tr><td colspan="5">PENDING · 不以正股回撤代替期權策略 MaxDD</td></tr>';
  chart.innerHTML="";
  note.textContent="等候以保存的每日期權腿估值重建序列組合曲線；單筆終值不能拼成逐日曲線。";
  return;
 }
 const m=portfolioStats(nav,policy);
 if(!m){status.textContent="BLOCKED";cards.innerHTML='<div class="empty">此政策沒有可用逐日曲線。</div>';rows.innerHTML="";chart.innerHTML="";return;}
 status.textContent="QUOTE-MARK REPLAY · NOT LIVE";
 const money=L.money,pct=L.pct,s=m.summary;
 cards.innerHTML=[
  ["逐日觀察 MaxDD",pct(m.maxPct),m.maxPeakDate+" → "+m.maxTroughDate],
  ["MaxDD 金額",money(-m.maxUsd),"峰值減谷值"],
  ["最後可觀察淨 P&L",money(m.finalPnl),"非複利、每段固定 1 單位"],
  ["估值覆蓋",pct(m.coverage),m.missing+" / "+m.dates.length+" sessions 未知"]
 ].map(x=>'<article class="metric"><span>'+x[0]+'</span><strong>'+x[1]+'</strong><small>'+x[2]+'</small></article>').join("");
 $("portfolioTradeMeta").textContent="政策："+(labels[policy]||policy)+" · "+(s.resolved_trades??"—")+"/"+(s.trades_in_serial_cohort??"—")+" 組結算 · WIN "+pct(s.win_rate_pct)+" · 起始 NAV "+money(nav)+" · 固定一組一組回放";
 rows.innerHTML=m.levels.map(x=>'<tr><td>−'+x.level+'%</td><td>'+x.count+'</td><td>'+x.perYear.toFixed(2)+'</td><td>'+(x.eventYears.length?x.eventYears.join(", "):"—")+' ('+x.years+'/'+x.allYears+' 年)</td><td>'+(x.medianGap===null?"—":Math.round(x.medianGap))+'</td></tr>').join("");
 const vals=m.pts.map(x=>x.eq),lo=Math.min(...vals),hi=Math.max(...vals),range=hi-lo||1,w=920,h=180,pad=14;
 let path="",open=false;
 for(let i=0;i<m.series.length;i++){
  const v=m.series[i];
  if(v===null||v===undefined||!Number.isFinite(Number(v))){open=false;continue;}
  const yv=nav+Number(v),x=pad+(i/Math.max(1,m.series.length-1))*(w-pad*2),y=h-pad-((yv-lo)/range)*(h-pad*2);
  path+=(open?" L ":" M ")+x.toFixed(2)+" "+y.toFixed(2);open=true;
 }
 chart.innerHTML='<svg viewBox="0 0 '+w+' '+h+'" role="img" aria-label="歷史逐日淨值估值"><line x1="'+pad+'" y1="'+(h-pad)+'" x2="'+(w-pad)+'" y2="'+(h-pad)+'" stroke="#30425b"/><path d="'+path+'" fill="none" stroke="#71b8ff" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/></svg><div class="chart-legend"><span>'+m.dates[0]+'</span><span>最低可觀察淨值 '+money(m.minEquity)+'</span><span>'+m.dates[m.dates.length-1]+'</span></div>';
 note.textContent="這是使用歷史 EOD 報價方向估算的逐日淨清算曲線，不是實際成交。缺失估值保持未知、不補值；缺口內可能漏掉更深回撤。每個歷史 episode 固定 1 單位、非重疊、不複利，也沒有券商保證金、指派或強制平倉模擬。若尾部風險限制的可用組數為 0，部署仍然 BLOCKED。";
}

function renderProfitWarningEvidence(){
 const el=$("profitWarningEvidence");
 if(!el)return;
 el.textContent="";
 const points=(data&&data.events&&data.events.profitThresholds)||{};
 const dollar=String.fromCharCode(36);
 const addLine=(card,value)=>{
  const line=document.createElement("div");
  line.textContent=value;
  card.appendChild(line);
 };
 const forwardText=(record,horizon)=>{
  const f=record&&record.forwardIfOriginal1x5Held&&record.forwardIfOriginal1x5Held[String(horizon)];
  if(!f)return String(horizon)+"-session forward: pending.";
  const med=f.medianPnlChangeUsd===null?"—":money(f.medianPnlChangeUsd);
  const giveback=f.fractionGivebackGeHalfTargetPct===null?"—":pct(f.fractionGivebackGeHalfTargetPct);
  return String(horizon)+"-session forward (original 1:5 hypothetically held): n="+f.n+
   "; median P&L change "+med+"; at-least-half-target giveback "+giveback+".";
 };
 ["800","1000"].forEach((key)=>{
  const p=points[key];
  const card=document.createElement("div");
  card.className="alert "+(!p||p.sampleStatus==="INSUFFICIENT_SMALL_TRIGGER_COHORT"?"warn":"good");
  const title=document.createElement("strong");
  title.textContent="Fixed target "+dollar+key+" policy — research only";
  card.appendChild(title);
  if(!p){
   addLine(card,"PENDING: awaiting direct replay of the same 62 episodes; no interpolation from adjacent targets.");
   el.appendChild(card);
   return;
  }
  addLine(card,"Counterfactual first EOD mark hit: "+p.counterfactualFirstMarkHitCount+"/62. Actual policy triggers: "+p.actualPolicyTriggerCount+"/62 ("+pct(p.actualPolicyTriggerPct)+"). Successful closes: "+p.successfulExitActionCount+"/"+p.actualPolicyTriggerCount+". Successful action on the next observed session: "+p.successfulActionOnNextObservedSessionCount+".");
  addLine(card,forwardText(p,5));
  addLine(card,forwardText(p,10));
  addLine(card,"Median trigger age: "+(p.medianTriggerAgeSessions===null?"—":p.medianTriggerAgeSessions)+" sessions. Median signal-to-action delay: "+(p.medianSignalToActionSessions===null?"—":p.medianSignalToActionSessions)+" sessions. "+p.sampleStatus+".");
  el.appendChild(card);
 });
 const caveat=document.createElement("p");
 caveat.className="subtle";
 caveat.textContent="First EOD mark hit counts the untouched original 1:5 hold path. Actual policy triggers account for DTE ≤ 7 fallback sequencing and pending actions. The 5/10-session marks assume continued holding of the original 1:5 after the signal; they are not realized post-exit returns. EOD quote marks are not confirmed fills.";
 el.appendChild(caveat);
}

function renderQuickEvidence(nav,dir,n,profitPct){
 const history=$("historyAnswer"),targetEl=$("targetEvidence");
 if(!history||!targetEl)return;
 history.textContent="";
 targetEl.textContent="";
 const policyId=$("curvePolicy")?.value||"BASE_DTE7_CLOSE_SHORT_RISK";
 const row=L.matchedHistory(dir,n,data,policyId);
 const addChip=(parent,label,value,detail)=>{
  const chip=document.createElement("div");chip.className="vol-chip";
  const l=document.createElement("span");l.textContent=label;
  const v=document.createElement("strong");v.textContent=value;
  const d=document.createElement("small");d.textContent=detail||"";
  chip.append(l,v,d);parent.appendChild(chip);
 };
 if(!row){
  const box=document.createElement("div");box.className="alert warn";
  const title=document.createElement("strong");title.textContent="沒有可直接引用的歷史勝率";
  const body=document.createElement("div");body.textContent="目前設定 "+(dir==="SHORT_HEAVY"?"LONG PUT 1 : SHORT PUT "+n:"LONG PUT "+n+" : SHORT PUT 1")+"，但保存的 62 組期權 episode 只直接驗證 LONG PUT 1 : SHORT PUT 5。其他方向／N 不複製勝率、MaxDD 或退出觸發率。";
  box.append(title,body);history.appendChild(box);
 }else{
  const m=portfolioStats(nav,policyId);
  const title=document.createElement("p");title.className="subtle";
  title.textContent="直接證據：LONG PUT 1 : SHORT PUT 5 · 所選政策「"+(labels[policyId]||policyId)+"」· 62 組非重疊歷史 episode（2018-03-01 至 2025-12-15）。以下累計損益固定每次一組、不複利。";
  history.appendChild(title);
  addChip(history,"歷史 WIN",pct(row.winRatePct),row.resolved+"/62 已結算");
  addChip(history,"累計淨損益",money(row.netPnlUsd),"固定一組、不複利");
  addChip(history,"逐日 MaxDD",m?pct(m.maxPct):"PENDING",m?m.maxPeakDate+" → "+m.maxTroughDate:"沒有曲線");
  if(m){
   const rates=document.createElement("p");rates.className="subtle";
   rates.textContent="策略 MaxDD 週期年平均（依目前 NAV 與所選政策）："+m.levels.filter(x=>[3,5,10,20,30].includes(x.level)).map(x=>"−"+x.level+"%： "+x.perYear.toFixed(2)+"/年（"+x.count+" 次）").join("；")+". 明細見下方 MaxDD 分級表；缺失估值可能令回撤被低估。";
   history.appendChild(rates);
  }
 }
 const amount=nav*profitPct/100,match=L.profitTargetPolicy(amount,data);
 const box=document.createElement("div");box.className="alert "+(match?"good":"warn");
 const title=document.createElement("strong");title.textContent="目前獲利預警："+money(amount)+"（"+Number(profitPct).toFixed(2)+"% NAV）";
 const body=document.createElement("div");
 if(match){
  const p=match.policy,study=data.events?.profitThresholds?.[String(match.targetUsd)],m=portfolioStats(nav,p.id);
  let details="直接重播的同額固定目標 +$"+match.targetUsd+"：WIN "+pct(p.winRatePct)+"；淨損益 "+money(p.netPnlUsd)+"；政策觸發 "+p.triggerCount+"/62；DTE ≤ 7 fallback "+p.fallbackCount+"/62。";
  if(m)details+=" 以目前輸入 NAV 重算的固定一組序列 MaxDD "+pct(m.maxPct)+"（"+m.maxPeakDate+" → "+m.maxTroughDate+"）。";
  if(study)details+=" 原倉反事實 EOD first-hit "+study.counterfactualFirstMarkHitCount+"/62，5 日內 "+study.counterfactualFirstHitWithin5Sessions+"/62；這不是退出後已實現收益。";
  else details+=" 此目標的逐日 first-hit 時間分布未單獨保存，不借用其他金額的時間結果。";
  details+=" 這是同額歷史對照，不是最佳獲利百分比；觸線只提示人工覆核。";
  body.textContent=details;
 }else{
  body.textContent="此 NAV 百分比換算出的金額，並非本批直接重播的固定目標（$500、$800、$1,000、$2,000）。不插值、不借用鄰近目標的勝率／MaxDD；當前門檻只作人工提醒。可在下方政策比較表檢視已實際重播的目標。";
 }
 box.append(title,body);targetEl.appendChild(box);
}

function draw(){
 const nav=input("nav")||0,dir=$("direction").value,n=input("ratioN")||5,riskPct=input("riskPct")||1,profitPct=input("profitPct")||1;
 const pnl=input("currentPnl"),age=input("age"),dte=input("dte"),rv=input("rv20"),horizon=input("horizon")||5;
 const activePolicyId=$("curvePolicy")?.value||"BASE_DTE7_CLOSE_SHORT_RISK";
 const ratio=L.ratioInfo(nav,dir,n,riskPct,data),matched=L.matchedHistory(dir,n,data,activePolicyId);
 $("winRate").textContent=matched?pct(matched.winRatePct):"PENDING";
 $("winRate").className=matched?"good":"warn";
 $("winRateSub").textContent=matched?"所選政策 · "+matched.resolved+"/62 組已結算 · 觸發 "+matched.triggerCount+"/62":"此方向／N 未有可在這裡直接引用的單位勝率；不沿用 1:5 數字";
 $("profitTarget").textContent=money(nav*profitPct/100);
 $("profitTargetSub").textContent=Number(profitPct).toFixed(2)+"% NAV；候選預警線，非經證實最佳退出";
 $("tailLoss").textContent=money(ratio.lossUsd);
 $("tailLossSub").textContent=(ratio.lossPctOfNav===null?"—":pct(ratio.lossPctOfNav))+" of current NAV · terminal scenario";
 $("units").textContent=ratio.unitsByTerminalTail===null?"PENDING":String(ratio.unitsByTerminalTail);
 $("units").className=ratio.unitsByTerminalTail===0?"bad":"";
 $("unitsSub").textContent="按所選尾部預算的整組算術上限；非可執行容量";
 $("inputSummary").textContent="NAV "+money(nav)+" · "+(dir==="SHORT_HEAVY"?"LONG 1 : SHORT "+n:"LONG "+n+" : SHORT 1")+" · 尾部預算 "+money(ratio.budgetUsd)+" ("+riskPct+"% NAV) · 獲利提醒 "+money(nav*profitPct/100)+" ("+profitPct+"% NAV)"+(rv===null?" · 現時 RV20 未輸入":" · 當前 RV20 "+pct(rv));
 $("alerts").innerHTML=L.alerts({nav:nav,direction:dir,n:n,riskPct:riskPct,profitPct:profitPct,currentPnl:pnl,age:age,dte:dte,rv20:rv,horizon:horizon},data).map(a=>'<div class="alert '+a.tone+'"><strong>'+a.title+'</strong><div>'+a.body+'</div></div>').join("");
 $("riskVerdict").innerHTML=ratio.unitsByTerminalTail===0?'<strong class="bad">TAIL-BUDGET BLOCK：</strong> 在此風險預算下，歷史觀察的最差終端損失不容納一組。這不是對券商保證金的估算，也不表示任何正股或期權現倉已被風險解除。':'<strong>容量解讀：</strong> 數字只按觀察終端損失與 NAV 百分比推算，尚未驗證保證金、途中清算及報價深度；不可當作下單數量。';
 $("policyNote").textContent="成本假設：每腿每邊滑點 $0.05 + 每張每邊佣金 $0.65。數據截止 "+data.metadata.optionSourceEnd+"；缺失 mark-session 不補值。$800 是固定金額歷史政策，只在 $80,000 NAV 下等於 +1%；現時 NAV 的百分比提醒與固定金額回測分開。原倉反事實 +$1,000 EOD first-hit "+data.events.plus1000Events+" 組（5 日內 "+data.events.plus1000Within5Sessions+"、5 日後 "+data.events.plus1000After5Sessions+"），不等於實際 policy trigger。";
 renderProfitWarningEvidence();
 $("policyRows").innerHTML=data.policies.map(p=>{
   const target=p.id.indexOf("500")>=0?"$500":p.id.indexOf("800")>=0?"$800":p.id.indexOf("1000")>=0?"$1,000":p.id.indexOf("2000")>=0?"$2,000":"—";
   const targetPct=target==="—"?"—":pct(Number(target.replace(/[$,]/g,""))/nav*100);
   return '<tr><td>'+ (labels[p.id]||p.id) +'<div class="subtle">'+target+(targetPct!=="—"?" · "+targetPct+" 當前 NAV":"")+'</div></td><td>'+p.triggerCount+'/62 · '+pct(p.triggerPct)+'</td><td class="'+(p.winRatePct>=90?"good":p.winRatePct<80?"warn":"")+'">'+pct(p.winRatePct)+'</td><td class="'+(p.netPnlUsd<0?"bad":"")+'">'+money(p.netPnlUsd)+'</td><td class="'+(p.worstTradeUsd<0?"bad":"")+'">'+money(p.worstTradeUsd)+'</td><td>'+Number(p.profitFactor).toFixed(2)+'</td></tr>';
 }).join("");
 const v=L.volRow(data,rv,horizon),sel=v.selected,all=v.all;
 $("volStateBadge").textContent=stateName(v.state);
 $("volSummary").innerHTML=sel&&all?[
   ["目前組別 P(QQQ 跌 ≥5%)",pct(sel.down5Pct),sel.n+" samples"],
   ["ALL 基準 P(QQQ 跌 ≥5%)",pct(all.down5Pct),all.n+" samples"],
   ["最差 5%分位回報",pct(sel.p05ReturnPct),horizon+" sessions"],
   ["相對 ALL",all.down5Pct>0?(sel.down5Pct/all.down5Pct).toFixed(2)+"×":"—","underlying path only"]
 ].map(x=>'<div class="vol-chip"><span>'+x[0]+'</span><strong>'+x[1]+'</strong><small>'+x[2]+'</small></div>').join(""):"<div class='empty'>此波動／期限組合沒有歷史樣本。</div>";
 $("volRows").innerHTML=data.probabilities.filter(r=>r.state===v.state&&[5,10,20,45].includes(r.horizonSessions)).map(r=>'<tr class="'+(r.horizonSessions===Number(horizon)?"highlight":"")+'"><td>'+r.horizonSessions+'</td><td>'+stateName(r.state)+'</td><td>'+r.n.toLocaleString("en-US")+'</td><td>'+pct(r.down3Pct)+'</td><td>'+pct(r.down5Pct)+'</td><td>'+pct(r.down10Pct)+'</td><td>'+pct(r.down5WilsonLowPct)+'–'+pct(r.down5WilsonHighPct)+'</td><td>'+pct(r.p05ReturnPct)+'</td></tr>').join("");
 const dd=data.drawdown;
 $("ddSummary").innerHTML=[
  ["資料跨度",dd.years.toFixed(2)+" 年",data.metadata.sourceStart+" → "+data.metadata.sourceEnd],
  ["樣本內最大 QQQ 回撤",pct(dd.maxObservedDrawdownPct), "正股 peak-to-trough"],
  ["價位觀察",data.metadata.priceRows.toLocaleString("en-US")+" closes","不是期權損益曲線"]
 ].map(x=>'<div class="vol-chip"><span>'+x[0]+'</span><strong>'+x[1]+'</strong><small>'+x[2]+'</small></div>').join("");
 $("ddRows").innerHTML=dd.levels.map(r=>'<tr><td>−'+r.levelPct+'%</td><td>'+r.episodes+'</td><td>'+r.eventsPerYear.toFixed(2)+'</td><td>'+r.yearsWithEvent+'/'+dd.calendarYears+'</td><td>'+(r.medianGapSessions===null?"—":r.medianGapSessions)+'</td></tr>').join("");
 $("ddCaveat").textContent="目前不能從這 62 組非重疊固定單位交易直接聲稱策略帳戶 MaxDD 的平均發生率；它需要連續日度持倉 MTM、再入場、資金複利、成本與強制清算規則。上表是 QQQ 正股回撤代理。";
 const tailRows=(dir==="SHORT_HEAVY"?data.tailLossShortHeavy:data.tailLossLongHeavy);
 $("tailRows").innerHTML=tailRows.map(r=>{
  const lossPct=r.worstUsd/nav*100,units=Math.max(0,Math.floor((nav*riskPct/100)/r.worstUsd));
  return '<tr class="'+(r.n===Number(n)?"highlight":"")+'"><td>'+(dir==="SHORT_HEAVY"?"LONG 1 : SHORT N":"LONG N : SHORT 1")+'</td><td>'+r.n+'</td><td>'+money(r.medianUsd)+'</td><td>'+money(r.p95Usd)+'</td><td>'+money(r.worstUsd)+'</td><td class="'+(lossPct>100?"bad":"")+'">'+pct(lossPct)+'</td><td class="'+(units===0?"bad":"")+'">'+units+'</td></tr>';
 }).join("");
 renderPortfolio(nav);
 renderQuickEvidence(nav,dir,n,profitPct);
 if(dir==="SHORT_HEAVY"&&n===1)$("inputSummary").textContent+=" · N=1 兩方向的 legs 數相同，但須確認同一合約與腿方向後才可視作同一結構。";
}
(async function init(){
 try{
  const r=await fetch("data.json",{cache:"no-store"});if(!r.ok)throw new Error("data.json load failed: "+r.status);data=await r.json();const cr=await fetch("portfolio_curve.json",{cache:"no-store"});if(cr.ok)curveData=await cr.json();
  ["nav","direction","ratioN","riskPct","profitPct","currentPnl","age","dte","rv20","horizon","curvePolicy"].forEach(id=>$(id).addEventListener("input",draw));
  draw();
 }catch(e){$("alerts").innerHTML='<div class="alert bad"><strong>DATA LOAD ERROR</strong><div>'+String(e.message||e)+'</div>請從 RUN.cmd 啟動本機 HTTP Server，而非直接打開 HTML 檔案。</div>';}
})();
})();
