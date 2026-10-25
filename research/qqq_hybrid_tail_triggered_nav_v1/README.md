# Original Hybrid + TAIL: paired account-NAV replay V1

**Research-only branch. Not merged to main; no broker API or orders.**

## Question

Does a TAIL position improve the inherited four-layer Original Hybrid at the account level, compared with no TAIL and with an always-held TAIL allocation?

The experiment intentionally reuses the inherited baseline policy and position-sizing rules. It does not retune them. The risk-triggered TAIL alternatives are an added diagnostic overlay, not a promoted live rule.

## Frozen base model

The model is copied from `research/qqq_hybrid_dynamic_deployment_v1_1_replay.py` at source SHA `ac74b3812c826ad491fb829108f26397322e45eb`. The base includes:
- QQQ shares: 42% NAV target;
- QQQ far-out-of-the-money call-credit spread: 0.8% NAV max-loss budget;
- VXX short-stock notional: 18% NAV;
- VXX call-credit spread: 2% NAV max-loss budget;
- inherited close/roll rules unchanged; dynamic deployment controller disabled.

This is a **DERIVED_BS_VIX** model replay. Option marks use the prior code's Black–Scholes/VIX-derived volatility and modeled spread haircut; they are not historical OPRA bid/ask fills.

## Paired test arms

All variants are replayed on the same common QQQ/VXX/VIX/Tail dates and start with USD 100,000. The final common date is the last TAIL adjusted-close date in the pinned source CSV, 2025-12-15.

- `NO_TAIL`: inherited four-layer model with no TAIL sleeve.
- `ALWAYS_ON_2P`: invest 2% of account NAV at the first aligned close, hold to the end.
- `TRIGGERED_1P`, `TRIGGERED_2P`, `TRIGGERED_5P`: invest 1%, 2%, or 5% of account NAV when the frozen trigger is observed.
- `TRIGGERED_2P_0BPS`, `TRIGGERED_2P_25BPS`, `TRIGGERED_2P_50BPS`: round-trip friction sensitivities for the 2% triggered overlay. The 10 bps base case is `TRIGGERED_2P`.

### Predeclared trigger and timing

At day `t` close, open a TAIL sleeve only if at least one condition is true:
- VXX's daily return > +6%;
- VIX > 35;
- inherited VIX/MA20 term-slope proxy < 0;
- QQQ's daily return < -3%.

The simulated order executes at the **next common session's TAIL adjusted close**, not at the signal-day close. A held sleeve is marked daily from the ratio of adjusted closes. It exits at the next common session's adjusted close after two consecutive non-triggering closes. Only one TAIL position may be open; episodes do not stack. A later trigger can re-enter after exit.

### Account accounting

TAIL's purchase debit and entry friction reduce the same cash ledger that finances the four-layer hybrid. TAIL's daily mark-to-market value is included in account NAV and therefore affects subsequent NAV-based option sizing. At exit, proceeds less exit friction return to cash. An unclosed terminal position is marked to market, not treated as a realized sale.

TAIL is valued with a dividend-adjusted close return proxy, not reconstructed historical executable trade prices or share-lot/split fills. The round-trip friction sensitivity is an explicit scenario assumption, split equally between entry and exit; it is not a measured historical TAIL spread.

## Outputs

The Actions workflow writes:
- `results/latest/report.json` — input hashes, frozen rules, limitations, and aggregate outcomes;
- `results/latest/summary.csv` — account-level final NAV, CAGR, daily MTM MaxDD, TAIL P&L, position-day counts, and friction;
- `results/latest/calendar_year.csv` — annual account-NAV diagnostics;
- a daily equity CSV and TAIL trade ledger per variant.

No Actions artifact upload is required; successful outputs are committed to this isolated branch to avoid the known artifact-storage quota issue.

## Acceptance limits

A successful workflow proves that the isolated replay and accounting contracts ran. It does **not** validate the option model as executable performance. Real historical VX M1/M2, option-chain quotes, bid/ask fill reconstruction, borrow/carry costs, margin/assignment and forced liquidation remain outside this experiment. The original 12.7049% historical-reference claim is not recertified by this run.
