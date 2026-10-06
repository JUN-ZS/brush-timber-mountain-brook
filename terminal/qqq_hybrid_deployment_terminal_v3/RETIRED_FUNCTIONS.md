
# V3 Function Lifecycle

| Function / mechanism | V3 status | Reason |
|---|---|---|
| Cboe delayed VX M1/M2 | ACTIVE | Zero-cost delayed term input for intended 1–2 day cadence |
| Futu OpenD QQQ/VXX/VIX | ACTIVE | Existing local source / fallback |
| Futu OpenD VX | ACTIVE FALLBACK | Better freshness when entitlement exists |
| Yahoo QQQ/VXX/VIX | ACTIVE FALLBACK | Per-field resilience; provenance preserved |
| Manual M1/M2 | TEST ONLY | Scenario / recovery only; never disguised as observed |
| Databento CFE VX | RETIRED FROM V3 | Paid secondary no longer needed for the intended free cadence |
| VIX → M2 proxy | FORBIDDEN | Not a real VX term structure |
| VIX-MA20 synthetic slope | FORBIDDEN | Research reconstruction only |
| Automatic broker order routing | RETIRED | User's current terminal is signal/decision support only |
| Numerical confidence score | RETIRED | Uncalibrated confidence is misleading |
| N/deployment optimizer | RESEARCH ONLY | Avoid contaminating fixed Original Hybrid terminal policy |
| Historical CAGR headline | REFERENCE ONLY | Never used as optimizer target or live confidence |
| Browser notification as primary monitor | RETIRED | V3 uses explicit refresh + journal; persistent service remains outside the terminal |
| Replay | RESEARCH ONLY | Uses frozen historical inputs and is not live state |
