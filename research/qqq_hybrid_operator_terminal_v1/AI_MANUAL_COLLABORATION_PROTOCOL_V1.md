# Manual AI Collaboration Protocol V1 — QQQ Hybrid

Status: research-branch operating contract. It is a repeatable human-in-the-loop process, not a broker integration and not a guarantee of investment performance.

## Objective

Let an operator provide the APP's measured state to an AI in a consistent packet. The AI independently checks source quality, contract geometry, arithmetic, capital reconciliation and research evidence, then returns a reasoned review card. The goal is broader applicability and disciplined integration without losing the original strategy boundaries.

## Standard session

1. **Enter account state.** Set NAV to the whole account equity. Set cash pool to only cash that is genuinely uncommitted and available for this plan. Enter current QQQ shares, VXX short shares, existing option contracts, and pending/open orders. For a brand-new $100,000 account, NAV and uncommitted cash are both USD 100,000 and current holdings are zero.
2. **Refresh market state.** Start the V3 read-only terminal, refresh the APP, and check QQQ / VXX / VIX plus dated VX M1/M2. If the required snapshot is missing, stale, or mixed, the result is BLOCKED/HOLD; do not fill a missing price from memory.
3. **Load candidate contracts.** Query QQQ far call-credit and VXX call-credit candidates. The APP's public chain may be delayed or estimated. Before acting, attach a fresh broker option-chain screenshot/CSV that shows exact root/symbol, expiry, strike, Bid/Ask, observation time/timezone, contract multiplier and deliverable. A screenshot fixture is not current data.
4. **Export the packet.** Click “Export AI Review Pack (.md)”. The file includes the current input object, market metadata, all computed rows, capital reconciliation, candidate objects, measurement lockbox and the fixed response contract. Attach it to ChatGPT. Do not include passwords, account identifiers, API keys, access tokens or other secrets.
5. **Review and reconcile.** AI rechecks the arithmetic independently and identifies missing evidence. The operator confirms account state, current broker quotes and contract terms before any manual action. Save the packet and AI review together if you want a reproducible audit record.

## Quantitative measurement contract

### Gate A — Accuracy

- Every displayed market and option quote must include source, as-of timestamp and timezone where available. Distinguish observed broker bid/ask from public delayed/EOD data and model-derived values.
- Both legs in a vertical must share the same actual expiry and be quoted on executable sides: short leg Bid, protective leg Ask. Verify exact contract root, multiplier and deliverable, especially adjusted VXX series.
- Independently recompute net credit, width, max loss, max gain and breakeven. For a standard 100-unit defined-risk vertical: net credit/share = short Bid − long Ask; estimated max loss = (width − net credit/share) × verified multiplier. Do not use this standard formula until deliverable and multiplier are verified.
- Position, option-risk and cash reconciliation errors must be no greater than USD 0.01 after rounding policy is specified. If a source row, fill, price basis, adjustment or multiplier is unknown, mark it UNKNOWN/BLOCKED rather than filling or inferring it.
- Unit tests and ledger reconciliation validate arithmetic only. They do not prove executable fills, model accuracy or positive strategy value.

### Gate B — Generality

- Report the sample window, expected observations, observed observations, missing observations, unmatched NAV dates and last source date, including numerator and denominator.
- Identify development data versus a genuinely untouched holdout. The previously examined 2018–2025 sample is development evidence, not virgin OOS.
- Where sample size allows, report at least five chronological rolling windows and performance by materially different market regimes. Keep every tested variant and failure in the trial ledger.
- Disclose adverse execution-cost stress of at least 1.5× where applicable; do not optimize a parameter after observing the same test outcome and call that test independent.

### Gate C — Integration / incremental value

Use the pre-registered measurement contract already committed to the repository. The current documented alternative objectives are:
- Return enhancement: final OOS net CAGR improves by at least 0.50 percentage points; MaxDD worsens by no more than 1.00 percentage point; Sharpe falls by no more than 0.05.
- Downside protection: OOS MaxDD improves at least 2.00 percentage points and daily-return ES95 improves at least 10%, with CAGR give-up at most 0.50 percentage points.
- Capital deployment: the downside gate passes, or terminal NAV is no worse than 0.50% below baseline and one pre-selected deployment metric improves by the contract's threshold.

These are this project's pre-registered research bars, not universal financial laws. All tracks still require the Accuracy hard gates, Generality evidence, no same-close look-ahead, transparent costs, and human review. If daily marks are incomplete or dates do not pair, CAGR / daily MTM MaxDD / Sharpe / ES95 must be UNAVAILABLE rather than inferred.

## Risk and allocation invariants

- The primary portfolio cash plan reconciles cash reserve, the shared option max-loss envelope, incremental QQQ stock purchases and estimated VXX short-stock margin. Existing stock positions are not re-counted as fresh purchases.
- Only QQQ far call-credit and VXX call-credit share the primary option max-loss pool. VXX put, QQQ research structures, debit trades, long options, and Hub / ratio research packages remain outside the primary budget.
- The VXX margin multiple is an operator-entered estimate, not a maximum-loss guarantee. VXX short stock has unbounded upside loss.
- An ADD/HOLD/REDUCE output is a portfolio-sizing preview. It does not prove expected return and never authorizes an order. Frozen Original Hybrid, main and broker permissions stay unchanged.
- A calculated position capacity is not a recommendation to use every available unit. All portfolio legs must fit within the same cash/risk envelope, and the final allocation must be checked against live broker quotes and margin.

## Required AI response

Return the following, in order:

1. **Gate verdicts:** DATA; CONTRACT; CAPITAL; EXECUTION EVIDENCE; STRATEGY EVIDENCE. Each must be PASS, BLOCK, WAIT, NOT DEMONSTRATED or FAIL as appropriate, with supporting evidence. Never average a hard failure away.
2. **Current regime:** QQQ / VXX / VIX, VX M1/M2, slope calculation, observation timestamps, source freshness and mismatch.
3. **Action table:** current units, computed target, delta and reason. For options, give exact root, expiry, short leg and Bid, protective leg and Ask, quantity, net credit/debit and source timestamps—or explicitly say PENDING.
4. **Risk arithmetic:** width, verified multiplier/deliverable, max profit/loss, breakeven, total max loss and shared pool consumption.
5. **Cash/margin reconciliation:** NAV, uncommitted cash, reserve, stock additions, VXX estimated margin, shared option risk, required capital and remaining cash. Explicitly flag any unexplained discrepancy above USD 0.01.
6. **Counter-evidence and failure modes:** missing data, stale quotes, price basis, spread realism, adjusted contracts, costs, uncovered positions, mismatched dates and evidence that could reverse the decision.
7. **Human action:** choose only BLOCK, WAIT FOR DATA, or ELIGIBLE FOR HUMAN REVIEW. For an eligible review, enumerate what the operator must confirm. No unqualified order-ready BUY signal, and no claim that an order was placed.

## Current research lockbox

The current Far-Call overlay result must be described precisely:
- Accuracy for trade-performance use: BLOCKED. The internal accounting sub-gate passed 1,688 / 1,688 closed rows with USD 0.00 maximum reconciliation error, but source coverage, spot price basis, spread realism and confirmed fills remain blocked.
- Generality: NOT DEMONSTRATED. The repeatedly examined 2018–2025 window is not an untouched holdout; the pinned source stops at 2025-12-15, leaving 11 expected sessions missing and 24 paired NAV dates unmatched.
- Integration: FAILS_CURRENT_BASE_SCREEN for the isolated Far-Call overlay: zero-cost 0.8% NAV max-loss arm had USD -5,646 closed-trade net P&L and USD -5,552 last paired-date NAV difference against a no-call control.
- Scope limitation: the comparison uses a 42% QQQ total-return proxy plus static 58% cash; it is not a complete performance test of the full Frozen Original Hybrid. It does not approve the add-on or prove the whole baseline strategy succeeds or fails.
- Keep Frozen Original Hybrid and main unchanged. No strategy promotion or parameter hunt until the required gates pass.

## Completion definition

A manual session is auditable when its exported pack, the contemporaneous broker quotes/position facts and the AI review agree on source time, exact contracts, capital arithmetic and explicit blockers. A completed export is a communication artifact, not a validated trade or investment outcome. No order is placed by this protocol.
