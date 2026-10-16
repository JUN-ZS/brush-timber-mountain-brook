(function(root){
"use strict";
function num(x){if(x===null||x===undefined||x==="")return null;var n=Number(x);return Number.isFinite(n)?n:null;}
function ratioInfo(nav,dir,n,riskPct,data){
  var key=dir==="LONG_HEAVY"?"tailLossLongHeavy":"tailLossShortHeavy";
  var row=(data[key]||[]).find(function(x){return Number(x.n)===Number(n);});
  var loss=row?num(row.worstUsd):null,budget=num(nav)!==null&&num(riskPct)!==null?num(nav)*num(riskPct)/100:null;
  var units=loss!==null&&budget!==null&&loss>0?Math.max(0,Math.floor(budget/loss)):null;
  return {row:row||null,lossUsd:loss,budgetUsd:budget,lossPctOfNav:loss!==null&&num(nav)>0?loss/num(nav)*100:null,unitsByTerminalTail:units};
}
function matchedHistory(dir,n,data,policyId){
  if(dir!=="SHORT_HEAVY"||Number(n)!==5)return null;
  var policies=data.policies||[];
  return (policyId&&policies.find(function(p){return p.id===policyId;}))||
    policies.find(function(p){return p.id==="BASE_DTE7_CLOSE_SHORT_RISK";})||null;
}
function profitTargetPolicy(targetUsd,data){
  var target=num(targetUsd);
  if(target===null)return null;
  var levels=[500,800,1000,2000];
  var level=levels.find(function(x){return Math.abs(target-x)<=0.5;});
  if(level===undefined)return null;
  var row=(data.policies||[]).find(function(p){return p.id==="TP_USD_"+level+"_CLOSE_SHORT_RISK";});
  return row?{targetUsd:level,policy:row}:null;
}
function volState(rv20){var v=num(rv20);if(v===null)return "ALL";if(v<15)return "RV20_LT15";if(v<25)return "RV20_15_25";if(v<35)return "RV20_25_35";return "RV20_GTE35";}
function volRow(data,rv20,horizon){var state=volState(rv20),h=Number(horizon),rows=data.probabilities||[];return {state:state,selected:rows.find(function(x){return x.state===state&&x.horizonSessions===h;})||null,all:rows.find(function(x){return x.state==="ALL"&&x.horizonSessions===h;})||null};}
function volStress(data,rv20,horizon){
  var rv=num(rv20),v=volRow(data,rv20,horizon),s=v.selected,a=v.all;
  var r5=s&&a&&num(a.down5Pct)>0?num(s.down5Pct)/num(a.down5Pct):null;
  var r10=s&&a&&num(a.down10Pct)>0?num(s.down10Pct)/num(a.down10Pct):null;
  var down5=rv!==null&&rv>=25&&r5!==null&&r5>=1.5;
  var down10=rv!==null&&rv>=25&&r10!==null&&r10>=1.5;
  return {state:v.state,selected:s,all:a,down5Ratio:r5,down10Ratio:r10,down5Elevated:down5,down10Elevated:down10,elevated:down5||down10};
}
function drawdownCycleStats(dates,points){
  if(!Array.isArray(dates)||!dates.length||!Array.isArray(points)||!points.length)return {spanYears:0,levels:[]};
  var cycles=[],cp=points[0],cw=0,ct=points[0];
  for(var i=1;i<points.length;i++){
    var p=points[i],d=cp.eq>0?(p.eq/cp.eq-1)*100:0;
    if(p.eq>=cp.eq){cycles.push({worst:cw,trough:ct.date,index:ct.i});cp=p;cw=0;ct=p;}
    else if(d<cw){cw=d;ct=p;}
  }
  cycles.push({worst:cw,trough:ct.date,index:ct.i});
  var span=(Date.parse(dates[dates.length-1])-Date.parse(dates[0]))/(365.2425*86400000);
  var allYears=Array.from(new Set(dates.map(function(x){return String(x).slice(0,4);}))).sort();
  var levels=[3,5,10,15,20,25,30].map(function(level){
    var hit=cycles.filter(function(x){return x.worst<=-level+1e-9;}).sort(function(a,b){return a.index-b.index;});
    var gaps=hit.slice(1).map(function(x,i){return x.index-hit[i].index;}).sort(function(a,b){return a-b;});
    var eventYears=Array.from(new Set(hit.map(function(x){return x.trough.slice(0,4);}))).sort();
    return {level:level,count:hit.length,perYear:span>0?hit.length/span:0,years:eventYears.length,allYears:allYears.length,eventYears:eventYears,
      medianGap:gaps.length?(gaps.length%2?gaps[(gaps.length-1)/2]:(gaps[gaps.length/2-1]+gaps[gaps.length/2])/2):null};
  });
  return {spanYears:span,levels:levels};
}
function alerts(input,data){
  var out=[],nav=num(input.nav),pnl=num(input.currentPnl),age=num(input.age),dte=num(input.dte),rv=num(input.rv20);
  var target=nav!==null&&num(input.profitPct)!==null?nav*num(input.profitPct)/100:null;
  var ratio=ratioInfo(nav,input.direction,input.n,input.riskPct,data);
  var targetMatch=profitTargetPolicy(target,data);
  var vol=volStress(data,rv,input.horizon);
  if(ratio.unitsByTerminalTail===0)out.push({tone:"bad",title:"尾部風險預算：BLOCK（終端損失算術）",body:"目前風險預算 "+money(ratio.budgetUsd)+"，低於一組最差觀察到期尾部損失 "+money(ratio.lossUsd)+"；按此單一限制整組數為 0。這仍未包含券商保證金、途中強平與實際成交限制。"});
  if(pnl!==null&&target!==null&&pnl>=target){
    var targetEvidence=targetMatch?
      "同額歷史政策 +"+money(targetMatch.targetUsd)+"：WIN "+pct(targetMatch.policy.winRatePct)+"、淨損益 "+money(targetMatch.policy.netPnlUsd)+"、政策觸發 "+targetMatch.policy.triggerCount+"/62。"+
        " 這是固定每次一組的歷史政策摘要，不表示最佳退出點。":
      "這個金額不是本批直接重播的固定獲利目標（$500/$800/$1,000/$2,000）；不由鄰近目標推算勝率或退出成效。";
    out.push({tone:"warn",title:"獲利 BAR 已達：需要人工覆核",body:"輸入的淨清算估算 P&L 已到 "+money(target)+"（"+Number(input.profitPct).toFixed(2)+"% NAV）。"+targetEvidence+" 核對各腿按清算方向的 Bid/Ask、報價時間和成本；這是提醒，不是自動平倉規則。"});
  }
  if(age!==null&&age>=20){
    if(pnl===null)out.push({tone:"warn",title:"時間警示：持有 ≥20 日但未輸入 P&L",body:"需要先核對當前淨清算估值，不能只憑持倉日數推斷盈利或虧損。研究中的第 20 日非正 P&L 政策觸發 10/62（16.13%），前瞻樣本有限。"});
    else if(pnl<=0)out.push({tone:"bad",title:"時間警示：持有 ≥20 日且未盈利",body:"目前 P&L 非正。歷史第 20 日非正 P&L 退出政策觸發 10/62（16.13%）；這是比較項，不是充分樣本證明的必然退出規則。"});
    else out.push({tone:"warn",title:"時間警示：持有 ≥20 日仍有盈利",body:"即使當前盈利，也請覆核剩餘期限、短 Put 的 Gamma／指派風險與獲利回吐；歷史第 20 日規則的前瞻證據不足，不可只因持倉有利潤而自動續抱。"});
  }
  if(dte!==null&&dte<=7)out.push({tone:"bad",title:"短倉期限警示：DTE ≤ 7",body:"既有 1:5 回放把 DTE ≤ 7 當共同短倉風險處理；需人工核對短倉回補報價、流動性與保證金。沒有有效期權鏈／保證金證據便不自動下單。"});
  if(pnl!==null&&target!==null&&pnl>=target&&age!==null&&age<=5){
    var sameTargetStudy=targetMatch&&data.events&&data.events.profitThresholds&&data.events.profitThresholds[String(targetMatch.targetUsd)];
    if(sameTargetStudy){
      out.push({tone:"warn",title:"早段獲利觸線：對照同額歷史樣本",body:"同額 +$"+targetMatch.targetUsd+" 歷史研究的原倉反事實 EOD first-hit 為 "+sameTargetStudy.counterfactualFirstMarkHitCount+"/62，其中 5 個交易日內 "+sameTargetStudy.counterfactualFirstHitWithin5Sessions+" 組；實際政策觸發 "+sameTargetStudy.actualPolicyTriggerCount+"/62。這不是平倉後的已實現回報。"});
    }else if(targetMatch){
      out.push({tone:"warn",title:"早段獲利觸線：時間證據未直接保存",body:"此金額可對應同額固定政策，但目前保存的分日 first-hit 分析沒有這個目標；不借用 $800／$1,000 的時間數字，先人工核對報價、DTE 與短倉風險。"});
    }else{
      out.push({tone:"warn",title:"早段獲利觸線：沒有同額歷史命中基準",body:"目前動態門檻 "+money(target)+" 不等於已直接重播的固定獲利門檻。沒有足夠證據可判定它在 5 日內是否異常；這只是人工覆核提醒。"});
    }
  }
  if(vol.elevated){
    var reasons=[];
    if(vol.down5Elevated)reasons.push("跌 ≥5% 頻率 "+vol.down5Ratio.toFixed(2)+"×");
    if(vol.down10Elevated)reasons.push("跌 ≥10% 頻率 "+vol.down10Ratio.toFixed(2)+"×");
    out.push({tone:"warn",title:"波動警示：指定期限的正股下跌頻率升高",body:"RV20="+pct(rv)+"（"+vol.state+"），"+input.horizon+" 個交易日歷史樣本 N="+vol.selected.n+"。"+reasons.join("；")+"。本組 P(跌≥5%) "+pct(vol.selected.down5Pct)+"，ALL "+pct(vol.all.down5Pct)+"；P(跌≥10%) "+pct(vol.selected.down10Pct)+"，ALL "+pct(vol.all.down10Pct)+"。此為 QQQ 正股路徑頻率，不是 Put Ratio 虧損概率。"});
  }
  if(vol.elevated&&(pnl!==null&&target!==null&&pnl>=target||age!==null&&age>=20||dte!==null&&dte<=7)){
    var triggers=[];
    if(pnl!==null&&target!==null&&pnl>=target)triggers.push("獲利預警線已到");
    if(age!==null&&age>=20)triggers.push("持倉已達 20 日");
    if(dte!==null&&dte<=7)triggers.push("DTE ≤ 7");
    out.push({tone:"bad",title:"時間／期限 × 波動共同警示：優先人工覆核",body:triggers.join(" + ")+"；目前 RV20="+pct(rv)+" 且 "+input.horizon+" 日下跌頻率高於歷史 ALL 基準。先重新估算整組淨清算 P&L、短 Put 回補成本與尾部風險；本提示不代表自動平倉。"});
  }
  if(!out.length)out.push({tone:"good",title:"沒有輸入條件觸發額外提醒",body:"不代表策略安全或可執行。仍需核對合約、實際 Bid/Ask、時間戳、保證金與尾部損失。"});
  return out;
}
function money(x){var v=num(x);return v===null?"—":(v<0?"−$":"$")+Math.abs(v).toLocaleString("en-US",{minimumFractionDigits:0,maximumFractionDigits:2});}
function pct(x,d){var v=num(x);return v===null?"—":v.toFixed(d===undefined?2:d)+"%";}
var api={num:num,ratioInfo:ratioInfo,matchedHistory:matchedHistory,profitTargetPolicy:profitTargetPolicy,volState:volState,volRow:volRow,volStress:volStress,drawdownCycleStats:drawdownCycleStats,alerts:alerts,money:money,pct:pct};
if(typeof module!=="undefined"&&module.exports)module.exports=api;else root.PutRatioLogic=api;
})(typeof window!=="undefined"?window:this);
