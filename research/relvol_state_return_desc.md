# RelVol × State × Return (DESC parallel)

> Join 波動 weekly DESC panel onto frozen V2.2 curve. **ASSOCIATION_ONLY**. `credit_unlocked=false`.

## Taxonomy note

- Panel `LAST_STATE`: LOW / NORMAL / HIGH / EXTREME (weekPct abs-vol bins)
- Soft map (DESC only): LOW→CALM, NORMAL→UNMAPPED, HIGH→UNSTABLE, EXTREME→TAIL
- **Not** the same as `regime.ts` DEAD_VOL / STABLE_LOW / …

Joined **5644** / 5644 curve days (QQQ week_end ≤ date).

## By RelVol `LAST_STATE`

| LAST_STATE | soft→ | Share | n | CAGR | MaxDD | mean/day | Stretch |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EXTREME | TAIL | 8.1% | 455 | 0.1% | -32.8% | 0.000136 | False |
| HIGH | UNSTABLE | 16.9% | 955 | 1.1% | -30.9% | 0.000316 | False |
| LOW | CALM | 34.0% | 1920 | 1.4% | -33.5% | 0.000213 | False |
| NORMAL | UNMAPPED | 41.0% | 2314 | 4.3% | -38.7% | 0.000451 | False |

## Soft agree vs disagree (V2.2 vs soft map)

- soft agree n=1567 CAGR=-1.1% MaxDD=-34.1%
- soft disagree n=1763 CAGR=3.8% MaxDD=-24.6%
- soft UNMAPPED (NORMAL) n=2314

## Cross (V2.2 × LAST_STATE) — n≥60

| V2.2 | LAST_STATE | n | CAGR | MaxDD | mean/day |
| --- | --- | --- | --- | --- | --- |
| CALM | EXTREME | 61 | 0.8% | -4.4% | 0.001739 |
| CALM | HIGH | 334 | 2.3% | -9.3% | 0.001421 |
| CALM | LOW | 970 | 0.4% | -22.7% | 0.000111 |
| CALM | NORMAL | 1173 | 3.2% | -11.6% | 0.000635 |
| RECOVERY | LOW | 167 | -0.2% | -11.7% | -0.000229 |
| RECOVERY | NORMAL | 179 | 0.4% | -10.2% | 0.000503 |
| TAIL | EXTREME | 158 | -0.7% | -19.6% | -0.000727 |
| TAIL | HIGH | 130 | -0.1% | -25.3% | -5.1e-05 |
| TAIL | LOW | 134 | 0.4% | -8.6% | 0.000722 |
| TAIL | NORMAL | 182 | 1.0% | -14.6% | 0.001304 |
| UNSTABLE | EXTREME | 187 | -0.6% | -27.1% | -0.000463 |
| UNSTABLE | HIGH | 439 | -0.9% | -18.9% | -0.000391 |
| UNSTABLE | LOW | 649 | 0.9% | -20.2% | 0.000376 |
| UNSTABLE | NORMAL | 780 | -0.3% | -35.3% | -3.7e-05 |

## Verdict

- Best LAST_STATE by mean/day: **NORMAL**
- Worst: **EXTREME**
- Stretch any: **False**

RelVol LOW (soft≈CALM) vs EXTREME (soft≈TAIL) descriptive geography on the same frozen V2.2 path; soft map is ASSOCIATION_ONLY and must not be treated as regime.ts labels.

Credit remains sealed. Next: optional dispersion_state stratum DESC-only.
