(async function(){
"use strict";
const $=id=>document.getElementById(id), L=window.PutRatioLogic;
const labels={
 BASE_DTE7_CLOSE_SHORT_RISK:"基準：DTE ≤ 7 短倉風險處理",
 TP_USD_500_CLOSE_SHORT_RISK:"獲利 +$500：全平短倉風險",
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
let data;
const money=L.money,pct=L.pct;
function input(id){return L.num($(id).value);}
function stateName(s){return ({ALL:"全部歷史樣本",RV20_LT15:"RV20 < 15%",RV20_15_25:"RV20 15–25%",RV20_25_35:"RV20 25–35%",RV20_GTE35:"RV20 ≥ 35%"}[s]||s);}
function draw(){
 const nav=input("nav")||0,dir=$("direction").value,n=input("ratioN")||5,riskPct=input("riskPct")||1,profitPct=input("profitPct")||1;
 const pnl=input("currentPnl"),age=input("age"),dte=input("dte"),rv=input("rv20"),horizon=input("horizon")||5;
 const ratio=L.ratioInfo(nav,dir,n,riskPct,data),matched=L.matchedHistory(dir,n,data);
 $("winRate").textContent=matched?pct(matched.winRatePct):"PENDING";
 $("winRate").className=matched?"good":"warn";
 $("winRateSub").textContent=matched?"62 組直接歷史回放 · "+matched.resolved+"/62 已結算":"此方向／N 未有可在這裡直接引用的單位勝率；不沿用 1:5 數字";
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
 $("policyNote").textContent="成本假設：每腿每邊滑點 $0.05 + 每張每邊佣金 $0.65。數據截止 "+data.metadata.optionSourceEnd+"；12 個缺失 mark-session 不補值。+1,000 首次 EOD 達標共 "+data.events.plus1000Events+" 組，其中 5 日內 "+data.events.plus1000Within5Sessions+" 組、5 日後 "+data.events.plus1000After5Sessions+" 組。";
 $("policyRows").innerHTML=data.policies.map(p=>{
   const target=p.id.indexOf("500")>=0?"$500":p.id.indexOf("1000")>=0?"$1,000":p.id.indexOf("2000")>=0?"$2,000":"—";
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
 if(dir==="SHORT_HEAVY"&&n===1)$("inputSummary").textContent+=" · N=1 兩方向的 legs 數相同，但須確認同一合約與腿方向後才可視作同一結構。";
}
(async function init(){
 try{
  const r=await fetch("data.json",{cache:"no-store"});if(!r.ok)throw new Error("data.json load failed: "+r.status);data=await r.json();
  ["nav","direction","ratioN","riskPct","profitPct","currentPnl","age","dte","rv20","horizon"].forEach(id=>$(id).addEventListener("input",draw));
  draw();
 }catch(e){$("alerts").innerHTML='<div class="alert bad"><strong>DATA LOAD ERROR</strong><div>'+String(e.message||e)+'</div>請從 RUN.cmd 啟動本機 HTTP Server，而非直接打開 HTML 檔案。</div>';}
})();
})();
