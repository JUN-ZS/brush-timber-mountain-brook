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
