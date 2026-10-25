# Weekly SPY -2% drop trigger + QQQ positive correlation — conditional path REF

Window 2018-03-01 to 2025-12-15; 7.792 years. Trigger: SPY rolling 5-session close return crosses from above -2% to <= -2%, and prior 60-session QQQ/SPY daily-return Pearson correlation is positive.

Entry contracts are selected at the signal close; entry is next common session subject to exact-contract quote and displayed-size gates. Same DTE14 premium-matched contract selector and base costs as the existing REF. Exit: HOLD_20_OR_DTE_LE_7.

## Trigger/run coverage

| Ratio | Scheduled daily opportunities | Qualified signals | Entered cohorts | Entry skips | Resolved | Unresolved |
|---|---:|---:|---:|---:|---:|---:|
| 1:3 | 1959 | 99 | 99 | 0 | 99 | 0 |
| 1:6 | 1959 | 99 | 99 | 0 | 99 | 0 |
| 2:6 half-premium | 1959 | 99 | 99 | 0 | 99 | 0 |
| 2:6 same contract | 1959 | 99 | 99 | 0 | 99 | 0 |

## QQQ unit premium and hedge sizing

The 2:6 half-premium arm selects an alternative QQQ put at approximately half the signal-time Ask of the 1:6 reference contract, locks the reference expiry and SPY contract, and buys two contracts; its QQQ Delta is unconstrained. The separate 2:6 same-contract arm buys two copies of the exact QQQ contract chosen by the 1:6 reference selector, subject to displayed size. Entry unit premium and total debit use next-session entry Ask quotes.
The aggregate Delta-equivalent column is the mean of abs(Delta per QQQ contract) × QQQ contract count × 100. It is only a first-order local sensitivity proxy, not equivalent tail convexity or guaranteed hedge value.

| Ratio | QQQ long : SPY short | QQQ reference multiple | Mean QQQ premium / contract | Median QQQ premium / contract | Mean total QQQ debit | Mean SPY short credit | Mean abs(Delta) / contract | Aggregate Delta-equivalent | Mean unit-premium reduction vs 1:6 | Paired N | QQQ/SPY/expiry match vs 1:6 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1:3 | 1 : 3 | 6x | USD 1,082.72 | USD 1,011.00 | USD 1,082.72 | USD 853.85 | 0.670 | 67.0 shares | -0.42% | 99 | 100.0%/100.0%/100.0% |
| 1:6 | 1 : 6 | 6x | USD 1,082.97 | USD 1,011.00 | USD 1,082.97 | USD 1,708.06 | 0.670 | 67.0 shares | 0.00% | 99 | 100.0%/100.0%/100.0% |
| 2:6 half-premium | 2 : 6 | 6x | USD 539.80 | USD 458.00 | USD 1,079.60 | USD 1,706.91 | 0.403 | 80.7 shares | 52.40% | 99 | 0.0%/100.0%/100.0% |
| 2:6 same contract | 2 : 6 | 6x | USD 1,076.21 | USD 1,011.00 | USD 2,152.42 | USD 1,685.27 | 0.669 | 133.8 shares | 0.38% | 99 | 100.0%/100.0%/100.0% |

## Conditional P&L (base strategy, no TAIL)

Annual-average episode sum = each group's episode P&L / the full 7.792-year study window. This is explicitly not account CAGR. The whole-period no-breach groups are hindsight counterfactual subsets, as requested.

| Ratio | Condition | N resolved | Sum episode P&L | Mean / episode | Median / episode | Win rate | Worst episode | Annual-average episode sum |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1:3 | all_resolved_weekly_trigger_trades | 99 | USD -8,359.80 | USD -84.44 | USD -50.20 | 44.44% | USD -8,355.20 | USD -1,072.86 |
| 1:3 | whole_holding_period_SPY_ATH_drawdown_not_below_minus_10pct | 53 | USD 2,435.40 | USD 45.95 | USD -42.20 | 43.40% | USD -1,090.20 | USD 312.55 |
| 1:3 | whole_holding_period_SPY_ATH_drawdown_not_below_minus_15pct | 72 | USD 3,444.60 | USD 47.84 | USD -50.20 | 41.67% | USD -1,090.20 | USD 442.06 |
| 1:3 | whole_holding_period_SPY_return_from_entry_not_below_minus_10pct | 97 | USD 2,364.60 | USD 24.38 | USD -42.20 | 45.36% | USD -3,209.20 | USD 303.46 |
| 1:3 | whole_holding_period_SPY_return_from_entry_not_below_minus_15pct | 98 | USD -5,990.60 | USD -61.13 | USD -46.20 | 44.90% | USD -8,355.20 | USD -768.81 |
| 1:6 | all_resolved_weekly_trigger_trades | 99 | USD -2,341.90 | USD -23.66 | USD 246.90 | 70.71% | USD -21,700.10 | USD -300.55 |
| 1:6 | whole_holding_period_SPY_ATH_drawdown_not_below_minus_10pct | 53 | USD 16,189.70 | USD 305.47 | USD 260.90 | 75.47% | USD -4,799.10 | USD 2,077.71 |
| 1:6 | whole_holding_period_SPY_ATH_drawdown_not_below_minus_15pct | 72 | USD 21,705.80 | USD 301.47 | USD 258.40 | 75.00% | USD -4,799.10 | USD 2,785.62 |
| 1:6 | whole_holding_period_SPY_return_from_entry_not_below_minus_10pct | 97 | USD 26,525.30 | USD 273.46 | USD 255.90 | 72.16% | USD -7,968.10 | USD 3,404.13 |
| 1:6 | whole_holding_period_SPY_return_from_entry_not_below_minus_15pct | 98 | USD 4,825.20 | USD 49.24 | USD 251.40 | 71.43% | USD -21,700.10 | USD 619.24 |
| 2:6 half-premium | all_resolved_weekly_trigger_trades | 99 | USD -5,207.60 | USD -52.60 | USD 235.60 | 67.68% | USD -18,148.40 | USD -668.32 |
| 2:6 half-premium | whole_holding_period_SPY_ATH_drawdown_not_below_minus_10pct | 53 | USD 12,734.80 | USD 240.28 | USD 239.60 | 73.58% | USD -3,850.40 | USD 1,634.33 |
| 2:6 half-premium | whole_holding_period_SPY_ATH_drawdown_not_below_minus_15pct | 72 | USD 15,333.20 | USD 212.96 | USD 242.60 | 70.83% | USD -3,850.40 | USD 1,967.79 |
| 2:6 half-premium | whole_holding_period_SPY_return_from_entry_not_below_minus_10pct | 97 | USD 19,407.20 | USD 200.07 | USD 239.60 | 69.07% | USD -6,802.40 | USD 2,490.63 |
| 2:6 half-premium | whole_holding_period_SPY_return_from_entry_not_below_minus_15pct | 98 | USD 1,258.80 | USD 12.84 | USD 237.60 | 68.37% | USD -18,148.40 | USD 161.55 |
| 2:6 same contract | all_resolved_weekly_trigger_trades | 99 | USD -17,791.60 | USD -179.71 | USD -100.40 | 44.44% | USD -16,710.40 | USD -2,283.29 |
| 2:6 same contract | whole_holding_period_SPY_ATH_drawdown_not_below_minus_10pct | 53 | USD 3,938.80 | USD 74.32 | USD -84.40 | 43.40% | USD -2,516.40 | USD 505.49 |
| 2:6 same contract | whole_holding_period_SPY_ATH_drawdown_not_below_minus_15pct | 72 | USD 5,817.20 | USD 80.79 | USD -106.40 | 41.67% | USD -2,516.40 | USD 746.55 |
| 2:6 same contract | whole_holding_period_SPY_return_from_entry_not_below_minus_10pct | 97 | USD 3,657.20 | USD 37.70 | USD -84.40 | 45.36% | USD -6,418.40 | USD 469.35 |
| 2:6 same contract | whole_holding_period_SPY_return_from_entry_not_below_minus_15pct | 98 | USD -13,053.20 | USD -133.20 | USD -92.40 | 44.90% | USD -16,710.40 | USD -1,675.19 |

## Interpretation

- The weekly 2% drop is an implementable event trigger with positive lagged QQQ/SPY correlation; the whole-period no-breach rule is NOT available at entry.
- SPY ATH drawdown uses a running close high-water mark from the earliest source date (1999), avoiding a reset at 2018. Intraday breaches may be missed.
- Episodes overlap and portfolio capital/margin are not constrained; these metrics cannot be converted to compound account CAGR.
- Daily close return correlation was 0.935952 in the full historical period; this descriptive full-period result is not used as a look-ahead gate.

Artifacts: episode_classification.csv, summary.json. The 2:6 arm is compared with the original 1:6 arm on the same signal dates; no orders or main-branch changes.
