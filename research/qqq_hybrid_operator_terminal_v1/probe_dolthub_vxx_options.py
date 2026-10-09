#!/usr/bin/env python3
"""Probe public DoltHub option_chain availability for VXX on fixed historical dates.

This is a source-availability test only. It does not establish exchange authority,
executable fills, or per-contract OCC root/deliverable identity. Network errors are
reported as INCONCLUSIVE rather than converted into absence of history.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

API = "https://www.dolthub.com/api/v1alpha1/post-no-preference/options/master"
CHECK_DATES = [
    "2019-03-04",  # early sample after reported 2019 start
    "2020-03-16",  # COVID shock
    "2022-06-13",  # 2022 risk-off
    "2024-08-05",  # after July 2024 VXX reverse-split adjustment
    "2025-04-07",  # 2025 volatility shock window
    "2026-07-07",  # reported latest date in earlier source survey
]

def query(sql: str) -> dict:
    url = API + "?" + urllib.parse.urlencode({"q": sql})
    req = urllib.request.Request(url, headers={"User-Agent": "qqq-hybrid-research-audit/1.0"})
    with urllib.request.urlopen(req, timeout=25) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if payload.get("query_execution_status") != "Success":
        raise RuntimeError(payload.get("query_execution_message", "Unknown DoltHub query error"))
    return payload

def main() -> int:
    report = {
        "source": API,
        "source_class": "COMMUNITY_MAINTAINED_PUBLIC_DATA",
        "purpose": "presence probe only; not exchange-authoritative",
        "checked_dates": CHECK_DATES,
        "results": [],
        "summary": {},
        "contract_root_warning": "positive row counts cannot independently prove OCC contract root/deliverable for adjusted VXX options",
    }
    successes = 0
    observed_any = False
    for day in CHECK_DATES:
        row = {"date_requested": day, "status": "INCONCLUSIVE"}
        try:
            date.fromisoformat(day)
            sql = (
                "SELECT date, act_symbol, expiration, strike, call_put, bid, ask, vol, delta "
                "FROM option_chain "
                f"WHERE act_symbol = 'VXX' AND date = '{day}' "
                "ORDER BY expiration, strike, call_put LIMIT 2000"
            )
            payload = query(sql)
            quotes = payload.get("rows") or []
            observed_any = True
            valid_two_sided = 0
            future_expiry = 0
            for quote in quotes:
                try:
                    if date.fromisoformat(str(quote.get("expiration", ""))[:10]) > date.fromisoformat(day):
                        future_expiry += 1
                except ValueError:
                    pass
                try:
                    bid, ask = float(quote.get("bid")), float(quote.get("ask"))
                    if bid > 0 and ask > 0 and bid <= ask:
                        valid_two_sided += 1
                except (TypeError, ValueError):
                    pass
            row.update({
                "status": "ROWS_FOUND" if quotes else "NO_ROWS_RETURNED",
                "row_count": len(quotes),
                "future_expiry_rows": future_expiry,
                "positive_non_crossed_two_sided_rows": valid_two_sided,
                "valid_quote_pct": round(100 * valid_two_sided / len(quotes), 2) if quotes else None,
                "expiry_examples": sorted({str(q.get("expiration", ""))[:10] for q in quotes})[:8],
                "sample_rows": [
                    {key: quote.get(key) for key in ("date", "act_symbol", "expiration", "strike", "call_put", "bid", "ask", "vol", "delta")}
                    for quote in quotes[:3]
                ],
            })
            if quotes:
                successes += 1
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, RuntimeError, OSError) as exc:
            row["error"] = type(exc).__name__ + ": " + str(exc)[:240]
        report["results"].append(row)
    if not observed_any:
        overall = "INCONCLUSIVE_API_UNAVAILABLE"
    elif successes == len(CHECK_DATES):
        overall = "ALL_CHECKPOINTS_HAVE_ROWS"
    elif successes == 0:
        overall = "VXX_NOT_FOUND_ON_CHECKPOINTS"
    else:
        overall = "PARTIAL_CHECKPOINT_COVERAGE"
    report["summary"] = {
        "overall": overall,
        "checkpoints_with_rows": successes,
        "checkpoints_total": len(CHECK_DATES),
        "api_responded_to_at_least_one_query": observed_any,
        "trade_replay_approved": False,
    }
    output = json.dumps(report, indent=2, sort_keys=True)
    print("DOLTHUB_VXX_OPTIONS_AUDIT_BEGIN")
    print(output)
    print("DOLTHUB_VXX_OPTIONS_AUDIT_END")
    try:
        Path("research/qqq_hybrid_operator_terminal_v1/dolthub_vxx_options_probe.json").write_text(output + "\n", encoding="utf-8")
    except OSError:
        pass
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
