# QQQ Universal Harvest Bank V19 — ALL real-chain

Research only. Not a live signal. Not part of V2.2.

## Purpose

Test the hypothesis that one N+ Risk-WIN can become a common Bank that slowly buys future rights from multiple real-chain strategies.

A single positive N>2 trade from the strict V16 path is used as an independent historical seed.

## Verified strategy pool

| Node | Source | Entry-risk definition |
| --- | --- | --- |
| RATIO_HARVEST_N2 | real Bid/Ask replay | original terminal-payoff max-loss proxy |
| CONVEXITY_REALCHAIN_ALWAYS_ON | real Bid/Ask replay | vertical debit = defined max loss |
| STATE_ADAPTIVE_GEOMETRY | real Bid/Ask replay | reconstructed entry terminal max-loss proxy |
| STAGGERED_1LAYER | real Bid/Ask replay | reconstructed entry terminal max-loss proxy |

The Convexity node is deliberately named ALWAYS_ON here. V18 called it CONVEXITY_SHOCK, but its workflow actually passed qqq_realchain_convexity_v1_cycles.csv from the always-on component replay.

Short-only is not included in V19 because the current GitHub source state does not expose a verifiable branch/file for that implementation.

## Frozen universal rule

- One active opportunity at a time.
- 10 calendar days after each realized exit.
- Candidate right executes only when entry risk <= Bank.
- Same-date tie-break is fixed: Convexity -> State Adaptive -> Staggered -> Ratio.
- ISOLATED: later positive P&L does not replenish Bank; only later losses consume it.
- REPLENISH: all realized P&L changes Bank and is the contamination comparator.
- Bank is a research risk currency, not NAV or cash collateral.

## Risk definition

The universal currency must be comparable across strategies. V19 uses an entry-time terminal max-loss proxy calculated from the actual historical entry Bid/Ask and the frozen entry geometry. It does not inspect future quotes, future P&L, or realized drawdown when deciding whether an entry is affordable.

For State Adaptive, the future migration path is not used to pre-price risk; only the frozen entry package is used. This avoids future information entering the admission rule.

## Interpretation

This remains a counterfactual rights/lifetime experiment. It does not prove that one WIN literally finances an indefinitely long live portfolio, and it does not calculate NAV/CAGR for the Universal Bank.
