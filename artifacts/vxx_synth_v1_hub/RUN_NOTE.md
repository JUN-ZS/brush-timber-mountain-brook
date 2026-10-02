# VXX Synthetic Option Tape V1 — local stand-in for Actions #37

TAKE_ID=vxx-synthetic-option-tape-v1-run37-local
ASOF=2026-10-03
BRUSH_HEAD=1ab79bc
FREEZE_EQ=NO
THIS_TAKE ≠ V0.1

Research only. MODEL_DERIVED_VXX_OPTION_TAPE. Not OPRA. Not LIVE. Not a broker order.

Actions #37 (run 37040890856) was queued on self-hosted runners and was cancelled so it would not stay queued. This commit is the HUB WEB / Linux `--summary-only` path of that job. Full tape write was OOM-killed on this 1.9GB host after the CONSERVATIVE parquet began (exit 137); summary-only does not materialize the four parquet tapes.

- quality_gate: PASS
- regression_test: PASS
- days: 1959 (2018-02-26 .. 2025-12-15)
- rows per family: 775764
- canonical_fingerprint: 59fe75db1e180e4cb01786577ef42b28c51ae11a1c159817f3d109185be6661f
- family_fingerprint: 7489a6f388feffcf7562babb1970de36ed4687bc50b659dc20174fd10031f5b6
- state_fingerprint: b1b009abbfd5e7e5ca6661dad8538c567c97ae93c3e8f74cfc40103cfc47808c
- script_sha256: 2fd0afdbcbe2adf52d08df965b5b0110449b7a47e079a9eac9c6ace41d1a6c14
- spots sha256: f80002db109f76ce6a84f51471cecf6051df91aa6cab466ccc99e0ef7cc45d4d
- QQQ_options sha256: 1f831556cd87ec9d7af43d3b47a69a829ffb2fb199cfcef4ff55d289badf8734
- QQQ_underlying sha256: 78c015fd7fa9d493cd798d5ae81b3c2ae6dc3b8176e25e7bb90cd4114b103351
- python: 3.10.21

Family tape fingerprints:
- CONSERVATIVE ae2c61ca9d9a35f66d2bee4923b1d703e08ba94a4e61ff2b619847a33edef875
- CENTRAL f76670fc9634ca95cb08342cf805b5e2c6a0a1625fa04d408f41951ba3c4bd2b
- HIGH_SKEW 60fc106bb1c623704633b45d8d4468dd3f79d581e2022a047c29c900c6f7e1b9
- STRESS 870d2bd813952451199dddbafe41c933bc5ee7ea47804d205deda780bf1a8069
