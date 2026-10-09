#!/usr/bin/env python3
"""SHA-pinned source/quote-quality probe of public QQQ EOD option chains; not a backtest."""
from __future__ import annotations
import hashlib, json, tempfile, urllib.request
from datetime import date, datetime
from pathlib import Path

BASE = "https://raw.githubusercontent.com/anahatsingh-ui/options-dataset-hist/main/qqq"
FILES = {
    "options_2020.parquet": {"url": BASE+"/options_2020.parquet", "size": 59412637,
        "sha": "9d7abe1144c55e0091d28eca61deec4ac72393a5", "dates": ["2020-03-16"]},
    "options_2024.parquet": {"url": BASE+"/options_2024.parquet", "size": 82434832,
        "sha": "40c1c2fd986da9b5bcf363cd44c9d5ac3eecc8c3", "dates": ["2024-08-05"]},
}
UNDERLYING = {"url": BASE+"/underlying_prices.parquet", "size": 332454,
    "sha": "f3a892bc4c88c692900b5c0071322c6db408996a"}
COLUMNS = ["contract_id","symbol","expiration","strike","type","bid","ask","bid_size","ask_size",
           "volume","open_interest","date","implied_volatility","delta"]

def git_blob_sha(path, expected_size):
    h=hashlib.sha1(); h.update(f"blob {expected_size}\0".encode("ascii"))
    with open(path,"rb") as handle:
        for block in iter(lambda: handle.read(1024*1024),b""): h.update(block)
    return h.hexdigest()

def download(spec, name, folder):
    path=Path(folder)/name
    if path.exists() and path.stat().st_size==spec["size"] and git_blob_sha(path,spec["size"])==spec["sha"]:
        return path,{"status":"CACHED_HASH_VERIFIED","bytes":spec["size"],"git_blob_sha":spec["sha"]}
    path.unlink(missing_ok=True)
    req=urllib.request.Request(spec["url"],headers={"User-Agent":"qqq-hybrid-eod-audit/1.0"})
    digest=hashlib.sha1(); digest.update(f"blob {spec['size']}\0".encode("ascii")); total=0
    with urllib.request.urlopen(req,timeout=90) as resp, open(path,"wb") as out:
        while True:
            block=resp.read(1024*1024)
            if not block: break
            total+=len(block); out.write(block); digest.update(block)
    actual=digest.hexdigest()
    if total!=spec["size"] or actual!=spec["sha"]:
        path.unlink(missing_ok=True)
        raise ValueError(f"{name} size/SHA mismatch: {total}/{spec['size']} bytes, {actual}/{spec['sha']}")
    return path,{"status":"DOWNLOADED_HASH_VERIFIED","bytes":total,"git_blob_sha":actual}

def as_day(v):
    if v is None: return ""
    return v.isoformat()[:10] if hasattr(v,"isoformat") else str(v)[:10]

def day_literals(pa, dtype, strings):
    if pa.types.is_date(dtype): return [date.fromisoformat(s) for s in strings]
    if pa.types.is_timestamp(dtype): return [datetime.fromisoformat(s+"T00:00:00") for s in strings]
    return strings

def numeric(v):
    try:
        n=float(v)
        return n if n==n and abs(n)!=float("inf") else None
    except (TypeError,ValueError): return None

def read_dates(path, dates, pa, ds, columns=None):
    data=ds.dataset(str(path),format="parquet"); schema=data.schema
    if "date" not in schema.names: raise ValueError("Parquet missing date column")
    pred=ds.field("date").isin(day_literals(pa,schema.field("date").type,dates))
    if "symbol" in schema.names: pred=pred & (ds.field("symbol")=="QQQ")
    cols=[c for c in (columns or schema.names) if c in schema.names]
    return data.to_table(columns=cols,filter=pred).to_pylist()

def inspect_day(day, rows):
    calls=[r for r in rows if str(r.get("type","")).lower() in ("c","call")]
    valid=[]; candidates=[]
    for r in rows:
        bid,ask=numeric(r.get("bid")),numeric(r.get("ask"))
        if bid is not None and ask is not None and bid>0 and ask>0 and bid<=ask: valid.append(r)
    for r in calls:
        try: dte=(date.fromisoformat(as_day(r.get("expiration")))-date.fromisoformat(day)).days
        except ValueError: continue
        bid,ask,delta=numeric(r.get("bid")),numeric(r.get("ask")),numeric(r.get("delta"))
        if (30<=dte<=60 and delta is not None and .03<=abs(delta)<=.10 and
            bid is not None and ask is not None and bid>0 and ask>0 and bid<=ask):
            mid=(bid+ask)/2
            candidates.append({"contract_id":r.get("contract_id"),"expiration":as_day(r.get("expiration")),
                "dte_calendar":dte,"strike":r.get("strike"),"bid":bid,"ask":ask,"delta":delta,
                "spread":round(ask-bid,4),"spread_pct_of_mid":round((ask-bid)/mid*100,2) if mid else None,
                "iv":r.get("implied_volatility"),"volume":r.get("volume"),"open_interest":r.get("open_interest")})
    candidates.sort(key=lambda r:(abs(abs(r["delta"])-.06),abs(r["dte_calendar"]-45),r["spread"]))
    return {"date":day,"status":"ROWS_FOUND" if rows else "NO_ROWS_RETURNED","option_rows":len(rows),
        "call_rows":len(calls),"put_rows":len(rows)-len(calls),
        "positive_non_crossed_two_sided_rows":len(valid),
        "valid_two_sided_quote_pct":round(100*len(valid)/len(rows),2) if rows else None,
        "call_candidates_30_60_dte_abs_delta_0p03_0p10":len(candidates),"candidate_samples":candidates[:5]}

def main():
    report={"source":"anahatsingh-ui/options-dataset-hist","source_class":"PUBLIC_EOD_CHAIN_PRESERVATION_MIRROR",
        "quote_convention":"README says 4:00 PM US Eastern; not a 15:45 or intraday fill",
        "role":"QQQ layer quote-quality cross-check only; does not cover VXX",
        "trade_replay_approved":False,"file_integrity":{},"results":[],"overall":"INCONCLUSIVE"}
    try:
        import pyarrow as pa
        import pyarrow.dataset as ds
        with tempfile.TemporaryDirectory(prefix="qqq-eod-audit-") as temp:
            local={}
            for name,spec in FILES.items():
                local[name],report["file_integrity"][name]=download(spec,name,temp)
            underlying,report["file_integrity"]["underlying_prices.parquet"]=download(UNDERLYING,"underlying_prices.parquet",temp)
            dates=sorted({d for spec in FILES.values() for d in spec["dates"]})
            for name,spec in FILES.items():
                rows=read_dates(local[name],spec["dates"],pa,ds,COLUMNS)
                by={d:[] for d in spec["dates"]}
                for row in rows:
                    d=as_day(row.get("date"))
                    if d in by: by[d].append(row)
                report["results"].extend(inspect_day(d,by[d]) for d in spec["dates"])
            spots=read_dates(underlying,dates,pa,ds)
            smap={as_day(r.get("date")):r for r in spots}
            report["underlying_spots"]={d:({"close":numeric(smap[d].get("close")),
                "adjusted_close":numeric(smap[d].get("adjusted_close")),"volume":smap[d].get("volume"),
                "split_coefficient":smap[d].get("split_coefficient")} if d in smap else None) for d in dates}
        integrity=all(x.get("status") in ("DOWNLOADED_HASH_VERIFIED","CACHED_HASH_VERIFIED") for x in report["file_integrity"].values())
        hits=sum(x["status"]=="ROWS_FOUND" for x in report["results"])
        report["integrity_ok"]=integrity
        report["overall"]=("SAMPLE_DATES_HAVE_QQQ_CHAIN_ROWS" if integrity and hits==len(report["results"]) else
            "PARTIAL_QQQ_CHAIN_COVERAGE" if integrity and hits>0 else
            "NO_QQQ_ROWS_ON_TEST_DATES" if integrity else "INCONCLUSIVE_INTEGRITY_OR_READ")
    except Exception as exc:
        report["overall"]="INCONCLUSIVE_DOWNLOAD_OR_PARQUET_READ"
        report["error"]=type(exc).__name__+": "+str(exc)[:400]
    print("QQQ_PUBLIC_EOD_AUDIT_BEGIN")
    print(json.dumps(report,indent=2,sort_keys=True))
    print("QQQ_PUBLIC_EOD_AUDIT_END")
    return 0

if __name__=="__main__": raise SystemExit(main())
