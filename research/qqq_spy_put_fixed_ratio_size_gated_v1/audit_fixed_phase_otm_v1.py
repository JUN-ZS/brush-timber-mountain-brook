#!/usr/bin/env python3
"""Audit realized PUT out-of-the-money distance from the selected strikes and underlying spots."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

PHASES = range(5)
TARGET_ABS_DELTA = 0.25
DELTA_BAND = (0.10, 0.50)
LEGS = (
    ("QQQ", "qqq_contract_id", "qqq_strike", "qqq_spot_signal", "qqq_spot_entry",
     "qqq_abs_delta", "qqq_otm_pct_signal", "qqq_moneyness_signal",
     "qqq_otm_pct_entry", "qqq_moneyness_entry", "LONG"),
    ("SPY", "spy_contract_id", "spy_strike", "spy_spot_signal", "spy_spot_entry",
     "spy_abs_delta", "spy_otm_pct_signal", "spy_moneyness_signal",
     "spy_otm_pct_entry", "spy_moneyness_entry", "SHORT"),
)
REQUIRED = {
    "episode_id", "signal_date", "entry_date", "expiry",
    "qqq_contract_id", "spy_contract_id", "qqq_strike", "spy_strike",
    "qqq_spot_signal", "spy_spot_signal", "qqq_spot_entry", "spy_spot_entry",
    "qqq_abs_delta", "spy_abs_delta",
    "qqq_otm_pct_signal", "qqq_moneyness_signal", "spy_otm_pct_signal", "spy_moneyness_signal",
    "qqq_otm_pct_entry", "qqq_moneyness_entry", "spy_otm_pct_entry", "spy_moneyness_entry",
}


def number(value: Any, name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name}: missing/non-numeric value {value!r}") from None
    if not math.isfinite(result):
        raise ValueError(f"{name}: non-finite value {value!r}")
    return result


def put_moneyness(spot: Any, strike: Any) -> dict[str, float | str]:
    """Positive distance means OTM for a put; negative means ITM."""
    s = number(spot, "spot")
    k = number(strike, "strike")
    if s <= 0 or k <= 0:
        raise ValueError(f"spot and strike must be > 0; got spot={s}, strike={k}")
    pct = (s - k) / s * 100.0
    status = "OTM" if k < s else "ITM" if k > s else "ATM"
    return {"otm_pct": pct, "status": status}


def close_enough(left: float, right: float, *, tolerance: float = 1e-5) -> bool:
    return abs(left - right) <= tolerance


def validate_contract_id(value: str, symbol: str, phase: int, episode_id: str) -> None:
    ident = re.sub(r"\s+", "", str(value or "").upper())
    if ident.startswith("O:"):
        ident = ident[2:]
    if not re.fullmatch(re.escape(symbol) + r"\d{6}P\d{8}", ident):
        raise ValueError(
            f"phase {phase} episode {episode_id}: invalid standard {symbol} PUT identity {value!r}"
        )


def make_detail_rows(phase: int, rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    details: list[dict[str, Any]] = []
    delta_rows: list[dict[str, Any]] = []
    for row in rows:
        missing = sorted(REQUIRED - set(row))
        if missing:
            raise ValueError(f"phase {phase} entry ledger missing columns: {missing}")
        eid = str(row.get("episode_id", ""))
        signal_date, entry_date = row.get("signal_date", ""), row.get("entry_date", "")
        for symbol, id_col, strike_col, signal_spot_col, entry_spot_col, delta_col, signal_pct_col, signal_status_col, entry_pct_col, entry_status_col, side in LEGS:
            validate_contract_id(row.get(id_col, ""), symbol, phase, eid)
            strike = number(row.get(strike_col), f"{symbol} strike")
            signal_spot = number(row.get(signal_spot_col), f"{symbol} signal spot")
            entry_spot = number(row.get(entry_spot_col), f"{symbol} entry spot")
            delta = abs(number(row.get(delta_col), f"{symbol} abs delta"))
            if not (DELTA_BAND[0] - 1e-8 <= delta <= DELTA_BAND[1] + 1e-8):
                raise ValueError(f"phase {phase} episode {eid}: {symbol} abs Delta {delta} outside {DELTA_BAND}")
            signal = put_moneyness(signal_spot, strike)
            entry = put_moneyness(entry_spot, strike)
            recorded_signal_pct = number(row.get(signal_pct_col), f"{symbol} recorded signal OTM pct")
            recorded_entry_pct = number(row.get(entry_pct_col), f"{symbol} recorded entry OTM pct")
            if not close_enough(float(signal["otm_pct"]), recorded_signal_pct):
                raise ValueError(
                    f"phase {phase} episode {eid}: {symbol} signal OTM percentage does not reconcile "
                    f"({recorded_signal_pct} vs recomputed {signal['otm_pct']})"
                )
            if not close_enough(float(entry["otm_pct"]), recorded_entry_pct):
                raise ValueError(
                    f"phase {phase} episode {eid}: {symbol} entry OTM percentage does not reconcile "
                    f"({recorded_entry_pct} vs recomputed {entry['otm_pct']})"
                )
            if row.get(signal_status_col) != signal["status"]:
                raise ValueError(f"phase {phase} episode {eid}: {symbol} signal moneyness status mismatch")
            if row.get(entry_status_col) != entry["status"]:
                raise ValueError(f"phase {phase} episode {eid}: {symbol} entry moneyness status mismatch")
            details.append({
                "phase": phase, "episode_id": eid, "signal_date": signal_date, "entry_date": entry_date,
                "expiry": row.get("expiry", ""), "leg": symbol, "position_side": side,
                "contract_id": row.get(id_col, ""), "strike": strike,
                "spot_at_signal": signal_spot, "otm_pct_at_signal": float(signal["otm_pct"]),
                "moneyness_at_signal": signal["status"],
                "spot_at_entry": entry_spot, "otm_pct_at_entry": float(entry["otm_pct"]),
                "moneyness_at_entry": entry["status"], "abs_delta_at_signal": delta,
                "abs_delta_target": TARGET_ABS_DELTA, "abs_delta_gap": abs(delta - TARGET_ABS_DELTA),
                "long_qqq_qty": row.get("long_qqq_qty", ""), "short_spy_qty": row.get("short_spy_qty", ""),
            })
            delta_rows.append({
                "phase": phase, "leg": symbol, "episode_id": eid,
                "abs_delta": delta, "abs_delta_gap": abs(delta - TARGET_ABS_DELTA),
            })
    return details, delta_rows


def summarize_moneyness(details: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[int, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in details:
        for when in ("signal", "entry"):
            groups[(int(row["phase"]), str(row["leg"]), when)].append(row)
    summaries = []
    for (phase, leg, when), rows in sorted(groups.items()):
        pcts = [float(r[f"otm_pct_at_{when}"]) for r in rows]
        positive = [v for v in pcts if v > 1e-9]
        atm = sum(abs(v) <= 1e-9 for v in pcts)
        itm = sum(v < -1e-9 for v in pcts)
        otm = len(positive)
        summaries.append({
            "phase": phase, "leg": leg, "reference_time": when, "n": len(pcts),
            "otm_n": otm, "atm_n": atm, "itm_n": itm, "non_otm_n": atm + itm,
            "non_otm_pct": (atm + itm) / len(pcts) * 100 if pcts else None,
            "mean_signed_otm_pct": statistics.mean(pcts) if pcts else None,
            "median_signed_otm_pct": statistics.median(pcts) if pcts else None,
            "min_signed_otm_pct": min(pcts) if pcts else None,
            "max_signed_otm_pct": max(pcts) if pcts else None,
            "mean_otm_pct_when_otm": statistics.mean(positive) if positive else None,
            "median_otm_pct_when_otm": statistics.median(positive) if positive else None,
            "min_otm_pct_when_otm": min(positive) if positive else None,
            "max_otm_pct_when_otm": max(positive) if positive else None,
        })
    return summaries


def summarize_delta(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(int(row["phase"]), str(row["leg"]))].append(row)
    out = []
    for (phase, leg), values in sorted(groups.items()):
        deltas = [float(r["abs_delta"]) for r in values]
        gaps = [float(r["abs_delta_gap"]) for r in values]
        out.append({
            "phase": phase, "leg": leg, "n": len(deltas), "target_abs_delta": TARGET_ABS_DELTA,
            "mean_abs_delta": statistics.mean(deltas), "median_abs_delta": statistics.median(deltas),
            "min_abs_delta": min(deltas), "max_abs_delta": max(deltas),
            "mean_abs_delta_gap": statistics.mean(gaps), "median_abs_delta_gap": statistics.median(gaps),
            "delta_outside_eligibility_band_n": sum(not (DELTA_BAND[0] <= d <= DELTA_BAND[1]) for d in deltas),
        })
    return out


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build(results_root: Path, out_dir: Path) -> dict[str, Any]:
    all_details: list[dict[str, Any]] = []
    all_delta: list[dict[str, Any]] = []
    input_hashes = []
    phase_counts = []
    for phase in PHASES:
        path = results_root / "fixed_phase_sensitivity" / f"phase_{phase}" / "entry_cohort.csv"
        if not path.is_file():
            raise FileNotFoundError(f"missing phase entry ledger: {path}")
        rows = read_csv(path)
        details, delta = make_detail_rows(phase, rows)
        all_details.extend(details)
        all_delta.extend(delta)
        input_hashes.append({
            "phase": phase, "path": str(path),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "entry_cohort_rows": len(rows),
        })
        phase_counts.append({
            "phase": phase, "entry_cohort_rows": len(rows),
            "leg_rows": len(details), "selected_pairs": len(rows),
            "non_otm_at_entry_leg_rows": sum(r["moneyness_at_entry"] != "OTM" for r in details),
        })
    moneyness_summary = summarize_moneyness(all_details)
    delta_summary = summarize_delta(all_delta)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "entry_leg_otm_detail.csv", all_details)
    write_csv(out_dir / "phase_leg_otm_summary.csv", moneyness_summary)
    write_csv(out_dir / "phase_leg_delta_summary.csv", delta_summary)
    non_otm_entries = sum(int(r["non_otm_at_entry_leg_rows"]) for r in phase_counts)
    phase_notes = []
    for row in moneyness_summary:
        if row["reference_time"] == "entry" and row["non_otm_n"]:
            phase_notes.append(
                f"Phase {row['phase']} {row['leg']}: {row['non_otm_n']}/{row['n']} entries are ATM/ITM "
                f"({row['non_otm_pct']:.2f}%)."
            )
    status = "WARN_NON_OTM_LEGS_FOUND" if non_otm_entries else "PASS_ALL_SELECTED_LEGS_OTM_AT_ENTRY"
    report_lines = [
        "# QQQ LONG PUT / SPY SHORT PUT — Realized OTM Distance Audit",
        "",
        f"Status: {status}",
        "",
        "- OTM percent is recomputed as (underlying spot - put strike) / underlying spot × 100.",
        "- Positive percentage = OTM; 0% = ATM; negative percentage = ITM.",
        "- Both signal-date spot and actual entry-date spot are measured. Entry-date moneyness is the primary execution-time diagnostic.",
        f"- Candidate Delta target remains absolute Delta {TARGET_ABS_DELTA:.2f}; eligible absolute-Delta band remains {DELTA_BAND[0]:.2f}–{DELTA_BAND[1]:.2f}. No P&L-driven re-selection or entry filter was added.",
        "- These are EOD underlying prices and option-chain Delta/quotes, not verified fills. Delta is not treated as an exact probability.",
        "",
        "## Actual entry distance by phase and leg",
        "",
        "| Phase | Leg | N | OTM | ATM | ITM | Mean signed % | Median signed % | Mean % among OTM only | Median % among OTM only | Min signed % | Max signed % |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in moneyness_summary:
        if r["reference_time"] != "entry":
            continue
        fmt = lambda v: "—" if v is None else f"{v:.3f}%"
        report_lines.append(
            f"| {r['phase']} | {r['leg']} | {r['n']} | {r['otm_n']} | {r['atm_n']} | {r['itm_n']} | "
            f"{fmt(r['mean_signed_otm_pct'])} | {fmt(r['median_signed_otm_pct'])} | "
            f"{fmt(r['mean_otm_pct_when_otm'])} | {fmt(r['median_otm_pct_when_otm'])} | "
            f"{fmt(r['min_signed_otm_pct'])} | {fmt(r['max_signed_otm_pct'])} |"
        )
    report_lines += [
        "",
        "## Interpretation",
        "",
        f"- Status across all five phase ledgers: {status}; count of selected entry-leg rows that are ATM/ITM: **{non_otm_entries}**.",
        "- Mean/median signed distance include ITM observations as negative values. The OTM-only columns are conditioned on being strictly OTM and must not hide the separate ATM/ITM counts.",
        "- No non-OTM row is silently filtered. A non-OTM finding is reported as a warning, preserving the original Delta-based selection so the diagnostic cannot improve results by changing the sample.",
    ]
    if phase_notes:
        report_lines += ["", "### Non-OTM warnings", ""] + [f"- {note}" for note in phase_notes]
    else:
        report_lines += ["", "No selected contract was ATM or ITM at the actual entry-date underlying close."]
    report_lines += [
        "",
        "## Delta diagnostics",
        "",
        "| Phase | Leg | N | Mean abs Delta | Median | Min | Max | Mean distance from target |",
        "|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in delta_summary:
        report_lines.append(
            f"| {r['phase']} | {r['leg']} | {r['n']} | {r['mean_abs_delta']:.4f} | "
            f"{r['median_abs_delta']:.4f} | {r['min_abs_delta']:.4f} | {r['max_abs_delta']:.4f} | "
            f"{r['mean_abs_delta_gap']:.4f} |"
        )
    report_lines += [
        "",
        "## Files",
        "",
        "- entry_leg_otm_detail.csv: one record per phase × entry cohort × leg, with spot, strike, signed OTM percent and moneyness status at signal and entry.",
        "- phase_leg_otm_summary.csv: phase/leg distributions at signal and entry.",
        "- phase_leg_delta_summary.csv: actual selected Delta distribution per phase and leg.",
        "- manifest.json: input hashes and reconciliation summary.",
        "",
    ]
    (out_dir / "report.md").write_text("\n".join(report_lines), encoding="utf-8")
    manifest = {
        "schema": "qqq-spy-put-realized-otm-audit.v1",
        "status": status,
        "delta_target_abs": TARGET_ABS_DELTA,
        "delta_eligible_band": list(DELTA_BAND),
        "otm_formula": "(spot - strike) / spot * 100",
        "phase_count": len(phase_counts),
        "input_ledgers": input_hashes,
        "phase_counts": phase_counts,
        "detail_leg_rows": len(all_details),
        "summary_rows": len(moneyness_summary),
        "delta_summary_rows": len(delta_summary),
        "non_otm_at_entry_leg_rows": non_otm_entries,
        "warning_notes": phase_notes,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-root", type=Path, default=Path("research/qqq_spy_put_fixed_ratio_size_gated_v1/results"))
    parser.add_argument("--out-dir", type=Path, default=Path("research/qqq_spy_put_fixed_ratio_size_gated_v1/results/fixed_phase_otm_audit"))
    args = parser.parse_args()
    manifest = build(args.results_root, args.out_dir)
    print(json.dumps({
        "status": manifest["status"], "phase_count": manifest["phase_count"],
        "detail_leg_rows": manifest["detail_leg_rows"],
        "non_otm_at_entry_leg_rows": manifest["non_otm_at_entry_leg_rows"],
        "out_dir": str(args.out_dir),
    }, indent=2))


if __name__ == "__main__":
    main()
