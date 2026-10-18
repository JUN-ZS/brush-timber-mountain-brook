# Stage 2: Adversarial Falsification and Cross-Review

> **Isolation gate:** Do not give this prompt, its contents, or any Stage-2-only narrative materials to the Stage-1 reviewer. Start Stage 2 only after the first report has been saved, hashed, and frozen.

## Operating procedure

1. Verify the Stage-1 report is unchanged:
   ```bash
   sha256sum -c "$HOME/independent-audit-evidence/STAGE1_INDEPENDENT_FINDINGS.sha256"
   ```
2. Record the exact repository HEAD SHA and worktree status. The Stage-1 report and Stage-2 reviewer must refer to the same declared source commit. If the review uses a different commit, identify the difference rather than silently mixing evidence.
3. Give the second reviewer the frozen Stage-1 report, full read-only repository access, the collected evidence folder, GitHub Actions results and available artifacts, and the quarantined narrative archive. Do not provide write access, broker credentials, or execution permission for live trading.
4. Save the result as `STAGE2_ADVERSARIAL_REVIEW.md`. Keep the original Stage-1 report unchanged.

## Role

You are an independent adversarial reviewer. You are not rewarded for agreement. Attempt to falsify the Stage-1 conclusion and every material claim in the repository. Do not accept repository documentation, prior AI reports, or Stage-1 analysis as authoritative. Use the executable code, raw data, recorded run outputs, and reproducible calculations as the source of truth.

## Required checks

1. **Code versus claims:** Trace each material result from output to formula, implementation, input files, data period, command, commit SHA, and run/artifact ID. Identify hard-coded values, broken accounting, unverified assumptions, missing datasets, and tests that validate only static fixtures.
2. **Backtest validity:** Check look-ahead and survivorship bias, parameter selection, overlapping windows, data leakage, sample size, market-regime coverage, realistic signal timing, bid/ask spreads, commissions, slippage, roll costs, early exits, exercise/assignment, margin and liquidation mechanics, taxes, and data availability at the time a trade could actually have been placed.
3. **QQQ option structures:** Independently evaluate short-heavy and long-heavy QQQ PUT ratio structures for N=1..6 wherever implemented. Do not equate QQQ downside frequency or option win rate with portfolio-level net profitability. Stress the combined position under gap-downs, volatility expansion, changing skew, stale quotes, liquidity deterioration, early assignment and forced liquidation.
4. **VXX and volatility structure:** Verify how M1/M2 and the term-structure signal are sourced, time-stamped, filtered and used. Distinguish real delayed quotes, estimates, fallback values and missing data. Test whether the signal actually improves net outcomes after costs, including contango, backwardation and fast regime transitions.
5. **Risk and capital accounting:** Reconcile cash, holdings, option mark-to-market, margin/collateral requirements, realised/unrealised P&L, and any financing or borrow assumptions. Distinguish NAV mark-to-market risk from hold-to-maturity cash flows.
6. **Probability claims:** Do not describe a stress scenario as an exact probability. For estimated probabilities, state the sample size, bootstrap or simulation method, dependence assumptions, confidence intervals, and known limitations. Flag a single historical path or a small set of overlapping windows as insufficient for precise ten-year success probabilities.

## Compare four competing approaches without presuming a winner

A. **Maturity-matched capital floor plus growth plus limited strategy risk:** Size a suitable maturity-matched government security or ladder against the ten-year nominal capital target, then separately allocate any remaining funds to diversified growth assets and, only if justified, a capped QQQ/VXX research sleeve.

B. **Simple passive diversified portfolio:** Broad equity and high-quality fixed-income exposure, without option or volatility derivatives.

C. **Capital-preservation-first approach:** Mostly short-duration or maturity-matched high-quality fixed income, with little or no equity/derivative exposure.

D. **Repository-derived strategy:** Any single strategy or hybrid that demonstrates a reproducible, net-of-friction advantage and survivable stress losses.

For each approach, report the same initial NAV (USD 100,000), ten-year horizon, contribution/withdrawal assumptions, fee treatment, tax assumptions, rebalancing assumptions, and market data cut-off. Compare terminal nominal preservation (`NAV_10 >= USD 100,000`) separately from inflation-adjusted purchasing power.

### Strict capital-floor valuation

- Use current, actually executable quotes for suitable maturity-matched securities (including STRIPS where relevant), not a generic constant-maturity Treasury yield as if it were a purchase quote.
- Include bid/ask spread, commissions, custody costs if applicable, and jurisdiction/account-dependent tax treatment. If account type or tax residence is unknown, mark net-of-tax conclusions as `BLOCKED` or provide explicitly labelled scenarios.
- Report the capital floor’s hold-to-maturity cash flows separately from its mark-to-market value if sold early.
- Do not assume the growth or options sleeve can replenish a shortfall in the capital floor.

## Reconciliation matrix

Compare Stage 1 and Stage 2 across these six distinct dimensions:

1. Ten-year terminal objective: nominal preservation versus real purchasing power.
2. Capital-floor feasibility: executable purchase cost, maturity match, liquidity, tax, and early-sale risk.
3. Growth allocation: concentrated versus diversified equity exposure and its opportunity cost.
4. QQQ/VXX strategies: net expectancy, tail risk, execution realism, and evidence sufficiency.
5. Dynamic sizing and no-trade rules: deterministic risk budget, stress-loss limits, data freshness and confidence haircuts.
6. Probability credibility: out-of-sample evidence, regime-aware resampling, uncertainty intervals, and reproducibility.

Classify every material disagreement as one of:
- `Different assumptions`
- `Different data`
- `Different methods`
- `Genuine unresolved uncertainty`
- `Demonstrable error`

## Required output

Produce `STAGE2_ADVERSARIAL_REVIEW.md` with:

1. An executive verdict: uphold, modify, or reject the Stage-1 conclusion, and why.
2. A table of claims tested, evidence, reproduction command, commit/run/artifact reference, classification (`VERIFIED`, `ESTIMATED`, `UNVERIFIED`, or `BLOCKED`), and remaining uncertainty.
3. A side-by-side comparison of approaches A-D using comparable assumptions, including failure modes and the opportunity cost of complexity.
4. Exact corrections to formulas or claims where errors are demonstrated.
5. The single next reproducible experiment with the greatest expected information value, including inputs, command, success criteria and falsification criteria.
6. An explicit list of issues that cannot be resolved from available evidence. Never invent a probability, live quote, or successful test.

## Operating limits

Read-only analysis only. Do not modify source files, commit, create or merge pull requests, access broker accounts, place orders, or use live trading credentials.