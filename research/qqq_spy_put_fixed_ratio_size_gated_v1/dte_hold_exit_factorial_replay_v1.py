#!/usr/bin/env python3
"""Source-pinned DTE × max-hold × expiry-guard replay with overlapping QQQ/SPY PUT 1:6 cohorts.

Each invocation evaluates all 12 exit policies in one pass over the same selected entries.
The DTE target and date-window are fixed for that invocation; phase anchors are predeclared.
This is an EOD quote-side research replay, not a brokerage-account/margin simulation.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import qqq_spy_put_premium_matched_phase_v1 as engine

# Symmetric, fixed-width DTE eligibility bands. Target is used to choose the closest
# common expiry; these bands are intentionally mutually exclusive except for the
# deliberately separated gaps near target values.
DTE_BANDS = {
    20: (14, 26),
    30: (24, 36),
    45: (39, 51),
    60: (54, 66),
}
PHASES = (0, 2, 4, 6, 8)
HOLD_SESSIONS = (5, 10, 15, 20)
GUARD_DTES = (None, 7, 14)


def make_policies() -> tuple[dict, ...]:
    policies = []
    for hold in HOLD_SESSIONS:
        for guard in GUARD_DTES:
            if guard is None:
                name = f"HOLD_{hold}_SESSIONS"
                policies.append({"policy": name, "hold_sessions": hold})
            else:
                name = f"HOLD_{hold}_OR_DTE_LE_{guard}"
                policies.append({
                    "policy": name,
                    "hold_sessions": hold,
                    "expiry_guard_dte": guard,
                })
    return tuple(policies)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dte-target", type=int, choices=tuple(DTE_BANDS), required=True)
    parser.add_argument("--phase", type=int, choices=PHASES, required=True)
    parser.add_argument("--start", default="2018-03-01")
    parser.add_argument("--end", default="2025-12-15")
    parser.add_argument("--out-root", default="research/qqq_spy_put_fixed_ratio_size_gated_v1/results/dte_hold_exit_factorial_v1")
    parser.add_argument("--qqq-cache", default=str(Path.home() / ".cache" / "qqq-spy-dte-hold-exit-v1" / "qqq"))
    parser.add_argument("--spy-cache", default=str(Path.home() / ".cache" / "qqq-spy-dte-hold-exit-v1" / "spy"))
    wrapper = parser.parse_args()

    dte_min, dte_max = DTE_BANDS[wrapper.dte_target]
    out = Path(wrapper.out_root) / f"dte_{wrapper.dte_target}" / f"phase_{wrapper.phase}"
    if (out / "summary.json").is_file() and (out / "summary.md").is_file() and (out / "trade_episodes.csv").is_file():
        print(f"REUSE: DTE{wrapper.dte_target} phase={wrapper.phase} already has outputs.")
        return 0

    engine.POLICIES = make_policies()
    sys.argv = [
        sys.argv[0],
        "--start", wrapper.start,
        "--end", wrapper.end,
        "--max-total-contracts", "10",
        "--entry-filter", "none",
        "--sizing-mode", "fixed_ratio",
        "--fixed-long-qty", "1",
        "--fixed-short-qty", "6",
        "--target-delta", "0.25",
        "--dte-min", str(dte_min),
        "--dte-max", str(dte_max),
        "--dte-target", str(wrapper.dte_target),
        "--cohort-stride-sessions", "10",
        "--initial-phase-sessions", str(wrapper.phase),
        "--allow-overlapping-cohorts",
        "--slippage-per-share", "0.05",
        "--commission-per-contract-per-side", "0.65",
        "--qqq-cache", wrapper.qqq_cache,
        "--spy-cache", wrapper.spy_cache,
        "--out", str(out),
    ]
    args = engine.parse_args()
    report = engine.run_replay(args)

    expected = {p["policy"] for p in engine.POLICIES}
    actual = set(report["policies"])
    if actual != expected:
        raise RuntimeError(f"policy set mismatch: expected={sorted(expected)} actual={sorted(actual)}")
    selection = report.get("selection", {})
    # Core report nests strategy-selection fields under report["selection"] in current replay.
    if selection and (
        selection.get("dte_target") != wrapper.dte_target
        or selection.get("dte_min") != dte_min
        or selection.get("dte_max") != dte_max
    ):
        raise RuntimeError(f"reported DTE config mismatch: {selection}")

    out.mkdir(parents=True, exist_ok=True)
    policy_rows = []
    for p in engine.POLICIES:
        s = report["policies"][p["policy"]]
        policy_rows.append({
            "policy": p["policy"],
            "hold_sessions": p["hold_sessions"],
            "expiry_guard_dte": p.get("expiry_guard_dte"),
            "resolved": s.get("resolved"),
            "unresolved": s.get("unresolved"),
            "win_rate_pct": s.get("win_rate_pct"),
            "expectancy_net_usd": s.get("expectancy_net_usd"),
            "median_net_usd": s.get("median_net_usd"),
            "total_net_pnl_usd": s.get("total_net_pnl_usd"),
            "worst_net_usd": s.get("worst_net_usd"),
            "profit_factor": s.get("profit_factor"),
        })
    (out / "factorial_policy_summary.json").write_text(
        json.dumps({
            "status": report.get("status"),
            "dte_target": wrapper.dte_target,
            "dte_min": dte_min,
            "dte_max": dte_max,
            "phase_sessions": wrapper.phase,
            "cohort_stride_sessions": 10,
            "entry_filter": "none",
            "ratio": "QQQ LONG PUT 1 : SPY SHORT PUT 6",
            "delta_target_abs_both_legs": 0.25,
            "slippage_per_share_side_usd": 0.05,
            "commission_per_contract_side_usd": 0.65,
            "policies": policy_rows,
        }, indent=2, allow_nan=False),
        encoding="utf-8",
    )
    print(json.dumps({
        "status": report.get("status"),
        "dte_target": wrapper.dte_target,
        "dte_band": [dte_min, dte_max],
        "phase": wrapper.phase,
        "entered": report.get("cohort", {}).get("entered_cohorts"),
        "policies": policy_rows,
        "out": str(out),
    }, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
