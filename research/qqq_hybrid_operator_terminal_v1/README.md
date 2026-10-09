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

## Tests

Run locally in Windows CMD:

\`\`\`cmd
node --check research\\qqq_hybrid_operator_terminal_v1\\engine.js
node --check research\\qqq_hybrid_operator_terminal_v1\\app.js
node research\\qqq_hybrid_operator_terminal_v1\\tests\\engine.test.cjs
py -3 -m py_compile research\\qqq_hybrid_operator_terminal_v1\\server.py
\`\`\`

The associated GitHub Actions workflow uses only \`[self-hosted, windows, x64]\`. There is no broker order endpoint and no policy mutation path.
