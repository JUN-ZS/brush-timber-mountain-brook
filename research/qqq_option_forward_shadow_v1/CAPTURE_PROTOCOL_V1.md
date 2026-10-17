# QQQ Forward Shadow Capture Protocol V1

**State: intake kit only. No market observation is included or implied by these templates.**

## Why this is the next experiment

The verified historical QQQ option archive ends on **2025-12-15**. The completed NAV-scale replay uses 28 exploratory signals and does not establish a virgin holdout edge. It also shows:
- CALL_DEBIT_50D_10D is the only structure from this shortlist worth keeping for further research, but it did not improve both return and drawdown consistently.
- Adding the same-expiry LONG PUT did not produce a consistent matched P&L improvement.
- PUT short-heavy 1x5 and 1x6 remained blocked for every NAV checkpoint ($80k, $100k and $1m) under the tested terminal-tail budgets. Their high one-unit episode win rates do not imply deployable capacity.

The next experiment is therefore a **prospective, timestamped paper observation** of CALL_DEBIT_50D_10D, with CALL_DEBIT_PLUS_LONG_PUT_10D as a separately recorded paired control when all three listed contracts are valid. QQQ Core is the underlying-only same-date control. Do not add new strategies or tune the signal threshold from the previously viewed sample.

## Frozen signal and candidate-selection rules

Signal rule ID: **QQQ_REVERSAL_2P1_MA20_VIX5D_V1**. A signal is TRIGGERED only when all are true:
1. QQQ close is at least 2.1% below rolling MA20 both today and the previous observed session.
2. QQQ closes up on the signal day.
3. VIX is below its value five observed market sessions earlier.

Keep all signal outcomes, including NOT_TRIGGERED and INCOMPLETE; do not log only the winners. The cooldown is 15 observed market sessions, as fixed in the source screen.

For a triggered day t, select and freeze exact listed QQQ contracts from the day-t chain:
- CALL_DEBIT_50D_10D: one LONG CALL below spot nearest +0.50 Delta, one SHORT CALL above spot nearest +0.10 Delta; same expiry, expiry selection target 45 calendar DTE and valid range 30–60 DTE.
- CALL_DEBIT_PLUS_LONG_PUT_10D: the same two calls plus one same-expiry LONG PUT below spot nearest -0.10 Delta. Record this as a separate strategy/event pair. If no valid same-expiry put exists, record the candidate as INCOMPLETE or blocked; do not silently omit the hedge and still label the observation “hedged”.
- No contract substitution after the signal record. If the precise selected contract has no valid quote at the next-session entry, record BLOCKED_ENTRY; do not replace it with a neighboring strike.

These choices are frozen research rules, not a recommendation to trade.

## Observation clock

1. **Signal at close t.** Capture QQQ close, MA20, previous-session distance, VIX, VIX five-session comparison, and the exact contract IDs selected from that day’s chain. The signal snapshot’s legs freeze the exact planned structure. If no valid structure can be selected, record an INCOMPLETE signal with no planned entry.
2. **Entry no earlier than next observed session t+1.** Reuse exactly the same IDs and expiry from the signal snapshot. Use the side-correct displayed price and depth. For entry: LONG buys at Ask and SHORT sells at Bid. If any leg fails quote/depth/identity checks, record BLOCKED_ENTRY, not a fill.
3. **Daily marks.** Preserve exact contract IDs and quantities. A missing quote is MISSING_MARK with null Bid/Ask/size/Delta and an explicit reason. Never carry a prior mark forward, interpolate or estimate a price.
4. **Scheduled exit.** First valid exact-ID, side-correct close at or after 10 observed sessions. For exit: LONG sells at Bid and SHORT buys at Ask. Defer missing/invalid exits for at most three observed sessions; after that record the position as censored rather than pretending it was closed.
5. **Keep paired candidates separate.** One event ID per signal date and strategy variant; the CALL-only record and CALL-plus-PUT record need different event_id/strategy_id pairs. Do not combine their P&L into one strategy.
6. **Account replay after collection.** The raw snapshots are quote evidence, not fills. Only after enough snapshots have accrued should per-leg cashflows, slippage, commissions, tail-risk sizing, available whole-contract capacity, P&L attribution and QQQ Core deltas be replayed at $80k, $100k and $1m NAV checkpoints.

## Evidence and timezone rules

Use only a source whose terms permit manual capture, broker export or licensed data. Allowed validator source types are MANUAL_SCREEN_CAPTURE, BROKER_EXPORT, and LICENSED_HISTORICAL_DATA. **Do not automatically scrape Cboe’s free/delayed quote webpage.** No broker API, order submission or live execution is enabled.

For each snapshot:
- Save the original screenshot or export unchanged under research/qqq_option_forward_shadow_v1/evidence/.
- Store the snapshot JSON under research/qqq_option_forward_shadow_v1/snapshots/ with a filename whose stem equals snapshot_id.
- Compute SHA-256 over the original evidence bytes; enter that digest in source.evidence_sha256.
- Set source.observation_timezone to the IANA timezone in which the provider dates its market observations, e.g. America/New_York for an Eastern-time market screen. Do not assume the computer’s local timezone is the provider timezone.
- ISO-8601 timestamps must retain their **actual offset**. The validator converts captured_at, market timestamps and leg quote timestamps to source.observation_timezone before comparing their market date to snapshot_date. Example: 2026-10-21T03:55:00+08:00 is 2026-10-20T15:55:00-04:00 in New York during daylight-saving time. This conversion fixes the midnight boundary without falsifying timestamps.
- If the source does not show exact contract identity, quote timestamps, both sides, displayed sizes and usable Delta for selection, mark the observation incomplete/blocked or use another permitted source. Do not derive a synthetic Delta or fill a quote gap.
- Snapshot and evidence files are append-only. Corrections get a new ID and a note; never overwrite the original capture.
- Templates live under templates/, **not** snapshots/, and must not be counted as observations. They contain deliberate FILL_REQUIRED fields and will fail validation until filled.

On Windows, hash an evidence file with:
    certutil -hashfile "C:\path\to\evidence.png" SHA256

On Linux, use:
    sha256sum evidence.png

## Validation commands

From the repository root, after placing real, completed records under snapshots/ and the untouched evidence files under evidence/:

    python research/qqq_option_forward_shadow_v1/validate_shadow_snapshot.py --snapshot research/qqq_option_forward_shadow_v1/snapshots/SNAPSHOT_ID.json --root research/qqq_option_forward_shadow_v1

or validate the append-only directory:

    python research/qqq_option_forward_shadow_v1/validate_shadow_snapshot.py --snapshot-dir research/qqq_option_forward_shadow_v1/snapshots --root research/qqq_option_forward_shadow_v1

The first capture must be sourced from an actual permitted source. No forward sample has been fabricated or pre-populated.

## Promotion gate

No signal win rate, CAGR or MaxDD target is predeclared. Review source coverage, valid and blocked entries/exits, missing-mark rate, per-leg P&L, BASE/STRESS friction, MAE/MFE, terminal loss, size feasibility, NAV reconciliation and uncertainty. Do not promote to HUB or live sizing unless there is sufficient prospective coverage, a frozen rule set, independent review and an untouched later evaluation. No broker orders are permitted in this phase.
