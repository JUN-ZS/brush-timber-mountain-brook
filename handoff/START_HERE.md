# ULTIMATE EVOLUTIONARY TRADING BRAIN — HANDOFF V1

## READ ORDER
1. `handoff/STATE_OF_KNOWLEDGE.md`
2. `handoff/RESEARCH_CONTRACT.md`
3. `handoff/SOURCE_MAP.md`
4. `handoff/AI_RESEARCH_OPERATING_RULES.md`
5. `handoff/NEXT_AI_TASK_QUEUE.md`
6. `attachments/QQQ-VXX-ChatGPT-完整對話.md` — full original conversation archive
7. `attachments/EVB_EVOLUTIONARY_REPORT.md`
8. `attachments/spots_qqq_vxx_vix.1csv`
9. `research/data/vx_m1_m2_external_2016_2022.csv`
10. `terminal/qqq_hybrid_deployment_v2/`
11. `backtest/`

## MISSION
Build a deterministic, auditable, live decision-support system that reconstructs the historical strategy before optimizing it, separates observed/derived/estimated/hypothetical data, works in FULL and PARTIAL market-data states, compares current versus target positions, records why/what changed/what evidence is missing/what trigger comes next, and evolves only from validated historical evidence and OOS tests.

## HARD RULES
- No broker order routing.
- Never fabricate VX M1/M2.
- Never use VIX spot, VXX, CME/COMEX futures, or QQQ IV as fake VX M1/M2.
- Missing M1/M2 means TERM UNKNOWN; only term-dependent decisions are blocked.
- Human action is independent of engine action and may be marked CONFLICT.
- Historical CAGR/MaxDD/win-rate numbers are references until independently replayed.
- Monte Carlo is distribution analysis, not model validation.
- Do not tune just to force a remembered target.

## LIVE OPERATING MODEL
MARKET DATA
→ FEATURE ENGINE
→ STATE MACHINE
→ HISTORICAL ANALOG
→ STRATEGY COMPETITION
→ RISK / SURVIVAL
→ CURRENT → TARGET
→ HUMAN ACTION
→ JOURNAL
→ NEXT STATE
