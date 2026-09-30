from __future__ import annotations
import argparse,json
from pathlib import Path
from .engine import Contract,Position,Order,select_far,select_near,plan
from .futu_reader import LiveFutuReader
from .futu_trade_reader import FutuTradeReader
from .state import StateStore

def C(x):
    return Contract(code=str(x["code"]),right=str(x.get("right","CALL")).upper(),strike=float(x["strike"]),expiry=str(x["expiry"]),
                    dte=int(x["dte"]),bid=x.get("bid"),ask=x.get("ask"),delta=x.get("delta"),gamma=x.get("gamma"),iv=x.get("iv"))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--far-dte",type=int,default=120);ap.add_argument("--far-delta",type=float,default=.08)
    ap.add_argument("--near-dte",type=int,default=30);ap.add_argument("--host",default="127.0.0.1");ap.add_argument("--port",type=int,default=11111)
    ap.add_argument("--simulate-account",action="store_true");ap.add_argument("--out",default="research/live_hedge_v1/live_state.json")
    args=ap.parse_args()
    acct=FutuTradeReader(args.host,args.port,real=not args.simulate_account).read()
    extra=[p["code"] for p in acct.get("positions",[])]+[o["code"] for o in acct.get("orders",[])]
    snap=LiveFutuReader(args.host,args.port).snapshot(extra)
    if snap.get("status")!="OK":
        print(json.dumps(snap,ensure_ascii=False,indent=2));return 2
    market=snap["market"];contracts=[C(x) for x in snap["contracts"]];quotes=snap.get("quotes",{});by={c.code:c for c in contracts}
    pos=[]
    for p in acct.get("positions",[]):
        meta=by.get(p["code"]);q=quotes.get(p["code"],{})
        pos.append(Position(p["code"],p["side"],p["qty"],p["avg_cost"],meta.strike if meta else None,meta.expiry if meta else None,
                            meta.dte if meta else None,q.get("delta"),q.get("gamma")))
    far_pos=next((p for p in pos if p.side=="SHORT" and ("QQQ" in p.code.upper() or p.code.upper().startswith("US.Q"))),None)
    far=by.get(far_pos.code) if far_pos else select_far(contracts,float(market["spot"]),args.far_dte,args.far_delta)
    if far is not None and far.code in quotes:
        z=quotes[far.code];far=Contract(far.code,far.right,far.strike,far.expiry,far.dte,z.get("bid"),z.get("ask"),z.get("delta"),z.get("gamma"),z.get("iv"),far.lot_size)
    near=select_near(contracts,float(market["spot"]),args.near_dte)
    if near is not None and near.code in quotes:
        z=quotes[near.code];near=Contract(near.code,near.right,near.strike,near.expiry,near.dte,z.get("bid"),z.get("ask"),z.get("delta"),z.get("gamma"),z.get("iv"),near.lot_size)
    st=StateStore(Path(args.out).with_name("state.json"));old=st.load();previous_delta=old.get("far_delta");hist=old.get("gamma_history") or []
    baseline=sum(hist[-20:])/len(hist[-20:]) if len(hist)>=3 else None
    p=plan(market=market,far=far,near=near,positions=pos,orders=[Order(**o) for o in acct.get("orders",[])],
           signal_active=bool(market.get("signal_active")),far_campaign_active=far_pos is not None,
           quotes_by_code=quotes,gamma_baseline=baseline,previous_far_delta_abs=previous_delta)
    if far:st.update_far(far.code,far.delta,far.gamma,previous_delta)
    p["positions_source"]=acct.get("source");p["source"]="FUTU_OPEND_READ_ONLY";p["manual_execution_only"]=True
    Path(args.out).parent.mkdir(parents=True,exist_ok=True);Path(args.out).write_text(json.dumps(p,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps(p,indent=2,ensure_ascii=False));return 0

if __name__=="__main__":raise SystemExit(main())
