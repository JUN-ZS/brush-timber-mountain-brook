from __future__ import annotations
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo
from typing import Any

from .engine import SIGNAL_EXT200_GTE, SIGNAL_RATIO52_GTE
from backtest.futu_adapter import FutuOpenDAdapter
from backtest.types import OptionContract, QQQ_CODE

_US_EXCHANGE_TZ = ZoneInfo("America/New_York")


def _normalize_quote_timestamp(timestamp):
    raw = str(timestamp or "").strip()
    if not raw:
        return None
    for candidate in (raw, raw.replace("Z", "+00:00")):
        try:
            parsed = datetime.fromisoformat(candidate)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=_US_EXCHANGE_TZ)
            return parsed.astimezone(timezone.utc).isoformat()
        except (TypeError, ValueError):
            continue
    return None


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
    def _quote_date(self, timestamp):
        raw = str(timestamp or "").strip()
        try:
            return datetime.strptime(raw[:10], "%Y-%m-%d").date()
        except Exception:
            return None

    def _expiry_targets(self, asof_date=None):
        ret_ok=getattr(self.a.futu,"RET_OK",0)
        ret,data=self.a.ctx.get_option_expiration_date(code=QQQ_CODE)
        if ret!=ret_ok:
            raise RuntimeError(str(data))
        vals=[str(x)[:10] for x in data["strike_time"].tolist()] if hasattr(data,"columns") and "strike_time" in data.columns else [str(x)[:10] for x in data]
        today=asof_date or date.today()
        expiries=[]
        for e in vals:
            try:
                d=(datetime.strptime(e,"%Y-%m-%d").date()-today).days
            except Exception:
                continue
            if 7 <= d <= 35 or 60 <= d <= 210:
                expiries.append((d,e))
        return [e for _,e in sorted(set(expiries), key=lambda z:(z[0],z[1]))]
    def contracts(self, asof_date=None):
        futu=self.a.futu; ret_ok=getattr(futu,"RET_OK",0); ot=getattr(futu,"OptionType").CALL
        raw=[]
        for exp in self._expiry_targets(asof_date=asof_date):
            ret,data=self.a.ctx.get_option_chain(code=QQQ_CODE,start=exp,end=exp,option_type=ot)
            if ret!=ret_ok:continue
            dte=(datetime.strptime(exp,"%Y-%m-%d").date()-(asof_date or date.today())).days
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
            q=self.a.get_qqq_quote(); hist=self.a.get_daily_closes(QQQ_CODE,n=320); collected_at=datetime.now(timezone.utc).isoformat()
            normalized_timestamp=_normalize_quote_timestamp(getattr(q, "timestamp", None))
            timestamp_ok=normalized_timestamp is not None
            order=sorted(zip(hist.get("dates") or [],hist.get("closes") or []),key=lambda z:z[0])
            dates=[x[0] for x in order]; closes=[x[1] for x in order]
            market_date=self._quote_date(getattr(q, "timestamp", None)) or date.today()
            ref=closes[:-1] if dates and str(dates[-1])[:10]==market_date.isoformat() else closes
            sig=False; ext=None; ratio=None
            if q.last is not None and len(ref)>=252:
                dma=sum(ref[-199:]+[q.last])/200; high=max(ref[-251:]+[q.last])
                ext=q.last/dma-1 if dma else None; ratio=q.last/high if high else None
                sig=bool(timestamp_ok and ratio is not None and ratio>=SIGNAL_RATIO52_GTE and ext is not None and ext>=SIGNAL_EXT200_GTE)
            cs=self.contracts(asof_date=market_date)
            # Keep the quote request practical: near-ATM calls plus the far OTM region,
            # while always including exact held/order codes for reconciliation.
            spot=q.last or 0.0
            tradable={c.code for c in cs if spot<=0 or (0.85*spot <= c.strike <= 1.60*spot)}
            codes=tradable|set(extra_codes or [])
            quotes={x.code:x.to_dict() for x in self.a.get_option_quotes(list(codes))}
            return {"status":"OK","connection":conn,
                "market":{"spot":q.last,"bid":q.bid,"ask":q.ask,"timestamp":normalized_timestamp,"collected_at_utc":collected_at,"source_timestamp":q.timestamp,"source":q.source,
                          "market_timestamp_status":"VALID" if timestamp_ok else "INVALID_OR_MISSING",
                          "signal_active":sig,"ratio52":ratio,"ext200":ext,"history_source":hist.get("source")},
                "contracts":[x.__dict__ for x in cs],"quotes":quotes,"source":"FUTU_OPEND_READ_ONLY"}
        finally:self.close()
