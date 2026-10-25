# Original Hybrid Reconstruction Contract

## Purpose

Keep the historical Original Hybrid result and the live follow-engine tied to one reproducible decision function.

## Required chain

RAW MARKET DATA
→ FEATURE VECTOR
→ STATE
→ LOCKED POLICY
→ TARGET POSITIONS
→ CURRENT→TARGET DELTAS
→ ACTION
→ EXECUTION MODEL
→ P&L
→ EQUITY CURVE

## Golden rule

For the same timestamp and the same normalized input record, LIVE and REPLAY must call the same `engine.js` decision function.

A mismatch is a **RECONSTRUCTION FAILURE**, not a tuning opportunity.

## Required normalized fields

- timestamp
- QQQ
- VXX
- VIX
- VX M1 code, expiry, quote
- VX M2 code, expiry, quote
- S_t = (M2 - M1) / M1
- option leg identity when a leg is present
- current simulated position ledger
- policy version
- engine version
- action and reason
- data provenance per field

## No leakage

Replay may only use values available at or before the replay timestamp. Future option prices, future contract selections, future regime labels, and future outcomes are forbidden.

## Baseline integrity

The 12.7049% / -23.1837% source-aligned replay is a reference result. It is not used as a live optimizer target.

The exact reconstruction gate remains pending until the original source-aligned option surface, contract identity, exit path, execution/friction rules and frozen reference vectors are present in source-visible form.

## Secondary VX source policy

Preferred order:

1. Futu OpenD VX quotes, if the account has CFE entitlement.
2. Databento CFE XCBF.PITCH, if the account has a valid live-data subscription/API key.
3. BLOCK.

Never:

- scrape Cboe delayed-quote HTML
- use VIX spot as M2
- manufacture term structure from a proxy
- silently mix a proxy into the VIX futures fields

## Position safety

If term structure is blocked, current position = target position. No automatic ADD or REDUCE instruction is generated.

If the policy is in a REDUCE state, target logic may reduce an existing seller leg but must not create a new ADD signal.

Human actions are recorded independently and may be marked CONFLICT.
