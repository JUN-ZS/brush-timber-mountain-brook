window.HybridEngine = (()=>{
  const POLICY=Object.freeze({
    corePct:42,
    vxxNormalPct:18,
    vxxHighPct:10,
    vxxCallBudgetPct:2,
    qqqCallBudgetPct:1.2,
    vixHigh:28,
    termSafe:5,
    qqqRollDte:14,
    qqqRollDelta:.16,
    vxxRollDte:14,
    vxxRollDelta:.20
  });
  const num=(v,d=null)=>{if(v===null||v===undefined||v==="")return d;const x=parseFloat(String(v).replace(/,/g,""));return Number.isFinite(x)?x:d};
  const term=(m1,m2)=>Number.isFinite(m1)&&Number.isFinite(m2)&&m1!==0?(m2-m1)/m1*100:null;
  const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
  function derive(d,opts={}){
    if(![d.qqq,d.vxx,d.vix].every(Number.isFinite)) return {state:"DATA INCOMPLETE",action:"HOLD",conf:5,gate:"BLOCKED",why:"Need QQQ + VXX + VIX. / 需要 QQQ、VXX、VIX。",vxxTarget:0,vxxCalls:0,reasons:["missing spot"],blocked:true};
    if(!Number.isFinite(d.s)) return {state:"DATA INCOMPLETE",action:"HOLD",conf:35,gate:"BLOCKED",why:"M1/M2 unavailable. No term-structure guess is permitted. / M1/M2 未有資料，禁止猜期限結構。",vxxTarget:0,vxxCalls:0,reasons:["M1/M2 missing"],blocked:true};
    const persistent=opts.persistent!==false;
    const high=d.vix>=POLICY.vixHigh, back=d.s<=0;
    let state,action,conf,why;
    if(high&&back){state="SHOCK";action="REDUCE";conf=97;why="High VIX + backwardation: reduce VXX seller legs first; QQQ core stays intact. / 高 VIX＋倒掛：先減 VXX 賣方，QQQ 核心保持。";}
    else if(back){state="PRE-SHOCK";action="REDUCE";conf=92;why="Backwardation removes the carry gate; stop adding short-vol carry. / 倒掛令 carry 閘門失效，停止追加 short-vol carry。";}
    else if(high){state="PRE-SHOCK";action="REDUCE";conf=88;why="VIX is high: cap VXX seller exposure and avoid new carry. / VIX 高，封頂 VXX 空頭並停止新 carry。";}
    else if(d.s<=POLICY.termSafe){state="WEAKENING";action="HOLD";conf=79;why="Contango is positive but thin: hold QQQ core and wait. / Contango 仍正但變薄，保留 QQQ 核心並等待。";}
    else{state="CARRY";action="BUY";conf=90;why="Supportive contango with VIX below high threshold: restore carry legs toward target. / Contango 充足且 VIX 未過閾值，向目標恢復 carry。";}
    const base=high?POLICY.vxxHighPct:POLICY.vxxNormalPct;
    const vxxTarget=back?0:base;
    const vxxCalls=(back||high)?0:POLICY.vxxCallBudgetPct;
    return {state,action,conf,gate:back?"CUT":high?"CAP":"OPEN",why,vxxTarget,vxxCalls,reasons:[high?"VIX ≥ 28":"VIX < 28",back?"S ≤ 0":"S > 0",d.s>POLICY.termSafe?"S > 5%":"S ≤ 5%"],blocked:false,persistent};
  }
  function optionQty(nav,budgetPct,credit){return nav>0&&credit>0?Math.max(0,Math.floor(nav*(budgetPct/100)/(credit*100))):0}
  function targets(d,e,ledger){
    const nav=num(ledger.nav,0), curShares=num(ledger.curQqq,100), curVxx=num(ledger.curVxx,0), curQCall=num(ledger.curQCall,0), curVCall=num(ledger.curVCall,0);
    // Critical safety rule: blocked data can never manufacture a target of zero.
    if(e.blocked){
      return {
        QQQ:{current:curShares,target:curShares,unit:"shares"},
        VXX:{current:curVxx,target:curVxx,unit:"% NAV"},
        QQQ_CALL:{current:curQCall,target:curQCall,unit:"spreads"},
        VXX_CALL:{current:curVCall,target:curVCall,unit:"spreads"},
        blocked:true
      };
    }
    const rawQqqTarget=nav>0&&Number.isFinite(d.qqq)?nav*(POLICY.corePct/100)/d.qqq:100;
    const rawQqqCalls=optionQty(nav,POLICY.qqqCallBudgetPct,num(document?.getElementById("qqqCredit")?.value,0));
    const rawVxxCalls=e.vxxCalls>0?optionQty(nav,POLICY.vxxCallBudgetPct,num(document?.getElementById("vxxCredit")?.value,0)):0;
    // In HOLD/REDUCE regimes, targets are ceilings: never create an ADD signal while the engine says reduce.
    const allowAdd=e.action==="BUY";
    const qqqTarget=allowAdd?rawQqqTarget:curShares;
    const qqqCalls=allowAdd?rawQqqCalls:Math.min(curQCall,rawQqqCalls);
    const vxxTarget=allowAdd?e.vxxTarget:Math.min(curVxx,e.vxxTarget);
    const vxxCalls=allowAdd?rawVxxCalls:Math.min(curVCall,rawVxxCalls);
    return {
      QQQ:{current:curShares,target:qqqTarget,unit:"shares"},
      VXX:{current:curVxx,target:vxxTarget,unit:"% NAV"},
      QQQ_CALL:{current:curQCall,target:qqqCalls,unit:"spreads"},
      VXX_CALL:{current:curVCall,target:vxxCalls,unit:"spreads"},
      blocked:false
    };
  }
  function delta(cur,tgt){const d=tgt-cur;if(Math.abs(d)<1e-9)return{kind:"hold",diff:0,label:"HOLD / 保持"};return d>0?{kind:"add",diff:d,label:"ADD / 加倉"}:{kind:"reduce",diff:d,label:"REDUCE / 減倉"};}
  function triggers(d,e,opt={}){
    const out=[];
    if(Number.isFinite(d.s))out.push({id:"TERM_ZERO",title:"S ≤ 0 / 倒掛",value:d.s<=0?"BREACHED / 已觸發":`${d.s.toFixed(2)}% → 0`,fire:d.s<=0,priority:"HIGH"});
    else out.push({id:"TERM_ZERO",title:"M1/M2 / 期限結構",value:"MISSING / 缺失",fire:true,priority:"BLOCK"});
    if(Number.isFinite(d.vix))out.push({id:"VIX_HIGH",title:"VIX ≥ 28 / 高 VIX",value:d.vix>=POLICY.vixHigh?"BREACHED / 已觸發":`${(POLICY.vixHigh-d.vix).toFixed(2)} away`,fire:d.vix>=POLICY.vixHigh,priority:"HIGH"});
    const qd=num(opt.qqqDte), qdel=num(opt.qqqDelta), vd=num(opt.vxxDte), vdel=num(opt.vxxDelta);
    const qFire=(Number.isFinite(qd)&&qd<=POLICY.qqqRollDte)||(Number.isFinite(qdel)&&qdel>=POLICY.qqqRollDelta);
    const vFire=(Number.isFinite(vd)&&vd<=POLICY.vxxRollDte)||(Number.isFinite(vdel)&&vdel>=POLICY.vxxRollDelta)||e.state==="SHOCK";
    out.push({id:"QQQ_ROLL",title:"QQQ Far Call / 遠價 Call",value:`DTE ${Number.isFinite(qd)?qd:"—"} · Δ ${Number.isFinite(qdel)?qdel.toFixed(2):"—"}`,fire:qFire,priority:"MED"});
    out.push({id:"VXX_ROLL",title:"VXX Call Spread / VXX Call",value:`DTE ${Number.isFinite(vd)?vd:"—"} · Δ ${Number.isFinite(vdel)?vdel.toFixed(2):"—"}`,fire:vFire,priority:"HIGH"});
    return out;
  }
  function candidateFromChain(chain,spot,targetDelta=.10){
    if(!Array.isArray(chain)||!chain.length||!Number.isFinite(spot))return null;
    const valid=chain.filter(x=>Number.isFinite(num(x.strike))&&Number.isFinite(num(x.delta))&&Number.isFinite(num(x.days))&&num(x.days)>0&&num(x.delta)>0&&num(x.delta)<=.25);
    if(!valid.length)return null;
    valid.sort((a,b)=>Math.abs(num(a.delta)-targetDelta)-Math.abs(num(b.delta)-targetDelta));
    const s=valid[0];
    const longs=valid.filter(x=>num(x.strike)>num(s.strike));
    if(!longs.length)return null;
    longs.sort((a,b)=>Math.abs(num(a.strike)-num(s.strike)*1.015)-Math.abs(num(b.strike)-num(s.strike)*1.015));
    const l=longs[0];
    return {shortStrike:num(s.strike),longStrike:num(l.strike),dte:num(s.days),delta:num(s.delta),credit:null,source:"LIVE CANDIDATE / 即時候選"};
  }
  return {POLICY,term,derive,targets,delta,triggers,candidateFromChain,num,clamp};
})();
