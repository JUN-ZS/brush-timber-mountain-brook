RelVol_WEEKLY_DESC_PANEL_SPY_QQQ_VXX
=====================================

STATUS: DESCRIPTIVE / ASSOCIATION_ONLY / NOT credit
Credit: LOCKED (no credit, no trading claims, no Yahoo fill, no Option EV)

Pack (READ-ONLY):
  path: /workspace/tango-shadow-bay-apple/DATA/replay/WAREHOUSE_L1_2026-09-06
  pack_hash verified: 7ca13ce290d28db4
  (manifest.manifest_hash + recomputed SHA256[:16] + bars.symbol_index.json manifestHash)

Purpose:
  Full-history weekly long panel for join with QQQ/VXX RelVol V2.2 association maps.
  Own-history PIT week abs-vol percentiles + LAST_STATE bins (PR#9 / path_credit_archaeology spirit).

Symbols:
  Primary: SPY, QQQ
  VXX: PRESENT
  Missing in warehouse for this build: none (SPY, QQQ, VXX all present)

Method (PIT, no look-ahead):
  - Source bars: warehouse bars.jsonl adj_close (seek by symbol_index ranges)
  - Week sample: every WEEK_STEP=5 trading bars, aligned from each symbol series end
    (same as research/path_credit_archaeology)
  - week_abs = |log(adj[t]/adj[t-5])|
  - weekPct = empirical rank of current week_abs among prior week samples whose bar
    index is within hist_cap of current index (samples[:si] only — no future weeks)
  - MIN_WEEK_HIST = 40 prior weeks required before first emitted row
  - hist_cap by tier: FULL_LONG=2520, MID=1260, SHORT=252, ULTRA_SHORT=63
    tier = FULL_LONG if n_daily>=2520 OR first_date<=2016-12-31; else MID/SHORT/...
  - LAST_STATE from weekPct: <0.30 LOW / <0.70 NORMAL / <0.90 HIGH / >=0.90 EXTREME

dispersion_state (OBSERVED proxy from warehouse alone — NOT IV dispersion):
  Join key: ISO calendar week of week_end (iso_week = YYYY-Www).
  Peer:
    SPY row  → peer QQQ weekPct same iso_week
    QQQ row  → peer SPY weekPct same iso_week
    VXX row  → peer SPY weekPct same iso_week
  gap = |weekPct_symbol - weekPct_peer|
  bands:
    LOW  if gap < 0.15
    MID  if 0.15 <= gap < 0.30
    HIGH if gap >= 0.30
    NA   if peer has no row that iso_week
  Columns dispersion_gap / dispersion_peer document the numeric gap and peer used.
  Do NOT invent IV / options dispersion.

Optional columns:
  week_abs          — week absolute log-return
  n_hist            — count of prior weeks in PIT hist window
  market_band       — SPY LAST_STATE on same iso_week (else NA)
  relative_to_SPY   — ABOVE/BELOW/INLINE vs SPY weekPct (eps=0.10); SPY=INLINE
  iso_week          — ISO week key used for peer joins
  pack_hash         — pinned warehouse hash

Row counts:
  SPY: n=1651  week_end 1993-11-23 → 2026-09-04  tier=FULL_LONG hist_cap=2520
  QQQ: n=1343  week_end 1999-12-30 → 2026-09-04  tier=FULL_LONG hist_cap=2520
  VXX: n=392  week_end 2018-11-21 → 2026-09-04  tier=MID hist_cap=1260
  TOTAL: 3386

Outputs:
  CSV:     /workspace/sp500-vol/output/RELEASE/RelVol_WEEKLY_DESC_PANEL_SPY_QQQ_VXX.csv
  parquet: NOT written (optional; pyarrow/pandas unavailable in box env)
  README:  /workspace/sp500-vol/output/RELEASE/RelVol_WEEKLY_DESC_PANEL_SPY_QQQ_VXX_README.txt

Reuse:
  Logic mirrored from:
    research/path_credit_archaeology/run_path_credit_archaeology.py
    research/l1_descriptive_inertia_features/build_l1_descriptive_inertia_features.py
  (level_of / WEEK_STEP / MIN_WEEK_HIST / hist_cap / PIT percentile)

Generated: UTC build on box; data_asof pack calendar_end=2026-09-04
