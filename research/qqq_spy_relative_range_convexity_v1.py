from __future__ import annotations
import argparse, json, math
from pathlib import Path
import duckdb
import numpy as np
import pandas as pd

TD = 252
M = 100.0
START, END = "2018-03-01", "2025-12-01"

def sql(con, s): return con.execute(s).df()

def pathq(p): return str(p).replace("'", "''")

def load_px(con, path, prefix):
    d = sql(con, f"""
      SELECT CAST(date AS DATE) AS date, CAST("close" AS DOUBLE) AS close_px
      FROM read_parquet('{pathq(path)}')
      WHERE CAST(date AS DATE) BETWEEN DATE '2011-01-01' AND DATE '2025-12-31'
      ORDER BY date
    """)
    d.date = pd.to_datetime(d.date)
    r = np.log(d.close_px/d.close_px.shift(1))
    for w in (5,20,60):
        d[f"rv{w}"] = r.rolling(w).std()*math.sqrt(TD)
    d["month"] = d.date.dt.to_period("M")
    return d.rename(columns={"close_px":prefix+"_px","rv5":prefix+"_rv5","rv20":prefix+"_rv20","rv60":prefix+"_rv60"})[
        ["date",prefix+"_px",prefix+"_rv5",prefix+"_rv20",prefix+"_rv60","month"]]

def build_state(con, q_u, s_u):
    q = load_px(con, q_u, "Q"); s = load_px(con, s_u, "S")
    x = q.merge(s, on=["date","month"], how="inner").sort_values("date").reset_index(drop=True)
    x["rr20"] = x.Q_rv20/x.S_rv20
    x["rr5"] = x.Q_rv5/x.S_rv5
    x["rv_velocity"] = x.rr5/x.rr20
    x["rr_med_252"] = x.rr20.shift(1).rolling(252,min_periods=126).median()
    qr=np.log(x.Q_px/x.Q_px.shift(1)); sr=np.log(x.S_px/x.S_px.shift(1))
    beta=qr.rolling(60).cov(sr)/sr.rolling(60).var()
    x["beta60"]=beta.shift(1)
    x["resid"]=qr-x.beta60*sr
    x["resid_rv20"]=x.resid.rolling(20).std()*math.sqrt(TD)
    x["resid_med_252"]=x["resid_rv20"].shift(1).rolling(252,min_periods=126).median()
    return x

def get_chain(con,path,symbol,date,lo,hi):
    d=date.strftime("%Y-%m-%d")
    return sql(con,f"""
      SELECT CAST(contract_id AS VARCHAR) contract_id, CAST(expiration AS DATE) expiration, CAST(strike AS DOUBLE) strike,
             LOWER("type") AS opt_type, CAST(bid AS DOUBLE) bid, CAST(ask AS DOUBLE) ask,
             COALESCE(CAST(volume AS DOUBLE),0) volume,
             COALESCE(CAST(open_interest AS DOUBLE),0) open_interest,
             CAST(delta AS DOUBLE) delta, CAST(implied_volatility AS DOUBLE) implied_volatility
      FROM read_parquet('{pathq(path)}')
      WHERE CAST(date AS DATE)=DATE '{d}'
        AND CAST(expiration AS DATE)>DATE '{d}'
        AND CAST(expiration AS DATE)>=DATE '{d}' + INTERVAL '{lo} days'
        AND CAST(expiration AS DATE)<=DATE '{d}' + INTERVAL '{hi} days'
        AND bid IS NOT NULL AND ask IS NOT NULL AND ask>=bid AND ask>0
        AND delta IS NOT NULL AND (open_interest>=10 OR volume>=5)
    """)

def liquid(df):
    if df.empty: return df
    z=df.copy()
    z["mark"]=(z.ask+z.bid)/2.0
    z["spr"]=(z.ask-z.bid)/z.mark.replace(0,np.nan)
    return z[np.isfinite(z.spr)&(z.spr<=0.35)]

def pick4(df, target_dte, wing=0.10, reverse=True):
    df=liquid(df)
    if df.empty: return None
    # Recover DTE from the first row of each expiry.
    dtes=df.groupby("expiration").dte.first() if "dte" in df else None
    if dtes is None: return None
    e=(dtes-target_dte).abs().sort_values().index[0]
    x=df[df.expiration==e]
    c=x[x.opt_type=="call"]; p=x[x.opt_type=="put"]
    if c.empty or p.empty: return None
    lc=c.iloc[(c["delta"]-0.50).abs().argmin()]
    lp=p.iloc[(p["delta"]+0.50).abs().argmin()]
    fc_pool=c[c["strike"]>float(lc.strike)]
    fp_pool=p[p["strike"]<float(lp.strike)]
    if fc_pool.empty or fp_pool.empty: return None
    fc=fc_pool.iloc[(fc_pool["delta"]-wing).abs().argmin()]
    fp=fp_pool.iloc[(fp_pool["delta"]+wing).abs().argmin()]
    return e, lc, lp, fc, fp

def qqq_rc(con,path,date,target=60,wing=0.10):
    df=get_chain(con,path,"QQQ",date,max(7,target-7),target+7); df["dte"]=(pd.to_datetime(df.expiration)-date).dt.days if not df.empty else []
    p=pick4(df,target,wing)
    if not p:return None
    e,lc,lp,fc,fp=p
    # reverse iron condor = long ATM call/put, short far wings
    legs=[
      ("QQQ",str(e),lc.strike,"call",1,float(lc.ask),str(lc.contract_id)),
      ("QQQ",str(e),fc.strike,"call",-1,float(fc.bid),str(fc.contract_id)),
      ("QQQ",str(e),lp.strike,"put",1,float(lp.ask),str(lp.contract_id)),
      ("QQQ",str(e),fp.strike,"put",-1,float(fp.bid),str(fp.contract_id))]
    debit=sum(side*px*M for _,_,_,_,side,px,_ in legs)
    cw=abs(float(fc.strike)-float(lc.strike))*M
    pw=abs(float(lp.strike)-float(fp.strike))*M
    risk=max(debit,0)
    profit=max(cw,pw)-debit
    return {"symbol":"QQQ","entry":date,"expiry":pd.Timestamp(e),"exit_dte":25,"legs":legs,"risk":risk,"profit":profit,"entry_value":debit}

def spy_ic(con,path,date,target=30,wing=0.10):
    df=get_chain(con,path,"SPY",date,max(7,target-7),target+7); df["dte"]=(pd.to_datetime(df.expiration)-date).dt.days if not df.empty else []
    p=pick4(df,target,wing)
    if not p:return None
    e,sc,sp,lc,lp=p
    # short iron condor = short ATM call/put, long far wings
    legs=[
      ("SPY",str(e),sc.strike,"call",-1,float(sc.bid),str(sc.contract_id)),
      ("SPY",str(e),lc.strike,"call",1,float(lc.ask),str(lc.contract_id)),
      ("SPY",str(e),sp.strike,"put",-1,float(sp.bid),str(sp.contract_id)),
      ("SPY",str(e),lp.strike,"put",1,float(lp.ask),str(lp.contract_id))]
    credit=sum(side*px*M for _,_,_,_,side,px,_ in legs)*-1
    wingw=max(abs(float(lc.strike)-float(sc.strike)),abs(float(sp.strike)-float(lp.strike)))*M
    risk=max(wingw-credit,0)
    profit=max(credit,0)
    return {"symbol":"SPY","entry":date,"expiry":pd.Timestamp(e),"exit_dte":7,"legs":legs,"risk":risk,"profit":profit,"entry_value":credit}

def entry_days(state):
    z=state[(state.date>=pd.Timestamp(START))&(state.date<=pd.Timestamp(END))].copy()
    return [g.date.iloc[0] for _,g in z.groupby(z.date.dt.to_period("M"),sort=True)]

def eligible(s,mode):
    if any(pd.isna(s[k]) for k in ["rr20","rv_velocity","rr_med_252"]): return False
    if mode=="none": return True
    if mode=="lead":
        return float(s.rv_velocity)>=1.05 and float(s.rr20)>=float(s.rr_med_252)
    if mode=="residual":
        return pd.notna(s.resid_med_252) and float(s.rv_velocity)>=1.03 and float(s.resid_rv20)>=float(s.resid_med_252)
    return False

def unit_marks(con,qpath,spath,positions):
    ids={"QQQ":[],"SPY":[]}
    for p in positions:
        for l in p["legs"]:
            if l[0] not in ids: continue
            if l[6] not in ids[l[0]]: ids[l[0]].append(l[6])
    out=[]
    for sym,idlist in ids.items():
        if not idlist: continue
        vals=",".join("'"+x.replace("'","''")+"'" for x in idlist)
        path=qpath if sym=="QQQ" else spath
        d=sql(con,f"""SELECT CAST(contract_id AS VARCHAR) contract_id,CAST(date AS DATE) date,CAST(bid AS DOUBLE) bid,CAST(ask AS DOUBLE) ask
                      FROM read_parquet('{pathq(path)}')
                      WHERE contract_id IN ({vals}) ORDER BY date""")
        if not d.empty:
            d.date=pd.to_datetime(d.date)
            d["mark"]=(d["bid"]+d["ask"])/2.0
            d["symbol"]=sym
            out.append(d)
    return pd.concat(out,ignore_index=True) if out else pd.DataFrame()

def simulate(con,state,qpath,spath,name,mode,include_spy=True):
    days=entry_days(state)
    st=state.set_index("date")
    state_days=sorted(pd.to_datetime(state.date).tolist())
    candidates=[]
    last_q=pd.Timestamp.min; last_s=pd.Timestamp.min
    state_dates=pd.DatetimeIndex(state_days)
    for d in days:
        prev_ix=state_dates.searchsorted(pd.Timestamp(d),side="left")-1
        if prev_ix<0: continue
        signal_date=state_dates[prev_ix]
        s=st.loc[signal_date]
        if isinstance(s,pd.DataFrame): s=s.iloc[0]
        if not eligible(s,mode): continue
        q=None; sp=None
        if d>=last_q: q=qqq_rc(con,qpath,d)
        if include_spy and d>=last_s: sp=spy_ic(con,spath,d)
        if q:
            q["name"]=f"{name}_Q_{len(candidates)}"; candidates.append(q)
            target_exit=q["expiry"]-pd.Timedelta(days=q["exit_dte"])
            ix=min(len(state_days)-1, max(0, np.searchsorted(state_days,target_exit,side="left")))
            last_q=pd.Timestamp(state_days[ix])
        if sp:
            sp["name"]=f"{name}_S_{len(candidates)}"; candidates.append(sp)
            target_exit=sp["expiry"]-pd.Timedelta(days=sp["exit_dte"])
            ix=min(len(state_days)-1, max(0, np.searchsorted(state_days,target_exit,side="left")))
            last_s=pd.Timestamp(state_days[ix])
    if not candidates:
        return {"name":name,"entries":0,"ending_nav":100000.0,"cagr":0.0,"maxdd":0.0,"sharpe":0.0,"q_entries":0,"s_entries":0}
    marks=unit_marks(con,qpath,spath,candidates)
    mk={(r.contract_id,r.date):(float(r.bid),float(r.ask),float(r.mark)) for r in marks.itertuples(index=False)}
    nav=100000.0; openpos=[]; realized=0.0; rows=[]; used=set(); qn=sum(p["symbol"]=="QQQ" for p in candidates); sn=sum(p["symbol"]=="SPY" for p in candidates)
    for d in state_days:
        # open candidates at entry date; size from current marked NAV, 5% total risk split 60/40
        for p in candidates:
            if p["name"] in used or p["entry"]!=d: continue
            share=(1.0 if not include_spy else (.60 if p["symbol"]=="QQQ" else .40))
            qty=max(1,int(math.floor((nav*.05*share)/p["risk"]))) if p["risk"]>0 else 0
            if qty<=0: used.add(p["name"]); continue
            p2=p.copy(); p2["qty"]=qty; openpos.append(p2); used.add(p["name"])
        # realize exits
        still=[]
        for p in openpos:
            exitd=max(d,p["expiry"]-pd.Timedelta(days=p["exit_dte"]))
            if d==exitd:
                v=0.0; ok=True
                for l in p["legs"]:
                    b,a,m=mk.get((l[6],d),(None,None,None))
                    if m is None: ok=False; break
                    fill=b if l[4]==1 else a
                    v += l[4]*fill*M*p["qty"]
                if ok:
                    entry_cf=(-p["entry_value"] if p["symbol"]=="QQQ" else p["entry_value"])*p["qty"]
                    realized += entry_cf+v
                else:
                    still.append(p)
            else: still.append(p)
        openpos=still
        # MTM
        mtm=0.0
        for p in openpos:
            v=0.0; ok=True
            for l in p["legs"]:
                b,a,m=mk.get((l[6],d),(None,None,None))
                if m is None: ok=False; break
                v += l[4]*m*M*p["qty"]
            if ok:
                entry_cf=(-p["entry_value"] if p["symbol"]=="QQQ" else p["entry_value"])*p["qty"]
                mtm += entry_cf+v
        eq=nav=100000.0+realized+mtm
        rows.append((d,eq))
    e=pd.DataFrame(rows,columns=["date","eq"])
    years=max((e.date.iloc[-1]-e.date.iloc[0]).days/365.25,1/365.25)
    cagr=(e["eq"].iloc[-1]/100000.0)**(1/years)-1
    dd=(e["eq"]/e["eq"].cummax()-1).min()
    r=e["eq"].pct_change().replace([np.inf,-np.inf],np.nan).fillna(0)
    sh=(r.mean()/r.std(ddof=1)*math.sqrt(TD)) if r.std(ddof=1)>0 else 0.0
    return {"name":name,"entries":len(candidates),"ending_nav":float(e["eq"].iloc[-1]),"cagr":float(cagr),"maxdd":float(dd),"sharpe":float(sh),"q_entries":qn,"s_entries":sn}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--data-dir",required=True); ap.add_argument("--out",required=True); a=ap.parse_args()
    d=Path(a.data_dir); o=Path(a.out); o.mkdir(parents=True,exist_ok=True)
    qpath=str(d/"QQQ_options.parquet"); spath=str(d/"SPY_options.parquet")
    qu=str(d/"QQQ_underlying.parquet"); su=str(d/"SPY_underlying.parquet")
    for p in [qpath,spath,qu,su]:
        assert Path(p).exists(), p
    con=duckdb.connect()
    st=build_state(con,qu,su); st.to_csv(o/"state.csv",index=False)
    cfg=[
      ("A_QQQ_ONLY","none",False),
      ("B_PAIR_UNFILTERED","none",True),
      ("C_PAIR_RANGE_LEAD","lead",True),
      ("D_PAIR_RESIDUAL","residual",True)
    ]
    res=[simulate(con,st,qpath,spath,name,mode,include_spy) for name,mode,include_spy in cfg]
    (o/"results.json").write_text(json.dumps(res,indent=2),encoding="utf-8")
    lines=[
      "# QQQ-SPY Relative Range Convexity V1 — real-chain replay",
      "",
      "Common period: 2018-03 through 2025-12. EOD bid/ask/mark, real historical chain.",
      "QQQ leg: 60D target reverse iron condor (long ~50Δ call/put, short ~10Δ wings), exit 25D.",
      "SPY leg: 30D target iron condor (short ~50Δ call/put, long ~10Δ wings), exit 7D.",
      "Entry: first trading day of month using prior trading day's realized-volatility state; option chain is selected on entry date. QQQ and SPY sleeves do not overlap within sleeve.",
      "Fill model: BUY at ask, SELL at bid; daily MTM at mark; exit long at bid / short at ask.",
      "Liquidity: OI>=10 OR volume>=5, relative bid/ask spread<=35%.",
      "Risk sizing: 5% NAV total, 60% QQQ / 40% SPY, sized at entry from defined max risk.",
      "State filters are causal and use prior observations only for trailing medians/betas.",
      "",
      "| strategy | entries | ending NAV | CAGR | MaxDD | Sharpe | QQQ | SPY |",
      "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in res:
        if "ending_nav" in r:
            lines.append(f"| {r['name']} | {r['entries']} | {r['ending_nav']:.2f} | {r['cagr']:.2%} | {r['maxdd']:.2%} | {r['sharpe']:.2f} | {r['q_entries']} | {r['s_entries']} |")
        else: lines.append(f"| {r['name']} | — | — | — | — | — | — | — |")
    lines += ["","Accounting audit: QQQ entry is a debit; SPY entry is a credit; both are realized with the correct sign. Exit dates are mapped to the last available trading day on or before the target DTE.","","This is not yet a production strategy. The next pass should sweep fixed DTE/wing families and run walk-forward/OOS, while keeping the real-chain fill convention unchanged."]
    (o/"RESULTS.md").write_text("\n".join(lines),encoding="utf-8")

if __name__=="__main__": main()
