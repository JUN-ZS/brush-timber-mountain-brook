#!/usr/bin/env python3
"""Inline the allocation panel and its independent SPY/TLT reverse replay data into the canonical single-file HTML."""
from pathlib import Path
import hashlib
import json
import math
import re

ROOT = Path.cwd()
HTML_PATH = ROOT / "v2.html"
JS_PATH = Path(__file__).with_name("trajectory-panel.js")
SOURCE_DATA_PATH = ROOT / "src" / "data" / "universe.json"
MARKER = "GLIDEPATH_TRAJECTORY_PANEL_V1"
DATA_MARKER = "GLIDEPATH_REVERSE_DATA_V1"
SCRIPT_ID = 'id="glidepath-trajectory-panel-inline"'
DATA_SCRIPT_ID = 'id="glidepath-reverse-data"'
PANEL_RE = re.compile(r'<script id="glidepath-trajectory-panel-inline">.*?</script>\s*', re.S)
DATA_RE = re.compile(r'<script id="glidepath-reverse-data" type="application/json">.*?</script>\s*', re.S)

html = HTML_PATH.read_text(encoding="utf-8")
script = JS_PATH.read_text(encoding="utf-8").strip()
source_bytes = SOURCE_DATA_PATH.read_bytes()
source = json.loads(source_bytes.decode("utf-8"))

if MARKER not in script or "GLIDEPATH_REVERSE_REPLAY_V1" not in script:
    raise SystemExit("Trajectory or reverse replay source marker is missing.")
if "</script" in script.lower():
    raise SystemExit("Inline JavaScript contains a closing-script sequence; refusing unsafe injection.")
if not isinstance(source.get("dates"), list) or not isinstance(source.get("c"), dict):
    raise SystemExit("universe.json schema is missing dates/close arrays.")
if "SPY" not in source["c"] or "TLT" not in source["c"]:
    raise SystemExit("Reverse replay requires observed SPY and TLT adjusted-close rows.")

source_dates = source["dates"]
spy_src = source["c"]["SPY"]
tlt_src = source["c"]["TLT"]
if not (len(source_dates) == len(spy_src) == len(tlt_src)):
    raise SystemExit("SPY/TLT/dates do not align; refusing to truncate or pad.")
dates, spy, tlt = [], [], []
dropped_common_missing = 0
for index, (day, spy_value, tlt_value) in enumerate(zip(source_dates, spy_src, tlt_src)):
    spy_missing = spy_value is None
    tlt_missing = tlt_value is None
    if spy_missing and tlt_missing:
        dropped_common_missing += 1
        continue
    if spy_missing != tlt_missing:
        raise SystemExit(f"Unmatched SPY/TLT missing price at source row {index} ({day}); refusing to fill.")
    sv, tv = float(spy_value), float(tlt_value)
    if not (math.isfinite(sv) and math.isfinite(tv) and sv > 0 and tv > 0):
        raise SystemExit(f"Invalid SPY/TLT price at source row {index} ({day}).")
    dates.append(day)
    spy.append(round(sv, 6))
    tlt.append(round(tv, 6))

protocol = {
    "startIndex": 60,
    "stride": 20,
    "tradingDaysPerYear": 252,
    "horizonYears": 10,
    "horizonTradingDays": 2520,
    "nWindows": 157
}
if any(protocol["startIndex"] + i * protocol["stride"] + protocol["horizonTradingDays"] >= len(dates)
       for i in range(protocol["nWindows"])):
    raise SystemExit("The current price data cannot support all 157 complete 10-year windows.")

pack = {
    "marker": DATA_MARKER,
    "datasetSource": "src/data/universe.json",
    "datasetSourceDescription": source.get("source", "unknown"),
    "sourceAsOf": source.get("asof", "unknown"),
    "sourceFileSha256": hashlib.sha256(source_bytes).hexdigest(),
    "originalRows": len(source_dates),
    "droppedCommonMissingRows": dropped_common_missing,
    "validRows": len(dates),
    "dateStart": dates[0],
    "dateEnd": dates[-1],
    "dates": dates,
    "prices": {"SPY": spy, "TLT": tlt},
    "windowProtocol": protocol
}
if dropped_common_missing < 1:
    raise SystemExit("Expected the current known shared non-trading/missing row to be identified rather than silently used.")

payload = json.dumps(pack, ensure_ascii=True, separators=(",", ":"), allow_nan=False)
if "</script" in payload.lower():
    raise SystemExit("Reverse price payload contains a closing-script sequence.")

panel_tag = '<script id="glidepath-trajectory-panel-inline">\n' + script + "\n</script>\n"
data_tag = '<script id="glidepath-reverse-data" type="application/json">\n' + payload + "\n</script>\n"

# Replace both injected scripts on every run. This keeps the ZIP deterministic and makes source edits effective.
if len(PANEL_RE.findall(html)) > 1 or len(DATA_RE.findall(html)) > 1:
    raise SystemExit("Duplicate injected panel or reverse-data script tags.")
html = PANEL_RE.sub("", html)
html = DATA_RE.sub("", html)
if html.count("</body>") != 1:
    raise SystemExit("Expected exactly one closing body tag in v2.html.")
html = html.replace("</body>", data_tag + panel_tag + "</body>", 1)
if MARKER not in html or DATA_MARKER not in html or SCRIPT_ID not in html or DATA_SCRIPT_ID not in html:
    raise SystemExit("Inline panel/data markers did not survive injection.")
if "Y(state.bond, state.target, state.timing, state.flow, year)" not in html:
    raise SystemExit("Annual target path must still use the canonical annual backtest record map.")

HTML_PATH.write_text(html, encoding="utf-8")
print(json.dumps({
    "inline_panel_characters": len(script),
    "reverse_data_rows": len(dates),
    "dropped_common_missing_rows": dropped_common_missing,
    "window_protocol": protocol,
    "source_as_of": pack["sourceAsOf"],
    "source_file_sha256": pack["sourceFileSha256"],
    "html_characters": len(html)
}, ensure_ascii=False, indent=2))
