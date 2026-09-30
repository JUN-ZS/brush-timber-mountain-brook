# QQQ Universal Harvest Bank V18

Research only. Not a live signal. Do not merge into V2.2. Do not add this to PR #32.

User sentence frozen:

- N+ = WIN Generator, not win-rate hunter
- After one Risk WIN: Bank → slowly 撢 N / buy other real-chain rights
- Later positive P&L must **not** mix into the isolated Bank
- Question: one WIN → how many future strategy opportunities?

## Bank

```
Seed Bank_0 = one isolated realized WIN (V16 path, N>2 and P>0)
ISOLATED (authoritative):
  P+ later = ignored
  P- later = consumes Bank
  Bank = max(0, Bank + min(0, P))
REPLENISH (contamination comparator only):
  Bank = max(0, Bank + P)
```

A candidate right `S_i` starts only if `ΔR_i ≤ Bank`.
One active opportunity. 10-calendar-day gap after each exit.
Tie-break frozen: earlier entry date, then `CONVEXITY_SHOCK`, then `RATIO_HARVEST_N2`.
Bank is risk currency, not NAV / cash collateral.

## Strategy nodes this take

| Status | Node | Chain |
| --- | --- | --- |
| ADMITTED | RATIO_HARVEST_N2 | real Bid/Ask |
| ADMITTED | CONVEXITY_SHOCK | real Bid/Ask |
| REGISTERED, not executed | Short-only, Staggered, State Adaptive | real-chain exists, no ΔR wired here |
| EXCLUDED | Hybrid Dynamic Deployment | Derived BS/VIX |

## What this run may answer

1. One isolated WIN → how many later rights, of which strategies, over how many days?
2. Does REPLENISH inflate that count? If yes, that inflation is contamination, not 一世.

N=10 seed on the V16 path was a loss. Seeds here are later N>2 wins. That is declared, not hidden.
