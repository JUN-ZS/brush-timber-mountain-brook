#!/usr/bin/env python3
"""Compare fresh DTE 7–21 (target 14) with the existing DTE 30–60 (target 45) five-phase baseline."""
from __future__ import annotations
import argparse, csv, hashlib, json, math
from pathlib import Path

PHASES = range(5)
POLICIES = ("HOLD_5_SESSIONS", "HOLD_10_SESSIONS", "HOLD_20_SESSIONS", "EXIT_AT_DTE_LE_7")
PERIODS = ("1Y", "3Y", "5Y")
D45 = {"dte_min": 30, "dte_max": 60, "dte_target": 45}
D14 = {"dte_min": 7, "dte_max": 21, "dte_target": 14}


def read_json(path):
    if not path.is_file():
        raise FileNotFoundError(f"missing required audit output: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path):
    if not path.is_file():
        raise FileNotFoundError(f"missing required audit output: {path}")
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows):
    if not rows:
        raise ValueError(f"refusing to write empty comparison output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def validate_run(root, expected, label):
    for phase in PHASES:
        summary = read_json(root / "fixed_phase_sensitivity" / f"phase_{phase}" / "summary.json")
        selection = summary.get("selection", {})
        if selection.get("schedule_mode") != "FIXED_ANCHOR_NO_REANCHOR":
            raise ValueError(f"{label} phase {phase}: fixed-anchor schedule mode missing")
        if selection.get("initial_phase_sessions") != phase or selection.get("cohort_stride_sessions") != 5:
            raise ValueError(f"{label} phase {phase}: phase/cadence mismatch")
        if not math.isclose(float(selection.get("target_abs_delta", 0)), 0.25, abs_tol=1e-8):
            raise ValueError(f"{label} phase {phase}: target absolute Delta is not 0.25")
        actual = tuple(selection.get(k) for k in ("dte_min", "dte_max", "dte_target"))
        wanted = tuple(expected[k] for k in ("dte_min", "dte_max", "dte_target"))
        if actual != wanted:
            raise ValueError(f"{label} phase {phase}: DTE {actual}, expected {wanted}")
        ratio = summary.get("ratio", {})
        if (ratio.get("fixed_long_qqq_contracts"), ratio.get("fixed_short_spy_contracts")) != (1, 3):
            raise ValueError(f"{label} phase {phase}: fixed ratio must be 1:3")
        if summary.get("entry_filter", {}).get("name") != "none":
            raise ValueError(f"{label} phase {phase}: entry filter must be none")
        if selection.get("allow_overlapping_cohorts") is not True:
            raise ValueError(f"{label} phase {phase}: overlapping cohorts not enabled")
    data = read_json(root / "fixed_phase_sensitivity_audit" / "comparison.json")
    meta = data.get("metadata", {})
    checks = meta.get("fixed_schedule_checks", [])
    if len(checks) != 5 or any(c.get("status") != "PASS" for c in checks):
        raise ValueError(f"{label}: all five fixed-anchor checks must pass")
    if len(data.get("period_records", [])) != 60 or meta.get("period_row_count") != 60:
        raise ValueError(f"{label}: expected 60 period records")
    return data


def index_records(rows, keys, label):
    out = {}
    for row in rows:
        key = tuple(row.get(k) for k in keys)
        if key in out:
            raise ValueError(f"{label}: duplicate key {key}")
        out[key] = row
    return out


def join_performance(rows45, rows14):
    keys = ("phase", "window", "policy")
    a = index_records(rows45, keys, "DTE45 performance")
    b = index_records(rows14, keys, "DTE14 performance")
    if set(a) != set(b):
        raise ValueError("DTE45 and DTE14 performance cases do not reconcile")
    metrics = ("opened", "resolved", "unresolved", "win_rate_pct", "mean_net_pnl_usd",
               "median_net_pnl_usd", "total_resolved_net_pnl_usd", "annualized_resolved_net_pnl_usd",
               "worst_resolved_trade_usd", "profit_factor", "stress_annualized_net_pnl_usd",
               "peak_concurrent_cohorts", "peak_short_assignment_obligation_usd")
    out = []
    for key in sorted(a, key=lambda k: (int(k[0]), PERIODS.index(str(k[1])), POLICIES.index(str(k[2])))):
        row = {"phase": int(key[0]), "window": key[1], "policy": key[2]}
        for name in metrics:
            x, y = a[key].get(name), b[key].get(name)
            row[f"dte45_{name}"], row[f"dte14_{name}"] = x, y
            try:
                row[f"delta_dte14_minus_dte45_{name}"] = round(float(y)-float(x), 4) if x is not None and y is not None else None
            except (TypeError, ValueError):
                row[f"delta_dte14_minus_dte45_{name}"] = None
        out.append(row)
    return out


def join_otm(rows45, rows14):
    keys = ("phase", "leg", "reference_time")
    a = index_records(rows45, keys, "DTE45 OTM")
    b = index_records(rows14, keys, "DTE14 OTM")
    if set(a) != set(b):
        raise ValueError("DTE45 and DTE14 OTM cases do not reconcile")
    metrics = ("n", "otm_n", "atm_n", "itm_n", "non_otm_pct", "mean_signed_otm_pct",
               "median_signed_otm_pct", "min_signed_otm_pct", "max_signed_otm_pct",
               "mean_otm_pct_when_otm", "median_otm_pct_when_otm")
    out = []
    for key in sorted(a, key=lambda k: (int(k[0]), str(k[1]), str(k[2]))):
        row = {"phase": int(key[0]), "leg": key[1], "reference_time": key[2]}
        for name in metrics:
            try:
                x = float(a[key][name]) if a[key].get(name) not in ("", None) else None
                y = float(b[key][name]) if b[key].get(name) not in ("", None) else None
            except (KeyError, ValueError):
                raise ValueError(f"missing/invalid OTM metric {name} at {key}")
            row[f"dte45_{name}"] = int(x) if name in ("n", "otm_n", "atm_n", "itm_n") and x is not None else x
            row[f"dte14_{name}"] = int(y) if name in ("n", "otm_n", "atm_n", "itm_n") and y is not None else y
            row[f"delta_dte14_minus_dte45_{name}"] = round(y-x, 6) if x is not None and y is not None else None
        out.append(row)
    return out


def build(root45, root14, out_dir):
    data45, data14 = validate_run(root45, D45, "DTE45"), validate_run(root14, D14, "DTE14")
    mpath45 = root45 / "fixed_phase_otm_audit" / "manifest.json"
    mpath14 = root14 / "fixed_phase_otm_audit" / "manifest.json"
    m45, m14 = read_json(mpath45), read_json(mpath14)
    for label, manifest in (("DTE45", m45), ("DTE14", m14)):
        if manifest.get("phase_count") != 5 or manifest.get("detail_leg_rows", 0) <= 0:
            raise ValueError(f"{label}: incomplete OTM audit")
    perf = join_performance(data45["period_records"], data14["period_records"])
    otm = join_otm(read_csv(root45 / "fixed_phase_otm_audit" / "phase_leg_otm_summary.csv"),
                   read_csv(root14 / "fixed_phase_otm_audit" / "phase_leg_otm_summary.csv"))
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "performance_comparison.csv", perf)
    write_csv(out_dir / "otm_comparison.csv", otm)
    money = lambda v: "—" if v in (None, "") else f"USD {float(v):,.2f}"
    pct = lambda v: "—" if v in (None, "") else f"{float(v):.2f}%"
    lines = [
        "# QQQ LONG PUT 1 : SPY SHORT PUT 3 — DTE 14 vs DTE 45 comparison", "",
        "## Frozen comparison design", "",
        "- DTE45 reference: DTE 30–60, target 45; target absolute Delta 0.25 on each leg.",
        "- DTE14 test: DTE 7–21, target 14; target absolute Delta 0.25 on each leg.",
        "- Both arms keep the same source pins, no entry filter, fixed 1:3, five-session fixed-anchor cadence, five phases, overlapping cohorts, same expiry, quote-side size checks and base costs (USD 0.05/share/side slippage plus USD 0.65/contract/side commission).",
        "- Fixed-size cohort estimates, not compounded NAV or confirmed fills. Unresolved trades stay explicit, especially where a longer holding policy nears expiry.", "",
        "## Fixed-anchor integrity", "",
        "| Arm | Phase | Scheduled slots | Selected signals | Skipped slots | Status |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for label, data in (("DTE45", data45), ("DTE14", data14)):
        for check in data["metadata"]["fixed_schedule_checks"]:
            lines.append(f"| {label} | {check['phase']} | {check['scheduled_opportunities']} | {check['selected_signals']} | {check['skipped_opportunities']} | {check['status']} |")
    lines += ["", "## Five-year performance by phase and exit policy", "",
        "| Phase | Policy | DTE45 resolved/opened | DTE14 resolved/opened | Win DTE45 | Win DTE14 | Mean net DTE45 | Mean net DTE14 | Worst DTE45 | Worst DTE14 | Peak obligation DTE45 | Peak obligation DTE14 |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in perf:
        if r["window"] != "5Y":
            continue
        lines.append(f"| {r['phase']} | {r['policy']} | {r['dte45_resolved']}/{r['dte45_opened']} | {r['dte14_resolved']}/{r['dte14_opened']} | {pct(r['dte45_win_rate_pct'])} | {pct(r['dte14_win_rate_pct'])} | {money(r['dte45_mean_net_pnl_usd'])} | {money(r['dte14_mean_net_pnl_usd'])} | {money(r['dte45_worst_resolved_trade_usd'])} | {money(r['dte14_worst_resolved_trade_usd'])} | {money(r['dte45_peak_short_assignment_obligation_usd'])} | {money(r['dte14_peak_short_assignment_obligation_usd'])} |")
    lines += ["", "## Actual entry-date moneyness", "",
        "| Phase | Leg | DTE45 median signed % | DTE14 median signed % | Difference (pp) | DTE45 ATM/ITM | DTE14 ATM/ITM |",
        "|---:|---|---:|---:|---:|---:|---:|"]
    for r in otm:
        if r["reference_time"] != "entry":
            continue
        delta = r["delta_dte14_minus_dte45_median_signed_otm_pct"]
        delta_text = "—" if delta is None else f"{delta:+.3f} pp"
        n45 = int(r["dte45_atm_n"] or 0) + int(r["dte45_itm_n"] or 0)
        n14 = int(r["dte14_atm_n"] or 0) + int(r["dte14_itm_n"] or 0)
        lines.append(f"| {r['phase']} | {r['leg']} | {pct(r['dte45_median_signed_otm_pct'])} | {pct(r['dte14_median_signed_otm_pct'])} | {delta_text} | {n45} | {n14} |")
    lines += ["", "## Interpretation safeguards", "",
        "- Delta 0.25 is not a fixed OTM percent and not a guaranteed 75% win probability.",
        "- Positive signed distance is OTM; negative is ITM. No selected ATM/ITM row is silently removed.",
        "- The five phases overlap as samples; they are anchor-sensitivity checks, not five independent cohorts.",
        "- Win rate uses resolved trades only. P&L is additive fixed-size cohort P&L. Gross SPY assignment obligation is not broker margin.", "",
        "## Input audit hashes", "",
        f"- DTE45 phase audit SHA-256: {hashlib.sha256((root45 / 'fixed_phase_sensitivity_audit' / 'comparison.json').read_bytes()).hexdigest()}",
        f"- DTE45 OTM manifest SHA-256: {hashlib.sha256(mpath45.read_bytes()).hexdigest()}",
        f"- DTE14 phase audit SHA-256: {hashlib.sha256((root14 / 'fixed_phase_sensitivity_audit' / 'comparison.json').read_bytes()).hexdigest()}",
        f"- DTE14 OTM manifest SHA-256: {hashlib.sha256(mpath14.read_bytes()).hexdigest()}",
        "- performance_comparison.csv: five phases × three windows × four exit policies (60 paired cases).",
        "- otm_comparison.csv: per phase, leg, and signal/entry time (20 paired rows).", ""]
    (out_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")
    manifest = {
        "schema": "qqq-spy-put-fixed-phase-dte14-vs-dte45.v1", "status": "COMPLETED",
        "dte45_selection": D45, "dte14_selection": D14,
        "fixed_strategy": {"entry_filter": "none", "ratio": "1:3", "stride_sessions": 5,
                           "phases": list(PHASES), "target_abs_delta_each_leg": 0.25, "overlap": True},
        "dte45_fixed_anchor_check_statuses": [c["status"] for c in data45["metadata"]["fixed_schedule_checks"]],
        "dte14_fixed_anchor_check_statuses": [c["status"] for c in data14["metadata"]["fixed_schedule_checks"]],
        "performance_rows": len(perf), "otm_summary_rows": len(otm),
        "dte45_fixed_anchor_manifest_sha256": hashlib.sha256((root45 / "fixed_phase_sensitivity_audit" / "comparison.json").read_bytes()).hexdigest(),
        "dte45_otm_manifest_sha256": hashlib.sha256(mpath45.read_bytes()).hexdigest(),
        "dte14_fixed_anchor_manifest_sha256": hashlib.sha256((root14 / "fixed_phase_sensitivity_audit" / "comparison.json").read_bytes()).hexdigest(),
        "dte14_otm_manifest_sha256": hashlib.sha256(mpath14.read_bytes()).hexdigest(),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False), encoding="utf-8")
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dte45-root", type=Path, default=Path("research/qqq_spy_put_fixed_ratio_size_gated_v1/results"))
    p.add_argument("--dte14-root", type=Path, default=Path("research/qqq_spy_put_fixed_ratio_size_gated_v1/results/dte14_fixed_phase"))
    p.add_argument("--out-dir", type=Path, default=Path("research/qqq_spy_put_fixed_ratio_size_gated_v1/results/dte14_vs_dte45_audit"))
    a = p.parse_args()
    r = build(a.dte45_root, a.dte14_root, a.out_dir)
    print(json.dumps({"status": r["status"], "performance_rows": r["performance_rows"],
                      "otm_summary_rows": r["otm_summary_rows"],
                      "dte14_fixed_anchor_check_statuses": r["dte14_fixed_anchor_check_statuses"]}, indent=2))


if __name__ == "__main__":
    main()
