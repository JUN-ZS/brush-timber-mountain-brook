# QQQ STATE-ADAPTIVE OPTION GEOMETRY V1

Research-only branch continuing the QQQ ratio-call and downside-convexity line.

## Frozen entry

- 1 ATM (~50 delta) Long Call
- 2 ~20 delta Short Calls
- 2 ~8 delta farther OTM Long Call Wings
- 1 ~25 delta Long Put
- 1 ~10 delta Short Put

## Frozen upward-wave transition

Trigger: previous trading-day Close >= current anchor Close + 1.0 x ATR20.

Execution: migrate on the next trading day (T+1).

- Short Calls: 20 delta -> 30 delta -> 40 delta, progressively closer to spot.
- Short Put: 10 delta -> 5 delta, farther OTM.
- Long Put: permanently retained and never migrated in V1.
- ATM Call: fixed.
- Call Wings: fixed.
- N: fixed at 2.
- Expiry: fixed from entry.

A successful migration buys the old short at Ask and sells the new short at Bid. The Long Put is not sold during this transition.

## Control

The exact same entry dates and initial contracts are compared under:

- STATIC_GEOMETRY: no migration.
- STATE_ADAPTIVE_GEOMETRY: frozen upward-wave migration.

No dynamic N, expiry switching, Black-Scholes pricing, interpolation, or parameter optimization.

Opening uses Ask for long legs and Bid for short legs. Daily marks use Mid. Exits use executable Bid/Ask.

The purpose is to test whether moving the Short Call inward while moving only the Short Put outward, with the Long Put retained as the convexity anchor, changes the economics of the payoff surface.

The canonical public QQQ option release is only used over dates covered by that real historical chain; this experiment does not claim a 2026 real-chain OOS result.
