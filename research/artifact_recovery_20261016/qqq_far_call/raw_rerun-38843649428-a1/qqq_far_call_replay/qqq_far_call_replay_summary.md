# QQQ FAR CALL listed-contract EOD-side replay

**Status:** research diagnostic only; not exchange-confirmed fills and not performance approval.
**Observed data window:** 2018-03-01–2025-12-15. Requested through 2025-12-31; terminal source gap remains.
**Coverage:** 1971 expected sessions, 1956 with QQQ chain rows.

## Paired scenarios (all trade P&L figures are quote-side proxies after listed cost scenarios)

| Budget | Slip/leg | Commission/contract/side | Opens | Closes | Closed-trade P&L sum | Avg closed-trade P&L | Open/unresolved end | Missing position marks |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| SOURCE_MAX_LOSS_0P8PCT_NAV | $0.000 | $0.00 | 106 | 105 | $-5646.00 | $-53.77 | 1 | 24 |
| SOURCE_MAX_LOSS_0P8PCT_NAV | $0.000 | $0.65 | 106 | 105 | $-6068.20 | $-57.79 | 1 | 24 |
| SOURCE_MAX_LOSS_0P8PCT_NAV | $0.025 | $0.00 | 107 | 106 | $-6730.00 | $-63.49 | 1 | 24 |
| SOURCE_MAX_LOSS_0P8PCT_NAV | $0.025 | $0.65 | 107 | 106 | $-7185.00 | $-67.78 | 1 | 24 |
| SOURCE_MAX_LOSS_0P8PCT_NAV | $0.050 | $0.00 | 107 | 106 | $-8566.00 | $-80.81 | 1 | 24 |
| SOURCE_MAX_LOSS_0P8PCT_NAV | $0.050 | $0.65 | 107 | 106 | $-9013.60 | $-85.03 | 1 | 24 |
| SOURCE_MAX_LOSS_0P8PCT_NAV | $0.100 | $0.00 | 108 | 108 | $-11268.00 | $-104.33 | 0 | 13 |
| SOURCE_MAX_LOSS_0P8PCT_NAV | $0.100 | $0.65 | 108 | 108 | $-11369.20 | $-105.27 | 0 | 14 |
| LEGACY_CREDIT_1P2PCT_NAV | $0.000 | $0.00 | 106 | 105 | $-66685.00 | $-635.10 | 1 | 24 |
| LEGACY_CREDIT_1P2PCT_NAV | $0.000 | $0.65 | 106 | 105 | $-73538.20 | $-700.36 | 1 | 24 |
| LEGACY_CREDIT_1P2PCT_NAV | $0.025 | $0.00 | 107 | 106 | $-85711.00 | $-808.59 | 1 | 24 |
| LEGACY_CREDIT_1P2PCT_NAV | $0.025 | $0.65 | 107 | 106 | $-91838.60 | $-866.40 | 1 | 24 |
| LEGACY_CREDIT_1P2PCT_NAV | $0.050 | $0.00 | 107 | 106 | $-112071.00 | $-1057.27 | 1 | 24 |
| LEGACY_CREDIT_1P2PCT_NAV | $0.050 | $0.65 | 107 | 106 | $-118899.60 | $-1121.69 | 1 | 24 |
| LEGACY_CREDIT_1P2PCT_NAV | $0.100 | $0.00 | 107 | 107 | $-144091.00 | $-1346.64 | 0 | 13 |
| LEGACY_CREDIT_1P2PCT_NAV | $0.100 | $0.65 | 97 | 97 | $-148175.40 | $-1527.58 | 0 | 12 |

## Matched-day NAV difference vs no-call control

This is a descriptive overlay-minus-control NAV difference on dates where both paths can be marked. It excludes unmarked dates without interpolation and is **not** CAGR, MaxDD, or performance approval.

| Budget | Slip/leg | Commission/contract/side | Matched dates | Unmatched dates | Last matched date | Last NAV difference | Minimum observed difference | Maximum observed difference | Positive mark days |
|---|---:|---:|---:|---:|---|---:|---:|---:|---:|
| SOURCE_MAX_LOSS_0P8PCT_NAV | $0.000 | $0.00 | 1947 | 24 | 2025-12-15 | $-5552.00 | $-5926.00 | $88.00 | 32/1947 |
| SOURCE_MAX_LOSS_0P8PCT_NAV | $0.000 | $0.65 | 1947 | 24 | 2025-12-15 | $-5976.80 | $-6345.60 | $77.60 | 30/1947 |
| SOURCE_MAX_LOSS_0P8PCT_NAV | $0.025 | $0.00 | 1947 | 24 | 2025-12-15 | $-6646.00 | $-7000.00 | $43.00 | 26/1947 |
| SOURCE_MAX_LOSS_0P8PCT_NAV | $0.025 | $0.65 | 1947 | 24 | 2025-12-15 | $-7103.60 | $-7452.40 | $35.20 | 24/1947 |
| SOURCE_MAX_LOSS_0P8PCT_NAV | $0.050 | $0.00 | 1947 | 24 | 2025-12-15 | $-8492.00 | $-8826.00 | $18.00 | 12/1947 |
| SOURCE_MAX_LOSS_0P8PCT_NAV | $0.050 | $0.65 | 1947 | 24 | 2025-12-15 | $-8942.20 | $-9271.00 | $12.80 | 10/1947 |
| SOURCE_MAX_LOSS_0P8PCT_NAV | $0.100 | $0.00 | 1947 | 24 | 2025-12-15 | $-11268.00 | $-11697.00 | $9.00 | 3/1947 |
| SOURCE_MAX_LOSS_0P8PCT_NAV | $0.100 | $0.65 | 1946 | 25 | 2025-12-15 | $-11369.20 | $-11795.60 | $1.20 | 1/1946 |
| LEGACY_CREDIT_1P2PCT_NAV | $0.000 | $0.00 | 1947 | 24 | 2025-12-15 | $-64993.00 | $-72682.00 | $2374.00 | 30/1947 |
| LEGACY_CREDIT_1P2PCT_NAV | $0.000 | $0.65 | 1947 | 24 | 2025-12-15 | $-71984.40 | $-79309.80 | $2201.60 | 27/1947 |
| LEGACY_CREDIT_1P2PCT_NAV | $0.025 | $0.00 | 1947 | 24 | 2025-12-15 | $-84367.00 | $-91029.00 | $1540.00 | 14/1947 |
| LEGACY_CREDIT_1P2PCT_NAV | $0.025 | $0.65 | 1947 | 24 | 2025-12-15 | $-90536.20 | $-97135.80 | $1195.60 | 13/1947 |
| LEGACY_CREDIT_1P2PCT_NAV | $0.050 | $0.00 | 1947 | 24 | 2025-12-15 | $-111035.00 | $-116528.00 | $567.00 | 6/1947 |
| LEGACY_CREDIT_1P2PCT_NAV | $0.050 | $0.65 | 1947 | 24 | 2025-12-15 | $-117971.40 | $-123166.00 | $435.20 | 6/1947 |
| LEGACY_CREDIT_1P2PCT_NAV | $0.100 | $0.00 | 1947 | 24 | 2025-12-15 | $-144091.00 | $-148750.00 | $0.00 | 0/1947 |
| LEGACY_CREDIT_1P2PCT_NAV | $0.100 | $0.65 | 1948 | 23 | 2025-12-15 | $-148175.40 | $-152808.40 | $0.00 | 0/1948 |

The control holds the same 42% QQQ core total-return proxy and static 58% cash but has no option trades. Option overlay marks include the conservative zero-wing-Bid floor where present. Since dates with missing marks are excluded, this table is a measurement/attribution diagnostic only; it cannot establish a complete portfolio CAGR or drawdown.

## Trade-level attribution (closed spreads only)

Cash-flow reconciliation: 1688 PASS, 0 FAIL, 0 BLOCKED rows. Every trade decomposes into gross entry credit − entry costs − gross exit debit − exit costs; a mismatch over $0.01 is a hard diagnostic failure.

The attributed trades CSV includes entry/exit leg quotes, leg spread/midpoint, Delta drift, raw nominal spot, signal/entry/exit VIX regime, 20-session raw-spot momentum regime, close-signal reason, missing-quote exit deferrals, holding days and loss as a percentage of the recorded scenario max-loss budget. These are descriptive strata, not changes to strategy rules or proof of fills.

| Scenario | Net P&L | Entry gross credit | Entry costs | Exit gross debit | Exit costs | Reconciliation failures | Mean short Delta drift | Mean loss / max-loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| LEGACY_CREDIT_1P2PCT_NAV|SLIP_PER_LEG_0.000|COMM_PER_CONTRACT_SIDE_0.00 | $-66685.00 | $128189.00 | $0.00 | $194874.00 | $0.00 | 0 | 0.1645 | 12.94% |
| LEGACY_CREDIT_1P2PCT_NAV|SLIP_PER_LEG_0.000|COMM_PER_CONTRACT_SIDE_0.65 | $-73538.20 | $125506.00 | $3285.10 | $192474.00 | $3285.10 | 0 | 0.1645 | 13.13% |
| LEGACY_CREDIT_1P2PCT_NAV|SLIP_PER_LEG_0.025|COMM_PER_CONTRACT_SIDE_0.00 | $-85711.00 | $129438.00 | $13400.00 | $188349.00 | $13400.00 | 0 | 0.1438 | 12.92% |
| LEGACY_CREDIT_1P2PCT_NAV|SLIP_PER_LEG_0.025|COMM_PER_CONTRACT_SIDE_0.65 | $-91838.60 | $126318.00 | $17047.80 | $184061.00 | $17047.80 | 0 | 0.1438 | 13.10% |
| LEGACY_CREDIT_1P2PCT_NAV|SLIP_PER_LEG_0.050|COMM_PER_CONTRACT_SIDE_0.00 | $-112071.00 | $113851.00 | $27970.00 | $169982.00 | $27970.00 | 0 | 0.1465 | 13.76% |
| LEGACY_CREDIT_1P2PCT_NAV|SLIP_PER_LEG_0.050|COMM_PER_CONTRACT_SIDE_0.65 | $-118899.60 | $108577.00 | $32216.30 | $163044.00 | $32216.30 | 0 | 0.1465 | 13.94% |
| LEGACY_CREDIT_1P2PCT_NAV|SLIP_PER_LEG_0.100|COMM_PER_CONTRACT_SIDE_0.00 | $-144091.00 | $106171.00 | $60940.00 | $128382.00 | $60940.00 | 0 | 0.1352 | 15.51% |
| LEGACY_CREDIT_1P2PCT_NAV|SLIP_PER_LEG_0.100|COMM_PER_CONTRACT_SIDE_0.65 | $-148175.40 | $118977.00 | $82409.70 | $102333.00 | $82409.70 | 0 | 0.1461 | 16.39% |
| SOURCE_MAX_LOSS_0P8PCT_NAV|SLIP_PER_LEG_0.000|COMM_PER_CONTRACT_SIDE_0.00 | $-5646.00 | $10782.00 | $0.00 | $16428.00 | $0.00 | 0 | 0.1654 | 13.02% |
| SOURCE_MAX_LOSS_0P8PCT_NAV|SLIP_PER_LEG_0.000|COMM_PER_CONTRACT_SIDE_0.65 | $-6068.20 | $10680.00 | $230.10 | $16288.00 | $230.10 | 0 | 0.1654 | 13.20% |
| SOURCE_MAX_LOSS_0P8PCT_NAV|SLIP_PER_LEG_0.025|COMM_PER_CONTRACT_SIDE_0.00 | $-6730.00 | $10959.00 | $875.00 | $15939.00 | $875.00 | 0 | 0.1446 | 13.00% |
| SOURCE_MAX_LOSS_0P8PCT_NAV|SLIP_PER_LEG_0.025|COMM_PER_CONTRACT_SIDE_0.65 | $-7185.00 | $10959.00 | $1102.50 | $15939.00 | $1102.50 | 0 | 0.1446 | 13.18% |
| SOURCE_MAX_LOSS_0P8PCT_NAV|SLIP_PER_LEG_0.050|COMM_PER_CONTRACT_SIDE_0.00 | $-8566.00 | $10629.00 | $1720.00 | $15755.00 | $1720.00 | 0 | 0.1473 | 13.84% |
| SOURCE_MAX_LOSS_0P8PCT_NAV|SLIP_PER_LEG_0.050|COMM_PER_CONTRACT_SIDE_0.65 | $-9013.60 | $10604.00 | $1932.30 | $15753.00 | $1932.30 | 0 | 0.1473 | 14.02% |
| SOURCE_MAX_LOSS_0P8PCT_NAV|SLIP_PER_LEG_0.100|COMM_PER_CONTRACT_SIDE_0.00 | $-11268.00 | $11067.00 | $3260.00 | $15815.00 | $3260.00 | 0 | 0.1515 | 16.59% |
| SOURCE_MAX_LOSS_0P8PCT_NAV|SLIP_PER_LEG_0.100|COMM_PER_CONTRACT_SIDE_0.65 | $-11369.20 | $10945.00 | $3344.10 | $15626.00 | $3344.10 | 0 | 0.1496 | 16.42% |

Group attribution CSV contains all scenarios. The Actions summary below renders the pre-selected base and adverse-cost scenario strata for visibility even if artifact storage is unavailable.


### Attribution strata: `SOURCE_MAX_LOSS_0P8PCT_NAV|SLIP_PER_LEG_0.000|COMM_PER_CONTRACT_SIDE_0.00`

| Dimension | Bucket | Trades | Net P&L | Mean P&L | Win fraction | Mean loss / max-loss | Mean short Delta drift | Reconciliation fails |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| exit_reason | DTE_LE_7 | 62 | $-4746.00 | $-76.55 | 46.8% | 14.51% | 0.1214 | 0 |
| exit_reason | EXPIRY_INTRINSIC_SETTLEMENT | 34 | $3250.00 | $95.59 | 100.0% | 0.00% | — | 0 |
| exit_reason | PNL_OVER_MAXLOSS_LE_NEG_0P55 | 9 | $-4150.00 | $-461.11 | 0.0% | 51.87% | 0.4682 | 0 |
| signal_regime | ELEVATED_25_35 | 16 | $388.00 | $24.25 | 62.5% | 7.08% | 0.0800 | 0 |
| signal_regime | HIGH_GTE35 | 3 | $-484.00 | $-161.33 | 33.3% | 20.70% | 0.2740 | 0 |
| signal_regime | LOW_LT15 | 26 | $-3474.00 | $-133.62 | 50.0% | 19.62% | 0.2315 | 0 |
| signal_regime | NORMAL_15_25 | 60 | $-2076.00 | $-34.60 | 65.0% | 11.35% | 0.1444 | 0 |
| entry_regime | ELEVATED_25_35 | 17 | $407.00 | $23.94 | 64.7% | 6.80% | 0.0689 | 0 |
| entry_regime | HIGH_GTE35 | 2 | $-429.00 | $-214.50 | 50.0% | 28.29% | 0.3454 | 0 |
| entry_regime | LOW_LT15 | 27 | $-2784.00 | $-103.11 | 55.6% | 18.05% | 0.1687 | 0 |
| entry_regime | NORMAL_15_25 | 59 | $-2840.00 | $-48.14 | 61.0% | 11.98% | 0.1828 | 0 |
| exit_regime | ELEVATED_25_35 | 16 | $666.00 | $41.63 | 81.2% | 8.00% | 0.1370 | 0 |
| exit_regime | HIGH_GTE35 | 3 | $-130.00 | $-43.33 | 66.7% | 18.86% | 0.1706 | 0 |
| exit_regime | LOW_LT15 | 26 | $-4063.00 | $-156.27 | 38.5% | 22.08% | 0.2798 | 0 |
| exit_regime | NORMAL_15_25 | 60 | $-2119.00 | $-35.32 | 63.3% | 10.14% | 0.1113 | 0 |
| signal_trend_regime | DOWN_LE_NEG2PCT_20S | 21 | $-787.00 | $-37.48 | 61.9% | 11.73% | 0.1119 | 0 |
| signal_trend_regime | RANGE_ABS_LT2PCT_20S | 24 | $-1532.00 | $-63.83 | 58.3% | 15.15% | 0.2184 | 0 |
| signal_trend_regime | UNKNOWN_INSUFFICIENT_20_SESSION_HISTORY | 1 | $58.00 | $58.00 | 100.0% | 0.00% | — | 0 |
| signal_trend_regime | UP_GE_2PCT_20S | 59 | $-3385.00 | $-57.37 | 59.3% | 12.83% | 0.1642 | 0 |
| entry_trend_regime | DOWN_LE_NEG2PCT_20S | 22 | $-565.00 | $-25.68 | 68.2% | 10.43% | 0.1012 | 0 |
| entry_trend_regime | RANGE_ABS_LT2PCT_20S | 23 | $-1925.00 | $-83.70 | 52.2% | 14.55% | 0.2134 | 0 |
| entry_trend_regime | UNKNOWN_INSUFFICIENT_20_SESSION_HISTORY | 1 | $58.00 | $58.00 | 100.0% | 0.00% | — | 0 |
| entry_trend_regime | UP_GE_2PCT_20S | 59 | $-3214.00 | $-54.47 | 59.3% | 13.60% | 0.1680 | 0 |
| exit_trend_regime | DOWN_LE_NEG2PCT_20S | 21 | $2211.00 | $105.29 | 100.0% | 0.00% | -0.1642 | 0 |
| exit_trend_regime | RANGE_ABS_LT2PCT_20S | 24 | $2314.00 | $96.42 | 100.0% | 0.00% | -0.1545 | 0 |
| exit_trend_regime | UP_GE_2PCT_20S | 60 | $-10171.00 | $-169.52 | 30.0% | 22.78% | 0.2376 | 0 |
| exit_signal_regime | ELEVATED_25_35 | 10 | $672.00 | $67.20 | 90.0% | 3.06% | 0.0269 | 0 |
| exit_signal_regime | HIGH_GTE35 | 4 | $-16.00 | $-4.00 | 75.0% | 14.15% | 0.1706 | 0 |
| exit_signal_regime | LOW_LT15 | 30 | $-4655.00 | $-155.17 | 40.0% | 21.81% | 0.2324 | 0 |
| exit_signal_regime | NORMAL_15_25 | 61 | $-1647.00 | $-27.00 | 63.9% | 10.25% | 0.1346 | 0 |
| exit_quote_missing_sessions | 0 | 69 | $-9043.00 | $-131.06 | 39.1% | 19.81% | 0.1736 | 0 |
| exit_quote_missing_sessions | 1 | 2 | $147.00 | $73.50 | 100.0% | 0.00% | -0.1192 | 0 |
| exit_quote_missing_sessions | 3 | 7 | $707.00 | $101.00 | 100.0% | 0.00% | — | 0 |
| exit_quote_missing_sessions | 4 | 27 | $2543.00 | $94.19 | 100.0% | 0.00% | — | 0 |
| entry_quote_quality_bucket | MODERATE_10_25PCT_MID | 17 | $-826.00 | $-48.59 | 52.9% | 13.19% | 0.3400 | 0 |
| entry_quote_quality_bucket | TIGHT_LE_10PCT_MID | 80 | $-3908.00 | $-48.85 | 61.3% | 12.45% | 0.1285 | 0 |
| entry_quote_quality_bucket | WIDE_GT25PCT_MID | 8 | $-912.00 | $-114.00 | 62.5% | 18.34% | 0.3593 | 0 |
| exit_quote_quality_bucket | MODERATE_10_25PCT_MID | 16 | $-442.00 | $-27.62 | 37.5% | 7.11% | 0.0978 | 0 |
| exit_quote_quality_bucket | TIGHT_LE_10PCT_MID | 32 | $-10519.00 | $-328.72 | 3.1% | 38.86% | 0.3974 | 0 |
| exit_quote_quality_bucket | UNKNOWN_QUOTE_SPREAD | 34 | $3250.00 | $95.59 | 100.0% | 0.00% | — | 0 |
| exit_quote_quality_bucket | WIDE_GT25PCT_MID | 23 | $2065.00 | $89.78 | 95.7% | 0.42% | -0.1104 | 0 |
| entry_year | 2018 | 11 | $-219.00 | $-19.91 | 72.7% | 9.12% | 0.3892 | 0 |
| entry_year | 2019 | 14 | $-1651.00 | $-117.93 | 21.4% | 20.07% | 0.2772 | 0 |
| entry_year | 2020 | 13 | $-1121.00 | $-86.23 | 61.5% | 19.35% | 0.2359 | 0 |
| entry_year | 2021 | 14 | $-712.00 | $-50.86 | 57.1% | 10.62% | 0.2050 | 0 |
| entry_year | 2022 | 13 | $92.00 | $7.08 | 69.2% | 7.13% | 0.1254 | 0 |
| entry_year | 2023 | 14 | $-875.00 | $-62.50 | 64.3% | 16.62% | 0.1812 | 0 |
| entry_year | 2024 | 14 | $-787.00 | $-56.21 | 78.6% | 10.87% | 0.0357 | 0 |
| entry_year | 2025 | 12 | $-373.00 | $-31.08 | 58.3% | 8.98% | 0.0497 | 0 |
| exit_year | 2018 | 11 | $-219.00 | $-19.91 | 72.7% | 9.12% | 0.3892 | 0 |
| exit_year | 2019 | 13 | $-1161.00 | $-89.31 | 23.1% | 17.35% | 0.2604 | 0 |
| exit_year | 2020 | 13 | $-1663.00 | $-127.92 | 53.8% | 23.60% | 0.2896 | 0 |
| exit_year | 2021 | 14 | $-930.00 | $-66.43 | 57.1% | 10.62% | 0.1719 | 0 |
| exit_year | 2022 | 13 | $311.00 | $23.92 | 69.2% | 7.13% | 0.1254 | 0 |
| exit_year | 2023 | 14 | $-922.00 | $-65.86 | 64.3% | 16.62% | 0.2216 | 0 |
| exit_year | 2024 | 14 | $-752.00 | $-53.71 | 78.6% | 10.87% | 0.0297 | 0 |
| exit_year | 2025 | 13 | $-310.00 | $-23.85 | 61.5% | 8.29% | 0.0356 | 0 |

### Attribution strata: `SOURCE_MAX_LOSS_0P8PCT_NAV|SLIP_PER_LEG_0.050|COMM_PER_CONTRACT_SIDE_0.65`

| Dimension | Bucket | Trades | Net P&L | Mean P&L | Win fraction | Mean loss / max-loss | Mean short Delta drift | Reconciliation fails |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| exit_reason | DTE_LE_7 | 64 | $-6856.40 | $-107.13 | 46.9% | 15.82% | 0.1075 | 0 |
| exit_reason | EXPIRY_INTRINSIC_SETTLEMENT | 33 | $1818.60 | $55.11 | 87.9% | 0.12% | — | 0 |
| exit_reason | PNL_OVER_MAXLOSS_LE_NEG_0P55 | 9 | $-3975.80 | $-441.76 | 0.0% | 52.16% | 0.4306 | 0 |
| signal_regime | ELEVATED_25_35 | 15 | $71.00 | $4.73 | 66.7% | 8.14% | 0.0799 | 0 |
| signal_regime | HIGH_GTE35 | 3 | $-551.80 | $-183.93 | 0.0% | 22.71% | 0.2740 | 0 |
| signal_regime | LOW_LT15 | 26 | $-4544.60 | $-174.79 | 46.2% | 22.09% | 0.2064 | 0 |
| signal_regime | NORMAL_15_25 | 62 | $-3988.20 | $-64.33 | 59.7% | 11.63% | 0.1220 | 0 |
| entry_regime | ELEVATED_25_35 | 18 | $63.60 | $3.53 | 66.7% | 7.21% | 0.0689 | 0 |
| entry_regime | HIGH_GTE35 | 2 | $-474.20 | $-237.10 | 0.0% | 30.26% | 0.3454 | 0 |
| entry_regime | LOW_LT15 | 29 | $-4078.00 | $-140.62 | 51.7% | 19.81% | 0.1500 | 0 |
| entry_regime | NORMAL_15_25 | 57 | $-4525.00 | $-79.39 | 56.1% | 12.65% | 0.1586 | 0 |
| exit_regime | ELEVATED_25_35 | 15 | $45.00 | $3.00 | 73.3% | 9.16% | 0.1370 | 0 |
| exit_regime | HIGH_GTE35 | 3 | $-220.40 | $-73.47 | 66.7% | 19.28% | 0.1706 | 0 |
| exit_regime | LOW_LT15 | 26 | $-4839.20 | $-186.12 | 38.5% | 22.74% | 0.2278 | 0 |
| exit_regime | NORMAL_15_25 | 62 | $-3999.00 | $-64.50 | 58.1% | 11.28% | 0.1058 | 0 |
| signal_trend_regime | DOWN_LE_NEG2PCT_20S | 22 | $-885.80 | $-40.26 | 59.1% | 11.70% | 0.0907 | 0 |
| signal_trend_regime | RANGE_ABS_LT2PCT_20S | 22 | $-2544.00 | $-115.64 | 54.5% | 16.81% | 0.1886 | 0 |
| signal_trend_regime | UNKNOWN_INSUFFICIENT_20_SESSION_HISTORY | 1 | $12.80 | $12.80 | 100.0% | 0.00% | — | 0 |
| signal_trend_regime | UP_GE_2PCT_20S | 61 | $-5596.60 | $-91.75 | 54.1% | 14.08% | 0.1513 | 0 |
| entry_trend_regime | DOWN_LE_NEG2PCT_20S | 23 | $-641.20 | $-27.88 | 60.9% | 10.16% | 0.0784 | 0 |
| entry_trend_regime | RANGE_ABS_LT2PCT_20S | 21 | $-2701.40 | $-128.64 | 52.4% | 16.34% | 0.1837 | 0 |
| entry_trend_regime | UNKNOWN_INSUFFICIENT_20_SESSION_HISTORY | 1 | $12.80 | $12.80 | 100.0% | 0.00% | — | 0 |
| entry_trend_regime | UP_GE_2PCT_20S | 61 | $-5683.80 | $-93.18 | 54.1% | 14.90% | 0.1552 | 0 |
| exit_trend_regime | DOWN_LE_NEG2PCT_20S | 22 | $1406.00 | $63.91 | 95.5% | 0.08% | -0.1770 | 0 |
| exit_trend_regime | RANGE_ABS_LT2PCT_20S | 22 | $1332.40 | $60.56 | 86.4% | 0.10% | -0.1545 | 0 |
| exit_trend_regime | UP_GE_2PCT_20S | 62 | $-11752.00 | $-189.55 | 30.6% | 23.90% | 0.2205 | 0 |
| exit_signal_regime | ELEVATED_25_35 | 10 | $446.00 | $44.60 | 80.0% | 3.63% | 0.0269 | 0 |
| exit_signal_regime | HIGH_GTE35 | 3 | $-220.40 | $-73.47 | 66.7% | 19.28% | 0.1706 | 0 |
| exit_signal_regime | LOW_LT15 | 28 | $-5662.40 | $-202.23 | 39.3% | 24.56% | 0.1995 | 0 |
| exit_signal_regime | NORMAL_15_25 | 65 | $-3576.80 | $-55.03 | 58.5% | 10.83% | 0.1249 | 0 |
| exit_quote_missing_sessions | 0 | 71 | $-10934.00 | $-154.00 | 39.4% | 20.87% | 0.1549 | 0 |
| exit_quote_missing_sessions | 1 | 2 | $101.80 | $50.90 | 100.0% | 0.00% | -0.1192 | 0 |
| exit_quote_missing_sessions | 3 | 8 | $274.40 | $34.30 | 62.5% | 0.27% | — | 0 |
| exit_quote_missing_sessions | 4 | 25 | $1544.20 | $61.77 | 96.0% | 0.07% | — | 0 |
| entry_quote_quality_bucket | MODERATE_10_25PCT_MID | 15 | $-1352.60 | $-90.17 | 40.0% | 14.89% | 0.3254 | 0 |
| entry_quote_quality_bucket | TIGHT_LE_10PCT_MID | 84 | $-6552.40 | $-78.00 | 60.7% | 13.39% | 0.1189 | 0 |
| entry_quote_quality_bucket | WIDE_GT25PCT_MID | 7 | $-1108.60 | $-158.37 | 28.6% | 19.72% | 0.2773 | 0 |
| exit_quote_quality_bucket | MODERATE_10_25PCT_MID | 16 | $-997.40 | $-62.34 | 37.5% | 10.04% | 0.0916 | 0 |
| exit_quote_quality_bucket | TIGHT_LE_10PCT_MID | 31 | $-11225.80 | $-362.12 | 3.2% | 41.81% | 0.3947 | 0 |
| exit_quote_quality_bucket | UNKNOWN_QUOTE_SPREAD | 33 | $1818.60 | $55.11 | 87.9% | 0.12% | — | 0 |
| exit_quote_quality_bucket | WIDE_GT25PCT_MID | 26 | $1391.00 | $53.50 | 88.5% | 0.96% | -0.1133 | 0 |
| entry_year | 2018 | 12 | $-614.40 | $-51.20 | 50.0% | 9.61% | 0.1336 | 0 |
| entry_year | 2019 | 14 | $-2131.00 | $-152.21 | 28.6% | 21.52% | 0.2146 | 0 |
| entry_year | 2020 | 13 | $-1482.60 | $-114.05 | 46.2% | 20.56% | 0.2359 | 0 |
| entry_year | 2021 | 14 | $-1313.40 | $-93.81 | 50.0% | 13.12% | 0.2304 | 0 |
| entry_year | 2022 | 13 | $-201.80 | $-15.52 | 69.2% | 7.72% | 0.1254 | 0 |
| entry_year | 2023 | 14 | $-1236.60 | $-88.33 | 64.3% | 17.30% | 0.1812 | 0 |
| entry_year | 2024 | 14 | $-1344.40 | $-96.03 | 78.6% | 11.24% | 0.0357 | 0 |
| entry_year | 2025 | 12 | $-689.40 | $-57.45 | 58.3% | 9.85% | 0.0497 | 0 |
| exit_year | 2018 | 11 | $-655.20 | $-59.56 | 45.5% | 10.48% | 0.1336 | 0 |
| exit_year | 2019 | 14 | $-1607.80 | $-114.84 | 35.7% | 17.20% | 0.1916 | 0 |
| exit_year | 2020 | 13 | $-1994.40 | $-153.42 | 38.5% | 25.21% | 0.2896 | 0 |
| exit_year | 2021 | 14 | $-1363.40 | $-97.39 | 50.0% | 13.12% | 0.1945 | 0 |
| exit_year | 2022 | 13 | $-150.80 | $-11.60 | 69.2% | 7.72% | 0.1254 | 0 |
| exit_year | 2023 | 14 | $-1283.60 | $-91.69 | 64.3% | 17.30% | 0.2216 | 0 |
| exit_year | 2024 | 14 | $-1309.40 | $-93.53 | 78.6% | 11.24% | 0.0297 | 0 |
| exit_year | 2025 | 13 | $-649.00 | $-49.92 | 61.5% | 9.09% | 0.0356 | 0 |

Subgroup P&L is closed-trade-only. The base and adverse-cost scenario are independent reruns and must not be added together. Regime/quote-spread bins are descriptive diagnostics, not entry/exit filters; EOD snapshots remain unverified execution proxies.

## Mark diagnostics

The zero/near-zero markability pattern from the initial run is explicitly surfaced below; use the new run to verify it is resolved rather than infer from workflow success alone.

`mark_status_counts`: {"CORE_TOTAL_RETURN_PRICE_MISSING": 11, "OK": 1684, "OK_ZERO_WING_BID_FLOOR": 263, "SHORT_ASK_MISSING_OR_NONPOSITIVE": 8, "SHORT_CONTRACT_ROW_MISSING": 5}

`first_mark_failure_samples`: [{"chain_present": false, "core_value_missing": false, "date": "2018-11-06", "mark_status": "SHORT_CONTRACT_ROW_MISSING", "position_expiry": "2018-11-30", "quote_rows": 0, "short_ask": null, "short_ask_below_wing_bid": null, "short_bid": null, "short_id": "QQQ181130C00179500", "short_quote_status": "CONTRACT_ROW_MISSING", "wing_ask": null, "wing_bid": null, "wing_id": "QQQ181130C00183000", "wing_quote_status": "CONTRACT_ROW_MISSING"}, {"chain_present": false, "core_value_missing": false, "date": "2020-06-23", "mark_status": "SHORT_CONTRACT_ROW_MISSING", "position_expiry": "2020-07-10", "quote_rows": 0, "short_ask": null, "short_ask_below_wing_bid": null, "short_bid": null, "short_id": "QQQ200710C00256000", "short_quote_status": "CONTRACT_ROW_MISSING", "wing_ask": null, "wing_bid": null, "wing_id": "QQQ200710C00262000", "wing_quote_status": "CONTRACT_ROW_MISSING"}, {"chain_present": false, "core_value_missing": false, "date": "2021-11-04", "mark_status": "SHORT_CONTRACT_ROW_MISSING", "position_expiry": "2021-11-29", "quote_rows": 0, "short_ask": null, "short_ask_below_wing_bid": null, "short_bid": null, "short_id": "QQQ211129C00401000", "short_quote_status": "CONTRACT_ROW_MISSING", "wing_ask": null, "wing_bid": null, "wing_id": "QQQ211129C00408000", "wing_quote_status": "CONTRACT_ROW_MISSING"}, {"chain_present": true, "core_value_missing": false, "date": "2023-12-28", "mark_status": "SHORT_ASK_MISSING_OR_NONPOSITIVE", "position_expiry": "2024-01-19", "quote_rows": 12496, "short_ask": 0.0, "short_ask_below_wing_bid": false, "short_bid": 0.0, "short_id": "QQQ240119C00426000", "short_quote_status": "BID_MISSING_OR_NONPOSITIVE", "wing_ask": 0.0, "wing_bid": 0.0, "wing_id": "QQQ240119C00435000", "wing_quote_status": "BID_MISSING_OR_NONPOSITIVE"}, {"chain_present": true, "core_value_missing": false, "date": "2023-12-29", "mark_status": "SHORT_ASK_MISSING_OR_NONPOSITIVE", "position_expiry": "2024-01-19", "quote_rows": 12924, "short_ask": 0.0, "short_ask_below_wing_bid": true, "short_bid": 0.0, "short_id": "QQQ240119C00426000", "short_quote_status": "BID_MISSING_OR_NONPOSITIVE", "wing_ask": 0.22, "wing_bid": 0.21, "wing_id": "QQQ240119C00435000", "wing_quote_status": "OK"}, {"chain_present": true, "core_value_missing": false, "date": "2024-01-02", "mark_status": "SHORT_ASK_MISSING_OR_NONPOSITIVE", "position_expiry": "2024-01-19", "quote_rows": 12206, "short_ask": 0.0, "short_ask_below_wing_bid": true, "short_bid": 0.0, "short_id": "QQQ240119C00426000", "short_quote_status": "BID_MISSING_OR_NONPOSITIVE", "wing_ask": 0.08, "wing_bid": 0.07, "wing_id": "QQQ240119C00435000", "wing_quote_status": "OK"}, {"chain_present": false, "core_value_missing": true, "date": "2025-12-16", "mark_status": "CORE_TOTAL_RETURN_PRICE_MISSING", "position_expiry": "2026-01-02", "quote_rows": 0, "short_ask": null, "short_ask_below_wing_bid": null, "short_bid": null, "short_id": "QQQ260102C00653000", "short_quote_status": "CONTRACT_ROW_MISSING", "wing_ask": null, "wing_bid": null, "wing_id": "QQQ260102C00665000", "wing_quote_status": "CONTRACT_ROW_MISSING"}, {"chain_present": false, "core_value_missing": true, "date": "2025-12-17", "mark_status": "CORE_TOTAL_RETURN_PRICE_MISSING", "position_expiry": "2026-01-02", "quote_rows": 0, "short_ask": null, "short_ask_below_wing_bid": null, "short_bid": null, "short_id": "QQQ260102C00653000", "short_quote_status": "CONTRACT_ROW_MISSING", "wing_ask": null, "wing_bid": null, "wing_id": "QQQ260102C00665000", "wing_quote_status": "CONTRACT_ROW_MISSING"}, {"chain_present": false, "core_value_missing": true, "date": "2025-12-18", "mark_status": "CORE_TOTAL_RETURN_PRICE_MISSING", "position_expiry": "2026-01-02", "quote_rows": 0, "short_ask": null, "short_ask_below_wing_bid": null, "short_bid": null, "short_id": "QQQ260102C00653000", "short_quote_status": "CONTRACT_ROW_MISSING", "wing_ask": null, "wing_bid": null, "wing_id": "QQQ260102C00665000", "wing_quote_status": "CONTRACT_ROW_MISSING"}]

`first_open_event`: {"budget_mode": "SOURCE_MAX_LOSS_0P8PCT_NAV", "commission_per_contract_per_side": 0.0, "date": "2018-03-02", "dte": 27, "event": "OPEN", "expiry": "2018-03-29", "gross_credit_per_share": 0.29000000000000004, "max_loss_per_spread_scenario": 371.0, "nav_for_sizing": 100385.58, "net_credit_per_share": 0.29000000000000004, "quantity": 2, "selection_signal_date": "2018-03-01", "short_delta": 0.15227, "short_id": "QQQ180329C00173000", "short_strike": 173.0, "slippage_per_leg": 0.0, "source_status": "OBSERVED_EOD_QUOTES / DERIVED_SIDE_PRICE_REPLAY; NOT_CONFIRMED_FILLS", "wing_delta": 0.05263, "wing_id": "QQQ180329C00177000", "wing_strike": 177.0}

## Hard limitations

- Contract IDs and expiry are selected from the signal-day chain and pinned; next session may reprice only the same exact IDs. A changed candidate set does not substitute a new contract.
- No same-close entry/exit: signals are carried forward to a later quote session.
- Stale/mixed quote dates are rejected; no quote forward-fill. Exact contract identity, root, same expiry, bid/ask and displayed sizes must be present.
- Non-standard/unparseable roots, crossed/invalid quotes and non-positive net credits block new positions.
- The 0.8% max-loss sizing scenario reproduces the inspected source-model budget setting; 1.2% NAV credit budget is a separate legacy-interpretation scenario, not assumed equivalent.
- Commissions ($0.00 / $0.65 per contract per side) and per-leg slippage are explicit scenarios, not verified broker fees or measured executions.
- No CAGR, daily MTM MaxDD, Sharpe or ES95 is claimed: source rows stop 2025-12-15, internal dates are missing, and EOD snapshots do not prove fills.
- VXX option history is not supplied here. This result covers only a QQQ-core plus QQQ far-call overlay research sleeve; it is not a full QQQ/VXX Hybrid strategy result.

## Reproducibility

All annual QQQ Parquet files and the underlying/universe/model/helper source pins must pass existing Git blob SHA/byte checks before this replay runs.
