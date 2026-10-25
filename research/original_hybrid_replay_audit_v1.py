#!/usr/bin/env python3
"""Reproduce the preserved Original Hybrid simulator over pinned historical windows.

This wrapper imports the existing simulator unchanged. It only reshapes and date
filters src/data/universe.json, then exports the daily account-NAV curve.
Option pricing remains DERIVED_BS_VIX, not historical OPRA fills.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import tempfile

import pandas as pd

from qqq_hybrid_dynamic_deployment_v1_1_replay import CAPITAL, simulate

AUDIT_ID = "ORIGINAL_HYBRID_CAGR_REPLAY_AUDIT_V1"
WINDOWS = (
    ("TO_2025_12_15", "2018-03-01", "2025-12-15"),
    ("TO_2026_09_04", "2018-03-01", "2026-09-04"),
)
VARIANTS = (("LEGACY_BASELINE", False), ("DEPLOY_V1_1", True))
PR98_GOLDEN_FULL = {
    "final_nav_usd": 298267.22,
    "cagr_pct_rounded": 13.70,
    "maxdd_pct_rounded": -23.02,
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_universe(path: Path) -> tuple[pd.DataFrame, str]:
    raw_bytes = path.read_bytes()
    raw = json.loads(raw_bytes.decode("utf-8"))
    dates = raw.get("dates") or []
    c = raw.get("c") or {}
    series = {
        "date": dates,
        "qqq": c.get("QQQ") or c.get("qqq"),
        "vxx": c.get("VXX") or c.get("vxx"),
        "vix": c.get("VIX") or c.get("vix"),
    }
    if any(series[k] is None for k in ("qqq", "vxx", "vix")):
        raise ValueError("universe.json needs dates and c.{QQQ,VXX,VIX}")
    lengths = {k: len(v) for k, v in series.items()}
    if len(set(lengths.values())) != 1:
        raise ValueError(f"Input series length mismatch: {lengths}")
    frame = pd.DataFrame(series)
    frame["date"] = pd.to_datetime(frame["date"], errors="raise").dt.normalize()
    for col in ("qqq", "vxx", "vix"):
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    frame = frame.sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)
    return frame, hashlib.sha256(raw_bytes).hexdigest()


def make_slice(frame: pd.DataFrame, start: str, end: str) -> tuple[dict, dict]:
    lo, hi = pd.Timestamp(start), pd.Timestamp(end)
    in_window = frame[(frame.date >= lo) & (frame.date <= hi)].copy()
    if in_window.empty:
        raise ValueError(f"No observations in {start}..{end}")
    valid = in_window.dropna(subset=["qqq", "vxx", "vix"]).copy()
    if valid.empty:
        raise ValueError(f"No complete QQQ/VXX/VIX observations in {start}..{end}")
    if valid.date.iloc[0] != lo:
        raise ValueError(f"First complete source date {valid.date.iloc[0].date()} != requested start {start}")
    payload = {
        "dates": [d.strftime("%Y-%m-%d") for d in valid.date],
        "qqq": [float(x) for x in valid.qqq],
        "vxx": [float(x) for x in valid.vxx],
        "vix": [float(x) for x in valid.vix],
        "source_adapter": "src/data/universe.json c.{QQQ,VXX,VIX}; date filter only",
    }
    meta = {
        "requested_start": start,
        "requested_end": end,
        "first_observation": valid.date.iloc[0].strftime("%Y-%m-%d"),
        "last_observation": valid.date.iloc[-1].strftime("%Y-%m-%d"),
        "raw_dates_in_window": int(len(in_window)),
        "complete_rows_used": int(len(valid)),
        "rows_dropped_for_missing_market_values": int(len(in_window) - len(valid)),
        "source_start": frame.date.min().strftime("%Y-%m-%d"),
        "source_end": frame.date.max().strftime("%Y-%m-%d"),
    }
    return payload, meta


def run_one(payload: dict, dynamic: bool, out_csv: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="original_hybrid_audit_") as temp:
        inp = Path(temp) / "spots.json"
        inp.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
        cagr, maxdd, final_nav, opens, closes, events, eq = simulate(str(inp), dynamic=dynamic)

    eq = eq.copy()
    eq["date"] = pd.to_datetime(eq["date"]).dt.normalize()
    eq = eq.sort_values("date").reset_index(drop=True)
    if eq.empty or eq.nav.isna().any() or not eq.nav.map(math.isfinite).all():
        raise ValueError("Simulator produced empty or non-finite NAV path")
    years = (eq.date.iloc[-1] - eq.date.iloc[0]).days / 365.25
    if years <= 0:
        raise ValueError("Replay window has zero elapsed years")
    cagr_recomputed = (float(eq.nav.iloc[-1]) / CAPITAL) ** (1.0 / years) - 1.0
    eq["peak_nav"] = eq.nav.cummax()
    eq["drawdown"] = eq.nav / eq.peak_nav - 1.0
    maxdd_recomputed = float(eq.drawdown.min())
    if abs(cagr_recomputed - float(cagr)) > 1e-10:
        raise AssertionError(f"CAGR mismatch: simulator={cagr}, recomputed={cagr_recomputed}")
    if abs(maxdd_recomputed - float(maxdd)) > 1e-10:
        raise AssertionError(f"MaxDD mismatch: simulator={maxdd}, recomputed={maxdd_recomputed}")
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    eq.to_csv(out_csv, index=False, float_format="%.10f")
    return {
        "variant": "DEPLOY_V1_1" if dynamic else "LEGACY_BASELINE",
        "initial_nav_usd": float(CAPITAL),
        "final_nav_usd": float(eq.nav.iloc[-1]),
        "net_profit_usd": float(eq.nav.iloc[-1] - CAPITAL),
        "total_return_pct": float((eq.nav.iloc[-1] / CAPITAL - 1.0) * 100.0),
        "cagr_pct": float(cagr_recomputed * 100.0),
        "maxdd_daily_mtm_pct": float(maxdd_recomputed * 100.0),
        "elapsed_years_actual_marks": float(years),
        "daily_nav_rows": int(len(eq)),
        "first_nav_date": eq.date.iloc[0].strftime("%Y-%m-%d"),
        "last_nav_date": eq.date.iloc[-1].strftime("%Y-%m-%d"),
        "opened_position_records": int(len(opens)),
        "closed_position_records": int(len(closes)),
        "event_records": int(len(events)),
        "equity_curve_csv": str(out_csv).replace("\\", "/"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spots-path", default="src/data/universe.json")
    ap.add_argument("--out", default="research/original_hybrid_replay_audit_v1/results")
    args = ap.parse_args()

    source_path = Path(args.spots_path)
    source_frame, source_hash = load_universe(source_path)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    module_path = Path("research/qqq_hybrid_dynamic_deployment_v1_1_replay.py")
    if not module_path.is_file():
        raise FileNotFoundError(f"Preserved simulator not found: {module_path}")

    results = []
    window_meta = {}
    for window_id, start, end in WINDOWS:
        payload, meta = make_slice(source_frame, start, end)
        window_results = []
        for label, dynamic in VARIANTS:
            curve_path = out_dir / f"{window_id.lower()}_{label.lower()}_equity.csv"
            row = run_one(payload, dynamic, curve_path)
            row["window_id"] = window_id
            row["requested_window"] = {"start": start, "end": end}
            results.append(row)
            window_results.append(row)
        meta["results"] = window_results
        window_meta[window_id] = meta

    full = next(r for r in results if r["window_id"] == "TO_2026_09_04" and r["variant"] == "LEGACY_BASELINE")
    golden = {
        "anchor": "PR #98 successful replay, Actions run 37866573537",
        "expected_final_nav_usd_rounded": PR98_GOLDEN_FULL["final_nav_usd"],
        "observed_final_nav_usd": full["final_nav_usd"],
        "final_nav_abs_difference_usd": abs(full["final_nav_usd"] - PR98_GOLDEN_FULL["final_nav_usd"]),
        "expected_cagr_pct_rounded": PR98_GOLDEN_FULL["cagr_pct_rounded"],
        "observed_cagr_pct": full["cagr_pct"],
        "expected_maxdd_pct_rounded": PR98_GOLDEN_FULL["maxdd_pct_rounded"],
        "observed_maxdd_pct": full["maxdd_daily_mtm_pct"],
        "pass": (
            abs(full["final_nav_usd"] - PR98_GOLDEN_FULL["final_nav_usd"]) <= 0.05
            and abs(full["cagr_pct"] - PR98_GOLDEN_FULL["cagr_pct_rounded"]) <= 0.03
            and abs(full["maxdd_daily_mtm_pct"] - PR98_GOLDEN_FULL["maxdd_pct_rounded"]) <= 0.03
        ),
    }
    report = {
        "audit_id": AUDIT_ID,
        "status": "COMPLETED_MODEL_DERIVED_REPLAY",
        "strategy_source": {
            "module": str(module_path).replace("\\", "/"),
            "module_sha256": sha256_file(module_path),
            "source_input": str(source_path).replace("\\", "/"),
            "source_input_sha256": source_hash,
            "source_observation_count": int(len(source_frame)),
            "source_first_date": source_frame.date.min().strftime("%Y-%m-%d"),
            "source_last_date": source_frame.date.max().strftime("%Y-%m-%d"),
        },
        "pricing_and_evidence_class": {
            "option_pricing": "Black-Scholes marks with VIX-derived IV proxies and modeled spread haircuts",
            "term_structure": "VIX / 20-session VIX mean proxy; not observed VX M1/M2",
            "historical_option_chain_fills": False,
            "evidence_class": "DERIVED_BS_VIX; NOT OPRA",
            "market_fill_assumption": "same-date daily-close signal/mark proxy; executable intraday fills not verified",
        },
        "window_metadata": window_meta,
        "results": results,
        "pr98_source_parity_control": golden,
        "prior_claimed_original_hybrid_reference": {
            "cagr_pct": 12.7049,
            "maxdd_daily_mtm_pct": -23.1837,
            "final_nav_usd": 276508.0,
            "exact_end_date_and_input_sha": "NOT_PINNED_IN_VISIBLE_REFERENCE_CONTRACT",
            "status": "REFERENCE_ONLY; comparison is not apples-to-apples until its original end date and input SHA are recovered",
        },
        "prior_claimed_dynamic_v1_1_reference": {
            "cagr_pct": 12.6828,
            "maxdd_daily_mtm_pct": -23.6965,
            "final_nav_usd": 276047.0,
            "exact_end_date_and_input_sha": "NOT_PINNED_IN_VISIBLE_REFERENCE_CONTRACT",
            "status": "REFERENCE_ONLY; comparison is not apples-to-apples until its original end date and input SHA are recovered",
        },
        "guardrails": [
            "The preserved simulator implementation is imported unchanged; only the source date window is filtered.",
            "The 2025-12-15 cutoff matches the common historical option-data cutoff but does not alone prove it was the original Hybrid reference end date.",
            "CAGR and MaxDD are calculated from a daily account-NAV curve, not from summed overlapping trade P&L.",
            "Derived option marks and synthetic VX term structure are not verified historical option-chain fills or observed VX futures.",
            "No optimization, live order routing, or main-branch change is included.",
        ],
    }
    (out_dir / "replay_summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    md = [
        "# Original Hybrid CAGR Replay Audit V1",
        "",
        "## Replayed account-NAV results",
        "",
        "| Window | Variant | Final NAV | Net profit | CAGR | Daily MTM MaxDD | NAV rows |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in results:
        md.append(
            f"| {row['requested_window']['start']} to {row['requested_window']['end']} "
            f"| {row['variant']} | USD {row['final_nav_usd']:,.2f} | USD {row['net_profit_usd']:,.2f} "
            f"| {row['cagr_pct']:.4f}% | {row['maxdd_daily_mtm_pct']:.4f}% | {row['daily_nav_rows']:,} |"
        )
    md += [
        "",
        "## Reproduction control",
        "",
        f"- Market-input SHA-256: {source_hash}",
        f"- Preserved simulator SHA-256: {report['strategy_source']['module_sha256']}",
        f"- PR #98 legacy full-window source-parity check: {'PASS' if golden['pass'] else 'FAIL'}; "
        f"final-NAV delta USD {golden['final_nav_abs_difference_usd']:.4f}.",
        "- Pricing/evidence: DERIVED_BS_VIX; NOT OPRA. VX term structure is a VIX/MA20 proxy.",
        "- The prior 12.7049% / -23.1837% / USD 276,508 figures remain a separate, not-yet-pinned reference. The exact historical end date, source-input hash and simulator version need to agree before claiming exact reproduction.",
        "- These are daily account-NAV replay metrics for the preserved model, not live fills, a brokerage statement, or an account-constrained OPRA options replay.",
    ]
    (out_dir / "REPLAY_AUDIT_REPORT.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({"results": results, "pr98_source_parity_control": golden}, indent=2))
    if not golden["pass"]:
        raise SystemExit("PR #98 source-parity regression failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
