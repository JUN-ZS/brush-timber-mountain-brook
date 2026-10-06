#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,datetime as dt,io,json,re,time,urllib.error,urllib.request
from pathlib import Path

HOSTS=[
 "https://cdn.cboe.com/resources/futures/archive/volume-and-price/{file}",
 "https://www.cboe.com/Publish/ScheduledTask/MktData/datahouse/{file}",
]
LETTERS={"F":1,"G":2,"H":3,"J":4,"K":5,"M":6,"N":7,"Q":8,"U":9,"V":10,"X":11,"Z":12}
CONTRACTS=[]
for yy in range(18,27):
    year=2000+yy
    for letter,month in LETTERS.items():
        if year==2026 and month>9:
            continue
        code=f"{letter}{yy:02d}"
        CONTRACTS.append(code)

def norm(s):
    return re.sub(r"[^a-z0-9]+","_",str(s or "").strip().lower()).strip("_")

def find_field(fields,*names):
    targets={norm(x) for x in names}
    for f in fields:
        if norm(f) in targets:
            return f
    return None

def parse_date(s):
    s=str(s or "").strip()
    for fmt in ("%m/%d/%Y","%Y-%m-%d","%m/%d/%y"):
        try:return dt.datetime.strptime(s,fmt).date()
        except ValueError: pass
    return None

def parse_float(s):
    s=str(s or "").strip().replace(",","")
    try:return float(s)
    except ValueError:return None

def fetch(file):
    last=None
    for url in [h.format(file=file) for h in HOSTS]:
        for attempt in range(3):
            try:
                req=urllib.request.Request(url,headers={"User-Agent":"JUN-ZS VX historical research","Accept":"text/csv,*/*"})
                with urllib.request.urlopen(req,timeout=45) as r:
                    body=r.read().decode("utf-8-sig","replace")
                if body and not body.lstrip().startswith("<"):
                    return body,url
            except Exception as e:
                last=repr(e); time.sleep(1.0*(attempt+1))
    raise RuntimeError(f"download failed {file}: {last}")

def read_contract(code):
    body,url=fetch(f"CFE_{code}_VX.csv")
    rows=list(csv.DictReader(io.StringIO(body)))
    if not rows:
        return [],{"code":code,"url":url,"rows":0}
    fields=list(rows[0].keys())
    date_f=find_field(fields,"Trade Date","Date")
    settle_f=find_field(fields,"Settle","Settlement Price","Settlement")
    if not date_f or not settle_f:
        raise ValueError(f"CFE_{code}_VX.csv: fields={fields}")
    out=[]
    for r in rows:
        d=parse_date(r.get(date_f)); p=parse_float(r.get(settle_f))
        if d is not None and p is not None:
            out.append((d.isoformat(),code,p))
    return out,{"code":code,"url":url,"rows":len(out)}

def part_codes(parts,idx):
    return [c for i,c in enumerate(CONTRACTS) if i % parts == idx]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--part-index",type=int,required=True)
    ap.add_argument("--parts",type=int,default=10)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    codes=part_codes(a.parts,a.part_index)
    p=Path(a.out); p.parent.mkdir(parents=True,exist_ok=True)
    fields=["trade_date","contract_code","settlement","source_url"]
    rows=[]; meta=[]
    for code in codes:
        data,m=read_contract(code); meta.append(m)
        rows += [{"trade_date":d,"contract_code":c,"settlement":px,"source_url":m["url"]} for d,c,px in data]
    rows.sort(key=lambda r:(r["trade_date"],r["contract_code"]))
    with p.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
    (p.parent/f"metadata_{a.part_index}.json").write_text(json.dumps({"part":a.part_index,"contracts":meta,"rows":len(rows)},indent=2),encoding="utf-8")
    print(json.dumps({"part":a.part_index,"contracts":[m["code"] for m in meta],"rows":len(rows)},indent=2))

if __name__=="__main__":
    main()
