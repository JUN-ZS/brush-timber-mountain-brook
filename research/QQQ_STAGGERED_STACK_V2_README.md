# QQQ STAGGERED STACK V2

## Purpose

V1 tested dynamic strike migration inside one option vintage. V2 isolates a different dynamic hypothesis: **cross-date overlapping vintages**.

The strategy does not search or optimize parameters.

## Frozen per-vintage package

`+1 ~50Δ Call -2 ~20Δ Calls +2 ~8Δ Call Wings +1 ~25Δ Long Put -1 ~10Δ Short Put`

Each vintage keeps its own expiry and geometry until its normal exit (30 days maximum or expiry).

## Cross-date stacking

Every qualifying original signal date becomes a candidate new vintage.

Three fixed structural modes are replayed:

- `1_LAYER_NO_OVERLAP`: one simultaneous vintage, 100% capital.
- `2_LAYER_HALF_STACK`: up to two simultaneous vintages, 50% capital per vintage.
- `4_LAYER_STACK`: up to four simultaneous vintages, 25% capital per vintage.

No global cooldown is applied. When a slot is free, the next qualifying signal may open a new vintage. Older vintages remain alive.

## Tail interpretation

Each live vintage retains its own Long Put and Short Put. Therefore stacking naturally creates multiple dated tail layers rather than migrating or deleting the existing Long Put.

## Execution

Historical QQQ option chain only.

- Entry: executable Bid/Ask.
- Daily MTM: Mid.
- Exit: executable Bid/Ask.
- No Black-Scholes.
- No interpolation.
- No parameter optimization.
- No look-ahead.

## Accounting

The portfolio starts at USD 100,000.

In K-layer mode, each admitted vintage uses USD 100,000 / K of portfolio capital. Its 100k-normalized daily MTM curve is scaled into the portfolio NAV. At exit, realized value returns to cash.

This produces a continuous portfolio curve with overlapping vintages and explicit active-layer counts.

## Interpretation

This test answers a narrower question than V1:

> Does the effect of the QQQ option package change when option vintages are allowed to overlap across dates, creating a staggered tail/premium stack?

It does **not** test within-vintage strike migration. That remains static here.
