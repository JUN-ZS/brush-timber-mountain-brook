# QQQ Hybrid Terminal V3 — Replacement Matrix

The V3 terminal is intended to supersede V2 for daily operator use. V2 is frozen as a regression/reference line.

| Capability | V2 | V3 |
|---|---|---|
| QQQ/VXX/VIX market data | OpenD + Yahoo fallback | OpenD + Yahoo fallback |
| VX M1/M2 | OpenD + paid Databento | **OpenD live first**, free delayed Cboe fallback |
| VX selection | monthly discovery | **strict actual-expiry selection** |
| VIX-as-M2 proxy | forbidden | forbidden |
| DATA BLOCK | current=target | current=target, explicit BLOCK |
| stale/as-of handling | limited | **FRESH / STALE / MIXED / BLOCKED** |
| current→target | yes | yes |
| REDUCE ceiling | yes | yes |
| trigger monitor | yes | yes, with source/as-of context |
| roll radar | yes | yes |
| numerical confidence | present | **retired** |
| Databento paid source | active optional | **retired from V3 path** |
| auto broker routing | absent | absent / forbidden |
| human-vs-engine conflict journal | present conceptually | **explicit append-only JSONL journal** |
| provenance | row-level | **field-level + source chain + as-of** |
| research references | mixed into live README | **visually separated REFERENCE ONLY** |
| replay | same terminal surface | research-only, kept out of default operator flow |
| option candidate monitor | yes | **active, read-only estimate + exact credit sizing when positive credit is available** |\n| manual overrides | present | research/test only |

## V3 design rule

More functions does not mean better.

V3 is better only when a function is:
- usable on the current workflow;
- provenance-labeled;
- deterministic;
- safe when data is missing;
- isolated when it is research-only.

Retired functions remain documented so they cannot silently return through future edits.
