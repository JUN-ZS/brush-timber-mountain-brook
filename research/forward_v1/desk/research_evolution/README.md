# Desk（信股慣性台）RESEARCH EVOLUTION V1

Learning layer on RESEARCH MEMORY V1. Does **not** replace memory artifacts.

## Files
- `RESEARCH_STATE.json` — node counts, resolved/waiting horizons, hypothesis lifecycle
- `HYPOTHESES.jsonl` — frozen hypotheses (formula immutable after freeze)
- `EVIDENCE_LOG.jsonl` — append-only evidence actions
- `DISCOVERY_RUN_*.json` — per forward-run discovery/evidence deltas
- `REPORT_RESEARCH_EVOLUTION.html` — interactive panel

## Locks
- DISCOVERY ≠ TRADING RULE
- HYPOTHESIS ≠ BUY
- observed ≠ probability; score/alignScore ≠ probability
- book_ADD = OBSERVATION only; never upgrade → MARK_BUY
- T0 untouched; LIVE ≠ REPLAY mix
- Discovery cohort (T0 market_bar_asof) ≠ confirmation cohort (EMPTY_UNTIL_T1)
- When resolved_*=0: freeze WAITING dimension hypotheses — do not invent returns (BEAM #42)
