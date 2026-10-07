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
