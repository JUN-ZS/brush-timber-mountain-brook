# PUT Out-of-the-Money Distance Audit Contract V1

## Purpose
Measure the actual strike-to-underlying distance of the selected QQQ LONG PUT and SPY SHORT PUT legs. An absolute Delta target of 0.25 is a selection target, not a fixed percentage OTM and not a guaranteed probability of expiring OTM or winning.

## Formula and status
For a put, at each reference time:

- Signed OTM percentage = (underlying spot - put strike) / underlying spot × 100.
- Positive percentage means OTM.
- Zero means ATM.
- Negative percentage means ITM.

The audit records both signal-date spot and actual entry-date spot. Entry-date moneyness is the primary diagnostic because the option contract is selected on the signal date and can enter on a later common session.

## Strategy is not re-filtered
- Keep absolute-Delta target = 0.25 and eligible absolute-Delta band = 0.10–0.50.
- Keep the same-expiry and DTE selection rule, fixed 1 QQQ LONG PUT : 3 SPY SHORT PUT ratio, no-filter signals, every-five-common-session schedule and overlapping cohorts.
- Do not silently discard a selected contract if its strike is at/above spot. Preserve the sample and report ATM/ITM rows as explicit warnings. This diagnostic must not improve measured results by changing the sample.
- Recompute reported percentages from spot and strike; the audit fails on missing required ledger fields, invalid standard PUT contract identity, Delta outside the engine's eligible band, or an unreconciled percentage/status.

## Outputs
- results/fixed_phase_otm_audit/entry_leg_otm_detail.csv: one row per phase, entry cohort and leg; contract ID, strike, signal/entry spot, signed distance and status.
- results/fixed_phase_otm_audit/phase_leg_otm_summary.csv: mean, median, min/max signed distance and OTM-only distance, plus OTM/ATM/ITM counts by phase, leg and reference time.
- results/fixed_phase_otm_audit/phase_leg_delta_summary.csv: selected absolute-Delta distribution by phase and leg.
- results/fixed_phase_otm_audit/report.md and manifest.json: human-readable result, source ledger SHA-256 hashes and row reconciliation.

## Interpretation limits
- These are historical EOD underlying closes and selected option-chain Greeks, not verified fills.
- A positive OTM percentage measures moneyness only. It does not establish profit, win rate, or a true probability of profit.
- The audit does not model strike adjustment, implied-volatility changes, assignment, slippage beyond the separate replay model, or actual broker fills.
