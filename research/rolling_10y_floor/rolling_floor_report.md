# Rolling 10Y Capital-Floor Controller

Data end: **2026-09-04**

## Architecture

- 10Y = fixed terminal horizon.
- 20/30/50Y = parallel historical-context trap scales; 10Y is only the terminal target horizon.
- Analog futures are admitted only after their own 10Y future has matured.
- Scale disagreement is preserved; it reduces signal authority instead of being averaged away.
- Clock is the hard backstop: remaining cash is forced into equal catch-up slices as the deadline approaches.
- QQQ outcome is the observed target path. NDX and NASDAQ Composite are price-only context proxies.

## Replay

Coupled replays: **153**
Coupled non-loss rate: **100.0%**
Coupled 5% terminal quantile: **2.0571**
Coupled worst terminal: **1.9801**
Coupled worst MaxDD: **-32.6%**

Clock-only non-loss: **100.0%**
Lump-now non-loss: **100.0%**

## Current (repo data as-of)

Robust signal target at phase 0: **100.0%**
Cross-scale agreement: **100.0%**
Divergence state: **CONVERGENT**
First-month minimum by clock: **0.833%**
First injection from coupled rule: **100.00%**

## Important limitation

This is a research controller, not a guarantee. NDX/NASDAQ Composite proxy channels are price-index histories, while the scored target is the observed QQQ path. The current repo's QQQ data begins in 2004, so the number of independent 10Y start regimes is limited.
