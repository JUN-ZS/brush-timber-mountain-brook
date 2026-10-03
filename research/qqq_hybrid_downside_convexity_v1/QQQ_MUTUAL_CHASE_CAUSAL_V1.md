# QQQ_MUTUAL_CHASE_CAUSAL_V1

Status: RESEARCH_ONLY / DIAGNOSTIC_ONLY.

This is an independent research layer on PR #77. It does not modify the formal 10Y Floor and does not create funding, BUY, ADD, SELL, broker, or withdrawal authority.

## Research question

The earlier DIP study asks whether future clock slices should be pulled forward after a drawdown.

This study asks a different question:

> Can prior investment performance itself change the amount of future external capital required, so that a gain can reduce later contributions and a loss can increase later contributions?

This is the causal "mutual-chase" idea.

## Fixed rule

Let planned principal be B = 1 for normalized research.

The monthly capital target is:

C_t = B * t / 120.

At month t:

1. Read only NAV at the previous month-end.
2. Compute the shortfall to the current target.
3. Contribute exactly the positive shortfall.
4. Cap cumulative external contributions at B.
5. Buy QQQ at month t close.
6. Mark the resulting account NAV at that same month-end.

Formally:

Contribution_t =
min(B - cumulative_contributions_{t-1},
    max(0, C_t - NAV_{t-1})).

The unspent balance:

Reserve_t = B - cumulative_contributions_t

remains outside the investment account.

Therefore:

EconomicWealth_t = NAV_t + Reserve_t.

A skipped contribution is NOT destroyed capital; it remains reserve.

## Why this is different from DIP

DIP moves an already-planned future slice earlier.

Mutual chase changes the amount of future external capital required based on prior realised performance.

Example:

- If month 1 produces a gain, NAV_1 can rise above C_2, so month 2 contribution becomes 0.
- If month 1 produces a loss, NAV_1 can fall below C_2, so month 2 contribution becomes greater than the normal clock slice.

No future price is read at the contribution decision.

## Fair comparison

CLOCK contributes B/120 every month and ends with zero reserve.

MUTUAL_CHASE can contribute less than B if investment gains cover future capital targets. It is therefore evaluated on both:

- account NAV / account MaxDD;
- whole economic wealth = account NAV + reserve / economic-wealth MaxDD.

This prevents an invalid conclusion that "return improved" merely because less capital was invested.

## Windows and leakage control

Use the canonical QQQ observed daily series from src/data/universe.json.

Convert to month-end closes and evaluate every complete rolling 120-month window.

All windows overlap and are diagnostics, not independent samples.

The executable rule uses no future price, no optimization, no ranking, no parameter sweep, and no post-result tuning.

## Evidence questions

The output is intended to answer:

1. Does mutual chase improve terminal economic wealth versus CLOCK?
2. Does it reduce account MaxDD?
3. Does it reduce whole-economic-wealth MaxDD?
4. How much of B is actually contributed across windows?
5. How often does terminal economic wealth fall below B?
6. Is any apparent benefit just the mechanical consequence of keeping more capital in reserve?

No result from this study is automatically promoted into the formal 10Y Floor.
