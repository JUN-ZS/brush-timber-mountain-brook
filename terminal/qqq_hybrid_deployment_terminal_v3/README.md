
# QQQ Hybrid Deployment Terminal V3 — Free VX / Provenance-First

V3 is the next-generation terminal for the older V2 line: it keeps the useful operator workflow and removes the known correctness regressions rather than simply reducing features.

It keeps the useful operator workflow:

MARKET DATA
→ STATE
→ CURRENT POSITION
→ TARGET POSITION
→ ACTION QUEUE
→ CHANGE MONITOR
→ ROLL RADAR
→ JOURNAL

and removes the paid VX dependency while keeping a fresh live path when OpenD is entitled and a zero-cost delayed Cboe failover.

## Active data path

QQQ / VXX / VIX:
1. Futu OpenD when available
2. Yahoo fallback per field

VX M1 / M2:
1. Futu OpenD VX live when available
2. Cboe public delayed VX endpoint (free, delayed)
3. manual test import
4. BLOCK

The Cboe web quote dashboard itself states that automated extraction of its delayed quote tables is prohibited. V3 therefore does not scrape the dashboard HTML. The delayed endpoint used by the adapter is treated as a public implementation surface, not as a contractual Cboe API guarantee. Users should verify permitted usage before unattended operation.

## Exact VX selection rule

- keep standard full-size VX monthly symbols only, e.g. VX/V6, VX/X6
- exclude numbered weekly-style VX contracts such as VX40/V6 and VX41/V6
- exclude VXM and VXT
- require expiry > New York as-of date
- sort by actual expiry date
- earliest eligible = M1
- second earliest eligible = M2
- S = (M2-M1)/M1
- settlement preferred for EOD/delayed cadence; last is optional fallback

The terminal never creates M2 from VIX, VIX-MA20, VXX or any synthetic proxy.

## User cadence

Designed for a 1–2 day operator refresh, not tick trading. OpenD VX is preferred when entitled; the free Cboe delayed path is the failover.

Every decision records:
- snapshot timestamp
- data as-of date
- per-field provenance
- M1/M2 code and expiry
- term slope
- state
- policy / engine version
- current position
- target position
- action
- reason
- human action
- conflict status

## Candidate vs Current Option Leg

**Candidate** is the next buy suggested from the option chain (Find QQQ / Find VXX). **Current Option Leg** is what is already held — Operator Memory / Watch fields (short, long, expiry, qty, entry credit, DTE, Δ). Candidate must never be confused with Current Leg: Cell 04 proves fixture selection; Cell 10 proves **Yahoo-only real retrieval** (LIVE or honest `OPTIONS_SOURCE_DOWN`); **Cell 11** adds the Yahoo→OpenD cascade (`providers/option_candidate_fetch.py`) with `BLOCKED_NO_OPEND` when OpenD is absent/not entitled — never invent strikes. `/api/options` uses the cascade (`status:"LIVE"` on HTTP 200; fail-soft `OPTIONS_SOURCE_DOWN` / `BLOCKED_NO_OPEND` on HTTP 502). Market regime (BUY / HOLD / REDUCE) is a separate clock from option maintenance: HOLD means do not add, keep existing; ROLL monitors held legs only. The ROLL panel prefers Cell 08 `currentOptionLegs` identity (DTE from explicit leg DTE, else calendar days from expiry→today; past expiry → 0) and never treats blank as zero.

## Operator clarity (Cell 13)

- Same-day delayed Cboe settlement + live last spot → `DATA FRESH · MIXED-SOURCE` warn badge (does not block; date-gap AS-OF MIXED >2d still blocks).
- VXX short exposure is **% NAV**; VXX call credit spreads are **contracts** (implied shares shown when VXX price is finite).
- Flat / zero option legs (or **No option legs**) silence ROLL — blank DTE never invents ROLL_NOW.

## Journal → Operator Memory (Cell 14)

After journaling (or from the last journal row), the operator can **從 Journal 還原 Memory · Restore Memory from last Journal** so a reload does not wipe Operator Memory. Map is 1:1 and easy to verify — **never** Candidate / NOW plan strikes.\n\n## Current Permission · Full Strategy

The operator screen now includes a read-only CURRENT PERMISSION · FULL STRATEGY table. It shows FULL frozen capacity, CAN KEEP NOW, MAX BUY NOW, and MAX SELL NOW for QQQ core, VXX short, QQQ far-call spreads, and VXX call spreads. QQQ FULL is displayed as **42% NAV plus its approximate share equivalent**; the frozen policy remains percentage-based.

Important: **CAN KEEP NOW does not mean CAN BUY NOW.** WEAKENING / HOLD keeps existing carry but permits no new short-vol carry; CARRY / BUY permits building toward the full target; REDUCE / SHOCK shows the current risk-reduction ceiling; DATA BLOCKED permits neither buy nor sell.

This is a visibility layer only. It does not create a second strategy, change the frozen policy, or submit broker orders.

## Strategy State → Operator Action Bridge (Cell 16)

Cell 16 is the read-only hand-off that closes the operator loop:

**DATA → DECISION → CURRENT → TARGET → FUNDING CONTEXT → WATCH → JOURNAL**

It takes the already-derived snapshot/state, the actual Memory position, the frozen target ledger, the Cell 15 funding context, current option-leg identity, and the last journal baseline. It returns one operator-facing **action class**:

- BUILD = frozen target currently calls for additions
- REBALANCE = engine remains BUY but Current → Target contains both additions and reductions
- MAINTAIN = hold existing position and watch the next transition
- DEFEND = frozen target currently calls for risk reduction
- PAUSE = data gate is blocked
- READY = no current position and no valid build delta

Cell 16 does not mutate targetLedger, does not turn Strategy Pool routing into execution sizing, and does not submit broker orders. Strategy Pool output is explicitly tagged **CONTEXT ONLY / RESEARCH ONLY**.

When a Journal event is written, the Cell 16 operator-facing result is stored under action_bridge. This records the hand-off without making the Journal a new source of strategy truth.



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

Rules: blank/missing → leave Memory EMPTY (do not write 0); explicit journal `0` → VALUE(0); map preview before/after apply; localStorage snapshot of last applied Memory + `event_id` restored on load.

## Safety

- signal / decision support only
- no broker order API
- no automatic order submission
- DATA BLOCKED never invents a REDUCE
- REDUCE states can only shrink current seller risk; they cannot create ADD
- human action never overwrites engine action; contrary action is JOURNALED as CONFLICT

## Lifecycle

### ACTIVE
- QQQ core
- QQQ far-call sleeve
- VXX short exposure
- VXX call sleeve
- real delayed Cboe M1/M2
- OpenD spot fallback
- state/target/action queue
- trigger monitor
- roll radar
- append-only decision journal

### RESEARCH ONLY
- historical source-swap parity
- historical P&L reconstruction
- 12.7049% / -23.1837% reference figures
- replay mode
- manual scenario overrides

### RETIRED / NOT IN V3 LIVE PATH
- Databento paid VX secondary
- VIX-as-M2 or any synthetic term proxy
- numerical "confidence %" claims without calibration
- automatic broker order transmission
- N/deployment parameter optimization inside the live terminal

V2 remains frozen for comparison. Do not silently change the Original Hybrid baseline inside V3.

## Local run

Windows CMD:

    cd C:\path\to\brush-timber-mountain-brook\terminal\qqq_hybrid_deployment_terminal_v3
    RUN.cmd

Then open:

    http://127.0.0.1:8788

No third-party package is required for the Cboe/Yahoo lane. Futu OpenD is optional.

