# QQQ TAIL BANK V4

This test isolates the idea that tail protection should survive beyond the short-cycle premium harvest.

Per vintage:
- Harvest: +1 ~50Δ Call, -2 ~20Δ Calls, +2 ~8Δ Call Wings.
- Tail: +1 ~25Δ Long Put, -1 ~10Δ Short Put.
- Harvest expiry: nearest listed expiry in 18-35 DTE.
- Tail expiry: next listed expiry after that harvest expiry.
- Up to 2 simultaneous vintages, 50% capital each.

No within-vintage strike migration, no parameter optimization, no Black-Scholes, no interpolation.

The test compares the structural consequence of decoupling tail duration from harvest duration against the synchronized stack benchmark from V2.
