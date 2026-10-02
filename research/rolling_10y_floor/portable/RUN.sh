#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
node --experimental-strip-types scripts/run-rolling-floor.ts --mode bridge --input-dir inputs/rolling_floor_shards --out-dir output
echo "PORTABLE PASS"
