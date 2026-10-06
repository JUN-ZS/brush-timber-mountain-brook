# REAL M1/M2 P&L SENSITIVITY — FORENSIC RESULT

Status: **CONTROLLED_DERIVED_PNL_SENSITIVITY**

This experiment changes exactly one input family: the term slope used by the recovered Original-Hybrid source-logic baseline.

## Window

- 2018-03-01 → 2022-04-08
- 1,036 complete spot/term overlap rows used by the P&L simulation
- External observed M1/M2 dataset: 1,540 rows, 2016-03-01 → 2022-04-08
- Full 2018-2026 REAL M1/M2 replay remains blocked because observed M1/M2 coverage ends 2022-04-08.

## A/B contract

Same:
- QQQ / VXX / VIX spot fixture
- QQQ core = 42%
- QQQ call-credit sleeve base risk = 0.8%
- VXX short = 18%
- VXX call-credit risk = 2%
- Black-Scholes/VIX-derived option pricing
- spread/friction model
- entry/exit mechanics
- shock logic
- no parameter search

Only term slope changes:

`PROXY = 0.10 * tanh((VIX_MA20 - VIX) / 6)`

`REAL = (M2 - M1) / M1`

## Results

| Metric | PROXY | REAL observed M1/M2 | REAL − PROXY |
|---|---:|---:|---:|
| CAGR | 13.9162% | 11.0502% | **-2.8660 pp** |
| MaxDD | -15.8821% | -20.0260% | **-4.1439 pp** |
| Final NAV | 170,698.30 | 153,749.55 | **-16,948.76 (-9.93%)** |
| Opens | 176 | 176 | 0 |
| Closes | 173 | 173 | 0 |

## Source-engine reproducibility check

The frozen source-logic baseline `research/qqq_hybrid_dynamic_deployment_v1_1.py`, run from the earlier GitHub Actions artifact, gives on the same 2018-03-01 → 2022-04-08 slice:

- CAGR: **13.9092%**
- MaxDD: **-15.8821%**
- Final NAV: **170,698.31**

The controlled PROXY lane gives:

- CAGR: **13.9162%**
- MaxDD: **-15.8821%**
- Final NAV: **170,698.30**

This validates that the sensitivity harness is effectively reproducing the source-logic baseline before changing the term input.

## Forensic term mismatch

Over the 1,036-row sensitivity window:

- Term-sign agreement: **67.95%**
- State mismatch: **243 / 1,036 = 23.46%**
- Action mismatch: **267 / 1,036 = 25.77%**
- Mean proxy-vs-real term error: **-5.03 percentage points**
- Mean absolute term error: **6.88 percentage points**

The largest divergence is concentrated in specific regimes rather than random noise. For example:

- 2020-09-04: REAL TS +21.51%, PROXY TS -8.04%
- 2020-09-02: REAL TS +22.15%, PROXY TS -5.19%
- 2020-08-31: REAL TS +18.95%, PROXY TS -5.36%

The recovered proxy therefore sometimes classified a materially positive real term structure as negative.

## Interpretation

The result is strong evidence that the archived VIX/MA20 term proxy is **not economically interchangeable** with observed M1/M2.

Within this derived source-logic P&L framework, replacing the proxy with observed M1/M2 reduced CAGR by about **2.87 percentage points** and worsened MaxDD by about **4.14 percentage points** over this overlap window.

This does **not** mean the historical 12.7049% CAGR is now disproven or exactly changed to 11.0502%. The 12.7049% figure belongs to a different full-period reconstruction reference and has not been fully replayed with validated contract-level VX futures and historical option executions.

The correct conclusion is narrower:

> **The old M1/M2 proxy can materially distort the term-dependent decision path and P&L. It cannot be used as a faithful historical substitute for real VX M1/M2.**

## Next gate

The next research gate should be **full-period REAL VX replay** only after obtaining a contract-level validated M1/M2 history covering the complete 2018-03-01 → 2026-09-04 window.

Until then:
- do not retune parameters to recover 12.5%;
- do not merge the REAL lane into production policy;
- keep the proxy explicitly classified as DERIVED/UNVALIDATED.
