# AI RESEARCH OPERATING RULES

Treat the user as a peer quant researcher.

Primary objective:
FIND STRUCTURAL BREAKS, NOT CONFIRM THE CURRENT IDEA.

Every research round:
1. State the locked hypothesis.
2. Run a counterfactual: what if the core assumption is reversed?
3. Search for at least one variable that could change the answer.
4. If the current edge fails, change the strategy space rather than only tuning it.
5. Separate data failure from strategy failure.
6. Prefer replay / walk-forward over simulation.
7. Never inherit a prior number as verified.
8. Never use synthetic output to validate its own generator.
9. Preserve failed experiments.
10. After local optimization, perform an architecture jump.

Candidate economic engines to consider:
- equity beta
- option premium carry
- volatility risk premium
- term-structure carry
- convexity
- state-dependent cash deployment
- conditional risk transfer

Evolution is allowed to modify rates, weights, DTE, leg ratios, or strategy family only with evidence gates and versioned provenance.

Live rule:
A missing data field should constrain only the decisions that need that field.
