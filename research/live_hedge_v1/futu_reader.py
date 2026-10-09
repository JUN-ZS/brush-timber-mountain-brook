from __future__ import annotations
from datetime import date, datetime, timezone
from typing import Any
from backtest.futu_adapter import FutuOpenDAdapter
from backtest.types import OptionContract, QQQ_CODE

def _enrich_contracts_with_quotes(contracts, quote_objects):
    """Attach LIVE option quote/greek fields to chain metadata before selection."""
    by_code = {str(q.code): q for q in quote_objects}
    out = []
    for c in contracts:
        q = by_code.get(str(c.code))
        if q is None:
            out.append(c)
            continue
        out.append(
            OptionContract(
                code=c.code,
                underlying=c.underlying,
                right=c.right,
                strike=c.strike,
                expiry=c.expiry,
                dte=c.dte,
                lot_size=c.lot_size,
                bid=q.bid,
                ask=q.ask,
                last=q.last,
                iv=q.iv,
                delta=q.delta,
                gamma=q.gamma,
                theta=q.theta,
                vega=q.vega,
                oi=q.oi,
                volume=q.volume,
                source=q.source,
                field_sources=q.field_sources,
                reason=q.reason,
            )
        )
    return out


def _source_age_sec(quote, now=None):
    now = now or datetime.now(timezone.utc)
    extra = getattr(quote, "extra", {}) or {}
    ts = extra.get("update_timestamp")
    try:
        if ts is None:
            return None
        return max(0.0, now.timestamp() - float(ts))
    except (TypeError, ValueError):
        return None


def _compute_signal(last, history):
    dates = [x[0] for x in history]
    closes = [x[1] for x in history]
    today = date.today().isoformat()
    ref = closes[:-1] if dates and str(dates[-1])[:10] == today else closes
    if last is None:
        return {
            "status": "DATA_GAP",
            "active": None,
            "ratio52": None,
            "ext200": None,
            "reference_count": len(ref),
            "reason": "QQQ spot unavailable",
        }
    if len(ref) < 252:
        return {
            "status": "DATA_GAP",
            "active": None,
            "ratio52": None,
            "ext200": None,
            "reference_count": len(ref),
            "reason": f"need >=252 reference daily closes; got {len(ref)}",
        }
    dma = sum(ref[-199:] + [last]) / 200
    high = max(ref[-251:] + [last])
    ext = last / dma - 1 if dma else None
    ratio = last / high if high else None
    active = bool(ratio is not None and ratio >= .98 and ext is not None and ext >= .08)
    return {
        "status": "OK",
        "active": active,
        "ratio52": ratio,
        "ext200": ext,
        "reference_count": len(ref),
        "reason": None,
    }


class LiveFutuReader:
    """Live QQQ quote/chain reader. Never places or modifies orders."""
    def __init__(self,host="127.0.0.1",port=11111):
        self.a=FutuOpenDAdapter(host,port)
    def connect(self):
        return self.a.connect().to_dict()
    def close(self):
        self.a.disconnect()
    def _row(self,row,name,default=None):
        if isinstance(row,dict): return row.get(name,default)
        try:return row[name]
        except Exception:return getattr(row,name,default)
    def _expiry_targets(self,targets=(14,30,45,90,120,180)):
        ret_ok=getattr(self.a.futu,"RET_OK",0)
        ret,data=self.a.ctx.get_option_expiration_date(code=QQQ_CODE)
        if ret!=ret_ok: raise RuntimeError(str(data))
        vals=[str(x)[:10] for x in data["strike_time"].tolist()] if hasattr(data,"columns") and "strike_time" in data.columns else [str(x)[:10] for x in data]
        today=date.today(); ds=[]
        for e in vals:
            try:d=(datetime.strptime(e,"%Y-%m-%d").date()-today).days
            except Exception:continue
            if 5<=d<=210:ds.append((d,e))
        out=[]; used=set()
        for t in targets:
            if not ds:break
            _,e=min(ds,key=lambda z:abs(z[0]-t))
            if e not in used:out.append(e);used.add(e)
        return out
    def contracts(self):
        futu=self.a.futu; ret_ok=getattr(futu,"RET_OK",0); ot=getattr(futu,"OptionType").CALL
        raw=[]
        for exp in self._expiry_targets():
            ret,data=self.a.ctx.get_option_chain(code=QQQ_CODE,start=exp,end=exp,option_type=ot)
            if ret!=ret_ok:continue
            dte=(datetime.strptime(exp,"%Y-%m-%d").date()-date.today()).days
            for row in self.a._iter_rows(data):
                code=str(self._row(row,"code",""))
                if not code:continue
                try:strike=float(self._row(row,"strike_price",self._row(row,"option_strike_price")))
                except Exception:continue
                try:lot=int(float(self._row(row,"lot_size",self._row(row,"option_contract_size",100)) or 100))
                except Exception:lot=100
                raw.append(OptionContract(code,QQQ_CODE,"CALL",strike,exp,dte,lot,None,None,None,None,None,None,None,None,None,None,"LIVE QUOTE",
                    {"code":"LIVE QUOTE","strike":"LIVE QUOTE","expiry":"LIVE QUOTE"}))
        return raw
    def snapshot(self,extra_codes=None):
        conn=self.connect()
        if conn.get("status") not in {"PASS","PARTIAL"}:return {"status":"BLOCKED","connection":conn}
        try:
            q=self.a.get_qqq_quote(); hist=self.a.get_daily_closes(QQQ_CODE,n=320); collected_at=datetime.now(timezone.utc)
            source_age = _source_age_sec(q, collected_at)
            order=sorted(zip(hist.get("dates") or [],hist.get("closes") or []),key=lambda z:z[0])
            signal=_compute_signal(q.last, order)
            cs=self.contracts()
            # Keep the quote request practical: near-ATM calls plus the far OTM region,
            # while always including exact held/order codes for reconciliation.
            spot=q.last or 0.0
            tradable={c.code for c in cs if spot<=0 or (0.85*spot <= c.strike <= 1.60*spot)}
            codes=tradable|set(extra_codes or [])
            quote_objects = self.a.get_option_quotes(list(codes))
            quotes={x.code:x.to_dict() for x in quote_objects}
            live_contracts = _enrich_contracts_with_quotes(cs, quote_objects)
            return {"status":"OK","connection":conn,
                "market":{"spot":q.last,"bid":q.bid,"ask":q.ask,"timestamp":collected_at.isoformat(),"source_timestamp":q.timestamp,"source":q.source,
                          "signal_active":signal["active"],"signal_status":signal["status"],
                          "source_age_sec":source_age,
                          "ratio52":signal["ratio52"],"ext200":signal["ext200"],
                          "history_source":hist.get("source"),
                          "history_reference_count":signal["reference_count"],
                          "history_requested":hist.get("requested"),
                          "history_available":hist.get("available"),
                          "history_start":hist.get("history_start"),
                          "history_end":hist.get("history_end"),
                          "history_reason":hist.get("reason") or signal["reason"]},
                "contracts":[x.__dict__ for x in live_contracts],"quotes":quotes,"source":"FUTU_OPEND_READ_ONLY"}
        finally:self.close()
