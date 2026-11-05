# TAIL CALL insurance overlay

**Status: BLOCKED — historical TAIL option quotes not yet authorized/available.**

Core cohorts found: 2334.
Per core cohort: buy 6 TAIL CALL contracts, standard multiplier 100, limit no higher than USD 0.10/share.
Maximum gross option premium: USD 60 per cohort, plus commissions. Actual cost will be the observed Ask, not a forced USD 60.
Entry selection: OTM calls, 21–45 calendar DTE (target 30), Ask <= USD 0.10, displayed Ask size >= 6; closest Ask to USD 0.10 first.
Daily mark: NBBO Bid. Exit: follow the core cohort's exit date; defer if a six-lot bid is unavailable, then settle at intrinsic on expiry if expiry quotes are present.

No option P&L, hedge coverage, CAGR or MaxDD is reported because no historical TAIL CALL bid/ask/size series was available.
Required: provide ORATS historical Data API access by adding GitHub Actions secret ORATS_API_TOKEN to this repository. The published Delayed Data API plan is USD 199/month and includes historical EOD options data; this research does not purchase a subscription.
The existing TAIL ETF adjusted-close overlay is not used as a substitute for option P&L.
