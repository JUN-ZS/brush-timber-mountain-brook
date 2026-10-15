# Strategy Preservation Register — QQQ Put Research

Status: active preservation contract. This file records **discoverability and research continuity**, not permission to add a strategy to the primary portfolio.

## Why this exists

The primary sizing path was deliberately narrowed to two defined-risk call-credit verticals: QQQ CALL-CREDIT and VXX CALL-CREDIT. That scope limit must not silently become a deletion/hiding rule for strategies already being researched. A primary-budget decision and a research-preservation decision are separate.

## Preserved tracks

| Stable track ID | What it means | Canonical implementation | Main-desk route | Status |
|---|---|---|---|---|
| `QQQ_LONG_PUT` | QQQ put chain / long-put candidate research. The screenshot fixture contains no Put marks; no sample put is fabricated. | `option_chain_lab.html`, QQQ_PUT chain; main engine research candidate `longPuts` | `option_chain_lab.html?chain=QQQ_PUT` | RESEARCH ONLY |
| `QQQ_PUT_RATIO_N1_LONG_HEAVY` | Buy N lower-strike QQQ LONG PUTs and sell 1 higher-strike SHORT PUT; N=1–6; same expiry. | `hub_research_pack.js:calculatePutRatio`; `QQQ_PUT_RATIO_BACKSPREAD_CONTRACT.md` | `hub_research_pack.html?strategyMode=put-ratio&putRatioDirection=long-heavy` | RESEARCH ONLY |
| `QQQ_PUT_RATIO_N1_SHORT_HEAVY` | Sell N lower-strike QQQ SHORT PUTs and buy 1 higher-strike LONG PUT; N=1–6; same expiry. | `hub_research_pack.js:calculatePutRatio`; `QQQ_PUT_RATIO_BACKSPREAD_CONTRACT.md` | `hub_research_pack.html?strategyMode=put-ratio&putRatioDirection=short-heavy` | RESEARCH ONLY |
| `QQQ_SHOCK_GATED_PUT_DEBIT` | Shock-gated long-put debit-spread candidate; its short Put is a separately modeled wing, not the N:1 ratio. | `hub_research_pack.js:calculateShockGatedPut` | `hub_research_pack.html?strategyMode=shock-put` | RESEARCH ONLY |

## Non-integration boundary

- The main terminal's primary option-risk whitelist remains exactly QQQ CALL-CREDIT and VXX CALL-CREDIT.
- A Hub calculation can inspect one selected research structure against a manually imported snapshot of remaining risk. It does **not** write a Put reservation back to the main ledger and does not coordinate simultaneous positions across multiple Hub strategies.
- Neither primary sizing, strategy weights, Frozen Original Hybrid, nor broker permissions may be changed just to make a research track visible.
- A Put track becoming eligible for production sizing requires a separate, explicit integration change: persistent position/leg records, one shared multi-strategy risk allocator, simultaneous-position reservation/release, assignment and deliverable handling, path/stress risk, source evidence, and cross-layer regression tests.

## Required regression invariants

1. The main terminal visibly exposes all three research routes above without requiring users to hunt through a collapsed generic research table.
2. Direct links select the requested QQQ_PUT chain / Hub mode **and N:1 direction** on load. Direct-link routing must not seed, invent, or authenticate quotes.
3. Both N:1 directions have their own visible direct entry and remain separately tested. The app must not silently replace one orientation with the other.
4. The primary engine must continue to have exactly two `mainBudgetEligible: true` option strategies until separately approved.
5. README, Hub notice copy and tests must state the same integration boundary. A statement that all Hub structures share one fully wired pool is invalid unless there is actually a simultaneous allocator and reservation write-back.
