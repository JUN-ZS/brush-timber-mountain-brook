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

html_bytes = HTML.read_bytes()
html_text = html_bytes.decode("utf-8")
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
if "<th>'+(s.cpi>0?'實質保本窗口（未精算）':'名目低於本金')+'</th>" not in html_text:
    raise SystemExit("Real-mode table header fix is missing.")
if "未精算（名目 " not in html_text:
    raise SystemExit("Real-mode table cell guard is missing.")

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

audit = json.loads(AUDIT.read_text(encoding="utf-8"))
audit["status"] = "BROWSER_AND_STATIC_VERIFICATION_PASSED"
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
    "zip_decompression_roundtrip": True,
    "zip_crc32_matches_html": True,
    "zip_sha256_matches_html": True,
    "trajectory_panel_source_marker": "GLIDEPATH_TRAJECTORY_PANEL_V1" in html_text,
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
review["known_limits"] = [
    "The proven zero-real-breach strategy counts are derived from each strategy's minimum terminal NAV versus the inflation-adjusted $100,000 threshold.",
    "Exact real-purchasing-power breach counts for strategies that fail the minimum-terminal-NAV proof are not inferred without per-window terminal NAV values or a fresh window-level replay.",
    "STRIPS/TIPS floor and terminal-value calculations remain unmodeled; no guarantee is implied.",
    "The year-by-year allocation strip reads the canonical annual backtest records via S()/Y() and displays median target stock/bond weights. These are annual rebalance targets, not actual daily holdings or executed trades; NAV outcomes remain the backtest data's rolling-window summaries."
]
review["residual_findings_for_v2_2"] = [
    "Exact real-purchasing-power breach counts for strategies whose worst terminal NAV is below the inflation-adjusted principal threshold remain uncomputed; the UI explicitly labels these as uncalculated instead of substituting nominal counts."
]
review["table_real_mode_label_fix"] = {
    "implemented": True,
    "nominal_header": "名目低於本金",
    "real_header": "實質保本窗口（未精算）",
    "real_cell_format": "未精算（名目 n/157）"
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
