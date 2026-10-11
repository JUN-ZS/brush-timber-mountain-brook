# QQQ Hybrid Operator Terminal V1

**Status:** isolated operator-preview feature on a research branch. It does not replace or mutate V3 and does not place broker orders.

## Purpose

The primary workflow is **capital-first sizing**:

> Enter principal / NAV, truly uncommitted cash, cash reserve, stock allocation caps and the VXX short-stock margin estimate. The primary option max-loss pool includes only QQQ far call-credit and VXX call-credit verticals. These quoted seller legs share one pool; QQQ stock purchases and VXX short-stock margin use the same cash reconciliation. VXX put and other catalogue structures stay outside the primary budget. Current holdings are used to compare the permitted target with the current state.

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

## PRO dashboard and live visual summaries

The primary page begins with a responsive **multi-row / multi-column PRO dashboard**. It is rendered from the current engine result and user-entered / refreshed prices, not from fixed screenshot values:

- Four portfolio KPIs: NAV, combined QQQ/VXX stock notional, maximum option loss at available capacity, and unallocated cash.
- A stacked capital-plan bar with cash reserve, the full shared option-risk envelope, incremental QQQ purchases, incremental VXX margin, and remaining cash.
- A shared option-risk donut and per-leg bars for QQQ call-credit and VXX call-credit; if one or both quotes are missing, the chart labels incomplete quote coverage rather than pretending missing risk is zero.
- Four capacity cards showing maximum QQQ shares, VXX short shares, QQQ call spreads and VXX call spreads.
- A detailed price/allocation table showing strikes and expiry, maximum quantities, notional/margin, estimated net credit, max loss and NAV percentages.

The visual grid shifts from four columns to two columns and then to a mobile layout as the viewport narrows. The existing operator table beneath it remains the authority for actual current-state ADD / HOLD / REDUCE review. The dashboard presents sizing outputs only; it does not place orders. Fresh market data and current option-chain candidates are required for fully populated live values. Historical uploaded quote fixtures exist only in regression tests and are not silently inserted into the live screen.

## QQQ / VXX Option Chain Lab (screenshot / research only)

After starting the existing local server, open:

`http://127.0.0.1:8790/option_chain_lab.html`

The separate page includes four editable chains from the latest user screenshot: QQQ CALL, QQQ PUT, VXX CALL, and VXX PUT, selected expiry 2026-11-20. It can load the screenshot sample explicitly, import/export CSV (`symbol,side,strike,bid,ask,delta`), enumerate two-leg credit verticals, compute net credit / breakeven / max gain / max loss / quantity under a user-entered risk budget, and draw expiry payoff. The screenshot's quote observation time is not verified; it is always labelled non-live. Inspect suspicious or wide quotes before relying on any result.

This page is an isolated calculator only. QQQ PUT and VXX PUT remain research-only and cannot enter the primary shared budget or send broker orders. Contract multiplier defaults to 100 as an assumption; verify VXX deliverables/adjustments before use.

Windows self-hosted regression: [Run #66](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/37983181658); option-chain unit test is `tests/chain_lab.test.cjs`.

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

## Joint portfolio budget — primary whitelist only

The primary page (http://127.0.0.1:8790/) is the authoritative sizing page. Its cash plan accounts for QQQ core shares, the VXX short-stock margin estimate, cash reserve and incremental QQQ purchases. Its shared option max-loss pool includes exactly two quoted defined-risk seller verticals:

- QQQ FAR CALL / CALL-CREDIT.
- VXX CALL-CREDIT.

The two eligible option legs request percentages of NAV but do not each receive an independent entitlement. After usable same-expiry quotes are available, the engine sums their requested risk, proportionally scales requests when they exceed the shared pool, and rounds to whole spreads. A quoted candidate with a budget too small for one whole spread still participates in the requested allocation before integer rounding. VXX put is intentionally excluded from this plan, regardless of whether a separate research quote is found.

VXX put, QQQ bull-put/bear-call, covered calls, protective puts, long/debit options, iron flies/condors, calendars, ratio structures, Hub packages and legacy hedge diagnostics are outside the primary budget. They can remain visible as research references, but receive no primary capacity, target changes, or risk reservation. Do not add their research estimates to the primary table.

The Hub-specific details page (hub_research_pack.html) is a structure/rule inspector, not a second allocation authority. Its standalone maximum must not be added to the primary page's capacities. All actions remain what-if/manual review; no broker order route is present.

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

## User-uploaded option-chain fixture

The deterministic fixture tests/fixtures/user_uploaded_option_chain_2026-11-20.json records the QQQ call and VXX call rows visible in the screenshot uploaded on 2026-10-08. It preserves the displayed expiry, strikes, Bid/Ask and Delta and labels its provenance as USER_UPLOADED_SCREENSHOT; these are historical test inputs, not live quotes. That screenshot does not show VXX puts, so it must not be used to invent a VXX put candidate. The allocator regression uses QQQ 799C short / 810C wing, VXX 21C short / 24C wing, and checks that VXX put remains PENDING without a candidate quote.

## Manual AI collaboration — fixed handoff protocol

Use the top-level **Export AI Review Pack (.md)** button after entering actual NAV / uncommitted cash / current holdings, refreshing the V3 snapshot, and loading the two primary call-credit candidates. Attach that dated Markdown packet to ChatGPT with a fresh broker-chain screenshot or CSV and report any pending orders or holdings the app does not show.

The packet contains the exact active APP input/result JSON, source timestamps, market gate, position-capacity rows, cash / risk reconciliation, option candidates, measurement lockbox and a fixed response contract. It explicitly separates Accuracy, Generality, Integration, and execution readiness; it does not average hard gates into one score. It instructs the reviewer to block or wait on missing/stale data, confirm exact option roots and deliverables, reconcile cash/risk arithmetic to USD 0.01, and return only BLOCK, WAIT FOR DATA, or ELIGIBLE FOR HUMAN REVIEW.

The current isolated FAR CALL overlay remains research-only: trade-performance Accuracy is blocked, Generality is not demonstrated, and its current base integration screen failed. This is not a full-composite test of the Frozen Original Hybrid, but it is not permission to promote the incremental overlay. No broker orders, strategy promotion, or frozen policy mutations are available through the handoff.

Protocol: AI_MANUAL_COLLABORATION_PROTOCOL_V1.md. Regression coverage is included in tests/chain_lab.test.cjs.



### Compact workflow and quote-width metrics (reviewed 2026-10-11)

- Default strategy list shows only the two primary seller legs; a button reveals the 16 research-only rows without deleting their controls or calculations. Additional option candidates and legacy N:X sizing controls are collapsed under explicit advanced disclosures.
- The QQQ/VXX primary risk weights have one canonical editable input in the capital section; the strategy table displays the configured percentage read-only.
- Candidate cards preserve exact contract symbols where returned, both legs' bid/ask, per-leg spread width / midpoint, net credit, expiry, DTE, source, chain retrieval timestamp, and an explicit unverified quote-timestamp warning.
- Width/mid triage bins <=10% TIGHT, >10–25% WATCH, >25% WIDE are descriptive only; they are not trade-approval gates. Multiplier 100 remains an assumption until contract deliverables are confirmed.
- New regressions cover quote-quality arithmetic, compact research-row controls, unique risk-weight input, visible source-time caveats, and AI packet transparency.

## Position facts and unrealized P&L register

The main workbench now has an optional, collapsed position register for only the four primary quantities: QQQ long shares, VXX short shares, QQQ far call-credit packages and VXX call-credit packages. Records persist in this browser's local storage; export/import the versioned JSON for backup or transfer. The register remains attribution-only unless the operator deliberately enables **Use registered holdings as current quantities**.

Supported mark-to-entry arithmetic is explicit:
- QQQ long shares: (current mark − average entry) × shares.
- VXX short shares: (entry mark − current mark) × shares.
- Credit vertical package: (entry net credit − current estimated close debit) × packages × multiplier.

P&L is gross and unrealized; it excludes transaction costs, slippage, dividends, borrow fees, assignment/exercise, tax and cash-flow timing. Blank marks stay unknown; blank stock marks may use the current APP spot snapshot and are labelled as derived but SOURCE UNVERIFIED, because this register does not yet retain the snapshot’s per-symbol source class. Mark age and source are shown separately from arithmetic. This register is not a realized P&L ledger and does not automatically alter account NAV.

When register mode is active, its four aggregated quantities feed the sizing engine only after the operator confirms all four primary categories have been reconciled (omitted categories mean zero). Importing, adding/editing, or removing a row clears that confirmation and disables register mode until reviewed again. An empty register cannot imply a zero-holdings account.

When register mode is active, its four aggregated quantities feed the sizing engine. An option row with incomplete symbols, expiry, strikes, or unchecked broker-verified deliverable/multiplier blocks only the affected strategy's Current → Target sizing row. It does not pretend to calculate a safe reduction quantity from unknown terms. Existing manual current quantities are restored when register mode is switched off or when its last row is removed.

Run the dedicated tests with Windows CMD:
node research\qqq_hybrid_operator_terminal_v1\tests\position_ledger.test.cjs

## Tests

Run locally in Windows CMD:

\`\`\`cmd
node --check research\\qqq_hybrid_operator_terminal_v1\\engine.js
node --check research\\qqq_hybrid_operator_terminal_v1\\app.js
node --check research\\qqq_hybrid_operator_terminal_v1\\position_ledger.js
node research\\qqq_hybrid_operator_terminal_v1\\tests\\engine.test.cjs
node research\\qqq_hybrid_operator_terminal_v1\\tests\\position_ledger.test.cjs
node research\\qqq_hybrid_operator_terminal_v1\\tests\\chain_lab.test.cjs
py -3 -m py_compile research\\qqq_hybrid_operator_terminal_v1\\server.py
\`\`\`

The associated GitHub Actions workflow uses only \`[self-hosted, windows, x64]\`. There is no broker order endpoint and no policy mutation path.


## Latest QQQ far-call replay result

- [Run #34 result report](./QQQ_FAR_CALL_REPLAY_RUN34.md) and [machine-readable summary](./QQQ_FAR_CALL_REPLAY_RUN34.json) preserve the actual Windows self-hosted Actions output. Run #34 passed 26 replay tests and all 1,688 closed-trade cash-flow reconciliations; markability gaps fell from 273 to 24 sessions in the base-cost arm, but all 16 budget/cost scenarios remained negative. The report blocks CAGR/MaxDD/Sharpe/ES95 due EOD-only quotes and incomplete source/core-price coverage. No strategy integration approved.
