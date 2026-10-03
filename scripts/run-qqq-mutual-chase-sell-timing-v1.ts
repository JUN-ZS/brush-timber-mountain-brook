import { readFileSync, mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

type QqqData = { source: string; asof: string; dates: string[]; c: { QQQ?: Array<number | null> } };
type MonthlyPoint = { date: string; close: number };
type RuleName = "ALWAYS_SURPLUS" | "NEAR_12M_HIGH" | "AT_12M_HIGH" | "STRONG_AND_HIGH" | "POST_RUNUP";
type M = { ew:number;cagr:number;rawDd:number;ecoDd:number;ext:number;harv:number;sells:number;belowB:boolean };

const ROOT=resolve(fileURLToPath(new URL("..",import.meta.url)));
const DATA_PATH=resolve(ROOT,"src/data/universe.json");
const OUT_DIR=resolve(ROOT,process.env.OUT_DIR ?? "research/qqq_hybrid_downside_convexity_v1");
const H=120, B=1, SELL=0.5;
const RULES:RuleName[]=["ALWAYS_SURPLUS","NEAR_12M_HIGH","AT_12M_HIGH","STRONG_AND_HIGH","POST_RUNUP"];

function monthlyQqq(d:QqqData):MonthlyPoint[]{
  const map=new Map<string,MonthlyPoint>();
  const ds=d.dates??[], cs=d.c.QQQ??[];
  for(let i=0;i<Math.min(ds.length,cs.length);i++){
    const v=Number(cs[i]), date=ds[i];
    if(!Number.isFinite(v)||v<=0||!/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/.test(date)) continue;
    const k=date.slice(0,7), p=map.get(k);
    if(!p||date>p.date) map.set(k,{date,close:v});
  }
  return [...map.values()].sort((a,b)=>a.date.localeCompare(b.date));
}

function maxDd(xs:number[]):number{let peak=0,out=0;for(const x of xs){peak=Math.max(peak,x);if(peak>1e-12)out=Math.min(out,x/peak-1);}return out;}
function high12(pr:number[],i:number):number{return Math.max(...pr.slice(Math.max(0,i-11),i+1));}
function eligible(rule:RuleName,pr:number[],t:number):boolean{
  if(rule==="ALWAYS_SURPLUS") return true;
  const i=t-1; if(i<12) return false;
  const p=pr[i], h=high12(pr,i), near=p>=0.95*h-1e-12;
  if(rule==="NEAR_12M_HIGH") return near;
  if(rule==="AT_12M_HIGH") return p>=h-1e-12;
  const r12=p/pr[i-12]-1;
  if(rule==="STRONG_AND_HIGH") return r12>=0&&near;
  const r6=p/pr[i-6]-1; return r6>=0.15&&near;
}

function clock(pr:number[]):M{
  let sh=0,res=B; const raw=[0],eco=[B];
  for(let t=1;t<=H;t++){const c=Math.min(res,B/H);res-=c;sh+=c/pr[t];const nav=sh*pr[t];raw.push(nav);eco.push(nav+res);}
  const ew=eco[H]; return {ew,cagr:Math.pow(Math.max(1e-12,ew),0.1)-1,rawDd:maxDd(raw.slice(1)),ecoDd:maxDd(eco),ext:1,harv:0,sells:0,belowB:ew<B-1e-10};
}

function simulate(pr:number[],rule:RuleName):M{
  let sh=0,plan=B,harv=0,ext=0,harvest=0,sells=0; const raw=[0],eco=[B];
  for(let t=1;t<=H;t++){
    const target=t/H, prev=pr[t-1], prevNav=sh*prev;
    if(prevNav>target+1e-12 && eligible(rule,pr,t)){
      const sellShares=Math.min(sh,(SELL*(prevNav-target))/Math.max(prev,1e-12));
      if(sellShares>0){const proceeds=sellShares*pr[t];sh-=sellShares;harv+=proceeds;harvest+=proceeds;sells++;}
    } else if(prevNav<target-1e-12){
      let need=target-prevNav;
      const h=Math.min(harv,need); harv-=h; need-=h;
      const p=Math.min(plan,need); plan-=p; need-=p; ext+=p;
      const used=h+p; if(used>0) sh+=used/pr[t];
    }
    const nav=sh*pr[t]; raw.push(nav); eco.push(nav+plan+harv);
  }
  const ew=eco[H]; return {ew,cagr:Math.pow(Math.max(1e-12,ew),0.1)-1,rawDd:maxDd(raw.slice(1)),ecoDd:maxDd(eco),ext,harv:harvest,sells,belowB:ew<B-1e-10};
}

function summary(v:number[]){const s=[...v].sort((a,b)=>a-b),mean=v.reduce((a,b)=>a+b,0)/Math.max(1,v.length);const q=(p:number)=>{const z=(s.length-1)*p,lo=Math.floor(z),hi=Math.ceil(z);return s[lo]+(s[hi]-s[lo])*(z-lo);};return {n:v.length,mean,median:q(.5),q05:q(.05),q25:q(.25),q75:q(.75),q95:q(.95)};}

function run(){
  const d=JSON.parse(readFileSync(DATA_PATH,"utf8")) as QqqData, months=monthlyQqq(d);
  const paths:Array<{start:string;end:string;c:M;v:Record<string,M>}>=[];
  for(let s=0;s+H<months.length;s++){const pr=months.slice(s,s+H+1).map(x=>x.close);const c=clock(pr);const v:Record<string,M>={};for(const r of RULES)v[r]=simulate(pr,r);paths.push({start:months[s].date,end:months[s+H].date,c,v});}
  const failures:string[]=[];
  for(const p of paths){for(const r of RULES){const m=p.v[r];if(m.ext>1+1e-8)failures.push(p.start+" "+r+" budget");if(m.ew<1-1e-8)failures.push(p.start+" "+r+" belowB");}}
  if(failures.length) throw new Error("SELL_TIMING_INVARIANT_FAIL "+failures.slice(0,20).join(" | "));
  const aggregated=RULES.map(r=>{
    const rows=paths.map(p=>({m:p.v[r],c:p.c}));
    const dt=rows.map(x=>x.m.ew-x.c.ew), dr=rows.map(x=>(x.m.rawDd-x.c.rawDd)*100), de=rows.map(x=>(x.m.ecoDd-x.c.ecoDd)*100), dc=rows.map(x=>(x.m.cagr-x.c.cagr)*100);
    return {rule:r,sellFraction:SELL,terminalDelta:summary(dt),rawMaxDdDeltaPp:summary(dr),economicMaxDdDeltaPp:summary(de),cagrDeltaPp:summary(dc),sellEvents:summary(rows.map(x=>x.m.sells)),harvestToReservePercent:summary(rows.map(x=>x.m.harv*100)),externalContributionPercent:summary(rows.map(x=>x.m.ext*100)),positiveTerminalVsClock:dt.filter(x=>x>0).length,terminalBelowB:rows.filter(x=>x.m.belowB).length};
  });
  const report={researchId:"QQQ_MUTUAL_CHASE_SELL_TIMING_V1",status:"RESEARCH_ONLY",provenance:{source:"src/data/universe.json",sourceAsOf:d.asof,monthlyPoints:months.length,completeRollingWindows:paths.length,overlappingWindows:true},fixedRule:{target:"C_t=B*t/120",sellFraction:SELL,decisionData:"t-1 month-end close only",execution:"t month-end close",futurePriceRead:false,parameterSearch:false,rules:RULES},sensitivity:aggregated,windows:paths};
  mkdirSync(OUT_DIR,{recursive:true});
  writeFileSync(resolve(OUT_DIR,"qqq_mutual_chase_sell_timing_v1.json"),JSON.stringify(report,null,2));
  const md=["# QQQ_MUTUAL_CHASE_SELL_TIMING_V1","","> RESEARCH_ONLY / DIAGNOSTIC_ONLY. SELL fraction fixed at 50%; only trigger timing changes.","","| Rule | Mean terminal delta B | Mean raw MaxDD delta | Mean economic MaxDD delta | Mean CAGR delta pp | Mean SELL events | Positive terminal |","| --- | ---: | ---: | ---: | ---: | ---: | ---: |",...aggregated.map(x=>"| "+x.rule+" | "+x.terminalDelta.mean.toFixed(6)+" | "+x.rawMaxDdDeltaPp.mean.toFixed(3)+" pp | "+x.economicMaxDdDeltaPp.mean.toFixed(3)+" pp | "+x.cagrDeltaPp.mean.toFixed(3)+" pp | "+x.sellEvents.mean.toFixed(2)+" | "+x.positiveTerminalVsClock+"/"+paths.length+" |"),"","No rule is promoted automatically."].join("\n");
  writeFileSync(resolve(OUT_DIR,"qqq_mutual_chase_sell_timing_v1.md"),md);
  const header=["startDate","endDate","rule","clockTerminalEW","terminalEW","deltaTerminalEW","clockRawMaxDd","rawMaxDd","deltaRawMaxDd","clockEconomicMaxDd","economicMaxDd","deltaEconomicMaxDd","terminalCagr","cagrDeltaPp","sellEvents","harvestToReserve","externalContribution"];
  const lines=[header.join(",")];
  for(const p of paths) for(const r of RULES){const m=p.v[r];lines.push([p.start,p.end,r,p.c.ew,m.ew,m.ew-p.c.ew,p.c.rawDd,m.rawDd,m.rawDd-p.c.rawDd,p.c.ecoDd,m.ecoDd,m.ecoDd-p.c.ecoDd,m.cagr,(m.cagr-p.c.cagr)*100,m.sells,m.harv,m.ext].map(x=>JSON.stringify(x)).join(","));}
  writeFileSync(resolve(OUT_DIR,"qqq_mutual_chase_sell_timing_v1.csv"),lines.join("\n")+"\n");
  console.log(md);
}
run();