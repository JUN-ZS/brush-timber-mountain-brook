# V3 Release Notes

## What changed

V3 keeps the useful V2 operator model but changes the data and safety contract.

### Better
- Free delayed Cboe VX term source is now the first term path.
- Standard monthly VX contracts are selected by actual expiry, not by screen order.
- Numbered VX contracts, VXT and VXM are excluded.
- Settlement is preferred for daily/1–2 day operation.
- Field-level provenance and data-as-of are visible.
- Stale and mixed-as-of data become explicit states.
- Missing term data preserves current position instead of generating a false REDUCE.
- REDUCE cannot create a new ADD.
- Human action is stored separately from engine action.
- Decision journal is append-only JSONL.
- Fake numerical confidence is gone.
- Paid Databento is removed from the active path.

## Still deliberately NOT implemented

Broker order transmission remains out of scope. Historical 12.7049% CAGR is reference metadata only. Exact option P&L reconstruction remains a research task, not a live-terminal assumption.
