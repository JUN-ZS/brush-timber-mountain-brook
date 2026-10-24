#!/usr/bin/env python3
"""Compare DTE45 and DTE14 with matching expiry-guarded 10/20-session exits."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

PHASES = range(5)
POLICIES = ("HOLD_10_OR_DTE_LE_7", "HOLD_20_OR_DTE_LE_7")
DTE45 = {"dte_min": 30, "dte_max": 60, "dte_target": 45}
DTE14 = {"dte_min": 7, "dte_max": 21, "dte_target": 14}
METRICS = (
    "opened", "resolved", "unresolved", "win_rate_pct", "mean_net_pnl_usd",
    "median_net_pnl_usd", "total_resolved_net_pnl_usd",
    "annualized_resolved_net_pnl_usd", "worst_resolved_trade_usd",
    "profit_factor", "stress_annualized_net_pnl_usd",
    "peak_concurrent_cohorts", "peak_short_assignment_obligation_usd",
)


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"missing required audit output: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_arm(root: Path, expected: dict[str, int], label: str) -> dict[str, Any]:
    for phase in PHASES:
        summary = read_json(root / "fixed_phase_sensitivity" / f"phase_{phase}" / "summary.json")
        selection = summary.get("selection", {})
        actual = tuple(selection.get(k) for k in ("dte_min", "dte_max", "dte_target"))
        wanted = tuple(expected[k] for k in ("dte_min", "dte_max", "dte_target"))
        if actual != wanted:
            raise ValueError(f"{label} phase {phase}: DTE {actual} != {wanted}")
        if not math.isclose(float(selection.get("target_abs_delta", 0)), 0.25, abs_tol=1e-8):
            raise ValueError(f"{label} phase {phase}: target absolute Delta must be 0.25")
        if selection.get("initial_phase_sessions") != phase or selection.get("cohort_stride_sessions") != 5:
            raise ValueError(f"{label} phase {phase}: fixed cadence metadata mismatch")
        if selection.get("schedule_mode") != "FIXED_ANCHOR_NO_REANCHOR":
            raise ValueError(f"{label} phase {phase}: not fixed-anchor")
        if selection.get("allow_overlapping_cohorts") is not True:
            raise ValueError(f"{label} phase {phase}: overlap must remain enabled")
        if summary.get("entry_filter", {}).get("name") != "none":
            raise ValueError(f"{label} phase {phase}: entry filter changed")
        ratio = summary.get("ratio", {})
        if (ratio.get("fixed_long_qqq_contracts"), ratio.get("fixed_short_spy_contracts")) != (1, 3):
            raise ValueError(f"{label} phase {phase}: fixed 1:3 ratio mismatch")
        variant = summary.get("execution_variant", {})
        if variant.get("name") != "EXPIRY_GUARDED_HOLD":
            raise ValueError(f"{label} phase {phase}: guarded policy manifest missing")
        policies = summary.get("policies", {})
        if set(policies) != set(POLICIES):
            raise ValueError(f"{label} phase {phase}: expected exactly guarded policy outputs, got {sorted(policies)}")
        if variant.get("trigger") != "close when age_sessions >= hold_sessions OR remaining calendar DTE <= 7":
            raise ValueError(f"{label} phase {phase}: exit guard definition mismatch")

    audit_path = root / "fixed_phase_sensitivity_audit" / "comparison.json"
    audit = read_json(audit_path)
    meta = audit.get("metadata", {})
    checks = meta.get("fixed_schedule_checks", [])
    if len(checks) != 5 or any(item.get("status") != "PASS" for item in checks):
        raise ValueError(f"{label}: all five fixed-anchor audits must PASS")
    if meta.get("period_row_count") != 30 or len(audit.get("period_records", [])) != 30:
        raise ValueError(f"{label}: expected 5 phases x 3 periods x 2 guarded exit policies")
    otm = read_json(root / "fixed_phase_otm_audit" / "manifest.json")
    if otm.get("phase_count") != 5 or int(otm.get("detail_leg_rows", 0)) <= 0:
        raise ValueError(f"{label}: OTM audit incomplete")
    return {"audit": audit, "otm": otm}


def index_rows(rows: list[dict[str, Any]], label: str) -> dict[tuple[int, str, str], dict[str, Any]]:
    indexed: dict[tuple[int, str, str], dict[str, Any]] = {}
    for row in rows:
        key = (int(row["phase"]), str(row["window"]), str(row["policy"]))
        if key in indexed:
            raise ValueError(f"{label}: duplicate case {key}")
        indexed[key] = row
    return indexed


def compare_rows(rows45: list[dict[str, Any]], rows14: list[dict[str, Any]]) -> list[dict[str, Any]]:
    a, b = index_rows(rows45, "DTE45"), index_rows(rows14, "DTE14")
    if set(a) != set(b) or len(a) != 30:
        raise ValueError("paired DTE45/DTE14 comparison cases do not reconcile to 30")
    result = []
    order = {"1Y": 0, "3Y": 1, "5Y": 2}
    for key in sorted(a, key=lambda k: (k[0], order.get(k[1], 99), POLICIES.index(k[2]))):
        row: dict[str, Any] = {"phase": key[0], "window": key[1], "policy": key[2]}
        for metric in METRICS:
            x, y = a[key].get(metric), b[key].get(metric)
            row[f"dte45_{metric}"] = x
            row[f"dte14_{metric}"] = y
            try:
                row[f"delta_dte14_minus_dte45_{metric}"] = round(float(y) - float(x), 6) if x is not None and y is not None else None
            except (TypeError, ValueError):
                row[f"delta_dte14_minus_dte45_{metric}"] = None
        result.append(row)
    return result


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty comparison: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def money(value: Any) -> str:
    return "—" if value in (None, "") else f"USD {float(value):,.2f}"


def pct(value: Any) -> str:
    return "—" if value in (None, "") else f"{float(value):.2f}%"


def make_report(rows: list[dict[str, Any]], info45: dict[str, Any], info14: dict[str, Any],
                root45: Path, root14: Path) -> str:
    lines = [
        "# QQQ LONG PUT 1 : SPY SHORT PUT 3 — expiry-guarded DTE14 vs DTE45",
        "",
        "## Frozen comparison design",
        "",
        "- Reference arm: DTE 30–60 targeting 45; test arm: DTE 7–21 targeting 14.",
        "- Both arms independently replay all five immutable phases from the pinned historical option files.",
        "- Each leg targets absolute Delta 0.25 within the existing 0.10–0.50 eligibility band; fixed QQQ LONG PUT 1 : SPY SHORT PUT 3; no entry filter; overlap enabled; five common-session cadence; same-expiry pair; quote-side size gates; USD 0.05/share/side slippage and USD 0.65/contract/side commission.",
        "- Guarded exit policies: trigger at either 10 or 20 common sessions held, OR calendar DTE <= 7, whichever comes first. The trigger is an EOD signal, not a guaranteed fill; exact contract identity, quote validity and displayed exit-side size remain mandatory.",
        "- A missed close is deferred and remains unresolved if no valid executable quote is found by expiry/source end. Unresolved P&L is not set to zero.",
        "- P&L is additive fixed-size cohort P&L, not compounded account NAV. The five phases overlap and are not independent samples.",
        "",
        "## Fixed-anchor integrity",
        "",
        "| Arm | Phase | Scheduled slots | Selected signals | Skipped slots | Status |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for label, info in (("DTE45", info45), ("DTE14", info14)):
        for check in info["audit"]["metadata"]["fixed_schedule_checks"]:
            lines.append(f"| {label} | {check['phase']} | {check['scheduled_opportunities']} | {check['selected_signals']} | {check['skipped_opportunities']} | {check['status']} |")
    lines += [
        "",
        "## Five-year result by anchor phase",
        "",
        "| Phase | Exit rule | Resolved/opened DTE45 | Resolved/opened DTE14 | Unresolved DTE45 | Unresolved DTE14 | Win DTE45 | Win DTE14 | Mean net DTE45 | Mean net DTE14 | Worst DTE45 | Worst DTE14 | Peak gross SPY obligation DTE45 | Peak gross SPY obligation DTE14 |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        if r["window"] != "5Y":
            continue
        lines.append(
            f"| {r['phase']} | {r['policy']} | "
            f"{r['dte45_resolved']}/{r['dte45_opened']} | {r['dte14_resolved']}/{r['dte14_opened']} | "
            f"{r['dte45_unresolved']} | {r['dte14_unresolved']} | "
            f"{pct(r['dte45_win_rate_pct'])} | {pct(r['dte14_win_rate_pct'])} | "
            f"{money(r['dte45_mean_net_pnl_usd'])} | {money(r['dte14_mean_net_pnl_usd'])} | "
            f"{money(r['dte45_worst_resolved_trade_usd'])} | {money(r['dte14_worst_resolved_trade_usd'])} | "
            f"{money(r['dte45_peak_short_assignment_obligation_usd'])} | {money(r['dte14_peak_short_assignment_obligation_usd'])} |"
        )
    lines += [
        "",
        "## Anchor-sensitivity summary (5Y, not pooled as independent samples)",
        "",
        "| Exit rule | DTE arm | Win-rate range across phases | Mean net/trade range | Worst resolved-trade range | Peak gross SPY obligation across phases |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for policy in POLICIES:
        subset = [r for r in rows if r["window"] == "5Y" and r["policy"] == policy]
        for arm in ("dte45", "dte14"):
            wins = [float(r[f"{arm}_win_rate_pct"]) for r in subset if r.get(f"{arm}_win_rate_pct") not in (None, "")]
            means = [float(r[f"{arm}_mean_net_pnl_usd"]) for r in subset if r.get(f"{arm}_mean_net_pnl_usd") not in (None, "")]
            worst = [float(r[f"{arm}_worst_resolved_trade_usd"]) for r in subset if r.get(f"{arm}_worst_resolved_trade_usd") not in (None, "")]
            obligations = [float(r[f"{arm}_peak_short_assignment_obligation_usd"]) for r in subset if r.get(f"{arm}_peak_short_assignment_obligation_usd") not in (None, "")]
            win_range = f"{min(wins):.2f}–{max(wins):.2f}%" if wins else "—"
            mean_range = f"USD {min(means):,.2f} to {max(means):,.2f}" if means else "—"
            worst_range = f"USD {min(worst):,.2f} to {max(worst):,.2f}" if worst else "—"
            peak = f"USD {max(obligations):,.2f}" if obligations else "—"
            lines.append(f"| {policy} | {arm.upper()} | {win_range} | {mean_range} | {worst_range} | {peak} |")
    lines += [
        "",
        "## Entry/source audit hashes",
        "",
        f"- DTE45 fixed-phase comparison SHA-256: {sha256(root45 / 'fixed_phase_sensitivity_audit' / 'comparison.json')}",
        f"- DTE14 fixed-phase comparison SHA-256: {sha256(root14 / 'fixed_phase_sensitivity_audit' / 'comparison.json')}",
        f"- DTE45 OTM manifest SHA-256: {sha256(root45 / 'fixed_phase_otm_audit' / 'manifest.json')}",
        f"- DTE14 OTM manifest SHA-256: {sha256(root14 / 'fixed_phase_otm_audit' / 'manifest.json')}",
        "",
        "## Interpretation limits",
        "",
        "- DTE14 Delta 0.25 does not imply a fixed OTM percentage or a guaranteed 75% win probability.",
        "- EOD option-chain estimates are not verified fills. A trigger does not guarantee a close on that date.",
        "- Gross SPY assignment obligation equals short strike × 100 × short contracts; it is not broker margin or proof of funding capacity.",
        "- Only resolved trades enter win rate and resolved-P&L statistics; always read opened/resolved/unresolved together.",
        "- This is historical in-sample research; no broker execution or live orders are involved.",
        "",
    ]
    return "\n".join(lines)


def build(root45: Path, root14: Path, out_dir: Path) -> dict[str, Any]:
    info45 = validate_arm(root45, DTE45, "DTE45")
    info14 = validate_arm(root14, DTE14, "DTE14")
    rows = compare_rows(info45["audit"]["period_records"], info14["audit"]["period_records"])
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "performance_comparison.csv", rows)
    report = make_report(rows, info45, info14, root45, root14)
    (out_dir / "report.md").write_text(report, encoding="utf-8")
    source_hashes = {
        "dte45_phase_audit_sha256": sha256(root45 / "fixed_phase_sensitivity_audit" / "comparison.json"),
        "dte14_phase_audit_sha256": sha256(root14 / "fixed_phase_sensitivity_audit" / "comparison.json"),
        "dte45_otm_manifest_sha256": sha256(root45 / "fixed_phase_otm_audit" / "manifest.json"),
        "dte14_otm_manifest_sha256": sha256(root14 / "fixed_phase_otm_audit" / "manifest.json"),
    }
    phase_hashes = {"DTE45": {}, "DTE14": {}}
    for label, root in (("DTE45", root45), ("DTE14", root14)):
        for phase in PHASES:
            phase_root = root / "fixed_phase_sensitivity" / f"phase_{phase}"
            phase_hashes[label][str(phase)] = {
                "summary_sha256": sha256(phase_root / "summary.json"),
                "trade_episodes_sha256": sha256(phase_root / "trade_episodes.csv"),
                "entry_cohort_sha256": sha256(phase_root / "entry_cohort.csv"),
                "source_manifest_sha256": sha256(phase_root / "source_manifest.json"),
            }
    manifest = {
        "schema": "qqq-spy-expiry-guarded-dte14-vs-dte45.v1",
        "status": "COMPLETED",
        "guard": {"hold_limits_sessions": [10, 20], "remaining_calendar_dte_lte": 7, "trigger": "first condition reached; valid exit quote still required"},
        "performance_rows": len(rows),
        "source_hashes": source_hashes,
        "phase_ledger_hashes": phase_hashes,
        "runner_commit_sha": __import__("os").environ.get("GITHUB_SHA"),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False), encoding="utf-8")
    return manifest


def main():
    default_root = Path(__file__).resolve().parent / "results"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dte45-root", type=Path, default=default_root / "expiry_guarded_dte45")
    parser.add_argument("--dte14-root", type=Path, default=default_root / "expiry_guarded_dte14")
    parser.add_argument("--out-dir", type=Path, default=default_root / "expiry_guarded_dte14_vs_dte45")
    args = parser.parse_args()
    manifest = build(args.dte45_root, args.dte14_root, args.out_dir)
    print(json.dumps({"status": manifest["status"], "performance_rows": manifest["performance_rows"], "out_dir": str(args.out_dir)}, indent=2))


if __name__ == "__main__":
    main()
