# QQQ Put Ratio $1,000,000 Exit / Risk Reference V1

**Status: historical research reference only. Not a live trade ticket, not an approved optimal percentage, and not a broker margin calculation.**

## 1. Keep the two N:1 directions separate

- **Short-heavy N SHORT : 1 LONG**: sell N lower-strike QQQ puts and buy one higher-strike QQQ put at the same expiry. At N=5, four short puts remain net-uncovered after the long put offsets one short put. This is the direction of the historical 1 LONG : 5 SHORT exit replay.
- **Long-heavy N LONG : 1 SHORT**: buy N lower-strike QQQ puts and sell one higher-strike QQQ put at the same expiry. It has a different payoff, theta/vega profile and loss zone. The historical Run #7 figures below do **not** measure this direction.

Hub currently calculates N=1–6 for either orientation from the entered strikes and prices. That is an arithmetic research tool; it is not a historical performance ranking of every N.

## 2. Historical evidence actually available

Source of truth: [Windows self-hosted Run #7 — QQQ 1x5 Put Ratio Exit Measurement V1](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38508705688). Its pinned replay and offline tests completed successfully; the report was printed into the job log. Artifact upload failed separately because GitHub Actions storage quota was full, so use the run log/step summary rather than claiming there is a downloadable artifact.

The replay covered 2018-03-01 through the last available public EOD option-chain session, 2025-12-15. It opened **62 non-overlapping 1 LONG : 5 SHORT trade episodes**. 1,956 of 1,960 expected sessions through 2025-12-15 had a chain (99.7959% session coverage); 11 further expected sessions through 2025-12-31 were missing. Public EOD marks report a 16:00 US/Eastern snapshot but do not establish the exact tick timestamp or a confirmed fill. No gaps were filled. Base cost sensitivity was $0.05 per leg per side plus $0.65 commission per contract per side; those are hypothetical costs, not broker-confirmed fees.

### Base-cost results on the same fixed one-unit cohort

Base case: $0.05 slippage per leg per side + $0.65 commission per contract per side.

| Historical exit rule | Closed P&L sum | Expectancy / episode | Custom rule fired | Win rate | Profit factor |
| --- | ---: | ---: | ---: | ---: | ---: |
| DTE ≤ 7 safety exit (baseline) | $18,067.60 | $291.41 | 0/62 | 95.16% | 19.43 |
| Close at +$500 | $14,199.60 | $229.03 | 16/62 (25.81%) | 93.55% | 7.35 |
| Close at +$1,000 | $18,067.60 | $291.41 | 3/62 (4.84%) | 95.16% | 19.43 |
| Close at +$2,000 | $18,067.60 | $291.41 | 0/62 | 95.16% | 19.43 |
| Close at 25% of modeled terminal maximum gain | $17,220.60 | $277.75 | 7/62 (11.29%) | 95.16% | 18.56 |
| Close at 50% of modeled terminal maximum gain | $18,067.60 | $291.41 | 0/62 | 95.16% | 19.43 |
| +$1,000 in first 5 sessions → trim four shorts | $18,067.60 | $291.41 | 0/62 | 95.16% | 19.43 |
| Day-20 non-positive → close all short risk | $10,789.60 | $174.03 | 10/62 (16.13%) | 90.32% | 2.64 |
| Day-20 non-positive → trim four shorts | $9,568.60 | $154.33 | 10/62 (16.13%) | 85.48% | 2.21 |
| Stop at −$500 | $751.60 | $12.12 | 20/62 (32.26%) | 70.97% | 1.08 |
| Stop at −$1,000 | $14.60 | $0.24 | 10/62 (16.13%) | 83.87% | 1.00 |
| Stop at −$2,000 | −$5,325.40 | −$85.89 | 6/62 (9.68%) | 87.10% | 0.74 |

**Correct interpretation:** these are sums/expectancies for a fixed one-unit, non-overlapping episode cohort under EOD side-mark replay, not a continuously invested $100k or $1m account return. They do not establish CAGR, full-account MaxDD, margin survival or live execution. The $1,000 rule tied the DTE≤7 baseline; the $500 rule had lower aggregate P&L; the $2,000 rule never triggered. The data therefore do not prove that a round-dollar target is optimal.

## 3. Translate the historical reference into $1m NAV

The historical run normalized $500 / $1,000 / $2,000 to **0.5% / 1% / 2% of a $100,000 reference NAV**. The same percentages on a $1,000,000 NAV are:

| Reference percentage | Dollar threshold at $1m NAV | Meaning |
| ---: | ---: | --- |
| 0.5% | $5,000 | Lower candidate threshold; the old fixed-$500 test reduced aggregate P&L versus DTE ≤ 7 |
| 1.0% | $10,000 | Same percentage as the old $1,000 test; its result tied the baseline, with no proved incremental value |
| 2.0% | $20,000 | Same percentage as the old $2,000 test; it never triggered in the old sample |

A **$1,000** gain on the user's $1,000,000 NAV is only **0.10% NAV**. It is not equivalent to the $1,000 threshold in the historical $100,000 reference study. The $5,000 / $10,000 / $20,000 values are like-for-like percentage conversions, **not tested optimal thresholds**. A new replay must test NAV-percentage targets directly before selecting one.

## 4. “QQQ surged for three days — exit?” — what history can actually say

The replay's event study recorded 9 first EOD marks at or above +$1,000; **0 occurred within the first 5 holding sessions**, and all 9 occurred later. The explicit rule “+$1,000 within five sessions → trim four of five shorts” triggered **0/62** episodes. A three-session winner is therefore outside the evidence in this sample. It is not valid to infer a win-lock rule from QQQ spot movement alone.

Market context is separate from trade P&L: QQQ closed at $751.27 on 2026-10-09 and $728.92 on 2026-10-14, a roughly **−2.98% move over three subsequent sessions**, not a three-day rally ([historical prices](https://chartexchange.com/symbol/nasdaq-qqq/historical/)). It says nothing by itself about the mark-to-liquidate P&L of a particular put ratio.

A future shadow test should separately register:
1. mark after-cost whole-combo liquidation value at each observed close;
2. target threshold as a percentage of the *confirmed* NAV, not underlying QQQ return;
3. signal date and earliest executable next-session date;
4. two counterfactual management actions on the same eligible episode: close all short risk, versus buy back four of five shorts and retain one short + the long put;
5. later 5/10-session P&L, residual tail loss, action coverage and skipped/deferred actions.

Missing or stale quotes must remain PENDING; an intraday touch cannot be inferred from an EOD mark.

## 5. Tail risk is the first gating issue for short-heavy 1x5

In the historical 1x5 sample, the median terminal loss if QQQ settled at $0 was **$106,392.40**, and the maximum observed case was **$214,696.90**. Scaled only as a reference to $1,000,000 NAV, that is approximately **10.64%** and **21.47%** of NAV. Actual loss varies with the selected expiry, strikes and entry credit; zero-price intrinsic arithmetic is not a forecast and is not the broker's margin requirement. It also omits interim volatility/margin calls, early assignment and forced liquidation.

A 0.5% / 1% / 2% NAV loss budget at $1m is $5,000 / $10,000 / $20,000. The observed median 1x5 terminal-tail amount exceeds every one of these budgets. Thus the historical short-heavy 1x5 structure is **not cleared** by a low single-digit NAV tail budget on these observed contracts. Do not use the Hub package-count result as proof of adequate margin or capacity.

## 6. Current decision boundary and next tests

- For now, use **0.5% / 1% / 2% NAV ($5k / $10k / $20k at $1m) as a research sensitivity grid only**. There is no statistically supported “best percentage” yet.
- No automatic exit solely because QQQ's spot rose three sessions in a row. Evaluate the position's *net mark-to-liquidate P&L* and actual leg quotes.
- The evidence currently available is exact to **N=5 short-heavy only**. It does not rank N=1, 2, 3, 4 or 6, and does not provide historical exit results for N-long / 1-short.
- Next empirical test required: paired, fixed source/calendar replay for N=1–6 and both orientations where the source has valid contract/depth, with matched entry-side quotes, $ costs applied to every contract, NAV-relative 0.5% / 1% / 2% exit levels, first-3-session and first-5-session trims, DTE≤7 baseline, day-20 close/trim, full tail-payoff grid and a separate untouched/forward period if one becomes available.
- Main terminal risk whitelist remains QQQ call-credit and VXX call-credit only. This work preserves QQQ Put research and does not silently activate it, merge the two N:1 directions, alter Frozen Original Hybrid or authorize broker orders.
