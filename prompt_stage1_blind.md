# Stage 1: Blind Independent Derivation Runbook & Prompt (`PROMPT_STAGE1_BLIND.md`)

## Operating Procedure (Before Starting Stage 1 AI)

1. Update your local repository clone and verify a clean working tree:
   ```bash
   cd /path/to/brush-timber-mountain-brook
   git fetch --all --prune --tags
   git rev-parse HEAD
   git status --short --branch
   ```
2. Run the merged read-only evidence collector outside the repository directory and create the blind-safe snapshot (recommended; required for strict Stage-1 isolation):
   ```bash
   python3 /path/to/collect_repo_evidence.py "$PWD" --out "$HOME/independent-audit-evidence" --snapshot --max-file-bytes 25000000 --max-snapshot-mb 100
   ```
   The collector refuses a dirty worktree because file hashes and CSV previews must match the pinned HEAD. This produces two separate archives:
   - `repository_text_snapshot_BLIND_SAFE_HEAD.tar.gz` (safe for Stage 1 blind review)
   - `quarantined_narrative_snapshot_STAGE2_ONLY_HEAD.tar.gz` (withheld until Stage 2)
3. Launch your **first coding agent** (e.g., Gemini CLI) in a **brand-new session**.
   - **Strict Blindness Rule**: do **not** share the Stage 2 prompt, prior AI reports, Git history/commit messages, PR/issue discussions, GitHub run titles, or your preferred portfolio structure with Stage 1.
   - For strict isolation, provide only the blind-safe archive `repository_text_snapshot_BLIND_SAFE_HEAD.tar.gz`, the pinned `head_sha` as a plain value, `collection_manifest.json`, and the data-preview manifest needed to identify coverage gaps. Do **not** expose the live checkout, its `.git` history, the full evidence directory, the GitHub metadata folder, or the Stage-2-only archive.
   - Extract the blind-safe archive into a temporary workspace without a `.git` directory. Analyze the included implementation code, tests, configurations, and data. The archive is bounded: mark any required binary/large data omitted from it as `BLOCKED`, instead of claiming the full repository was inspected.
4. Once Stage 1 completes, save its output to `$HOME/independent-audit-evidence/STAGE1_INDEPENDENT_FINDINGS.md` and freeze its hash:
   ```bash
   sha256sum "$HOME/independent-audit-evidence/STAGE1_INDEPENDENT_FINDINGS.md" > "$HOME/independent-audit-evidence/STAGE1_INDEPENDENT_FINDINGS.sha256"
   chmod 444 "$HOME/independent-audit-evidence/STAGE1_INDEPENDENT_FINDINGS.md"
   ```

## Copy-Paste Prompt for Stage 1 Reviewer (Blind Code-First Review)

> **Independent Ten-Year Capital Preservation and Strategy Review**
>
> **Blinding & Quarantine Protocol**
> 1. First record the checked-out commit SHA (`head_sha` in `collection_manifest.json`) and worktree state.
> 2. **Quarantine Rule**: Do NOT access the full repository checkout, Git history/commit messages, README files, strategy narrative reports, previous AI recommendations, Stage-2 prompt, PR descriptions, issue discussions, GitHub run titles, marketing text, or files listed under `quarantined_readme_and_narrative_docs` until `STAGE1_INDEPENDENT_FINDINGS.md` is completed and frozen. Stage 1 receives only the blind-safe snapshot and minimal manifest; do not try to obtain hidden files or metadata.
> 3. Start strictly with implementation source (`strategy_and_backtest_code`), test code (`configs_and_test_entrypoints`), raw datasets (`data_candidates` and `git/data_files_preview.json`), run commands, configuration, accounting paths, and reproducible calculations. Treat test fixtures and hard-coded expected numbers as assertions to verify, not proof of real-world performance.
> 4. If required inputs cannot be found or reproduced, classify the item as `BLOCKED` or `UNVERIFIED` rather than guessing.
>
> **Mission & Objective**
> Independently examine the repository and determine the most defensible investment architecture for **USD 100,000** over a **10-year horizon** (assuming no additional contributions or withdrawals unless separately modeled).
> - **Primary objective**: maximize the probability that the portfolio's terminal nominal USD NAV at Year 10 is at least USD 100,000 (`NAV_10 >= $100,000`).
> - **Secondary objective**: report terminal inflation-adjusted purchasing power (`Real_NAV_10`) separately. Do not conflate nominal break-even with real break-even.
> - Do not assume any strategy family or portfolio structure must be selected. Compare repository strategies against simple, non-leveraged benchmarks and other feasible allocations that could meet the stated terminal objective. Derive any capital-preservation or dynamic risk-budget mechanisms only if the evidence supports them; do not start from a preselected architecture.
>
> **Repository & Strategy Investigation**
> 1. Map all strategy source files, signals, formula definitions, sizing rules, exit rules, accounting paths, datasets, and tests present in the pinned-HEAD blind-safe snapshot (beyond UI-only changes). Do not inspect historical commit messages or branch-only source before the report is frozen. If branch-only or historical implementations could materially change the conclusion, record that comparison as `BLOCKED until Stage 2`.
> 2. Separate implemented code behavior from docstrings/comments and intended behavior.
> 3. Reproduce material headline results where possible. Record exact command, data period, source files, commit SHA, and run identifier.
> 4. Check for look-ahead leakage, parameter selection bias, survivorship bias, stale/missing option chains, quote availability, realistic entry/exit timing, bid-ask spread, commissions, slippage, early assignment/exercise, margin/liquidation rules, tax drag, and adverse market regimes.
> 5. Examine both **short-heavy and long-heavy QQQ PUT ratio structures** (`N=1..6` where implemented), QQQ concentration risk, and all **VXX / VX volatility-term-structure components**. Do not assume the underlying ETF's probability of decline equals option strategy P&L probability.
> 6. Evaluate early-sale market-value risk, credit risk, reinvestment risk, liquidity, complexity, and opportunity cost. Do not invent exact probabilities; state the sample size, resampling method, regime assumptions, and limitations.
>
> **Required Output (`STAGE1_INDEPENDENT_FINDINGS.md`)**
> 1. **Executive Conclusion & Candidate Architecture**: Independently derived allocation architecture, if the evidence supports one.
> 2. **Ranked Strategy Comparison**: Repository candidate strategies compared against sensible non-leveraged benchmarks after costs and risk.
> 3. **Evidence Table**: Every major claim classified as `VERIFIED`, `ESTIMATED`, `UNVERIFIED`, or `BLOCKED`, with exact file path, line numbers, command/run ID, input period, and limitations.
> 4. **Dynamic Sizing & Reallocation Formulas**: Exact mathematical formulas, variable definitions, and explicit **no-trade / circuit-breaker conditions**.
> 5. **Stress Tests & Data Gaps**: Multi-regime stress-test ranges, missing data, and the single next reproducible experiment with the highest value of information.
> 6. **Falsification Criteria**: What concrete evidence would cause you to change your recommendation.
>
> **Safety and Operating Limits**
> Read-only review only. Do not modify source files, commit, open or merge pull requests, access broker accounts, place orders, or use live trading credentials.