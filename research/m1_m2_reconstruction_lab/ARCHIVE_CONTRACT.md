# Recovered Archive M1/M2 Contract — Forensic V1

## Source of truth

Repository: `JUN-ZS/timber-blade-kind-dawn`
Ref: `main`

Recovered source files and blob SHAs:

- `src/engine/radar.ts` — `8f05a2bbf35ccc136eaab081eadbd52723b50db9`
- `src/engine/policy.ts` — `6e9a1cab6fdc50c2f025f1c5d0db7a7d1bf97645`
- `src/engine/book.ts` — `641dc4b6f8d64d596b00031b00c108f47b3db1d9`
- `src/engine/splits.ts` — `7936337677dc402184b68e132b476de184282b1f`
- `src/data/spots.json` — `2a12ac605cb1bb96522cbd7195fc93e95e1c1fe7`

## Exact recovered term implementation

From `radar.ts::termSlope(vix, vixMa20)`:

```
m1_proxy = max(VIX, 1e-6)
lift = 0.10 * tanh((VIX_MA20 - VIX) / 6)
m2_proxy = m1_proxy * (1 + lift)
S_proxy = (m2_proxy - m1_proxy) / m1_proxy = lift
```

The source comment explicitly calls this a **term-structure proxy**.

Therefore the forensic classification is:

- SOURCE-CODE-EXACT: YES
- TRUE VX FUTURES M1/M2: NO
- Reconstruction provenance: DERIVED_FROM_ARCHIVE_SOURCE
- Observed M1/M2 truth: external dataset, evaluation-only

## Exact archived state/action logic

From `radar.ts`:

1. Shock if `rV > 0.06` OR `VIX > 35` OR `rQ < -0.03`.
2. High-Spread if `halfSpreadV(VIX) > 0.14`.
3. Decay-Optimal if `S >= 0 AND VIX < 28`.
4. Otherwise Normal.

From `policy.ts`:

- Shock -> QQQ core only / no VXX seller.
- Else if `S < 0` -> QQQ core + 0.8% QQQ call sleeve / no VXX seller.
- Else -> PAIR: QQQ core + QQQ call + VXX short + VXX call.
- VXX short target: 18% when VIX < 28, otherwise 10%.
- VXX call sleeve target: 2%.
- QQQ call sleeve: 1.2% when prior QQQ return > 0.6%, otherwise 0.8%.

## Forensic masking experiment

The lab uses:

### Reconstruction input
- VIX_t
- all VIX observations up to t
- fixed archive constants

### Evaluation-only truth
- observed M1_t
- observed M2_t

The comparison layers are:

1. M1/M2 numerical error
2. S_t error
3. term sign / regime agreement
4. archived state agreement
5. archived action agreement
6. VXX carry eligibility agreement
7. future-truth mutation leakage audit

No future M1/M2 value may enter the reconstruction path.

## Formal interpretation

A mismatch means the recovered archive proxy cannot faithfully substitute for the real M1/M2 series.

It does **not** by itself invalidate the Original Hybrid or the historical 12.5% claim.

To establish the exact historical 12.5% generator, a separate replay must recover the full data/execution contract and reproduce its trade sequence and performance without tuning to the headline result.
