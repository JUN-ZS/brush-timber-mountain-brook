# Independent Cash-Flow Ledger Replay Contract

The eight-timing preview workflow uses the pinned Stage 2 artifact from run `39546097174` and runs `replay-window-ledger.py` on the Linux BOT before publishing the preview. The replay does not import the production backtest engine.

The replay reconstructs the 157 overlapping ten-year windows for each strategy/cash-flow combination from the frozen adjusted-close panel, applies the documented month-end deposits and withdrawals, performs the anniversary glidepath rebalance, and reconciles per-window NAV/cash-flow fields, yearly NAV marks, annual aggregates, and daily drawdown paths to the source artifact.

A successful audit is expected to cover 1,024 strategy/cash-flow combinations, 160,768 window records, and 11,264 annual summary rows. The final audit JSON exposes those replay counts both in the top-level `cashflow_window_ledger_replay` object (for a stable machine gate) and in its detailed `counters` object.

## Interpretation limits

The 157 ten-year windows overlap and are not 157 independent trials. A pass means the independent accounting replay reconciles to the pinned historical artifact within the declared tolerances; it does not establish predictive validity or guarantee future investment outcomes. Investor XIRR is not independently recomputed by this ledger check.
