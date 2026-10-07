# QQQ Hybrid Broker Reconciliation V1

Independent read-only cross-check between:

    Broker Import V1 canonical events
                    |
                    v
          reconstructed positions / cash
                    |
                    v
          current Futu OpenD REAL
          positions + USD cash

This increment sits after Broker Import V1 and before any Ledger adapter.

## Hard boundaries

- Futu OpenD REAL read-only only.
- No order placement, modification, cancel, or unlock.
- No automatic Ledger append.
- No V3 strategy changes.
- No invented starting cash.
- Position matching uses broker-side trade direction semantics preserved by Broker Import V1.
- Cash matching is exact only when a USD opening-cash anchor exists and no cash-impacting row remains quarantined.

## Why position reconstruction uses the original Futu trade side

The canonical Ledger vocabulary maps:

    BUY        -> BUY
    SELL       -> SELL
    SELL_SHORT -> SELL
    BUY_BACK   -> BUY

That mapping is appropriate for the existing Ledger generic BUY / SELL contract, but it is not enough by itself to distinguish long from short position exposure.

This reconciler therefore uses the preserved sourceTradeSide:

    BUY        -> LONG + qty
    SELL       -> LONG - qty
    SELL_SHORT -> SHORT + qty
    BUY_BACK   -> SHORT - qty

The current broker snapshot is read with position_list_query, including position_side and qty. The result is compared by symbol plus LONG or SHORT rather than collapsing long and short exposure into one signed number.

Futu documents position_list_query as the holding-position interface; its returned quantity is holdings quantity, and option/future quantities are in contracts.

## Cash reconstruction boundary

Futu accinfo_query provides current fund data, including currency-specific USD cash. The reconciler never treats current cash as a historical opening balance.

With an opening USD cash anchor:

    expectedCash
      = openingCash
      + known fill cash effects
      + explicit CASHFLOW
      + DIVIDEND
      + INTEREST
      + BORROW_FEE

Fill cash effect:

    BUY / BUY_BACK:
      -(qty * price * multiplier) - fees

    SELL / SELL_SHORT:
      +(qty * price * multiplier) - fees

Trade settlement audit rows are not added again.

A non-zero quarantined cash row blocks exact cash parity because its economic effect has not been given an explicit accounting contract. This deliberately prevents silent treatment of taxes, fees, transfers, assignment, expiry, corporate actions, FX, and other ambiguous cash effects.

Without an opening cash anchor, the result is NEEDS_OPENING_CASH rather than a guessed balance.

## Output

The report is broker_import_..._reconcile.json and contains:

- current broker position and fund evidence,
- reconstructed position buckets,
- position comparison rows,
- known cash reconstruction,
- the exact reason when cash cannot be declared reconciled,
- readOnly=true,
- ordersPlaced=false.

## Windows CMD

First run Broker Import V1:

    cd C:\path\to\brush-timber-mountain-brook\research\qqq_hybrid_broker_import_v1
    RUN.cmd 2026-09-01 2026-10-06 US America/New_York 123456

Then reconcile current Futu position and cash:

    cd C:\path\to\brush-timber-mountain-brook\research\qqq_hybrid_broker_reconcile_v1
    RUN.cmd C:\path\to\broker_import_2026-09-01_2026-10-06.json 123456

With a known USD opening cash anchor:

    RUN.cmd C:\path\to\broker_import_2026-09-01_2026-10-06.json 123456 OPENING_CASH=50000

The reconciler refreshes OpenD position and fund cache by default. Use the no-refresh option only when cached broker data is explicitly desired.

## Source-of-truth rule

A MATCH is a current broker-versus-history observation from the same account identifier and real trading environment. It is not proof that an arbitrary history range contains every event ever executed.

A mismatch can represent missing history, a broker-event normalization problem, or a true accounting discrepancy. The report keeps those possibilities visible instead of forcing a conclusion.

## Next boundary

Only after this read-only broker cross-check is stable should a separate adapter translate READY_FOR_LEDGER canonical events into the existing Ledger FILL or CASHFLOW contract.

Complex events remain outside that adapter until explicit accounting contracts exist.
