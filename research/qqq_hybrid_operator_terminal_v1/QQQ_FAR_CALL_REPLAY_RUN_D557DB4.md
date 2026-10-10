# QQQ Far-Call Listed-Contract EOD Replay — Run D557DB4

**Research ID:** `QQQ_FAR_CALL_LISTED_CONTRACT_EOD_REPLAY_V1`  
**Replay code commit:** `d557db4a83befd76e88a72fd1ce9214522bd3636`  
**GitHub Actions run:** https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38028967333  
**Status:** Replay script and 13 offline regressions passed. The job's final artifact-upload step failed because the repository's GitHub Actions artifact-storage quota was exhausted. The replay itself completed and printed the summary below. The workflow was subsequently patched so artifact-quota failure will not mask test/replay success; missing local outputs are checked separately.

## Decision-level result

The tested QQQ call-credit overlay did **not** show positive closed-trade incremental P&L in any of the 16 tested cost/budget combinations. This is a negative result for the current rules and source, not proof that every QQQ call-credit structure is unprofitable. The overlay is not promoted to the frozen hybrid or live sizing.

- Initial capital: USD 100,000.
- QQQ core sleeve: 42% adjusted-close total-return proxy; kept separate from raw nominal QQQ option-strike geometry.
- Contract choice: actual listed QQQ calls, a 20–40 calendar-DTE expiry nearest 30 DTE, source Delta targets 0.16 short / 0.08 wing, same expiry and listed strikes.
- Point-in-time constraint: contract IDs/expiry/strikes selected at signal close (t); on (t+1), only those exact contracts may be repriced. Missing/invalid contracts are skipped, not substituted.
- Entries use short Bid minus long-wing Ask; exits use short Ask minus long-wing Bid, plus explicit per-leg slippage and per-contract commission scenarios. A quote-side replay is not an exchange-confirmed fill.
- No CAGR, daily MTM MaxDD, Sharpe, or ES95 is claimed because the option observation path contains missing marks and ends before the requested window.

## Closed-trade result by scenario

Amounts are USD. P&L is the sum for **closed spreads only**; it excludes any terminal open position.

| Budget interpretation | Slippage per leg | Commission per contract per side | Opens | Closes | Closed-trade net P&L | Mean per closed trade | Open/unresolved at end | Missing position marks |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Source max-loss budget: 0.8% NAV | $0.000 | $0.00 | 106 | 105 | -4,255.00 | -40.52 | 1 | 273 |
| Source max-loss budget: 0.8% NAV | $0.000 | $0.65 | 106 | 105 | -4,643.00 | -44.22 | 1 | 273 |
| Source max-loss budget: 0.8% NAV | $0.025 | $0.00 | 107 | 106 | -5,136.00 | -48.45 | 1 | 253 |
| Source max-loss budget: 0.8% NAV | $0.025 | $0.65 | 107 | 106 | -5,583.20 | -52.67 | 1 | 253 |
| Source max-loss budget: 0.8% NAV | $0.050 | $0.00 | 107 | 106 | -6,895.00 | -65.05 | 1 | 253 |
| Source max-loss budget: 0.8% NAV | $0.050 | $0.65 | 107 | 106 | -7,382.80 | -69.65 | 1 | 253 |
| Source max-loss budget: 0.8% NAV | $0.100 | $0.00 | 108 | 108 | -11,281.00 | -104.45 | 0 | 258 |
| Source max-loss budget: 0.8% NAV | $0.100 | $0.65 | 108 | 108 | -11,379.60 | -105.37 | 0 | 254 |
| Legacy credit budget: 1.2% NAV | $0.000 | $0.00 | 106 | 105 | -49,316.00 | -469.68 | 1 | 284 |
| Legacy credit budget: 1.2% NAV | $0.000 | $0.65 | 106 | 105 | -57,206.60 | -544.82 | 1 | 284 |
| Legacy credit budget: 1.2% NAV | $0.025 | $0.00 | 107 | 106 | -70,119.00 | -661.50 | 1 | 264 |
| Legacy credit budget: 1.2% NAV | $0.025 | $0.65 | 107 | 106 | -76,622.80 | -722.86 | 1 | 264 |
| Legacy credit budget: 1.2% NAV | $0.050 | $0.00 | 107 | 106 | -99,334.00 | -937.11 | 1 | 264 |
| Legacy credit budget: 1.2% NAV | $0.050 | $0.65 | 107 | 106 | -107,840.40 | -1,017.36 | 1 | 264 |
| Legacy credit budget: 1.2% NAV | $0.100 | $0.00 | 107 | 107 | -142,282.00 | -1,329.74 | 0 | 229 |
| Legacy credit budget: 1.2% NAV | $0.100 | $0.65 | 97 | 97 | -147,984.40 | -1,525.61 | 0 | 216 |

## Data and markability

- Expected sessions: 1,971 (2018-03-01 through 2025-12-31).
- Sessions with option-chain rows: 1,956.
- Last observed option-chain date: 2025-12-15; 11 terminal trading sessions through 2025-12-31 have no source observations, plus 4 missing sessions earlier in the period.
- Pair-selection statuses: 1,953 selected pairs; 15 sessions with no chain; 2 sessions with no valid standard QQQ calls; 1 session without a valid positive-credit vertical.
- All eight annual option Parquet files and the pinned underlying/universe/model/helper sources passed the run's byte/Git-blob integrity checks.
- Aggregate mark statuses: 1,698 `OK`; 257 `INVALID_EXIT_QUOTE`; 5 `CONTRACT_ROW_MISSING`; 11 `CORE_TOTAL_RETURN_PRICE_MISSING` (1,971 sessions total). About 13.8% of the daily path is unmarked.
- The public mirror describes its option snapshot as 4:00 p.m. US Eastern; exact tick timestamp and execution feasibility remain unverified.

## Interpretation and next experiment

1. Keep `SOURCE_MAX_LOSS_0P8PCT_NAV` and `LEGACY_CREDIT_1P2PCT_NAV` as distinct policies. A percent-of-credit budget is not a max-loss budget: the 1.2% credit interpretation allowed much larger defined-risk exposure and produced materially worse closed-trade losses.
2. Do not tune a new universal credit coefficient to these aggregate outcomes. First produce a trade-level loss decomposition: entry credit, exit debit, maximum-loss utilization, Delta drift, quote-quality/mark gap, expiry settlements, and P&L by volatility/trend regime.
3. Reconstruct marked NAV only after the missing quote/underlying sessions are addressed or are explicitly treated as an incomplete path. Until then, return/drawdown metrics remain blocked.
4. This experiment has no VXX-option history and is not the original full QQQ/VXX Hybrid. No strategy, main branch, live sizing, or broker-order permission was changed.

