# Weekly SPY -2% drop trigger + QQQ positive correlation — conditional path REF

Window 2018-03-01 to 2025-12-15; 7.792 years. Trigger: SPY rolling 5-session close return crosses from above -2% to <= -2%, and prior 60-session QQQ/SPY daily-return Pearson correlation is positive.

Entry contracts are selected at the signal close; entry is next common session subject to exact-contract quote and displayed-size gates. Same DTE14 premium-matched contract selector and base costs as the existing REF. Exit: HOLD_20_OR_DTE_LE_7.

## Trigger/run coverage

| Ratio | Scheduled daily opportunities | Qualified signals | Entered cohorts | Entry skips | Resolved | Unresolved |
|---|---:|---:|---:|---:|---:|---:|
| 1:3 | 1959 | 99 | 99 | 0 | 99 | 0 |
| 1:6 | 1959 | 99 | 99 | 0 | 99 | 0 |
| 2:6 | 1959 | 99 | 99 | 0 | 99 | 0 |

## QQQ unit premium and hedge sizing

The 2:6 arm selects an alternative same-expiry QQQ put at approximately half the signal-time Ask of the existing 1:6 reference contract, then buys two contracts. The alternative QQQ Delta is intentionally unconstrained, because cheaper contracts generally change hedge sensitivity. Entry unit premium and total debit are measured from next-session entry Ask quotes.

| Ratio | QQQ long : SPY short | QQQ reference multiple | Mean QQQ premium / contract | Median QQQ premium / contract | Mean total QQQ debit | Mean SPY short credit | Mean QQQ |Delta| at entry | Mean unit-premium reduction vs 1:6 | Paired N |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1:3 | 1 : 3 | 6x | USD 1,082.72 | USD 1,011.00 | USD 1,082.72 | USD 853.85 | 0.670 | -0.42% | 99 |
| 1:6 | 1 : 6 | 6x | USD 1,082.97 | USD 1,011.00 | USD 1,082.97 | USD 1,708.06 | 0.670 | 0.00% | 99 |
| 2:6 | 2 : 6 | 6x | USD 544.75 | USD 458.00 | USD 1,089.49 | USD 1,729.27 | 0.403 | 51.99% | 99 |

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
| 2:6 | all_resolved_weekly_trigger_trades | 99 | USD -1,881.60 | USD -19.01 | USD 239.60 | 67.68% | USD -18,148.40 | USD -241.48 |
| 2:6 | whole_holding_period_SPY_ATH_drawdown_not_below_minus_10pct | 53 | USD 13,510.80 | USD 254.92 | USD 239.60 | 73.58% | USD -3,850.40 | USD 1,733.91 |
| 2:6 | whole_holding_period_SPY_ATH_drawdown_not_below_minus_15pct | 72 | USD 16,829.20 | USD 233.74 | USD 242.60 | 70.83% | USD -3,850.40 | USD 2,159.78 |
| 2:6 | whole_holding_period_SPY_return_from_entry_not_below_minus_10pct | 97 | USD 22,733.20 | USD 234.36 | USD 245.60 | 69.07% | USD -4,652.40 | USD 2,917.47 |
| 2:6 | whole_holding_period_SPY_return_from_entry_not_below_minus_15pct | 98 | USD 4,584.80 | USD 46.78 | USD 242.60 | 68.37% | USD -18,148.40 | USD 588.39 |

## Interpretation

- The weekly 2% drop is an implementable event trigger with positive lagged QQQ/SPY correlation; the whole-period no-breach rule is NOT available at entry.
- SPY ATH drawdown uses a running close high-water mark from the earliest source date (1999), avoiding a reset at 2018. Intraday breaches may be missed.
- Episodes overlap and portfolio capital/margin are not constrained; these metrics cannot be converted to compound account CAGR.
- Daily close return correlation was 0.935952 in the full historical period; this descriptive full-period result is not used as a look-ahead gate.

Artifacts: episode_classification.csv, summary.json. The 2:6 arm is compared with the original 1:6 arm on the same signal dates; no orders or main-branch changes.
