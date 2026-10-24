# SPY Far-Tail In-Holding Risk Trigger — Research V1

> Source-pinned historical EOD replay; no broker connection or live orders.

## 1. Decision question and frozen baseline

- Primary baseline: QQQ LONG PUT 1 : SPY SHORT PUT 3, HOLD_20_OR_DTE_LE_7; existing DTE14/DTE45 arms and five fixed phases retained.
- No hedge is the control. Each hedge arm adds 1 or 3 same-expiry SPY far-OTM PUT contracts only after its first holding-period trigger; the exact selected contract is held to the original base exit date.
- Original positions, entries, exit dates, cadence, and base trade P&L are read-only; the overlay does not delay or alter the base exit.
- Day T uses observed data to evaluate the trigger and select a candidate. Entry is attempted only on the next SPY underlying trading session using that session's exact-contract Ask; same-day EOD fills, fallback quotes and retries are prohibited. Exit uses the original base exit date's exact-contract Bid. Costs are $0.05 per option-share per side plus $0.65 per contract per side; displayed size is not proof of a fill.

## 2. Pre-declared trigger rules

| Rule | Frozen condition | Required current observations |
|---|---|---|
| Short-put Delta | Exact selected SPY short PUT absolute Delta >= 0.35 | Current exact-contract option row, valid bid/ask and Delta |
| SPY drawdown | SPY close >= 5% below actual entry SPY spot | Current-day SPY underlying close; no price forward-fill |
| Package MTM loss | Full-package executable mark-to-close P&L <= -50% of initial gross SPY short-put credit | Same-day QQQ long PUT bid and SPY short PUT ask, valid contracts and sufficient displayed sizes |
| OR composite | First date any of the three rules fires | At least one rule feature available that day |

All rules fire at most once per position, on the first observed qualifying date strictly after entry and strictly before the frozen base exit date. The composite records which component(s) fired. Thresholds were fixed before this run and are not selected by comparing results.
No missing price, Delta, or quote is forward-filled. The package-MTM rule is unavailable when either leg lacks an executable current mark.

## 3. Chronological validation design

- Descriptive / development segment by entry date: 2018-01-01 through 2022-12-31.
- Locked chronological holdout by entry date: 2023-01-01 through 2025-12-31.
- The holdout outcomes must not be used to revise thresholds. Because this repository has analyzed the same broad years for other strategy questions, this is a locked holdout for this trigger family, not a globally virgin data set. Truly untouched forward validation requires later dated option-chain data; the pinned chain ends at the date recorded below.
- Five phase schedules overlap. Cross-phase medians/ranges are robustness summaries, not independent samples or confidence intervals.

## 4. Historical holdout results — mean paired net P&L delta and worst trade

The table below reports medians across the five phases. Delta is conditional strategy mean minus no-hedge mean on exactly the same rows where the conditional realized outcome is known. A failed entry means no hedge was bought and the base result remains; an eligible hedge with missing/undersized exit data makes the conditional realized outcome missing, not zero.

| Arm | Rule | Tail target | Qty | Trigger rate | Outcome coverage | Mean Δ / position | Original worst-trade paired Δ | Difference between minima (unpaired) | Losses improved / flipped positive | Total entry debit, phase median |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| DTE14 | ANY_OF_THREE_PREDECLARED | TAIL_025_DELTA | 1 | 37.84% | 100.00% | −$7.41 | $71.70 | $71.70 | $3.00 / $0.00 | $1,419.25 |
| DTE14 | ANY_OF_THREE_PREDECLARED | TAIL_025_DELTA | 3 | 37.84% | 100.00% | −$19.79 | $215.10 | $20.10 | $3.00 / $0.00 | $4,257.75 |
| DTE14 | ANY_OF_THREE_PREDECLARED | TAIL_05_DELTA | 1 | 37.84% | 100.00% | −$7.15 | $296.70 | $125.70 | $5.00 / $0.00 | $2,398.85 |
| DTE14 | ANY_OF_THREE_PREDECLARED | TAIL_05_DELTA | 3 | 37.84% | 100.00% | −$21.46 | $890.10 | $377.10 | $4.00 / $0.00 | $6,728.55 |
| DTE14 | ANY_OF_THREE_PREDECLARED | TAIL_10_DELTA | 1 | 37.84% | 100.00% | −$8.00 | $578.70 | $285.70 | $9.00 / $0.00 | $4,510.50 |
| DTE14 | ANY_OF_THREE_PREDECLARED | TAIL_10_DELTA | 3 | 37.84% | 99.32% | −$24.01 | $1,736.10 | $566.10 | $9.00 / $0.00 | $12,704.55 |
| DTE14 | PACKAGE_MTM_LOSS_GE_50PCT_SPY_SHORT_CREDIT | TAIL_025_DELTA | 1 | 25.00% | 100.00% | −$4.17 | $6.70 | $6.70 | $2.00 / $0.00 | $932.15 |
| DTE14 | PACKAGE_MTM_LOSS_GE_50PCT_SPY_SHORT_CREDIT | TAIL_025_DELTA | 3 | 25.00% | 100.00% | −$10.03 | $20.10 | $14.10 | $2.00 / $0.00 | $2,796.45 |
| DTE14 | PACKAGE_MTM_LOSS_GE_50PCT_SPY_SHORT_CREDIT | TAIL_05_DELTA | 1 | 25.00% | 100.00% | −$4.60 | $125.70 | $56.70 | $4.00 / $0.00 | $1,670.20 |
| DTE14 | PACKAGE_MTM_LOSS_GE_50PCT_SPY_SHORT_CREDIT | TAIL_05_DELTA | 3 | 25.00% | 100.00% | −$13.79 | $377.10 | $0.00 | $4.00 / $0.00 | $5,010.60 |
| DTE14 | PACKAGE_MTM_LOSS_GE_50PCT_SPY_SHORT_CREDIT | TAIL_10_DELTA | 1 | 25.00% | 100.00% | −$5.11 | $285.70 | $0.00 | $5.00 / $0.00 | $3,497.80 |
| DTE14 | PACKAGE_MTM_LOSS_GE_50PCT_SPY_SHORT_CREDIT | TAIL_10_DELTA | 3 | 25.00% | 100.00% | −$15.33 | $857.10 | $0.00 | $5.00 / $0.00 | $9,344.55 |
| DTE14 | SHORT_PUT_ABS_DELTA_GE_0.35 | TAIL_025_DELTA | 1 | 31.76% | 100.00% | −$6.54 | $0.00 | $0.00 | $2.00 / $0.00 | $1,292.95 |
| DTE14 | SHORT_PUT_ABS_DELTA_GE_0.35 | TAIL_025_DELTA | 3 | 31.76% | 100.00% | −$17.16 | $11.10 | $11.10 | $2.00 / $0.00 | $3,878.85 |
| DTE14 | SHORT_PUT_ABS_DELTA_GE_0.35 | TAIL_05_DELTA | 1 | 31.76% | 100.00% | −$6.95 | $0.00 | $0.00 | $3.00 / $0.00 | $2,092.00 |
| DTE14 | SHORT_PUT_ABS_DELTA_GE_0.35 | TAIL_05_DELTA | 3 | 31.76% | 100.00% | −$20.86 | $0.00 | $0.00 | $3.00 / $0.00 | $5,547.30 |
| DTE14 | SHORT_PUT_ABS_DELTA_GE_0.35 | TAIL_10_DELTA | 1 | 31.76% | 100.00% | −$9.10 | $0.00 | $0.00 | $6.00 / $0.00 | $3,863.75 |
| DTE14 | SHORT_PUT_ABS_DELTA_GE_0.35 | TAIL_10_DELTA | 3 | 31.76% | 99.32% | −$24.44 | $0.00 | $0.00 | $6.00 / $0.00 | $11,037.00 |
| DTE14 | SPY_ENTRY_DRAWDOWN_GE_5PCT | TAIL_025_DELTA | 1 | 0.68% | 100.00% | −$0.11 | $0.00 | $0.00 | $0.00 / $0.00 | $90.65 |
| DTE14 | SPY_ENTRY_DRAWDOWN_GE_5PCT | TAIL_025_DELTA | 3 | 0.68% | 100.00% | −$0.33 | $0.00 | $0.00 | $0.00 / $0.00 | $271.95 |
| DTE14 | SPY_ENTRY_DRAWDOWN_GE_5PCT | TAIL_05_DELTA | 1 | 0.68% | 100.00% | −$0.12 | $0.00 | $0.00 | $0.00 / $0.00 | $114.65 |
| DTE14 | SPY_ENTRY_DRAWDOWN_GE_5PCT | TAIL_05_DELTA | 3 | 0.68% | 100.00% | −$0.35 | $0.00 | $0.00 | $0.00 / $0.00 | $343.95 |
| DTE14 | SPY_ENTRY_DRAWDOWN_GE_5PCT | TAIL_10_DELTA | 1 | 0.68% | 100.00% | −$0.17 | $0.00 | $0.00 | $0.00 / $0.00 | $240.65 |
| DTE14 | SPY_ENTRY_DRAWDOWN_GE_5PCT | TAIL_10_DELTA | 3 | 0.68% | 100.00% | −$0.52 | $0.00 | $0.00 | $0.00 / $0.00 | $721.95 |
| DTE45 | ANY_OF_THREE_PREDECLARED | TAIL_025_DELTA | 1 | 44.59% | 98.58% | −$29.14 | $3.70 | $3.70 | $2.00 / $0.00 | $4,634.25 |
| DTE45 | ANY_OF_THREE_PREDECLARED | TAIL_025_DELTA | 3 | 44.59% | 98.58% | −$82.55 | $11.10 | $11.10 | $2.00 / $0.00 | $12,984.75 |
| DTE45 | ANY_OF_THREE_PREDECLARED | TAIL_05_DELTA | 1 | 44.59% | 100.00% | −$46.17 | $127.70 | $127.70 | $3.00 / $0.00 | $7,941.90 |
| DTE45 | ANY_OF_THREE_PREDECLARED | TAIL_05_DELTA | 3 | 44.59% | 100.00% | −$129.88 | $383.10 | $383.10 | $3.00 / $0.00 | $22,540.80 |
| DTE45 | ANY_OF_THREE_PREDECLARED | TAIL_10_DELTA | 1 | 44.59% | 100.00% | −$73.14 | $735.70 | $735.70 | $6.00 / $0.00 | $14,350.90 |
| DTE45 | ANY_OF_THREE_PREDECLARED | TAIL_10_DELTA | 3 | 44.59% | 100.00% | −$195.57 | $2,207.10 | $575.10 | $6.00 / $0.00 | $40,802.85 |
| DTE45 | PACKAGE_MTM_LOSS_GE_50PCT_SPY_SHORT_CREDIT | TAIL_025_DELTA | 1 | 33.78% | 99.29% | −$22.89 | −$13.30 | −$13.30 | $1.00 / $0.00 | $3,750.15 |
| DTE45 | PACKAGE_MTM_LOSS_GE_50PCT_SPY_SHORT_CREDIT | TAIL_025_DELTA | 3 | 33.78% | 99.29% | −$68.67 | −$39.90 | −$39.90 | $0.00 / $0.00 | $10,848.60 |
| DTE45 | PACKAGE_MTM_LOSS_GE_50PCT_SPY_SHORT_CREDIT | TAIL_05_DELTA | 1 | 33.78% | 100.00% | −$37.97 | $82.70 | $82.70 | $2.00 / $0.00 | $6,381.15 |
| DTE45 | PACKAGE_MTM_LOSS_GE_50PCT_SPY_SHORT_CREDIT | TAIL_05_DELTA | 3 | 33.78% | 100.00% | −$101.41 | $248.10 | $248.10 | $2.00 / $0.00 | $18,312.60 |
| DTE45 | PACKAGE_MTM_LOSS_GE_50PCT_SPY_SHORT_CREDIT | TAIL_10_DELTA | 1 | 33.78% | 100.00% | −$60.86 | $334.70 | $334.70 | $4.00 / $0.00 | $11,512.15 |
| DTE45 | PACKAGE_MTM_LOSS_GE_50PCT_SPY_SHORT_CREDIT | TAIL_10_DELTA | 3 | 33.78% | 100.00% | −$169.26 | $1,004.10 | $575.10 | $4.00 / $0.00 | $31,184.70 |
| DTE45 | SHORT_PUT_ABS_DELTA_GE_0.35 | TAIL_025_DELTA | 1 | 43.24% | 98.58% | −$28.40 | $3.70 | $3.70 | $2.00 / $0.00 | $4,387.60 |
| DTE45 | SHORT_PUT_ABS_DELTA_GE_0.35 | TAIL_025_DELTA | 3 | 43.24% | 98.58% | −$75.18 | $11.10 | $11.10 | $2.00 / $0.00 | $12,461.85 |
| DTE45 | SHORT_PUT_ABS_DELTA_GE_0.35 | TAIL_05_DELTA | 1 | 43.24% | 100.00% | −$44.56 | $127.70 | $127.70 | $3.00 / $0.00 | $7,625.65 |
| DTE45 | SHORT_PUT_ABS_DELTA_GE_0.35 | TAIL_05_DELTA | 3 | 43.24% | 100.00% | −$120.66 | $383.10 | $383.10 | $3.00 / $0.00 | $21,303.00 |
| DTE45 | SHORT_PUT_ABS_DELTA_GE_0.35 | TAIL_10_DELTA | 1 | 43.24% | 100.00% | −$69.32 | $735.70 | $735.70 | $5.00 / $0.00 | $13,916.25 |
| DTE45 | SHORT_PUT_ABS_DELTA_GE_0.35 | TAIL_10_DELTA | 3 | 43.24% | 100.00% | −$183.95 | $2,207.10 | $179.10 | $5.00 / $0.00 | $39,388.80 |
| DTE45 | SPY_ENTRY_DRAWDOWN_GE_5PCT | TAIL_025_DELTA | 1 | 12.16% | 99.29% | −$10.42 | −$26.30 | −$26.30 | $0.00 / $0.00 | $1,870.40 |
| DTE45 | SPY_ENTRY_DRAWDOWN_GE_5PCT | TAIL_025_DELTA | 3 | 12.16% | 99.29% | −$31.25 | −$78.90 | −$78.90 | $0.00 / $0.00 | $5,471.25 |
| DTE45 | SPY_ENTRY_DRAWDOWN_GE_5PCT | TAIL_05_DELTA | 1 | 12.16% | 100.00% | −$15.45 | −$22.30 | −$22.30 | $0.00 / $0.00 | $3,103.40 |
| DTE45 | SPY_ENTRY_DRAWDOWN_GE_5PCT | TAIL_05_DELTA | 3 | 12.16% | 100.00% | −$46.36 | −$66.90 | −$66.90 | $0.00 / $0.00 | $7,817.25 |
| DTE45 | SPY_ENTRY_DRAWDOWN_GE_5PCT | TAIL_10_DELTA | 1 | 12.16% | 100.00% | −$26.85 | $0.00 | $0.00 | $1.00 / $0.00 | $5,520.05 |
| DTE45 | SPY_ENTRY_DRAWDOWN_GE_5PCT | TAIL_10_DELTA | 3 | 12.16% | 100.00% | −$80.56 | $0.00 | −$231.90 | $1.00 / $0.00 | $14,272.20 |

- The exact original worst-trade paired change is computed on the same trade row. The separate difference between minimum outcomes may compare different trades and must not be interpreted as paired improvement.

Do not select a winner solely from the holdout values. These are predeclared comparisons; a later untouched forward sample is required before a strategy-selection claim.

## 5. Annual outcomes by entry year

Full annual-by-entry-year results are in holding_annual_by_entry_year.csv. Entry-year grouping keeps the chronology split fixed to the date when the rule had to act, rather than assigning an earlier entry to a later holdout because it exited later.

## 6. Completeness and limitations

- Replay status: **COMPLETED**; selected baseline trades: 3907; trigger rows: 15628; trade/configuration rows: 93768.
- Source chain window: 2018-03-02 to 2025-12-12; option-chain source: anahatsingh-ui/options-dataset-hist at pin 37f6c456fe1a4775c875673fb8ef907d5cd2fd66.
- Source files downloaded and hash/byte verified: 18; baseline ledger hashes matched the original overlay manifest: True.
- The next-session daily Ask is still an execution-timing proxy rather than a timestamped verified fill. Displayed size is not guaranteed liquidity; costs are modeled, not broker statements.
- Unresolved base positions remain mark-only; their outcomes are not counted as realized P&L.
- Results are not account-level NAV, portfolio MaxDD, broker margin, assignment/early exercise, forced-liquidation, or cross-position capital simulations.
- No threshold tuning, live trading, main-branch merge, or broker order is performed by this research.

## 7. Reproducible outputs

- holding_trigger_events.csv: first trigger date and feature availability per position/rule.
- holding_trade_level.csv: each baseline position × rule × tail target × quantity, paired outcomes and missing-exit handling.
- holding_summary_by_period_phase.csv: train/holdout/full results per phase.
- holding_robustness_by_period.csv: medians and ranges across overlapping phases.
- holding_annual_by_entry_year.csv: outcomes grouped by entry cohort year.
- holding_manifest.json: pinned baseline hashes, source file pins, rule thresholds, output counts and warnings.
