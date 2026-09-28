# Desk APP_INTENT_PROFILE (documentation of truth)

See `APP_INTENT_PROFILE.json` for the machine-readable contract.

## One-line intent
信股慣性台 (`xin_gu_inertia_desk` / `DESK_CORE_V1`) scans `DEFAULT_SYMBOLS` via juniper-kite `scanSymbol` + `marketTape`, and emits AS_EMITTED research signals (`desk.book_ADD` | `desk.MARK_BUY` | `desk.ARMED` | `desk.TRUST_UP`) from original engine geometry — never Yahoo-invented geometry.

## Hard distinctions (code-backed)
- `book_ADD` = BOOK_ACTION / OBSERVATION (`EXECUTION_POLICY.md`) ≠ `MARK_BUY`
- `alignScore` / `opportunity` = NOT_A_PROBABILITY; `claimed_p=null`
- Yahoo = bar/outcome feed only
- T1 genuine emit requires provenance_gate=REQUIRED (`source=ORIGINAL_ENGINE` + engine_run_id + source_hash + Desk geometry)

## Genuine T1 already on main
`market_bar_asof=2026-09-25`, 7× `desk.book_ADD`, MARK_BUY=0. Next progress = completed US daily bars **after** that asof for 5D/21D/… maturity — not a new T1 mint.
