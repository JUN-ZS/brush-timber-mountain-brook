# Read-only OpenD code probe used on DESKTOP-GNMQ0PF 2026-10-06 (no trade context, no orders).
from futu import *
ctx = OpenQuoteContext(host="127.0.0.1", port=11111)
try:
    for codes in (["US.QQQ", "US.VXX"], ["US..VIX"], ["US.VIX"], ["US.VXmain"], ["US.VX2610"], ["US.VX2611"], ["US.VXM2610"]):
        print(codes, ctx.get_market_snapshot(codes)[1])
    ret, d = ctx.get_stock_basicinfo(Market.US, SecurityType.FUTURE)
    if ret == RET_OK:
        print(d[d["code"].str.match(r"^US\.VX")][["code", "name", "last_trade_time", "exchange_type"]].to_string())
    for c in ("US.VX2610", "US..VIX"):
        print(c, "subscribe", ctx.subscribe([c], [SubType.QUOTE], subscribe_push=False))
        print(c, "history_kline", ctx.request_history_kline(c, ktype=KLType.K_DAY, max_count=3)[1])
finally:
    ctx.close()
