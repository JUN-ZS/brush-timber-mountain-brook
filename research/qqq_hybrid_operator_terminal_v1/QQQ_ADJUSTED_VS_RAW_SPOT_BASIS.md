# QQQ option price-basis audit — Run #5

**Status:** price-basis discrepancy is measured on two historical EOD checkpoints; strategy replay is not approved.  
**Workflow:** [Windows self-hosted Run #5](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38004657651)  
**Data source:** public anahatsingh-ui/options-dataset-hist EOD preservation mirror.  
**Model source:** research/qqq_hybrid_dynamic_deployment_v1_1_replay.py, Git blob SHA ac74b3812c826ad491fb829108f26397322e45eb.  
**Underlying series:** src/data/universe.json, Git blob SHA 43c1b3053d17b278cfc01bb0b87e41679f3e85c9.

## 1. Integrity and method

Run #5 verified all three downloaded public Parquet files by both expected bytes and Git blob SHA, and verified the exact source blobs for universe.json and the preserved V1.1 replay before doing the model comparison.

The preserved quoteCC implementation prices QQQ calls from row.qqq. However, the repo's universe file identifies its price data as a Yahoo adjusted-close series. The audit independently reads the public EOD close and adjusted_close, holds the repo VIX fixed, and replicates the exact QQQ call-credit proxy assumptions.

For each checkpoint it:
1. generates target short/wing strikes at 30/365 years using the preserved proxy assumptions (short Call Delta target 0.16; wing target 0.08);
2. chooses the nearest listed 20–40 calendar DTE expiry (both chosen dates resolve to 32 DTE) and a listed-strike Call pair near those targets;
3. calculates snapshot credit as short-leg Bid minus wing Ask, and separately records midpoint-minus-midpoint credit;
4. reprices those exact same listed strikes twice—once using the repo's adjusted-series QQQ input and once using the public raw close—so the price-basis comparison is not confounded by changing contracts inside that pair.

The contract root / OCC deliverable is not independently verified by this public mirror; the 100-share multiplier remains an explicit assumption. EOD snapshot quotes are not confirmed fills.

## 2. Raw spot versus adjusted spot changes target contracts

| Snapshot | Repo QQQ input | Public raw close | Repo input vs raw | Adjusted-input target (short / wing) | Raw-close target (short / wing) |
|---|---:|---:|---:|---:|---:|
| 2020-03-16 | $162.9786 | $169.30 | -3.7338% | $214.25 / $231.84 | $222.56 / $240.83 |
| 2024-08-05 | $430.8515 | $435.37 | -1.0379% | $486.45 / $505.06 | $491.55 / $510.36 |

The selected expiries are 2020-04-17 and 2024-09-06. In these checkpoints, the adjusted series moves the short target down by $8.31 and $5.10 respectively, and the wing target down by $8.99 and $5.30. It can therefore select a different nominal option contract than a model using contemporaneous raw underlying price.

## 3. Same listed strikes: model credit remains above the observed quote

“Model credit” is the preserved model's conservative estimate (model short Bid less model wing Ask, with its proxy volatility and spread assumptions); “snapshot credit” is the displayed short Bid minus wing Ask.

| Snapshot / geometry used to select pair | Listed calls | Actual short Δ / wing Δ | Snapshot short Bid − wing Ask | Snapshot mid − mid | Model credit at adjusted input | Model credit at raw close | Raw-vs-adjusted model credit shift |
|---|---|---:|---:|---:|---:|---:|---:|
| 2020-03-16 / raw-close target | 223C / 240C | 0.04427 / 0.00780 | $0.18 | $0.41 | $1.1419 | $1.4813 | +$0.3393 |
| 2020-03-16 / adjusted-input target | 214C / 232C | 0.09248 / 0.01144 | $0.52 | $1.055 | $1.5548 | $1.9788 | +$0.4239 |
| 2024-08-05 / raw-close target | 490C / 510C | 0.09066 / 0.02929 | $0.97 | $1.105 | $2.0880 | $2.4167 | +$0.3288 |
| 2024-08-05 / adjusted-input target | 485C / 505C | 0.12134 / 0.03858 | $1.44 | $1.54 | $2.4015 | $2.7612 | +$0.3596 |

At these same listed strikes, switching only from the adjusted input to raw close raises model conservative credit by approximately $0.33–$0.42 per share. But correcting the spot basis alone does not close the larger model-to-quote gap: using raw close, model credit remains around $1.30–$1.46 per share above the displayed short-Bid/wing-Ask credit. These are snapshot discrepancies on two selected dates, not whole-period results.

The model's target deltas were 0.16 / 0.08, yet actual paired contract Deltas above are materially lower (short 0.044–0.121; wing 0.008–0.039). This is consistent with another calibration issue in the VIX-to-QQQ-IV proxy and/or spread model, but does not by itself prove which component causes the gap. The exact selected legs' reported implied-volatility fields were not included in Run #5 output; the next audit revision will capture them and reprice the same strikes using those per-leg IVs as a diagnostic.

## 4. What this establishes

**Measured:** on two source-pinned dates, the adjusted-close QQQ series differs from raw nominal QQQ close, changes target strikes, and changes the model mark for the exact same listed option pair. The preserved model's conservative credit estimates also sit substantially above observed EOD quote-credit arithmetic on these examples.

**Not established:** which single factor explains the complete discrepancy; whether source-provided IV is exchange-authoritative; intraday 15:45 quotes; actual fills, commissions or slippage; full-period strategy results; or VXX option history. This is not a performance claim and does not authorize a strategy change.

## 5. Required next step

Add each selected contract's source-reported IV and quote sizes; compare four controlled cases at exact same strikes:
- adjusted spot + VIX-derived proxy IV (current model basis);
- raw spot + VIX-derived proxy IV;
- adjusted spot + the two legs' source-reported IVs (diagnostic only);
- raw spot + the two legs' source-reported IVs (diagnostic only).

Report predicted short/wing values, modelled credit, observed midpoint credit and Bid−Ask execution-side credit side by side. Preserve the EOD / preservation-mirror caveat. Only after this attribution should a separate raw-spot replay be proposed; do not change main, frozen sizing, VXX policy, or broker-order behavior.
