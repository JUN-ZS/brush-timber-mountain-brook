# QQQ V22 Locked OOS Family V2 — local stand-in for Actions #632

TAKE_ID=qqq-v22-locked-oos-family-v2-run632-local
ASOF=2026-10-03
BRUSH_HEAD=55df185bdc6b343326a7a2e0cd7b9a298437478c
FREEZE_EQ=NO
THIS_TAKE ≠ V0.1

Research only. Not a live signal. Not a Champion vote. Not a broker order.

Actions run 37044768138 (#632) was queued on `self-hosted windows x64` behind run 37002600214 (#564, older SHA 7cd2fbd, same workflow, same runner `desktop-gnmq0pf`). This commit is the local completion of the #632 job steps, not a rewrite of locked V22 alpha.

- script: `research/qqq_v22_locked_oos_family_v2.py` from main `5d1ea092835d411c1f8d6f3fe71520dc30aa4b91` (not present on this research branch; left uncommitted)
- engine copy hash sha256: `12d8eb7725812ca99f27d14356aff8e8fb87a5c5e83c59fe31994fd676a40dc1`
- engine_commit stamp in manifest: `930c949ec5260865f2bf3ee1c6e030dab7b8e4c4`
- data: lambdaclass `options_portfolio_backtester` release `data-v1`
  - QQQ_options.parquet sha256 `1f831556cd87ec9d7af43d3b47a69a829ffb2fb199cfcef4ff55d289badf8734`
  - QQQ_underlying.parquet sha256 `78c015fd7fa9d493cd798d5ae81b3c2ae6dc3b8176e25e7bb90cd4114b103351`
- gamma_mode: OBSERVED_GAMMA (both windows)
- selection_status: LOCKED_FROM_PRIOR_FULL_SAMPLE_V22_AUDIT
- virgin_oos_status: NOT_VIRGIN_BECAUSE_PRIOR_SELECTION_USED_FULL_V22_SAMPLE

Family (72 configs, no sub-selection inside OOS):

| window | positive_config_ratio | median_config_pnl | total_pnl | far_pnl | near_realized | worst_campaign |
| --- | --- | --- | --- | --- | --- | --- |
| 2022-03-08 .. 2025-12-15 | 0.8889 | 9313 | 752996 | -644800 | 1397796 | -9827 |
| 2024-01-02 .. 2025-12-15 | 1.0000 | 10732.5 | 852234 | 187040 | 665194 | -9827 |
