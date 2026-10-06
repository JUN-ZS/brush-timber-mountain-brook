# STATE OF KNOWLEDGE

## 1. Original Hybrid reference
Prior research cited:
- CAGR +12.7049%
- daily MTM MaxDD -23.1837%
- final NAV ~276,508

Older benchmark:
- CAGR +12.52%
- MaxDD -23.51%
- win rate 56.2%
- PF 1.74
- Sharpe 0.88
- trades 104

These are REFERENCE RESULTS. Current PR #80 explicitly says exact 12.7049 parity is not yet source-certified.

## 2. Original Hybrid architecture
- ~42% QQQ core long
- QQQ far OTM call-credit financing
- VXX short spot carry, ~18% normal and ~10% at high VIX
- VXX short call spread budget ~2%
- shock/backwardation logic reduces/closes VXX seller legs
- QQQ core is normally retained

Later protected-put / downside-convexity strategies are separate families. Do not merge them into the Original Hybrid reconstruction.

## 3. RETRACTED synthetic result
A prior synthetic experiment reported about 20.8% CAGR / -25% MaxDD for 2018–2025. Later review found a material fixed-lot + split-adjusted-price / synthetic pricing problem. This point estimate is RETRACTED and must not be used as a benchmark.

A later conversational table reported:
- QQQ put + VXX put: -1.7% CAGR
- + small QQQ call: +3.3%
- four-leg debit: -1.4%
- VXX put only: +17.1%
- QQQ put only: -32.3%
- QQQ buy-and-hold: +19.1%

These are also unverified conversational results. They are hypotheses only.

## 4. Real historical M1/M2 acquired
File:
`research/data/vx_m1_m2_external_2016_2022.csv`

Coverage:
- 1,540 rows
- 2016-03-01 → 2022-04-08
- Date, VIX, M1, M2

External origin:
`ayoubbensakhria/wqu690/data/vix_futures.csv`

Status:
EXTERNAL_OBSERVED / UNVALIDATED_AGAINST_OFFICIAL_SOURCE

Do not label it Cboe-official until contract-level validation is complete.

## 5. Historical synthetic clues
The full conversation archive contains an older engine prototype with:
- state.vix_m1
- state.vix_m2
- an input `vix_spread_change`
- a scenario function that shifts `simulated.vix_m2` and recomputes term structure.

The archive also contains:
`VXX_t = VXX_{t-1}(1 - 4.67% + 0.542 * ΔVIX_t)`
for 2011–2017 VXX reconstruction. This is a VXX-path reconstruction, NOT M1/M2 reconstruction.

## 6. Current PR #80 terminal
Branch:
`feat/qqq-hybrid-terminal-v2-secondary-vx-golden-20261006`
Head:
`0f6b533958b879fc10fda289a2cc549df8663afa`

Contains OpenD, optional Databento CFE VX, deterministic engine, current→target action flow, roll radar, journal, golden tests, and reconstruction contract.

Current code still has broad DATA BLOCKED behavior when M1/M2 are missing. Future evolution should refine this to PARTIAL / RISK_ONLY / NO_NEW_CARRY without fabricating term structure.

## 7. Important research philosophy
12.5% is a historical observation/reference, not a next-period expectation.
The brain must allow the next realized path to change weights, confidence, strategy eligibility, and expected outcome.
