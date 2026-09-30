# QQQ REALCHAIN CONVEXITY V1

This is a research-only data-wall test.

Frozen portfolio: 42% QQQ buy-and-hold core plus a permanent QQQ bearish put spread.
The spread is long approximately 25-delta put and short approximately 10-delta put.
Budget is fixed at 2% NAV premium per hedge cycle.

Execution is actual historical chain data:
- long put bought at Ask
- short put sold at Bid
- daily mark at Mid
- long put sold at Bid
- short put bought at Ask
- no interpolation
- no Black-Scholes contract selection

Expiry selection is the nearest expiry in 18-35 calendar DTE; delta selection uses the actual chain delta field. Both legs use the same expiry.

The test intentionally isolates the convexity component and excludes VIX/VXX and the other hybrid layers.

Canonical public release: lambdaclass/options_portfolio_backtester data-v1, which publishes QQQ_options.parquet and QQQ_underlying.parquet for the 2008-2025 data release. The published release identifies the options and underlying sources and asset hashes.