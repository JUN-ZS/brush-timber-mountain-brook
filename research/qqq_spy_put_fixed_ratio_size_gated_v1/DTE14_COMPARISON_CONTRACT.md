# QQQ/SPY PUT DTE14 vs DTE45 Fixed-Anchor Comparison Contract V1

## Question
Under identical fixed entry cadence and contract-size rules, how do a near-two-week option selection and the existing ~45-DTE selection compare on realized entry-date moneyness, resolved outcome statistics, losses, unresolved exits and stacked short-SPY assignment exposure?

## Frozen arms
- Reference arm: DTE 30–60, target DTE 45.
- Test arm: DTE 7–21, target DTE 14.
- Both arms retain absolute Delta target 0.25 for each put leg, eligible absolute-Delta band 0.10–0.50, same expiry, standard contract identities, quote-side/displayed-size checks, fixed QQQ LONG PUT 1 : SPY SHORT PUT 3, no entry filter, overlapping cohorts, five immutable phases, and one scheduled opportunity every five common underlying sessions.
- Use the same source commit pins, history period 2018-03-01 through 2025-12-15, conservative quote sides, USD 0.05/option-share/side slippage and USD 0.65/contract/side commission.

## Replays must be independent
- DTE14 must run the full option selection, entry and exit quote checks, P&L accounting, and each of the five fixed-start phases. Do not reuse DTE45 strikes, option IDs, entry dates, P&L, or phase ledgers.
- A phase's scheduled indices are phase + k × 5, with skipped slots logged and no cadence reanchoring.
- Both arms must pass the fixed-slot audit and their OTM ledger reconciliation before the comparison report is written.
- Compare by phase × signal-date window (1Y, 3Y, 5Y) × exit policy. Never pool the five phase samples into an assumed independent-trade confidence interval.

## DTE14 exit policies
- Keep exit policies identical to the DTE45 reference: 5 sessions, 10 sessions, 20 sessions, and exit trigger at remaining DTE ≤ 7.
- Longer holding periods can approach or exceed DTE14 expiration before an executable close quote is found. Report unresolved trades explicitly; do not mark them as zero P&L.

## Outputs
- results/dte14_fixed_phase/fixed_phase_sensitivity/phase_0..phase_4/: independently replayed source manifests, cohort/trade ledgers, skip ledgers, and run metadata.
- results/dte14_fixed_phase/fixed_phase_sensitivity_audit/: fixed-anchor period/calendar comparison and integrity report.
- results/dte14_fixed_phase/fixed_phase_otm_audit/: per-leg strike-to-spot detail, entry/signal distributions, Delta diagnostics and input SHA-256 manifest.
- results/dte14_vs_dte45_audit/: paired performance and OTM CSVs, readable report, and manifest pinning the two input audits.

## Metrics and interpretation
- OTM percent = (underlying spot - put strike) / underlying spot × 100. Positive is OTM; zero is ATM; negative is ITM.
- Report OTM/ATM/ITM counts, median/mean signed OTM percent, win rate among resolved trades, opened/resolved/unresolved counts, average and total resolved P&L, worst resolved trade, cost stress, peak cohort overlap and gross SPY assignment obligation.
- Delta 0.25 is not a fixed OTM percentage or a guaranteed 75% win probability.
- EOD quote-side historical estimates are not verified fills. Additive fixed-size cohort P&L is not compounded account NAV. Gross SPY assignment obligation is not broker margin or a proof of account capacity.
