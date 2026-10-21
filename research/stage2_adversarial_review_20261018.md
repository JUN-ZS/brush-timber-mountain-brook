# Stage 2 Adversarial Review — Ten-Year USD 100,000 Capital Preservation

**Review date:** 2026-10-18  
**Stage 1 report:** [`stage1_independent_findings.md`](../blob/main/stage1_independent_findings.md), Git blob `068a7c53bf0e0bf9f7df005365ec3ff0aa1979dc`  
**Stage 1 source snapshot SHA:** `a4e04edf7d28978615d34652299b2964afc39a14`  
**Adversarial baseline:** the material source and data blobs listed below must match Stage 1's pinned inputs.  
**Scope:** read-only audit of claims, re-computable calculations, and the proposed portfolio architecture. This is not a live securities quote, tax opinion, or investment guarantee.

## 1. Executive verdict

**Uphold the direction; do not accept the exact allocation or all Stage 1 wording as proven.**

The repo's current QQQ/option/volatility strategy evidence does not establish a reliable ten-year nominal-capital floor. A maturity-matched high-quality government security can be used to target a contractual nominal amount at maturity if sized from an executable security price and held to maturity; broad unleveraged equities can provide a growth sleeve; QQQ/VXX options should stay at zero or strictly sandboxed until accounting and empirical execution-data blockers are resolved. This broad architecture survives the adversarial review.

However, the proposed exact allocation **$60,500 STRIPS + $14,500 TIPS/T-bill reserve + $25,000 equities** is not yet a verified optimum, and the statement that it also guarantees real purchasing-power break-even is false under a total equity wipeout. The bond figures use unverified hypothetical yields rather than an executable 2036 security quote; the source mixes dated market benchmarks; a few terminal-value totals are inconsistent; and the forecast equity value is an assumption rather than a calibrated expectation.

The most important verified repository defect is the PUT overlay's opening accounting: it subtracts the full ask premium while only crediting subsequent mark-to-market differences from the initial mid, thereby charging the initial mid value twice. This means the published return, premium-drag, and CPCV results for that engine must be rerun after correcting and testing the ledger before interpreting their economic magnitude. The accounting defect is real; its exact effect on the final optimal strategy is not yet established.

## 2. Evidence classification at a glance

| Claim / issue | Stage 2 status | What was independently checked | What remains open |
|---|---|---|---|
| The rolling-floor input omits the 1999–2003 dot-com period | **VERIFIED** | `src/data/universe.json` starts 2004-01-02; the pinned market CSV starts 1999-03-10. Recomputed historical 120-month windows from the older series. | The longer series is a QQQ price field, not verified dividend-reinvested total return. |
| The current rolling-floor result's 100% non-loss rate means high future safety | **REJECTED / VERIFIED LIMITATION** | The result's two proxy series have zero months; 13,895 of 13,989 monthly window-state observations are `THIN`. When authority is absent, the code falls back to the mandatory clock; the resulting QQQ exposure has no principal floor. | Whether a newly populated, point-in-time clean proxy channel would improve outcomes requires a new, independent replay. |
| PUT overlay opening cashflow is double-counted | **VERIFIED CODE BUG** | Directly traced `src/lib/pulse/protected.ts` open, mark and return lines; toy cashflow example gives -$10.20 under current algebra vs -$0.20 buy-at-ask/sell-at-bid cashflow. | Corrected full-run P&L and CPCV metrics remain to be produced. |
| Published PUT overlay/CPCV results support use for capital preservation | **NOT SUPPORTED** | Stored result explicitly says VIX is used as an IV proxy, puts are Black–Scholes-derived, spread is estimated, and it is **not** an OPRA historical-fill replay. Stored OOS and refit results miss stated drawdown bands. | Re-run after the accounting fix, then acquire/replay actual option quotes with realistic fills. |
| V22 call-ratio family is virgin OOS | **FALSE BY ITS OWN MANIFEST** | `artifacts/oos_family/manifest.json` says `NOT_VIRGIN_BECAUSE_PRIOR_SELECTION_USED_FULL_V22_SAMPLE`; `research/evidence_v1/STRATEGY_LOCK.json` says `NOT_VIRGIN_YET`. | Raw option-chain Parquet is not present in the pinned source tree/Stage 1 snapshot; campaign P&L and tail exposure cannot be fully reproduced from the material reviewed. |
| V22 / short-heavy PUT structures are suitable to fund the floor | **BLOCKED / DO NOT DEPLOY** | No authenticated option chain and no verified historical exit path are available in the relevant contract replay. Reported short-ratio tail figures are scenario arithmetic, not event probabilities. | Obtain the missing artifacts and verify margin, liquidity, settlement, and executable bid/ask logic. |
| `run_instance.py` is executable as checked in | **VERIFIED SOURCE DEFECT** | Pinned file contains literal backslash-n characters inside a source line around line 314, which interrupts Python statements rather than starting new lines. | Run the actual pinned Python compile/test command on the BOT to record the runtime error and fix it separately. |
| The proposed bond sleeve costs exactly $60,500 and guarantees both nominal and real break-even | **PARTLY REJECTED** | The report's own yield assumptions recalculate to about $60,141 PV for $100,000 face; $60,500 grows to about $100,597 at that assumed yield; real break-even at 2.35% inflation is about $126,147. If the equity sleeve is wiped out, the nominal STRIPS floor plus the stated TIPS value is still below the real-break-even target. | Need executable maturity-matched security quotes, account/tax assumptions, exact cash reserve composition, and after-tax cashflow schedule. |
| Stage 1's overlapping historical windows imply a future success probability | **NOT VERIFIED** | 211 windows share most of their monthly price path and are not independent trials. | Need an explicitly justified uncertainty method/regime set; historical-window frequency alone is not a calibrated future probability. |

## 3. Independent recomputation: QQQ ten-year price-window evidence

### Data identity and method

The input is the Stage 1 pinned blob `artifacts/pulse_v2/data_market_data.csv`, Git blob SHA `048f335b359848e1c1f261a488dd7366668806d1`. It contains 6,915 usable daily QQQ price-field rows from 1999-03-10 through 2026-09-03. Monthly observations use the last available QQQ value in each calendar month. For each available start month with a 120-month endpoint:

- Lump sum: terminal QQQ value divided by starting QQQ value.
- Mandatory 120-month clock purchases: invest 1/120 of the initial cash at each month (k=0,ldots,119), then mark all units at month 120.
- A losing window has terminal multiple below 1. This counts each overlapping start as a historical observation; it does not claim independent samples.

### Recomputed results

| Metric | Lump sum | 120-month clock purchases |
|---|---:|---:|
| Number of overlapping ten-year windows | 211 | 211 |
| Historical windows ending below initial capital | 23 | 4 |
| Historical non-loss frequency | 89.10% | 98.10% |
| Worst terminal value per $100,000 | $43,143 | $77,035 |
| Worst window | 2000-02-29 → 2010-02-26 | 1999-03-31 → 2009-03-31 |

The lump-sum worst window's daily price-field maximum drawdown is approximately **-82.96%**, from the 2000-03-27 peak to the 2002-10-09 trough. This corroborates the report's claim that beginning in 2004 hides the most important early tech-bubble experience.

**Limits:** the CSV does not expose an identified dividend-reinvested total-return field. These calculations are therefore price-field simulations. The 211 windows are highly overlapping, not 211 independent observations; 89.10% / 98.10% are historical window frequencies and cannot be presented as the future ten-year probability of preserving capital. The DCA result describes a cash-deployment schedule, not a capital guarantee.

### Rolling-floor controller finding

Pinned source `research/rolling_10y_floor/rolling_floor_result.json` (blob `19e1b512c1677d000de44ee5cf5674f0e476a6eb`) reports `version=rolling-floor.v1`, `evidenceClass=RESEARCH_ONLY`, 153 windows, 100% non-loss, and a worst coupled terminal multiple near 1.98008. It reports QQQ with 273 monthly points, but proxy channels `NASDAQ100` and `NASDAQCOM` with `months=0`.

Counting the stored `divergenceStateByDate` arrays gives 13,989 state steps: 13,895 `THIN` and 94 `CONVERGENT` (99.33% THIN). In `src/lib/pulse/rolling-floor.ts`, missing / insufficient robust targets fall back to the calendar clock, and `replayOne` forces at least the mandatory monthly addition. Thus the favourable 153-window score mainly validates the clock-based deployment path on the post-2004 sample; it does not prove the proxy-based controller has authority or that the money is protected from a late-horizon QQQ crash.

**Decision:** keep this controller out of any principal-guarantee label until the 1999+ series, dividend/total-return definition, proxy channels, and late-horizon risk-control behavior have been independently tested.

## 4. PUT overlay: exact ledger fault and what it means

Pinned source `src/lib/pulse/protected.ts`, blob `88eca992eef600541dff1e54f51ce30feadd64b0`:

- Lines 299–301 adds only daily price changes, `contracts × (mid - lastMark)`, then replaces `lastMark`.
- Lines 328–330 obtains `pay = mid × (1 + spread)`, records the full `contracts × pay` as `premium`, and opens the lot with `lastMark = mid`.
- Line 338 subtracts the full `premium` from the daily return: `(putPnl - premium) / equity`.
- Roll/close lines 309–315 book the change from the last mid to the assumed bid hair-cut. They do not reverse the missing opening-mid asset charge.

For one contract, entry mid $10, estimated spread 10%, exit mid $12 and exit bid $10.80:

[
P_{	ext{cash flow}} = 10.80 - 11.00 = -0.20
]

But the implemented calculation aggregates:

[
(12-10) + (10.80-12) - 11.00 = -10.20
]

The difference is exactly (-$10): the opening mid was charged a second time. Expiry handling also requires explicit validation so intrinsic settlement is credited consistently rather than relying on disappearance of a marked lot.

### Corrective accounting specification

Make opening cash and asset recognition explicit. Either (A) on open add the purchased option's mid mark to the mark-to-market asset ledger and subtract the full ask cash outlay, or (B) use a cashflow-realized ledger with entry ask, each holding's mark value on each day, and exit bid/intrinsic settlement. Do not mix those accounting representations. For the mark-to-market path, opening-day effect should be only the estimated spread / execution haircut—not the full option mid. A unit test must verify:

1. Buy at entry mid $10 / ask $11.
2. Mark at $12.
3. Close at bid $10.80.
4. Total strategy P&L equals -$0.20 before commission; add commissions separately.
5. A zero-value expiry yields the full correct loss but not more than the original cash paid; a profitable intrinsic expiry credits correct settlement.
6. Multiple lots / add / roll / partial close preserve NAV and realised/unrealised P&L without duplication.

### Impact on interpretation of stored backtests

Stored `artifacts/backtest-result.json` (blob `4c737eb299b4226d8e3d1265e606b8699a95a0f4`) has a full-sample selected-variant CAGR of about 7.02%, max drawdown -53.38%, QQQ buy-and-hold CAGR about 15.12%, and QQQ max drawdown -53.40%. It states the put path is derived from Black–Scholes using VIX as IV, with an estimated 10% spread, and is **not** an OPRA historical-option-fill backtest. `research/refit_cpcv.json` (blob `3e623fcf32f3a18ce1ec4162f92d4c3443974e38`) reports refit test CAGR mean 7.84%, minimum -10.03%, worst test MaxDD -55.81%, and 0 joint-band passes across 9 tests. `research/cost_oos_cpcv_survival.json` (blob `c12f0b79237341f99a3e39f347f6b8318e8904df`) reports -4.30% CAGR / -74.95% MaxDD in its 2x *extra-premium-drag* sensitivity.

These stored results remain valid descriptions of the old implementation's calculation, not estimates of a correct put overlay's true performance. The accounting fix may materially change them. The source's `premiumDrag` is computed from gross premium sum annualised by days, and that metric is also separately penalised in validation scoring; therefore it should be labelled as gross premium expenditure/regularisation, not casually treated as a proven annual economic loss rate. Preserve the old result, rerun under a new version, and compare before-and-after under the same frozen grid. Do not re-search OOS after seeing corrected OOS outcomes.

## 5. V22 / strategy-instance adversarial findings

### V22 family

`artifacts/oos_family/manifest.json` (blob `4f146ef9bcf65e19f5ca9e421f4028fb806e93f5`) declares `NOT_VIRGIN_BECAUSE_PRIOR_SELECTION_USED_FULL_V22_SAMPLE`; `research/evidence_v1/STRATEGY_LOCK.json` (blob `1ba879f24e367570c3a4e3b04bca607450dc2b8d`) declares `NOT_VIRGIN_YET`. These self-reported locks invalidate a claim of untouched virgin OOS for the already-selected family, even if certain campaign rows are positive. Stage 1 cites the raw `QQQ_options.parquet` and `QQQ_underlying.parquet` as absent; they are not present in the available source tree inventory for the pinned snapshot, so net-of-cost contract P&L and jump/assignment exposure remain **BLOCKED**.

### Strategy instance Python source

At the pinned Stage 1 source, `research/strategy_instance_v1/run_instance.py` blob `1757feda167a360fa63197d11d73835ce8f73526`, source line around 314 contains literal characters `\\n` between two Python statements. This is not a newline in the checked-in source; it is a syntax defect. The Stage 1 statement is therefore a source-level finding, not yet an independently recorded BOT compile-test result. Fix in a dedicated PR and require `python3 -m py_compile research/strategy_instance_v1/run_instance.py` plus targeted tests before treating the module as executable.

### SharedContractEngine / QQQ ratios / VXX

The Stage 1 snapshot reports zero verified exit episodes, zero price windows and no paired coverage for the reviewed v4.4 contract replay. Without verified episodes, the N:1 result is blocked from historical performance claims. The short-heavy tail values ($65,890–$339,907 per unit) are scenario arithmetic under the specified contractual legs—not a calibrated probability. Long-heavy N:1's 3/62 wins (4.84%) is a small, possibly regime-skewed sample, not enough to generalise win probability. No variant should be admitted to a live risk budget solely because its synthetic contract/golden tests pass.

## 6. Recalculate the proposed Treasury / TIPS / equity numbers

### Benchmark-yield issue

The Stage 1 report uses DGS10 = 5.21%, T10YIE = 2.35% and real yield approximately 2.86% as an October 2026 pricing basis. The available FRED daily benchmark pages show:
- DGS10 was 5.21% on 2026-10-13 but 5.10% on 2026-10-15: https://fred.stlouisfed.org/data/DGS10
- T10YIE was 2.32% on 2026-10-15 and 2.35% on 2026-10-16: https://fred.stlouisfed.org/data/T10YIE
- DFII10 was 2.78% on 2026-10-15: https://fred.stlouisfed.org/data/DFII10

These are constant-maturity / breakeven benchmark observations, not an executable bid/ask quote for one specific 2036 STRIPS or TIPS security. The report's 5.15% STRIPS net yield and $355 of transaction/tax buffers are assumptions; the exact CUSIP/security price, settlement, accrued amount, commission, tax status, and after-tax cashflow are not provided. A hard-floor dollar amount cannot be finalised from DGS10 alone.

### Arithmetic check under Stage 1's own assumptions

Using, solely for arithmetic verification, a 5.15% nominal yield compounded semi-annually for 20 periods:

| Calculation | Recomputed value | Stage 1 presentation / issue |
|---|---:|---|
| PV required for $100,000 face at Year 10 | $60,140.84 | Report says ~$60,145; small rounding discrepancy. Not an executable quote. |
| Year-10 value if all $60,500 buys at the assumed yield | $100,597.20 | Not simultaneously the same as assuming a $100,000 par redemption plus a separate $355 cash reserve. |
| 2.35% ten-year cumulative inflation factor | 1.261474 | Requires ~$126,147 nominal for $100,000 in today's purchasing power. |
| $14,500 if all earns the assumed 2.86% real yield plus 2.35% inflation for ten years | ~$24,250 nominal / ~$19,224 in start-year real dollars | Report says ~$24,230 / ~$19,207; close in arithmetic, but it does not specify how much is TIPS versus short bills. |
| $25,000 at a stipulated 8.8% annual compound rate | ~$58,107 | The report's ~$58,040 differs slightly and, more importantly, 8.8% is a scenario assumption, not a validated forecast. |

The Stage 1 component table reports A1 maturity $100,590, A2 $24,230 and equity $58,040; those components sum to **$182,860**, not its stated $182,270. Its -83% equity scenario components ($100,590 + $24,230 + $4,250) sum to **$129,070**, not $128,480. The lower totals are obtained by using exactly $100,000 for A1, not $100,590. Fix the inconsistency before comparing alternative allocations.

### Nominal floor is not a real floor

At 2.35% annual inflation, `100,000 × 1.0235^10 ≈ $126,147`. With A1 paying $100,000 nominal at maturity and the Stage 1 TIPS sleeve valued at $24,230 nominal, nominal assets excluding equity total $124,230, which is about $98,496 in today's purchasing power. Thus if the equity sleeve fell to zero, the described allocation would miss real break-even. Its -83% equity scenario can leave positive equity value, but does not prove protection against a -100% terminal equity loss or a harsher inflation path.

If real purchasing power is a strict requirement, price and compare (i) a nominal STRIPS floor plus separately budgeted inflation reserve, (ii) a maturity-matched TIPS portfolio sized from its actual security price/cashflow schedule, and (iii) a blended nominal/real floor. Keep a separate after-tax scenario for the investor's actual tax residence/account type; the current report does not have enough information to resolve OID/phantom-income treatment. The IRS discusses OID and zero-coupon security tax treatment here: https://www.irs.gov/publications/p1212.

## 7. Reconciled allocation direction and no-trade rules

### What survives

1. **If the binding requirement is nominal $100,000 at Year 10:** calculate the face amount of an appropriately maturity-matched, high-quality government security using executable bid/ask price and exact cashflows, costs and tax reserve. Keep it separate from risk assets, assume hold-to-maturity, and disclose sovereign-credit and early-sale mark-to-market risks. Do not borrow against or use that sleeve to replenish option losses.
2. **If the binding requirement is real $100,000 in today's purchasing power:** the nominal face floor alone does not satisfy it. Obtain an actual maturity-matched TIPS quote/cashflow schedule and size a real principal floor, or model a transparently probabilistic real target. Do not call a nominal STRIPS plus small equity reserve a real guarantee.
3. **Growth sleeve:** compare diversified unleveraged equities to S&P 500/QQQ blends only after defining the risk target. Do not treat 8.8% CAGR as a verified base case; show conservative/base/upside assumptions and disclose the possibility that the entire equity sleeve is lost.
4. **QQQ/VXX/option sleeve:** default to zero deployment until (a) accounting tests pass, (b) actual data coverage / quote-source provenance is sufficient, (c) positions pass a defined margin + gap + early-exit stress budget, and (d) a new, pre-registered out-of-sample / walk-forward result survives costs. Given current source evidence, the allowable live strategy position is **BLOCK / no-trade**, not because options are universally unusable, but because this repo hasn't established its needed evidence.
5. **Monitoring:** update current NAV, debt price/yield, inflation assumption, exact security cashflows, realised tax/cash outflows, option chain marks, VX M1/M2 freshness and total stress loss separately. Missing quote, stale mark, failed ledger invariant, or unverified margin must reduce permitted risk budget to zero, not substitute an estimate as if observed.

### Dynamic formulas for a later implementation

Let (F_{10}) be the actual cost of maturity-matched nominal face amount sufficient to redeem $100,000 after explicit costs/taxes; (B) be an explicitly priced tax/liquidity buffer; (NAV_t) be current marked portfolio value.

[
R_t = \max(0, NAV_t - F_{10} - B)
]

(R_t) is the residual amount potentially available for growth/risk assets, not a promise that a residual risk allocation can restore a shortfall. For a real floor, replace (F_{10}) with the executable cost of the required TIPS-based real cashflow target, not the same nominal formula.

For an option candidate (j), define (L_{j,s}) as loss in stress scenario (s), (L_j^{max}=\max_s L_{j,s}), and (G_t) as approved aggregate stress-loss budget after all current positions. New contracts must be zero unless quotes are fresh and verified, margin and assignment mechanics are known, and:

[
\sum_j L_{j,s}^{\text{post trade}} \le G_t\quad\text{for every approved scenario }s
]

When any required quote/source/ledger or margin value is missing, set the permitted new contracts to zero. Do not equate option premium received, QQQ down probability, or historical window frequency with net portfolio expectancy.

## 8. Six-dimension reconciliation

| Dimension | Stage 1 position | Stage 2 adversarial result |
|---|---|---|
| Ten-year objective | Nominal preserve at least $100k; also explores real break-even | Correct to separate nominal and real. Real threshold at 2.35% is ~$126,147. Exact real guarantee not shown. |
| Capital-floor mechanism | STRIPS + TIPS reserve | Direction upheld; exact $60.5k/$14.5k mix unpriced and contains arithmetic/component mismatch. |
| Equity allocation | $25k SPY/QQQ blended, assumed 8.8% CAGR | Diversified unleveraged exposure reasonable to test; return is scenario, not evidence. Equity can be wiped out; then real break-even fails. |
| QQQ / VXX / options | Existing strategies rejected for sole capital-preservation role | Upheld. PUT accounting bug changes historical results; lack of verified OPRA fills and verified exits is still decisive. |
| Dynamic sizing / no-trade | Capital-floor ratchet + risk budgets | Upheld in principle; formulas must be based on executable security costs and verified stress losses, not benchmark yields or empty proxy data. |
| Probability credibility | Historical windows + repo backtests | Reject point-estimate interpretation. Overlapping windows, price-only data and selected/non-virgin samples cannot establish future ten-year odds. |

## 9. Best next reproducible experiment (highest value of information)

Run a two-part controlled experiment, preserving the current outputs:

**Experiment A — correct the protected PUT accounting**
- Create a new version/branch; do not overwrite `artifacts/backtest-result.json` from the old engine.
- Implement explicit opening option asset recognition or cashflow accounting. Add the entry $10 / ask $11 / exit mid $12 / bid $10.80 test; require -$0.20 net P&L before commission, plus expiry / roll / multiple-lot lifecycle tests.
- On the same frozen grid, rerun `scripts/run-backtest.ts`, `scripts/run-refit-cpcv.ts`, and the 2x-cost sensitivity. Compare old vs corrected full/OOS/CPCV under identical data and parameters; do not tune on OOS results.
- Report exactly which published conclusions change and retain non-OPRA data disclaimers.

**Experiment B — exact-date decade floor**
- Retrieve verifiable, licensed or official market data for the same maturity-matched 2036 Treasury STRIPS and 2036 TIPS that could actually be bought by the investor; record bid/ask, settlement, face value, all dated cashflows, fees and tax assumptions.
- Compare nominal STRIPS floor, TIPS real floor and a blend under the same ten-year date and tax scenario. Independently recalculate terminal nominal and real dollars and test an equity terminal value of $0.
- Keep the 1999–2026 QQQ price-window replay as a separate benchmark, not a substitute for actual bond valuation or total-return data.

The accounting fix is the more immediate software experiment because it is completely reproducible from current repo code and can change the apparent value of the main option overlay. The exact Treasury/TIPS execution-price check is required before the proposed allocation can be called executable or optimal.

## 10. Reproducibility

Run the standard-library verifier from the repository root:

```bash
python3 scripts/stage2_recompute_stage1_claims.py > stage2_recompute_results.json
```

It is intended to fail closed when any key Stage 1 source blob changes or an expected input is missing. It prints the input blob manifest and recalculated historical windows, source accounting markers, recorded engine/CPCV results, and capital arithmetic. This verifier is not itself a backtest of corrected options and does not produce a future success probability.

## References

- Stage 1 report: `stage1_independent_findings.md`
- Rolling floor source: `src/lib/pulse/rolling-floor.ts` (Stage 1 blob `131c7ea3022af31a3c3e46ae0e9de76bec7fa084`)
- Rolling floor result: `research/rolling_10y_floor/rolling_floor_result.json` (blob `19e1b512c1677d000de44ee5cf5674f0e476a6eb`)
- PUT accounting source: `src/lib/pulse/protected.ts` (blob `88eca992eef600541dff1e54f51ce30feadd64b0`)
- Protected stored result: `artifacts/backtest-result.json` (blob `4c737eb299b4226d8e3d1265e606b8699a95a0f4`)
- Refit CPCV result: `research/refit_cpcv.json` (blob `3e623fcf32f3a18ce1ec4162f92d4c3443974e38`)
- Cost sensitivity: `research/cost_oos_cpcv_survival.json` (blob `c12f0b79237341f99a3e39f347f6b8318e8904df`)
- V22 family manifest: `artifacts/oos_family/manifest.json` (blob `4f146ef9bcf65e19f5ca9e421f4028fb806e93f5`)
- Strategy lock: `research/evidence_v1/STRATEGY_LOCK.json` (blob `1ba879f24e367570c3a4e3b04bca607450dc2b8d`)
- Input QQQ price field: `artifacts/pulse_v2/data_market_data.csv` (blob `048f335b359848e1c1f261a488dd7366668806d1`)
- Current-rate benchmark sources: FRED DGS10 / T10YIE / DFII10 URLs above.
