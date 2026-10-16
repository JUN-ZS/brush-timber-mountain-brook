# QQQ Hybrid Measurement Scorecard — Replay #148 / Audit #177

**Disposition:** Accuracy for trade-performance use = **BLOCKED**; Generality = **NOT DEMONSTRATED**; FAR CALL integration into the Frozen Original Hybrid = **FAILS CURRENT BASE SCREEN**. Engineering integration = **PASS on the tested head**. This scorecard is a measured snapshot, not a strategy approval.

## Exact evidence identity

- App/research code head: `57fd41b2d47c8721b445a6f704610e0e524a890e` — [commit](https://github.com/JUN-ZS/brush-timber-mountain-brook/commit/57fd41b2d47c8721b445a6f704610e0e524a890e).
- [Windows Operator Terminal Run #260](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38450162103) — SUCCESS.
- [Grok Bot Linux Run #104](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38450162086) — SUCCESS.
- [Listed-Contract Replay Run #148](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38450162087) — SUCCESS.
- [Public EOD Audit Run #177](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38450162090) — SUCCESS.

The listed replay and full-history audit steps completed on this head. The workflows verify the pinned source files and regression contracts; workflow success alone does not authenticate quote sources or establish executable fills. This report transcribes the measured summary from those completed Actions logs. A new commit containing this scorecard has not yet been tested at the time this file is authored; the links above are for the stated code head only.

## The three axes

| Axis | Status | Measured evidence | Decision |
|---|---|---|---|
| **Accuracy — app arithmetic and safety contracts** | **PASS for tested cases** | Windows Run #260: 29 engine test groups, 9 Position Register groups, 11 Hub Option Pack groups; Option Chain Lab, AI handoff, quote quality, partial-risk KPI, paper observation journal, lockbox, syntax and static boundary checks passed. Grok Run #104 also passed terminal and replay regressions. | This proves the tested implementation behaves as specified for those cases, not that any external data source is authenticated. |
| **Accuracy — closed-trade cash-flow ledger** | **PASS for this diagnostic ledger** | Replay Run #148 independently rechecked 1,688 closed-trade rows: 1,688 pass, 0 fail, 0 blocked; maximum absolute reconciliation error USD 0.00 against the USD 0.01 tolerance. | The cash-flow identity reconciles. It does not repair missing marks or convert EOD quote sides into fills. |
| **Accuracy — historical source completeness** | **BLOCKED for full-window performance** | 1,971 expected sessions; 1,960 raw underlying-price dates (99.44%); 1,956 option-chain dates (99.24%); 1,946 raw-spot target pairs (98.73%). The available QQQ source ends **2025-12-15** although the requested period ends 2025-12-31, leaving 11 expected terminal sessions uncovered. | Earlier-period quote diagnostics remain useful; terminal NAV and full-window portfolio performance are incomplete. Missing quotes are not zero-filled or forward-filled. |
| **Accuracy — option pricing / execution realism** | **BLOCKED for trade replay** | The historical spot-basis diagnostic measured the repository spot input at median **−2.72% vs raw nominal close**; short/wing target selections differ on **96.61% / 95.84%** of matched dates under raw-vs-adjusted target geometry. The VIX-derived proxy credit exceeds the observed EOD short-Bid-minus-wing-Ask reference by median **USD 0.181/share** (median absolute gap about USD 0.196). Modeled half-spread haircuts are narrower than observed on **30.0% of short legs** and **57.2% of wings**, rising to **81.5% / 100%** when VIX is at least 35 (54 matched observations). | These are material pricing/selection gaps. EOD snapshots are not verified fills at the model's decision time; do not fix them by tuning one universal haircut. |
| **Generality** | **NOT DEMONSTRATED** | The 2018–2025 sample has been repeatedly inspected and is development evidence, not an untouched final holdout. Current source ends early; regime/rolling final-OOS evidence is not accepted. The prospective quote journal and exact-contract/time-comparison tests pass, but this Actions run contains no demonstrated real prospective fill dataset. | No generalization or statistical edge claim. Use prospective, timestamped records or a genuinely reserved dataset; do not reuse the reviewed sample as a virgin holdout. |
| **Integration — FAR CALL vs current no-call screen** | **FAILS CURRENT BASE SCREEN** | For the source max-loss budget of 0.8% NAV, zero extra slippage and zero commission: 106 spreads opened, 105 closed, closed-trade net P&L **−USD 5,646**, 1 position open/unresolved at period end, and 24 missing position-mark sessions. On 1,947 matched NAV dates, the last overlay-minus-control difference is **−USD 5,552**; 24 dates are unmatched and only 32/1,947 matched marks are positive. All 16 budget/cost arms have negative closed-trade net P&L. | Keep FAR CALL research-only. This control is a 42% QQQ total-return proxy plus static 58% cash, **not** the full Frozen Original Hybrid. The matched marks are not CAGR, MaxDD, Sharpe, ES95, or full portfolio-return evidence. |
| **Engineering integration** | **PASS on the tested code head** | Operator Terminal #260, Grok Bot #104, Listed-Contract Replay #148 and Public EOD Audit #177 succeeded on the same head. The New York market-date fix and explicit timestamp/freshness regressions passed. | The tested modules integrate; it does not imply that the FAR CALL strategy integrates economically or is approved for live sizing. |

## Cost sensitivity — source max-loss budget

Independent replay arms; values are closed-trade net P&L in USD. Extra slippage is a hypothetical amount **per leg**, not measured execution cost.

| Extra slippage / leg | Commission / contract / side | Opened | Closed | Closed-trade net P&L | End position unresolved/open |
|---:|---:|---:|---:|---:|---:|
| $0.000 | $0.00 | 106 | 105 | **−$5,646.00** | 1 |
| $0.025 | $0.00 | 107 | 106 | **−$6,730.00** | 1 |
| $0.050 | $0.00 | 107 | 106 | **−$8,566.00** | 1 |
| $0.100 | $0.00 | 108 | 108 | **−$11,268.00** | 0 |
| $0.000 | $0.65 | 106 | 105 | −$6,068.20 | 1 |
| $0.025 | $0.65 | 107 | 106 | −$7,185.00 | 1 |
| $0.050 | $0.65 | 107 | 106 | −$9,013.60 | 1 |
| $0.100 | $0.65 | 108 | 108 | −$11,369.20 | 0 |

Trade count changes across scenarios because stressed credit affects eligibility and whole-contract sizing. The legacy **1.2% NAV credit** budget is a different unit from the **0.8% NAV maximum-loss** budget and must not be compared as if they were the same risk limit.

## Measured decision — no parameter fishing

- Do **not** tune delta, DTE, stop-loss, quote-width thresholds, or slippage to rescue the already-inspected 2018–2025 interval.
- Keep the Frozen Original Hybrid, `main`, live sizing and broker-order permissions unchanged. No broker orders are enabled by this research.
- Keep missing source rows, unmarked position dates, unresolved positions and unauthenticated fills explicit; do not interpolate, forward-fill or treat a user-entered reference string as independent source authentication.
- The next useful work is **evidence collection and reconciliation, not feature expansion**: capture prospective two-leg option observations with exact OCC symbols and timezone-bearing timestamps, then compare only matching reported fills where the source quote time is no later than the fill and no more than 15 minutes earlier. Count all excluded fill reports and their exclusion reasons. Separately resolve the terminal source gap and missing NAV marks before calculating portfolio-level performance metrics.
- Only after these data/timing and accounting gates pass should the FAR CALL overlay be compared against the fully specified Frozen Original Hybrid on identical dates, capital flows and costs, with a genuinely untouched or prospective evaluation window.

Full preregistered thresholds: [RESEARCH_MEASUREMENT_CONTRACT.md](RESEARCH_MEASUREMENT_CONTRACT.md). Prior scorecard: [QQQ_HYBRID_MEASUREMENT_SCORECARD_RUN50.md](QQQ_HYBRID_MEASUREMENT_SCORECARD_RUN50.md).
