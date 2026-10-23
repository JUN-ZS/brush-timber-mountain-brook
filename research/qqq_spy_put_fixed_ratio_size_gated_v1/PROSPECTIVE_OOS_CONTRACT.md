# QQQ/SPY Prospective Out-of-Sample Protocol V1

## Purpose
Move from retrospective 2018-2025 ratio selection to a frozen paper-replay period using quote data strictly after this protocol was committed. Do not retune against the new outcomes.

## Primary candidate and comparators
- Primary descriptive candidate: QQQ LONG PUT 1 : SPY SHORT PUT 3, held 20 common sessions.
- Locked comparators: 2:4, 4:5 and 1:6 at 20 sessions; all four ratios at 10 sessions.
- The 1:3 / 20-session choice reflects the lowest short-put assignment exposure among the tested positive 20-session candidates with comparable in-sample average performance. It is still an in-sample choice, not an established edge.
- All ratios and exits remain frozen for the prospective run. No interim winner can be promoted by changing the ratios, exit policy, signal, DTE or delta parameters.

## Frozen mechanics
- Entry signal: QQQ trailing 20-common-session return below SPY; evaluate at signal close and enter no earlier than next common session.
- One cohort every 45 common sessions.
- Same expiry, DTE 30-60 (target 45); each leg absolute-delta target 0.25 with eligibility 0.10-0.50.
- Fixed whole-contract ratios only; combined contract count <= 9; lock exact contract IDs after signal.
- Use the historical quote-side direction: QQQ LONG enters ask/exits bid; SPY SHORT enters bid/exits ask.
- Require displayed quote size for the full quantity on the relevant side at both entry and exit. Never forward-fill or substitute a contract. Defer on the same contract if size is insufficient; report skipped/unresolved distinctly.
- Base cost: USD 0.05/option-share/side slippage plus USD 0.65/contract/side commission. Also report USD 0.10 slippage stress.
- Primary endpoint is resolved-cohort mean net P&L for 1:3 / 20 sessions, always paired with unresolved count, coverage, worst trade, per-leg contribution, adverse marks and capital/assignment obligation. This is descriptive, not a hard automatic PASS.

## Data contract and current gate
Primary evidence requires post-2025-12-15 EOD options snapshots with bid, ask, bid size, ask size, delta, exact contract identity and underlying closes; every source file must have a SHA-256 hash and documented snapshot convention. Price-only data cannot satisfy the primary execution-screen test.

The historical GitHub preservation mirror used in PR #138 ends in 2025. Public provider documentation reviewed during this step indicates:
- the preservation mirror covers options through 2025;
- OnclickMedia documents its backtester data ending 2026-03-05 and warns that its aggregate data may have gaps/inconsistencies;
- HistoricalData.net publishes current EOD chains with bid/ask and size fields, but the archive is a paid product;
- Cboe's official Option EOD Summary provides EOD bid/ask and size history, also as a purchased product.

No data was purchased and no live broker connection was made. Until a validated quote archive is supplied, the readiness status must remain BLOCKED_MISSING_FRESH_QUOTES; a green protocol test is not a strategy replay or performance PASS.

## Safety
Paper replay only. No broker connection, live orders, app sizing changes, or merge to main.
