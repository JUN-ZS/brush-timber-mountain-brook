# Original Hybrid + TAIL Account-NAV Audit Results

**Actions run:** https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/40184810939  
**Research branch:** \`research/original-hybrid-tail-account-nav-v1\`  
**Result schema:** \`original-hybrid-tail-account-nav.v1\`  
**Result evidence:** COMPLETED by the isolated workflow; account ledger/unit tests and output contract passed.  
**Source class:** DERIVED_BS_VIX_MODEL_NOT_OPRA. No broker orders.

## 1. Scope and common window

- Starting account NAV: USD 100,000.
- Common history: 2018-03-01 through 2025-12-15, 1,960 common sessions. The end date is constrained by the pinned TAIL adjusted-close series.
- Base strategy policy: inherited Original Hybrid baseline, dynamic deployment controller disabled. Same base rules are used in each corrected-account TAIL arm.
- Included sleeves: QQQ core shares, QQQ far-OTM call-credit spread, VXX short-stock notional, VXX call-credit spread.
- TAIL signal known at day \(t\) close and entered no earlier than the next common session's adjusted close. One TAIL position at a time; not a stack of overlapping per-episode positions.
- TAIL trigger, frozen before the run: VXX daily return > +6%, or VIX > 35, or inherited VIX/MA20 term-slope proxy < 0, or QQQ daily return < -3%. Exit at next common session close after two consecutive non-triggering closes. Later triggers can re-enter after exit.
- TAIL purchase cost, adjusted-close mark-to-market, sale proceeds, and assumed friction flow through the same cash/NAV ledger. TAIL NAV affects subsequent NAV-based option sizing.

## 2. Material inherited accounting defect

Source: \`research/qqq_hybrid_dynamic_deployment_v1_1_replay.py\`, the QQQ stock-open statement currently at line 161 in the inherited source SHA \`ac74b3812c826ad491fb829108f26397322e45eb\`.

The line uses the no-op expression:

\`\`\`python
cash_box[0]-row.qqq*n
\`\`\`

It has no assignment operator, so QQQ share purchase cost is **not deducted from cash**. The model then adds the QQQ shares' marked value to NAV. This double-counts the purchase-funded equity: the shares appear as an asset while their cash cost remains in cash. It is a material account-NAV defect.

To quantify the defect, the replay contains a diagnostic arm \`LEGACY_NO_QQQ_DEBIT\` that deliberately reproduces this issue. It is not a valid account-return baseline. All recommended TAIL comparisons use the corrected account ledger: \`cash_box[0] -= row.qqq*n\`.

| Same-date-window result | Corrected no-TAIL account | Legacy missing-cash-debit diagnostic | Legacy minus corrected |
|---|---:|---:|---:|
| Final NAV | USD 254,787.62 | USD 302,739.53 | +USD 47,951.91 |
| Net P&L on USD 100k start | USD 154,787.62 | USD 202,739.53 | +USD 47,951.91 |
| CAGR | 12.7530% | 15.2761% | +2.5231 percentage points |
| Daily MTM MaxDD | -23.0213% | -21.2557% | appears 1.7656 pp less severe |

These differences are **not strategy alpha**. The legacy control has a broken funding ledger and also feeds the inflated NAV into subsequent NAV-sized option positions. This directly invalidates the legacy control as executable account performance. But the common-window diagnostic alone does not prove that every previously reported headline was generated from the buggy code; the original report's exact run-source provenance must be checked separately.

## 3. Full original-history accounting reproduction (2018-03-01 to 2026-09-04)

A second same-code, no-TAIL replay was run on the full original-history window: 2,141 sessions. It does not use the shorter TAIL price pairing window.

| Full-window control | Final NAV | CAGR | Daily MTM MaxDD |
|---|---:|---:|---:|
| Corrected account ledger, no TAIL | USD 298,267.22 | 13.6992% | -23.0213% |
| Legacy missing-QQQ-cash-debit control | USD 348,116.65 | 15.7824% | -21.2557% |
| Legacy minus corrected | +USD 49,849.42 | +2.0832 pp | appears 1.7656 pp less severe |

**Important reconciliation:** the corrected full-window replay reproduces the archived Original Hybrid combined replay headline to the displayed precision: about USD 298,267 final NAV, 13.70% CAGR, and -23.02% daily MTM MaxDD. The deliberately buggy no-debit control does *not* reproduce those numbers; it is materially higher. Therefore the archived 13.70% output appears to correspond to the corrected account ledger, while the currently pinned source file contains a no-op expression for the cash debit. This is a **source-to-result provenance inconsistency**: the output can be reproduced with the corrected code, but the source blob attached to the current replay lineage should not be claimed as the exact generating source until its commit history / original run code is reconciled. The previous 13.70% should not be discarded solely because a later/current source file contains this defect, but its exact historical provenance remains pending.

## 3. TAIL comparison using corrected account-NAV ledger

All amounts are USD. CAGR and drawdown are calculated from the same common daily NAV path and dates. The “final NAV delta” is versus the corrected \`NO_TAIL\` baseline. A positive MaxDD delta means a less-negative drawdown.

| Variant | TAIL allocation at entry | Friction round trip | Final NAV | CAGR | Daily MTM MaxDD | Final NAV delta vs no TAIL | MaxDD improvement vs no TAIL | Net TAIL P&L |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| NO_TAIL | 0% | N/A | 254,787.62 | 12.7530% | -23.0213% | — | — | 0.00 |
| ALWAYS_ON_2P | 2% | 10 bps | 253,239.68 | 12.6649% | -23.0451% | -1,547.94 | -0.0238 pp (worse) | -798.23 |
| TRIGGERED_1P | 1% | 10 bps | 253,893.13 | 12.7021% | -22.9570% | -894.49 | +0.0642 pp | -710.08 |
| TRIGGERED_2P | 2% | 10 bps | 253,018.72 | 12.6522% | -22.8497% | -1,768.90 | +0.1716 pp | -1,417.79 |
| TRIGGERED_5P | 5% | 10 bps | 251,038.93 | 12.5387% | -22.4970% | -3,748.69 | +0.5242 pp | -3,534.33 |
| TRIGGERED_2P_0BPS | 2% | 0 bps | 253,406.98 | 12.6744% | -22.8190% | -1,380.64 | +0.2023 pp | -1,010.85 |
| TRIGGERED_2P_25BPS | 2% | 25 bps | 252,173.91 | 12.6039% | -22.9125% | -2,613.71 | +0.1087 pp | -2,023.99 |
| TRIGGERED_2P_50BPS | 2% | 50 bps | 248,000.73 | 12.3630% | -23.2199% | -6,786.90 | -0.1986 pp (worse) | -3,002.27 |

## 5. What the experiment says

1. **The fixed-hold TAIL variant did not help this account.** Holding 2% TAIL through the entire sample reduced CAGR by 0.0881 pp and made maximum drawdown slightly worse. Its net TAIL P&L was -USD 798.23.
2. **The risk-triggered TAIL overlay reduced maximum drawdown modestly but lost money on its own.** At a 1% NAV allocation, MaxDD improves by 0.0642 pp while CAGR decreases by 0.0509 pp. At 2%, MaxDD improves by 0.1716 pp while CAGR decreases by 0.1008 pp. At 5%, MaxDD improves by 0.5242 pp, but CAGR falls by 0.2143 pp and the overlay loses USD 3,534.33.
3. **Transaction costs matter.** At a 2% allocation, the assumed 50 bps round-trip case makes both CAGR and MaxDD worse than no TAIL. Even with 0 bps, TAIL's adjusted-close return over the triggered holding windows is negative in aggregate (-USD 1,010.85).
4. **No overlay in this tested grid dominates the corrected no-TAIL account on both CAGR and maximum drawdown.** The 1% triggered arm is the most modest premium-loss case but buys only 0.0642 pp of historical MaxDD improvement. These results do not establish that all TAIL timing or hedging rules fail; the fixed trigger and exit policy are only one preregistered hypothesis.
5. **The common window matters.** These are 2018-03-01 to 2025-12-15 results, not the original 2026-09-04 full-history period. This window is required to pair every model arm to the saved TAIL price history.

## 6. Limits and reproduction evidence

- The original Hybrid option legs use Black–Scholes marks with VIX-derived IV and modeled spread haircuts, not historical OPRA chains or executable quote-side fills.
- The VX condition is the inherited VIX/MA20 term-slope proxy, not real historical VX M1/M2.
- TAIL uses a pinned Yahoo Finance adjusted-close return proxy and assumed 0/10/25/50 bps friction sensitivities, not reconstructed executable fills or historical bid/ask spread.
- No broker commissions, option margin, early assignment, forced liquidation, borrow/carry costs, or broker buying-power rules are modeled.
- In-sample replay only; no forward-alpha claim.

Successful current workflow: [Actions run #7](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/40184810939). The corrected account-ledger comparisons are outputs from the actual run, not theoretical arithmetic. The isolated workflow passed syntax/accounting tests, the nine-arm replay contract and persisted \`report.json\`, \`summary.csv\`, \`calendar_year.csv\`, daily equity curves and TAIL trade ledgers on the research branch.

