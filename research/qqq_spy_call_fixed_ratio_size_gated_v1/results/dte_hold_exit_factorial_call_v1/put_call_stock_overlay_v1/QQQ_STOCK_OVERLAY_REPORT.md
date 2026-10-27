# PUT + CALL paired replay with a QQQ-stock overlay

- Option replay window: 2018-03-01 to 2025-12-15 (7.792 calendar years).
- Options: QQQ LONG PUT 1 : SPY SHORT PUT 6 at target abs-Delta 0.25; QQQ LONG CALL 1 : SPY SHORT CALL 6 at target abs-Delta 0.20.
- Both option baskets use same-expiry legs internally; PUT and CALL baskets are paired only when signal date, expiry, and actual entry date all match.
- Exit policy: HOLD_20_OR_DTE_LE_7; a basket reserves one combined slot until both option trades resolve. At most one paired basket is active; unresolved baskets reserve the slot through source end.
- Unmatched PUT-only or CALL-only entries are skipped as a pair. No independent annual medians are added.
- Option trade P&L is the existing source-pinned quote-side estimate after the study's fixed slippage and commissions; unresolved option-leg P&L is not marked.
- HUB QQQ history: yahoo-chart interval=1d adjclose windows, as-of 2026-09-04; adjusted-close ratio is used as a total-return proxy.
- Current value input: USD 63,694.00; current reference price USD 712.20 (2026-10-26; StockAnalysis QQQ history, close on 2026-10-26); implied shares approx. 89.4327.
- Historical stock position under that current-value basis: estimated start value USD 14,709.90; end total-return wealth USD 57,460.87; stock total-return P&L USD 42,750.98 (290.63% on starting value).
- Alternative interpretation: investing USD 63,694.00 on 2018-03-01 and holding through 2025-12-15 gives estimated stock total-return P&L USD 185,112.14. This is not the same as a current holding worth USD 63,694.
- QQQ stock-only max drawdown in the study window, based on the HUB adjusted-close series: -35.12%. This is not the combined portfolio drawdown.

## DTE summary (phase aggregation)

| DTE target | Median annual P&L of completed paired option sets | Phase range | Median stock + completed-pair P&L (current-value share basis) | Median stock + resolved option-leg P&L (current-value share basis) | Median admitted sets | Median matched pairs skipped by capacity | Median unresolved option legs | Worst completed pair across phases |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 20 | 83.27 | 0.00–402.13 | 43,399.78 | 41,956.68 | 2.0 | 175.0 | 1.0 | -1,118.20 |
| 30 | 0.00 | 0.00–417.82 | 42,750.98 | 41,407.88 | 1.0 | 185.0 | 1.0 | 1,035.80 |
| 45 | 577.65 | -411.68–3,060.58 | 47,251.98 | 40,266.68 | 7.0 | 160.0 | 1.0 | -3,879.20 |
| 60 | 4,132.95 | 1,418.08–7,692.48 | 74,954.58 | 74,995.48 | 43.0 | 69.0 | 1.0 | -8,376.20 |

## All phase results

| DTE | Phase | Matched pairs | Admitted pairs | Capacity skipped | Fully resolved pairs | Unresolved pairs | Pair net P&L (completed only) | Realized option-leg P&L (unresolved legs excluded) | Stock P&L (current-value share basis) | Stock + completed-pair P&L | Stock + resolved-leg P&L |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 20 | 0 | 183 | 9 | 174 | 8 | 1 | 3,133.40 | 3,342.30 | 42,750.98 | 45,884.38 | 46,093.28 |
| 20 | 2 | 177 | 2 | 175 | 1 | 1 | 648.80 | -794.30 | 42,750.98 | 43,399.78 | 41,956.68 |
| 20 | 4 | 183 | 1 | 182 | 0 | 1 | 0.00 | -3,156.10 | 42,750.98 | 42,750.98 | 39,594.88 |
| 20 | 6 | 183 | 1 | 182 | 0 | 1 | 0.00 | -3,784.10 | 42,750.98 | 42,750.98 | 38,966.88 |
| 20 | 8 | 179 | 7 | 172 | 6 | 1 | 2,354.80 | 2,750.70 | 42,750.98 | 45,105.78 | 45,501.68 |
| 30 | 0 | 188 | 3 | 185 | 2 | 1 | 3,255.60 | 2,964.50 | 42,750.98 | 46,006.58 | 45,715.48 |
| 30 | 2 | 181 | 1 | 180 | 0 | 1 | 0.00 | 304.90 | 42,750.98 | 42,750.98 | 43,055.88 |
| 30 | 4 | 189 | 1 | 188 | 0 | 1 | 0.00 | -1,343.10 | 42,750.98 | 42,750.98 | 41,407.88 |
| 30 | 6 | 189 | 1 | 188 | 0 | 1 | 0.00 | -5,110.10 | 42,750.98 | 42,750.98 | 37,640.88 |
| 30 | 8 | 184 | 1 | 183 | 0 | 1 | 0.00 | -3,038.10 | 42,750.98 | 42,750.98 | 39,712.88 |
| 45 | 0 | 176 | 6 | 170 | 5 | 1 | 4,501.00 | 5,445.90 | 42,750.98 | 47,251.98 | 48,196.88 |
| 45 | 2 | 166 | 7 | 159 | 6 | 1 | 4,271.80 | -2,484.30 | 42,750.98 | 47,022.78 | 40,266.68 |
| 45 | 4 | 173 | 7 | 166 | 6 | 1 | 4,827.80 | -5,102.30 | 42,750.98 | 47,578.78 | 37,648.68 |
| 45 | 6 | 165 | 5 | 160 | 4 | 1 | -3,207.80 | -12,656.90 | 42,750.98 | 39,543.18 | 30,094.08 |
| 45 | 8 | 169 | 32 | 137 | 31 | 1 | 23,847.80 | 20,817.70 | 42,750.98 | 66,598.78 | 63,568.68 |
| 60 | 0 | 111 | 55 | 56 | 54 | 1 | 59,939.20 | 59,939.20 | 42,750.98 | 102,690.18 | 102,690.18 |
| 60 | 2 | 112 | 43 | 69 | 42 | 1 | 32,203.60 | 32,244.50 | 42,750.98 | 74,954.58 | 74,995.48 |
| 60 | 4 | 114 | 55 | 59 | 55 | 0 | 30,619.00 | 30,619.00 | 42,750.98 | 73,369.98 | 73,369.98 |
| 60 | 6 | 103 | 13 | 90 | 12 | 1 | 11,049.60 | -13,842.50 | 42,750.98 | 53,800.58 | 28,908.48 |
| 60 | 8 | 114 | 42 | 72 | 41 | 1 | 40,779.80 | 41,065.70 | 42,750.98 | 83,530.78 | 83,816.68 |

## Interpretation limits

- These are additive USD outcomes, not CAGR, account return, or proof that $63,694 covers the options' buying-power requirements.
- The share overlay uses a total-return adjusted-close ratio; it estimates dividends/distributions reinvested. The option legs use raw underlying close for contract selection and separate EOD bid/ask quotes.
- The market price used to infer current share count is a dated reference, so the implied share count is approximate rather than a live account-position read.
- A QQQ share holding is not contractual coverage for SPY short puts or SPY short calls. SPY assignment cash and short-call delivery obligations remain separate and unmodeled.
- Unresolved option legs are excluded from resolved P&L and remain an uncertainty. A full combined max drawdown cannot be calculated from the trade ledger alone because it does not preserve the complete daily marked P&L for all open options.
- Pair net P&L requires both PUT and CALL trades to resolve; the realized-option-leg column separately counts a leg that closed even if its paired leg remains unresolved. These two totals intentionally differ.
- This is an isolated research artifact. No main merge and no broker orders.

Files: put_call_stock_overlay_by_phase.csv, put_call_stock_overlay_config_summary.csv, put_call_stock_overlay_selected_pairs.csv.
