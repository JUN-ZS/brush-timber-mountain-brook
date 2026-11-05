#!/usr/bin/env python3
"""Observed ORATS EOD TAIL CALL overlay for the alternating SPY/QQQ put-cycle study.

Buy six standard TAIL calls at the natural ask, never pay above USD 0.10/share,
require displayed ask size >= six, mark at bid, and defer liquidation until six
contracts are displayed at the bid or the option expires. No ETF-price proxy or
Black-Scholes substitution is permitted.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

SYMBOL = "TAIL"
MULTIPLIER = 100
CONTRACTS = 6
TARGET_ASK = 0.10
MIN_DTE, MAX_DTE, TARGET_DTE = 21, 45, 30
COMMISSION_PER_CONTRACT_PER_SIDE = 0.65
FIELDS = (
    "tradeDate,expirDate,dte,strike,spotPrice,delta,"
    "callBidPrice,callAskPrice,callBidSize,callAskSize,"
    "callVolume,callOpenInterest,callBidIv,callMidIv,callAskIv,updatedAt"
)
API_URL = "https://api.orats.io/datav2/hist/strikes"
SCHEMA = "tail-call-six-contract-overlay.v1"


def num(value):
    try:
        x = float(value)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def positive_int(value):
    x = num(value)
    return int(x) if x is not None and x > 0 else 0


def money(value):
    return round(float(value), 6)


def quote_key(expiry, strike):
    return (str(expiry), round(float(strike), 4))


def pick_call(rows, day, target_ask=TARGET_ASK, min_dte=MIN_DTE,
              max_dte=MAX_DTE, target_dte=TARGET_DTE, contracts=CONTRACTS):
    """Pick the closest executable OTM call at or below the USD 0.10 limit."""
    candidates = []
    for row in rows:
        if str(row.get("tradeDate", ""))[:10] != day:
            continue
        expiry = str(row.get("expirDate", ""))[:10]
        dte = positive_int(row.get("dte"))
        strike, spot = num(row.get("strike")), num(row.get("spotPrice"))
        ask, bid = num(row.get("callAskPrice")), num(row.get("callBidPrice"))
        ask_size = positive_int(row.get("callAskSize"))
        delta = num(row.get("delta"))
        if not expiry or dte < min_dte or dte > max_dte:
            continue
        if strike is None or spot is None or strike <= spot:
            continue
        if ask is None or ask <= 0 or ask > target_ask + 1e-9:
            continue
        if ask_size < contracts or bid is None or bid < 0 or delta is None:
            continue
        bid_size = positive_int(row.get("callBidSize"))
        oi = positive_int(row.get("callOpenInterest"))
        candidates.append((
            (abs(ask - target_ask), abs(dte - target_dte), -ask_size, -oi, -delta, strike, expiry),
            {
                "symbol": SYMBOL, "expiry": expiry, "strike": float(strike),
                "dte_entry": dte, "spot_entry": float(spot), "entry_ask": float(ask),
                "entry_bid": float(bid), "entry_ask_size": ask_size,
                "entry_bid_size": bid_size, "entry_delta": float(delta),
                "entry_open_interest": oi, "entry_volume": positive_int(row.get("callVolume")),
                "entry_bid_iv": num(row.get("callBidIv")), "entry_mid_iv": num(row.get("callMidIv")),
                "entry_ask_iv": num(row.get("callAskIv")), "entry_quote_updated_at": row.get("updatedAt"),
            }
        ))
    return min(candidates, key=lambda x: x[0])[1] if candidates else None


def option_mark_pnl(entry_ask, mark_bid, contracts=CONTRACTS, multiplier=MULTIPLIER):
    entry_commission = contracts * COMMISSION_PER_CONTRACT_PER_SIDE
    return contracts * multiplier * (float(mark_bid) - float(entry_ask)) - entry_commission


def option_closed_pnl(entry_ask, exit_bid, contracts=CONTRACTS, multiplier=MULTIPLIER):
    commissions = 2.0 * contracts * COMMISSION_PER_CONTRACT_PER_SIDE
    return contracts * multiplier * (float(exit_bid) - float(entry_ask)) - commissions


def load_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows, fieldnames=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        if fieldnames:
            with path.open("w", newline="", encoding="utf-8") as handle:
                csv.DictWriter(handle, fieldnames=fieldnames).writeheader()
        else:
            path.write_text("", encoding="utf-8")
        return
    names = fieldnames or list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=names, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def fetch_day(day, token, cache_dir, retries=6):
    """Fetch one date's TAIL strike grid. Cache stores response only, never the token."""
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / (day + ".json")
    if cache_file.is_file():
        raw = cache_file.read_bytes()
        payload = json.loads(raw)
        if isinstance(payload, dict) and isinstance(payload.get("data"), list):
            return payload["data"], hashlib.sha256(raw).hexdigest(), "CACHE"
    params = {"token": token, "ticker": SYMBOL, "tradeDate": day, "dte": "0,45", "fields": FIELDS}
    url = API_URL + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={
        "User-Agent": "tail-call-overlay-research/1.0", "Accept": "application/json",
    })
    last_error = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                raw = response.read()
            payload = json.loads(raw)
            if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
                raise RuntimeError("ORATS response schema missing data[]")
            cache_file.write_bytes(raw)
            return payload["data"], hashlib.sha256(raw).hexdigest(), "API"
        except urllib.error.HTTPError as exc:
            last_error = f"HTTP_{exc.code}"
            if exc.code not in (408, 425, 429, 500, 502, 503, 504):
                raise RuntimeError(f"ORATS request failed for {day}: HTTP {exc.code}") from None
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, RuntimeError) as exc:
            last_error = type(exc).__name__
        if attempt < retries - 1:
            time.sleep(min(2 ** attempt, 20))
    raise RuntimeError(f"ORATS request exhausted retries for {day}: {last_error}")


def all_dates(arms, data_dir):
    dates = set()
    for arm in arms:
        for row in load_csv(Path(data_dir) / f"{arm}_daily_nav.csv"):
            dates.add(str(row["date"])[:10])
    return sorted(dates)


def find_quote(rows, expiry, strike, day):
    key = quote_key(expiry, strike)
    for row in rows:
        row_strike = num(row.get("strike"))
        if str(row.get("tradeDate", ""))[:10] == day and row_strike is not None:
            if quote_key(str(row.get("expirDate", ""))[:10], row_strike) == key:
                return row
    return None


def run_arm(arm, data_dir, daily_quotes):
    root = Path(data_dir)
    entries = load_csv(root / f"{arm}_entries.csv")
    trades = load_csv(root / f"{arm}_trades.csv")
    core_daily = load_csv(root / f"{arm}_daily_nav.csv")
    if not core_daily:
        raise RuntimeError(f"{arm}: missing core daily NAV")
    dates = [str(row["date"])[:10] for row in core_daily]
    date_set = set(dates)
    core_nav = {str(row["date"])[:10]: float(row["nav_usd"]) for row in core_daily}
    last_date = dates[-1]
    trade_by_id = {str(t.get("episode_id")): t for t in trades}
    entries_by_date = defaultdict(list)
    for ep in entries:
        entries_by_date[str(ep["entry_date"])[:10]].append(ep)

    active, tail_trades, tail_entries, quote_audit, daily = [], [], [], [], []
    realized_total = 0.0
    for day in dates:
        rows = daily_quotes.get(day, [])
        keep = []
        for pos in active:
            row = find_quote(rows, pos["expiry"], pos["strike"], day)
            if row is not None:
                bid = num(row.get("callBidPrice"))
                bid_size = positive_int(row.get("callBidSize"))
                ask = num(row.get("callAskPrice"))
                ask_size = positive_int(row.get("callAskSize"))
                if bid is not None and bid >= 0:
                    pos["last_bid"] = float(bid)
                    pos["last_bid_size"] = bid_size
                    pos["last_mark_date"] = day
                    pos["stale_sessions"] = 0
                else:
                    pos["stale_sessions"] += 1
                quote_audit.append({
                    "arm": arm, "episode_id": pos["episode_id"], "date": day,
                    "expiry": pos["expiry"], "strike": pos["strike"], "dte": row.get("dte"),
                    "spot": row.get("spotPrice"), "bid": bid, "bid_size": bid_size,
                    "ask": ask, "ask_size": ask_size, "delta": row.get("delta"),
                    "call_volume": row.get("callVolume"), "call_oi": row.get("callOpenInterest"),
                    "updated_at": row.get("updatedAt"),
                    "mark_quality": "BID_SIZE_GE_6" if bid is not None and bid_size >= CONTRACTS
                                    else "BID_SIZE_LT_6_OR_ZERO",
                })
            else:
                pos["stale_sessions"] += 1

            expired = day >= pos["expiry"]
            if day >= pos["core_exit_date"] and row is not None:
                bid = num(row.get("callBidPrice"))
                bid_size = positive_int(row.get("callBidSize"))
                if bid is not None and bid > 0 and bid_size >= CONTRACTS:
                    pnl = option_closed_pnl(pos["entry_ask"], bid)
                    delay = (dates.index(day) - dates.index(pos["core_exit_date"])) if pos["core_exit_date"] in date_set else None
                    pos.update({
                        "status": "RESOLVED_BID_SIZE_GE_6", "exit_date": day,
                        "exit_bid": bid, "exit_bid_size": bid_size,
                        "tail_net_pnl_usd": money(pnl), "exit_delay_sessions": delay,
                    })
                    tail_trades.append(pos.copy())
                    realized_total += pnl
                    continue

            if expired and row is not None and num(row.get("spotPrice")) is not None:
                intrinsic = max(float(row["spotPrice"]) - float(pos["strike"]), 0.0)
                pnl = option_closed_pnl(pos["entry_ask"], intrinsic)
                pos.update({
                    "status": "SETTLED_AT_EXPIRY_INTRINSIC", "exit_date": day,
                    "exit_bid": intrinsic, "exit_bid_size": None,
                    "tail_net_pnl_usd": money(pnl), "exit_delay_sessions": None,
                })
                tail_trades.append(pos.copy())
                realized_total += pnl
                continue
            keep.append(pos)
        active = keep

        for ep in entries_by_date.get(day, []):
            core_trade = trade_by_id.get(str(ep.get("episode_id")))
            core_exit = str((core_trade or {}).get("exit_date") or last_date)[:10]
            if core_exit not in date_set:
                core_exit = last_date
            candidate = pick_call(rows, day)
            if candidate is None:
                tail_entries.append({
                    "arm": arm, "episode_id": ep["episode_id"], "entry_date": day,
                    "status": "NO_EXECUTABLE_CALL_AT_OR_BELOW_0.10_WITH_SIZE_6",
                    "core_exit_date": core_exit, "contracts": CONTRACTS,
                    "premium_cap_per_share": TARGET_ASK,
                    "premium_budget_usd": CONTRACTS * MULTIPLIER * TARGET_ASK,
                })
                continue
            position = {
                "arm": arm, "episode_id": ep["episode_id"], "entry_date": day,
                "core_exit_date": core_exit, "expiry": candidate["expiry"],
                "strike": candidate["strike"], "dte_entry": candidate["dte_entry"],
                "spot_entry": candidate["spot_entry"], "entry_ask": candidate["entry_ask"],
                "entry_bid": candidate["entry_bid"], "entry_ask_size": candidate["entry_ask_size"],
                "entry_bid_size": candidate["entry_bid_size"], "entry_delta": candidate["entry_delta"],
                "entry_open_interest": candidate["entry_open_interest"], "entry_volume": candidate["entry_volume"],
                "entry_bid_iv": candidate["entry_bid_iv"], "entry_mid_iv": candidate["entry_mid_iv"],
                "entry_ask_iv": candidate["entry_ask_iv"], "entry_quote_updated_at": candidate["entry_quote_updated_at"],
                "contracts": CONTRACTS, "multiplier": MULTIPLIER,
                "premium_per_contract_usd": money(candidate["entry_ask"] * MULTIPLIER),
                "gross_premium_usd": money(candidate["entry_ask"] * MULTIPLIER * CONTRACTS),
                "entry_commission_usd": money(CONTRACTS * COMMISSION_PER_CONTRACT_PER_SIDE),
                "premium_cap_per_share": TARGET_ASK, "status": "OPEN",
                "last_bid": candidate["entry_bid"], "last_bid_size": candidate["entry_bid_size"],
                "last_mark_date": day, "stale_sessions": 0,
            }
            active.append(position)
            tail_entries.append({
                **{k: v for k, v in position.items() if k not in ("last_bid", "last_bid_size", "stale_sessions")},
                "status": "PURCHASED_AT_ASK",
            })

        unrealized = 0.0
        stale_positions = 0
        executable_bid_positions = 0
        for pos in active:
            mark_bid = max(0.0, float(pos.get("last_bid") or 0.0))
            unrealized += option_mark_pnl(pos["entry_ask"], mark_bid)
            stale_positions += int(pos.get("stale_sessions", 0) > 0)
            executable_bid_positions += int(pos.get("last_bid_size", 0) >= CONTRACTS and mark_bid > 0)
        tail_pnl = realized_total + unrealized
        daily.append({
            "date": day, "arm": arm, "core_nav_usd": money(core_nav[day]),
            "tail_realized_pnl_usd": money(realized_total), "tail_unrealized_pnl_usd": money(unrealized),
            "tail_total_pnl_usd": money(tail_pnl), "combined_nav_usd": money(core_nav[day] + tail_pnl),
            "active_tail_positions": len(active), "active_tail_contracts": len(active) * CONTRACTS,
            "positions_with_executable_6_lot_bid": executable_bid_positions,
            "stale_tail_positions": stale_positions,
        })

    for pos in active:
        mark = option_mark_pnl(pos["entry_ask"], max(0.0, float(pos.get("last_bid") or 0.0)))
        pos.update({
            "status": "UNRESOLVED_SOURCE_END", "exit_date": None,
            "exit_bid": pos.get("last_bid"), "tail_net_pnl_usd": money(mark),
            "stale_sessions_at_source_end": pos.get("stale_sessions", 0),
        })
        tail_trades.append(pos.copy())

    tail_trade_map = {str(t.get("episode_id")): t for t in tail_trades}
    resolved_core = [t for t in trades if num(t.get("net_pnl_usd")) is not None]
    core_losers = [t for t in resolved_core if float(t["net_pnl_usd"]) < 0]
    loser_pairs = []
    for core in core_losers:
        hedge = tail_trade_map.get(str(core.get("episode_id")))
        if hedge and num(hedge.get("tail_net_pnl_usd")) is not None:
            loser_pairs.append({
                "episode_id": core.get("episode_id"), "core_net_pnl_usd": float(core["net_pnl_usd"]),
                "tail_net_pnl_usd": float(hedge["tail_net_pnl_usd"]),
            })

    navs = [float(r["combined_nav_usd"]) for r in daily]
    peak, max_dd_usd, max_dd_pct = None, 0.0, 0.0
    for value in navs:
        peak = value if peak is None else max(peak, value)
        max_dd_usd = min(max_dd_usd, value - peak)
        max_dd_pct = min(max_dd_pct, (value / peak - 1.0) * 100.0 if peak > 0 else 0.0)
    start_nav, end_nav = navs[0], navs[-1]
    years = (date.fromisoformat(dates[-1]) - date.fromisoformat(dates[0])).days / 365.25
    cagr = ((end_nav / start_nav) ** (1.0 / years) - 1.0) * 100.0 if years > 0 and end_nav > 0 else None
    purchased = [x for x in tail_entries if x.get("status") == "PURCHASED_AT_ASK"]
    blocked = [x for x in tail_entries if x.get("status") != "PURCHASED_AT_ASK"]
    total_premium = sum(float(x["gross_premium_usd"]) for x in purchased)
    total_entry_fees = sum(float(x["entry_commission_usd"]) for x in purchased)
    total_tail_pnl = float(daily[-1]["tail_total_pnl_usd"])
    positive_tail = sum(x["tail_net_pnl_usd"] > 0 for x in loser_pairs)
    offset25 = sum(x["tail_net_pnl_usd"] >= 0.25 * abs(x["core_net_pnl_usd"]) for x in loser_pairs)
    total_core_loss = sum(abs(float(x["net_pnl_usd"])) for x in core_losers)
    tail_gain_on_losers = sum(max(0.0, x["tail_net_pnl_usd"]) for x in loser_pairs)
    worst_core = min(resolved_core, key=lambda x: float(x["net_pnl_usd"])) if resolved_core else None
    worst_hedged = None
    if worst_core:
        hedge = tail_trade_map.get(str(worst_core.get("episode_id")))
        if hedge:
            worst_hedged = float(worst_core["net_pnl_usd"]) + float(hedge["tail_net_pnl_usd"])
    return {
        "arm": arm, "core_entries": len(entries), "tail_purchased": len(purchased),
        "tail_entry_blocked": len(blocked),
        "tail_fill_coverage_pct": money(100.0 * len(purchased) / max(len(entries), 1)),
        "contracts_purchased": len(purchased) * CONTRACTS,
        "target_premium_budget_usd": money(len(entries) * CONTRACTS * MULTIPLIER * TARGET_ASK),
        "actual_gross_premium_paid_usd": money(total_premium), "entry_commissions_usd": money(total_entry_fees),
        "avg_entry_ask_per_share": money(statistics.mean([x["entry_ask"] for x in purchased])) if purchased else None,
        "median_entry_dte": statistics.median([x["dte_entry"] for x in purchased]) if purchased else None,
        "median_entry_delta": statistics.median([x["entry_delta"] for x in purchased]) if purchased else None,
        "tail_total_pnl_usd": money(total_tail_pnl),
        "tail_roi_on_gross_premium_pct": money(100.0 * total_tail_pnl / total_premium) if total_premium else None,
        "core_ending_nav_usd": money(core_nav[last_date]), "combined_ending_nav_usd": money(end_nav),
        "combined_cagr_pct": money(cagr) if cagr is not None else None,
        "combined_max_drawdown_usd": money(max_dd_usd), "combined_max_drawdown_pct": money(max_dd_pct),
        "core_losing_resolved_trades": len(core_losers), "losers_with_tail_quote_result": len(loser_pairs),
        "core_losers_with_tail_gain": positive_tail,
        "tail_positive_coverage_of_core_losses_pct": money(100.0 * positive_tail / max(len(core_losers), 1)),
        "tail_positive_coverage_among_quoted_core_losses_pct": money(100.0 * positive_tail / max(len(loser_pairs), 1)),
        "core_losers_offset_by_25pct": offset25,
        "core_losers_offset_by_25pct_pct": money(100.0 * offset25 / max(len(core_losers), 1)),
        "core_loss_dollars_usd": money(total_core_loss),
        "positive_tail_pnl_on_core_losers_usd": money(tail_gain_on_losers),
        "tail_gain_as_pct_of_core_loss_dollars": money(100.0 * tail_gain_on_losers / total_core_loss) if total_core_loss else None,
        "worst_core_trade_net_pnl_usd": money(float(worst_core["net_pnl_usd"])) if worst_core else None,
        "worst_core_trade_after_tail_usd": money(worst_hedged) if worst_hedged is not None else None,
        "active_tail_positions_at_end": len(active),
        "unresolved_tail_trades_at_end": sum(x.get("status") == "UNRESOLVED_SOURCE_END" for x in tail_trades),
        "tail_trade_count": len(tail_trades),
        "tail_entry_rows": tail_entries, "tail_trade_rows": tail_trades,
        "tail_daily_rows": daily, "tail_quote_audit_rows": quote_audit,
    }


def write_blocked_status(data_dir, out_dir, reason="MISSING_ORATS_API_TOKEN"):
    data_dir, out_dir = Path(data_dir), Path(out_dir)
    arms = (
        "SPY_SHORT_QQQ_LONG_only", "QQQ_SHORT_SPY_LONG_only",
        "SPY_SHORT_QQQ_LONG_only_hold10", "QQQ_SHORT_SPY_LONG_only_hold10",
        "alternate_weekly_close", "alternate_two_week_staggered",
    )
    counts = {}
    for arm in arms:
        path = data_dir / f"{arm}_entries.csv"
        counts[arm] = len(load_csv(path)) if path.is_file() else None
    payload = {
        "schema": SCHEMA, "status": "BLOCKED_DATA_ACCESS", "reason": reason,
        "ticker": SYMBOL, "direction": "LONG_CALL", "contracts_per_cohort": CONTRACTS,
        "premium_limit_per_share_usd": TARGET_ASK,
        "maximum_gross_premium_per_cohort_usd": CONTRACTS * MULTIPLIER * TARGET_ASK,
        "entry_dte_range_calendar_days": [MIN_DTE, MAX_DTE],
        "target_entry_dte_calendar_days": TARGET_DTE, "core_cohort_counts": counts,
        "required_environment_secret": "ORATS_API_TOKEN", "data_source": API_URL, "data_fields": FIELDS,
        "note": "No option-return estimates were generated. TAIL ETF share prices are not substituted for TAIL CALL quotes.",
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "TAIL_CALL_MANIFEST.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# TAIL CALL insurance overlay", "",
        "**Status: BLOCKED — historical TAIL option quotes not yet authorized/available.**", "",
        f"Core cohorts found: {sum(v or 0 for v in counts.values())}.",
        "Per core cohort: buy 6 TAIL CALL contracts, standard multiplier 100, limit no higher than USD 0.10/share.",
        "Maximum gross option premium: USD 60 per cohort, plus commissions. Actual cost will be the observed Ask, not a forced USD 60.",
        f"Entry selection: OTM calls, {MIN_DTE}–{MAX_DTE} calendar DTE (target {TARGET_DTE}), Ask <= USD 0.10, displayed Ask size >= 6; closest Ask to USD 0.10 first.",
        "Daily mark: NBBO Bid. Exit: follow the core cohort's exit date; defer if a six-lot bid is unavailable, then settle at intrinsic on expiry if expiry quotes are present.", "",
        "No option P&L, hedge coverage, CAGR or MaxDD is reported because no historical TAIL CALL bid/ask/size series was available.",
        "Required: provide ORATS historical Data API access by adding GitHub Actions secret ORATS_API_TOKEN to this repository. The published Delayed Data API plan is USD 199/month and includes historical EOD options data; this research does not purchase a subscription.",
        "The existing TAIL ETF adjusted-close overlay is not used as a substitute for option P&L.", "",
    ]
    (out_dir / "TAIL_CALL_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    return payload


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="research/alternating_qqq_spy_put_cycle_v1/results/latest")
    parser.add_argument("--out-dir", default="research/alternating_qqq_spy_put_cycle_v1/results/latest")
    parser.add_argument("--cache-dir", default=os.path.expanduser("~/.cache/tail-orats-eod"))
    parser.add_argument("--blocked", action="store_true")
    parser.add_argument("--pause-seconds", type=float, default=0.12)
    args = parser.parse_args()
    data_dir, out_dir = Path(args.data_dir), Path(args.out_dir)
    if args.blocked or not os.environ.get("ORATS_API_TOKEN", "").strip():
        status = write_blocked_status(data_dir, out_dir)
        print(json.dumps({"status": status["status"], "reason": status["reason"]}))
        return

    arms = (
        "SPY_SHORT_QQQ_LONG_only", "QQQ_SHORT_SPY_LONG_only",
        "SPY_SHORT_QQQ_LONG_only_hold10", "QQQ_SHORT_SPY_LONG_only_hold10",
        "alternate_weekly_close", "alternate_two_week_staggered",
    )
    dates = all_dates(arms, data_dir)
    cache_dir = Path(args.cache_dir)
    daily_quotes, source_rows = {}, []
    for index, day in enumerate(dates, 1):
        rows, digest, source_kind = fetch_day(day, os.environ["ORATS_API_TOKEN"].strip(), cache_dir)
        daily_quotes[day] = rows
        source_rows.append({"date": day, "sha256": digest, "source": source_kind, "rows": len(rows)})
        if source_kind == "API":
            time.sleep(max(0.0, args.pause_seconds))
        if index % 100 == 0 or index == len(dates):
            print(f"TAIL ORATS EOD fetched {index}/{len(dates)} dates")

    results = [run_arm(arm, data_dir, daily_quotes) for arm in arms]
    summary = [{k: v for k, v in result.items() if not k.endswith("_rows")} for result in results]
    out_dir.mkdir(parents=True, exist_ok=True)
    for result in results:
        arm = result["arm"]
        write_csv(out_dir / f"{arm}_tail_call_entries.csv", result["tail_entry_rows"])
        write_csv(out_dir / f"{arm}_tail_call_trades.csv", result["tail_trade_rows"])
        write_csv(out_dir / f"{arm}_tail_call_daily_nav.csv", result["tail_daily_rows"])
        write_csv(out_dir / f"{arm}_tail_call_quote_audit.csv", result["tail_quote_audit_rows"])
        core_daily = load_csv(data_dir / f"{arm}_daily_nav.csv")
        tail_daily = {r["date"]: r for r in result["tail_daily_rows"]}
        combined = [{
            "date": core["date"], "arm": arm, "core_nav_usd": core["nav_usd"],
            "tail_pnl_usd": tail_daily[core["date"]]["tail_total_pnl_usd"],
            "combined_nav_usd": tail_daily[core["date"]]["combined_nav_usd"],
            "active_tail_positions": tail_daily[core["date"]]["active_tail_positions"],
            "stale_tail_positions": tail_daily[core["date"]]["stale_tail_positions"],
        } for core in core_daily]
        write_csv(out_dir / f"{arm}_combined_tail_call_daily_nav.csv", combined)

    payload = {
        "schema": SCHEMA,
        "status": "COMPLETED_WITH_ENTRY_GAPS" if any(x["tail_entry_blocked"] for x in summary) else "COMPLETED",
        "ticker": SYMBOL, "direction": "LONG_CALL", "contracts_per_cohort": CONTRACTS, "multiplier": MULTIPLIER,
        "premium_limit_per_share_usd": TARGET_ASK,
        "maximum_gross_premium_per_cohort_usd": CONTRACTS * MULTIPLIER * TARGET_ASK,
        "entry_rule": {
            "dte_min": MIN_DTE, "dte_max": MAX_DTE, "target_dte": TARGET_DTE, "otm_only": True,
            "max_ask": TARGET_ASK, "min_ask_size_contracts": CONTRACTS,
            "candidate_priority": ["closest_ask_to_0.10", "closest_dte_to_30", "larger_ask_size", "larger_open_interest"],
        },
        "exit_rule": "Exit from core cohort exit date at Bid only when displayed bid size >= 6; defer while unavailable; settle at intrinsic on expiration if same-day TAIL spot quote exists.",
        "mark_rule": "Daily mark at NBBO Bid; zero bid is marked at zero; missing quote carries last bid and increments stale count.",
        "costs": {"commission_per_contract_per_side_usd": COMMISSION_PER_CONTRACT_PER_SIDE,
                  "extra_slippage_beyond_natural_ask_bid_usd": 0.0},
        "source": {
            "provider": "ORATS Historical Data API", "endpoint": API_URL, "ticker": SYMBOL, "fields": FIELDS,
            "dates_requested": len(dates), "dates_with_rows": sum(x["rows"] > 0 for x in source_rows),
            "total_chain_rows": sum(x["rows"] for x in source_rows), "response_sha256_by_date": source_rows,
            "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        },
        "arms": summary,
        "limitations": [
            "Quotes are ORATS near-EOD snapshots, not guaranteed executable fills.",
            "An entry is counted only when Ask <= USD 0.10 and displayed Ask size >= 6.",
            "A closing fill requires positive Bid and displayed Bid size >= 6; otherwise exit is deferred.",
            "Displayed quote size and a historical snapshot do not prove six contracts would have filled at one price.",
            "The TAIL CALL overlay is additive to each core arm; delayed exits can leave tail exposure open after core close.",
            "Core financing, assignment and buying-power constraints remain those of the underlying core replay.",
        ],
    }
    (out_dir / "TAIL_CALL_MANIFEST.json").write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    lines = [
        "# TAIL CALL insurance overlay — six contracts at USD 0.10 limit", "",
        f"Status: **{payload['status']}**. Sample {dates[0]} to {dates[-1]}, {len(dates)} common sessions.",
        "Each entered core cohort attempts to buy six standard TAIL CALL contracts, multiplier 100, at the natural Ask with a hard limit of USD 0.10/share (maximum gross premium USD 60/cohort). The actual Ask is charged; no artificial USD 60 debit is inserted.",
        "Calls must be out-of-the-money, 21–45 calendar DTE (target 30), and show at least six contracts at the Ask. No entry is skipped because of core direction; only absence of an executable quote blocks that cohort's insurance.", "",
        "| Arm | Core entries | TAIL fills | Fill coverage | Premium paid | TAIL net P&L | Ending NAV core | Ending NAV + TAIL | Combined MaxDD |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for s in summary:
        lines.append(
            f"| {s['arm']} | {s['core_entries']} | {s['tail_purchased']} | {s['tail_fill_coverage_pct']:.2f}% | "
            f"USD {s['actual_gross_premium_paid_usd']:,.2f} | USD {s['tail_total_pnl_usd']:,.2f} | "
            f"USD {s['core_ending_nav_usd']:,.2f} | USD {s['combined_ending_nav_usd']:,.2f} | "
            f"{s['combined_max_drawdown_pct']:.2f}% |"
        )
    lines += ["", "## Coverage of losing core trades", "",
        "| Arm | Core losing trades | Tail positive on core losses | >=25% loss offset | Tail positive P&L / core loss dollars | Worst core trade | Same trade after TAIL |",
        "|---|---:|---:|---:|---:|---:|---:|"]
    for s in summary:
        worst_after = s["worst_core_trade_after_tail_usd"]
        lines.append(
            f"| {s['arm']} | {s['core_losing_resolved_trades']} | {s['core_losers_with_tail_gain']} | "
            f"{s['core_losers_offset_by_25pct']} | USD {s['positive_tail_pnl_on_core_losers_usd']:,.2f} / "
            f"USD {s['core_loss_dollars_usd']:,.2f} ({(s['tail_gain_as_pct_of_core_loss_dollars'] or 0):.2f}%) | "
            f"USD {(s['worst_core_trade_net_pnl_usd'] or 0):,.2f} | "
            + (f"USD {worst_after:,.2f} |" if worst_after is not None else "n/a |")
        )
    lines += ["", "## Data and execution caveats", "",
        "- ORATS near-EOD historical quotes include call Bid/Ask, displayed Bid/Ask size, volume, OI, IV and Greeks.",
        "- Six displayed contracts at the Ask/Bid is a necessary screen, not proof of six fills without market impact.",
        "- Missing quote dates carry the last observed Bid for daily marking; stale counts are reported. Zero Bid marks at zero.",
        "- A zero Bid or Bid size below six prevents an executable close; the position is held until a six-lot positive Bid appears or expiration intrinsic settlement is available.",
        "- Every call can lose its full premium. Repeated insurance purchases can increase total strategy losses.", ""]
    (out_dir / "TAIL_CALL_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": payload["status"], "arms": summary}, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
