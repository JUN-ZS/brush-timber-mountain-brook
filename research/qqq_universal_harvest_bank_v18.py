#!/usr/bin/env python3
"""QQQ Universal Harvest Bank V18.

Strategy pool is deliberately limited to real-chain, previously executed lines:
1) Ratio-Call Harvest V1, N=2 BASELINE_TOUCH.
2) Real-Chain Downside Convexity V1, SHOCK_GATED.

Seed:
- every positive N>2 trade in the strict V16 path is treated as an independent
  historical Risk-Win seed.
- Each seed is replayed forward through the universal opportunity pool.

Universal bank:
- Bank starts at the seed WIN P&L.
- One opportunity at a time; no overlap.
- A candidate is executable only if its strategy-specific observed risk
  requirement <= current Bank.
- After realization: Bank=max(0, Bank+P&L).
- This is a rights/risk budget, not cash collateral or NAV.
- Fixed tie-break: entry date, then CONVEXITY_SHOCK, then RATIO_HARVEST_N2.
- A 10-calendar-day global re-entry gap after each realized opportunity.
- Two modes:
  REPLENISH: subsequent strategy WINs replenish Bank.
  ISOLATED: subsequent strategy WINs are not allowed to replenish Bank;
            only losses consume the original seed.

This is an explicit counterfactual research construct, not a deployment rule.
No parameter optimization, BS pricing, or interpolation is introduced.
"""

from __future__ import annotations
import argparse,json
from pathlib import Path
import pandas as pd
import numpy as np

BASE_GATE=64102.5641025641*0.02
GLOBAL_GAP_DAYS=10

def load_seed(path):
    x=pd.read_csv(path)
    x["entry"]=pd.to_datetime(x["entry"])
    x["exit"]=pd.to_datetime(x["exit"])
    x=x[(x["n"]>2)&(x["pnl_usd"]>0)].copy()
    return x.sort_values("entry").reset_index(drop=True)

def ratio_pool(path):
    x=pd.read_csv(path)
    x["entry"]=pd.to_datetime(x["entry"])
    x["exit"]=pd.to_datetime(x["exit"])
    x["risk"]=x["max_loss_proxy_usd"].astype(float)
    x["pnl"]=x["pnl_usd"].astype(float)
    return x[["entry","exit","risk","pnl"]].assign(strategy="RATIO_HARVEST_N2")

def conv_pool(path):
    x=pd.read_csv(path)
    x["entry"]=pd.to_datetime(x["entry"])
    x["exit"]=pd.to_datetime(x["exit"])
    x["risk"]=x["debit_usd"].astype(float)
    x["pnl"]=x["realized_pnl_usd"].astype(float)
    return x[["entry","exit","risk","pnl"]].assign(strategy="CONVEXITY_SHOCK")

def simulate_seed(seed_row,pool,replenish):
    bank=float(seed_row["pnl_usd"])
    start=pd.Timestamp(seed_row["exit"])
    last_exit=start
    accepted=[]
    i=0
    while i<len(pool):
        avail=pool[pool.entry>last_exit+pd.Timedelta(days=GLOBAL_GAP_DAYS)]
        if avail.empty: break
        cand=avail.sort_values(["entry","priority"]).iloc[0]
        if float(cand.risk)>bank:
            i=pool.index[pool.entry==cand.entry].max()+1 if (pool.entry==cand.entry).any() else i+1
            # Move beyond this candidate date; it cannot be used later.
            pool=pool[pool.entry>cand.entry].copy().reset_index(drop=True)
            i=0
            continue
        accepted.append(cand.to_dict())
        bank=max(0.0,bank+float(cand.pnl) if replenish else bank+min(0.0,float(cand.pnl)))
        last_exit=pd.Timestamp(cand.exit)
        pool=pool[pool.entry>last_exit].copy().reset_index(drop=True)
        if bank<=0: break
    end=pd.Timestamp(accepted[-1]["exit"]) if accepted else start
    return accepted,bank, {
        "seed_entry":str(pd.Timestamp(seed_row["entry"]).date()),
        "seed_exit":str(start.date()),
        "seed_n":int(seed_row["n"]),
        "seed_pnl_usd":float(seed_row["pnl_usd"]),
        "mode":"REPLENISH" if replenish else "ISOLATED",
        "future_opportunities":len(accepted),
        "distinct_strategies":len(set(x["strategy"] for x in accepted)),
        "ratio_count":sum(x["strategy"]=="RATIO_HARVEST_N2" for x in accepted),
        "convexity_count":sum(x["strategy"]=="CONVEXITY_SHOCK" for x in accepted),
        "max_n_ahead":int(max([int(seed_row["n"])] + [2 if x["strategy"]=="RATIO_HARVEST_N2" else 0 for x in accepted])),
        "gross_risk_traversed_usd":float(sum(float(x["risk"]) for x in accepted)),
        "lifetime_days":int((end-pd.Timestamp(seed_row["entry"])).days),
        "final_bank_usd":float(bank),
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--seed-ledger",required=True)
    ap.add_argument("--ratio-ledger",required=True)
    ap.add_argument("--convexity-ledger",required=True)
    ap.add_argument("--out",default="artifacts")
    a=ap.parse_args()
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)

    seeds=load_seed(a.seed_ledger)
    ratio=ratio_pool(a.ratio_ledger)
    conv=conv_pool(a.convexity_ledger)
    ratio["priority"]=1;conv["priority"]=0
    pool=pd.concat([conv,ratio],ignore_index=True).sort_values(["entry","priority"]).reset_index(drop=True)

    rows=[];events=[]
    for _,seed in seeds.iterrows():
        for replenish in (False,True):
            ev,bank,summary=simulate_seed(seed,pool.copy(),replenish)
            rows.append(summary)
            for e in ev:
                e2=dict(e)
                e2["seed_entry"]=str(pd.Timestamp(seed["entry"]).date())
                e2["seed_n"]=int(seed["n"])
                e2["mode"]="REPLENISH" if replenish else "ISOLATED"
                events.append(e2)

    df=pd.DataFrame(rows); edf=pd.DataFrame(events)
    df.to_csv(out/"universal_harvest_seed_summary.csv",index=False)
    edf.to_csv(out/"universal_harvest_events.csv",index=False)

    agg=[]
    for mode in ("ISOLATED","REPLENISH"):
        z=df[df.mode==mode]
        if z.empty: continue
        agg.append({
            "mode":mode,"seeds":len(z),
            "mean_lifetime_days":float(z.lifetime_days.mean()),
            "median_lifetime_days":float(z.lifetime_days.median()),
            "max_lifetime_days":int(z.lifetime_days.max()),
            "mean_future_opportunities":float(z.future_opportunities.mean()),
            "median_future_opportunities":float(z.future_opportunities.median()),
            "max_future_opportunities":int(z.future_opportunities.max()),
            "mean_distinct_strategies":float(z.distinct_strategies.mean()),
            "seeds_using_both_strategies":int((z.distinct_strategies>=2).sum()),
            "mean_gross_risk_traversed_usd":float(z.gross_risk_traversed_usd.mean()),
            "median_gross_risk_traversed_usd":float(z.gross_risk_traversed_usd.median()),
            "max_gross_risk_traversed_usd":float(z.gross_risk_traversed_usd.max()),
        })

    report={
      "research_id":"QQQ_UNIVERSAL_HARVEST_BANK_V18",
      "status":"REAL_QQQ_CHAIN_STRATEGY_POOL_COUNTERFACTUAL",
      "strategies":[
        {"name":"RATIO_HARVEST_N2","source_run":36550743553,"risk_field":"max_loss_proxy_usd","pnl_field":"pnl_usd"},
        {"name":"CONVEXITY_SHOCK","source_run":36550732916,"risk_field":"debit_usd","pnl_field":"realized_pnl_usd"}],
      "contract":{
        "seed":"positive N>2 V16 Risk-Win",
        "bank":"seed WIN is common Universal Bank",
        "entry_rule":"candidate risk <= Bank",
        "update_replenish":"Bank=max(0,Bank+all realized strategy P&L)",
        "update_isolated":"later positive P&L ignored; only later losses consume Bank",
        "one_active_opportunity":True,
        "global_gap_days":GLOBAL_GAP_DAYS,
        "tie_break":"entry date, then CONVEXITY_SHOCK, then RATIO_HARVEST_N2",
        "bank_is_not_nav":True,
        "optimization":False},
      "data":{"options_sha256":"1f831556cd87ec9d7af43d3b47a69a829ffb2fb199cfcef4ff55d289badf8734",
              "underlying_sha256":"78c015fd7fa9d493cd798d5ae81b3c2ae6dc3b8176e25e7bb90cd4114b103351"},
      "results":{"aggregate":agg}}
    (out/"qqq_universal_harvest_bank_v18_result.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2),flush=True)

if __name__=="__main__":
    main()
