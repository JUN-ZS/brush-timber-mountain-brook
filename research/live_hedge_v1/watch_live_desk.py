from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=15)
    ap.add_argument("--far-dte", type=int, default=120)
    ap.add_argument("--far-delta", type=float, default=0.08)
    ap.add_argument("--near-dte", type=int, default=30)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=11111)
    ap.add_argument("--acc-id", type=int, default=None,
                    help="Futu trading account ID; falls back to FUTU_ACC_ID")
    args = ap.parse_args()

    if args.interval < 5:
        raise ValueError("interval must be >=5 seconds")

    while True:
        started = datetime.now(timezone.utc).isoformat()
        cmd = [
            sys.executable,
            "-m",
            "research.live_hedge_v1.run_live_desk",
            "--far-dte",
            str(args.far_dte),
            "--far-delta",
            str(args.far_delta),
            "--near-dte",
            str(args.near_dte),
            "--host",
            args.host,
            "--port",
            str(args.port),
        ]
        if args.acc_id is not None:
            cmd.extend(["--acc-id", str(args.acc_id)])
        result = subprocess.run(cmd, text=True, capture_output=True)

        log = Path("research/live_hedge_v1/live_cycles.jsonl")
        log.parent.mkdir(parents=True, exist_ok=True)
        line = {
            "started_at": started,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "returncode": result.returncode,
            "stdout_tail": (result.stdout or "")[-12000:],
            "stderr_tail": (result.stderr or "")[-5000:],
        }
        with log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(line, ensure_ascii=False, separators=(",", ":")) + "\n")

        if result.stdout:
            print("\n" + result.stdout, flush=True)
        if result.returncode != 0 and result.stderr:
            print(result.stderr, flush=True)

        time.sleep(args.interval)


if __name__ == "__main__":
    main()
