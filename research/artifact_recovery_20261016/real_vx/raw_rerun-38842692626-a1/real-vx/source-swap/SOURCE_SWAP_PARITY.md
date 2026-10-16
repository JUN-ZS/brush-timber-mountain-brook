# VX SOURCE-SWAP PARITY — OLD EXTERNAL vs REAL CBOE

Status: DIAGNOSTIC / SOURCE-SWAP

Same spot inputs; only the M1/M2 source changes.

| Metric | Result |
|---|---:|
| Overlap rows | **1036** |
| Term-sign agreement | **99.421%** |
| Archive-state agreement | **99.517%** |
| Archive-action agreement | **99.517%** |
| VXX-carry agreement | **99.517%** |
| Term-sign mismatches | **6** |
| State mismatches | **5** |
| Action mismatches | **5** |

Interpretation:
1. Only M1/M2 source is changed.
2. High agreement means this recovered policy is relatively insensitive to the exact M1/M2 point values over the measured overlap.
3. This is not a CAGR proof.
4. No parameter search or threshold tuning is performed.

Outputs: source_swap_metrics.json, source_swap_rows.csv
