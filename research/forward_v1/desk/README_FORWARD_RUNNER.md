# Desk FORWARD RUNNER V1.0（信股慣性台）

## 入口

```bash
cd /path/to/brush-timber-mountain-brook
python research/forward_v1/desk/forward_runner.py --now
# 或
python research/forward_v1/desk/forward_runner.py
```

兩者都跑完整 FORWARD NOW cycle（含 RESEARCH MEMORY；即使 NEW_SIGNAL=0 都會更新 memory）。

單獨建 memory：

```bash
python research/forward_v1/desk/tools/research_memory_build.py
```

## 做咩

DATA →（原引擎檢查）→ SIGNAL CAPTURE → IMMUTABLE EVENT  
→ RESEARCH SHADOW BOOK（book_ADD 閘）→ OUTCOME RESOLUTION  
→ RESEARCH MEMORY（profile → signal append → outcome join → analysis → report）  
→ RUN HISTORY → STATUS → HTML REPORT

## Hard locks

- GitHub SoT > chat
- T0 immutable（`T0_20260921T183800/`）
- `book_ADD ≠ MARK_BUY`
- `evaluation_clock=LIVE_FORWARD`
- score / alignScore / opportunity ≠ probability
- 唔同 Cap-Rail/RelVol REPLAY 混池
- YAHOO_FALLBACK 要標 provenance
- signal_memory append-only；profile versioned
- 唔發明 FIT / confidence / P&L

## 產物

- `run_history/FORWARD_RUN_<UTC>.json` — 每次 cycle 永久 append
- `reports/REPORT_*.html` + `ANALYSIS_*.json`
- `ledgers/` — positions / trades / signal_trade_map / portfolio_daily / execution_gate_log
- `shadow_book/SHADOW_BOOK_STATUS.json`
- `status/FORWARD_SYSTEM_STATUS.json` + `RECONCILIATION.json`
- `research_profile.json` — research_profile_v1 + provenance
- `research_memory/` — signal_memory / signal_outcome_join / REPORT_RESEARCH_MEMORY.html
- `conditional_analysis/CONDITIONAL_5D_DECLARED_V1.json` — DECLARED_V1 桶
