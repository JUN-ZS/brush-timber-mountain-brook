# Daily portfolio NAV and maximum drawdown — DTE20 / exit DTE <= 4

- Replay period: 2018-03-01 through 2025-12-12; 1959 common-session marks per phase.
- Options: QQQ LONG PUT 1 : SPY SHORT PUT 6 (target abs-Delta 0.25) plus QQQ LONG CALL 1 : SPY SHORT CALL 6 (target abs-Delta 0.20).
- Entry: DTE20 band 14-26, no filter, every 10 common sessions with independent phases 0/2/4/6/8. Exit trigger is remaining calendar DTE <=4; exit is deferred until executable quote/size criteria are met.
- Pairing: same signal date, expiry and actual entry date; maximum one matched PUT+CALL basket at a time in each independent phase.
- QQQ holding input: USD 63,694.00 current value, reference close USD 712.20 on 2026-10-26; implied shares 89.4327.
- Historical stock starting value: USD 14,709.90; ending total-return proxy value: USD 57,750.75.
- Stock path is the 2018-03-01 raw QQQ close scaled by HUB adjusted-close ratio (distribution-reinvestment proxy). Options use exact-contract EOD quotes; longs marked at bid, shorts at ask. Missing daily quotes carry forward with stale age flagged.
- Resolved option-leg P&L persists in NAV after exit. Every open option leg is valued daily. Unresolved options reaching expiry receive an intrinsic-settlement proxy; source-end open legs stay marked at last quote.
- Resolved trades deduct USD 0.05/share/side slippage plus USD 0.65/contract/side commission. Expiry settlement proxy deducts entry-side costs only; exercise/assignment fees are not modeled.
- NAV = stock value proxy + cumulative realized option-leg P&L + open option net-liquidation P&L. This is not broker buying power, cash, margin, tax or forced-liquidation simulation.

## Quote/data acceptance

- Entry-leg source quotes reconciled: 2080; resolved exit-leg quotes reconciled: 1754.
- Missing entry quotes: 0; missing exit quotes: 0; price mismatches: 0.
- Resolved two-leg trade P&L reconciled to source replay: 877; mismatches: 0.
- Daily option-leg valuation coverage: 25048/25048 expected leg-session marks; missing/duplicate/unpriced: 0/0/0.
- SHA-pinned option parquet files scanned: 16; source anahatsingh-ui/options-dataset-hist@37f6c456fe1a4775c875673fb8ef907d5cd2fd66.

## Daily NAV and maximum drawdown by independent phase

| Phase | Strict matches | Admitted | Skipped | Start NAV | End NAV | Change | Max DD USD | Max DD % | Peak | Trough | Final realized option P&L | Final open option P&L | Max SPY put obligation | Max SPY call delivery notional | Max stale age |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---:|---:|---:|---:|---:|
| 0 | 183 | 104 | 79 | USD 14,709.90 | USD 99,986.10 | USD 85,276.20 | USD -23,133.93 | -106.91% | 2018-10-01 | 2020-03-23 | USD 40,486.55 | USD 1,748.80 | USD 399,600.00 | USD 418,800.00 | 2 |
| 2 | 177 | 103 | 74 | USD 14,709.90 | USD 18,695.30 | USD 3,985.40 | USD -66,221.54 | -128.76% | 2022-01-03 | 2025-04-08 | USD -40,129.25 | USD 1,073.80 | USD 400,800.00 | USD 420,600.00 | 2 |
| 4 | 183 | 103 | 80 | USD 14,709.90 | USD 43,363.75 | USD 28,653.85 | USD -26,402.45 | -114.80% | 2020-02-21 | 2020-03-20 | USD -14,387.00 | USD 0.00 | USD 397,800.00 | USD 415,800.00 | 2 |
| 6 | 183 | 106 | 77 | USD 14,709.90 | USD 81,748.05 | USD 67,038.15 | USD -32,303.54 | -166.17% | 2020-02-19 | 2020-03-09 | USD 24,400.50 | USD -403.20 | USD 404,400.00 | USD 422,400.00 | 1 |
| 8 | 179 | 104 | 75 | USD 14,709.90 | USD 71,853.80 | USD 57,143.90 | USD -16,738.24 | -82.44% | 2018-10-01 | 2018-12-24 | USD 11,871.25 | USD 2,231.80 | USD 399,600.00 | USD 420,600.00 | 1 |

## Matching / capacity diagnostics

| Phase | PUT entries | CALL entries | Common signals | Same expiry | Same entry | Strict pairs | Admitted | Skipped | PUT-only signals | CALL-only signals |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 196 | 196 | 196 | 186 | 183 | 183 | 104 | 79 | 0 | 0 |
| 2 | 195 | 195 | 195 | 186 | 177 | 177 | 103 | 74 | 0 | 0 |
| 4 | 194 | 195 | 194 | 186 | 183 | 183 | 103 | 80 | 0 | 1 |
| 6 | 196 | 196 | 196 | 191 | 183 | 183 | 106 | 77 | 0 | 0 |
| 8 | 194 | 194 | 194 | 182 | 179 | 179 | 104 | 75 | 0 | 0 |

## Limits

- Five phases are independent robustness runs; do not combine their curves.
- USD 63,694 is treated as current holding value; historical starting stock value is not USD 63,694.
- Gross SPY put assignment obligation and short-call delivery notional are exposure diagnostics, not broker margin. QQQ stock does not contractually cover SPY options.
- EOD quotes are estimates, not verified fills. Intrinsic expiry settlement is a proxy when no executable close is observed.
- Option history ends in December 2025; no 2026 option performance is observed.

Outputs: daily_nav_by_phase.csv; daily_option_leg_marks.csv; phase_max_drawdown_summary.csv; pair_matching_and_capacity_audit.csv; quote_reconciliation.json; daily_nav_max_drawdown_audit.json; replay/.
