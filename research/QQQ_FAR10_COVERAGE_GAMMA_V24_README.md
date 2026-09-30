# QQQ V24 Coverage-Gated Near Gamma

Research only. Not a live signal. V23 is NOT this contract.

Question
Can 10 persistent far FOTM short calls be fed by a harvestable near-month long gamma layer?

Frozen rules
- N_short = 10 always. Far short DTE 60-120. Stays open until DTE < 30 or High touches short strike.
- Coverage_t = sum_i q_i |Delta_near,i| / (10 |Delta_far|)
- If Coverage < 1: buy 1 near ATM (14-21 DTE) if q < 15.
- If Coverage > 2: sell 1 oldest near long (harvest).
- Rebalance on extreme-high signal days that fall inside the short's life.
- Singularity test: count days with Coverage < 1 after a harvest, and days with q_near = 0 while |10 Delta_far| > 0.5.
