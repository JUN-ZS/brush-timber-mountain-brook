# QQQ Forward Shadow Test V1 — Contract

Purpose: collect genuinely new, timestamped option observations after the pinned historical archive ends. Research-only; no live sizing promotion, broker API or order placement.

## Frozen candidate

Primary candidate: QQQ_REVERSAL_2P1_MA20_VIX5D_V1 with CALL_DEBIT_50D_10D. Evaluate CALL_DEBIT_PLUS_LONG_PUT_10D as a separate hedge hypothesis, not an automatic leg. PUT Ratio candidates remain blocked unless the whole structure passes terminal-tail budget, cash-reserve and visible-size checks.

Record a trigger only when all fixed facts hold:
- QQQ close is at least 2.1% below rolling MA20 on both current and previous observed sessions.
- QQQ closes up on the signal day.
- VIX is below its value five observed market sessions earlier.

Do not change signal thresholds, DTE/Delta selection, hold clock or cost assumptions after looking at forward outcomes; a changed rule becomes a new version.

## Immutable observation records

Store each snapshot as a new JSON file beneath snapshots/, with filename stem exactly equal to snapshot_id. Store its screenshot or source export beneath evidence/. Include a SHA-256 digest of the exact evidence bytes. Never modify an old snapshot; corrections use a new ID plus a correction note.

Each record includes snapshot date, an ISO-8601 capture time with UTC offset, account NAV, QQQ/VIX readings and their source times, event ID, strategy ID, event type, exact contract IDs, right, expiry, strike, LONG/SHORT position side, quantity, Bid/Ask, displayed sizes, Delta, quote date and quote capture time.

## Evidence and execution rules

- Permitted sources: manually captured delayed screen, broker export, or licensed historical source. Do not automatically scrape the free/delayed Cboe webpage; capture manually only where source terms permit.
- Quote date must match the observation date. Missing quotes are explicit nulls with a reason. No forward filling, interpolation, synthetic replacement contracts or silent contract-ID changes.
- For ENTRY and EXIT records, every leg must have side-correct quote prices and sufficient displayed size. Otherwise record BLOCKED_ENTRY or BLOCKED_EXIT; no fill is inferred.
- Set execution_enabled=false and order_placed=false in every snapshot.
- Validation proves only internal identity/provenance/field consistency. It does not authenticate an exchange fill or prove strategy edge.

## Minimum report once observations accrue

Report signal frequency, entries/exits, blocked actions, per-leg P&L, BASE/STRESS cost sensitivity, terminal tail loss, viable whole-unit count, time-to-exit, MAE/MFE, NAV reconciliation, unresolved exits and missing-mark uncertainty. Compare to QQQ Core on the same dates. No claim is out-of-sample until the parameter choices have been frozen before those observations.
