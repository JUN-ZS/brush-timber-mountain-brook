# SPY Far-Tail In-Holding Risk Trigger — Research V1

> Source-pinned historical EOD replay; no broker connection or live orders.

## 1. Decision question and frozen baseline

- Primary baseline: QQQ LONG PUT 1 : SPY SHORT PUT 3, HOLD_20_OR_DTE_LE_7; existing DTE14/DTE45 arms and five fixed phases retained.
- No hedge is the control. Each hedge arm adds 1 or 3 same-expiry SPY far-OTM PUT contracts only after its first holding-period trigger; the exact selected contract is held to the original base exit date.
- Original positions, entries, exit dates, cadence, and base trade P&L are read-only; the overlay does not delay or alter the base exit.
- Enter at the trigger-date ask and exit at the base position's exact exit-date bid, with $0.05 per option-share per side and $0.65 per contract per side. Displayed size is a gate, not proof of execution.

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

| Arm | Rule | Tail target | Qty | Trigger rate | Outcome coverage | Mean Δ / trade | Worst-trade improvement | Entry debit median across phases |
|---|---|---|---:|---:|---:|---:|---:|---:|
| DTE14 | ANY_OF_THREE_PREDECLARED | TAIL_025_DELTA | 1 | 37.84% | 100.00% | −$7.97 | $248.70 | $1,634.40 |
| DTE14 | ANY_OF_THREE_PREDECLARED | TAIL_025_DELTA | 3 | 37.84% | 99.32% | −$24.19 | $588.10 | $4,903.20 |
| DTE14 | ANY_OF_THREE_PREDECLARED | TAIL_05_DELTA | 1 | 37.84% | 100.00% | −$9.92 | $479.70 | $2,726.40 |
| DTE14 | ANY_OF_THREE_PREDECLARED | TAIL_05_DELTA | 3 | 37.84% | 99.32% | −$29.77 | $1,439.10 | $8,179.20 |
| DTE14 | ANY_OF_THREE_PREDECLARED | TAIL_10_DELTA | 1 | 37.84% | 100.00% | −$12.70 | $891.70 | $5,115.75 |
| DTE14 | ANY_OF_THREE_PREDECLARED | TAIL_10_DELTA | 3 | 37.84% | 99.32% | −$33.50 | $2,675.10 | $15,093.30 |
| DTE14 | PACKAGE_MTM_LOSS_GE_50PCT_SPY_SHORT_CREDIT | TAIL_025_DELTA | 1 | 25.00% | 100.00% | −$4.76 | $248.70 | $1,048.40 |
| DTE14 | PACKAGE_MTM_LOSS_GE_50PCT_SPY_SHORT_CREDIT | TAIL_025_DELTA | 3 | 25.00% | 99.32% | −$15.69 | $588.10 | $3,145.20 |
| DTE14 | PACKAGE_MTM_LOSS_GE_50PCT_SPY_SHORT_CREDIT | TAIL_05_DELTA | 1 | 25.00% | 100.00% | −$4.80 | $479.70 | $1,772.40 |
| DTE14 | PACKAGE_MTM_LOSS_GE_50PCT_SPY_SHORT_CREDIT | TAIL_05_DELTA | 3 | 25.00% | 99.32% | −$14.40 | $1,439.10 | $5,317.20 |
| DTE14 | PACKAGE_MTM_LOSS_GE_50PCT_SPY_SHORT_CREDIT | TAIL_10_DELTA | 1 | 25.00% | 100.00% | −$5.81 | $891.70 | $3,387.05 |
| DTE14 | PACKAGE_MTM_LOSS_GE_50PCT_SPY_SHORT_CREDIT | TAIL_10_DELTA | 3 | 25.00% | 100.00% | −$17.44 | $2,675.10 | $10,161.15 |
| DTE14 | SHORT_PUT_ABS_DELTA_GE_0.35 | TAIL_025_DELTA | 1 | 31.76% | 100.00% | −$6.60 | $176.70 | $1,440.85 |
| DTE14 | SHORT_PUT_ABS_DELTA_GE_0.35 | TAIL_025_DELTA | 3 | 31.76% | 100.00% | −$23.05 | $0.00 | $4,322.55 |
| DTE14 | SHORT_PUT_ABS_DELTA_GE_0.35 | TAIL_05_DELTA | 1 | 31.76% | 100.00% | −$8.03 | $479.70 | $2,363.25 |
| DTE14 | SHORT_PUT_ABS_DELTA_GE_0.35 | TAIL_05_DELTA | 3 | 31.76% | 100.00% | −$24.10 | $1,439.10 | $7,089.75 |
| DTE14 | SHORT_PUT_ABS_DELTA_GE_0.35 | TAIL_10_DELTA | 1 | 31.76% | 100.00% | −$10.00 | $891.70 | $4,485.90 |
| DTE14 | SHORT_PUT_ABS_DELTA_GE_0.35 | TAIL_10_DELTA | 3 | 31.76% | 99.32% | −$26.31 | $2,675.10 | $13,457.70 |
| DTE14 | SPY_ENTRY_DRAWDOWN_GE_5PCT | TAIL_025_DELTA | 1 | 0.68% | 100.00% | −$0.49 | $0.00 | $128.65 |
| DTE14 | SPY_ENTRY_DRAWDOWN_GE_5PCT | TAIL_025_DELTA | 3 | 0.68% | 100.00% | −$1.46 | $0.00 | $385.95 |
| DTE14 | SPY_ENTRY_DRAWDOWN_GE_5PCT | TAIL_05_DELTA | 1 | 0.68% | 100.00% | −$0.68 | $0.00 | $156.65 |
| DTE14 | SPY_ENTRY_DRAWDOWN_GE_5PCT | TAIL_05_DELTA | 3 | 0.68% | 100.00% | −$1.59 | $0.00 | $469.95 |
| DTE14 | SPY_ENTRY_DRAWDOWN_GE_5PCT | TAIL_10_DELTA | 1 | 0.68% | 100.00% | −$1.23 | $0.00 | $298.65 |
| DTE14 | SPY_ENTRY_DRAWDOWN_GE_5PCT | TAIL_10_DELTA | 3 | 0.68% | 100.00% | −$3.68 | $0.00 | $895.95 |
| DTE45 | ANY_OF_THREE_PREDECLARED | TAIL_025_DELTA | 1 | 44.59% | 98.58% | −$25.82 | −$5.30 | $4,249.90 |
| DTE45 | ANY_OF_THREE_PREDECLARED | TAIL_025_DELTA | 3 | 44.59% | 98.58% | −$75.25 | −$15.90 | $12,435.75 |
| DTE45 | ANY_OF_THREE_PREDECLARED | TAIL_05_DELTA | 1 | 44.59% | 100.00% | −$40.70 | $114.70 | $7,238.90 |
| DTE45 | ANY_OF_THREE_PREDECLARED | TAIL_05_DELTA | 3 | 44.59% | 100.00% | −$122.09 | $344.10 | $21,716.70 |
| DTE45 | ANY_OF_THREE_PREDECLARED | TAIL_10_DELTA | 1 | 44.59% | 100.00% | −$64.52 | $717.70 | $13,482.90 |
| DTE45 | ANY_OF_THREE_PREDECLARED | TAIL_10_DELTA | 3 | 44.59% | 100.00% | −$185.59 | $1,632.10 | $39,428.70 |
| DTE45 | PACKAGE_MTM_LOSS_GE_50PCT_SPY_SHORT_CREDIT | TAIL_025_DELTA | 1 | 33.78% | 99.29% | −$20.39 | −$24.30 | $3,332.50 |
| DTE45 | PACKAGE_MTM_LOSS_GE_50PCT_SPY_SHORT_CREDIT | TAIL_025_DELTA | 3 | 33.78% | 99.29% | −$59.70 | −$72.90 | $9,782.55 |
| DTE45 | PACKAGE_MTM_LOSS_GE_50PCT_SPY_SHORT_CREDIT | TAIL_05_DELTA | 1 | 33.78% | 100.00% | −$33.57 | $52.70 | $5,546.85 |
| DTE45 | PACKAGE_MTM_LOSS_GE_50PCT_SPY_SHORT_CREDIT | TAIL_05_DELTA | 3 | 33.78% | 100.00% | −$97.87 | $158.10 | $16,640.55 |
| DTE45 | PACKAGE_MTM_LOSS_GE_50PCT_SPY_SHORT_CREDIT | TAIL_10_DELTA | 1 | 33.78% | 100.00% | −$54.10 | $271.70 | $10,117.85 |
| DTE45 | PACKAGE_MTM_LOSS_GE_50PCT_SPY_SHORT_CREDIT | TAIL_10_DELTA | 3 | 33.78% | 100.00% | −$156.18 | $815.10 | $29,466.60 |
| DTE45 | SHORT_PUT_ABS_DELTA_GE_0.35 | TAIL_025_DELTA | 1 | 43.24% | 98.58% | −$24.55 | −$5.30 | $4,185.60 |
| DTE45 | SHORT_PUT_ABS_DELTA_GE_0.35 | TAIL_025_DELTA | 3 | 43.24% | 98.58% | −$70.88 | −$15.90 | $12,161.85 |
| DTE45 | SHORT_PUT_ABS_DELTA_GE_0.35 | TAIL_05_DELTA | 1 | 43.24% | 100.00% | −$38.71 | $114.70 | $7,137.60 |
| DTE45 | SHORT_PUT_ABS_DELTA_GE_0.35 | TAIL_05_DELTA | 3 | 43.24% | 100.00% | −$116.14 | $344.10 | $20,945.85 |
| DTE45 | SHORT_PUT_ABS_DELTA_GE_0.35 | TAIL_10_DELTA | 1 | 43.24% | 100.00% | −$57.88 | $717.70 | $13,086.60 |
| DTE45 | SHORT_PUT_ABS_DELTA_GE_0.35 | TAIL_10_DELTA | 3 | 43.24% | 100.00% | −$160.34 | $1,632.10 | $36,148.95 |
| DTE45 | SPY_ENTRY_DRAWDOWN_GE_5PCT | TAIL_025_DELTA | 1 | 12.16% | 99.29% | −$7.99 | −$38.30 | $1,449.70 |
| DTE45 | SPY_ENTRY_DRAWDOWN_GE_5PCT | TAIL_025_DELTA | 3 | 12.16% | 100.00% | −$23.97 | −$114.90 | $3,987.15 |
| DTE45 | SPY_ENTRY_DRAWDOWN_GE_5PCT | TAIL_05_DELTA | 1 | 12.16% | 100.00% | −$10.88 | −$35.30 | $2,182.70 |
| DTE45 | SPY_ENTRY_DRAWDOWN_GE_5PCT | TAIL_05_DELTA | 3 | 12.16% | 100.00% | −$32.63 | −$105.90 | $6,548.10 |
| DTE45 | SPY_ENTRY_DRAWDOWN_GE_5PCT | TAIL_10_DELTA | 1 | 12.16% | 100.00% | −$20.37 | $51.70 | $4,017.40 |
| DTE45 | SPY_ENTRY_DRAWDOWN_GE_5PCT | TAIL_10_DELTA | 3 | 12.16% | 100.00% | −$53.53 | $155.10 | $10,233.30 |

## 5. Annual outcomes by entry year

Full annual-by-entry-year results are in holding_annual_by_entry_year.csv. Entry-year grouping keeps the chronology split fixed to the date when the rule had to act, rather than assigning an earlier entry to a later holdout because it exited later.

## 6. Completeness and limitations

- Replay status: **COMPLETED**; selected baseline trades: 3907; trigger rows: 15628; trade/configuration rows: 93768.
- Source chain window: 2018-03-02 to 2025-12-12; option-chain source: anahatsingh-ui/options-dataset-hist at pin 37f6c456fe1a4775c875673fb8ef907d5cd2fd66.
- Source files downloaded and hash/byte verified: 18; baseline ledger hashes matched the original overlay manifest: True.
- EOD quote-side replay is not confirmed fills. Displayed size is not guaranteed liquidity. Costs are modeled, not broker statements.
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
