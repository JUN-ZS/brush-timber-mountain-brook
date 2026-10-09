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

## 4. The model spread haircut is not sufficiently liquidity-aware

For each selected pair, the model applies one VIX-derived half-spread percentage to both legs. The actual option-chain half-spread is calculated as \((Ask-Bid)/2 \div Mid\) on each observed leg.

| Snapshot / pair | Model half-spread assumption | Observed short-leg half-spread / mid | Observed wing half-spread / mid | Read-through |
|---|---:|---:|---:|---|
| 2020-03-16 / 223C–240C | 7.84% | 42.55% | 50.00% | Both real quote spreads far wider than the model haircut |
| 2020-03-16 / 214C–232C | 7.84% | 43.23% | 44.44% | Both real quote spreads far wider than the model haircut |
| 2024-08-05 / 490C–510C | 4.31% | 4.44% | 19.44% | Short-leg haircut is close; wing spread remains much wider |
| 2024-08-05 / 485C–505C | 4.31% | 3.65% | 4.85% | The observed spreads are close to the current model haircut |

This is a separate error source from spot basis or volatility. In the 2020 shock snapshot, the current VIX-derived spread haircut is roughly five to six times narrower than the observed half-spread relative to midpoint. A single VIX-only haircut does not capture strike-/leg-specific liquidity. The 2024 examples are materially tighter on the short leg, but one wing remains much wider; a spread is only as executable as its less-liquid leg.

**Consequence:** do not allow a model-generated credit to be described as an executable fill if its leg-level haircut is narrower than the corresponding observed quote spread. Where an historical entry/exit quote exists, the diagnostic must show short Bid and wing Ask explicitly; where it does not, report INSUFFICIENT_DATA rather than synthesize an exchange quote.

## 5. VIX-derived IV proxy versus the chain's reported per-leg IV

Run #8 added the selected contracts' source-reported implied volatility and re-priced the exact same listed strikes using each leg's IV. The proxy / source-IV ratios were:

| Snapshot / pair | Proxy short σ | Source short IV | Ratio | Proxy wing σ | Source wing IV | Ratio |
|---|---:|---:|---:|---:|---:|---:|
| 2020-03-16 / 223C–240C | 84.84% | 52.22% | 1.62× | 80.37% | 47.34% | 1.70× |
| 2020-03-16 / 214C–232C | 84.84% | 56.12% | 1.51× | 80.37% | 45.39% | 1.77× |
| 2024-08-05 / 490C–510C | 39.57% | 27.83% | 1.42× | 37.49% | 26.85% | 1.40× |
| 2024-08-05 / 485C–505C | 39.57% | 28.80% | 1.37× | 37.49% | 26.85% | 1.40× |

The existing VIX→QQQ-IV rule therefore gives materially higher volatility than the chain's reported IV on all four selected pairs. This is a source-to-source comparison, not proof that the mirror IV is exchange-authoritative.

### Controlled repricing using the per-leg source IV

| Snapshot / pair | Observed midpoint credit | Observed executable-side credit | Chain-IV model midpoint credit, raw spot | Chain-IV model conservative credit, raw spot |
|---|---:|---:|---:|---:|
| 2020-03-16 / 223C–240C | $0.410 | $0.180 | $0.403 | $0.362 |
| 2020-03-16 / 214C–232C | $1.055 | $0.520 | $1.075 | $0.977 |
| 2024-08-05 / 490C–510C | $1.105 | $0.970 | $1.020 | $0.945 |
| 2024-08-05 / 485C–505C | $1.540 | $1.440 | $1.541 | $1.433 |

At raw close, repricing with the chain's per-leg IV reproduces snapshot midpoint credit closely in these examples. **This is not independent validation:** the published IV may itself be calculated from the same quote's mark/midpoint, and the calculation method has not been independently verified. Treat this as an internal arithmetic / attribution diagnostic.

The chain-IV conservative credit still sits above observed executable-side credit on the two 2020 examples by about $0.18 and $0.46 per share, while the 2024 examples are within about $0.025 and $0.008. With Section 4's spread data, this is consistent with the VIX-only spread haircut being too narrow on the shock-day quotes.

## 6. Eight-date price-basis × IV regime diagnostic — Run #11

Windows self-hosted [Run #11](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38005508316) passed the byte-count/Git-blob checks for both annual option files and the underlying-price file, and passed the pinned repo universe/model source checks. All eight preselected dates returned QQQ option rows and matched a nearby 20–40 calendar DTE expiry. The rows are a development sample selected after inspecting the initial two dates; this is **not blind OOS** and not a strategy replay.

| Date | VIX | Repo spot vs raw close | Raw-target short / wing Δ | Adjusted-target short / wing Δ | Proxy σ ÷ source IV, short / wing | Valid two-sided rows |
|---|---:|---:|---:|---:|---:|---:|
| 2020-01-15 | 12.42 | -3.7339% | 0.143 / 0.075 | 0.527 / 0.396 | 1.04× / 0.99× | 93.93% |
| 2020-03-16 | 82.69 | -3.7338% | 0.044 / 0.008 | 0.092 / 0.011 | 1.62× / 1.70× | 89.76% |
| 2020-06-08 | 25.81 | -3.5287% | 0.079 / 0.038 | 0.225 / 0.114 | 1.39× / 1.32× | 98.65% |
| 2020-10-30 | 38.02 | -3.3610% | 0.070 / 0.027 | 0.173 / 0.070 | 1.35× / 1.28× | 97.14% |
| 2024-02-01 | 13.88 | -1.3254% | 0.195 / 0.145 | 0.288 / 0.195 | 0.88× / 0.84× | 92.58% |
| 2024-04-15 | 19.23 | -1.1949% | 0.136 / 0.084 | 0.245 / 0.136 | 1.09× / 1.09× | 93.66% |
| 2024-08-05 | 38.57 | -1.0379% | 0.091 / 0.029 | 0.121 / 0.039 | 1.42× / 1.40× | 93.93% |
| 2024-11-06 | 16.27 | -0.8988% | 0.145 / 0.088 | 0.215 / 0.124 | 1.10× / 0.98× | 95.72% |

Eight daily chains held 4,712–8,560 option rows each; 89.76%–98.65% had a positive, non-crossed two-sided quote. For all eight dates, the repo's QQQ input series was below the public raw close by 0.8988%–3.7339%. Therefore its model target strikes were consistently shifted lower than targets generated from raw spot.

The key regime effect is **error compensation**. On the quiet 2020-01-15 sample, the raw-target pair's actual Deltas were 0.143 / 0.075—close to the model targets 0.16 / 0.08—while the adjusted-target pair was 0.527 / 0.396. In the high-VIX 2020-03-16 sample, proxy-volatility was much higher than the per-leg source IV and the raw-target pair Deltas were only 0.044 / 0.008. On 2024-02-01, proxy/source-IV ratios fell below 1.0, so the proxy can also understate source IV in a quieter regime. Adjusted spot can accidentally offset an overly high IV proxy in some stress samples, and make the model appear better aligned; that is not evidence the adjusted price is appropriate for nominal option strikes.

### Eight-date executable-credit cross-check using source IV

The next table keeps the pair selected by the **raw-close target geometry** fixed. The “chain-IV model conservative credit” uses each leg's reported IV with the existing model half-spread haircut; it does not assume those quotes are independently verified or executable fills.

| Date | Listed pair | Observed short Bid − wing Ask | Observed mid − mid | Chain-IV model conservative credit | Model minus observed executable-side credit |
|---|---|---:|---:|---:|---:|
| 2020-01-15 | 229C / 232C | $0.310 | $0.330 | $0.291 | $-0.019 |
| 2020-03-16 | 223C / 240C | $0.180 | $0.410 | $0.362 | $0.182 |
| 2020-06-08 | 262C / 267.5C | $0.200 | $0.225 | $0.274 | $0.074 |
| 2020-10-30 | 304C / 315C | $0.390 | $0.425 | $0.410 | $0.020 |
| 2024-02-01 | 441C / 445C | $0.610 | $0.670 | $0.507 | $-0.103 |
| 2024-04-15 | 460C / 465C | $0.530 | $0.560 | $0.616 | $0.086 |
| 2024-08-05 | 490C / 510C | $0.970 | $1.105 | $0.945 | $-0.025 |
| 2024-11-06 | 532C / 541C | $0.890 | $0.930 | $0.564 | $-0.326 |

This row-level comparison does **not** show a stable one-direction credit error after raw spot and source-reported IV are used: the eight-date model-minus-executable gap ranges from roughly -$0.103 to +$0.182 per share (depending on date and selected pair). However, it still inherits a model-derived half-spread and the IV field may be computed from the same quote's mark/midpoint, so the close midpoint fit is not independent validation. It is a price-attribution diagnostic only.

## 7. What this establishes

**Measured:** on two source-pinned dates, the adjusted-close QQQ series differs from raw nominal QQQ close, changes target strikes, and changes the model mark for the exact same listed option pair. The preserved model's conservative credit estimates also sit substantially above observed EOD quote-credit arithmetic on these examples.

**Not established:** which single factor explains the complete discrepancy; whether source-provided IV is exchange-authoritative; intraday 15:45 quotes; actual fills, commissions or slippage; full-period strategy results; or VXX option history. This is not a performance claim and does not authorize a strategy change.

## 8. Required next step

The next engineering/research step is a standalone QQQ option-layer replay—not a change to the live Hybrid:

1. Keep the QQQ equity core's total-return accounting series separate from the **raw nominal QQQ spot** used for option strikes, Black–Scholes marks and payoff calculations. Record the raw/adjusted transformation and reconcile dividends/corporate actions explicitly; do not silently swap the stock accounting series.
2. Compare three IV/quote modes on identical contract IDs: current VIX-derived proxy (MODEL_ONLY), reported per-leg IV with its source and circularity caveat (DIAGNOSTIC_ONLY), and historical observed leg Bid/Ask where the dataset supplies them. Do not call a mid-price match independent validation if the IV may be reverse-solved from the same quote.
3. Model liquidity per leg. Use actual historical short Bid and protective-wing Ask for the EOD diagnostic; for full-period daily replay, either verify the snapshot-to-decision-time convention or apply a pre-registered adverse-fill rule whose slippage is not narrower than observed spreads. Flag missing/zero/crossed quotes instead of synthesizing executable fills.
4. Add a separate `QQQ_CALL_CREDIT_RAW_SPOT_REPLAY_V1` report over a continuous date range only after confirming the public dataset's annual coverage and contract mapping. Keep VXX option P&L as `DERIVED_BS_VIX / NOT_OPRA`; do not imply the QQQ mirror provides VXX history.
5. Compare paired no-QQQ-option baseline vs QQQ-call-credit variants over exactly the same dates, cash accounting, costs and corporate-action handling. The eight selected dates are development evidence, not final OOS; any later split in the familiar 2018–2025 span must be labelled previously exposed, not a virgin lockbox.

No merge, frozen-policy change, or broker-order permission is implied by this research step.
