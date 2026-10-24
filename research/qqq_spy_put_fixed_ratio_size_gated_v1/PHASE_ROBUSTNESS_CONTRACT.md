# QQQ/SPY 1:3 No-Filter Five-Session Start-Phase Robustness Audit

## Question
The existing in-sample grid shows that a no-filter 5-session cadence with fixed QQQ LONG PUT 1 : SPY SHORT PUT 3 can produce a high summed historical P&L. Before optimizing further, test whether that finding depends materially on the arbitrary first eligible session used to seed the cadence.

## Frozen candidate
- Entry filter: none.
- Fixed ratio: QQQ LONG PUT 1 : SPY SHORT PUT 3.
- Cadence: every 5 common QQQ/SPY underlying sessions.
- Overlapping cohorts explicitly enabled.
- Contract selection: same expiry; DTE 30–60 targeting 45; absolute Delta target 0.25 within the engine's eligibility band.
- Quote-side display-size gates and conservative entry/exit quote sides retained.
- Cost: $0.05 per option share per side slippage plus $0.65 per contract per side commission.
- Exits: 5 sessions, 10 sessions, 20 sessions, and DTE <= 7.
- Historical source/data window stays pinned to the existing replay source, through 2025-12-12 for common option-chain observations.
- Period windows: 1Y 2024-07-23 to 2025-07-23; 3Y 2022-07-23 to 2025-07-23; 5Y 2020-07-23 to 2025-07-23.

## Phase variation
Rerun the full contract-selection and quote-side accounting pipeline for initial phase offsets 0, 1, 2, 3 and 4 common sessions. Each phase must select its own actual signal dates, strikes, contracts, entry quotes and exit quotes. Do not shift the prior P&L rows or reuse the phase-0 trade list.

## Reported outputs
For each phase, each horizon and each exit policy:
- unique opened cohorts; resolved and unresolved counts;
- win rate; mean and median resolved net P&L; cumulative and annualized resolved P&L;
- worst resolved trade and $0.10/share/side slippage stress;
- peak concurrent cohorts and peak summed SPY short-put assignment obligation as an exposure proxy;
- per-calendar-year 20-session-exit P&L and worst calendar-year result.
Include the original phase-0 cadence grid row as a baseline cross-check.

## Interpretation
All phase runs use the same historical data and are still in-sample. Phase variation is robustness analysis, not forward validation. A positive average does not guarantee positive years or bound portfolio losses. P&L is not compounded NAV. The SPY short-put assignment obligation is not broker margin. EOD quote-side estimates and displayed size do not guarantee live multi-leg fills. No execution recommendation is made by this audit alone.
