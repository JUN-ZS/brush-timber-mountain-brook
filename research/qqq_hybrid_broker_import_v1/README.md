# QQQ Hybrid Broker Import / Event Normalization V1

Separate source-adapter layer for turning Futu OpenD history into canonical accounting events.

## Purpose

This layer does not change the existing Ledger or V3 strategy. It answers:

> What did the broker actually report, and how can we translate it without inventing accounting semantics?

Pipeline:

    Futu historical deals
          + order-level fees
          + account cash-flow records
                    |
                    v
          Broker Event Normalizer
                    |
          +---------+-----------+
          |                     |
       canonical            quarantine
        events          ambiguous / unsupported
          |                     |
          v                     v
      future Ledger          manual review

## Futu source-of-truth choice

For executed trades, this layer uses historical deals rather than historical orders. Futu documents history_deal_list_query as the historical executed-trade interface and returns deal_id, order_id, code, qty, price, trd_side and create_time. The documented historical deal interface is for live trading accounts, not paper trading.

Order fees are fetched separately with order_fee_query. Futu reports fee_amount as the total fee for an order and allows up to 400 order IDs per request. Therefore one order with multiple fills cannot safely have the full order fee copied onto every fill.

Rule:

    one order -> one fill + fee present
        => FILL accountingStatus READY

    one order -> multiple fills + only order-level fee
        => every FILL INCOMPLETE_FEE_ALLOCATION
        => no guessed split

Missing fee data likewise remains INCOMPLETE.

## Cash-flow anti-double-count rule

Futu account cash flow records cover deposits, withdrawals, transfers, currency exchange, asset purchases/sales, margin interest and securities-lending interest.

That means a cash-flow row is not automatically an external cash contribution. In particular, trade settlement must not be imported as a second CASHFLOW because the trade is already represented by FILL cash accounting.

Only explicit deposit / withdrawal classification becomes CASHFLOW.
Ambiguous transfers become ACCOUNT_TRANSFER and remain quarantined until account mapping proves their externality.
Fee / commission / tax cash rows remain quarantined until there is a deduplication link to the exact charge source.

## Canonical event types

- FILL — executed broker deal.
- CASHFLOW — explicit external cash contribution or withdrawal classification.
- DIVIDEND — dividend cash event.
- INTEREST — financing / margin interest.
- BORROW_FEE — securities lending / borrow cost.
- FEE — broker fee / commission / tax charge; currently quarantine-first because deduplication against order fees must be explicit.
- ACCOUNT_TRANSFER — account-to-account transfer with unknown externality.
- FX_CONVERSION — currency conversion; quarantine until multi-currency accounting exists.
- ASSIGNMENT — option assignment / exercise detection; quarantine until contract-to-position transformation is explicit.
- OPTION_EXPIRY — option expiry detection; quarantine until outcome semantics are explicit.
- CORPORATE_ACTION — split / merger / spinoff detection; quarantine until security mapping is explicit.
- TRADE_SETTLEMENT_AUDIT — broker cash movement attributable to trading; quarantine to prevent double-counting.

Unknown records never get a guessed type. They become quarantine evidence.

## Time semantics

Futu deal timestamps can be returned without an offset. The importer therefore requires an explicit IANA timezone, converts broker-local deal time to UTC, and stores the exact source timezone in provenance. This avoids machine-local parsing and handles daylight-saving changes correctly.

Cash-flow records are date-oriented in the documented API, with clearing date and settlement date. The normalizer preserves those dates rather than inventing a clock time.

## Read-only importer

futu_import.py connects to OpenD only for history reads. It does not call any order-placement or order-modification API.

Example Windows CMD:

    cd C:\path\to\brush-timber-mountain-brook\research\qqq_hybrid_broker_import_v1
    python futu_import.py --start 2026-09-01 --end 2026-10-06 --market US --timezone America/New_York --acc-id 123456 --with-cashflows

The output is a broker_import_YYYY-MM-DD_YYYY-MM-DD.json bundle containing raw broker evidence plus normalized events and quarantine records.

Cash-flow queries are deliberately throttled because Futu documents a per-account request limit. The importer queries clearing dates one day at a time and defaults to 1.6 seconds between weekday requests.

## Current accounting boundary

This increment intentionally does not teach the existing Ledger how to apply new event types.

Not yet applied to Ledger:

    ASSIGNMENT
    OPTION_EXPIRY
    CORPORATE_ACTION
    FX_CONVERSION
    ACCOUNT_TRANSFER
    broker FEE rows

Those require separate accounting contracts because they can transform positions, currencies, tax basis, or cash treatment. They must not be silently encoded as generic CASHFLOW.

DIVIDEND / INTEREST / BORROW_FEE are normalized as their own event types but remain outside the current Ledger apply contract until their accounting effects and source deduplication are explicitly wired.

## Provenance

Every normalized event carries broker, source API, source record ID, source order ID when available, import timestamp and timezone provenance.

Raw broker records stay in the evidence bundle. Canonical events are a derived representation.

## Safety

    broker read -> normalize -> quarantine / review

not:

    broker read -> auto-order

Broker order submission remains disabled. V3 strategy policy remains untouched.

## CI evidence rule

A broker-import change is considered validated only by the GitHub Actions run attached to the current branch head. A cancelled or stale-head run is not evidence for the current head.


## Broker trade-side normalization

Futu trade directions are normalized to the existing Ledger's BUY / SELL vocabulary without losing the broker-side meaning:

    BUY        -> BUY
    SELL       -> SELL
    SELL_SHORT -> SELL   (opens / increases a short position)
    BUY_BACK   -> BUY    (closes / reduces a short position)

The original broker direction is retained in provenance. This avoids treating a legitimate short-open or buy-back deal as an unknown side while keeping the existing Ledger position sign contract unchanged.
