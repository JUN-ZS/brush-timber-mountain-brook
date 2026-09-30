# V22 Ridge Audit — 4×3 Near-DTE × Coverage Surface

## Provenance

- V22 engine commit: `930c949ec5260865f2bf3ee1c6e030dab7b8e4c4`
- Archived result bundle: `qqq-dynamic-near-long-state-engine-v22.zip`
- `v22_dynamic_state_summary.csv`: **864 config rows**
- `v22_dynamic_state_detail.csv`: **24,768 campaign rows**
- Canonical options SHA256: `1f831556cd87ec9d7af43d3b47a69a829ffb2fb199cfcef4ff55d289badf8734`
- Canonical underlying SHA256: `78c015fd7fa9d493cd798d5ae81b3c2ae6dc3b8176e25e7bb90cd4114b103351`
- Underlying range: `2011-01-03` → `2025-12-15`
- Gamma mode: `OBSERVED_GAMMA`

**Matrix-count warning:** the result JSON has an inconsistent `data.matrix_configs=1152`, while its explicit `matrix.configs=864`, the source engine loops are 9×4×3×8, and the actual summary CSV contains exactly 864 rows. This audit treats **864 summary rows as the source of truth**.

## What each 4×3 cell means

- `positive_config_ratio`: among the 72 far-DTE × far-delta × policy rows belonging to that cell, fraction with total P&L > 0.
- `median_campaign_pnl_usd`: median over all campaign rows in that cell (2,064 campaigns here).
- `positive_campaign_ratio`: fraction of those campaign rows with total P&L > 0.
- `worst_campaign_pnl_usd`: minimum campaign total P&L.
- `mean_campaign_maxdd`: mean of campaign max drawdown.
- `near_win_rate`: pooled near long wins / (wins + losses).

## 4×3 surface

| Near DTE | Coverage | Config + | Median campaign P&L | Campaign + | Worst campaign | Mean MaxDD | Near WR | Total P&L |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 7 | 0.75× | 2.8% | $-180.5 | 37.6% | $-21,321 | -2.81% | 50.99% | $-1,250,835 |
| 7 | 1× | 6.9% | $-177.0 | 39.4% | $-21,321 | -2.87% | 51.29% | $-963,317 |
| 7 | 1.5× | 12.5% | $-141.5 | 42.2% | $-21,505 | -3.15% | 51.42% | $-723,485 |
| 14 | 0.75× | 9.7% | $-70.0 | 44.9% | $-21,321 | -2.71% | 57.70% | $-869,028 |
| 14 | 1× | 20.8% | $-51.0 | 46.0% | $-23,056 | -2.78% | 57.94% | $-549,763 |
| 14 | 1.5× | 40.3% | $-9.5 | 49.8% | $-21,824 | -3.07% | 58.27% | $-157,382 |
| 21 | 0.75× | 19.4% | $-68.0 | 44.4% | $-17,861 | -2.54% | 63.22% | $-723,949 |
| 21 | 1× | 26.4% | $-41.0 | 47.0% | $-18,455 | -2.64% | 64.03% | $-378,945 |
| 21 | 1.5× | 62.5% | +$37.0 | 52.5% | $-19,316 | -2.92% | 64.52% | +$191,423 |
| 30 | 0.75× | 31.9% | $-72.0 | 44.9% | $-16,696 | -2.43% | 68.51% | $-485,757 |
| 30 | 1× | 43.1% | $-22.0 | 48.5% | $-16,281 | -2.54% | 69.43% | $-128,226 |
| 30 | 1.5× | 75.0% | +$80.0 | 54.2% | $-16,281 | -2.84% | 70.23% | +$532,918 |

## Strict ridge test

| Cell | Median campaign P&L | Config + | Campaign + |
|---|---:|---:|---:|
| 21D / 1× | $-41.0 | 26.4% | 47.0% |
| 21D / 1.5× | +$37.0 | 62.5% | 52.5% |
| 30D / 1× | $-22.0 | 43.1% | 48.5% |
| 30D / 1.5× | +$80.0 | 75.0% | 54.2% |

Under the strict 2×2 definition, this is **not yet a robustness ridge**: the four core cells contain two negative median-campaign cells (21D/1.0× and 30D/1.0×). The surface instead shows a clear upper-right gradient, culminating at 30D/1.5×.

The especially clean directional pattern is:

- At **30D**, increasing coverage 0.75× → 1.0× → 1.5× changes median campaign P&L −$72 → −$22 → **+$80** and config-positive ratio 31.9% → 43.1% → **75.0%**.
- At **1.5×**, increasing Near DTE 7D → 14D → 21D → 30D changes median campaign P&L −$141.5 → −$9.5 → +$37 → **+$80** and config-positive ratio 12.5% → 40.3% → 62.5% → **75.0%**.

This is stronger evidence for a **corner/gradient effect** than for a flat ridge.

## Policy decomposition at 30D / 1.5×

| Policy | Total P&L | Median campaign P&L | Campaign + | Worst | Mean MaxDD | Near WR |
|---|---:|---:|---:|---:|---:|---:|
| TP50_IMMEDIATE | +$187,652 | +$307.0 | 64.7% | $-15,106 | -2.56% | 74.05% |
| TP75_IMMEDIATE | +$142,193 | +$190.5 | 60.1% | $-15,071 | -2.69% | 69.14% |
| TP50_ON_RISK | +$120,304 | +$80.0 | 55.0% | $-15,106 | -2.63% | 80.86% |
| TP100_IMMEDIATE | +$62,524 | +$112.5 | 55.0% | $-15,071 | -2.81% | 62.68% |
| TP75_ON_RISK | +$50,935 | +$7.0 | 50.4% | $-16,281 | -2.76% | 76.61% |
| TP75_COOLDOWN3 | +$1,864 | +$32.5 | 52.3% | $-14,671 | -3.14% | 64.91% |
| TRAIL20_ON_RISK | $-5,416 | $-29.5 | 47.7% | $-13,011 | -3.01% | 69.22% |
| TRAIL20_IMMEDIATE | $-27,138 | $-61.0 | 48.4% | $-15,441 | -3.14% | 59.37% |

At 30D/1.5×, **6/8 policies have positive median campaign P&L**, and **6/8 have campaign-positive ratio above 50%**. The largest single policy contributes 35.2% of the cell's aggregate P&L, so the cell is not numerically identical to a one-policy-only result.

## Far-configuration decomposition at 30D / 1.5×

| Far DTE | Far Δ | Campaigns | Median campaign P&L | Campaign + | Worst | Mean MaxDD |
|---:|---:|---:|---:|---:|---:|---:|
| 90 | 5% | 272 | +$62.0 | 53.3% | $-6,424 | -2.03% |
| 90 | 8% | 272 | +$100.0 | 55.9% | $-6,526 | -2.77% |
| 90 | 10% | 288 | +$6.0 | 51.0% | $-6,802 | -2.81% |
| 120 | 5% | 232 | +$26.0 | 52.6% | $-7,309 | -2.66% |
| 120 | 8% | 232 | +$68.0 | 53.9% | $-8,088 | -2.84% |
| 120 | 10% | 240 | $-93.0 | 45.4% | $-12,122 | -2.96% |
| 180 | 5% | 160 | +$49.0 | 50.6% | $-9,389 | -3.00% |
| 180 | 8% | 184 | +$292.5 | 65.8% | $-16,281 | -3.15% |
| 180 | 10% | 184 | +$479.0 | 63.6% | $-14,671 | -3.84% |

At 30D/1.5×, **8/9 far configurations have positive median campaign P&L**, and **8/9 have more than 50% positive campaigns.** The only negative-median far combination is 120D / 10% delta (−$93 median).

## Research interpretation

1. `30D + 1.5×` is empirically the strongest cell in this 4×3 surface under the chosen aggregate metrics.
2. It is **not** yet a strict robustness ridge under the 2×2-neighborhood definition; the 1.0× cells remain negative on median campaign P&L.
3. The 1.5× edge is substantially more stable across Far configurations and across policies than a single isolated top row would suggest.
4. This remains an **in-sample historical matrix audit**. It does not establish OOS robustness, future performance, or deployability.

## Files

- `v22_ridge_surface_4x3.csv` — exact 12-cell surface.
- `v22_ridge_policy_breakdown_96.csv` — all 12 cells × 8 policies.
- `v22_ridge_far_composition_30d_1_5x.csv` — 30D/1.5× across 9 Far configurations.
