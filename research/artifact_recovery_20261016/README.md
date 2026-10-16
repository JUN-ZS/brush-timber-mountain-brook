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
- `backtest/backtest-v2-2-gate-summary.json` — gate metrics printed by the V2.2 backtest. The output confirms `FINAL FAIL`; original curve/result JSON/CSV were not uploaded and are not fabricated.
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
| Backtest V2.2 protected put overlay | [37694035278](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/37694035278) | Report summary printed; result gate was FAIL | Raw result JSON and curve CSV were written on runner but not uploaded; only printed gate metrics are recovered. |
| Cboe REAL VX + fixed Original Hybrid | [37506316510](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/37506316510) | REAL VX archive build, delayed snapshot, historical replay, and contract checks completed | Artifact upload failed due storage quota. External-vs-REAL price validation remains FAIL; source-swap agreement is diagnostic, not proof that every mark matches. |
| QQQ 1×5 Put Ratio exit study | [38778540717](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38778540717) | Run #12 completed successfully; replay, NAV/cost matrix, BAR sample audit and VXN price-proxy supplement completed | Results were already persisted directly to its isolated research branch because Actions artifact upload quota was exhausted: [run-7653cfba outputs](https://github.com/JUN-ZS/brush-timber-mountain-brook/tree/research/qqq-put-ratio-exit-measurement-v1/research/qqq_put_ratio_exit_results_v1/run-7653cfba). |

## Important interpretation

- The baseline and Dynamic V1.1 figures are historical model replay outputs, not current sizing instructions.
- VXX option reports label their pricing as derived/non-OPRA and must not be represented as actual historical fills.
- The Cboe archive builder produced 2,143 REAL VX rows for 2018-03-01–2026-09-04. A separate external price validation returned FAIL (combined M1/M2 price match rate about 88.71%, term-sign mismatch rate about 1.06%); this fail state is kept as evidence.
- The 2026-10-15 delayed VX snapshot belongs to that run's timestamp and should not be treated as a current quote.
- No main branch was changed, no PR was merged, and broker-order permission was not enabled.
- This recovery branch does not claim restoration of the original GitHub Actions ZIPs. Those uploads were rejected with: “Artifact storage quota has been hit. Usage is recalculated every 6-12 hours.”


## Additional raw-file recoveries verified on 2026-10-16

### REAL VX + historical state replay — persisted successfully

Source run: [38842692626](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38842692626). All workflow calculation, parity-diagnostic, delayed snapshot, replay, and contract-check steps completed; the recovery commit succeeded. The secondary Artifact ZIP still failed to upload due to the Actions storage quota.

Saved under `real_vx/raw_rerun-38842692626-a1/`:
- Full REAL VX M1/M2 CSV (2,143 rows, 2018-03-01 to 2026-09-04) plus build metadata.
- Cboe delayed VX snapshot and external overlap diagnostic.
- Full overlap CSV.
- Full source-swap metrics, source-swap rows CSV, and parity Markdown.
- Historical state replay CSV and Markdown.

The external-vs-REAL price comparison remains **FAIL** and is not overridden by high state/action agreement.

### Order Machine V2 — current replay files persisted

Two duplicate push-triggered runs completed successfully: [38842599615](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38842599615) and [38842604455](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38842604455). Their raw JSON/CSV and metadata are saved under `order_machine/current_v2/rerun-38842599615-a1/` and `order_machine/current_v2/rerun-38842604455-a1/`. ZIP upload still fails due to the quota. This deterministic parent-intent replay is a newer test than the older 153-window order-machine run log; it does not replace that older dataset.

### Windows persistence runner correction

VXX persistence step ran its calculations and contract checks successfully, then failed before saving because the Windows self-hosted runner does not have `pwsh` installed (`pwsh: command not found`). Windows recovery steps were changed to use Windows PowerShell (`shell: powershell`) and retriggered. The new runs are queued at the time of this note; no success is claimed until the raw files appear in this recovery branch.

- VXX retry: [38843599343](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38843599343)
- Profit Trend retry: [38843606498](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38843606498)
- Operator QA, FAR CALL, NAV exit matrix, IV/RV and public EOD quote audit are also queued from the corrected workflow revision. The branch's PR synchronize trigger was removed from these workflows to reduce duplicate replay storms.

The original Action ZIPs are still not available from the old runs. Raw file persistence into this branch is now the primary recovery path; ZIP upload remains a secondary backup only.


### VXX short-call/put raw replay — persisted successfully

Source run: [38843599343](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38843599343). This retry completed the four-layer baseline, VXX short-call/put replay, and strategy contract checks; the persistence step itself succeeded. The old run at commit `c46e2ed5` did not persist because `pwsh` was missing; the retry uses Windows PowerShell.

Files are under `vxx_short_call_put/rerun-38843599343-a1/`, including:
- Baseline profit-trend CSV/JSON.
- Strategy report Markdown and JSON.
- Per-variant equity-attribution CSVs and event JSONs for legacy, call-only, call/put, RSI/DTE and stock-sleeve comparisons.
- Recovery metadata with the tested commit and run URL.

These results remain derived research / non-OPRA, not confirmed option fills. Artifact ZIP upload is a secondary backup and is still not the recovery source of truth.


### Backtest V2.2 — original result and equity curve now persisted

Source run: [38842775770](https://github.com/JUN-ZS/brush-timber-mountain-brook/actions/runs/38842775770). The backtest engine and persistence step completed successfully; the original generated files now exist under `backtest/raw_v2_2/rerun-38842775770-a1/`:
- `backtest-result.json`
- `backtest-curve.csv`
- `backtest-report.md`
- `backtest-v2-2.json`
- `RECOVERY_META.txt`

The run's Actions artifact list remains empty, so this recovery came from the direct Git branch commit, not from the original ZIP. The model decision remains **FAIL**: OOS CAGR 11.64%, OOS MaxDD −28.59%, below the stated CAGR ≥12% and MaxDD ≥−5% gates. These files are now available for review rather than only the console summary.
