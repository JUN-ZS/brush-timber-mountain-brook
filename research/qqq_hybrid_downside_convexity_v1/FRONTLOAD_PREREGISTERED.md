# QQQ_MUTUAL_CHASE_FRONTLOAD_V1 — PREREGISTRATION

RESEARCH_ONLY. The 10Y budget is fixed; only the timing of its target curve changes.

B=1, H=120.

For front-load fraction F:
C_t(F)=F*B+(1-F)*B*t/120.

Grid is fixed in advance:
F={0,10%,20%,30%,40%,50%,60%,70%,80%,90%,100%}.

F=0 is the original CLOCK. F=100% targets the full budget from month 1. Every curve reaches B at month 120.

Two-sided mutual chase:
- Month-t BUY/SELL dollar amount uses only prior month-end NAV versus C_t(F).
- Below target: BUY shortfall.
- Above target: SELL excess into internal harvest reserve.
- Future BUY uses harvest reserve first, then remaining planned budget.
- External contribution <= B; no borrowing.
- Execution at month-t close.

Economic wealth = QQQ NAV + planned reserve + harvest reserve.

Report full 153-window distributions and BUY/SELL/reserve turnover for every front-load level.

No finer search, optimizer, target reset, extra funding, leverage, or future-price read.
