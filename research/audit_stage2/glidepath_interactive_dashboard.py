#!/usr/bin/env python3
"""Generate an offline interactive stock/bond glidepath dashboard from the full replay JSON."""
import argparse, json
from pathlib import Path

FIELDS = ("bond_proxy","target_bond_conversion_pct_at_year10","timing_rule","cashflow_mode","rolling_windows","median_terminal_nav_usd","p05_terminal_nav_usd","p95_terminal_nav_usd","worst_terminal_nav_usd","median_time_weighted_cagr","p05_time_weighted_cagr","worst_time_weighted_cagr","median_daily_max_drawdown","worst_daily_max_drawdown","windows_below_initial_capital_at_year10","windows_with_withdrawal_shortfall","median_actual_withdrawals_usd","p95_withdrawal_shortfall_usd","median_investor_xirr")
ANNUAL_FIELDS = ("year","bond_proxy","target_bond_conversion_pct_at_year10","timing_rule","cashflow_mode","rolling_windows","median_nav_usd","p05_nav_usd","p95_nav_usd","worst_nav_usd","median_cumulative_twr_cagr","p05_cumulative_twr_cagr","median_year_twr","p05_year_twr","median_drawdown_to_date","worst_drawdown_to_date","windows_below_initial_capital","windows_with_withdrawal_shortfall","median_actual_withdrawals_usd","median_shortfall_usd","p95_shortfall_usd","median_target_bond_weight","median_target_stock_weight")
HTML = r'''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>股票轉債互動追蹤台</title><style>
*{box-sizing:border-box}body{margin:0;background:#f3f6fa;color:#1c2e43;font:15px/1.45 system-ui,Arial,sans-serif}main{max-width:1450px;margin:auto;padding:22px 16px}h1{font-size:clamp(24px,3vw,36px);margin:0 0 6px}h2{font-size:18px;margin:0 0 5px}.muted{color:#667b90}.note{padding:12px;background:#fff7e9;border:1px solid #efd9ad;border-radius:12px;font-size:13px;margin:15px 0}.controls,.grid{display:grid;gap:11px}.controls{grid-template-columns:repeat(4,minmax(140px,1fr))}.control,.panel,.metric{background:white;border:1px solid #dce4ed;border-radius:14px;padding:13px;min-width:0}.control label{display:block;font-size:12px;font-weight:750;color:#667b90;margin-bottom:7px}.control select{width:100%;padding:9px;border:1px solid #ccd6e1;border-radius:9px;background:white;font:inherit}input[type=range]{width:100%;accent-color:#203a59;cursor:ew-resize}.full{grid-column:span 2}.ends,.head{display:flex;justify-content:space-between;align-items:center;gap:8px}.ends{font-size:11px;color:#7a8b9c}.head output{font-weight:800;font-size:19px;color:#203a59}.metrics{display:grid;grid-template-columns:repeat(6,minmax(105px,1fr));gap:9px;margin:12px 0}.metric .k{font-size:12px;color:#667b90;min-height:28px}.metric .v{font-size:clamp(18px,2vw,25px);font-weight:820;margin:6px 0}.metric .s,.tiny{font-size:11px;color:#667b90}.grid{grid-template-columns:repeat(2,minmax(0,1fr));margin-top:13px}.panel p{font-size:12px;color:#667b90;margin:4px 0 9px}.chart{width:100%;height:auto;display:block}.chart [data-target],.chart [data-pick]{cursor:pointer}.chart [data-target]:hover,.chart [data-pick]:hover{filter:brightness(.72)}.legend{display:flex;gap:10px;flex-wrap:wrap;font-size:11px;color:#667b90;margin-top:5px}.legend i{display:inline-block;width:15px;height:3px;vertical-align:middle;margin-right:4px}.barrow{display:grid;grid-template-columns:108px 1fr 85px;gap:8px;align-items:center;font-size:12px;margin:12px 0}.track{height:13px;background:#edf1f5;border-radius:99px;overflow:hidden}.fill{height:100%;border-radius:99px}.tablebox{overflow:auto}table{border-collapse:collapse;width:100%;font-size:12px}th,td{padding:8px;border-bottom:1px solid #e8edf3;text-align:right;white-space:nowrap}th:first-child,td:first-child{text-align:left}th{background:#f6f8fb;color:#526177}tr.active{background:#eef5fc}.foot{font-size:11px;color:#667b90;line-height:1.6;margin-top:17px}@media(max-width:1100px){.controls{grid-template-columns:repeat(2,1fr)}.metrics{grid-template-columns:repeat(3,1fr)}}@media(max-width:700px){main{padding:13px 8px}.grid{grid-template-columns:1fr}.metrics{grid-template-columns:repeat(2,1fr)}.full{grid-column:span 2}}
</style></head><body><main><h1>股票逐年轉債：互動追蹤台</h1><p class="muted">拖動 BAR 或點圖表資料點，資產、回報、回撤、提款缺口和配置路徑會同步變化。初始 NAV：US$100,000。</p><div class="note"><b>限制：</b>這是歷史 ETF 代理回測，不是預測，也不保本。157 個十年窗口互相重疊，不是未來機率。資料截至 2026-09-30，沒有 2000–2002 科技股崩跌。100%債券目標到第120個月才達成；ETF 不等於持有到期的個別國債／STRIPS。</div>
<section class="controls"><div class="control"><label for="bond">債券代理</label><select id="bond"><option>AGG</option><option>SHY</option><option>IEF</option><option>TLT</option></select></div><div class="control"><label for="timing">轉換時間規則</label><select id="timing"><option value="front_fast">加速前置：第2年半程</option><option value="front_loaded">前置：第3年半程</option><option value="linear">線性：每年等量</option><option value="mid_loaded">中段加速：S曲線</option><option value="back_loaded">後置：第5年開始</option><option value="back_late">延後：第7年開始</option></select></div><div class="control"><label for="flow">提款／投入模式</label><select id="flow"><option value="no_withdrawals">不提款</option><option value="delayed_stepup_example">延遲／升降提款＋投入</option><option value="monthly_withdrawal_500_usd_stress">每月提款 $500 壓力</option><option value="monthly_withdrawal_1000_usd_stress">每月提款 $1,000 壓力</option></select></div><div class="control"><label for="target">第10年目標轉債</label><div class="head"><span class="tiny">可拖動或點圖</span><output id="targetOut">60%</output></div><input id="target" type="range" min="30" max="100" step="10" value="60"><div class="ends"><span>30%</span><span>100%</span></div></div><div class="control full"><label for="year">查看哪一年配置（拖動 BAR）</label><div class="head"><span class="tiny">查看當年股票／債券配置</span><output id="yearOut">第5年</output></div><input id="year" type="range" min="0" max="10" step="1" value="5"><div class="ends"><span>第0年</span><span>第10年</span></div><div id="allocation"></div></div><div class="control full"><label>目前選定情境</label><div class="head"><output id="label" style="font-size:15px">AGG · 60% · 線性</output><span id="nwin" class="tiny">157窗口</span></div><p id="flowNote" class="tiny">所有值是歷史統計，不是預測。</p></div></section>
<section id="metrics" class="metrics"></section><div class="grid">
<section class="panel"><h2>1. 所選年份資產</h2><p>所有曲線都依「查看第幾年」切換為該年觀測值；點資料點可同步更換目標和轉換曲線。</p><div id="wealth"></div><div id="leg1" class="legend"></div></section>
<section class="panel"><h2>2. 中位最大回撤</h2><p>顯示截至所選年份的最大回撤；提款本身不直接算成投資回撤。</p><div id="drawdown"></div><div id="leg2" class="legend"></div></section>
<section class="panel"><h2>3. 年化時間加權回報</h2><p>顯示由起點累計至所選年份的時間加權年化回報；第0年尚未形成回報期。</p><div id="returns"></div><div id="leg3" class="legend"></div></section>
<section class="panel"><h2>4. 提款缺口窗口數</h2><p>截至所選年份，157個歷史窗口中已出現提款缺口的窗口數；滑桿改變時本圖也更新。</p><div id="gaps"></div><div id="leg4" class="legend"></div></section>
<section class="panel"><h2>5. 回報 × 回撤互追圖</h2><p>每點為一個策略，套用目前選定的現金流模式；點擊後其他圖表同步追蹤。越左回撤越小，越高回報越高。</p><div id="frontier"></div><div class="legend">顏色＝AGG／SHY／IEF／TLT；○ 線性　□ 加速前置　△ 前置　◇ 中段S曲線　▽ 後置　＋ 延後</div></section>
<section class="panel"><h2>6. 同策略現金流對照</h2><p>固定目前策略，比較四種現金流假設的中位終值和提款缺口。</p><div id="flows"></div><p class="tiny">提款示例和月提款模式僅用作壓力測試。</p></section>
<section class="panel"><h2>7. 十年配置路徑</h2><p>拖動查看年份 BAR，比較六條轉換曲線和所選年份的股票／債券配置。</p><div id="glide"></div><div id="shares"></div></section>
<section class="panel"><h2>8. 同目標、不同時間規則</h2><p>固定目標、債券代理及現金流，逐行比較六種轉換規則。</p><div id="table" class="tablebox"></div></section>
</div><p class="foot">資料：Yahoo Finance 股息／拆股調整收市價作近似總回報；共同日資料 5,788 筆（2003-09-29 至 2026-09-30），277 個共同月末，157 個重疊十年窗口。稅項、交易成本和買賣差價未另行建模。資料 SHA-256：8d34a8772fd5c74a7df20957cab971c3c2685963e54b160c3c958c8b9d4b7e70。</p></main>
<script>
const D=__DATA__,A=__ANNUAL__,TG=[30,40,50,60,70,80,90,100],TM=["front_fast","front_loaded","linear","mid_loaded","back_loaded","back_late"],FL=["no_withdrawals","delayed_stepup_example","monthly_withdrawal_500_usd_stress","monthly_withdrawal_1000_usd_stress"],TN={front_fast:"加速前置",front_loaded:"前置",linear:"線性",mid_loaded:"中段S曲線",back_loaded:"後置",back_late:"延後"},FN={no_withdrawals:"不提款",delayed_stepup_example:"延遲提款＋投入",monthly_withdrawal_500_usd_stress:"每月$500",monthly_withdrawal_1000_usd_stress:"每月$1,000"},C={blue:"#3977a8",teal:"#329b8a",AGG:"#3274a1",SHY:"#2a9d8f",IEF:"#e07a35",TLT:"#7966a8",front_fast:"#c94c4c",front_loaded:"#dd8547",linear:"#3274a1",mid_loaded:"#59a14f",back_loaded:"#8c78bd",back_late:"#b07aa1",grid:"#e8edf3",muted:"#718096",navy:"#203a59"},$=x=>document.getElementById(x),usd=n=>n==null?"—":"$"+Math.round(n).toLocaleString("en-US"),pct=n=>n==null?"—":(n*100).toFixed(2)+"%";
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
 let tr=TM.map(m=>Y(s.bond,s.target,m,s.flow,s.year));
 $("table").innerHTML='<table><thead><tr><th>轉換時間</th><th>第'+s.year+'年中位資產</th><th>P05資產</th><th>累計年化回報</th><th>截至當年回撤</th><th>累計缺口窗口</th></tr></thead><tbody>'+tr.map(v=>'<tr class="'+(v.timing_rule===s.timing?"active":"")+'"><td>'+TN[v.timing_rule]+'</td><td>'+usd(v.median_nav_usd)+'</td><td>'+usd(v.p05_nav_usd)+'</td><td>'+pct(v.median_cumulative_twr_cagr)+'</td><td>'+pct(v.median_drawdown_to_date)+'</td><td>'+v.windows_with_withdrawal_shortfall+'/'+v.rolling_windows+'</td></tr>').join("")+'</tbody></table>';
}
["bond","timing","flow","target","year"].forEach(id=>$(id).addEventListener("input",update));document.addEventListener("click",e=>{let p=e.target.closest("[data-target]");if(!p)return;if(p.dataset.target)$("target").value=p.dataset.target;if(p.dataset.timing)$("timing").value=p.dataset.timing;if(p.dataset.bond)$("bond").value=p.dataset.bond;update();});update();
</script></body></html>'''


def render_dashboard(scenarios, annual_scenarios):
    payload=json.dumps([{k:r.get(k) for k in FIELDS} for r in scenarios],ensure_ascii=False,separators=(",",":")).replace("</","<\\/")
    annual_payload=json.dumps([{k:r.get(k) for k in ANNUAL_FIELDS} for r in annual_scenarios],ensure_ascii=False,separators=(",",":")).replace("</","<\\/")
    return HTML.replace("__DATA__",payload).replace("__ANNUAL__",annual_payload)


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
    output=outdir/"interactive_dashboard.html"
    output.write_text(render_dashboard(report["scenarios"],annual),encoding="utf-8")
    return output


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir",type=Path,required=True)
    args=parser.parse_args()
    path=generate(args.outdir)
    print(json.dumps({"interactive_dashboard":path.name,"bytes":path.stat().st_size,"scenario_rows":768,"annual_summary_rows":8448,"year_range":[0,10],"timing_rules":6},ensure_ascii=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
