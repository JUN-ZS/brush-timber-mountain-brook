#!/usr/bin/env python3
"""Independent daily-price and external-cashflow replay for the pinned glidepath artifact."""
from __future__ import annotations
import argparse, csv, datetime as dt, hashlib, json, math
from pathlib import Path
import numpy as np
BONDS=("AGG","SHY","IEF","TLT"); TICKERS=("QQQ","SPY","AGG","SHY","IEF","TLT")
TARGETS=(30,40,50,60,70,80,90,100)
TIMINGS=("front_rapid","front_fast","front_loaded","linear","mid_loaded","staggered","back_loaded","back_late")
FLOWS=("no_withdrawals","delayed_stepup_example","monthly_withdrawal_500_usd_stress","monthly_withdrawal_1000_usd_stress")
INITIAL=100000.0; HORIZON=120; USD_TOL=0.12; RATE_TOL=2e-6; DD_TOL=2e-6

def need(condition,message):
    if not condition: raise ValueError(message)

def quantile(values,p):
    if not values: return None
    xs=sorted(values)
    if len(xs)==1: return xs[0]
    pos=(len(xs)-1)*p; lo=math.floor(pos); hi=math.ceil(pos); f=pos-lo
    return xs[lo]*(1-f)+xs[hi]*f

def bond_weight(target,elapsed,timing):
    y=min(10,max(0,elapsed//12))
    if timing=="front_rapid": p=.5*y if y<=1 else .5+.5*(y-1)/9
    elif timing=="front_fast": p=.5*y/2 if y<=2 else .5+.5*(y-2)/8
    elif timing=="front_loaded": p=.5*y/3 if y<=3 else .5+.5*(y-3)/7
    elif timing=="linear": p=y/10
    elif timing=="mid_loaded":
        x=y/10; p=3*x*x-2*x*x*x
    elif timing=="staggered":
        if y<=2: p=.25*y/2
        elif y<=5: p=.25+.25*(y-2)/3
        elif y<=8: p=.5+.25*(y-5)/3
        else: p=.75+.25*(y-8)/2
    elif timing=="back_loaded": p=max(0,(y-5)/5)
    elif timing=="back_late": p=max(0,(y-7)/3)
    else: raise ValueError("Unsupported glidepath timing: "+timing)
    return target/100*p

def load_schedule(path):
    out={}
    with path.open(newline="",encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            m=int(row["month_index"]); kind=row["flow_type"].strip().lower(); amount=float(row["amount_usd"])
            need(1<=m<=HORIZON and kind in ("deposit","withdrawal") and math.isfinite(amount) and amount>0,f"Invalid flow: {row}")
            out.setdefault(m,[]).append((kind,amount))
    need(sum(a for es in out.values() for k,a in es if k=="withdrawal")==12800,"Pinned example withdrawals changed")
    need(sum(a for es in out.values() for k,a in es if k=="deposit")==5000,"Pinned example deposits changed")
    return out

def schedule_for(mode,custom):
    if mode=="no_withdrawals": return {}
    if mode=="delayed_stepup_example": return custom
    amount=500.0 if mode=="monthly_withdrawal_500_usd_stress" else 1000.0
    return {m:[("withdrawal",amount)] for m in range(1,HORIZON+1)}

def load_panel(path,report):
    raw=path.read_bytes(); sha=hashlib.sha256(raw).hexdigest()
    need(sha==report["data"]["raw_panel_canonical_sha256"],f"Daily-panel SHA mismatch: expected {report['data']['raw_panel_canonical_sha256']}, got {sha}")
    dates=[]; rows=[]
    with path.open(newline="",encoding="utf-8") as f:
        reader=csv.DictReader(f); need(tuple(reader.fieldnames or ())==("date",*TICKERS),"Unexpected daily panel schema")
        for row in reader:
            d=row["date"]; vals=[float(row[t]) for t in TICKERS]
            need(all(math.isfinite(x) and x>0 for x in vals),f"Invalid daily mark: {d}")
            dates.append(d); rows.append(vals)
    need(len(dates)==int(report["data"]["daily_common_observations"])==5788,"Daily row-count mismatch")
    need(dates[-1]==report["data"]["last_common_date"]=="2026-09-30","Source as-of mismatch")
    month_last={}
    for i,d in enumerate(dates): month_last[(int(d[:4]),int(d[5:7]))]=i
    month_ends=sorted(month_last.values())
    need(len(month_ends)==int(report["data"]["common_month_end_observations"])==277,"Month-end row-count mismatch")
    need(len(month_ends)-HORIZON==157,"Expected 157 rolling windows")
    return dates,np.asarray(rows,dtype=np.float64),month_ends,sha

def replay_window(dates,prices,month_ends,start_m,bond,target,timing,mode,schedule):
    start_i=month_ends[start_m]; end_i=month_ends[start_m+HORIZON]
    start_date,end_date=dates[start_i],dates[end_i]; bc=TICKERS.index(bond)
    units=np.zeros(6,dtype=np.float64); units[0]=.5/prices[start_i,0]; units[1]=.5/prices[start_i,1]
    scale=INITIAL; requested=paid=shortfall=deposits=0.0; first_depletion=None; depleted=False
    perf=INITIAL; peak=INITIAL; max_dd=0.0
    marks=[{"year":0,"date":start_date,"nav_usd":round(INITIAL,2),"performance_index":perf,
      "year_twr":None,"cumulative_twr_cagr":None,"max_drawdown_to_date":0.0,"actual_withdrawals_usd":0.0,
      "withdrawal_shortfall_usd":0.0,"additional_deposits_usd":0.0,"target_bond_weight":0.0,"target_stock_weight":1.0}]
    for year in range(10):
        rel0=year*12; d0=month_ends[start_m+rel0]; d1=month_ends[start_m+rel0+12]
        raw=np.sum(prices[d0:d1+1]*units[None,:],axis=1)
        need(np.all(np.isfinite(raw)) and np.all(raw>0),"Invalid underlying daily path")
        raw=raw/raw[0]; depletion_offset=None
        for month in range(rel0+1,rel0+13):
            gi=month_ends[start_m+month]; g=float(raw[gi-d0]); nav=scale*g
            for kind,amount in schedule.get(month,[]):
                if kind=="deposit":
                    need(nav>1e-10,"Deposit after NAV depletion needs segmented replay; BLOCK")
                    deposits+=amount; scale+=amount/g; nav=scale*g
                else:
                    requested+=amount; paid_now=min(amount,max(0.0,nav)); shortfall+=amount-paid_now
                    if nav>1e-10 and paid_now>0:
                        scale=max(0.0,nav-paid_now)/g; paid+=paid_now; nav=scale*g
            if nav<=1e-8:
                if first_depletion is None: first_depletion=month
                if not depleted: depletion_offset=gi-d0
                depleted=True
        if not depleted or depletion_offset is not None:
            last=depletion_offset if depletion_offset is not None else len(raw)-1
            pi=perf*raw[1:last+1]
            if pi.size:
                peaks=np.maximum.accumulate(np.maximum(peak,pi))
                max_dd=min(max_dd,float(np.min(pi/peaks-1)))
                peak=max(peak,float(np.max(pi))); perf=float(pi[-1])
        nav_end=max(0.0,scale*float(raw[-1]))
        elapsed=(dt.date.fromisoformat(dates[d1])-dt.date.fromisoformat(start_date)).days/365.25
        cagr=(perf/INITIAL)**(1/elapsed)-1 if elapsed>0 and perf>0 else None
        prev=marks[-1]["performance_index"]; yrret=perf/prev-1 if prev>1e-10 else None
        tw=bond_weight(target,(year+1)*12,timing)
        marks.append({"year":year+1,"date":dates[d1],"nav_usd":round(nav_end,2),"performance_index":perf,
          "year_twr":yrret,"cumulative_twr_cagr":cagr,"max_drawdown_to_date":max_dd,
          "actual_withdrawals_usd":round(paid,2),"withdrawal_shortfall_usd":round(shortfall,2),
          "additional_deposits_usd":round(deposits,2),"target_bond_weight":tw,"target_stock_weight":1-tw})
        if year<9:
            w=bond_weight(target,(year+1)*12,timing); units=np.zeros(6,dtype=np.float64)
            units[0]=.5*(1-w)/prices[d1,0]; units[1]=.5*(1-w)/prices[d1,1]; units[bc]=w/prices[d1,bc]
            scale=nav_end
    terminal=marks[-1]["nav_usd"]
    elapsed=(dt.date.fromisoformat(end_date)-dt.date.fromisoformat(start_date)).days/365.25
    cagr=(perf/INITIAL)**(1/elapsed)-1 if elapsed>0 and perf>0 else None
    return {"window_start":start_date,"window_end":end_date,"bond_proxy":bond,
      "target_bond_conversion_pct_at_year10":target,"timing_rule":timing,"cashflow_mode":mode,
      "initial_capital_usd":INITIAL,"additional_deposits_usd":round(deposits,2),"total_capital_supplied_usd":round(INITIAL+deposits,2),
      "requested_withdrawals_usd":round(requested,2),"actual_withdrawals_usd":round(paid,2),
      "withdrawal_shortfall_usd":round(shortfall,2),"terminal_nav_usd":terminal,
      "nominal_net_result_usd":round(paid+terminal-deposits-INITIAL,2),"time_weighted_cagr":cagr,
      "daily_max_drawdown":max_dd,"first_nav_depletion_month":"" if first_depletion is None else first_depletion,
      "ending_stock_weight":1-target/100,"ending_bond_weight":target/100},marks

def close_value(got,expected,field,stats,label):
    if field in ("window_start","window_end","bond_proxy","target_bond_conversion_pct_at_year10","timing_rule","cashflow_mode","first_nav_depletion_month"):
        a="" if got is None else str(got); b="" if expected is None else str(expected)
        need(a==b,f"{label} {field}: replay={a!r} source={b!r}")
    elif got is None:
        need(expected in (None,"","null"),f"{label} {field}: replay=null source={expected!r}")
    else:
        a=float(got); b=float(expected)
        tol=USD_TOL if field.endswith("_usd") or field=="nominal_net_result_usd" else (DD_TOL if field=="daily_max_drawdown" else RATE_TOL)
        err=abs(a-b)
        stats["max_abs_error"][field]=max(stats["max_abs_error"].get(field,0),err)
        need(err<=tol,f"{label} {field}: replay={a} source={b} abs_error={err} tol={tol}")
    stats["fields_compared"]+=1

def annual_summary(marks):
    nav=[float(x["nav_usd"]) for x in marks]; cagr=[float(x["cumulative_twr_cagr"]) for x in marks if x["cumulative_twr_cagr"] is not None]
    yr=[float(x["year_twr"]) for x in marks if x["year_twr"] is not None]; dd=[float(x["max_drawdown_to_date"]) for x in marks]
    sf=[float(x["withdrawal_shortfall_usd"]) for x in marks]; paid=[float(x["actual_withdrawals_usd"]) for x in marks]
    bw=[float(x["target_bond_weight"]) for x in marks]
    return {"median_nav_usd":round(quantile(nav,.5),2),"p05_nav_usd":round(quantile(nav,.05),2),
      "p95_nav_usd":round(quantile(nav,.95),2),"worst_nav_usd":round(min(nav),2),
      "median_cumulative_twr_cagr":quantile(cagr,.5),"p05_cumulative_twr_cagr":quantile(cagr,.05),
      "median_year_twr":quantile(yr,.5),"p05_year_twr":quantile(yr,.05),
      "median_drawdown_to_date":quantile(dd,.5),"worst_drawdown_to_date":min(dd),
      "windows_below_initial_capital":sum(x<INITIAL for x in nav),
      "windows_with_withdrawal_shortfall":sum(x>.01 for x in sf),
      "median_actual_withdrawals_usd":round(quantile(paid,.5),2),"median_shortfall_usd":round(quantile(sf,.5),2),
      "p95_shortfall_usd":round(quantile(sf,.95),2),"median_target_bond_weight":quantile(bw,.5),
      "median_target_stock_weight":quantile([1-x for x in bw],.5)}

def real_principal_breach_counts(nav_values, year, expected_windows=157):
    """Count year-end NAV marks below inflation-adjusted principal; cohort samples may contain fewer windows."""
    need(isinstance(year, int) and 0 <= year <= 10, f"Invalid real-principal count year: {year}")
    need(isinstance(expected_windows, int) and expected_windows > 0,
         f"Invalid expected real-principal sample size: {expected_windows}")
    need(len(nav_values) == expected_windows,
         f"Real-principal count needs {expected_windows} window NAVs, got {len(nav_values)}")
    navs = [float(value) for value in nav_values]
    need(all(math.isfinite(value) and value >= 0 for value in navs),
         "Real-principal counts require finite non-negative remaining NAVs")
    threshold235 = INITIAL * (1.0 + 0.0235) ** year
    threshold350 = INITIAL * (1.0 + 0.035) ** year
    # Strictly less than counts a breach; a NAV exactly on the threshold is not below it.
    count235 = sum(value < threshold235 for value in navs)
    count350 = sum(value < threshold350 for value in navs)
    need(0 <= count235 <= count350 <= expected_windows,
         f"Real-principal breach counts violate threshold ordering: {year}/{count235}/{count350}/{expected_windows}")
    if year == 0:
        need(count235 == count350 == 0, "Year-zero real-principal breach counts must both be zero")
    return count235, count350


def scenario_summary(rows):
    nav=[float(x["terminal_nav_usd"]) for x in rows]; cagr=[float(x["time_weighted_cagr"]) for x in rows if x["time_weighted_cagr"] is not None]
    dd=[float(x["daily_max_drawdown"]) for x in rows]; paid=[float(x["actual_withdrawals_usd"]) for x in rows]
    sf=[float(x["withdrawal_shortfall_usd"]) for x in rows]
    return {"median_terminal_nav_usd":round(quantile(nav,.5),2),"p05_terminal_nav_usd":round(quantile(nav,.05),2),
      "p95_terminal_nav_usd":round(quantile(nav,.95),2),"worst_terminal_nav_usd":round(min(nav),2),
      "median_time_weighted_cagr":quantile(cagr,.5),"p05_time_weighted_cagr":quantile(cagr,.05),
      "worst_time_weighted_cagr":min(cagr) if cagr else None,"median_daily_max_drawdown":quantile(dd,.5),
      "worst_daily_max_drawdown":min(dd),"windows_below_initial_capital_at_year10":sum(x<INITIAL for x in nav),
      "windows_with_withdrawal_shortfall":sum(x>.01 for x in sf),"median_actual_withdrawals_usd":round(quantile(paid,.5),2),
      "p95_withdrawal_shortfall_usd":round(quantile(sf,.95),2)}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for x in ("panel","windows","summary","flows-csv","out"): ap.add_argument("--"+x,type=Path,required=True)
    a=ap.parse_args(); report=json.loads(a.summary.read_text(encoding="utf-8"))
    need(report.get("schema")=="stock-bond-glidepath-backtest.v1","Unexpected Stage 2 source schema")
    need(float(report["method"]["initial_capital_usd"])==INITIAL,"Initial NAV contract changed")
    need(int(report["method"]["rolling_windows_per_scenario"])==157,"Window count contract changed")
    dates,prices,month_ends,panel_sha=load_panel(a.panel,report); custom=load_schedule(a.flows_csv)
    scenarios={(r["bond_proxy"],int(r["target_bond_conversion_pct_at_year10"]),r["timing_rule"],r["cashflow_mode"]):r for r in report["scenarios"]}
    annuals={(r["bond_proxy"],int(r["target_bond_conversion_pct_at_year10"]),r["timing_rule"],r["cashflow_mode"],int(r["year"])):r for r in report["annual_scenarios"]}
    need(len(scenarios)==1024 and len(annuals)==11264,"Incomplete source summaries")
    stats={"fields_compared":0,"max_abs_error":{},"window_rows_replayed":0,"annual_rows_reconciled":0,
      "scenario_summaries_reconciled":0,"cashflow_invariants_checked":0,"yearly_navs_reconciled":0,"daily_drawdown_paths_replayed":0,"real_floor_annual_rows":0,"real_floor_cohort_rows":0}
    real_floor_annual_counts=[]
    real_floor_cohort_counts=[]
    expected_cohort_years=list(range(2003,2017))
    with a.windows.open(newline="",encoding="utf-8") as f:
      sources=iter(csv.DictReader(f))
      for mode in FLOWS:
       sch=schedule_for(mode,custom)
       for timing in TIMINGS:
        for bond in BONDS:
         for target in TARGETS:
          key=(bond,target,timing,mode); rows=[]; marks_by_year=[[] for _ in range(11)]
          for start in range(157):
           got,marks=replay_window(dates,prices,month_ends,start,bond,target,timing,mode,sch)
           try: src=next(sources)
           except StopIteration: raise ValueError("Window CSV ended before replay completed")
           for field,value in got.items(): close_value(value,src[field],field,stats,f"{key}/{got['window_start']}")
           need(abs(got["requested_withdrawals_usd"]-got["actual_withdrawals_usd"]-got["withdrawal_shortfall_usd"])<=.03,
             f"Requested withdrawals != paid + shortfall: {key}/{got['window_start']}")
           need(abs(got["total_capital_supplied_usd"]-INITIAL-got["additional_deposits_usd"])<=.01,
             f"Supplied capital does not reconcile: {key}/{got['window_start']}")
           need(abs(got["nominal_net_result_usd"]-(got["terminal_nav_usd"]+got["actual_withdrawals_usd"]-got["additional_deposits_usd"]-INITIAL))<=.03,
             f"Nominal net result does not reconcile: {key}/{got['window_start']}")
           stats["cashflow_invariants_checked"]+=3; rows.append(got)
           for i,m in enumerate(marks): marks_by_year[i].append(m)
           stats["window_rows_replayed"]+=1; stats["daily_drawdown_paths_replayed"]+=1
          derived=scenario_summary(rows)
          for field,value in derived.items():
           expected=scenarios[key].get(field)
           if value is None or expected is None:
            need(value is None and expected is None,f"Scenario null mismatch {key}/{field}"); continue
           tol=USD_TOL if field.endswith("_usd") else (DD_TOL if "drawdown" in field else RATE_TOL)
           err=abs(float(value)-float(expected)); name="scenario."+field
           stats["max_abs_error"][name]=max(stats["max_abs_error"].get(name,0),err)
           need(err<=tol,f"Scenario summary mismatch {key}/{field}: {value} vs {expected}")
          stats["scenario_summaries_reconciled"]+=1
          # Re-group the same independently replayed terminal NAVs by calendar start year.
          cohort_navs={}
          for window in rows:
           start_year=int(window["window_start"][:4])
           cohort_navs.setdefault(start_year,[]).append(float(window["terminal_nav_usd"]))
          need(sorted(cohort_navs)==expected_cohort_years,
               f"Real-principal cohort grid differs from pinned start-year grid: {key}/{sorted(cohort_navs)}")
          for start_year in expected_cohort_years:
           nav_values=cohort_navs[start_year]
           count235,count350=real_principal_breach_counts(nav_values,10,expected_windows=len(nav_values))
           real_floor_cohort_counts.append([
             BONDS.index(bond),target,TIMINGS.index(timing),FLOWS.index(mode),
             start_year,len(nav_values),count235,count350
           ])
          for y in range(11):
           ak=(*key,y); derived=annual_summary(marks_by_year[y]); src=annuals[ak]
           for field,value in derived.items():
            expected=src.get(field)
            if value is None or expected is None:
             need(value is None and expected is None,f"Annual null mismatch {ak}/{field}"); continue
            if field.startswith("windows_"):
             need(int(value)==int(expected),f"Annual count mismatch {ak}/{field}"); continue
            tol=USD_TOL if field.endswith("_usd") or field.endswith("_nav_usd") else (DD_TOL if "drawdown" in field else RATE_TOL)
            err=abs(float(value)-float(expected)); name="annual."+field
            stats["max_abs_error"][name]=max(stats["max_abs_error"].get(name,0),err)
            need(err<=tol,f"Annual summary mismatch {ak}/{field}: {value} vs {expected}")
           stats["annual_rows_reconciled"]+=1; stats["yearly_navs_reconciled"]+=1
           year_navs=[float(mark["nav_usd"]) for mark in marks_by_year[y]]
           count235,count350=real_principal_breach_counts(year_navs,y)
           real_floor_annual_counts.append([
             y,BONDS.index(bond),target,TIMINGS.index(timing),FLOWS.index(mode),count235,count350
           ])
           stats["real_floor_annual_rows"]+=1
          if stats["scenario_summaries_reconciled"]%32==0:
           print("LEDGER_REPLAY_PROGRESS",stats["scenario_summaries_reconciled"],"/1024",flush=True)
      try: next(sources); raise ValueError("Window CSV contains unexpected extra rows")
      except StopIteration: pass
    need(stats["window_rows_replayed"]==160768,"Expected 160,768 replayed windows")
    need(stats["annual_rows_reconciled"]==11264,"Expected 11,264 annual rows")
    need(stats["real_floor_annual_rows"]==11264 and len(real_floor_annual_counts)==11264,
         "Expected exact real-principal counts for all 11,264 strategy/year rows")
    stats["real_floor_cohort_rows"]=len(real_floor_cohort_counts)
    need(stats["real_floor_cohort_rows"]==14336,
         f"Expected exact real-principal counts for all 14,336 strategy/start-year cohort rows, got {stats['real_floor_cohort_rows']}")
    need(len({tuple(row[:5]) for row in real_floor_cohort_counts})==14336,
         "Duplicate strategy/start-year real-principal cohort count key")
    need(all(0 < row[5] <= 12 and 0 <= row[6] <= row[7] <= row[5] for row in real_floor_cohort_counts),
         "Cohort real-principal counts violate sample-size/threshold-order contract")
    result={"schema":"glidepath-window-cashflow-ledger-replay.v1","status":"PASS",
      "method":"Independent normalized-share replay from daily adjusted prices with explicit external cashflows; source engine not imported",
      "source_panel_sha256":panel_sha,"source_as_of":dates[-1],"initial_capital_usd":INITIAL,
      "rolling_windows_per_scenario":157,"scenario_count":stats["scenario_summaries_reconciled"],
      "window_rows_expected":160768,"annual_summary_rows_expected":11264,"cashflow_modes":list(FLOWS),"counters":stats,
      "real_floor_annual_count_schema":["year","bond_index","target_pct","timing_index","flow_index","below_real_principal_235_count","below_real_principal_350_count"],
      "real_floor_annual_count_rates":[0.0235,0.035],
      "real_floor_annual_counts":real_floor_annual_counts,
      "real_floor_cohort_count_schema":["bond_index","target_pct","timing_index","flow_index","start_year","window_count","below_real_principal_235_count","below_real_principal_350_count"],
      "real_floor_cohort_count_rates":[0.0235,0.035],
      "real_floor_cohort_count_rows":len(real_floor_cohort_counts),
      "real_floor_cohort_counts":real_floor_cohort_counts,
      "limitations":["Counts compare annual year-end portfolio NAV against initial capital × (1 + assumed annual inflation)^year with a strict less-than test.",
       "For withdrawal modes, counts use remaining portfolio NAV and do not add previously withdrawn cash back to account NAV.",
       "Daily marks are rounded to 10 decimals in the pinned panel; USD tolerance allows sub-cent drift.",
       "XIRR is not recomputed; this audit checks NAV, market return, and external cashflow arithmetic.",
       "157 overlapping ten-year windows are not independent trials.",
       "Pass validates independent accounting reconstruction against a pinned artifact, not predictive validity."]}
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"window_rows_replayed":stats["window_rows_replayed"],
      "annual_rows_reconciled":stats["annual_rows_reconciled"],"scenario_summaries_reconciled":stats["scenario_summaries_reconciled"],
      "cashflow_invariants_checked":stats["cashflow_invariants_checked"],"max_abs_error":stats["max_abs_error"],"audit_file":str(a.out)},
      ensure_ascii=False,indent=2))
if __name__=="__main__": main()
