# QQQ_HYBRID_DYNAMIC_DEPLOYMENT_V1_1

Research-only reconstruction of the historical hybrid architecture from the original workspace.

**This branch does not modify the official V2.2 strategy.**

Frozen backbone:
- 42% NAV QQQ long core.
- QQQ call-credit financing layer: derived BS/VIX, 16Δ short / 8Δ long wing, base risk 0.8% NAV.
- VXX short: 18% notional when source policy permits it.
- VXX call-credit spread: 2% risk budget.
- Shock/backwardation-style logic closes VXX sellers but keeps the QQQ core.

Only QQQ financing-layer deployment is dynamic.

Deployment levels are exactly 0.8%, 0.4%, or 0.0% NAV risk.
Downshift is immediate; redeployment requires 2 consecutive clear sessions.

Frozen downshift triggers:
- portfolio drawdown <= -10%
- QQQ >= 99% of 252-session high
- QQQ 5-session return >= +6%
- QQQ short-call delta >= 0.30
- QQQ short-call delta >= 0.40 => zero deployment
- QQQ call-credit PnL / risk >= +50%
- strong breakout: QQQ 10-session return >= +10% and >=99.5% of 252-session high
- T+1 continuation after a >=98% short-strike approach => zero deployment

Entry signal:
QQQ close / 252-session high >= 0.98 AND QQQ close / 200DMA - 1 >= 0.08.

No parameter optimization is performed by the runner.

## Data / pricing provenance

The GitHub workflow consumes the repository's committed src/data/universe.json fixture.
The local source-logic reconstruction used the original workspace src/data/spots.json with SHA256:
e53883bab02df88196ec7dc84098f0b0e4f138b29958fa826e721ea916535599

Pricing is DERIVED_BS_VIX; this is **not OPRA historical option execution**.
Results are source-logic reconstruction evidence, not observed broker fills.

## Pre-run local checkpoint

Using the original workspace fixture, V1.1 reproduced:
- CAGR 13.2266%
- daily MTM MaxDD -23.1242%
- final NAV 291,028.34 from 100,000

GitHub Actions output is the formal branch artifact.
