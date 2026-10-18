# QQQ STAGGERED + DYNAMIC GEOMETRY V3

V3 combines the two previously isolated dimensions.

Per-vintage package is frozen:
`+1 ~50Δ Call -2 ~20Δ Calls +2 ~8Δ Call Wings +1 ~25Δ Long Put -1 ~10Δ Short Put`.

Cross-date:
- 1 layer
- 2 layer half-stack
- 4 layer stack

Within-vintage adaptive mode:
- previous close >= anchor close + 1.0 ATR20
- next trading day migration
- Short Call 20Δ -> 30Δ -> 40Δ
- Short Put 10Δ -> 5Δ
- Long Put retained
- ATM / wings / N / expiry fixed

The comparison is static stack vs adaptive stack at each stack depth.

No parameter optimization, Black-Scholes pricing, or interpolation.
