#!/usr/bin/env python3
"""Idempotently inline the year-by-year target allocation panel into the canonical HTML."""
from pathlib import Path
import re

ROOT = Path.cwd()
HTML_PATH = ROOT / "v2.html"
JS_PATH = Path(__file__).with_name("trajectory-panel.js")
MARKER = "GLIDEPATH_TRAJECTORY_PANEL_V1"
SCRIPT_ID = 'id="glidepath-trajectory-panel-inline"'

html = HTML_PATH.read_text(encoding="utf-8")
script = JS_PATH.read_text(encoding="utf-8").strip()

if MARKER not in script:
    raise SystemExit("Trajectory-panel source marker is missing.")
if "</script" in script.lower():
    raise SystemExit("Inline JavaScript contains a closing-script sequence; refusing unsafe injection.")

if MARKER in html:
    if SCRIPT_ID not in html:
        raise SystemExit("Trajectory marker exists but its inline script tag is missing.")
    print("Trajectory panel is already inlined; no HTML rewrite needed.")
else:
    if html.count("</body>") != 1:
        raise SystemExit("Expected exactly one closing body tag in v2.html.")
    inline = '<script id="glidepath-trajectory-panel-inline">\n' + script + "\n</script>\n"
    html = html.replace("</body>", inline + "</body>", 1)
    HTML_PATH.write_text(html, encoding="utf-8")
    print("Inlined trajectory panel: " + str(len(script)) + " JavaScript characters.")
