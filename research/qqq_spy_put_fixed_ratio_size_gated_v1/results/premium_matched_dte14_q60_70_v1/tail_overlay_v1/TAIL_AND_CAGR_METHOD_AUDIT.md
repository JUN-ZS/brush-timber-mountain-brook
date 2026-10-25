# TAIL Overlay + Historical CAGR Method Audit

As of 2026-10-25. Research-only; no orders and no merge to main.

## 1. Executive findings

1. The paired TAIL episode arithmetic is internally consistent: per episode it calculates
   \`TAIL notional × (exit adjusted close / entry adjusted close − 1) − assumed round-trip friction\`,
   then adds that amount to the option episode's existing net P&L.
2. This report is **not** a portfolio CAGR / account-NAV replay. It stacks overlapping option cohorts and a separate TAIL position for each cohort, then sums episode P&L. "Annual average episode P&L" is only summed episode P&L divided by 7.792 years.
3. The premium-matching intent is not sufficiently enforced at execution. The selector chooses the QQQ contract on the signal date, targeting 6 × SPY bid, but entry may occur on the next common session with the same exact contracts. No actual-entry mismatch limit skips a trade. All 392 signals entered in each arm even though median premium-match percentages at entry were only 70.86% (1:3 arm's shared QQQ leg) and 69.13% (1:6 arm). The 1:6 average entry credit was about USD 1,399.79 vs. QQQ debit USD 916.12; the strategy was not near debit/credit neutral on the actual entry quotes.
4. The tested overlay buys TAIL for every resolved option cohort and closes TAIL at that cohort's exit. It does **not** test a predeclared risk-triggered hedge, nor a continuously held account-level TAIL allocation.
5. The prior ~10% annualized method most closely matching the repository's record is the **Original Hybrid source-aligned reference**, documented as 12.7049% CAGR / -23.1837% daily MTM MaxDD / USD 276,508 terminal NAV. However, the terminal README and reconstruction contract explicitly state that exact historical reconstruction is still pending: source-visible original contract identities, exits, execution/friction rules and frozen reference vectors are not all available. Treat 12.7049% as a historical reference claim, not a presently re-certified result.

## 2. Paired TAIL overlay snapshot

Window 2018-03-01 to 2025-12-15; 391 resolved episodes per ratio; exact-date TAIL-price pairing coverage 100%.

| Metric | 1:3 no TAIL | 1:3 + USD 1,000 TAIL / cohort, 10 bps | 1:6 no TAIL | 1:6 + USD 1,000 TAIL / cohort, 10 bps |
|---|---:|---:|---:|---:|
| Total episode P&L | -33,466.20 | -34,327.04 | -16,768.10 | -17,663.04 |
| Mean net P&L / episode | -85.59 | -87.79 | -42.89 | -45.17 |
| Median net P&L / episode | -10.20 | -8.48 | +286.90 | +275.84 |
| Win rate | 49.10% | 48.59% | 75.45% | 75.45% |
| Worst episode | -10,629.20 | -10,482.78 | -26,768.10 | -26,636.95 |
| Improvement of the original worst episode | — | +146.42 | — | +131.15 |
| Sum episode P&L / 7.792 years | -4,294.90/year | -4,405.37/year | -2,151.94/year | -2,266.79/year |

At USD 2,500 per cohort and 10 bps friction, total episode P&L becomes -USD 35,618.30 for 1:3 and -USD 19,005.46 for 1:6; the original worst episode improves by USD 366.05 and USD 327.86 respectively. These are episode sums—not an account return or CAGR.

## 3. What the TAIL output does and does not establish

- Correct calculation unit: each resolved option episode's net P&L plus TAIL's same-date adjusted-close return on its assigned notional, less the assumed friction.
- Price source: Yahoo Finance TAIL adjusted close, saved in \`TAIL_adjusted_close.csv\`; source URL, retrieval timestamp and raw-response SHA-256 are in \`source_manifest.json\`. These are adjusted-close return proxies, not verified executable bid/ask fills.
- 0 / 10 / 25 / 50 bps are assumed friction sensitivities, not historically reconstructed TAIL spreads.
- Because overlapping cohorts each get their own TAIL notional, total TAIL capital tied up at any one time is not constrained. No portfolio NAV, assignment cash, margin or forced liquidation is modeled.
- A positive TAIL return on a losing option episode is not equivalent to material loss coverage: at USD 1,000 per cohort and 10 bps, TAIL was positive on 75/199 losing 1:3 episodes and 69/96 losing 1:6 episodes, but offset at least 25% of only 6/199 and 5/96 losses. Positive TAIL gains on losing episodes were only about 1.81% / 1.01% of the respective gross core-loss dollars, before counting negative TAIL episodes.
- No formula arithmetic defect was identified in the paired overlay calculation. The material issue is **interpretation / execution design**: these are overlapping per-cohort diagnostics, not a capital-constrained strategy account, and actual-entry premium matching is loose.

## 4. Locate the previous ~10% method

### Original Hybrid reference

- Source-visible terminal policy sketch: 42% QQQ core; VXX seller target 18% NAV in ordinary low-VIX / positive-contango state, reduced to 10% at high VIX, and cut when VX term structure is backwardated; separate QQQ far-call and VXX call-spread budgets; QQQ/VXX option rolling gates are present in the terminal engine.
- Recovered archive policy code: \`JUN-ZS/timber-blade-kind-dawn\` \`src/engine/policy.ts\` uses a 42% QQQ core with a QQQ far-OTM credit-call spread and VXX carry/call legs; \`src/engine/book.ts\` prices option legs using Black–Scholes with bid/ask haircuts. \`src/engine/radar.ts\` defines \`ivQqq = clamp(1.08 × VIX/100, ...)\`, a VIX-derived VXX IV proxy, and a term-slope proxy \`M1=VIX\`, \`M2=M1 × (1 + 0.10 × tanh((VIX_MA20−VIX)/6))\`. Those are modeled option prices and synthetic term structure—not historical option-chain bid/ask or actual VX futures for every date.
- Documented reference: 12.7049% CAGR, -23.1837% daily MTM MaxDD, USD 276,508 final NAV.
- Verification caveat: the terminal README labels these figures reference metadata, not live targets/proof of profit. The reconstruction contract says exact parity is pending the original option identities, exit paths, execution/friction rules and frozen reference vectors. PR #80 explicitly says the 12.7049% result is not re-certified by the terminal implementation.
- The PR #84 REAL VX workflow (run \`38842695919\`, job \`116786164471\`) successfully built 2,143 Cboe VX M1/M2 rows, completed the source-swap diagnostic, and ran the 1,540-row historical state replay; however, it did **not** run an account-level option P&L / NAV replay. The job's final artifact upload failed because GitHub Actions artifact storage quota was exceeded. Its source-swap output reported 1,036 overlaps, 99.42% term-sign agreement, 99.52% state/action agreement (5 state/action mismatch rows), while the stricter numeric-overlap gate failed: term-sign mismatch rate 1.0618% vs. <=1% limit and the M1/M2 ±0.10-point matching tests did not pass. This is useful data/state evidence, not a reproduction of the 12.7049% CAGR.
- A separate masked reconstruction audit of the VIX/MA20 term proxy reported only 60.19% term-sign agreement and approximately 64.72% archive action agreement against observed historical M1/M2. Do not silently treat the proxy term slope as observed VX futures data.

### Do not confuse it with later experiments

- Separate \`QQQ_HYBRID_DOWNSIDE_CONVEXITY_V1\`: 42% QQQ core + a 2%-NAV 25Δ/10Δ protective QQQ put spread, real option-chain bid/ask, 2018-03 to 2025-12. Its previously observed always-on version reported CAGR 3.67%, MaxDD -17.17%, 210 cycles and realized hedge P&L -USD 82,992; that is not the 12.7049% Original Hybrid reference.
- Separate Pulse V2.2 derived put overlay: the repo's current backtest report shows full-sample CAGR 7.02%, OOS CAGR 11.64%, OOS MaxDD -28.59%; option pricing is derived from VIX as IV and a 10% spread haircut is estimated, not OPRA. It fails its stated 12% CAGR / -5% MaxDD gate.
- The QQQ/SPY put-ratio episodes here are a third, different method. Their negative total episode P&L cannot validate or refute Original Hybrid CAGR because they have different rules, position accounting, periods and metrics.

## 5. References

- TAIL report: \`TAIL_OVERLAY_REPORT.md\`
- TAIL input/provenance: \`TAIL_adjusted_close.csv\`, \`source_manifest.json\`
- Original Hybrid terminal reference and rules: \`terminal/qqq_hybrid_deployment_v2/README.md\` and \`RECONSTRUCTION_CONTRACT.md\` on branch \`feat/qqq-hybrid-terminal-v2-secondary-vx-golden-20261006\`.
- Original Hybrid exact-parity status: PR #80.
- Separate real-chain put-spread experiment: \`research/QQQ_HYBRID_DOWNSIDE_CONVEXITY_V1_README.md\` on branch \`research/qqq-hybrid-downside-convexity-v1-20260929\`.
- Separate V2.2 derived-overlay report: \`artifacts/backtest-report.md\` on the repository default branch.

## 6. CI status caveat

The output-generating commit is \`c49b35b47d19fa527818f4ad8beb4788da6b1cee\`, authored by \`github-actions[bot]\`. At audit time, associated Actions runs \`40178260393\` (TAIL workflow #11) and \`40178260405\` (DTE14 replay workflow #22) returned \`action_required\`, and the jobs endpoint returned no jobs for either run. The audit-document-only commit was added afterward; it does not change replay code or recalculated metrics. Therefore, do not treat the current branch as having a fully verified latest CI PASS until the associated required-action state is resolved and a run with actual jobs concludes successfully.
