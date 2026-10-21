# QQQ Hybrid Deployment Terminal V2 — Evolved

This version uses the original V2 as the base and absorbs the local-test findings without replacing it with the OpenD PR package.

## Core behavior

The terminal is a simulation-only follow-engine:

RAW LIVE / REPLAY DATA
→ Feature: S_t
→ LOCKED ORIGINAL HYBRID control layer
→ State
→ Current Position
→ Target Position
→ Action Queue
→ Change Monitor
→ Roll Radar
→ Journal

It never submits broker orders.

## What was absorbed from the field test

- Historical Replay now shows its date, state and prices in the replay panel.
- The top bar is compact and the decision/chart area is no longer hidden behind a tall sticky header.
- Engine action and human action are stored separately; contrary actions are marked as CONFLICT.
- Current → Target is the primary instruction, not a generic BUY/HOLD label.
- The action control supports ACK → STAGE → MARK DEPLOYED as simulation steps.
- State changes require persistence in the live polling loop before a notification is emitted, reducing one-tick noise.
- M1/M2 remain blocked when they are missing; no VIX-spot fake term structure is created.
- A candidate option chain may be shown, but it is explicitly separated from historical baseline contract identity.

## OpenD path

The Python adapter attempts:

Futu OpenD (127.0.0.1:11111 by default)
→ US QQQ / VXX / VIX snapshots
→ US futures static information (SecurityType.FUTURE)
→ identify upcoming VX futures by expiry
→ sort by first valid expiry
→ first two distinct valid maturities = M1/M2
→ snapshot their last prices
→ S_t=(M2-M1)/M1

Futu's current docs expose `get_market_snapshot()` for market snapshots and futures fields, and `get_stock_basicinfo()` for market-wide static information with futures support; `get_future_info()` is also available for futures contract metadata.

The code never substitutes VIX spot for M1/M2. If less than two valid VX monthly prices are available, the term-structure decision remains blocked.

## OpenD codes verified on this PC (2026-10-06, futu-api 10.11.7108, OpenD server_ver 1010)

| Purpose | Code | Result on this account |
|---|---|---|
| QQQ / VXX | `US.QQQ`, `US.VXX` | `get_market_snapshot` OK |
| VIX index | `US..VIX` (two dots = US index) | `暂不支持美股指数` — no US index quote permission |
| (wrong) | `US.VIX` | `未知股票 VIX` — invalid code, removed |
| VX monthlies | `US.VX2610`, `US.VX2611`, … (`US.VX<YYMM>`) | Discoverable via `get_stock_basicinfo(Market.US, SecurityType.FUTURE)` (exchange `US_CBOE`, `last_trade_time` = expiry). Snapshot / subscribe / history kline → `暂不支持 CBOE 行情` |
| VX aliases / mini | `US.VXmain`, `US.VXcurrent`, `US.VXnext`, `US.VXM<YYMM>` | same CBOE block; aliases/mini are excluded from M1/M2 selection |

No prior project on this machine ever received a VX futures or `US..VIX` quote from OpenD; the prior working pattern
(brush-timber-mountain-brook `backtest/vix_proxy.py`, LOCAL_RUN.md "VIX note") is: keep VIX index UNAVAILABLE on OpenD and
build a **DERIVED** QQQ ~30D ATM put IV proxy, never using it as VIX index or as term structure.

Adapter behavior now:
- QQQ/VXX and `US..VIX` are requested in **separate** snapshots, so the unsupported VIX code no longer knocks QQQ/VXX off OpenD.
- `vix` = OpenD `US..VIX` if permitted, else Yahoo `^VIX` (real index quote, labeled in `sources.vix`).
- `vix_proxy` = DERIVED QQQ ATM put IV from OpenD (informational only; not fed into `vix`, M1 or M2).
- M1/M2 = first two `US.VX<YYMM>` monthlies by expiry. Codes/expiries are reported; prices stay `null` and the
  term-structure decision stays **DATA BLOCK** until the account has CBOE futures quote permission (Futu 行情卡 for CBOE/CFE).

## Live data fallback

QQQ/VXX/VIX spot may fall back to Yahoo when the Python Futu package or OpenD connection is unavailable, but **M1/M2 do not fall back to Yahoo spot or synthetic formulas**.

This is intentional: a degraded spot feed is not equivalent to a verified VX term structure.

## Important research boundary

The app displays these historical/reference values:

- 12.7049% source-aligned replay CAGR
- -23.1837% daily MTM MaxDD
- 12.52% / -23.51% historical benchmark

They are reference metadata only. This app does not claim that its live candidate-contract selection reproduces those exact historical results.

The live policy layer contains the previously locked operational control values:

- QQQ core 42%
- VXX short 18% in normal VIX conditions
- VXX short 10% at VIX >= 28
- VXX short target 0 when S_t <= 0 as a conservative seller gate
- QQQ far-call budget 1.2%
- VXX call-spread budget 2%

Option DTE/Delta gates in the UI are explicitly operational monitoring gates, not claims about a hidden historical truth.

## Option candidate

`/api/options?symbol=QQQ` and `/api/options?symbol=VXX` are candidate-data helpers. Candidate selection uses Delta/DTE/strike heuristics only for operational assistance. The candidate is not written into the research baseline as a historical contract identity.

## Run on Windows

Double-click `RUN.cmd`, or:

```cmd
cd C:\path\to\QQQ_HYBRID_DEPLOYMENT_TERMINAL_V2_EVOLVED
py -3 server.py
```

Open:

`http://127.0.0.1:8787`

OpenD defaults to:

`127.0.0.1:11111`

Override with environment variables if needed:

```cmd
set FUTU_OPEND_HOST=127.0.0.1
set FUTU_OPEND_PORT=11111
set HYBRID_UI_PORT=8787
python server.py
```

## Journal philosophy

Every journal entry keeps:

- Engine signal
- Human action
- Conflict flag
- Inputs (QQQ/VXX/S)
- Mode
- State
- Reason

This is deliberate: we want to distinguish engine error from human non-adherence later.

## Professional UI references absorbed

The interface uses patterns seen in current professional trading tools: chart-visible order/position context, multi-leg strategy/roll grouping, and direct current-vs-new position comparison. It is an original interface, not a copy.

TradingView documents chart-visible positions/orders and direct chart order management. IBKR documents a multi-leg Roll Builder that compares the current combination with the new combination and surfaces estimated combo premium and margin impact.
