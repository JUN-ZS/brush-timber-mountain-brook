# QQQ PROFIT RECYCLE LOOP V6

The hypothesis is path-dependent:

previous realized P&L -> opportunity credit -> next-cycle ratio -> next realized P&L.

With the existing base N=2:
- seed cycle: N+50 = 52 short-call/wing pairs against 1 ATM Long Call
- after realization: opportunity credit = max(0, prior credit + realized P&L)
- next eligible signal may use N+20 = 22 pairs only when the credit covers the incremental max-loss proxy from N=2 to N=22
- otherwise it reverts to N=2

The opportunity credit is a risk/decision ledger, not extra NAV.

The same signal conditions, DTE selection, historical Bid/Ask execution, daily Mid mark, 2% risk gate, and cooldown are retained.

No Black-Scholes, interpolation, optimization, or look-ahead.
