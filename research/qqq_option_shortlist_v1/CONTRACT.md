# QQQ Option Shortlist Replay V1 — Measurement Contract

**Status:** Draft research only. This job does not change main, Frozen Original Hybrid, live sizing, or broker permissions.

## Fixed comparison design

- Data: SHA-pinned public QQQ EOD option snapshots plus the repository's QQQ/VIX daily series, 2018-03-01 through the last verified chain date 2025-12-15.
- Signal: QQQ close is at least 2.1% below rolling MA20 on the current and prior sessions, QQQ closes up on the signal day, and repository VIX is below its value five observed sessions earlier. Signals are cooled down to keep event windows non-overlapping.
- Timing: signal after day-t close; select contracts from the day-t chain; enter with the same contract IDs no earlier than day t+1. Exit after 10 observed sessions, using the first valid side-quote close, deferred at most 3 observed sessions. No quote is forward-filled.
- Structures: 50-delta LONG CALL / 10-delta SHORT CALL debit vertical; the same vertical plus one 10-delta LONG PUT at the same expiry; and PUT ratios using LONG abs-delta near .30 versus SHORT abs-delta near .10, testing 1:N and N:1 for N=1..6.
- Quote model: actual displayed Bid/Ask sides, displayed-size checks on open and close, standard QQQ OCC-style roots/expiry/strike consistency, standard-strike grid, $0.05/share/leg/side slippage and $0.65/contract/side assumed commission.
- Risk: compute worst expiry-intrinsic payoff over all payoff knots using the actual entry-side cash flow. Illustrative $80,000 NAV tail-risk budgets 0.5%, 1%, and 2% are capped by observed entry quote depth. They are not broker margin or a hard bound on interim liquidation loss.

## Separate outcome classes

- QQQ Core control: matched 10-session underlying return, normalized to $1,000 notional. Not an option return.
- Options: fixed-horizon, one-unit episode outcomes, per-leg cashflows, unresolved exits, MAE/MFE from valid daily liquidation marks, terminal payoff risk and depth-limited illustrative sizing.
- Do not label episode win rate as portfolio win rate, terminal-payoff sizing as broker-approved capacity, or this event study as a compounded CAGR/MaxDD backtest.

## Promotion gate

A candidate is only eligible for a later test if it has sufficient resolved events, no material unresolved-mark bias, acceptable net expectancy and tail behavior under adverse costs, and stability under a separate untouched time holdout. This first run is a screening study only.
