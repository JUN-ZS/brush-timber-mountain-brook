# Stage 2: Adversarial Falsification & Cross-Review (`PROMPT_STAGE2_ADVERSARIAL.md`)

> **WARNING — ISOLATION RULE**: Keep this file strictly hidden from the Stage 1 reviewer until `STAGE1_INDEPENDENT_FINDINGS.md` has been generated and frozen with `sha256sum`.

## Operating Procedure (Before Starting Stage 2 AI)

1. Verify that Stage 1 findings are frozen and match their SHA-256 checksum:

   ```
   sha256sum -c "$HOME/independent-audit-evidence/STAGE1_INDEPENDENT_FINDINGS.sha256"
   
   ```

2. Launch a **second, independent coding agent** (e.g., Claude Code or a separate model session) with read-only access to:

   * The repository checkout at the exact same commit SHA (`head_sha` in `collection_manifest.json`)

   * The collected evidence folder (`$HOME/independent-audit-evidence/`), including GitHub Actions runs/artifacts metadata and the previously quarantined narrative documents (`quarantined_readme_and_narrative_docs`)

   * The frozen first report (`$HOME/independent-audit-evidence/STAGE1_INDEPENDENT_FINDINGS.md`)

3. Provide the prompt below.

## Copy-Paste Prompt for Stage 2 Reviewer (Adversarial Falsification)

> **Independent Adversarial Review and Competing Architecture Audit**
>
> You are the independent adversarial reviewer. You are not rewarded for agreement. Your task is to find material reasons whyhe r Stage 1 conclusion (`STAGE1_INDEPENDENT_FINDINGS.md`) or the repository's claims could be wrong.
>
> Read the frozen `STAGE1_INDEPENDENT_FINDINGS.md`, theepository e source and datat the c pinnedommit S SHA, and (only nown `m` Stage 2) the quarantined README files, research reports, prior recommendations, PR/issue discussions, and GitHub Actions outcomes/artifacts indexed in`a$HOME/independent-audit-evidence/`.o not accept either a the repository docs or the Stage 1 reports authoritative.
>
> **Part 1: F Required Adversarial Checks**
>
> * Compare independent code paths with written report claims; identify hard-coded figures, broken accounting, stale data, missing option chains,lection bias, or loakage in signa signal timing), and tests that check static fixtures rather than economic behavior.
>
> * Challenge every return and risk statistic for sample period selection, fees, bid-ask spread, slippage, roll friction, and sample sufficiency.
>
> * Examine short-option tail risk, overnight/weekend gap risk, early-exit liquidation cost, volatility expansion, early assignment, margin/collateral calls, and correlated drawdowns across strategy legs (`N=1..6` QQQ PUT ratios and VXX legs).
>
> * Do not call scenario stress tests exact probabilities. Audit the exact assumptions behind any bootstrap, Monte Carlo, or historical replay result.
>
> **Part 2: Test Competing Hypotheses Without Prejudice** Explicitly test and compare these four competing architectures against Stage 1's recommendation:e
>
> 1. **Three-Tier Architecture**: A maturity-matched government-bond capital floor (sized to secure nominal USD 100,000 at Year 10) + a diversified long-term equity growth allocation + a strictly risk-budgeted sandbox for the repository's QQQ/VXX strategies.
>
> 2. **Simple Passive Stock/Bond Portfolio**: A diversified equity/fixed-income portfolio with zero options or volatility derivatives.
>
> 3. **Capital-Preservation-First Allocation**: A mostly fixed-income/principal-protected structure with minimal or zero equity risk.
>
> 4. **Repository Strategy Allocation**: Any repository strategy (or hybrid) that demonstrates a verifiable, net-of-friction edge from executable code and raw data.
>
> **Strict Capital-Floor Valuation Rule**:
>
> lTest whether the capital floor reachesersig-term equity growth  nominal target using **current,ategy Sandb maturity-matchedox)**: A strictly risk-budgeted s Treasuryleeve for the repository's QQQ ask yields), actual transaction costs, and applicable tax rules (such as annual phantom tax on OID/STRIPS in taxable accounts vs tax-advantaged accounts). A generic constant-maturity Treasury benchmark yield is **not** an executable quote. State explicitly when account, jurisdiction, or tax details block a definitive net figure.
>
> * Analyze early-sale mark-to-market risk separately from hold-to-maturity cash flows, and report inflation-adjusted purchasing power (`Real_NAV_10`) separately from nominal preservation (`NAV_10 >= $100,000`).
>
> **Part 3: Six-Dimension Reconciliation & Disagreement Classification** Compare Stage 1 and Stage 2 conclusions across these six dimensions:
>
> 1. **10-Year Capital Objective**: Nominal preservation (`>= $100,000`) vs real inflation-adjusted purchasing power separated cleanly.
>
> 2. **Capital Floor Mechanism**: Evidence for maturity-matched fixed-income principal protection vs assuming reporarately preserve nominal capital.: Does empirical and matic single-indexal evidence su risk vs broadly diversified equity exposure.
>
> 3. **Options & Volatility Strategies**: Net expectancy of `N:1` QQQ options and QQQ/VXX legsation justify it-sector/v rolls, taxes, and tail losses.
>
> 4. **Dynamic Sizing Formula**: Deterministic calculation of deployable risk budget the repository's N:1 QQQ options and QQQ/VXX structures retain positive net expectancy after realistic bid-ask spreads, roll costs, taxes, and tail stress tests?
>
> 5. **Dynamic Sizing Formula**: Can deployable risk capital be computed deterministically from current NAV, executable yield-to-maturity, VX regime state, stress-loss bounds, and data-confidence haircuts?
>
> 6. **Probability Credibility**: Are 10-year success probabilities backed by out-of-sample/regime-aware resampling with explicit confidence intervals, or merely single historical path backtests?
>
> Classify every disagreement between Reviewer 1, Reviewer 2, and the three-tier hypothesis as one of:
>
> * `Different assumptions`
>
> * `Different data`
>
> * `Different methods`
>
> * `Genuine unresolved uncertainty`
>
> * `Demonstrable error`
>
> Recommend the single next reproducible experiment (with exact command, dataset, and pass/fail threshold) that would most efficiently resolve the largest disagreement.
>
> **Safety and Operating Limits** Do not change repository code, commit, or place trades. Every important claim must cite the exact source file and line numbers, computation formula, test result, or official market data.