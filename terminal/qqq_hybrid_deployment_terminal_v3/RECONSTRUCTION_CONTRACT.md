
# V3 Reconstruction / Decision Contract

## One brain

LIVE and REPLAY must normalize inputs and call the same decision rules.

## Required normalized fields

- timestamp
- data_asof
- QQQ
- VXX
- VIX
- M1 symbol
- M1 expiry
- M1 price
- M2 symbol
- M2 expiry
- M2 price
- S_t = (M2-M1)/M1
- term_source
- provenance
- current position ledger
- policy version
- engine version
- state
- target positions
- action
- reason

## No leakage

No future outcome, future option quote, future contract identity, or future state may enter a decision at timestamp t.

## Term source contract

REAL Cboe delayed:
- Cboe public delayed implementation endpoint
- strict standard-monthly filter
- expiry > as-of
- sort by actual expiry

OpenD:
- full-size VX monthly discovery via contract expiry
- snapshot prices

Manual:
- explicitly TEST_ONLY
- never labelled OBSERVED

## Data state

FRESH:
source as-of is current enough for the user's 1–2 day operating cadence.

STALE:
source is older than the configured maximum age.

MIXED:
QQQ/VXX/VIX and VX term data have materially different as-of timestamps.

BLOCKED:
term structure unavailable or incomplete.

BLOCKED means:
CURRENT = TARGET
NO NEW DEPLOYMENT ACTION
NO AUTOMATIC REDUCE

## Baseline policy

Original Hybrid baseline is immutable in V3:

- QQQ core budget: 42%
- VXX seller target: 18% when VIX < 28
- VXX seller target: 10% when VIX >= 28
- VXX call sleeve: 2% in CARRY
- QQQ far-call sleeve: 1.2% in CARRY
- term safe line: S > 5%
- backwardation: seller carry is cut
- high VIX: seller exposure capped / reduced
- QQQ core is preserved through VXX shock handling

These are baseline policy constants, not optimized live parameters.

## Important

V3 improves the terminal/data path. It does not assert that the historic 12.7049% CAGR has been fully reconstructed.
