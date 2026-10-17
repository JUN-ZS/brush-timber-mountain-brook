# QQQ Event-Driven Risk-Budget Portfolio Replay V1

Research-only account-level replay for the prespecified QQQ reversal-event candidate set.

Unlike per-unit event statistics, this layer creates an independent $80,000 NAV account for each selected option structure, NAV-relative terminal-tail budget (0.5%, 1%, 2%), and BASE/STRESS cost case. Every account holds fixed QQQ Core shares initially funded to 42% of initial NAV; the rest starts as cash. Entry sizing is dynamic and constrained by prior complete liquidation NAV, option quote-side entry costs, terminal expiry payoff loss, displayed entry-side depth, and a conservative cash reserve proxy for credit structures.

Daily NAV is cash + fixed-share QQQ market value + exact-contract, side-quote close-out cashflow for any open option position. Missing identity, quote, or required displayed depth remains unknown; no price is forward-filled. Output includes compressed daily NAV marks, summary, annual returns, trade ledger, source pins and NAV reconciliation.

Caveats: not authenticated fills; no broker margin/assignment/forced-liquidation model; terminal expiry loss is not an upper bound on interim liquidation loss; QQQ Core is price-only without dividends/rebalancing; option history ends 2025-12-15; the event screen is exploratory and not a virgin OOS approval.
