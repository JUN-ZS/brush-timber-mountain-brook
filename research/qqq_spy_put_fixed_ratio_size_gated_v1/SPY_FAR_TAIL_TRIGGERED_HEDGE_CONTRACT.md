# SPY Far-Tail Risk-Triggered Hedge — Research Contract V1

## Objective
Test a predeclared close-based risk trigger that buys a same-expiry far-OTM SPY long PUT only after the frozen QQQ LONG PUT 1 : SPY SHORT PUT 3 cohort has moved against its fixed entry SPY spot. Keep both the no-hedge ledger and the existing unconditional-hedge results as controls.

## Frozen strategy and source
- Baseline anchor commit: c0cc1de3f196a312c00582d9ee9600c689c388d9.
- Base ledgers are read-only. The base signal, contract selection, five-session cadence, quantities and exit logic are unchanged.
- Daily underlying close and historical option chain files are pinned to anahatsingh-ui/options-dataset-hist commit 37f6c456fe1a4775c875673fb8ef907d5cd2fd66.
- This is an EOD preservation mirror. Hashes prove byte identity against the referenced Git blobs, not OPRA provenance or executable fills.

## Predeclared trigger rules
- Trigger A: SPY daily close <= the base cohort's fixed entry SPY spot × 0.97.
- Trigger B: SPY daily close <= the base cohort's fixed entry SPY spot × 0.95.
- Only dates strictly after base entry and strictly before the frozen base exit/last-observed date are eligible.
- A close-confirmed trigger on day T enters no earlier than the next SPY option-chain session T+1. No same-close fill or intraday assumption.
- At next session, select a standard listed SPY PUT with the same expiration as the base SPY short PUT; strike below that session's SPY close; valid quote and positive bid. Rank by closest absolute Delta to target, then ask size, open interest, relative spread and stable contract ID.
- Compare 2.5-delta and 5-delta targets. Both share the same eligible absolute Delta band 0.01–0.08. Test quantity 1 and 3 contracts from the same selected contract. No retry after a blocked next-session entry.
- Close on the original base exit date. Base-unresolved trades stay unresolved; hedge marks are MTM only.

## Fixed costs
- Slippage: USD 0.05 per option share per side.
- Commission: USD 0.65 per contract per side.
- Long tail entry uses ask; exit uses bid. Displayed size is an eligibility screen, not proof of fills.

## Required outputs
- triggered_selection.csv: trigger date, next-session entry, selected contract and exit quote.
- triggered_trade_level.csv: per-trade no-hedge and triggered hedge accounting for all configurations.
- triggered_summary.csv: trigger rate, entry/exit coverage, paired means, win rate, same-worst-base-trade improvement, premium outlay, unpriced positions and common 1x/3x comparison.
- triggered_annual.csv: outcomes grouped by base exit year without pooling overlapping phases.
- triggered_tail_stress.csv: tail-leg-only expiry intrinsic P&L after shock from actual hedge-entry spot.
- SPY_FAR_TAIL_TRIGGERED_HEDGE_REPORT.md: comparison with no-hedge baseline and prior unconditional overlay.

## Interpretation and exclusions
- Five shifted base phases overlap and are not independent samples.
- EOD quotes/sizes are not verified fills; quote availability can select the paired sample.
- Tail stress is not whole-book stress. It excludes updated base SPY short-put market value at trigger, QQQ long PUT, margin, forced liquidation, assignment/exercise fees and financing.
- No live broker orders. No fixed pass threshold. Judge the insurance by realized-P&L drag, same-trade worst-loss change, quote coverage, premium outlay, tail stress and whole-book NAV/margin analysis together.
