# QQQ LONG PUT / SPY SHORT PUT — Realized OTM Distance Audit

Status: WARN_NON_OTM_LEGS_FOUND

- OTM percent is recomputed as (underlying spot - put strike) / underlying spot × 100.
- Positive percentage = OTM; 0% = ATM; negative percentage = ITM.
- Both signal-date spot and actual entry-date spot are measured. Entry-date moneyness is the primary execution-time diagnostic.
- Candidate Delta target remains absolute Delta 0.25; eligible absolute-Delta band remains 0.10–0.50. No P&L-driven re-selection or entry filter was added.
- These are EOD underlying prices and option-chain Delta/quotes, not verified fills. Delta is not treated as an exact probability.

## Actual entry distance by phase and leg

| Phase | Leg | N | OTM | ATM | ITM | Mean signed % | Median signed % | Mean % among OTM only | Median % among OTM only | Min signed % | Max signed % |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | QQQ | 392 | 386 | 0 | 6 | 3.036% | 2.733% | 3.093% | 2.752% | -1.511% | 13.497% |
| 0 | SPY | 392 | 384 | 0 | 8 | 2.358% | 2.064% | 2.417% | 2.094% | -1.568% | 13.859% |
| 1 | QQQ | 392 | 387 | 0 | 5 | 3.187% | 2.991% | 3.242% | 3.024% | -1.652% | 16.814% |
| 1 | SPY | 392 | 387 | 0 | 5 | 2.538% | 2.251% | 2.583% | 2.319% | -1.487% | 18.313% |
| 2 | QQQ | 391 | 379 | 0 | 12 | 2.890% | 2.592% | 3.019% | 2.658% | -5.139% | 11.950% |
| 2 | SPY | 391 | 380 | 0 | 11 | 2.275% | 2.029% | 2.370% | 2.051% | -2.981% | 12.029% |
| 3 | QQQ | 390 | 380 | 0 | 10 | 3.132% | 2.802% | 3.236% | 2.843% | -1.734% | 17.097% |
| 3 | SPY | 390 | 379 | 0 | 11 | 2.443% | 2.083% | 2.536% | 2.131% | -2.320% | 15.690% |
| 4 | QQQ | 388 | 379 | 0 | 9 | 3.048% | 2.695% | 3.132% | 2.726% | -1.322% | 9.724% |
| 4 | SPY | 388 | 383 | 1 | 4 | 2.424% | 2.089% | 2.459% | 2.102% | -1.150% | 10.045% |

## Interpretation

- Status across all five phase ledgers: WARN_NON_OTM_LEGS_FOUND; count of selected entry-leg rows that are ATM/ITM: **82**.
- Mean/median signed distance include ITM observations as negative values. The OTM-only columns are conditioned on being strictly OTM and must not hide the separate ATM/ITM counts.
- No non-OTM row is silently filtered. A non-OTM finding is reported as a warning, preserving the original Delta-based selection so the diagnostic cannot improve results by changing the sample.

### Non-OTM warnings

- Phase 0 QQQ: 6/392 entries are ATM/ITM (1.53%).
- Phase 0 SPY: 8/392 entries are ATM/ITM (2.04%).
- Phase 1 QQQ: 5/392 entries are ATM/ITM (1.28%).
- Phase 1 SPY: 5/392 entries are ATM/ITM (1.28%).
- Phase 2 QQQ: 12/391 entries are ATM/ITM (3.07%).
- Phase 2 SPY: 11/391 entries are ATM/ITM (2.81%).
- Phase 3 QQQ: 10/390 entries are ATM/ITM (2.56%).
- Phase 3 SPY: 11/390 entries are ATM/ITM (2.82%).
- Phase 4 QQQ: 9/388 entries are ATM/ITM (2.32%).
- Phase 4 SPY: 5/388 entries are ATM/ITM (1.29%).

## Delta diagnostics

| Phase | Leg | N | Mean abs Delta | Median | Min | Max | Mean distance from target |
|---:|---|---:|---:|---:|---:|---:|---:|
| 0 | QQQ | 392 | 0.2500 | 0.2499 | 0.1954 | 0.3264 | 0.0070 |
| 0 | SPY | 392 | 0.2514 | 0.2503 | 0.1935 | 0.4175 | 0.0076 |
| 1 | QQQ | 392 | 0.2500 | 0.2496 | 0.2012 | 0.3063 | 0.0070 |
| 1 | SPY | 392 | 0.2511 | 0.2505 | 0.2067 | 0.3268 | 0.0079 |
| 2 | QQQ | 391 | 0.2511 | 0.2507 | 0.1718 | 0.3968 | 0.0079 |
| 2 | SPY | 391 | 0.2511 | 0.2504 | 0.1724 | 0.3387 | 0.0078 |
| 3 | QQQ | 390 | 0.2506 | 0.2501 | 0.1521 | 0.3067 | 0.0076 |
| 3 | SPY | 390 | 0.2515 | 0.2504 | 0.1807 | 0.3838 | 0.0085 |
| 4 | QQQ | 388 | 0.2502 | 0.2498 | 0.1736 | 0.3257 | 0.0072 |
| 4 | SPY | 388 | 0.2488 | 0.2496 | 0.1442 | 0.3042 | 0.0077 |

## Files

- entry_leg_otm_detail.csv: one record per phase × entry cohort × leg, with spot, strike, signed OTM percent and moneyness status at signal and entry.
- phase_leg_otm_summary.csv: phase/leg distributions at signal and entry.
- phase_leg_delta_summary.csv: actual selected Delta distribution per phase and leg.
- manifest.json: input hashes and reconciliation summary.
