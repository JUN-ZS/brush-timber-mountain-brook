# QQQ Event-Driven Risk-Budget Account Replay V1

**Status: research only. No broker orders, no HUB execution, and no Frozen Original Hybrid policy change.**

- Run ID: 39041334471; tested SHA: 4b59a5e4665b316604686f5aadbe8be583979515.- Source window: 2018-03-01 to 2025-12-15; 1960 sessions and 28 event signals.
- Starting NAV: USD 100,000; fixed QQQ Core shares initially funded with 42% of NAV; no dividends or rebalancing.
- Every option account is independently sized from the prior complete NAV at a 0.5%, 1%, or 2% terminal-tail budget. Units are capped by displayed entry-side depth and conservative free-cash/reserve arithmetic.
- Exit signal is after 10 observed sessions; exact-ID close can defer up to 3 observed sessions. Missing/invalid quotes and insufficient displayed size are not forward-filled.

## Account results

| Strategy | Tail budget | Costs | Final NAV USD | CAGR % | Observed MaxDD % | Worst year % | Entries | Exits | Blocked entries | Incomplete marks | NAV recon max USD |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| CORE_ONLY | — | NONE | 213745.3 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 0 | 0 | 0.0 |
| CALL_DEBIT_50D_10D | 0.5% | BASE | 213735.1 | 10.2391 | -22.9557 | -21.0989 | 2 | 2 | 26 | 0 | 0.0 |
| CALL_DEBIT_50D_10D | 0.5% | STRESS | 213633.7 | 10.2324 | -22.9797 | -21.1222 | 1 | 1 | 27 | 0 | 0.0 |
| CALL_DEBIT_50D_10D | 1.0% | BASE | 216063.7 | 10.3925 | -23.0721 | -21.1183 | 20 | 20 | 8 | 1 | 0.0 |
| CALL_DEBIT_50D_10D | 1.0% | STRESS | 215643.7 | 10.3649 | -23.184 | -21.2291 | 20 | 20 | 8 | 1 | 0.0 |
| CALL_DEBIT_50D_10D | 2.0% | BASE | 217639.9 | 10.4955 | -24.3152 | -21.8533 | 28 | 28 | 0 | 5 | 0.0 |
| CALL_DEBIT_50D_10D | 2.0% | STRESS | 216559.9 | 10.425 | -24.5251 | -22.133 | 28 | 28 | 0 | 5 | 0.0 |
| CALL_DEBIT_PLUS_LONG_PUT_10D | 0.5% | BASE | 213745.3 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| CALL_DEBIT_PLUS_LONG_PUT_10D | 0.5% | STRESS | 213745.3 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| CALL_DEBIT_PLUS_LONG_PUT_10D | 1.0% | BASE | 214777.6 | 10.3079 | -23.0134 | -21.2465 | 13 | 13 | 15 | 1 | 0.0 |
| CALL_DEBIT_PLUS_LONG_PUT_10D | 1.0% | STRESS | 214391.5 | 10.2825 | -23.0881 | -21.3203 | 12 | 12 | 16 | 1 | 0.0 |
| CALL_DEBIT_PLUS_LONG_PUT_10D | 2.0% | BASE | 215556.2 | 10.3592 | -23.7278 | -21.8313 | 24 | 24 | 4 | 2 | 0.0 |
| CALL_DEBIT_PLUS_LONG_PUT_10D | 2.0% | STRESS | 214390.1 | 10.2824 | -24.0195 | -22.1215 | 24 | 24 | 4 | 2 | 0.0 |
| PUT_SHORT_HEAVY_1x1 | 0.5% | BASE | 209654.3 | 9.9667 | -22.984 | -21.3475 | 26 | 26 | 2 | 2 | 0.0 |
| PUT_SHORT_HEAVY_1x1 | 0.5% | STRESS | 208954.3 | 9.9195 | -23.1376 | -21.4997 | 26 | 26 | 2 | 2 | 0.0 |
| PUT_SHORT_HEAVY_1x1 | 1.0% | BASE | 203068.9 | 9.5172 | -23.5053 | -21.9663 | 28 | 28 | 0 | 4 | 0.0 |
| PUT_SHORT_HEAVY_1x1 | 1.0% | STRESS | 201766.1 | 9.4268 | -23.8761 | -22.3342 | 28 | 28 | 0 | 4 | 0.0 |
| PUT_SHORT_HEAVY_1x1 | 2.0% | BASE | 190852.9 | 8.6486 | -24.5138 | -23.1909 | 28 | 28 | 0 | 5 | 0.0 |
| PUT_SHORT_HEAVY_1x1 | 2.0% | STRESS | 189012.3 | 8.5136 | -25.1088 | -23.7856 | 28 | 28 | 0 | 5 | 0.0 |
| PUT_SHORT_HEAVY_1x4 | 0.5% | BASE | 213745.3 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x4 | 0.5% | STRESS | 213745.3 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x4 | 1.0% | BASE | 213745.3 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x4 | 1.0% | STRESS | 213745.3 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x4 | 2.0% | BASE | 213745.3 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x4 | 2.0% | STRESS | 213745.3 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x5 | 0.5% | BASE | 213745.3 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x5 | 0.5% | STRESS | 213745.3 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x5 | 1.0% | BASE | 213745.3 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x5 | 1.0% | STRESS | 213745.3 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x5 | 2.0% | BASE | 213745.3 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x5 | 2.0% | STRESS | 213745.3 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x6 | 0.5% | BASE | 213745.3 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x6 | 0.5% | STRESS | 213745.3 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x6 | 1.0% | BASE | 213745.3 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x6 | 1.0% | STRESS | 213745.3 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x6 | 2.0% | BASE | 213745.3 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x6 | 2.0% | STRESS | 213745.3 | 10.2398 | -22.7794 | -21.0335 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_LONG_HEAVY_2x1 | 0.5% | BASE | 213273.6 | 10.2085 | -22.772 | -21.0266 | 3 | 3 | 25 | 1 | 0.0 |
| PUT_LONG_HEAVY_2x1 | 0.5% | STRESS | 213183.6 | 10.2025 | -22.7805 | -21.0345 | 3 | 3 | 25 | 1 | 0.0 |
| PUT_LONG_HEAVY_2x1 | 1.0% | BASE | 205228.0 | 9.666 | -23.5534 | -22.1237 | 24 | 24 | 4 | 2 | 0.0 |
| PUT_LONG_HEAVY_2x1 | 1.0% | STRESS | 205028.9 | 9.6523 | -23.9656 | -22.1932 | 23 | 23 | 5 | 2 | 0.0 |
| PUT_LONG_HEAVY_2x1 | 2.0% | BASE | 193769.9 | 8.8604 | -24.8415 | -23.3699 | 27 | 27 | 1 | 4 | 0.0 |
| PUT_LONG_HEAVY_2x1 | 2.0% | STRESS | 193917.6 | 8.871 | -24.6534 | -23.1798 | 27 | 27 | 1 | 3 | 0.0 |

## Decision limits

- Risk sizing uses expiry-intrinsic payoff knots, not broker margin models. It cannot cap interim mark-to-market losses, assignment, forced liquidation, early exercise, or multi-leg fill risk.
- Free cash reserved for short-heavy structures is a conservative research proxy, not a claim about actual broker margin.
- MaxDD and CAGR are based on complete daily side-quote liquidation marks; missing marks stay missing and can understate drawdown.
- QQQ Core is price-only, fixed shares funded to 42% of initial NAV; dividends are not included.
- This is a historical screen using options quotes through 2025-12-15. It is not an untouched out-of-sample test and no result authorizes live deployment.
