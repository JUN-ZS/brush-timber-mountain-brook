# INERTIA DISCOVERY KERNEL — SEED

Status: REFERENCE seed from user (2026-09-08). Deliberately **no predetermined answer**.
Owner for Phase-1 discovery run: **波動** (RelVol archive). Consumer for strategy geography: **QQQ VXX 年化** (ASSOCIATION_ONLY join only).
Credit / Option EV: **SEALED** until real options/snapshots exist (currently 0 rows).

## Purpose
Find: after an observable state, does future behavior deviate from unconditional baseline?
「偏離正常」才叫慣性。Do not presuppose MACD/BOLL/P90-revert/WR>50%.

## Allowed data (Phase 1 — no new Yahoo/API)
- `archive_csv/returns/returns.csv`
- `archive_csv/volatility/thresholds.csv`
- `archive_csv/persistence/persistence.csv`
- `archive_csv/rankings/board_snapshots.csv`
- Options: `archive_csv/options/snapshots.csv` = **0 rows** → no fake historical Option EV

Pack pin when joining warehouse: `7ca13ce290d28db4`

## Core ideas (do not collapse early)
1. INERTIA CREDIT SURFACE — state = percentile + run + shape + threshold; name frequency honestly (`conditional_reversion_frequency`), not「信用」
2. Monotone ladder P80→P90→P95→P99 → MONOTONIC/ACCELERATING/DECELERATING/REVERSING/NOISE
3. Horizon weights: compare equal / sqrt(n) / log(n) / stability / adaptive — judge by **next unseen period**, not in-sample beauty
4. Counter-intuitive scans A–F → math archetypes only (no Personality names)
5. Run-length break points P(revert|run=k)
6. Inertia-of-inertia composites with anti-overfit; train-only lift = `DISCOVERY_ARTIFACT`
7. Credit factors separate: Probability × Payoff × Consistency × Sample × Stability — no premature 0–100
8. 3WIN/1LOSS full payoff table (expectancy, PF, streaks) — WR alone insufficient
9. Search only bins/cond-prob/transition/payoff/stability — no deep models / new indicators / magic formulas
10. Every claim: DISCOVERY / VALIDATION / OOS with STATUS FAILED when collapse
11. **INERTIA PURITY**: how little extra info keeps predictive power (stable under added features > fragile stacked lift)

## Pipeline (never reverse)
OBSERVATION → STATE → TRANSITION PROBABILITY → INERTIA → CREDIT → PAYOFF → OPTION STRUCTURE

## Phase-1 deliverables (6 files)
inertia_candidates.csv, inertia_credit_surface.csv, inertia_transition_matrix.csv,
inertia_stability.csv, inertia_anti_overfit.csv, INERTIA_DISCOVERY_REPORT.md
Each row/result: DATA_SOURCE, DATA_HASH, DISCOVERY_RULE, SAMPLE_COUNT, OBSERVED/VALIDATION/OOS, STATUS

## Final questions
Not「哪隻最好」. Ask: under what observable state does behavior recur abnormally? Can that become positive expectancy? When does it fail? Only then Option structure.
