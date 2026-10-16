# QQQ FAR CALL Listed-Contract EOD Replay — Run #34

**Decision:** keep the overlay research-only. Do not integrate into Frozen Original Hybrid.

**Evidence class:** observed EOD quote sides and derived replay cash flows; **not exchange-confirmed fills**.
**Run:** [Windows self-hosted Actions Run #34](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38085894573)
**Exact source head:** `e3b3b8faab15374941b8a4dc4be448168a1c0f42`
**Scope:** 42% QQQ-core proxy plus QQQ far-call credit-spread overlay. This is not the full QQQ/VXX Hybrid.

## What was verified

- Replay workflow completed successfully on the stated head. The offline regression suite ran **26 tests: all passed**, including missing-chain DTE exit handling and the distinction between conservative zero-wing-Bid marks and exit execution.
- **1,688 / 1,688 closed-trade rows** reconciled to entry cash flows less entry costs, exit cash flows and exit costs within **$0.01**; 0 failed and 0 were blocked.
- All eight replay output files were generated and existence-checked on the Windows runner. GitHub artifact upload then failed because the repository artifact-storage quota was full; detail CSVs are not downloadable from this run. The values below are transcribed from the actual completed Actions log.
- Source Parquet pins were hash-verified. Observed option-chain data cover **2018-03-01 to 2025-12-15**; the requested range ends 2025-12-31.

## Markability diagnostic

| Mark status | Sessions |
|---|---:|
| Ordinary valid side mark | 1,684 |
| Conservative zero-wing-Bid floor mark | 263 |
| Short contract row missing | 5 |
| Short Ask missing / non-positive | 8 |
| Core total-return price missing | 11 |

The base-cost scenario has **24 position-mark sessions still missing**, compared with 273 in Run #31. The 263 zero-wing-Bid cases are not executable-fill evidence: the long wing is valued at a conservative zero floor for NAV marking, while an attempted exit still requires an admissible quote. The remaining 5 missing contract rows, 8 invalid short Ask marks and 11 missing core-price sessions are not imputed or forward-filled.

## Paired scenario results

All figures are USD closed-trade net P&L. Each row is an independent replay; do not add scenarios together. Slippage is a hypothetical adverse amount per leg; commission is a hypothetical amount per contract per side.

| Budget interpretation | Slippage / leg | Commission / contract / side | Opened | Closed | Closed-trade net P&L | Missing marks |
|---|---:|---:|---:|---:|---:|---:|
| 0.8% NAV maximum-loss | $0.000 | $0.00 | 106 | 105 | $-5,646.00 | 24 |
| 0.8% NAV maximum-loss | $0.000 | $0.65 | 106 | 105 | $-6,068.20 | 24 |
| 0.8% NAV maximum-loss | $0.025 | $0.00 | 107 | 106 | $-6,730.00 | 24 |
| 0.8% NAV maximum-loss | $0.025 | $0.65 | 107 | 106 | $-7,185.00 | 24 |
| 0.8% NAV maximum-loss | $0.050 | $0.00 | 107 | 106 | $-8,566.00 | 24 |
| 0.8% NAV maximum-loss | $0.050 | $0.65 | 107 | 106 | $-9,013.60 | 24 |
| 0.8% NAV maximum-loss | $0.100 | $0.00 | 108 | 108 | $-11,268.00 | 13 |
| 0.8% NAV maximum-loss | $0.100 | $0.65 | 108 | 108 | $-11,369.20 | 14 |
| 1.2% NAV Credit (legacy) | $0.000 | $0.00 | 106 | 105 | $-66,685.00 | 24 |
| 1.2% NAV Credit (legacy) | $0.000 | $0.65 | 106 | 105 | $-73,538.20 | 24 |
| 1.2% NAV Credit (legacy) | $0.025 | $0.00 | 107 | 106 | $-85,711.00 | 24 |
| 1.2% NAV Credit (legacy) | $0.025 | $0.65 | 107 | 106 | $-91,838.60 | 24 |
| 1.2% NAV Credit (legacy) | $0.050 | $0.00 | 107 | 106 | $-112,071.00 | 24 |
| 1.2% NAV Credit (legacy) | $0.050 | $0.65 | 107 | 106 | $-118,899.60 | 24 |
| 1.2% NAV Credit (legacy) | $0.100 | $0.00 | 107 | 107 | $-144,091.00 | 13 |
| 1.2% NAV Credit (legacy) | $0.100 | $0.65 | 97 | 97 | $-148,175.40 | 12 |

## Base-cost exit attribution

Source maximum-loss budget, zero extra slippage and zero commission; 105 closed spreads.

| Exit reason | Trades | Net P&L | Win fraction |
|---|---:|---:|---:|
| DTE ≤ 7 | 62 | -$4,746.00 | 46.8% |
| Expiry intrinsic-settlement proxy | 34 | +$3,250.00 | 100.0% |
| Loss stop at ≤ −0.55 × scenario max loss | 9 | -$4,150.00 | 0.0% |
| **Total** | **105** | **-$5,646.00** | — |

The expiry group uses intrinsic value derived from observed raw close (or an explicitly tagged prior-session fallback); it is not confirmed exercise or a proven fill. The loss-stop group is especially costly per trade, but this descriptive attribution does not by itself prove the exit threshold caused the losses.

## Interpretation and next decision

1. The mark-coverage change is a **measurement correction**, not alpha. The base-cost closed-trade sum is now **−$5,646**, compared with −$4,255 in Run #30. The trade count and exit lifecycle changed when DTE exits were correctly signalled on sessions with missing option chains, so this difference is not a clean same-policy comparison.
2. All 16 tested budget/cost combinations remain negative. The 1.2% NAV Credit budget is not equivalent to a maximum-loss budget and produces materially larger sizing and losses.
3. **No strategy performance approval:** no CAGR, daily MTM MaxDD, Sharpe or ES95 is accepted. EOD data are not confirmed fills; 11 core-price dates remain missing at the end of the source window, and some internal contract rows are missing.
4. Do not tune the stop threshold to rescue this result. Next research should compare a frozen no-overlay control against the overlay with strictly paired dates/capital flows, and test the existing exit rules as pre-declared alternatives with mark/fill feasibility kept separate. Because 2018–2025 has already been inspected, this remains DEVELOPMENT/REVISIT, not virgin holdout.
5. No VXX option history is included. Frozen Original Hybrid, `main`, live sizing and broker-order permissions remain unchanged.
