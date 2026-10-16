# QQQ FAR CALL Paired NAV Diagnostic — Run #36

**Decision: FAILS CURRENT INCREMENTAL-VALUE SCREEN; KEEP RESEARCH-ONLY.** Do not tune thresholds to rescue the result and do not integrate into Frozen Original Hybrid.

## Evidence and run identity

- Actions: https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38088699286
- Code commit: https://github.com/JUN-ZS/brush-timber-mountain-brook/commit/565fd0f85b831239516147c8c1c38a944c582a42
- Workflow job completed successfully; offline regressions and SHA-pinned replay passed.
- The Actions artifact upload failed because repository artifact storage quota was full. Values below were transcribed from the actual completed job log, not from a downloadable artifact.
- Observed QQQ option-chain window: 2018-03-01 through 2025-12-15; requested source window extended to 2025-12-31.
- This is a 42% QQQ total-return proxy plus static 58% cash control against the QQQ far-call overlay, not the full QQQ/VXX Hybrid. EOD quote-side marks are not confirmed fills.

## Matched-day NAV differences vs no-call control

Differences are overlay marked NAV minus no-call baseline NAV on dates where both values exist. Missing dates are excluded, never interpolated. These are descriptive matched-date diagnostics, not a complete return series.

| Budget | Slippage per leg | Commission per contract per side | Matched dates | Unmatched dates | Last matched date | Last NAV difference | Minimum observed difference | Maximum observed difference | Positive mark days |
|---|---:|---:|---:|---:|---|---:|---:|---:|---:|
| Source max-loss 0.8% NAV | $0.000 | $0.00 | 1947 | 24 | 2025-12-15 | -$5,552.00 | -$5,926.00 | $88.00 | 32/1947 |
| Source max-loss 0.8% NAV | $0.000 | $0.65 | 1947 | 24 | 2025-12-15 | -$5,976.80 | -$6,345.60 | $77.60 | 30/1947 |
| Source max-loss 0.8% NAV | $0.025 | $0.00 | 1947 | 24 | 2025-12-15 | -$6,646.00 | -$7,000.00 | $43.00 | 26/1947 |
| Source max-loss 0.8% NAV | $0.025 | $0.65 | 1947 | 24 | 2025-12-15 | -$7,103.60 | -$7,452.40 | $35.20 | 24/1947 |
| Source max-loss 0.8% NAV | $0.050 | $0.00 | 1947 | 24 | 2025-12-15 | -$8,492.00 | -$8,826.00 | $18.00 | 12/1947 |
| Source max-loss 0.8% NAV | $0.050 | $0.65 | 1947 | 24 | 2025-12-15 | -$8,942.20 | -$9,271.00 | $12.80 | 10/1947 |
| Source max-loss 0.8% NAV | $0.100 | $0.00 | 1947 | 24 | 2025-12-15 | -$11,268.00 | -$11,697.00 | $9.00 | 3/1947 |
| Source max-loss 0.8% NAV | $0.100 | $0.65 | 1946 | 25 | 2025-12-15 | -$11,369.20 | -$11,795.60 | $1.20 | 1/1946 |
| Legacy credit 1.2% NAV | $0.000 | $0.00 | 1947 | 24 | 2025-12-15 | -$64,993.00 | -$72,682.00 | $2,374.00 | 30/1947 |
| Legacy credit 1.2% NAV | $0.000 | $0.65 | 1947 | 24 | 2025-12-15 | -$71,984.40 | -$79,309.80 | $2,201.60 | 27/1947 |
| Legacy credit 1.2% NAV | $0.025 | $0.00 | 1947 | 24 | 2025-12-15 | -$84,367.00 | -$91,029.00 | $1,540.00 | 14/1947 |
| Legacy credit 1.2% NAV | $0.025 | $0.65 | 1947 | 24 | 2025-12-15 | -$90,536.20 | -$97,135.80 | $1,195.60 | 13/1947 |
| Legacy credit 1.2% NAV | $0.050 | $0.00 | 1947 | 24 | 2025-12-15 | -$111,035.00 | -$116,528.00 | $567.00 | 6/1947 |
| Legacy credit 1.2% NAV | $0.050 | $0.65 | 1947 | 24 | 2025-12-15 | -$117,971.40 | -$123,166.00 | $435.20 | 6/1947 |
| Legacy credit 1.2% NAV | $0.100 | $0.00 | 1947 | 24 | 2025-12-15 | -$144,091.00 | -$148,750.00 | $0.00 | 0/1947 |
| Legacy credit 1.2% NAV | $0.100 | $0.65 | 1948 | 23 | 2025-12-15 | -$148,175.40 | -$152,808.40 | $0.00 | 0/1948 |

The control holds the same 42% QQQ core total-return proxy and static 58% cash but has no option trades. Option overlay marks include the conservative zero-wing-Bid floor where present. Since dates with missing marks are excluded, this table is a measurement/attribution diagnostic only; it cannot establish a complete portfolio CAGR or drawdown.

## Interpretation

1. Under the source max-loss budget, all tested slippage/commission scenarios show negative terminal matched-date NAV differences. At zero extra costs, the final difference is -$5,552 and only 32/1,947 paired mark days are positive.
2. Adverse execution-cost assumptions worsen the observed difference. These costs are scenario assumptions, not measured fills.
3. The legacy 1.2% NAV credit sizing is not equivalent to the 0.8% maximum-loss budget; its losses are much larger and it should not be treated as a comparable risk budget.
4. A matched-day difference series is not a complete portfolio return series. It does not establish CAGR, MaxDD, Sharpe, ES95, statistical significance, or executable strategy edge.
5. Remaining unmatched mark sessions and the terminal source gap must be handled through source recovery or explicit blocked status, never interpolation or forward-fill.
6. The 2018–2025 data have been inspected; this is development evidence, not a virgin holdout.

## Next research gate (pre-declared, no parameter fishing)

- Freeze the no-overlay control and sizing definitions.
- Split the overlay effect into entry credit/selection, mark-to-market, exit lifecycle, and costs, using trade/event-level cash-flow accounting.
- Reconcile the complete daily capital path and unresolved terminal position before any performance metric is computed.
- Use a genuinely untouched later period or prospective paper-tracking for confirmation; do not reuse the inspected period as an out-of-sample claim.
- If the economics remain negative after data completeness and accounting are resolved, retire the FAR CALL overlay from the candidate Hybrid rather than optimize stop thresholds.

## Guardrails

- Keep PR #99 Draft/research-only unless separately reviewed.
- Do not merge into main, alter Frozen Original Hybrid, change live sizing, or enable broker orders.
- Artifact quota failure does not invalidate the completed replay, but means detailed generated CSVs are not retained as downloadable run artifacts.
