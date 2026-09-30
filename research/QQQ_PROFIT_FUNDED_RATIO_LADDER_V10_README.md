# QQQ PROFIT-FUNDED RATIO LADDER V10

Base package remains N=2.

After each realized trade, only the immediately previous positive realized P&L may fund extra short-call/wing pairs on the next signal. The next N is:

N = 2 + k, 0 <= k <= 20

where k is the largest integer whose incremental defined-loss proxy versus N=2 is less than or equal to the prior positive realized P&L.

Thus the loop can use N+20 when the previous profit is large enough, but otherwise uses a smaller incremental opportunity instead of all-or-nothing N+20.

The existing 2% risk gate still applies to the selected total N.

No look-ahead, Black-Scholes, interpolation, or parameter fitting.
