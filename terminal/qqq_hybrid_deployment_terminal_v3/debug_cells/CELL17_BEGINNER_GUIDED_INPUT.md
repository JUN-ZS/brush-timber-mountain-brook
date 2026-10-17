# Cell 17 — Beginner Guided Input

Purpose: give a non-technical operator a step-by-step questionnaire that translates ordinary answers into the V3 Current → Target → Action inputs, then independently audits the frozen baseline rules against the real engine.

This is not a second strategy engine.

The program:
1. asks for cash, QQQ shares and market inputs one question at a time;
2. calculates the simple NAV used by this guided example as cash + QQQ market value;
3. asks for existing VXX short exposure and option spread counts;
4. calculates M1/M2 term slope itself, so the operator does not need to calculate S;
5. calls the real engine.js for Decision, Target Ledger, Funding Context and Cell 16;
6. independently computes the expected frozen-baseline Decision / Target / Action Class without calling those engine functions;
7. compares both sides and returns AUDIT RESULT: PASS or FAIL.

Important boundaries:
- no market fetch;
- no broker connection;
- no broker order;
- VXX short is entered as % NAV;
- QQQ/VXX call spreads are entered as contract counts;
- Strategy Pool is not an execution input;
- the independent audit constants are intentionally hard-coded to the frozen Original Hybrid contract. A policy change should therefore cause an audit mismatch rather than silently changing the guide.

## Windows

Interactive questionnaire:

    RUN.cmd 17

Small-white demo (100 QQQ + USD 100,000 cash, QQQ=750):

    RUN.cmd 17-demo

Full independent reverse audit:

    RUN.cmd 17-selftest

The demo should reach:

    NAV = USD 175,000
    CARRY / BUY
    QQQ 100 → 98 shares
    VXX short 0% → 18% NAV
    Cell 16 = REBALANCE

REBALANCE is intentional: the engine action can remain BUY while the frozen target requires one leg to reduce and another to add. The operator-facing class describes the actual Current → Target movement; it does not replace the primary policy action.

A BLOCKED or stale-data result must never become a BUILD action.

## Input discipline (beginner path)

- Blank answer → `EMPTY`, re-asked ("留空唔等於 0"). Never silently 0.
- `abc`, `-1` → `INVALID`, re-asked. Explicit `0` is a real zero.
- `100,000` is accepted as 100000 (thousands separators stripped explicitly).
- Dates must be valid `YYYY-MM-DD`; anything else is re-asked (an unparseable date must not bypass the STALE / AS-OF MIXED gate).
- Piped / scripted stdin works (e.g. `printf '...' | node cell17_beginner_guided_input.js`); stdin ending early exits non-zero (`INPUT_ENDED`).
- `--demo` and the interactive run exit non-zero when the reverse audit FAILs.

## Contract pins in `--self-test`

Every frozen constant / gate boundary has a case whose outcome flips if either the engine POLICY or the CONTRACT copy drifts:
termSafe (S≈5.5 CARRY / S≈4.5 WEAKENING), vixHigh (VIX 28.0 CAP / 27.99 WEAKENING), vxxHighPct (CAP active seller 18→10),
S = 0 backwardation, maxTermAgeDays (4d FRESH / 5d STALE), date-mix 2d / 3d, option budgets (BUY + candidate → floor(NAV × budget% / (credit × 100)); REDUCE → 0),
plus a scripted interactive run that proves NAV = cash + QQQ shares × price.
`tests/golden_test.js` also runs `--self-test`, so both V3 CI workflows gate Cell 17.
