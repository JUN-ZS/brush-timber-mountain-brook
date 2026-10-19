"""Build a deterministic ZIP and refresh its machine-readable audit metadata.

This is run only after the independent static/data tests pass on the exact HTML.
The ZIP deliberately excludes the audit JSON itself so bundle_bytes is not
self-referential; the audit JSON remains a separate file beside the archive.
"""
import hashlib
import json
import re
import zipfile
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[2]
HTML_PATH = ROOT / "v2.html"
AUDIT_PATH = ROOT / "glidepath_preview_optimized_audit.json"
DOC_PATH = ROOT / "glidepath_preview_v2.1_methodology.md"
BUNDLE_PATH = ROOT / "glidepath_interactive_preview_optimized_bundle.zip"
README = """Glidepath Preview v2.1

1. Extract this archive.
2. Open v2.html in a current Edge or Chrome browser. It is a standalone offline HTML file.
3. Read glidepath_preview_v2.1_methodology.md before interpreting any results.

Important:
- The inflation selector is a scenario input, not actual CPI or a forecast.
- Counts below initial capital are nominal-only; they are not real purchasing-power breach rates.
- Withdrawal and shortfall dollar values remain nominal.
- STRIPS/TIPS are not modeled here; this does not claim a guaranteed floor.
- The optimizer buttons are in-sample historical rankings, not predictions.
- The 157 rolling 10-year windows overlap and are not independent probability trials.
- This package's separate machine audit JSON is kept next to the ZIP in the repository.
"""


class IdAudit(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name == "id" and value:
                self.ids.append(value)


def main():
    html_bytes = HTML_PATH.read_bytes()
    html = html_bytes.decode("utf-8")
    doc_bytes = DOC_PATH.read_bytes()
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    audit["status"] = "STATIC_AND_DATA_CHECKS_PASS_BROWSER_INTERACTION_NOT_RUN"
    audit["html_bytes"] = len(html_bytes)
    audit["html_chars"] = len(html)
    audit["html_size_reduction_pct"] = round((1 - len(html_bytes) / audit["original_html_bytes"]) * 100, 2)
    audit["sha256"] = hashlib.sha256(html_bytes).hexdigest()
    audit["sha256_status"] = "VERIFIED_FROM_CURRENT_HTML_BYTES"
    audit["bundle_status"] = "CURRENT_ZIP_BUILT_FROM_VERIFIED_HTML"
    audit["runtime_checks_status"] = "STATIC_AND_DATA_CHECKS_PASS; BROWSER_INTERACTION_NOT_RUN"
    audit["browser_interaction_tested"] = False
    audit["limitations"] = [
        "No inflation-adjusted below-capital window count is computed; displayed capital-breach counts are nominal-only.",
        "Withdrawal and shortfall amounts remain nominal because cash flows occur on different dates.",
        "STRIPS/TIPS are not modeled; no guaranteed floor or expected terminal value is claimed.",
        "157 overlapping 10-year windows are descriptive and not independent probability trials.",
        "Static/data tests do not replace browser visual and interaction tests."
    ]
    audit["remaining_limitations"] = [
        "The dashboard does not calculate an inflation-adjusted below-capital window count; do not interpret the nominal count as a real purchasing-power breach rate.",
        "Withdrawal/shortfall dollar amounts remain nominal because withdrawal dates differ; no single end-of-horizon deflator is applied.",
        "STRIPS/TIPS are not a modeled strategy here; no guaranteed floor or expected terminal value is claimed.",
        "157 rolling 10-year windows overlap and are descriptive, not independent probability trials.",
        "The ZIP contains a byte-identical copy of v2.html; browser visual and interaction regression remains untested."
    ]

    parser = IdAudit()
    parser.feed(html)
    frequencies = {}
    for element_id in parser.ids:
        frequencies[element_id] = frequencies.get(element_id, 0) + 1
    audit["element_ids_count"] = len(parser.ids)
    audit["duplicate_ids"] = sorted(key for key, count in frequencies.items() if count > 1)
    if audit["duplicate_ids"]:
        raise SystemExit(f"Duplicate HTML IDs found: {audit['duplicate_ids']}")

    entries = {
        "v2.html": html_bytes,
        "glidepath_preview_v2.1_methodology.md": doc_bytes,
        "README.txt": README.encode("utf-8"),
    }
    with zipfile.ZipFile(BUNDLE_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for name, data in entries.items():
            info = zipfile.ZipInfo(name, date_time=(2024, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)

    bundle_bytes = BUNDLE_PATH.stat().st_size
    audit["bundle_bytes"] = bundle_bytes
    audit["bundle_size_reduction_pct"] = round((1 - bundle_bytes / audit["original_bundle_bytes"]) * 100, 2)
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Re-open the produced archive and verify its embedded HTML matches byte-for-byte.
    with zipfile.ZipFile(BUNDLE_PATH) as bundle:
        if bundle.testzip() is not None:
            raise SystemExit("ZIP CRC verification failed")
        if bundle.read("v2.html") != html_bytes:
            raise SystemExit("ZIP HTML differs from the tested standalone HTML")
        if bundle.read("glidepath_preview_v2.1_methodology.md") != doc_bytes:
            raise SystemExit("ZIP methodology document mismatch")
        if "README.txt" not in bundle.namelist():
            raise SystemExit("ZIP README missing")

    # Recompute report metadata after the final audit write. The audit file is not in the ZIP,
    # so the exact bundle size cannot be affected by this update.
    final = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    final["bundle_bytes"] = BUNDLE_PATH.stat().st_size
    final["sha256"] = hashlib.sha256(HTML_PATH.read_bytes()).hexdigest()
    AUDIT_PATH.write_text(json.dumps(final, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": final["status"],
        "html_bytes": final["html_bytes"],
        "html_sha256": final["sha256"],
        "bundle_bytes": final["bundle_bytes"],
        "bundle_sha256": hashlib.sha256(BUNDLE_PATH.read_bytes()).hexdigest(),
        "bundle_members": list(entries),
        "browser_interaction_tested": False,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
