# NEXT AI TASK QUEUE

## P0 — M1/M2 truth experiment
Validate the imported dataset against an authoritative contract-level source.
Normalize contract code, expiry, timestamp, quote/settlement, and M1/M2 selection.

Then mask real M1/M2 and run the historical reconstruction method.
Compare numerical error, S_t error, regime agreement, action agreement, and P&L impact.

## P1 — Exact Original Hybrid reconstruction
Rebuild the 12.7049% / -23.1837% reference from source-visible policy, option identity, exits, friction, and frozen vectors.
Do not tune to force parity.

## P2 — Attribution / ablation
Remove one economic component at a time:
- QQQ core
- QQQ call-credit
- VXX short
- VXX call
- shock breaker
Measure incremental return, DD, tail loss, turnover, crisis contribution.

## P3 — Strategy evolution
Only after P0/P1:
compare Original Hybrid, QQQ-only, QQQ+call-credit, VXX carry, conditional VXX carry, VXX convexity, QQQ convexity, hybrids.
Use minimum sample + confidence shrinkage + OOS.

## P4 — Live terminal
Refine PR #80 from all-or-nothing M1/M2 blocking to:
FULL STATE
PARTIAL STATE
RISK ONLY
NO NEW CARRY
BLOCKED

Never invent term structure.

## P5 — Persistent memory
Record timestamp, raw/normalized data, provenance, state, policy/engine version, current ledger, target ledger, delta, reason, confidence, missing evidence, trigger/PIN, human action, conflict, LIVE/REPLAY.

## DO NOT
- route broker orders
- use VIX as M2
- mark synthetic as LIVE
- search until PASS
- optimize against a remembered CAGR
- mix protected-put V2.2 into the Original Hybrid reconstruction
