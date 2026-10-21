# OpenD probe results — 2026-10-06 19:05 HKT (DESKTOP-GNMQ0PF)

futu-api 10.11.7108, OpenD server_ver 1010, qot_logined=True, market_usfuture=FUTURE_OPEN.

| Code | API | Result |
|---|---|---|
| `US.QQQ`, `US.VXX` | get_market_snapshot | OK (756.2 / 17.2) |
| `US..VIX` | snapshot / subscribe / history_kline | `暂不支持美股指数` |
| `US.VIX` | snapshot | `未知股票 VIX` (invalid code — the old adapter used this) |
| `US.VIXmain` | snapshot | `未知股票 VIXmain` |
| `US.VX2610`, `US.VX2611`, `US.VXM2610`, `US.VXmain`, `US.VXcurrent` | snapshot / subscribe / history_kline | `暂不支持 CBOE 行情` |
| `US.ESmain`, `US.NQmain` | snapshot | `行情权限不足，请前往行情商城购买行情卡` |
| — | get_future_info(VXmain) | `行情权限不足…` |
| Market.US / SecurityType.FUTURE | get_stock_basicinfo | OK, 12782 rows; VX monthlies `US.VX2610` (exp 2026-10-21), `US.VX2611` (2026-11-18), `US.VX2612` … `US.VX2706`, exchange `US_CBOE` |

Conclusion: the codes are now right; the remaining block is **account quote permission** (US index + CBOE futures),
not code. No prior project on this machine ever obtained VIX index or VX futures quotes from OpenD
(brush-timber-mountain-brook `reports/local_run_result.txt`: `VIX.reason: 暂不支持美股指数`, `vix_test.class: PERMISSION`).
M1/M2 therefore remain DATA BLOCK; nothing is synthesised.
