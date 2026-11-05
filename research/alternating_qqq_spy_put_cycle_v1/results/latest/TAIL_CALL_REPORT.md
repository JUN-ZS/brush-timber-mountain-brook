# TAIL CALL overlay — QQQ/SPY DTE20 alternating PUT strategy

**Status: BLOCKED — no ORATS_API_TOKEN was available in GitHub Actions.**
Core strategy: alternate_dte20_every10; DTE target 20; new cohort every 10 common sessions; A/B alternating.
Core-only ending NAV: USD 96,447.50; net P&L: USD -3,552.50.
Core-only MaxDD: USD -14,746.40 (-13.84%).
TAIL overlay rule: buy six standard TAIL CALLs per core cohort, natural Ask <= USD 0.10/share, displayed Ask size >= 6; maximum gross premium USD 60 per cohort plus commissions.
TAIL CALL entry DTE: 21–45 calendar days (target 30); OTM calls only.

**No option P&L, hedged MaxDD, or post-TAIL ending NAV/net P&L is calculated.** Historical TAIL CALL bid/ask/size data was not accessed; no TAIL ETF proxy or synthetic option mark is used.
Required to complete the hedge comparison: add ORATS historical-data API access as the GitHub Actions secret ORATS_API_TOKEN, then rerun the overlay.