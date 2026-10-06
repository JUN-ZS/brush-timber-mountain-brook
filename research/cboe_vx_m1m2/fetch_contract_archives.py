#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,datetime as dt,io,json,re,time,urllib.error,urllib.request
from pathlib import Path

HOSTS=[
 "https://cdn.cboe.com/resources/futures/archive/volume-and-price/{file}",
 "https://www.cboe.com/Publish/ScheduledTask/MktData/datahouse/{file}",
]
LETTERS={"F":1,"G":2,"H":3,"J":4,"K":5,"M":6,"N":7,"Q":8,"U":9,"V":10,"X":11,"Z":12}

def norm(s):
    return re.sub(r"[^a-z0-9]+","_",str(s or "").strip().lower()).strip("_")

def find_field(fields,*names):
    for f in fields:
        n=norm(f)
        if n in {norm(x) for x in names}:
            return f
    return None

def parse_date(s):
    s=str(s or "").strip()
    for fmt in ("%m/%d/%Y","%Y-%m-%d","%m/%d/%y"):
        try:return dt.datetime.strptime(s,fmt).date()
        except ValueError:pass
    return None

def parse_float(s):
    s=str(s or "").strip().replace(",","")
    try:return float(s)
    except ValueError:return None

def contract_meta(code):
    m=re.fullmatch(r"([FGHJKMNQUVXZ])(\d{2})",code)
    if not m: raise ValueError(f"bad contract code: {code}")
    return int("20"+m.group(2)), LETTERS[m.group(1)]

def url_for(file):
    return [h.format(file=file) for h in HOSTS]

def fetch(file):
    last=None
    for url in url_for(file):
        for attempt in range(3):
            try:
                req=urllib.request.Request(url,headers={"User-Agent":"JUN-ZS VX historical research"})
                with urllib.request.urlopen(req,timeout=45) as r:
                    body=r.read().decode("utf-8-sig","replace")
                if body and not body.lstrip().startswith("<"):
                    return body,url
            except Exception as e:
                last=repr(e)
                time.sleep(1.0*(attempt+1))
    raise RuntimeError(f"download failed {file}: {last}")

def read_contract(code):
    file=f"CFE_{code}_VX.csv"
    body,url=fetch(file)
    rows=list(csv.DictReader(io.StringIO(body)))
    if not rows: return [],{"code":code,"url":url,"rows":0}
    fields=list(rows[0].keys())
    date_f=find_field(fields,"Trade Date","Date")
    settle_f=find_field(fields,"Settle","Settlement Price","Settlement")
    if not date_f or not settle_f:
        raise ValueError(f"{file}: fields={fields}")
    out=[]
    for r in rows:
        d=parse_date(r.get(date_f)); p=parse_float(r.get(settle_f))
        if d is None or p is None: continue
        out.append((d,p))
    return out,{"code":code,"url":url,"rows":len(out)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--part-index",type=int,required=True)
    ap.add_argument("--parts",type=int,default=10)
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    all_codes=[["F18","X18","U19","N20","K21","H22","F23","X23","U24","N25","K26"],["G18","Z18","V19","Q20","M21","J22","G23","Z23","V24","Q25","M26"],["H18","F19","X19","U20","N21","K22","H23","F24","X24","U25","N26"],["J18","G19","Z19","V20","Q21","M22","J23","G24","Z24","V25","Q26"],["K18","H19","F20","X20","U21","N22","K23","H24","F25","X25","U26"],["M18","J19","G20","Z20","V21","Q22","M23","J24","G25","Z25"],["N18","K19","H20","F21","X21","U22","N23","K24","H25","F26"],["Q18","M19","J20","G21","Z21","V22","Q23","M24","J25","G26"],["U18","N19","K20","H21","F22","X22","U23","N24","K25","H26"],["V18","Q19","M20","J21","G22","Z22","V23","Q24","M25","J26"]]
    codes=all_codes[args.part_index]
    by_date={}
    meta=[]
    for code in codes:
        rows,m=read_contract(code); meta.append(m)
        year,month=contract_meta(code)
        for d,p in rows:
            by_date.setdefault(d,[]).append({"code":code,"year":year,"month":month,"price":p})
    out_rows=[]
    for d,arr in by_date.items():
        arr=sorted(arr,key=lambda x:(x["year"],x["month"]))
        if len(arr)<2: continue
        a,b=arr[0],arr[1]
        out_rows.append({
            "trade_date":d.isoformat(),
            "m1_code":a["code"],"m1_settlement":a["price"],
            "m2_code":b["code"],"m2_settlement":b["price"],
            "term_slope":(b["price"]-a["price"])/a["price"] if a["price"] else "",
            "source":"CBOE_CONTRACT_ARCHIVE_DAILY_SETTLEMENT",
            "source_m1_url":next(x["url"] for x in meta if x["code"]==a["code"]),
            "source_m2_url":next(x["url"] for x in meta if x["code"]==b["code"]),
        })
    out_rows.sort(key=lambda x:x["trade_date"])
    p=Path(args.out); p.parent.mkdir(parents=True,exist_ok=True)
    fields=["trade_date","m1_code","m1_settlement","m2_code","m2_settlement","term_slope","source","source_m1_url","source_m2_url"]
    with p.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(out_rows)
    (p.parent/f"metadata_{args.part_index}.json").write_text(json.dumps({"part":args.part_index,"contracts":meta,"rows":len(out_rows)},indent=2),encoding="utf-8")
    print(json.dumps({"part":args.part_index,"contracts":[m["code"] for m in meta],"rows":len(out_rows)},indent=2))

if __name__=="__main__":
    main()
