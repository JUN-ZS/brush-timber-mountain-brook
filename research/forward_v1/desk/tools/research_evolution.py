#!/usr/bin/env python3
"""Desk（信股慣性台）RESEARCH EVOLUTION V1 + T1 HYPOTHESIS CONFIRMATION V1

Learning layer on RESEARCH MEMORY V1.
Reads memory artifacts; does NOT rewrite T0 / engine / EXECUTION_POLICY.

Locks:
- DISCOVERY ≠ TRADING RULE / HYPOTHESIS ≠ BUY
- observed ≠ probability; score/alignScore ≠ probability
- evaluation_clock = LIVE_FORWARD; benchmark = QQQ
- Discovery cohort (T0) ≠ confirmation cohort (T1+ ONLY; temporal split)
- confirmation_status ∈ {UNTESTED, PENDING, CONFIRMED, REJECTED} only
- Never CONFIRMED from discovery cohort alone; never rewrite H formula
- No new H mass-mint from T0 once frozen set exists (T1 stage → new_hypotheses=0)
- Keep all MEMORY artifacts intact
- book_ADD = observation only; never upgrade → MARK_BUY
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

NODE = "desk"
VERSION = "RESEARCH_EVOLUTION_V1_T1_CONFIRM"
EVAL_CLOCK = "LIVE_FORWARD"
BENCHMARK = "QQQ"
HORIZONS = [5, 21, 63, 126, 252]
THIN_N = 10  # Desk T0 is small (7)
MIN_FREEZE_RESOLVED = 1  # when resolutions exist; WAITING path uses n>0
MAX_NEW_FREEZE_PER_RUN = 48
PROFILE_VERSION = "research_profile_v1"

# Desk priority dims — only used when present with provenance in profile.
PRIORITY_DIMS = [
    "alignScore", "opportunity", "desk_state", "regime", "shape",
    "trend.rising", "trustUp", "hot", "bandPosPct", "relVol20",
    "book_addScore", "book_trimScore", "book_board", "book_action",
    "whyNotBuy", "signal_type",
]
PRIMARY_HZ = 5


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_stamp(dt: datetime | None = None) -> str:
    return (dt or utc_now()).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_stamp(dt: datetime | None = None) -> str:
    return (dt or utc_now()).strftime("%Y%m%dT%H%M%SZ")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def append_jsonl(path: Path, rows: Iterable[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("a") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
    return n


def write_jsonl(path: Path, rows: Iterable[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
    return n


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def desk_root(repo: Path) -> Path:
    return repo / "research" / "forward_v1" / "desk"


def memory_dir(desk: Path) -> Path:
    return desk / "research_memory"


def evolution_dir(desk: Path) -> Path:
    # Desk-only evolution tree; builds on MEMORY, does not replace it.
    return desk / "research_evolution"


def find_t0(desk: Path) -> Path:
    t0s = sorted(desk.glob("T0_*"))
    if not t0s:
        raise SystemExit("no T0_* under desk")
    return t0s[-1]


def t0_paths(t0: Path) -> tuple[Path, Path]:
    events = t0 / "events.jsonl"
    outcomes = t0 / "outcomes.jsonl"
    if not events.exists():
        raise SystemExit(f"missing T0 events: {events}")
    if not outcomes.exists():
        raise SystemExit(f"missing T0 outcomes: {outcomes}")
    return events, outcomes


def _num(v: Any) -> float | None:
    if v is None or v == "NOT_AVAILABLE":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _median(xs: list[float]) -> float | None:
    if not xs:
        return None
    return float(statistics.median(xs))


def _stdev(xs: list[float]) -> float | None:
    if len(xs) < 2:
        return None
    return float(statistics.pstdev(xs))


# ---------------------------------------------------------------------------
# A-priori discovery buckets (DECLARED_V1 + Desk priority; no hindsight search)
# ---------------------------------------------------------------------------

def bucket_align(v: Any) -> str:
    x = _num(v)
    if x is None:
        return "align_null"
    if x < 35:
        return "align_lt_35"
    if x < 55:
        return "align_35_55"
    return "align_ge_55"


def bucket_band(v: Any) -> str:
    x = _num(v)
    if x is None:
        return "band_null"
    if x <= 25:
        return "band_le_25"
    if x <= 50:
        return "band_25_50"
    if x <= 75:
        return "band_50_75"
    return "band_gt_75"


def bucket_opportunity(v: Any) -> str:
    x = _num(v)
    if x is None:
        return "opp_null"
    if x <= 0:
        return "opp_0"
    if x < 25:
        return "opp_lt_25"
    if x < 50:
        return "opp_25_50"
    return "opp_ge_50"


def bucket_relvol(v: Any) -> str:
    x = _num(v)
    if x is None:
        return "relvol_null"
    if x < 0.70:
        return "relvol_lt_0p70"
    if x < 1.0:
        return "relvol_0p70_1p0"
    if x < 1.5:
        return "relvol_1p0_1p5"
    return "relvol_ge_1p5"


def bucket_book_add(v: Any) -> str:
    x = _num(v)
    if x is None:
        return "book_add_null"
    if x < 25:
        return "book_add_lt_25"
    if x < 50:
        return "book_add_25_50"
    return "book_add_ge_50"


def bucket_why_not_buy(v: Any) -> str:
    if v is None or v == "NOT_AVAILABLE":
        return "whyNotBuy_null"
    if isinstance(v, list):
        n = len(v)
    else:
        n = 1 if v else 0
    if n == 0:
        return "whyNotBuy_0"
    if n <= 3:
        return "whyNotBuy_1_3"
    if n <= 6:
        return "whyNotBuy_4_6"
    return "whyNotBuy_ge_7"


def bool_bucket(name: str, v: Any) -> str:
    if v is None or v == "NOT_AVAILABLE":
        return f"{name}_null"
    return f"{name}_{str(bool(v)).lower()}"


def conditions_of(sig: dict) -> dict[str, Any]:
    fs = sig.get("feature_snapshot") or {}
    raw = sig.get("conditions_raw") or {}
    state = sig.get("state") or {}

    def g(*keys: str) -> Any:
        for k in keys:
            if k in fs and fs[k] is not None:
                return fs[k]
            if k in raw and raw[k] is not None:
                return raw[k]
            if k in state and state[k] is not None:
                return state[k]
            if k in sig and sig[k] is not None:
                return sig[k]
        return None

    align = g("alignScore", "score")
    band = g("bandPosPct")
    opp = g("opportunity")
    relv = g("relVol20")
    book_add = g("book_addScore")
    why = g("whyNotBuy")
    trust = g("trustUp")
    hot = g("hot")
    trend = g("trend.rising")
    return {
        "alignScore": align,
        "alignScore_bucket": fs.get("alignScore_bucket") or bucket_align(align),
        "opportunity": opp,
        "opportunity_bucket": bucket_opportunity(opp),
        "bandPosPct": band,
        "bandPosPct_bucket": fs.get("bandPosPct_bucket") or bucket_band(band),
        "relVol20": relv,
        "relVol20_bucket": bucket_relvol(relv),
        "desk_state": g("desk_state"),
        "regime": g("regime"),
        "shape": g("shape"),
        "trustUp": trust,
        "trustUp_bucket": bool_bucket("trustUp", trust),
        "hot": hot,
        "hot_bucket": bool_bucket("hot", hot),
        "trend.rising": trend,
        "trend_rising_bucket": bool_bucket("trend_rising", trend),
        "book_action": g("book_action"),
        "book_board": g("book_board"),
        "book_addScore": book_add,
        "book_addScore_bucket": bucket_book_add(book_add),
        "book_trimScore": g("book_trimScore"),
        "whyNotBuy": why,
        "whyNotBuy_bucket": bucket_why_not_buy(why),
        "signal_type": sig.get("signal_type"),
        "priceState": g("priceState"),
        "volState": g("volState"),
    }


def provenance_present(profile: dict) -> set[str]:
    names: set[str] = set()
    for row in profile.get("feature_provenance") or []:
        n = row.get("name")
        if n:
            names.add(n)
    for section in (
        "signal_features", "state_features", "ranking_features",
        "regime_features", "execution_features", "market_context_features",
    ):
        for row in profile.get(section) or []:
            n = row.get("name")
            if n:
                names.add(n)
    for row in profile.get("derived_features") or []:
        n = row.get("name")
        src = row.get("source")
        if n and src and (src in names):
            names.add(n)
    names.add("signal_type")
    hv = profile.get("hypothesis_verification") or {}
    for k, v in hv.items():
        if isinstance(v, str) and v.startswith("PRESENT"):
            names.add(k)
    return names


def discovery_dim_specs(present: set[str]) -> list[tuple[str, Callable[[dict], str | None]]]:
    specs: list[tuple[str, Callable[[dict], str | None]]] = []

    def add(dim: str, getter: Callable[[dict], str | None], need: set[str] | None = None) -> None:
        if need and not any(n in present for n in need):
            return
        specs.append((dim, getter))

    # DECLARED_V1
    add("alignScore_bucket", lambda c: c.get("alignScore_bucket"), {"alignScore", "alignScore_bucket"})
    add("bandPosPct_bucket", lambda c: c.get("bandPosPct_bucket"), {"bandPosPct", "bandPosPct_bucket"})
    add("signal_type", lambda c: c.get("signal_type"), {"signal_type"})
    add("regime", lambda c: c.get("regime"), {"regime"})
    add("shape", lambda c: c.get("shape"), {"shape"})
    add("desk_state", lambda c: c.get("desk_state"), {"desk_state"})
    add("book_board", lambda c: c.get("book_board"), {"book_board"})
    add("trustUp_bucket", lambda c: c.get("trustUp_bucket"), {"trustUp"})

    # DISCOVERY_CANDIDATES (Desk priority)
    add("opportunity_bucket", lambda c: c.get("opportunity_bucket"), {"opportunity"})
    add("relVol20_bucket", lambda c: c.get("relVol20_bucket"), {"relVol20"})
    add("hot_bucket", lambda c: c.get("hot_bucket"), {"hot"})
    add("trend_rising_bucket", lambda c: c.get("trend_rising_bucket"), {"trend.rising"})
    add("book_action", lambda c: c.get("book_action"), {"book_action"})
    add("book_addScore_bucket", lambda c: c.get("book_addScore_bucket"), {"book_addScore"})
    add("whyNotBuy_bucket", lambda c: c.get("whyNotBuy_bucket"), {"whyNotBuy"})
    return specs


def combo_specs(present: set[str]) -> list[tuple[str, Callable[[dict], str | None]]]:
    out: list[tuple[str, Callable[[dict], str | None]]] = []
    if {"desk_state", "shape"} & present:
        out.append(("desk_state+shape", lambda c: f"{c.get('desk_state')}|{c.get('shape')}"))
    if {"alignScore", "bandPosPct"} & present or {"alignScore_bucket", "bandPosPct_bucket"} & present:
        out.append(("alignScore_bucket+bandPosPct_bucket",
                    lambda c: f"{c.get('alignScore_bucket')}|{c.get('bandPosPct_bucket')}"))
    if {"trustUp", "hot"} & present:
        out.append(("trustUp_bucket+hot_bucket",
                    lambda c: f"{c.get('trustUp_bucket')}|{c.get('hot_bucket')}"))
    if {"regime", "shape"} & present:
        out.append(("regime+shape", lambda c: f"{c.get('regime')}|{c.get('shape')}"))
    if {"book_board", "desk_state"} & present:
        out.append(("book_board+desk_state",
                    lambda c: f"{c.get('book_board')}|{c.get('desk_state')}"))
    return out


def hyp_id(condition_key: str, horizon: int) -> str:
    digest = hashlib.sha256(f"{condition_key}|{horizon}".encode()).hexdigest()[:12]
    return f"HYP_DESK_{digest}"


def condition_label(dim: str, key: str) -> dict[str, Any]:
    return {
        "dimension": dim,
        "bucket": key,
        "formula": f"{dim} == {key}",
        "expression": f"{dim}={key}",
    }


def empty_stats() -> dict[str, Any]:
    return {
        "n": 0,
        "resolved_n": 0,
        "waiting_n": 0,
        "mean_return": None,
        "median_return": None,
        "mean_benchmark": None,
        "mean_excess": None,
        "hit_rate": None,
        "excess_hit_rate": None,
        "MFE": None,
        "MAE": None,
        "dispersion": None,
        "abs_returns": [],
        "excess_returns": [],
        "bench_returns": [],
        "mfes": [],
        "maes": [],
        "abs_hits": 0,
        "excess_hits": 0,
    }


def finalize_stats(st: dict[str, Any], *, time_period: str, cohort: str) -> dict[str, Any]:
    r = st["resolved_n"]
    abs_r = st["abs_returns"]
    exc_r = st["excess_returns"]
    ben_r = st["bench_returns"]
    waiting_only = r == 0 and st["waiting_n"] > 0
    out = {
        "n": st["n"],
        "resolved_n": r,
        "waiting_n": st["waiting_n"],
        "mean_return": (sum(abs_r) / r) if r else None,
        "median_return": _median(abs_r),
        "mean_benchmark": (sum(ben_r) / r) if r and ben_r else None,
        "mean_excess": (sum(exc_r) / r) if r and exc_r else None,
        "hit_rate": (st["abs_hits"] / r) if r else None,
        "excess_hit_rate": (st["excess_hits"] / r) if r else None,
        "MFE": _median(st["mfes"]) if st["mfes"] else None,
        "MAE": _median(st["maes"]) if st["maes"] else None,
        "dispersion": _stdev(exc_r) if exc_r else _stdev(abs_r),
        "time_period": time_period,
        "cohort": cohort,
        "evaluation_clock": EVAL_CLOCK,
        "benchmark": BENCHMARK,
        "thin_sample": bool(r < THIN_N),
        "sample_flag": (
            "WAITING_NO_RETURNS"
            if waiting_only
            else ("THIN_SAMPLE" if r < THIN_N else ("ADEQUATE_SAMPLE" if r else "NO_RESOLVED"))
        ),
        "returns_observable": bool(r > 0),
        "label": "OBSERVED_FORWARD_OUTCOME_NOT_PROBABILITY",
        "note": (
            "returns NOT observable yet — WAITING_FOR_FUTURE_BARS; do not invent returns "
            "(same honesty as BEAM #42)"
            if waiting_only
            else "observed_hit_rate + n + cohort + clock + benchmark — NOT a success probability"
        ),
    }
    return out


def accumulate(st: dict[str, Any], outcome: dict) -> None:
    st["n"] += 1
    status = outcome.get("status")
    if status == "RESOLVED":
        st["resolved_n"] += 1
        if outcome.get("absolute_return") is not None:
            st["abs_returns"].append(float(outcome["absolute_return"]))
        if outcome.get("excess_return") is not None:
            st["excess_returns"].append(float(outcome["excess_return"]))
        if outcome.get("benchmark_return") is not None:
            st["bench_returns"].append(float(outcome["benchmark_return"]))
        if outcome.get("absolute_hit") is True:
            st["abs_hits"] += 1
        if outcome.get("excess_hit") is True:
            st["excess_hits"] += 1
        if outcome.get("MFE") is not None:
            st["mfes"].append(float(outcome["MFE"]))
        if outcome.get("MAE") is not None:
            st["maes"].append(float(outcome["MAE"]))
    elif status in ("WAITING_FOR_FUTURE_BARS", "WAITING"):
        st["waiting_n"] += 1



def accumulate_horizon(st: dict[str, Any], hz_row: dict | None) -> None:
    if not hz_row:
        return
    st["n"] += 1
    status = hz_row.get("status")
    if status == "RESOLVED":
        st["resolved_n"] += 1
        if hz_row.get("absolute_return") is not None:
            st["abs_returns"].append(float(hz_row["absolute_return"]))
        if hz_row.get("excess_return") is not None:
            st["excess_returns"].append(float(hz_row["excess_return"]))
        if hz_row.get("benchmark_return") is not None:
            st["bench_returns"].append(float(hz_row["benchmark_return"]))
        if hz_row.get("absolute_hit") is True:
            st["abs_hits"] += 1
        if hz_row.get("excess_hit") is True:
            st["excess_hits"] += 1
        if hz_row.get("MFE") is not None:
            st["mfes"].append(float(hz_row["MFE"]))
        if hz_row.get("MAE") is not None:
            st["maes"].append(float(hz_row["MAE"]))
    elif status in ("WAITING_FOR_FUTURE_BARS", "WAITING"):
        st["waiting_n"] += 1


def flatten_joins(joins: list[dict]) -> list[dict]:
    """Expand signal_outcome_join horizons into flat outcome-like rows."""
    flat: list[dict] = []
    for j in joins:
        horizons = j.get("horizons") or {}
        for hz_s, row in horizons.items():
            flat.append({
                "event_id": j.get("event_id"),
                "ticker": j.get("ticker"),
                "horizon_trading_days": int(hz_s),
                "status": (row or {}).get("status"),
                "absolute_return": (row or {}).get("absolute_return"),
                "benchmark_return": (row or {}).get("benchmark_return"),
                "excess_return": (row or {}).get("excess_return"),
                "absolute_hit": (row or {}).get("absolute_hit"),
                "excess_hit": (row or {}).get("excess_hit"),
                "MFE": (row or {}).get("MFE"),
                "MAE": (row or {}).get("MAE"),
                "evaluation_clock": j.get("evaluation_clock") or EVAL_CLOCK,
                "benchmark": j.get("benchmark") or BENCHMARK,
            })
    return flat


def discovery_cohort_id(signals: list[dict]) -> str:
    asofs = sorted({s.get("market_bar_asof") for s in signals if s.get("market_bar_asof")})
    asof = asofs[0] if asofs else "UNKNOWN"
    return f"T0_DISCOVERY_COHORT|desk_market_bar_asof={asof}|mature_horizons=NONE_YET"


FORMAL_PREVIOUS_ASOF = "2026-09-18"


def confirmation_cohort_id(t1_status: dict | None = None) -> str:
    if t1_status and t1_status.get("confirmation_cohort_open") and t1_status.get("confirmation_cohort"):
        return str(t1_status["confirmation_cohort"])
    return "CONFIRMATION_COHORT|EMPTY"


def is_discovery_signal(sig: dict, formal_asof: str = FORMAL_PREVIOUS_ASOF) -> bool:
    if sig.get("signal_cohort") == "confirmation" or sig.get("capture_wave") == "T1":
        return False
    asof = str(sig.get("market_bar_asof") or "")[:10]
    return (not asof) or asof <= formal_asof


def is_confirmation_signal(sig: dict, formal_asof: str = FORMAL_PREVIOUS_ASOF) -> bool:
    if sig.get("signal_cohort") == "confirmation" or sig.get("capture_wave") == "T1":
        return True
    asof = str(sig.get("market_bar_asof") or "")[:10]
    return bool(asof and asof > formal_asof)


def load_t1_events(desk: Path) -> list[dict]:
    rows: list[dict] = []
    for t1 in sorted(desk.glob("T1_*")):
        for name in ("events.jsonl",):
            p = t1 / name
            if p.exists():
                rows.extend(load_jsonl(p))
        for p in sorted((t1 / "events").glob("*.jsonl")) if (t1 / "events").is_dir() else []:
            rows.extend(load_jsonl(p))
    # Accepted inbox mirrors
    inbox = desk / "signal_capture" / "T1_ENGINE_INBOX"
    if inbox.is_dir():
        for p in sorted(inbox.rglob("events.jsonl")):
            rows.extend(load_jsonl(p))
    return rows


def normalize_confirmation_status(raw: str | None, *, has_confirmation_cohort: bool, conf_n: int) -> str:
    """Statuses allowed: UNTESTED | PENDING | CONFIRMED | REJECTED."""
    allowed = {"UNTESTED", "PENDING", "CONFIRMED", "REJECTED"}
    if raw in ("CONFIRMED", "REJECTED"):
        return raw
    if not has_confirmation_cohort or conf_n <= 0:
        return "UNTESTED"
    if raw in allowed:
        return "PENDING" if raw in ("PENDING", "UNTESTED", None, "N/A", "WAITING") else raw
    return "PENDING" if conf_n > 0 else "UNTESTED"


def compute_stats_for_condition_joins(
    signals: list[dict],
    joins: list[dict],
    *,
    dimension: str,
    bucket: str,
    horizon: int,
    cohort_id: str,
    time_period: str,
) -> dict[str, Any]:
    """Accumulate join horizons for one frozen condition on a signal subset."""
    present = set(PRIORITY_DIMS)
    specs = {dim: getter for dim, getter in discovery_dim_specs(present) + combo_specs(present)}
    getter = specs.get(dimension)
    st = empty_stats()
    join_by_eid = {j["event_id"]: j for j in joins if j.get("event_id")}
    if getter is None:
        return finalize_stats(st, time_period=time_period, cohort=cohort_id)
    for sig in signals:
        cond = conditions_of(sig)
        key = getter(cond)
        if key is None or str(key) != str(bucket):
            continue
        j = join_by_eid.get(sig.get("event_id"))
        horizons = (j or {}).get("horizons") or {}
        accumulate_horizon(st, horizons.get(str(horizon)))
    return finalize_stats(st, time_period=time_period, cohort=cohort_id)


def score_for_rank(stats: dict[str, Any]) -> float:
    """Rank helper for freezing — NOT a probability."""
    r = stats.get("resolved_n") or 0
    if r <= 0:
        # Waiting dimension hyps: rank by n only (structural coverage)
        return float(stats.get("n") or 0) * 0.001
    mex = stats.get("mean_excess")
    if mex is None:
        return -1e9
    return abs(float(mex)) * math.sqrt(r)


def build_candidates(
    signals: list[dict],
    joins: list[dict],
    profile: dict,
) -> list[dict]:
    present = provenance_present(profile)
    present_priority = [d for d in PRIORITY_DIMS if d in present or d.split(".")[0] in present]
    specs = discovery_dim_specs(present) + combo_specs(present)

    join_by_eid = {j["event_id"]: j for j in joins if j.get("event_id")}
    cond_rows = [(s, conditions_of(s)) for s in signals]
    disc_cohort = discovery_cohort_id(signals)
    asofs = sorted({s.get("market_bar_asof") for s in signals if s.get("market_bar_asof")})
    time_period = f"{asofs[0]}→+horizons" if asofs else "UNKNOWN"

    declared_dims = {
        "alignScore_bucket", "bandPosPct_bucket", "signal_type", "regime",
        "shape", "desk_state", "book_board", "trustUp_bucket",
    }

    candidates: list[dict] = []
    for dim, getter in specs:
        cells: dict[str, dict[int, dict]] = defaultdict(lambda: {h: empty_stats() for h in HORIZONS})
        for sig, cond in cond_rows:
            key = getter(cond)
            if key is None or key == "None":
                continue
            key = str(key)
            j = join_by_eid.get(sig.get("event_id"))
            horizons = (j or {}).get("horizons") or {}
            for hz in HORIZONS:
                accumulate_horizon(cells[key][hz], horizons.get(str(hz)))
        for key, by_hz in cells.items():
            for hz, st in by_hz.items():
                stats = finalize_stats(st, time_period=time_period, cohort=disc_cohort)
                if stats["n"] <= 0:
                    continue
                kind = "DECLARED_BUCKET" if dim in declared_dims else "DISCOVERY_CANDIDATE"
                cond = condition_label(dim, key)
                candidates.append({
                    "candidate_id": hyp_id(f"{dim}={key}", hz),
                    "kind": kind,
                    "condition": cond,
                    "horizon_trading_days": hz,
                    "stats": stats,
                    "features_used": [dim.split("+")[0]] if "+" not in dim else dim.split("+"),
                    "priority_dims_available": present_priority,
                    "evaluation_clock": EVAL_CLOCK,
                    "benchmark": BENCHMARK,
                    "discovery_lock": "DISCOVERY_NOT_TRADING_RULE",
                    "hypothesis_lock": "HYPOTHESIS_NOT_BUY",
                })
    return candidates


def load_hypotheses(path: Path) -> dict[str, dict]:
    rows = load_jsonl(path)
    return {r["hypothesis_id"]: r for r in rows if "hypothesis_id" in r}


def freeze_formula(cond: dict, horizon: int) -> dict[str, Any]:
    return {
        "condition_dimension": cond["dimension"],
        "condition_bucket": cond["bucket"],
        "formula": cond["formula"],
        "threshold": cond["bucket"],
        "features": [cond["dimension"]],
        "horizon_trading_days": horizon,
        "frozen": True,
        "rewrite_forbidden": True,
    }


def pick_freeze_targets(
    candidates: list[dict],
    existing: dict[str, dict],
    *,
    all_waiting: bool,
) -> list[dict]:
    """Select candidates to freeze this run.

    When all outcomes WAITING: freeze primary-horizon dimension hyps with n>0
    (resolved_n=0 / WAITING) — do NOT invent returns.
    When resolutions exist: prefer resolved with adequate n.
    """
    scored = []
    for c in candidates:
        hid = c["candidate_id"]
        if hid in existing:
            continue
        st = c["stats"]
        if all_waiting:
            if c["horizon_trading_days"] != PRIMARY_HZ:
                continue
            if st["n"] <= 0:
                continue
            scored.append((float(st["n"]), c))
        else:
            if st["resolved_n"] < MIN_FREEZE_RESOLVED:
                continue
            scored.append((score_for_rank(st), c))
    scored.sort(key=lambda x: x[0], reverse=True)
    if all_waiting:
        declared = [c for s, c in scored if c["kind"] == "DECLARED_BUCKET" and "+" not in c["condition"]["dimension"]]
        disc = [c for s, c in scored if c["kind"] != "DECLARED_BUCKET" and "+" not in c["condition"]["dimension"]]
        combo = [c for s, c in scored if "+" in c["condition"]["dimension"]]
        ordered = declared + disc + combo
    else:
        five = [c for s, c in scored if c["horizon_trading_days"] == 5]
        other = [c for s, c in scored if c["horizon_trading_days"] != 5]
        ordered = five + other
    return ordered[:MAX_NEW_FREEZE_PER_RUN]


def compare_stats(prev: dict | None, cur: dict) -> dict[str, Any]:
    prev = prev or {}
    return {
        "resolved_n_delta": (cur.get("resolved_n") or 0) - (prev.get("resolved_n") or 0),
        "n_delta": (cur.get("n") or 0) - (prev.get("n") or 0),
        "mean_excess_prev": prev.get("mean_excess"),
        "mean_excess_now": cur.get("mean_excess"),
        "excess_hit_rate_prev": prev.get("excess_hit_rate"),
        "excess_hit_rate_now": cur.get("excess_hit_rate"),
    }


def decide_lifecycle(
    hyp: dict,
    *,
    discovery_stats: dict,
    confirmation_stats: dict,
    has_confirmation_cohort: bool,
    prev_confirmation_resolved: int,
) -> tuple[str, str, str]:
    """
    Returns (status, confirmation_status, evidence_action).
    confirmation_status ∈ {UNTESTED, PENDING, CONFIRMED, REJECTED} only.
    Discovery n never mixed into confirmed — CONFIRM/REJECT use confirmation_stats only.
    """
    prior = hyp.get("confirmation_status")
    if prior in ("CONFIRMED", "REJECTED"):
        return "HYPOTHESIS_FROZEN", prior, "UNCHANGED"

    cr = int(confirmation_stats.get("resolved_n") or 0)
    if not has_confirmation_cohort or cr <= 0:
        # Discovery maturity alone never promotes beyond UNTESTED
        return "HYPOTHESIS_FROZEN", "UNTESTED", "UNCHANGED"

    disc_mex = discovery_stats.get("mean_excess")
    conf_mex = confirmation_stats.get("mean_excess")
    if cr >= THIN_N and disc_mex is not None and conf_mex is not None:
        same_sign = (float(disc_mex) >= 0) == (float(conf_mex) >= 0)
        if same_sign:
            return "HYPOTHESIS_FROZEN", "CONFIRMED", "CONFIRM"
        return "HYPOTHESIS_FROZEN", "REJECTED", "REJECT"

    if cr > int(prev_confirmation_resolved or 0):
        return "HYPOTHESIS_FROZEN", "PENDING", "EXTEND_SAMPLE"
    return "HYPOTHESIS_FROZEN", "PENDING" if cr > 0 else "UNTESTED", "UNCHANGED"


def top_relationships(hypotheses: list[dict], limit: int = 8) -> list[dict]:
    frozen = [h for h in hypotheses if h.get("status") == "HYPOTHESIS_FROZEN"]
    def key(h: dict) -> float:
        st = h.get("current_stats") or h.get("discovery_stats") or {}
        return score_for_rank(st)
    frozen.sort(key=key, reverse=True)
    out = []
    for h in frozen[:limit]:
        st = h.get("current_stats") or h.get("discovery_stats") or {}
        cst = h.get("confirmation_stats") or {}
        out.append({
            "hypothesis_id": h["hypothesis_id"],
            "condition": h.get("condition", {}).get("formula") or h.get("condition"),
            "horizon": h.get("horizon_trading_days"),
            "n": st.get("n"),
            "discovery_n": h.get("discovery_n", st.get("resolved_n") or st.get("n")),
            "confirmation_n": h.get("confirmation_n", cst.get("resolved_n") or 0),
            "resolved_n": st.get("resolved_n"),
            "waiting_n": st.get("waiting_n"),
            "observed_return": st.get("mean_return"),
            "observed_excess": st.get("mean_excess"),
            "confirmation_mean_excess": cst.get("mean_excess"),
            "observed_hit_rate": st.get("hit_rate"),
            "observed_excess_hit_rate": st.get("excess_hit_rate"),
            "sample_flag": st.get("sample_flag"),
            "confirmation_status": h.get("confirmation_status"),
            "label": "OBSERVED_NOT_PROBABILITY",
            "note": st.get("note"),
        })
    return out


def research_progress(prev_state: dict | None, new_state: dict, run_summary: dict) -> dict[str, Any]:
    prev_state = prev_state or {}
    before = {
        "knew": [
            "RESEARCH MEMORY V1 profile + feature provenance",
            f"signal_memory rows={prev_state.get('signals_total') or 'MEMORY-only'}",
            f"outcome joins + resolved_5d={((prev_state.get('resolved') or {}).get('5'))}",
            "DECLARED_BUCKET conditional analysis (feature→horizon observed rates)",
            "Frozen T0 discovery hypotheses; confirmation cohort EMPTY until genuine T1",
        ],
        "hypotheses_total": prev_state.get("hypotheses_total", 0),
        "hypotheses_frozen": prev_state.get("hypotheses_frozen", prev_state.get("hypotheses_active", 0)),
        "last_discovery_run": prev_state.get("last_discovery_run"),
    }
    if not prev_state:
        before["knew"] = [
            "RESEARCH MEMORY V1 only: profile, 7 book_ADD signals, WAITING outcome slots",
            "No RESEARCH_STATE / HYPOTHESES / EVIDENCE_LOG / DISCOVERY_RUN",
            "No frozen condition→horizon hypotheses with confirmation cohort split",
        ]
    now_new = [
        (
            f"Frozen hypotheses exist: total={new_state.get('hypotheses_total')} "
            f"frozen={new_state.get('hypotheses_frozen')} "
            f"untested={new_state.get('hypotheses_untested')} "
            f"pending={new_state.get('hypotheses_pending')} "
            f"confirmed={new_state.get('hypotheses_confirmed')} rejected={new_state.get('hypotheses_rejected')} "
            f"— DISCOVERY≠BUY; confirmation_status ∈ UNTESTED|PENDING|CONFIRMED|REJECTED"
        ),
        (
            f"Evidence log + DISCOVERY_RUN deltas track learning across forward runs "
            f"(last_discovery_run={new_state.get('last_discovery_run')})"
        ),
        (
            f"Discovery cohort={new_state.get('discovery_cohort')}; "
            f"Confirmation cohort={new_state.get('confirmation_cohort')} "
            f"(temporal split; NEVER confirm on discovery cohort alone)"
        ),
        (
            "Top research relationships show discovery_n vs confirmation_n split "
            "(NOT probabilities; WAITING_NO_RETURNS when unresolved)"
        ),
    ]
    if run_summary.get("new_hypotheses", 0) > 0:
        now_new.insert(0,
            f"This run froze {run_summary['new_hypotheses']} new HYPOTHESIS_FROZEN records; DISCOVERY≠BUY"
        )
    if run_summary.get("new_evidence", 0) > 0:
        now_new.insert(0, f"This run appended {run_summary['new_evidence']} evidence events")
    if run_summary.get("extended_hypotheses", 0) > 0:
        now_new.append(f"This run extended sample on {run_summary['extended_hypotheses']} frozen hypotheses")
    if run_summary.get("confirmed", 0) > 0:
        now_new.append(f"This run confirmed {run_summary['confirmed']} hypotheses on confirmation cohort")
    if run_summary.get("rejected", 0) > 0:
        now_new.append(f"This run rejected {run_summary['rejected']} hypotheses on confirmation cohort")
    if not any([
        run_summary.get("new_hypotheses"),
        run_summary.get("new_evidence"),
        run_summary.get("extended_hypotheses"),
        run_summary.get("confirmed"),
        run_summary.get("rejected"),
    ]):
        now_new.append(
            "This run: NEW_SIGNAL=0 and no new resolutions — maturity/evidence checks ran with "
            "explicit unchanged counts (anti-loop / blocked waiting new bar)"
        )
    t1 = run_summary.get("t1_status_label") or run_summary.get("T1_STATUS")
    if t1 in ("BLOCKED_WAITING_NEW_BAR", "BLOCKED_WAITING_ENGINE_EMIT"):
        now_new.append(
            f"T1_STATUS={t1} — no genuine Desk T1 yet (need market_bar_asof > "
            f"{FORMAL_PREVIOUS_ASOF} + original engine emit); confirmation_cohort EMPTY; "
            "NEW_SIGNAL=0; did NOT invent T1 from Yahoo or re-label T0 "
            "(honesty like RelVol #44 / BEAM #45)."
        )
    elif t1:
        now_new.append(f"T1_STATUS={t1}")

    kd_none = (
        int(run_summary.get("new_signals") or 0) == 0
        and int(run_summary.get("new_evidence") or 0) == 0
        and int(run_summary.get("new_hypotheses") or 0) == 0
        and int(run_summary.get("confirmed") or 0) == 0
        and int(run_summary.get("rejected") or 0) == 0
        and int(run_summary.get("extended_hypotheses") or 0) == 0
    )
    knowledge_delta = "NONE" if kd_none else "UPDATED"

    untested_n = int(run_summary.get("untested") or new_state.get("hypotheses_untested") or 0)
    changed = []
    if run_summary.get("new_signals"):
        changed.append(f"new_signals={run_summary['new_signals']}")
    if run_summary.get("new_evidence"):
        changed.append(f"new_evidence={run_summary['new_evidence']}")
    if run_summary.get("confirmed"):
        changed.append(f"confirmed={run_summary['confirmed']}")
    if run_summary.get("rejected"):
        changed.append(f"rejected={run_summary['rejected']}")
    if run_summary.get("new_hypotheses"):
        changed.append(f"new_hypotheses={run_summary['new_hypotheses']}")
    if not changed:
        changed.append("none (anti-loop / blocked waiting new bar)")

    return {
        "BEFORE": before,
        "NOW": now_new,
        "CHANGED": changed,
        "UNTESTED": untested_n,
        "WHAT WE KNEW BEFORE": before,
        "WHAT WE KNOW NOW": now_new,
        "WHAT CHANGED": changed,
        "WHAT REMAINS UNTESTED": untested_n,
        "what_system_knew_before": before,
        "what_system_knows_now_that_it_did_not_know_before": now_new,
        "KNOWLEDGE_DELTA": knowledge_delta,
        "learning_delta": {
            "new_signals": run_summary.get("new_signals", 0),
            "new_resolved_outcomes": run_summary.get("new_resolved_outcomes", 0),
            "new_evidence": run_summary.get("new_evidence", 0),
            "new_hypotheses": run_summary.get("new_hypotheses", 0),
            "extended_hypotheses": run_summary.get("extended_hypotheses", 0),
            "confirmed": run_summary.get("confirmed", 0),
            "rejected": run_summary.get("rejected", 0),
            "unchanged": run_summary.get("unchanged", 0),
            "KNOWLEDGE_DELTA": knowledge_delta,
            "T1_STATUS": t1,
        },
    }



def count_resolved(outcomes: list[dict]) -> dict[str, int]:
    out = {str(h): 0 for h in HORIZONS}
    for o in outcomes:
        if o.get("status") == "RESOLVED":
            out[str(o["horizon_trading_days"])] = out.get(str(o["horizon_trading_days"]), 0) + 1
    return out


def count_waiting(outcomes: list[dict]) -> dict[str, int]:
    out = {str(h): 0 for h in HORIZONS}
    for o in outcomes:
        if o.get("status") in ("WAITING_FOR_FUTURE_BARS", "WAITING"):
            out[str(o["horizon_trading_days"])] = out.get(str(o["horizon_trading_days"]), 0) + 1
    return out


def count_live_replay(signals: list[dict]) -> tuple[int, int]:
    live = replay = 0
    for s in signals:
        clock = s.get("evaluation_clock") or EVAL_CLOCK
        if clock == "REPLAY_FORWARD":
            replay += 1
        else:
            live += 1
    return live, replay



def _write_evolution_html(path: Path, status: dict, discovery_run: dict, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": status,
        "discovery_run": discovery_run,
        "research_state": state,
        "disclaimer": (
            "Desk RESEARCH EVOLUTION V1 + T1 CONFIRM — DISCOVERY≠BUY · observed≠probability · "
            "score/alignScore≠probability · book_ADD=OBSERVATION · LIVE≠REPLAY · "
            "discovery_n ≠ confirmation_n · confirmation_status ∈ UNTESTED|PENDING|CONFIRMED|REJECTED"
        ),
    }
    data_js = json.dumps(payload, ensure_ascii=False)
    path.write_text(
        "<!DOCTYPE html>\n"
        "<html lang=\"zh-Hant\"><head><meta charset=\"utf-8\"/>\n"
        "<title>Desk RESEARCH EVOLUTION + T1 CONFIRM</title>\n"
        "<style>body{font-family:ui-monospace,monospace;margin:24px;background:#0b0f14;color:#e6edf3}"
        "h1,h2{color:#9ecbff}.badge{display:inline-block;padding:2px 8px;border-radius:6px;background:#1e2a44;margin-right:6px}"
        ".warn{color:#ffb4a2}.ok{color:#7ee787}.card{background:#121a2e;border:1px solid #2a3b5c;border-radius:10px;padding:12px;margin-top:12px}"
        ".grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}pre{background:#111827;padding:12px;overflow:auto;border-radius:8px;max-height:420px}"
        ".note{color:#9aa8c7;font-size:12px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #2a3b5c;padding:6px 8px;font-size:12px}th{background:#152038}</style></head><body>\n"
        "<h1>信股慣性台 / Desk — RESEARCH EVOLUTION <span class=\"badge\">V1</span> <span class=\"badge\">T1 CONFIRM</span></h1>\n"
        "<p class=\"note\" id=\"disclaimer\"></p>\n"
        "<p><span class=\"badge\">LIVE_FORWARD</span><span class=\"badge\">QQQ</span>"
        "<span class=\"badge warn\">DISCOVERY≠BUY</span><span class=\"badge warn\">discovery≠confirmation</span>"
        "<span class=\"badge\">UNTESTED|PENDING|CONFIRMED|REJECTED</span></p>\n"
        "<div class=\"grid\"><div class=\"card\"><h2>RESEARCH_STATE</h2><pre id=\"state\"></pre></div>"
        "<div class=\"card\"><h2>DISCOVERY_RUN + T1</h2><pre id=\"run\"></pre></div></div>\n"
        "<div class=\"card\"><h2>DISCOVERY vs CONFIRMATION SPLIT</h2>"
        "<table id=\"split\"><thead><tr><th>condition</th><th>hz</th><th>discovery_n</th><th>confirmation_n</th>"
        "<th>disc excess</th><th>conf excess</th><th>flag</th><th>confirm_status</th></tr></thead><tbody></tbody></table>"
        "<p class=\"note\">confirmation_status ∈ UNTESTED|PENDING|CONFIRMED|REJECTED. "
        "UNTESTED while confirmation_cohort EMPTY / BLOCKED_WAITING_NEW_BAR. "
        "Never CONFIRMED from discovery cohort alone.</p></div>\n"
        "<div class=\"card\"><h2>RESEARCH PROGRESS</h2><pre id=\"progress\"></pre></div>\n"
        "<div class=\"card\"><h2>Example hypothesis</h2><pre id=\"example\"></pre></div>\n"
        "<script>const DATA = " + data_js + ";\n"
        "document.getElementById('disclaimer').textContent = DATA.disclaimer;\n"
        "const st = DATA.research_state || {}; const dr = DATA.discovery_run || {};\n"
        "document.getElementById('state').textContent = JSON.stringify({signals_total:st.signals_total,discovery_signals_n:st.discovery_signals_n,confirmation_signals_n:st.confirmation_signals_n,resolved:st.resolved,waiting:st.waiting,hypotheses_frozen:st.hypotheses_frozen,hypotheses_untested:st.hypotheses_untested,hypotheses_pending:st.hypotheses_pending,hypotheses_confirmed:st.hypotheses_confirmed,hypotheses_rejected:st.hypotheses_rejected,discovery_cohort:st.discovery_cohort,confirmation_cohort:st.confirmation_cohort,confirmation_cohort_open:st.confirmation_cohort_open,T1_STATUS:st.T1_STATUS,KNOWLEDGE_DELTA:st.KNOWLEDGE_DELTA,t0_integrity:st.t0_integrity,locks:st.locks},null,2);\n"
        "document.getElementById('run').textContent = JSON.stringify({run_id:dr.run_id,new_signals:dr.new_signals,new_resolved_outcomes:dr.new_resolved_outcomes,new_evidence:dr.new_evidence,new_hypotheses:dr.new_hypotheses,unchanged:dr.unchanged,confirmed:dr.confirmed,rejected:dr.rejected,pending:dr.pending,untested:dr.untested,KNOWLEDGE_DELTA:dr.KNOWLEDGE_DELTA,T1_STATUS:dr.T1_STATUS,confirmation_cohort:dr.confirmation_cohort,maturity_checks:dr.maturity_checks},null,2);\n"
        "document.getElementById('progress').textContent = JSON.stringify(dr.research_progress||st.research_progress,null,2);\n"
        "document.getElementById('example').textContent = JSON.stringify(dr.example_hypothesis,null,2);\n"
        "const tb=document.querySelector('#split tbody');\n"
        "(dr.top_research_relationships||[]).forEach(r=>{const tr=document.createElement('tr');tr.innerHTML=`<td>${r.condition}</td><td>${r.horizon}</td><td>${r.discovery_n}</td><td>${r.confirmation_n}</td><td>${r.observed_excess}</td><td>${r.confirmation_mean_excess}</td><td>${r.sample_flag}</td><td>${r.confirmation_status}</td>`;tb.appendChild(tr);});\n"
        "</script></body></html>\n",
        encoding="utf-8",
    )



def run_research_evolution(
    repo: Path,
    *,
    run_id: str | None = None,
    new_signals: int | None = None,
    memory_status: dict | None = None,
    t1_status: dict | None = None,
) -> dict:
    desk = desk_root(repo)
    mem = memory_dir(desk)
    evo = evolution_dir(desk)
    evo.mkdir(parents=True, exist_ok=True)

    profile_path = desk / "research_profile.json"
    profile = load_json(profile_path)
    signals = load_jsonl(mem / "signal_memory.jsonl")
    joins = load_jsonl(mem / "signal_outcome_join.jsonl")
    if not signals or not joins:
        raise SystemExit("research_memory missing signal/join rows — run RESEARCH MEMORY first")

    # Merge T1 events into signal universe for confirmation stats (memory may lag)
    t1_events = load_t1_events(desk)
    seen_eids = {s.get("event_id") for s in signals}
    for row in t1_events:
        if row.get("event_id") not in seen_eids:
            signals.append(row)
            seen_eids.add(row.get("event_id"))

    outcomes = flatten_joins(joins)

    t0 = find_t0(desk)
    ev_path, oc_path = t0_paths(t0)
    t0_ev_sha = sha256_file(ev_path)
    t0_oc_sha = sha256_file(oc_path)

    state_path = evo / "RESEARCH_STATE.json"
    hyp_path = evo / "HYPOTHESES.jsonl"
    evidence_path = evo / "EVIDENCE_LOG.jsonl"

    prev_state = load_json(state_path) if state_path.exists() else None
    existing = load_hypotheses(hyp_path)
    frozen_formulas = {
        hid: dict(h["frozen_formula"])
        for hid, h in existing.items()
        if h.get("frozen_formula")
    }

    now = utc_now()
    rid = run_id or f"EVO_{run_stamp(now)}"
    formal_asof = FORMAL_PREVIOUS_ASOF
    disc_signals = [s for s in signals if is_discovery_signal(s, formal_asof)]
    conf_signals = [s for s in signals if is_confirmation_signal(s, formal_asof)]

    disc_cohort = discovery_cohort_id(disc_signals or signals)
    conf_cohort = confirmation_cohort_id(t1_status)
    if t1_status and t1_status.get("confirmation_cohort_open"):
        conf_cohort = str(t1_status.get("confirmation_cohort") or conf_cohort)
    elif conf_signals:
        asofs = sorted({str(s.get("market_bar_asof"))[:10] for s in conf_signals if s.get("market_bar_asof")})
        conf_cohort = f"CONFIRMATION_COHORT|T1_PLUS|desk_market_bar_asof={asofs[0] if asofs else 'UNKNOWN'}"
    has_confirmation_cohort = bool(
        (t1_status and t1_status.get("confirmation_cohort_open")) or len(conf_signals) > 0
    )
    if not has_confirmation_cohort:
        conf_cohort = "CONFIRMATION_COHORT|EMPTY"

    # Snapshot prior resolved counts for delta
    prev_resolved = (prev_state or {}).get("resolved") or {}
    cur_resolved = count_resolved(outcomes)
    cur_waiting = count_waiting(outcomes)
    new_resolved_outcomes = 0
    for h in HORIZONS:
        new_resolved_outcomes += max(0, cur_resolved.get(str(h), 0) - int(prev_resolved.get(str(h), 0) or 0))

    prev_signals_total = int((prev_state or {}).get("signals_total") or 0)
    if new_signals is None:
        if t1_status is not None and "NEW_SIGNAL" in t1_status:
            new_signals = int(t1_status.get("NEW_SIGNAL") or 0)
        else:
            new_signals = max(0, len(signals) - prev_signals_total)

    all_waiting = sum(cur_resolved.values()) == 0 and sum(cur_waiting.values()) > 0

    # Maturity checks (always, even when NEW_SIGNAL=0)
    maturity_checks = []
    for h in HORIZONS:
        maturity_checks.append({
            "horizon": h,
            "resolved": cur_resolved.get(str(h), 0),
            "prev_resolved": int(prev_resolved.get(str(h), 0) or 0),
            "new_resolved": max(0, cur_resolved.get(str(h), 0) - int(prev_resolved.get(str(h), 0) or 0)),
            "waiting": cur_waiting.get(str(h), 0),
            "discovery_n": sum(
                1 for s in disc_signals
                for o in outcomes
                if o.get("event_id") == s.get("event_id")
                and int(o.get("horizon_trading_days") or 0) == h
                and o.get("status") == "RESOLVED"
            ),
            "confirmation_n": sum(
                1 for s in conf_signals
                for o in outcomes
                if o.get("event_id") == s.get("event_id")
                and int(o.get("horizon_trading_days") or 0) == h
                and o.get("status") == "RESOLVED"
            ),
        })

    # Discovery candidates from T0 discovery signals only
    candidates = build_candidates(disc_signals or signals, joins, profile)
    cand_by_id = {c["candidate_id"]: c for c in candidates}

    # HARD LOCK: no new H mass-mint from T0 once a frozen set already exists
    already_frozen = sum(1 for h in existing.values() if h.get("status") == "HYPOTHESIS_FROZEN")
    allow_new_freeze = (
        already_frozen == 0
        and (
            prev_state is None
            or int(new_signals) > 0
            or int(new_resolved_outcomes) > 0
        )
    )
    to_freeze = (
        pick_freeze_targets(candidates, existing, all_waiting=all_waiting)
        if allow_new_freeze else []
    )

    evidence_rows: list[dict] = []
    new_hypotheses = 0
    extended = 0
    confirmed = 0
    rejected = 0
    unchanged = 0
    new_evidence = 0

    # Create / freeze new hypotheses
    for c in to_freeze:
        hid = c["candidate_id"]
        formula = freeze_formula(c["condition"], c["horizon_trading_days"])
        conf_status = "UNTESTED"
        hyp = {
            "schema": "DESK_HYPOTHESIS.v1",
            "hypothesis_id": hid,
            "node": NODE,
            "status": "HYPOTHESIS_FROZEN",
            "prior_status": "HYPOTHESIS_CANDIDATE",
            "confirmation_status": conf_status,
            "condition": c["condition"],
            "frozen_formula": formula,
            "horizon_trading_days": c["horizon_trading_days"],
            "features": c.get("features_used"),
            "kind_source": c["kind"],
            "creation_run": rid,
            "discovery_cohort": disc_cohort,
            "confirmation_cohort": conf_cohort,
            "discovery_stats": c["stats"],
            "confirmation_stats": {
                "n": 0, "resolved_n": 0, "waiting_n": 0,
                "mean_return": None, "mean_excess": None,
                "hit_rate": None, "excess_hit_rate": None,
                "cohort": conf_cohort,
                "sample_flag": "NO_CONFIRMATION_SAMPLES",
                "label": "CONFIRMATION_EMPTY_UNTIL_T1",
            },
            "current_stats": c["stats"],
            "discovery_n": c["stats"].get("resolved_n") or c["stats"].get("n") or 0,
            "confirmation_n": 0,
            "evaluation_clock": EVAL_CLOCK,
            "benchmark": BENCHMARK,
            "locks": {
                "DISCOVERY_NE_TRADING_RULE": True,
                "HYPOTHESIS_NE_BUY": True,
                "observed_ne_probability": True,
                "score_alignScore_ne_probability": True,
                "book_ADD_observation_only": True,
                "formula_rewrite_after_freeze": False,
                "never_confirm_on_discovery_cohort": True,
            },
            "updated_at_utc": utc_stamp(now),
        }
        existing[hid] = hyp
        frozen_formulas[hid] = dict(formula)
        new_hypotheses += 1
        ev = {
            "schema": "DESK_EVIDENCE.v1",
            "evidence_id": f"EV_{hid}_{run_stamp(now)}_FREEZE",
            "hypothesis_id": hid,
            "run_id": rid,
            "action": "FREEZE",
            "evidence_action": "DISCOVERED_AND_FROZEN",
            "new_resolved_delta": c["stats"].get("resolved_n") or 0,
            "stats": c["stats"],
            "confirmation_status": conf_status,
            "discovery_cohort": disc_cohort,
            "confirmation_cohort": conf_cohort,
            "note": (
                "Initial freeze on Desk T0 discovery cohort. confirmation_status=UNTESTED "
                "until T1+ confirmation cohort opens. Never confirm on discovery alone."
            ),
            "written_at_utc": utc_stamp(now),
        }
        evidence_rows.append(ev)
        new_evidence += 1

    # Update all existing frozen / candidate hypotheses with discovery vs confirmation stats
    asofs_disc = sorted({s.get("market_bar_asof") for s in disc_signals if s.get("market_bar_asof")})
    time_period_disc = f"{asofs_disc[0]}→+horizons" if asofs_disc else "DISCOVERY"
    asofs_conf = sorted({s.get("market_bar_asof") for s in conf_signals if s.get("market_bar_asof")})
    time_period_conf = f"{asofs_conf[0]}→+horizons" if asofs_conf else "CONFIRMATION_EMPTY"

    for hid, hyp in list(existing.items()):
        if hid in frozen_formulas:
            hyp["frozen_formula"] = dict(frozen_formulas[hid])

        # Migrate legacy WAITING/PENDING → UNTESTED when confirmation cohort still empty
        if not has_confirmation_cohort and hyp.get("confirmation_status") in ("WAITING", "PENDING", "N/A"):
            hyp["confirmation_status"] = "UNTESTED"

        cond = hyp.get("condition") or {}
        dim = cond.get("dimension") or (hyp.get("frozen_formula") or {}).get("condition_dimension")
        bucket = cond.get("bucket") or (hyp.get("frozen_formula") or {}).get("condition_bucket")
        hz = int(hyp.get("horizon_trading_days") or (hyp.get("frozen_formula") or {}).get("horizon_trading_days") or 5)

        c = cand_by_id.get(hid)
        if c is not None:
            disc_stats = c["stats"]
        elif dim and bucket is not None:
            disc_stats = compute_stats_for_condition_joins(
                disc_signals, joins,
                dimension=dim, bucket=str(bucket), horizon=hz,
                cohort_id=disc_cohort, time_period=time_period_disc,
            )
        else:
            disc_stats = hyp.get("discovery_stats") or empty_stats()

        if dim and bucket is not None and conf_signals:
            conf_stats = compute_stats_for_condition_joins(
                conf_signals, joins,
                dimension=dim, bucket=str(bucket), horizon=hz,
                cohort_id=conf_cohort, time_period=time_period_conf,
            )
        else:
            conf_stats = {
                "n": 0, "resolved_n": 0, "waiting_n": 0,
                "mean_return": None, "mean_excess": None,
                "hit_rate": None, "excess_hit_rate": None,
                "cohort": conf_cohort,
                "sample_flag": "NO_CONFIRMATION_SAMPLES",
                "label": "CONFIRMATION_EMPTY_UNTIL_T1_OR_MATURITY",
            }

        if hyp.get("discovery_stats") and hyp.get("status") == "HYPOTHESIS_FROZEN":
            hyp["discovery_stats_refresh"] = disc_stats
            frozen_disc = hyp["discovery_stats"]
        else:
            hyp["discovery_stats"] = disc_stats
            frozen_disc = disc_stats

        prev_conf_res = int((hyp.get("confirmation_stats") or {}).get("resolved_n") or 0)
        hyp["confirmation_stats"] = conf_stats
        hyp["discovery_n"] = int(frozen_disc.get("resolved_n") or frozen_disc.get("n") or 0)
        hyp["confirmation_n"] = int(conf_stats.get("resolved_n") or 0)
        hyp["current_stats"] = frozen_disc
        hyp["confirmation_cohort"] = conf_cohort

        status, conf_status, action = decide_lifecycle(
            hyp,
            discovery_stats=frozen_disc,
            confirmation_stats=conf_stats,
            has_confirmation_cohort=has_confirmation_cohort,
            prev_confirmation_resolved=prev_conf_res,
        )

        if hyp.get("creation_run") == rid and action in ("DISCOVERED", "UNCHANGED"):
            hyp["status"] = status
            hyp["confirmation_status"] = conf_status
            continue

        delta = {
            "discovery_resolved_delta": 0,
            "confirmation_resolved_delta": int(conf_stats.get("resolved_n") or 0) - prev_conf_res,
            "discovery_n": hyp["discovery_n"],
            "confirmation_n": hyp["confirmation_n"],
        }
        hyp["status"] = status
        hyp["confirmation_status"] = conf_status
        hyp["updated_at_utc"] = utc_stamp(now)
        hyp["last_evidence_action"] = action
        hyp["last_evidence_run"] = rid

        if action == "EXTEND_SAMPLE":
            extended += 1
            new_evidence += 1
            evidence_rows.append({
                "schema": "DESK_EVIDENCE.v1",
                "evidence_id": f"EV_{hid}_{run_stamp(now)}_EXT",
                "hypothesis_id": hid,
                "run_id": rid,
                "action": "EXTEND_SAMPLE",
                "evidence_action": action,
                "cohort": "confirmation",
                "delta": delta,
                "discovery_stats": frozen_disc,
                "confirmation_stats": conf_stats,
                "confirmation_status": conf_status,
                "written_at_utc": utc_stamp(now),
            })
        elif action == "CONFIRM":
            confirmed += 1
            new_evidence += 1
            evidence_rows.append({
                "schema": "DESK_EVIDENCE.v1",
                "evidence_id": f"EV_{hid}_{run_stamp(now)}_CONF",
                "hypothesis_id": hid,
                "run_id": rid,
                "action": "CONFIRM",
                "evidence_action": action,
                "cohort": "confirmation",
                "delta": delta,
                "discovery_stats": frozen_disc,
                "confirmation_stats": conf_stats,
                "confirmation_status": conf_status,
                "note": "CONFIRMED on confirmation cohort only — discovery n not mixed",
                "written_at_utc": utc_stamp(now),
            })
        elif action == "REJECT":
            rejected += 1
            new_evidence += 1
            hyp["status"] = "HYPOTHESIS_FROZEN"
            hyp["confirmation_status"] = "REJECTED"
            evidence_rows.append({
                "schema": "DESK_EVIDENCE.v1",
                "evidence_id": f"EV_{hid}_{run_stamp(now)}_REJ",
                "hypothesis_id": hid,
                "run_id": rid,
                "action": "REJECT",
                "evidence_action": action,
                "cohort": "confirmation",
                "delta": delta,
                "discovery_stats": frozen_disc,
                "confirmation_stats": conf_stats,
                "confirmation_status": "REJECTED",
                "note": "REJECTED on confirmation cohort only — discovery n not mixed",
                "written_at_utc": utc_stamp(now),
            })
        else:
            unchanged += 1

    # Persist hypotheses (snapshot rewrite; formulas immutable per id — never rewrite formula)
    hyp_list = sorted(existing.values(), key=lambda h: h["hypothesis_id"])
    for h in hyp_list:
        fid = h["hypothesis_id"]
        if fid in frozen_formulas:
            h["frozen_formula"] = dict(frozen_formulas[fid])
    write_jsonl(hyp_path, hyp_list)
    if evidence_rows:
        append_jsonl(evidence_path, evidence_rows)

    live, replay = count_live_replay(signals)
    hyp_counts = {
        "total": len(hyp_list),
        "candidates": sum(1 for h in hyp_list if h.get("status") == "HYPOTHESIS_CANDIDATE"),
        "frozen": sum(1 for h in hyp_list if h.get("status") == "HYPOTHESIS_FROZEN"),
        "active": sum(
            1 for h in hyp_list
            if h.get("status") == "HYPOTHESIS_FROZEN"
            and h.get("confirmation_status") in ("UNTESTED", "PENDING", "CONFIRMED")
        ),
        "untested": sum(1 for h in hyp_list if h.get("confirmation_status") == "UNTESTED"),
        "pending": sum(1 for h in hyp_list if h.get("confirmation_status") == "PENDING"),
        "confirmed": sum(1 for h in hyp_list if h.get("confirmation_status") == "CONFIRMED"),
        "rejected": sum(1 for h in hyp_list if h.get("confirmation_status") == "REJECTED"),
    }

    # Keep leftover candidates as reportable (not frozen) — write separate snapshot count
    unfrozen_candidates = [
        c for c in candidates
        if c["candidate_id"] not in existing and c["stats"]["n"] > 0
    ]

    run_summary = {
        "new_signals": int(new_signals),
        "new_resolved_outcomes": int(new_resolved_outcomes),
        "new_evidence": int(new_evidence),
        "new_hypotheses": int(new_hypotheses),
        "extended_hypotheses": int(extended),
        "confirmed": int(confirmed),
        "rejected": int(rejected),
        "unchanged": int(unchanged),
        "untested": hyp_counts["untested"],
        "pending": hyp_counts["pending"],
        "discovery_candidates_scanned": len(candidates),
        "unfrozen_candidates_remaining": len(unfrozen_candidates),
        "waiting_freeze": bool(all_waiting and new_hypotheses > 0),
        "T1_STATUS": (t1_status or {}).get("T1_STATUS"),
        "t1_status_label": (t1_status or {}).get("T1_STATUS"),
        "confirmation_cohort_open": has_confirmation_cohort,
    }
    kd_none = (
        run_summary["new_signals"] == 0
        and run_summary["new_evidence"] == 0
        and run_summary["new_hypotheses"] == 0
        and run_summary["confirmed"] == 0
        and run_summary["rejected"] == 0
        and run_summary["extended_hypotheses"] == 0
    )
    run_summary["KNOWLEDGE_DELTA"] = "NONE" if kd_none else "UPDATED"

    # T0 integrity
    t0_ok = (
        t0_ev_sha == sha256_file(ev_path)
        and t0_oc_sha == sha256_file(oc_path)
    )

    mem_ok = (mem / "signal_memory.jsonl").exists() and (mem / "signal_outcome_join.jsonl").exists()
    mem_report_ok = (mem / "REPORT_RESEARCH_MEMORY.html").exists()

    new_state = {
        "schema": "DESK_RESEARCH_STATE.v1",
        "node": NODE,
        "hub": "信股慣性台",
        "version": VERSION,
        "profile_version": profile.get("profile_version") or PROFILE_VERSION,
        "signals_total": len(signals),
        "signals_live": live,
        "signals_replay": replay,
        "joins_total": len(joins),
        "resolved": {
            "5": cur_resolved.get("5", 0),
            "21": cur_resolved.get("21", 0),
            "63": cur_resolved.get("63", 0),
            "126": cur_resolved.get("126", 0),
            "252": cur_resolved.get("252", 0),
        },
        "waiting": {
            "5": cur_waiting.get("5", 0),
            "21": cur_waiting.get("21", 0),
            "63": cur_waiting.get("63", 0),
            "126": cur_waiting.get("126", 0),
            "252": cur_waiting.get("252", 0),
        },
        "resolved_5d": cur_resolved.get("5", 0),
        "resolved_21d": cur_resolved.get("21", 0),
        "resolved_63d": cur_resolved.get("63", 0),
        "resolved_126d": cur_resolved.get("126", 0),
        "resolved_252d": cur_resolved.get("252", 0),
        "hypotheses_total": hyp_counts["total"],
        "hypotheses_candidates": hyp_counts["candidates"],
        "hypotheses_frozen": hyp_counts["frozen"],
        "hypotheses_active": hyp_counts["active"],
        "hypotheses_untested": hyp_counts["untested"],
        "hypotheses_pending": hyp_counts["pending"],
        "hypotheses_confirmed": hyp_counts["confirmed"],
        "hypotheses_rejected": hyp_counts["rejected"],
        "discovery_signals_n": len(disc_signals),
        "confirmation_signals_n": len(conf_signals),
        "confirmation_cohort_open": has_confirmation_cohort,
        "KNOWLEDGE_DELTA": run_summary["KNOWLEDGE_DELTA"],
        "T1_STATUS": (t1_status or {}).get("T1_STATUS"),
        "last_discovery_run": rid,
        "last_evidence_update": utc_stamp(now),
        "discovery_cohort": disc_cohort,
        "confirmation_cohort": conf_cohort,
        "evaluation_clock": EVAL_CLOCK,
        "benchmark": BENCHMARK,
        "execution_policy": "book_ADD => BOOK_ACTION / OBSERVATION; MARK_BUY=0 unless engine-emitted",
        "locks": {
            "DISCOVERY_NE_TRADING_RULE": True,
            "HYPOTHESIS_NE_BUY": True,
            "book_ADD_observation_only": True,
            "T0_untouched": True,
            "no_LIVE_REPLAY_mix": replay == 0,
            "engine_untouched": True,
            "never_confirm_on_discovery_cohort": True,
            "score_alignScore_ne_probability": True,
            "discovery_n_ne_confirmed": True,
            "no_new_H_from_T0_once_frozen": True,
            "confirmation_status_enum": "UNTESTED|PENDING|CONFIRMED|REJECTED",
        },
        "memory_paths_preserved": [
            "research_profile.json",
            "research_memory/signal_memory.jsonl",
            "research_memory/signal_outcome_join.jsonl",
            "research_memory/conditional_analysis/",
            "research_memory/REPORT_RESEARCH_MEMORY.html",
            "run_history/",
        ],
        "memory_intact": mem_ok and mem_report_ok,
        "evolution_path": "research/forward_v1/desk/research_evolution/",
        "t0_integrity": "PASS" if t0_ok else "FAIL",
        "t0_events_sha256": t0_ev_sha,
        "t0_outcomes_sha256": t0_oc_sha,
        "updated_at_utc": utc_stamp(now),
    }

    progress = research_progress(prev_state, new_state, run_summary)
    new_state["research_progress"] = progress
    write_json(state_path, new_state)

    top = top_relationships(hyp_list)
    example = None
    if top:
        example = next((h for h in hyp_list if h["hypothesis_id"] == top[0]["hypothesis_id"]), None)
    elif hyp_list:
        example = hyp_list[0]

    discovery_run = {
        "schema": "DESK_DISCOVERY_RUN.v1",
        "run_id": rid,
        "node": NODE,
        "hub": "信股慣性台",
        "version": VERSION,
        "written_at_utc": utc_stamp(now),
        "evaluation_clock": EVAL_CLOCK,
        "benchmark": BENCHMARK,
        "new_signals": run_summary["new_signals"],
        "new_resolved_outcomes": run_summary["new_resolved_outcomes"],
        "new_evidence": run_summary["new_evidence"],
        "new_hypotheses": run_summary["new_hypotheses"],
        "extended_hypotheses": run_summary["extended_hypotheses"],
        "confirmed": run_summary["confirmed"],
        "rejected": run_summary["rejected"],
        "unchanged": run_summary["unchanged"],
        "untested": run_summary["untested"],
        "pending": run_summary["pending"],
        "KNOWLEDGE_DELTA": run_summary["KNOWLEDGE_DELTA"],
        "T1_STATUS": run_summary.get("T1_STATUS"),
        "maturity_checks": maturity_checks,
        "discovery_cohort": disc_cohort,
        "confirmation_cohort": conf_cohort,
        "confirmation_cohort_open": has_confirmation_cohort,
        "top_research_relationships": top,
        "example_hypothesis_id": (example or {}).get("hypothesis_id"),
        "example_hypothesis": {
            "hypothesis_id": (example or {}).get("hypothesis_id"),
            "condition": (example or {}).get("condition"),
            "horizon": (example or {}).get("horizon_trading_days"),
            "discovery_stats": (example or {}).get("discovery_stats"),
            "confirmation_stats": (example or {}).get("confirmation_stats"),
            "current_stats": (example or {}).get("current_stats"),
            "discovery_n": (example or {}).get("discovery_n"),
            "confirmation_n": (example or {}).get("confirmation_n"),
            "status": (example or {}).get("status"),
            "confirmation_status": (example or {}).get("confirmation_status"),
            "discovery_cohort": (example or {}).get("discovery_cohort"),
            "confirmation_cohort": (example or {}).get("confirmation_cohort"),
            "frozen_formula": (example or {}).get("frozen_formula"),
        } if example else None,
        "research_progress": progress,
        "hypothesis_counts": hyp_counts,
        "discovery_candidates_scanned": len(candidates),
        "declared_buckets_retained": True,
        "waiting_dimension_freeze": bool(all_waiting),
        "t0_integrity": "PASS" if t0_ok else "FAIL",
        "memory_status_ref": {
            "signal_memory_rows": (memory_status or {}).get("signal_memory_total", len(signals)),
            "joins": (memory_status or {}).get("joins", len(joins)),
            "outcome_slots_waiting": (memory_status or {}).get("outcome_slots_waiting"),
            "outcome_slots_resolved": (memory_status or {}).get("outcome_slots_resolved"),
            "t0_integrity": (memory_status or {}).get("t0_integrity"),
        },
        "locks": new_state["locks"],
        "note": (
            "NEW_SIGNAL=0 is expected while market_bar_asof stuck at T0; "
            "WAITING freezes still advance knowledge (hypothesis lifecycle). "
            "DISCOVERY≠BUY. observed≠probability. NEVER confirm on discovery cohort."
        ),
    }
    run_path = evo / f"DISCOVERY_RUN_{rid.replace('FORWARD_RUN_', '').replace('EVO_', '')}.json"
    # normalize filename
    safe = rid
    if safe.startswith("FORWARD_RUN_"):
        safe = safe[len("FORWARD_RUN_"):]
    if safe.startswith("EVO_"):
        safe = safe[len("EVO_"):]
    run_path = evo / f"DISCOVERY_RUN_{safe}.json"
    write_json(run_path, discovery_run)

    # README for evolution tree
    readme = evo / "README.md"
    readme.write_text(
        """# Desk（信股慣性台）RESEARCH EVOLUTION V1

Learning layer on RESEARCH MEMORY V1. Does **not** replace memory artifacts.

## Files
- `RESEARCH_STATE.json` — node counts, resolved/waiting horizons, hypothesis lifecycle
- `HYPOTHESES.jsonl` — frozen hypotheses (formula immutable after freeze)
- `EVIDENCE_LOG.jsonl` — append-only evidence actions
- `DISCOVERY_RUN_*.json` — per forward-run discovery/evidence deltas
- `REPORT_RESEARCH_EVOLUTION.html` — interactive panel

## Locks
- DISCOVERY ≠ TRADING RULE
- HYPOTHESIS ≠ BUY
- observed ≠ probability; score/alignScore ≠ probability
- book_ADD = OBSERVATION only; never upgrade → MARK_BUY
- T0 untouched; LIVE ≠ REPLAY mix
- Discovery cohort (T0 market_bar_asof) ≠ confirmation cohort (T1+ ONLY / EMPTY until genuine T1)
- confirmation_status ∈ UNTESTED|PENDING|CONFIRMED|REJECTED
- discovery_n never mixed into confirmed; never rewrite H formula after freeze
- No new H mass-mint from T0 once frozen set exists (T1 stage → new_hypotheses=0)
"""
    )

    # Final T0 check after writes
    t0_ok2 = t0_ev_sha == sha256_file(ev_path) and t0_oc_sha == sha256_file(oc_path)

    status = {
        "schema": "DESK_RESEARCH_EVOLUTION_STATUS.v1",
        "status": "OK",
        "node": NODE,
        "version": VERSION,
        "run_id": rid,
        "evolution_path": "research/forward_v1/desk/research_evolution/",
        "research_state": new_state,
        "hypothesis_counts": hyp_counts,
        "evidence_log_rows_appended": len(evidence_rows),
        "evidence_log_rows_total": len(load_jsonl(evidence_path)),
        "discovery_run_path": str(run_path.relative_to(repo)),
        "discovery_run": {
            "new_signals": discovery_run["new_signals"],
            "new_resolved_outcomes": discovery_run["new_resolved_outcomes"],
            "new_evidence": discovery_run["new_evidence"],
            "new_hypotheses": discovery_run["new_hypotheses"],
            "extended_hypotheses": discovery_run["extended_hypotheses"],
            "confirmed": discovery_run["confirmed"],
            "rejected": discovery_run["rejected"],
            "unchanged": discovery_run["unchanged"],
            "untested": discovery_run["untested"],
            "pending": discovery_run["pending"],
            "KNOWLEDGE_DELTA": discovery_run["KNOWLEDGE_DELTA"],
            "T1_STATUS": discovery_run.get("T1_STATUS"),
            "confirmation_cohort": discovery_run.get("confirmation_cohort"),
            "confirmation_cohort_open": discovery_run.get("confirmation_cohort_open"),
            "example_hypothesis_id": discovery_run["example_hypothesis_id"],
            "top_research_relationships": top,
            "maturity_checks": maturity_checks,
            "research_progress": progress,
        },
        "example_hypothesis": discovery_run["example_hypothesis"],
        "research_progress": progress,
        "t0_integrity": "PASS" if (t0_ok and t0_ok2) else "FAIL",
        "locks": new_state["locks"],
        "report": "research/forward_v1/desk/research_evolution/REPORT_RESEARCH_EVOLUTION.html",
        "updated_at_utc": utc_stamp(now),
    }
    status["discovery_run"]["waiting_dimension_freeze"] = discovery_run.get("waiting_dimension_freeze")
    write_json(evo / "RESEARCH_EVOLUTION_STATUS.json", status)
    _write_evolution_html(evo / "REPORT_RESEARCH_EVOLUTION.html", status, discovery_run, new_state)
    return status


def main() -> None:
    ap = argparse.ArgumentParser(description="Desk RESEARCH EVOLUTION V1 + T1 CONFIRM")
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    ap.add_argument("--run-id", type=str, default=None)
    ap.add_argument("--new-signals", type=int, default=None)
    ap.add_argument("--t1-status-json", type=Path, default=None,
                    help="Optional path to T1_CAPTURE_STATUS.json")
    args = ap.parse_args()
    t1 = None
    if args.t1_status_json and args.t1_status_json.exists():
        t1 = load_json(args.t1_status_json)
    else:
        default_t1 = args.repo_root.resolve() / "research/forward_v1/desk/status/T1_CAPTURE_STATUS.json"
        if default_t1.exists():
            t1 = load_json(default_t1)
    status = run_research_evolution(
        args.repo_root.resolve(),
        run_id=args.run_id,
        new_signals=args.new_signals,
        t1_status=t1,
    )
    print(json.dumps({
        "status": status["status"],
        "run_id": status["run_id"],
        "new_signals": status["discovery_run"]["new_signals"],
        "new_evidence": status["discovery_run"]["new_evidence"],
        "new_hypotheses": status["discovery_run"]["new_hypotheses"],
        "unchanged": status["discovery_run"]["unchanged"],
        "KNOWLEDGE_DELTA": status["discovery_run"].get("KNOWLEDGE_DELTA"),
        "T1_STATUS": status["discovery_run"].get("T1_STATUS"),
        "hypothesis_counts": status["hypothesis_counts"],
        "t0_integrity": status["t0_integrity"],
        "example_hypothesis_id": status["discovery_run"]["example_hypothesis_id"],
        "waiting_dimension_freeze": status["discovery_run"].get("waiting_dimension_freeze"),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
