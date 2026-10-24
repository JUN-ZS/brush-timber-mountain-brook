# QQQ LONG PUT 1 : SPY SHORT PUT 3 — expiry-guarded DTE14 vs DTE45

## Frozen comparison design

- Reference arm: DTE 30–60 targeting 45; test arm: DTE 7–21 targeting 14.
- Both arms independently replay all five immutable phases from the pinned historical option files.
- Each leg targets absolute Delta 0.25 within the existing 0.10–0.50 eligibility band; fixed QQQ LONG PUT 1 : SPY SHORT PUT 3; no entry filter; overlap enabled; five common-session cadence; same-expiry pair; quote-side size gates; USD 0.05/share/side slippage and USD 0.65/contract/side commission.
- Guarded exit policies: trigger at either 10 or 20 common sessions held, OR calendar DTE <= 7, whichever comes first. The trigger is an EOD signal, not a guaranteed fill; exact contract identity, quote validity and displayed exit-side size remain mandatory.
- A missed close is deferred and remains unresolved if no valid executable quote is found by expiry/source end. Unresolved P&L is not set to zero.
- P&L is additive fixed-size cohort P&L, not compounded account NAV. The five phases overlap and are not independent samples.

## Fixed-anchor integrity

| Arm | Phase | Scheduled slots | Selected signals | Skipped slots | Status |
|---|---:|---:|---:|---:|---|
| DTE45 | 0 | 392 | 392 | 0 | PASS |
| DTE45 | 1 | 392 | 392 | 0 | PASS |
| DTE45 | 2 | 392 | 391 | 1 | PASS |
| DTE45 | 3 | 392 | 391 | 1 | PASS |
| DTE45 | 4 | 391 | 389 | 2 | PASS |
| DTE14 | 0 | 392 | 392 | 0 | PASS |
| DTE14 | 1 | 392 | 392 | 0 | PASS |
| DTE14 | 2 | 392 | 391 | 1 | PASS |
| DTE14 | 3 | 392 | 391 | 1 | PASS |
| DTE14 | 4 | 391 | 388 | 3 | PASS |

## Five-year result by anchor phase

| Phase | Exit rule | Resolved/opened DTE45 | Resolved/opened DTE14 | Unresolved DTE45 | Unresolved DTE14 | Win DTE45 | Win DTE14 | Mean net DTE45 | Mean net DTE14 | Worst DTE45 | Worst DTE14 | Peak gross SPY obligation DTE45 | Peak gross SPY obligation DTE14 |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | HOLD_10_OR_DTE_LE_7 | 250/251 | 251/251 | 1 | 0 | 74.40% | 76.89% | USD 151.40 | USD 51.30 | USD -4,891.20 | USD -9,955.20 | USD 557,700.00 | USD 368,700.00 |
| 0 | HOLD_20_OR_DTE_LE_7 | 248/251 | 251/251 | 3 | 0 | 82.66% | 76.89% | USD 362.65 | USD 51.30 | USD -6,016.20 | USD -9,955.20 | USD 963,450.00 | USD 368,700.00 |
| 1 | HOLD_10_OR_DTE_LE_7 | 250/251 | 251/251 | 1 | 0 | 75.20% | 74.90% | USD 116.10 | USD 44.06 | USD -6,330.20 | USD -6,020.20 | USD 553,800.00 | USD 370,500.00 |
| 1 | HOLD_20_OR_DTE_LE_7 | 248/251 | 251/251 | 3 | 0 | 82.26% | 74.90% | USD 329.11 | USD 44.06 | USD -6,439.20 | USD -6,020.20 | USD 958,200.00 | USD 370,500.00 |
| 2 | HOLD_10_OR_DTE_LE_7 | 251/251 | 251/251 | 0 | 0 | 74.90% | 72.91% | USD 90.43 | USD 29.62 | USD -8,412.20 | USD -4,188.20 | USD 543,300.00 | USD 369,300.00 |
| 2 | HOLD_20_OR_DTE_LE_7 | 249/251 | 251/251 | 2 | 0 | 82.73% | 72.91% | USD 310.07 | USD 29.62 | USD -9,376.20 | USD -4,188.20 | USD 958,200.00 | USD 369,300.00 |
| 3 | HOLD_10_OR_DTE_LE_7 | 251/251 | 251/251 | 0 | 0 | 75.70% | 76.10% | USD 125.80 | USD 53.07 | USD -8,076.20 | USD -9,164.20 | USD 540,900.00 | USD 369,000.00 |
| 3 | HOLD_20_OR_DTE_LE_7 | 251/251 | 251/251 | 0 | 0 | 82.47% | 76.10% | USD 314.07 | USD 53.07 | USD -7,886.20 | USD -9,164.20 | USD 891,000.00 | USD 369,000.00 |
| 4 | HOLD_10_OR_DTE_LE_7 | 251/251 | 249/250 | 0 | 1 | 75.30% | 76.71% | USD 140.25 | USD 65.46 | USD -3,990.20 | USD -7,156.20 | USD 544,500.00 | USD 369,600.00 |
| 4 | HOLD_20_OR_DTE_LE_7 | 250/251 | 249/250 | 1 | 1 | 79.60% | 76.71% | USD 323.79 | USD 65.46 | USD -6,244.20 | USD -7,156.20 | USD 891,000.00 | USD 369,600.00 |

## Anchor-sensitivity summary (5Y, not pooled as independent samples)

| Exit rule | DTE arm | Win-rate range across phases | Mean net/trade range | Worst resolved-trade range | Peak gross SPY obligation across phases |
|---|---|---:|---:|---:|---:|
| HOLD_10_OR_DTE_LE_7 | DTE45 | 74.40–75.70% | USD 90.43 to 151.40 | USD -8,412.20 to -3,990.20 | USD 557,700.00 |
| HOLD_10_OR_DTE_LE_7 | DTE14 | 72.91–76.89% | USD 29.62 to 65.46 | USD -9,955.20 to -4,188.20 | USD 370,500.00 |
| HOLD_20_OR_DTE_LE_7 | DTE45 | 79.60–82.73% | USD 310.07 to 362.65 | USD -9,376.20 to -6,016.20 | USD 963,450.00 |
| HOLD_20_OR_DTE_LE_7 | DTE14 | 72.91–76.89% | USD 29.62 to 65.46 | USD -9,955.20 to -4,188.20 | USD 370,500.00 |

## Entry/source audit hashes

- DTE45 fixed-phase comparison SHA-256: 63de2433d23231b5d2008b621d8c4a8fe0d4296effeff3a97266569fb5aff235
- DTE14 fixed-phase comparison SHA-256: db80259f54fff48c60fdb9dfebddbfd096de0cc982aca954f72b72ff4675a467
- DTE45 OTM manifest SHA-256: 5d1b7737a6693d08d327c2dfbe4c02cf929f488af473593500871c7cf2d936d2
- DTE14 OTM manifest SHA-256: c311fc17d2da99545c34708119352c2b486f448ec28c51c3ea64582ea4d67913

## Interpretation limits

- DTE14 Delta 0.25 does not imply a fixed OTM percentage or a guaranteed 75% win probability.
- EOD option-chain estimates are not verified fills. A trigger does not guarantee a close on that date.
- Gross SPY assignment obligation equals short strike × 100 × short contracts; it is not broker margin or proof of funding capacity.
- Only resolved trades enter win rate and resolved-P&L statistics; always read opened/resolved/unresolved together.
- This is historical in-sample research; no broker execution or live orders are involved.
