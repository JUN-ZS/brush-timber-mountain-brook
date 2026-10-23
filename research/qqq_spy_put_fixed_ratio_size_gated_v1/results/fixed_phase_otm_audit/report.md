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
| 0 | QQQ | 392 | 391 | 0 | 1 | 5.071% | 4.696% | 5.085% | 4.702% | -0.383% | 16.623% |
| 0 | SPY | 392 | 392 | 0 | 0 | 4.133% | 3.750% | 4.133% | 3.750% | 0.806% | 16.922% |
| 1 | QQQ | 392 | 392 | 0 | 0 | 5.263% | 4.948% | 5.263% | 4.948% | 0.285% | 19.528% |
| 1 | SPY | 392 | 392 | 0 | 0 | 4.310% | 3.888% | 4.310% | 3.888% | 0.048% | 20.169% |
| 2 | QQQ | 391 | 389 | 0 | 2 | 5.007% | 4.700% | 5.041% | 4.701% | -2.185% | 15.513% |
| 2 | SPY | 391 | 390 | 0 | 1 | 4.064% | 3.753% | 4.078% | 3.755% | -1.360% | 15.427% |
| 3 | QQQ | 390 | 389 | 0 | 1 | 5.205% | 4.772% | 5.220% | 4.773% | -0.350% | 17.238% |
| 3 | SPY | 390 | 389 | 0 | 1 | 4.230% | 3.875% | 4.242% | 3.881% | -0.340% | 19.803% |
| 4 | QQQ | 389 | 388 | 0 | 1 | 5.104% | 4.684% | 5.117% | 4.692% | -0.202% | 11.557% |
| 4 | SPY | 389 | 388 | 0 | 1 | 4.156% | 3.759% | 4.168% | 3.764% | -0.206% | 12.881% |

## Interpretation

- Status across all five phase ledgers: WARN_NON_OTM_LEGS_FOUND; count of selected entry-leg rows that are ATM/ITM: **8**.
- Mean/median signed distance include ITM observations as negative values. The OTM-only columns are conditioned on being strictly OTM and must not hide the separate ATM/ITM counts.
- No non-OTM row is silently filtered. A non-OTM finding is reported as a warning, preserving the original Delta-based selection so the diagnostic cannot improve results by changing the sample.

### Non-OTM warnings

- Phase 0 QQQ: 1/392 entries are ATM/ITM (0.26%).
- Phase 2 QQQ: 2/391 entries are ATM/ITM (0.51%).
- Phase 2 SPY: 1/391 entries are ATM/ITM (0.26%).
- Phase 3 QQQ: 1/390 entries are ATM/ITM (0.26%).
- Phase 3 SPY: 1/390 entries are ATM/ITM (0.26%).
- Phase 4 QQQ: 1/389 entries are ATM/ITM (0.26%).
- Phase 4 SPY: 1/389 entries are ATM/ITM (0.26%).

## Delta diagnostics

| Phase | Leg | N | Mean abs Delta | Median | Min | Max | Mean distance from target |
|---:|---|---:|---:|---:|---:|---:|---:|
| 0 | QQQ | 392 | 0.2510 | 0.2496 | 0.2166 | 0.4460 | 0.0053 |
| 0 | SPY | 392 | 0.2501 | 0.2494 | 0.2321 | 0.3169 | 0.0039 |
| 1 | QQQ | 392 | 0.2508 | 0.2504 | 0.2119 | 0.3398 | 0.0048 |
| 1 | SPY | 392 | 0.2503 | 0.2499 | 0.2329 | 0.3159 | 0.0038 |
| 2 | QQQ | 391 | 0.2505 | 0.2501 | 0.2311 | 0.3071 | 0.0042 |
| 2 | SPY | 391 | 0.2500 | 0.2497 | 0.2342 | 0.2731 | 0.0036 |
| 3 | QQQ | 390 | 0.2515 | 0.2502 | 0.2216 | 0.4105 | 0.0064 |
| 3 | SPY | 390 | 0.2503 | 0.2497 | 0.2326 | 0.3900 | 0.0045 |
| 4 | QQQ | 389 | 0.2507 | 0.2500 | 0.2262 | 0.3504 | 0.0045 |
| 4 | SPY | 389 | 0.2506 | 0.2501 | 0.2246 | 0.3437 | 0.0043 |

## Files

- entry_leg_otm_detail.csv: one record per phase × entry cohort × leg, with spot, strike, signed OTM percent and moneyness status at signal and entry.
- phase_leg_otm_summary.csv: phase/leg distributions at signal and entry.
- phase_leg_delta_summary.csv: actual selected Delta distribution per phase and leg.
- manifest.json: input hashes and reconciliation summary.
