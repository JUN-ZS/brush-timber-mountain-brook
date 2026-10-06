# QQQ Hybrid Deployment Terminal V2 — OpenD

This bundle is the standalone QQQ hybrid deployment terminal.

## Live data path

Futu OpenD (default 127.0.0.1:11111)
→ QQQ / VXX / VIX spot
→ VX futures discovery
→ first two identifiable monthly VX contracts
→ M1 / M2
→ S = (M2 - M1) / M1
→ carry / risk state

No synthetic M1/M2 fallback is used.

Manual M1/M2 fields remain available only as explicit test/override inputs; they are not the live source.

## Safety boundary

- Read-only market data.
- No broker order routing.
- No OpenSecTradeContext.
- Missing/insufficient VX futures data blocks the live term-structure decision instead of guessing.

## Runtime

The archive contains:
- app.js
- index.html
- server.py
- styles.css
- RUN.cmd
- sample_replay.csv
- qa_opend_term_structure.py
- README.md

The default UI port is 8787. OpenD host/port and UI port are configurable by environment variables.

## Verification

The OpenD contract-selection helper test passes locally with synthetic-free parsing cases. Actual live OpenD values must be verified against the user's logged-in OpenD instance and its US futures market-data authority.

Research only / signal interface.