import { readFileSync, mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

type QqqData={asof:string;dates:string[];c:{QQQ?:Array<number|null>}};
type MP={date:string;close:number};
type State="NORMAL"|"EXTENDED_CANDIDATE"|"ARMED"|"COOLDOWN";
type Variant="CURRENT_STATE_MACHINE"|"PROFIT_HOLD";
type M={ew:number;cagr:number;rawDd:number;ecoDd:number;ext:number;harvest:number;sells:number;holds:number;terminalReserve:number};

const ROOT=resolve(fileURLToPath(new URL("..",import.meta.url)));
const DATA_PATH=resolve(ROOT,"src/data/universe.json");
const OUT_DIR=resolve(ROOT,process.env.OUT_DIR??"research/qqq_hybrid_downside_convexity_v1");
const H=120,B=1,SELL=0.10;

function monthly(data:QqqData):MP[]{
  const m=new Map<string,MP>(),ds=data.dates??[],cs=data.c.QQQ??[];
  for(let i=0;i<Math.min(ds.length,cs.length);i++){
    const date=ds[i],v=Number(cs[i]);
    if(typeof date!=="string"||date.length!==10||!Number.isFinite(v)||v<=0)continue;
    const k=date.slice(0,7),p=m.get(k);
    if(!p||date>p.date)m.set(k,{date,close:v});
  }
  return [...m.values()].sort((a,b)=>a.date.localeCompare(b.date));
}

function maxDd(xs:number[]):number{let peak=0,out=0;for(const x of xs){peak=Math.max(peak,x);if(peak>1e-12)out=Math.min(out,x/peak-1)}return out}
function high12(pr:number[],i:number){return Math.max(...pr.slice(Math.max(0,i-11),i+1))}
function extension(pr:number[],i:number){if(i<12)return false;return pr[i]>=0.95*high12(pr,i)-1e-12&&pr[i]/pr[i-6]-1>=0.15}
function summary(xs:number[]){
  const s=[...xs].sort((a,b)=>a-b),mean=xs.reduce((a,b)=>a+b,0)/Math.max(1,xs.length);
  const q=(p:number)=>{const z=(s.length-1)*p,lo=Math.floor(z),hi=Math.ceil(z);return s[lo]+(s[hi]-s[lo])*(z-lo)};
  return{n:xs.length,mean,median:q(.5),q05:q(.05),q25:q(.25),q75:q(.75),q95:q(.95),positiveRate:xs.filter(x=>x>0).length/Math.max(1,xs.length)};
}

function clock(pr:number[]):M{
  let sh=0,plan=1;const raw=[0],eco=[1];
  for(let t=1;t<=H;t++){const c=Math.min(plan,1/H);plan-=c;sh+=c/pr[t];const nav=sh*pr[t];raw.push(nav);eco.push(nav+plan)}
  const ew=eco[H];
  return{ew,cagr:Math.pow(ew,.1)-1,rawDd:maxDd(raw.slice(1)),ecoDd:maxDd(eco),ext:1,harvest:0,sells:0,holds:0,terminalReserve:plan};
}

function sim(pr:number[],variant:Variant):M{
  let sh=0,plan=1,reserve=0,harvest=0,sells=0,holds=0,state:State="NORMAL",holdTarget:number|null=null;
  const raw=[0],eco=[1];

  for(let t=1;t<=H;t++){
    const i=t-1,p=pr[i],clockTarget=t/H,prevNav=sh*p,e=extension(pr,i);
    if(state==="NORMAL"){
      if(e)state="EXTENDED_CANDIDATE";
    }else if(state==="EXTENDED_CANDIDATE"){
      state=e?"ARMED":"NORMAL";
    }else if(state==="ARMED"){
      const activeTarget=(variant==="PROFIT_HOLD"&&holdTarget!==null)?holdTarget:clockTarget;
      if(e&&prevNav>activeTarget+1e-12){
        const sellSh=Math.min(sh,SELL*(prevNav-activeTarget)/Math.max(p,1e-12));
        if(sellSh>0){
          if(holdTarget!==null)throw new Error("existing hold before new SELL");
          sh-=sellSh;
          const proceeds=sellSh*pr[t];
          reserve+=proceeds;harvest+=proceeds;sells++;
          if(variant==="PROFIT_HOLD"){holdTarget=activeTarget;holds++}
          state="COOLDOWN";
        }
      }else if(!e){
        state="NORMAL";
      }
    }else{
      if(!e){state="NORMAL";if(variant==="PROFIT_HOLD")holdTarget=null}
    }

    const held=variant==="PROFIT_HOLD"&&state==="COOLDOWN"&&holdTarget!==null;
    const activeTarget=variant==="PROFIT_HOLD"&&holdTarget!==null?holdTarget:clockTarget;

    if(!held&&prevNav<activeTarget-1e-12){
      let need=activeTarget-prevNav;
      const fromReserve=Math.min(reserve,need);reserve-=fromReserve;need-=fromReserve;
      const fromPlan=Math.min(plan,need);plan-=fromPlan;
      const used=fromReserve+fromPlan;
      if(used>0)sh+=used/pr[t];
    }

    const nav=sh*pr[t];raw.push(nav);eco.push(nav+plan+reserve);
  }

  const ew=eco[H];
  return{ew,cagr:Math.pow(ew,.1)-1,rawDd:maxDd(raw.slice(1)),ecoDd:maxDd(eco),ext:1-plan,harvest,sells,holds,terminalReserve:plan+reserve};
}

function cmp(rows:any[],x:Variant,y:"CLOCK"|Variant){
  const term=rows.map(r=>r.v[x].ew-(y==="CLOCK"?r.c.ew:r.v[y].ew));
  const raw=rows.map(r=>(r.v[x].rawDd-(y==="CLOCK"?r.c.rawDd:r.v[y].rawDd))*100);
  const eco=rows.map(r=>(r.v[x].ecoDd-(y==="CLOCK"?r.c.ecoDd:r.v[y].ecoDd))*100);
  const cg=rows.map(r=>(r.v[x].cagr-(y==="CLOCK"?r.c.cagr:r.v[y].cagr))*100);
  return{terminal:summary(term),rawDd:summary(raw),ecoDd:summary(eco),cagr:summary(cg),higherTerminal:term.filter(z=>z>0).length,lowerRawDd:raw.filter(z=>z<0).length,lowerEcoDd:eco.filter(z=>z<0).length,higherCagr:cg.filter(z=>z>0).length};
}

function run(){
  const data=JSON.parse(readFileSync(DATA_PATH,"utf8")) as QqqData;
  const ms=monthly(data),rows:any[]=[];
  const variants:Variant[]=["CURRENT_STATE_MACHINE","PROFIT_HOLD"];
  for(let s=0;s+H<ms.length;s++){
    const pr=ms.slice(s,s+H+1).map(x=>x.close);
    const c=clock(pr),v={} as Record<Variant,M>;
    for(const x of variants)v[x]=sim(pr,x);
    rows.push({start:ms[s].date,end:ms[s+H].date,c,v});
  }

  const failures:string[]=[];
  for(const r of rows)for(const x of variants){
    if(r.v[x].ew<1-1e-8)failures.push(r.start+" "+x+" principal breach");
    if(r.v[x].ext>1+1e-8)failures.push(r.start+" "+x+" external budget");
  }
  if(failures.length)throw new Error("PROFIT_HOLD_INVARIANT_FAIL "+failures.slice(0,20).join(" | "));

  const report={
    researchId:"QQQ_MUTUAL_CHASE_PROFIT_HOLD_V1",
    status:"RESEARCH_ONLY",
    provenance:{source:"src/data/universe.json",sourceAsOf:data.asof,monthlyPoints:ms.length,completeRollingWindows:rows.length,overlappingWindows:true},
    fixedRule:{clock:"C_t=B*t/120",sellFraction:SELL,postRunup:"prior QQQ 6M return >= +15% and price >=95% trailing 12M high",confirmation:2,decision:"t-1 month-end",execution:"t month-end close",futurePriceRead:false,parameterSearch:false},
    variants:{CURRENT_STATE_MACHINE:"clock target; harvested reserve reusable",PROFIT_HOLD:"freeze target at harvest target until extension breaks; reserve held during episode"},
    comparisonVsClock:Object.fromEntries(variants.map(x=>[x,cmp(rows,x,"CLOCK")])),
    incrementalVsCurrent:cmp(rows,"PROFIT_HOLD","CURRENT_STATE_MACHINE"),
    windows:rows
  };

  mkdirSync(OUT_DIR,{recursive:true});
  writeFileSync(resolve(OUT_DIR,"qqq_mutual_chase_profit_hold_v1.json"),JSON.stringify(report,null,2));
  const md=[
    "# QQQ_MUTUAL_CHASE_PROFIT_HOLD_V1","",
    "> RESEARCH_ONLY / DIAGNOSTIC_ONLY.","",
    "| Variant | Mean terminal dB | Mean raw MaxDD d | Mean economic MaxDD d | Mean CAGR d pp | Mean SELL | Mean holds | Higher terminal |",
    "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ...variants.map(x=>{const z=report.comparisonVsClock[x],avgSell=rows.map(r=>r.v[x].sells).reduce((a,b)=>a+b,0)/rows.length,avgHold=rows.map(r=>r.v[x].holds).reduce((a,b)=>a+b,0)/rows.length;return"| "+x+" | "+z.terminal.mean.toFixed(6)+" | "+z.rawDd.mean.toFixed(3)+" pp | "+z.ecoDd.mean.toFixed(3)+" pp | "+z.cagr.mean.toFixed(3)+" pp | "+avgSell.toFixed(2)+" | "+avgHold.toFixed(2)+" | "+z.higherTerminal+"/"+rows.length+" |";}),
    "","## PROFIT_HOLD incremental vs CURRENT_STATE_MACHINE","",
    "- Mean terminal dB: "+report.incrementalVsCurrent.terminal.mean.toFixed(6),
    "- Mean raw MaxDD d: "+report.incrementalVsCurrent.rawDd.mean.toFixed(3)+" pp",
    "- Mean economic MaxDD d: "+report.incrementalVsCurrent.ecoDd.mean.toFixed(3)+" pp",
    "- Mean CAGR d: "+report.incrementalVsCurrent.cagr.mean.toFixed(3)+" pp",
    "- Higher terminal windows: "+report.incrementalVsCurrent.higherTerminal+"/"+rows.length,
    "- Lower economic MaxDD windows: "+report.incrementalVsCurrent.lowerEcoDd+"/"+rows.length,
    "- Higher CAGR windows: "+report.incrementalVsCurrent.higherCagr+"/"+rows.length,
    "","No automatic promotion."
  ].join("\n");
  writeFileSync(resolve(OUT_DIR,"qqq_mutual_chase_profit_hold_v1.md"),md);
  console.log(JSON.stringify({provenance:report.provenance,comparisonVsClock:report.comparisonVsClock,incrementalVsCurrent:report.incrementalVsCurrent},null,2));
}
run();