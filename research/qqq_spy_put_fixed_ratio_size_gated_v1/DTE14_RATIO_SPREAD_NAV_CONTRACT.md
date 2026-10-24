# DTE14 Ratio Spread NAV Replay — Contract V1

## Question
Can QQQ long PUT 1 : SPY short PUT 3 or 6 produce more than USD 10,000 per year on a single USD 100,000 starting-NAV account when SPY short puts are collateralized with same-expiry SPY far-tail long PUTs?

## Frozen inputs
- Use the DTE14 HOLD_20_OR_DTE_LE_7 base ledger from the source-pinned historical replay; five existing phase schedules, no tuning of entry/exit or contract selection.
- QQQ leg quantity remains 1. SPY short quantity is overridden to 3 or 6 and every entry/exit must pass the displayed side-size gate for that quantity.
- The tail is the already source-pinned TAIL_10_DELTA selection: same entry date, same expiration, exact SPY listed PUT, strike strictly below the short SPY PUT. It is bought at Ask alongside entry to make its spread protection real from inception.
- Starting NAV: exactly USD 100,000; one fixed strategy cohort size per signal; no dynamic size scaling.

## Configurations
- QQQ1:SPY3 with zero tail puts (cash-secured control) and with 3 tail puts (fully paired).
- QQQ1:SPY6 with zero tail puts (cash-secured control), 3 tail puts (half paired), and 6 tail puts (fully paired).
- A tail PUT covers one SPY short PUT only. QQQ puts do not collateralize SPY short puts.

## Capital reserve
For each position, conservative reserve is:
max(short_strike - tail_strike, 0) * 100 * paired_qty + short_strike * 100 * uncovered_qty.
No tail means all short puts reserve strike × 100. Full pairing uses the vertical strike width for each spread. This is a conservative risk-capital proxy, not a claim about any specific broker's margin algorithm. No QQQ/SPY cross-margin offset is assumed.

## Execution and accounting
- Entry/exit at exact selected-contract Ask/Bid; USD 0.05 per option-share per side slippage and USD 0.65 per contract per side commission.
- Tail contract, date, expiry, strike, and Ask must match the locked selection source. Tail ask-side displayed size must support the entire requested tail quantity.
- Exit attempts close the QQQ long, SPY shorts, and tail puts as a package. If any required quote/size gate fails on the scheduled exit date, no package leg is assumed closed later; remaining legs settle to intrinsic at expiry using underlying close, documented as an exercise/immediate-liquidation proxy.
- No forward-fill. NAV is missing on a day if any open-leg mark is unavailable. MaxDD is measured only on observed marks and may understate risk around missing gaps.
- Five phase schedules overlap; summarize their median and range, never sum them as if they were independent accounts.
- No broker order, main-branch merge, forced-liquidation engine, borrowing, interest, financing, taxes, dividends, early assignment fees or verified fills.
