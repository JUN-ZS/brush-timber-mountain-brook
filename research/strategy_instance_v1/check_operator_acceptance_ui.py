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
    if mode not in {"exclusivity", "gap", "attribution"}:
        print("usage: python check_operator_acceptance_ui.py exclusivity|gap|attribution")
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
    if mode == "attribution":
        for token in (
            "BROKER EXECUTIONS AWAITING ATTRIBUTION",
            'id="attributionQueue"',
            '"/api/attribution?instance_id="',
            '"/api/confirm"',
            "CONFIRM LONG",
            "CONFIRM SHORT",
            "EXPLICIT_USER_CONFIRMATION_ONLY",
            'MUTATING_PATHS = {"/api/manual", "/api/refresh", "/api/confirm"}',
            'self.headers.get(MUTATION_HEADER)',
        ):
            if token not in (html + server):
                fail("missing explicit attribution boundary token: " + token)
        for token in (
            "strategy_attribution_policy",
            "POTENTIAL_PREDECISION_MATCH",
            "BROKER_EXECUTION_UNATTRIBUTED",
        ):
            if token not in (html + server + str(ROOT / "research/strategy_instance_v1/run_instance.py")):
                fail("missing conservative attribution token: " + token)
        print("Explicit broker attribution workflow: PASS")
        return 0


    for token in ("place_order", "modify_order", "unlock_trade"):
        if token in server:
            fail("forbidden execution token in operator server: " + token)
    print("Gap semantics/data source: PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
