# QQQ LONG PUT × SPY SHORT PUT paired replay

## Objective

Estimate the historical combined-package win rate for configurable quantities of long QQQ puts and short SPY puts. The default display ratio is **4 QQQ long puts : 5 SPY short puts**. The primary question is whether the long-put convexity offsets the short-put premium income and tail liability under the same market path—not whether QQQ or SPY happened to rise or fall.

## Contract pairing is an explicit sensitivity

The report compares three independent signal-day contract-selection rules:

1. **Premium matched (default UI):** select the QQQ long put closest to target absolute delta, then select a SPY short put whose signal-day bid is closest to the QQQ signal-day ask. This matches one-contract premium approximately, not aggregate package cash flow; at a 4:5 ratio the package can still have a net opening credit or debit.
2. **Delta matched:** choose the put on each ETF closest to target absolute delta.
3. **Percent-OTM matched:** choose the put on each ETF closest to the same percentage below its own spot price.

Default selection target is 30 calendar days to expiry ±10 days, absolute delta 0.25, and 5% out of the money. These are research defaults and can be overridden by command-line inputs. The contract is selected on the signal-day end-of-day chain and kept fixed for the replay; this is not a strategy that reselects an option each day.

## Timing and quote-side accounting

- Historical quotes are signal data; entry is the **next common SPY/QQQ underlying session's** EOD quote, avoiding same-close look-ahead.
- Open QQQ long put at ask; open SPY short put at bid.
- Close QQQ long put at bid; buy back SPY short put at ask, on the same later common session.
- Holding horizons: 1, 3, 5, 10, and 20 common trading sessions.
- Each leg uses multiplier 100. Commissions and slippage are separate scenarios. Quote-side touch is a modeled fill assumption, not an observed execution.
- Invalid/crossed quotes and absent live marks are **not** forward-filled or converted to zero. An observed zero bid for a still-live QQQ long put is retained as a zero bid mark, not dropped from the sample. If a fixed contract has expired before the requested horizon, its expiration-date intrinsic value is used; if that date's underlying close is missing, the pair is excluded for that horizon.

## Reported results

Every selected mode / holding period / friction / long-quantity / short-quantity combination reports:
- combined net-P&L wins, losses, breakeven count, win rate and paired sample size;
- mean/median net P&L, P05/P01, mean of the worst approximately 5%, historical worst observed exit P&L, and profit factor;
- regime splits for both underlyings falling (including which fell more), both rising/flat, and mixed-direction outcomes;
- opening net cash flow and premium mismatch, to make the financing identity visible;
- hypothetical expiry stress if both underlyings went to zero, separated from the observed holding-period worst outcome;
- min/median/max win rate across holding-horizon-spaced entry-date offset cohorts, exposing overlapping-window timing sensitivity.

## Evidence and limitations

- Inputs come from the public data-v1 release: https://github.com/lambdaclass/options_portfolio_backtester/releases/tag/data-v1. Their SHA-256 hashes are embedded in the script and verified by the workflow before replay. Do not commit or upload the raw parquet chains to this repository.
- These are end-of-day historical option quotes; they are not OPRA tick-level fills, and quote sizes are unavailable in this particular input contract. The source notice says original provenance was not documented and the dataset is supplied as-is for research reproduction; matching hashes establish file identity, not quote correctness or execution certainty. Opening/closing at quote touch is an execution model.
- Short SPY puts can create large tail liabilities and assignment/buying-power demands. The report's historical worst observed exit is not maximum possible loss. The both-underlyings-to-zero figure is a stylized terminal stress and does not represent actual joint probability.
- Daily-start holding windows overlap. Offset cohorts are sensitivity diagnostics, not independent-trial confidence bounds and not forward probabilities.
- Expiration intrinsic values use the underlying close on listed expiration date; this approximates terminal payoff but does not model American-style early assignment/exercise. No broker margin, intraday gap execution, portfolio concurrency, taxes, or capital-capacity proof is inferred. A high win rate alone does not establish positive expectancy, robust return, or acceptable tail risk.
- Missing data and insufficient paired samples are reported as missing/blocked rather than fabricated.

## Reproduction

The GitHub Actions workflow runs on the self-hosted grokbot-box-linux-x64 runner, downloads only the four hash-pinned EOD chain/underlying files, runs the unit tests, creates aggregate-only JSON and interactive HTML, then commits those generated reports to the research branch. Quote-level input files stay outside the repository and no Actions artifact is uploaded.
