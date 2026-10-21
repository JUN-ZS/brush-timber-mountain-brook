# QQQ Hybrid Deployment Terminal V2 — Evolved

This is the V2 follow-engine rebuilt from the original terminal shell and strengthened with the useful OpenD lessons found in the later branch work.

## Primary objective

The terminal is for **simulation / decision support only**. It does not submit broker orders.

The operating chain is:

```
Market Data → State → Current Position → Target Position → Action Queue → Change Monitor → Roll Radar → Journal
```

## Data sources

### Primary
Futu OpenD at `127.0.0.1:11111` by default.

- QQQ/VXX: `US.QQQ`, `US.VXX`
- VIX index: `US..VIX`, requested separately
- VX full-size monthlies only: `US.VX####`
- VXM and main/next aliases are excluded

### Secondary VX source

Databento CFE `XCBF.PITCH` is the optional secondary VX source. It is a licensed API feed; it is **not** a Cboe web-page scraper.

Databento documents CFE VX futures as available for real-time and historical data, with live data under a CFE subscription. The provider uses the official Python client and keeps exchange-provided definitions/expiry information separate from quote records.

Set:

```cmd
set DATABENTO_API_KEY=YOUR_KEY
python -m pip install -r requirements-optional.txt
```

Term-source priority:

```
OpenD VX
   ↓ unavailable / blocked
Databento CFE VX
   ↓ unavailable / unconfigured
BLOCK
```

There is **no VIX-spot-as-M2 fallback** and no synthetic term structure in LIVE mode.

## Important data-policy boundary

Cboe's public delayed VX quote page explicitly prohibits automated extraction of delayed quote tables. This project therefore does **not** scrape that page. Manual entry/import remains available as a human test path only.

## Golden engine

`engine.js` is the single decision function used by LIVE and REPLAY. `tests/golden_test.js` checks that the same inputs produce the same output and that the major state gates behave consistently.

These golden tests are behavioral guards. They do **not** certify that the UI has reproduced the historical 12.7049% result.

## Baseline integrity

The UI retains the historical reference figures:

- source-aligned replay reference: 12.7049% CAGR / -23.1837% daily MTM MaxDD
- older reference benchmark: 12.52% CAGR / -23.51% MaxDD

Those numbers remain reference metadata. They are not used as a live target or as proof of current profitability.

The exact historical reconstruction still needs the original source-aligned option contract identity, exits, execution/friction and frozen reference vectors. The terminal must not invent missing pieces.

## Operator safety

When M1/M2 are unavailable the engine emits `DATA INCOMPLETE / HOLD / BLOCKED` and does **not** manufacture a reduce instruction.

In REDUCE states, target logic is a ceiling: it can reduce existing risk but will not create a new ADD signal.

Human actions are recorded separately from engine actions. A contrary human action is flagged as `CONFLICT` rather than overwriting the engine signal.

## Local run

```cmd
cd C:\path\to\brush-timber-mountain-brook\terminal\qqq_hybrid_deployment_v2
python server.py
```

Then open `http://127.0.0.1:8787`.

If the optional provider is configured, the server will attempt Databento CFE for VX whenever OpenD cannot provide M1/M2.

## No order routing

No Futu trade context, IBKR order API, tastytrade order API, or other broker order submission exists in this terminal.
