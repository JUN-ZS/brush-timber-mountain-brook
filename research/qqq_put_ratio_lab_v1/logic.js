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
function matchedHistory(dir,n,data){return dir==="SHORT_HEAVY"&&Number(n)===5?(data.policies||[]).find(function(p){return p.id==="BASE_DTE7_CLOSE_SHORT_RISK";})||null:null;}
function volState(rv20){var v=num(rv20);if(v===null)return "ALL";if(v<15)return "RV20_LT15";if(v<25)return "RV20_15_25";if(v<35)return "RV20_25_35";return "RV20_GTE35";}
function volRow(data,rv20,horizon){var state=volState(rv20),h=Number(horizon),rows=data.probabilities||[];return {state:state,selected:rows.find(function(x){return x.state===state&&x.horizonSessions===h;})||null,all:rows.find(function(x){return x.state==="ALL"&&x.horizonSessions===h;})||null};}
function alerts(input,data){
  var out=[],nav=num(input.nav),pnl=num(input.currentPnl),age=num(input.age),dte=num(input.dte),rv=num(input.rv20);
  var target=nav!==null&&num(input.profitPct)!==null?nav*num(input.profitPct)/100:null;
  var ratio=ratioInfo(nav,input.direction,input.n,input.riskPct,data);
  if(ratio.unitsByTerminalTail===0)out.push({tone:"bad",title:"尾部風險預算：BLOCK（終端損失算術）",body:"目前風險預算 "+money(ratio.budgetUsd)+"，低於一組最差觀察到期尾部損失 "+money(ratio.lossUsd)+"；按此單一限制整組數為 0。這仍未包含券商保證金、途中強平與實際成交限制。"});
  if(pnl!==null&&target!==null&&pnl>=target)out.push({tone:"warn",title:"獲利 BAR 已達：需要人工覆核",body:"輸入的淨清算估算 P&L 已到 "+money(target)+"（"+Number(input.profitPct).toFixed(2)+"% NAV）。核對各腿按清算方向的 Bid/Ask、報價時間和成本；這是提醒，不是自動平倉規則。"});
  if(pnl!==null&&target!==null&&pnl<0&&age!==null&&age>=20)out.push({tone:"bad",title:"時間警示：持有 ≥20 日且未盈利",body:"直接歷史研究中 10/62（16.13%）交易在第 20 日觸發非正 P&L 規則；該條件前瞻樣本只有 "+data.events.day20NonpositiveForward5N+" 組，證據不足以指定必然退出。"});
  else if(age!==null&&age>=20)out.push({tone:"warn",title:"時間警示：已到第 20 個交易日",body:"對照歷史第 20 日的淨清算估值；目前 P&L 未輸入／未驗證，所以不能判定是否觸發非正 P&L 條件。"});
  if(dte!==null&&dte<=7)out.push({tone:"bad",title:"短倉期限警示：DTE ≤ 7",body:"既有 1:5 回放把 DTE ≤ 7 當共同短倉風險處理；這是需人工核對風險的期限提示，沒有期權鏈／保證金證據便不自動下單。"});
  if(pnl!==null&&target!==null&&pnl>=target&&age!==null&&age<=5)out.push({tone:"warn",title:"早段獲利觸線：歷史對照有限",body:"研究中的固定 +$1,000 EOD 門檻在 62 組中 0 組於 5 個交易日內達到、9 組在第 5 日後達到。你的 NAV 百分比門檻可能不是 $1,000，所以這只是異常覆核提示，不是經驗證的同一規則。"});
  if(rv!==null&&rv>=25){var v=volRow(data,rv,input.horizon);if(v.selected&&v.all&&v.selected.down5Pct>=v.all.down5Pct*1.5)out.push({tone:"warn",title:"波動警示：歷史下跌頻率高於 ALL 基準",body:"RV20 分組下 "+input.horizon+" 日 QQQ 收市跌幅 ≥5% 的歷史頻率為 "+pct(v.selected.down5Pct)+"，ALL 基準為 "+pct(v.all.down5Pct)+"。這是正股路徑頻率，不是 Put Ratio 虧損概率。"});}
  if(!out.length)out.push({tone:"good",title:"沒有輸入條件觸發額外提醒",body:"不代表策略安全或可執行。仍需核對合約、實際 Bid/Ask、時間戳、保證金與尾部損失。"});
  return out;
}
function money(x){var v=num(x);return v===null?"—":(v<0?"−$":"$")+Math.abs(v).toLocaleString("en-US",{minimumFractionDigits:0,maximumFractionDigits:2});}
function pct(x,d){var v=num(x);return v===null?"—":v.toFixed(d===undefined?2:d)+"%";}
var api={num:num,ratioInfo:ratioInfo,matchedHistory:matchedHistory,volState:volState,volRow:volRow,alerts:alerts,money:money,pct:pct};
if(typeof module!=="undefined"&&module.exports)module.exports=api;else root.PutRatioLogic=api;
})(typeof window!=="undefined"?window:this);
