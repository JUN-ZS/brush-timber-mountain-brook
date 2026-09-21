#!/usr/bin/env python3
"""Desk（信股慣性台）RESEARCH MEMORY V1 — profile-driven signal_memory + outcome join.

Append-only signal_memory. Never rewrite T0. Never invent features / P&L / probability.
book_ADD stays BOOK_ACTION / OBSERVATION. evaluation_clock = LIVE_FORWARD. Benchmark = QQQ.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

T0_EVENTS = "research/forward_v1/desk/T0_20260921T183800/events.jsonl"
T0_OUTCOMES = "research/forward_v1/desk/T0_20260921T183800/outcomes.jsonl"
HORIZONS = [5, 21, 63, 126, 252]
BUCKET_RULE = "DECLARED_V1"
EVAL_CLOCK = "LIVE_FORWARD"
BENCHMARK = "QQQ"
NODE = "desk"

# Emit-time keys verified on T0 conditions_raw / state (never invent extras).
CONDITIONS_KEYS = [
    "alignScore",
    "opportunity",
    "bandPosPct",
    "relVol20",
    "markBuyLine",
    "book_action",
    "book_board",
    "book_line",
    "book_addScore",
    "book_trimScore",
    "whyNotBuy",
    "reason",
    "priceState",
    "volState",
    "source",
    "alignScore_note",
    "opportunity_note",
]
STATE_KEYS = ["desk_state", "regime", "shape", "trustUp", "hot", "trend.rising"]
# Engine-known but absent on T0 → always NOT_AVAILABLE in snapshot
ENGINE_ONLY_NOT_ON_T0 = ["ATR", "pressure_upper_price", "pressure_lower_price", "relState"]


def iso_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_jsonl(path: Path) -> list:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def append_jsonl(path: Path, rows: list) -> int:
    """Append-only by event_id — skip if already present."""
    path.parent.mkdir(parents=True, exist_ok=True)
    existing_ids = {r.get("event_id") for r in load_jsonl(path)}
    n = 0
    with path.open("a", encoding="utf-8") as fh:
        for row in rows:
            eid = row.get("event_id")
            if eid in existing_ids:
                continue
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            existing_ids.add(eid)
            n += 1
    return n


def na(value):
    return value if value is not None else "NOT_AVAILABLE"


def bucket_align(v) -> str:
    if v is None or v == "NOT_AVAILABLE":
        return "align_null"
    try:
        x = float(v)
    except (TypeError, ValueError):
        return "align_null"
    if x < 35:
        return "align_lt_35"
    if x < 55:
        return "align_35_55"
    return "align_ge_55"


def bucket_band(v) -> str:
    if v is None or v == "NOT_AVAILABLE":
        return "band_null"
    try:
        x = float(v)
    except (TypeError, ValueError):
        return "band_null"
    if x <= 25:
        return "band_le_25"
    if x <= 50:
        return "band_25_50"
    if x <= 75:
        return "band_50_75"
    return "band_gt_75"


def classify_execution(event: dict) -> str:
    st = str(event.get("signal_type") or "")
    base = st.split(".")[-1] if st else ""
    if "book_ADD" in st or "book_TRIM" in st or "book_HOLD" in st or base in {
        "book_ADD",
        "book_TRIM",
        "book_HOLD",
    }:
        return "BOOK_ACTION"
    exec_types = {
        "MARK_BUY",
        "ARMED",
        "TRUST_UP",
        "BUY",
        "SELL",
        "OPEN",
        "CLOSE",
        "TRIM",
        "REDUCE",
        "REVERSE",
    }
    if base.upper() in exec_types or st.upper() in exec_types:
        return "EXECUTABLE"
    if event.get("provenance_label") == "Historical" or str(event.get("source") or "").startswith(
        "ui_demo"
    ):
        return "AUDIT_ONLY"
    return "RESEARCH_SIGNAL"


def extract_conditions(event: dict) -> dict:
    raw = event.get("conditions_raw") or event.get("conditionsRaw") or {}
    out = {}
    for k in CONDITIONS_KEYS:
        out[k] = raw[k] if k in raw else "NOT_AVAILABLE"
    for k in ENGINE_ONLY_NOT_ON_T0:
        out[k] = raw[k] if k in raw else "NOT_AVAILABLE"
    return out


def extract_state(event: dict) -> dict:
    st = event.get("state") or {}
    out = {}
    for k in STATE_KEYS:
        out[k] = st[k] if k in st else "NOT_AVAILABLE"
    return out


def feature_snapshot(event: dict) -> dict:
    cond = extract_conditions(event)
    state = extract_state(event)
    align = cond.get("alignScore")
    band = cond.get("bandPosPct")
    if align == "NOT_AVAILABLE":
        align_v = None
    else:
        align_v = align
    if band == "NOT_AVAILABLE":
        band_v = None
    else:
        band_v = band
    return {
        "alignScore": cond.get("alignScore"),
        "opportunity": cond.get("opportunity"),
        "bandPosPct": cond.get("bandPosPct"),
        "relVol20": cond.get("relVol20"),
        "desk_state": state.get("desk_state"),
        "regime": state.get("regime"),
        "shape": state.get("shape"),
        "trustUp": state.get("trustUp"),
        "hot": state.get("hot"),
        "trend.rising": state.get("trend.rising"),
        "book_action": cond.get("book_action"),
        "book_board": cond.get("book_board"),
        "book_line": cond.get("book_line"),
        "book_addScore": cond.get("book_addScore"),
        "book_trimScore": cond.get("book_trimScore"),
        "markBuyLine": cond.get("markBuyLine"),
        "whyNotBuy": cond.get("whyNotBuy"),
        "priceState": cond.get("priceState"),
        "volState": cond.get("volState"),
        "source": cond.get("source"),
        "score": event.get("score"),
        "score_field": event.get("score_field"),
        "score_label": event.get("score_label") or "NOT_A_PROBABILITY",
        "rank": event.get("rank"),
        "price_at_signal": event.get("price_at_signal"),
        "universe_id": event.get("universe_id"),
        "universe_asof": event.get("universe_asof"),
        "claimed_p": event.get("claimed_p"),
        "claimed_p_note": event.get("claimed_p_note"),
        # engine-only absences
        "ATR": cond.get("ATR"),
        "pressure_upper_price": cond.get("pressure_upper_price"),
        "pressure_lower_price": cond.get("pressure_lower_price"),
        "relState": cond.get("relState"),
        # declared derived (a priori — no hindsight)
        "alignScore_bucket": bucket_align(align_v),
        "bandPosPct_bucket": bucket_band(band_v),
        "bucket_rule_version": BUCKET_RULE,
    }


def build_signal_rows(events: list, run_id: str) -> list:
    rows = []
    for e in events:
        snap = feature_snapshot(e)
        exec_class = classify_execution(e)
        rows.append(
            {
                "schema": "desk.research_memory.signal_v1",
                "memory_id": f"mem|{e.get('event_id')}",
                "event_id": e.get("event_id"),
                "run_id": run_id,
                "profile_version": "research_profile_v1",
                "ticker": e.get("ticker"),
                "signal_timestamp": e.get("signal_timestamp"),
                "market_bar_asof": e.get("market_bar_asof"),
                "signal_type": e.get("signal_type"),
                "rank": e.get("rank"),
                "score": e.get("score"),
                "score_field": e.get("score_field"),
                "score_label": e.get("score_label") or "NOT_A_PROBABILITY",
                "evaluation_clock": EVAL_CLOCK,
                "benchmark": BENCHMARK,
                "pool": "FORMAL",
                "execution_class": exec_class,
                "trade_action": "OBSERVATION"
                if exec_class == "BOOK_ACTION"
                else ("NO_TRADE" if exec_class != "EXECUTABLE" else "EXECUTABLE_PENDING"),
                "feature_snapshot": snap,
                "state": extract_state(e),
                "conditions_raw": extract_conditions(e),
                "provenance": {
                    "source": "T0_EVENTS_AS_EMITTED",
                    "model_version": e.get("model_version"),
                    "data_source": e.get("data_source"),
                    "code_commit": e.get("code_commit"),
                    "app_id": e.get("app_id"),
                    "leakage": "NONE_EMIT_TIME_FIELDS_ONLY",
                },
                "recorded_at": iso_z(),
                "immutable": True,
            }
        )
    return rows


def load_outcomes(node: Path, repo: Path) -> dict:
    """event_id -> {horizon -> outcome}. Prefer RESOLVED from resolution appends over T0 stubs."""
    by: dict = defaultdict(dict)

    def ingest(rows: list) -> None:
        for o in rows:
            eid = o.get("event_id")
            h = o.get("horizon_trading_days")
            if eid is None or h is None:
                continue
            prev = by[eid].get(h)
            if prev and prev.get("status") == "RESOLVED" and o.get("status") != "RESOLVED":
                continue
            by[eid][h] = o

    ingest(load_jsonl(repo / T0_OUTCOMES))
    for name in ("OUTCOME_APPEND.jsonl", "OUTCOME_APPEND_5D.jsonl"):
        ingest(load_jsonl(node / "resolution" / name))
    return by


def join_rows(sig_rows: list, outcomes_by: dict) -> list:
    out = []
    for s in sig_rows:
        eid = s["event_id"]
        oc = outcomes_by.get(eid) or {}
        join = {
            "schema": "desk.research_memory.signal_outcome_join_v1",
            "event_id": eid,
            "ticker": s["ticker"],
            "signal_type": s["signal_type"],
            "pool": s["pool"],
            "evaluation_clock": s["evaluation_clock"],
            "benchmark": s["benchmark"],
            "feature_snapshot": s["feature_snapshot"],
            "execution_class": s["execution_class"],
            "trade_action": s["trade_action"],
            "horizons": {},
            "pnl_linked": None,
            "pnl_note": "book_ADD = BOOK_ACTION/OBSERVATION → no invented trade P&L",
            "joined_at": iso_z(),
        }
        for h in HORIZONS:
            o = oc.get(h)
            if not o:
                join["horizons"][str(h)] = {
                    "status": "WAITING_FOR_FUTURE_BARS",
                    "absolute_return": None,
                    "benchmark_return": None,
                    "excess_return": None,
                    "absolute_hit": None,
                    "excess_hit": None,
                }
            else:
                st = o.get("status") or o.get("label") or "WAITING_FOR_FUTURE_BARS"
                if st == "RESOLVED":
                    join["horizons"][str(h)] = {
                        "status": "RESOLVED",
                        "absolute_return": o.get("raw_return")
                        if o.get("raw_return") is not None
                        else o.get("absolute_return"),
                        "benchmark_return": o.get("benchmark_return"),
                        "excess_return": o.get("excess_return"),
                        "absolute_hit": o.get("absolute_hit"),
                        "excess_hit": o.get("excess_hit"),
                        "entry_price": o.get("entry_price"),
                        "exit_price": o.get("exit_price"),
                        "MFE": o.get("MFE"),
                        "MAE": o.get("MAE"),
                        "data_source": o.get("data_source") or o.get("price_source"),
                        "evaluation_clock": o.get("evaluation_clock") or EVAL_CLOCK,
                    }
                else:
                    if st in ("WAITING", "IMMATURE"):
                        st = "WAITING_FOR_FUTURE_BARS"
                    join["horizons"][str(h)] = {
                        "status": st,
                        "absolute_return": None,
                        "benchmark_return": None,
                        "excess_return": None,
                        "absolute_hit": None,
                        "excess_hit": None,
                        "entry_price": o.get("entry_price"),
                        "note": o.get("note"),
                    }
        out.append(join)
    return out


def conditional_analysis(joins: list) -> dict:
    """DECLARED_V1 buckets only; FORMAL rows; RESOLVED 5D; THIN_SAMPLE if n<10."""
    dims = [
        ("alignScore_bucket", lambda j: (j.get("feature_snapshot") or {}).get("alignScore_bucket")),
        ("bandPosPct_bucket", lambda j: (j.get("feature_snapshot") or {}).get("bandPosPct_bucket")),
        ("signal_type", lambda j: j.get("signal_type")),
        ("regime", lambda j: (j.get("feature_snapshot") or {}).get("regime")),
        ("shape", lambda j: (j.get("feature_snapshot") or {}).get("shape")),
        ("desk_state", lambda j: (j.get("feature_snapshot") or {}).get("desk_state")),
        ("book_board", lambda j: (j.get("feature_snapshot") or {}).get("book_board")),
        ("trustUp", lambda j: (j.get("feature_snapshot") or {}).get("trustUp")),
    ]
    formal = [j for j in joins if j.get("pool") == "FORMAL"]
    report = {
        "schema": "desk.conditional_analysis_v1",
        "bucket_rule_version": BUCKET_RULE,
        "evaluation_clock": EVAL_CLOCK,
        "benchmark": BENCHMARK,
        "horizon": 5,
        "note": (
            "OBSERVED on RESOLVED formal only; THIN_SAMPLE if n<10; "
            "not probability; no hindsight rebucket; LIVE ≠ REPLAY"
        ),
        "groups": {},
        "n_formal_signals": len(formal),
        "n_resolved_5d": 0,
        "generated_at": iso_z(),
    }
    resolved_count = 0
    for dim_name, getter in dims:
        cells: dict = defaultdict(list)
        for j in formal:
            key = getter(j)
            if key is None or key == "NOT_AVAILABLE":
                key = "NULL"
            h5 = (j.get("horizons") or {}).get("5") or {}
            if h5.get("status") != "RESOLVED":
                continue
            cells[str(key)].append(h5)
        dim_out = {}
        for k, rows in sorted(cells.items()):
            n = len(rows)
            if dim_name == "alignScore_bucket":
                resolved_count = max(resolved_count, sum(len(v) for v in cells.values()))
            abs_hits = sum(1 for r in rows if r.get("absolute_hit") is True)
            ex_hits = sum(1 for r in rows if r.get("excess_hit") is True)
            avg_abs = (
                sum((r.get("absolute_return") or 0) for r in rows) / n if n else None
            )
            avg_ex = sum((r.get("excess_return") or 0) for r in rows) / n if n else None
            dim_out[k] = {
                "n": n,
                "sample_status": "THIN_SAMPLE" if n < 10 else "OK",
                "absolute_hit_rate_RESOLVED_ONLY": abs_hits / n if n else None,
                "excess_hit_rate_RESOLVED_ONLY": ex_hits / n if n else None,
                "mean_absolute_return_RESOLVED_ONLY": avg_abs,
                "mean_excess_return_RESOLVED_ONLY": avg_ex,
                "label": "OBSERVED_FORWARD_OUTCOME_NOT_PROBABILITY",
            }
        report["groups"][dim_name] = dim_out
    # accurate resolved count
    report["n_resolved_5d"] = sum(
        1
        for j in formal
        if ((j.get("horizons") or {}).get("5") or {}).get("status") == "RESOLVED"
    )
    return report


def write_html(path: Path, profile: dict, joins: list, analysis: dict, example: dict) -> None:
    data = json.dumps(joins, ensure_ascii=False)
    analysis_j = json.dumps(analysis, ensure_ascii=False)
    ex = json.dumps(example, ensure_ascii=False)
    html = f"""<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="utf-8"/>
<title>Desk RESEARCH MEMORY</title>
<style>
body{{font-family:system-ui,sans-serif;margin:20px;background:#0b0f14;color:#e6edf3}}
.badge{{display:inline-block;padding:2px 8px;border-radius:999px;background:#238636;margin-right:6px}}
.warn{{background:#9e6a03}}
input,select{{background:#161b22;color:#e6edf3;border:1px solid #30363d;padding:6px;margin:4px}}
table{{border-collapse:collapse;width:100%;font-size:13px}}
th,td{{border:1px solid #30363d;padding:6px;vertical-align:top}}
th{{background:#161b22}}
pre{{background:#161b22;padding:12px;overflow:auto;max-height:480px}}
.panel{{margin:16px 0;padding:12px;border:1px solid #30363d;border-radius:8px}}
</style></head><body>
<h1>信股慣性台 / Desk — RESEARCH MEMORY</h1>
<p><span class="badge">{EVAL_CLOCK}</span><span class="badge">{BENCHMARK}</span>
<span class="badge">profile {profile.get('profile_version')}</span>
<span class="badge warn">book_ADD≠MARK_BUY</span></p>
<p>score / alignScore / opportunity = <b>NOT_A_PROBABILITY</b> · claimed_p = MODEL_CLAIM ·
observed outcomes separate · BOOK_ACTION = OBSERVATION · no invented P&amp;L</p>
<div class="panel">
<label>ticker <input id="ft" placeholder="SMH"/></label>
<label>signal_type <input id="fs" placeholder="book_ADD"/></label>
<label>regime <input id="fr" placeholder="RISK_ON_COMPAT"/></label>
<label>shape <input id="fsh" placeholder="CHOPPY"/></label>
<label>desk_state <input id="fd" placeholder="DORMANT"/></label>
<button onclick="render()">Filter</button>
</div>
<div class="panel"><h2>Signals → features → outcomes</h2><div id="tbl"></div></div>
<div class="panel"><h2>Selected signal drill-down</h2><pre id="detail">click a row</pre></div>
<div class="panel"><h2>Example (acceptance)</h2><pre id="ex"></pre></div>
<div class="panel"><h2>Conditional analysis (DECLARED_V1 · 5D formal)</h2><pre id="an"></pre></div>
<script>
const JOINS = {data};
const ANALYSIS = {analysis_j};
const EXAMPLE = {ex};
document.getElementById('ex').textContent = JSON.stringify(EXAMPLE, null, 2);
document.getElementById('an').textContent = JSON.stringify(ANALYSIS, null, 2);
function render(){{
  const ft=document.getElementById('ft').value.trim().toUpperCase();
  const fs=document.getElementById('fs').value.trim();
  const fr=document.getElementById('fr').value.trim();
  const fsh=document.getElementById('fsh').value.trim();
  const fd=document.getElementById('fd').value.trim();
  const rows=JOINS.filter(j=>{{
    const f=j.feature_snapshot||{{}};
    if(ft && j.ticker!==ft) return false;
    if(fs && !(j.signal_type||'').includes(fs)) return false;
    if(fr && f.regime!==fr) return false;
    if(fsh && f.shape!==fsh) return false;
    if(fd && f.desk_state!==fd) return false;
    return true;
  }});
  let h='<table><tr><th>ticker</th><th>type</th><th>exec</th><th>align</th><th>band%</th><th>desk</th><th>shape</th><th>5D abs</th><th>5D excess</th><th>5D status</th></tr>';
  rows.forEach((j,i)=>{{
    const f=j.feature_snapshot||{{}};
    const h5=(j.horizons||{{}})['5']||{{}};
    const abs=h5.absolute_return==null?'—':(Number(h5.absolute_return)*100).toFixed(2)+'%';
    const ex=h5.excess_return==null?'—':(Number(h5.excess_return)*100).toFixed(2)+'%';
    h+=`<tr onclick="show(${{i}})" style="cursor:pointer"><td>${{j.ticker}}</td><td>${{j.signal_type}}</td><td>${{j.execution_class}}</td><td>${{f.alignScore??'—'}}</td><td>${{f.bandPosPct??'—'}}</td><td>${{f.desk_state??'—'}}</td><td>${{f.shape??'—'}}</td><td>${{abs}}</td><td>${{ex}}</td><td>${{h5.status}}</td></tr>`;
  }});
  window._rows=rows;
  h+='</table><p>n='+rows.length+'</p>';
  document.getElementById('tbl').innerHTML=h;
}}
function show(i){{
  const j=window._rows[i];
  const block={{
    SIGNAL: {{ticker:j.ticker, event_id:j.event_id, signal_type:j.signal_type, pool:j.pool}},
    WHAT_ENGINE_SAW: j.feature_snapshot,
    WHAT_ACTION: j.execution_class + ' / ' + j.trade_action + ' (book_ADD ≠ MARK_BUY; no shadow BUY)',
    WHAT_HAPPENED_AFTER: j.horizons,
    TRADE_RESULT: 'NONE — BOOK_ACTION/OBSERVATION; MARK_BUY=0',
    BENCHMARK: j.benchmark,
    PNL: null
  }};
  document.getElementById('detail').textContent=JSON.stringify(block,null,2);
}}
render();
</script>
</body></html>"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


def build_example(joins: list) -> dict:
    if not joins:
        return {"note": "no joins"}
    # Prefer first FORMAL row (SMH typically)
    j = next((x for x in joins if x.get("pool") == "FORMAL"), joins[0])
    return {
        "schema": "desk.research_memory.example_v1",
        "event_id": j.get("event_id"),
        "ticker": j.get("ticker"),
        "signal_type": j.get("signal_type"),
        "what_recorded": j.get("feature_snapshot"),
        "execution_class": j.get("execution_class"),
        "trade_action": j.get("trade_action"),
        "future_outcomes_linked": j.get("horizons"),
        "pnl_linked": None,
        "note": "book_ADD → BOOK_ACTION/OBSERVATION; no P&L; outcomes are research signal-level only",
    }


def run_research_memory(repo: Path, run_id: str | None = None) -> dict:
    node = repo / "research/forward_v1/desk"
    mem = node / "research_memory"
    mem.mkdir(parents=True, exist_ok=True)
    (mem / "conditional_analysis").mkdir(parents=True, exist_ok=True)
    (node / "conditional_analysis").mkdir(parents=True, exist_ok=True)

    profile_path = node / "research_profile.json"
    if not profile_path.exists():
        raise SystemExit(f"missing {profile_path}")
    profile = json.loads(profile_path.read_text(encoding="utf-8"))

    t0_ev = repo / T0_EVENTS
    t0_oc = repo / T0_OUTCOMES
    sha_before_ev = sha256_file(t0_ev)
    sha_before_oc = sha256_file(t0_oc)

    run_id = run_id or f"MEMORY_BUILD_{iso_z().replace(':', '').replace('-', '')}"
    events = load_jsonl(t0_ev)
    # Also append any newer capture events if present (still append-only by event_id)
    capture_events = node / "signal_capture"
    for path in sorted(capture_events.glob("*.jsonl")) if capture_events.exists() else []:
        # only event-like files — skip status
        if "STATUS" in path.name.upper():
            continue
        events.extend(load_jsonl(path))

    # Dedup source events by event_id (prefer first / T0)
    seen = set()
    uniq_events = []
    for e in events:
        eid = e.get("event_id")
        if not eid or eid in seen:
            continue
        seen.add(eid)
        uniq_events.append(e)

    sig_rows = build_signal_rows(uniq_events, run_id)
    n_new = append_jsonl(mem / "signal_memory.jsonl", sig_rows)

    all_sig = load_jsonl(mem / "signal_memory.jsonl")
    by_eid = {}
    for s in all_sig:
        by_eid[s["event_id"]] = s
    sig_unique = list(by_eid.values())

    outcomes = load_outcomes(node, repo)
    joins = join_rows(sig_unique, outcomes)
    (mem / "signal_outcome_join.jsonl").write_text(
        "".join(json.dumps(j, ensure_ascii=False) + "\n" for j in joins),
        encoding="utf-8",
    )

    analysis = conditional_analysis(joins)
    analysis_json = json.dumps(analysis, indent=2, ensure_ascii=False) + "\n"
    (mem / "conditional_analysis" / "CONDITIONAL_5D_DECLARED_V1.json").write_text(
        analysis_json, encoding="utf-8"
    )
    (node / "conditional_analysis" / "CONDITIONAL_5D_DECLARED_V1.json").write_text(
        analysis_json, encoding="utf-8"
    )

    example = build_example(joins)
    (mem / "EXAMPLE_SIGNAL.json").write_text(
        json.dumps(example, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    report = mem / "REPORT_RESEARCH_MEMORY.html"
    write_html(report, profile, joins, analysis, example)

    readme = """# Desk RESEARCH MEMORY V1（信股慣性台）

Append-only 研究記憶：信號特徵 → 條件×結果 join → DECLARED 桶分析。

## 檔案
- `signal_memory.jsonl` — 發射時欄位（唔漏未來棒）；append-only
- `signal_outcome_join.jsonl` — 5/21/63/126/252；未熟 = WAITING
- `conditional_analysis/CONDITIONAL_5D_DECLARED_V1.json` — DECLARED_V1 桶
- `REPORT_RESEARCH_MEMORY.html` — 互動 drill-down
- `EXAMPLE_SIGNAL.json` — 驗收例
- `MEMORY_STATUS.json` — 最新 build

## 鎖
- T0 immutable
- evaluation_clock = LIVE_FORWARD；benchmark = QQQ
- score / alignScore / opportunity = NOT_A_PROBABILITY
- book_ADD = BOOK_ACTION / OBSERVATION；唔發明 P&L；MARK_BUY=0
- LIVE ≠ REPLAY 混池
"""
    (mem / "README.md").write_text(readme, encoding="utf-8")

    sha_after_ev = sha256_file(t0_ev)
    sha_after_oc = sha256_file(t0_oc)
    t0_ok = sha_before_ev == sha_after_ev and sha_before_oc == sha_after_oc

    waiting = sum(
        1
        for j in joins
        for h in HORIZONS
        if ((j.get("horizons") or {}).get(str(h)) or {}).get("status")
        == "WAITING_FOR_FUTURE_BARS"
    )
    resolved = sum(
        1
        for j in joins
        for h in HORIZONS
        if ((j.get("horizons") or {}).get(str(h)) or {}).get("status") == "RESOLVED"
    )
    book_add = sum(1 for s in sig_unique if "book_ADD" in str(s.get("signal_type") or ""))
    mark_buy = sum(1 for s in sig_unique if str(s.get("signal_type") or "").endswith("MARK_BUY"))

    status = {
        "schema": "desk.research_memory.status_v1",
        "node": NODE,
        "version": "RESEARCH_MEMORY_V1",
        "profile_version": profile.get("profile_version"),
        "evaluation_clock": EVAL_CLOCK,
        "benchmark": BENCHMARK,
        "signal_memory_total": len(sig_unique),
        "signal_memory_new_appended": n_new,
        "joins": len(joins),
        "outcome_slots_waiting": waiting,
        "outcome_slots_resolved": resolved,
        "book_ADD": book_add,
        "MARK_BUY": mark_buy,
        "execution_policy": "book_ADD=BOOK_ACTION/OBSERVATION; MARK_BUY=0",
        "t0_untouched": t0_ok,
        "t0_events_sha256": sha_before_ev,
        "t0_outcomes_sha256": sha_before_oc,
        "t0_integrity": "PASS" if t0_ok else "FAIL",
        "example_event_id": example.get("event_id"),
        "report": str(report.relative_to(repo)),
        "built_at": iso_z(),
        "run_id": run_id,
    }
    (mem / "MEMORY_STATUS.json").write_text(
        json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return status


def main() -> None:
    ap = argparse.ArgumentParser(description="Desk RESEARCH MEMORY V1")
    ap.add_argument("--repo-root", type=Path, default=None)
    ap.add_argument("--run-id", default=None)
    args = ap.parse_args()
    repo = (args.repo_root or Path(__file__).resolve().parents[3]).resolve()
    status = run_research_memory(repo, run_id=args.run_id)
    print(json.dumps(status, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
