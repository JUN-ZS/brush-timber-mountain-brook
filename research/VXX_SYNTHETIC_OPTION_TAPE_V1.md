# VXX Synthetic Option Tape V1

## Evidence class

`MODEL_DERIVED_VXX_OPTION_TAPE` is a research-only reconstruction.

It is **not** a historical VXX OPRA tape and must not be labelled LIVE,
OBSERVED, or EXECUTED. The purpose is to answer structural questions when the
repository has VXX/VIX spot history but no historical VXX option chain.

## Observed inputs

1. `attachments/spots_qqq_vxx_vix.1csv` — observed QQQ/VXX/VIX daily history.
2. Canonical QQQ option data — observed historical QQQ bid/ask/delta/IV where available.
3. Canonical QQQ underlying data — used for QQQ realized volatility.

## Model construction

The model is intentionally layered:

```text
VXX spot + causal RV20/RV60
        + VIX level / causal regime
        + QQQ observed option surface (lagged one observation)
        ↓
VXX ATM IV
        ↓
VXX call/put wing + tail skew
        ↓
Black-Scholes price + Greeks
        ↓
QQQ-informed liquidity envelope → Bid / Ask
```

The four surface families are deliberately separated rather than fitted to
P&L:

- `CONSERVATIVE`
- `CENTRAL`
- `HIGH_SKEW`
- `STRESS`

The same observed underlying path is used for all four.

## Causality lock

All rolling volatility inputs are shifted one observation before use.
The QQQ option reference surface is also shifted one observation. Therefore a
same-day VXX synthetic price cannot use same-day QQQ option information.

## Quality gates

The runner must reject the tape if any of the following fail:

- every row is explicitly `MODEL_DERIVED_VXX_OPTION_TAPE`;
- `bid <= mid <= ask` and quotes are non-negative;
- IV stays inside the declared model bounds;
- every expiry is strictly after the trade date;
- finite IV / delta / gamma / vega / theta;
- calibration source date is strictly earlier than trade date;
- call prices decrease with strike inside each date/expiry;
- put prices increase with strike;
- call delta decreases with strike;
- put delta increases with strike;
- every family/date state is represented exactly once.

## Two-runner verification

The workflow intentionally uses both available self-hosted runner classes:

- Windows x64 builds the complete tape and uploads the manifest/artifact.
- Linux x64 independently rebuilds and must match the Windows canonical
  fingerprint.

This catches platform-dependent numerical or serialization drift before the
synthetic tape is allowed into later research.

## Important interpretation

The canonical fingerprint proves reproducibility of **our model**, not truth
of the historical VXX tape.

The next research stage should compare Hybrid outcomes across all four surfaces,
keeping V22 strategy logic frozen and keeping this synthetic VXX layer outside
the strategy's source of truth.
