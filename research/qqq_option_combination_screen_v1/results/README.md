# Corrected replay pending

Do not use the root-level results as current findings until the corrected replay completes.

The first replay was moved intact to `preliminary_per_cycle_budget/` because two model defects were found during audit: put premium had been budgeted per cycle instead of annually, and spread quotes were not checked against the vertical's theoretical payoff bounds. The corrected code adds a prorated annual put premium budget, bounded spread quote checks, and a clearly labelled expiry intrinsic proxy if a position cannot be closed with valid quotes. The current self-hosted replay must regenerate summary.csv, daily_nav.csv, trade_ledger.csv, manifest.json, and REPORT.md before results can be ranked.

Status: RESEARCH ONLY / NOT CLEARED FOR HUB / NO BROKER ORDERS.
