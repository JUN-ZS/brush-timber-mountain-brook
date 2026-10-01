from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HTML = ROOT / "research" / "strategy_instance_v1" / "operator_dashboard.html"
SERVER = ROOT / "research" / "strategy_instance_v1" / "serve_operator.py"

def fail(msg: str) -> None:
    raise SystemExit("CHECK_FAILED: " + msg)

def main() -> int:
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else ""
    if mode not in {"exclusivity", "gap"}:
        print("usage: python check_operator_acceptance_ui.py exclusivity|gap")
        return 2

    html = HTML.read_text(encoding="utf-8")
    server = SERVER.read_text(encoding="utf-8")

    if mode == "exclusivity":
        for token in (
            ".view-audit",
            ".view-desk",
            'querySelectorAll(".view-audit")',
            'querySelectorAll(".view-desk")',
            'view !== "audit"',
            'view === "desk"',
        ):
            if token not in html:
                fail("missing DESK/AUDIT token: " + token)
        print("DESK/AUDIT exclusivity: PASS")
        return 0

    for token in (
        "MANUAL ↔ LIVE POSITION GAP",
        "<th>Live Position</th>",
        "<th>Manual Book</th>",
        "Manual Book − Live Desk Position",
        "const live=(strategy?.positions||[])",
        "const manual=(state?.manual_book?.positions||[])",
    ):
        if token not in html:
            fail("missing Gap semantic token: " + token)
    if "Derived as Manual − Locked Strategy" in html:
        fail("stale locked-strategy Gap wording remains")
    for token in ("place_order", "modify_order", "unlock_trade"):
        if token in server:
            fail("forbidden execution token in operator server: " + token)
    print("Gap semantics/data source: PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
