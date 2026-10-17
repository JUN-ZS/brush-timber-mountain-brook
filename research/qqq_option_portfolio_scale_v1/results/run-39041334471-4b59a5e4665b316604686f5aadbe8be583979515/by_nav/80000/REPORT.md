# QQQ Event-Driven Risk-Budget Account Replay V1

**Status: research only. No broker orders, no HUB execution, and no Frozen Original Hybrid policy change.**

- Run ID: 39041334471; tested SHA: 4b59a5e4665b316604686f5aadbe8be583979515.- Source window: 2018-03-01 to 2025-12-15; 1960 sessions and 28 event signals.
- Starting NAV: USD 80,000; fixed QQQ Core shares initially funded with 42% of NAV; no dividends or rebalancing.
- Every option account is independently sized from the prior complete NAV at a 0.5%, 1%, or 2% terminal-tail budget. Units are capped by displayed entry-side depth and conservative free-cash/reserve arithmetic.
- Exit signal is after 10 observed sessions; exact-ID close can defer up to 3 observed sessions. Missing/invalid quotes and insufficient displayed size are not forward-filled.

## Account results

| Strategy | Tail budget | Costs | Final NAV USD | CAGR % | Observed MaxDD % | Worst year % | Entries | Exits | Blocked entries | Incomplete marks | NAV recon max USD |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| CORE_ONLY | — | NONE | 170996.24 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 0 | 0 | 0.0 |
| CALL_DEBIT_50D_10D | 0.5% | BASE | 170996.24 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| CALL_DEBIT_50D_10D | 0.5% | STRESS | 170996.24 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| CALL_DEBIT_50D_10D | 1.0% | BASE | 170381.24 | 10.1888 | -23.5001 | -21.6239 | 10 | 10 | 18 | 1 | 0.0 |
| CALL_DEBIT_50D_10D | 1.0% | STRESS | 170181.24 | 10.1722 | -23.5529 | -21.6755 | 10 | 10 | 18 | 1 | 0.0 |
| CALL_DEBIT_50D_10D | 2.0% | BASE | 171983.24 | 10.3212 | -24.281 | -22.0403 | 28 | 28 | 0 | 1 | 0.0 |
| CALL_DEBIT_50D_10D | 2.0% | STRESS | 171183.24 | 10.2552 | -24.4643 | -22.282 | 28 | 28 | 0 | 1 | 0.0 |
| CALL_DEBIT_PLUS_LONG_PUT_10D | 0.5% | BASE | 170996.24 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| CALL_DEBIT_PLUS_LONG_PUT_10D | 0.5% | STRESS | 170996.24 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| CALL_DEBIT_PLUS_LONG_PUT_10D | 1.0% | BASE | 170084.94 | 10.1642 | -23.1741 | -21.3966 | 7 | 7 | 21 | 1 | 0.0 |
| CALL_DEBIT_PLUS_LONG_PUT_10D | 1.0% | STRESS | 169874.94 | 10.1467 | -23.2423 | -21.4638 | 7 | 7 | 21 | 1 | 0.0 |
| CALL_DEBIT_PLUS_LONG_PUT_10D | 2.0% | BASE | 171261.34 | 10.2617 | -23.976 | -21.9513 | 24 | 24 | 4 | 1 | 0.0 |
| CALL_DEBIT_PLUS_LONG_PUT_10D | 2.0% | STRESS | 170331.34 | 10.1847 | -24.2175 | -22.2607 | 24 | 24 | 4 | 1 | 0.0 |
| PUT_SHORT_HEAVY_1x1 | 0.5% | BASE | 168460.84 | 10.0286 | -23.2232 | -21.468 | 21 | 21 | 7 | 2 | 0.0 |
| PUT_SHORT_HEAVY_1x1 | 0.5% | STRESS | 167980.84 | 9.9883 | -23.3499 | -21.5934 | 21 | 21 | 7 | 2 | 0.0 |
| PUT_SHORT_HEAVY_1x1 | 1.0% | BASE | 163088.84 | 9.5719 | -23.5163 | -21.8907 | 27 | 27 | 1 | 3 | 0.0 |
| PUT_SHORT_HEAVY_1x1 | 1.0% | STRESS | 162784.44 | 9.5457 | -23.9374 | -22.3104 | 27 | 27 | 1 | 3 | 0.0 |
| PUT_SHORT_HEAVY_1x1 | 2.0% | BASE | 153889.84 | 8.7585 | -24.5481 | -23.2028 | 28 | 28 | 0 | 4 | 0.0 |
| PUT_SHORT_HEAVY_1x1 | 2.0% | STRESS | 151753.84 | 8.5636 | -25.0391 | -23.6863 | 28 | 28 | 0 | 4 | 0.0 |
| PUT_SHORT_HEAVY_1x4 | 0.5% | BASE | 170996.24 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x4 | 0.5% | STRESS | 170996.24 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x4 | 1.0% | BASE | 170996.24 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x4 | 1.0% | STRESS | 170996.24 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x4 | 2.0% | BASE | 170996.24 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x4 | 2.0% | STRESS | 170996.24 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x5 | 0.5% | BASE | 170996.24 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x5 | 0.5% | STRESS | 170996.24 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x5 | 1.0% | BASE | 170996.24 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x5 | 1.0% | STRESS | 170996.24 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x5 | 2.0% | BASE | 170996.24 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x5 | 2.0% | STRESS | 170996.24 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x6 | 0.5% | BASE | 170996.24 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x6 | 0.5% | STRESS | 170996.24 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x6 | 1.0% | BASE | 170996.24 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x6 | 1.0% | STRESS | 170996.24 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x6 | 2.0% | BASE | 170996.24 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x6 | 2.0% | STRESS | 170996.24 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_LONG_HEAVY_2x1 | 0.5% | BASE | 170524.54 | 10.2007 | -22.7702 | -21.0249 | 3 | 3 | 25 | 1 | 0.0 |
| PUT_LONG_HEAVY_2x1 | 0.5% | STRESS | 170434.54 | 10.1932 | -22.7808 | -21.0348 | 3 | 3 | 25 | 1 | 0.0 |
| PUT_LONG_HEAVY_2x1 | 1.0% | BASE | 164856.44 | 9.7236 | -24.0482 | -22.2817 | 19 | 19 | 9 | 2 | 0.0 |
| PUT_LONG_HEAVY_2x1 | 1.0% | STRESS | 164196.44 | 9.6672 | -24.1947 | -22.4259 | 19 | 19 | 9 | 2 | 0.0 |
| PUT_LONG_HEAVY_2x1 | 2.0% | BASE | 155436.54 | 8.8982 | -24.7566 | -23.3725 | 27 | 27 | 1 | 2 | 0.0 |
| PUT_LONG_HEAVY_2x1 | 2.0% | STRESS | 154480.24 | 8.812 | -25.131 | -23.7478 | 27 | 27 | 1 | 2 | 0.0 |

## Decision limits

- Risk sizing uses expiry-intrinsic payoff knots, not broker margin models. It cannot cap interim mark-to-market losses, assignment, forced liquidation, early exercise, or multi-leg fill risk.
- Free cash reserved for short-heavy structures is a conservative research proxy, not a claim about actual broker margin.
- MaxDD and CAGR are based on complete daily side-quote liquidation marks; missing marks stay missing and can understate drawdown.
- QQQ Core is price-only, fixed shares funded to 42% of initial NAV; dividends are not included.
- This is a historical screen using options quotes through 2025-12-15. It is not an untouched out-of-sample test and no result authorizes live deployment.
