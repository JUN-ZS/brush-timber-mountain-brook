#!/usr/bin/env python3
"""Paired historical replay of QQQ LONG PUT and SPY SHORT PUT contracts.

Uses SHA-pinned EOD option-chain bid/ask and underlying closes. Entry fills are
QQQ ask / SPY bid; exits are QQQ bid / SPY ask. Missing quotes stay unpriced.
Daily entry cohorts overlap, so this is not an independent-trials probability
estimate or a capital-normalized portfolio backtest.
"""
from __future__ import annotations
import argparse, bisect, hashlib, json, math, random, statistics
from datetime import date, datetime, timedelta
from pathlib import Path
from statistics import NormalDist
import duckdb
import pandas as pd

DATA_HASHES = {
    "SPY_options.parquet": "a7152991b45b81f090f970e945bf88def8093b8ecb9b250e9891cb6d88041f0a",
    "SPY_underlying.parquet": "847e60a441eb10969d87cd4a6da604257b782d9076168f68d5730b84096c79db",
    "QQQ_options.parquet": "1f831556cd87ec9d7af43d3b47a69a829ffb2fb199cfcef4ff55d289badf8734",
    "QQQ_underlying.parquet": "78c015fd7fa9d493cd798d5ae81b3c2ae6dc3b8176e25e7bb90cd4114b103351",
}
EXIT_HORIZONS = (1, 3, 5, 10, 21)
RATIO_GRID = ((1, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (1, 3))


def as_date(x):
    if isinstance(x, date) and not isinstance(x, datetime):
        return x
    return pd.Timestamp(x).date()


def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_inputs(data_dir):
    found = {}
    for name, expected in DATA_HASHES.items():
        path = data_dir / name
        if not path.is_file():
            raise FileNotFoundError(f"Missing canonical input: {path}")
        actual = sha256_file(path)
        if actual != expected:
            raise ValueError(f"SHA-256 mismatch for {name}: expected {expected}, got {actual}")
        found[name] = {"sha256": actual, "bytes": path.stat().st_size}
    return found


def load_underlying(path):
    df = pd.read_parquet(path)
    df.columns = [str(c).lower() for c in df.columns]
    if not {"date", "close"}.issubset(df.columns):
        raise ValueError(f"{path.name} must have date and close columns")
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None).dt.date
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df = df.dropna(subset=["date", "close"]).sort_values("date").drop_duplicates("date", keep="last")
    return {as_date(r.date): float(r.close) for r in df.itertuples(index=False) if float(r.close) > 0}


def load_candidates(con, options_path, prices, label, start, end, target_dte, target_delta, min_oi):
    spot_df = pd.DataFrame({"trade_date": pd.to_datetime(list(prices.keys())), "spot": list(prices.values())})
    spot_view = "spot_" + label.lower()
    con.register(spot_view, spot_df)
    sql = f"""
      WITH base AS (
        SELECT CAST(o.date AS DATE) AS trade_date,
               CAST(o.expiration AS DATE) AS expiry,
               CAST(o.contract_id AS VARCHAR) AS contract_id,
               CAST(o.strike AS DOUBLE) AS strike,
               CAST(o.bid AS DOUBLE) AS bid,
               CAST(o.ask AS DOUBLE) AS ask,
               CAST(o.delta AS DOUBLE) AS delta,
               CAST(o.implied_volatility AS DOUBLE) AS iv,
               COALESCE(CAST(o.volume AS DOUBLE),0.0) AS volume,
               COALESCE(CAST(o.open_interest AS DOUBLE),0.0) AS oi,
               COALESCE(CAST(o.bid_size AS DOUBLE),0.0) AS bid_size,
               COALESCE(CAST(o.ask_size AS DOUBLE),0.0) AS ask_size,
               CAST(s.spot AS DOUBLE) AS spot,
               date_diff('day',CAST(o.date AS DATE),CAST(o.expiration AS DATE))::INTEGER AS dte,
               (CAST(o.ask AS DOUBLE)-CAST(o.bid AS DOUBLE)) /
                   NULLIF((CAST(o.ask AS DOUBLE)+CAST(o.bid AS DOUBLE))/2.0,0.0) AS spread_pct
        FROM read_parquet(?) o
        JOIN {spot_view} s ON CAST(o.date AS DATE)=CAST(s.trade_date AS DATE)
        WHERE CAST(o.date AS DATE) BETWEEN CAST(? AS DATE) AND CAST(? AS DATE)
          AND UPPER(TRIM(CAST(o.type AS VARCHAR))) IN ('PUT','P')
          AND CAST(o.contract_id AS VARCHAR) IS NOT NULL
          AND CAST(o.expiration AS DATE)>CAST(o.date AS DATE)
          AND date_diff('day',CAST(o.date AS DATE),CAST(o.expiration AS DATE)) BETWEEN ? AND ?
          AND CAST(o.bid AS DOUBLE)>0
          AND CAST(o.ask AS DOUBLE)>=CAST(o.bid AS DOUBLE)
          AND CAST(o.ask AS DOUBLE)>0
          AND COALESCE(CAST(o.bid_size AS DOUBLE),0.0)>0
          AND COALESCE(CAST(o.ask_size AS DOUBLE),0.0)>0
          AND COALESCE(CAST(o.open_interest AS DOUBLE),0.0)>=?
          AND ABS(CAST(o.delta AS DOUBLE)) BETWEEN 0.05 AND 0.60
      ), ranked AS (
        SELECT *, ROW_NUMBER() OVER (
          PARTITION BY trade_date
          ORDER BY ABS(dte-?) ASC, ABS(ABS(delta)-?) ASC,
                   COALESCE(spread_pct,999.0) ASC, volume DESC, oi DESC
        ) AS rn FROM base
      )
      SELECT * EXCLUDE(rn) FROM ranked WHERE rn<=20 ORDER BY trade_date
    """
    df = con.execute(sql, [
        str(options_path), start.isoformat(), end.isoformat(),
        max(7, target_dte-12), target_dte+12, min_oi, target_dte, target_delta
    ]).df()
    con.unregister(spot_view)
    if not df.empty:
        df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
        df["expiry"] = pd.to_datetime(df["expiry"]).dt.date
    return df


def select_pair(qs, ss, mode, target_dte, target_delta, target_otm, long_n, short_n):
    choices = []
    for q in qs:
        for s in ss:
            if abs(int(q["dte"])-int(s["dte"])) > 3:
                continue
            dte = abs(int(q["dte"])-target_dte)+abs(int(s["dte"])-target_dte)+1.5*abs(int(q["dte"])-int(s["dte"]))
            delta = abs(abs(float(q["delta"]))-target_delta)+abs(abs(float(s["delta"]))-target_delta)
            qsp = float(q["spread_pct"]) if pd.notna(q["spread_pct"]) else 999.0
            ssp = float(s["spread_pct"]) if pd.notna(s["spread_pct"]) else 999.0
            spread = .2*(qsp+ssp)
            if mode == "delta":
                score = dte + 10*delta + spread
            elif mode == "otm":
                otm = abs(1-float(q["strike"])/float(q["spot"])-target_otm)+abs(1-float(s["strike"])/float(s["spot"])-target_otm)
                score = dte + 20*otm + 2*delta + spread
            elif mode == "premium":
                debit = float(q["ask"])*long_n
                credit = float(s["bid"])*short_n
                score = dte + 5*delta + 2*abs(math.log(max(debit,1e-9)/max(credit,1e-9))) + spread
            else:
                raise ValueError(mode)
            choices.append((score,q,s))
    if not choices:
        return None
    score,q,s = min(choices,key=lambda z:z[0])
    out = {"entry_date":as_date(q["trade_date"]),"match_mode":mode,"match_score":float(score)}
    for ticker, row in (("qqq",q),("spy",s)):
        for out_name, col in (("contract_id","contract_id"),("expiry","expiry"),("strike","strike"),
                              ("bid","bid"),("ask","ask"),("delta","delta"),("iv","iv"),
                              ("spot","spot"),("dte","dte"),("spread_pct","spread_pct")):
            val = row[col]
            if out_name in ("expiry",):
                val = as_date(val)
            elif out_name in ("contract_id",):
                val = str(val)
            elif pd.isna(val):
                val = None
            else:
                val = float(val) if out_name not in ("dte",) else int(val)
            out[f"{ticker}_{out_name}"] = val
    return out


def build_pairs(qdf,sdf,modes,entry_sessions,target_dte,target_delta,target_otm,long_n,short_n):
    qgroups = {d:g.to_dict("records") for d,g in qdf.groupby("trade_date",sort=False)} if not qdf.empty else {}
    sgroups = {d:g.to_dict("records") for d,g in sdf.groupby("trade_date",sort=False)} if not sdf.empty else {}
    eligible = set(entry_sessions).intersection(qgroups).intersection(sgroups)
    result = {m:[] for m in modes}
    for day in sorted(eligible):
        for mode in modes:
            p = select_pair(qgroups[day],sgroups[day],mode,target_dte,target_delta,target_otm,long_n,short_n)
            if p is not None:
                result[mode].append(p)
    return result


def load_quotes(con,path,ids,temp_name,ticker):
    if not ids:
        return {}
    con.register(temp_name,pd.DataFrame({"contract_id":sorted(ids)}))
    df = con.execute(f"""
      SELECT CAST(o.contract_id AS VARCHAR) AS cid, CAST(o.date AS DATE) AS trade_date,
             CAST(o.bid AS DOUBLE) AS bid, CAST(o.ask AS DOUBLE) AS ask
      FROM read_parquet(?) o JOIN {temp_name} i
        ON CAST(o.contract_id AS VARCHAR)=i.contract_id
    """,[str(path)]).df()
    con.unregister(temp_name)
    result={}
    for r in df.itertuples(index=False):
        result[(ticker,str(r.cid),as_date(r.trade_date))] = (
            float(r.bid) if pd.notna(r.bid) else None,
            float(r.ask) if pd.notna(r.ask) else None,
        )
    return result


_PRICE_DATE_CACHE = {}

def latest_date_at_or_before(prices,target):
    key=id(prices)
    cached=_PRICE_DATE_CACHE.get(key)
    if cached is None or cached[0] is not prices:
        dates=sorted(prices)
        _PRICE_DATE_CACHE[key]=(prices,dates)
    else:
        dates=cached[1]
    if not dates or target>dates[-1]:
        return None
    i=bisect.bisect_right(dates,target)-1
    return dates[i] if i>=0 else None


def exit_value(ticker,pair,target,quotes,prices,is_long):
    prefix=ticker.lower()
    expiry=pair[f"{prefix}_expiry"]
    strike=float(pair[f"{prefix}_strike"])
    if target>=expiry:
        settle=latest_date_at_or_before(prices,expiry)
        if settle is None:
            return None,None,"NO_EXPIRY_UNDERLYING"
        return max(strike-prices[settle],0.0),settle,"EXPIRY_INTRINSIC"
    q=quotes.get((ticker,str(pair[f"{prefix}_contract_id"]),target))
    if q is None:
        return None,None,"MISSING_EXIT_QUOTE"
    bid,ask=q
    if bid is None or ask is None or bid<0 or ask<bid or ask<=0:
        return None,None,"INVALID_EXIT_QUOTE"
    return (bid if is_long else ask),target,("EXIT_BID" if is_long else "EXIT_ASK")


def outcome(pair,horizon,ratio,sessions,index,quotes,qprices,sprices,commission):
    entry=pair["entry_date"]
    long_n,short_n=ratio
    if horizon=="expiry":
        qsettle=latest_date_at_or_before(qprices,pair["qqq_expiry"])
        ssettle=latest_date_at_or_before(sprices,pair["spy_expiry"])
        target=max(qsettle,ssettle) if qsettle and ssettle else None
    else:
        i=index.get(entry)
        target=sessions[i+int(horizon)] if i is not None and i+int(horizon)<len(sessions) else None
    row={
        "match_mode":pair["match_mode"],"ratio":f"{long_n}:{short_n}",
        "horizon":"expiry" if horizon=="expiry" else f"{horizon}d",
        "entry_date":entry.isoformat(),"exit_date":target.isoformat() if target else None,
        "qqq_expiry":pair["qqq_expiry"].isoformat(),"spy_expiry":pair["spy_expiry"].isoformat(),
        "qqq_contract_id":pair["qqq_contract_id"],"spy_contract_id":pair["spy_contract_id"],
        "qqq_dte":pair["qqq_dte"],"spy_dte":pair["spy_dte"],
        "qqq_strike":pair["qqq_strike"],"spy_strike":pair["spy_strike"],
        "qqq_spot":pair["qqq_spot"],"spy_spot":pair["spy_spot"],
        "qqq_delta":pair["qqq_delta"],"spy_delta":pair["spy_delta"],
        "qqq_iv":pair["qqq_iv"],"spy_iv":pair["spy_iv"],
        "gross_qqq_premium_usd":pair["qqq_ask"]*long_n*100,
        "gross_spy_credit_usd":pair["spy_bid"]*short_n*100,
        "spy_assignment_purchase_usd":pair["spy_strike"]*short_n*100,
        "both_underlyings_zero_net_pnl_usd":(pair["qqq_strike"]-pair["qqq_ask"])*long_n*100+(pair["spy_bid"]-pair["spy_strike"])*short_n*100-2*commission*(long_n+short_n),
        "entry_year":entry.year,"market_regime":pair.get("market_regime","UNKNOWN"),
        "pnl_qqq_long_usd":None,"pnl_spy_short_usd":None,"pnl_net_usd":None,"fees_usd":None,
        "qqq_exit_method":None,"spy_exit_method":None,
        "status":"OUTSIDE_DATA" if target is None else None,
    }
    if target is None:
        return row
    qexit,qd,qm=exit_value("QQQ",pair,target,quotes,qprices,True)
    sexit,sd,sm=exit_value("SPY",pair,target,quotes,sprices,False)
    if qexit is None:
        row["status"]="QQQ_"+qm
        return row
    if sexit is None:
        row["status"]="SPY_"+sm
        return row
    qgross=(qexit-pair["qqq_ask"])*long_n*100
    sgross=(pair["spy_bid"]-sexit)*short_n*100
    fees=2*commission*(long_n+short_n)
    row.update({
        "exit_date":max(qd or target,sd or target).isoformat(),
        "pnl_qqq_long_usd":qgross-2*commission*long_n,
        "pnl_spy_short_usd":sgross-2*commission*short_n,
        "pnl_net_usd":qgross+sgross-fees,"fees_usd":fees,
        "qqq_exit_method":qm,"spy_exit_method":sm,"status":"OK",
    })
    return row


def wilson_interval(wins,n,z=1.959963984540054):
    if n<=0:
        return None,None
    p=wins/n
    den=1+z*z/n
    centre=(p+z*z/(2*n))/den
    half=z*math.sqrt((p*(1-p)+z*z/(4*n))/n)/den
    return max(0,centre-half),min(1,centre+half)


def block_bootstrap_interval(flags,block_len=20,reps=500,seed=20261022):
    if len(flags)<max(30,block_len*2):
        return None,None
    rng=random.Random(seed)
    n=len(flags)
    vals=[]
    for _ in range(reps):
        sample=[]
        while len(sample)<n:
            start=rng.randrange(n)
            sample.extend(flags[(start+j)%n] for j in range(block_len))
        vals.append(sum(sample[:n])/n)
    vals.sort()
    return vals[int(.025*(len(vals)-1))],vals[int(.975*(len(vals)-1))]


def summarize(rows):
    priced=sorted([r for r in rows if r.get("status")=="OK" and r.get("pnl_net_usd") is not None],key=lambda r:r["entry_date"])
    pnl=[float(r["pnl_net_usd"]) for r in priced]
    wins=sum(x>0 for x in pnl)
    low,high=wilson_interval(wins,len(pnl))
    blo,bhi=block_bootstrap_interval([x>0 for x in pnl])
    spyloss=[r for r in priced if float(r["pnl_spy_short_usd"])<0]
    covered=sum(float(r["pnl_qqq_long_usd"])>=-float(r["pnl_spy_short_usd"]) for r in spyloss)
    bothloss=sum(float(r["pnl_qqq_long_usd"])<0 and float(r["pnl_spy_short_usd"])<0 for r in priced)
    s=sorted(pnl)
    p05=s[max(0,math.ceil(.05*len(s))-1)] if s else None
    tail=[x for x in pnl if p05 is not None and x<=p05]
    loss_sum=sum(-x for x in pnl if x<0)
    win_sum=sum(x for x in pnl if x>0)
    zeros=[float(r["both_underlyings_zero_net_pnl_usd"]) for r in rows]
    return {
        "entries_selected":len(rows),"priced_outcomes":len(priced),
        "exit_quote_coverage_pct":100*len(priced)/len(rows) if rows else None,
        "wins":wins,"losses":sum(x<0 for x in pnl),"flats":len(pnl)-wins-sum(x<0 for x in pnl),
        "win_rate_net_pct":100*wins/len(pnl) if pnl else None,
        "win_rate_wilson95_low_pct":100*low if low is not None else None,
        "win_rate_wilson95_high_pct":100*high if high is not None else None,
        "win_rate_block_bootstrap95_low_pct":100*blo if blo is not None else None,
        "win_rate_block_bootstrap95_high_pct":100*bhi if bhi is not None else None,
        "mean_net_pnl_usd":statistics.fmean(pnl) if pnl else None,
        "median_net_pnl_usd":statistics.median(pnl) if pnl else None,
        "p05_net_pnl_usd":p05,"es05_net_pnl_usd":statistics.fmean(tail) if tail else None,
        "worst_net_pnl_usd":min(pnl) if pnl else None,
        "profit_factor":loss_sum and win_sum/loss_sum or (None if win_sum==0 else "INF"),
        "mean_qqq_long_pnl_usd":statistics.fmean(float(r["pnl_qqq_long_usd"]) for r in priced) if priced else None,
        "mean_spy_short_pnl_usd":statistics.fmean(float(r["pnl_spy_short_usd"]) for r in priced) if priced else None,
        "spy_short_losing_trade_pct":100*len(spyloss)/len(priced) if priced else None,
        "qqq_long_covers_spy_loss_pct":100*covered/len(spyloss) if spyloss else None,
        "both_legs_lose_pct":100*bothloss/len(priced) if priced else None,
        "mean_both_underlyings_zero_net_pnl_usd":statistics.fmean(zeros) if zeros else None,
        "worst_both_underlyings_zero_net_pnl_usd":min(zeros) if zeros else None,
    }


def normalize_iv(v):
    if v is None or pd.isna(v):
        return None
    iv=float(v)
    if iv>3: iv/=100
    return iv if .01<=iv<=5 else None


def bs_put(spot,strike,years,iv):
    if years<=0 or spot<=0 or strike<=0 or iv<=0:
        return max(strike-spot,0)
    vol=iv*math.sqrt(years)
    d1=(math.log(spot/strike)+.5*iv*iv*years)/vol
    d2=d1-vol
    n=NormalDist()
    return max(0,strike*n.cdf(-d2)-spot*n.cdf(-d1))


def same_move_scenarios(pairs_by_mode,long_n,short_n,commission,hold_days=10):
    out=[]
    for mode,pairs in pairs_by_mode.items():
        for p in pairs:
            for move in (-.20,-.15,-.10,-.05,0,.05,.10):
                for mult in (1.0,1.5):
                    total=0.0
                    valid=True
                    for ticker,count,is_long in (("QQQ",long_n,True),("SPY",short_n,False)):
                        pref=ticker.lower()
                        iv=normalize_iv(p[f"{pref}_iv"])
                        if iv is None:
                            valid=False
                            break
                        spot=float(p[f"{pref}_spot"]); strike=float(p[f"{pref}_strike"])
                        bid=float(p[f"{pref}_bid"]); ask=float(p[f"{pref}_ask"])
                        entry=p["entry_date"]; expiry=p[f"{pref}_expiry"]
                        t0=max(0,(expiry-entry).days)/365
                        t1=max(0,(expiry-(entry+timedelta(days=hold_days))).days)/365
                        base=bs_put(spot,strike,t0,iv)
                        shocked=bs_put(spot*(1+move),strike,t1,iv*mult)
                        exit_mid=(bid+ask)/2+shocked-base
                        half=max(0,(ask-bid)/2)
                        if is_long:
                            total+=(max(0,exit_mid-half)-ask)*count*100-2*commission*count
                        else:
                            total+=(bid-max(0,exit_mid+half))*count*100-2*commission*count
                    if valid:
                        out.append({"match_mode":mode,"ratio":f"{long_n}:{short_n}",
                            "hold_calendar_days":hold_days,"same_pct_move_qqq_and_spy":move,
                            "exit_iv_multiplier_vs_entry":mult,"net_pnl_usd":total,
                            "classification":"HYPOTHETICAL_BS_NOT_PROBABILITY"})
    return out


def add_regimes(pairs_by_mode,spy_prices):
    dates=sorted(spy_prices)
    df=pd.DataFrame({"date":pd.to_datetime(dates),"close":[spy_prices[d] for d in dates]})
    df["ret"]=df.close.pct_change()
    df["rv20"]=df.ret.rolling(20,min_periods=20).std()*math.sqrt(252)
    df["trend63"]=df.close/df.close.shift(63)-1
    regimes={}
    for r in df.itertuples(index=False):
        d=as_date(r.date)
        if pd.isna(r.trend63) or pd.isna(r.rv20):
            regimes[d]="WARMUP"
        else:
            trend="UP" if r.trend63>=0 else "DOWN"
            vol="LOWVOL" if r.rv20<.15 else ("MIDVOL" if r.rv20<.25 else "HIGHVOL")
            regimes[d]=f"{trend}_{vol}"
    for pairs in pairs_by_mode.values():
        for p in pairs:
            p["market_regime"]=regimes.get(p["entry_date"],"UNKNOWN")


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-dir",type=Path,default=Path("data"))
    ap.add_argument("--out-dir",type=Path,required=True)
    ap.add_argument("--start",default="2011-01-01")
    ap.add_argument("--end",default="2025-12-31")
    ap.add_argument("--target-dte",type=int,default=30)
    ap.add_argument("--target-delta",type=float,default=.25)
    ap.add_argument("--target-otm",type=float,default=.05)
    ap.add_argument("--long-contracts",type=int,default=4)
    ap.add_argument("--short-contracts",type=int,default=5)
    ap.add_argument("--commission-per-side",type=float,default=.65)
    ap.add_argument("--min-open-interest",type=int,default=10)
    ap.add_argument("--match-mode",choices=("all","delta","otm","premium"),default="all")
    a=ap.parse_args()
    if a.target_dte<14 or a.target_dte>90 or not .05<=a.target_delta<=.6 or not 0<=a.target_otm<=.3:
        raise ValueError("Invalid DTE/delta/OTM setting")
    if a.long_contracts<1 or a.short_contracts<1 or a.commission_per_side<0 or a.min_open_interest<0:
        raise ValueError("Contract counts must be positive; commission and OI must be non-negative")
    start,end=date.fromisoformat(a.start),date.fromisoformat(a.end)
    if start>end: raise ValueError("--start must be <= --end")
    a.out_dir.mkdir(parents=True,exist_ok=True)
    hashes=verify_inputs(a.data_dir)
    qprices=load_underlying(a.data_dir/"QQQ_underlying.parquet")
    sprices=load_underlying(a.data_dir/"SPY_underlying.parquet")
    sessions=sorted(set(qprices).intersection(sprices))
    in_range=[d for d in sessions if start<=d<=end]
    if not in_range: raise RuntimeError("No common underlying sessions in requested range")
    index={d:i for i,d in enumerate(sessions)}
    con=duckdb.connect()
    qdf=load_candidates(con,a.data_dir/"QQQ_options.parquet",qprices,"QQQ",start,end,a.target_dte,a.target_delta,a.min_open_interest)
    sdf=load_candidates(con,a.data_dir/"SPY_options.parquet",sprices,"SPY",start,end,a.target_dte,a.target_delta,a.min_open_interest)
    modes=["delta","otm","premium"] if a.match_mode=="all" else [a.match_mode]
    pairs=build_pairs(qdf,sdf,modes,in_range,a.target_dte,a.target_delta,a.target_otm,a.long_contracts,a.short_contracts)
    if not any(pairs.values()): raise RuntimeError("No paired entries passed data and matching filters")
    add_regimes(pairs,sprices)
    qids={p["qqq_contract_id"] for group in pairs.values() for p in group}
    sids={p["spy_contract_id"] for group in pairs.values() for p in group}
    quotes=load_quotes(con,a.data_dir/"QQQ_options.parquet",qids,"selected_qqq","QQQ")
    quotes.update(load_quotes(con,a.data_dir/"SPY_options.parquet",sids,"selected_spy","SPY"))
    con.close()

    requested=(a.long_contracts,a.short_contracts)
    ratios=[requested]+[r for r in RATIO_GRID if r!=requested]
    rows=[]
    for mode,group in pairs.items():
        for p in group:
            for ratio in ratios:
                for h in [str(x) for x in EXIT_HORIZONS]+["expiry"]:
                    rows.append(outcome(p,h,ratio,sessions,index,quotes,qprices,sprices,a.commission_per_side))
    detail=pd.DataFrame(rows)
    metrics=[]
    for key,g in detail.groupby(["match_mode","ratio","horizon"],sort=False):
        s=summarize(g.to_dict("records")); s.update({"match_mode":key[0],"ratio":key[1],"horizon":key[2]}); metrics.append(s)
    priced=detail[(detail.status=="OK") & detail.pnl_net_usd.notna()].copy()
    annual=[]; regimes=[]
    if not priced.empty:
        priced["entry_year"]=priced.entry_date.str.slice(0,4)
        for key,g in priced.groupby(["match_mode","ratio","horizon","entry_year"],sort=False):
            s=summarize(g.to_dict("records")); s.update(dict(zip(["match_mode","ratio","horizon","entry_year"],key))); annual.append(s)
        for key,g in priced.groupby(["match_mode","ratio","horizon","market_regime"],sort=False):
            s=summarize(g.to_dict("records")); s.update(dict(zip(["match_mode","ratio","horizon","market_regime"],key))); regimes.append(s)
    scenarios=same_move_scenarios(pairs,a.long_contracts,a.short_contracts,a.commission_per_side)
    scen_summary=[]
    if scenarios:
        sdf2=pd.DataFrame(scenarios)
        for key,g in sdf2.groupby(["match_mode","same_pct_move_qqq_and_spy","exit_iv_multiplier_vs_entry"],sort=False):
            vals=sorted(float(x) for x in g.net_pnl_usd)
            scen_summary.append({"match_mode":key[0],"ratio":f"{a.long_contracts}:{a.short_contracts}",
                "same_pct_move_qqq_and_spy":key[1],"exit_iv_multiplier_vs_entry":key[2],"n":len(vals),
                "positive_pnl_pct":100*sum(x>0 for x in vals)/len(vals) if vals else None,
                "median_net_pnl_usd":statistics.median(vals) if vals else None,
                "p05_net_pnl_usd":vals[max(0,math.ceil(.05*len(vals))-1)] if vals else None,
                "worst_net_pnl_usd":min(vals) if vals else None,"classification":"HYPOTHETICAL_BS_NOT_PROBABILITY"})
    pd.DataFrame(metrics).to_csv(a.out_dir/"metrics_by_horizon.csv",index=False)
    pd.DataFrame(annual).to_csv(a.out_dir/"metrics_by_year.csv",index=False)
    pd.DataFrame(regimes).to_csv(a.out_dir/"metrics_by_regime.csv",index=False)
    detail.to_csv(a.out_dir/"trade_level_outcomes.csv",index=False)
    pd.DataFrame(scenarios).to_csv(a.out_dir/"same_move_scenarios.csv",index=False)
    pd.DataFrame(scen_summary).to_csv(a.out_dir/"same_move_summary.csv",index=False)
    manifest={
        "version":"qqq-long-put-spy-short-put-ratio.v1","source_release":"lambdaclass/options_portfolio_backtester data-v1",
        "source_hashes":hashes,"requested_start":start.isoformat(),"requested_end":end.isoformat(),
        "common_underlying_start":min(sessions).isoformat(),"common_underlying_end":max(sessions).isoformat(),
        "common_sessions_in_requested_range":len(in_range),"paired_entries_by_mode":{m:len(v) for m,v in pairs.items()},
        "requested_ratio":f"{a.long_contracts}:{a.short_contracts}","ratios_tested":[f"{x}:{y}" for x,y in ratios],
        "match_modes":modes,"target_dte_calendar_days":a.target_dte,"target_abs_delta":a.target_delta,
        "target_otm_distance":a.target_otm,"min_open_interest":a.min_open_interest,
        "commission_per_contract_per_side_usd":a.commission_per_side,
        "filters":["PUT only, valid nonzero bid/ask, positive displayed bid/ask size","minimum open interest, abs(delta) 0.05-0.60",
          "DTE target +/- 12 calendar days","QQQ and SPY expiration dates within 3 calendar days",
          "no exit-quote imputation; missing outcomes explicitly marked"],
        "accounting":{"multiplier":100,"QQQ":"buy at ask; exit at bid","SPY":"sell at bid; exit at ask",
          "fees":"commission charged entry and exit/expiry proxy","expiry":"intrinsic at last underlying close on/before expiration; early assignment not modeled",
          "portfolio":"no capital denominator or margin/liquidation replay","dependence":"daily cohorts overlap; not independent trials"},
        "same_move_scenario":{"same percentage move to both underlyings":[-.2,-.15,-.1,-.05,0,.05,.1],
          "exit_iv_multipliers":[1,1.5],"hold_calendar_days":10,
          "classification":"hypothetical BS repricing, not historical P&L or win probability"},
        "outputs":["metrics_by_horizon.csv","metrics_by_year.csv","metrics_by_regime.csv",
          "trade_level_outcomes.csv","same_move_scenarios.csv","same_move_summary.csv","manifest.json","summary.json"]
    }
    (a.out_dir/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    summary={"manifest":manifest,"selected_ratio_metrics":[r for r in metrics if r["ratio"]==f"{a.long_contracts}:{a.short_contracts}"],
       "delta_matched_ratio_sensitivity_5d":[r for r in metrics if r["match_mode"]=="delta" and r["horizon"]=="5d"],
       "selected_ratio_year_metrics":[r for r in annual if r["ratio"]==f"{a.long_contracts}:{a.short_contracts}"],
       "selected_ratio_regime_metrics":[r for r in regimes if r["ratio"]==f"{a.long_contracts}:{a.short_contracts}"],
       "same_move_summary":scen_summary}
    (a.out_dir/"summary.json").write_text(json.dumps(summary,indent=2,allow_nan=False),encoding="utf-8")
    print("PAIRED_PUT_RESEARCH_RESULT_BEGIN")
    print(json.dumps(summary,ensure_ascii=False,allow_nan=False))
    print("PAIRED_PUT_RESEARCH_RESULT_END")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
