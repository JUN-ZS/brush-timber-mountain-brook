# Strategy Pool → Actual Deployment Replay V1

Research-only controlled replay of the current Cell 15 Strategy / Funding Context semantics.

## Question
Does the current funding layer add deployment value when connected to a fixed Strategy Pool?

## Frozen inputs
- QQQ observed path: repository attachments/spots_qqq_vxx_vix.1csv
- VX term: official Cboe daily settlement; standard monthly VX only; expiry > trade date; M1/M2 sorted by actual expiry
- Regime: CARRY (S > 5% and VIX < 28), WEAKENING (0% < S <= 5%), PRE-SHOCK (S <= 0% or VIX >= 28%), SHOCK (S <= 0% and VIX >= 28%)
- QQQ core target: 42% NAV
- Research pool interpretation: fixed 10-year pool B, equal monthly tranches B/120
- Pool size: 120000 USD, so monthly tranche is 1000 USD
- Horizon: 2018-03-01 to 2026-09-04
- Causality: monthly capital is recorded at first observed trading-session close; routing uses that close; QQQ execution is next observed session close

## Controls
1. FULL_QQQ: 100% of each monthly tranche to QQQ.
2. TARGET_42: fill the same 42% QQQ gap regardless of regime.
3. POOL_GATED: current Cell 15 semantics: fill the 42% QQQ gap only in CARRY / WEAKENING; PRE-SHOCK / SHOCK leave new money in reserve.

TARGET_42 versus POOL_GATED is the primary A/B because the 42% target is held constant and only the regime gate changes.

## Deliberate exclusions
- No VXX P&L.
- No option P&L or option candidate selection.
- No broker execution.
- No parameter optimization.
- No VIX-to-M1/M2 proxy.
- No mutation of frozen targetLedger.

This isolates the deployment layer. It is not a full Original Hybrid P&L backtest.
