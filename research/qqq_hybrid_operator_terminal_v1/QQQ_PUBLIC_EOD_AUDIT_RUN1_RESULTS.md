# QQQ Public EOD Option Chain Audit — Run #1

**Result:** `SAMPLE_DATES_HAVE_QQQ_CHAIN_ROWS`  
**Workflow:** [Windows self-hosted Run #1](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38002570136)  
**Research status:** source availability and quote quality verified for two dates; **not** a strategy backtest and **not** an executable fill proof.

## 1. File-integrity gate

All three downloaded Parquet files matched expected sizes and Git blob SHAs before they were queried.

| File | Expected / downloaded bytes | Git blob SHA | Result |
|---|---:|---|---|
| `qqq/options_2020.parquet` | 59,412,637 | `9d7abe1144c55e0091d28eca61deec4ac72393a5` | `DOWNLOADED_HASH_VERIFIED` |
| `qqq/options_2024.parquet` | 82,434,832 | `40c1c2fd986da9b5bcf363cd44c9d5ac3eecc8c3` | `DOWNLOADED_HASH_VERIFIED` |
| `qqq/underlying_prices.parquet` | 332,454 | `f3a892bc4c88c692900b5c0071322c6db408996a` | `DOWNLOADED_HASH_VERIFIED` |

The script calculated Git blob hashes over downloaded bytes; this is more than checking a URL or filename. The data files themselves were stored in the system temp directory and were not committed to this repo.

## 2. Selected date results

| Date | Context | Option rows | Calls | Puts | Positive, non-crossed two-sided rows | Valid two-sided % | Calls matching 30–60 DTE / absolute Delta 0.03–0.10 |
|---|---|---:|---:|---:|---:|---:|---:|
| 2020-03-16 | COVID shock | 5,760 | 2,880 | 2,880 | 5,170 | 89.76% | 47 |
| 2024-08-05 | volatility shock | 7,704 | 3,852 | 3,852 | 7,236 | 93.93% | 25 |

Underlying snapshot rows recovered from the companion file:

| Date | Close | Adjusted close | Volume | Split coefficient |
|---|---:|---:|---:|---:|
| 2020-03-16 | $169.30 | $163.355096 | 92,054,386 | 1.0 |
| 2024-08-05 | $435.37 | $432.455928 | 87,483,452 | 1.0 |

The mirror README describes the option data as a **4:00 PM US Eastern snapshot**. It is not an intraday 15:45 snapshot and does not prove that a hypothetical strategy could fill at the displayed Bid or Ask at its actual decision timestamp.

## 3. Candidate quote samples and the liquidity warning

These are calls selected only as a *diagnostic slice*: calendar DTE 30–60, absolute Delta 0.03–0.10, positive bid and ask, and Bid <= Ask. Ranking is by proximity to absolute Delta 0.06, then 45 DTE, then tighter spread. This is not an optimized rule and is not a recommended trade list.

| Snapshot date | Contract | DTE | Bid | Ask | Bid/Ask spread | Spread / midpoint | Delta | Open interest | Volume |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2020-03-16 | QQQ200515C00232000 | 60 | $0.49 | $1.04 | $0.55 | 71.90% | 0.06137 | 2,086 | 5 |
| 2020-03-16 | QQQ200424C00221000 | 39 | $0.24 | $0.98 | $0.74 | 121.31% | 0.05801 | 0 | 0 |
| 2020-03-16 | QQQ200417C00217000 | 32 | $0.47 | $0.95 | $0.48 | 67.61% | 0.06342 | 9,719 | 345 |
| 2024-08-05 | QQQ240930C00510000 | 56 | $0.95 | $1.11 | $0.16 | 15.53% | 0.06008 | 3,016 | 60 |
| 2024-08-05 | QQQ240920C00504780 | 46 | $1.01 | $1.09 | $0.08 | 7.62% | 0.06019 | 2,723 | 287 |
| 2024-08-05 | QQQ240920C00505000 | 46 | $0.99 | $1.07 | $0.08 | 7.77% | 0.05961 | 13,251 | 2,113 |

**Interpretation:** the dataset contains useful quote and liquidity fields, but “a valid two-sided quote exists” is not the same as “this option is liquid or could be filled at the displayed mark.” In this small sample, the COVID-day candidates have particularly wide spreads, including examples with zero volume and zero open interest. The APP must keep data availability, quote validity, liquidity, and execution assumptions as distinct measures.

## 4. What this establishes — and what it does not

**Established by Run #1:** the selected public mirror files downloaded; their byte counts and Git blob SHAs matched; the requested two QQQ dates returned thousands of option rows with Bid/Ask/IV/Greeks and a measurable percentage of valid non-crossed quotes.

**Not established:** exchange-authoritative completeness, official NBBO provenance for each quote, intraday decision-time prices, executable fills, commissions/slippage, or performance of the QQQ/VXX Hybrid. The source contains QQQ options, not VXX options, and is a preservation mirror of a previously published dataset.

## 5. Pre-registered next test

Before proposing any policy integration, use this sample to compare the QQQ far-call model against observed EOD quotes by exact date / expiry / strike, and report:

1. quote availability at the model's candidate strike;
2. model mark against Bid / Ask / midpoint, with distance expressed in dollars and spread units;
3. the change in candidate/credit/risk sizing if actual Bid/Ask replaces the derived mark;
4. sensitivity under adverse fill/slippage and commission assumptions.

Do **not** extrapolate results from these two event dates to full-period strategy performance. The public EOD sample is a calibration diagnostic only.
