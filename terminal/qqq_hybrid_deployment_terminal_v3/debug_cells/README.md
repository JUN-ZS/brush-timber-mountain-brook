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

These cells use deterministic fixtures. They do not call OpenD, do not place orders, and do not write the Ledger.

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

## Next increment

Delayed-data DATA cell, then real option-candidate retrieval, each still isolated.
