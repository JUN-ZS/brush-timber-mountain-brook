# QQQ Hybrid Operator Terminal V1

**Status:** isolated operator-preview feature on a research branch. It does not replace or mutate V3 and does not place broker orders.

## Purpose

The primary workflow is **capital-first sizing**:

> Enter principal / NAV (for example, $100,000), uncommitted deployable cash, cash reserve, stock allocation caps, a user-entered VXX margin estimate, and option max-loss budgets. The engine calculates maximum units for each Hybrid leg and available option candidate, capital/margin estimates, a shared option-risk envelope, and the target the current state permits. Current holdings are optional inputs only for ADD / HOLD / REDUCE deltas.

An intentionally excessive 1,000-unit input is a collapsed self-audit diagnostic only, not the normal workflow.

The table distinguishes:

- **Capacity:** the maximum units permitted by NAV allocation, cash after reserve, VXX margin estimate, and the shared option-risk envelope.
- **Action target:** the quantity this state permits now. Excess positions can be trimmed during HOLD; positions below capacity are not increased unless the regime permits new risk.
- **Capital reconciliation:** planned incremental cash = cash reserve + shared option-risk envelope + incremental QQQ buys + estimated margin for incremental VXX short shares, preventing the same cash from being counted twice.
- **Recommendation:** ADD / HOLD / REDUCE / PENDING / BLOCKED, with the reason retained.

The V3 market snapshot is read-only. All sizing percentages are editable what-if inputs. The V3 reference profile is only a convenient preview preset; it is not automatically promoted into current sizing. Initial deployment: set NAV and uncommitted cash to the principal amount. Existing portfolio: enter total current equity as NAV and only truly uncommitted cash as the cash pool.

## Components

- \`engine.js\`: market-state gate, capacity calculation, reverse-sizing deltas, defined-risk vertical sizing, strategy catalogue and N:X campaign preview.
- \`server.py\`: local static server, read-only snapshot bridge to V3 at \`127.0.0.1:8788\`, Yahoo option chain lookup, and append-only manual preview journal.
- \`index.html\` / \`app.js\` / \`styles.css\`: responsive operator workbench.
- \`tests/engine.test.cjs\`: deterministic engine tests.

## Windows CMD launch

Start V3 in its own CMD window first:

\`\`\`cmd
cd /d <repo>\\terminal\\qqq_hybrid_deployment_terminal_v3
py -3 server.py
\`\`\`

Then start Hybrid in another CMD window:

\`\`\`cmd
cd /d <repo>
py -3 research\\qqq_hybrid_operator_terminal_v1\\server.py
\`\`\`

Open:

\`http://127.0.0.1:8790\`

V3 must be healthy for the read-only market bridge. If it is not available, the workbench reports BLOCKED until the operator supplies a manually verified, date-stamped snapshot. It does not invent prices.

## Option strategy coverage

### Original Hybrid layers
1. QQQ core shares.
2. QQQ far call / call-credit vertical.
3. VXX short stock.
4. VXX call-credit vertical.

### Other discussed strategies available in the planning catalogue
- VXX put-credit vertical and QQQ bull-put / bear-call verticals.
- Covered call.
- QQQ protective put.
- Long call, long put and long straddle.
- Iron fly, iron condor, broken-wing butterfly and calendar spread.
- Hub-style 1:N:1 call/put ratios.
- Legacy QQQ N-far-short / dynamic near-long hedge campaign.

Candidate lookup is available for QQQ/VXX call and put verticals and QQQ long calls/puts. Manually defined structures require an explicit per-unit maximum-loss or debit input. Missing candidate prices stay PENDING; no credit floor or quantity is invented.

## Capital-first planning example

With the editable V3-reference preview profile, NAV/cash of $100,000, 10% cash reserve, $3,200 shared option-risk envelope, QQQ at $100, VXX at $20, and a user-entered 1.5× VXX short-margin estimate, a fresh CARRY-state preview caps QQQ core at 420 shares ($42,000 notional) and VXX short stock at 900 shares ($18,000 notional / $27,000 estimated margin). The plan envelopes $10,000 cash reserve + $3,200 option-risk reserve + $42,000 QQQ + $27,000 VXX margin = $82,200, leaving $17,800 unallocated. This is arithmetic for an editable scenario, not a claim that these inputs are validated or safe.

## Sizing and risk boundaries

For a credit vertical:

\`max_loss_per_spread = (spread_width - net_credit) * 100\`

The number of contracts is bounded by both the individual leg budget and the shared option max-loss pool. This prevents several option legs from each spending the same risk reserve.

- A 0% budget explicitly disables that strategy's target capacity.
- Baseline QQQ/VXX option legs may build only in CARRY.
- High VIX or backwardation disables seller-option targets.
- Positive-but-thin contango holds new entries, but over-cap positions remain eligible for trimming.
- Missing/stale VX M1/M2 or missing spot data blocks resizing.
- The VXX short-stock notional cap is not a maximum-loss guarantee. Its margin multiple is a broker-specific user estimate, not a universal requirement.
- The cash pool means uncommitted cash available for this plan. Do not enter total NAV as available cash if some of that NAV is already tied up in existing holdings.
- Ratio call/put structures may have unbounded tails. A manually entered stress loss yields a **stress-only estimate**, not a hard loss cap.
- The legacy N:X hedge result is per campaign, not portfolio-wide capacity, and is never presented as max-loss-capped.
- Public Yahoo option quotes may be delayed/incomplete and are not guaranteed executable; verify broker bid/ask, expiry, adjusted contracts and fills.

## Hub-researched structures (separate research workbench)

Open \`http://127.0.0.1:8790/hub_research_pack.html\` from the same local server. This is a dedicated add-on to the original four-layer Hybrid, not a replacement for it.

It prioritizes structures that already have Hub research code / frozen geometry rather than treating every standard option strategy as equally researched:

- **Ratio-Call HARVEST50 V1**: \`+1 ATM Call - N OTM Short Calls + N farther-OTM Call Wings\`. The approach/reversal harvest needs both the event sequence and positive pair P&L from observed exit quotes; missing exit quotes cannot be treated as zero-price fills.
- **Risk-Budget Dynamic-N V2**: entry N is selected from N=1..4 by the entry terminal-payoff risk proxy and available budget; each +0.15 step from the 0.20 short-call delta target removes a pair. At/above 25% package-risk consumption the frozen downside pair target also applies.
- **Fresh-Pair Dynamic-N V7**: starts with its frozen N=2 campaign, caps at N=4; add requires short delta <=0.10 for two sessions, a five-session change cooldown, and the resulting entry-risk proxy inside budget. Reduction / approach-state decisions are exposed as operator-entered state inputs, not inferred from a future bar.
- **State-Adaptive Geometry**: \`+1 ~50Δ Call -2 ~20Δ Calls +2 ~8Δ farther call wings +1 ~25Δ Long Put -1 ~10Δ farther-OTM Short Put\`. A supplied prior close >= anchor + 1×ATR20 flags a wave; the target short-call delta steps 0.20→0.30→0.40 and short-put absolute delta 0.10→0.05 while the other frozen legs remain unchanged.
- **Staggered Stack**: the same static per-vintage package under fixed 1 / 2 / 4 overlapping-vintage caps. This is distinct from strike migration within one vintage; all layers consume the shared risk amount entered on this page.
- **SHOCK-GATED put debit spread**: \`+1 higher-strike Long Put -1 farther-OTM Short Put\`; the frozen trigger is trailing 252-session drawdown <= -8% OR 5-session return <= -4%. No target is permitted before the trigger, and the observed Long Put Ask minus Short Put Bid must be a positive debit.
- **Universal Harvest Bank**: optional ISOLATED risk-rights gate uses one realized positive N>2 Risk-WIN seed; later wins are ignored and later losses consume the balance. \`REPLENISH\` exists only as a comparison mode. The research README explicitly treats this Bank as a *risk currency*, not NAV, uncommitted cash, margin or broker collateral; it is a counterfactual rights/lifetime experiment, not a guarantee of repeatable live deployment.

Entry risk is calculated from the selected leg Bid/Ask and an expiry-payoff node proxy. It is not a daily MTM maximum-loss guarantee and does not replace the canonical historical real-chain backtest. The chain loader uses the server's public Yahoo option endpoint; quotes may be delayed/incomplete and a missing candidate remains pending. Provider Delta is labelled separately from Black-Scholes-estimated Delta.

Capital safety boundary: the page computes **one selected research structure at a time**. Enter the existing Hybrid legs' already-reserved option risk in “base Hybrid option risk reserved” before using the remaining pool. This page is not yet automatically synchronized with the primary desk's holdings or allocations; do not add independent “maximum” values from both screens together. All actions remain what-if/manual review; no broker order route is present.

## Tests

Run locally in Windows CMD:

\`\`\`cmd
node --check research\\qqq_hybrid_operator_terminal_v1\\engine.js
node --check research\\qqq_hybrid_operator_terminal_v1\\app.js
node research\\qqq_hybrid_operator_terminal_v1\\tests\\engine.test.cjs
py -3 -m py_compile research\\qqq_hybrid_operator_terminal_v1\\server.py
\`\`\`

The associated GitHub Actions workflow uses only \`[self-hosted, windows, x64]\`. There is no broker order endpoint and no policy mutation path.
