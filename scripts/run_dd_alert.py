"""Smoke: drawdown_alert prefer DD_EPISODES cache. Run from repo root with PYTHONPATH=."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backtest.drawdown_alert import PINNED_FEATURE_HASH, PINNED_PACK_HASH, alert_report  # noqa: E402


def clean(series):
    out = []
    last = None
    for x in series:
        if isinstance(x, (int, float)) and x == x and x > 0:
            last = float(x)
            out.append(last)
        else:
            out.append(last if last is not None else float("nan"))
    return out


def main() -> int:
    u = json.loads((ROOT / "src/data/universe.json").read_text(encoding="utf-8"))
    dates = u["dates"]
    qqq = clean(u["c"]["QQQ"])
    vix = clean(u["c"].get("VIX") or [])
    start = next(i for i, x in enumerate(qqq) if x == x)
    rep = alert_report(
        dates[start:],
        qqq[start:],
        vix[start:] if vix else None,
        repo_root=ROOT,
    )
    print("source", rep["episodes_source"].get("source"))
    print("feature_hash", rep["episodes_source"].get("feature_hash"))
    print("manifest_hash", rep["episodes_source"].get("manifest_hash"))
    print("looks_like_max_dd", rep["looks_like_historical_max_dd"])
    cur = rep["current_dd_from_ath"]
    print("cur_dd%", None if cur is None else round(cur * 100, 2))
    bc = rep["best_crash_match"] or {}
    print("best_crash", {k: bc.get(k) for k in ["alert_score", "path_corr", "peak_date", "trough_date", "dd"]})
    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "reports" / "drawdown_alert.json").write_text(
        json.dumps(rep, indent=2, default=str), encoding="utf-8"
    )
    assert rep["episodes_source"].get("source") == "DD_EPISODES_CACHE", rep["episodes_source"]
    assert rep["episodes_source"].get("manifest_hash") == PINNED_PACK_HASH
    assert rep["episodes_source"].get("feature_hash") == PINNED_FEATURE_HASH
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
