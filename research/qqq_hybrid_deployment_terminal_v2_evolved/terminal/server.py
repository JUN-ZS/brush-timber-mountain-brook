import os, json, datetime, threading, re, urllib.request, urllib.parse, ssl
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

HOST=os.getenv("HYBRID_UI_HOST","127.0.0.1")
PORT=int(os.getenv("HYBRID_UI_PORT","8787"))
OPEND_HOST=os.getenv("FUTU_OPEND_HOST","127.0.0.1")
OPEND_PORT=int(os.getenv("FUTU_OPEND_PORT","11111"))
ROOT=Path(__file__).resolve().parent

try:
    import futu
except Exception:
    futu=None

_ctx=None
_ctx_lock=threading.Lock()
_contract_cache={"ts":0,"rows":[]}
_snapshot_lock=threading.Lock()  # one OpenD context shared by threaded HTTP handler

def ts_now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()

def opend_ctx():
    global _ctx
    if futu is None: return None
    with _ctx_lock:
        if _ctx is None:
            _ctx=futu.OpenQuoteContext(host=OPEND_HOST, port=OPEND_PORT)
    return _ctx

# --- Futu OpenD codes verified on this PC (2026-10-06, futu-api 10.11.7108) ---
# US.QQQ / US.VXX           -> get_market_snapshot OK (US stock LV1)
# US..VIX (index, two dots) -> "暂不支持美股指数" (no US index quote permission)
# US.VIX                    -> "未知股票 VIX" (wrong code; never valid)
# US.VX2610 / US.VX2611 ... -> discoverable via get_stock_basicinfo(Market.US, SecurityType.FUTURE),
#                              exchange_type US_CBOE, last_trade_time = expiry; quotes/subscribe/kline
#                              all return "暂不支持 CBOE 行情" (no CBOE futures quote permission)
# US.VXmain/VXcurrent/VXnext and US.VXM* (mini) -> same CBOE block.
STOCK_CODES=["US.QQQ","US.VXX"]
VIX_INDEX_CODE="US..VIX"
VX_MONTHLY_RE=re.compile(r"^US\.VX(\d{2})(\d{2})$")   # standard monthly VX only (excludes VXM mini, VXmain aliases)
_proxy_cache={"ts":0,"val":None}

def _snap(codes):
    ctx=opend_ctx()
    if ctx is None: raise RuntimeError("futu package unavailable")
    ret,data=ctx.get_market_snapshot(codes)
    if ret!=futu.RET_OK: raise RuntimeError(str(data))
    return data

def opend_spots():
    """QQQ/VXX and VIX are fetched separately: one bad code must not fail the whole batch."""
    out={}; errs={}
    try:
        for _,r in _snap(STOCK_CODES).iterrows():
            out[str(r["code"]).split(".")[-1].upper()]={"price":float(r["last_price"]),"update_time":str(r.get("update_time",""))}
    except Exception as e: errs["opend_qqq_vxx"]=str(e)
    try:
        for _,r in _snap([VIX_INDEX_CODE]).iterrows():
            out["VIX"]={"price":float(r["last_price"]),"update_time":str(r.get("update_time",""))}
    except Exception as e: errs["opend_vix"]=f"{VIX_INDEX_CODE}: {e}"
    return out,errs

def candidate_vx_contracts():
    now=datetime.datetime.now()
    if _contract_cache["rows"] and now.timestamp()-_contract_cache["ts"]<300:
        return _contract_cache["rows"]
    ctx=opend_ctx()
    if ctx is None: return []
    ret,data=ctx.get_stock_basicinfo(futu.Market.US, futu.SecurityType.FUTURE)
    if ret!=futu.RET_OK: raise RuntimeError(str(data))
    rows=[]
    for _,r in data.iterrows():
        code=str(r.get("code","")).strip()
        if not VX_MONTHLY_RE.match(code): continue
        ltd=str(r.get("last_trade_time","") or "").strip()
        m=re.search(r"(20\d\d[-/]\d\d[-/]\d\d)",ltd)
        if not m: continue
        try: expiry=datetime.datetime.strptime(m.group(1).replace("/","-"),"%Y-%m-%d")
        except ValueError: continue
        if expiry.date()<now.date(): continue
        rows.append({"code":code,"name":str(r.get("name","")),"expiry":expiry.strftime("%Y-%m-%d"),"exchange":str(r.get("exchange_type",""))})
    rows.sort(key=lambda x:x["expiry"])
    _contract_cache["rows"]=rows[:12]; _contract_cache["ts"]=now.timestamp()
    return _contract_cache["rows"]

def opend_vx():
    contracts=candidate_vx_contracts()
    if len(contracts)<2: return {"ok":False,"contracts":contracts,"reason":"less than two identifiable VX monthly futures"}
    try: data=_snap([c["code"] for c in contracts[:4]])
    except Exception as e:
        return {"ok":False,"contracts":contracts[:2],"reason":f"VX quote blocked by OpenD for {contracts[0]['code']}/{contracts[1]['code']}: {e}"}
    price={}
    for _,r in data.iterrows():
        try:
            v=float(r.get("last_price"))
            if v>0: price[str(r["code"])]=v
        except (TypeError,ValueError): pass
    picked=[{**c,"last_price":price[c["code"]]} for c in contracts if c["code"] in price][:2]
    if len(picked)<2 or picked[0]["code"]!=contracts[0]["code"]:
        return {"ok":False,"contracts":contracts[:2],"reason":"front two VX monthly prices not both valid"}
    return {"ok":True,"m1":picked[0],"m2":picked[1]}

def qqq_atm_iv_proxy(spot):
    """DERIVED VIX-units proxy (prior brush-timber-mountain-brook pattern): QQQ ~30D ATM put IV.
    Reported separately as vix_proxy; never written into vix, m1 or m2."""
    now=datetime.datetime.now()
    if _proxy_cache["val"] and now.timestamp()-_proxy_cache["ts"]<120: return _proxy_cache["val"]
    ctx=opend_ctx()
    if ctx is None or not spot: return None
    ret,ex=ctx.get_option_expiration_date(code="US.QQQ")
    if ret!=futu.RET_OK: raise RuntimeError(str(ex))
    best=None
    for _,r in ex.iterrows():
        d=r.get("option_expiry_date_distance")
        try: d=int(d)
        except (TypeError,ValueError): continue
        if d<7: continue
        if best is None or abs(d-30)<abs(best[1]-30): best=(str(r["strike_time"]),d)
    if not best: return None
    ret,ch=ctx.get_option_chain(code="US.QQQ",start=best[0],end=best[0],option_type=futu.OptionType.PUT)
    if ret!=futu.RET_OK: raise RuntimeError(str(ch))
    ch=ch.assign(_dist=(ch["strike_price"].astype(float)-float(spot)).abs()).sort_values("_dist").head(3)
    snap=_snap(list(ch["code"]))
    for _,r in snap.iterrows():
        try: iv=float(r.get("option_implied_volatility"))
        except (TypeError,ValueError): continue
        if iv>0:
            level=iv*100 if iv<=3 else iv
            val={"level":round(level,3),"source":"DERIVED","method":"QQQ_ATM_PUT_IV","code":str(r["code"]),"expiry":best[0],"dte":best[1],
                 "note":"QQQ ~30D ATM put IV in VIX units. NOT the Cboe VIX index; not used for M1/M2."}
            _proxy_cache.update(ts=now.timestamp(),val=val); return val
    return None

def yahoo(sym):
    u=f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym,safe='')}?range=1d&interval=1m&includePrePost=true"
    req=urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"})
    with urllib.request.urlopen(req,timeout=7,context=ssl.create_default_context()) as r: j=json.load(r)
    rs=j["chart"]["result"][0];return rs["meta"].get("regularMarketPrice")

def snapshot():
    out={"source":"OPEND","timestamp":ts_now(),"qqq":None,"vxx":None,"vix":None,"m1":None,"m2":None,"m1_code":None,"m2_code":None,
         "sources":{},"term_structure":"BLOCKED"}
    errs={}
    try:
        s,e=opend_spots(); errs.update(e)
        for k in ("qqq","vxx","vix"):
            if k.upper() in s: out[k]=s[k.upper()]["price"]; out["sources"][k]="OPEND"
    except Exception as e: errs["opend_spot"]=str(e)
    for k,sym in [("qqq","QQQ"),("vxx","VXX"),("vix","^VIX")]:
        if out[k] is not None: continue
        try: out[k]=float(yahoo(sym)); out["sources"][k]=f"YAHOO {sym}"
        except Exception as ee: errs[f"yahoo_{k}"]=str(ee)
    srcs=set(out["sources"].values())
    out["source"]="OPEND" if srcs=={"OPEND"} else ("OPEND+YAHOO" if "OPEND" in srcs else ("YAHOO-SPOT-FALLBACK" if srcs else "UNAVAILABLE"))
    try:
        vx=opend_vx()
        if vx.get("ok"):
            out.update(m1=vx["m1"]["last_price"],m2=vx["m2"]["last_price"],m1_code=vx["m1"]["code"],m2_code=vx["m2"]["code"],
                       m1_expiry=vx["m1"]["expiry"],m2_expiry=vx["m2"]["expiry"],term_structure="OPEND")
            out["sources"]["m1m2"]="OPEND"
        else:
            errs["vx_futures"]=vx.get("reason"); out["sources"]["m1m2"]="BLOCKED"
            c=vx.get("contracts") or []
            if len(c)>=2:  # contract identity only; prices stay null (DATA BLOCK)
                out.update(m1_code=c[0]["code"],m2_code=c[1]["code"],m1_expiry=c[0]["expiry"],m2_expiry=c[1]["expiry"])
    except Exception as e: errs["vx_futures"]=str(e); out["sources"]["m1m2"]="BLOCKED"
    try: out["vix_proxy"]=qqq_atm_iv_proxy(out["qqq"]) if out["sources"].get("qqq")=="OPEND" else None
    except Exception as e: errs["vix_proxy"]=str(e)
    if errs: out["errors"]=errs
    return out

def yahoo_options(symbol):
    url=f"https://query2.finance.yahoo.com/v7/finance/options/{urllib.parse.quote(symbol,safe='')}"
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
    with urllib.request.urlopen(req,timeout=8,context=ssl.create_default_context()) as r:j=json.load(r)
    res=j["optionChain"]["result"][0]
    calls=res.get("options",[{}])[0].get("calls",[])
    spot=res.get("quote",{}).get("regularMarketPrice")
    norm=[]
    now=datetime.datetime.now(datetime.timezone.utc).timestamp()
    for x in calls:
        if not x.get("strike"): continue
        exp=x.get("expiration",0); days=max(1,int(round((exp-now)/86400))) if exp else None
        delta=x.get("delta")
        norm.append({"strike":x.get("strike"),"delta":delta,"days":days,"bid":x.get("bid"),"ask":x.get("ask"),"last":x.get("lastPrice")})
    return {"symbol":symbol,"spot":spot,"calls":norm,"source":"YAHOO OPTIONS CANDIDATE"}

class H(SimpleHTTPRequestHandler):
    def log_message(self,fmt,*args): return
    def do_GET(self):
        if self.path.startswith("/api/health"):
            raw=json.dumps({"ok":True,"opend_package":futu is not None,"host":OPEND_HOST,"port":OPEND_PORT}).encode();self.send_response(200);self.send_header("Content-Type","application/json");self.end_headers();self.wfile.write(raw);return
        if self.path.startswith("/api/snapshot"):
            try:
                with _snapshot_lock: raw=json.dumps(snapshot(),ensure_ascii=False).encode("utf-8");code=200
            except Exception as e: raw=json.dumps({"error":str(e)}).encode();code=502
            self.send_response(code);self.send_header("Content-Type","application/json; charset=utf-8");self.send_header("Cache-Control","no-store");self.end_headers();self.wfile.write(raw);return
        if self.path.startswith("/api/options"):
            q=urllib.parse.urlparse(self.path);p=urllib.parse.parse_qs(q.query);sym=p.get("symbol",["QQQ"])[0].upper()
            if sym not in {"QQQ","VXX"}: self.send_error(400,"symbol must be QQQ or VXX");return
            try: raw=json.dumps(yahoo_options(sym)).encode();code=200
            except Exception as e: raw=json.dumps({"error":str(e)}).encode();code=502
            self.send_response(code);self.send_header("Content-Type","application/json");self.send_header("Cache-Control","no-store");self.end_headers();self.wfile.write(raw);return
        return super().do_GET()

if __name__=="__main__":
    print(f"QQQ Hybrid Deployment Terminal V2 Evolved -> http://{HOST}:{PORT}")
    print(f"OpenD -> {OPEND_HOST}:{OPEND_PORT} (read-only market data)")
    print("No order routing. / 不傳送券商真單。")
    ThreadingHTTPServer((HOST,PORT),H).serve_forever()
