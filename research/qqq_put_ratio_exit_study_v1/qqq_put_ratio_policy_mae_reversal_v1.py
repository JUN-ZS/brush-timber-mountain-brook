#!/usr/bin/env python3
"""Walk-forward policy-MAE sizing and exact same-contract put-ratio sign reversal. Research only."""
from __future__ import annotations
import argparse, copy, csv, json, math
from datetime import date
from pathlib import Path
from typing import Any
import qqq_put_ratio_scale_volatility_v1 as core

RID="QQQ_PUT_RATIO_POLICY_MAE_AND_STRICT_REVERSAL_V1"
SLIP=0.05
FEE=0.65
N=5
MIN_TRAIN=10
TARGET_MULTIPLE=3.14012
BUDGETS=(0.02,0.05,0.10,0.15,0.20,0.30,0.40,0.50,0.75,1.00)
STRESSES=(1.0,1.5,2.0)
DELAYS=(0,1,2,3,5)
ORIENTATIONS=("ORIGINAL_1_LONG_5_SHORT","STRICT_SIGN_REVERSAL_SAME_TWO_CONTRACT_IDS")
POLICIES=(
 {"name":"DTE7_RETAIN_RESIDUAL_LONG","kind":"DTE7","sell_residual_longs":False},
 {"name":"DTE7_SELL_RESIDUAL_LONG_IF_EXECUTABLE","kind":"DTE7","sell_residual_longs":True},
)

def day(x: Any)->str:
 if x is None:return ""
 return x.isoformat()[:10] if hasattr(x,"isoformat") else str(x)[:10]

def gap(expiry: Any, d: Any)->int|None:
 try:return (date.fromisoformat(day(expiry))-date.fromisoformat(day(d))).days
 except (TypeError,ValueError):return None

def invert_same_contract_trade(t: dict[str,Any])->dict[str,Any]:
 """Original +1 high put/-5 low puts -> -1 same high put/+5 same low puts."""
 o=copy.deepcopy(t)
 o["long_strike"],o["short_strike"]=t["short_strike"],t["long_strike"]
 for a,b in (("long_id","short_id"),("long_abs_delta","short_abs_delta"),("long_delta","short_delta")):
  if a in t or b in t:o[a],o[b]=t.get(b),t.get(a)
 q=t.get("entry_quotes") or {}
 o["entry_quotes"]={"long":copy.deepcopy(q.get("short")),"short":copy.deepcopy(q.get("long"))}
 path=[]
 for raw in t.get("path") or []:
  s=copy.deepcopy(raw);s["long"],s["short"]=raw.get("short"),raw.get("long");path.append(s)
 o["path"]=path
 o["strict_sign_reversal_of_trade_id"]=t.get("trade_id")
 o["strict_sign_reversal_same_contract_ids"]=True
 return o

def orientation_trade(t:dict[str,Any],orientation:str)->tuple[dict[str,Any],str,int]:
 if orientation==ORIENTATIONS[0]:return copy.deepcopy(t),core.SHORT_HEAVY,N
 if orientation==ORIENTATIONS[1]:return invert_same_contract_trade(t),core.LONG_HEAVY,N
 raise ValueError("unknown orientation: "+orientation)

def signal_age(t:dict[str,Any])->int|None:
 for i,s in enumerate(t.get("path") or []):
  d=gap(t.get("expiry"),s.get("date"))
  if d is not None and 0<d<=7:return i
 return None

def apply_delay(t:dict[str,Any],delay:int)->tuple[dict[str,Any],int]:
 o=copy.deepcopy(t)
 if delay<=0:return o,0
 sig=signal_age(o)
 if sig is None:return o,0
 changed=0
 for i in range(sig+1,min(len(o.get("path") or []),sig+1+delay)):
  q=(o["path"][i] or {}).get("short")
  if isinstance(q,dict):q["ask_size"]=0;changed+=1
 return o,changed

def load_cohort(p:Path)->list[dict[str,Any]]:
 x=json.loads(p.read_text(encoding="utf-8"))
 if not isinstance(x,list) or not x or any(not isinstance(t,dict) for t in x):
  raise ValueError("cohort must be a non-empty list of episode objects")
 return sorted(x,key=lambda t:(day(t.get("entry_date")),str(t.get("trade_id",""))))

def load_prices(p:Path)->list[dict[str,Any]]:
 with p.open(newline="",encoding="utf-8") as f:
  rows=[{"date":day(r.get("date")),"close":core.num(r.get("raw_close") or r.get("close")),"vix":core.num(r.get("vix"))} for r in csv.DictReader(f)]
 return sorted((r for r in rows if r["date"]),key=lambda r:r["date"])

def depth_cap(t:dict[str,Any],direction:str,n:int)->int:
 q=t.get("entry_quotes") or {};l=q.get("long");s=q.get("short")
 if not core.quote_ok(l,"ask") or not core.quote_ok(s,"bid"):return 0
 la=core.num(l.get("ask_size"));sb=core.num(s.get("bid_size"))
 if la is None or sb is None or la<0 or sb<0:return 0
 nl,ns=core.quantities(direction,n)
 return max(0,min(math.floor(la/nl),math.floor(sb/ns)))

def mark_stats(result:dict[str,Any])->dict[str,Any]:
 curve=result.get("mark_curve") or []
 vals=[float(x["pnl_usd"]) for x in curve if x.get("pnl_usd") is not None]
 missing=sum(x.get("pnl_usd") is None for x in curve)
 return {"_curve":curve,"valid_mark_rows":len(vals),"missing_mark_rows":missing,
         "observed_policy_mae_usd":round(max(0.0,-min(vals)),4) if vals else None,
         "observed_policy_mfe_usd":round(max(0.0,max(vals)),4) if vals else None}

def reference(t:dict[str,Any],i:int,ori:str,direction:str,n:int,p:dict[str,Any],delay:int)->dict[str,Any]:
 prepared,forced=apply_delay(t,delay)
 r=core.simulate(prepared,direction,n,100000.0,p,SLIP,FEE,units=1,include_mark_path=True)
 m=mark_stats(r);pnl=core.num(r.get("final_pnl_usd"));curve=m["_curve"]
 ex=day(curve[-1].get("date")) if curve and pnl is not None else None
 env=core.terminal_envelope(prepared,*core.quantities(direction,n),SLIP,FEE)
 entry_capacity_ok=core.entry_size_ok(t,direction,n)
 clean=pnl is not None and m["missing_mark_rows"]==0 and m["observed_policy_mae_usd"] is not None and entry_capacity_ok
 return {"trade_index":i,"trade_id":t.get("trade_id"),"entry_date":day(t.get("entry_date")),"exit_date":ex,
  "orientation":ori,"policy":p["name"],"forced_exit_delay_sessions":delay,"forced_short_exit_blocked_sessions":forced,
  "one_unit_final_pnl_usd":round(pnl,4) if pnl is not None else None,"one_unit_final_status":r.get("final_status"),
  "one_unit_max_terminal_loss_usd":core.num(env.get("max_terminal_loss_usd")),
  "valid_mark_rows":m["valid_mark_rows"],"missing_mark_rows":m["missing_mark_rows"],
  "observed_policy_mae_usd":m["observed_policy_mae_usd"],"observed_policy_mfe_usd":m["observed_policy_mfe_usd"],
  "training_eligible":bool(clean),"entry_capacity_eligible":bool(entry_capacity_ok),"training_exclusion_reason":"" if clean else ("UNRESOLVED_FINAL_PNL" if pnl is None else "MISSING_OR_NO_VALID_MARK" if m["missing_mark_rows"] or m["observed_policy_mae_usd"] is None else "ENTRY_DEPTH_INSUFFICIENT"),
  "trigger_age_sessions":r.get("custom_trigger_age_sessions"),"trigger_to_action_delay_sessions":r.get("trigger_to_action_delay_sessions"),
  "evidence":"SHA_PINNED_EOD_QUOTE_SIDE_MODEL_NOT_CONFIRMED_FILLS"}

def clean_prior(refs:list[dict[str,Any]],entry:str)->list[dict[str,Any]]:
 cutoff=day(entry)
 return [r for r in refs if r.get("training_eligible") and r.get("exit_date") and day(r["exit_date"])<cutoff]

def size_mae(nav:float,pct:float,worst:float|None,stress:float,depth:int)->dict[str,Any]:
 budget=nav*pct
 if worst is None or not math.isfinite(worst) or worst<=0:
  return {"budget_usd":budget,"denominator_usd":None,"planned":0,"units":0,"status":"PENDING_NO_PRIOR_MAE"}
 denom=worst*stress;planned=max(0,math.floor(budget/denom+1e-9));units=min(planned,depth)
 status=("BLOCKED_ZERO_UNITS_BY_MAE_BUDGET" if planned==0 else "BLOCKED_NO_ENTRY_DEPTH" if depth==0 else "DEPTH_CAPPED" if units<planned else "SIZED_BY_WALK_FORWARD_POLICY_MAE")
 return {"budget_usd":budget,"denominator_usd":denom,"planned":planned,"units":units,"status":status}

def percentile(values:list[float],p:float)->float|None:
 x=sorted(values)
 return x[min(len(x)-1,max(0,math.ceil(p*len(x))-1))] if x else None

def daily_metrics(prices:list[dict[str,Any]],executions:list[dict[str,Any]],start:float)->dict[str,Any]:
 dates=[day(x["date"]) for x in prices]
 if not dates:return {"valid_nav_marks":0,"missing_nav_mark_days":0,"max_drawdown_pct":None}
 end=dates[-1];actual=sorted([x for x in executions if x.get("ratio_units",0)>0],key=lambda x:x["entry_date"])
 maps=[(x,{day(m.get("date")):core.num(m.get("pnl_usd")) for m in x.get("_curve",[])},x.get("exit_date") or end) for x in actual]
 nav=float(start);cur=0;peak=float(start);maxdd=0.0;valid=missing=nonpositive=0
 for d in dates:
  while cur<len(maps) and maps[cur][0].get("final_pnl_usd") is not None and day(maps[cur][0]["exit_date"])<d:
   nav=float(maps[cur][0]["nav_after_usd"]);cur+=1
  if cur<len(maps):
   row,mp,active_end=maps[cur]
   if row["entry_date"]<=d<=active_end:
    pnl=mp.get(d);mark=None if pnl is None else float(row["nav_before_usd"])+pnl
   else:mark=nav
  else:mark=nav
  if mark is None:missing+=1;continue
  valid+=1
  if mark<=0:nonpositive+=1;dd=-100.0
  else:peak=max(peak,mark);dd=100*(mark/peak-1) if peak>0 else -100.0
  maxdd=min(maxdd,dd)
 return {"valid_nav_marks":valid,"missing_nav_mark_days":missing,"nonpositive_nav_marks":nonpositive,
         "max_drawdown_pct":round(maxdd,4),"max_drawdown_is_descriptive_only":True}

def csv_write(path:Path,rows:list[dict[str,Any]])->None:
 if not rows:path.write_text("",encoding="utf-8");return
 keys=[]
 for r in rows:
  for k in r:
   if not k.startswith("_") and k not in keys:keys.append(k)
 with path.open("w",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=keys,extrasaction="ignore");w.writeheader()
  for r in rows:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list,tuple)) else v for k,v in r.items() if not k.startswith("_")})

def replay_config(trades:list[dict[str,Any]],refs:list[dict[str,Any]],prices:list[dict[str,Any]],ori:str,p:dict[str,Any],
                  delay:int,stress:float,pct:float,start:float)->tuple[dict[str,Any],list[dict[str,Any]]]:
 nav=float(start);last_exit=None;censored=False;executions=[];rows=[]
 warm=zero=depthskip=overlap=unresolved=forcedtotal=0
 target=start*TARGET_MULTIPLE
 for i,raw in enumerate(trades):
  entry=day(raw.get("entry_date"))
  if not entry or nav<=0 or censored:break
  t,direction,n=orientation_trade(raw,ori);prepared,forced=apply_delay(t,delay);forcedtotal+=forced
  if last_exit is not None and entry<=last_exit:
   overlap+=1;rows.append({"trade_index":i,"trade_id":raw.get("trade_id"),"entry_date":entry,"orientation":ori,
    "policy":p["name"],"forced_exit_delay_sessions":delay,"mae_stress_multiplier":stress,"nav_risk_budget_pct":pct*100,
    "nav_before_usd":round(nav,4),"training_episode_count":0,"ratio_units":0,"status":"SKIPPED_OVERLAPPING_ACTIVE_POSITION"})
   continue
  train=clean_prior(refs,entry);maes=[float(r["observed_policy_mae_usd"]) for r in train if r.get("observed_policy_mae_usd") is not None]
  worst=max(maes) if maes else None;p95=percentile(maes,.95);depth=depth_cap(prepared,direction,n)
  if len(train)<MIN_TRAIN:
   size={"budget_usd":nav*pct,"denominator_usd":None,"planned":0,"units":0,"status":"PENDING_WALK_FORWARD_MAE_WARMUP"};warm+=1
  else:
   size=size_mae(nav,pct,worst,stress,depth)
   if size["status"]=="BLOCKED_ZERO_UNITS_BY_MAE_BUDGET":zero+=1
   if size["status"]=="BLOCKED_NO_ENTRY_DEPTH":depthskip+=1
  env=core.terminal_envelope(prepared,*core.quantities(direction,n),SLIP,FEE);unit_tail=core.num(env.get("max_terminal_loss_usd"));units=int(size["units"])
  row={"trade_index":i,"trade_id":raw.get("trade_id"),"entry_date":entry,"orientation":ori,"policy":p["name"],
   "forced_exit_delay_sessions":delay,"mae_stress_multiplier":stress,"nav_risk_budget_pct":pct*100,
   "nav_before_usd":round(nav,4),"risk_budget_usd":round(size["budget_usd"],4),"training_episode_count":len(train),
   "prior_worst_unit_mae_usd":round(worst,4) if worst is not None else None,"prior_p95_unit_mae_usd":round(p95,4) if p95 is not None else None,
   "mae_denominator_usd":round(size["denominator_usd"],4) if size["denominator_usd"] is not None else None,
   "planned_units":size["planned"],"entry_depth_cap_units":depth,"ratio_units":units,"sizing_status":size["status"],
   "one_unit_max_terminal_loss_usd":round(unit_tail,4) if unit_tail is not None else None,
   "modeled_terminal_loss_usd":round(unit_tail*units,4) if unit_tail is not None and units else 0.0,
   "modeled_terminal_loss_pct_current_nav":round(100*unit_tail*units/nav,4) if unit_tail is not None and units and nav>0 else 0.0,
   "terminal_loss_budget_is_separate_from_mae_budget":True,"status":size["status"]}
  if units<=0:rows.append(row);continue
  result=core.simulate(prepared,direction,n,nav,p,SLIP,FEE,units=units,include_mark_path=True);m=mark_stats(result);pnl=core.num(result.get("final_pnl_usd"));curve=m["_curve"]
  exitdate=day(curve[-1].get("date")) if curve else day(raw.get("expiry"))
  if pnl is None:
   unresolved+=1;censored=True;exitdate=day(prices[-1]["date"]) if prices else exitdate;after=None;row["status"]="CENSORED_UNRESOLVED_ACTIVE_RISK"
  else:
   after=nav+pnl;last_exit=exitdate;row["status"]="EXECUTED_RESOLVED_MODEL_PNL"
  row.update({"exit_date":exitdate,"nav_after_usd":round(after,4) if after is not None else None,
   "final_pnl_usd":round(pnl,4) if pnl is not None else None,"final_pnl_pct_nav_before":round(100*pnl/nav,4) if pnl is not None and nav>0 else None,
   "final_status":result.get("final_status"),"observed_policy_mae_usd":m["observed_policy_mae_usd"],
   "observed_policy_mae_pct_nav_before":round(100*m["observed_policy_mae_usd"]/nav,4) if m["observed_policy_mae_usd"] is not None and nav>0 else None,
   "missing_mark_rows":m["missing_mark_rows"],"valid_mark_rows":m["valid_mark_rows"],
   "mae_training_eligible_for_future":bool(pnl is not None and m["missing_mark_rows"]==0 and m["observed_policy_mae_usd"] is not None),
   "trigger_age_sessions":result.get("custom_trigger_age_sessions"),"trigger_to_action_delay_sessions":result.get("trigger_to_action_delay_sessions"),
   "_curve":curve})
  executions.append(row);rows.append({k:v for k,v in row.items() if not k.startswith("_")})
  if pnl is None:break
  nav=float(after)
  if nav<=0:break
 final=None if censored else nav
 years=(date.fromisoformat(day(prices[-1]["date"]))-date.fromisoformat(day(prices[0]["date"]))).days/365.2425 if len(prices)>1 else 0
 cagr=100*((final/start)**(1/years)-1) if final is not None and final>0 and years>0 else None
 dd=daily_metrics(prices,executions,start)
 tailp=[core.num(r.get("modeled_terminal_loss_pct_current_nav")) for r in executions]
 summary={"start_nav_usd":start,"target_nav_multiple":TARGET_MULTIPLE,"target_nav_usd":round(target,2),"orientation":ori,"policy":p["name"],
  "forced_exit_delay_sessions":delay,"mae_stress_multiplier":stress,"nav_risk_budget_pct":pct*100,"cost_case":"BASE_005_065",
  "slippage_per_leg_usd":SLIP,"commission_per_contract_per_side_usd":FEE,"training_minimum_episodes":MIN_TRAIN,
  "executed_episodes":len(executions),"resolved_episodes":sum(r.get("final_pnl_usd") is not None for r in executions),
  "skipped_warmup":warm,"skipped_zero_units_by_mae":zero,"skipped_no_entry_depth":depthskip,"skipped_overlap":overlap,
  "unresolved_active_risk":unresolved,"forced_short_exit_blocked_quote_sessions":forcedtotal,
  "net_pnl_usd":round(final-start,2) if final is not None else None,"final_nav_usd":round(final,2) if final is not None else None,
  "cagr_pct":round(cagr,4) if cagr is not None else None,"target_reached":bool(final is not None and final>=target),
  "max_drawdown_pct":dd["max_drawdown_pct"],"max_drawdown_is_descriptive_only":True,
  "max_modeled_terminal_loss_pct_current_nav":round(max((x for x in tailp if x is not None),default=0.0),4),
  "status":"CENSORED_UNRESOLVED_ACTIVE_RISK" if censored else "RESOLVED_MODEL_PATH_NOT_CONFIRMED_FILLS",**dd}
 return summary,rows

def run(trades:list[dict[str,Any]],prices:list[dict[str,Any]],navs:list[float],out:Path)->dict[str,Any]:
 out.mkdir(parents=True,exist_ok=True);refs={}
 for ori in ORIENTATIONS:
  for p in POLICIES:
   for delay in DELAYS:
    items=[]
    for i,raw in enumerate(trades):
     t,direction,n=orientation_trade(raw,ori)
     items.append(reference(t,i,ori,direction,n,p,delay))
    refs[(ori,p["name"],delay)]=items
 refrows=[x for z in refs.values() for x in z];matrix=[];trade_rows=[]
 for start in navs:
  for ori in ORIENTATIONS:
   for p in POLICIES:
    for delay in DELAYS:
     rr=refs[(ori,p["name"],delay)]
     for stress in STRESSES:
      for budget in BUDGETS:
       summary,detail=replay_config(trades,rr,prices,ori,p,delay,stress,budget,start)
       matrix.append(summary);trade_rows.extend(detail)
 csv_write(out/"policy_mae_nav_matrix.csv",matrix)
 csv_write(out/"policy_mae_trade_rows.csv",trade_rows)
 csv_write(out/"policy_mae_unit_episode_reference.csv",refrows)
 resolved=[r for r in matrix if r.get("final_nav_usd") is not None]
 targets=[r for r in matrix if r.get("target_reached")]
 best=sorted(resolved,key=lambda x:x.get("final_nav_usd") or 0,reverse=True)[:10]
 output={"research_id":RID,"status":"RESEARCH_ONLY_NO_POLICY_PROMOTED","source_episode_count":len(trades),
  "option_source_end":"2025-12-15","orientation_contract":{"original":"+1 original high-strike / -5 original low-strike puts",
  "strict_inverse":"-1 same original high-strike contract / +5 same original low-strike contract","replacement_strikes_or_ids":False},
  "risk_method":{"walk_forward":True,"training_max_policy_mae_from_clean_prior_resolved_episodes":True,
  "minimum_clean_prior_episodes":MIN_TRAIN,"nav_risk_budget_pct":[100*x for x in BUDGETS],"mae_stress_multipliers":list(STRESSES),
  "forced_exit_delay_sessions":list(DELAYS),"displayed_entry_depth_cap":True,"terminal_loss_reported_separately":True},
  "costs":{"case":"BASE_005_065","slippage_per_leg_usd":SLIP,"commission_per_contract_per_side_usd":FEE},
  "configurations":len(matrix),"resolved_nav_configurations":len(resolved),"configurations_reaching_scaled_target":len(targets),
  "target_definition":f"Ending NAV >= {TARGET_MULTIPLE:.5f}x starting NAV; searched historical path, not forward probability or acceptance gate.",
  "maxdd_policy":"Descriptive outcome only; never used as a pass/fail filter.",
  "best_historical_paths_for_inspection_only":[{k:r.get(k) for k in ("start_nav_usd","orientation","policy","forced_exit_delay_sessions",
  "mae_stress_multiplier","nav_risk_budget_pct","executed_episodes","final_nav_usd","cagr_pct","max_drawdown_pct","target_reached",
  "max_modeled_terminal_loss_pct_current_nav")} for r in best],
  "outputs":["policy_mae_nav_matrix.csv","policy_mae_trade_rows.csv","policy_mae_unit_episode_reference.csv","policy_mae_study_summary.json","policy_mae_study_summary.md"],
  "integrity_limits":["Option-chain mirror ends 2025-12-15; no later option P&L is inferred.",
  "Daily quote-side MAE can miss intraday losses and missing marks; incomplete-mark episodes cannot calibrate.",
  "Forced 1/2/3/5-session delays are deterministic depth-block stresses, not delay probabilities.",
  "Prior-worst MAE is an in-sample walk-forward feature, not a guarantee or validated tail quantile.",
  "Whole-unit P&L may not scale linearly; impact, margin, assignment and forced liquidation are not fully modeled.",
  "Expiry intrinsic proxy is not broker settlement; terminal QQQ=0 loss can exceed the MAE budget by multiples.",
  "The study period was previously examined; MaxDD is descriptive, not a feasibility gate."]}
 (out/"policy_mae_study_summary.json").write_text(json.dumps(output,indent=2),encoding="utf-8")
 md=["# QQQ policy-MAE, exit-delay and strict same-contract reversal study","",
 "**Research-only; no policy promoted. MaxDD is descriptive only.**","",
 f"- Source episodes: {len(trades)}; option source ends 2025-12-15.",
 f"- Configurations: {len(matrix)}; resolved NAV paths: {len(resolved)}; target reached in {len(targets)} searched configurations.",
 f"- Target: ending NAV >= {TARGET_MULTIPLE:.5f}x start NAV (USD 100,000 -> USD 314,012; USD 1,000,000 -> USD 3,140,120).",
 f"- Walk-forward warm-up: at least {MIN_TRAIN} clean prior resolved episodes, strictly before each new entry.",
 f"- Budget ladder: {', '.join(str(int(100*x))+'%' for x in BUDGETS)}; MAE stress: {', '.join(str(x)+'x' for x in STRESSES)}; forced delays: {', '.join(str(x) for x in DELAYS)} sessions.","",
 "## Exact inversion","",
 "- Original: +1 original high-strike put and -5 original low-strike puts.",
 "- Strict inverse: -1 of the same original high-strike contract and +5 of the same original low-strike contract. Same expiration, IDs, strikes and quote streams; only position signs/quantities reverse.",
 "- This does not use the previous different-strike long-heavy family as a proxy.","",
 "## Risk accounting","",
 "- Size = floor(current NAV x budget / (worst clean prior one-unit policy MAE x stress multiple)); current entry depth caps whole units.",
 "- Full-to-expiry loss including QQQ=0 is separately output; the MAE sizing rule does not cap that tail exposure.",
 "- Forced-delay stress blocks displayed short-leg ask size after the DTE<=7 signal while leaving prices unchanged. This is a stress scenario, not a probability.",
 "- Missing marks are never forward-filled and do not qualify for MAE training. MaxDD is not a PASS/FAIL filter.","",
 "## Highest historical ending-NAV rows (inspection only)","",
 "| Start NAV | Structure | Policy | Delay | Stress | Budget | Executed | Ending NAV | CAGR | MaxDD | Target | Terminal loss/current NAV |",
 "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---|---:|"]
 for r in best:
  final=f"USD {r['final_nav_usd']:,.2f}" if r["final_nav_usd"] is not None else "CENSORED"
  cagr=f"{r['cagr_pct']:.2f}%" if r["cagr_pct"] is not None else "—"
  dd=f"{r['max_drawdown_pct']:.2f}%" if r["max_drawdown_pct"] is not None else "—"
  md.append(f"| NAV {r['start_nav_usd']:,.0f} | {r['orientation']} | {r['policy']} | {r['forced_exit_delay_sessions']} | {r['mae_stress_multiplier']:.1f}x | {r['nav_risk_budget_pct']:.0f}% | {r['executed_episodes']} | {final} | {cagr} | {dd} | {'YES' if r['target_reached'] else 'NO'} | {r['max_modeled_terminal_loss_pct_current_nav']:.2f}% |")
 md += ["","Top rows are grid-search results on previously examined data, not recommendations. The option chain ends 2025-12-15; EOD side quotes are not confirmed fills; exact timestamp, intraday MAE, market impact, margin, assignment and forced liquidation are not authenticated or fully modeled. A 100% budget is a sensitivity point, not an approved risk level. No App, main branch, Frozen Hybrid sizing or order permission changes."]
 (out/"policy_mae_study_summary.md").write_text("\n".join(md)+"\n",encoding="utf-8")
 return output

def main()->None:
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument("--cohort",type=Path,required=True);ap.add_argument("--prices",type=Path,required=True);ap.add_argument("--out",type=Path,required=True)
 ap.add_argument("--start-nav",type=float,action="append",default=None)
 a=ap.parse_args();navs=a.start_nav or [100000.0,1000000.0]
 if any(not math.isfinite(x) or x<=0 for x in navs):ap.error("every --start-nav must be positive and finite")
 trades=load_cohort(a.cohort);prices=load_prices(a.prices)
 if not prices:ap.error("price series is empty")
 print(json.dumps(run(trades,prices,navs,a.out),indent=2))

if __name__=="__main__":main()
