# Rolling 10Y Floor — Portable Rerun

The previous GitHub Actions artifact named rolling-10y-floor was a **result-only artifact**. It contained JSON/JSONL/report output, but not the executable research source, the QQQ snapshot, or the FRED proxy inputs. Copying that ZIP into another program therefore did not constitute a reproducible runtime package.

The new final artifact is different.

## Portable bundle

The bundle contains:

- the exact rolling-floor runner source
- the exact rolling-floor controller source
- the QQQ source snapshot used by the controller
- the three immutable channel shards produced by the parallel workers
- the bridge output from the current run
- RUN.cmd for Windows
- RUN.sh for Linux/macOS/WSL

## External rerun contract

Requirements:

- Node.js 22 or newer
- no npm install
- no package-lock/package.json dependency resolution
- no network connection
- no FRED download

Bridge mode consumes only the bundled channel shards and the bundled QQQ snapshot.

On Windows:

    RUN.cmd

On Linux/macOS/WSL:

    ./RUN.sh

The command regenerates:

    output/rolling_floor_result.json
    output/rolling_floor_replays.jsonl
    output/rolling_floor_clock_partial_b_floor_withdrawal_replays.jsonl
    output/rolling_floor_state_path.json
    output/rolling_floor_report.md

## Three-machine topology

One workflow launches three parallel workers:

1. Windows (windows-latest) — QQQ audit channel, non-blocking
2. Linux self-hosted — NDX proxy channel, required
3. HUB-Web (ubuntu-latest) — NASDAQ Composite proxy channel, required

A separate ubuntu-latest Bridge job downloads the two required immutable proxy shards, reconstructs the canonical QQQ shard directly from the bundled/repository QQQ snapshot, validates schema and shared QQQ hash, then performs the coupling and rolling replay.

The Windows QQQ worker is audit-only. It never substitutes for the canonical QQQ target and never blocks the Bridge.

A failed or missing shard is not silently substituted by another channel.

## Research isolation

The QQQ target path remains the observed terminal outcome. NDX and NASDAQ Composite are proxy state channels only. Their own future returns are never used as the QQQ terminal payoff.

The 10Y horizon remains fixed. The historical context scales remain 20Y/30Y/50Y. Cross-scale disagreement remains a first-class market state.

The state-path file is descriptive, not a second controller. It reports how CONVERGENT / TENSION / DIVERGENT / THIN periods displaced cumulative deployment relative to the hard clock, including contiguous episode lengths and peak/end displacement.

This bundle is research-only and does not claim live suitability or a guaranteed non-loss outcome.

## Withdrawal experiment isolation

The primary withdrawal diagnostic is pre-registered and fixed at alpha = 0.50.

CONTROL:
    CLOCK_FUNDED + NONE

TEST:
    CLOCK_FUNDED + PARTIAL_ABOVE_PLANNED_PRINCIPAL

The only changed research variable is:
    W_t = 0.50 * max(0, NAV_t - B)

Adaptive-funded no-withdrawal and adaptive-funded fixed-alpha withdrawal remain secondary diagnostics only. They do not replace the isolated CLOCK comparison and are not used to select alpha.
