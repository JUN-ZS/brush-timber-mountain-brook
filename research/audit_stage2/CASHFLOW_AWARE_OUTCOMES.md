# Ten-year outcomes with an explicit nominal capital floor

## Investor objective

The default investor starts with USD 100,000 and makes no external deposits or withdrawals unless a cash-flow schedule is supplied. The first question is not "how much remains after assumed monthly spending?" It is:

**Can a maturity-matched nominal principal floor be protected at year 10, while the remaining capital seeks higher return?**

The report keeps the terminal value of the protected floor and the performance of the growth sleeve separate. It deliberately does not promise a 10% CAGR: a nominal maturity floor and high growth are competing constraints, so upside is measured as a distribution, not declared in advance.

## Default no-withdrawal replay

With no --flows-csv and no --withdrawal-grid, the program compares:
- QQQ buy-and-hold price-path control;
- SPY buy-and-hold price-path control;
- a nominal maturity floor plus the remaining balance in zero-yield cash;
- the same floor plus the remaining balance in QQQ;
- the same floor plus the remaining balance in SPY;
- the same floor plus an unlevered 50/50 QQQ/SPY growth sleeve.

The fixed-withdrawal sensitivity grid is **opt-in** via --withdrawal-grid; it is never assumed to represent the user's actual spending. For an irregular pattern of taking money out and putting money back in, supply --flows-csv with relative-month events.

## Indicative principal-floor sizing

The default scenario protects a nominal USD 100,000 maturity payment. Its illustrative purchase-cost placeholder is calculated from the official 10-year Treasury par yield of 5.09% on 2026-10-16 using semiannual compounding:

100,000 / (1 + 0.0509 / 2)^20 = USD 60,493.71

That leaves an indicative USD 39,506.29 growth sleeve. This is **not an executable STRIPS quote**: the Treasury par yield is not the zero-coupon yield or ask price of a specific maturity-matched STRIPS CUSIP. Replace it with an actual quote and include purchase fees, tax/phantom-income reserve and any other cash costs before treating the floor as investable.

Treasury STRIPS are zero-coupon securities that make a single payment at maturity and are bought through an eligible financial institution, broker or dealer. The modeled floor pays its face value only at the horizon. It is not daily marked-to-market, not liquid spending capacity before maturity, and not a promise that the whole portfolio value cannot fall below USD 100,000 at interim dates.

The default floor calculation excludes taxes, transaction costs and tax payments from the protected payment. If those must be paid from the same USD 100,000 pool and cannot be paid externally, the floor face value or separate reserve needs to be sized to cover them; don't label the illustrative model as net-of-tax principal protection.

## Historical comparison method

The pinned daily CSV is converted to 331 month-end observations from 1999-03-31 through 2026-09-03, producing 211 overlapping 120-month windows. Market returns and scheduled cash flows use month-end prices. Maximum drawdown for the unprotected QQQ/SPY control uses daily marks within each 10-year window, so an intramonth selloff is not hidden by month-end sampling.

The floor-plus-growth outcomes use the exact same 211 windows for the growth-sleeve price multiple:
- QQQ-only growth;
- SPY-only growth;
- unlevered 50/50 QQQ/SPY;
- zero-yield cash control.

At the endpoint, total scenario wealth is modeled as floor face payment + remaining growth sleeve value. The principal-floor claim is about the matched security's nominal maturity payment, conditional on holding it to maturity and not drawing its protected value to fund spending. It is not derived from historical QQQ returns and cannot be treated as proof of a historically executable bond strategy.

## Optional personal cash-flow schedule

For custom deposits/withdrawals, pass --flows-csv with month_index,flow_type,amount_usd,note. There is no assumed withdrawal frequency or amount; the only events are the rows you supply. Example: no withdrawals for the first full year, then a stepped-up annual amount:

    month_index,flow_type,amount_usd,note
    13,withdrawal,1000,after first full year
    25,withdrawal,1250,step up
    37,withdrawal,1500,step up
    49,withdrawal,1750,step up
    61,withdrawal,2000,step up
    73,withdrawal,2000,hold amount
    85,withdrawal,1500,reduce spending
    97,deposit,5000,optional later top-up
    108,withdrawal,1800,irregular event

Those amounts are **illustrative test values only**, not a spending recommendation or a default. You can change the months, add irregular events, skip entire years, reduce/raise amounts, or add a later deposit.

Month indices range from 1 to 120. Amounts are positive; flow_type is deposit or withdrawal. Same-month rows are processed in file order. For the unprotected QQQ/SPY baseline, a withdrawal is paid only up to available account NAV. For floor-plus-growth scenarios, the maturity-floor bond is locked; deposits are invested at the growth sleeve's target weights, and withdrawals are paid pro-rata from the growth sleeve only. Any unpaid withdrawal amount is recorded as a shortfall; the model never silently raids the protected maturity payment.

Deposits are negative investor cash flows; paid withdrawals and final portfolio value (including the maturity-floor payment) are positive investor cash flows for XIRR. With a custom schedule, the same relative-month events are replayed over each historical 120-month start window. This tests how the same timing pattern would have behaved across different start dates; it is not a forecast of future spending needs.

## Run commands

Default: no withdrawals, includes the nominal floor:

    python3 research/audit_stage2/cashflow_aware_qqq_spy.py \
      --input artifacts/pulse_v2/data_market_data.csv \
      --out /tmp/cashflow_summary.json \
      --rows-out /tmp/cashflow_windows.csv

Opt in to fixed withdrawal sensitivities:

    python3 research/audit_stage2/cashflow_aware_qqq_spy.py \
      --input artifacts/pulse_v2/data_market_data.csv \
      --out /tmp/cashflow_sensitivity.json \
      --rows-out /tmp/cashflow_sensitivity.csv \
      --withdrawal-grid

Supply a specific floor instrument all-in purchase cost once available:

    python3 research/audit_stage2/cashflow_aware_qqq_spy.py \
      --input artifacts/pulse_v2/data_market_data.csv \
      --out /tmp/floor_quote_sensitivity.json \
      --rows-out /tmp/floor_quote_sensitivity.csv \
      --floor-cost-usd 61234.56

## Evidence and interpretation limits

- The input is SHA-pinned; it fails closed if market data changes without an explicit re-pin.
- The source is price-only, not a dividend-reinvested total-return series.
- No stock transaction costs, taxes, cash yield, options, leverage or live orders are modeled.
- Rolling windows overlap; historical window fractions are not independent trials or forward probabilities.
- Terminal CAGR is a scenario statistic; the median or best result is not a forecast.
- The maturity-floor scenarios don't calculate daily bond market value or liquidity; a bond can be worth less than its face before maturity when market yields move.
- This model reports nominal USD preservation only. Inflation-adjusted purchasing power is a separate goal.
- It does not declare any strategy a winner based on a fixed CAGR threshold. The next strategy must show incremental after-cost upside without spending or risking the protected floor.
