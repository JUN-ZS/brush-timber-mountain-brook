# QQQ_MUTUAL_CHASE_FRONTLOAD_V1 — EXACT-DATA REPLAY

Status: RESEARCH_ONLY / DIAGNOSTIC_ONLY.

Provenance: GitHub `src/data/universe.json`, as-of 2026-09-04; 273 monthly points; 153 complete overlapping rolling 10Y windows.

Front-load parameter: `C_t(F)=F*B+(1-F)*B*t/120`, with B=1 and F={0%,10%,...,100%}. BUY/SELL uses only t-1 month-end NAV; SELL proceeds recycle through reserve; external contribution never exceeds B.

This file is an exact-data replay of the fixed script. GitHub Actions verification is separate.

## Aggregate curve

| F | Month-1 target | Mean terminal EW | Mean CAGR | Mean raw MaxDD | Mean economic MaxDD | Mean external contribution | BUY events | SELL events | Gross turnover / month |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0% | 0.83%B | 190414 | 6.630% | -14.945% | -12.831% | 41.281%B | 69.12 | 50.88 | 2.016%B |\n| 10% | 10.75%B | 198296 | 7.062% | -15.310% | -13.866% | 39.995%B | 61.78 | 58.22 | 2.236%B |\n| 20% | 20.67%B | 206177 | 7.478% | -15.781% | -15.030% | 41.575%B | 56.24 | 63.76 | 2.501%B |\n| 30% | 30.58%B | 214058 | 7.879% | -16.364% | -16.174% | 46.829%B | 53.20 | 66.80 | 2.785%B |\n| 40% | 40.50%B | 221938 | 8.267% | -17.028% | -17.302% | 55.179%B | 51.01 | 68.99 | 3.076%B |\n| 50% | 50.42%B | 229817 | 8.641% | -17.572% | -18.397% | 64.395%B | 49.37 | 70.63 | 3.372%B |\n| 60% | 60.33%B | 237694 | 9.004% | -18.018% | -19.467% | 73.842%B | 47.50 | 72.50 | 3.671%B |\n| 70% | 70.25%B | 245404 | 9.348% | -18.512% | -20.587% | 82.339%B | 45.93 | 73.76 | 3.953%B |\n| 80% | 80.17%B | 252709 | 9.662% | -20.138% | -21.640% | 89.077%B | 45.04 | 73.65 | 4.199%B |\n| 90% | 90.08%B | 259758 | 9.956% | -22.655% | -22.612% | 95.385%B | 44.58 | 72.84 | 4.422%B |\n| 100% | 100.00%B | 266517 | 10.229% | -25.644% | -23.444% | 100.000%B | 41.90 | 71.48 | 4.558%B |\n
## Relative to F=0

| F | Terminal Δ | CAGR Δ pp | Economic MaxDD Δ pp | Higher terminal windows |
|---:|---:|---:|---:|---:|
| 0% | $0 | 0.000 | 0.000 | 0/153 |\n| 10% | $7882 | 0.432 | -1.035 | 153/153 |\n| 20% | $15764 | 0.848 | -2.200 | 153/153 |\n| 30% | $23644 | 1.249 | -3.343 | 153/153 |\n| 40% | $31524 | 1.637 | -4.471 | 153/153 |\n| 50% | $39403 | 2.011 | -5.567 | 153/153 |\n| 60% | $47280 | 2.374 | -6.637 | 153/153 |\n| 70% | $54990 | 2.718 | -7.756 | 153/153 |\n| 80% | $62295 | 3.032 | -8.809 | 153/153 |\n| 90% | $69344 | 3.326 | -9.782 | 153/153 |\n| 100% | $76103 | 3.599 | -10.614 | 153/153 |\n
## 100,000 example

Mean terminal economic wealth at F=0 is about $190414. At F=100% it is about $266517. The simple terminal-gain/120 equivalent is about $753/month versus $1388/month; this is NOT an actual monthly profit stream.

The curve therefore measures a capital-budget timing trade-off: more front-loading increases earlier exposure and terminal compounding, while mutual-chase still generates SELL-to-reserve recycling. Turnover rises substantially as front-loading increases.

No front-load level is promoted automatically.
