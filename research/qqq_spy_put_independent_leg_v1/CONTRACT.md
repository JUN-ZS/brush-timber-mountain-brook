# QQQ LONG PUT / SPY SHORT PUT — Independent-Leg Sizing V1

**Research-only.** This add-on does not change the equal-premium replay, application sizing, main branch, broker settings or order behavior.

## Why this study exists

The preceding equal-premium replay chose variable contract quantities for QQQ LONG PUT and SPY SHORT PUT together. That does not answer whether the QQQ long leg has standalone value, whether the SPY short leg has standalone value, and what a fixed-N cross-pair changes.

This study:
1. Runs QQQ LONG PUT alone at N=1 through N=9 contracts.
2. Runs SPY SHORT PUT alone at N=1 through N=9 contracts.
3. Cross-compares each fixed N:M pair with N>=1, M>=1 and N+M<=9 (36 combinations) against the original variable-size equal-premium baseline.

## Frozen inputs and calculations

- Input is the committed V1 trade_episodes.csv and summary.json, pinned by Git blob SHA in the script.
- Reuses selected contract IDs, signal/entry dates and recorded conservative quote-side exit marks from V1; does not reselect options or choose strikes on P&L.
- QQQ LONG PUT gross P&L per contract = (exit QQQ Bid - entry QQQ Ask) x 100.
- SPY SHORT PUT gross P&L per contract = (entry SPY Bid - exit SPY Ask) x 100.
- Base round-trip cost per contract = 2 x $0.05 per share x 100 + 2 x $0.65 commission = $11.30. Zero-cost and adverse-cost sensitivities are included.
- P&L and win rate use resolved episodes only; unresolved episodes remain explicit and are not set to zero.
- The original premium-matched baseline is recalculated using each cohort's actual quantities to support base-cost reconciliation and expectancy comparison.

## Critical limit: fixed N is not certified executable

The source output persists the quotes and per-leg gross P&L but not all entry/exit displayed-size values for every selected contract. The new fixed-N rows therefore cannot verify that each N would have passed quote-depth constraints or could have been filled at the displayed EOD marks. They are counterfactual quote-side sizing comparisons, not verified execution backtests. The original equal-premium baseline alone inherits the source run's entry/exit displayed-size screening. No market-impact model, early assignment, margin, liquidation or financing model is added.

Premium matched means option-premium cash-flow matching only, not equal Delta, underlying notional, maximum loss, collateral or assignment risk. Do not promote the best grid cell as a strategy without independent out-of-sample validation.
