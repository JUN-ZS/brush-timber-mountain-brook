# External Evidence Matrix — QQQ Hybrid / VXX Options

**Purpose:** absorb useful public research without treating external results as proof of this portfolio. This file is an evidence register and implementation contract, not a strategy signal or a recommendation to alter frozen policy.

## Evidence labels

- **OBSERVED:** directly present in a dated source, source file, quote, or trade record.
- **DERIVED:** reproducible arithmetic/calculation from identified inputs.
- **ESTIMATED:** model-based price, fill, risk, or parameter.
- **HYPOTHETICAL:** scenario assumption (for example, an assumed borrow rate).
- **UNVERIFIED:** source, timestamp, contract terms, or fill cannot yet be independently established.

Never silently upgrade ESTIMATED/HYPOTHETICAL to OBSERVED.

## External findings, transferable value, and blind spots

| Source | What the source actually supports | Useful lesson | Blind spot / why we do not copy it as policy | App / test consequence |
|---|---|---|---|---|
| [ORATS, “The Tale of Two Backtests” (2019)](https://orats.com/blog/the-tale-of-two-backtests-why-arent-opposite-strategies-absolute-returns-equal) | A particular VXX two-leg call-spread example reported -9.23% annualized for the long spread and +3.51% for the short spread. ORATS attributed the asymmetry to its assumed slippage and commissions: it described a 66%-of-bid/ask-spread slippage convention, $0.02 commission per trade, and near-close option snapshots. | Costs can materially change apparent option-strategy results. Use bid/ask-aware pricing and expose commissions/slippage assumptions. | This is one vendor's model and one historical setup, not independent proof that this Hybrid earns 3.51%. A fill convention is an assumption, not a guaranteed execution. | Show fill/cost assumptions explicitly in any future historical options replay; distinguish leg-touch estimates, midpoint references, and after-cost results. Do not silently use midpoint fills. |
| [Volatility Trading Strategies, VXX decay estimate (2023)](https://www.volatilitytradingstrategies.com/blog/estimating-future-vxx-prices-for-short-volatility-trading) | The article estimates an average daily VXX decay of about -0.249% from a long-run regression, including a synthetic back-history based on VIX futures. | Long-run decay is useful as context and as one scenario input. | A long-run average is not a path forecast. It can hide volatility shocks, curve regimes, drawdown/borrow/margin risk, and the fact that option value depends on the path and implied volatility—not only expected terminal VXX price. | If used, label it ESTIMATED and show stress ranges. Never use a constant daily decay factor as the sole live signal or as proof that a short has survivable risk. |
| [OCC Information Memo #54914 (2024), adjusted VXX1 options](https://infomemo.theocc.com/infomemos?number=54914) | The adjusted series VXX1 was further adjusted around a VXX reverse split. The memo specifies a deliverable of six VXX shares plus cash in lieu of a fractional share; the adjusted-series terms are not interchangeable with an ordinary 100-share equity option. | Contract identity and deliverable are part of the price/payoff calculation. | A generic “multiplier = 100” does not prove that exercising an adjusted option delivers 100 shares. Other dates/series can have different adjustment terms. | Unknown or adjusted VXX series must require an identified contract symbol and OCC deliverable terms before being treated as standard. Otherwise show PENDING/SCENARIO ONLY; do not silently apply standard 100-share payoff math. |
| [Cboe, backwardation and future market direction (2022)](https://www.cboe.com/insights/posts/inside-volatility-trading-is-vix-backwardation-necessarily-a-sign-of-a-future-down-market/) | The article distinguishes contango and backwardation as volatility-futures term-structure states; it notes contango was common historically and directly asks whether backwardation necessarily means a future down market. | Term structure is useful state/carry information, not a deterministic direction oracle. | A regime label alone does not predict the size or timing of the next QQQ move, VXX spike, or option P&L. Thresholds may fail outside the sample used to motivate them. | Keep term-structure state separate from return forecasts. Test state-conditioned P&L, transition lag, false positives, and stress exits against a frozen baseline. |
| [Simon, “Trading the VIX Futures Roll and Volatility Premiums with VIX Options” (2017)](https://onlinelibrary.wiley.com/doi/full/10.1002/fut.21788) | Academic study of VIX-option strategies over Jan 2007–Mar 2014; its abstract explicitly cautions about often-wide VIX option bid/ask quotes in the early years. | Regime-conditioned volatility premia and limited-risk expressions are researchable. | VIX options are not VXX options; a paper on long VIX options does not validate VXX call-credit, QQQ/VXX interaction, or this account's sizing. | Use only to generate isolated hypotheses. Require product-specific quotes, contract handling, costs, and full-portfolio counterfactuals before integration. |
| [Arian, Norouzi Mobarekeh & Seco, out-of-sample methods (2024)](https://doi.org/10.1016/j.knosys.2024.112477) | A controlled synthetic-environment study compares OOS methods and reports better PBO/Deflated Sharpe findings for Combinatorial Purged Cross-Validation than conventional walk-forward in that experiment. | Evaluate robustness across independent windows and control overlap/leakage; do not trust one attractive OOS slice after many trials. | A methodological paper is not evidence that CPCV will always dominate on every financial series, and no validation protocol fixes bad data or bad execution assumptions. | Keep a trial ledger, frozen controls, untouched final holdout, cost stress, and regime splits. Report failed variants; do not search until a desired CAGR/MaxDD gate passes. |

## Current repository boundary

- The existing VXX options historical research in PR #98 uses **DERIVED_BS_VIX** option marks. It is not an OPRA/exchange quote replay.
- Its borrow rates are user-stated or hypothetical scenario inputs unless a broker's historical fee record is attached.
- The user-uploaded screenshot fixture is an **OBSERVED input transcription** only for visible rows; its quote timestamp, executable status, and contract deliverables remain **UNVERIFIED**.
- Research results must not mutate the frozen strategy policy, current target sizing, or any broker-order boundary without a separately reviewed change.

## Acceptance gates before outside research can influence the primary APP

1. **Provenance gate:** every imported quote records instrument, option right, expiry, strike, source, observation timestamp/time zone, and whether the quote was observed, manually transcribed, or model-derived. Missing rows stay missing; missing puts are never inferred from calls.
2. **Freshness gate:** stale/missing/mixed timestamps are visible and block trade-ready status. A calculation can remain available as SCENARIO ONLY, but must not masquerade as live.
3. **Contract gate:** standard versus adjusted contract identity and deliverable are explicit. An unknown VXX deliverable blocks standard payoff sizing.
4. **Execution gate:** option backtests expose bid/ask fill rules, commissions, and slippage assumptions; show the baseline plus adverse-cost sensitivity. Midpoint is a reference, not a free fill.
5. **Risk comparability gate:** stock-short notional and option max-loss are never labelled equal risk just because both are percentages of NAV. Compare explicit shock losses, margin/borrow, path drawdown, and capped versus uncapped tail risk.
6. **Generalization gate:** preserve the frozen baseline, use paired counterfactuals, regime/rolling windows, stress events, and independent holdouts. Avoid broad hyperparameter searches chosen by the desired result.
7. **Integration gate:** external findings first enter a research-only adapter or view. Promotion into the primary policy requires a reproducible source, passing tests, measured incremental value, and an explicit human-reviewed policy change.

## First integrity correction made in PR #99

The Option Chain Lab's loaded screenshot sample now follows the canonical fixture: QQQ CALL strikes 799/805/810 and VXX CALL strikes 21–26 only. QQQ PUT and VXX PUT arrays are empty because the screenshot did not show them. Tests pin the exact QQQ 799C/810C and VXX 21C/24C credit/max-loss arithmetic and confirm independently imported manual put rows still work. This corrects data lineage; it is not a strategy-performance claim.


## Measurable external-evidence scoring

The companion [QQQ Hybrid Research Measurement Contract](RESEARCH_MEASUREMENT_CONTRACT.md) defines a pre-registered 0–12 evidence triage score and separate Accuracy / Generality / Integration gates. The source scores prioritize replication effort only; they are not a probability that an author's claim is true and cannot override missing instrument-matched historical quote data.


## OCC VXX adjustment detail (July–August 2024)

- [OCC Memo #54913](https://infomemo.theocc.com/infomemos?number=54913) says existing VXX/1VXX option roots changed to VXX2/1VXX2 effective 2024-07-24, with 25 post-split VXX shares as the deliverable for that adjusted series; the premium multiplier remains 100.
- [OCC Memo #54914](https://infomemo.theocc.com/infomemos?number=54914) and [Memo #54997](https://infomemo.theocc.com/infomemos?number=54997) describe the separate adjusted VXX1 series, whose later deliverable became 6 VXX shares plus $11.90 cash in lieu of 0.25 share.
- These are adjustment memos for specific adjusted roots, **not a claim that every current VXX option has those deliverables**. The APP must capture the actual option root / contract symbol before applying payoff arithmetic. Underlying label VXX alone is insufficient to classify a contract.

## Free historical VXX chain coverage probe

- [DoltHub post-no-preference/options](https://www.dolthub.com/repositories/post-no-preference/options) is a public community-maintained candidate with a SQL API. Public documentation reports irregular/filtered snapshots; the presence of VXX at required historical checkpoints has not been independently confirmed from this web environment because direct SQL API responses were not accessible.
- The Windows-runnable script `probe_dolthub_vxx_options.py` checks 2019-03-04, 2020-03-16, 2022-06-13, 2024-08-05, 2025-04-07 and 2026-07-07. It records rows returned, expiries, two-sided quote quality and samples. Network/API errors are INCONCLUSIVE, not proof of absence.
- Even if data rows are found, the public table schema does not establish executable fills or OCC adjusted deliverables. The probe can nominate a research source; it cannot clear the trade-replay gate.



- The unbounded `ORDER BY date DESC LIMIT 10` query timed out in Run #82. It was marked INCONCLUSIVE; it is not evidence that the full table has no VXX rows. The probe now uses date-bounded windows and reports `ROWS_FOUND`, `NO_ROWS_IN_WINDOW`, or `INCONCLUSIVE` for each window.

## Run #80 public SQL probe result — measured, not inferred

- Windows self-hosted [Actions Run #80](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38001567750) successfully queried the DoltHub SQL API at six fixed dates (2019-03-04, 2020-03-16, 2022-06-13, 2024-08-05, 2025-04-07, 2026-07-07). Each date returned **zero** `act_symbol='VXX'` rows. The API responded successfully; this is not a network failure.
- Six zero-row checkpoints disqualify those exact dates as demonstrated VXX coverage; they do **not** prove the entire database contains no VXX rows. The undated symbol-wide query in Run #82 timed out, so its result is **INCONCLUSIVE**. The next probe replaces that full-table/sort query with four date-bounded history windows (early 2019, March 2020, June 2024, June–July 2026), each with a 12-second query timeout.
- Regardless of source-wide result, DoltHub remains `COMMUNITY_MAINTAINED / NOT EXCHANGE-AUTHORITATIVE` and does not establish the exact OCC deliverable for adjusted contracts. It cannot be promoted to trade replay solely on row presence.
- New hard gate: `ADJUSTED_TERMS_RECORDED` contracts and known adjusted roots (`VXX1`, `VXX2`, `1VXX1`, `1VXX2`) are blocked from capacity/payoff calculation while this Lab lacks deliverable/underlying-scale normalization. A root/status conflict also blocks.



## New QQQ EOD mirror candidate (separate from VXX-source audit)

- The public preservation mirror [anahatsingh-ui/options-dataset-hist](https://github.com/anahatsingh-ui/options-dataset-hist) covers QQQ 2011–2025 according to its README, with a 4:00 PM Eastern EOD snapshot, and does not include VXX. It is a recovered preservation mirror, not an exchange-hosted endpoint; file-level Git blob SHA and byte size are checked by the separate workflow before parsing.
- The two fixed QQQ audit dates are 2020-03-16 and 2024-08-05. The script samples annual Parquet files plus a small underlying-price file. It measures valid two-sided quote percentage and potential 30–60 DTE / absolute delta 0.03–0.10 call candidates. This calibrates QQQ model-mark plausibility only; the EOD snapshot is not 15:45 or an executable fill.
- Current source audit workflow: [Run #1](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38002570136) is queued. No QQQ chain data or integrity result is treated as established until its log confirms the expected byte counts / Git blob SHAs and the two date probes.



## Measured public QQQ EOD probe (Run #1)

- [Run #1 passed](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38002570136): 2020-03-16 option rows 5,760 / valid non-crossed two-sided 89.76% / 47 DTE-Delta diagnostic candidates; 2024-08-05 rows 7,704 / valid two-sided 93.93% / 25 candidates. All 2020, 2024 and underlying Parquet downloads passed exact byte count and Git blob SHA checks.
- The 2020 diagnostic call candidates included spread/midpoint from 67.61% to 121.31%; selected 2024 samples ranged 7.62% to 15.53%. Hence source availability and quote validity are a lower bar than practical liquidity. Details: [QQQ_PUBLIC_EOD_AUDIT_RUN1_RESULTS.md](QQQ_PUBLIC_EOD_AUDIT_RUN1_RESULTS.md).
- Decision: this mirror is presently usable to **cross-check QQQ EOD quote distributions only**. It does not establish 15:45 executable fills, strategy-level OOS returns, or any VXX option history. No policy integration based on row counts alone.


## Run #5 — QQQ option nominal-spot basis / same-strike chain comparison

- Windows self-hosted [Run #5](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38004657651) passed on the source-pinned model and universe blobs and compared two public EOD QQQ chain dates. Selected expiry was 32 calendar DTE on both days.
- 2020-03-16: repo adjusted-series spot $162.9786 vs raw close $169.30 (-3.7338%); target strikes shift from 214.25/231.84 to 222.56/240.83 when raw close is used.
- 2024-08-05: repo adjusted-series spot $430.8515 vs raw close $435.37 (-1.0379%); target strikes shift from 486.45/505.06 to 491.55/510.36 with raw close.
- At exact same listed strikes, using raw close raises model credit by $0.33–$0.42/share. Yet proxy model credit remains materially higher than displayed short-Bid-minus-wing-Ask credit (about $0.96–$1.46/share above across selected pairs). Actual paired short-leg Deltas were 0.044–0.121 and wings 0.008–0.039 versus model target Deltas 0.16/0.08.
- Interpretation: adjusted nominal price basis is a real contract-selection issue but not the only likely calibration error. Next add selected legs' source-reported IV and run a controlled spot-basis × IV-basis matrix at identical strikes; do not tune VIX→IV until the decomposition is measured. This two-date diagnostic is not a strategy-performance assertion.
- Detailed report: [QQQ_ADJUSTED_VS_RAW_SPOT_BASIS.md](QQQ_ADJUSTED_VS_RAW_SPOT_BASIS.md).


## Run #5 — per-leg spread realism diagnostic

The same matched pairs show actual option half-spread/mid of 42.55% / 50.00% (short / wing) and 43.23% / 44.44% on 2020-03-16, versus the model haircut of 7.84%. On 2024-08-05, matched-pair leg ratios were 4.44% / 19.44% and 3.65% / 4.85%, versus model haircut 4.31%. The 2020 shock quote set and one 2024 wing demonstrate that a uniform VIX-only haircut is not sufficient for execution realism. Use observed leg Bid/Ask where available; otherwise label the fill assumption synthetic and stress it adversely.



## Run #8 — source-reported per-leg IV attribution (not independent validation)

- Selected-pair short-leg proxy σ / reported IV ratios were 1.37×–1.62×; wing ratios were 1.40×–1.77× across the two fixed dates. Example: 2020-03-16 raw-target pair's proxy σ was 84.84% / 80.37%, while the source-reported leg IVs were 52.22% / 47.34%; 2024-08-05 raw-target pair was 39.57% / 37.49% proxy versus 27.83% / 26.85% chain IV.
- Using raw close and chain-reported per-leg IV, model midpoint credit came close to snapshot midpoint credit in all four matched pairs. This may be circular because the source IV may be calculated from the same quote's mark/mid; the IV calculation provenance is not independently verified. Do not call this independent validation.
- With the VIX-derived spread haircut left unchanged, chain-IV conservative credit was still above observed short-Bid/wing-Ask credit by ~$0.18 / $0.46 per share on the two 2020 pairs, but within ~$0.025 / $0.008 on the two 2024 pairs. This aligns with the spread diagnostic: on the 2020 shock sample, observed leg spreads were far wider than the model haircut.
- Detailed raw output is pinned at [QQQ_MODEL_PRICE_ALIGNMENT_RUN8.json](QQQ_MODEL_PRICE_ALIGNMENT_RUN8.json); report tables are in [QQQ_ADJUSTED_VS_RAW_SPOT_BASIS.md](QQQ_ADJUSTED_VS_RAW_SPOT_BASIS.md). Both remain two-date development diagnostics, not a strategy backtest or blind OOS result.



## Next step: preselected multi-regime QQQ quote diagnostic

The next audit version samples eight dates from the already hash-pinned 2020 and 2024 annual Parquet files: 2020-01-15, 2020-03-16, 2020-06-08, 2020-10-30, 2024-02-01, 2024-04-15, 2024-08-05 and 2024-11-06. They are intended to cover lower-volatility, shock, rebound/rotation and recovery contexts. This expands regime coverage without adding new annual-file downloads. Because the date set was chosen after reviewing initial results, it is a development diagnostic—not blind OOS. Report the row/quote quality and price-basis × IV-basis comparisons at each date; do not collapse these observations into a strategy CAGR claim.


## Run #11 — eight-date price-basis × IV regime diagnostic

- Windows self-hosted [Run #11](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38005508316) passed. All 8 preselected dates returned QQQ chain rows (4,712–8,560 rows/date); 89.76%–98.65% had positive non-crossed two-sided quotes. All three downloaded Parquet files and the repo model/universe blobs passed the recorded hash checks.
- The repo QQQ input was 0.8988%–3.7339% below raw QQQ close on every tested date. The raw-target pair's actual short/wing Deltas varied from 0.044/0.008 (2020-03-16 shock) to 0.195/0.145 (2024-02-01 quiet regime). The adjusted-target pair on 2020-01-15 had Delta 0.527/0.396, versus 0.143/0.075 for the raw-target pair.
- The VIX-derived proxy/source-IV ratios on raw-target pairs varied by regime: short-leg 0.88×–1.62×; wing 0.84×–1.70×. It therefore tends to overstate source-reported IV in higher-volatility samples but can understate it in a quieter sample. A single mapping cannot be presumed valid across states.
- Repricing raw-target pairs with raw close and each leg's reported IV left a model-minus-observed executable-side gap ranging roughly -$0.103 to +$0.182/share across the eight dates. This is not independent validation (the IV may be derived from the same quote), nor proof of executable fills. It does show the mismatch depends on volatility regime and leg-level liquidity rather than one universal offset.
- The eight dates were selected after the first two-date investigation; these are development diagnostics, not blind OOS or strategy-level returns. Detailed raw JSON: [QQQ_MULTI_REGIME_ALIGNMENT_RUN11.json](QQQ_MULTI_REGIME_ALIGNMENT_RUN11.json). The next proposed unit of work is a separate raw-spot QQQ option replay with per-leg execution treatment, not an integration change.



## Run #16 — full-period QQQ EOD quote-alignment evidence (source coverage caveat)

[Windows self-hosted Run #16](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38006925584) completed successfully and verified all eight annual option-file Git blob SHA/byte-count pins, the underlying-price file, the repo universe, and the frozen replay/helper source blobs. This is a quote/price-basis diagnostic, **not** strategy P&L and not trade-replay approval.

- Against the **1,971 expected repo-universe sessions** from 2018-03-01 through 2025-12-31, the source has raw underlying prices for 1,960 sessions, QQQ option rows for 1,956 sessions, and raw-target model/quote pairs on 1,946 sessions. The annual option and underlying files both stop at **2025-12-15**, leaving 11 expected late-December sessions unobserved; the four additional missing option dates inside the source span are 2018-11-06, 2019-09-03, 2020-06-23 and 2021-11-04. Do not call this calendar-end-complete coverage.
- On 1,946 matched raw-spot pairs, the VIX-derived proxy model's conservative credit minus observed **short Bid − wing Ask** had median **+$0.181/share** and median absolute gap **$0.196/share**. Positive means the modeled credit was higher than the observed EOD executable-side reference. This is not a simulated fill or strategy return.
- Repricing with per-leg source-reported IV reduced the absolute model-vs-observed credit-gap median to **$0.060/share**, but the source IV may be derived from the same quote midpoint; it is not independent pricing validation.
- The model's VIX-only half-spread haircut was narrower than observed leg half-spreads on **30.0% of short legs** and **57.2% of wings**. In the VIX ≥35 subset (54 matched pairs), those rates were **81.5%** and **100%** respectively.
- The repo option model's QQQ input was below raw close by a median **2.72%** over source dates. That basis difference can change strikes and modeled credit; option-layer strike/quote replay must use contemporaneous raw nominal spot or an explicit, versioned corporate-action transformation.
- EOD rows are reported as 4:00 PM US Eastern snapshots; they do not prove fills at the model's decision timestamp. QQQ-only history does not supply VXX option history. VXX option marks remain DERIVED_BS_VIX / NOT_OPRA.

The date denominator and output mappings were corrected and rerun successfully in Run #18. See the corrected full-history report linked below. No strategy-policy or broker-order permission change is made.


## Corrected full-history quote evidence — Run #18

- [Corrected report](https://github.com/JUN-ZS/brush-timber-mountain-brook/blob/feat/qqq-hybrid-operator-terminal-v1-20261009/research/qqq_hybrid_operator_terminal_v1/QQQ_FULL_HISTORY_ALIGNMENT_RUN18.md) and [summary JSON](https://github.com/JUN-ZS/brush-timber-mountain-brook/blob/feat/qqq-hybrid-operator-terminal-v1-20261009/research/qqq_hybrid_operator_terminal_v1/QQQ_FULL_HISTORY_ALIGNMENT_RUN18.json) are based on successful Windows self-hosted [Actions Run #18](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38009943427) with source hashes verified.
- Correct denominator: 1,971 expected sessions; raw underlying coverage 99.44%, chain coverage 99.24%, raw-target pair coverage 98.73%. Both underlying and option data stop on 2025-12-15; requested coverage through 2025-12-31 is incomplete.
- Median repo QQQ input vs raw nominal close: -2.72%. VIX-proxy credit gap median: +$0.181/share; source-IV absolute gap median: $0.060/share, but source IV is not independent validation.
- Haircut-too-narrow rates: 30.0% short / 57.2% wings; VIX ≥35: 81.5% / 100.0%. Price-basis and spread-realism gates remain blocked for trade replay.


## Full-history adverse-fill validation — Run #22 (2026-10-10)

The full-history diagnostic completed successfully on Windows self-hosted [Actions Run #22](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38015730909) at head `28532f97b2694138b1b85a08cb498001061358b5`. The machine-readable aggregate is [Run #22 JSON](https://github.com/JUN-ZS/brush-timber-mountain-brook/blob/feat/qqq-hybrid-operator-terminal-v1-20261009/research/qqq_hybrid_operator_terminal_v1/QQQ_FULL_HISTORY_ALIGNMENT_RUN22.json); date-level quote pairs are in [Run #22 daily CSV](https://github.com/JUN-ZS/brush-timber-mountain-brook/blob/feat/qqq-hybrid-operator-terminal-v1-20261009/research/qqq_hybrid_operator_terminal_v1/QQQ_FULL_HISTORY_DAILY_PAIRS_RUN22.csv).

- **Scope / denominator:** 1,971 expected sessions (2018-03-01–2025-12-31); 1,960 raw-underlying dates (99.44%), 1,956 option-chain dates (99.24%), and 1,946 raw-target pairs (98.73% of expected sessions; 99.49% of chain dates). Both source series stop on 2025-12-15, leaving 11 terminal expected sessions uncovered; four additional interior dates have no option rows.
- **Price basis:** median repository input vs raw close −2.72%; selected short/wing contracts differ under raw-vs-adjusted target geometry on 96.61% / 95.84% of matched dates. Repository-input pair Delta medians are 0.28174 / 0.16985, not the intended 0.16 / 0.08 targets.
- **Quote gap:** median VIX-proxy model minus observed EOD short Bid − wing Ask is +$0.181/share (median absolute gap $0.196); median absolute source-IV gap is $0.060 but is not independent validation. Model half-spread haircuts are narrower than observed on 30.0% of short legs / 57.2% of wings, and 81.5% / 100.0% at VIX ≥35 (54 pairs).
- **Adverse-fill sensitivity:** at $0.025 per leg, 1.23% of pairs have non-positive stressed credit; at $0.05 per leg, 2.93%; at $0.10 per leg, 13.62%. These are analyst-selected assumptions, not measured fills or fees. Price-basis and spread-realism gates remain BLOCKED for trade replay.

This is source/quote-quality evidence only, not strategy P&L, not proof of executable fills, and not authorization to change frozen strategy policy or broker-order permissions.
