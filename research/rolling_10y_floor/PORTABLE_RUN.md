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
    output/rolling_floor_report.md

## Three-machine topology

One workflow defines one matrix job with three parallel workers:

1. Windows self-hosted — QQQ observed channel
2. Linux self-hosted — NDX proxy channel
3. HUB-Web ubuntu-latest — NASDAQ Composite proxy channel

A separate ubuntu-latest Bridge job downloads all three immutable shards, validates their schema and shared QQQ snapshot hash, then performs the coupling and rolling replay.

A failed or missing shard is not silently substituted by another channel.

## Research isolation

The QQQ target path remains the observed terminal outcome. NDX and NASDAQ Composite are proxy state channels only. Their own future returns are never used as the QQQ terminal payoff.

The 10Y horizon remains fixed. The historical context scales remain 20Y/30Y/50Y. Cross-scale disagreement remains a first-class market state.

This bundle is research-only and does not claim live suitability or a guaranteed non-loss outcome.
