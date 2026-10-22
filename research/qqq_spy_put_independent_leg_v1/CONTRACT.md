# QQQ LONG PUT / SPY SHORT PUT — Independent-Leg Sizing V2

Research-only: separate single-leg quote-side replay, fixed-pair depth replay, and comparison against the frozen equal-premium baseline.

## Scope
- Freeze the 44 contract cohorts selected by the prior study; no fresh strike search or P&L-selected contracts.
- QQQ LONG PUT standalone: fixed N=1–9; SPY SHORT PUT standalone: fixed N=1–9.
- Paired fixed N:M grid: N>=1, M>=1, N+M<=9.
- Use the exact selected contract IDs. Entry attempts start on the next common session after the signal and can defer until expiry/source end.
- QQQ enters Ask/exits Bid; SPY enters Bid/exits Ask. Standalone quote availability and depth depend only on that leg. Pair entry/exit requires both legs.
- Costs include zero, base USD 0.05/share/side + USD 0.65/contract/side, and adverse USD 0.10/share/side + USD 0.65/contract/side.
- Unresolved and entry-skipped cases stay separate; never replace them with zero.

## Why independent exits matter
A QQQ long put can exit when its own QQQ bid/depth is adequate, regardless of SPY's quote/depth. A SPY short put uses its own SPY ask/depth. Pair trades remain coupled. This removes the opposite-leg dependency from standalone results.

## Integrity and limitations
The selected cohort, trade outcome and summary inputs are checked against Git blob SHAs; annual option files and underlying files are re-used only after byte count and Git blob SHA checks. Those hashes identify mirror files but do not prove OPRA/exchange authenticity. EOD depth is not a guarantee of fills. Fixed N:M does not mean equal premium or equal risk; debit, credit, mismatch and match score are included. No early assignment, margin, forced liquidation, financing, taxes, compounding or intraday path is modeled.
