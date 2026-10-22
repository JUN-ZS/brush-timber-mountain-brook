# QQQ LONG PUT / SPY SHORT PUT Cross-Underlying Replay V1

**Status:** isolated research only. Default what-if is LONG 4 QQQ puts : SHORT 5 SPY puts. Both contract counts are configurable inputs, not a recommendation.

## Question

Measure combined P&L and historical win rate for QQQ long puts against SPY short puts using each leg's own listed contract and quote path. This differs from a QQQ-only put ratio: QQQ and SPY have different prices, volatility surfaces, premiums, and returns. Equal percentage moves in the two ETFs do not imply equal option P&L.

## Frozen replay convention

- Source: public preservation mirror anahatsingh-ui/options-dataset-hist. Every annual QQQ/SPY Parquet file and both underlying-price files must match pinned Git blob SHA and exact byte count before use.
- Default window: 2018-03-01 through 2025-12-15, the latest option-chain date established in the repository's existing QQQ audit.
- Both put chains must be present on the signal date. Select actual standard-root QQQ and SPY puts with a common expiration in 30–60 calendar DTE; choose expiry nearest 45 DTE, then each leg absolute Delta nearest 0.25 within 0.10–0.50. This is a declared measurement convention, not an optimized signal.
- Enter no earlier than the next common observed underlying session using the exact selected IDs: buy QQQ LONG PUT at Ask and sell SPY SHORT PUT at Bid. Require displayed size for requested quantity. No replacement contracts or forward-filling.
- Default what-if: LONG 4 QQQ puts and SHORT 5 SPY puts, multiplier 100. Cohorts are non-overlapping: wait at least 45 sessions from signal and until every exit-policy clone from the prior cohort closes.
- Compare EOD exit signals at holding session 5, 10, 20 and DTE <= 7. A signal executes only at a later observed session with valid quote sides and enough close-side size. Missing quotes defer action; no valid close by expiry/source end remains UNRESOLVED.
- Close QQQ longs at Bid and buy back SPY shorts at Ask. Base-cost convention is $0.05 per option share per side plus $0.65 commission per contract per side. Recompute net win rates across zero/base/adverse cost scenarios.
- The equal-percentage expiry-shock grid applies each hypothetical percentage move independently to QQQ and SPY from each real entry spot. It uses intrinsic-value payoff, charges entry-side slippage/commission once, and does not assume an exit trade. Exercise/assignment charges, financing, taxes, broker margin, forced liquidation, and interim path are not modeled. This is not historical win-rate evidence.

## Required report

Contract IDs, entry/exit dates, expiry, strikes, deltas, leg quote sides and quantities; selected signals, entries/skips, resolved/unresolved trades, missing marks and exit delays; resolved-only win-rate numerator/denominator and nominal Wilson 95% interval; combined net P&L and gross leg attribution; expectancy, median, best/worst, profit factor; cost sensitivity; QQQ-return × SPY-return scenario matrix; source coverage and SHA manifest.

## Interpretation boundaries

EOD snapshots are not confirmed fills or authenticated OPRA tick timestamps. Displayed size is a screening gate, not proof of multi-leg execution. Nominal Wilson intervals do not correct for regime clustering, dependence, or prior research selection. No taxes, financing, broker margin, assignment, forced liquidation, or intraday path is modeled. Premium credit is not a maximum-loss budget; SPY short-put tail risk can dominate even if the QQQ long put appreciates.

This branch must not mutate the Frozen Original Hybrid, live sizing, app action targets, broker credentials, order paths, or deployment permissions.
