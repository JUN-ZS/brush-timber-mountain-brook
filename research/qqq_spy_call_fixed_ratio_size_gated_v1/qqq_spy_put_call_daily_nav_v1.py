#!/usr/bin/env python3
"""Daily mark-to-market acceptance for QQQ/SPY PUT+CALL 1:6 with a QQQ stock overlay.

Opening DTE target is 20; exit trigger is remaining calendar DTE <= 4. EOD quote-side
marks are research estimates, not a broker cash/margin simulation.
"""
from __future__ import annotations
import argparse, csv, json, math, sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
PUT_ENGINE_DIR = Path("research/qqq_spy_put_fixed_ratio_size_gated_v1").resolve()
if str(PUT_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(PUT_ENGINE_DIR))
import qqq_spy_put_premium_matched_phase_v1 as put_engine
import qqq_spy_call_premium_matched_phase_v1 as call_engine

CALL_ROOT = Path("research/qqq_spy_call_fixed_ratio_size_gated_v1/results/dte_hold_exit_factorial_call_v1")
OUT = CALL_ROOT / "daily_nav_dte20_exit4_v1"
REPLAY_ROOT = OUT / "replay"
UNIVERSE_PATH = Path("src/data/universe.json")
START, END = "2018-03-01", "2025-12-15"
DTE_MIN, DTE_MAX, DTE_TARGET = 14, 26, 20
PHASES = (0, 2, 4, 6, 8)
POLICY = "EXIT_AT_DTE_LE_4"
HUNDRED = 100.0
SLIPPAGE_PER_SHARE = 0.05
COMMISSION_PER_CONTRACT_PER_SIDE = 0.65
UNIT_COST = SLIPPAGE_PER_SHARE * HUNDRED + COMMISSION_PER_CONTRACT_PER_SIDE


def number(value):
    try:
        v = float(value)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def daystr(value):
    return value.isoformat()[:10] if hasattr(value, "isoformat") else str(value or "")[:10]


def normalize_contract_id(value):
    text = "".join(str(value or "").strip().upper().split())
    return text[2:] if text.startswith("O:") else text


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_json(path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def write_csv(path, rows, fields=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(dict.fromkeys(k for r in rows for k in r.keys() if not k.startswith("_")))
    if not fields:
        fields = ["status"]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def resolved(row):
    return str(row.get("status", "")).upper() == "RESOLVED" and number(row.get("net_pnl_usd")) is not None


def run_dte20_exit4_replay(side, phase, cache_root):
    engine = put_engine if side == "put" else call_engine
    target_delta = 0.25 if side == "put" else 0.20
    out = REPLAY_ROOT / side / f"phase_{phase}"
    required = ("summary.json", "entry_cohort.csv", "trade_episodes.csv", "source_manifest.json")
    if all((out / name).is_file() and (out / name).stat().st_size > 0 for name in required):
        old = read_json(out / "summary.json")
        selection = old.get("selection", {})
        if (selection.get("dte_target") == DTE_TARGET
                and abs(float(selection.get("target_abs_delta") or 0) - target_delta) < 1e-9
                and POLICY in old.get("policies", {})):
            return old
    # Targeted DTE20 replay only; the prior full PUT factorial is not rerun.
    engine.POLICIES = ({"policy": POLICY, "hold_sessions": None, "expiry_guard_dte": 4},)
    sys.argv = [
        str(Path(engine.__file__)), "--start", START, "--end", END,
        "--max-total-contracts", "10", "--entry-filter", "none",
        "--sizing-mode", "fixed_ratio", "--fixed-long-qty", "1", "--fixed-short-qty", "6",
        "--target-delta", str(target_delta), "--dte-min", str(DTE_MIN), "--dte-max", str(DTE_MAX),
        "--dte-target", str(DTE_TARGET), "--cohort-stride-sessions", "10",
        "--initial-phase-sessions", str(phase), "--allow-overlapping-cohorts",
        "--slippage-per-share", str(SLIPPAGE_PER_SHARE),
        "--commission-per-contract-per-side", str(COMMISSION_PER_CONTRACT_PER_SIDE),
        "--qqq-cache", str(cache_root / "qqq"), "--spy-cache", str(cache_root / "spy"),
        "--out", str(out),
    ]
    report = engine.run_replay(engine.parse_args())
    selection = report.get("selection", {})
    if selection.get("dte_target") != DTE_TARGET or POLICY not in report.get("policies", {}):
        raise RuntimeError(f"{side} replay did not honor DTE20 / DTE<=4: {selection}")
    if abs(float(selection.get("target_abs_delta") or 0) - target_delta) > 1e-9:
        raise RuntimeError(f"{side} target Delta mismatch: {selection}")
    return report


def strict_key(row):
    vals = tuple(str(row.get(k) or "") for k in ("signal_date", "expiry", "entry_date"))
    return vals if all(vals) else None


def pair_entries(put_rows, call_rows):
    put_rows = [r for r in put_rows if r.get("entry_date") and r.get("signal_date")]
    call_rows = [r for r in call_rows if r.get("entry_date") and r.get("signal_date")]
    p_by_signal = {str(r["signal_date"]): r for r in put_rows}
    c_by_signal = {str(r["signal_date"]): r for r in call_rows}
    common = set(p_by_signal) & set(c_by_signal)
    same_expiry = {s for s in common if p_by_signal[s].get("expiry") == c_by_signal[s].get("expiry")}
    same_entry = {s for s in same_expiry if p_by_signal[s].get("entry_date") == c_by_signal[s].get("entry_date")}
    p_by_key = {strict_key(r): r for r in put_rows if strict_key(r)}
    c_by_key = {strict_key(r): r for r in call_rows if strict_key(r)}
    pairs = []
    for key in sorted(set(p_by_key) & set(c_by_key),
                      key=lambda k: (int(float(p_by_key[k].get("signal_index") or 0)),
                                     int(float(p_by_key[k].get("entry_index") or 0)), k)):
        p, c = p_by_key[key], c_by_key[key]
        if int(float(p.get("signal_index") or 0)) != int(float(c.get("signal_index") or 0)):
            raise RuntimeError(f"paired signal index differs for {key}")
        if int(float(p.get("entry_index") or 0)) != int(float(c.get("entry_index") or 0)):
            raise RuntimeError(f"paired entry index differs for {key}")
        pairs.append({"signal_date": key[0], "expiry": key[1], "entry_date": key[2],
                      "signal_index": int(float(p.get("signal_index") or 0)),
                      "entry_index": int(float(p.get("entry_index") or 0)), "put": p, "call": c})
    return pairs, {
        "put_entered_cohorts": len(put_rows), "call_entered_cohorts": len(call_rows),
        "common_signal_dates": len(common), "same_expiry_signal_dates": len(same_expiry),
        "same_entry_date_signal_dates": len(same_entry), "strict_matched_pairs": len(pairs),
        "put_only_signal_dates": len(set(p_by_signal) - set(c_by_signal)),
        "call_only_signal_dates": len(set(c_by_signal) - set(p_by_signal)),
    }


def settlement_index(expiry, dates, date_to_index):
    if expiry in date_to_index:
        return date_to_index[expiry]
    eligible = [i for i, d in enumerate(dates) if d <= expiry]
    return eligible[-1] if eligible else 0


def terminal_index(trade, dates, date_to_index):
    if resolved(trade):
        exit_day = daystr(trade.get("exit_date"))
        if exit_day not in date_to_index:
            raise RuntimeError(f"resolved trade exit is not a common session: {exit_day}")
        return date_to_index[exit_day]
    expiry = daystr(trade.get("expiry"))
    if expiry and expiry <= dates[-1]:
        return settlement_index(expiry, dates, date_to_index)
    return len(dates)


def gate_pairs(pairs, dates, date_to_index, cap=1):
    selected, blocked = [], []
    for pair in sorted(pairs, key=lambda p: (p["signal_index"], p["entry_index"], p["signal_date"])):
        active = [s for s in selected
                  if max(terminal_index(s["put"], dates, date_to_index),
                         terminal_index(s["call"], dates, date_to_index)) > pair["signal_index"]]
        (selected if len(active) < cap else blocked).append(pair)
    return selected, blocked


def make_leg_position(pair, trade, strategy, leg_name, phase):
    if leg_name == "QQQ_LONG":
        symbol, right, side = "QQQ", ("P" if strategy == "PUT" else "C"), "LONG"
        contract = normalize_contract_id(trade.get("qqq_contract_id"))
        qty = int(float(trade.get("long_qqq_qty") or 0))
        entry, exit_price = number(trade.get("qqq_entry_ask")), number(trade.get("exit_qqq_bid"))
        gross_key, cost_key = "qqq_long_gross_pnl_usd", "qqq_long_cost_usd"
        entry_bid, entry_ask, strike = number(trade.get("qqq_entry_bid")), number(trade.get("qqq_entry_ask")), number(trade.get("qqq_strike"))
    else:
        symbol, right, side = "SPY", ("P" if strategy == "PUT" else "C"), "SHORT"
        contract = normalize_contract_id(trade.get("spy_contract_id"))
        qty = int(float(trade.get("short_spy_qty") or 0))
        entry, exit_price = number(trade.get("spy_entry_bid")), number(trade.get("exit_spy_ask"))
        gross_key, cost_key = "spy_short_gross_pnl_usd", "spy_short_cost_usd"
        entry_bid, entry_ask, strike = number(trade.get("spy_entry_bid")), number(trade.get("spy_entry_ask")), number(trade.get("spy_strike"))
    if not contract or qty < 1 or entry is None or entry <= 0 or strike is None:
        raise RuntimeError(f"invalid selected leg {strategy}/{leg_name}/{pair['signal_date']}")
    is_resolved = resolved(trade)
    final_pnl = None
    if is_resolved:
        gross, cost = number(trade.get(gross_key)), number(trade.get(cost_key))
        if gross is not None and cost is not None:
            final_pnl = gross - cost
        elif exit_price is not None:
            gross = qty * HUNDRED * ((exit_price - entry) if side == "LONG" else (entry - exit_price))
            final_pnl = gross - 2.0 * qty * UNIT_COST
        else:
            raise RuntimeError(f"resolved {strategy}/{leg_name} lacks exit P&L")
    return {
        "phase_sessions": phase, "signal_date": pair["signal_date"], "expiry": daystr(trade.get("expiry")),
        "entry_date": daystr(trade.get("entry_date")), "strategy": strategy, "leg_name": leg_name,
        "symbol": symbol, "right": right, "contract_id": contract, "position_side": side, "qty": qty,
        "strike": strike, "entry_price": entry, "entry_bid": entry_bid, "entry_ask": entry_ask,
        "exit_date": daystr(trade.get("exit_date")) if is_resolved else "",
        "exit_price": exit_price if is_resolved else None, "trade_status": str(trade.get("status") or ""),
        "is_resolved": is_resolved, "final_pnl_usd": final_pnl,
        "_source_trade_net_pnl_usd": number(trade.get("net_pnl_usd")),
        "_source_episode_id": str(trade.get("episode_id") or pair["signal_date"]),
        "terminal_kind": "RESOLVED" if is_resolved else "OPEN_END",
        "terminal_date": daystr(trade.get("exit_date")) if is_resolved else "",
        "last_quote_date": "", "last_bid": None, "last_ask": None, "_last_quote_index": None,
    }


def prepare_positions(pairs_by_phase, dates, date_to_index):
    positions_by_phase, diagnostics, audit_rows = {}, {}, []
    for phase, (pairs, base_diag) in pairs_by_phase.items():
        selected, blocked = gate_pairs(pairs, dates, date_to_index, cap=1)
        diag = dict(base_diag)
        diag.update({"admitted_paired_sets": len(selected), "capacity_skipped_matched_pairs": len(blocked)})
        positions = []
        for pair in selected:
            for strategy in ("PUT", "CALL"):
                trade = pair[strategy.lower()]
                for leg in ("QQQ_LONG", "SPY_SHORT"):
                    pos = make_leg_position(pair, trade, strategy, leg, phase)
                    if not pos["is_resolved"] and pos["expiry"] <= dates[-1]:
                        pos["terminal_kind"] = "INTRINSIC_SETTLEMENT_PROXY"
                        pos["terminal_date"] = dates[settlement_index(pos["expiry"], dates, date_to_index)]
                    positions.append(pos)
        positions_by_phase[phase] = positions
        diagnostics[phase] = diag
        audit_rows.append({"phase_sessions": phase, **diag})
    return positions_by_phase, diagnostics, audit_rows


def quote_valid(row):
    if not row:
        return False
    bid, ask = number(row.get("bid")), number(row.get("ask"))
    return bid is not None and ask is not None and bid >= 0 and ask > 0 and bid <= ask


def collect_selected_quotes(positions, engine, cache_root):
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.parquet as pq
    by_symbol = defaultdict(set)
    for pos in positions:
        by_symbol[pos["symbol"]].add(pos["contract_id"])
    quotes, integrity = {}, []
    for symbol in ("QQQ", "SPY"):
        wanted = by_symbol.get(symbol, set())
        if not wanted:
            continue
        raw_ids = wanted | {"O:" + x for x in wanted}
        for year in range(2018, 2026):
            path, meta = engine.download_verified(symbol, year, cache_root / symbol.lower())
            integrity.append(meta)
            parquet = pq.ParquetFile(path)
            names = {n.lower(): n for n in parquet.schema_arrow.names}
            cid_col = names.get("contract_id")
            if not cid_col:
                raise RuntimeError(f"{path.name} lacks contract_id")
            for batch in parquet.iter_batches(batch_size=131072, columns=list(engine.OPTION_COLUMNS)):
                cid_index = batch.schema.get_field_index(cid_col)
                if cid_index < 0:
                    raise RuntimeError(f"{path.name} batch lacks contract_id column")
                mask = pc.is_in(batch.column(cid_index), value_set=pa.array(sorted(raw_ids)))
                if not pc.any(mask).as_py():
                    continue
                for row in batch.filter(mask).to_pylist():
                    if str(row.get("symbol") or "").upper() != symbol:
                        continue
                    cid, day = normalize_contract_id(row.get("contract_id")), daystr(row.get("date"))
                    if cid not in wanted or not day or day < START or day > END or not quote_valid(row):
                        continue
                    quotes[(symbol, cid, day)] = {
                        "date": day, "bid": float(row["bid"]), "ask": float(row["ask"]),
                        "bid_size": number(row.get("bid_size")), "ask_size": number(row.get("ask_size")),
                    }
    return quotes, integrity


def load_underlying(engine, cache_root):
    qpath, qmeta = engine.download_verified("QQQ", None, cache_root / "qqq")
    spath, smeta = engine.download_verified("SPY", None, cache_root / "spy")
    qspots, sspots = engine.load_spots(qpath, "QQQ"), engine.load_spots(spath, "SPY")
    dates = sorted(d for d in (set(qspots) & set(sspots)) if START <= d <= END)
    if not dates or dates[0] != START:
        raise RuntimeError(f"invalid common underlying coverage: first={dates[0] if dates else None}")
    return dates, qspots, sspots, [qmeta, smeta]


def drawdown_metrics(rows):
    if not rows:
        raise RuntimeError("cannot calculate drawdown from an empty series")
    peak_value = float(rows[0].get("nav_usd", rows[0].get("portfolio_nav_usd")))
    peak_day = rows[0]["date"]
    max_dd_usd = max_dd_pct = 0.0
    max_peak_day = max_trough_day = rows[0]["date"]
    for row in rows:
        nav = float(row.get("nav_usd", row.get("portfolio_nav_usd")))
        if nav > peak_value:
            peak_value, peak_day = nav, row["date"]
        dd_usd = nav - peak_value
        dd_pct = (nav / peak_value - 1.0) * 100.0 if peak_value > 0 else None
        if dd_pct is not None and dd_pct < max_dd_pct:
            max_dd_pct, max_dd_usd = dd_pct, dd_usd
            max_peak_day, max_trough_day = peak_day, row["date"]
    return {"max_drawdown_usd": round(max_dd_usd, 2), "max_drawdown_pct": round(max_dd_pct, 4),
            "max_drawdown_peak_date": max_peak_day, "max_drawdown_trough_date": max_trough_day}


def load_stock_series(dates, qspots, stock_value, current_price, current_price_date):
    universe = read_json(UNIVERSE_PATH)
    universe_dates = [daystr(d) for d in universe["dates"]]
    adjusted = universe["c"]["QQQ"]
    if len(universe_dates) != len(adjusted):
        raise RuntimeError("HUB QQQ dates and adjusted-close values do not align")
    adjusted_by_date = dict(zip(universe_dates, adjusted))
    start_adj, start_raw = number(adjusted_by_date.get(START)), number(qspots.get(START))
    if start_adj is None or start_raw is None or min(start_adj, start_raw) <= 0:
        raise RuntimeError("could not anchor stock valuation on 2018-03-01")
    implied_shares = stock_value / current_price
    start_value = implied_shares * start_raw
    values = {}
    for d in dates:
        adj = number(adjusted_by_date.get(d))
        if adj is None or adj <= 0:
            raise RuntimeError(f"HUB adjusted close missing for daily NAV date {d}")
        values[d] = start_value * adj / start_adj
    stock_dd = drawdown_metrics([{"date": d, "nav_usd": values[d]} for d in dates])
    return values, {
        "stated_current_qqq_position_value_usd": stock_value, "current_qqq_price_reference_usd": current_price,
        "current_qqq_price_reference_date": current_price_date, "implied_current_shares": implied_shares,
        "historical_stock_value_at_start_usd": start_value, "stock_value_at_end_total_return_proxy_usd": values[dates[-1]],
        "stock_total_return_pnl_proxy_usd": values[dates[-1]] - start_value,
        "stock_only_max_drawdown_pct": stock_dd["max_drawdown_pct"],
        "stock_series_method": "Historical starting value is implied shares times raw QQQ close on 2018-03-01, scaled by HUB adjusted-close ratio (distribution-reinvestment proxy).",
        "warning": "USD 63,694 is treated as current holding value, not starting account capital; historical starting stock value is lower.",
    }


def intrinsic_value(right, spot, strike):
    return max(float(strike) - float(spot), 0.0) if right == "P" else max(float(spot) - float(strike), 0.0)


def mark_open_leg(pos, day, index, quote):
    if quote_valid(quote):
        pos["last_quote_date"], pos["last_bid"], pos["last_ask"] = day, float(quote["bid"]), float(quote["ask"])
        pos["_last_quote_index"] = index
        valuation, quote_age = "LIVE_QUOTE", 0
    else:
        if pos["last_bid"] is None or pos["last_ask"] is None or pos["_last_quote_index"] is None:
            raise RuntimeError(f"no live/prior option quote to value {pos['contract_id']} on {day}")
        valuation = "STALE_LAST_VALID_QUOTE"
        quote_age = max(0, index - int(pos["_last_quote_index"]))
    mark = pos["last_bid"] if pos["position_side"] == "LONG" else pos["last_ask"]
    gross = pos["qty"] * HUNDRED * ((mark - pos["entry_price"]) if pos["position_side"] == "LONG"
                                    else (pos["entry_price"] - mark))
    pnl = gross - 2.0 * pos["qty"] * UNIT_COST
    mv = mark * pos["qty"] * HUNDRED * (1.0 if pos["position_side"] == "LONG" else -1.0)
    return {"mark_price": mark, "bid": pos["last_bid"], "ask": pos["last_ask"],
            "quote_date_used": pos["last_quote_date"], "quote_age_sessions": quote_age,
            "valuation_method": valuation, "signed_open_market_value_usd": mv,
            "net_liquidation_pnl_usd": pnl, "realized_pnl_usd": 0.0,
            "unrealized_pnl_usd": pnl, "is_open_eod": True}


def position_value_for_day(pos, day, index, quote_map, qspots, sspots, dates, date_to_index):
    entry_index = date_to_index.get(pos["entry_date"])
    if entry_index is None:
        raise RuntimeError(f"position entry date not in common session list: {pos['entry_date']}")
    if index < entry_index:
        return None
    terminal_kind, terminal_day = pos["terminal_kind"], pos["terminal_date"]
    terminal_index = date_to_index.get(terminal_day, len(dates))
    if terminal_kind == "RESOLVED" and index >= terminal_index:
        pnl = float(pos["final_pnl_usd"])
        return {"mark_price": pos["exit_price"], "bid": None, "ask": None,
                "quote_date_used": terminal_day, "quote_age_sessions": 0, "valuation_method": "REALIZED_EXIT_PNL",
                "signed_open_market_value_usd": 0.0, "net_liquidation_pnl_usd": pnl,
                "realized_pnl_usd": pnl, "unrealized_pnl_usd": 0.0, "is_open_eod": False}
    if terminal_kind == "INTRINSIC_SETTLEMENT_PROXY" and index >= terminal_index:
        spots = qspots if pos["symbol"] == "QQQ" else sspots
        spot, strike = number(spots.get(terminal_day)), number(pos["strike"])
        if spot is None or strike is None:
            raise RuntimeError(f"missing underlying close for expiry settlement {pos['contract_id']} {terminal_day}")
        intrinsic = intrinsic_value(pos["right"], spot, strike)
        gross = pos["qty"] * HUNDRED * ((intrinsic - pos["entry_price"]) if pos["position_side"] == "LONG"
                                        else (pos["entry_price"] - intrinsic))
        pnl = gross - pos["qty"] * UNIT_COST  # Entry-side cost only; exercise/assignment fees excluded.
        pos["final_pnl_usd"] = pnl
        return {"mark_price": intrinsic, "bid": None, "ask": None, "quote_date_used": terminal_day,
                "quote_age_sessions": 0, "valuation_method": "EXPIRY_INTRINSIC_SETTLEMENT_PROXY",
                "signed_open_market_value_usd": 0.0, "net_liquidation_pnl_usd": pnl,
                "realized_pnl_usd": pnl, "unrealized_pnl_usd": 0.0, "is_open_eod": False}
    quote = quote_map.get((pos["symbol"], pos["contract_id"], day))
    return mark_open_leg(pos, day, index, quote)


def build_daily_curve(positions, quote_map, dates, date_to_index, qspots, sspots, stock_by_date, phase, diagnostics):
    daily, leg_rows = [], []
    max_put_obligation = max_call_delivery = 0.0
    for index, day in enumerate(dates):
        realized_total = unrealized_total = open_mv = 0.0
        active_legs = valued_legs = stale_legs = unresolved_live = 0
        max_stale_age = resolved_legs_today = settled_legs_today = 0
        put_obligation = call_delivery = 0.0
        for pos in positions:
            value = position_value_for_day(pos, day, index, quote_map, qspots, sspots, dates, date_to_index)
            if value is None:
                continue
            valued_legs += 1
            realized_total += float(value["realized_pnl_usd"])
            unrealized_total += float(value["unrealized_pnl_usd"])
            open_mv += float(value["signed_open_market_value_usd"])
            method = value["valuation_method"]
            if value["is_open_eod"]:
                active_legs += 1
                if method == "STALE_LAST_VALID_QUOTE":
                    stale_legs += 1
                    max_stale_age = max(max_stale_age, int(value["quote_age_sessions"]))
                if pos["trade_status"] != "RESOLVED":
                    unresolved_live += 1
                if pos["expiry"] <= day:
                    raise RuntimeError(f"expired option remains marked as open: {pos['contract_id']} on {day}")
                if pos["symbol"] == "SPY" and pos["position_side"] == "SHORT":
                    notional = float(pos["strike"]) * HUNDRED * int(pos["qty"])
                    if pos["right"] == "P":
                        put_obligation += notional
                    else:
                        call_delivery += notional
            elif method == "REALIZED_EXIT_PNL" and pos["exit_date"] == day:
                resolved_legs_today += 1
            elif method == "EXPIRY_INTRINSIC_SETTLEMENT_PROXY" and pos["terminal_date"] == day:
                settled_legs_today += 1
            if day == pos["entry_date"] or value["is_open_eod"] or (
                method in ("REALIZED_EXIT_PNL", "EXPIRY_INTRINSIC_SETTLEMENT_PROXY") and pos["terminal_date"] == day
            ):
                leg_rows.append({
                    "phase_sessions": phase, "date": day, "signal_date": pos["signal_date"], "expiry": pos["expiry"],
                    "entry_date": pos["entry_date"], "terminal_date": pos["terminal_date"], "strategy": pos["strategy"],
                    "leg_name": pos["leg_name"], "symbol": pos["symbol"], "right": pos["right"],
                    "contract_id": pos["contract_id"], "position_side": pos["position_side"], "qty": pos["qty"],
                    "strike": pos["strike"], "trade_status": pos["trade_status"], "valuation_method": method,
                    "quote_date_used": value["quote_date_used"], "quote_age_sessions": value["quote_age_sessions"],
                    "bid": value["bid"], "ask": value["ask"], "mark_price": value["mark_price"],
                    "signed_open_market_value_usd": round(value["signed_open_market_value_usd"], 2),
                    "net_liquidation_pnl_usd": round(value["net_liquidation_pnl_usd"], 2),
                    "realized_pnl_usd": round(value["realized_pnl_usd"], 2),
                    "unrealized_pnl_usd": round(value["unrealized_pnl_usd"], 2), "is_open_eod": value["is_open_eod"],
                })
        max_put_obligation, max_call_delivery = max(max_put_obligation, put_obligation), max(max_call_delivery, call_delivery)
        nav = float(stock_by_date[day]) + realized_total + unrealized_total
        daily.append({
            "phase_sessions": phase, "date": day, "stock_market_value_total_return_proxy_usd": round(stock_by_date[day], 2),
            "cumulative_realized_option_pnl_usd": round(realized_total, 2),
            "open_option_net_liquidation_pnl_usd": round(unrealized_total, 2),
            "total_option_net_pnl_usd": round(realized_total + unrealized_total, 2),
            "open_option_signed_market_value_usd": round(open_mv, 2), "portfolio_nav_usd": round(nav, 2),
            "running_peak_nav_usd": None, "drawdown_usd": None, "drawdown_pct": None,
            "valued_option_legs": valued_legs, "open_option_legs_eod": active_legs,
            "unresolved_live_option_legs": unresolved_live, "stale_mark_option_legs": stale_legs,
            "max_stale_quote_age_sessions": max_stale_age, "realized_option_legs_today": resolved_legs_today,
            "intrinsic_settled_legs_today": settled_legs_today,
            "gross_spy_short_put_assignment_obligation_usd": round(put_obligation, 2),
            "gross_spy_short_call_delivery_notional_usd": round(call_delivery, 2),
        })
    peak, peak_day = -float("inf"), ""
    for row in daily:
        nav = float(row["portfolio_nav_usd"])
        if nav > peak:
            peak, peak_day = nav, row["date"]
        row["running_peak_nav_usd"] = round(peak, 2)
        row["drawdown_usd"] = round(nav - peak, 2)
        row["drawdown_pct"] = round((nav / peak - 1.0) * 100.0, 4) if peak > 0 else None
    summary = drawdown_metrics(daily)
    summary.update({
        "phase_sessions": phase, "start_date": dates[0], "end_date": dates[-1], "daily_rows": len(daily),
        "start_nav_usd": daily[0]["portfolio_nav_usd"], "end_nav_usd": daily[-1]["portfolio_nav_usd"],
        "total_nav_change_usd": round(float(daily[-1]["portfolio_nav_usd"]) - float(daily[0]["portfolio_nav_usd"]), 2),
        "total_nav_return_pct": round((float(daily[-1]["portfolio_nav_usd"]) / float(daily[0]["portfolio_nav_usd"]) - 1) * 100, 4)
            if float(daily[0]["portfolio_nav_usd"]) > 0 else None,
        "final_realized_option_pnl_usd": daily[-1]["cumulative_realized_option_pnl_usd"],
        "final_unrealized_option_pnl_usd": daily[-1]["open_option_net_liquidation_pnl_usd"],
        "final_total_option_net_pnl_usd": daily[-1]["total_option_net_pnl_usd"],
        "final_open_option_legs": daily[-1]["open_option_legs_eod"],
        "max_open_option_legs": max(int(r["open_option_legs_eod"]) for r in daily),
        "max_stale_mark_option_legs_any_day": max(int(r["stale_mark_option_legs"]) for r in daily),
        "max_quote_staleness_sessions": max(int(r["max_stale_quote_age_sessions"]) for r in daily),
        "max_gross_spy_put_assignment_obligation_usd": round(max_put_obligation, 2),
        "max_gross_spy_call_delivery_notional_usd": round(max_call_delivery, 2),
        **diagnostics,
    })
    return daily, leg_rows, summary


def audit_entry_exit_quotes(positions, quote_map):
    checked_entry = checked_exit = entry_missing = exit_missing = 0
    mismatches = []
    for pos in positions:
        q = quote_map.get((pos["symbol"], pos["contract_id"], pos["entry_date"]))
        if not quote_valid(q):
            entry_missing += 1
            continue
        checked_entry += 1
        actual = q["ask"] if pos["position_side"] == "LONG" else q["bid"]
        if abs(float(actual) - float(pos["entry_price"])) > 0.011:
            mismatches.append({"field": "entry", "contract_id": pos["contract_id"], "date": pos["entry_date"],
                               "ledger": pos["entry_price"], "source_quote": actual})
        if pos["is_resolved"]:
            qx = quote_map.get((pos["symbol"], pos["contract_id"], pos["exit_date"]))
            if not quote_valid(qx):
                exit_missing += 1
                continue
            checked_exit += 1
            actual_exit = qx["bid"] if pos["position_side"] == "LONG" else qx["ask"]
            if pos["exit_price"] is None or abs(float(actual_exit) - float(pos["exit_price"])) > 0.011:
                mismatches.append({"field": "exit", "contract_id": pos["contract_id"], "date": pos["exit_date"],
                                   "ledger": pos["exit_price"], "source_quote": actual_exit})
    if entry_missing or exit_missing or mismatches:
        raise RuntimeError(f"quote reconciliation failed: missing entry={entry_missing}, missing exit={exit_missing}, "
                           f"price mismatches={len(mismatches)}, sample={mismatches[:3]}")
    return {"entry_leg_quotes_reconciled": checked_entry, "resolved_exit_leg_quotes_reconciled": checked_exit,
            "entry_quotes_missing": entry_missing, "exit_quotes_missing": exit_missing, "entry_exit_price_mismatches": 0}


def audit_trade_pnl_reconciliation(positions):
    """Reconcile each resolved two-leg trade against the replay ledger's net P&L."""
    groups = defaultdict(list)
    for pos in positions:
        if pos["is_resolved"]:
            key = (pos["phase_sessions"], pos["strategy"], pos["_source_episode_id"],
                   pos["signal_date"], pos["entry_date"])
            groups[key].append(pos)
    checked = 0
    mismatches = []
    for key, legs in groups.items():
        if len(legs) != 2 or {r["leg_name"] for r in legs} != {"QQQ_LONG", "SPY_SHORT"}:
            mismatches.append({"key": key, "reason": "expected exactly QQQ_LONG and SPY_SHORT legs", "legs": len(legs)})
            continue
        source_values = [number(r.get("_source_trade_net_pnl_usd")) for r in legs]
        actual = sum(float(r["final_pnl_usd"]) for r in legs if r.get("final_pnl_usd") is not None)
        if any(v is None for v in source_values):
            mismatches.append({"key": key, "reason": "missing source trade net P&L"})
            continue
        expected = float(source_values[0])
        if any(abs(float(v) - expected) > 0.02 for v in source_values) or abs(actual - expected) > 0.02:
            mismatches.append({"key": key, "expected": expected, "actual": actual, "per_leg_source": source_values})
            continue
        checked += 1
    if mismatches:
        raise RuntimeError(f"resolved two-leg P&L does not reconcile for {len(mismatches)} trades; sample={mismatches[:3]}")
    return {"resolved_trade_groups_reconciled": checked, "mismatches": 0,
            "reconciliation_tolerance_usd": 0.02,
            "method": "QQQ_LONG gross minus leg cost + SPY_SHORT gross minus leg cost equals source trade net P&L"}


def audit_daily_leg_mark_coverage(positions, leg_rows, dates, date_to_index):
    """Require one finite valuation row for every selected option leg on every held session."""
    if not dates:
        raise RuntimeError("cannot audit option-leg marks without dates")

    def key(row):
        return tuple(str(row.get(k) or "") for k in (
            "phase_sessions", "strategy", "signal_date", "leg_name", "contract_id", "entry_date"
        ))

    expected_by_key = {}
    for pos in positions:
        pos_key = key(pos)
        if pos_key in expected_by_key:
            raise RuntimeError(f"duplicate option position key in daily valuation audit: {pos_key}")
        entry_day = daystr(pos.get("entry_date"))
        if entry_day not in date_to_index:
            raise RuntimeError(f"entry date missing from valuation calendar: {pos_key} {entry_day}")
        start_index = date_to_index[entry_day]
        terminal_kind = str(pos.get("terminal_kind") or "OPEN_END")
        terminal_day = daystr(pos.get("terminal_date"))
        if terminal_kind in ("RESOLVED", "INTRINSIC_SETTLEMENT_PROXY"):
            if terminal_day not in date_to_index:
                raise RuntimeError(f"terminal date missing from valuation calendar: {pos_key} {terminal_day}")
            end_index = date_to_index[terminal_day]
        else:
            end_index = len(dates) - 1
        if end_index < start_index:
            raise RuntimeError(f"option position terminal date precedes entry: {pos_key}")
        expected_by_key[pos_key] = set(dates[start_index:end_index + 1])

    actual_by_key = defaultdict(list)
    invalid_rows = []
    for row in leg_rows:
        row_key = key(row)
        actual_by_key[row_key].append(str(row.get("date") or ""))
        if number(row.get("mark_price")) is None or not str(row.get("valuation_method") or ""):
            invalid_rows.append({"key": row_key, "date": row.get("date"),
                                 "mark_price": row.get("mark_price"),
                                 "valuation_method": row.get("valuation_method")})

    missing = []
    extra = []
    duplicate = []
    for pos_key, expected_days in expected_by_key.items():
        observed_list = actual_by_key.get(pos_key, [])
        observed_days = set(observed_list)
        if len(observed_list) != len(observed_days):
            duplicate.append({"key": pos_key, "count": len(observed_list),
                              "unique_dates": len(observed_days)})
        for d in sorted(expected_days - observed_days):
            missing.append({"key": pos_key, "date": d})
        for d in sorted(observed_days - expected_days):
            extra.append({"key": pos_key, "date": d})
    unknown_keys = sorted(set(actual_by_key) - set(expected_by_key))
    if unknown_keys:
        extra.extend({"key": k, "date": d} for k in unknown_keys for d in sorted(set(actual_by_key[k])))
    if missing or extra or duplicate or invalid_rows:
        raise RuntimeError(
            "daily option-leg valuation coverage failed: "
            f"missing={len(missing)}, extra={len(extra)}, duplicates={len(duplicate)}, "
            f"invalid_rows={len(invalid_rows)}; "
            f"samples={{'missing':{missing[:3]},'extra':{extra[:3]},"
            f"'duplicates':{duplicate[:3]},'invalid':{invalid_rows[:3]}}}"
        )
    expected_rows = sum(len(v) for v in expected_by_key.values())
    return {
        "status": "PASS",
        "position_legs": len(expected_by_key),
        "expected_daily_leg_mark_rows": expected_rows,
        "actual_daily_leg_mark_rows": len(leg_rows),
        "missing_daily_leg_marks": 0,
        "duplicate_daily_leg_marks": 0,
        "extra_daily_leg_marks": 0,
        "invalid_or_unpriced_leg_marks": 0,
        "method": "Exact one-to-one coverage by phase/strategy/signal/leg/contract: every session from entry through exit/expiry settlement or source end.",
    }


def render_report(stock, summaries, diagnostics, quote_audit, quote_integrity, pnl_audit, leg_coverage_audit):
    lines = [
        "# Daily portfolio NAV and maximum drawdown — DTE20 / exit DTE <= 4", "",
        f"- Replay period: {START} through {summaries[0]['end_date']}; {summaries[0]['daily_rows']} common-session marks per phase.",
        "- Options: QQQ LONG PUT 1 : SPY SHORT PUT 6 (target abs-Delta 0.25) plus QQQ LONG CALL 1 : SPY SHORT CALL 6 (target abs-Delta 0.20).",
        "- Entry: DTE20 band 14-26, no filter, every 10 common sessions with independent phases 0/2/4/6/8. Exit trigger is remaining calendar DTE <=4; exit is deferred until executable quote/size criteria are met.",
        "- Pairing: same signal date, expiry and actual entry date; maximum one matched PUT+CALL basket at a time in each independent phase.",
        f"- QQQ holding input: USD {stock['stated_current_qqq_position_value_usd']:,.2f} current value, reference close USD {stock['current_qqq_price_reference_usd']:,.2f} on {stock['current_qqq_price_reference_date']}; implied shares {stock['implied_current_shares']:.4f}.",
        f"- Historical stock starting value: USD {stock['historical_stock_value_at_start_usd']:,.2f}; ending total-return proxy value: USD {stock['stock_value_at_end_total_return_proxy_usd']:,.2f}.",
        "- Stock path is the 2018-03-01 raw QQQ close scaled by HUB adjusted-close ratio (distribution-reinvestment proxy). Options use exact-contract EOD quotes; longs marked at bid, shorts at ask. Missing daily quotes carry forward with stale age flagged.",
        "- Resolved option-leg P&L persists in NAV after exit. Every open option leg is valued daily. Unresolved options reaching expiry receive an intrinsic-settlement proxy; source-end open legs stay marked at last quote.",
        "- Resolved trades deduct USD 0.05/share/side slippage plus USD 0.65/contract/side commission. Expiry settlement proxy deducts entry-side costs only; exercise/assignment fees are not modeled.",
        "- NAV = stock value proxy + cumulative realized option-leg P&L + open option net-liquidation P&L. This is not broker buying power, cash, margin, tax or forced-liquidation simulation.", "",
        "## Quote/data acceptance", "",
        f"- Entry-leg source quotes reconciled: {quote_audit['entry_leg_quotes_reconciled']}; resolved exit-leg quotes reconciled: {quote_audit['resolved_exit_leg_quotes_reconciled']}.",
        f"- Missing entry quotes: {quote_audit['entry_quotes_missing']}; missing exit quotes: {quote_audit['exit_quotes_missing']}; price mismatches: {quote_audit['entry_exit_price_mismatches']}.",
        f"- Resolved two-leg trade P&L reconciled to source replay: {pnl_audit['resolved_trade_groups_reconciled']}; mismatches: {pnl_audit['mismatches']}.",
        f"- Daily option-leg valuation coverage: {leg_coverage_audit['actual_daily_leg_mark_rows']}/{leg_coverage_audit['expected_daily_leg_mark_rows']} expected leg-session marks; missing/duplicate/unpriced: {leg_coverage_audit['missing_daily_leg_marks']}/{leg_coverage_audit['duplicate_daily_leg_marks']}/{leg_coverage_audit['invalid_or_unpriced_leg_marks']}.",
        f"- SHA-pinned option parquet files scanned: {len(quote_integrity)}; source {put_engine.SOURCE_REPO}@{put_engine.SOURCE_COMMIT}.", "",
        "## Daily NAV and maximum drawdown by independent phase", "",
        "| Phase | Strict matches | Admitted | Skipped | Start NAV | End NAV | Change | Max DD USD | Max DD % | Peak | Trough | Final realized option P&L | Final open option P&L | Max SPY put obligation | Max SPY call delivery notional | Max stale age |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---:|---:|---:|---:|---:|",
    ]
    for r in summaries:
        lines.append(
            f"| {r['phase_sessions']} | {r['strict_matched_pairs']} | {r['admitted_paired_sets']} | {r['capacity_skipped_matched_pairs']} | "
            f"USD {r['start_nav_usd']:,.2f} | USD {r['end_nav_usd']:,.2f} | USD {r['total_nav_change_usd']:,.2f} | "
            f"USD {r['max_drawdown_usd']:,.2f} | {r['max_drawdown_pct']:.2f}% | {r['max_drawdown_peak_date']} | {r['max_drawdown_trough_date']} | "
            f"USD {r['final_realized_option_pnl_usd']:,.2f} | USD {r['final_unrealized_option_pnl_usd']:,.2f} | "
            f"USD {r['max_gross_spy_put_assignment_obligation_usd']:,.2f} | USD {r['max_gross_spy_call_delivery_notional_usd']:,.2f} | {r['max_quote_staleness_sessions']} |"
        )
    lines += ["", "## Matching / capacity diagnostics", "",
              "| Phase | PUT entries | CALL entries | Common signals | Same expiry | Same entry | Strict pairs | Admitted | Skipped | PUT-only signals | CALL-only signals |",
              "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for phase, d in sorted(diagnostics.items()):
        lines.append(f"| {phase} | {d['put_entered_cohorts']} | {d['call_entered_cohorts']} | {d['common_signal_dates']} | {d['same_expiry_signal_dates']} | "
                     f"{d['same_entry_date_signal_dates']} | {d['strict_matched_pairs']} | {d['admitted_paired_sets']} | "
                     f"{d['capacity_skipped_matched_pairs']} | {d['put_only_signal_dates']} | {d['call_only_signal_dates']} |")
    lines += ["", "## Limits", "",
        "- Five phases are independent robustness runs; do not combine their curves.",
        "- USD 63,694 is treated as current holding value; historical starting stock value is not USD 63,694.",
        "- Gross SPY put assignment obligation and short-call delivery notional are exposure diagnostics, not broker margin. QQQ stock does not contractually cover SPY options.",
        "- EOD quotes are estimates, not verified fills. Intrinsic expiry settlement is a proxy when no executable close is observed.",
        "- Option history ends in December 2025; no 2026 option performance is observed.", "",
        "Outputs: daily_nav_by_phase.csv; daily_option_leg_marks.csv; phase_max_drawdown_summary.csv; pair_matching_and_capacity_audit.csv; quote_reconciliation.json; daily_nav_max_drawdown_audit.json; replay/.", ""]
    return "\n".join(lines)


def generate(stock_value, current_price, current_price_date):
    cache_root = Path.home() / ".cache" / "qqq-spy-pair-daily-nav-v1"
    for side in ("put", "call"):
        for phase in PHASES:
            run_dte20_exit4_replay(side, phase, cache_root)

    dates, qspots, sspots, underlying_integrity = load_underlying(put_engine, cache_root)
    date_to_index = {d: i for i, d in enumerate(dates)}
    stock_by_date, stock_config = load_stock_series(dates, qspots, stock_value, current_price, current_price_date)
    phase_pairs = {}
    for phase in PHASES:
        pdir, cdir = REPLAY_ROOT / "put" / f"phase_{phase}", REPLAY_ROOT / "call" / f"phase_{phase}"
        p_rows = [r for r in read_csv(pdir / "trade_episodes.csv") if r.get("policy") == POLICY]
        c_rows = [r for r in read_csv(cdir / "trade_episodes.csv") if r.get("policy") == POLICY]
        phase_pairs[phase] = pair_entries(p_rows, c_rows)
    positions_by_phase, diagnostics, pair_audit = prepare_positions(phase_pairs, dates, date_to_index)
    all_positions = [p for seq in positions_by_phase.values() for p in seq]
    if not all_positions:
        raise RuntimeError("No strictly matched PUT+CALL baskets; refusing to publish an empty daily NAV")
    quote_map, quote_integrity = collect_selected_quotes(all_positions, put_engine, cache_root)
    quote_audit = audit_entry_exit_quotes(all_positions, quote_map)
    pnl_audit = audit_trade_pnl_reconciliation(all_positions)

    all_daily, all_legs, summaries = [], [], []
    for phase in PHASES:
        daily, legs, summary = build_daily_curve(
            positions_by_phase[phase], quote_map, dates, date_to_index, qspots, sspots, stock_by_date, phase, diagnostics[phase])
        summary.update({
            "admitted_paired_sets": diagnostics[phase]["admitted_paired_sets"],
            "capacity_skipped_matched_pairs": diagnostics[phase]["capacity_skipped_matched_pairs"],
            "stock_start_value_usd": stock_config["historical_stock_value_at_start_usd"],
            "stock_end_value_total_return_proxy_usd": stock_config["stock_value_at_end_total_return_proxy_usd"],
        })
        summaries.append(summary)
        all_daily.extend(daily)
        all_legs.extend(legs)

    expected_daily = len(dates) * len(PHASES)
    if len(all_daily) != expected_daily:
        raise RuntimeError(f"daily NAV coverage mismatch: got {len(all_daily)}, expected {expected_daily}")
    leg_coverage_audit = audit_daily_leg_mark_coverage(all_positions, all_legs, dates, date_to_index)
    max_stale_age = max(int(r["max_quote_staleness_sessions"]) for r in summaries)
    if max_stale_age > 10:
        raise RuntimeError(f"stale option valuation exceeded 10 common sessions; refusing acceptance: {max_stale_age}")
    audit = {
        "status": "PASS", "policy": POLICY, "opening_dte_target": DTE_TARGET, "opening_dte_band": [DTE_MIN, DTE_MAX],
        "exit_rule": "remaining calendar DTE <= 4", "put_target_abs_delta": 0.25, "call_target_abs_delta": 0.20,
        "source_dates": [dates[0], dates[-1]], "common_sessions": len(dates), "phases": list(PHASES),
        "daily_nav_rows": len(all_daily), "daily_nav_rows_expected": expected_daily,
        "admitted_matched_baskets": sum(len(x) for x in positions_by_phase.values()),
        "option_leg_mark_rows": len(all_legs), "daily_leg_mark_coverage": leg_coverage_audit,
        "max_stale_quote_age_sessions": max_stale_age, "resolved_option_leg_pnl_persists_in_nav": True,
        "open_option_legs_are_marked_daily_or_flagged_stale": True, "max_drawdown_computed_from_daily_nav": True,
        "quote_audit": quote_audit, "trade_pnl_reconciliation": pnl_audit,
        "unresolved_expiry_intrinsic_proxy_used": True,
        "broker_margin_cash_forced_liquidation_and_exercise_fees_modeled": False,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUT / "daily_nav_by_phase.csv", all_daily)
    write_csv(OUT / "daily_option_leg_marks.csv", all_legs)
    write_csv(OUT / "phase_max_drawdown_summary.csv", summaries)
    write_csv(OUT / "pair_matching_and_capacity_audit.csv", pair_audit)
    (OUT / "quote_reconciliation.json").write_text(json.dumps({
        "quote_audit": quote_audit, "source_option_integrity_files": quote_integrity,
        "underlying_integrity_files": underlying_integrity,
        "source_repository": put_engine.SOURCE_REPO, "source_tree_commit": put_engine.SOURCE_COMMIT,
        "stock_position_assumption": stock_config,
    }, indent=2, allow_nan=False), encoding="utf-8")
    (OUT / "daily_nav_max_drawdown_audit.json").write_text(json.dumps(audit, indent=2, allow_nan=False), encoding="utf-8")
    (OUT / "DAILY_NAV_MAX_DRAWDOWN_REPORT.md").write_text(
        render_report(stock_config, summaries, diagnostics, quote_audit, quote_integrity, pnl_audit, leg_coverage_audit), encoding="utf-8")
    print(json.dumps({
        "status": "PASS", "policy": POLICY, "dte_target": DTE_TARGET, "daily_nav_rows": len(all_daily),
        "option_leg_mark_rows": len(all_legs), "max_stale_quote_age_sessions": max_stale_age,
        "phase_max_drawdown": [{k: r[k] for k in ("phase_sessions", "max_drawdown_usd", "max_drawdown_pct",
                            "max_drawdown_peak_date", "max_drawdown_trough_date", "end_nav_usd", "final_total_option_net_pnl_usd")}
                            for r in summaries],
        "report": str(OUT / "DAILY_NAV_MAX_DRAWDOWN_REPORT.md"),
    }, indent=2, allow_nan=False))
    return audit


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--qqq-stock-value-usd", type=float, default=63694.0)
    p.add_argument("--current-qqq-price", type=float, default=712.20)
    p.add_argument("--current-price-date", default="2026-10-26")
    args = p.parse_args()
    if args.qqq_stock_value_usd <= 0 or args.current_qqq_price <= 0:
        raise SystemExit("stock value and current QQQ price must be positive")
    generate(args.qqq_stock_value_usd, args.current_qqq_price, args.current_price_date)


if __name__ == "__main__":
    main()
