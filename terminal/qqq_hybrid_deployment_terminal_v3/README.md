
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

**Candidate** is the next buy suggested from the option chain (Find QQQ / Find VXX). **Current Option Leg** is what is already held — Operator Memory / Watch fields (short, long, expiry, qty, entry credit, DTE, Δ). Market regime (BUY / HOLD / REDUCE) is a separate clock from option maintenance: HOLD means do not add, keep existing; ROLL monitors held legs only. The ROLL panel prefers Cell 08 `currentOptionLegs` identity (DTE from explicit leg DTE, else calendar days from expiry→today; past expiry → 0) and never treats blank as zero.

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

