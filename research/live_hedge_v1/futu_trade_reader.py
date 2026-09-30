from __future__ import annotations

class FutuTradeReader:
    """Read-only Futu US account reconciliation. Never unlocks or submits."""
    def __init__(self,host="127.0.0.1",port=11111,real=True):
        self.host=host;self.port=port;self.real=real;self.ctx=None;self.futu=None
    def connect(self):
        import futu
        self.futu=futu
        self.ctx=futu.OpenSecTradeContext(host=self.host,port=self.port,filter_trdmarket=futu.TrdMarket.US)
    def close(self):
        if self.ctx:
            try:self.ctx.close()
            except Exception:pass
            self.ctx=None
    def read(self):
        self.connect()
        try:
            env=self.futu.TrdEnv.REAL if self.real else self.futu.TrdEnv.SIMULATE
            ret,pos=self.ctx.position_list_query(position_market=self.futu.TrdMarket.US,trd_env=env)
            if ret!=self.futu.RET_OK:raise RuntimeError("position_list_query: "+str(pos))
            ret2,orders=self.ctx.order_list_query(order_market=self.futu.TrdMarket.US,trd_env=env)
            if ret2!=self.futu.RET_OK:raise RuntimeError("order_list_query: "+str(orders))
            ps=[]
            if hasattr(pos,"iterrows"):
                for _,r in pos.iterrows():
                    raw=str(r.get("position_side","") or r.get("positionSide","")).upper()
                    side="LONG" if ("LONG" in raw or raw in {"0","BUY"}) else "SHORT"
                    ps.append({"code":str(r.get("code","")),"side":side,"qty":int(float(r.get("qty",0) or 0)),
                               "avg_cost":float(r.get("average_cost_price",r.get("cost_price",0)) or 0)})
            os=[]
            if hasattr(orders,"iterrows"):
                for _,r in orders.iterrows():
                    os.append({"order_id":str(r.get("order_id","")),"code":str(r.get("code","")),
                               "side":str(r.get("trd_side","")).upper(),"qty":int(float(r.get("qty",0) or 0)),
                               "price":float(r.get("price",0) or 0),"status":str(r.get("order_status","")).upper(),
                               "updated_at":str(r.get("updated_time",r.get("create_time","")) or "")})
            return {"source":"FUTU_TRADE_READ_ONLY","positions":ps,"orders":os}
        finally:self.close()
