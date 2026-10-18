#!/usr/bin/env python3
"""Generate an offline interactive stock/bond glidepath dashboard from the full replay JSON."""
import argparse, csv, json, math
from pathlib import Path

FIELDS = ("bond_proxy","target_bond_conversion_pct_at_year10","timing_rule","cashflow_mode","rolling_windows","median_terminal_nav_usd","p05_terminal_nav_usd","p95_terminal_nav_usd","worst_terminal_nav_usd","median_time_weighted_cagr","p05_time_weighted_cagr","worst_time_weighted_cagr","median_daily_max_drawdown","worst_daily_max_drawdown","windows_below_initial_capital_at_year10","windows_with_withdrawal_shortfall","median_actual_withdrawals_usd","p95_withdrawal_shortfall_usd","median_investor_xirr")
ANNUAL_FIELDS = ("year","bond_proxy","target_bond_conversion_pct_at_year10","timing_rule","cashflow_mode","rolling_windows","median_nav_usd","p05_nav_usd","p95_nav_usd","worst_nav_usd","median_cumulative_twr_cagr","p05_cumulative_twr_cagr","median_year_twr","p05_year_twr","median_drawdown_to_date","worst_drawdown_to_date","windows_below_initial_capital","windows_with_withdrawal_shortfall","median_actual_withdrawals_usd","median_shortfall_usd","p95_shortfall_usd","median_target_bond_weight","median_target_stock_weight")
HISTOGRAM_METRICS = ("terminal_nav_usd", "time_weighted_cagr", "daily_max_drawdown", "withdrawal_shortfall_usd")
HTML = r'''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>股票轉債互動追蹤台</title><style>
*{box-sizing:border-box}body{margin:0;background:#f3f6fa;color:#1c2e43;font:15px/1.45 system-ui,Arial,sans-serif}main{max-width:1450px;margin:auto;padding:22px 16px}h1{font-size:clamp(24px,3vw,36px);margin:0 0 6px}h2{font-size:18px;margin:0 0 5px}.muted{color:#667b90}.note{padding:12px;background:#fff7e9;border:1px solid #efd9ad;border-radius:12px;font-size:13px;margin:15px 0}.controls,.grid{display:grid;gap:11px}.controls{grid-template-columns:repeat(4,minmax(140px,1fr))}.control,.panel,.metric{background:white;border:1px solid #dce4ed;border-radius:14px;padding:13px;min-width:0}.control label{display:block;font-size:12px;font-weight:750;color:#667b90;margin-bottom:7px}.control select{width:100%;padding:9px;border:1px solid #ccd6e1;border-radius:9px;background:white;font:inherit}input[type=range]{width:100%;accent-color:#203a59;cursor:ew-resize}.full{grid-column:span 2}.ends,.head{display:flex;justify-content:space-between;align-items:center;gap:8px}.ends{font-size:11px;color:#7a8b9c}.head output{font-weight:800;font-size:19px;color:#203a59}.metrics{display:grid;grid-template-columns:repeat(6,minmax(105px,1fr));gap:9px;margin:12px 0}.metric .k{font-size:12px;color:#667b90;min-height:28px}.metric .v{font-size:clamp(18px,2vw,25px);font-weight:820;margin:6px 0}.metric .s,.tiny{font-size:11px;color:#667b90}.grid{grid-template-columns:repeat(2,minmax(0,1fr));margin-top:13px}.panel p{font-size:12px;color:#667b90;margin:4px 0 9px}.chart{width:100%;height:auto;display:block}.chart [data-target],.chart [data-pick]{cursor:pointer}.chart [data-target]:hover,.chart [data-pick]:hover{filter:brightness(.72)}.legend{display:flex;gap:10px;flex-wrap:wrap;font-size:11px;color:#667b90;margin-top:5px}.legend i{display:inline-block;width:15px;height:3px;vertical-align:middle;margin-right:4px}.toolbar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;justify-content:flex-end;margin:12px 0}.action{border:1px solid #cbd5e1;border-radius:9px;background:#fff;color:#203a59;font:inherit;font-size:12px;font-weight:750;padding:9px 12px;cursor:pointer}.action:hover{background:#eef5fc}.barrow{display:grid;grid-template-columns:108px 1fr 85px;gap:8px;align-items:center;font-size:12px;margin:12px 0}.track{height:13px;background:#edf1f5;border-radius:99px;overflow:hidden}.fill{height:100%;border-radius:99px}.tablebox{overflow:auto}table{border-collapse:collapse;width:100%;font-size:12px}th,td{padding:8px;border-bottom:1px solid #e8edf3;text-align:right;white-space:nowrap}th:first-child,td:first-child{text-align:left}th{background:#f6f8fb;color:#526177}tr.active{background:#eef5fc}.foot{font-size:11px;color:#667b90;line-height:1.6;margin-top:17px}@media(max-width:1100px){.controls{grid-template-columns:repeat(2,1fr)}.metrics{grid-template-columns:repeat(3,1fr)}}@media(max-width:700px){main{padding:13px 8px}.grid{grid-template-columns:1fr}.metrics{grid-template-columns:repeat(2,1fr)}.full{grid-column:span 2}}
</style></head><body><main><h1>股票逐年轉債：互動追蹤台</h1><p class="muted">拖動 BAR 或點圖表資料點，資產、回報、回撤、提款缺口和配置路徑會同步變化。初始 NAV：US$100,000。</p><div class="note"><b>限制：</b>這是歷史 ETF 代理回測，不是預測，也不保本。157 個十年窗口互相重疊，不是未來機率。資料截至 2026-09-30，沒有 2000–2002 科技股崩跌。100%債券目標到第120個月才達成；ETF 不等於持有到期的個別國債／STRIPS。</div>
<section class="controls"><div class="control"><label for="bond">債券代理</label><select id="bond"><option>AGG</option><option>SHY</option><option>IEF</option><option>TLT</option></select></div><div class="control"><label for="timing">轉換時間規則</label><select id="timing"><option value="front_fast">加速前置：第2年半程</option><option value="front_loaded">前置：第3年半程</option><option value="linear">線性：每年等量</option><option value="mid_loaded">中段加速：S曲線</option><option value="back_loaded">後置：第5年開始</option><option value="back_late">延後：第7年開始</option></select></div><div class="control"><label for="flow">提款／投入模式</label><select id="flow"><option value="no_withdrawals">不提款</option><option value="delayed_stepup_example">延遲／升降提款＋投入</option><option value="monthly_withdrawal_500_usd_stress">每月提款 $500 壓力</option><option value="monthly_withdrawal_1000_usd_stress">每月提款 $1,000 壓力</option></select></div><div class="control"><label for="target">第10年目標轉債</label><div class="head"><span class="tiny">可拖動或點圖</span><output id="targetOut">60%</output></div><input id="target" type="range" min="30" max="100" step="10" value="60"><div class="ends"><span>30%</span><span>100%</span></div></div><div class="control"><label for="heatMetric">配置熱圖指標</label><select id="heatMetric"><option value="median_nav_usd">中位資產 NAV</option><option value="p05_nav_usd">P05 資產（下尾）</option><option value="median_cumulative_twr_cagr">累計年化回報</option><option value="median_drawdown_to_date">截至當年最大回撤</option><option value="windows_with_withdrawal_shortfall">提款缺口窗口數</option></select><p class="tiny">選指標後比較 8 個目標 × 6 條曲線；點格可切換其他圖表。</p></div><div class="control full"><label for="year">查看哪一年配置（拖動 BAR）</label><div class="head"><span class="tiny">查看當年股票／債券配置</span><output id="yearOut">第5年</output></div><input id="year" type="range" min="0" max="10" step="1" value="5"><div class="ends"><span>第0年</span><span>第10年</span></div><div id="allocation"></div></div><div class="control full"><label>目前選定情境</label><div class="head"><output id="label" style="font-size:15px">AGG · 60% · 線性</output><span id="nwin" class="tiny">157窗口</span></div><p id="flowNote" class="tiny">所有值是歷史統計，不是預測。</p></div></section><div class="toolbar"><span class="tiny">研究資料匯出（本地瀏覽器處理，不連外傳送）</span><button id="exportMatrix" class="action" type="button">匯出目前年份 48 組比較 CSV</button><button id="exportAnnual" class="action" type="button">匯出完整 8,448 筆年度 CSV</button></div>
<section id="metrics" class="metrics"></section><div class="grid">
<section class="panel"><h2>1. 所選年份資產</h2><p>所有曲線都依「查看第幾年」切換為該年觀測值；點資料點可同步更換目標和轉換曲線。</p><div id="wealth"></div><div id="leg1" class="legend"></div></section>
<section class="panel"><h2>2. 中位最大回撤</h2><p>顯示截至所選年份的最大回撤；提款本身不直接算成投資回撤。</p><div id="drawdown"></div><div id="leg2" class="legend"></div></section>
<section class="panel"><h2>3. 年化時間加權回報</h2><p>顯示由起點累計至所選年份的時間加權年化回報；第0年尚未形成回報期。</p><div id="returns"></div><div id="leg3" class="legend"></div></section>
<section class="panel"><h2>4. 提款缺口窗口數</h2><p>截至所選年份，157個歷史窗口中已出現提款缺口的窗口數；滑桿改變時本圖也更新。</p><div id="gaps"></div><div id="leg4" class="legend"></div></section>
<section class="panel"><h2>5. 回報 × 回撤互追圖</h2><p>每點為一個策略，套用目前選定的現金流模式；點擊後其他圖表同步追蹤。越左回撤越小，越高回報越高。</p><div id="frontier"></div><div class="legend">顏色＝AGG／SHY／IEF／TLT；○ 線性　□ 加速前置　△ 前置　◇ 中段S曲線　▽ 後置　＋ 延後</div></section>
<section class="panel"><h2>6. 同策略現金流對照</h2><p>固定目前策略，比較四種現金流假設的中位終值和提款缺口。</p><div id="flows"></div><p class="tiny">提款示例和月提款模式僅用作壓力測試。</p></section>
<section class="panel"><h2>7. 十年配置路徑</h2><p>拖動查看年份 BAR，比較六條轉換曲線和所選年份的股票／債券配置。</p><div id="glide"></div><div id="shares"></div></section>
<section class="panel"><h2>8. 同目標、不同時間規則</h2><p>固定目標、債券代理及現金流，逐行比較六種轉換規則。</p><div id="table" class="tablebox"></div></section>
<section class="panel"><h2>9. 十年資產分布帶</h2><p>所選策略逐年顯示 P05／中位數／P95 與最差窗口；陰影是重疊歷史窗口的分位範圍，不是預測信賴區間。點選年份可直接移動 BAR。</p><div id="fan"></div><div id="fanLegend" class="legend"></div></section>
<section class="panel"><h2>10. 回撤水下路徑</h2><p>追蹤最大回撤如何隨時間累積；同時顯示中位與最差歷史窗口，讓「典型回撤」與尾部風險不再混為一談。</p><div id="drawdownPath"></div><div id="riskLegend" class="legend"></div></section>
<section class="panel"><h2>11. 目標 × 時間規則熱圖</h2><p>固定債券代理、現金流與年份，橫向比較 8 個轉債目標、縱向比較 6 條轉換曲線。色階代表所選指標相對高低，不是策略優劣的通用排名。</p><div id="heatmap"></div></section>
<section class="panel"><h2>12. 第十年結果分布直方圖</h2><p>直接使用完整窗口 CSV，查看所選策略在 157 個重疊十年窗口的終值、年化回報、最大回撤或提款缺口分布。這是歷史樣本分布，不是未來機率；分位標記為 P05／中位／P95。</p><div class="control"><label for="histMetric">分布指標</label><select id="histMetric"><option value="terminal_nav_usd">第十年資產終值</option><option value="time_weighted_cagr">十年年化時間加權回報</option><option value="daily_max_drawdown">十年每日最大回撤</option><option value="withdrawal_shortfall_usd">十年累計提款缺口</option></select></div><div id="histogram"></div><div id="histLegend" class="legend"></div></section>
<section class="panel"><h2>13. 歷史起點敏感度</h2><p>同一策略在不同歷史起始年份的十年窗口會走出不同結果。切換指標並點擊柱狀組，可以讀取該起始年份群組的窗口數、終值分布、回報／回撤與提款缺口；這不是獨立試驗，也不是未來機率。</p><div class="control"><label for="cohortMetric">起點比較指標</label><select id="cohortMetric"><option value="median_terminal_nav_usd">中位終值</option><option value="p05_terminal_nav_usd">P05 終值（下尾）</option><option value="median_time_weighted_cagr">中位年化回報</option><option value="p05_time_weighted_cagr">P05 年化回報</option><option value="median_daily_max_drawdown">中位最大回撤</option><option value="worst_daily_max_drawdown">最差窗口回撤</option><option value="windows_with_withdrawal_shortfall">提款缺口窗口數</option></select></div><div id="cohort"></div><div id="cohortDetail"></div></section>
</div><p class="foot">資料：Yahoo Finance 股息／拆股調整收市價作近似總回報；共同日資料 5,788 筆（2003-09-29 至 2026-09-30），277 個共同月末，157 個重疊十年窗口。稅項、交易成本和買賣差價未另行建模。資料 SHA-256：8d34a8772fd5c74a7df20957cab971c3c2685963e54b160c3c958c8b9d4b7e70。</p></main>
<script>
const D=__DATA__,A=__ANNUAL__,HIST=__HIST__,COHORT=__COHORT__,TG=[30,40,50,60,70,80,90,100],TM=["front_fast","front_loaded","linear","mid_loaded","back_loaded","back_late"],FL=["no_withdrawals","delayed_stepup_example","monthly_withdrawal_500_usd_stress","monthly_withdrawal_1000_usd_stress"],TN={front_fast:"加速前置",front_loaded:"前置",linear:"線性",mid_loaded:"中段S曲線",back_loaded:"後置",back_late:"延後"},FN={no_withdrawals:"不提款",delayed_stepup_example:"延遲提款＋投入",monthly_withdrawal_500_usd_stress:"每月$500",monthly_withdrawal_1000_usd_stress:"每月$1,000"},C={blue:"#3977a8",teal:"#329b8a",AGG:"#3274a1",SHY:"#2a9d8f",IEF:"#e07a35",TLT:"#7966a8",front_fast:"#c94c4c",front_loaded:"#dd8547",linear:"#3274a1",mid_loaded:"#59a14f",back_loaded:"#8c78bd",back_late:"#b07aa1",grid:"#e8edf3",muted:"#718096",navy:"#203a59"},$=x=>document.getElementById(x),usd=n=>n==null?"—":"$"+Math.round(n).toLocaleString("en-US"),pct=n=>n==null?"—":(n*100).toFixed(2)+"%";
function S(){return {bond:$("bond").value,target:+$("target").value,timing:$("timing").value,flow:$("flow").value,year:+$("year").value};}
function R(b,t,m,f){return D.find(r=>r.bond_proxy===b&&+r.target_bond_conversion_pct_at_year10===+t&&r.timing_rule===m&&r.cashflow_mode===f);}
function Y(b,t,m,f,y){return A.find(r=>r.bond_proxy===b&&+r.target_bond_conversion_pct_at_year10===+t&&r.timing_rule===m&&r.cashflow_mode===f&&+r.year===+y);}

function H(title,w,h){return '<svg class="chart" viewBox="0 0 '+w+' '+h+'" role="img" aria-label="'+title+'"><title>'+title+'</title>';}
function chart(metric,flow,title,fmt,s){
 if(metric==="median_cumulative_twr_cagr"&&s.year===0)return '<p class="tiny">第0年是起始點，沒有完整年度可計算年化回報。</p>';
 let w=800,h=290,x0=62,y0=18,pw=690,ph=195,vals=[];
 TM.forEach(m=>TG.forEach(t=>{let r=Y(s.bond,t,m,flow,s.year);if(r&&r[metric]!=null)vals.push(+r[metric]);}));
 if(!vals.length)return '<p class="tiny">所選年份沒有可用數據。</p>';
 let lo=Math.min(0,...vals),hi=Math.max(.00001,...vals);
 if(metric==="median_drawdown_to_date"){lo=Math.min(...vals,0)*1.15;hi=0;}
 else if(metric==="windows_with_withdrawal_shortfall"){lo=0;hi=Math.max(1,...vals)*1.15;}
 else if(metric==="median_nav_usd"){lo=0;hi=Math.max(...vals)*1.12;}
 else {lo=Math.min(0,...vals)*1.1;hi=Math.max(0,...vals)*1.1;if(hi===lo)hi=lo+0.01;}
 if(hi===lo)hi=lo+1;
 let z=H(title,w,h);
 for(let i=0;i<=4;i++){let v=lo+(hi-lo)*i/4,y=y0+ph-(v-lo)/(hi-lo)*ph;z+='<line x1="'+x0+'" y1="'+y+'" x2="'+(x0+pw)+'" y2="'+y+'" stroke="'+C.grid+'"/><text x="'+(x0-6)+'" y="'+(y+3)+'" text-anchor="end" font-size="10" fill="'+C.muted+'">'+fmt(v)+'</text>';}
 TG.forEach((t,i)=>z+='<text x="'+(x0+pw*i/7)+'" y="'+(y0+ph+16)+'" font-size="10" text-anchor="middle" fill="'+C.muted+'">'+t+'%</text>');
 const dash={front_fast:"1 3",front_loaded:"7 4",linear:"",mid_loaded:"6 2 1 2",back_loaded:"2 4",back_late:"10 3"};
 TM.forEach(m=>{
   let ps=TG.map((t,i)=>{let q=Y(s.bond,t,m,flow,s.year);return q&&q[metric]!=null?{t:t,v:+q[metric],x:x0+pw*i/7}:null;}).filter(Boolean).map(p=>({...p,y:y0+ph-(p.v-lo)/(hi-lo)*ph}));
   if(ps.length>1)z+='<path d="'+ps.map((p,i)=>(i?"L":"M")+p.x+" "+p.y).join(" ")+'" fill="none" stroke="'+C[m]+'" stroke-width="'+(m===s.timing?3:1.5)+'" opacity="'+(m===s.timing?1:.62)+'" stroke-dasharray="'+dash[m]+'"/>';
   ps.forEach(p=>{let selected=p.t===s.target&&m===s.timing;z+='<circle data-target="'+p.t+'" data-timing="'+m+'" cx="'+p.x+'" cy="'+p.y+'" r="'+(selected?6:3.2)+'" fill="'+C[m]+'" stroke="'+(selected?C.navy:"#fff")+'" stroke-width="'+(selected?2.3:1)+'"><title>第'+s.year+'年 '+p.t+'% '+TN[m]+': '+fmt(p.v)+'</title></circle>';});
 });
 return z+"</svg>";
}
function scatter(s){
 let rr=A.filter(r=>r.cashflow_mode===s.flow&&+r.year===s.year&&r.median_cumulative_twr_cagr!=null);
 if(!rr.length)return '<p class="tiny">第0年尚未形成回報／回撤座標。</p>';
 let w=800,h=290,x0=62,y0=18,pw=690,ph=195,xx=rr.map(r=>Math.abs(+r.median_drawdown_to_date)),yy=rr.map(r=>+r.median_cumulative_twr_cagr),mx=Math.max(.01,...xx)*1.1,mn=Math.min(0,...yy)*1.1,mr=Math.max(.01,...yy)*1.08;
 if(mr===mn)mr=mn+.01;
 let xp=v=>x0+v/mx*pw,yp=v=>y0+ph-(v-mn)/(mr-mn)*ph,z=H("第"+s.year+"年回報與回撤（"+FN[s.flow]+"）",w,h);
 for(let i=0;i<=4;i++){let a=mx*i/4,x=xp(a),b=mn+(mr-mn)*i/4,y=yp(b);z+='<line x1="'+x+'" y1="'+y0+'" x2="'+x+'" y2="'+(y0+ph)+'" stroke="'+C.grid+'"/><text x="'+x+'" y="'+(y0+ph+16)+'" font-size="10" text-anchor="middle">'+Math.round(a*100)+'%</text><line x1="'+x0+'" y1="'+y+'" x2="'+(x0+pw)+'" y2="'+y+'" stroke="'+C.grid+'"/><text x="'+(x0-6)+'" y="'+(y+3)+'" text-anchor="end" font-size="10">'+(b*100).toFixed(1)+'%</text>';}
 rr.forEach(r=>{
   let x=xp(Math.abs(+r.median_drawdown_to_date)),y=yp(+r.median_cumulative_twr_cagr),sel=r.bond_proxy===s.bond&&+r.target_bond_conversion_pct_at_year10===s.target&&r.timing_rule===s.timing;
   let shape=r.timing_rule,mark;
   if(shape==="front_fast")mark='<rect x="'+(x-3.5)+'" y="'+(y-3.5)+'" width="7" height="7"';
   else if(shape==="front_loaded")mark='<polygon points="'+x+','+(y-4.5)+' '+(x-4.5)+','+(y+3.5)+' '+(x+4.5)+','+(y+3.5)+'"';
   else if(shape==="linear")mark='<circle cx="'+x+'" cy="'+y+'" r="3.1"';
   else if(shape==="mid_loaded")mark='<polygon points="'+x+','+(y-5)+' '+(x-5)+','+y+' '+x+','+(y+5)+' '+(x+5)+','+y+'"';
   else if(shape==="back_loaded")mark='<polygon points="'+(x-4.5)+','+(y-3.5)+' '+(x+4.5)+','+(y-3.5)+' '+x+','+(y+5)+'"';
   else mark='<path d="M '+(x-4)+' '+y+' H '+(x+4)+' M '+x+' '+(y-4)+' V '+(y+4)+'" ';
   let close=shape==="front_fast"?"</rect>":shape==="front_loaded"||shape==="mid_loaded"||shape==="back_loaded"?"</polygon>":shape==="linear"?"</circle>":"</path>";
   z+=mark+' data-pick="1" data-flow="'+r.cashflow_mode+'" data-bond="'+r.bond_proxy+'" data-target="'+r.target_bond_conversion_pct_at_year10+'" data-timing="'+r.timing_rule+'" fill="'+(shape==="back_late"?"none":C[r.bond_proxy])+'" stroke="'+(sel?C.navy:C[r.bond_proxy])+'" stroke-width="'+(sel?3:1.4)+'"><title>'+r.bond_proxy+' '+r.target_bond_conversion_pct_at_year10+'% '+TN[r.timing_rule]+' · '+pct(r.median_cumulative_twr_cagr)+' · '+pct(r.median_drawdown_to_date)+'</title>'+close;
 });
 return z+'<text x="'+(x0+pw/2)+'" y="'+(h-5)+'" text-anchor="middle" font-size="11">截至第'+s.year+'年：中位最大回撤幅度（越左越小）</text></svg>';
}
function bbar(label,v,color){return '<div class="barrow"><span>'+label+'</span><div class="track"><div class="fill" style="width:'+v+'%;background:'+color+'"></div></div><b style="text-align:right">'+v.toFixed(1)+'%</b></div>';}
function glide(s){let w=800,h=255,x0=62,y0=15,pw=690,ph=165,z=H("十年配置路徑",w,h);for(let i=0;i<=5;i++){let v=20*i,y=y0+ph-v*ph/100;z+='<line x1="'+x0+'" y1="'+y+'" x2="'+(x0+pw)+'" y2="'+y+'" stroke="'+C.grid+'"/><text x="'+(x0-6)+'" y="'+(y+3)+'" text-anchor="end" font-size="10">'+v+'%</text>';}for(let y=0;y<=10;y++)z+='<text x="'+(x0+pw*y/10)+'" y="'+(y0+ph+16)+'" text-anchor="middle" font-size="10">'+y+'</text>';TM.forEach(m=>{let ps=Array.from({length:11},(_,y)=>({y:y,v:100*Y(s.bond,s.target,m,s.flow,y).median_target_bond_weight,x:x0+pw*y/10}));z+='<path d="'+ps.map((p,i)=>(i?"L":"M")+p.x+" "+(y0+ph-p.v*ph)).join(" ")+'" fill="none" stroke="'+C[m]+'" stroke-width="'+(m===s.timing?3:1.6)+'" stroke-dasharray="'+(m==="front_loaded"?"6 4":m==="back_loaded"?"2 4":"")+'"/>';ps.filter(p=>p.y===s.year).forEach(p=>z+='<circle cx="'+p.x+'" cy="'+(y0+ph-p.v*ph)+'" r="5" fill="'+C[m]+'" stroke="'+C.navy+'" stroke-width="2"/>');});let x=x0+pw*s.year/10;z+='<line x1="'+x+'" y1="'+y0+'" x2="'+x+'" y2="'+(y0+ph)+'" stroke="'+C.navy+'" stroke-dasharray="4 4"/></svg>';let yr=Y(s.bond,s.target,s.timing,s.flow,s.year),bd=100*yr.median_target_bond_weight,st=100*yr.median_target_stock_weight;$("shares").innerHTML=bbar("股票目標",st,C.navy)+bbar("債券目標",bd,C.teal)+'<p class="tiny">第'+s.year+'年實際回測的配置目標：股票 '+st.toFixed(1)+'%／債券 '+bd.toFixed(1)+'%。此數值由回測每年記錄的再平衡目標而來。</p>';return z;}

function fan(s){
 const rows=Array.from({length:11},(_,y)=>Y(s.bond,s.target,s.timing,s.flow,y));
 const fields=["p05_nav_usd","median_nav_usd","p95_nav_usd","worst_nav_usd"];
 const values=rows.flatMap(r=>fields.map(k=>+r[k])).filter(Number.isFinite);
 let lo=Math.max(0,Math.min(...values)*0.94),hi=Math.max(...values)*1.06;
 if(hi<=lo)hi=lo+1;
 const w=800,h=285,x0=68,y0=18,pw=680,ph=190;
 const x=y=>x0+pw*y/10, py=v=>y0+ph-(v-lo)/(hi-lo)*ph;
 let z=H("十年資產分位分布帶",w,h);
 for(let i=0;i<=4;i++){const v=lo+(hi-lo)*i/4,yy=py(v);z+='<line x1="'+x0+'" y1="'+yy+'" x2="'+(x0+pw)+'" y2="'+yy+'" stroke="'+C.grid+'"/><text x="'+(x0-8)+'" y="'+(yy+4)+'" text-anchor="end" font-size="10" fill="'+C.muted+'">'+usd(v)+'</text>';}
 for(let y=0;y<=10;y++)z+='<text x="'+x(y)+'" y="'+(y0+ph+17)+'" text-anchor="middle" font-size="10" fill="'+C.muted+'">'+y+'</text>';
 const band=rows.map((r,i)=>(i?"L":"M")+x(i)+" "+py(+r.p95_nav_usd)).join(" ")+rows.slice().reverse().map((r,i)=>"L"+x(10-i)+" "+py(+r.p05_nav_usd)).join(" ")+" Z";
 z+='<path d="'+band+'" fill="#93bfe0" fill-opacity=".38" stroke="none"/>';
 const line=(key,color,width,dash="")=>'<path d="'+rows.map((r,i)=>(i?"L":"M")+x(i)+" "+py(+r[key])).join(" ")+'" fill="none" stroke="'+color+'" stroke-width="'+width+'"'+(dash?' stroke-dasharray="'+dash+'"':'')+'/>';
 z+=line("median_nav_usd",C.navy,3)+line("worst_nav_usd","#c94c4c",1.8,"5 4");
 rows.forEach((r,y)=>{z+='<circle data-year="'+y+'" data-target="'+s.target+'" data-timing="'+s.timing+'" data-bond="'+s.bond+'" cx="'+x(y)+'" cy="'+py(+r.median_nav_usd)+'" r="'+(y===s.year?6:3.5)+'" fill="'+(y===s.year?C.navy:"#fff")+'" stroke="'+C.navy+'" stroke-width="1.8"><title>第'+y+'年：P05 '+usd(r.p05_nav_usd)+'；中位 '+usd(r.median_nav_usd)+'；P95 '+usd(r.p95_nav_usd)+'；最差 '+usd(r.worst_nav_usd)+'</title></circle>';});
 z+='<line x1="'+x(s.year)+'" y1="'+y0+'" x2="'+x(s.year)+'" y2="'+(y0+ph)+'" stroke="'+C.navy+'" stroke-dasharray="4 4"/><text x="'+(x0+pw/2)+'" y="'+(h-5)+'" text-anchor="middle" font-size="11">年數（0–10）</text></svg>';
 $("fanLegend").innerHTML='<span><i style="background:#93bfe0"></i> P05–P95 歷史分位帶</span><span><i style="background:'+C.navy+'"></i> 中位資產</span><span><i style="background:#c94c4c"></i> 最差窗口</span>';
 return z;
}
function drawdownPath(s){
 const rows=Array.from({length:11},(_,y)=>Y(s.bond,s.target,s.timing,s.flow,y));
 const vals=rows.flatMap(r=>[+r.median_drawdown_to_date,+r.worst_drawdown_to_date]).filter(Number.isFinite);
 let lo=Math.min(-0.01,...vals)*1.08,hi=0;
 const w=800,h=265,x0=68,y0=18,pw=680,ph=175;
 const x=y=>x0+pw*y/10,py=v=>y0+ph-(v-lo)/(hi-lo)*ph;
 let z=H("最大回撤水下路徑",w,h);
 for(let i=0;i<=4;i++){const v=lo+(hi-lo)*i/4,yy=py(v);z+='<line x1="'+x0+'" y1="'+yy+'" x2="'+(x0+pw)+'" y2="'+yy+'" stroke="'+C.grid+'"/><text x="'+(x0-8)+'" y="'+(yy+4)+'" text-anchor="end" font-size="10" fill="'+C.muted+'">'+pct(v)+'</text>';}
 for(let y=0;y<=10;y++)z+='<text x="'+x(y)+'" y="'+(y0+ph+17)+'" text-anchor="middle" font-size="10" fill="'+C.muted+'">'+y+'</text>';
 const band=rows.map((r,i)=>(i?"L":"M")+x(i)+" "+py(+r.median_drawdown_to_date)).join(" ")+rows.slice().reverse().map((r,i)=>"L"+x(10-i)+" "+py(+r.worst_drawdown_to_date)).join(" ")+" Z";
 z+='<path d="'+band+'" fill="#e7a7a0" fill-opacity=".32" stroke="none"/>';
 const path=key=>rows.map((r,i)=>(i?"L":"M")+x(i)+" "+py(+r[key])).join(" ");
 z+='<path d="'+path("median_drawdown_to_date")+'" fill="none" stroke="'+C.navy+'" stroke-width="2.8"/><path d="'+path("worst_drawdown_to_date")+'" fill="none" stroke="#c94c4c" stroke-width="1.8" stroke-dasharray="5 4"/>';
 rows.forEach((r,y)=>{z+='<circle data-year="'+y+'" data-target="'+s.target+'" data-timing="'+s.timing+'" data-bond="'+s.bond+'" cx="'+x(y)+'" cy="'+py(+r.median_drawdown_to_date)+'" r="'+(y===s.year?5.5:3)+'" fill="'+(y===s.year?C.navy:"#fff")+'" stroke="'+C.navy+'" stroke-width="1.5"><title>第'+y+'年：中位回撤 '+pct(r.median_drawdown_to_date)+'；最差窗口 '+pct(r.worst_drawdown_to_date)+'</title></circle>';});
 z+='<line x1="'+x(s.year)+'" y1="'+y0+'" x2="'+x(s.year)+'" y2="'+(y0+ph)+'" stroke="'+C.navy+'" stroke-dasharray="4 4"/><text x="'+(x0+pw/2)+'" y="'+(h-5)+'" text-anchor="middle" font-size="11">年數（0–10）</text></svg>';
 $("riskLegend").innerHTML='<span><i style="background:'+C.navy+'"></i> 中位最大回撤</span><span><i style="background:#c94c4c"></i> 最差窗口回撤</span>';
 return z;
}
function heatColor(value,min,max,invert){
 let t=max===min?0.5:(value-min)/(max-min);if(invert)t=1-t;
 const stops=["#f0b3ad","#f5dda0","#d8e9ae","#8dcbb7"];
 const idx=Math.min(3,Math.max(0,Math.floor(t*4)));
 return stops[idx];
}
function heatmap(s){
 const metric=$("heatMetric").value;
 const labels={median_nav_usd:"中位資產",p05_nav_usd:"P05資產",median_cumulative_twr_cagr:"累計年化回報",median_drawdown_to_date:"最大回撤",windows_with_withdrawal_shortfall:"提款缺口窗口"};
 const vals=[];
 for(const timing of TM)for(const target of TG){const r=Y(s.bond,target,timing,s.flow,s.year);if(r&&r[metric]!=null)vals.push(+r[metric]);}
 if(!vals.length)return '<p class="tiny">此年份的所選指標沒有足夠數據。</p>';
 const min=Math.min(...vals),max=Math.max(...vals),invert=metric==="windows_with_withdrawal_shortfall";
 const fmt=v=>metric.includes("nav_usd")?usd(v):metric==="windows_with_withdrawal_shortfall"?String(Math.round(v)):pct(v);
 const w=800,h=300,x0=153,y0=43,cw=75,rh=36;
 let z=H("配置熱圖："+labels[metric],w,h);
 z+='<text x="'+(x0-9)+'" y="17" text-anchor="end" font-size="10" fill="'+C.muted+'">轉換規則 ↓</text>';
 TG.forEach((t,i)=>z+='<text x="'+(x0+cw*i+cw/2)+'" y="32" text-anchor="middle" font-size="10" fill="'+C.muted+'">'+t+'%</text>');
 TM.forEach((timing,ri)=>{
  z+='<text x="'+(x0-10)+'" y="'+(y0+rh*ri+rh/2+4)+'" text-anchor="end" font-size="10" fill="'+C.ink+'">'+TN[timing]+'</text>';
  TG.forEach((target,ci)=>{
   const r=Y(s.bond,target,timing,s.flow,s.year);if(!r||r[metric]==null)return;
   const v=+r[metric],selected=target===s.target&&timing===s.timing,x=x0+cw*ci,y=y0+rh*ri;
   z+='<g data-target="'+target+'" data-timing="'+timing+'" data-bond="'+s.bond+'" data-year="'+s.year+'" style="cursor:pointer"><rect x="'+(x+2)+'" y="'+(y+2)+'" width="'+(cw-4)+'" height="'+(rh-4)+'" rx="5" fill="'+heatColor(v,min,max,invert)+'" stroke="'+(selected?C.navy:"#fff")+'" stroke-width="'+(selected?3:1)+'"><title>'+s.bond+' · '+target+'% · '+TN[timing]+' · '+labels[metric]+': '+fmt(v)+'</title></rect><text x="'+(x+cw/2)+'" y="'+(y+rh/2+4)+'" text-anchor="middle" font-size="10" fill="#263746" pointer-events="none">'+(metric==="median_cumulative_twr_cagr"||metric==="median_drawdown_to_date"?pct(v):metric==="windows_with_withdrawal_shortfall"?Math.round(v):usd(v))+'</text></g>';
  });
 });
 z+='<text x="'+(x0+cw*4)+'" y="'+(y0+rh*6+20)+'" text-anchor="middle" font-size="10" fill="'+C.muted+'">橫軸：第10年目標轉債比重</text></svg>';
 return z;
}
function csvEscape(v){const textValue=v==null?"":String(v);return '"'+textValue.replace(/"/g,'""')+'"';}
function downloadCsv(filename,rows){
 if(!rows.length)return;
 const keys=Array.from(new Set(rows.flatMap(r=>Object.keys(r))));
 const csv="\uFEFF"+[keys.map(csvEscape).join(","),...rows.map(r=>keys.map(k=>csvEscape(r[k])).join(","))].join("\r\n");
 const blob=new Blob([csv],{type:"text/csv;charset=utf-8"});
 const href=URL.createObjectURL(blob),a=document.createElement("a");
 a.href=href;a.download=filename;document.body.appendChild(a);a.click();a.remove();
 setTimeout(()=>URL.revokeObjectURL(href),1000);
}
function exportMatrix(){
 const s=S();
 const rows=TM.flatMap(timing=>TG.map(target=>{const r=Y(s.bond,target,timing,s.flow,s.year);return {year:s.year,bond_proxy:s.bond,cashflow_mode:s.flow,target_bond_conversion_pct_at_year10:target,timing_rule:timing,...r};}));
 downloadCsv("glidepath-year-"+s.year+"-matrix.csv",rows);
}


function histogram(s){
 const metric=$("histMetric").value;
 const labels={terminal_nav_usd:"第十年資產終值",time_weighted_cagr:"十年年化時間加權回報",daily_max_drawdown:"十年每日最大回撤",withdrawal_shortfall_usd:"十年累計提款缺口"};
 const d=HIST.find(h=>h.bond_proxy===s.bond&&+h.target_bond_conversion_pct_at_year10===s.target&&h.timing_rule===s.timing&&h.cashflow_mode===s.flow&&h.metric===metric);
 if(!d||!d.bins||!d.bins.length){$("histLegend").innerHTML="";return '<p class="tiny">此策略沒有足夠有效窗口計算所選指標。</p>';}
 let lo=+d.min,hi=+d.max;
 if(lo===hi){lo-=Math.max(1,Math.abs(lo)*0.02);hi+=Math.max(1,Math.abs(hi)*0.02);}
 const fmt=v=>(metric==="terminal_nav_usd"||metric==="withdrawal_shortfall_usd")?usd(v):pct(v);
 const w=800,h=300,x0=70,y0=20,pw=675,ph=175,maxCount=Math.max(1,...d.bins.map(b=>+b.count));
 const x=v=>x0+(v-lo)/(hi-lo)*pw, py=v=>y0+ph-v/maxCount*ph;
 let z=H(labels[metric]+"："+s.bond+" "+s.target+"% "+TN[s.timing]+" "+FN[s.flow],w,h);
 for(let i=0;i<=4;i++){const v=maxCount*i/4,yy=py(v);z+='<line x1="'+x0+'" y1="'+yy+'" x2="'+(x0+pw)+'" y2="'+yy+'" stroke="'+C.grid+'"/><text x="'+(x0-8)+'" y="'+(yy+4)+'" text-anchor="end" font-size="10" fill="'+C.muted+'">'+Math.round(v)+'</text>';}
 d.bins.forEach((b,i)=>{
   const left=x(+b.low),right=x(+b.high),bw=Math.max(2,(right-left)-1),xx=(metric==="terminal_nav_usd"||metric==="withdrawal_shortfall_usd")?left:left;
   const top=py(+b.count),barH=y0+ph-top;
   z+='<rect x="'+xx+'" y="'+top+'" width="'+bw+'" height="'+barH+'" fill="#76a9cf" stroke="#fff" stroke-width=".7"><title>'+fmt(+b.low)+' – '+fmt(+b.high)+'：'+b.count+' 個窗口</title></rect>';
 });
 const marks=[["P05",d.p05,"#dd8547","5 3"],["P50",d.median,C.navy,""],["P95",d.p95,"#329b8a","5 3"]];
 marks.forEach(([lab,val,color,dash])=>{if(val==null)return;const xx=x(+val);z+='<line x1="'+xx+'" y1="'+y0+'" x2="'+xx+'" y2="'+(y0+ph)+'" stroke="'+color+'" stroke-width="'+(lab==="P50"?2.8:1.8)+'"'+(dash?' stroke-dasharray="'+dash+'"':'')+'><title>'+lab+': '+fmt(+val)+'</title></line><text x="'+Math.max(x0+20,Math.min(x0+pw-20,xx))+'" y="'+(lab==="P05"?y0+12:lab==="P95"?y0+25:y0+38)+'" text-anchor="middle" font-size="10" fill="'+color+'">'+lab+'</text>';});
 for(let i=0;i<=4;i++){const v=lo+(hi-lo)*i/4,xx=x(v);z+='<text x="'+xx+'" y="'+(y0+ph+17)+'" text-anchor="middle" font-size="10" fill="'+C.muted+'">'+fmt(v)+'</text>';}
 z+='<text x="'+(x0+pw/2)+'" y="'+(h-5)+'" text-anchor="middle" font-size="11">歷史窗口指標值</text></svg>';
 $("histLegend").innerHTML='<span>'+labels[metric]+' · 有效窗口 '+d.n+'/'+D.find(r=>r.bond_proxy===s.bond&&+r.target_bond_conversion_pct_at_year10===s.target&&r.timing_rule===s.timing&&r.cashflow_mode===s.flow).rolling_windows+'</span><span><i style="background:#76a9cf"></i>窗口數（柱高）</span><span><i style="background:'+C.navy+'"></i>中位數</span>';
 return z;
}


let selectedCohortYear=null;
function cohortChart(s){
 const metric=$("cohortMetric").value;
 const labels={median_terminal_nav_usd:"中位終值",p05_terminal_nav_usd:"P05終值",median_time_weighted_cagr:"中位年化回報",p05_time_weighted_cagr:"P05年化回報",median_daily_max_drawdown:"中位最大回撤",worst_daily_max_drawdown:"最差窗口回撤",windows_with_withdrawal_shortfall:"提款缺口窗口數"};
 const rows=COHORT.filter(r=>r.bond_proxy===s.bond&&+r.target_bond_conversion_pct_at_year10===s.target&&r.timing_rule===s.timing&&r.cashflow_mode===s.flow).sort((a,b)=>a.start_year-b.start_year);
 if(!rows.length){$("cohortDetail").innerHTML='<p class="tiny">這個選定策略沒有可用的起始年份分組資料。</p>';return '<p class="tiny">沒有可用起點資料。</p>';}
 if(!rows.some(r=>+r.start_year===+selectedCohortYear))selectedCohortYear=+rows[rows.length-1].start_year;
 const values=rows.map(r=>r[metric]).filter(v=>v!=null&&Number.isFinite(+v)).map(Number);
 const fmt=v=>metric.includes("terminal_nav")?usd(v):metric==="windows_with_withdrawal_shortfall"?String(Math.round(v)):pct(v);
 let lo=Math.min(0,...values),hi=Math.max(0,...values);
 if(metric==="median_daily_max_drawdown"||metric==="worst_daily_max_drawdown"){lo=Math.min(...values,0)*1.12;hi=0;}
 if(metric==="windows_with_withdrawal_shortfall"){lo=0;hi=Math.max(1,...values)*1.12;}
 if(hi===lo)hi=lo+1;
 const w=800,h=292,x0=68,y0=20,pw=680,ph=185,step=pw/rows.length;
 const x=i=>x0+i*step+step*.15, bw=Math.max(4,step*.7),py=v=>y0+ph-(v-lo)/(hi-lo)*ph;
 let z=H("歷史起點敏感度："+labels[metric],w,h);
 for(let i=0;i<=4;i++){const v=lo+(hi-lo)*i/4,yy=py(v);z+='<line x1="'+x0+'" y1="'+yy+'" x2="'+(x0+pw)+'" y2="'+yy+'" stroke="'+C.grid+'"/><text x="'+(x0-8)+'" y="'+(yy+4)+'" text-anchor="end" font-size="10" fill="'+C.muted+'">'+fmt(v)+'</text>';}
 rows.forEach((r,i)=>{
   if(r[metric]==null)return;
   const val=+r[metric],xx=x(i),yy=py(val),zero=py(Math.max(lo,Math.min(hi,0))),top=Math.min(yy,zero),height=Math.max(1,Math.abs(zero-yy)),sel=+r.start_year===+selectedCohortYear;
   z+='<rect data-target="'+s.target+'" data-timing="'+s.timing+'" data-bond="'+s.bond+'" data-flow="'+s.flow+'" data-cohort-year="'+r.start_year+'" x="'+xx+'" y="'+top+'" width="'+bw+'" height="'+height+'" rx="2" fill="'+(sel?C.navy:"#78b2a8")+'" stroke="'+(sel?"#111827":"#fff")+'" stroke-width="'+(sel?2:1)+'"><title>起始年份 '+r.start_year+'；'+r.window_count+' 個窗口；'+labels[metric]+'：'+fmt(val)+'；中位終值 '+usd(r.median_terminal_nav_usd)+'；P05終值 '+usd(r.p05_terminal_nav_usd)+'；中位回報 '+pct(r.median_time_weighted_cagr)+'；最差回撤 '+pct(r.worst_daily_max_drawdown)+'；提款缺口 '+r.windows_with_withdrawal_shortfall+' 個窗口</title></rect>';
   if(rows.length<=16||i%2===0)z+='<text x="'+(xx+bw/2)+'" y="'+(y0+ph+16)+'" text-anchor="middle" font-size="10" fill="'+C.muted+'">'+r.start_year+'</text>';
 });
 z+='<text x="'+(x0+pw/2)+'" y="'+(h-5)+'" text-anchor="middle" font-size="11">十年窗口的起始日所屬年份（柱高＝'+labels[metric]+'）</text></svg>';
 const selected=rows.find(r=>+r.start_year===+selectedCohortYear);
 $("cohortDetail").innerHTML='<div class="metrics" style="grid-template-columns:repeat(4,minmax(0,1fr))"><article class="metric"><div class="k">窗口起始年份</div><div class="v">'+selected.start_year+'</div><div class="s">'+selected.first_window_start+' 至 '+selected.last_window_start+'</div></article><article class="metric"><div class="k">該年起始窗口</div><div class="v">'+selected.window_count+'</div><div class="s">此策略 157 個窗口中的一組</div></article><article class="metric"><div class="k">中位／P05 終值</div><div class="v">'+usd(selected.median_terminal_nav_usd)+'</div><div class="s">P05 '+usd(selected.p05_terminal_nav_usd)+'</div></article><article class="metric"><div class="k">中位回報／最差回撤</div><div class="v">'+pct(selected.median_time_weighted_cagr)+'</div><div class="s">最差回撤 '+pct(selected.worst_daily_max_drawdown)+'</div></article></div><p class="tiny">此起始年份的提款缺口窗口：'+selected.windows_with_withdrawal_shortfall+'；最差終值 '+usd(selected.worst_terminal_nav_usd)+'。每個起始年份的窗口數不同且彼此重疊，不適合解讀成年度成功率。</p>';
 return z;
}

function update(){
 let s=S(),r=Y(s.bond,s.target,s.timing,s.flow,s.year);
 $("targetOut").textContent=s.target+"%";$("yearOut").textContent="第"+s.year+"年";
 $("label").textContent="第"+s.year+"年 · "+s.bond+" · 目標 "+s.target+"% · "+TN[s.timing]+" · "+FN[s.flow];
 $("nwin").textContent=r.rolling_windows+"個歷史窗口";
 $("flowNote").textContent=s.flow==="no_withdrawals"?"以下數字均截至所選年份的歷史狀態。":s.flow==="delayed_stepup_example"?"截至所選年份：示例提款 $12,800、後續投入 $5,000 的完整時程中已發生事件會累計顯示。":s.flow==="monthly_withdrawal_500_usd_stress"?"每月要求提款 $500，累計最高要求 $60,000；數據只計至所選年份。":"每月要求提款 $1,000，累計最高要求 $120,000；數據只計至所選年份。";
 let ms=[["第"+s.year+"年中位資產",usd(r.median_nav_usd),"所選年份的歷史 NAV"],["第"+s.year+"年P05資產",usd(r.p05_nav_usd),"歷史第5百分位，非保證"],["截至當年累計年化回報",pct(r.median_cumulative_twr_cagr),"時間加權；第0年不適用"],["截至當年最大回撤",pct(r.median_drawdown_to_date),"不把外部提款本身計作回撤"],["最差窗口截至當年回撤",pct(r.worst_drawdown_to_date),"157個窗口中的最差值"],["累計缺口窗口",r.windows_with_withdrawal_shortfall+"/"+r.rolling_windows,"截至當年P95缺口 "+usd(r.p95_shortfall_usd)]];
 $("metrics").innerHTML=ms.map(m=>'<article class="metric"><div class="k">'+m[0]+'</div><div class="v">'+m[1]+'</div><div class="s">'+m[2]+'</div></article>').join("");
 $("wealth").innerHTML=chart("median_nav_usd",s.flow,"第"+s.year+"年中位資產",usd,s);
 $("drawdown").innerHTML=chart("median_drawdown_to_date",s.flow,"截至第"+s.year+"年最大回撤",pct,s);
 $("returns").innerHTML=chart("median_cumulative_twr_cagr",s.flow,"截至第"+s.year+"年累計年化回報",pct,s);
 $("gaps").innerHTML=chart("windows_with_withdrawal_shortfall",s.flow,"截至第"+s.year+"年提款缺口",v=>String(Math.round(v)),s);
 ["leg1","leg2","leg3","leg4"].forEach(id=>$(id).innerHTML=TM.map(m=>'<span><i style="background:'+C[m]+'"></i>'+TN[m]+(m===s.timing?" ✓":"")+'</span>').join(""));
 $("frontier").innerHTML=scatter(s);
 let fs=FL.map(f=>Y(s.bond,s.target,s.timing,f,s.year)),mx=Math.max.apply(null,fs.map(v=>+v.median_nav_usd));
 $("flows").innerHTML=fs.map((v,i)=>'<div class="barrow"><span>'+FN[FL[i]]+(FL[i]===s.flow?" ✓":"")+'</span><div class="track"><div class="fill" style="width:'+(100*v.median_nav_usd/mx)+'%;background:'+(FL[i]===s.flow?C.navy:C.blue)+'"></div></div><b style="text-align:right">'+usd(v.median_nav_usd)+'</b></div><p class="tiny" style="margin:-6px 0 6px 112px">截至當年缺口 '+v.windows_with_withdrawal_shortfall+'/'+v.rolling_windows+'；P95缺口 '+usd(v.p95_shortfall_usd)+'</p>').join("");
 $("glide").innerHTML=glide(s);
 $("fan").innerHTML=fan(s);
 $("drawdownPath").innerHTML=drawdownPath(s);
 $("heatmap").innerHTML=heatmap(s);
 $("histogram").innerHTML=histogram(s);
 $("cohort").innerHTML=cohortChart(s);
 let tr=TM.map(m=>Y(s.bond,s.target,m,s.flow,s.year));
 $("table").innerHTML='<table><thead><tr><th>轉換時間</th><th>第'+s.year+'年中位資產</th><th>P05資產</th><th>累計年化回報</th><th>截至當年回撤</th><th>累計缺口窗口</th></tr></thead><tbody>'+tr.map(v=>'<tr class="'+(v.timing_rule===s.timing?"active":"")+'"><td>'+TN[v.timing_rule]+'</td><td>'+usd(v.median_nav_usd)+'</td><td>'+usd(v.p05_nav_usd)+'</td><td>'+pct(v.median_cumulative_twr_cagr)+'</td><td>'+pct(v.median_drawdown_to_date)+'</td><td>'+v.windows_with_withdrawal_shortfall+'/'+v.rolling_windows+'</td></tr>').join("")+'</tbody></table>';
}
["bond","timing","flow","target","year","heatMetric","histMetric","cohortMetric"].forEach(id=>$(id).addEventListener("input",update));$("exportMatrix").addEventListener("click",exportMatrix);$("exportAnnual").addEventListener("click",()=>downloadCsv("glidepath-all-annual-summaries.csv",A));document.addEventListener("click",e=>{let p=e.target.closest("[data-target]");if(!p)return;if(p.dataset.target)$("target").value=p.dataset.target;if(p.dataset.timing)$("timing").value=p.dataset.timing;if(p.dataset.bond)$("bond").value=p.dataset.bond;if(p.dataset.flow)$("flow").value=p.dataset.flow;if(p.dataset.year!==undefined)$("year").value=p.dataset.year;if(p.dataset.cohortYear!==undefined)selectedCohortYear=+p.dataset.cohortYear;update();});update();
</script></body></html>'''


def render_dashboard(scenarios, annual_scenarios, histogram_data=None, cohort_data=None):
    payload=json.dumps([{k:r.get(k) for k in FIELDS} for r in scenarios],ensure_ascii=False,separators=(",",":")).replace("</","<\\/")
    annual_payload=json.dumps([{k:r.get(k) for k in ANNUAL_FIELDS} for r in annual_scenarios],ensure_ascii=False,separators=(",",":")).replace("</","<\\/")
    hist_payload=json.dumps(histogram_data or [],ensure_ascii=False,separators=(",",":")).replace("</","<\\/")
    cohort_payload=json.dumps(cohort_data or [],ensure_ascii=False,separators=(",",":")).replace("</","<\\/")
    return HTML.replace("__DATA__",payload).replace("__ANNUAL__",annual_payload).replace("__HIST__",hist_payload).replace("__COHORT__",cohort_payload)


def _hist_quantile(sorted_values, probability):
    if not sorted_values:
        return None
    pos=(len(sorted_values)-1)*probability
    lo=int(math.floor(pos)); hi=int(math.ceil(pos))
    if lo==hi:
        return float(sorted_values[lo])
    weight=pos-lo
    return float(sorted_values[lo])*(1-weight)+float(sorted_values[hi])*weight


def summarize_histogram(values):
    values=sorted(float(v) for v in values if math.isfinite(float(v)))
    if not values:
        return {"n":0,"min":None,"max":None,"p05":None,"median":None,"p95":None,"bins":[]}
    low,high=values[0],values[-1]
    summary={"n":len(values),"min":low,"max":high,"p05":_hist_quantile(values,0.05),
             "median":_hist_quantile(values,0.50),"p95":_hist_quantile(values,0.95)}
    if low==high:
        summary["bins"]=[{"low":low,"high":high,"count":len(values)}]
        return summary
    q1,q3=_hist_quantile(values,0.25),_hist_quantile(values,0.75)
    iqr=q3-q1
    width=2*iqr/(len(values)**(1/3)) if iqr>0 else 0.0
    bins_count=int(math.ceil((high-low)/width)) if width>0 else int(math.ceil(math.log2(len(values))+1))
    bins_count=max(8,min(18,bins_count))
    width=(high-low)/bins_count
    bins=[{"low":low+i*width,"high":high if i==bins_count-1 else low+(i+1)*width,"count":0}
          for i in range(bins_count)]
    for value in values:
        index=min(bins_count-1,int((value-low)/width))
        bins[index]["count"]+=1
    summary["bins"]=bins
    if sum(item["count"] for item in bins)!=len(values):
        raise ValueError("Histogram bins must conserve every valid rolling-window observation")
    return summary


def build_window_histograms(path, expected_scenarios=768, expected_windows=157):
    if not path.exists():
        raise FileNotFoundError(f"Window-level replay CSV is required for real outcome distributions: {path}")
    required={"bond_proxy","target_bond_conversion_pct_at_year10","timing_rule","cashflow_mode",
              "terminal_nav_usd","time_weighted_cagr","daily_max_drawdown","withdrawal_shortfall_usd"}
    groups={}
    with path.open("r",newline="",encoding="utf-8-sig") as handle:
        reader=csv.DictReader(handle)
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            raise ValueError(f"Window CSV must contain columns: {sorted(required)}")
        for row in reader:
            key=(row["bond_proxy"],int(row["target_bond_conversion_pct_at_year10"]),row["timing_rule"],row["cashflow_mode"])
            group=groups.setdefault(key,{"rows":0,"metrics":{metric:[] for metric in HISTOGRAM_METRICS}})
            group["rows"]+=1
            for metric in HISTOGRAM_METRICS:
                raw=(row.get(metric) or "").strip()
                if not raw:
                    continue
                value=float(raw)
                if math.isfinite(value):
                    group["metrics"][metric].append(value)
    if len(groups)!=expected_scenarios:
        raise ValueError(f"Expected {expected_scenarios} window-level scenario groups, got {len(groups)}")
    output=[]
    for key,group in sorted(groups.items()):
        if group["rows"]!=expected_windows:
            raise ValueError(f"Expected {expected_windows} rolling windows for {key}, got {group['rows']}")
        bond,target,timing,flow=key
        for metric in HISTOGRAM_METRICS:
            output.append({
                "bond_proxy":bond,"target_bond_conversion_pct_at_year10":target,
                "timing_rule":timing,"cashflow_mode":flow,"metric":metric,
                **summarize_histogram(group["metrics"][metric]),
            })
    if len(output)!=expected_scenarios*len(HISTOGRAM_METRICS):
        raise ValueError("Window distribution summary is incomplete")
    return output



def build_cohort_profiles(path, expected_scenarios=768, expected_windows=157):
    """Summarize actual rolling-window outcomes by the calendar year each window starts."""
    if not path.exists():
        raise FileNotFoundError(f"Window-level replay CSV is required for start-period analysis: {path}")
    required={"window_start","bond_proxy","target_bond_conversion_pct_at_year10","timing_rule","cashflow_mode",
              "terminal_nav_usd","time_weighted_cagr","daily_max_drawdown","withdrawal_shortfall_usd"}
    scenario_groups={}
    with path.open("r",newline="",encoding="utf-8-sig") as handle:
        reader=csv.DictReader(handle)
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            raise ValueError(f"Window CSV must contain columns: {sorted(required)}")
        for row in reader:
            window_start=(row.get("window_start") or "").strip()
            if len(window_start)<4 or not window_start[:4].isdigit():
                raise ValueError(f"Invalid rolling-window start date: {window_start!r}")
            key=(row["bond_proxy"],int(row["target_bond_conversion_pct_at_year10"]),row["timing_rule"],row["cashflow_mode"])
            start_year=int(window_start[:4])
            group=scenario_groups.setdefault(key,{"window_starts":set(),"cohorts":{}})
            if window_start in group["window_starts"]:
                raise ValueError(f"Duplicate window start for scenario {key}: {window_start}")
            group["window_starts"].add(window_start)
            cohort=group["cohorts"].setdefault(start_year,{"starts":[],"metrics":{metric:[] for metric in HISTOGRAM_METRICS}})
            cohort["starts"].append(window_start)
            for metric in HISTOGRAM_METRICS:
                raw=(row.get(metric) or "").strip()
                if raw:
                    value=float(raw)
                    if math.isfinite(value):
                        cohort["metrics"][metric].append(value)
    if len(scenario_groups)!=expected_scenarios:
        raise ValueError(f"Expected {expected_scenarios} rolling-window strategy groups, got {len(scenario_groups)}")
    output=[]
    for key,group in sorted(scenario_groups.items()):
        if len(group["window_starts"])!=expected_windows:
            raise ValueError(f"Expected {expected_windows} distinct window starts for {key}, got {len(group['window_starts'])}")
        bond,target,timing,flow=key
        for start_year,cohort in sorted(group["cohorts"].items()):
            terminal=sorted(cohort["metrics"]["terminal_nav_usd"])
            cagr=sorted(cohort["metrics"]["time_weighted_cagr"])
            drawdown=sorted(cohort["metrics"]["daily_max_drawdown"])
            shortfall=cohort["metrics"]["withdrawal_shortfall_usd"]
            median_terminal=_hist_quantile(terminal,.50)
            p05_terminal=_hist_quantile(terminal,.05)
            p95_terminal=_hist_quantile(terminal,.95)
            median_cagr=_hist_quantile(cagr,.50)
            p05_cagr=_hist_quantile(cagr,.05)
            worst_cagr=min(cagr) if cagr else None
            median_dd=_hist_quantile(drawdown,.50)
            worst_dd=min(drawdown) if drawdown else None
            output.append({
                "bond_proxy":bond,"target_bond_conversion_pct_at_year10":target,"timing_rule":timing,
                "cashflow_mode":flow,"start_year":start_year,"window_count":len(cohort["starts"]),
                "first_window_start":min(cohort["starts"]),"last_window_start":max(cohort["starts"]),
                "median_terminal_nav_usd":median_terminal,"p05_terminal_nav_usd":p05_terminal,
                "p95_terminal_nav_usd":p95_terminal,"worst_terminal_nav_usd":min(terminal) if terminal else None,
                "median_time_weighted_cagr":median_cagr,"p05_time_weighted_cagr":p05_cagr,
                "worst_time_weighted_cagr":worst_cagr,"median_daily_max_drawdown":median_dd,
                "worst_daily_max_drawdown":worst_dd,
                "windows_with_withdrawal_shortfall":sum(float(v)>0.01 for v in shortfall),
            })
    per_strategy={}
    for row in output:
        key=(row["bond_proxy"],row["target_bond_conversion_pct_at_year10"],row["timing_rule"],row["cashflow_mode"])
        per_strategy[key]=per_strategy.get(key,0)+int(row["window_count"])
    if len(per_strategy)!=expected_scenarios or any(count!=expected_windows for count in per_strategy.values()):
        raise ValueError("Start-year cohorts must conserve every source rolling window in every strategy")
    return output


def generate(outdir):
    source=outdir/"stock_bond_glidepath_summary.json"
    if not source.exists():
        raise FileNotFoundError(f"Run the glidepath backtest first: {source}")
    report=json.loads(source.read_text(encoding="utf-8"))
    scenarios=report.get("scenarios",[])
    if len(scenarios)!=768:
        raise ValueError("Expected 768 scenarios (8 targets x 6 timing rules x 4 bond proxies x 4 cash-flow modes)")
    annual=report.get("annual_scenarios",[])
    if len(annual)!=8448 or {int(r["year"]) for r in annual}!=set(range(11)):
        raise ValueError("Expected 8,448 annual summaries covering every year 0-10")
    if any(row.get("median_nav_usd") is None for row in annual):
        raise ValueError("Annual summaries must contain year-specific NAVs")

    # Audit the full data contract before embedding 200k+ bytes in an interactive page.
    scenario_key=lambda r:(r["bond_proxy"],int(r["target_bond_conversion_pct_at_year10"]),r["timing_rule"],r["cashflow_mode"])
    annual_key=lambda r:(r["bond_proxy"],int(r["target_bond_conversion_pct_at_year10"]),r["timing_rule"],r["cashflow_mode"],int(r["year"]))
    scenarios_by_key={scenario_key(r):r for r in scenarios}
    annual_by_key={annual_key(r):r for r in annual}
    if len(scenarios_by_key)!=768 or len(annual_by_key)!=8448:
        raise ValueError("Duplicate scenario/annual keys would make the UI select an ambiguous row")
    if {r["bond_proxy"] for r in scenarios}!={"AGG","SHY","IEF","TLT"}:
        raise ValueError("Bond-proxy set is incomplete")
    if {int(r["target_bond_conversion_pct_at_year10"]) for r in scenarios}!={30,40,50,60,70,80,90,100}:
        raise ValueError("Target conversion set is incomplete")
    if {r["timing_rule"] for r in scenarios}!={"front_fast","front_loaded","linear","mid_loaded","back_loaded","back_late"}:
        raise ValueError("Six-timing-rule set is incomplete")
    if {r["cashflow_mode"] for r in scenarios}!={"no_withdrawals","delayed_stepup_example","monthly_withdrawal_500_usd_stress","monthly_withdrawal_1000_usd_stress"}:
        raise ValueError("Cash-flow mode set is incomplete")
    paths_by_group={}
    for row in annual:
        key=scenario_key(row)
        year=int(row["year"])
        wb=row.get("median_target_bond_weight")
        ws=row.get("median_target_stock_weight")
        if wb is None or ws is None or not (-1e-10<=float(wb)<=1+1e-10) or not (-1e-10<=float(ws)<=1+1e-10):
            raise ValueError(f"Invalid annual target weight at {key}, year {year}")
        if abs(float(wb)+float(ws)-1.0)>1e-9:
            raise ValueError(f"Stock/bond target weights do not sum to 100% at {key}, year {year}")
        paths_by_group.setdefault((row["bond_proxy"],int(row["target_bond_conversion_pct_at_year10"]),row["cashflow_mode"]),{}).setdefault(row["timing_rule"],[]).append((year,float(wb)))
        if year==0 and row.get("median_cumulative_twr_cagr") is not None:
            raise ValueError("Year zero must not report an annualized return before an elapsed period")
        if year==10:
            sr=scenarios_by_key.get(key)
            if sr is None or abs(float(row["median_nav_usd"])-float(sr["median_terminal_nav_usd"]))>0.02:
                raise ValueError(f"Year-10 NAV does not reconcile to terminal summary for {key}")
            if row.get("median_cumulative_twr_cagr") is not None and sr.get("median_time_weighted_cagr") is not None:
                if abs(float(row["median_cumulative_twr_cagr"])-float(sr["median_time_weighted_cagr"]))>1e-8:
                    raise ValueError(f"Year-10 cumulative return does not reconcile for {key}")
            if abs(float(row["median_drawdown_to_date"])-float(sr["median_daily_max_drawdown"]))>1e-8:
                raise ValueError(f"Year-10 drawdown does not reconcile for {key}")
            if int(row["windows_with_withdrawal_shortfall"])!=int(sr["windows_with_withdrawal_shortfall"]):
                raise ValueError(f"Year-10 shortfall-window count does not reconcile for {key}")
    for (bond,target,flow), timing_paths in paths_by_group.items():
        normalized=[]
        for timing,marks in timing_paths.items():
            marks=sorted(marks)
            if len(marks)!=11 or [year for year,_ in marks]!=list(range(11)):
                raise ValueError(f"Incomplete yearly timing path: {bond}/{target}/{flow}/{timing}")
            weights=[weight for _,weight in marks]
            if abs(weights[0])>1e-9 or abs(weights[-1]-target/100.0)>1e-9:
                raise ValueError(f"Timing path endpoints invalid: {bond}/{target}/{flow}/{timing}")
            if any(a>b+1e-9 for a,b in zip(weights,weights[1:])):
                raise ValueError(f"Bond share must not decline: {bond}/{target}/{flow}/{timing}")
            normalized.append(tuple(round(weight,10) for weight in weights))
        if len(timing_paths)!=6 or len(set(normalized))!=6:
            raise ValueError(f"Six timing options must have six distinct annual paths: {bond}/{target}/{flow}")
    distribution_summary=build_window_histograms(outdir/"stock_bond_glidepath_windows.csv",expected_scenarios=len(scenarios),expected_windows=int(report["method"]["rolling_windows_per_scenario"]))
    distribution_report={"schema":"stock-bond-glidepath-window-distributions.v1","rolling_windows_per_scenario":int(report["method"]["rolling_windows_per_scenario"]),"metric_names":list(HISTOGRAM_METRICS),"distributions":distribution_summary}
    (outdir/"window_distribution_summary.json").write_text(json.dumps(distribution_report,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8")
    cohort_profiles=build_cohort_profiles(outdir/"stock_bond_glidepath_windows.csv",expected_scenarios=len(scenarios),expected_windows=int(report["method"]["rolling_windows_per_scenario"]))
    cohort_report={"schema":"stock-bond-glidepath-start-cohorts.v1","rolling_windows_per_scenario":int(report["method"]["rolling_windows_per_scenario"]),"cohorts":cohort_profiles}
    (outdir/"window_start_cohort_summary.json").write_text(json.dumps(cohort_report,ensure_ascii=False,separators=(",",":"))+"\n",encoding="utf-8")
    output=outdir/"interactive_dashboard.html"
    output.write_text(render_dashboard(report["scenarios"],annual,distribution_summary,cohort_profiles),encoding="utf-8")
    return output


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir",type=Path,required=True)
    args=parser.parse_args()
    path=generate(args.outdir)
    print(json.dumps({"interactive_dashboard":path.name,"bytes":path.stat().st_size,"scenario_rows":768,"annual_summary_rows":8448,"window_distribution_groups":3072,"start_year_cohorts":len(cohort_profiles),"year_range":[0,10],"timing_rules":6},ensure_ascii=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
