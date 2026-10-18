# Cash-flow-aware ten-year outcomes (research only)

## Why this exists

An ending balance alone is not a useful comparison when money is repeatedly taken out or put back in. This calculator keeps four different quantities separate:

1. **Ending NAV** still invested after the last scheduled cash flow.
2. **Actual cash withdrawn** and **unpaid withdrawal demand** (shortfall).
3. **Additional deposits** made after the initial USD 100,000.
4. **Investor XIRR**, which includes the dates and actual amounts of initial capital, later deposits, paid withdrawals, and ending NAV.

A nominal accounting cross-check is also reported: actual withdrawals + ending NAV - additional deposits - initial capital. It is not time-adjusted; XIRR is the dated cash-flow return.

## Historical comparison

The default scenario grid replays 120-month windows for QQQ and SPY at nominal monthly withdrawals of USD 0, 250, 500, 1,000, 1,500 and 2,000. Each window begins with USD 100,000 fully invested at the initial monthly close. For each subsequent month, monthly-close price return is applied first, then the month's external cash-flow events are processed at that close. Maximum drawdown uses the full available daily price marks between the monthly window endpoints, so an intramonth selloff is not hidden by month-end sampling. The rolling windows overlap; counts are historical sample counts, not independent trials or forward probabilities.

The input file is SHA-pinned. If the market data changes, the program fails closed until a deliberate source review and re-pin occurs.

## Provide your own add/withdraw rhythm

Optional --flows-csv uses relative month numbers shared by every replay window. For example, save the following as a CSV file:

    month_index,flow_type,amount_usd,note
    3,withdrawal,1200,spending
    9,deposit,5000,put money back
    10,withdrawal,800,spending
    24,deposit,2500,top-up
    120,withdrawal,1000,final month spending

- month_index ranges from 1 to 120; month 1 means the first monthly close after initial investment.
- flow_type is deposit or withdrawal; amount_usd is always a positive magnitude.
- Deposits increase invested NAV and are negative investor cash flows.
- A withdrawal is paid only up to available NAV. Any unpaid part is a visible shortfall; NAV is never allowed to become negative.
- When multiple rows share a month, file order defines their order.
- The same schedule is replayed on each historical start date. It is a sensitivity analysis of a cash-flow pattern, not a prediction of your future withdrawals.

## Run

    python3 research/audit_stage2/cashflow_aware_qqq_spy.py \
      --input artifacts/pulse_v2/data_market_data.csv \
      --out /tmp/cashflow_summary.json \
      --rows-out /tmp/cashflow_windows.csv

Append --flows-csv path/to/my_schedule.csv to use a custom pattern instead of the default fixed-withdrawal grid.

## Boundaries

- The pinned source is a **price series**, not a dividend-reinvested total-return series. Dividends are excluded.
- The run assumes zero transaction costs, zero taxes, zero cash interest and no leverage or options.
- Additional deposits are invested at that month's close; external flows happen after that month's market return.
- XIRR is searched from -99.9% to +1,000% annualized. No-root or multiple-root cash flows remain explicitly status-coded; they are not filled with zero or a chosen root.
- The underlying price CAGR and MaxDD describe the asset path, not the user's actual spending capacity. Actual cash paid, ending NAV and shortfall must be read together.
- No strategy is declared a winner by a CAGR threshold. This tool is a baseline for withdrawal-aware comparisons, not a deployment recommendation or broker integration.
