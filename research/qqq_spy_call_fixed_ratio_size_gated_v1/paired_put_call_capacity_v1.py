#!/usr/bin/env python3
"""Pair source-pinned QQQ/SPY PUT 1:6 and CALL 1:6 replays.

Unresolved episodes use their last recorded mark only as a sensitivity proxy.
This is not an order, margin, or broker-liquidation engine.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, statistics
from collections import defaultdict
from pathlib import Path

DTES = (20, 30, 45, 60)
PHASES = (0, 2, 4, 6, 8)
YEARS = 7.792
DATA_END_SESSION_INDEX = 1958
CAPS = (("1", 1), ("2", 2), ("unlimited", None))
PUT_ROOT = Path("research/qqq_spy_put_fixed_ratio_size_gated_v1/results/dte_hold_exit_factorial_v1")
CALL_ROOT = Path("research/qqq_spy_call_fixed_ratio_size_gated_v1/results/dte_hold_exit_factorial_call_v1")
POLICIES_EXPECTED = {
    "HOLD_5_SESSIONS", "HOLD_5_OR_DTE_LE_7", "HOLD_5_OR_DTE_LE_14",
    "HOLD_10_SESSIONS", "HOLD_10_OR_DTE_LE_7", "HOLD_10_OR_DTE_LE_14",
    "HOLD_15_SESSIONS", "HOLD_15_OR_DTE_LE_7", "HOLD_15_OR_DTE_LE_14",
    "HOLD_20_SESSIONS", "HOLD_20_OR_DTE_LE_7", "HOLD_20_OR_DTE_LE_14",
}
MATRIX_FIELDS = [
    "dte_target","phase","exit_policy","capacity_limit","signal_intersection",
    "entry_date_mismatches","cross_expiry_mismatches","eligible_four_leg_pairs",
    "complete_four_leg_pairs_before_capacity","admitted_pairs","skipped_eligible_pairs","skip_pct",
    "put_resolved_pairs_admitted","call_resolved_pairs_admitted","both_resolved_pairs_admitted",
    "unresolved_or_incomplete_pairs_admitted","mark_missing_pairs",
    "put_mark_proxy_total_usd","call_mark_proxy_total_usd","combined_mark_proxy_total_usd",
    "combined_mark_proxy_annual_usd","combined_mark_proxy_median_per_pair_usd",
    "combined_marked_win_pct","realized_both_closed_total_usd","realized_both_closed_annual_usd",
    "worst_combined_pair_mark_usd","peak_gross_put_assignment_plus_call_delivery_usd",
    "put_ledger_git_blob_sha","call_ledger_git_blob_sha","annualization_years",
]
SUMMARY_FIELDS = [
    "dte_target","exit_policy","capacity_limit","phase_count",
    "median_eligible_four_leg_pairs","median_entry_date_mismatches","median_cross_expiry_mismatches",
    "median_admitted_pairs","median_skip_pct","median_both_resolved_pairs",
    "median_combined_mark_proxy_annual_usd","min_phase_combined_mark_proxy_annual_usd",
    "max_phase_combined_mark_proxy_annual_usd","phase_combined_mark_proxy_annual_usd",
    "median_realized_both_closed_annual_usd","min_phase_realized_both_closed_annual_usd",
    "max_phase_realized_both_closed_annual_usd","median_put_mark_proxy_annual_usd",
    "median_call_mark_proxy_annual_usd","worst_combined_pair_mark_usd_across_phases",
    "peak_gross_obligation_usd_across_phases",
]

def git_blob_sha(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()

def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"No episode rows in {path}")
    required = {"signal_date","expiry","entry_date","entry_index","policy","status","exit_index","net_pnl_usd","last_mark_pnl_usd"}
    missing = required.difference(rows[0].keys())
    if missing:
        raise ValueError(f"{path} missing fields: {sorted(missing)}")
    return rows

def num(row: dict[str, str], key: str) -> float | None:
    value = row.get(key, "")
    if value is None or value == "":
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None

def session_index(row: dict[str, str], key: str, fallback: int) -> int:
    value = num(row, key)
    return int(value) if value is not None else fallback

def pnl_mark(row: dict[str, str]) -> float | None:
    return num(row, "net_pnl_usd") if row.get("status") == "RESOLVED" else num(row, "last_mark_pnl_usd")

def median_or_none(values: list[float]) -> float | None:
    values = [v for v in values if math.isfinite(v)]
    return statistics.median(values) if values else None

def money(value: float | None) -> str:
    return "" if value is None or not math.isfinite(value) else f"{value:.2f}"

def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

def load_delta_metadata(root: Path, dte: int, phase: int) -> dict:
    folder = root / f"dte_{dte}" / f"phase_{phase}"
    summary_path, factor_path = folder / "summary.json", folder / "factorial_policy_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
    factor = json.loads(factor_path.read_text(encoding="utf-8")) if factor_path.exists() else {}
    return {
        "summary": summary.get("selection", {}).get("target_abs_delta"),
        "factorial": factor.get("delta_target_abs_both_legs"),
    }

def run(root: Path, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    matrix, metadata = [], []
    loaded_pairs = 0
    for dte in DTES:
        for phase in PHASES:
            pp = root / PUT_ROOT / f"dte_{dte}" / f"phase_{phase}" / "trade_episodes.csv"
            cp = root / CALL_ROOT / f"dte_{dte}" / f"phase_{phase}" / "trade_episodes.csv"
            if not pp.exists() or not cp.exists():
                raise FileNotFoundError(f"Missing ledger: {pp if not pp.exists() else cp}")
            put_rows, call_rows = read_csv(pp), read_csv(cp)
            put_sha, call_sha = git_blob_sha(pp), git_blob_sha(cp)
            loaded_pairs += 1
            pm, cm = load_delta_metadata(root / PUT_ROOT, dte, phase), load_delta_metadata(root / CALL_ROOT, dte, phase)
            metadata.append({"dte":dte,"phase":phase,"put_summary":pm["summary"],"put_factorial":pm["factorial"],"call_summary":cm["summary"],"call_factorial":cm["factorial"]})
            if {r.get("policy","") for r in put_rows} != POLICIES_EXPECTED or {r.get("policy","") for r in call_rows} != POLICIES_EXPECTED:
                raise ValueError(f"Policy grid mismatch at DTE{dte}/phase{phase}")
            for policy in sorted(POLICIES_EXPECTED):
                pmap = {r["signal_date"]:r for r in put_rows if r.get("policy")==policy}
                cmap = {r["signal_date"]:r for r in call_rows if r.get("policy")==policy}
                if len(pmap) != sum(r.get("policy")==policy for r in put_rows) or len(cmap) != sum(r.get("policy")==policy for r in call_rows):
                    raise ValueError(f"Duplicate signal/policy key at DTE{dte}/phase{phase}/{policy}")
                shared = sorted(set(pmap).intersection(cmap))
                same_entry = [s for s in shared if pmap[s].get("entry_date")==cmap[s].get("entry_date")]
                same_expiry = [s for s in same_entry if pmap[s].get("expiry")==cmap[s].get("expiry")]
                cohorts = []
                for sig in same_expiry:
                    p,c = pmap[sig],cmap[sig]
                    pdone, cdone = p.get("status")=="RESOLVED", c.get("status")=="RESOLVED"
                    pexit = session_index(p,"exit_index",DATA_END_SESSION_INDEX) if pdone else DATA_END_SESSION_INDEX
                    cexit = session_index(c,"exit_index",DATA_END_SESSION_INDEX) if cdone else DATA_END_SESSION_INDEX
                    cohorts.append({
                        "signal":sig,"p":p,"c":c,"entry":max(session_index(p,"entry_index",0),session_index(c,"entry_index",0)),
                        "release":max(pexit,cexit) if pdone and cdone else math.inf,
                        "pdone":pdone,"cdone":cdone,"bothdone":pdone and cdone,
                        "ppnl":pnl_mark(p),"cpnl":pnl_mark(c),
                        "pob":num(p,"spy_put_strike_assignment_obligation_usd") or 0.0,
                        "cob":num(c,"spy_call_strike_delivery_obligation_usd") or 0.0,
                        "pexit":pexit,"cexit":cexit,
                    })
                for cap_name,cap_value in CAPS:
                    active,admitted = [],[]
                    for z in sorted(cohorts,key=lambda z:(z["entry"],z["signal"])):
                        active = [a for a in active if a["release"] > z["entry"]]
                        if cap_value is not None and len(active) >= cap_value:
                            continue
                        admitted.append(z); active.append(z)
                    pvals, cvals = [z["ppnl"] for z in admitted], [z["cpnl"] for z in admitted]
                    pairs = [None if z["ppnl"] is None or z["cpnl"] is None else z["ppnl"]+z["cpnl"] for z in admitted]
                    valid = [x for x in pairs if x is not None]
                    done = [z for z in admitted if z["bothdone"]]
                    realized = [z["ppnl"]+z["cpnl"] for z in done if z["ppnl"] is not None and z["cpnl"] is not None]
                    ptotal = sum(pvals) if all(x is not None for x in pvals) else None
                    ctotal = sum(cvals) if all(x is not None for x in cvals) else None
                    btotal = sum(valid) if len(valid)==len(admitted) else None
                    events = []
                    for z in admitted:
                        events.extend([(z["entry"],1,z["pob"]+z["cob"]),(min(z["pexit"],DATA_END_SESSION_INDEX),0,-z["pob"]),(min(z["cexit"],DATA_END_SESSION_INDEX),0,-z["cob"])])
                    events.sort(key=lambda e:(e[0],e[1]))
                    current = peak = 0.0
                    for _,_,change in events:
                        current += change; peak=max(peak,current)
                    skipped = len(cohorts)-len(admitted)
                    matrix.append({
                        "dte_target":dte,"phase":phase,"exit_policy":policy,"capacity_limit":cap_name,
                        "signal_intersection":len(shared),"entry_date_mismatches":len(shared)-len(same_entry),
                        "cross_expiry_mismatches":len(same_entry)-len(same_expiry),
                        "eligible_four_leg_pairs":len(cohorts),"complete_four_leg_pairs_before_capacity":sum(z["bothdone"] for z in cohorts),
                        "admitted_pairs":len(admitted),"skipped_eligible_pairs":skipped,"skip_pct":money(100*skipped/len(cohorts) if cohorts else 0),
                        "put_resolved_pairs_admitted":sum(z["pdone"] for z in admitted),"call_resolved_pairs_admitted":sum(z["cdone"] for z in admitted),
                        "both_resolved_pairs_admitted":len(done),"unresolved_or_incomplete_pairs_admitted":len(admitted)-len(done),
                        "mark_missing_pairs":len(admitted)-len(valid),"put_mark_proxy_total_usd":money(ptotal),"call_mark_proxy_total_usd":money(ctotal),
                        "combined_mark_proxy_total_usd":money(btotal),"combined_mark_proxy_annual_usd":money(btotal/YEARS if btotal is not None else None),
                        "combined_mark_proxy_median_per_pair_usd":money(median_or_none(valid)),
                        "combined_marked_win_pct":money(100*sum(x>0 for x in valid)/len(valid) if valid else None),
                        "realized_both_closed_total_usd":money(sum(realized)),"realized_both_closed_annual_usd":money(sum(realized)/YEARS),
                        "worst_combined_pair_mark_usd":money(min(valid) if valid else None),
                        "peak_gross_put_assignment_plus_call_delivery_usd":money(peak),
                        "put_ledger_git_blob_sha":put_sha,"call_ledger_git_blob_sha":call_sha,"annualization_years":YEARS,
                    })
    expected = len(DTES)*len(PHASES)*len(POLICIES_EXPECTED)*len(CAPS)
    if loaded_pairs != len(DTES)*len(PHASES) or len(matrix) != expected:
        raise ValueError(f"Incomplete matrix: loaded phase pairs={loaded_pairs}; rows={len(matrix)}; expected={expected}")
    keys=[(r["dte_target"],r["phase"],r["exit_policy"],r["capacity_limit"]) for r in matrix]
    if len(keys)!=len(set(keys)): raise ValueError("Duplicate matrix rows")
    write_csv(output/"paired_put_call_capacity_matrix.csv",MATRIX_FIELDS,matrix)
    groups=defaultdict(list)
    for row in matrix: groups[(row["dte_target"],row["exit_policy"],row["capacity_limit"])].append(row)
    summary=[]
    for (dte,policy,cap),rows in sorted(groups.items()):
        marked=[float(r["combined_mark_proxy_annual_usd"]) for r in rows if r["combined_mark_proxy_annual_usd"]!=""]
        realized=[float(r["realized_both_closed_annual_usd"]) for r in rows if r["realized_both_closed_annual_usd"]!=""]
        putann=[float(r["put_mark_proxy_total_usd"])/YEARS for r in rows if r["put_mark_proxy_total_usd"]!=""]
        callann=[float(r["call_mark_proxy_total_usd"])/YEARS for r in rows if r["call_mark_proxy_total_usd"]!=""]
        summary.append({
            "dte_target":dte,"exit_policy":policy,"capacity_limit":cap,"phase_count":len(rows),
            "median_eligible_four_leg_pairs":money(median_or_none([float(r["eligible_four_leg_pairs"]) for r in rows])),
            "median_entry_date_mismatches":money(median_or_none([float(r["entry_date_mismatches"]) for r in rows])),
            "median_cross_expiry_mismatches":money(median_or_none([float(r["cross_expiry_mismatches"]) for r in rows])),
            "median_admitted_pairs":money(median_or_none([float(r["admitted_pairs"]) for r in rows])),
            "median_skip_pct":money(median_or_none([float(r["skip_pct"]) for r in rows])),
            "median_both_resolved_pairs":money(median_or_none([float(r["both_resolved_pairs_admitted"]) for r in rows])),
            "median_combined_mark_proxy_annual_usd":money(median_or_none(marked)),
            "min_phase_combined_mark_proxy_annual_usd":money(min(marked) if marked else None),
            "max_phase_combined_mark_proxy_annual_usd":money(max(marked) if marked else None),
            "phase_combined_mark_proxy_annual_usd":"|".join(f'{r["phase"]}:{r["combined_mark_proxy_annual_usd"]}' for r in rows),
            "median_realized_both_closed_annual_usd":money(median_or_none(realized)),
            "min_phase_realized_both_closed_annual_usd":money(min(realized) if realized else None),
            "max_phase_realized_both_closed_annual_usd":money(max(realized) if realized else None),
            "median_put_mark_proxy_annual_usd":money(median_or_none(putann)),
            "median_call_mark_proxy_annual_usd":money(median_or_none(callann)),
            "worst_combined_pair_mark_usd_across_phases":money(min(float(r["worst_combined_pair_mark_usd"]) for r in rows if r["worst_combined_pair_mark_usd"]!="")),
            "peak_gross_obligation_usd_across_phases":money(max(float(r["peak_gross_put_assignment_plus_call_delivery_usd"]) for r in rows if r["peak_gross_put_assignment_plus_call_delivery_usd"]!="")),
        })
    if len(summary)!=len(DTES)*len(POLICIES_EXPECTED)*len(CAPS): raise ValueError(f"Incomplete summary: {len(summary)} rows")
    write_csv(output/"paired_put_call_capacity_summary.csv",SUMMARY_FIELDS,summary)
    md=[
      "# Paired QQQ/SPY PUT + CALL capacity audit","",
      "- Historical window: 2018-03-01 to 2025-12-15; annualization denominator 7.792 calendar years.",
      "- Entry cadence: every 10 common QQQ/SPY sessions; phase anchors 0, 2, 4, 6, 8.",
      "- PUT: QQQ LONG PUT 1 : SPY SHORT PUT 6, target absolute Delta 0.25.",
      "- CALL: QQQ LONG CALL 1 : SPY SHORT CALL 6, target absolute Delta 0.20.",
      "- A paired cohort must share signal date, actual entry date, expiry across all four legs, and exit policy. If a sleeve does not align, neither side enters that paired cohort.",
      "- Capacity gate: maximum 1, maximum 2, or unlimited paired cohorts. A slot is released only when both sleeves are resolved; unresolved cohorts retain the slot to the end of the source history.",
      "- Source ledgers already include $0.05 option-share slippage per side and $0.65 per contract per side.",
      "",
      "## Output definitions","",
      f"- Loaded {loaded_pairs} PUT/CALL phase pairs; produced {len(matrix)} matrix rows and {len(summary)} summary rows.",
      "- The matrix contains DTE × phase × exit policy × capacity. Every row records the Git blob SHA for each source ledger.",
      "- Mark-proxy P&L uses realized net P&L for resolved episodes and the last recorded mark for unresolved episodes. The latter is not guaranteed executable or realized.",
      "- Annualized P&L is total additive trade P&L divided by 7.792 years; it is not CAGR, account return, or withdrawable income.",
      "- Peak gross obligation adds open SPY short-PUT assignment notional and open SPY short-CALL delivery notional without netting. It is not broker margin or maximum loss.",
      "",
      "## Delta metadata audit","",
      "The CALL per-phase summary files and selected raw CALL deltas support target absolute Delta 0.20. Existing generated CALL factorial summary labels and narrative report hardcode 0.25. This is a reporting metadata defect; the pair calculations use raw per-episode P&L/contract-selection ledgers and do not use that conflicting label.",
      "",
      "| DTE | Phase | PUT target in summary | PUT factorial label | CALL target in summary | CALL factorial label |",
      "|---:|---:|---:|---:|---:|---:|",
    ]
    for m in metadata:
        md.append(f'| {m["dte"]} | {m["phase"]} | {m["put_summary"]} | {m["put_factorial"]} | {m["call_summary"]} | {m["call_factorial"]} |')
    md.extend(["","## Focal scan: hold 20 sessions or exit at remaining DTE ≤ 7","","| DTE | Capacity | Median annual mark proxy | Phase minimum | Phase maximum | Median skipped % | Median admitted pairs | Worst paired mark | Peak gross obligation |","|---:|---|---:|---:|---:|---:|---:|---:|---:|"])
    for r in summary:
        if r["exit_policy"]!="HOLD_20_OR_DTE_LE_7": continue
        vals=[float(v.split(":",1)[1]) for v in r["phase_combined_mark_proxy_annual_usd"].split("|") if v.split(":",1)[1]!=""]
        md.append(f'| {r["dte_target"]} | {r["capacity_limit"]} | {float(r["median_combined_mark_proxy_annual_usd"]):,.0f} | {min(vals):,.0f} | {max(vals):,.0f} | {float(r["median_skip_pct"]):.1f}% | {float(r["median_admitted_pairs"]):.0f} | {float(r["worst_combined_pair_mark_usd_across_phases"]):,.0f} | {float(r["peak_gross_obligation_usd_across_phases"]):,.0f} |')
    md.extend(["","## DTE60, max 15 sessions","","A remaining-DTE guard of ≤14 does not activate during a 15-session hold from DTE60; this is effectively a 15-session max-hold test, not proof that the guard itself helps.","","| Capacity | Median annual mark proxy | Phase minimum | Phase maximum | Median skipped % | Median admitted pairs | Median PUT mark/year | Median CALL mark/year | Median realized both-closed P&L/year | Worst paired mark | Peak gross obligation |","|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"])
    for cap in ("1","2","unlimited"):
        r=next(x for x in summary if x["dte_target"]==60 and x["exit_policy"]=="HOLD_15_OR_DTE_LE_14" and x["capacity_limit"]==cap)
        vals=[float(v.split(":",1)[1]) for v in r["phase_combined_mark_proxy_annual_usd"].split("|") if v.split(":",1)[1]!=""]
        md.append(f'| {cap} | {float(r["median_combined_mark_proxy_annual_usd"]):,.0f} | {min(vals):,.0f} | {max(vals):,.0f} | {float(r["median_skip_pct"]):.1f}% | {float(r["median_admitted_pairs"]):.0f} | {float(r["median_put_mark_proxy_annual_usd"]):,.0f} | {float(r["median_call_mark_proxy_annual_usd"]):,.0f} | {float(r["median_realized_both_closed_annual_usd"]):,.0f} | {float(r["worst_combined_pair_mark_usd_across_phases"]):,.0f} | {float(r["peak_gross_obligation_usd_across_phases"]):,.0f} |')
    md.extend(["","## Boundary of this audit","","This is a research pairing audit, not a strategy PASS. It does not generate a daily combined equity curve or portfolio max drawdown, and does not model broker margin, forced liquidation, assignment timing, or whether size-insufficient quotes could actually be exited. The QQQ long option does not cap the six SPY short options because the underlyings differ. The five phase anchors are descriptive, not out-of-sample proof.",""])
    (output/"PAIRED_PUT_CALL_AUDIT.md").write_text("\n".join(md),encoding="utf-8")

if __name__ == "__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root",type=Path,default=Path("."))
    ap.add_argument("--output-dir",type=Path,required=True)
    args=ap.parse_args()
    run(args.repo_root.resolve(),args.output_dir.resolve())
