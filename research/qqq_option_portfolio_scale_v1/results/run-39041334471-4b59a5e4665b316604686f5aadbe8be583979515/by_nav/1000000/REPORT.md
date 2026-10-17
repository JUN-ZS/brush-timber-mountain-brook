# QQQ Event-Driven Risk-Budget Account Replay V1

**Status: research only. No broker orders, no HUB execution, and no Frozen Original Hybrid policy change.**

- Run ID: 39041334471; tested SHA: 4b59a5e4665b316604686f5aadbe8be583979515.- Source window: 2018-03-01 to 2025-12-15; 1960 sessions and 28 event signals.
- Starting NAV: USD 1,000,000; fixed QQQ Core shares initially funded with 42% of NAV; no dividends or rebalancing.
- Every option account is independently sized from the prior complete NAV at a 0.5%, 1%, or 2% terminal-tail budget. Units are capped by displayed entry-side depth and conservative free-cash/reserve arithmetic.
- Exit signal is after 10 observed sessions; exact-ID close can defer up to 3 observed sessions. Missing/invalid quotes and insufficient displayed size are not forward-filled.

## Account results

| Strategy | Tail budget | Costs | Final NAV USD | CAGR % | Observed MaxDD % | Worst year % | Entries | Exits | Blocked entries | Incomplete marks | NAV recon max USD |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| CORE_ONLY | — | NONE | 2138791.18 | 10.2486 | -22.796 | -21.049 | 0 | 0 | 0 | 0 | 0.0 |
| CALL_DEBIT_50D_10D | 0.5% | BASE | 2149192.18 | 10.3173 | -23.2233 | -21.3594 | 28 | 28 | 0 | 16 | 0.0 |
| CALL_DEBIT_50D_10D | 0.5% | STRESS | 2146266.98 | 10.298 | -23.2455 | -21.396 | 28 | 28 | 0 | 15 | 0.0 |
| CALL_DEBIT_50D_10D | 1.0% | BASE | 2163898.58 | 10.4139 | -23.4744 | -21.3645 | 28 | 28 | 0 | 43 | 0.0 |
| CALL_DEBIT_50D_10D | 1.0% | STRESS | 2157265.78 | 10.3704 | -23.5981 | -21.5155 | 28 | 28 | 0 | 43 | 0.0 |
| CALL_DEBIT_50D_10D | 2.0% | BASE | 2183671.38 | 10.5428 | -23.5761 | -21.0701 | 28 | 28 | 0 | 83 | 0.0 |
| CALL_DEBIT_50D_10D | 2.0% | STRESS | 2172660.38 | 10.4711 | -23.7913 | -21.358 | 28 | 28 | 0 | 82 | 0.0 |
| CALL_DEBIT_PLUS_LONG_PUT_10D | 0.5% | BASE | 2142991.98 | 10.2764 | -23.0307 | -21.2683 | 24 | 24 | 4 | 13 | 0.0 |
| CALL_DEBIT_PLUS_LONG_PUT_10D | 0.5% | STRESS | 2139793.68 | 10.2552 | -23.1185 | -21.3557 | 24 | 24 | 4 | 13 | 0.0 |
| CALL_DEBIT_PLUS_LONG_PUT_10D | 1.0% | BASE | 2148011.78 | 10.3095 | -23.2551 | -21.3522 | 24 | 24 | 4 | 29 | 0.0 |
| CALL_DEBIT_PLUS_LONG_PUT_10D | 1.0% | STRESS | 2141254.28 | 10.2649 | -23.3873 | -21.5284 | 24 | 24 | 4 | 29 | 0.0 |
| CALL_DEBIT_PLUS_LONG_PUT_10D | 2.0% | BASE | 2154391.28 | 10.3515 | -23.3414 | -21.1856 | 24 | 24 | 4 | 64 | 0.0 |
| CALL_DEBIT_PLUS_LONG_PUT_10D | 2.0% | STRESS | 2147554.98 | 10.3065 | -23.5065 | -21.4457 | 24 | 24 | 4 | 63 | 0.0 |
| PUT_SHORT_HEAVY_1x1 | 0.5% | BASE | 2068844.58 | 9.7792 | -23.2887 | -21.6663 | 28 | 28 | 0 | 32 | 0.0 |
| PUT_SHORT_HEAVY_1x1 | 0.5% | STRESS | 2062046.18 | 9.7328 | -23.4758 | -21.8394 | 28 | 28 | 0 | 32 | 0.0 |
| PUT_SHORT_HEAVY_1x1 | 1.0% | BASE | 2014272.18 | 9.4032 | -24.135 | -22.6405 | 28 | 28 | 0 | 69 | 0.0 |
| PUT_SHORT_HEAVY_1x1 | 1.0% | STRESS | 1999965.98 | 9.3031 | -24.5216 | -23.0262 | 28 | 28 | 0 | 68 | 0.0 |
| PUT_SHORT_HEAVY_1x1 | 2.0% | BASE | None | None | -11.6068 | -4.1161 | 5 | 4 | 23 | 1657 | 0.0 |
| PUT_SHORT_HEAVY_1x1 | 2.0% | STRESS | None | None | -24.9373 | -23.7062 | 25 | 24 | 3 | 427 | 0.0 |
| PUT_SHORT_HEAVY_1x4 | 0.5% | BASE | 2138791.18 | 10.2486 | -22.796 | -21.049 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x4 | 0.5% | STRESS | 2138791.18 | 10.2486 | -22.796 | -21.049 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x4 | 1.0% | BASE | 2138791.18 | 10.2486 | -22.796 | -21.049 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x4 | 1.0% | STRESS | 2138791.18 | 10.2486 | -22.796 | -21.049 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x4 | 2.0% | BASE | 2138791.18 | 10.2486 | -22.796 | -21.049 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x4 | 2.0% | STRESS | 2138791.18 | 10.2486 | -22.796 | -21.049 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x5 | 0.5% | BASE | 2138791.18 | 10.2486 | -22.796 | -21.049 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x5 | 0.5% | STRESS | 2138791.18 | 10.2486 | -22.796 | -21.049 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x5 | 1.0% | BASE | 2138791.18 | 10.2486 | -22.796 | -21.049 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x5 | 1.0% | STRESS | 2138791.18 | 10.2486 | -22.796 | -21.049 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x5 | 2.0% | BASE | 2138791.18 | 10.2486 | -22.796 | -21.049 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x5 | 2.0% | STRESS | 2138791.18 | 10.2486 | -22.796 | -21.049 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x6 | 0.5% | BASE | 2138791.18 | 10.2486 | -22.796 | -21.049 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x6 | 0.5% | STRESS | 2138791.18 | 10.2486 | -22.796 | -21.049 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x6 | 1.0% | BASE | 2138791.18 | 10.2486 | -22.796 | -21.049 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x6 | 1.0% | STRESS | 2138791.18 | 10.2486 | -22.796 | -21.049 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x6 | 2.0% | BASE | 2138791.18 | 10.2486 | -22.796 | -21.049 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_SHORT_HEAVY_1x6 | 2.0% | STRESS | 2138791.18 | 10.2486 | -22.796 | -21.049 | 0 | 0 | 28 | 0 | 0.0 |
| PUT_LONG_HEAVY_2x1 | 0.5% | BASE | 2079526.88 | 9.8517 | -23.2066 | -21.6041 | 28 | 28 | 0 | 26 | 0.0 |
| PUT_LONG_HEAVY_2x1 | 0.5% | STRESS | 2074473.48 | 9.8174 | -23.3619 | -21.7243 | 28 | 28 | 0 | 25 | 0.0 |
| PUT_LONG_HEAVY_2x1 | 1.0% | BASE | 2007978.08 | 9.3592 | -24.1818 | -22.6984 | 28 | 28 | 0 | 55 | 0.0 |
| PUT_LONG_HEAVY_2x1 | 1.0% | STRESS | 1997797.18 | 9.2879 | -24.5005 | -23.0164 | 28 | 28 | 0 | 55 | 0.0 |
| PUT_LONG_HEAVY_2x1 | 2.0% | BASE | 1919283.58 | 8.727 | -24.7678 | -23.563 | 28 | 28 | 0 | 99 | 0.0 |
| PUT_LONG_HEAVY_2x1 | 2.0% | STRESS | 1899865.08 | 8.5852 | -25.5417 | -24.32 | 28 | 28 | 0 | 95 | 0.0 |

## Decision limits

- Risk sizing uses expiry-intrinsic payoff knots, not broker margin models. It cannot cap interim mark-to-market losses, assignment, forced liquidation, early exercise, or multi-leg fill risk.
- Free cash reserved for short-heavy structures is a conservative research proxy, not a claim about actual broker margin.
- MaxDD and CAGR are based on complete daily side-quote liquidation marks; missing marks stay missing and can understate drawdown.
- QQQ Core is price-only, fixed shares funded to 42% of initial NAV; dividends are not included.
- This is a historical screen using options quotes through 2025-12-15. It is not an untouched out-of-sample test and no result authorizes live deployment.
