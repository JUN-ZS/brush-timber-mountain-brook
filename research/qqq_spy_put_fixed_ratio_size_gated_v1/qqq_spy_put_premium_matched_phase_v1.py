#!/usr/bin/env python3
"""Premium-matched DTE14 QQQ LONG PUT / SPY SHORT PUT replay, fixed 1:3 and 1:6 ratios."""
from __future__ import annotations
import argparse, csv, hashlib, json, math, re, statistics, urllib.request
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

SOURCE_REPO = "anahatsingh-ui/options-dataset-hist"
SOURCE_COMMIT = "37f6c456fe1a4775c875673fb8ef907d5cd2fd66"
SOURCE_BASE = "https://raw.githubusercontent.com/anahatsingh-ui/options-dataset-hist/main"
START_DEFAULT, END_DEFAULT = "2018-03-01", "2025-12-15"
MULTIPLIER, COHORT_STRIDE_SESSIONS = 100, 45
DTE_MIN_DEFAULT, DTE_MAX_DEFAULT, DTE_TARGET_DEFAULT = 30, 60, 45
DELTA_TARGET_DEFAULT, DELTA_MIN, DELTA_MAX = 0.25, 0.10, 0.50
BASE_SLIPPAGE, BASE_COMMISSION = 0.05, 0.65
SLIPPAGE_GRID, COMMISSION_GRID = (0.0, 0.025, 0.05, 0.10), (0.0, 0.65)
POLICIES = (
    {"policy": "HOLD_5_SESSIONS", "hold_sessions": 5},
    {"policy": "HOLD_10_SESSIONS", "hold_sessions": 10},
    {"policy": "HOLD_20_SESSIONS", "hold_sessions": 20},
    {"policy": "HOLD_20_OR_DTE_LE_7", "hold_sessions": 20, "expiry_guard_dte": 7},
    {"policy": "EXIT_AT_DTE_LE_7", "hold_sessions": None},
)
OPTION_COLUMNS = ["contract_id", "symbol", "expiration", "strike", "type", "bid", "ask",
                  "bid_size", "ask_size", "volume", "open_interest", "date",
                  "implied_volatility", "delta"]
YEARS = range(2018, 2026)
PINS = {
 "QQQ": {
  2018:(29215815,"4a130fe579ee141c5836ccaaf093c0cb752ebb19"),
  2019:(30998008,"95386cb37a6b1ca757e7fd6a0b0fd458c91e04ca"),
  2020:(59412637,"9d7abe1144c55e0091d28eca61deec4ac72393a5"),
  2021:(74224966,"3488cffd498a8851861a8dca7d1849a748bc759d"),
  2022:(69941736,"e9bcb16986835e3eba304300aeb6d6a8ed56bbe9"),
  2023:(71647343,"bbaa5aeefc54c76628142a6e95c7424995049063"),
  2024:(82434832,"40c1c2fd986da9b5bcf363cd44c9d5ac3eecc8c3"),
  2025:(85765453,"e92ad6b5c2e757d2c869f747a94853e630142cbf")},
 "SPY": {
  2018:(36266339,"473e4fe80281ca9371b5f531b97f19394e8e2814"),
  2019:(41731396,"2d06f2ca587452ea9a6ffa52e6ddc4262c3e6f4d"),
  2020:(59100008,"f0093698ac9fbbe7dbd9159735fcb73ff9418ff2"),
  2021:(64071426,"459555aaed9be451a504d68d2db6cce4b94c3a6d"),
  2022:(57070606,"f0a15b8263b7650147bfa62bce2cd44d59ef17a5"),
  2023:(47343699,"ead8adeee0689d26e49f5b39f6d5536443931ac3"),
  2024:(56948550,"8e0b7ca48dffa92fe93ceeffefdfce8557eab74a"),
  2025:(58216546,"133bf1d95c3479149bf4771bc8b3fd8b625064ce")}
}
UNDERLYING_PINS = {
 "QQQ":(332454,"f3a892bc4c88c692900b5c0071322c6db408996a"),
 "SPY":(252066,"4c22934a77ba09ced10fd1c413b5d8c9e0cb4a8d")
}

def as_day(value: Any) -> str:
    if value is None: return ""
    return value.isoformat()[:10] if hasattr(value, "isoformat") else str(value)[:10]

def num(value: Any) -> float | None:
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (TypeError, ValueError): return None


def put_moneyness(spot: Any, strike: Any) -> dict[str, Any]:
    """For a put, positive (spot-strike)/spot is OTM; negative is ITM."""
    s, k = num(spot), num(strike)
    if s is None or k is None or s <= 0 or k <= 0:
        return {"otm_pct": None, "status": "INVALID"}
    pct = (s - k) / s * 100.0
    status = "OTM" if k < s else "ITM" if k > s else "ATM"
    return {"otm_pct": pct, "status": status}

def normalized_contract_id(row: dict[str, Any]) -> str:
    ident = re.sub(r"\s+", "", str(row.get("contract_id") or "").strip().upper())
    return ident[2:] if ident.startswith("O:") else ident

def standard_put_identity(row: dict[str, Any], symbol: str) -> bool:
    ident = normalized_contract_id(row)
    m = re.fullmatch(re.escape(symbol) + r"(\d{6})P(\d{8})", ident)
    if not m or str(row.get("symbol", "")).upper() != symbol:
        return False
    if str(row.get("type", "")).strip().lower() not in ("p", "put"): return False
    try: expiry = datetime.strptime(m.group(1), "%y%m%d").date().isoformat()
    except ValueError: return False
    strike = num(row.get("strike"))
    return (as_day(row.get("expiration")) == expiry and strike is not None and strike > 0
            and abs(strike - int(m.group(2)) / 1000.0) < 0.00051)

def valid_quote(row: dict[str, Any] | None, require_positive_bid: bool = False) -> bool:
    if not isinstance(row, dict): return False
    bid, ask = num(row.get("bid")), num(row.get("ask"))
    return (bid is not None and ask is not None and ask > 0 and bid >= 0 and bid <= ask
            and (not require_positive_bid or bid > 0))

def displayed_size(row: dict[str, Any] | None, side: str) -> int:
    if not isinstance(row, dict): return 0
    value = num(row.get("bid_size" if side == "bid" else "ask_size"))
    return int(value) if value is not None and value > 0 else 0

def git_blob_sha_file(path: Path, expected_size: int) -> str:
    h = hashlib.sha1(); h.update(f"blob {expected_size}\0".encode("ascii"))
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""): h.update(block)
    return h.hexdigest()

def download_verified(symbol: str, year: int | None, cache: Path):
    cache.mkdir(parents=True, exist_ok=True)
    if year is None:
        size, sha = UNDERLYING_PINS[symbol]; name = "underlying_prices.parquet"
    else:
        size, sha = PINS[symbol][year]; name = f"options_{year}.parquet"
    path = cache / name
    if path.is_file() and path.stat().st_size == size:
        actual = git_blob_sha_file(path, size)
        if actual == sha:
            return path, {"symbol":symbol,"file":name,"status":"CACHED_HASH_VERIFIED","bytes":size,"git_blob_sha":actual}
        path.unlink()
    url = f"{SOURCE_BASE}/{symbol.lower()}/{name}"
    request = urllib.request.Request(url, headers={"User-Agent":"qqq-spy-cross-put-replay/1.0"})
    h = hashlib.sha1(); h.update(f"blob {size}\0".encode("ascii")); total = 0
    with urllib.request.urlopen(request, timeout=180) as response, path.open("wb") as output:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk: break
            total += len(chunk); output.write(chunk); h.update(chunk)
    actual = h.hexdigest()
    if total != size or actual != sha:
        path.unlink(missing_ok=True)
        raise ValueError(f"{symbol}/{name} pin mismatch: bytes={total}/{size}; sha={actual}/{sha}")
    return path, {"symbol":symbol,"file":name,"status":"DOWNLOADED_HASH_VERIFIED","bytes":total,"git_blob_sha":actual}

def spot_rows_to_map(date_values, symbol_values, close_values, symbol: str) -> dict[str, float]:
    if not (len(date_values) == len(symbol_values) == len(close_values)):
        raise ValueError("underlying date/symbol/close columns have different lengths")
    result = {}
    for dv, sv, cv in zip(date_values, symbol_values, close_values):
        day, close = as_day(dv), num(cv)
        if str(sv).strip().upper() == symbol.upper() and day and close is not None and close > 0:
            result[day] = close
    return result


def load_spots(path: Path, symbol: str) -> dict[str, float]:
    import pyarrow.parquet as pq
    table = pq.read_table(path)
    names = {name.lower(): name for name in table.column_names}
    dc, sc, cc = names.get("date"), names.get("symbol"), names.get("close") or names.get("raw_close")
    if not dc or not cc:
        raise ValueError(f"{path.name} lacks date/close; columns={table.column_names}")
    if not sc:
        raise ValueError(f"{path.name} lacks a symbol column; refusing ambiguous underlying prices")
    result = spot_rows_to_map(table[dc].to_pylist(), table[sc].to_pylist(), table[cc].to_pylist(), symbol)
    if not result:
        raise ValueError(f"{path.name} contains no underlying rows for symbol={symbol}")
    return result

def iter_symbol_days(paths: list[Path], symbol: str, start_day: str, end_day: str, stats: dict[str, Any]) -> Iterable:
    import pyarrow.parquet as pq
    previous_day = ""
    for path in paths:
        parquet = pq.ParquetFile(path)
        missing = sorted(set(OPTION_COLUMNS) - set(parquet.schema_arrow.names))
        if missing: raise ValueError(f"{path.name} missing required columns: {missing}")
        current_day, rows = None, []
        def emit(day, day_rows):
            if day and start_day <= day <= end_day and day_rows:
                stats["chain_dates"] += 1; stats["put_rows"] += len(day_rows); stats["last_chain_date"] = day
                return day, day_rows
            return None
        for batch in parquet.iter_batches(batch_size=65536, columns=OPTION_COLUMNS):
            for row in batch.to_pylist():
                day = as_day(row.get("date"))
                if not day: continue
                if previous_day and day < previous_day:
                    raise ValueError(f"{path.name} is not date ordered at {day} after {previous_day}")
                previous_day = day
                if current_day is None: current_day = day
                elif day != current_day:
                    item = emit(current_day, rows)
                    if item is not None: yield item
                    current_day, rows = day, []
                if start_day <= day <= end_day and str(row.get("symbol","")).upper() == symbol and str(row.get("type","")).strip().lower() in ("p","put"):
                    rows.append(row)
        item = emit(current_day, rows)
        if item is not None: yield item

def choose_leg(rows, symbol, day, expiry, target_delta):
    candidates = []
    for row in rows:
        if not standard_put_identity(row, symbol) or as_day(row.get("date")) != day: continue
        if as_day(row.get("expiration")) != expiry or not valid_quote(row, require_positive_bid=True): continue
        delta, strike = num(row.get("delta")), num(row.get("strike"))
        if delta is None or not DELTA_MIN <= abs(delta) <= DELTA_MAX or strike is None or strike <= 0: continue
        bid, ask = float(row["bid"]), float(row["ask"])
        candidates.append({"row":row,"id":normalized_contract_id(row),"strike":strike,"abs_delta":abs(delta),
            "spread":(ask-bid)/max((ask+bid)/2,1e-9),"size":min(displayed_size(row,"bid"),displayed_size(row,"ask")),
            "oi":num(row.get("open_interest")) or 0})
    if not candidates: return None
    return min(candidates,key=lambda x:(abs(x["abs_delta"]-target_delta),-x["size"],-x["oi"],x["spread"],x["id"]))

def choose_pair(qqq_rows, spy_rows, signal_day, qqq_spot, spy_spot, target_delta=DELTA_TARGET_DEFAULT,
                dte_min=DTE_MIN_DEFAULT, dte_max=DTE_MAX_DEFAULT, dte_target=DTE_TARGET_DEFAULT):
    if not qqq_rows or not spy_rows or qqq_spot <= 0 or spy_spot <= 0: return None
    date.fromisoformat(signal_day)
    def expiries(rows, symbol):
        found = {}
        for row in rows:
            if not standard_put_identity(row,symbol) or as_day(row.get("date")) != signal_day: continue
            if not valid_quote(row,require_positive_bid=True): continue
            expiry = as_day(row.get("expiration"))
            try: dte = (date.fromisoformat(expiry)-date.fromisoformat(signal_day)).days
            except ValueError: continue
            if dte_min <= dte <= dte_max: found[expiry] = dte
        return found
    q_exp, s_exp = expiries(qqq_rows,"QQQ"), expiries(spy_rows,"SPY")
    choices=[]
    for expiry in sorted(set(q_exp)&set(s_exp)):
        qleg=choose_leg(qqq_rows,"QQQ",signal_day,expiry,target_delta)
        sleg=choose_leg(spy_rows,"SPY",signal_day,expiry,target_delta)
        if qleg is None or sleg is None: continue
        dte=q_exp[expiry]
        key=(abs(dte-dte_target),abs(qleg["abs_delta"]-target_delta)+abs(sleg["abs_delta"]-target_delta),
             -(qleg["size"]+sleg["size"]),-(qleg["oi"]+sleg["oi"]),expiry,qleg["id"],sleg["id"])
        choices.append((key,expiry,dte,qleg,sleg))
    if not choices:return None
    _,expiry,dte,qleg,sleg=min(choices,key=lambda x:x[0])
    qsig = put_moneyness(qqq_spot, qleg["strike"])
    ssig = put_moneyness(spy_spot, sleg["strike"])
    return {"signal_date":signal_day,"expiry":expiry,"signal_dte":dte,
        "qqq_contract_id":qleg["id"],"qqq_strike":qleg["strike"],"qqq_abs_delta":qleg["abs_delta"],
        "spy_contract_id":sleg["id"],"spy_strike":sleg["strike"],"spy_abs_delta":sleg["abs_delta"],
        "qqq_spot_signal":qqq_spot,"spy_spot_signal":spy_spot,
        "qqq_otm_pct_signal":qsig["otm_pct"],"qqq_moneyness_signal":qsig["status"],
        "spy_otm_pct_signal":ssig["otm_pct"],"spy_moneyness_signal":ssig["status"],
        "selection_rule":"same expiry; nearest DTE45 then abs-delta nearest target; no P&L optimization"}



def choose_pair_by_premium(qqq_rows, spy_rows, signal_day, qqq_spot, spy_spot,
                           target_delta=DELTA_TARGET_DEFAULT, dte_min=7, dte_max=21,
                           dte_target=14, premium_match_short_qty=6,
                           qqq_target_abs_delta=None, qqq_delta_tolerance=0.10,
                           qqq_reference_premium_fraction=None, qqq_required_size=1):
    """Select same-expiry QQQ/SPY puts; optionally buy multiple half-premium QQQ contracts.

    Normal mode matches one QQQ put Ask to N times the SPY short-put Bid, optionally
    inside a QQQ Delta band. Fraction mode first identifies that reference QQQ put,
    then selects an alternative QQQ put at the requested fraction of the reference
    put's Ask on the same expiry. The final alternative's Delta is deliberately not
    constrained: a cheaper option is not assumed to have equivalent hedge sensitivity.
    """
    if premium_match_short_qty < 1:
        raise ValueError("premium_match_short_qty must be a positive integer")
    if qqq_required_size < 1:
        raise ValueError("qqq_required_size must be positive")
    if qqq_reference_premium_fraction is not None and not 0 < qqq_reference_premium_fraction < 1:
        raise ValueError("qqq_reference_premium_fraction must be between 0 and 1")
    if qqq_target_abs_delta is not None:
        if not 0 < qqq_target_abs_delta < 1:
            raise ValueError("qqq_target_abs_delta must be between 0 and 1")
        if qqq_delta_tolerance < 0 or qqq_target_abs_delta-qqq_delta_tolerance < 0 or qqq_target_abs_delta+qqq_delta_tolerance > 1:
            raise ValueError("QQQ Delta tolerance must keep the full band between 0 and 1")
    if not qqq_rows or not spy_rows or qqq_spot <= 0 or spy_spot <= 0:
        return None

    def expiry_map(rows, symbol):
        found = {}
        for row in rows:
            if not standard_put_identity(row, symbol) or as_day(row.get("date")) != signal_day:
                continue
            if not valid_quote(row, require_positive_bid=True):
                continue
            expiry = as_day(row.get("expiration"))
            try:
                dte = (date.fromisoformat(expiry) - date.fromisoformat(signal_day)).days
            except ValueError:
                continue
            if dte_min <= dte <= dte_max:
                found[expiry] = dte
        return found

    q_exp, s_exp = expiry_map(qqq_rows, "QQQ"), expiry_map(spy_rows, "SPY")
    choices = []
    for expiry in sorted(set(q_exp) & set(s_exp)):
        dte = q_exp[expiry]
        sleg = choose_leg(spy_rows, "SPY", signal_day, expiry, target_delta)
        if sleg is None:
            continue
        spy_bid = float(sleg["row"]["bid"])
        normal_target_ask = spy_bid * int(premium_match_short_qty)
        q_candidates = []
        for row in qqq_rows:
            if not standard_put_identity(row, "QQQ") or as_day(row.get("date")) != signal_day:
                continue
            if as_day(row.get("expiration")) != expiry or not valid_quote(row, require_positive_bid=True):
                continue
            delta, strike = num(row.get("delta")), num(row.get("strike"))
            if delta is None or strike is None or strike <= 0:
                continue
            bid, ask = float(row["bid"]), float(row["ask"])
            size = min(displayed_size(row, "bid"), displayed_size(row, "ask"))
            if size < 1:
                continue
            abs_delta = abs(delta)
            q_candidates.append({
                "row": row, "id": normalized_contract_id(row), "strike": strike,
                "abs_delta": abs_delta, "spread": (ask-bid)/max((ask+bid)/2, 1e-9),
                "size": size, "oi": num(row.get("open_interest")) or 0,
                "ask": ask, "bid": bid,
            })
        if not q_candidates:
            continue

        def reference_key(x):
            return (
                abs(x["ask"]-normal_target_ask),
                abs(x["abs_delta"]-qqq_target_abs_delta) if qqq_target_abs_delta is not None else 0.0,
                -x["size"], -x["oi"], x["spread"], x["id"]
            )

        if qqq_reference_premium_fraction is not None:
            # Establish the original QQQ protection contract using the existing rules.
            reference_candidates = [
                x for x in q_candidates
                if qqq_target_abs_delta is None or
                qqq_target_abs_delta-qqq_delta_tolerance <= x["abs_delta"] <= qqq_target_abs_delta+qqq_delta_tolerance
            ]
            if not reference_candidates:
                continue
            qref = min(reference_candidates, key=reference_key)
            desired_ask = qref["ask"] * qqq_reference_premium_fraction
            # The alternative needs enough displayed size for the requested multi-contract buy.
            alternative_candidates = [x for x in q_candidates if x["size"] >= qqq_required_size]
            if not alternative_candidates:
                continue
            qleg = min(alternative_candidates, key=lambda x: (
                abs(x["ask"]-desired_ask), -x["size"], -x["oi"], x["spread"], x["id"]
            ))
            premium_error = qleg["ask"] - desired_ask
        else:
            reference_candidates = [
                x for x in q_candidates
                if qqq_target_abs_delta is None or
                qqq_target_abs_delta-qqq_delta_tolerance <= x["abs_delta"] <= qqq_target_abs_delta+qqq_delta_tolerance
            ]
            if not reference_candidates:
                continue
            qleg = min(reference_candidates, key=reference_key)
            qref = qleg
            desired_ask = normal_target_ask
            premium_error = qleg["ask"] - normal_target_ask

        # Nearest-DTE-first is preserved; within an expiry, use the selected put's premium error.
        key = (
            abs(dte-dte_target),
            abs(premium_error)/max(desired_ask, 0.01),
            abs(sleg["abs_delta"]-target_delta),
            -(qleg["size"]+sleg["size"]),
            -(qleg["oi"]+sleg["oi"]),
            expiry, qleg["id"], sleg["id"],
        )
        choices.append((key, expiry, dte, qleg, sleg, desired_ask, premium_error, qref))

    if not choices:
        return None
    _, expiry, dte, qleg, sleg, desired_ask, premium_error, qref = min(choices, key=lambda x: x[0])
    qsig = put_moneyness(qqq_spot, qleg["strike"])
    ssig = put_moneyness(spy_spot, sleg["strike"])
    fraction_mode = qqq_reference_premium_fraction is not None
    rule = (
        f"same expiry; nearest DTE{dte_target}; SPY abs-Delta nearest {target_delta:.2f}; "
        f"reference QQQ abs-Delta {qqq_target_abs_delta:.2f} +/- {qqq_delta_tolerance:.2f} "
        f"Ask nearest {premium_match_short_qty}x SPY short-put Bid; "
        f"alternative QQQ Ask nearest {qqq_reference_premium_fraction:.0%} of reference QQQ Ask; "
        f"selected QQQ Delta unconstrained; selected QQQ displayed size >= {qqq_required_size}"
        if fraction_mode else
        f"same expiry; nearest DTE{dte_target}; SPY abs-Delta nearest {target_delta:.2f}; "
        + (f"QQQ abs-Delta {qqq_target_abs_delta:.2f} +/- {qqq_delta_tolerance:.2f}; " if qqq_target_abs_delta is not None else "")
        + f"QQQ Ask nearest {premium_match_short_qty}x SPY short-put Bid"
    )
    return {
        "signal_date": signal_day, "expiry": expiry, "signal_dte": dte,
        "qqq_contract_id": qleg["id"], "qqq_strike": qleg["strike"],
        "qqq_abs_delta": qleg["abs_delta"], "qqq_signal_ask": qleg["ask"],
        "qqq_target_abs_delta": qqq_target_abs_delta,
        "qqq_delta_tolerance": qqq_delta_tolerance if qqq_target_abs_delta is not None else None,
        "qqq_delta_band_low": qqq_target_abs_delta-qqq_delta_tolerance if qqq_target_abs_delta is not None else None,
        "qqq_delta_band_high": qqq_target_abs_delta+qqq_delta_tolerance if qqq_target_abs_delta is not None else None,
        "qqq_target_ask_signal": desired_ask,
        "qqq_premium_match_short_qty": int(premium_match_short_qty),
        "qqq_premium_match_error_signal": premium_error,
        "qqq_premium_reference_contract_id": qref["id"],
        "qqq_premium_reference_ask_signal": qref["ask"],
        "qqq_premium_reference_abs_delta": qref["abs_delta"],
        "qqq_reference_premium_fraction": qqq_reference_premium_fraction,
        "spy_contract_id": sleg["id"], "spy_strike": sleg["strike"],
        "spy_abs_delta": sleg["abs_delta"], "spy_signal_bid": spy_bid,
        "qqq_spot_signal": qqq_spot, "spy_spot_signal": spy_spot,
        "qqq_otm_pct_signal": qsig["otm_pct"], "qqq_moneyness_signal": qsig["status"],
        "spy_otm_pct_signal": ssig["otm_pct"], "spy_moneyness_signal": ssig["status"],
        "selection_rule": rule,
    }

def rows_by_id(rows): return {normalized_contract_id(row):row for row in rows if normalized_contract_id(row)}



def evaluate_entry_filter(filter_name, idx, dates, qspots, sspots, lookback=20):
    """Evaluate filters strictly from current/prior underlying closes; no future prices."""
    empty = {
        "entry_filter": filter_name,
        "filter_lookback_sessions": 0,
        "qqq_trailing_return_pct": None,
        "spy_trailing_return_pct": None,
        "qqq_minus_spy_trailing_return_pct": None,
        "spy_previous_trailing_return_pct": None,
        "qqq_spy_corr_60d": None,
        "filter_pass_reason": None,
    }
    if filter_name == "none":
        empty.update({"entry_filter": "none", "filter_pass_reason": "FILTER_DISABLED"})
        return True, empty

    if filter_name == "spy_weekly_drop_2pct_corr60_pos":
        # Event trigger: SPY rolling 5-session return crosses from > -2% to <= -2%.
        # Require positive Pearson correlation of the prior 60 daily returns, ending before signal day.
        lookback = 5
        if idx < 61:
            empty.update({"filter_lookback_sessions": 60, "filter_pass_reason": "INSUFFICIENT_LOOKBACK"})
            return False, empty
        current_day, prior_day = dates[idx], dates[idx - lookback]
        previous_day, previous_week_start = dates[idx - 1], dates[idx - lookback - 1]
        qnow, qprior = num(qspots.get(current_day)), num(qspots.get(prior_day))
        snow, sprior = num(sspots.get(current_day)), num(sspots.get(prior_day))
        sprev, sprevprior = num(sspots.get(previous_day)), num(sspots.get(previous_week_start))
        if None in (qnow, qprior, snow, sprior, sprev, sprevprior) or min(qprior, sprior, sprevprior) <= 0:
            empty.update({"filter_lookback_sessions": lookback, "filter_pass_reason": "MISSING_OR_INVALID_LOOKBACK_PRICE"})
            return False, empty
        qret = (qnow / qprior - 1) * 100
        sret = (snow / sprior - 1) * 100
        previous_sret = (sprev / sprevprior - 1) * 100
        xs, ys = [], []
        for j in range(idx - 60, idx):
            day0, day1 = dates[j - 1], dates[j]
            q0, q1 = num(qspots.get(day0)), num(qspots.get(day1))
            s0, s1 = num(sspots.get(day0)), num(sspots.get(day1))
            if None in (q0, q1, s0, s1) or min(q0, s0) <= 0:
                continue
            xs.append(q1 / q0 - 1)
            ys.append(s1 / s0 - 1)
        corr = None
        if len(xs) >= 45:
            mx, my = statistics.mean(xs), statistics.mean(ys)
            dx, dy = [v-mx for v in xs], [v-my for v in ys]
            den = math.sqrt(sum(v*v for v in dx) * sum(v*v for v in dy))
            corr = sum(a*b for a,b in zip(dx,dy)) / den if den > 0 else None
        crossed = sret <= -2.0 and previous_sret > -2.0
        positive_corr = corr is not None and corr > 0
        passed = crossed and positive_corr
        reason = ("SPY_5D_DROPPED_THROUGH_MINUS_2PCT_AND_PRIOR_60D_CORR_POSITIVE" if passed
                  else "NO_NEW_SPY_5D_MINUS_2PCT_CROSSING" if not crossed
                  else "PRIOR_60D_QQQ_SPY_CORRELATION_NOT_POSITIVE")
        return passed, {
            "entry_filter": filter_name,
            "filter_lookback_sessions": lookback,
            "qqq_trailing_return_pct": finite_round(qret, 4),
            "spy_trailing_return_pct": finite_round(sret, 4),
            "qqq_minus_spy_trailing_return_pct": finite_round(qret-sret, 4),
            "spy_previous_trailing_return_pct": finite_round(previous_sret, 4),
            "qqq_spy_corr_60d": finite_round(corr, 6),
            "filter_pass_reason": reason,
        }

    if filter_name != "qqq_underperforms_spy_20d":
        raise ValueError(f"unknown entry filter: {filter_name}")
    if idx < lookback:
        empty.update({"filter_lookback_sessions": lookback, "filter_pass_reason": "INSUFFICIENT_LOOKBACK"})
        return False, empty
    current_day, prior_day = dates[idx], dates[idx - lookback]
    qnow, qprior = num(qspots.get(current_day)), num(qspots.get(prior_day))
    snow, sprior = num(sspots.get(current_day)), num(sspots.get(prior_day))
    if None in (qnow, qprior, snow, sprior) or min(qprior, sprior) <= 0:
        empty.update({"filter_lookback_sessions": lookback, "filter_pass_reason": "MISSING_OR_INVALID_LOOKBACK_PRICE"})
        return False, empty
    qret = (qnow / qprior - 1) * 100
    sret = (snow / sprior - 1) * 100
    relative = qret - sret
    passed = relative < 0
    return passed, {
        "entry_filter": filter_name,
        "filter_lookback_sessions": lookback,
        "qqq_trailing_return_pct": finite_round(qret, 4),
        "spy_trailing_return_pct": finite_round(sret, 4),
        "qqq_minus_spy_trailing_return_pct": finite_round(relative, 4),
        "spy_previous_trailing_return_pct": None,
        "qqq_spy_corr_60d": None,
        "filter_pass_reason": "QQQ_UNDERPERFORMED_SPY" if passed else "QQQ_DID_NOT_UNDERPERFORM_SPY",
    }


def choose_equal_premium_quantities(qqq_put_ask, spy_put_bid, max_total_contracts,
                                    max_long_available, max_short_available):
    """Match QQQ LONG PUT premium debit to SPY SHORT PUT premium credit."""
    qprice, sprice = num(qqq_put_ask), num(spy_put_bid)
    if (qprice is None or sprice is None or qprice <= 0 or sprice <= 0
            or max_total_contracts < 2):
        return None
    max_long = min(max_total_contracts - 1, int(max_long_available))
    max_short = min(max_total_contracts - 1, int(max_short_available))
    candidates = []
    for long_qty in range(1, max_long + 1):
        for short_qty in range(1, min(max_short, max_total_contracts - long_qty) + 1):
            debit = long_qty * qprice * MULTIPLIER
            credit = short_qty * sprice * MULTIPLIER
            mismatch = abs(debit - credit) / max(debit, credit)
            candidates.append(((mismatch, -min(debit, credit), -(long_qty + short_qty),
                                long_qty, short_qty),
                               long_qty, short_qty, debit, credit))
    if not candidates:
        return None
    _, long_qty, short_qty, debit, credit = min(candidates, key=lambda x: x[0])
    mismatch_usd = abs(debit - credit)
    return {
        "long_qqq_qty": long_qty,
        "short_spy_qty": short_qty,
        "qqq_long_premium_debit_usd": debit,
        "spy_short_premium_credit_usd": credit,
        "premium_mismatch_usd": mismatch_usd,
        "premium_match_pct": (1 - mismatch_usd / max(debit, credit)) * 100,
    }


def choose_fixed_ratio_quantities(qqq_put_ask, spy_put_bid, long_qty, short_qty, max_total_contracts):
    """Return fixed quantities and premium diagnostics; displayed depth is checked separately."""
    qprice, sprice = num(qqq_put_ask), num(spy_put_bid)
    if (qprice is None or sprice is None or qprice <= 0 or sprice <= 0
            or long_qty < 1 or short_qty < 1
            or long_qty + short_qty > max_total_contracts):
        return None
    debit = long_qty * qprice * MULTIPLIER
    credit = short_qty * sprice * MULTIPLIER
    mismatch = abs(debit - credit)
    return {
        "long_qqq_qty": int(long_qty),
        "short_spy_qty": int(short_qty),
        "qqq_long_premium_debit_usd": debit,
        "spy_short_premium_credit_usd": credit,
        "premium_mismatch_usd": mismatch,
        "premium_match_pct": (1 - mismatch / max(debit, credit)) * 100,
    }

def summarize_premium_matching(entries):
    if not entries:
        return {"cohort_n": 0, "ratio_counts": {}, "mean_qqq_premium_debit_usd": None,
                "mean_spy_premium_credit_usd": None, "mean_abs_mismatch_usd": None,
                "median_abs_mismatch_usd": None, "mean_match_pct": None, "median_match_pct": None}
    ratios = {}
    for e in entries:
        key = f"{int(e['long_qqq_qty'])}:{int(e['short_spy_qty'])}"
        ratios[key] = ratios.get(key, 0) + 1
    debits = [float(e["qqq_long_premium_debit_usd"]) for e in entries]
    credits = [float(e["spy_short_premium_credit_usd"]) for e in entries]
    mismatches = [float(e["premium_mismatch_usd"]) for e in entries]
    scores = [float(e["premium_match_pct"]) for e in entries]
    return {
        "cohort_n": len(entries),
        "ratio_counts": dict(sorted(ratios.items(), key=lambda x: (int(x[0].split(":")[0]), int(x[0].split(":")[1])))),
        "mean_qqq_premium_debit_usd": finite_round(statistics.mean(debits), 2),
        "mean_spy_premium_credit_usd": finite_round(statistics.mean(credits), 2),
        "mean_abs_mismatch_usd": finite_round(statistics.mean(mismatches), 2),
        "median_abs_mismatch_usd": finite_round(statistics.median(mismatches), 2),
        "mean_match_pct": finite_round(statistics.mean(scores), 2),
        "median_match_pct": finite_round(statistics.median(scores), 2),
    }

def entry_quotes_valid(qrow,srow,long_qty,short_qty):
    if qrow is None or srow is None:return False,"EXACT_SELECTED_CONTRACT_MISSING"
    if not standard_put_identity(qrow,"QQQ") or not standard_put_identity(srow,"SPY"):return False,"CONTRACT_IDENTITY_INVALID"
    if not valid_quote(qrow) or not valid_quote(srow,require_positive_bid=True):return False,"ENTRY_BID_ASK_INVALID"
    if displayed_size(qrow,"ask") < long_qty:return False,"QQQ_LONG_ASK_SIZE_INSUFFICIENT"
    if displayed_size(srow,"bid") < short_qty:return False,"SPY_SHORT_BID_SIZE_INSUFFICIENT"
    return True,"OK"

def exit_quotes_valid(qrow,srow,long_qty,short_qty):
    if qrow is None or srow is None:return False,"EXACT_SELECTED_CONTRACT_MISSING"
    if not standard_put_identity(qrow,"QQQ") or not standard_put_identity(srow,"SPY"):return False,"CONTRACT_IDENTITY_INVALID"
    if not valid_quote(qrow) or not valid_quote(srow):return False,"EXIT_BID_ASK_INVALID"
    if displayed_size(qrow,"bid") < long_qty:return False,"QQQ_LONG_BID_SIZE_INSUFFICIENT"
    if displayed_size(srow,"ask") < short_qty:return False,"SPY_SHORT_ASK_SIZE_INSUFFICIENT"
    return True,"OK"

def episode_pnl(ep, qqq_exit_bid, spy_exit_ask, slippage_per_share, commission_per_contract_side):
    qqq_gross=ep["long_qqq_qty"]*MULTIPLIER*(qqq_exit_bid-ep["qqq_entry_ask"])
    spy_gross=ep["short_spy_qty"]*MULTIPLIER*(ep["spy_entry_bid"]-spy_exit_ask)
    total=ep["long_qqq_qty"]+ep["short_spy_qty"]
    unit_cost=slippage_per_share*MULTIPLIER+commission_per_contract_side
    qcost=2*ep["long_qqq_qty"]*unit_cost; scost=2*ep["short_spy_qty"]*unit_cost
    gross=qqq_gross+spy_gross; cost=qcost+scost
    return {"qqq_long_gross_pnl_usd":qqq_gross,"spy_short_gross_pnl_usd":spy_gross,
            "gross_pnl_usd":gross,"qqq_long_cost_usd":qcost,"spy_short_cost_usd":scost,
            "cost_usd":cost,"net_pnl_usd":gross-cost}


def qqq_value_decomposition(ep, qqq_exit_bid, qqq_spot_exit, qrow=None):
    """Decompose quoted QQQ put P&L; extrinsic residual change is not pure Theta."""
    if qqq_spot_exit is None or qqq_exit_bid is None:
        return {}
    strike=float(ep["qqq_strike"])
    entry_intrinsic=max(strike-float(ep["qqq_spot_entry"]),0.0)
    exit_intrinsic=max(strike-float(qqq_spot_exit),0.0)
    entry_extrinsic=float(ep["qqq_entry_ask"])-entry_intrinsic
    exit_extrinsic=float(qqq_exit_bid)-exit_intrinsic
    qty=int(ep["long_qqq_qty"])
    result={
        "qqq_exit_intrinsic_per_share":exit_intrinsic,
        "qqq_exit_extrinsic_bid_proxy_per_share":exit_extrinsic,
        "qqq_intrinsic_pnl_usd":qty*MULTIPLIER*(exit_intrinsic-entry_intrinsic),
        "qqq_extrinsic_change_proxy_usd":qty*MULTIPLIER*(exit_extrinsic-entry_extrinsic),
        "qqq_moneyness_exit":put_moneyness(qqq_spot_exit,strike)["status"],
        "qqq_abs_delta_exit":abs(num(qrow.get("delta"))) if qrow is not None and num(qrow.get("delta")) is not None else None,
    }
    result["qqq_decomposition_check_usd"]=result["qqq_intrinsic_pnl_usd"]+result["qqq_extrinsic_change_proxy_usd"]-qty*MULTIPLIER*(float(qqq_exit_bid)-float(ep["qqq_entry_ask"]))
    return result


def update_qqq_value_path(ep,qrow,qspot,day):
    """Track daily QQQ put intrinsic value and extrinsic bid residual when quotes exist."""
    if qrow is None or qspot is None or not valid_quote(qrow): return
    strike,spot=float(ep["qqq_strike"]),float(qspot)
    intrinsic=max(strike-spot,0.0)
    extrinsic=float(qrow["bid"])-intrinsic
    ep["qqq_value_observed_sessions"]=ep.get("qqq_value_observed_sessions",0)+1
    ep["qqq_current_moneyness"]=put_moneyness(spot,strike)["status"]
    ep["qqq_current_intrinsic_per_share"]=intrinsic
    ep["qqq_current_extrinsic_bid_proxy_per_share"]=extrinsic
    delta=num(qrow.get("delta"));ep["qqq_current_abs_delta"]=abs(delta) if delta is not None else None
    if strike>spot:
        ep["qqq_itm_quote_sessions"]=ep.get("qqq_itm_quote_sessions",0)+1
        if not ep.get("qqq_first_itm_date"):
            ep["qqq_first_itm_date"]=day
            ep["qqq_first_itm_dte"]=(date.fromisoformat(ep["expiry"])-date.fromisoformat(day)).days
            ep["qqq_first_itm_extrinsic_bid_proxy_per_share"]=extrinsic
            ep["qqq_first_itm_abs_delta"]=abs(delta) if delta is not None else None
    if ep.get("qqq_first_itm_date"):
        ep["qqq_observations_since_first_itm"]=ep.get("qqq_observations_since_first_itm",0)+1
        lo=ep.get("qqq_min_extrinsic_bid_proxy_after_first_itm_per_share")
        hi=ep.get("qqq_max_extrinsic_bid_proxy_after_first_itm_per_share")
        ep["qqq_min_extrinsic_bid_proxy_after_first_itm_per_share"]=extrinsic if lo is None else min(lo,extrinsic)
        ep["qqq_max_extrinsic_bid_proxy_after_first_itm_per_share"]=extrinsic if hi is None else max(hi,extrinsic)
        ep["qqq_last_extrinsic_bid_proxy_after_first_itm_per_share"]=extrinsic


def mark_pnl(ep,qrow,srow):
    return episode_pnl(ep,float(qrow["bid"]),float(srow["ask"]),ep["base_slippage_per_share"],
        ep["base_commission_per_contract_per_side"])["net_pnl_usd"]


def update_mark_extremes(ep, mark):
    previous_favorable = ep.get("max_favorable_mark_pnl_usd")
    previous_adverse = ep.get("max_adverse_mark_pnl_usd")
    ep["max_favorable_mark_pnl_usd"] = mark if previous_favorable is None else max(previous_favorable, mark)
    ep["max_adverse_mark_pnl_usd"] = mark if previous_adverse is None else min(previous_adverse, mark)

def wilson95(wins,n):
    if n<=0:return None,None
    z=1.959963984540054;p=wins/n;den=1+z*z/n
    center=(p+z*z/(2*n))/den
    margin=z*math.sqrt((p*(1-p)+z*z/(4*n))/n)/den
    return max(0,center-margin)*100,min(1,center+margin)*100

def profit_factor(values):
    gains=sum(x for x in values if x>0);losses=-sum(x for x in values if x<0)
    if losses==0:return None if gains==0 else math.inf
    return gains/losses

def finite_round(value,digits=6):
    if value is None or not math.isfinite(value):return None
    return round(value,digits)

def policy_summary(policy,trade_rows):
    rows=[r for r in trade_rows if r["policy"]==policy]
    resolved=[r for r in rows if r.get("status")=="RESOLVED" and r.get("net_pnl_usd") is not None]
    pnl=[float(r["net_pnl_usd"]) for r in resolved]
    wins=sum(x>0.005 for x in pnl);losses=sum(x < -0.005 for x in pnl);flats=len(pnl)-wins-losses
    low,high=wilson95(wins,len(pnl)); q=[float(r["qqq_long_gross_pnl_usd"]) for r in resolved]; s=[float(r["spy_short_gross_pnl_usd"]) for r in resolved]
    pf=profit_factor(pnl)
    return {"policy":policy,"opened":len(rows),"resolved":len(resolved),
        "unresolved":sum(str(r.get("status","")).startswith("UNRESOLVED") for r in rows),
        "wins":wins,"losses":losses,"flat":flats,
        "win_rate_pct":finite_round(100*wins/len(pnl),4) if pnl else None,
        "win_rate_wilson95_low_pct":finite_round(low,4),"win_rate_wilson95_high_pct":finite_round(high,4),
        "expectancy_net_usd":finite_round(statistics.mean(pnl)) if pnl else None,
        "median_net_usd":finite_round(statistics.median(pnl)) if pnl else None,
        "total_net_pnl_usd":finite_round(sum(pnl)) if pnl else None,
        "best_net_usd":finite_round(max(pnl)) if pnl else None,"worst_net_usd":finite_round(min(pnl)) if pnl else None,
        "profit_factor":finite_round(pf) if pf is not None and math.isfinite(pf) else ("INF" if pf==math.inf else None),
        "mean_qqq_long_gross_pnl_usd":finite_round(statistics.mean(q)) if q else None,
        "mean_spy_short_gross_pnl_usd":finite_round(statistics.mean(s)) if s else None,
        "resolved_coverage_pct":finite_round(100*len(resolved)/len(rows)) if rows else None,
        "denominator_definition":"wins / resolved episodes for this policy; unresolved episodes counted separately"}

def summarize_costs(trades):
    output=[]
    for policy in POLICIES:
        rows=[r for r in trades if r.get("policy")==policy["policy"] and r.get("status")=="RESOLVED"]
        for slip in SLIPPAGE_GRID:
            for commission in COMMISSION_GRID:
                vals=[float(r["gross_pnl_usd"])-2*(int(r["long_qqq_qty"])+int(r["short_spy_qty"]))*(slip*MULTIPLIER+commission) for r in rows]
                wins=sum(x>0.005 for x in vals);lo,hi=wilson95(wins,len(vals));pf=profit_factor(vals)
                output.append({"policy":policy["policy"],"slippage_per_option_share_usd":slip,
                    "commission_per_contract_per_side_usd":commission,"resolved_n":len(vals),"wins":wins,
                    "losses":sum(x < -0.005 for x in vals),"win_rate_pct":finite_round(100*wins/len(vals),4) if vals else None,
                    "win_rate_wilson95_low_pct":finite_round(lo,4),"win_rate_wilson95_high_pct":finite_round(hi,4),
                    "expectancy_net_usd":finite_round(statistics.mean(vals)) if vals else None,
                    "total_net_pnl_usd":finite_round(sum(vals)) if vals else None,
                    "median_net_usd":finite_round(statistics.median(vals)) if vals else None,
                    "worst_net_usd":finite_round(min(vals)) if vals else None,
                    "profit_factor":finite_round(pf) if pf is not None and math.isfinite(pf) else ("INF" if pf==math.inf else None)})
    return output

def summarize_sizing_sensitivity(trades,max_long_qqq,max_short_spy,slippage,commission,max_total_contracts=None):
    """Rescale resolved per-leg gross P&L on the same selected contracts and dates."""
    output=[]
    unit_cost=slippage*MULTIPLIER+commission
    for policy_def in POLICIES:
        policy=policy_def["policy"]
        policy_rows=[r for r in trades if r.get("policy")==policy]
        resolved=[r for r in policy_rows if r.get("status")=="RESOLVED"
                  and r.get("qqq_long_gross_pnl_usd") is not None
                  and r.get("spy_short_gross_pnl_usd") is not None]
        unresolved=sum(str(r.get("status","")).startswith("UNRESOLVED") for r in policy_rows)
        for long_qty in range(1,max_long_qqq+1):
            for short_qty in range(1,max_short_spy+1):
                if max_total_contracts is not None and long_qty + short_qty > max_total_contracts:
                    continue
                pnls=[]
                for r in resolved:
                    base_long=int(r.get("long_qqq_qty") or max_long_qqq)
                    base_short=int(r.get("short_spy_qty") or max_short_spy)
                    gross=(float(r["qqq_long_gross_pnl_usd"])*long_qty/base_long
                           +float(r["spy_short_gross_pnl_usd"])*short_qty/base_short)
                    pnls.append(gross-2*(long_qty+short_qty)*unit_cost)
                wins=sum(v>0.005 for v in pnls)
                losses=sum(v < -0.005 for v in pnls)
                flats=len(pnls)-wins-losses
                low,high=wilson95(wins,len(pnls))
                pf=profit_factor(pnls)
                output.append({
                    "policy":policy,"long_qqq_contracts":long_qty,"short_spy_contracts":short_qty,
                    "opened_n":len(policy_rows),"resolved_n":len(pnls),"unresolved_n":unresolved,
                    "wins":wins,"losses":losses,"flat":flats,
                    "win_rate_pct":finite_round(100*wins/len(pnls),4) if pnls else None,
                    "win_rate_wilson95_low_pct":finite_round(low,4),
                    "win_rate_wilson95_high_pct":finite_round(high,4),
                    "expectancy_net_usd":finite_round(statistics.mean(pnls)) if pnls else None,
                    "median_net_usd":finite_round(statistics.median(pnls)) if pnls else None,
                    "total_net_pnl_usd":finite_round(sum(pnls)) if pnls else None,
                    "best_net_usd":finite_round(max(pnls)) if pnls else None,
                    "worst_net_usd":finite_round(min(pnls)) if pnls else None,
                    "profit_factor":finite_round(pf) if pf is not None and math.isfinite(pf) else ("INF" if pf==math.inf else None)
                })
    return output


def build_shock_grid(entries,long_qty=None,short_qty=None,slippage=BASE_SLIPPAGE,commission=BASE_COMMISSION):
    shocks=[-1.0,-0.75,-0.5,-0.4,-0.30,-0.25,-0.20,-0.15,-0.10,-0.05,0.0,0.05,0.10,0.20];output=[]
    unit_cost=slippage*MULTIPLIER+commission
    for qr in shocks:
        for sr in shocks:
            vals=[]
            for e in entries:
                qs,ss=num(e.get("qqq_spot_entry")),num(e.get("spy_spot_entry"))
                if qs is None or ss is None:continue
                qintr=max(float(e["qqq_strike"])-qs*(1+qr),0)
                sintr=max(float(e["spy_strike"])-ss*(1+sr),0)
                qn=int(e.get("long_qqq_qty") or long_qty or 1); sn=int(e.get("short_spy_qty") or short_qty or 1)
                cash=MULTIPLIER*(sn*float(e["spy_entry_bid"])-qn*float(e["qqq_entry_ask"]))
                # Intrinsic-value expiry payoff: charge entry-side slippage/commission once.
                # No closing trade is assumed; exercise/assignment fees are not modeled.
                entry_cost=(qn+sn)*unit_cost
                vals.append(cash+MULTIPLIER*(qn*qintr-sn*sintr)-entry_cost)
            wins=sum(v>0.005 for v in vals)
            output.append({"qqq_pct_move":round(qr*100,2),"spy_pct_move":round(sr*100,2),
                "same_pct_move_diagonal":qr==sr,"entry_cohort_n":len(vals),"positive_scenario_n":wins,
                "positive_scenario_pct":finite_round(100*wins/len(vals),4) if vals else None,
                "mean_expiry_scenario_pnl_usd":finite_round(statistics.mean(vals)) if vals else None,
                "median_expiry_scenario_pnl_usd":finite_round(statistics.median(vals)) if vals else None,
                "worst_expiry_scenario_pnl_usd":finite_round(min(vals)) if vals else None,
                "classification":"HYPOTHETICAL_EXPIRY_SHOCK_NOT_HISTORICAL_WIN_RATE"})
    return output

def write_csv(path,rows,fallback_fields=None):
    path.parent.mkdir(parents=True,exist_ok=True)
    fields=list(dict.fromkeys(k for r in rows for k in r.keys())) if rows else (fallback_fields or ["status"])
    with path.open("w",newline="",encoding="utf-8") as handle:
        writer=csv.DictWriter(handle,fieldnames=fields,extrasaction="ignore");writer.writeheader();writer.writerows(rows)

def render_markdown(report,costs,shock,sizing):
    lines=["# QQQ LONG PUT / SPY SHORT PUT — Cross-Underlying Replay V1","",
        f"Status: **{report['status']}**. EOD quote-side estimate, not confirmed fills.","",
        f"- Window requested: {report['window']['start']} to {report['window']['end']}; last QQQ/SPY chain dates: {report['coverage']['qqq_last_chain_date']} / {report['coverage']['spy_last_chain_date']}.",
        f"- Entry filter: {report['entry_filter']['name']} — {report['entry_filter']['description']}.",
        f"- Filter evaluation: {report['entry_filter']['evaluated_sessions']} checks; {report['entry_filter']['qualified_sessions']} qualified; {report['entry_filter']['rejected_sessions']} rejected (includes insufficient lookback).",
        f"- Position sizing: {report['ratio']['description']}; max total contracts = {report['ratio']['max_total_contracts']}.",
        f"- Selection: same expiry; DTE {report['selection']['dte_min']}–{report['selection']['dte_max']} (target {report['selection']['dte_target']}); each leg absolute-Delta target {report['selection']['target_abs_delta']:.2f}.",
        f"- Base costs: slippage USD {report['costs']['base_slippage_per_option_share_usd']:.3f}/option-share/side; USD {report['costs']['base_commission_per_contract_per_side_usd']:.2f}/contract/side.",
        (f"- Mean actual entry premium debit/credit: USD {report['premium_matching']['mean_qqq_premium_debit_usd']:,.2f} / USD {report['premium_matching']['mean_spy_premium_credit_usd']:,.2f}; mean absolute mismatch USD {report['premium_matching']['mean_abs_mismatch_usd']:,.2f}; mean match score {report['premium_matching']['mean_match_pct']:.2f}%." if report["premium_matching"]["cohort_n"] else "- No valid entry cohorts; premium cash-flow statistics are unavailable."),
        f"- Actual selected contract ratios: {report['premium_matching']['ratio_counts']}.",
        "","## Coverage and source integrity","",
        f"- Common underlying sessions: {report['coverage']['common_underlying_sessions']}; QQQ chain dates with puts: {report['coverage']['qqq_chain_dates']}; SPY chain dates with puts: {report['coverage']['spy_chain_dates']}; sessions with both chains: {report['coverage']['sessions_with_both_chains']}.",
        f"- Selected signals: {report['cohort']['selected_signals']}; entered cohorts: {report['cohort']['entered_cohorts']}; skipped entries: {report['cohort']['entry_skipped']}.",
        "- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.",
        "","## Historical win rate — base assumed costs","","| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    fmt=lambda v:"—" if v is None else f"USD {v:,.2f}"
    for p in report["policies"].values():
        rate="—" if p["win_rate_pct"] is None else f"{p['win_rate_pct']:.2f}% ({p['win_rate_wilson95_low_pct']:.2f}–{p['win_rate_wilson95_high_pct']:.2f}%)"
        lines.append(f"| {p['policy']} | {p['resolved']}/{p['opened']} | {p['wins']}/{p['losses']}/{p['flat']} | {rate} | {fmt(p['expectancy_net_usd'])} | {fmt(p['median_net_usd'])} | {fmt(p['total_net_pnl_usd'])} | {fmt(p['worst_net_usd'])} | {p['unresolved']} |")
    lines += ["","Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.",
        "","## Leg attribution","","| Exit rule | Mean gross QQQ LONG PUT P&L | Mean gross SPY SHORT PUT P&L |","|---|---:|---:|"]
    for p in report["policies"].values():
        lines.append(f"| {p['policy']} | {fmt(p['mean_qqq_long_gross_pnl_usd'])} | {fmt(p['mean_spy_short_gross_pnl_usd'])} |")
    lines += ["","## Cost sensitivity","","| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |","|---|---:|---:|---:|---:|---:|---:|---:|"]
    for r in costs:
        rate="—" if r["win_rate_pct"] is None else f"{r['win_rate_pct']:.2f}%"
        lines.append(f"| {r['policy']} | {r['slippage_per_option_share_usd']:.3f} | {r['commission_per_contract_per_side_usd']:.2f} | {r['resolved_n']} | {rate} | {fmt(r['expectancy_net_usd'])} | {fmt(r['total_net_pnl_usd'])} | {fmt(r['worst_net_usd'])} |")
    size_meta=report["position_size_sensitivity"]
    cap=size_meta["max_total_contracts"]
    qsample=min(size_meta["max_long_qqq_contracts"],max(1,cap//2))
    ssample=min(size_meta["max_short_spy_contracts"],max(1,cap-qsample))
    size_pairs=list(dict.fromkeys([(1,1),(1,min(size_meta["max_short_spy_contracts"],cap-1)),
        (min(size_meta["max_long_qqq_contracts"],cap-1),1),(qsample,ssample)]))
    lines += ["","## Position-size sensitivity (reference grid; not the premium-matched policy)","",
        f"- Grid: LONG QQQ 1–{size_meta['max_long_qqq_contracts']} × SHORT SPY 1–{size_meta['max_short_spy_contracts']} contracts, with combined count capped at {size_meta['max_total_contracts']}; CSV contains valid combinations only.",
        "- This is a fixed-sample rescaling of each leg's gross P&L on the same selected contracts and dates, not a fresh contract-selection replay. Transaction costs scale per contract; size-dependent market impact is not modeled.",
        "- Fixed-ratio rows are rescaled counterfactuals, not fresh entries or verified quote-depth executions; they may exceed a cohort’s actual displayed size, and inherit unresolved status from the variable-ratio base path.",
        "- P&L statistics use resolved episodes only; unresolved counts are shown separately.","",
        "| Exit rule | QQQ LONG : SPY SHORT | Resolved/opened (unresolved) | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Total net P&L (resolved) | Worst trade (resolved) |",
        "|---|---:|---:|---:|---:|---:|---:|"]
    for p in report["policies"].values():
        for long_qty,short_qty in size_pairs:
            row=next((x for x in sizing if x["policy"]==p["policy"]
                and x["long_qqq_contracts"]==long_qty and x["short_spy_contracts"]==short_qty),None)
            if row is None: continue
            rate="—" if row["win_rate_pct"] is None else f"{row['win_rate_pct']:.2f}% ({row['win_rate_wilson95_low_pct']:.2f}–{row['win_rate_wilson95_high_pct']:.2f}%)"
            lines.append(f"| {row['policy']} | {long_qty} : {short_qty} | {row['resolved_n']}/{row['opened_n']} ({row['unresolved_n']}) | {rate} | {fmt(row['expectancy_net_usd'])} | {fmt(row['total_net_pnl_usd'])} | {fmt(row['worst_net_usd'])} |")
    lines += ["","The CSV contains every size combination in the grid. The 1:5 and configured 4:5 comparisons share the same selected historical episodes; they are not evidence that any ratio is profitable.",""]
    lines += ["","## Equal-percentage QQQ/SPY expiry shocks (hypothetical)","","These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.",
        "Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff.",
        "Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.","",
        "| Same move on both ETFs | Positive scenarios / cohort N | Positive scenario % | Mean expiry P&L | Worst expiry P&L |","|---:|---:|---:|---:|---:|"]
    for r in [x for x in shock if x["same_pct_move_diagonal"]]:
        rate="—" if r["positive_scenario_pct"] is None else f"{r['positive_scenario_pct']:.2f}%"
        lines.append(f"| {r['qqq_pct_move']:.0f}% | {r['positive_scenario_n']}/{r['entry_cohort_n']} | {rate} | {fmt(r['mean_expiry_scenario_pnl_usd'])} | {fmt(r['worst_expiry_scenario_pnl_usd'])} |")
    lines += ["","## Limitations",""]
    lines.extend(f"- {x}" for x in report["limitations"])
    lines += ["","Files: trade_episodes.csv, entry_cohort.csv, entry_skips.csv, cost_sensitivity.csv, sizing_sensitivity.csv, expiry_shock_grid.csv, source_manifest.json."]
    return "\n".join(lines)

def run_replay(args):
    start_day,end_day=args.start,args.end
    if date.fromisoformat(start_day)>date.fromisoformat(end_day):raise ValueError("--start must be <= --end")
    if args.max_total_contracts < 2 or args.max_total_contracts > 20:raise ValueError("--max-total-contracts must be between 2 and 20")
    if args.entry_filter not in ("none", "qqq_underperforms_spy_20d", "spy_weekly_drop_2pct_corr60_pos"):raise ValueError("unsupported entry filter")
    if args.sizing_mode not in ("equal_premium", "fixed_ratio"):raise ValueError("unsupported sizing mode")
    if args.sizing_mode == "fixed_ratio":
        if args.fixed_long_qty < 1 or args.fixed_short_qty < 1:
            raise ValueError("fixed ratio quantities must be positive")
        if args.fixed_long_qty + args.fixed_short_qty > args.max_total_contracts:
            raise ValueError("fixed ratio total contract count exceeds --max-total-contracts")
    if not 0<args.target_delta<1 or args.dte_min<1 or args.dte_max<args.dte_min:raise ValueError("invalid Delta/DTE bounds")
    if args.qqq_premium_match_short_qty is not None and args.qqq_premium_match_short_qty < 1:
        raise ValueError("--qqq-premium-match-short-qty must be positive")
    if args.qqq_reference_premium_fraction is not None:
        if not 0 < args.qqq_reference_premium_fraction < 1:
            raise ValueError("--qqq-reference-premium-fraction must be between 0 and 1")
        if args.sizing_mode != "fixed_ratio" or args.fixed_long_qty < 2:
            raise ValueError("--qqq-reference-premium-fraction requires fixed-ratio sizing with at least 2 QQQ long contracts")
        if args.qqq_target_abs_delta is None:
            raise ValueError("--qqq-reference-premium-fraction requires --qqq-target-abs-delta to define the reference contract")
    if args.qqq_target_abs_delta is not None:
        if not 0 < args.qqq_target_abs_delta < 1:
            raise ValueError("--qqq-target-abs-delta must be between 0 and 1")
        if args.qqq_delta_tolerance < 0 or args.qqq_target_abs_delta-args.qqq_delta_tolerance < 0 or args.qqq_target_abs_delta+args.qqq_delta_tolerance > 1:
            raise ValueError("--qqq-delta-tolerance must keep the QQQ Delta band between 0 and 1")
    if not DELTA_MIN<=args.target_delta<=DELTA_MAX:raise ValueError("target Delta must be within 0.10–0.50")
    if args.cohort_stride_sessions<1 or args.slippage_per_share<0 or args.commission_per_contract_per_side<0:raise ValueError("invalid cohort stride or costs")
    if args.initial_phase_sessions<0 or args.initial_phase_sessions>=args.cohort_stride_sessions:raise ValueError("initial phase must be within [0, cohort stride)")
    qcache,scache=Path(args.qqq_cache),Path(args.spy_cache);integrity=[];qpaths=[];spaths=[]
    years=[y for y in YEARS if int(start_day[:4])<=y<=int(end_day[:4])]
    for symbol,cache,paths in (("QQQ",qcache,qpaths),("SPY",scache,spaths)):
        for year in years:
            path,meta=download_verified(symbol,year,cache);paths.append(path);integrity.append(meta)
    qu,qmeta=download_verified("QQQ",None,qcache);su,smeta=download_verified("SPY",None,scache);integrity.extend([qmeta,smeta])
    qspots,sspots=load_spots(qu, 'QQQ'),load_spots(su, 'SPY')
    dates=sorted(d for d in set(qspots)&set(sspots) if start_day<=d<=end_day)
    if not dates:raise ValueError("No common QQQ/SPY underlying sessions in the requested date range")
    qs={"chain_dates":0,"put_rows":0,"last_chain_date":None};ss={"chain_dates":0,"put_rows":0,"last_chain_date":None}
    qi=iter_symbol_days(qpaths,"QQQ",start_day,end_day,qs);si=iter_symbol_days(spaths,"SPY",start_day,end_day,ss)
    qitem,sitem=next(qi,None),next(si,None)
    active=[];trades=[];entries=[];skips=[];schedule_skips=[];pending=None;signal_count=entered_count=both_chains=scheduled_opportunities=0
    scheduled_indices=set(fixed_schedule_indices(len(dates),args.initial_phase_sessions,args.cohort_stride_sessions))
    filter_evaluations=filter_qualified=filter_rejected=0
    for idx,day in enumerate(dates):
        while qitem is not None and qitem[0]<day:qitem=next(qi,None)
        while sitem is not None and sitem[0]<day:sitem=next(si,None)
        qrows=qitem[1] if qitem is not None and qitem[0]==day else []
        srows=sitem[1] if sitem is not None and sitem[0]==day else []
        if qitem is not None and qitem[0]==day:qitem=next(qi,None)
        if sitem is not None and sitem[0]==day:sitem=next(si,None)
        if qrows and srows:both_chains+=1
        qmap,smap=rows_by_id(qrows),rows_by_id(srows);remaining=[]
        for ep in active:
            ep["age_sessions"]=idx-ep["entry_index"]
            qrow,srow=qmap.get(ep["qqq_contract_id"]),smap.get(ep["spy_contract_id"])
            update_qqq_value_path(ep,qrow,qspots.get(day),day)
            if ep["pending_exit"]:
                valid,reason=exit_quotes_valid(qrow,srow,ep["long_qqq_qty"],ep["short_spy_qty"])
                if valid:
                    vals=episode_pnl(ep,float(qrow["bid"]),float(srow["ask"]),args.slippage_per_share,args.commission_per_contract_per_side)
                    qspot,sspot=qspots.get(day),sspots.get(day);ep.update(vals)
                    ep.update(qqq_value_decomposition(ep,float(qrow["bid"]),qspot,qrow))
                    ep.update({"status":"RESOLVED","exit_date":day,"exit_qqq_bid":float(qrow["bid"]),"exit_spy_ask":float(srow["ask"]),
                        "exit_delay_sessions":idx-ep["exit_signal_index"],"exit_quote_status":"VALID_SIZED_SIDE_QUOTES",
                        "qqq_return_pct":finite_round((qspot/ep["qqq_spot_entry"]-1)*100) if qspot else None,
                        "spy_return_pct":finite_round((sspot/ep["spy_spot_entry"]-1)*100) if sspot else None})
                    trades.append(ep);continue
                ep["exit_deferred_sessions"]+=1
                if day>=ep["expiry"]:
                    ep.update({"status":"UNRESOLVED_EXPIRED_NO_EXECUTABLE_CLOSE","exit_date":None,"unresolved_reason":reason,"last_observed_date":day})
                    trades.append(ep);continue
                remaining.append(ep);continue
            if valid_quote(qrow) and valid_quote(srow):
                mark=mark_pnl(ep,qrow,srow);ep["valid_mark_sessions"]+=1;ep["last_mark_pnl_usd"]=mark
                update_mark_extremes(ep, mark)
            else:ep["missing_mark_sessions"]+=1
            if day>=ep["expiry"]:
                ep.update({"status":"UNRESOLVED_EXPIRED_NO_EXIT","exit_date":None,"unresolved_reason":"EXPIRY_REACHED_BEFORE_EXECUTABLE_EXIT","last_observed_date":day})
                trades.append(ep);continue
            policy=next(p for p in POLICIES if p["policy"]==ep["policy"])
            dte=(date.fromisoformat(ep["expiry"])-date.fromisoformat(day)).days
            if policy["policy"] == "HOLD_20_OR_DTE_LE_7":
                trigger=(ep["age_sessions"]>=20 or dte<=7)
            else:
                trigger=ep["age_sessions"]>=policy["hold_sessions"] if policy["hold_sessions"] is not None else dte<=7
            if trigger:
                ep["pending_exit"]=True;ep["exit_signal_date"]=day;ep["exit_signal_index"]=idx
                if policy["policy"] == "HOLD_20_OR_DTE_LE_7":
                    ep["exit_reason"]="HOLD_20_OR_DTE_LE_7"
                else:
                    ep["exit_reason"]=f"HOLD_{policy['hold_sessions']}_SESSIONS" if policy["hold_sessions"] is not None else "DTE_LE_7"
            remaining.append(ep)
        active=remaining
        if pending is not None:
            qrow,srow=qmap.get(pending["qqq_contract_id"]),smap.get(pending["spy_contract_id"])
            quantities=None
            valid,reason=False,"EXACT_SELECTED_CONTRACT_MISSING"
            if (qrow is not None and srow is not None
                    and valid_quote(qrow,require_positive_bid=True)
                    and valid_quote(srow,require_positive_bid=True)):
                if args.sizing_mode == "equal_premium":
                    quantities=choose_equal_premium_quantities(
                        float(qrow["ask"]),float(srow["bid"]),args.max_total_contracts,
                        displayed_size(qrow,"ask"),displayed_size(srow,"bid"))
                else:
                    quantities=choose_fixed_ratio_quantities(
                        float(qrow["ask"]),float(srow["bid"]),args.fixed_long_qty,
                        args.fixed_short_qty,args.max_total_contracts)
                if quantities is None:
                    valid,reason=False,("NO_SIZED_EQUAL_PREMIUM_CONTRACT_PAIR" if args.sizing_mode == "equal_premium" else "INVALID_FIXED_RATIO_OR_ENTRY_PRICE")
                else:
                    long_qty,short_qty=quantities["long_qqq_qty"],quantities["short_spy_qty"]
                    valid,reason=entry_quotes_valid(qrow,srow,long_qty,short_qty)
            if valid:
                qspot,sspot=qspots.get(day),sspots.get(day)
                if qspot is None or sspot is None:valid,reason=False,"ENTRY_UNDERLYING_CLOSE_MISSING"
                else:
                    long_qty,short_qty=quantities["long_qqq_qty"],quantities["short_spy_qty"]
                    qentry=put_moneyness(qspot,pending["qqq_strike"])
                    sentry=put_moneyness(sspot,pending["spy_strike"])
                    qqq_entry_intrinsic=max(float(pending["qqq_strike"])-float(qspot),0.0)
                    qqq_entry_extrinsic_ask_proxy=float(qrow["ask"])-qqq_entry_intrinsic
                    qqq_entry_delta=num(qrow.get("delta"))
                    entry_cash=MULTIPLIER*(short_qty*float(srow["bid"])-long_qty*float(qrow["ask"]))
                    entry_cost=(long_qty+short_qty)*(args.slippage_per_share*MULTIPLIER+args.commission_per_contract_per_side)
                    base={**pending,**quantities,"entry_date":day,"entry_index":idx,
                        "qqq_entry_ask":float(qrow["ask"]),"qqq_entry_bid":float(qrow["bid"]),
                        "spy_entry_bid":float(srow["bid"]),"spy_entry_ask":float(srow["ask"]),
                        "qqq_spot_entry":qspot,"spy_spot_entry":sspot,
                        "qqq_abs_delta_entry":abs(qqq_entry_delta) if qqq_entry_delta is not None else None,
                        "qqq_entry_intrinsic_per_share":qqq_entry_intrinsic,
                        "qqq_entry_extrinsic_ask_proxy_per_share":qqq_entry_extrinsic_ask_proxy,
                        "qqq_value_observed_sessions":0,"qqq_itm_quote_sessions":0,
                        "qqq_first_itm_date":None,"qqq_first_itm_dte":None,
                        "qqq_first_itm_extrinsic_bid_proxy_per_share":None,"qqq_first_itm_abs_delta":None,
                        "qqq_observations_since_first_itm":0,
                        "qqq_min_extrinsic_bid_proxy_after_first_itm_per_share":None,
                        "qqq_max_extrinsic_bid_proxy_after_first_itm_per_share":None,
                        "qqq_last_extrinsic_bid_proxy_after_first_itm_per_share":None,
                        "qqq_otm_pct_entry":qentry["otm_pct"],"qqq_moneyness_entry":qentry["status"],
                        "spy_otm_pct_entry":sentry["otm_pct"],"spy_moneyness_entry":sentry["status"],
                        "spy_put_strike_assignment_obligation_usd":float(pending["spy_strike"])*MULTIPLIER*short_qty,
                        "entry_net_credit_before_cost_usd":entry_cash,
                        "entry_cash_after_entry_cost_usd":entry_cash-entry_cost,"base_slippage_per_share":args.slippage_per_share,
                        "base_commission_per_contract_per_side":args.commission_per_contract_per_side,
                        "entry_delay_sessions":idx-pending["signal_index"]}
                    entries.append(dict(base));entered_count+=1
                    for p in POLICIES:
                        active.append({**base,"policy":p["policy"],"status":"OPEN","pending_exit":False,
                            "exit_signal_date":None,"exit_signal_index":None,"exit_reason":None,"exit_deferred_sessions":0,
                            "missing_mark_sessions":0,"valid_mark_sessions":0,"last_mark_pnl_usd":None,
                            "max_favorable_mark_pnl_usd":None,"max_adverse_mark_pnl_usd":None})
            if not valid:
                pending["entry_defer_sessions"]+=1
                if day>=pending["expiry"]:
                    skips.append({"episode_id":pending["episode_id"],"signal_date":pending["signal_date"],"signal_index":pending["signal_index"],"status":"ENTRY_SKIPPED",
                        "reason":"NO_VALID_ENTRY_BEFORE_EXPIRY","last_attempt_date":day,"last_quote_reason":reason,
                        "entry_defer_sessions":pending["entry_defer_sessions"]});pending=None
            else:pending=None
        if idx in scheduled_indices:
            scheduled_opportunities+=1
            slot={"scheduled_index":idx,"scheduled_signal_date":day,"status":"SCHEDULE_SKIPPED"}
            if pending is not None:
                schedule_skips.append({**slot,"reason":"PRIOR_ENTRY_PENDING"})
            elif not entry_gate_open(active,args.allow_overlapping_cohorts):
                schedule_skips.append({**slot,"reason":"ACTIVE_COHORT_GATE_CLOSED"})
            elif not qrows or not srows:
                missing=("QQQ" if not qrows else "") + ("_AND_" if not qrows and not srows else "") + ("SPY" if not srows else "")
                schedule_skips.append({**slot,"reason":"MISSING_"+missing+"_OPTION_CHAIN"})
            elif qspots.get(day) is None or sspots.get(day) is None:
                schedule_skips.append({**slot,"reason":"MISSING_UNDERLYING_CLOSE"})
            else:
                qspot,sspot=qspots[day],sspots[day]
                filter_pass,filter_metrics=evaluate_entry_filter(args.entry_filter,idx,dates,qspots,sspots)
                filter_evaluations+=1
                if filter_pass:
                    filter_qualified+=1
                    if args.qqq_premium_match_short_qty is None:
                        pair=choose_pair(qrows,srows,day,qspot,sspot,args.target_delta,args.dte_min,args.dte_max,args.dte_target)
                    else:
                        pair=choose_pair_by_premium(qrows,srows,day,qspot,sspot,args.target_delta,args.dte_min,args.dte_max,args.dte_target,args.qqq_premium_match_short_qty,args.qqq_target_abs_delta,args.qqq_delta_tolerance,args.qqq_reference_premium_fraction,(args.fixed_long_qty if args.sizing_mode == "fixed_ratio" else 1))
                    if pair is not None:
                        signal_count+=1
                        pending={**pair,**filter_metrics,"episode_id":signal_count,"signal_index":idx,"entry_defer_sessions":0}
                    else:
                        schedule_skips.append({**slot,"reason":"NO_ELIGIBLE_COMMON_EXPIRY_PAIR"})
                else:
                    filter_rejected+=1
                    schedule_skips.append({**slot,"reason":"ENTRY_FILTER_REJECTED"})
    if pending is not None:
        skips.append({"episode_id":pending["episode_id"],"signal_date":pending["signal_date"],"signal_index":pending["signal_index"],"status":"ENTRY_SKIPPED",
            "reason":"SOURCE_END_BEFORE_VALID_ENTRY","last_attempt_date":dates[-1],"last_quote_reason":"NO_LATER_SOURCE_DATE",
            "entry_defer_sessions":pending["entry_defer_sessions"]})
    for ep in active:
        ep.update({"status":"UNRESOLVED_SOURCE_END","exit_date":None,"unresolved_reason":"SOURCE_END_BEFORE_EXECUTABLE_EXIT","last_observed_date":dates[-1]})
        trades.append(ep)
    for r in trades:r["base_cost_win"]=r["net_pnl_usd"]>0.005 if r.get("status")=="RESOLVED" and r.get("net_pnl_usd") is not None else None
    policies={p["policy"]:policy_summary(p["policy"],trades) for p in POLICIES}
    schedule_reason_counts={}
    for row in schedule_skips:schedule_reason_counts[row["reason"]]=schedule_reason_counts.get(row["reason"],0)+1
    costs=summarize_costs(trades);shock=build_shock_grid(entries,None,None,args.slippage_per_share,args.commission_per_contract_per_side)
    size_max_qqq=min(args.max_total_contracts-1,6);size_max_spy=min(args.max_total_contracts-1,6)
    sizing=summarize_sizing_sensitivity(trades,size_max_qqq,size_max_spy,args.slippage_per_share,args.commission_per_contract_per_side,args.max_total_contracts)
    premium_summary=summarize_premium_matching(entries)
    report={"schema":"qqq-spy-fixed-anchor-put-replay.v1",
        "status":"COMPLETED_WITH_UNRESOLVEDS" if any(p["unresolved"] for p in policies.values()) or skips else "COMPLETED",
        "source":{"repository":SOURCE_REPO,"tree_commit":SOURCE_COMMIT},"window":{"start":start_day,"end":end_day},
        "ratio":{
            "method":"PER_COHORT_EQUAL_PREMIUM" if args.sizing_mode == "equal_premium" else "FIXED_RATIO_SIZE_GATED",
            "description":(
                "match LONG QQQ PUT premium debit to SHORT SPY PUT premium credit per cohort; whole-contract ratio varies by entry"
                if args.sizing_mode == "equal_premium"
                else f"fixed QQQ LONG PUT {args.fixed_long_qty} : SPY SHORT PUT {args.fixed_short_qty}; entry and exit require displayed side size for every contract"
            ),
            "fixed_long_qqq_contracts":args.fixed_long_qty if args.sizing_mode == "fixed_ratio" else None,
            "fixed_short_spy_contracts":args.fixed_short_qty if args.sizing_mode == "fixed_ratio" else None,
            "max_total_contracts":args.max_total_contracts,"contract_multiplier":MULTIPLIER,
            "mean_spy_put_assignment_obligation_usd":finite_round(statistics.mean(
                [float(e["spy_strike"])*MULTIPLIER*int(e["short_spy_qty"]) for e in entries]
            ),2) if entries else None,
        },
        "premium_matching":premium_summary,
        "entry_filter":{"name":args.entry_filter,
            "description":("No filter; entry when standard contract selection is available" if args.entry_filter=="none" else ("SPY rolling 5-session return crosses from above -2% to <= -2%, with positive Pearson correlation over the prior 60 daily returns; entry no earlier than next observed common session" if args.entry_filter=="spy_weekly_drop_2pct_corr60_pos" else "Require QQQ trailing 20-session close-to-close return to be lower than SPY; evaluated at signal close, entry no earlier than next observed common session")),
            "lookback_sessions":0 if args.entry_filter=="none" else (5 if args.entry_filter=="spy_weekly_drop_2pct_corr60_pos" else 20),
            "evaluated_sessions":filter_evaluations,"qualified_sessions":filter_qualified,
            "rejected_sessions":filter_rejected},
        "selection":{"target_abs_delta":args.target_delta,"delta_eligible_band":[DELTA_MIN,DELTA_MAX],
            "qqq_premium_match_short_qty":args.qqq_premium_match_short_qty,
            "qqq_target_abs_delta":args.qqq_target_abs_delta,
            "qqq_delta_tolerance":args.qqq_delta_tolerance if args.qqq_target_abs_delta is not None else None,
            "qqq_reference_premium_fraction":args.qqq_reference_premium_fraction,
            "qqq_delta_band":[args.qqq_target_abs_delta-args.qqq_delta_tolerance,args.qqq_target_abs_delta+args.qqq_delta_tolerance] if args.qqq_target_abs_delta is not None else None,
            "qqq_premium_match_rule":(
                (f"Reference QQQ abs-Delta {args.qqq_target_abs_delta:.2f} +/- {args.qqq_delta_tolerance:.2f}; reference Ask nearest {args.qqq_premium_match_short_qty}x SPY Bid; selected same-expiry QQQ Ask nearest {args.qqq_reference_premium_fraction:.0%} of reference QQQ Ask; selected contract Delta unconstrained"
                 if args.qqq_premium_match_short_qty is not None and args.qqq_target_abs_delta is not None
                 else "Select same-expiry QQQ Ask nearest fraction of the selected reference QQQ Ask; selected contract Delta unconstrained")
                if args.qqq_reference_premium_fraction is not None
                else (f"QQQ abs-Delta constrained to {args.qqq_target_abs_delta:.2f} +/- {args.qqq_delta_tolerance:.2f}; in-band Ask nearest N x SPY Bid"
                    if args.qqq_premium_match_short_qty is not None and args.qqq_target_abs_delta is not None
                    else ("QQQ Ask nearest N x selected SPY short-put Bid; QQQ Delta unconstrained" if args.qqq_premium_match_short_qty is not None else "QQQ Delta nearest target"))
            ),
            "dte_min":args.dte_min,
            "dte_max":args.dte_max,"dte_target":args.dte_target,"cohort_stride_sessions":args.cohort_stride_sessions,
            "allow_overlapping_cohorts":args.allow_overlapping_cohorts,"initial_phase_sessions":args.initial_phase_sessions,
            "schedule_mode":"FIXED_ANCHOR_NO_REANCHOR","common_expiry_required":True},
        "costs":{"base_slippage_per_option_share_usd":args.slippage_per_share,"base_commission_per_contract_per_side_usd":args.commission_per_contract_per_side,
            "alternative_slippage_per_option_share_usd":list(SLIPPAGE_GRID),"alternative_commission_per_contract_per_side_usd":list(COMMISSION_GRID)},
        "position_size_sensitivity":{"max_long_qqq_contracts":size_max_qqq,"max_short_spy_contracts":size_max_spy,"max_total_contracts":args.max_total_contracts,
            "method":"fixed-ratio per-leg gross-P&L rescaling on the same selected contracts, quote dates and resolved cohort set; ratio sensitivity is not a fresh premium-matched selection replay; total contracts capped in displayed grid; no size-dependent market impact"},
        "coverage":{"common_underlying_sessions":len(dates),"qqq_chain_dates":qs["chain_dates"],"qqq_put_rows":qs["put_rows"],
            "spy_chain_dates":ss["chain_dates"],"spy_put_rows":ss["put_rows"],"sessions_with_both_chains":both_chains,
            "qqq_last_chain_date":qs["last_chain_date"],"spy_last_chain_date":ss["last_chain_date"],
            "qqq_underlying_first_date":min(qspots) if qspots else None,"qqq_underlying_last_date":max(qspots) if qspots else None,
            "spy_underlying_first_date":min(sspots) if sspots else None,"spy_underlying_last_date":max(sspots) if sspots else None,
            "expected_common_first_date":dates[0],"expected_common_last_date":dates[-1]},
        "cohort":{"selected_signals":signal_count,"entered_cohorts":entered_count,"entry_skipped":len(skips),"entry_skip_rows":skips},
        "fixed_entry_schedule":{"mode":"FIXED_ANCHOR_NO_REANCHOR","phase_sessions":args.initial_phase_sessions,
            "stride_sessions":args.cohort_stride_sessions,"scheduled_opportunities":scheduled_opportunities,
            "selected_signals":signal_count,"skipped_opportunities":len(schedule_skips),
            "skip_reason_counts":schedule_reason_counts,"skip_rows":schedule_skips},
        "policies":policies,"limitations":[
            "Public EOD preservation mirror; hashes establish file identity, not exchange or OPRA authenticity.",
            "EOD quotes are not verified fills; displayed size is a screening gate, not guaranteed multi-leg execution.",
            "Conservative sides: QQQ LONG enters Ask/exits Bid; SPY SHORT enters Bid/exits Ask.",
            "Missing exit quotes/size at expiry or source end remain unresolved; win-rate denominator is resolved episodes only.",
            "Option chain source ends in 2025; no 2026 performance is observed here.",
            "Nominal Wilson interval does not correct for regime clustering, dependence, or prior strategy selection.",
            "Expiry shock grid charges entry-side slippage/commission once and uses intrinsic-value payoff; exercise/assignment fees, broker margin, forced liquidation, financing and interim path are not modeled.",
            "Equal premium debit/credit does not equalize Delta, max loss, collateral or assignment risk; SPY short put can dominate downside even when QQQ long put appreciates.",
            "Fixed-cohort replay does not model portfolio compounding, taxes, financing, or verified fills.",
            "When overlapping cohorts are enabled, multiple fixed-size trades can be open at once; total portfolio cash, margin, forced liquidation, and stacked assignment obligations are not constrained by this replay."],
        "source_integrity":integrity}
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    write_csv(out/"entry_cohort.csv",entries,[
        "episode_id","signal_index","entry_index","signal_date","entry_date","expiry","signal_dte",
        "qqq_contract_id","spy_contract_id","qqq_strike","spy_strike",
        "qqq_spot_signal","spy_spot_signal","qqq_spot_entry","spy_spot_entry",
        "qqq_abs_delta","spy_abs_delta","qqq_signal_ask","qqq_target_ask_signal",
        "qqq_premium_match_short_qty","qqq_premium_match_error_signal","spy_signal_bid",
        "qqq_otm_pct_signal","qqq_moneyness_signal","spy_otm_pct_signal","spy_moneyness_signal",
        "qqq_otm_pct_entry","qqq_moneyness_entry","spy_otm_pct_entry","spy_moneyness_entry",
        "entry_filter","qqq_trailing_return_pct","spy_trailing_return_pct","spy_previous_trailing_return_pct","qqq_spy_corr_60d","filter_pass_reason","qqq_minus_spy_trailing_return_pct","long_qqq_qty","short_spy_qty","premium_match_pct"])
    write_csv(out/"trade_episodes.csv",trades,["episode_id","policy","status","net_pnl_usd"])
    write_csv(out/"entry_skips.csv",skips,["episode_id","signal_date","signal_index","status","reason"])
    write_csv(out/"scheduled_signal_skips.csv",schedule_skips,["scheduled_index","scheduled_signal_date","status","reason"])
    write_csv(out/"cost_sensitivity.csv",costs);write_csv(out/"expiry_shock_grid.csv",shock)
    write_csv(out/"sizing_sensitivity.csv",sizing)
    (out/"source_manifest.json").write_text(json.dumps({
        "source_repository":SOURCE_REPO,"source_tree_commit":SOURCE_COMMIT,
        "source_integrity":integrity,"source_window":report["window"],
        "sizing_mode":args.sizing_mode,
        "fixed_ratio":{"qqq_long_put_contracts":args.fixed_long_qty,"spy_short_put_contracts":args.fixed_short_qty} if args.sizing_mode == "fixed_ratio" else None,
        "entry_filter":args.entry_filter,
        "cohort_stride_sessions":args.cohort_stride_sessions,
        "qqq_premium_match_short_qty":args.qqq_premium_match_short_qty,
        "qqq_target_abs_delta":args.qqq_target_abs_delta,
        "qqq_delta_tolerance":args.qqq_delta_tolerance if args.qqq_target_abs_delta is not None else None,
        "qqq_reference_premium_fraction":args.qqq_reference_premium_fraction,
        "qqq_delta_band":[args.qqq_target_abs_delta-args.qqq_delta_tolerance,args.qqq_target_abs_delta+args.qqq_delta_tolerance] if args.qqq_target_abs_delta is not None else None,
        "qqq_premium_match_rule":"QQQ LONG PUT Ask nearest 6x SPY SHORT PUT Bid within QQQ abs-Delta 0.60–0.70 candidates" if args.qqq_target_abs_delta is not None and args.qqq_premium_match_short_qty==6 else "QQQ LONG PUT Ask nearest N x SPY SHORT PUT Bid at signal date",
        "initial_phase_sessions":args.initial_phase_sessions,
        "schedule_mode":"FIXED_ANCHOR_NO_REANCHOR","scheduled_opportunities":scheduled_opportunities,
        "selected_signals":signal_count,"skipped_schedule_opportunities":len(schedule_skips),
        "allow_overlapping_cohorts":args.allow_overlapping_cohorts,
        "actual_entry_and_exit_side_size_gate":"enforced by entry_quotes_valid and exit_quotes_valid; inability to enter is deferred to same selected contract until expiry, inability to exit remains deferred/unresolved",
        "known_limitations":["EOD quotes are not confirmed fills","reported fixed-ratio sizing sensitivity is still a counterfactual for alternate ratios","fixed ratios were identified after inspecting in-sample sensitivity and require prospective/out-of-sample confirmation"]
    },indent=2),encoding="utf-8")
    (out/"summary.json").write_text(json.dumps(report,indent=2,allow_nan=False),encoding="utf-8")
    (out/"summary.md").write_text(render_markdown(report,costs,shock,sizing),encoding="utf-8")
    return report

def entry_gate_open(active: list[dict[str, Any]], allow_overlapping_cohorts: bool) -> bool:
    """Allow a new cohort when overlap is enabled, otherwise serialize cohorts."""
    return allow_overlapping_cohorts or not active


def fixed_schedule_indices(session_count: int, initial_phase: int, stride: int) -> range:
    """Return immutable session indices for a fixed cadence; missing signals never move later slots."""
    if stride < 1:
        raise ValueError("stride must be positive")
    if initial_phase < 0 or initial_phase >= stride:
        raise ValueError("initial phase must be within [0, stride)")
    if session_count < 0:
        raise ValueError("session count must be non-negative")
    return range(initial_phase, session_count, stride)


def parse_args():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--start",default=START_DEFAULT);p.add_argument("--end",default=END_DEFAULT)
    p.add_argument("--max-total-contracts",type=int,default=9,help="maximum combined whole option contracts per entry cohort")
    p.add_argument("--entry-filter",choices=("none","qqq_underperforms_spy_20d","spy_weekly_drop_2pct_corr60_pos"),default="qqq_underperforms_spy_20d")
    p.add_argument("--sizing-mode",choices=("equal_premium","fixed_ratio"),default="equal_premium")
    p.add_argument("--fixed-long-qty",type=int,default=1,help="fixed QQQ LONG PUT contracts when --sizing-mode=fixed_ratio")
    p.add_argument("--fixed-short-qty",type=int,default=6,help="fixed SPY SHORT PUT contracts when --sizing-mode=fixed_ratio")
    p.add_argument("--target-delta",type=float,default=DELTA_TARGET_DEFAULT)
    p.add_argument("--qqq-premium-match-short-qty",type=int,default=None,
        help="select QQQ LONG PUT Ask closest to N times the selected SPY SHORT PUT Bid")
    p.add_argument("--qqq-target-abs-delta",type=float,default=None,
        help="optional target absolute Delta for QQQ LONG PUT; restrict candidate contracts to this band")
    p.add_argument("--qqq-delta-tolerance",type=float,default=0.10,
        help="absolute-Delta tolerance; 0.10 around target 0.50 admits 0.40–0.60")
    p.add_argument("--qqq-reference-premium-fraction",type=float,default=None,
        help="select a same-expiry QQQ put priced near this fraction of the normal delta-band reference put; its Delta is not constrained")
    p.add_argument("--dte-min",type=int,default=DTE_MIN_DEFAULT);p.add_argument("--dte-max",type=int,default=DTE_MAX_DEFAULT)
    p.add_argument("--dte-target",type=int,default=DTE_TARGET_DEFAULT);p.add_argument("--cohort-stride-sessions",type=int,default=COHORT_STRIDE_SESSIONS)
    p.add_argument("--initial-phase-sessions",type=int,default=0,help="first eligible common-session index offset; must be less than cohort stride")
    p.add_argument("--allow-overlapping-cohorts",action="store_true",help="allow a new fixed-size cohort while earlier cohorts remain open; portfolio margin/capital is not constrained")
    p.add_argument("--slippage-per-share",type=float,default=BASE_SLIPPAGE);p.add_argument("--commission-per-contract-per-side",type=float,default=BASE_COMMISSION)
    p.add_argument("--qqq-cache",default=str(Path.home()/".cache"/"qqq-options-full-history"))
    p.add_argument("--spy-cache",default=str(Path.home()/".cache"/"spy-options-cross-put-v1"))
    p.add_argument("--out",default="research/qqq_spy_put_relative_signal_v1/results/latest")
    return p.parse_args()

def main():
    args=parse_args();report=run_replay(args)
    print(json.dumps({"status":report["status"],"window":report["window"],"entry_filter":report["entry_filter"],"ratio":report["ratio"],"premium_matching":report["premium_matching"],"coverage":report["coverage"],
        "cohort":{k:report["cohort"][k] for k in ("selected_signals","entered_cohorts","entry_skipped")},
        "fixed_entry_schedule":report["fixed_entry_schedule"],"policies":report["policies"],"output_dir":args.out},indent=2,allow_nan=False))

if __name__=="__main__":main()
