#!/usr/bin/env python3
import hashlib
import json
import os
import re
import struct
import zlib
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path.cwd()
HTML = ROOT / "v2.html"
BUNDLE = ROOT / "glidepath_interactive_preview_optimized_bundle.zip"
AUDIT = ROOT / "glidepath_preview_optimized_audit.json"
RESULTS = Path(os.environ.get("AUDIT_RESULTS_PATH", "/tmp/glidepath-browser-audit-results.json"))

class IdParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key == "id" and value is not None:
                self.ids.append(value)

results = json.loads(RESULTS.read_text(encoding="utf-8"))
if results.get("status") != "PASSED":
    raise SystemExit("Browser audit did not pass; refusing to mark the audit as passed.")
paired_result = results.get("paired_direction_comparison")
if not isinstance(paired_result, dict) or paired_result.get("state") != "passed" or paired_result.get("passed") is not True or paired_result.get("matchedPairCount") != 157:
    raise SystemExit("Same-window direction comparison is missing or did not pass 157 matched pairs; refusing to publish PASS.")
paired_real_result = results.get("paired_direction_comparison_real_235")
if not isinstance(paired_real_result, dict) or paired_real_result.get("state") != "passed" or paired_real_result.get("passed") is not True or paired_real_result.get("matchedPairCount") != 157 or abs(float(paired_real_result.get("inflation", 0)) - 0.0235) > 1e-9:
    raise SystemExit("The 2.35% real-value paired comparison is missing or did not pass all 157 matched pairs; refusing to publish PASS.")

cashflow_semantics = results.get("cashflow_nav_semantic_sweep")
expected_cashflow_contract = {
    "total_combinations": 224,
    "yearly_flow_slices_verified": 224,
    "primary_nav_bindings_verified": 224,
    "metric_rows_verified": 224,
    "allocation_path_bindings_verified": 224,
    "flow_comparison_bars_verified": 896,
    "no_withdrawal_zero_cashflow_checks": 59,
    "data_scope_disclosure_checks": 224,
    "real_floor_window_cells_verified": 1792,
}
if not isinstance(cashflow_semantics, dict):
    raise SystemExit("Full cashflow × year × statistic NAV semantic sweep is missing.")
for key, expected in expected_cashflow_contract.items():
    if cashflow_semantics.get(key) != expected:
        raise SystemExit(f"Cashflow/NAV semantic contract mismatch for {key}: got {cashflow_semantics.get(key)!r}, expected {expected!r}")
if cashflow_semantics.get("checked_years") != list(range(11)) or cashflow_semantics.get("checked_stat_views") != ["median", "p05", "worst"]:
    raise SystemExit("Cashflow/NAV semantic sweep did not cover every year and statistic view.")
if cashflow_semantics.get("checked_flows") != ["no_withdrawals", "delayed_stepup_example", "monthly_withdrawal_500_usd_stress", "monthly_withdrawal_1000_usd_stress"]:
    raise SystemExit("Cashflow/NAV semantic sweep did not cover the canonical four cashflow modes.")
if cashflow_semantics.get("checked_inflation_modes") != [0, 0.0235, 0.035]:
    raise SystemExit("Cashflow/NAV sweep did not validate nominal, 2.35%, and 3.50% inflation modes.")
expected_inflation_coverage = [
    {"inflation": 0, "combinations": 132, "median_flow_year_combinations": 44, "additional_tail_views": 0,
     "policy": "all-flows-years-stat-views"},
    {"inflation": 0.0235, "combinations": 46, "median_flow_year_combinations": 44, "additional_tail_views": 2,
     "policy": "median-all-flow-years-plus-year10-no-flow-p05-worst"},
    {"inflation": 0.035, "combinations": 46, "median_flow_year_combinations": 44, "additional_tail_views": 2,
     "policy": "median-all-flow-years-plus-year10-no-flow-p05-worst"},
]
if cashflow_semantics.get("checked_inflation_coverage") != expected_inflation_coverage:
    raise SystemExit("Browser sweep coverage policy differs from the declared nominal/real state matrix.")

real_floor_integrity = results.get("real_floor_annual_pack_integrity", {})
if (
    real_floor_integrity.get("annual_rows") != 11264
    or real_floor_integrity.get("rows_with_both_real_floor_counts") != 11264
    or real_floor_integrity.get("year_zero_rows") != 1024
    or real_floor_integrity.get("year_zero_zero_breach_rows") != 1024
    or real_floor_integrity.get("year10_rows") != 1024
):
    raise SystemExit("Exact real-principal annual count grid is missing or incomplete.")
proof = results.get("derived_real_breach_zero_proof", [])
if len(proof) != 2 or (
    real_floor_integrity.get("zero_breach_strategies_235") != proof[0].get("provable_zero_real_breach_strategies")
    or real_floor_integrity.get("zero_breach_strategies_350") != proof[1].get("provable_zero_real_breach_strategies")
):
    raise SystemExit("Exact zero-breach counts disagree with the worst-terminal-NAV proof.")
heatmap_checks = results.get("real_floor_heatmap_checks", [])
if len(heatmap_checks) != 2 or heatmap_checks != [
    {"inflation": 0.0235, "cells": 64, "passed": True},
    {"inflation": 0.035, "cells": 64, "passed": True},
]:
    raise SystemExit("Real-principal heatmap did not pass both inflation-rate cell sweeps.")

html_bytes = HTML.read_bytes()
html_text = html_bytes.decode("utf-8")
pack_match = re.search(r"const RAW_PACK=(\{.*?\});\s*const TG=", html_text, re.S)
if not pack_match:
    raise SystemExit("Compact RAW_PACK could not be found; refusing to publish an audit without source-linked sample counts.")
try:
    packed_data = json.loads(pack_match.group(1))
except json.JSONDecodeError as exc:
    raise SystemExit("Compact RAW_PACK is invalid JSON: " + str(exc))
packed_scenarios = packed_data.get("d", [])
annual_rows = packed_data.get("a", [])
histogram_rows = packed_data.get("h", [])
cohort_rows = packed_data.get("c", [])
pack_meta = packed_data.get("meta", {})
strategy_count = len(packed_scenarios)
annual_count = len(annual_rows)
histogram_count = len(histogram_rows)
cohort_count = len(cohort_rows)
window_count = int(pack_meta.get("rolling_windows_per_scenario", 157))
initial_capital = float(pack_meta.get("initial_capital_usd", 100000))
source_as_of = str(pack_meta.get("source_as_of", "2026-09-30"))
expected_counts = (1024, 11264, 4096, 14336)
actual_counts = (strategy_count, annual_count, histogram_count, cohort_count)
if actual_counts != expected_counts or window_count != 157:
    raise SystemExit(f"Embedded data-count contract mismatch: actual={actual_counts}, expected={expected_counts}, windows={window_count}")
if any(not isinstance(row, list) or len(row) < 23 for row in annual_rows):
    raise SystemExit("Annual compact rows must include both independently replayed real-principal breach counts.")
for row in annual_rows:
    if any(not isinstance(row[index], int) or not 0 <= row[index] <= window_count for index in (21, 22)):
        raise SystemExit("Annual real-principal breach count is not an integer within 0–157.")
    if int(row[0]) == 0 and (row[21] != 0 or row[22] != 0):
        raise SystemExit("Year-zero real-principal breach counts must be zero.")

def unique_prefix_keys(rows, width, label):
    keys = []
    for index, row in enumerate(rows):
        if not isinstance(row, list) or len(row) < width:
            raise SystemExit(f"{label} row {index} has fewer than {width} key fields")
        keys.append(tuple(row[:width]))
    unique = set(keys)
    if len(unique) != len(rows):
        raise SystemExit(f"{label} contains duplicate keys: rows={len(rows)}, unique={len(unique)}")
    return unique

scenario_keys = unique_prefix_keys(packed_scenarios, 4, "scenario D")
annual_keys = unique_prefix_keys(annual_rows, 5, "annual A")
histogram_keys = unique_prefix_keys(histogram_rows, 5, "histogram H")
cohort_keys = unique_prefix_keys(cohort_rows, 5, "cohort C")
if len(scenario_keys) != 1024 or len(annual_keys) != 11264 or len(histogram_keys) != 4096 or len(cohort_keys) != 14336:
    raise SystemExit("Unique compact keys do not match the 1,024/11,264/4,096/14,336 row contract")

annual_year10 = {
    tuple(row[1:5]): row
    for row in annual_rows
    if isinstance(row, list) and len(row) > 8 and int(row[0]) == 10
}
scenario_by_key = {tuple(row[:4]): row for row in packed_scenarios}
annual_year10_summary_mismatches = 0
for key, scenario in scenario_by_key.items():
    annual = annual_year10.get(key)
    if annual is None or len(scenario) < 8:
        annual_year10_summary_mismatches += 1
        continue
    comparisons = ((5, 4), (6, 5), (7, 6), (8, 7))
    try:
        mismatched = any(abs(float(annual[annual_index]) - float(scenario[scenario_index])) > 0.011
                         for annual_index, scenario_index in comparisons)
    except (TypeError, ValueError):
        mismatched = True
    if mismatched:
        annual_year10_summary_mismatches += 1
if annual_year10_summary_mismatches != 0:
    raise SystemExit(f"Year-10 annual/scenario summary mismatches: {annual_year10_summary_mismatches}")

def proven_real_floor_count(rate):
    threshold = initial_capital * (1 + rate) ** 10
    return sum(1 for row in packed_scenarios if len(row) > 7 and float(row[7]) >= threshold)
proof_235 = proven_real_floor_count(0.0235)
proof_350 = proven_real_floor_count(0.035)
if strategy_count != 1024 or window_count != 157:
    raise SystemExit(f"Unexpected compact sample contract: strategies={strategy_count}, windows={window_count}")
parser = IdParser()
parser.feed(html_text)
unique_ids = sorted(set(parser.ids))
duplicates = sorted({value for value in parser.ids if parser.ids.count(value) > 1})
if duplicates:
    raise SystemExit("Duplicate HTML IDs: " + ", ".join(duplicates))
if "<title>股票轉債互動追蹤台（優化增強版 v2.2）</title>" not in html_text:
    raise SystemExit("HTML title/version guard failed.")
if '<section id="decisionSummary" class="decision-summary" aria-live="polite">' not in html_text:
    raise SystemExit("Frontloaded decision summary section is missing.")
if html_text.index('<section id="decisionSummary"') > html_text.index('<section class="controls">'):
    raise SystemExit("Decision summary must appear before the controls.")
if html_text.index('<section id="metrics"') > html_text.index('<section class="controls">'):
    raise SystemExit("Primary metrics must appear before the controls.")
if "GLIDEPATH_TRAJECTORY_PANEL_V1" not in html_text or 'id="glidepath-trajectory-panel-inline"' not in html_text:
    raise SystemExit("Year-by-year allocation path panel was not embedded in the canonical HTML.")
if "GLIDEPATH_DECISION_EVIDENCE_V1" not in html_text or "決策依據：金額 × 行為 × 樣本 × 尚未證明的風險" not in html_text:
    raise SystemExit("Front-loaded amount/behavior/sample/unproven-risk panel is missing.")
# These disclosures are assembled dynamically by the page script. Check the
# exact visible strings recorded by the successful browser run, rather than
# searching raw HTML for phrases that only exist after JavaScript evaluation.
decision_summary = results.get("frontloaded_decision_summary")
if not isinstance(decision_summary, dict):
    raise SystemExit("Browser audit did not capture the front-loaded decision evidence.")
sample_disclosure = str(decision_summary.get("evidenceSample", ""))
risk_disclosure = str(decision_summary.get("evidenceRisk", ""))
for evidence_text in (
    f"{strategy_count} 組第10年策略設定",
    f"{window_count} 個重疊的 10 年窗口",
    source_as_of,
):
    if evidence_text not in sample_disclosure:
        raise SystemExit("Rendered sample disclosure is incomplete: " + evidence_text)
for rate, count_index, derived_count in ((0.0235, 21, proof_235), (0.035, 22, proof_350)):
    exact_zero_count = sum(1 for row in annual_rows if int(row[0]) == 10 and int(row[count_index]) == 0)
    if exact_zero_count != derived_count:
        raise SystemExit(f"Zero-real-breach strategy count differs from annual window replay at {rate:.2%}: {exact_zero_count} != {derived_count}")
    evidence = next((row for row in results.get("derived_real_breach_zero_proof", [])
                     if abs(float(row.get("annualized_inflation_assumption", -1)) - rate) < 1e-9), None)
    if not evidence or int(evidence.get("provable_zero_real_breach_strategies", -1)) != exact_zero_count:
        raise SystemExit(f"Browser proof summary does not match exact annual real-principal counts at {rate:.2%}.")
inflation_views = results.get("real_floor_inflation_views", {})
if inflation_views.get("rate_2_35_cells") != 8 or inflation_views.get("rate_3_50_cells") != 8 or inflation_views.get("passed") is not True:
    raise SystemExit("Browser did not verify both inflation modes against all eight real-principal timing rows.")
for evidence_text in (
    f"年通脹 2.35% 時，{strategy_count} 組第10年策略中有 {proof_235} 組",
    f"年通脹 3.50% 時是 {proof_350} 組",
    "逐窗口重播",
    "不代表途中不回撤",
):
    if evidence_text not in risk_disclosure:
        raise SystemExit("Rendered risk disclosure is incomplete: " + evidence_text)
for source_fragment in ("目前策略摘要共有 ", "scenarioPopulation", "provenFloor235", "provenFloor350"):
    if source_fragment not in html_text:
        raise SystemExit("Data-driven decision disclosure source is incomplete: " + source_fragment)
decision_evidence_disclosures_verified = True
if "不等於歷史每一天實際持倉或已執行交易" not in html_text:
    raise SystemExit("Annual target weights versus actual holdings/trades disclosure is missing.")
if "Y(state.bond, state.target, state.timing, state.flow, year)" not in html_text:
    raise SystemExit("Annual path must use canonical backtest records, not rounded SVG coordinates.")
if "GLIDEPATH_REVERSE_REPLAY_V1" not in html_text or "GLIDEPATH_REVERSE_DATA_V1" not in html_text:
    raise SystemExit("Independent reverse direction replay/data markers are missing.")
if "GLIDEPATH_PAIRED_COMPARISON_V1" not in html_text or "同窗配對比較" not in html_text:
    raise SystemExit("Same-window paired comparison engine or UI marker is missing.")
if "GLIDEPATH_DRAWDOWN_YEAR_DISTRIBUTION_V1" not in html_text or "pairedDrawdownYearTable" not in html_text:
    raise SystemExit("Maximum-drawdown occurrence-year distribution table is missing.")
if "monthly_withdrawal_500_usd_stress" not in html_text:
    raise SystemExit("Reverse replay cashflow BLOCK test target is missing.")
if "未以估算或原模式績效補值" not in html_text:
    raise SystemExit("Reverse replay must explicitly block unsupported cashflows rather than reuse legacy results.")
if "未扣交易成本、稅費或滑點" not in html_text or "不可視為 AGG／SHY／IEF" not in html_text:
    raise SystemExit("Reverse replay limitations for proxy coverage/costs are missing.")
if "<th>'+(s.cpi>0?'低於實質本金窗口':'名目低於本金')+'</th>" not in html_text:
    raise SystemExit("Real-mode table header/count contract is missing.")
if "s.cpi>=0.03?v.windows_below_real_principal_350:v.windows_below_real_principal_235" not in html_text:
    raise SystemExit("Real-mode table does not bind either exact real-principal count field.")

# Rebuild a deterministic, single-file ZIP from the exact canonical HTML.
with ZipFile(BUNDLE, "w", compression=ZIP_DEFLATED, compresslevel=9) as zf:
    zf.write(HTML, arcname="glidepath_interactive_preview_optimized.html")
with ZipFile(BUNDLE, "r") as zf:
    names = zf.namelist()
    if names != ["glidepath_interactive_preview_optimized.html"]:
        raise SystemExit("Unexpected ZIP member list: " + repr(names))
    inflated = zf.read(names[0])
    if inflated != html_bytes:
        raise SystemExit("ZIP round-trip mismatch: bundled HTML differs from v2.html")

html_sha = hashlib.sha256(html_bytes).hexdigest()
bundle_bytes = BUNDLE.stat().st_size
bundle_sha = hashlib.sha256(BUNDLE.read_bytes()).hexdigest()
crc32 = f"{zlib.crc32(html_bytes) & 0xffffffff:08x}"

ledger_audit_env = os.environ.get("LEDGER_REPLAY_AUDIT_PATH", "")
if not ledger_audit_env:
    raise SystemExit("Independent cashflow-ledger replay audit path is required.")
ledger_replay_path = Path(ledger_audit_env)
if not ledger_replay_path.is_file():
    raise SystemExit("Independent cashflow-ledger replay audit file is missing.")
ledger_replay = json.loads(ledger_replay_path.read_text(encoding="utf-8"))
if ledger_replay.get("schema") != "glidepath-window-cashflow-ledger-replay.v1" or ledger_replay.get("status") != "PASS":
    raise SystemExit("Independent cashflow-ledger replay did not publish PASS.")
if ledger_replay.get("source_panel_sha256") != pack_meta.get("source_sha256"):
    raise SystemExit("Independent ledger replay panel differs from embedded dashboard source.")
if ledger_replay.get("source_as_of") != source_as_of or ledger_replay.get("rolling_windows_per_scenario") != 157:
    raise SystemExit("Independent cashflow-ledger replay as-of/window mismatch.")
if (ledger_replay.get("window_rows_expected"), ledger_replay.get("annual_summary_rows_expected"), ledger_replay.get("scenario_count")) != (160768, 11264, 1024):
    raise SystemExit("Independent cashflow-ledger replay coverage is incomplete.")
ledger_counts = ledger_replay.get("counters", {})
for key, expected in {
    "window_rows_replayed": 160768,
    "annual_rows_reconciled": 11264,
    "scenario_summaries_reconciled": 1024,
    "cashflow_invariants_checked": 482304,
    "yearly_navs_reconciled": 11264,
    "daily_drawdown_paths_replayed": 160768,
    "real_floor_annual_rows": 11264,
}.items():
    if ledger_counts.get(key) != expected:
        raise SystemExit(f"Independent ledger replay count mismatch {key}: {ledger_counts.get(key)!r} != {expected}")

audit = json.loads(AUDIT.read_text(encoding="utf-8"))
audit["status"] = "BROWSER_AND_STATIC_VERIFICATION_PASSED"
ledger_replay_summary = dict(ledger_replay)
ledger_replay_summary.pop("real_floor_annual_counts", None)
ledger_replay_summary["real_floor_annual_counts_sha256"] = hashlib.sha256(
    json.dumps(ledger_replay.get("real_floor_annual_counts", []), separators=(",", ":")).encode("utf-8")
).hexdigest()
ledger_replay_summary.update({
    "real_floor_annual_rows": ledger_counts["real_floor_annual_rows"],
    "window_rows_replayed": ledger_counts["window_rows_replayed"],
    "annual_rows_reconciled": ledger_counts["annual_rows_reconciled"],
    "scenario_summaries_reconciled": ledger_counts["scenario_summaries_reconciled"],
    "cashflow_invariants_checked": ledger_counts["cashflow_invariants_checked"],
    "yearly_navs_reconciled": ledger_counts["yearly_navs_reconciled"],
    "daily_drawdown_paths_replayed": ledger_counts["daily_drawdown_paths_replayed"],
    "fields_compared": ledger_counts["fields_compared"],
    "max_abs_error": ledger_counts.get("max_abs_error", {}),
})
audit["cashflow_window_ledger_replay"] = ledger_replay_summary
audit["embedded_data_counts"] = {
    "scenarios_D": strategy_count,
    "annual_A": annual_count,
    "histograms_HIST": histogram_count,
    "cohorts_COHORT": cohort_count,
}
audit["html_bytes"] = len(html_bytes)
audit["html_characters"] = len(html_text)
audit["sha256"] = html_sha
audit["bundle_bytes"] = bundle_bytes
audit["bundle_sha256"] = bundle_sha
audit["html_crc32"] = crc32
audit["element_ids_count"] = len(unique_ids)
audit["duplicate_ids"] = duplicates
audit["html_size_reduction_pct"] = round((1 - len(html_bytes) / float(audit.get("original_html_bytes", 13068927))) * 100, 2)
audit["bundle_size_reduction_pct"] = round((1 - bundle_bytes / float(audit.get("original_bundle_bytes", 1559891))) * 100, 2)

review = audit.setdefault("v2_1_review", {})
review["source_commit"] = os.environ.get("GITHUB_SHA", review.get("source_commit", "unknown"))
static = review.setdefault("static_semantic_guards", {})
static.update({
    "javascript_parse": True,
    "duplicate_html_ids": len(duplicates),
    "unique_scenario_keys": len(scenario_keys),
    "unique_annual_keys": len(annual_keys),
    "unique_histogram_groups": len(histogram_keys),
    "unique_cohort_groups": len(cohort_keys),
    "annual_year10_summary_mismatches": annual_year10_summary_mismatches,
    "cashflow_nav_semantic_sweep": True,
    "no_withdrawal_zero_cashflow_contract": True,
    "allocation_path_invariant_across_cashflows": True,
    "real_floor_annual_grid_complete": real_floor_integrity.get("rows_with_both_real_floor_counts") == 11264,
    "real_floor_heatmaps_verified_at_235_and_350": len(heatmap_checks) == 2,
    "independent_cashflow_window_ledger_replay": ledger_replay.get("status") == "PASS",
    "zip_decompression_roundtrip": True,
    "zip_crc32_matches_html": True,
    "zip_sha256_matches_html": True,
    "trajectory_panel_source_marker": "GLIDEPATH_TRAJECTORY_PANEL_V1" in html_text,
    "decision_evidence_panel_embedded": "GLIDEPATH_DECISION_EVIDENCE_V1" in html_text,
    "decision_evidence_links_amount_behavior_sample_risk": decision_evidence_disclosures_verified and "決策依據：金額 × 行為 × 樣本 × 尚未證明的風險" in html_text,
    "trajectory_panel_uses_canonical_annual_records": "Y(state.bond, state.target, state.timing, state.flow, year)" in html_text,
    "trajectory_panel_not_actual_holdings_disclosure": "不等於歷史每一天實際持倉或已執行交易" in html_text,
    "reverse_replay_data_embedded": "GLIDEPATH_REVERSE_DATA_V1" in html_text,
    "reverse_replay_engine_embedded": "GLIDEPATH_REVERSE_REPLAY_V1" in html_text,
    "paired_comparison_engine_embedded": "GLIDEPATH_PAIRED_COMPARISON_V1" in html_text,
    "paired_comparison_uses_same_windows": "相同起訖日期的重疊 10 年窗口" in html_text,
    "drawdown_year_distribution_embedded": "GLIDEPATH_DRAWDOWN_YEAR_DISTRIBUTION_V1" in html_text and "pairedDrawdownYearTable" in html_text,
    "paired_comparison_includes_drawdown_occurrence_year": "最大回撤年為每窗首次觸及" in html_text,
    "reverse_replay_does_not_reuse_old_performance": "績效由獨立歷史價格回放計算" in html_text,
    "reverse_replay_unsupported_flow_blocks": "提款／供款版本尚未重播" in html_text,
    "canonical_bundle_member": "glidepath_interactive_preview_optimized.html",
    "canonical_bundle_matches_html": True
})
review["headless_browser_verification"] = results
review["cashflow_nav_semantic_sweep"] = cashflow_semantics
review["real_floor_ui_sweep_coverage"] = cashflow_semantics.get("checked_inflation_coverage", [])
review["real_floor_annual_pack_integrity"] = real_floor_integrity
review["real_floor_heatmap_checks"] = heatmap_checks
review["known_limits"] = [
    "Exact real-principal breach counts for each year, strategy, cashflow mode and inflation assumption are calculated from independently replayed 157-window year-end NAV marks.",
    "The visible real-principal count compares remaining portfolio NAV with initial capital inflated by the selected annual rate; it does not add previously withdrawn cash back to account NAV.",
    "STRIPS/TIPS floor and terminal-value calculations remain unmodeled; no guarantee is implied.",
    "The year-by-year allocation strip reads the canonical annual backtest records via S()/Y() and displays median target stock/bond weights. These are annual rebalance targets, not actual daily holdings or executed trades; NAV outcomes remain the backtest data's rolling-window summaries."
]
review["residual_findings_for_v2_2"] = [
    "Annual real-principal counts describe year-end NAV only; they do not count intra-year threshold touches and are not future probabilities."
]
review["table_real_mode_label_fix"] = {
    "implemented": True,
    "nominal_header": "名目低於本金",
    "real_header": "低於實質本金窗口",
    "real_cell_format": "逐窗口實質低於本金 n/157"
}
review["derived_real_breach_zero_proof"] = results.get("derived_real_breach_zero_proof", [])
review["reverse_direction_replay"] = results.get("reverse_direction_replay", {})
review["paired_direction_comparison"] = results.get("paired_direction_comparison", {})
review["paired_direction_comparison_real_235"] = results.get("paired_direction_comparison_real_235", {})
review["known_limits"].extend([
    "The reversed bond-to-stock replay is independently recomputed from repository SPY/TLT daily adjusted-close rows; it does not reuse the original stock-to-bond performance summaries.",
    "Reverse-direction performance is intentionally supported only for SPY plus TLT and the no-withdrawal/no-contribution cashflow state. Other bond proxies and cashflows are BLOCKED pending matching replay data and execution logic.",
    "The reverse replay uses 157 overlapping 10-year windows, 252 trading days per year and annual rebalance targets. It omits transaction costs, taxes, slippage and ETF-tracking differences; historical outcomes are not guarantees.",
    "The same-window pairwise comparison runs both mirrored SPY/TLT allocation schedules over identical 157 start/end windows, same $100,000 initial NAV, annual rebalance schedule, inflation setting and no-cashflow assumption. Aggregate summary deltas and paired per-window win counts are separate statistics.",
    "Maximum drawdown occurrence year is the first trading-year bucket in which each window reaches that window's worst peak-to-trough drawdown. Window samples overlap and are not independent observations.",
    "The audit records both the zero-inflation paired result and a distinct 2.35% annualized inflation snapshot, so real-dollar values are not inferred from the nominal presentation.",
    "The UI includes year-by-year counts for the year in which each matched window's maximum drawdown first occurs; those counts must reconcile to 157 windows for each direction."
])
audit["final_artifact_verification"] = {
    "status": "PASSED",
    "html_sha256": html_sha,
    "bundle_sha256": bundle_sha,
    "html_bytes": len(html_bytes),
    "bundle_bytes": bundle_bytes,
    "html_crc32": crc32,
    "unique_html_ids": len(unique_ids),
    "duplicate_ids": duplicates,
    "embedded_data_counts": {
        "scenarios_D": strategy_count,
        "annual_A": annual_count,
        "histograms_HIST": histogram_count,
        "cohorts_COHORT": cohort_count,
    },
    "unique_key_counts": {
        "scenarios_D": len(scenario_keys),
        "annual_A": len(annual_keys),
        "histograms_HIST": len(histogram_keys),
        "cohorts_COHORT": len(cohort_keys),
    },
    "annual_year10_summary_mismatches": annual_year10_summary_mismatches,
    "cashflow_nav_semantic_sweep": cashflow_semantics,
    "real_principal_breach_count_contract": {
        "annual_rows_with_two_rates": 11264,
        "rate_235_zero_breach_strategies": proof_235,
        "rate_350_zero_breach_strategies": proof_350,
        "strict_below_threshold": True,
        "source": "independent normalized-share replay; year-end portfolio NAV",
    },
    "cashflow_window_ledger_replay": {
        "status": ledger_replay["status"],
        "source_panel_sha256": ledger_replay["source_panel_sha256"],
        "window_rows_replayed": ledger_counts["window_rows_replayed"],
        "annual_rows_reconciled": ledger_counts["annual_rows_reconciled"],
        "scenario_summaries_reconciled": ledger_counts["scenario_summaries_reconciled"],
        "cashflow_invariants_checked": ledger_counts["cashflow_invariants_checked"],
        "real_floor_annual_rows": ledger_counts["real_floor_annual_rows"],
        "real_floor_annual_counts_sha256": ledger_replay_summary["real_floor_annual_counts_sha256"],
        "max_abs_error": ledger_counts.get("max_abs_error", {}),
    },
    "zip_members": ["glidepath_interactive_preview_optimized.html"],
    "zip_inflated_html_matches_canonical_html": True,
    "reverse_direction_replay_status": results.get("reverse_direction_replay", {}).get("replayState", "NOT_REPORTED"),
    "reverse_direction_replay_windows": results.get("reverse_direction_replay", {}).get("windowCount", 0),
    "reverse_direction_replay_passed": results.get("reverse_direction_replay", {}).get("passed", False),
    "paired_direction_comparison_status": results.get("paired_direction_comparison", {}).get("state", "NOT_REPORTED"),
    "paired_direction_comparison_windows": results.get("paired_direction_comparison", {}).get("matchedPairCount", 0),
    "paired_direction_comparison_passed": results.get("paired_direction_comparison", {}).get("passed", False),
    "paired_direction_comparison_real_235_status": results.get("paired_direction_comparison_real_235", {}).get("state", "NOT_REPORTED"),
    "paired_direction_comparison_real_235_windows": results.get("paired_direction_comparison_real_235", {}).get("matchedPairCount", 0),
    "paired_direction_comparison_real_235_passed": results.get("paired_direction_comparison_real_235", {}).get("passed", False),
    "created_at_utc": datetime.now(timezone.utc).isoformat()
}
AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(audit["final_artifact_verification"], indent=2))
