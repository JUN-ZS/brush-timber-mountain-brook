# QQQ Put Ratio $1,000,000 Exit / Risk Reference V1

**Status: historical research reference only. Not a live trade ticket, not an approved optimal percentage, and not a broker margin calculation.**

## 1. Keep the two N:1 directions separate

- **Short-heavy N SHORT : 1 LONG**: sell N lower-strike QQQ puts and buy one higher-strike QQQ put at the same expiry. At N=5, four short puts remain net-uncovered after the long put offsets one short put. This is the direction of the historical 1 LONG : 5 SHORT exit replay.
- **Long-heavy N LONG : 1 SHORT**: buy N lower-strike QQQ puts and sell one higher-strike QQQ put at the same expiry. It has a different payoff, theta/vega profile and loss zone. The historical Run #7 figures below do **not** measure this direction.

Hub currently calculates N=1–6 for either orientation from the entered strikes and prices. That is an arithmetic research tool; it is not a historical performance ranking of every N.

## 2. Historical evidence actually available

Source of truth: [Windows self-hosted Run #7 — QQQ 1x5 Put Ratio Exit Measurement V1](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38508705688). Its pinned replay and offline tests completed successfully; the report was printed into the job log. Artifact upload failed separately because GitHub Actions storage quota was full, so use the run log/step summary rather than claiming there is a downloadable artifact.

The replay's pinned entry-selection rule chose a same-expiry pair at **30–60 calendar-day DTE on entry (target 45 DTE)**. It is therefore an approximately one-month-to-expiry cohort, not an exact 30-DTE-only cohort. The replay covered 2018-03-01 through the last available public EOD option-chain session, 2025-12-15. It opened **62 non-overlapping 1 LONG : 5 SHORT trade episodes**. 1,956 of 1,960 expected sessions through 2025-12-15 had a chain (99.7959% session coverage); 11 further expected sessions through 2025-12-31 were missing. Public EOD marks report a 16:00 US/Eastern snapshot but do not establish the exact tick timestamp or a confirmed fill. No gaps were filled. Base cost sensitivity was $0.05 per leg per side plus $0.65 commission per contract per side; those are hypothetical costs, not broker-confirmed fees.

**Three distinct clocks (do not conflate):** (1) entry DTE = 30–60 calendar days at entry, target 45; (2) holding age = observed trading sessions after entry, with entry date age 0; (3) current remaining DTE = calendar days left at the mark. The DTE≤7 baseline is a safety exit on clock (3), not the opening tenor and not a “close after 3/5 days” rule.

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

## 5. Worked $1m model scenario — not an observed option chain

This is an illustrative model calculation so the N sensitivity is numerically visible, **not** a quote, a backtest, or a live ticket.

Assumptions: QQQ reference close $728.92 (2026-10-14); 45 calendar days to expiry; flat 22% volatility; 3.75% annual risk-free rate; standard 100 multiplier. Black–Scholes gives approximately $11.06 for the $705 long put (absolute delta about 0.298) and $2.72 for the $665 short put (absolute delta about 0.099). For the entry scenario only, approximate the long Ask as model value + $0.05 and the short Bid as model value − $0.05; charge $0.65 per contract for entry commission. Actual expiry, bid/ask, displayed size, volatility skew, costs, assignment and margin are not authenticated.

For N short puts at $665 and one long put at $705:
- Entry net cash flow (positive = credit, negative = debit) = (100[N(2.7246-0.05)-(11.0642+0.05)]-0.65(N+1)).
- P&L if QQQ settles at $0 = entry net cash flow + (100(705-N\times665)).
- For N≥2, the zero-price outcome is the modeled terminal tail loss. For N=1 this is a 1×1 debit put vertical, not a short-heavy ratio; its maximum terminal loss is the entry debit.

| N SHORT : 1 LONG | Modeled entry cash flow | P&L at QQQ = $0 | Estimated max terminal loss | % of $1m NAV |
| ---: | ---: | ---: | ---: | ---: |
| 1 : 1 | $845.25 debit | +$3,154.75 | $845.25 | 0.085% |
| 2 : 1 | $578.44 debit | −$63,078.44 | $63,078.44 | 6.308% |
| 3 : 1 | $311.63 debit | −$129,311.63 | $129,311.63 | 12.931% |
| 4 : 1 | $44.81 debit | −$195,544.81 | $195,544.81 | 19.554% |
| 5 : 1 | $222.00 credit | −$261,778.00 | $261,778.00 | 26.178% |
| 6 : 1 | $488.82 credit | −$328,011.18 | $328,011.18 | 32.801% |

**What this scenario says:** under this particular assumed strike pair, N=2–6 all exceed a 2% NAV tail budget ($20,000). The credit received for N=5 or N=6 is tiny beside the zero-price tail. N=1 fits the budget but is not an asymmetric short-heavy ratio. This is not enough to choose a current trade: actual strikes/expiry/quotes can materially change the result, and the $0 payoff does not model path-dependent margin calls or forced liquidation. The Hub must remain PENDING until the current broker chain and contract terms have been checked.

## 6. Tail risk is the first gating issue for short-heavy 1x5

In the historical 1x5 sample, the median terminal loss if QQQ settled at $0 was **$106,392.40**, and the maximum observed case was **$214,696.90**. Scaled only as a reference to $1,000,000 NAV, that is approximately **10.64%** and **21.47%** of NAV. Actual loss varies with the selected expiry, strikes and entry credit; zero-price intrinsic arithmetic is not a forecast and is not the broker's margin requirement. It also omits interim volatility/margin calls, early assignment and forced liquidation.

A 0.5% / 1% / 2% NAV loss budget at $1m is $5,000 / $10,000 / $20,000. The observed median 1x5 terminal-tail amount exceeds every one of these budgets. Thus the historical short-heavy 1x5 structure is **not cleared** by a low single-digit NAV tail budget on these observed contracts. Do not use the Hub package-count result as proof of adequate margin or capacity.

## 7. Current decision boundary and next tests

- For now, use **0.5% / 1% / 2% NAV ($5k / $10k / $20k at $1m) as a research sensitivity grid only**. There is no statistically supported “best percentage” yet.
- No automatic exit solely because QQQ's spot rose three sessions in a row. Evaluate the position's *net mark-to-liquidate P&L* and actual leg quotes.
- The evidence currently available is exact to **N=5 short-heavy only**. It does not rank N=1, 2, 3, 4 or 6, and does not provide historical exit results for N-long / 1-short.
- **Entry-tenor design:** keep the exact Run #7 replication cohort as same-expiry QQQ puts opened at 30–60 calendar DTE (target 45). Report disjoint 30–44 and 45–60 DTE subgroups separately; any shorter/longer tenor extension must be its own labelled cohort and must not be pooled silently.
- **First-3/first-5 design:** age 0 is the entry-day mark. At each of the first 3 and first 5 completed holding sessions, only episodes that actually hit an after-cost ±0.5% / ±1% / ±2% NAV threshold enter that action comparison. Compare full close versus reduce SHORT on the same episode and same quote timestamp; signal is EOD and earliest action is the next executable session. Spot movement alone never qualifies as an option P&L trigger.
- **DTE≤7 design:** remain a separate safety-exit baseline triggered by current remaining DTE ≤7, irrespective of whether the holding-age window is 3 or 5 sessions. Report it on the same entry cohort for apples-to-apples comparison.
- **Structure/risk grid:** replay N=1–6 and both N:1 directions where exact same-expiry, contract/depth and source coverage are valid. N=1 is a vertical-spread control, not an asymmetric ratio. Apply all contract-level costs, record mark coverage, same-time P&L reconciliation, residual short exposure/tail loss, 5/10-session forward outcomes, action coverage/skipped decisions, and a separately frozen forward period if available.
- Main terminal risk whitelist remains QQQ call-credit and VXX call-credit only. This work preserves QQQ Put research and does not silently activate it, merge the two N:1 directions, alter Frozen Original Hybrid or authorize broker orders.


## 8. Interactive NAV-bar exit measurement contract

Hub exposes a draggable candidate threshold from 0.1% to 3.0% NAV (default 1.0%), plus 0.5% / 1.0% / 2.0% comparison points. At $1,000,000 NAV, these points are $5,000 / $10,000 / $20,000. A $1,000 position gain is 0.10% of a $1m NAV, not the historical $1,000-per-$100k (1%) normalized reference.

For a current-position what-if, enter **entry DTE at opening** and **current remaining calendar DTE** as two separate values, plus current Long Put Bid, Short Put Ask, quote timestamp with explicit timezone, package count, held trading sessions, commission and one-way close slippage. The opening reference prices are the existing Long Put Ask and Short Put Bid fields; if actual fills exist, use actual average fill prices instead. The calculator stays PENDING when either DTE field is blank or when current remaining DTE exceeds entry DTE; it never assumes DTE=7 or infers DTE from holding age. Historical entry cohort was 30–60 DTE (target 45). Missing marks leave P&L PENDING; marks older than 15 minutes or timestamps without timezone are not qualified as current. A fresh timestamp does not authenticate source or displayed size.

The tool compares (A) full close after costs and (B) reduce SHORT: in short-heavy, buy back N−1 shorts per package and retain one SHORT plus one LONG; in long-heavy, buy back the one SHORT and retain N LONG puts. It reconciles both actions at the same current marks by reserving future close costs for residual contracts. Same-time whole-position P&L should reconcile; differences are realized-vs-open P&L and the residual expiry-only risk—not a claim that trimming creates extra instant P&L.

DTE ≤ 7 remains the historical baseline comparator based on current remaining DTE. Holding-day 3 / 5 windows are post-entry trading-session ages; the historical comparison cohort entered at 30–60 DTE, target 45. These windows are scenario labels, never automatic triggers. The current-position bar is not a historical replay or a proof that all N / both directions were measured. It cannot declare an optimum, force an exit, change the main call-credit whitelist or authorize orders. Residual expiry loss uses intrinsic payoffs at zero/strike/above-strike breakpoints relative to the current bid/ask mark; it excludes future IV/time-value paths, intraday margin calls, early assignment, liquidity gaps and forced liquidation.
