#!/usr/bin/env python3
"""Public-price-only supplement for the QQQ option-chain data gap.

Fetches Yahoo Finance daily QQQ closes and FRED/Cboe VIXCLS observations. This
can extend underlying-price path probabilities beyond the option mirror's last
date; it does NOT estimate or claim actual option-strategy P&L for missing dates.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

HORIZONS = (1, 3, 5, 10, 20, 30, 45)
SOURCE_END = date(2025, 12, 15)
YAHOO_CHART = "https://query1.finance.yahoo.com/v8/finance/chart/QQQ"
YAHOO_VIX_CHART = "https://query1.finance.yahoo.com/v8/finance/chart/%5EVIX"
YAHOO_VXN_CHART = "https://query1.finance.yahoo.com/v8/finance/chart/%5EVXN"
FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS"
USER_AGENT = "Mozilla/5.0 (compatible; QQQResearchSupplement/1.0)"


def fetch_text(url: str, timeout: int = 30) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def validate_close(value: Any, session_date: date) -> float:
    if value is None:
        raise RuntimeError(f"Yahoo chart returned a missing/invalid close for dated bar {session_date.isoformat()}; refusing to bridge the gap.")
    try:
        close = float(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"Yahoo chart returned a non-numeric close for {session_date.isoformat()}.") from exc
    if not math.isfinite(close) or close <= 0:
        raise RuntimeError(f"Yahoo chart returned a missing/invalid close for dated bar {session_date.isoformat()}; refusing to bridge the gap.")
    return round(close, 6)


def fetch_qqq(start: date, end: date) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    params = {
        "period1": int(datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc).timestamp()),
        "period2": int(datetime.combine(end + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc).timestamp()),
        "interval": "1d",
        "events": "history",
        "includeAdjustedClose": "true",
    }
    url = YAHOO_CHART + "?" + urlencode(params)
    last_error: Exception | None = None
    payload = None
    for attempt in range(3):
        try:
            payload = json.loads(fetch_text(url))
            break
        except Exception as exc:  # network/provider failures are reported, not silently replaced
            last_error = exc
            if attempt < 2:
                time.sleep(1.5 * (attempt + 1))
    if payload is None:
        raise RuntimeError(f"Yahoo QQQ daily history unavailable: {last_error}")
    chart = payload.get("chart") or {}
    if chart.get("error"):
        raise RuntimeError(f"Yahoo chart API error: {chart['error']}")
    results = chart.get("result") or []
    if not results:
        raise RuntimeError("Yahoo chart API returned no QQQ data.")
    item = results[0]
    timestamps = item.get("timestamp") or []
    quotes = ((item.get("indicators") or {}).get("quote") or [{}])[0]
    closes = quotes.get("close") or []
    adj = ((item.get("indicators") or {}).get("adjclose") or [{}])[0].get("adjclose") or []
    rows = []
    for i, ts in enumerate(timestamps):
        d = datetime.fromtimestamp(int(ts), tz=timezone.utc).date()
        if d < start or d > end:
            continue
        close = closes[i] if i < len(closes) else None
        adj_close = adj[i] if i < len(adj) else None
        clean_close = validate_close(close, d)
        rows.append({
            "date": d.isoformat(),
            "raw_close": clean_close,
            "adj_close": round(float(adj_close), 6) if adj_close is not None else None,
            "vix": None,
            "price_source": "Yahoo Finance chart API",
        })
    rows.sort(key=lambda x: x["date"])
    if not rows:
        raise RuntimeError("Yahoo QQQ history contains no valid daily closes in the requested range.")
    dates = [x["date"] for x in rows]
    if dates != sorted(set(dates)):
        raise RuntimeError("Yahoo QQQ dates are not unique and ascending.")
    return rows, {
        "source": "Yahoo Finance chart API",
        "url": url,
        "returned_rows": len(rows),
        "first_date": rows[0]["date"],
        "last_date": rows[-1]["date"],
        "raw_close_definition": "Unadjusted daily Close returned by the provider; adjusted close retained separately for audit only.",
    }


def parse_yahoo_vix_payload(payload: dict[str, Any], start: date, end: date) -> tuple[dict[str, float], dict[str, Any]]:
    chart = payload.get("chart") or {}
    if chart.get("error"):
        raise RuntimeError(f"Yahoo ^VIX chart API error: {chart['error']}")
    results = chart.get("result") or []
    if not results:
        raise RuntimeError("Yahoo ^VIX chart API returned no observations.")
    item = results[0]
    timestamps = item.get("timestamp") or []
    quotes = ((item.get("indicators") or {}).get("quote") or [{}])[0]
    closes = quotes.get("close") or []
    values: dict[str, float] = {}
    for i, ts in enumerate(timestamps):
        d = datetime.fromtimestamp(int(ts), tz=timezone.utc).date()
        if d < start or d > end:
            continue
        raw = closes[i] if i < len(closes) else None
        # A missing VIX observation stays missing; we never forward-fill a volatility value.
        if raw is None:
            continue
        try:
            val = float(raw)
        except (TypeError, ValueError):
            continue
        if math.isfinite(val) and val > 0:
            values[d.isoformat()] = val
    if not values:
        raise RuntimeError("Yahoo ^VIX chart API contained no valid daily Close observations.")
    return values, {
        "source": "Yahoo Finance chart API ^VIX daily Close",
        "url": YAHOO_VIX_CHART,
        "observations": len(values),
        "first_date": min(values),
        "last_date": max(values),
        "note": "Broad S&P 500 implied volatility proxy only; not QQQ IV or QQQ put skew. Missing days are not forward-filled."
    }


def fetch_yahoo_vix(start: date, end: date) -> tuple[dict[str, float], dict[str, Any]]:
    params = {
        "period1": int(datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc).timestamp()),
        "period2": int(datetime.combine(end + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc).timestamp()),
        "interval": "1d",
        "events": "history"
    }
    url = YAHOO_VIX_CHART + "?" + urlencode(params)
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            payload = json.loads(fetch_text(url, timeout=20))
            values, meta = parse_yahoo_vix_payload(payload, start, end)
            meta["url"] = url
            return values, meta
        except Exception as exc:
            last_error = exc
            if attempt < 1:
                time.sleep(1.0)
    raise RuntimeError(f"Yahoo ^VIX daily history unavailable: {last_error}")


def fetch_vix(start: date, end: date) -> tuple[dict[str, float], dict[str, Any]]:
    last_error: Exception | None = None
    text = None
    # FRED can stall on a multi-year CSV. Bound retries, then use Yahoo ^VIX as a
    # clearly labeled broad-market proxy; never imply this is QQQ option IV/skew.
    for attempt in range(2):
        try:
            text = fetch_text(FRED_CSV, timeout=8)
            break
        except Exception as exc:
            last_error = exc
            if attempt < 1:
                time.sleep(0.75)
    if text is not None:
        reader = csv.DictReader(text.splitlines())
        vix: dict[str, float] = {}
        for row in reader:
            d = row.get("observation_date") or row.get("DATE") or row.get("date")
            value = row.get("VIXCLS") or row.get("value")
            if not d or not value or value.strip() in (".", ""):
                continue
            try:
                val = float(value)
            except ValueError:
                continue
            if math.isfinite(val) and val > 0:
                vix[d[:10]] = val
        if vix:
            return vix, {
                "source": "FRED VIXCLS daily series (Cboe VIX close)",
                "url": FRED_CSV,
                "observations": len(vix),
                "first_date": min(vix),
                "last_date": max(vix),
                "fallback_used": False,
                "note": "VIX is a broad U.S. equity implied-volatility proxy, not QQQ option implied volatility or QQQ put skew.",
            }
        last_error = RuntimeError("FRED CSV returned no valid VIXCLS observations.")
    fred_error = str(last_error or "FRED VIXCLS unavailable.")
    yahoo_values, yahoo_meta = fetch_yahoo_vix(start, end)
    yahoo_meta["fallback_used"] = True
    yahoo_meta["primary_source_error"] = fred_error
    return yahoo_values, yahoo_meta


def rv_buckets(rows: list[dict[str, Any]]) -> list[float | None]:
    closes = [float(x["raw_close"]) for x in rows]
    logs: list[float | None] = [None] * len(closes)
    for i in range(1, len(closes)):
        logs[i] = math.log(closes[i] / closes[i - 1])
    rv: list[float | None] = [None] * len(closes)
    for i in range(20, len(closes)):
        sample = logs[i - 19:i + 1]
        if len(sample) == 20 and all(x is not None for x in sample):
            rv[i] = statistics.stdev([float(x) for x in sample]) * math.sqrt(252)
    return rv


def rv_label(value: float | None) -> str | None:
    if value is None:
        return None
    if value < .15:
        return "RV20_LT15"
    if value < .25:
        return "RV20_15_25"
    if value < .35:
        return "RV20_25_35"
    return "RV20_GTE35"


def vix_label(value: float | None) -> str | None:
    if value is None:
        return None
    if value < 15:
        return "VIX_LT15"
    if value < 25:
        return "VIX_15_25"
    if value < 35:
        return "VIX_25_35"
    return "VIX_GTE35"


def vxn_label(value: float | None) -> str | None:
    if value is None:
        return None
    # VXN usually runs at a different level from VIX; use separately named buckets.
    if value < 20:
        return "VXN_LT20"
    if value < 30:
        return "VXN_20_30"
    if value < 40:
        return "VXN_30_40"
    return "VXN_GTE40"



def parse_yahoo_vxn_payload(payload: dict[str, Any], start: date, end: date) -> tuple[dict[str, float], dict[str, Any]]:
    chart = payload.get("chart") or {}
    if chart.get("error"):
        raise RuntimeError(f"Yahoo ^VXN chart API error: {chart['error']}")
    results = chart.get("result") or []
    if not results:
        raise RuntimeError("Yahoo ^VXN chart API returned no observations.")
    item = results[0]
    timestamps = item.get("timestamp") or []
    quotes = ((item.get("indicators") or {}).get("quote") or [{}])[0]
    closes = quotes.get("close") or []
    values: dict[str, float] = {}
    for i, ts in enumerate(timestamps):
        d = datetime.fromtimestamp(int(ts), tz=timezone.utc).date()
        if d < start or d > end:
            continue
        raw = closes[i] if i < len(closes) else None
        # Missing VXN observations stay missing; never forward-fill an implied-volatility proxy.
        if raw is None:
            continue
        try:
            val = float(raw)
        except (TypeError, ValueError):
            continue
        if math.isfinite(val) and val > 0:
            values[d.isoformat()] = val
    if not values:
        raise RuntimeError("Yahoo ^VXN chart API contained no valid daily Close observations.")
    return values, {
        "source": "Yahoo Finance chart API ^VXN daily Close",
        "url": YAHOO_VXN_CHART,
        "observations": len(values),
        "first_date": min(values),
        "last_date": max(values),
        "note": "Nasdaq-100 implied-volatility index proxy; not a QQQ option IV/skew surface and not executable option data. Missing days are not forward-filled."
    }


def fetch_yahoo_vxn(start: date, end: date) -> tuple[dict[str, float], dict[str, Any]]:
    params = {
        "period1": int(datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc).timestamp()),
        "period2": int(datetime.combine(end + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc).timestamp()),
        "interval": "1d",
        "events": "history"
    }
    url = YAHOO_VXN_CHART + "?" + urlencode(params)
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            payload = json.loads(fetch_text(url, timeout=20))
            values, meta = parse_yahoo_vxn_payload(payload, start, end)
            meta["url"] = url
            return values, meta
        except Exception as exc:
            last_error = exc
            if attempt < 1:
                time.sleep(1.0)
    raise RuntimeError(f"Yahoo ^VXN daily history unavailable: {last_error}")


def wilson95(k: int, n: int) -> tuple[float | None, float | None]:
    if n <= 0:
        return None, None
    z = 1.959963984540054
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return 100 * (c - h), 100 * (c + h)


def price_stats(rows: list[dict[str, Any]], rv: list[float | None], period_start: date,
                period_end: date, window_name: str) -> list[dict[str, Any]]:
    dates = [date.fromisoformat(x["date"]) for x in rows]
    result = []
    for h in HORIZONS:
        groups: dict[str, list[dict[str, Any]]] = {"ALL": []}
        for i in range(len(rows) - h):
            if not (period_start <= dates[i] <= period_end):
                continue
            future = rows[i:i + h + 1]
            if len(future) != h + 1 or dates[i + h] > period_end:
                continue
            # Yahoo provides trading-session bars only; a missing returned close censors the path.
            first, last = float(future[0]["raw_close"]), float(future[-1]["raw_close"])
            if first <= 0 or last <= 0:
                continue
            v = rows[i].get("vix")
            ret = last / first - 1
            obj = {"index": i, "return": ret, "rv": rv[i], "vix": v}
            groups["ALL"].append(obj)
            rlabel, vlabel, xnlabel = rv_label(rv[i]), vix_label(v), vxn_label(rows[i].get("vxn"))
            if rlabel:
                groups.setdefault(rlabel, []).append(obj)
            if vlabel:
                groups.setdefault(vlabel, []).append(obj)
            if xnlabel:
                groups.setdefault(xnlabel, []).append(obj)
        for state, items in sorted(groups.items()):
            returns = [float(x["return"]) for x in items]
            n = len(returns)
            if not n:
                result.append({"window": window_name, "state": state, "horizon_sessions": h, "n": 0})
                continue
            ordered = sorted(returns)
            q = lambda p: ordered[min(n - 1, max(0, int(round((n - 1) * p))))]
            k5 = sum(x <= -.05 for x in returns)
            lo, hi = wilson95(k5, n)
            offset_rates = []
            for offset in range(max(1, h)):
                sub = [x for x in items if x["index"] % h == offset]
                if sub:
                    offset_rates.append(100 * sum(x["return"] <= -.05 for x in sub) / len(sub))
            rvvals = [float(x["rv"]) for x in items if x.get("rv") is not None]
            sample_vol = statistics.stdev([math.log1p(x) for x in returns if x > -1]) if n > 1 else None
            median_rv = statistics.median(rvvals) if rvvals else None
            ratio = sample_vol / (median_rv * math.sqrt(h / 252)) if sample_vol is not None and median_rv and median_rv > 0 else None
            result.append({
                "window": window_name, "state": state, "horizon_sessions": h, "n": n,
                "p_positive_pct": round(100 * sum(x > 0 for x in returns) / n, 4),
                "p_down_3pct_pct": round(100 * sum(x <= -.03 for x in returns) / n, 4),
                "p_down_5pct_pct": round(100 * k5 / n, 4),
                "p_down_5pct_wilson95_nominal_low": round(lo, 4) if lo is not None else None,
                "p_down_5pct_wilson95_nominal_high": round(hi, 4) if hi is not None else None,
                "p_down_10pct_pct": round(100 * sum(x <= -.10 for x in returns) / n, 4),
                "p_up_5pct_pct": round(100 * sum(x >= .05 for x in returns) / n, 4),
                "p05_return_pct": round(100 * q(.05), 4),
                "median_return_pct": round(100 * q(.50), 4),
                "p95_return_pct": round(100 * q(.95), 4),
                "nonoverlap_p_down5_min_pct": round(min(offset_rates), 4) if offset_rates else None,
                "nonoverlap_p_down5_max_pct": round(max(offset_rates), 4) if offset_rates else None,
                "median_rv20_pct": round(100 * median_rv, 4) if median_rv is not None else None,
                "rv_sqrt_time_scale_ratio": round(ratio, 4) if ratio is not None else None,
            })
    return result


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("status,detail\nEMPTY,No observations\n", encoding="utf-8")
        return
    fields = list(dict.fromkeys(key for row in rows for key in row.keys()))
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def run(start: date, source_end: date, end: date, out: Path) -> dict[str, Any]:
    if start >= source_end or source_end >= end:
        raise ValueError("Require start < source-end < end.")
    rows, yahoo_meta = fetch_qqq(start, end)
    vix_status = "OK"
    try:
        vix_map, vix_meta = fetch_vix(start, end)
        vix_status = "OK_YAHOO_FALLBACK" if vix_meta.get("fallback_used") else "OK_FRED"
    except Exception as exc:
        vix_map, vix_meta, vix_status = {}, {"source": "FRED VIXCLS then Yahoo ^VIX fallback", "error": str(exc)}, "UNAVAILABLE_RV_ONLY"
    try:
        vxn_map, vxn_meta = fetch_yahoo_vxn(start, end)
        vxn_status = "OK_YAHOO"
    except Exception as exc:
        vxn_map, vxn_meta, vxn_status = {}, {"source": "Yahoo Finance chart API ^VXN", "error": str(exc)}, "UNAVAILABLE_VXN_PROXY_ONLY"
    for row in rows:
        row["vix"] = vix_map.get(row["date"])
        row["vxn"] = vxn_map.get(row["date"])
    rv = rv_buckets(rows)
    full_start, full_end = start, date.fromisoformat(rows[-1]["date"])
    base_stats = price_stats(rows, rv, start, source_end, "YAHOO_PRICE_WINDOW_2018_03_TO_2025_12_15")
    ext_stats = price_stats(rows, rv, source_end + timedelta(days=1), full_end, "YAHOO_PRICE_ONLY_EXTENSION_AFTER_2025_12_15")
    full_stats = price_stats(rows, rv, full_start, full_end, "YAHOO_PRICE_WINDOW_FULL")
    # Current selloff metric is peak-to-last close over the most recent 8 trading bars (7 close-to-close returns).
    last8 = rows[-8:] if len(rows) >= 8 else rows
    recent_peak = max(float(x["raw_close"]) for x in last8)
    recent_last = float(last8[-1]["raw_close"])
    meta = {
        "research_id": "QQQ_PUBLIC_PRICE_PROXY_SUPPLEMENT_V1",
        "status": "PRICE_PATH_ONLY_OPTION_PNL_NOT_ESTIMATED",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "start_date": rows[0]["date"], "end_date": rows[-1]["date"],
        "daily_rows": len(rows),
        "option_chain_boundary": SOURCE_END.isoformat(),
        "yahoo": yahoo_meta,
        "vix_proxy": {**vix_meta, "status": vix_status},
        "vxn_proxy": {**vxn_meta, "status": vxn_status},
        "current_tape_observations": {
            "last_7_session_peak_close_usd": round(recent_peak, 4),
            "last_close_usd": round(recent_last, 4),
            "peak_to_last_pct": round(100 * (recent_last / recent_peak - 1), 4),
            "interpretation": "Observed price path only; neither an option-strategy loss estimate nor a tradable signal."
        },
        "limitations": [
            "The Yahoo price series is a separately fetched vendor proxy, not the pinned option-source's underlying field.",
            "VIXCLS, when available, is broad S&P 500 implied volatility; it is not QQQ IV or a QQQ put-skew surface.",
            "Post-2025-12-15 probabilities describe QQQ prices only. No option-chain outcomes, bid/ask marks, fills, margin, or assignments are inferred.",
            "Historical windows overlap; Wilson intervals are nominal and do not remove serial dependence.",
            "2018-2025 remains development/revisit history, not a blind holdout."
        ],
        "outputs": [
            "qqq_public_price_proxy_daily.csv",
            "qqq_public_price_proxy_probabilities.csv",
            "qqq_public_price_proxy_summary.md",
            "qqq_public_price_proxy_summary.json"
        ]
    }
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "qqq_public_price_proxy_daily.csv", rows)
    write_csv(out / "qqq_public_price_proxy_probabilities.csv", base_stats + ext_stats + full_stats)
    (out / "qqq_public_price_proxy_summary.json").write_text(json.dumps({**meta, "probability_rows": len(base_stats + ext_stats + full_stats)}, indent=2), encoding="utf-8")
    lines = [
        "# QQQ public-price proxy supplement",
        "",
        "**Status: price-path supplement only. No option strategy P&L is estimated for dates without an option chain.**",
        "",
        f"- Yahoo daily Close window: {rows[0]['date']} to {rows[-1]['date']} ({len(rows)} observations).",
        f"- Option mirror boundary: {SOURCE_END.isoformat()}; use the post-boundary probability rows as an underlying-only sensitivity, not an option replay.",
        f"- Broad-market VIX proxy status: {vix_status}; source: {vix_meta.get('source', 'unavailable')}. This is not QQQ option IV/skew.",
        f"- Nasdaq-100 VXN proxy status: {vxn_status}; source: {vxn_meta.get('source', 'unavailable')}. This is not a QQQ option IV/skew surface.",
        f"- Recent peak-to-last (up to 7 close-to-close sessions): {meta['current_tape_observations']['peak_to_last_pct']}%.",
        "",
        "## Downside frequencies by period",
        "",
        "| Window | State | Sessions | N | P(down >=3%) | P(down >=5%) | P(down >=10%) | P05 return | Median | P95 return | Nominal 95% interval for down >=5% |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
    ]
    for item in base_stats + ext_stats:
        if item["state"] not in ("ALL", "VXN_20_30", "VXN_30_40", "VXN_GTE40", "VIX_25_35", "VIX_GTE35") or item["horizon_sessions"] not in (5, 10, 20, 45):
            continue
        lo, hi = item.get("p_down_5pct_wilson95_nominal_low"), item.get("p_down_5pct_wilson95_nominal_high")
        ci = "—" if lo is None else f"{lo}%–{hi}%"
        lines.append(f"| {item['window']} | {item['state']} | {item['horizon_sessions']} | {item['n']} | {item.get('p_down_3pct_pct')}% | {item.get('p_down_5pct_pct')}% | {item.get('p_down_10pct_pct')}% | {item.get('p05_return_pct')}% | {item.get('median_return_pct')}% | {item.get('p95_return_pct')}% | {ci} |")
    lines += [
        "",
        "## Data boundaries / use",
        "",
        "- This supplement intentionally does not extend option-strategy P&L. A QQQ price down-move is not the probability of a particular put ratio losing money.",
        "- A current-market observation can inform a stress scenario, but without QQQ option bid/ask and IV/skew on the same decision dates it cannot recreate fills, strategy gamma/vega, or margin actions.",
        "- Any unavailable Yahoo data blocks this external supplement; it must not be silently substituted with zeros or forward-filled prices.",
        "- All price-frequency estimates are empirical overlapping windows; non-overlap ranges are sensitivity checks, not independent-trial confidence intervals.",
    ]
    (out / "qqq_public_price_proxy_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return meta


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--start", default="2018-03-01")
    p.add_argument("--source-end", default=SOURCE_END.isoformat())
    p.add_argument("--end", default="2026-10-15")
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    result = run(date.fromisoformat(a.start), date.fromisoformat(a.source_end), date.fromisoformat(a.end), a.out)
    print(json.dumps(result, indent=2))
    print((a.out / "qqq_public_price_proxy_summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
