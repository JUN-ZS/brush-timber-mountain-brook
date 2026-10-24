#!/usr/bin/env python3
"""Run assignment-exposure/capital-capacity audit for expiry-guarded policies."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
POLICIES = ("HOLD_10_OR_DTE_LE_7", "HOLD_20_OR_DTE_LE_7")
LABELS = {
    "HOLD_10_OR_DTE_LE_7": "10d or DTE<=7",
    "HOLD_20_OR_DTE_LE_7": "20d or DTE<=7",
}


def build(results_root: Path, out_dir: Path):
    sys.path.insert(0, str(ROOT))
    import audit_fixed_phase_capacity_v1 as audit
    audit.POLICIES = POLICIES
    audit.LABELS = LABELS
    return audit.build(results_root, out_dir)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-root", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.results_root, args.out_dir)
    print({
        "status": "COMPLETED",
        "phases": len(result.get("checks", [])) if isinstance(result, dict) else 5,
        "policies": list(POLICIES),
        "out_dir": str(args.out_dir),
    })


if __name__ == "__main__":
    main()
