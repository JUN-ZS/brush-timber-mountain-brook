#!/usr/bin/env python3
"""Conditional historical REF: SPY drawdown state x lagged QQQ/SPY correlation."""
import csv, hashlib, json, math, statistics, urllib.request
from collections import defaultdict
from datetime import date
from pathlib import Path
import pyarrow.parquet as pq

ROOT=Path(__file__).resolve().parent
BASE=ROOT/"results"/"premium_matched_dte14_q60_70_v1"
TAIL=BASE/"tail_overlay_v1"/"episode_paired.csv"
OUT=BASE/"spy_drawdown_correlation_ref_v1"
START,END="2018-03-01","2025-12-15"
YEARS=(date.fromisoformat(END)-date.fromisoformat(START)).days/365.2425
SOURCE="https://raw.githubusercontent.com/anahatsingh-ui/options-dataset-hist/main"
PINS={"QQQ":(332454,"f3a892bc4c88c692900b5c0071322c6db408996a"),
      "SPY":(252066,"4c22934a77ba09ced10fd1c413b5d8c9e0cb4a8d")}
EXPECTED={"1x3":-33466.20,"1x6":-16768.10}

def blob_sha(p,n):
    h=hashlib.sha1(); h.update(f"blob {n}\0".encode())
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()

def load_prices(sym,cache):
    n,sha=PINS[sym]; p=cache/(sym.lower()+"_underlying_prices.parquet")
    if not p.exists() or p.stat().st_size!=n or blob_sha(p,n)!=sha:
        p.unlink(missing_ok=True); h=hashlib.sha1(); h.update(f"blob {n}\0".encode()); size=0
        req=urllib.request.Request(f"{SOURCE}/{sym.lower()}/underlying_prices.parquet",
          headers={"User-Agent":"spy-qqq-drawdown-correlation-ref/1.0"})
        with urllib.request.urlopen(req,timeout=180) as r,p.open("wb") as f:
            while True:
                b=r.read(1<<20)
                if not b: break
                f.write(b); h.update(b); size+=len(b)
        if size!=n or h.hexdigest()!=sha: raise ValueError(f"{sym} source hash mismatch")
    t=pq.read_table(p); c={x.lower():x for x in t.column_names}
    dc,sc,cc=c.get("date"),c.get("symbol"),c.get("close") or c.get("raw_close")
    if not dc or not sc or not cc: raise ValueError(f"Unexpected schema {t.column_names}")
    out={}
    for d,s,v in zip(t[dc].to_pylist(),t[sc].to_pylist(),t[cc].to_pylist()):
        day=d.isoformat()[:10] if hasattr(d,"isoformat") else str(d)[:10]
        try: v=float(v)
        except (TypeError,ValueError): continue
        if str(s).upper()==sym and v>0 and math.isfinite(v): out[day]=v
    if not out: raise ValueError(f"No {sym} data")
    return out,{"symbol":sym,"bytes":n,"git_blob_sha":sha,"rows":len(out),
      "first_date":min(out),"last_date":max(out),"price_field":cc}

def pearson(x,y):
    if len(x)<2 or len(x)!=len(y): return None
    mx,my=statistics.mean(x),statistics.mean(y)
    dx=[v-mx for v in x]; dy=[v-my for v in y]
    den=math.sqrt(sum(v*v for v in dx)*sum(v*v for v in dy))
    return sum(a*b for a,b in zip(dx,dy))/den if den else None

def episodes(ratio):
    found={}
    with TAIL.open(newline="",encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("ratio")!=ratio: continue
            try: budget=float(r["tail_budget_usd_per_cohort"]); bps=float(r["tail_friction_bps_round_trip"])
            except (KeyError,ValueError): continue
            if abs(budget-250)>1e-9 or abs(bps)>1e-9: continue
            eid=r["episode_id"]
            if eid in found: raise ValueError(f"Duplicate episode {eid}")
            found[eid]={"ratio":ratio,"episode_id":eid,"entry_date":r["entry_date"],
              "exit_date":r["exit_date"],"base_net_pnl_usd":float(r["base_net_pnl_usd"])}
    rows=sorted(found.values(),key=lambda x:(x["entry_date"],x["episode_id"]))
    if len(rows)!=391: raise ValueError(f"{ratio}: expected 391 resolved episodes, got {len(rows)}")
    total=sum(r["base_net_pnl_usd"] for r in rows)
    if abs(total-EXPECTED[ratio])>1: raise ValueError(f"{ratio}: base P&L integrity mismatch {total}")
    return rows

def summarize(rows,condition,ratio):
    p=[r["base_net_pnl_usd"] for r in rows]; by_year=defaultdict(float)
    for r in rows: by_year[r["entry_date"][:4]]+=r["base_net_pnl_usd"]
    return {"ratio":ratio,"condition":condition,"n":len(p),"sum_episode_pnl_usd":round(sum(p),2),
      "mean_per_episode_usd":round(statistics.mean(p),2) if p else None,
      "median_per_episode_usd":round(statistics.median(p),2) if p else None,
      "win_rate_pct":round(100*sum(v>0 for v in p)/len(p),2) if p else None,
      "worst_episode_usd":round(min(p),2) if p else None,
      "best_episode_usd":round(max(p),2) if p else None,
      "annual_average_episode_sum_usd":round(sum(p)/YEARS,2),
      "entry_year_pnl_usd":{k:round(v,2) for k,v in sorted(by_year.items())},
      "cagr":None,"cagr_note":"Overlapping episode P&L is not an account NAV; CAGR unavailable."}

def main():
    OUT.mkdir(parents=True,exist_ok=True); cache=OUT/"source_cache"; cache.mkdir(exist_ok=True)
    q,qmeta=load_prices("QQQ",cache); s,smeta=load_prices("SPY",cache)
    common=sorted(set(q)&set(s)); idx={d:i for i,d in enumerate(common)}
    qr,sr={},{}
    for i in range(1,len(common)):
        d,prev=common[i],common[i-1]; qr[d]=q[d]/q[prev]-1; sr[d]=s[d]/s[prev]-1
    study=[d for d in common if START<=d<=END and d in qr and d in sr]
    fullcorr=pearson([qr[d] for d in study],[sr[d] for d in study])
    # SPY high-water mark starts from earliest available date, not from March 2018.
    dd={}; peak=-float("inf")
    for d in sorted(s):
        peak=max(peak,s[d]); dd[d]=s[d]/peak-1
    rollcorr={}
    for d in common:
        i=idx[d]; prev=common[max(1,i-60):i]
        x=[qr[z] for z in prev if z in qr and z in sr]
        y=[sr[z] for z in prev if z in qr and z in sr]
        rollcorr[d]=pearson(x,y) if len(x)>=45 else None
    details=[]; summary=[]
    for ratio in ("1x3","1x6"):
        rr=[]
        for e in episodes(ratio):
            a,b=e["entry_date"],e["exit_date"]
            if a not in s or b not in s or a not in q or b not in q: raise ValueError(f"Missing price {a}->{b}")
            active=[d for d in common if a<=d<=b]
            if not active: raise ValueError("No underlying observations during episode")
            entrydd=dd[a]; pathdd=min(dd[d] for d in active)
            entryret=min(s[d]/s[a]-1 for d in active); c=rollcorr.get(a); pos=c is not None and c>0
            z={**e,"spy_ath_drawdown_at_entry_pct":round(100*entrydd,4),
               "spy_worst_ath_drawdown_during_episode_pct":round(100*pathdd,4),
               "spy_worst_return_from_entry_during_episode_pct":round(100*entryret,4),
               "qqq_spy_pearson_corr_prior_60_sessions":round(c,6) if c is not None else None,
               "prior_60d_corr_positive":pos}
            for t in (10,15):
                z[f"entry_ath_no_breach_{t}pct_corrpos"]=bool(entrydd>=-t/100 and pos)
                z[f"whole_episode_ath_no_breach_{t}pct_corrpos"]=bool(pathdd>=-t/100 and pos)
                z[f"whole_episode_entry_return_no_breach_{t}pct_corrpos"]=bool(entryret>=-t/100 and pos)
            details.append(z); rr.append(z)
        filters=[("all_resolved_baseline",lambda x:True),
                 ("positive_prior_60d_correlation_only",lambda x:x["prior_60d_corr_positive"])]
        for t in (10,15):
            filters += [
              (f"entry_SPY_ATH_drawdown_not_below_minus_{t}pct_AND_corr60_positive",lambda x,t=t:x[f"entry_ath_no_breach_{t}pct_corrpos"]),
              (f"whole_episode_SPY_ATH_drawdown_not_below_minus_{t}pct_AND_corr60_positive",lambda x,t=t:x[f"whole_episode_ath_no_breach_{t}pct_corrpos"]),
              (f"whole_episode_SPY_return_from_entry_not_below_minus_{t}pct_AND_corr60_positive",lambda x,t=t:x[f"whole_episode_entry_return_no_breach_{t}pct_corrpos"])]
        for name,fn in filters: summary.append(summarize([x for x in rr if fn(x)],name,ratio))
    with (OUT/"episode_classification.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(details[0])); w.writeheader(); w.writerows(details)
    result={"schema":"spy-drawdown-qqq-correlation-ref.v1","status":"COMPLETED",
      "window":{"start":START,"end":END,"elapsed_years":round(YEARS,6)},
      "strategy":{"source":"existing premium-matched DTE14 replay; no re-selection",
        "positions":"1 QQQ LONG PUT : 3 or 6 SPY SHORT PUTs","exit_policy":"HOLD_20_OR_DTE_LE_7",
        "resolved_episodes_each_ratio":391,"tail_pnl_included":False,
        "episode_pnl_source":"base_net_pnl_usd; one unique row from $250 / zero-friction carrier slice"},
      "source":{"repository":"anahatsingh-ui/options-dataset-hist","tree_commit":"37f6c456fe1a4775c875673fb8ef907d5cd2fd66","QQQ":qmeta,"SPY":smeta},
      "correlation":{"full_period_daily_close_return_pearson":round(fullcorr,6),"daily_return_observations":len(study),
        "entry_gate":"Pearson correlation over prior 60 common-session returns; ends before entry; strictly > 0"},
      "drawdown_definitions":{"ATH":"SPY close / running maximum close since earliest available source date (1999) - 1",
        "entry_ATH":"Implementable entry-time state; drawdown no worse than threshold",
        "whole_episode_ATH":"Ex-post: ATH drawdown never worse than threshold during entry-to-exit path",
        "entry_return":"Ex-post: SPY never falls more than threshold below cohort-entry close",
        "intraday_data":False},"summary":summary,
      "limitations":["Cohorts overlap; episode sums and episode sums divided by calendar years are not account CAGR.",
        "Whole-episode gates use future prices and are diagnostics, not tradable entry filters.",
        "Close-based SPY drawdown can miss intraday threshold breaches; close series is not total-return data.",
        "Historical EOD options quotes are not verified fills; base P&L uses existing costs.",
        "No account capital, margin, assignment funding, forced liquidation, tax or financing model."]}
    (OUT/"summary.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    lines=["# SPY drawdown x QQQ correlation — historical REF condition replay","",
      f"Window: {START} to {END} ({YEARS:.3f} years); premium-matched DTE14; HOLD_20_OR_DTE_LE_7; 391 resolved cohorts per ratio.","",
      "## Correlation","",
      f"- Full-period Pearson correlation of daily close returns on common QQQ/SPY sessions: **{fullcorr:.4f}**.",
      "- Entry correlation filter: prior 60 common-session daily returns, ending before entry; strictly positive.","",
      "## Conditional results — base strategy P&L, no TAIL","",
      "Annual-average episode sum = qualifying P&L divided by the full 7.792-year sample; this is NOT CAGR or a capital-constrained annual return.","",
      "| Ratio | Condition | N | Sum P&L | Mean / episode | Median / episode | Win rate | Worst | Annual-average episode sum |",
      "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for z in summary:
        fmt=lambda v:"n/a" if v is None else "USD "+format(v,",.2f")
        win="n/a" if z["win_rate_pct"] is None else format(z["win_rate_pct"],".2f")+"%"
        lines.append(f"| {z['ratio'].replace('x',':')} | {z['condition']} | {z['n']} | {fmt(z['sum_episode_pnl_usd'])} | {fmt(z['mean_per_episode_usd'])} | {fmt(z['median_per_episode_usd'])} | {win} | {fmt(z['worst_episode_usd'])} | {fmt(z['annual_average_episode_sum_usd'])} |")
    lines += ["","## Definitions","",
      "- Entry ATH gate: at entry, SPY is no more than 10%/15% below its running all-history close high. This is the implementable state filter.",
      "- Whole-episode ATH gate: every close during a trade remains above the threshold relative to SPY's all-history high. Ex-post only.",
      "- Whole-episode entry-return gate: SPY never closes 10%/15% below the cohort's entry close through exit. Ex-post only.",
      "- ATH starts at the earliest source date in 1999 to avoid resetting the high-water mark at the 2018 start. Intraday breaches may be missed.",
      "- Episodes overlap. Their P&L sum is not compounded account P&L; account CAGR requires daily NAV, capital sizing, margin and assignment handling.",
      "- Rolling correlation is a lagged condition, not causation or a guarantee of future correlation.","",
      "## Outputs","",
      "- episode_classification.csv: each cohort's entry/exit path, SPY drawdown and lagged correlation flags.",
      "- summary.json: aggregate results and data-source identities. Price files are checked against pinned Git blob hashes."]
    (OUT/"REF_REPORT.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps({"status":"COMPLETED","full_period_daily_return_pearson":fullcorr,"episodes":len(details),
      "summary_rows":len(summary),"baseline":{r:round(sum(x["base_net_pnl_usd"] for x in episodes(r)),2) for r in ("1x3","1x6")}},indent=2))

if __name__=="__main__": main()
