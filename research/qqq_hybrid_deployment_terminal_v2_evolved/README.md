# QQQ Hybrid Deployment Terminal V2 — EVOLVED (OpenD fix, 2026-10-06)

Simulation-only terminal (no order routing; STRATEGY_LOCK / policy constants unchanged).
Full source in `terminal/`, zip in `attachments/QQQ_HYBRID_DEPLOYMENT_TERMINAL_V2_EVOLVED.zip`.

## What changed (server.py / app.js / RUN.cmd / README)
- `US.VIX` (invalid, `未知股票 VIX`) → `US..VIX` (Futu US-index code), requested in its **own** snapshot so a
  permission error no longer pushes QQQ/VXX off OpenD into the Yahoo fallback.
- VX M1/M2 discovery restricted to `^US\.VX\d{4}$` monthlies from `get_stock_basicinfo(Market.US, SecurityType.FUTURE)`
  (excludes `VXM` mini and `VXmain/current/next` aliases); M1 must be the front contract.
- When VX quotes are blocked, snapshot still reports `m1_code/m2_code/m1_expiry/m2_expiry` (identity only) with
  `m1/m2 = null`, `term_structure = BLOCKED` → UI stays DATA BLOCK and shows "no CBOE quote permission".
- `vix`: OpenD `US..VIX` if permitted, else Yahoo `^VIX` (labeled in `sources.vix`).
- New `vix_proxy` (prior brush `backtest/vix_proxy.py` pattern): DERIVED QQQ ~30D ATM put IV from OpenD; informational only.
- Per-field `sources`, `errors`, a lock around the shared OpenD context, UTF-8 JSON; `RUN.cmd` prefers `py -3`.

## Live retest (2026-10-06 19:09 HKT)
`source=OPEND+YAHOO`, qqq 756.2 (OPEND), vxx 17.2 (OPEND), vix 15.34 (YAHOO ^VIX), m1/m2 null (BLOCKED),
m1_code US.VX2610 (2026-10-21), m2_code US.VX2611 (2026-11-18), vix_proxy 19.33 (QQQ261106P756000, 31 DTE).
See `evidence/`.

## To unblock M1/M2
Buy/enable CBOE futures quotes (and US index quotes for `US..VIX`) for the Futu account; no code change needed.
