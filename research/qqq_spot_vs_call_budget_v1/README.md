# QQQ spot versus budgeted long-call study

Status: isolated research study; not a trading recommendation and not a broker-connected workflow.

## Frozen comparison

Each historical path has exactly USD 7,000 in total outside contributions:

1. QQQ spot buy-and-hold: invest the full USD 7,000 on the first session and hold for ten years.
2. Weekly long Call: contribute the USD 7,000 evenly over five-trading-session entry dates; select the OTM Call closest to +0.05 Delta in the accepted absolute-Delta band 0.01–0.10, with 7 DTE target and 5–10 DTE allowed.
3. Annual long Call: contribute USD 700 at each of ten yearly entry dates; select the OTM Call closest to +0.05 Delta in the same accepted Delta band, with 365 DTE target and 330–400 DTE allowed.

Options are whole contracts (100 multiplier), purchased at the observed historical ask. Cash that cannot buy a whole contract carries forward without interest. Expired-option proceeds also remain in the account and may fund later calls. Calls that reach expiration settle at intrinsic value using QQQ close on or immediately before expiration; only calls still open at the ten-year window end are marked at the latest observed bid within five calendar days, with intrinsic value counted as a fallback if no fresh bid exists. Commissions, taxes and fees are excluded.

The spot benchmark uses adjusted close if the source dataset provides one; otherwise it is a price-only comparison. Historical option chains are pinned by SHA-256 in the script and workflow. No Black–Scholes synthetic marks are used.

## Outputs

The GitHub-hosted Ubuntu runner creates:

- results/latest/study_report.md
- results/latest/aggregate_summary.csv
- results/latest/window_results.csv
- results/latest/candidate_coverage.csv
- results/latest/run_manifest.json

Rolling ten-year windows overlap heavily, so the distribution is an empirical path comparison, not a count of independent trials. The USD 7,000 spot benchmark is fully invested at the start while the Call strategies receive contributions through ten years; that timing difference is part of the requested comparison and is explicitly reported.
