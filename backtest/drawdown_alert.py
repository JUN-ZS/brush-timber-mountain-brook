"""Drawdown alert — separate from return optimization.

Scores how much the recent QQQ path looks like historical stress windows.
Prefers Data Factory DD_EPISODES feature cache when present.
Does NOT search for annualized profit. Similarity is not a trade signal by itself.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Optional

DAYS = 252

# Pinned Data Factory contract (QQQ VXX 年化)
PINNED_PACK_HASH = "7ca13ce290d28db4"
PINNED_FEATURE_HASH = "e804cdb1f491b4d6"
PINNED_ALGORITHM = "dd_episodes.v1"
DEFAULT_FEATURE_REL = Path("data/features/DD_EPISODES") / f"dd_episodes.v1_{PINNED_PACK_HASH}" / "dd_episodes.json"


def _rets(prices: list[float]) -> list[float]:
    out = []
    for i in range(1, len(prices)):
        if prices[i - 1] > 0 and prices[i] > 0:
            out.append(prices[i] / prices[i - 1] - 1.0)
    return out


def path_features(prices: list[float], vix: Optional[list[float]] = None, window: int = 60) -> Optional[dict[str, Any]]:
    if len(prices) < window + 1:
        return None
    sl = prices[-(window + 1) :]
    rets = _rets(sl)
    if len(rets) < 10:
        return None
    peak = sl[0]
    path_dd = 0.0
    for p in sl:
        peak = max(peak, p)
        path_dd = min(path_dd, p / peak - 1.0)
    m = sum(rets) / len(rets)
    vol = math.sqrt(sum((r - m) ** 2 for r in rets) / len(rets)) * math.sqrt(DAYS)
    mom20 = sl[-1] / sl[-21] - 1.0 if len(sl) > 21 and sl[-21] > 0 else 0.0
    vix_lvl = None
    if vix:
        vv = [x for x in vix[-window:] if isinstance(x, (int, float)) and x == x]
        vix_lvl = vv[-1] if vv else None
    return {
        "rets": rets,
        "vol": vol,
        "mom20": mom20,
        "path_dd": path_dd,
        "vix": vix_lvl,
        "window": window,
    }


def corr(a: list[float], b: list[float]) -> float:
    n = min(len(a), len(b))
    if n < 10:
        return 0.0
    a, b = a[-n:], b[-n:]
    ma, mb = sum(a) / n, sum(b) / n
    num = sum((a[i] - ma) * (b[i] - mb) for i in range(n))
    da = math.sqrt(sum((x - ma) ** 2 for x in a))
    db = math.sqrt(sum((x - mb) ** 2 for x in b))
    if da < 1e-12 or db < 1e-12:
        return 0.0
    return num / (da * db)


def similarity(cur: dict[str, Any], hist: dict[str, Any]) -> dict[str, float]:
    c = corr(cur["rets"], hist["rets"])
    parts = [max(0.0, c)]
    parts.append(max(0.0, 1 - abs(cur["vol"] - hist["vol"]) / max(cur["vol"], hist["vol"], 1e-6)))
    parts.append(max(0.0, 1 - abs(cur["mom20"] - hist["mom20"]) / 0.15))
    parts.append(max(0.0, 1 - abs(cur["path_dd"] - hist["path_dd"]) / max(abs(hist["path_dd"]), 0.05)))
    score = 100.0 * sum(parts) / len(parts)
    alert = 100.0 * (
        0.55 * max(0.0, c)
        + 0.45 * max(0.0, 1 - abs(cur["path_dd"] - hist["path_dd"]) / max(abs(hist["path_dd"]), 0.05))
    )
    return {"feature_score": score, "alert_score": alert, "path_corr": c}


def find_drawdown_episodes(dates: list[str], prices: list[float], *, min_dd: float = -0.05) -> list[dict[str, Any]]:
    """Fallback scanner when DD_EPISODES cache is absent."""
    episodes: list[dict[str, Any]] = []
    i = 0
    n = len(prices)
    while i < n:
        while i + 1 < n and prices[i + 1] >= prices[i]:
            i += 1
        peak_i, peak = i, prices[i]
        j = i + 1
        trough_i, trough = i, peak
        recovered = False
        while j < n:
            if prices[j] < trough:
                trough, trough_i = prices[j], j
            if prices[j] >= peak and trough_i > peak_i:
                recovered = True
                break
            j += 1
        if trough_i > peak_i:
            dd = trough / peak - 1.0
            if dd <= min_dd:
                episodes.append(
                    {
                        "peak_date": dates[peak_i],
                        "trough_date": dates[trough_i],
                        "peak_i": peak_i,
                        "trough_i": trough_i,
                        "dd": dd,
                        "days": trough_i - peak_i,
                        "recover_date": dates[j] if recovered and j < n else None,
                    }
                )
        i = max(trough_i, i) + 1
    episodes.sort(key=lambda e: e["dd"])
    return episodes


def resolve_feature_path(explicit: Optional[Path] = None, repo_root: Optional[Path] = None) -> Optional[Path]:
    candidates: list[Path] = []
    if explicit is not None:
        candidates.append(Path(explicit))
    root = repo_root or Path(__file__).resolve().parents[1]
    candidates.append(root / DEFAULT_FEATURE_REL)
    # Box Data Factory layout (shared machine)
    candidates.append(
        Path("/workspace/tango-shadow-bay-apple/DATA/features/DD_EPISODES")
        / f"dd_episodes.v1_{PINNED_PACK_HASH}"
        / "dd_episodes.json"
    )
    for p in candidates:
        if p.is_file():
            return p
    return None


def load_dd_episodes(
    path: Optional[Path] = None,
    *,
    symbol: str = "QQQ",
    repo_root: Optional[Path] = None,
    expect_pack_hash: str = PINNED_PACK_HASH,
) -> tuple[Optional[list[dict[str, Any]]], dict[str, Any]]:
    """Load factory DD_EPISODES. Returns (episodes_or_None, meta)."""
    meta: dict[str, Any] = {
        "source": "NOT_PRESENT",
        "path": None,
        "feature_hash": None,
        "manifest_hash": None,
        "algorithm_version": None,
        "symbol": symbol,
    }
    p = resolve_feature_path(path, repo_root)
    if p is None:
        return None, meta
    doc = json.loads(Path(p).read_text(encoding="utf-8"))
    meta.update(
        {
            "source": "DD_EPISODES_CACHE",
            "path": str(p),
            "feature_hash": doc.get("feature_hash"),
            "manifest_hash": doc.get("manifest_hash"),
            "algorithm_version": doc.get("algorithm_version"),
            "pack_id": doc.get("pack_id"),
            "data_asof": doc.get("data_asof"),
        }
    )
    if expect_pack_hash and doc.get("manifest_hash") and doc.get("manifest_hash") != expect_pack_hash:
        meta["source"] = "HASH_MISMATCH"
        meta["expected_manifest_hash"] = expect_pack_hash
        return None, meta
    sym = (doc.get("symbols") or {}).get(symbol)
    if not sym:
        meta["source"] = "SYMBOL_MISSING"
        return None, meta
    eps = list(sym.get("episodes") or [])
    meta["n_episodes"] = len(eps)
    meta["history_first_date"] = sym.get("history_first_date")
    meta["history_last_date"] = sym.get("history_last_date")
    return eps, meta


def index_episodes(dates: list[str], episodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach peak_i / trough_i using the price calendar."""
    idx = {d: i for i, d in enumerate(dates)}
    out: list[dict[str, Any]] = []
    for e in episodes:
        pi = idx.get(e.get("peak_date"))
        ti = idx.get(e.get("trough_date"))
        if pi is None or ti is None:
            continue
        row = dict(e)
        row["peak_i"] = pi
        row["trough_i"] = ti
        out.append(row)
    out.sort(key=lambda x: x["dd"])
    return out


def alert_report(
    dates: list[str],
    prices: list[float],
    vix: Optional[list[float]] = None,
    *,
    top_n: int = 8,
    window: int = 60,
    symbol: str = "QQQ",
    dd_episodes_path: Optional[Path] = None,
    repo_root: Optional[Path] = None,
    prefer_cache: bool = True,
) -> dict[str, Any]:
    """Return drawdown-alert payload. Never invents CAGR / annualized profit."""
    cache_meta: dict[str, Any] = {"source": "SCANNER_FALLBACK"}
    episodes: list[dict[str, Any]] = []
    if prefer_cache:
        raw, cache_meta = load_dd_episodes(dd_episodes_path, symbol=symbol, repo_root=repo_root)
        if raw is not None:
            episodes = index_episodes(dates, raw)
            if not episodes:
                cache_meta = {**cache_meta, "source": "CACHE_INDEX_MISS"}
    if not episodes:
        episodes = find_drawdown_episodes(dates, prices)
        if cache_meta.get("source") not in {"DD_EPISODES_CACHE"}:
            cache_meta = {**cache_meta, "source": "SCANNER_FALLBACK", "n_episodes": len(episodes)}

    worst = episodes[:top_n]
    cur = path_features(prices, vix, window=window)
    finite_prices = [(i, p) for i, p in enumerate(prices) if isinstance(p, (int, float)) and p == p and p > 0]
    if finite_prices:
        peak_i, peak = max(finite_prices, key=lambda t: t[1])
        cur_dd = prices[-1] / peak - 1.0 if prices[-1] == prices[-1] and prices[-1] > 0 else 0.0
        ath_date = dates[peak_i] if peak_i < len(dates) else None
    else:
        peak_i, peak, cur_dd, ath_date = 0, None, None, None

    crash_sims: list[dict[str, Any]] = []
    pre_sims: list[dict[str, Any]] = []
    if cur:
        for e in worst:
            ti = e.get("trough_i")
            pi = e.get("peak_i")
            if isinstance(ti, int) and ti >= window + 1:
                hist = path_features(prices[: ti + 1], (vix or [])[: ti + 1] if vix else None, window)
                if hist:
                    s = similarity(cur, hist)
                    crash_sims.append({**s, **{k: e.get(k) for k in ("peak_date", "trough_date", "dd", "days", "recover_date")}})
            if isinstance(pi, int) and pi >= window + 1:
                hist = path_features(prices[: pi + 1], (vix or [])[: pi + 1] if vix else None, window)
                if hist:
                    s = similarity(cur, hist)
                    pre_sims.append({**s, **{k: e.get(k) for k in ("peak_date", "trough_date", "dd", "days", "recover_date")}})
    crash_sims.sort(key=lambda x: x["alert_score"], reverse=True)
    pre_sims.sort(key=lambda x: x["alert_score"], reverse=True)
    best_crash = crash_sims[0] if crash_sims else None
    best_pre = pre_sims[0] if pre_sims else None
    looks_like_max_dd = bool(
        best_crash
        and cur
        and cur["path_dd"] <= -0.12
        and best_crash["path_corr"] >= 0.25
        and best_crash["alert_score"] >= 45
    )
    return {
        "module": "drawdown_alert",
        "purpose": "stress similarity only — not annualized return search",
        "asof": dates[-1] if dates else None,
        "symbol": symbol,
        "episodes_source": cache_meta,
        "current_dd_from_ath": cur_dd,
        "current_features": {k: v for k, v in (cur or {}).items() if k != "rets"},
        "looks_like_historical_max_dd": looks_like_max_dd,
        "best_crash_match": best_crash,
        "best_precrash_match": best_pre,
        "top_crash_matches": crash_sims[:5],
        "top_precrash_matches": pre_sims[:5],
        "worst_episodes": [{k: e.get(k) for k in ("peak_date", "trough_date", "dd", "days", "recover_date")} for e in worst[:8]],
        "ath_date": ath_date,
        "ath_price": peak,
    }
