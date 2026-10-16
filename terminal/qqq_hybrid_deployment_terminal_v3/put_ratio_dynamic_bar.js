(function(root){
"use strict";
const POLICY_IDS=["DTE7_CLOSE_SHORT_RISK","DTE7_CLOSE_SHORT_AND_SELL_LONG_IF_EXECUTABLE"];
const STATUS={0:"BAR_SAMPLE_OK_DIAGNOSTIC_ONLY",1:"PENDING_SMALL_EPISODE_SAMPLE",2:"BLOCKED_NO_EXECUTED_EPISODES"};
function validateSnapshot(s){
  const reasons=[];
  if(!s||s.schemaVersion!=="QQQ_PUT_RATIO_DYNAMIC_BAR_SNAPSHOT_V1")reasons.push("Unsupported dynamic BAR snapshot schema.");
  const m=s?.metadata||{};
  if(m.start!=="2018-03-01"||m.end!=="2025-12-15"||Number(m.episodes)!==62)reasons.push("Dynamic BAR source window / cohort mismatch.");
  if(m.direction!=="SHORT_HEAVY_1_LONG_N_SHORT"||Number(m.long)!==1||Number(m.short)!==5)reasons.push("Dynamic BAR snapshot is not the exact LONG 1 : SHORT 5 cohort.");
  if(m.sizing!=="FIXED_1_UNIT_BUDGET_BYPASS"||Number(m.allowedUnits)!==0||Number(m.budgetBreachEpisodes)!==62||!(Number(m.oneUnitWorstTerminalLossUsd)>Number(m.budgetUsd)))reasons.push("Budget-bypass diagnostic gate is missing or inconsistent.");
  if(s?.status!=="RESEARCH_DIAGNOSTIC_ONLY_BUDGET_BYPASS")reasons.push("Deployment-blocked status is missing.");
  if(!Array.isArray(s?.policies)||s.policies.length!==2||!POLICY_IDS.every(id=>s.policies.some(p=>p.id===id)))reasons.push("Required DTE7 policy comparison is incomplete.");
  if(!Array.isArray(s?.barRows)||s.barRows.length!==162)reasons.push("Dynamic BAR row count mismatch.");
  if(!Array.isArray(s?.drawdownRows)||s.drawdownRows.length!==14)reasons.push("Dynamic drawdown row count mismatch.");
  if(!Array.isArray(m.states)||m.states.length!==9||!Array.isArray(m.barTypes)||m.barTypes.length!==3)reasons.push("Dynamic BAR state/type dictionaries are incomplete.");
  const seen=new Set();
  for(const r of (s?.barRows||[])){
    if(!Array.isArray(r)||r.length!==11){reasons.push("Malformed BAR row.");break;}
    const [p,st,bt,level,n,hits,pct,marks,markHits,markPct,code]=r;
    if(!Number.isInteger(p)||p<0||p>=2||!Number.isInteger(st)||st<0||st>=9||!Number.isInteger(bt)||bt<0||bt>=3||![0.5,1,2].includes(Number(level))||!Number.isInteger(n)||n<0||!Number.isInteger(hits)||hits<0||hits>n||!Number.isInteger(marks)||marks<0||!Number.isInteger(markHits)||markHits<0||markHits>marks||![0,1,2].includes(code)){
      reasons.push("BAR row contains out-of-range fields.");break;
    }
    if(n>0&&pct!==null&&Math.abs(Number(pct)-100*hits/n)>0.02) {reasons.push("BAR episode percentage does not match hits / denominator.");break;}
    if(marks>0&&markPct!==null&&Math.abs(Number(markPct)-100*markHits/marks)>0.02) {reasons.push("BAR mark percentage does not match hits / denominator.");break;}
    const key=[p,st,bt,level].join("|");
    if(seen.has(key)){reasons.push("Duplicate BAR row.");break;}
    seen.add(key);
  }
  if(seen.size!==162)reasons.push("Dynamic BAR combinations are missing.");
  for(const r of (s?.drawdownRows||[])){
    if(!Array.isArray(r)||r.length!==10||![0,1].includes(r[0])||![3,5,10,15,20,25,30].includes(r[1])||!Number.isInteger(r[2])||r[2]<0){reasons.push("Malformed drawdown row.");break;}
  }
  if(!m.runUrl||!/^https:\/\/github\.com\/JUN-ZS\/brush-timber-mountain-brook\/actions\/runs\/\d+$/.test(m.runUrl)||!/^([0-9a-f]{40})$/.test(String(m.testedCommit||"")))reasons.push("Research run provenance is incomplete.");
  return {ok:reasons.length===0,reasons};
}
function policyById(s,id){return (s?.policies||[]).find(p=>p.id===id)||null;}
function barRowsFor(s,policyIndex,stateIndex){
  return (s?.barRows||[]).filter(r=>Number(r[0])===Number(policyIndex)&&Number(r[1])===Number(stateIndex)).map(r=>({
    policyIndex:r[0],stateIndex:r[1],barTypeIndex:r[2],levelPct:r[3],episodeN:r[4],episodeHits:r[5],episodePct:r[6],
    markN:r[7],markHits:r[8],markPct:r[9],sampleStatus:STATUS[r[10]]||"PENDING"
  })).sort((a,b)=>a.barTypeIndex-b.barTypeIndex||a.levelPct-b.levelPct);
}
function drawdownRowsFor(s,policyIndex){
  return (s?.drawdownRows||[]).filter(r=>Number(r[0])===Number(policyIndex)).map(r=>({
    policyIndex:r[0],levelPct:r[1],cycles:r[2],cyclesPerYear:r[3],eventYearPct:r[4],eventYears:r[5],
    daysAtOrBelow:r[6],dayPct:r[7],validDays:r[8],missingNavMarks:r[9]
  })).sort((a,b)=>a.levelPct-b.levelPct);
}
const api={validateSnapshot,policyById,barRowsFor,drawdownRowsFor};
if(typeof module!=="undefined"&&module.exports)module.exports=api;else root.PutRatioDynamicBarV1=api;
})(typeof window!=="undefined"?window:globalThis);
