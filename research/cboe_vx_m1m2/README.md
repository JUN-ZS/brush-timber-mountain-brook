# Cboe VX M1/M2 Bridge

## Purpose
This lane makes real Cboe VX M1/M2 a replaceable market-data input for Original Hybrid research.

Two separate tests are kept:
1. Historical source-swap parity: old external M1/M2 versus Cboe-built M1/M2.
2. Delayed live collection: current VX chain → strict standard-monthly M1/M2 selection.

Neither test alone proves the historical CAGR.

## Historical selection rule
- standard monthly VX contracts only
- exclude weekly numbered VX contracts
- exclude VXM/VXT
- expiry must be later than the trade date
- sort by actual expiry
- earliest eligible contract is M1; second is M2
- S = (M2-M1)/M1
- expiry-day final settlement is not used as a prior-close state

## Delayed source
Primary endpoint: https://www-api.cboe.com/us/futures/api/data/?symbol=VX
Official delayed page: https://www.cboe.com/delayed_quotes/vx/future_quotes/

The endpoint is treated as a public implementation surface, not as a contractual Cboe API guarantee. The collector fails closed when fewer than two standard monthly VX contracts have usable prices.

Settlement is preferred so the delayed lane is aligned with the historical daily-settlement research lane. --allow-last is explicit fallback only.

## Why the filter is strict
Cboe currently displays normal VX monthly contracts together with numbered contracts such as VX40/V6 and separate VXT/VXM products. The collector keeps only the standard monthly slash-form.

## Provenance
- CBOE_VX_CONTRACT_ARCHIVE_DAILY_SETTLEMENT = historical Cboe per-expiry daily settlement source
- CBOE_PUBLIC_DELAYED_VX_FUTURES_API = public delayed endpoint source
- TERM_CARRY / TERM_REDUCE / TERM_HOLD = term-only hint, not the full Original Hybrid action

## Important
This bridge solves M1/M2 acquisition. It does not replace QQQ/VXX spot, option-chain, or execution inputs and it does not transmit broker orders.