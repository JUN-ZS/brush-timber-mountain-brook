#!/usr/bin/env python3
"""Desk（信股慣性台）FORWARD RUNNER V1.0 + T1 LIVE FORWARD / HYPOTHESIS CONFIRMATION V1

DATA → original engine check → SIGNAL CAPTURE / T1 GATE → IMMUTABLE EVENT
→ RESEARCH SHADOW BOOK (book_ADD gated) → OUTCOME RESOLUTION
→ RESEARCH MEMORY (profile → signal append → outcome join → analysis → report)
→ RESEARCH EVOLUTION (confirmation cohort on frozen H; discovery_n vs confirmation_n)
→ RUN HISTORY → STATUS → HTML REPORT

T0 immutable. book_ADD ≠ MARK_BUY / ARMED / TRUST_UP.
evaluation_clock = LIVE_FORWARD. Benchmark = QQQ.
score / alignScore ≠ probability. Never invent fee / slippage.
Do NOT invent T1 from Yahoo; T0 re-emit ≠ T1; new_hypotheses from T0 discovery = 0 this stage.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import importlib.util

HKT = ZoneInfo("Asia/Hong_Kong")


def _load_t1_capture():
    tool = Path(__file__).resolve().parent / "tools" / "t1_capture.py"
    spec = importlib.util.spec_from_file_location("desk_t1_capture", tool)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod
NODE = "desk"
APP_ID = "xin_gu_inertia_desk"
MODEL = "DESK_CORE_V1"
EVAL_CLOCK = "LIVE_FORWARD"
BENCH = "QQQ"
HUB_NAME = "信股慣性台"
T0_EVENTS = "research/forward_v1/desk/T0_20260921T183800/events.jsonl"

ENGINE_DIR = Path("/workspace/juniper-kite/juniper-kite-shadow-frost-up-down-get")
ENGINE_WRITE = ENGINE_DIR / "scripts" / "desk_run_warehouse_write.mts"
ENGINE_SNAP = ENGINE_DIR / "scripts" / "live-scan-snapshot.mts"

EXECUTABLE_TYPES = {
    "MARK_BUY", "ARMED", "TRUST_UP", "BUY", "SELL", "OPEN", "CLOSE", "TRIM", "REDUCE", "REVERSE",
}
BOOK_ACTION_TYPES = {
    "desk.book_ADD", "book_ADD", "desk.book_TRIM", "book_TRIM", "desk.book_HOLD", "book_HOLD",
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_z(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def hkt_str(dt: datetime) -> str:
    return dt.astimezone(HKT).strftime("%Y-%m-%d %H:%M:%S HKT")


def load_jsonl(path: Path) -> list:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def classify_execution(event: dict) -> str:
    """BOOK_ACTION | RESEARCH_SIGNAL | EXECUTABLE | AUDIT_ONLY."""
    st = str(event.get("signal_type") or "")
    base = st.split(".")[-1] if st else ""
    if st in BOOK_ACTION_TYPES or base in {"book_ADD", "book_TRIM", "book_HOLD"}:
        return "BOOK_ACTION"
    candidates = {st, base, st.upper(), base.upper()}
    if candidates & EXECUTABLE_TYPES or base.upper() in EXECUTABLE_TYPES:
        return "EXECUTABLE"
    if event.get("provenance_label") == "Historical" or str(event.get("source") or "").startswith("ui_demo"):
        return "AUDIT_ONLY"
    return "RESEARCH_SIGNAL"


def run_py(repo: Path, script_rel: str, extra: list[str] | None = None, timeout: int = 600) -> tuple[int, str]:
    cmd = [sys.executable, str(repo / script_rel), "--repo-root", str(repo)]
    if extra:
        cmd.extend(extra)
    try:
        proc = subprocess.run(cmd, cwd=str(repo), capture_output=True, text=True, timeout=timeout)
        return proc.returncode, ((proc.stdout or "") + (proc.stderr or ""))[-4000:]
    except Exception as exc:  # noqa: BLE001
        return 1, str(exc)


def ensure_empty_ledgers(ledgers: Path, run_id: str, policy_reason: str) -> dict:
    ledgers.mkdir(parents=True, exist_ok=True)
    schemas = {
        "positions.jsonl": {
            "schema": "desk.shadow_position.v1",
            "note": "Empty by EXECUTION_POLICY — book_ADD is OBSERVATION only",
        },
        "trades.jsonl": {
            "schema": "desk.shadow_trade.v1",
            "note": "No invented trades from book_ADD",
        },
        "signal_trade_map.jsonl": {
            "schema": "desk.signal_trade_map.v1",
            "note": "No trade mapping until EXECUTABLE signal",
        },
        "portfolio_daily.jsonl": {
            "schema": "desk.portfolio_daily.v1",
            "note": "No portfolio marks without positions; NET_PNL=NOT_AVAILABLE",
        },
    }
    meta: dict = {}
    for name, hdr in schemas.items():
        path = ledgers / name
        if not path.exists():
            path.write_text("")
        rows = sum(1 for line in path.read_text().splitlines() if line.strip())
        meta[name] = {
            "path": f"research/forward_v1/desk/ledgers/{name}",
            **hdr,
            "rows": rows,
        }

    gate = {
        "run_id": run_id,
        "policy": "desk.book_ADD => BOOK_ACTION/OBSERVATION; NEVER auto MARK_BUY/ARMED/TRUST_UP",
        "shadow_book": "EMPTY_BY_POLICY",
        "reason": policy_reason,
        "open_positions": 0,
        "closed_trades": 0,
        "net_pnl": "NOT_AVAILABLE",
    }
    with (ledgers / "execution_gate_log.jsonl").open("a") as fh:
        fh.write(json.dumps(gate, ensure_ascii=False) + "\n")
    return meta


def write_html_report(path: Path, run: dict, policy_text: str) -> None:
    rows = "".join(
        f"<tr><th>{key}</th><td><code>{json.dumps(val, ensure_ascii=False)}</code></td></tr>"
        for key, val in run.items()
        if key not in {"honesty", "research_evolution", "research_memory"}
    )
    honesty = "".join(f"<li>{item}</li>" for item in (run.get("honesty") or []))
    evo = run.get("research_evolution") or {}
    dr = evo.get("discovery_run") or {}
    t1c = run.get("t1_capture") or evo.get("t1_capture") or {}
    evo_summary = {
        "status": evo.get("status"),
        "hypothesis_counts": evo.get("hypothesis_counts"),
        "new_signals": dr.get("new_signals"),
        "new_evidence": dr.get("new_evidence"),
        "new_hypotheses": dr.get("new_hypotheses"),
        "unchanged": dr.get("unchanged"),
        "confirmed": dr.get("confirmed"),
        "rejected": dr.get("rejected"),
        "pending": dr.get("pending"),
        "untested": dr.get("untested"),
        "KNOWLEDGE_DELTA": dr.get("KNOWLEDGE_DELTA"),
        "T1_STATUS": dr.get("T1_STATUS") or t1c.get("T1_STATUS"),
        "confirmation_cohort": dr.get("confirmation_cohort") or t1c.get("confirmation_cohort"),
        "confirmation_cohort_open": dr.get("confirmation_cohort_open") or t1c.get("confirmation_cohort_open"),
        "t0_integrity": evo.get("t0_integrity"),
        "report": evo.get("report"),
    }
    evo_panel = (
        "<h2>RESEARCH EVOLUTION + T1 CONFIRMATION</h2>"
        "<p>DISCOVERY≠BUY · observed≠probability · discovery_n≠confirmation_n · "
        "confirmation_status ∈ UNTESTED|PENDING|CONFIRMED|REJECTED</p>"
        "<pre>" + json.dumps(evo_summary, ensure_ascii=False, indent=2) + "</pre>"
        "<p>Full panel: <code>research/forward_v1/desk/research_evolution/REPORT_RESEARCH_EVOLUTION.html</code></p>"
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="utf-8"/>
<title>Desk FORWARD RUN {run.get('run_id')}</title>
<style>
body{{font-family:system-ui,sans-serif;margin:24px;background:#0b0f14;color:#e6edf3}}
table{{border-collapse:collapse;width:100%;max-width:980px}}
th,td{{border:1px solid #30363d;padding:8px;text-align:left;vertical-align:top}}
th{{width:28%;background:#161b22}}
code{{white-space:pre-wrap;word-break:break-word}}
.badge{{display:inline-block;padding:2px 8px;border-radius:999px;background:#238636;margin-right:6px}}
.warn{{background:#9e6a03}}
pre{{background:#161b22;padding:12px;border:1px solid #30363d;overflow:auto}}
</style></head><body>
<h1>信股慣性台 / Desk — FORWARD RUN</h1>
<p><span class="badge">{run.get('evaluation_clock')}</span>
<span class="badge {'warn' if run.get('blocked_reason') else ''}">{run.get('status')}</span>
<span class="badge">benchmark={run.get('benchmark')}</span>
<span class="badge">RESEARCH EVOLUTION V1</span>
<span class="badge">T1 CONFIRM V1</span></p>
<p>score/alignScore = <b>NOT_A_PROBABILITY</b> · book_ADD ≠ MARK_BUY · T0 immutable · LIVE ≠ REPLAY · DISCOVERY≠BUY · never invent T1 from Yahoo</p>
<table>{rows}</table>
{evo_panel}
<h2>Honesty</h2><ul>{honesty}</ul>
<h2>EXECUTION_POLICY</h2><pre>{policy_text}</pre>
</body></html>
""",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Desk FORWARD RUNNER V1.0")
    parser.add_argument("--now", action="store_true", help="full FORWARD NOW cycle (default too)")
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument(
        "--skip-bridge",
        action="store_true",
        help="reuse existing DATA_BRIDGE_STATUS (faster; still writes run history)",
    )
    args = parser.parse_args()
    _ = args.now

    repo = (args.repo_root or Path(__file__).resolve().parents[3]).resolve()
    node_dir = repo / "research/forward_v1/desk"
    started = utc_now()
    run_id = f"FORWARD_RUN_{started.strftime('%Y%m%dT%H%M%SZ')}"

    # 1 READ T0 (immutable)
    t0_path = repo / T0_EVENTS
    t0_events = load_jsonl(t0_path)
    class_counts: dict[str, int] = {}
    for event in t0_events:
        cls = classify_execution(event)
        class_counts[cls] = class_counts.get(cls, 0) + 1
    t0_asof = sorted({e.get("market_bar_asof") for e in t0_events if e.get("market_bar_asof")})
    mark_buy = sum(1 for e in t0_events if str(e.get("signal_type") or "").endswith("MARK_BUY"))
    book_add = sum(1 for e in t0_events if "book_ADD" in str(e.get("signal_type") or ""))

    # 2 DATA
    tool_rcs: dict[str, int] = {}
    bridge_out = ""
    if not args.skip_bridge:
        tool_rcs["data_bridge"], bridge_out = run_py(
            repo, "research/forward_v1/desk/tools/data_bridge.py", timeout=900
        )
    else:
        tool_rcs["data_bridge"] = 0
    tool_rcs["data_factory"], _ = run_py(
        repo, "research/forward_v1/desk/tools/data_factory_status.py"
    )

    bridge = load_json(node_dir / "data_bridge/DATA_BRIDGE_STATUS.json")
    df = load_json(node_dir / "data_factory/DATA_FACTORY_STATUS.json")
    data_status = bridge.get("status") or df.get("status") or "UNKNOWN"
    latest_bar = bridge.get("latest_bar") or df.get("latest_bar")
    if bridge.get("yahoo_fallback"):
        data_source = "PRIMARY+YAHOO_FALLBACK"
    elif bridge.get("source"):
        data_source = bridge.get("source")
    else:
        data_source = df.get("source") or "UNKNOWN"

    # 3-4 SIGNAL
    engine_meta = {
        "desk_run_warehouse_write": str(ENGINE_WRITE),
        "live_scan_snapshot": str(ENGINE_SNAP),
        "engine_dir_exists": ENGINE_DIR.exists(),
        "write_script_exists": ENGINE_WRITE.exists(),
        "snap_script_exists": ENGINE_SNAP.exists(),
    }
    tool_rcs["signal_capture"], _ = run_py(
        repo,
        "research/forward_v1/desk/signal_capture/capture_as_emitted.py",
        extra=["--mode", "status"],
    )
    sc = load_json(node_dir / "signal_capture/SIGNAL_CAPTURE_STATUS.json")
    signal_status = sc.get("status") or "SIGNAL_CAPTURE_BLOCKED"
    new_events = int(sc.get("events_written") or 0)
    signal_reason = sc.get("note") or sc.get("distinction") or None
    if not signal_status:
        if not ENGINE_WRITE.exists():
            signal_status = "SIGNAL_CAPTURE_BLOCKED"
            signal_reason = "ORIGINAL engine scripts missing on this box"
        else:
            signal_status = "NO_NEW_SIGNAL"
            signal_reason = "capture adapter returned empty status"

    # T1 LIVE FORWARD capture gate — never invent T1; never re-label T0
    try:
        t1mod = _load_t1_capture()
        t1_capture_status = t1mod.capture_t1_if_ready(repo, run_id=run_id)
        tool_rcs["t1_capture"] = 0
    except Exception as exc:  # noqa: BLE001
        t1_capture_status = {
            "schema": "DESK_T1_CAPTURE_STATUS.v1",
            "T1_STATUS": "ERROR",
            "NEW_SIGNAL": 0,
            "new_events": 0,
            "new_trades": 0,
            "confirmation_cohort_open": False,
            "confirmation_cohort": "CONFIRMATION_COHORT|EMPTY",
            "error": str(exc),
            "t0_untouched": True,
        }
        tool_rcs["t1_capture"] = 1
    if t1_capture_status.get("T1_STATUS") == "CAPTURED":
        signal_status = "T1_CAPTURED"
        new_events = int(t1_capture_status.get("new_events") or 0)
        signal_reason = (t1_capture_status.get("gate") or {}).get("reason") or signal_reason
    elif t1_capture_status.get("T1_STATUS") == "CAPTURED_ALREADY":
        signal_status = "NO_NEW_SIGNAL"
        new_events = 0
        signal_reason = (
            (t1_capture_status.get("gate") or {}).get("reason")
            or t1_capture_status.get("knowledge_note")
            or "anti-reprocess: T1 emit already captured"
        )
    else:
        # Prefer honest NO_NEW_SIGNAL / blocker; do not invent
        if signal_status not in {"SIGNAL_CAPTURE_BLOCKED", "SIGNAL_CAPTURE_BLOCKED_DATA_STALE", "SIGNAL_CAPTURE_BLOCKED_ENGINE_MISSING"}:
            if t1_capture_status.get("T1_STATUS") in {
                "BLOCKED_WAITING_NEW_BAR", "BLOCKED_WAITING_ENGINE_EMIT"
            }:
                signal_status = "NO_NEW_SIGNAL"
                signal_reason = (
                    f"T1={t1_capture_status.get('T1_STATUS')}: "
                    + str((t1_capture_status.get("gate") or {}).get("reason")
                          or t1_capture_status.get("knowledge_note") or "")
                )

    # 5-8 SHADOW BOOK
    executable_events = [e for e in t0_events if classify_execution(e) == "EXECUTABLE"]
    policy_reason = (
        f"T0: book_ADD={book_add} MARK_BUY={mark_buy}; "
        "EXECUTION_POLICY: book_ADD=BOOK_ACTION/OBSERVATION only → EMPTY_BY_POLICY"
    )
    ledger_meta = ensure_empty_ledgers(node_dir / "ledgers", run_id, policy_reason)

    shadow = {
        "schema": "desk.shadow_book_status.v1",
        "run_id": run_id,
        "checked_at_utc": iso_z(utc_now()),
        "checked_at_hkt": hkt_str(utc_now()),
        "status": "EMPTY_BY_POLICY",
        "open_positions": 0,
        "closed_trades": 0,
        "new_orders": 0,
        "observation_only_events": book_add,
        "executable_events": len(executable_events),
        "policy": "desk.book_ADD => BOOK_ACTION/OBSERVATION; never auto MARK_BUY/ARMED/TRUST_UP",
        "reason": policy_reason,
        "net_pnl": "NOT_AVAILABLE",
        "fee_slippage": "NOT_INVENTED",
    }
    shadow_dir = node_dir / "shadow_book"
    shadow_dir.mkdir(parents=True, exist_ok=True)
    (shadow_dir / "SHADOW_BOOK_STATUS.json").write_text(
        json.dumps(shadow, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    with (shadow_dir / "observation_ledger.jsonl").open("a", encoding="utf-8") as fh:
        for event in t0_events:
            fh.write(
                json.dumps(
                    {
                        "run_id": run_id,
                        "event_id": event.get("event_id"),
                        "ticker": event.get("ticker"),
                        "signal_type": event.get("signal_type"),
                        "classification": classify_execution(event),
                        "price_at_signal": event.get("price_at_signal"),
                        "market_bar_asof": event.get("market_bar_asof"),
                        "action": "OBSERVATION_ONLY",
                        "shadow_order": None,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    # 9 RESOLVE — reuse live_forward_resolver (all horizons; no invented prices)
    tool_rcs["live_forward_resolver"], _ = run_py(
        repo, "research/forward_v1/desk/tools/live_forward_resolver.py", timeout=600
    )
    res = load_json(node_dir / "resolution/FORWARD_STATUS.json")
    resolved_5d = int(res.get("resolved_5d") or 0)
    resolved_21d = int(res.get("resolved_21d") or 0)
    resolved_63d = int(res.get("resolved_63d") or 0)
    resolved_126d = int(res.get("resolved_126d") or 0)
    resolved_252d = int(res.get("resolved_252d") or 0)
    newly_resolved = int(res.get("newly_resolved") or 0)
    waiting = int(res.get("waiting") or 0)

    # 9b RESEARCH MEMORY V1 — always update even when NEW_SIGNAL=0
    tool_rcs["research_memory_build"], mem_out = run_py(
        repo,
        "research/forward_v1/desk/tools/research_memory_build.py",
        extra=["--run-id", run_id],
        timeout=300,
    )
    mem_status = load_json(node_dir / "research_memory/MEMORY_STATUS.json")
    if not mem_status and mem_out:
        try:
            mem_status = json.loads(mem_out.strip().splitlines()[-1])
        except Exception:  # noqa: BLE001
            mem_status = {"status": "MEMORY_BUILD_PARSE_FAILED", "raw_tail": mem_out[-500:]}

    # 9c RESEARCH EVOLUTION V1 + T1 CONFIRM — even when NEW_SIGNAL=0
    t1_new = int(t1_capture_status.get("NEW_SIGNAL") or 0) if isinstance(t1_capture_status, dict) else 0
    evo_new_signals = t1_new if t1_new else new_events
    t1_status_path = node_dir / "status/T1_CAPTURE_STATUS.json"
    evo_extra = ["--run-id", run_id, "--new-signals", str(evo_new_signals)]
    if t1_status_path.exists():
        evo_extra.extend(["--t1-status-json", str(t1_status_path)])
    tool_rcs["research_evolution"], evo_out = run_py(
        repo,
        "research/forward_v1/desk/tools/research_evolution.py",
        extra=evo_extra,
        timeout=300,
    )
    evo_status = load_json(node_dir / "research_evolution/RESEARCH_EVOLUTION_STATUS.json")
    if not evo_status and evo_out:
        try:
            evo_status = json.loads(evo_out.strip().splitlines()[-1])
        except Exception:  # noqa: BLE001
            evo_status = {"status": "EVOLUTION_PARSE_FAILED", "raw_tail": evo_out[-500:]}
    if isinstance(evo_status, dict) and isinstance(t1_capture_status, dict):
        evo_status["t1_capture"] = {
            "T1_STATUS": t1_capture_status.get("T1_STATUS"),
            "NEW_SIGNAL": t1_capture_status.get("NEW_SIGNAL"),
            "confirmation_cohort": t1_capture_status.get("confirmation_cohort"),
            "confirmation_cohort_open": t1_capture_status.get("confirmation_cohort_open"),
            "formal_previous_asof": t1_capture_status.get("formal_previous_asof"),
        }

    post_days = int(
        bridge.get("post_anchor_trading_days_qqq")
        or bridge.get("post_anchor_trading_days_min_t0_tickers")
        or 0
    )
    waiting_21 = "WAITING_FOR_FUTURE_BARS" if post_days < 21 else "ELIGIBLE_CHECK"

    analysis = {
        "schema": "desk.forward_analysis.v1",
        "run_id": run_id,
        "shadow_book": "EMPTY_BY_POLICY",
        "reason": policy_reason,
        "signal_level_outcomes": {
            "events_total": len(t0_events),
            "waiting_slots": waiting,
            "resolved_5d": resolved_5d,
            "newly_resolved": newly_resolved,
            "benchmark": BENCH,
            "evaluation_clock": EVAL_CLOCK,
            "note": "OBSERVED research outcomes only — not trade P&L; not probability; never mix REPLAY",
        },
        "horizons": {
            "5": "RESOLVED" if resolved_5d else "WAITING_FOR_FUTURE_BARS",
            "21": waiting_21,
            "63": "WAITING_FOR_FUTURE_BARS",
            "126": "WAITING_FOR_FUTURE_BARS",
            "252": "WAITING_FOR_FUTURE_BARS",
        },
        "portfolio": {
            "open_positions": 0,
            "closed_trades": 0,
            "realized_pnl": None,
            "unrealized_pnl": None,
            "net_pnl": "NOT_AVAILABLE",
            "note": "No executable signals → no shadow positions; NET_PNL not assumed; fees/slippage not invented",
        },
        "mix_policy": "NEVER_MIX_LIVE_FORWARD_WITH_REPLAY_FORWARD_WINRATE",
    }
    reports_dir = node_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    analysis_rel = f"research/forward_v1/desk/reports/ANALYSIS_{run_id}.json"
    (repo / analysis_rel).write_text(
        json.dumps(analysis, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    finished = utc_now()
    blocked_reason = None
    status = "OK_CYCLE_COMPLETE"
    if data_status in {"DATA_STALE", "BLOCKED", "DATA_BLOCKED"}:
        status = "DATA_BLOCKED"
        blocked_reason = f"data_status={data_status}"
    if signal_status == "NO_NEW_SIGNAL":
        blocked_reason = signal_reason or "NO_NEW_SIGNAL (same bar as T0 or no new engine emit)"
        status = "OK_CYCLE_COMPLETE"
    elif str(signal_status).startswith("SIGNAL_CAPTURE_BLOCKED"):
        blocked_reason = signal_reason or signal_status
        status = "SIGNAL_CAPTURE_BLOCKED"
    elif data_status not in {"DATA_FRESH", "FRESH", "OK"} and tool_rcs.get("data_bridge", 0) != 0:
        status = "DATA_BLOCKED"
        blocked_reason = (blocked_reason or "") + f"; bridge_rc={tool_rcs.get('data_bridge')} {bridge_out[-200:]}"

    report_rel = f"research/forward_v1/desk/reports/REPORT_{run_id}.html"
    hist_rel = f"research/forward_v1/desk/run_history/{run_id}.json"

    run_doc = {
        "run_id": run_id,
        "started_at": iso_z(started),
        "finished_at": iso_z(finished),
        "started_at_hkt": hkt_str(started),
        "finished_at_hkt": hkt_str(finished),
        "node": NODE,
        "app_id": APP_ID,
        "hub_name": HUB_NAME,
        "model_version": MODEL,
        "evaluation_clock": EVAL_CLOCK,
        "benchmark": BENCH,
        "data_asof": latest_bar,
        "engine_asof": t0_asof,
        "data_status": data_status,
        "data_source": data_source,
        "yahoo_fallback": bool(bridge.get("yahoo_fallback")),
        "signal_status": signal_status,
        "new_events": new_events,
        "new_executable_signals": len(executable_events),
        "new_orders": 0,
        "position_changes": 0,
        "resolved_5d": resolved_5d,
        "resolved_21d": resolved_21d,
        "resolved_63d": resolved_63d,
        "resolved_126d": resolved_126d,
        "resolved_252d": resolved_252d,
        "newly_resolved": newly_resolved,
        "waiting": waiting,
        "open_positions": 0,
        "closed_trades": 0,
        "portfolio_value": None,
        "realized_pnl": None,
        "unrealized_pnl": None,
        "total_pnl": None,
        "net_pnl": "NOT_AVAILABLE",
        "total_return_pct": None,
        "benchmark_return_pct": None,
        "excess_return_pct": None,
        "status": status,
        "blocked_reason": blocked_reason,
        "event_class_counts": class_counts,
        "t0_events": len(t0_events),
        "t0_book_ADD": book_add,
        "t0_MARK_BUY": mark_buy,
        "t0_untouched": True,
        "original_engine": engine_meta,
        "event_file": T0_EVENTS,
        "position_file": "research/forward_v1/desk/ledgers/positions.jsonl",
        "trade_file": "research/forward_v1/desk/ledgers/trades.jsonl",
        "signal_trade_map_file": "research/forward_v1/desk/ledgers/signal_trade_map.jsonl",
        "portfolio_daily_file": "research/forward_v1/desk/ledgers/portfolio_daily.jsonl",
        "shadow_book_file": "research/forward_v1/desk/shadow_book/SHADOW_BOOK_STATUS.json",
        "analysis_file": analysis_rel,
        "report_file": report_rel,
        "resolution_status_file": "research/forward_v1/desk/resolution/FORWARD_STATUS.json",
        "research_memory": mem_status,
        "research_memory_report": "research/forward_v1/desk/research_memory/REPORT_RESEARCH_MEMORY.html",
        "research_profile": "research/forward_v1/desk/research_profile.json",
        "research_evolution": evo_status,
        "research_evolution_report": "research/forward_v1/desk/research_evolution/REPORT_RESEARCH_EVOLUTION.html",
        "t1_capture": t1_capture_status,
        "honesty": [
            "T0 immutable",
            "book_ADD => BOOK_ACTION/OBSERVATION only — never auto MARK_BUY/ARMED/TRUST_UP",
            "score/alignScore != probability",
            "LIVE_FORWARD != REPLAY_FORWARD (no Cap-Rail/RelVol mix)",
            "YAHOO_FALLBACK provenance labeled when used",
            "fees/slippage NET_PNL = NOT_AVAILABLE without real source",
            "no invented prices or trades from book_ADD",
            "RESEARCH MEMORY append-only; profile versioned; no invented features",
            "RESEARCH EVOLUTION: DISCOVERY≠BUY; NEVER confirm on discovery cohort alone",
            "T1 gate: market_bar_asof > formal previous asof + original engine emit; Yahoo must not invent Desk signals",
            "confirmation_status ∈ UNTESTED|PENDING|CONFIRMED|REJECTED; discovery_n ≠ confirmation_n",
            "Anti-loop: identical run → new T1=0, new evidence=0, KNOWLEDGE_DELTA=NONE",
            "new_hypotheses from T0 discovery MUST be 0 this stage (frozen set already exists)",
        ],
        "tool_rcs": tool_rcs,
        "ledger_meta": {k: {"rows": v.get("rows"), "note": v.get("note")} for k, v in ledger_meta.items()},
    }

    hist_dir = node_dir / "run_history"
    hist_dir.mkdir(parents=True, exist_ok=True)
    (hist_dir / f"{run_id}.json").write_text(
        json.dumps(run_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    policy_path = node_dir / "EXECUTION_POLICY.md"
    policy_text = policy_path.read_text(encoding="utf-8") if policy_path.exists() else ""
    write_html_report(repo / report_rel, run_doc, policy_text)

    tool_rcs["write_system_status"], _ = run_py(
        repo, "research/forward_v1/desk/tools/write_forward_system_status.py"
    )
    sys_path = node_dir / "status/FORWARD_SYSTEM_STATUS.json"
    sys_doc = load_json(sys_path)
    sys_doc.update(
        {
            "forward_runner": "V1.0",
            "last_run_id": run_id,
            "last_run_at_utc": iso_z(finished),
            "last_run_at_hkt": hkt_str(finished),
            "last_run_status": status,
            "last_blocked_reason": blocked_reason,
            "shadow_book": "EMPTY_BY_POLICY",
            "new_events": new_events,
            "new_orders": 0,
            "newly_resolved": newly_resolved,
            "run_history_file": hist_rel,
            "report_file": report_rel,
            "evaluation_clock": EVAL_CLOCK,
            "execution_policy": "book_ADD=OBSERVATION; MARK_BUY/ARMED/TRUST_UP only if engine-emitted executable",
            "research_memory": {
                "signal_memory_total": (mem_status or {}).get("signal_memory_total"),
                "t0_integrity": (mem_status or {}).get("t0_integrity"),
                "report": "research/forward_v1/desk/research_memory/REPORT_RESEARCH_MEMORY.html",
                "profile": "research/forward_v1/desk/research_profile.json",
            },
            "research_evolution": {
                "status": (evo_status or {}).get("status"),
                "hypotheses_frozen": ((evo_status or {}).get("hypothesis_counts") or {}).get("frozen"),
                "new_hypotheses": ((evo_status or {}).get("discovery_run") or {}).get("new_hypotheses"),
                "new_evidence": ((evo_status or {}).get("discovery_run") or {}).get("new_evidence"),
                "KNOWLEDGE_DELTA": ((evo_status or {}).get("discovery_run") or {}).get("KNOWLEDGE_DELTA"),
                "t0_integrity": (evo_status or {}).get("t0_integrity"),
                "report": "research/forward_v1/desk/research_evolution/REPORT_RESEARCH_EVOLUTION.html",
            },
            "t1_capture": {
                "T1_STATUS": (t1_capture_status or {}).get("T1_STATUS"),
                "NEW_SIGNAL": (t1_capture_status or {}).get("NEW_SIGNAL"),
                "confirmation_cohort": (t1_capture_status or {}).get("confirmation_cohort"),
                "confirmation_cohort_open": (t1_capture_status or {}).get("confirmation_cohort_open"),
                "formal_previous_asof": (t1_capture_status or {}).get("formal_previous_asof"),
            },
        }
    )
    sys_path.parent.mkdir(parents=True, exist_ok=True)
    sys_path.write_text(json.dumps(sys_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    (node_dir / "status/FORWARD_STATUS.json").write_text(
        json.dumps(
            {
                "schema": "FORWARD_STATUS.runner_overlay.v1",
                "last_run_id": run_id,
                "checked_at_utc": iso_z(finished),
                "checked_at_hkt": hkt_str(finished),
                "evaluation_clock": EVAL_CLOCK,
                "data": data_status,
                "signal": signal_status,
                "event": "T0_IMMUTABLE" if new_events == 0 else "NEW_EVENTS",
                "resolver": {
                    "resolved_5d": resolved_5d,
                    "waiting": waiting,
                    "newly_resolved": newly_resolved,
                    "maturity_anchor": res.get("maturity_anchor_value") or bridge.get("maturity_anchor"),
                },
                "shadow_book": "EMPTY_BY_POLICY",
                "blocked_reason": blocked_reason,
                "run_history": hist_rel,
                "report": report_rel,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    integrity = {
        "run_id": run_id,
        "t0_event_count_expected": 7,
        "t0_event_count_actual": len(t0_events),
        "book_ADD": book_add,
        "MARK_BUY": mark_buy,
        "class_counts": class_counts,
        "executable": class_counts.get("EXECUTABLE", 0),
        "open_positions": 0,
        "positions_must_be_zero": True,
        "t0_path_untouched": True,
        "evaluation_clock": EVAL_CLOCK,
        "no_replay_mix": True,
        "pass": (
            len(t0_events) == 7
            and mark_buy == 0
            and class_counts.get("EXECUTABLE", 0) == 0
            and book_add == 7
        ),
    }
    (node_dir / "status/RECONCILIATION.json").write_text(
        json.dumps(integrity, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


    evo_dr = (evo_status or {}).get("discovery_run") or {}
    evo_st = (evo_status or {}).get("research_state") or {}
    evo_prog = (evo_status or {}).get("research_progress") or {}
    evo_hc = (evo_status or {}).get("hypothesis_counts") or {}
    section19 = {
        "NODE": NODE,
        "T1": {
            "new_signals": int((t1_capture_status or {}).get("NEW_SIGNAL") or 0),
            "new_events": int((t1_capture_status or {}).get("new_events") or new_events or 0),
            "new_trades": 0,
            "status": (t1_capture_status or {}).get("T1_STATUS"),
            "blocked": (
                None if (t1_capture_status or {}).get("T1_STATUS") in {"CAPTURED", "CAPTURED_ALREADY"}
                else ((t1_capture_status or {}).get("gate") or {}).get("reason")
                or (t1_capture_status or {}).get("knowledge_note")
                or (t1_capture_status or {}).get("T1_STATUS")
            ),
            "provenance_gate": (t1_capture_status or {}).get("provenance_gate")
                or ((t1_capture_status or {}).get("gate") or {}).get("provenance_gate")
                or "REQUIRED",
            "engine_run_id": (t1_capture_status or {}).get("engine_run_id"),
            "source_hash": (t1_capture_status or {}).get("source_hash"),
            "market_bar_asof": (t1_capture_status or {}).get("market_bar_asof"),
            "confirmation_cohort_id": (t1_capture_status or {}).get("confirmation_cohort_id")
                or (t1_capture_status or {}).get("confirmation_cohort"),
        },
        "OUTCOME": {
            "new_5D": next((m.get("new_resolved") for m in (evo_dr.get("maturity_checks") or []) if m.get("horizon") == 5), 0),
            "new_21D": next((m.get("new_resolved") for m in (evo_dr.get("maturity_checks") or []) if m.get("horizon") == 21), 0),
            "new_63D": next((m.get("new_resolved") for m in (evo_dr.get("maturity_checks") or []) if m.get("horizon") == 63), 0),
            "new_126D": next((m.get("new_resolved") for m in (evo_dr.get("maturity_checks") or []) if m.get("horizon") == 126), 0),
            "new_252D": next((m.get("new_resolved") for m in (evo_dr.get("maturity_checks") or []) if m.get("horizon") == 252), 0),
        },
        "EVOLUTION": {
            "new_evidence": evo_dr.get("new_evidence", 0),
            "hypotheses_updated": evo_dr.get("extended_hypotheses", 0),
            "new_hypotheses": evo_dr.get("new_hypotheses", 0),
            "confirmed": evo_dr.get("confirmed", 0),
            "rejected": evo_dr.get("rejected", 0),
            "pending": evo_dr.get("pending") or evo_hc.get("pending", 0),
            "untested": evo_dr.get("untested") or evo_hc.get("untested", 0),
            "knowledge_delta": evo_dr.get("KNOWLEDGE_DELTA") or evo_st.get("KNOWLEDGE_DELTA") or evo_prog.get("KNOWLEDGE_DELTA"),
        },
        "CONFIRMATION_COHORT": {
            "n": int(evo_st.get("confirmation_signals_n") or 0),
            "id": evo_st.get("confirmation_cohort") or (t1_capture_status or {}).get("confirmation_cohort"),
            "open": bool(evo_st.get("confirmation_cohort_open") or (t1_capture_status or {}).get("confirmation_cohort_open")),
        },
        "RESEARCH_PROGRESS": {
            "WHAT WE KNEW BEFORE": evo_prog.get("BEFORE") or evo_prog.get("what_system_knew_before"),
            "WHAT WE KNOW NOW": evo_prog.get("NOW") or evo_prog.get("what_system_knows_now_that_it_did_not_know_before"),
            "WHAT CHANGED": evo_prog.get("CHANGED"),
            "WHAT REMAINS UNTESTED": evo_prog.get("UNTESTED") or evo_hc.get("untested"),
        },
        "T0_INTEGRITY": "PASS" if integrity.get("pass") and (evo_status or {}).get("t0_integrity") != "FAIL" else "FAIL",
    }
    run_doc["section19"] = section19
    # rewrite run history with section19
    (hist_dir / f"{run_id}.json").write_text(
        json.dumps(run_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    summary = {
        "run_id": run_id,
        "status": status,
        "signal": signal_status,
        "data": data_status,
        "new_events": new_events,
        "new_orders": 0,
        "newly_resolved": newly_resolved,
        "resolved_5d": resolved_5d,
        "waiting": waiting,
        "shadow_book": "EMPTY_BY_POLICY",
        "blocked_reason": blocked_reason,
        "hist": hist_rel,
        "report": report_rel,
        "integrity_pass": integrity["pass"],
        "research_memory_rows": (mem_status or {}).get("signal_memory_total"),
        "research_memory_t0_integrity": (mem_status or {}).get("t0_integrity"),
        "research_memory_example_event_id": (mem_status or {}).get("example_event_id"),
        "research_evolution_new_hypotheses": ((evo_status or {}).get("discovery_run") or {}).get("new_hypotheses"),
        "research_evolution_new_evidence": ((evo_status or {}).get("discovery_run") or {}).get("new_evidence"),
        "research_evolution_unchanged": ((evo_status or {}).get("discovery_run") or {}).get("unchanged"),
        "research_evolution_t0_integrity": (evo_status or {}).get("t0_integrity"),
        "T1_STATUS": (t1_capture_status or {}).get("T1_STATUS"),
        "NEW_SIGNAL": (t1_capture_status or {}).get("NEW_SIGNAL"),
        "provenance_gate": (t1_capture_status or {}).get("provenance_gate") or "REQUIRED",
        "KNOWLEDGE_DELTA": ((evo_status or {}).get("discovery_run") or {}).get("KNOWLEDGE_DELTA"),
        "confirmation_cohort": (t1_capture_status or {}).get("confirmation_cohort"),
        "section19": section19,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if integrity["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
