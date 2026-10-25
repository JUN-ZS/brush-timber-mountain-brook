# QQQ_MUTUAL_CHASE_SELL_TIMING_V1 — Runtime Result

Status: RESEARCH_ONLY / DIAGNOSTIC_ONLY.

Source data was fetched from the actual GitHub branch at commit `9587d2250dbf1b20f222da4346bc1f3f3ab92ab4`, using `src/data/universe.json`.

Coverage: 2026-09-04 data-as-of, 273 monthly points, 153 complete overlapping rolling 10Y windows.

The SELL fraction was fixed at 50%. Only SELL eligibility changed. Decision uses t-1 month-end data; execution uses t month-end close. No future price read and no parameter search.

## CLOCK reference

Mean terminal economic wealth: 2.559447 B

Mean terminal economic CAGR: 9.748981%

Mean raw account MaxDD: -23.040635%

Mean economic-wealth MaxDD: -19.470311%

## Timing results

| Rule | Mean terminal delta B | Mean raw MaxDD delta | Mean economic MaxDD delta | Mean CAGR delta pp | Mean CAGR | Mean SELL events |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ALWAYS_SURPLUS | -0.645671 | +7.713 pp | +6.478 pp | -3.066 pp | 6.683% | 60.19 |
| NEAR_12M_HIGH | -0.638691 | +7.749 pp | +6.390 pp | -3.026 pp | 6.723% | 54.25 |
| AT_12M_HIGH | -0.636986 | +7.640 pp | +6.389 pp | -3.016 pp | 6.733% | 44.43 |
| STRONG_AND_HIGH | -0.636422 | +6.965 pp | +6.390 pp | -3.014 pp | 6.735% | 53.70 |
| POST_RUNUP | -0.618999 | +6.438 pp | +6.291 pp | -2.918 pp | 6.831% | 22.29 |

Positive terminal windows versus CLOCK: 0/153 for all five timing rules.

## Decision

Within this pre-registered timing set:

1. Selling continuously whenever NAV is above target is not necessary.
2. Restricting SELL to market-extension states reduces SELL frequency substantially and recovers a small amount of compounding.
3. The strongest compounding-preserving rule tested was POST_RUNUP: prior QQQ 6M return >= +15% and price >= 95% of trailing 12M high.
4. POST_RUNUP still loses about 2.92 percentage points of terminal CAGR versus CLOCK while retaining about 6.29 percentage points of economic-wealth MaxDD improvement.
5. Therefore timing alone does not solve the compounding problem.

## Structural interpretation

The evidence points away from:

SELL whenever NAV > target

and toward:

profit surplus
  -> wait through normal trend continuation
  -> SELL only in an objectively extended state
  -> reserve
  -> redeploy after subsequent weakness

However, the remaining CAGR gap is too large to promote any timing rule.

No controller promotion. No parameter selection from these results.

Important provenance note: this result was reproduced in the analysis runtime from the exact GitHub branch dataset. GitHub Actions #25 verified the research workflow including the SELL-sensitivity step, but the connector did not expose a newer dedicated Actions artifact for this timing-only extension; therefore this file is explicitly labelled Runtime Result rather than CI artifact evidence.
