import { readFileSync, mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

type QqqData = { asof:string; dates:string[]; c:{QQQ?:Array<number|null>} };
type MP = { date:string; close:number };
type State = "NORMAL"|"EXTENDED_CANDIDATE"|"ARMED"|"COOLDOWN";
type Variant = "CURRENT_REUSE"|"PROFIT_FLOOR_CREDIT"|"PROFIT_DRAWDOWN_RELEASE";
type M = { ew:number; cagr:number; rawDd:number; ecoDd:number; ext:number; harvest:number; sells:number; release:number; terminalLocked:number; terminalAvailable:number };

const ROOT=resolve(fileURLToPath(new URL("..",import.meta.url)));
const DATA_PATH=resolve(ROOT,"src/data/universe.json");
const OUT_DIR=resolve(ROOT,process.env.OUT_DIR ?? "research/qqq_hybrid_downside_convexity_v1");
const H=120, B=1, SELL=0.10, DD_TRIGGER=-0.10;

function monthly(data:QqqData):MP[]{
  const m=new Map<string,MP>();
  const ds=data.dates??[], cs=data.c.QQQ??[];
  for(let i=0;i<Math.min(ds.length,cs.length);i++){
    const date=ds[i],v=Number(cs[i]);
    if(!Number.isFinite(v)||v<=0||typeof date!=="string"||date.length!==10) continue;
    const k=date.slice(0,7),p=m.get(k);
    if(!p||date>p.date)m.set(k,{date,close:v});
  }
  return [...m.values()].sort((a,b)=>a.date.localeCompare(b.date));
}

function maxDd(xs:number[]):number{
  let peak=0,out=0;
  for(const x of xs){
    peak=Math.max(peak,x);
    if(peak>1e-12)out=Math.min(out,x/peak-1);
  }
  return out;
}

function high12(pr:number[],i:number):number{
  return Math.max(...pr.slice(Math.max(0,i-11),i+1));
}

function extension(pr:number[],i:number):boolean{
  if(i<12)return false;
  const p=pr[i];
  return p>=0.95*high12(pr,i)-1e-12 && p/pr[i-6]-1>=0.15;
}

function drawdown12(pr:number[],i:number):number{
  if(i<12)return 0;
  return pr[i]/high12(pr,i)-1;
}

function summary(xs:number[]){
  const s=[...xs].sort((a,b)=>a-b);
  const mean=xs.reduce((a,b)=>a+b,0)/Math.max(1,xs.length);
  const q=(p:number)=>{
    if(!s.length)return 0;
    const z=(s.length-1)*p,lo=Math.floor(z),hi=Math.ceil(z);
    return s[lo]+(s[hi]-s[lo])*(z-lo);
  };
  return {n:xs.length,mean,median:q(.5),q05:q(.05),q25:q(.25),q75:q(.75),q95:q(.95),positiveRate:xs.filter(x=>x>0).length/Math.max(1,xs.length)};
}

function riskTarget(v:Variant,clock:number,locked:number){
  return v==="CURRENT_REUSE" ? clock : Math.max(0,clock-locked);
}

function clock(pr:number[]):M{
  let sh=0,plan=B;
  const raw=[0],eco=[B];
  for(let t=1;t<=H;t++){
    const c=Math.min(plan,B/H);
    plan-=c;
    sh+=c/pr[t];
    const nav=sh*pr[t];
    raw.push(nav);
    eco.push(nav+plan);
  }
  const ew=eco[H];
  return {ew,cagr:Math.pow(Math.max(1e-12,ew),0.1)-1,rawDd:maxDd(raw.slice(1)),ecoDd:maxDd(eco),ext:B,harvest:0,sells:0,release:0,terminalLocked:0,terminalAvailable:0};
}

function simulate(pr:number[],variant:Variant):M{
  let sh=0,planned=B,locked=0,available=0,ext=0,harvest=0,sells=0,releases=0;
  let state:State="NORMAL";
  let soldInEpisode=false;
  const raw=[0],eco=[B];

  for(let t=1;t<=H;t++){
    const i=t-1,price=pr[i],clockTarget=t/H,prevNav=sh*price;
    const isExt=extension(pr,i);
    const isTrigger=drawdown12(pr,i)<=DD_TRIGGER;

    if(state==="NORMAL"){
      if(isExt){state="EXTENDED_CANDIDATE";soldInEpisode=false;}
    }else if(state==="EXTENDED_CANDIDATE"){
      state=isExt ? "ARMED" : "NORMAL";
    }else if(state==="ARMED"){
      const target=riskTarget(variant,clockTarget,locked);
      if(isExt && prevNav>target+1e-12){
        const sellShares=Math.min(sh,(SELL*(prevNav-target))/Math.max(price,1e-12));
        if(sellShares>0){
          if(soldInEpisode)throw new Error("duplicate SELL inside episode");
          sh-=sellShares;
          const proceeds=sellShares*pr[t];
          locked+=proceeds;
          harvest+=proceeds;
          sells++;
          soldInEpisode=true;
          state="COOLDOWN";
        }
      }else if(!isExt){
        state="NORMAL";
      }
    }else if(state==="COOLDOWN"){
      if(!isExt)state="NORMAL";
    }

    if(variant==="PROFIT_DRAWDOWN_RELEASE" && locked>1e-12 && isTrigger){
      available+=locked;
      locked=0;
      releases++;
    }

    const target=riskTarget(variant,clockTarget,locked);
    if(prevNav<target-1e-12){
      let need=target-prevNav;

      if(variant==="CURRENT_REUSE" || variant==="PROFIT_DRAWDOWN_RELEASE"){
        const fromReserve=Math.min(available,need);
        available-=fromReserve;
        need-=fromReserve;
        const fromPlan=Math.min(planned,need);
        planned-=fromPlan;
        ext+=fromPlan;
        const used=fromReserve+fromPlan;
        if(used>0)sh+=used/pr[t];
      }else{
        const fromPlan=Math.min(planned,need);
        planned-=fromPlan;
        ext+=fromPlan;
        if(fromPlan>0)sh+=fromPlan/pr[t];
      }
    }

    const nav=sh*pr[t];
    raw.push(nav);
    eco.push(nav+planned+locked+available);
  }

  const ew=eco[H];
  return {ew,cagr:Math.pow(Math.max(1e-12,ew),0.1)-1,rawDd:maxDd(raw.slice(1)),ecoDd:maxDd(eco),ext,harvest,sells,release:releases,terminalLocked:locked,terminalAvailable:available};
}

function compare(rows:any[],x:Variant,y:Variant){
  const term=rows.map(r=>r.v[x].ew-r.v[y].ew);
  const raw=rows.map(r=>(r.v[x].rawDd-r.v[y].rawDd)*100);
  const eco=rows.map(r=>(r.v[x].ecoDd-r.v[y].ecoDd)*100);
  const cg=rows.map(r=>(r.v[x].cagr-r.v[y].cagr)*100);
  return {
    terminalDelta:summary(term),
    rawMaxDdDeltaPp:summary(raw),
    economicMaxDdDeltaPp:summary(eco),
    cagrDeltaPp:summary(cg),
    higherTerminalWindows:term.filter(x=>x>0).length,
    lowerRawDdWindows:raw.filter(x=>x<0).length,
    lowerEconomicDdWindows:eco.filter(x=>x<0).length,
    higherCagrWindows:cg.filter(x=>x>0).length
  };
}

function run(){
  const data=JSON.parse(readFileSync(DATA_PATH,"utf8")) as QqqData;
  const ms=monthly(data);
  const variants:Variant[]=["CURRENT_REUSE","PROFIT_FLOOR_CREDIT","PROFIT_DRAWDOWN_RELEASE"];
  const rows:any[]=[];

  for(let s=0;s+H<ms.length;s++){
    const pr=ms.slice(s,s+H+1).map(x=>x.close);
    const c=clock(pr);
    const v={} as Record<Variant,M>;
    for(const x of variants)v[x]=simulate(pr,x);
    rows.push({start:ms[s].date,end:ms[s+H].date,c,v});
  }

  const failures:string[]=[];
  for(const r of rows){
    for(const x of variants){
      const m=r.v[x];
      if(m.ext>B+1e-8)failures.push(r.start+" "+x+" external budget");
      if(m.ew<1-1e-8)failures.push(r.start+" "+x+" principal breach");
      if(!Number.isFinite(m.ew))failures.push(r.start+" "+x+" non-finite");
    }
  }
  if(failures.length)throw new Error("PROFIT_TARGET_RESERVE_INVARIANT_FAIL "+failures.slice(0,20).join(" | "));

  const vsClock=Object.fromEntries(variants.map(x=>[x,{
    terminalDelta:summary(rows.map(r=>r.v[x].ew-r.c.ew)),
    rawMaxDdDeltaPp:summary(rows.map(r=>(r.v[x].rawDd-r.c.rawDd)*100)),
    economicMaxDdDeltaPp:summary(rows.map(r=>(r.v[x].ecoDd-r.c.ecoDd)*100)),
    cagrDeltaPp:summary(rows.map(r=>(r.v[x].cagr-r.c.cagr)*100)),
    externalContributionPercent:summary(rows.map(r=>r.v[x].ext*100)),
    harvestPercent:summary(rows.map(r=>r.v[x].harvest*100)),
    sellEvents:summary(rows.map(r=>r.v[x].sells)),
    releaseEvents:summary(rows.map(r=>r.v[x].release)),
    terminalLockedPercent:summary(rows.map(r=>r.v[x].terminalLocked*100)),
    terminalAvailablePercent:summary(rows.map(r=>r.v[x].terminalAvailable*100)),
    positiveTerminalVsClock:rows.filter(r=>r.v[x].ew>r.c.ew).length
  }]));

  const incrementalVsCurrent={
    PROFIT_FLOOR_CREDIT:compare(rows,"PROFIT_FLOOR_CREDIT","CURRENT_REUSE"),
    PROFIT_DRAWDOWN_RELEASE:compare(rows,"PROFIT_DRAWDOWN_RELEASE","CURRENT_REUSE")
  };
  const releaseVsFloor=compare(rows,"PROFIT_DRAWDOWN_RELEASE","PROFIT_FLOOR_CREDIT");

  const report={
    researchId:"QQQ_MUTUAL_CHASE_PROFIT_TARGET_RESERVE_V1",
    status:"RESEARCH_ONLY",
    provenance:{source:"src/data/universe.json",sourceAsOf:data.asof,monthlyPoints:ms.length,completeRollingWindows:rows.length,overlappingWindows:true},
    fixedRule:{clock:"C_t=B*t/120",sellFraction:SELL,postRunup:"prior QQQ 6M return >= +15% and price >= 95% trailing 12M high",confirmation:2,cooldown:"one SELL maximum per episode",decision:"t-1 month-end",execution:"t month-end close",futurePriceRead:false,parameterSearch:false,drawdownReleaseTrigger:DD_TRIGGER},
    variants:{
      CURRENT_REUSE:"NAV target; harvested reserve reused for buys",
      PROFIT_FLOOR_CREDIT:"riskTarget=max(0,C_t-lockedHarvest); locked reserve never redeployed normally",
      PROFIT_DRAWDOWN_RELEASE:"same Floor Credit; locked reserve released on prior QQQ 12M drawdown <= -10%"
    },
    comparisonVsClock:vsClock,
    incrementalVsCurrent,
    incrementalReleaseVsFloor:releaseVsFloor,
    windows:rows
  };

  mkdirSync(OUT_DIR,{recursive:true});
  writeFileSync(resolve(OUT_DIR,"qqq_mutual_chase_profit_target_reserve_v1.json"),JSON.stringify(report,null,2));

  const md=[
    "# QQQ_MUTUAL_CHASE_PROFIT_TARGET_RESERVE_V1",
    "",
    "> RESEARCH_ONLY / DIAGNOSTIC_ONLY.",
    "",
    "## Fixed variants",
    "",
    "- CURRENT_REUSE: NAV target; harvested reserve reused for BUY.",
    "- PROFIT_FLOOR_CREDIT: harvested reserve lowers the risky target and stays protected.",
    "- PROFIT_DRAWDOWN_RELEASE: same protected reserve, but it becomes reusable after prior QQQ 12M drawdown <= -10%.",
    "",
    "## Results versus CLOCK",
    "",
    "| Variant | Mean terminal dB | Mean raw MaxDD d | Mean economic MaxDD d | Mean CAGR d pp | Mean SELL | Mean releases | Positive terminal |",
    "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ...variants.map(x=>{const z=vsClock[x];return "| "+x+" | "+z.terminalDelta.mean.toFixed(6)+" | "+z.rawMaxDdDeltaPp.mean.toFixed(3)+" pp | "+z.economicMaxDdDeltaPp.mean.toFixed(3)+" pp | "+z.cagrDeltaPp.mean.toFixed(3)+" pp | "+z.sellEvents.mean.toFixed(2)+" | "+z.releaseEvents.mean.toFixed(2)+" | "+z.positiveTerminalVsClock+"/"+rows.length+" |";}),
    "",
    "## Incremental versus CURRENT_REUSE",
    ...Object.entries(incrementalVsCurrent).flatMap(([x,z]:any)=>[
      "### "+x,
      "- Mean terminal dB: "+z.terminalDelta.mean.toFixed(6),
      "- Mean raw MaxDD d: "+z.rawMaxDdDeltaPp.mean.toFixed(3)+" pp",
      "- Mean economic MaxDD d: "+z.economicMaxDdDeltaPp.mean.toFixed(3)+" pp",
      "- Mean CAGR d: "+z.cagrDeltaPp.mean.toFixed(3)+" pp",
      "- Higher terminal windows: "+z.higherTerminalWindows+"/"+rows.length,
      "- Lower economic MaxDD windows: "+z.lowerEconomicDdWindows+"/"+rows.length,
      ""
    ]),
    "## Release effect: PROFIT_DRAWDOWN_RELEASE minus PROFIT_FLOOR_CREDIT",
    "- Mean terminal dB: "+releaseVsFloor.terminalDelta.mean.toFixed(6),
    "- Mean economic MaxDD d: "+releaseVsFloor.economicMaxDdDeltaPp.mean.toFixed(3)+" pp",
    "- Mean CAGR d: "+releaseVsFloor.cagrDeltaPp.mean.toFixed(3)+" pp",
    "",
    "No variant is promoted automatically."
  ].join("\n");

  writeFileSync(resolve(OUT_DIR,"qqq_mutual_chase_profit_target_reserve_v1.md"),md);
  console.log(JSON.stringify({provenance:report.provenance,comparisonVsClock:report.comparisonVsClock,incrementalVsCurrent:report.incrementalVsCurrent,incrementalReleaseVsFloor:report.incrementalReleaseVsFloor},null,2));
}

run();