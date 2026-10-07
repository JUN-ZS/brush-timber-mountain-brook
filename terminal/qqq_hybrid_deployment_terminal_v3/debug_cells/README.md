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

Cells 01–08 use deterministic fixtures. Cell 09 reads Cboe delayed VX (read-only). Cell 10 attempts a real Yahoo options fetch (read-only, fail-soft). None call OpenD, place orders, or write the Ledger.

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
No OpenD, no broker orders, no Ledger writes.

Run (Linux / CI):

    python3 cell10_option_candidate_retrieval.py

Windows (`RUN.cmd 10`) uses `python` / the launcher available on PATH.
