# Original Hybrid CAGR Replay Audit V1

## Replayed account-NAV results

| Window | Variant | Final NAV | Net profit | CAGR | Daily MTM MaxDD | NAV rows |
|---|---|---:|---:|---:|---:|---:|
| 2018-03-01 to 2025-12-15 | LEGACY_BASELINE | USD 254,787.62 | USD 154,787.62 | 12.7530% | -23.0213% | 1,960 |
| 2018-03-01 to 2025-12-15 | DEPLOY_V1_1 | USD 258,651.97 | USD 158,651.97 | 12.9710% | -22.8480% | 1,960 |
| 2018-03-01 to 2026-09-04 | LEGACY_BASELINE | USD 298,267.22 | USD 198,267.22 | 13.6992% | -23.0213% | 2,141 |
| 2018-03-01 to 2026-09-04 | DEPLOY_V1_1 | USD 303,257.38 | USD 203,257.38 | 13.9210% | -22.8480% | 2,141 |

## Reproduction control

- Market-input SHA-256: e5012c786152a510e297afe2c98131ed179eecb002181a97d72a89f8de061d6d
- Preserved simulator SHA-256: 82cb129787ddbba84138d4ce7b32fb1339e45ba0c41b1af8401df64235137e91
- PR #98 legacy full-window source-parity check: PASS; final-NAV delta USD 0.0040.
- Pricing/evidence: DERIVED_BS_VIX; NOT OPRA. VX term structure is a VIX/MA20 proxy.
- The prior 12.7049% / -23.1837% / USD 276,508 figures remain a separate, not-yet-pinned reference. The exact historical end date, source-input hash and simulator version need to agree before claiming exact reproduction.
- These are daily account-NAV replay metrics for the preserved model, not live fills, a brokerage statement, or an account-constrained OPRA options replay.
