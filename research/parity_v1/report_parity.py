"""Generate / refresh PARITY_REPORT.md from PARITY_REPORT.json or by re-running tests."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

PARITY_DIR = Path(__file__).resolve().parent


def md_from_json(payload: dict) -> str:
    lines = [
        "# Research ↔ Live PARITY REPORT",
        "",
        "Local-only diagnostic. Does **not** change STRATEGY_LOCK / alpha parameters.",
        "",
        f"- Cases recorded: **{payload.get('case_count', len(payload.get('cases', [])))}**",
        f"- PARITY: **{payload.get('parity_count', 0)}**",
        f"- Drift counts: `{json.dumps(payload.get('drift_counts', {}), ensure_ascii=False)}`",
        "",
        "## Summary table",
        "",
        "| CASE | equal | difference_type | research_value | live_value | difference | alpha_impact |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in payload.get("cases", []):
        lines.append(
            "| {CASE} | {equal} | {difference_type} | `{rv}` | `{lv}` | `{df}` | {ai} |".format(
                CASE=r["CASE"],
                equal=r["equal"],
                difference_type=r["difference_type"],
                rv=str(r["research_value"])[:80].replace("|", "/"),
                lv=str(r["live_value"])[:80].replace("|", "/"),
                df=str(r["difference"])[:60].replace("|", "/"),
                ai=str(r["alpha_impact"])[:120].replace("|", "/"),
            )
        )
    lines += [
        "",
        "## Recommended next step",
        "",
        "- Infrastructure-only live alignment to locked research (median/shift/min_periods=5, "
        "volume tie-break, near 1.02/1.01 pool).",
        "- Do **not** change research alpha / STRATEGY_LOCK.",
        "",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    # Re-run tests to refresh RESULTS + reports
    from research.parity_v1 import test_research_live_parity as t

    t.RESULTS.clear()
    suite = unittest.defaultTestLoader.loadTestsFromModule(t)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    t.write_reports()
    json_path = PARITY_DIR / "PARITY_REPORT.json"
    md_path = PARITY_DIR / "PARITY_REPORT.md"
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print(f"Tests: ran={result.testsRun} failures={len(result.failures)} errors={len(result.errors)}")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
