# QQQ Hybrid — VXX Short Stock vs Call-Credit Experiment

**Research-only result snapshot from Windows self-hosted Actions Run #30**  
**Run:** https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/37996642341  
**PR:** https://github.com/JUN-ZS/brush-timber-mountain-brook/pull/98  
**Range:** 2018-03-01 through 2026-09-04; 2,141 daily observations  
**Starting capital:** $100,000  
**Status:** Model-derived; not live strategy proof. No broker orders.

## Experimental contract

Every case keeps QQQ Core and QQQ Call-Credit logic enabled and unchanged. Only the two VXX sleeves are switched:

- VXX short stock can be enabled or disabled independently.
- VXX call-credit vertical can be enabled or disabled independently.
- The existing VXX market entry gate and each sleeve's prior exit rules are retained.
- Short-stock percentage is a NAV notional target. Call-credit allocation is a maximum-loss budget. These are not inherently equal risk budgets.
- Option marks use the repo's DERIVED_BS_VIX model, not historical OPRA chains/fills. Historical VXX option adjustments/reverse splits are not reconstructed.

The 0%, 3% and 10% annualized borrow rates are explicit hypothetical sensitivities, not observed historical VXX borrow fees. Costs accrue on marked short notional using calendar days and a 360-day denominator. Options commissions and real historical executable quotes remain unavailable.

## Primary four-case comparison — using the user-specified 3% annual VXX stock-borrow fee

The 3% borrow rate is treated as the user's stated planning assumption, not independently verified historical broker fee data. To avoid presenting a 0%-borrow stock short as the base case, use these rows for the practical comparison:

| VXX sleeve case | VXX stock-short notional | VXX call-credit max-loss budget | Borrow rate used | Final NAV | CAGR | Daily MTM MaxDD | Annualized vol. | Sharpe (rf=0) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Neither | 0% NAV | 0% NAV | — | $248,998.73 | 11.31% | -22.18% | 13.52% | 0.862 |
| Stock only | 18% NAV | 0% NAV | 3% | $269,366.91 | 12.35% | -23.45% | 16.10% | 0.806 |
| Call-credit only | 0% NAV | 2% NAV | — | $266,334.56 | 12.20% | -22.18% | 13.84% | 0.903 |
| Both | 18% NAV | 2% NAV | 3% | $285,614.36 | 13.12% | -24.93% | 16.63% | 0.827 |

These are four separate full-portfolio replays, not just isolated sleeve-PnL comparisons. NAV-dependent sizing feedback in the remaining Hybrid is retained. A parallel 0%-borrow scenario remains only as a frictionless upper-bound sensitivity; it is no longer the practical base case given the user's 3% assumption.

## Portfolio counterfactual deltas

Positive MaxDD delta means the variant has a less negative drawdown than the comparator.

| Comparison (A vs B) | Final NAV delta A−B | CAGR delta | MaxDD delta | Annualized vol. delta |
|---|---:|---:|---:|---:|
| Stock only (18%) vs neither | +$24,509.51 | +1.235 pp | -0.978 pp | +2.468 pp |
| Call-credit only (2% max loss) vs neither | +$17,335.83 | +0.884 pp | 0.000 pp | +0.314 pp |
| Both vs neither | +$40,457.94 | +1.986 pp | -2.437 pp | +2.995 pp |
| Both vs stock only (18%) | +$15,948.43 | +0.752 pp | -1.459 pp | +0.527 pp |
| Both vs call-credit only | +$23,122.11 | +1.103 pp | -2.437 pp | +2.681 pp |

The pairwise differences need not add exactly to component PnL because the full portfolio's NAV and subsequent NAV-based position sizing respond to each counterfactual.

## Smaller stock-short notional: limited stress alignment

A 2% NAV stock-short notional position would lose about 2% NAV if VXX rose 100% from entry, before borrow costs; that is a single-stress reference, not universal risk equivalence to a 2% maximum-loss spread.

| Case | Stock-short notional | Final NAV | CAGR | Daily MTM MaxDD | Annualized vol. | Sharpe (rf=0) |
|---|---:|---:|---:|---:|---:|---:|
| Stock only, stress reference | 2% NAV | $250,103.37 | 11.37% | -22.06% | 13.74% | 0.855 |
| Stock only, sensitivity | 5% NAV | $254,634.72 | 11.61% | -21.69% | 14.00% | 0.857 |
| Call-credit only | 0% NAV stock; 2% max loss | $266,334.56 | 12.20% | -22.18% | 13.84% | 0.903 |

Against the 2% max-loss call spread, the 2% stock-short case finishes $16,231.19 lower and has 0.826 percentage points lower CAGR. Its modeled MaxDD is only 0.122 points less negative, but stock-short loss remains uncapped for larger VXX increases.

## Borrow-cost sensitivity

| Case | Hypothetical annual borrow rate | Modeled borrow costs | Final NAV | CAGR | Daily MTM MaxDD |
|---|---:|---:|---:|---:|---:|
| Stock only, 18% notional | 0% | $0 | $273,508.24 | 12.55% | -23.16% |
| Stock only, 18% notional | 3% | $4,256.45 | $269,366.91 | 12.35% | -23.45% |
| Stock only, 18% notional | 10% | $13,843.92 | $259,452.07 | 11.85% | -24.19% |
| Both, 18% stock + 2% call | 0% | $0 | $289,456.67 | 13.30% | -24.62% |
| Both, 18% stock + 2% call | 3% | $4,309.23 | $285,614.36 | 13.12% | -24.93% |
| Both, 18% stock + 2% call | 10% | $14,036.70 | $275,979.08 | 12.67% | -25.52% |

These are simulated costs under stipulated rates. They must not be reported as historical realized fees. The final-NAV difference versus the 0% cost case is not identical to the cost total because position sizes and portfolio paths change through the replay.

## Interpretation

1. **Using the user's 3% annual borrow-fee assumption**, stock-only (18% NAV notional) has slightly higher terminal NAV and CAGR than call-credit only (2% max-loss budget), but higher volatility, about 1.28 percentage points worse MaxDD, and lower Sharpe. This does not establish stock-short superiority because the risk bases differ sharply.
2. **Call-credit only** has a higher modeled Sharpe (0.903 vs 0.862) than the neither-sleeve control, with the same recorded MaxDD in this sample.
3. **Both sleeves** produce the highest terminal NAV/CAGR, but also the worst MaxDD (-24.93%) and higher volatility; adding the 18% stock-short to Call-only worsens MaxDD by about 2.75 percentage points at the 3% fee assumption.
4. **Under the limited +100% VXX shock reference**, the 2% NAV stock-short is much smaller than the original 18% stock-short. It has less terminal wealth than the 2% max-loss Call-credit, while its MaxDD is only marginally better. This supports further testing of the capped-loss option sleeve, not an unconditional declaration of a winner.
5. **Borrow costs matter**: the user's 3% assumption reduces model terminal NAV by approximately $4.1k in the stock-only case and $3.8k in the combined case versus the 0%-borrow versions (the modeled fees are about $4.26k and $4.31k respectively; portfolio path and position sizing also change). The 10% annual scenario is a stress sensitivity, not the user's base case. Actual historical VXX borrow fees/availability were not in the input data.

## Verification and artifact limitation

Run #30 passed syntax checks, **9 unit tests**, legacy daily-NAV parity (maximum absolute difference $5.82e-11), the report contract, and the new VXX sleeve experiment contract. The runner verified component PnL reconciliation below $0.01 and that the 3%/10% borrow-cost scenarios generate increasing costs.

The final Actions artifact upload failed because GitHub Actions artifact storage quota was exhausted. Therefore this numeric snapshot is transcribed from the successful runner's emitted JSON and its checked report, rather than downloaded from a newly uploaded artifact. A follow-up change prints the sleeve-comparison matrix in Actions logs and tolerates a quota-blocked artifact upload; no live policy or main branch is changed.
