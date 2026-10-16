# QQQ FAR CALL incremental-value decomposition V2

Status: DESCRIPTIVE DECOMPOSITION ONLY — NOT PERFORMANCE APPROVED.

This report measures four predeclared dimensions. It does not change strategy rules and does not treat EOD quote sides as confirmed fills.

## Gate status

- Base screen: FAILS_CURRENT_BASE_SCREEN
- Independent cash-flow ledger: PASS
- Independently rechecked trade rows: 1688 / 1688
- Maximum absolute independent reconciliation error: USD 0.0
- Source terminal gap sessions: 11
- Last source date: 2025-12-15
- Frozen Original Hybrid changed: False
- Main changed: False
- Broker orders enabled: False

## Coverage

- Expected sessions: 1971
- Sessions with QQQ chain rows: 1956
- Expected date range: 2018-03-01 to 2025-12-31
- Last source observation: 2025-12-15
- Terminal source gap sessions: 11
- The inspected 2018–2025 interval is development evidence, not a virgin holdout.

## Scenario decomposition

| Budget | Slippage/leg | Commission/contract/side | Opens | Closes | Entry gross credit | Entry costs | Exit gross debit | Exit costs | Closed-trade P&L | Paired NAV days | Unmatched days | Last observed NAV difference | Open but unmarked days |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| LEGACY_CREDIT_1P2PCT_NAV | 0.0 | 0.0 | 106 | 105 | USD 128,189.00 | USD 0.00 | USD 194,874.00 | USD 0.00 | USD -66,685.00 | 1947 | 24 | USD -64,993.00 | 24 |
| LEGACY_CREDIT_1P2PCT_NAV | 0.0 | 0.65 | 106 | 105 | USD 125,506.00 | USD 3,285.10 | USD 192,474.00 | USD 3,285.10 | USD -73,538.20 | 1947 | 24 | USD -71,984.40 | 24 |
| LEGACY_CREDIT_1P2PCT_NAV | 0.025 | 0.0 | 107 | 106 | USD 129,438.00 | USD 13,400.00 | USD 188,349.00 | USD 13,400.00 | USD -85,711.00 | 1947 | 24 | USD -84,367.00 | 24 |
| LEGACY_CREDIT_1P2PCT_NAV | 0.025 | 0.65 | 107 | 106 | USD 126,318.00 | USD 17,047.80 | USD 184,061.00 | USD 17,047.80 | USD -91,838.60 | 1947 | 24 | USD -90,536.20 | 24 |
| LEGACY_CREDIT_1P2PCT_NAV | 0.05 | 0.0 | 107 | 106 | USD 113,851.00 | USD 27,970.00 | USD 169,982.00 | USD 27,970.00 | USD -112,071.00 | 1947 | 24 | USD -111,035.00 | 24 |
| LEGACY_CREDIT_1P2PCT_NAV | 0.05 | 0.65 | 107 | 106 | USD 108,577.00 | USD 32,216.30 | USD 163,044.00 | USD 32,216.30 | USD -118,899.60 | 1947 | 24 | USD -117,971.40 | 24 |
| LEGACY_CREDIT_1P2PCT_NAV | 0.1 | 0.0 | 107 | 107 | USD 106,171.00 | USD 60,940.00 | USD 128,382.00 | USD 60,940.00 | USD -144,091.00 | 1947 | 24 | USD -144,091.00 | 13 |
| LEGACY_CREDIT_1P2PCT_NAV | 0.1 | 0.65 | 97 | 97 | USD 118,977.00 | USD 82,409.70 | USD 102,333.00 | USD 82,409.70 | USD -148,175.40 | 1948 | 23 | USD -148,175.40 | 12 |
| SOURCE_MAX_LOSS_0P8PCT_NAV | 0.0 | 0.0 | 106 | 105 | USD 10,782.00 | USD 0.00 | USD 16,428.00 | USD 0.00 | USD -5,646.00 | 1947 | 24 | USD -5,552.00 | 24 |
| SOURCE_MAX_LOSS_0P8PCT_NAV | 0.0 | 0.65 | 106 | 105 | USD 10,680.00 | USD 230.10 | USD 16,288.00 | USD 230.10 | USD -6,068.20 | 1947 | 24 | USD -5,976.80 | 24 |
| SOURCE_MAX_LOSS_0P8PCT_NAV | 0.025 | 0.0 | 107 | 106 | USD 10,959.00 | USD 875.00 | USD 15,939.00 | USD 875.00 | USD -6,730.00 | 1947 | 24 | USD -6,646.00 | 24 |
| SOURCE_MAX_LOSS_0P8PCT_NAV | 0.025 | 0.65 | 107 | 106 | USD 10,959.00 | USD 1,102.50 | USD 15,939.00 | USD 1,102.50 | USD -7,185.00 | 1947 | 24 | USD -7,103.60 | 24 |
| SOURCE_MAX_LOSS_0P8PCT_NAV | 0.05 | 0.0 | 107 | 106 | USD 10,629.00 | USD 1,720.00 | USD 15,755.00 | USD 1,720.00 | USD -8,566.00 | 1947 | 24 | USD -8,492.00 | 24 |
| SOURCE_MAX_LOSS_0P8PCT_NAV | 0.05 | 0.65 | 107 | 106 | USD 10,604.00 | USD 1,932.30 | USD 15,753.00 | USD 1,932.30 | USD -9,013.60 | 1947 | 24 | USD -8,942.20 | 24 |
| SOURCE_MAX_LOSS_0P8PCT_NAV | 0.1 | 0.0 | 108 | 108 | USD 11,067.00 | USD 3,260.00 | USD 15,815.00 | USD 3,260.00 | USD -11,268.00 | 1947 | 24 | USD -11,268.00 | 13 |
| SOURCE_MAX_LOSS_0P8PCT_NAV | 0.1 | 0.65 | 108 | 108 | USD 10,945.00 | USD 3,344.10 | USD 15,626.00 | USD 3,344.10 | USD -11,369.20 | 1946 | 25 | USD -11,369.20 | 14 |

## Existing exit-mechanism attribution — source budget, zero extra costs

| Existing exit reason | Trades | Net P&L | Mean holding days | Exit quote-delay sessions | Exit basis counts |
|---|---:|---:|---:|---:|---|
| DTE_LE_7 | 62 | USD -4,746.00 | 24.61 | 2.0 | {"OBSERVED_EOD_SHORT_ASK_MINUS_WING_BID": 62} |
| EXPIRY_INTRINSIC_SETTLEMENT | 34 | USD 3,250.00 | 28.24 | 129.0 | {"INTRINSIC_SETTLEMENT_PROXY": 34} |
| PNL_OVER_MAXLOSS_LE_NEG_0P55 | 9 | USD -4,150.00 | 18.22 | 0.0 | {"OBSERVED_EOD_SHORT_ASK_MINUS_WING_BID": 9} |

## Cost-arm differences

These are separately sized replay outcomes versus the zero-cost arm, not isolated fee deductions. Entry eligibility and trade counts can change.

| Budget | Slippage/leg | Commission/side | Closed-trade P&L delta | Open-count delta | Close-count delta | Terminal paired-NAV delta |
|---|---:|---:|---:|---:|---:|---:|
| LEGACY_CREDIT_1P2PCT_NAV | 0.0 | 0.0 | USD 0.00 | 0 | 0 | USD 0.00 |
| LEGACY_CREDIT_1P2PCT_NAV | 0.0 | 0.65 | USD -6,853.20 | 0 | 0 | USD -6,991.40 |
| LEGACY_CREDIT_1P2PCT_NAV | 0.025 | 0.0 | USD -19,026.00 | 1 | 1 | USD -19,374.00 |
| LEGACY_CREDIT_1P2PCT_NAV | 0.025 | 0.65 | USD -25,153.60 | 1 | 1 | USD -25,543.20 |
| LEGACY_CREDIT_1P2PCT_NAV | 0.05 | 0.0 | USD -45,386.00 | 1 | 1 | USD -46,042.00 |
| LEGACY_CREDIT_1P2PCT_NAV | 0.05 | 0.65 | USD -52,214.60 | 1 | 1 | USD -52,978.40 |
| LEGACY_CREDIT_1P2PCT_NAV | 0.1 | 0.0 | USD -77,406.00 | 1 | 2 | USD -79,098.00 |
| LEGACY_CREDIT_1P2PCT_NAV | 0.1 | 0.65 | USD -81,490.40 | -9 | -8 | USD -83,182.40 |
| SOURCE_MAX_LOSS_0P8PCT_NAV | 0.0 | 0.0 | USD 0.00 | 0 | 0 | USD 0.00 |
| SOURCE_MAX_LOSS_0P8PCT_NAV | 0.0 | 0.65 | USD -422.20 | 0 | 0 | USD -424.80 |
| SOURCE_MAX_LOSS_0P8PCT_NAV | 0.025 | 0.0 | USD -1,084.00 | 1 | 1 | USD -1,094.00 |
| SOURCE_MAX_LOSS_0P8PCT_NAV | 0.025 | 0.65 | USD -1,539.00 | 1 | 1 | USD -1,551.60 |
| SOURCE_MAX_LOSS_0P8PCT_NAV | 0.05 | 0.0 | USD -2,920.00 | 1 | 1 | USD -2,940.00 |
| SOURCE_MAX_LOSS_0P8PCT_NAV | 0.05 | 0.65 | USD -3,367.60 | 1 | 1 | USD -3,390.20 |
| SOURCE_MAX_LOSS_0P8PCT_NAV | 0.1 | 0.0 | USD -5,622.00 | 2 | 3 | USD -5,716.00 |
| SOURCE_MAX_LOSS_0P8PCT_NAV | 0.1 | 0.65 | USD -5,723.20 | 2 | 3 | USD -5,817.20 |

## Measurement verdict

A. Entry economics: report observed-side credit, assumed costs, contract quantity and all entry skips/blocks.

B. Capital occupancy and marks: use paired dates only. No missing mark is filled and no return-series metrics are inferred from the paired differences.

C. Exit lifecycle: summarize existing exit groups and quote-delay/settlement bases only. This is not proof that an exit rule caused the loss.

D. Data completeness and value: source stops before the requested final date, quotes are EOD, and the reviewed period is not an untouched holdout. Integration remains blocked.

CAGR, daily MTM MaxDD, Sharpe and ES95 are not calculated or claimed. This report does not mutate the Frozen Original Hybrid, main, live sizing, or broker-order permissions.
