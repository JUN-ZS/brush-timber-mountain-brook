# V3 Operator Debug Cells

These cells are deliberately independent. Each one has its own fixture, calculation, assertions, and PASS output.

Run one cell:

    RUN.cmd 1

Run the full set:

    RUN.cmd ALL

## Cell 01 — Operator Input

Purpose: prove that manual input has three states:

    real zero -> VALUE(0)
    blank     -> EMPTY
    bad value -> INVALID

Blank is never silently converted to zero.

## Cell 02 — Decision

Purpose: prove the frozen policy mapping:

    healthy contango -> BUY / OPEN
    thin contango    -> HOLD / WATCH
    backwardation   -> REDUCE / CUT
    shock            -> REDUCE / CUT

This cell does not know anything about candidates or positions.

## Cell 03 — Operator Current

Purpose: prove current-position input is a separate object from market decision.

Incomplete current-position fields block BUILD math but do not change the decision itself.

## Cell 04 — Candidate

Purpose: prove option-chain selection alone.

Candidate selection outputs short strike, long strike, DTE, delta, credit, and source.

It does not modify current position or policy.

## Cell 05 — Build

Purpose: prove Current -> Target.

Critical rule:

    HOLD + no candidate
        => existing option count stays unchanged

    BUY + no candidate
        => existing option count stays unchanged

    BUY + valid candidate
        => sizing may calculate a target

Thus a missing option feed cannot manufacture a REDUCE action.

## Cell 06 — Watch

Purpose: prove roll monitoring is position-aware.

    no option position
        => OFF

    option position + missing DTE/delta
        => NEEDS_POSITION_DATA

    option position + threshold crossed
        => TRIGGER

Thin carry is WATCH only; it is not an execution trigger.

## Debug boundary

Cells 01–08, 12, 13, and 14 use deterministic fixtures. Cell 09 reads Cboe delayed VX (read-only). Cell 10 is Yahoo-only option retrieval (unit). Cell 11 is the Yahoo→OpenD cascade (optional OpenD; never invents strikes). None place broker orders or write the Ledger.

## Cell 07 — Operator Summary

Purpose: prove the top-level human view answers four questions without reconstructing the dashboard:

    What mode am I in?
    What should I buy / hold / reduce now?
    How far is the market from the next regime line?
    How far is each existing option spread from its roll line?

This cell is pure logic only. It does not fetch market data or identify an actual broker option leg.

## Cell 08 — Current Option Leg Identity

Purpose: prove Operator Memory can name WHICH credit-spread legs are held, not only counts, and that ROLL reads that identity.

Per underlying (QQQ / VXX), `parseOptionLeg` returns qty, shortStrike, longStrike, expiry, dte, delta, entryCredit with VALUE / EMPTY / INVALID discipline (blank ≠ 0), plus:

    FLAT        qty VALUE(0), or qty EMPTY with all other fields EMPTY
    READY       qty > 0 and shortStrike + longStrike + expiry are VALUE
    INCOMPLETE  qty > 0 but missing required identity fields
    INVALID     any field INVALID

`rollReady` is true only when status is READY and both dte and delta are VALUE.
`entryCredit` is credit-positive; a debit may be negative.
Optional `width = longStrike - shortStrike` when both strikes are VALUE.

ROLL wiring (via `operatorSummary` + `currentOptionLegs`):

    FLAT                              → NO POSITION
    INCOMPLETE / INVALID              → NEEDS_POSITION_DATA (never ROLL_NOW)
    READY + explicit leg.dte          → that DTE
    READY + blank dte + expiry VALUE  → dteFromExpiry(expiry, today); past → 0
    Delta                             → leg.delta VALUE else manual opt else missing

This cell does not change Decision, Candidate, or Build target math.

## Cell 09 — Delayed DATA

Purpose: verify the production VX term-data boundary against the Cboe public delayed adapter itself.

The cell performs a real read-only fetch and asserts:

    CBOE_PUBLIC_DELAYED_VX source
    standard monthly VX symbols only
    M1 expiry < M2 expiry
    both expiries > data_asof
    settlement used by default (no silent last-price substitution)
    S = (M2-M1)/M1 and state are internally consistent

This cell does not alter Decision, Build, Candidate, Ledger, or broker state.

Run (Linux / CI):

    python3 cell09_delayed_data.py

Windows (`RUN.cmd 9`) uses `python` / the launcher available on PATH.

## Cell 10 — Option Candidate Retrieval (real)

Purpose: prove **retrieval** of a next-buy candidate from a real Yahoo options attempt, with fail-soft contract. Independent of Cell 04 (fixture selection) and Cell 08 (Current Leg identity).

**Candidate ≠ Current Leg.** This cell never writes Current Leg fields and always reports `currentLeg: null`.

PASS paths (either is OK for CI — do not flake):

    A) LIVE
       Yahoo returns non-empty calls
       -> Node harness runs engine `candidateFromChain`
       -> candidate has shortStrike, longStrike, dte, and delta/credit/sizingAvailable
       -> source tagged YAHOO_OPTIONS (retrieval); engine estimate tag preserved on candidate

    B) OPTIONS_SOURCE_DOWN
       ok=false, status exact, candidate=null, calls=[]
       -> still PASS:true with reason SOURCE_DOWN
       -> never invents strikes (honest down)

`/api/options` uses the same `providers/yahoo_options.py` helper:
LIVE -> HTTP 200 `{ok:true,status:"LIVE",...}`;
OPTIONS_SOURCE_DOWN -> HTTP 502 `{ok:false,status:"OPTIONS_SOURCE_DOWN",calls:[],candidate:null}`.

Does not change Decision/Build policy. Does not auto-fill Current Leg from Candidate.
Cell 10 stays Yahoo-only (stable unit). **Cell 11** adds the OpenD fallback cascade.
No broker orders, no Ledger writes.

Run (Linux / CI):

    python3 cell10_option_candidate_retrieval.py

Windows (`RUN.cmd 10`) uses `python` / the launcher available on PATH.

## Cell 11 — OpenD Option-Chain Fallback (cascade)

Purpose: after Yahoo `OPTIONS_SOURCE_DOWN`, try Futu OpenD option chain so the operator still has a LIVE candidate path after hours (when OpenD is entitled). Prefer keeping Cell 10 as Yahoo-only; this cell owns the cascade.

Priority:

    1. Yahoo (`providers/yahoo_options.py`) → LIVE return
    2. OpenD (`providers/opend_options.py`) when Yahoo down → LIVE return
    3. Else honest fail-soft:
       BLOCKED_NO_OPEND (no OpenD / not entitled / connect fail; expected on CI)
       or OPTIONS_SOURCE_DOWN (both sources down)

**Candidate ≠ Current Leg.** Never invents strikes. Always reports `currentLeg: null`.

PASS paths (any is OK for CI — do not flake):

    A) LIVE from YAHOO_OPTIONS or OPEND_OPTIONS
       -> select via existing cell10 `candidateFromChain` harness when calls present
    B) BLOCKED_NO_OPEND after Yahoo down (honest)
    C) OPTIONS_SOURCE_DOWN from both (honest)

`/api/options` uses `providers/option_candidate_fetch.py` (same cascade).
Does not change Decision/Build. No broker orders, no Ledger writes.

Run (Linux / CI):

    python3 cell11_opend_option_fallback.py

Windows (`RUN.cmd 11`) uses `python` / the launcher available on PATH.

## Cell 12 — Journal Contract

Purpose: prove journal **payload construction** rules (pure engine helper; no live server required).

`HybridEngineV3.journalRecord({engine, book, humanAction, optionsStatus, candidates, currentOptionLegs})` returns the journalable object plus conflict flags:

    conflict: NONE | CONFLICT | DELTA_ACTION_MISMATCH

Rules:

    humanAction set and ≠ engine.action → CONFLICT
    HOLD/BUY + negative option deltas without candidate (or OPTIONS_SOURCE_DOWN / BLOCKED_NO_OPEND)
        → clamp those option deltas to 0, set deltas_guarded:true, flag DELTA_ACTION_MISMATCH
        (human CONFLICT takes precedence when both apply)
    Prefer correct `targetLedger` book (deltas already 0); the mismatch path catches synthetic/legacy bad books
    Never copy Candidate strikes into `current_position` / Current Leg fields
    `options_status`, `candidate_present:{qqq,vxx}` always recorded
    `current_option_legs` only when explicitly passed (identity), never from candidate

Live `app.js` `journalDecision` uses `journalRecord` and tracks module-level `optionsStatus` from option fetch success/catch.

Does not place broker orders. Append shape may use the journal API when the UI journals; this cell itself is fixture-only.

Run (Linux / CI):

    node cell12_journal_contract.js

Windows (`RUN.cmd 12`) uses `node` on PATH.

## Cell 13 — Operator Clarity (MEDIUM pains #6/#7/#8)

Purpose: three independent clarity contracts sharing engine helpers (no broker / no Ledger).

### A) Data cadence / MIXED-SOURCE (pain #7)

`sourceCadence(d)` + `dataHealth(d)` attach:

    termCadence  DELAYED_SETTLEMENT when term_source / M1–M2 provenance is CBOE delayed
    spotCadence  LAST when spot provenance is OPEND / YAHOO
    sourceMix    MIXED_SOURCE when delayed settlement term meets live last spot
    badges       e.g. MIXED-SOURCE · DELAYED SETTLEMENT vs LAST

Same-calendar-day MIXED_SOURCE stays **FRESH** with warn badge only — it does **not** block trading
(unlike date-gap AS-OF MIXED >2 days, which still blocks). Label example: `DATA FRESH · MIXED-SOURCE`.

### B) VXX naming (pain #6)

`exposureLabels()`:

    VXX short exposure (% NAV)     — not option spreads
    VXX call credit spreads        — contracts

`impliedVxxShares(nav, vxxPct, vxxPrice)` when price is finite.

### C) Flat-book silence (pain #8)

`flatBookSilence({qqqCalls,vxxCalls,forceFlat,currentOptionLegs})` and wiring in `triggers` /
`operatorSummary` ROLL:

    both call counts VALUE 0, or forceFlat, or both legs FLAT
        → QQQ_ROLL / VXX_ROLL fire suppressed, mode NO_POSITION / OFF
        → never ROLL_NOW from blank DTE on a flat book

UI optional checkbox **No option legs** sets `forceFlat`.

Run (Linux / CI):

    node cell13_operator_clarity.js

Windows (`RUN.cmd 13`) uses `node` on PATH.


## Cell 14 — Journal → Operator Memory write-back

Purpose: prove a **1:1 verifiable field map** from a journal row back into Operator Memory UI ids so reload does not wipe Memory. Never invent Current Leg from Candidate / NOW plan.

`HybridEngineV3.memoryFromJournal(row)` → `{fields:{id:string|null}, skipped:[], sourceEventId, warnings[], map}`

Rules:

    null in fields[id]  → skip write (blank/missing journal field)
    explicit journal 0  → Memory "0" (VALUE(0) kept)
    never map candidates / NOW plan strikes into Current Leg fields

### Easy field map (Journal path → Memory UI id)

| Journal path | Memory UI id |
|---|---|
| `current_position.nav` (if present) OR leave nav | `nav` |
| `current_position.qqqShares` | `qqqShares` |
| `current_position.vxxPct` | `vxxPct` |
| `current_position.qqqCalls` | `qqqCalls` |
| `current_position.vxxCalls` | `vxxCalls` |
| `current_option_legs.qqq.shortStrike` (`.value` / raw) | `qqqShortStrike` |
| `current_option_legs.qqq.longStrike` | `qqqLongStrike` |
| `current_option_legs.qqq.expiry` | `qqqExpiry` |
| `current_option_legs.qqq.dte` | `qqqDte` |
| `current_option_legs.qqq.delta` | `qqqDelta` |
| `current_option_legs.qqq.entryCredit` | `qqqEntryCredit` |
| same for `vxx*` | `vxx*` |

UI: **從 Journal 還原 Memory · Restore Memory from last Journal** applies mapped fields, shows map preview (`journal.qqqCalls → Memory qqqCalls = 2`), flashes updated ids. Successful JOURNAL also saves a localStorage Memory snapshot keyed by `event_id`; page load restores that snapshot if present.

Does not place broker orders. No Ledger. No OpenD required.

Run (Linux / CI):

    node cell14_journal_memory.js

Windows (`RUN.cmd 14`) uses `node` on PATH.

## Cell 15 — Strategy / Funding Context

Purpose: make the strategy explicit even when the market action is HOLD, and separately show capital-pool context without changing frozen target math.

Inputs:

    strategy pool = capital assigned to this strategy
    new capital   = this round's fresh contribution (not yet in NAV)

The cell verifies:

    ORIGINAL HYBRID BASELINE is always identifiable
    CARRY          → FULL HYBRID; QQQ far-call is eligible
    WEAKENING/HOLD → QQQ CORE ONLY; maintain existing short-vol, no new short-vol
    PRE-SHOCK/SHOCK → DEFENSIVE / RESERVE; no new carry
    QQQ current value / % NAV / frozen 42% target / target gap are visible
    funding preview does not mutate targetLedger
    funding context can be journaled and restored to Memory

This is an operator-context layer. It does not remove or rewrite Decision, Build, Candidate, or Roll functions.

## Cell 16 — Strategy State → Funding → Operator Action Bridge

Purpose: translate the frozen engine action + Current → Target deltas into one operator-facing class. Read-only; `noBrokerOrder: true`; never changes targets.

    DATA blocked / stale / mixed      → PAUSE
    REDUCE                            → DEFEND
    BUY with additions + reductions   → REBALANCE
    BUY with additions only           → BUILD
    HOLD + position + any reduction   → TRIM   (F4: only the part above frozen target; nothing added)
    HOLD + position, no deltas        → MAINTAIN
    no position                       → READY

`reduceLines` lists each reduction, e.g. `VXX short 25% → 18% NAV (TRIM − 7%)`.

F4 HOLD target (engine `targetLedger`, unchanged): QQQ core and option legs stay at current; VXX short = min(current, 18% NAV). HOLD never adds and never trims QQQ core.
Journal: a HOLD trim delta is journaled as-is (no DELTA_ACTION_MISMATCH; that guard only covers negative option deltas). A human action equal to the engine action or to the Cell 16 class (e.g. `TRIM`, `REBALANCE`) is not a CONFLICT.

Run: `node cell16_strategy_action_bridge.js` (Windows `RUN.cmd 16`).

## Cell 18 — Web Beginner Input

Purpose: prove the web "第一步：輸入你而家持有乜" block turns ordinary answers into the same Operator Memory ledger the engine always used, without inventing zeros.

Pure helpers (engine.js, no DOM): `beginnerNav`, `vxxSharesToPct`, `beginnerLedger`, `inputGapText`.

    NAV (AUTO)   = cash + QQQ shares × QQQ price     (VXX short / option spreads NOT included — UI says so)
    NAV (MANUAL) = "NAV 手動 override" when it is a number > 0 (labelled MANUAL in the UI)
    price missing / field blank → NAV EMPTY "未能計" (never 0); NAV 0 → INVALID
    VXX short    = % NAV, or VXX shares × VXX price ÷ NAV when % is blank
    blank → EMPTY → targetLedger inputBlocked → Cell 16 NEEDS_INPUT / summary "NEEDS INPUT" (never BUILD from 0)
    "abc", "0x10", "1,5", "1e3" → INVALID ; "100,000" → 100000 ; explicit "0" → VALUE 0

The cell also checks index.html (no prefilled numbers, text+inputmode=decimal inputs) and runs the real
app.js in a minimal fake DOM with a stubbed snapshot (no network) to confirm the wiring.

Run: `node cell18_web_beginner_input.js` (Windows `RUN.cmd 18`). Gated in CI through `tests/golden_test.js`.
