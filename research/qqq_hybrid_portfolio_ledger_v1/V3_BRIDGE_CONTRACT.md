# V3 Read-Only Bridge Contract

Ledger V1 and V3 remain separate authorities.

## Authorities

- Ledger V1: actual recorded fills, cashflows, positions, cost basis, NAV and P&L.
- V3: frozen Original Hybrid strategy state, target policy and BUY/HOLD/REDUCE recommendation.

## Direction

    V3 market snapshot
           |
    read-only bridge
           |
    Ledger UI recommendation

Never:

    Ledger P&L -> V3 policy
    Ledger P&L -> BUY/HOLD/REDUCE
    Bridge -> broker order

## Runtime behavior

The bridge searches for the real V3 engine at:

    ../../terminal/qqq_hybrid_deployment_terminal_v3/engine.js

relative to this directory, or uses QHP_V3_ENGINE when explicitly configured.

It asks the V3 terminal at QHP_V3_URL (default http://127.0.0.1:8788) for its existing /api/snapshot.

The bridge then loads the actual HybridEngineV3 source and calls its existing derive() function.

It does not copy or re-implement V3 policy.

When the V3 engine or V3 server is unavailable:

    connected = false
    available = false
    no recommendation is fabricated

This is intentional while PR #86 remains separate.

## Next reconciliation increment

A separate read-only reconciliation layer can later compare:

    Ledger actual position
    vs
    V3 target position

That comparison remains display-only until independently tested.
