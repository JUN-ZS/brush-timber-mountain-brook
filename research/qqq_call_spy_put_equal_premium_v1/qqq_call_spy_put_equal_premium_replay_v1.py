#!/usr/bin/env python3
"""Paired EOD replay: LONG QQQ calls versus SHORT SPY puts with matched premium dollars."""
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

def normalized_contract_id(row: dict[str, Any]) -> str:
    ident = re.sub(r"\s+", "", str(row.get("contract_id") or "").strip().upper())
    return ident[2:] if ident.startswith("O:") else ident

def option_right_code(right: str) -> str:
    text = str(right).strip().upper()
    if text in ("C", "CALL"): return "C"
    if text in ("P", "PUT"): return "P"
    raise ValueError(f"unsupported option right: {right}")


def standard_option_identity(row: dict[str, Any], symbol: str, right: str) -> bool:
    code = option_right_code(right)
    ident = normalized_contract_id(row)
    m = re.fullmatch(re.escape(symbol) + r"(\d{6})" + code + r"(\d{8})", ident)
    if not m or str(row.get("symbol", "")).upper() != symbol:
        return False
    expected_types = ("c", "call") if code == "C" else ("p", "put")
    if str(row.get("type", "")).strip().lower() not in expected_types: return False
    try: expiry = datetime.strptime(m.group(1), "%y%m%d").date().isoformat()
    except ValueError: return False
    strike = num(row.get("strike"))
    return (as_day(row.get("expiration")) == expiry and strike is not None and strike > 0
            and abs(strike - int(m.group(2)) / 1000.0) < 0.00051)


def standard_call_identity(row: dict[str, Any], symbol: str) -> bool:
    return standard_option_identity(row, symbol, "C")


def standard_put_identity(row: dict[str, Any], symbol: str) -> bool:
    return standard_option_identity(row, symbol, "P")

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
    request = urllib.request.Request(url, headers={"User-Agent":"qqq-call-spy-put-equal-premium/1.0"})
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

def iter_symbol_days(paths: list[Path], symbol: str, right: str, start_day: str, end_day: str, stats: dict[str, Any]) -> Iterable:
    import pyarrow.parquet as pq
    previous_day = ""
    for path in paths:
        parquet = pq.ParquetFile(path)
        missing = sorted(set(OPTION_COLUMNS) - set(parquet.schema_arrow.names))
        if missing: raise ValueError(f"{path.name} missing required columns: {missing}")
        current_day, rows = None, []
        def emit(day, day_rows):
            if day and start_day <= day <= end_day and day_rows:
                stats["chain_dates"] += 1; stats["option_rows"] += len(day_rows); stats["last_chain_date"] = day
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
                if start_day <= day <= end_day and str(row.get("symbol","")).upper() == symbol and str(row.get("type","")).strip().lower() in (("c","call") if option_right_code(right) == "C" else ("p","put")):
                    rows.append(row)
        item = emit(current_day, rows)
        if item is not None: yield item

def choose_leg(rows, symbol, day, expiry, target_delta, right):
    candidates = []
    for row in rows:
        if not standard_option_identity(row, symbol, right) or as_day(row.get("date")) != day: continue
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
    """Select common expiry QQQ CALL / SPY PUT, without optimizing on P&L."""
    if not qqq_rows or not spy_rows or qqq_spot <= 0 or spy_spot <= 0: return None
    date.fromisoformat(signal_day)
    def expiries(rows, symbol, right):
        found = {}
        for row in rows:
            if not standard_option_identity(row,symbol,right) or as_day(row.get("date")) != signal_day: continue
            if not valid_quote(row,require_positive_bid=True): continue
            expiry = as_day(row.get("expiration"))
            try: dte = (date.fromisoformat(expiry)-date.fromisoformat(signal_day)).days
            except ValueError: continue
            if dte_min <= dte <= dte_max: found[expiry] = dte
        return found
    q_exp, s_exp = expiries(qqq_rows,"QQQ","C"), expiries(spy_rows,"SPY","P")
    choices=[]
    for expiry in sorted(set(q_exp)&set(s_exp)):
        qleg=choose_leg(qqq_rows,"QQQ",signal_day,expiry,target_delta,"C")
        sleg=choose_leg(spy_rows,"SPY",signal_day,expiry,target_delta,"P")
        if qleg is None or sleg is None: continue
        dte=q_exp[expiry]
        key=(abs(dte-dte_target),abs(qleg["abs_delta"]-target_delta)+abs(sleg["abs_delta"]-target_delta),
             -(qleg["size"]+sleg["size"]),-(qleg["oi"]+sleg["oi"]),expiry,qleg["id"],sleg["id"])
        choices.append((key,expiry,dte,qleg,sleg))
    if not choices:return None
    _,expiry,dte,qleg,sleg=min(choices,key=lambda x:x[0])
    return {"signal_date":signal_day,"expiry":expiry,"signal_dte":dte,
        "qqq_contract_id":qleg["id"],"qqq_strike":qleg["strike"],"qqq_abs_delta":qleg["abs_delta"],
        "spy_contract_id":sleg["id"],"spy_strike":sleg["strike"],"spy_abs_delta":sleg["abs_delta"],
        "qqq_spot_signal":qqq_spot,"spy_spot_signal":spy_spot,
        "selection_rule":"QQQ CALL + SPY PUT; same expiry; nearest DTE45; each abs-Delta nearest 0.25; no P&L optimization"}


def rows_by_id(rows): return {normalized_contract_id(row):row for row in rows if normalized_contract_id(row)}

def choose_equal_premium_quantities(qqq_call_ask, spy_put_bid, max_total_contracts,
                                  max_long_available, max_short_available):
    """Match total QQQ-call debit to total SPY-put credit using whole contracts."""
    qprice, sprice = num(qqq_call_ask), num(spy_put_bid)
    if qprice is None or sprice is None or qprice <= 0 or sprice <= 0 or max_total_contracts < 2:
        return None
    max_long = min(max_total_contracts - 1, int(max_long_available))
    max_short = min(max_total_contracts - 1, int(max_short_available))
    candidates = []
    for long_qty in range(1, max_long + 1):
        for short_qty in range(1, min(max_short, max_total_contracts - long_qty) + 1):
            debit = long_qty * qprice * MULTIPLIER
            credit = short_qty * sprice * MULTIPLIER
            mismatch = abs(debit - credit) / max(debit, credit)
            candidates.append(((mismatch, -min(debit, credit), -(long_qty + short_qty), long_qty, short_qty),
                               long_qty, short_qty, debit, credit))
    if not candidates: return None
    _, long_qty, short_qty, debit, credit = min(candidates, key=lambda x: x[0])
    mismatch_usd = abs(debit - credit)
    match_pct = (1 - mismatch_usd / max(debit, credit)) * 100
    return {"long_qqq_qty":long_qty,"short_spy_qty":short_qty,
            "qqq_call_premium_debit_usd":debit,"spy_put_premium_credit_usd":credit,
            "premium_mismatch_usd":mismatch_usd,"premium_match_pct":match_pct}


def entry_quotes_valid(qrow,srow,long_qty,short_qty):
    if qrow is None or srow is None:return False,"EXACT_SELECTED_CONTRACT_MISSING"
    if not standard_call_identity(qrow,"QQQ") or not standard_put_identity(srow,"SPY"):return False,"CONTRACT_IDENTITY_INVALID"
    if not valid_quote(qrow,require_positive_bid=True) or not valid_quote(srow,require_positive_bid=True):return False,"ENTRY_BID_ASK_INVALID"
    if displayed_size(qrow,"ask") < long_qty:return False,"QQQ_CALL_ASK_SIZE_INSUFFICIENT"
    if displayed_size(srow,"bid") < short_qty:return False,"SPY_PUT_BID_SIZE_INSUFFICIENT"
    return True,"OK"


def exit_quotes_valid(qrow,srow,long_qty,short_qty):
    if qrow is None or srow is None:return False,"EXACT_SELECTED_CONTRACT_MISSING"
    if not standard_call_identity(qrow,"QQQ") or not standard_put_identity(srow,"SPY"):return False,"CONTRACT_IDENTITY_INVALID"
    if not valid_quote(qrow) or not valid_quote(srow):return False,"EXIT_BID_ASK_INVALID"
    if displayed_size(qrow,"bid") < long_qty:return False,"QQQ_CALL_BID_SIZE_INSUFFICIENT"
    if displayed_size(srow,"ask") < short_qty:return False,"SPY_PUT_ASK_SIZE_INSUFFICIENT"
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

def summarize_sizing_sensitivity(trades,max_total_contracts,slippage,commission):
    """Compare fixed contract ratios on the same selected contracts and quote paths."""
    output=[]
    unit_cost=slippage*MULTIPLIER+commission
    for policy_def in POLICIES:
        policy=policy_def["policy"]
        policy_rows=[r for r in trades if r.get("policy")==policy]
        resolved=[r for r in policy_rows if r.get("status")=="RESOLVED"
                  and r.get("qqq_long_gross_pnl_usd") is not None
                  and r.get("spy_short_gross_pnl_usd") is not None]
        unresolved=sum(str(r.get("status","")).startswith("UNRESOLVED") for r in policy_rows)
        for long_qty in range(1,max_total_contracts):
            for short_qty in range(1,max_total_contracts-long_qty+1):
                pnls=[]
                for r in resolved:
                    base_long=int(r.get("long_qqq_qty") or 1)
                    base_short=int(r.get("short_spy_qty") or 1)
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
                    "total_contracts":long_qty+short_qty,"opened_n":len(policy_rows),
                    "resolved_n":len(pnls),"unresolved_n":unresolved,
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


def build_shock_grid(entries,slippage,commission):
    shocks=[-1.0,-0.75,-0.5,-0.4,-0.30,-0.25,-0.20,-0.15,-0.10,-0.05,0.0,0.05,0.10,0.20];output=[]
    unit_cost=slippage*MULTIPLIER+commission
    for qr in shocks:
        for sr in shocks:
            vals=[]
            for e in entries:
                qs,ss=num(e.get("qqq_spot_entry")),num(e.get("spy_spot_entry"))
                if qs is None or ss is None:continue
                long_qty,short_qty=int(e["long_qqq_qty"]),int(e["short_spy_qty"])
                qintr=max(qs*(1+qr)-float(e["qqq_strike"]),0)
                sintr=max(float(e["spy_strike"])-ss*(1+sr),0)
                cash=MULTIPLIER*(short_qty*float(e["spy_entry_bid"])-long_qty*float(e["qqq_entry_ask"]))
                entry_cost=(long_qty+short_qty)*unit_cost
                vals.append(cash+MULTIPLIER*(long_qty*qintr-short_qty*sintr)-entry_cost)
            wins=sum(v>0.005 for v in vals)
            output.append({"qqq_pct_move":round(qr*100,2),"spy_pct_move":round(sr*100,2),
                "same_pct_move_diagonal":qr==sr,"entry_cohort_n":len(vals),"positive_scenario_n":wins,
                "positive_scenario_pct":finite_round(100*wins/len(vals),4) if vals else None,
                "mean_expiry_scenario_pnl_usd":finite_round(statistics.mean(vals)) if vals else None,
                "median_expiry_scenario_pnl_usd":finite_round(statistics.median(vals)) if vals else None,
                "worst_expiry_scenario_pnl_usd":finite_round(min(vals),4) if vals else None,
                "classification":"HYPOTHETICAL_EXPIRY_SHOCK_NOT_HISTORICAL_WIN_RATE"})
    return output


def write_csv(path,rows,fallback_fields=None):
    path.parent.mkdir(parents=True,exist_ok=True)
    fields=list(dict.fromkeys(k for r in rows for k in r.keys())) if rows else (fallback_fields or ["status"])
    with path.open("w",newline="",encoding="utf-8") as handle:
        writer=csv.DictWriter(handle,fieldnames=fields,extrasaction="ignore");writer.writeheader();writer.writerows(rows)

def render_markdown(report,costs,shock,sizing):
    lines=["# QQQ LONG CALL / SPY SHORT PUT — Equal-Premium Replay V1","",
        f"Status: **{report['status']}**. EOD quote-side estimate, not confirmed fills.","",
        f"- Window requested: {report['window']['start']} to {report['window']['end']}; last QQQ-call/SPY-put chain dates: {report['coverage']['qqq_last_chain_date']} / {report['coverage']['spy_last_chain_date']}.",
        f"- Position rule: buy QQQ CALL at Ask and sell SPY PUT at Bid. Per cohort, integer contract counts minimize relative mismatch between call premium paid and put premium received, subject to a total-contract cap of {report['premium_matching']['max_total_contracts']} and entry-side displayed sizes.",
        f"- Average QQQ call premium debit: USD {report['premium_matching']['mean_call_debit_usd']:,.2f}; average SPY put premium credit: USD {report['premium_matching']['mean_put_credit_usd']:,.2f}; average absolute mismatch: USD {report['premium_matching']['mean_absolute_mismatch_usd']:,.2f}; average matching score: {report['premium_matching']['mean_match_pct']:.2f}%.",
        f"- Selection: same expiry; DTE {report['selection']['dte_min']}–{report['selection']['dte_max']} (target {report['selection']['dte_target']}); each leg absolute-Delta target {report['selection']['target_abs_delta']:.2f}. Base costs: USD {report['costs']['base_slippage_per_option_share_usd']:.3f}/option-share/side + USD {report['costs']['base_commission_per_contract_per_side_usd']:.2f}/contract/side.",
        "","## Selected matched-premium ratios","","| QQQ LONG CALL : SPY SHORT PUT | Cohorts | Mean QQQ premium debit | Mean SPY premium credit | Mean mismatch | Mean premium-match % |","|---:|---:|---:|---:|---:|---:|"]
    fmt=lambda v:"—" if v is None else f"USD {v:,.2f}"
    for r in report["premium_matching"]["ratio_distribution"]:
        lines.append(f"| {r['long_qqq_qty']} : {r['short_spy_qty']} | {r['cohorts']} | {fmt(r['mean_call_debit_usd'])} | {fmt(r['mean_put_credit_usd'])} | {fmt(r['mean_mismatch_usd'])} | {r['mean_match_pct']:.2f}% |")
    lines += ["","Equal premium dollars means debit/credit parity only; it does not equalize Delta exposure, notional, collateral, assignment risk, or maximum loss.","",
        "## Coverage and source integrity","",
        f"- Common underlying sessions: {report['coverage']['common_underlying_sessions']}; QQQ chain dates with calls: {report['coverage']['qqq_chain_dates']}; SPY chain dates with puts: {report['coverage']['spy_chain_dates']}; sessions with both chains: {report['coverage']['sessions_with_both_chains']}.",
        f"- Selected signals: {report['cohort']['selected_signals']}; entered cohorts: {report['cohort']['entered_cohorts']}; skipped entries: {report['cohort']['entry_skipped']}.",
        "- Every annual options file and underlying file is SHA/byte-count verified. No quote is forward-filled; exact selected contract IDs are retained.",
        "","## Historical win rate — base assumed costs","","| Exit rule | Resolved/opened | Wins/losses/flat | Win rate (nominal Wilson 95%) | Mean net P&L (resolved) | Median (resolved) | Total net P&L (resolved) | Worst trade (resolved) | Unresolved |","|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for p in report["policies"].values():
        rate="—" if p["win_rate_pct"] is None else f"{p['win_rate_pct']:.2f}% ({p['win_rate_wilson95_low_pct']:.2f}–{p['win_rate_wilson95_high_pct']:.2f}%)"
        lines.append(f"| {p['policy']} | {p['resolved']}/{p['opened']} | {p['wins']}/{p['losses']}/{p['flat']} | {rate} | {fmt(p['expectancy_net_usd'])} | {fmt(p['median_net_usd'])} | {fmt(p['total_net_pnl_usd'])} | {fmt(p['worst_net_usd'])} | {p['unresolved']} |")
    lines += ["","Win-rate denominator is **resolved episodes only**. Mean, median, total P&L, profit factor, and worst trade also use resolved episodes only; unresolved trades are excluded, not assigned zero. Entry skips stay separate. The nominal Wilson interval does not correct for time dependence or strategy selection.",
        "","## Leg attribution","","| Exit rule | Mean gross QQQ LONG CALL P&L | Mean gross SPY SHORT PUT P&L |","|---|---:|---:|"]
    for p in report["policies"].values():
        lines.append(f"| {p['policy']} | {fmt(p['mean_qqq_long_gross_pnl_usd'])} | {fmt(p['mean_spy_short_gross_pnl_usd'])} |")
    lines += ["","## Transaction-cost sensitivity","","| Exit rule | Slippage/share | Commission/contract/side | N | Win rate | Expectancy | Total net P&L | Worst |","|---|---:|---:|---:|---:|---:|---:|---:|"]
    for r in costs:
        rate="—" if r["win_rate_pct"] is None else f"{r['win_rate_pct']:.2f}%"
        lines.append(f"| {r['policy']} | {r['slippage_per_option_share_usd']:.3f} | {r['commission_per_contract_per_side_usd']:.2f} | {r['resolved_n']} | {rate} | {fmt(r['expectancy_net_usd'])} | {fmt(r['total_net_pnl_usd'])} | {fmt(r['worst_net_usd'])} |")
    lines += ["","## Fixed contract-ratio sensitivity (same selected contracts and quote path)","",
        f"- Grid includes all fixed whole-contract combinations with QQQ CALL + SPY PUT total contracts ≤ {report['premium_matching']['max_total_contracts']}; it rescales the same per-leg historical gross P&L and is not a fresh contract-selection replay.",
        "- Full grid is in sizing_sensitivity.csv. Results inherit the base replay's resolved/unresolved cohort status; no size-dependent market impact is modeled.",
        "","## Equal-percentage QQQ/SPY expiry shocks (hypothetical)","",
        "These are intrinsic-value scenarios based on actual entry quotes and spots, not historical option trade outcomes.",
        "Only entry-side slippage/commission is charged once; no closing trade is assumed for the expiry payoff. Exercise/assignment charges, financing, taxes, broker margin and forced-liquidation costs are not modeled.","",
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
    if args.max_total_contracts<2 or args.max_total_contracts>20:raise ValueError("max total contracts must be in 2–20")
    if not 0<args.target_delta<1 or args.dte_min<1 or args.dte_max<args.dte_min:raise ValueError("invalid Delta/DTE bounds")
    if not DELTA_MIN<=args.target_delta<=DELTA_MAX:raise ValueError("target Delta must be within 0.10–0.50")
    if args.cohort_stride_sessions<1 or args.slippage_per_share<0 or args.commission_per_contract_per_side<0:raise ValueError("invalid cohort stride or costs")
    qcache,scache=Path(args.qqq_cache),Path(args.spy_cache);integrity=[];qpaths=[];spaths=[]
    years=[y for y in YEARS if int(start_day[:4])<=y<=int(end_day[:4])]
    for symbol,cache,paths in (("QQQ",qcache,qpaths),("SPY",scache,spaths)):
        for year in years:
            path,meta=download_verified(symbol,year,cache);paths.append(path);integrity.append(meta)
    qu,qmeta=download_verified("QQQ",None,qcache);su,smeta=download_verified("SPY",None,scache);integrity.extend([qmeta,smeta])
    qspots,sspots=load_spots(qu, 'QQQ'),load_spots(su, 'SPY')
    dates=sorted(d for d in set(qspots)&set(sspots) if start_day<=d<=end_day)
    if not dates:raise ValueError("No common QQQ/SPY underlying sessions in the requested date range")
    qs={"chain_dates":0,"option_rows":0,"last_chain_date":None};ss={"chain_dates":0,"option_rows":0,"last_chain_date":None}
    qi=iter_symbol_days(qpaths,"QQQ","C",start_day,end_day,qs);si=iter_symbol_days(spaths,"SPY","P",start_day,end_day,ss)
    qitem,sitem=next(qi,None),next(si,None)
    active=[];trades=[];entries=[];skips=[];pending=None;next_signal=0;signal_count=entered_count=both_chains=0
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
            if ep["pending_exit"]:
                valid,reason=exit_quotes_valid(qrow,srow,ep["long_qqq_qty"],ep["short_spy_qty"])
                if valid:
                    vals=episode_pnl(ep,float(qrow["bid"]),float(srow["ask"]),args.slippage_per_share,args.commission_per_contract_per_side)
                    qspot,sspot=qspots.get(day),sspots.get(day);ep.update(vals)
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
            trigger=ep["age_sessions"]>=policy["hold_sessions"] if policy["hold_sessions"] is not None else dte<=7
            if trigger:
                ep["pending_exit"]=True;ep["exit_signal_date"]=day;ep["exit_signal_index"]=idx
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
                quantities=choose_equal_premium_quantities(
                    float(qrow["ask"]),float(srow["bid"]),args.max_total_contracts,
                    displayed_size(qrow,"ask"),displayed_size(srow,"bid"))
                if quantities is None:
                    valid,reason=False,"NO_SIZED_EQUAL_PREMIUM_CONTRACT_PAIR"
                else:
                    long_qty,short_qty=quantities["long_qqq_qty"],quantities["short_spy_qty"]
                    valid,reason=entry_quotes_valid(qrow,srow,long_qty,short_qty)
            if valid:
                qspot,sspot=qspots.get(day),sspots.get(day)
                if qspot is None or sspot is None:valid,reason=False,"ENTRY_UNDERLYING_CLOSE_MISSING"
                else:
                    long_qty,short_qty=quantities["long_qqq_qty"],quantities["short_spy_qty"]
                    entry_cash=MULTIPLIER*(short_qty*float(srow["bid"])-long_qty*float(qrow["ask"]))
                    entry_cost=(long_qty+short_qty)*(args.slippage_per_share*MULTIPLIER+args.commission_per_contract_per_side)
                    base={**pending,"entry_date":day,"entry_index":idx,"long_qqq_qty":long_qty,"short_spy_qty":short_qty,
                        "qqq_entry_ask":float(qrow["ask"]),"qqq_entry_bid":float(qrow["bid"]),
                        "spy_entry_bid":float(srow["bid"]),"spy_entry_ask":float(srow["ask"]),
                        "qqq_spot_entry":qspot,"spy_spot_entry":sspot,"entry_net_credit_before_cost_usd":entry_cash,
                        "entry_cash_after_entry_cost_usd":entry_cash-entry_cost,
                        "qqq_call_premium_debit_usd":quantities["qqq_call_premium_debit_usd"],
                        "spy_put_premium_credit_usd":quantities["spy_put_premium_credit_usd"],
                        "premium_mismatch_usd":quantities["premium_mismatch_usd"],
                        "premium_match_pct":quantities["premium_match_pct"],
                        "base_slippage_per_share":args.slippage_per_share,
                        "base_commission_per_contract_per_side":args.commission_per_contract_per_side,
                        "entry_delay_sessions":idx-pending["signal_index"]}
                    entries.append({k:v for k,v in base.items() if k!="signal_index"});entered_count+=1
                    for p in POLICIES:
                        active.append({**base,"policy":p["policy"],"status":"OPEN","pending_exit":False,
                            "exit_signal_date":None,"exit_signal_index":None,"exit_reason":None,"exit_deferred_sessions":0,
                            "missing_mark_sessions":0,"valid_mark_sessions":0,"last_mark_pnl_usd":None,
                            "max_favorable_mark_pnl_usd":None,"max_adverse_mark_pnl_usd":None})
            if not valid:
                pending["entry_defer_sessions"]+=1
                if day>=pending["expiry"]:
                    skips.append({"episode_id":pending["episode_id"],"signal_date":pending["signal_date"],"status":"ENTRY_SKIPPED",
                        "reason":"NO_VALID_ENTRY_BEFORE_EXPIRY","last_attempt_date":day,"last_quote_reason":reason,
                        "entry_defer_sessions":pending["entry_defer_sessions"]});pending=None
            else:pending=None
        if pending is None and not active and idx>=next_signal and qrows and srows:
            qspot,sspot=qspots.get(day),sspots.get(day)
            if qspot is not None and sspot is not None:
                pair=choose_pair(qrows,srows,day,qspot,sspot,args.target_delta,args.dte_min,args.dte_max,args.dte_target)
                if pair is not None:
                    signal_count+=1;pending={**pair,"episode_id":signal_count,"signal_index":idx,"entry_defer_sessions":0}
                    next_signal=idx+args.cohort_stride_sessions
    if pending is not None:
        skips.append({"episode_id":pending["episode_id"],"signal_date":pending["signal_date"],"status":"ENTRY_SKIPPED",
            "reason":"SOURCE_END_BEFORE_VALID_ENTRY","last_attempt_date":dates[-1],"last_quote_reason":"NO_LATER_SOURCE_DATE",
            "entry_defer_sessions":pending["entry_defer_sessions"]})
    for ep in active:
        ep.update({"status":"UNRESOLVED_SOURCE_END","exit_date":None,"unresolved_reason":"SOURCE_END_BEFORE_EXECUTABLE_EXIT","last_observed_date":dates[-1]})
        trades.append(ep)
    for r in trades:r["base_cost_win"]=r["net_pnl_usd"]>0.005 if r.get("status")=="RESOLVED" and r.get("net_pnl_usd") is not None else None
    policies={p["policy"]:policy_summary(p["policy"],trades) for p in POLICIES}
    costs=summarize_costs(trades);shock=build_shock_grid(entries,args.slippage_per_share,args.commission_per_contract_per_side)
    sizing=summarize_sizing_sensitivity(trades,args.max_total_contracts,args.slippage_per_share,args.commission_per_contract_per_side)
    ratio_groups={}
    for e in entries:
        key=(int(e["long_qqq_qty"]),int(e["short_spy_qty"]))
        ratio_groups.setdefault(key,[]).append(e)
    ratio_distribution=[]
    for (long_qty,short_qty),items in sorted(ratio_groups.items()):
        ratio_distribution.append({"long_qqq_qty":long_qty,"short_spy_qty":short_qty,"cohorts":len(items),
            "mean_call_debit_usd":finite_round(statistics.mean(float(x["qqq_call_premium_debit_usd"]) for x in items)),
            "mean_put_credit_usd":finite_round(statistics.mean(float(x["spy_put_premium_credit_usd"]) for x in items)),
            "mean_mismatch_usd":finite_round(statistics.mean(float(x["premium_mismatch_usd"]) for x in items)),
            "mean_match_pct":finite_round(statistics.mean(float(x["premium_match_pct"]) for x in items))})
    premium_matching={"max_total_contracts":args.max_total_contracts,
        "mean_call_debit_usd":finite_round(statistics.mean(float(x["qqq_call_premium_debit_usd"]) for x in entries)) if entries else 0.0,
        "mean_put_credit_usd":finite_round(statistics.mean(float(x["spy_put_premium_credit_usd"]) for x in entries)) if entries else 0.0,
        "mean_absolute_mismatch_usd":finite_round(statistics.mean(float(x["premium_mismatch_usd"]) for x in entries)) if entries else 0.0,
        "mean_match_pct":finite_round(statistics.mean(float(x["premium_match_pct"]) for x in entries)) if entries else 0.0,
        "ratio_distribution":ratio_distribution}
    report={"schema":"qqq-call-spy-put-equal-premium-replay.v1",
        "status":"COMPLETED_WITH_UNRESOLVEDS" if any(p["unresolved"] for p in policies.values()) or skips else "COMPLETED",
        "source":{"repository":SOURCE_REPO,"tree_commit":SOURCE_COMMIT},"window":{"start":start_day,"end":end_day},
        "ratio":{"method":"premium-dollar-matched integer quantities","max_total_contracts":args.max_total_contracts,"contract_multiplier":MULTIPLIER},
        "premium_matching":premium_matching,
        "selection":{"target_abs_delta":args.target_delta,"delta_eligible_band":[DELTA_MIN,DELTA_MAX],"dte_min":args.dte_min,
            "dte_max":args.dte_max,"dte_target":args.dte_target,"cohort_stride_sessions":args.cohort_stride_sessions,"common_expiry_required":True},
        "costs":{"base_slippage_per_option_share_usd":args.slippage_per_share,"base_commission_per_contract_per_side_usd":args.commission_per_contract_per_side,
            "alternative_slippage_per_option_share_usd":list(SLIPPAGE_GRID),"alternative_commission_per_contract_per_side_usd":list(COMMISSION_GRID)},
        "position_size_sensitivity":{"max_total_contracts":args.max_total_contracts,
            "method":"fixed whole-contract ratio sensitivity on the same selected contracts, quote dates and resolved cohort set; sum of contracts capped at max_total_contracts; cost scales per contract; no size-dependent market impact"},
        "coverage":{"common_underlying_sessions":len(dates),"qqq_chain_dates":qs["chain_dates"],"qqq_call_rows":qs["option_rows"],
            "spy_chain_dates":ss["chain_dates"],"spy_put_rows":ss["option_rows"],"sessions_with_both_chains":both_chains,
            "qqq_last_chain_date":qs["last_chain_date"],"spy_last_chain_date":ss["last_chain_date"],
            "qqq_underlying_first_date":min(qspots) if qspots else None,"qqq_underlying_last_date":max(qspots) if qspots else None,
            "spy_underlying_first_date":min(sspots) if sspots else None,"spy_underlying_last_date":max(sspots) if sspots else None,
            "expected_common_first_date":dates[0],"expected_common_last_date":dates[-1]},
        "cohort":{"selected_signals":signal_count,"entered_cohorts":entered_count,"entry_skipped":len(skips),"entry_skip_rows":skips},
        "policies":policies,"limitations":[
            "Public EOD preservation mirror; hashes establish file identity, not exchange or OPRA authenticity.",
            "Equal-dollar premium matching does not equalize delta exposure, notional, margin, assignment or max loss.",
            "EOD quotes are not verified fills; displayed size is a screening gate, not guaranteed multi-leg execution.",
            "Conservative sides: QQQ LONG enters Ask/exits Bid; SPY SHORT enters Bid/exits Ask.",
            "Missing exit quotes/size at expiry or source end remain unresolved; win-rate denominator is resolved episodes only.",
            "Option chain source ends in 2025; no 2026 performance is observed here.",
            "Nominal Wilson interval does not correct for regime clustering, dependence, or prior strategy selection.",
            "Expiry shock grid uses QQQ call and SPY put intrinsic value, charges entry-side slippage/commission once; exercise/assignment fees, broker margin, forced liquidation, financing and interim path are not modeled.",
            "SPY short put can dominate downside even when QQQ long call appreciates; premium credit is not a max-loss budget.",
            "Fixed-cohort replay does not model portfolio compounding, taxes, financing, or verified fills."],
        "source_integrity":integrity}
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    write_csv(out/"entry_cohort.csv",entries,["episode_id","signal_date","entry_date"])
    write_csv(out/"trade_episodes.csv",trades,["episode_id","policy","status","net_pnl_usd"])
    write_csv(out/"entry_skips.csv",skips,["episode_id","signal_date","status","reason"])
    write_csv(out/"cost_sensitivity.csv",costs);write_csv(out/"expiry_shock_grid.csv",shock)
    write_csv(out/"sizing_sensitivity.csv",sizing)
    (out/"source_manifest.json").write_text(json.dumps({"source_repository":SOURCE_REPO,"source_tree_commit":SOURCE_COMMIT,
        "source_integrity":integrity,"source_window":report["window"],
        "selected_option_rights":{"QQQ":"CALL","SPY":"PUT"},"sizing_method":"equal premium debit/credit; total contracts capped"},indent=2),encoding="utf-8")
    (out/"summary.json").write_text(json.dumps(report,indent=2,allow_nan=False),encoding="utf-8")
    (out/"summary.md").write_text(render_markdown(report,costs,shock,sizing),encoding="utf-8")
    return report

def parse_args():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--start",default=START_DEFAULT);p.add_argument("--end",default=END_DEFAULT)
    p.add_argument("--max-total-contracts",type=int,default=9)
    p.add_argument("--target-delta",type=float,default=DELTA_TARGET_DEFAULT)
    p.add_argument("--dte-min",type=int,default=DTE_MIN_DEFAULT);p.add_argument("--dte-max",type=int,default=DTE_MAX_DEFAULT)
    p.add_argument("--dte-target",type=int,default=DTE_TARGET_DEFAULT);p.add_argument("--cohort-stride-sessions",type=int,default=COHORT_STRIDE_SESSIONS)
    p.add_argument("--slippage-per-share",type=float,default=BASE_SLIPPAGE);p.add_argument("--commission-per-contract-per-side",type=float,default=BASE_COMMISSION)
    p.add_argument("--qqq-cache",default=str(Path.home()/".cache"/"qqq-options-full-history"))
    p.add_argument("--spy-cache",default=str(Path.home()/".cache"/"spy-options-cross-put-v1"))
    p.add_argument("--out",default="research/qqq_spy_cross_put_v1/results/latest")
    return p.parse_args()

def main():
    args=parse_args();report=run_replay(args)
    print(json.dumps({"status":report["status"],"window":report["window"],"ratio":report["ratio"],"coverage":report["coverage"],
        "cohort":{k:report["cohort"][k] for k in ("selected_signals","entered_cohorts","entry_skipped")},
        "policies":report["policies"],"output_dir":args.out},indent=2,allow_nan=False))

if __name__=="__main__":main()
