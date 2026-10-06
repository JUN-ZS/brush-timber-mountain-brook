# RESEARCH CONTRACT

## RECONSTRUCTION FIRST
The first gate is forensic reconstruction, not optimization.

Same timestamp + same normalized inputs must produce the same LIVE and REPLAY decision.
Mismatch = RECONSTRUCTION FAILURE.
Do not solve mismatch by tuning.

## REQUIRED CHAIN
RAW MARKET DATA
→ FEATURE VECTOR
→ STATE
→ LOCKED POLICY
→ TARGET POSITIONS
→ CURRENT→TARGET DELTAS
→ ACTION
→ EXECUTION MODEL
→ P&L
→ EQUITY CURVE

## DATA LABELS
OBSERVED = observed source record
DERIVED = deterministic calculation
ESTIMATED = model/calibration estimate
HYPOTHETICAL = assumed scenario

Every material field should carry provenance.

## NO LEAKAGE
Only information available by the replay timestamp may be used.
No future contract selection, IV, state, outcome, split state, or trade result may leak backward.

## POSITION SIZING
For defined-risk spreads:
N_t = floor(NAV_t * risk_fraction / max_loss_per_contract_t)

Never keep option lot count fixed across split-adjusted historical series.

## M1/M2 MASK TEST
Use the real M1/M2 dataset as truth.
Mask M1/M2.
Run the historical reconstruction method.
Compare:
1. M1 error
2. M2 error
3. S_t error, S_t=(M2-M1)/M1
4. regime agreement
5. action agreement
6. strategy/P&L impact

## VALIDATION ORDER
Exact replay
>
masked reconstruction
>
walk-forward/OOS
>
stress/bootstrap
>
Monte Carlo distribution

Monte Carlo does not validate the generator.

## EVOLUTION
Only after reconstruction is stable may strategy family, weights, DTE, leg ratios, cash, or triggers mutate.
Every mutation must be versioned and tested on unseen data.

## LIVE
Missing one feed constrains only decisions that depend on it.
Existing risk can still be monitored or reduced when independent evidence supports it.
