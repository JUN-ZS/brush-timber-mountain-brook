# App Artifact Recovery — 2026-10-16

This branch preserves report objects and QA summaries that were fully printed in GitHub Actions job logs after the original Actions artifact uploads were blocked by GitHub's artifact storage quota.

**This is a recovery of log-verifiable outputs, not a recreation of the original ZIP bundles.** Daily CSVs or other files that were generated on a runner but not printed in full in the retained job log are not reconstructed or fabricated.

## Recovered files

- `operator_terminal/qa_summary.txt` — operator terminal QA marker from the run log.
- `operator_terminal/qa_run_evidence.json` — verified test/log details; engine tests 26 groups PASS, hub research pack 10 groups PASS, static asset contract PASS; attempt 2's final upload failed due quota.
- `profit_trend/baseline_run_summary.json` — log-printed baseline run summary.
- `profit_trend/dynamic_v1_1_run_summary.json` — log-printed Dynamic V1.1 run summary.
- `profit_trend/vxx_call_spread_contribution.json` — log-printed VXX call-spread attribution summary.
- `vxx_short_call_put/strategy_report.json` — complete strategy report JSON printed by the VXX short-call/put replay.
- `order_machine/RESULTS_ORDER_MACHINE_REPLAY.json` — complete 153-window replay JSON printed by Order Machine.
- `real_vx/real_vx_build_summary.json` — complete REAL VX build summary printed in logs.
- `real_vx/external_source_validation.json` — preserved validation result, including its **FAIL** status. This is not silently converted to PASS.
- `real_vx/source_swap_parity.json` — complete source-swap comparison object printed in logs.
- `real_vx/delayed_vx_snapshot_2026-10-15.json` — dated delayed Cboe snapshot as observed by that run; historical run evidence, not a current live quote.
- `real_vx/historical_state_replay_summary.json` — M1/M2 historical replay summary printed in logs.

## Source runs and status

| Study | Actions run | What the latest rerun established | Limitation |
|---|---|---|---|
| Operator Terminal QA | [37881169553](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/37881169553) | Attempt 2 tests and static asset contract passed | Artifact upload failed due storage quota. Attempt 3 was queued at last check and is not claimed as passed. |
| Profit Trend + VXX call-spread contribution | [37845459299](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/37845459299) | Baseline, Dynamic V1.1, VXX call-spread calculation, and contract checks completed | Artifact upload failed due storage quota; only log-emitted summaries are recovered here. |
| VXX short call / put hybrid | [37866573537](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/37866573537) | Full strategy report JSON emitted; legacy parity and strategy contract passed | Artifact upload failed due storage quota; pricing is derived research, not OPRA-confirmed fills. |
| Order Machine 153 × 10-year windows | [37184309811](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/37184309811) | Replay JSON for 153 windows printed | Artifact upload failed due storage quota. Fill rule assumes daily-close touch and the logged model explicitly has no fees/slippage. |
| Cboe REAL VX + fixed Original Hybrid | [37506316510](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/37506316510) | REAL VX archive build, delayed snapshot, historical replay, and contract checks completed | Artifact upload failed due storage quota. External-vs-REAL price validation remains FAIL; source-swap agreement is diagnostic, not proof that every mark matches. |
| QQQ 1×5 Put Ratio exit study | [38778540717](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38778540717) | Run #12 completed successfully; replay, NAV/cost matrix, BAR sample audit and VXN price-proxy supplement completed | Results were already persisted directly to its isolated research branch because Actions artifact upload quota was exhausted: [run-7653cfba outputs](https://github.com/JUN-ZS/brush-timber-mountain-brook/tree/research/qqq-put-ratio-exit-measurement-v1/research/qqq_put_ratio_exit_results_v1/run-7653cfba). |

## Important interpretation

- The baseline and Dynamic V1.1 figures are historical model replay outputs, not current sizing instructions.
- VXX option reports label their pricing as derived/non-OPRA and must not be represented as actual historical fills.
- The Cboe archive builder produced 2,143 REAL VX rows for 2018-03-01–2026-09-04. A separate external price validation returned FAIL (combined M1/M2 price match rate about 88.71%, term-sign mismatch rate about 1.06%); this fail state is kept as evidence.
- The 2026-10-15 delayed VX snapshot belongs to that run's timestamp and should not be treated as a current quote.
- No main branch was changed, no PR was merged, and broker-order permission was not enabled.
- This recovery branch does not claim restoration of the original GitHub Actions ZIPs. Those uploads were rejected with: “Artifact storage quota has been hit. Usage is recalculated every 6-12 hours.”
