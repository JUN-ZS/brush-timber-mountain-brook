# V20 — N+50 One-and-Done
Question: what 1 x ITM-ish long call versus N x FOTM short calls gives the highest observed win rate?
The test preserves the existing QQQ signal, earliest 18-35 DTE expiry selection, 30-day max lifecycle, and 10-calendar-day signal cooldown.
Long call targets: 60/70/80/90 delta. Short call targets: 1/2/3/5/8/10 delta, strictly above long strike.
N: 2/3/4/5/8/10/15/20/30/40/50.
Entry is long Ask minus N x short Bid. Exit is the existing BASELINE_TOUCH rule: first post-entry underlying High touching the selected short strike, else 30 days or expiry, using executable Bid/Ask.
WIN = realized P&L > 0. The matrix reports win rate, P&L distribution, profit factor, longest win streak, and empirical 10-WIN completion rate.
No BS, interpolation, optimization, or 2% risk gate is used; risk is reported through P&L/worst-loss rather than used to filter the win-rate question.


CI execution trigger: base workflow installed on V19 research branch.
