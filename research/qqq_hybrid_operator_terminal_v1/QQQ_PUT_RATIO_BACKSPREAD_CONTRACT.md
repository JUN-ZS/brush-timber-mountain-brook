# QQQ Put Ratio — Direction, Payoff and Entry Contract

Status: HUB research-only calculator. It is not a recommendation, not an execution-ready ticket, and not part of the primary QQQ/VXX call-credit risk pool. It does not change Frozen Original Hybrid, account targets, NAV, or broker permissions.

## Direction must be selected first

The user explicitly selects one of two different structures. Here, N is the quantity on the selected "heavy" side; the other side is exactly one contract. Both legs must be QQQ puts with the exact same expiry and confirmed standard multiplier/deliverable.

### A. Default: N SHORT : 1 LONG — short-heavy ratio put spread

- BUY TO OPEN 1 higher-strike QQQ put (Long Put), using its Ask as the conservative entry-side estimate.
- SELL TO OPEN N lower-strike QQQ puts (Short Puts), using their Bid as the conservative entry-side estimate.
- Geometry: K_long > K_short > 0.
- Signed net debit D in dollars/package = 100 × (Ask_long − N × Bid_short). D > 0 means debit paid; D < 0 means credit received.
- Expiry P&L at underlying settlement S = 100 × [max(K_long − S, 0) − N × max(K_short − S, 0)] − D.
- At S = 0, P&L = 100 × (K_long − N × K_short) − D.

For N > 1, when QQQ falls below the lower Short Put strike, the one Long Put no longer offsets all N Short Puts: (N−1) net short puts remain. This is **not a defined-risk protective hedge**. Its loss can become very large if QQQ approaches zero; receiving a credit does not remove this tail risk. OIC describes the worst expiration outcome as the underlying becoming worthless and the maximum gain as occurring at the lower short strike. See [OIC: Short Ratio Put Spread](https://www.optionseducation.org/strategies/all-strategies/short-ratio-put-spread).

### B. N LONG : 1 SHORT — long put ratio / put backspread

- BUY TO OPEN N lower-strike QQQ puts (Long Puts), using their Ask as the conservative entry-side estimate.
- SELL TO OPEN 1 higher-strike QQQ put (Short Put), using its Bid as the conservative entry-side estimate.
- Geometry: K_short > K_long > 0.
- Signed net debit D in dollars/package = 100 × (N × Ask_long − Bid_short). D > 0 means debit paid; D < 0 means credit received.
- Expiry P&L at settlement S = 100 × [N × max(K_long − S, 0) − max(K_short − S, 0)] − D.
- This direction may benefit from a sufficiently sharp decline, but can lose around the lower Long Put strike; do not describe it as guaranteed protection. OIC identifies the maximum expiration loss at the lower long strike and notes initiation may be a debit or credit. See [OIC: Long Ratio Put Spread](https://www.optionseducation.org/strategies/all-strategies/long-ratio-put-spread).

When N = 1, the structure has no contract-count asymmetry, but buy/sell direction and strike ordering still define different vertical spreads. Do not infer that N=1 offers added crash convexity.

## Measurement and sizing rules

1. The expiry field must be explicit, valid and not already past. The structure selector, Long/Short strike labels and N/1 quantities must agree; wrong geometry returns PENDING.
2. Before capacity is displayed, the operator must attest that both legs have been cross-checked against the current broker chain (timestamps, Bid/Ask and size) and that both are standard QQQ 100-share contracts. This attestation is manual; the app does not authenticate the source.
3. Net cash flow is signed: positive = debit outflow; negative = credit inflow. A net credit is a valid entry cash flow and must not be rejected merely because it is negative.
4. For each package, calculate P&L at expiry across relevant strike breakpoints, including S = 0, then set estimated maximum loss to max(0, −minimum expiry P&L). The estimate uses supplied leg prices and the generic 100 multiplier.
5. Research capacity = floor(known remaining research risk budget / estimated maximum expiry loss per package). Unknown Hybrid reservations stay PENDING, not zero. A zero/invalid risk denominator never yields infinite capacity.
6. Display both legs as explicit BUY TO OPEN / SELL TO OPEN quantities, the same expiry, strike, source-side price, signed package cash flow, estimated terminal max loss, and P&L if QQQ expires at $0. These are calculations from input data, not predicted returns or guaranteed fills.
7. The public chain can be delayed or incomplete. Verify exact expiry, contract root, multiplier and deliverable in the broker chain. Adjusted or unknown deliverables remain out of scope. Manual edits do not count as independently authenticated data.
8. The UI may explain how to construct a broker's multi-leg LIMIT combo order, but never transmits an order. Never infer that the risk-budget count proves adequate broker buying power, margin or suitability. A multi-leg order may not fill at displayed reference prices; early assignment, expiration handling, execution cost, volatility changes and path risk are outside the expiry calculator.

## Explicit non-integration boundary

This calculator is isolated inside HUB Research. Its package capacity must not be added to the main dashboard, and it cannot amend the primary risk whitelist (QQQ call-credit and VXX call-credit), Frozen Original Hybrid or live-order permissions.
