# QQQ Option Shortlist — Temporal / Friction Audit V1

Research-only follow-up for QQQ Option Shortlist Replay V1.

It reuses the persisted, SHA-pinned trade ledger rather than re-running or replacing the underlying option chain. It produces:
- BASE / ZERO / STRESS friction comparisons using explicit round-trip per-contract arithmetic.
- Full sample and 2018–2022 versus 2023–2025 descriptive splits.
- An exact-leg paired comparison for CALL_DEBIT_50D_10D and CALL_DEBIT_PLUS_LONG_PUT_10D.
- 0.5% / 1% / 2% NAV terminal-tail unit-capacity counts from the original audit outputs.

The ZERO / STRESS values are arithmetic sensitivity adjustments, not re-run executable fills. Period splits are descriptive after the exploratory full sample has been inspected; they are not virgin OOS. A trade episode's win rate and P&L are not portfolio CAGR / MaxDD or confirmed fills.
