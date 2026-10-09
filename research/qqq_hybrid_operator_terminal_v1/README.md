# QQQ Hybrid Operator Terminal V1

**Status:** isolated operator-preview feature on a research branch. It does not replace or mutate V3 and does not place broker orders.

## Purpose

The missing workflow was **reverse sizing**:

> An operator enters an intentionally excessive current quantity (for example, 1,000 QQQ shares or VXX short shares). The engine compares it to capacity calculated from the current NAV, confirmed market state, cash pool, sizing inputs, and option-risk budget, then displays the action target and exact quantity difference.

The table distinguishes:

- **Capacity:** the maximum units permitted by the entered sizing profile and risk pool.
- **Action target:** the quantity this state permits now. Excess positions can be trimmed during HOLD; positions below capacity are not increased unless the regime permits new risk.
- **Recommendation:** ADD / HOLD / REDUCE / PENDING / BLOCKED, with the reason retained.

The V3 market snapshot is read-only. All sizing percentages are editable what-if inputs. The V3 reference profile is only a convenient preview preset; it is not automatically promoted into current sizing.

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

## Sizing and risk boundaries

For a credit vertical:

\`max_loss_per_spread = (spread_width - net_credit) * 100\`

The number of contracts is bounded by both the individual leg budget and the shared option max-loss pool. This prevents several option legs from each spending the same risk reserve.

- A 0% budget explicitly disables that strategy's target capacity.
- Baseline QQQ/VXX option legs may build only in CARRY.
- High VIX or backwardation disables seller-option targets.
- Positive-but-thin contango holds new entries, but over-cap positions remain eligible for trimming.
- Missing/stale VX M1/M2 or missing spot data blocks resizing.
- The VXX short-stock notional cap is not a maximum-loss guarantee.
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
