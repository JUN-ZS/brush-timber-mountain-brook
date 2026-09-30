from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from math import ceil
from typing import Optional

N_SHORT=10
LONG_DELTA=0.50
MAX_STACK=5
COVERAGE_MULT=1.50
NEAR_TP=0.50
NEAR_ROLL_DTE=2
STALE_ORDER_SEC=120
MAX_QUOTE_AGE_SEC=45

@dataclass
class Contract:
    code:str; right:str; strike:float; expiry:str; dte:int
    bid:Optional[float]; ask:Optional[float]; delta:Optional[float]; gamma:Optional[float]
    iv:Optional[float]=None; lot_size:int=100
    @property
    def mid(self):
        return (self.bid+self.ask)/2 if self.bid is not None and self.ask is not None and self.ask>=self.bid else (self.bid if self.bid is not None else self.ask)

@dataclass
class Position:
    code:str; side:str; qty:int; avg_cost:float
    strike:Optional[float]=None; expiry:Optional[str]=None; dte:Optional[int]=None
    delta:Optional[float]=None; gamma:Optional[float]=None

@dataclass
class Order:
    order_id:str; code:str; side:str; qty:int; price:Optional[float]; status:str; updated_at:str

def _dt(s):
    try:return datetime.fromisoformat(str(s).replace("Z","+00:00"))
    except Exception:return None

def quote_age_sec(s,now=None):
    t=_dt(s)
    if t is None:return None
    now=now or datetime.now(timezone.utc)
    return max(0,(now-t).total_seconds())

def risk_state(far,spot,gamma_baseline=None,prev_delta=None):
    da=abs(float(far.delta or 0))
    dist=(far.strike-spot)/spot if spot>0 else 0
    ds=1 if da<.04 else 2 if da<.06 else 3 if da<.08 else 4 if da<.10 else 5
    xs=1 if dist>.10 else 2 if dist>.07 else 3 if dist>.04 else 4 if dist>.02 else 5
    gr=1.0 if not gamma_baseline or not far.gamma else abs(float(far.gamma))/gamma_baseline
    dj=0 if prev_delta is None else abs(da-prev_delta)
    gs=1 if gr<1.20 and dj<.01 else 2 if gr<1.50 and dj<.02 else 3
    score=.50*ds+.30*xs+.20*gs
    target=max(1,min(MAX_STACK,ceil((COVERAGE_MULT*N_SHORT*da)/LONG_DELTA)))
    if score>=4.2: target=min(MAX_STACK,target+2)
    elif score>=3.2: target=min(MAX_STACK,target+1)
    return {"far_delta_abs":da,"distance_pct":dist,"gamma_rel":gr,"delta_jump":dj,
            "dscore":ds,"xscore":xs,"gscore":gs,"risk_score":score,"desired_stack":target}

def select_far(cs,spot,dte_target,delta_target):
    xs=[c for c in cs if c.right=="CALL" and c.strike>spot and 60<=c.dte<=210 and c.bid is not None and c.ask is not None and c.ask>=c.bid and c.delta is not None]
    if not xs:return None
    xs.sort(key=lambda c:(abs(c.dte-dte_target),abs(abs(c.delta)-delta_target),c.strike))
    return xs[0]

def select_near(cs,spot,dte_target):
    xs=[c for c in cs if c.right=="CALL" and c.strike<=spot*1.01 and 7<=c.dte<=35 and c.bid is not None and c.ask is not None and c.ask>=c.bid and c.delta is not None]
    if not xs:return None
    xs.sort(key=lambda c:(abs(c.dte-dte_target),abs(abs(c.delta)-LONG_DELTA),c.strike))
    return xs[0]

def plan(*,market,far,near,positions,orders,signal_active,far_campaign_active,
         quotes_by_code=None,gamma_baseline=None,previous_far_delta_abs=None,now=None):
    now=now or datetime.now(timezone.utc)
    qage=quote_age_sec(market.get("timestamp"),now)
    if market.get("source")!="LIVE QUOTE" or not market.get("spot") or qage is None or qage>MAX_QUOTE_AGE_SEC:
        return {"status":"BLOCKED_STALE_MARKET","timestamp":now.isoformat(),"actions":[],"market":market}
    spot=float(market["spot"]); quotes_by_code=quotes_by_code or {}
    qqqp=lambda p: "QQQ" in p.code.upper() or p.code.upper().startswith("US.Q")
    near_pos=[p for p in positions if p.side=="LONG" and qqqp(p)]
    far_positions=[p for p in positions if p.side=="SHORT" and qqqp(p)]
    pending={o.code for o in orders if o.status.upper() not in {"FILLED","CANCELLED","REJECTED","FAILED"}}
    actions=[]; reasons=[]
    if not far_campaign_active:
        if signal_active and far:
            actions.append({"action":"SELL_FAR","code":far.code,"qty":N_SHORT,"price":far.bid,"why":"EXTREME_HIGH_SIGNAL_ACTIVE"})
        else:
            reasons.append("NO_NEW_CAMPAIGN")
    else:
        if far is None:
            return {"status":"BLOCKED_NO_FAR_QUOTE","timestamp":now.isoformat(),"actions":[],
                    "reasons":["held far short exists but its live option quote is unavailable"]}
        state=risk_state(far,spot,gamma_baseline,previous_far_delta_abs)
        active_near=sum(max(0,int(p.qty)) for p in near_pos)
        reasons += [f"RISK_SCORE={state['risk_score']:.2f}",f"TARGET_NEAR={state['desired_stack']}",f"ACTIVE_NEAR={active_near}"]
        far_qty=sum(abs(int(p.qty)) for p in far_positions if p.code==far.code)
        if far_qty!=N_SHORT:
            actions.append({"action":"REPAIR_FAR","code":far.code,"target_qty":N_SHORT,"current_qty":far_qty,
                            "direction":"ADD" if far_qty<N_SHORT else "REDUCE","why":"fixed 10-lot far short invariant"})
        if spot>=far.strike:
            actions.append({"action":"CLOSE_FAR_EMERGENCY","code":far.code,"qty":max(N_SHORT,far_qty),
                            "price":far.ask,"why":"spot at/above far short strike"})
            for p in near_pos:
                actions.append({"action":"CLOSE_NEAR","code":p.code,"qty":p.qty,"price":quotes_by_code.get(p.code,{}).get("bid"),
                                "why":"campaign termination after far strike touch"})
        else:
            if active_near<state["desired_stack"] and near and near.code not in pending:
                actions.append({"action":"ADD_NEAR","code":near.code,"qty":state["desired_stack"]-active_near,
                                "price":near.ask,"dte":near.dte,"delta":near.delta,"why":"dynamic risk coverage below target"})
            if active_near>state["desired_stack"]:
                excess=active_near-state["desired_stack"]
                for p in sorted(near_pos,key=lambda z:(z.avg_cost,z.dte if z.dte is not None else 999)):
                    if excess<=0:break
                    q=min(excess,p.qty); excess-=q
                    actions.append({"action":"REDUCE_NEAR","code":p.code,"qty":q,
                                    "price":quotes_by_code.get(p.code,{}).get("bid"),
                                    "why":"dynamic target stack fell below current inventory"})
            for p in near_pos:
                q=quotes_by_code.get(p.code,{})
                bid=q.get("bid")
                if bid is not None and p.avg_cost>0 and bid/p.avg_cost-1>=NEAR_TP:
                    actions.append({"action":"HARVEST_NEAR","code":p.code,"qty":p.qty,"price":bid,
                                    "return_pct":bid/p.avg_cost-1,"why":"near profit target reached"})
                if p.dte is not None and p.dte<=NEAR_ROLL_DTE:
                    actions.append({"action":"ROLL_NEAR","code":p.code,"qty":p.qty,"price":bid,"why":"near expiry risk"})
    for o in orders:
        age=quote_age_sec(o.updated_at,now)
        q=quotes_by_code.get(o.code,{})
        if age is not None and age>=STALE_ORDER_SEC and o.status.upper() not in {"FILLED","CANCELLED","REJECTED","FAILED"}:
            actions.append({"action":"REPRICE_OR_CANCEL","order_id":o.order_id,"code":o.code,"qty":o.qty,
                            "side":o.side,"current_price":o.price,"suggested_price":q.get("mid"),
                            "why":f"pending order stale {age:.0f}s; requote before modifying"})
    return {"status":"ACTIONABLE" if actions else "HOLD","timestamp":now.isoformat(),
            "signal_active":signal_active,"far_campaign_active":far_campaign_active,
            "market":market,"far":asdict(far) if far else None,"near_candidate":asdict(near) if near else None,
            "actions":actions,"reasons":reasons}
