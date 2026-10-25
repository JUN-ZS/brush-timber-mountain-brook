#!/usr/bin/env python3
"""Model a per-trade virtual SPY -10% floor using same-day historical option IV.

SPY put asks are shifted by the Black-Scholes theoretical price change from actual SPY close
to max(actual close, 90% of that episode's entry close), preserving the observed quote residual.
QQQ put marks remain observed historical bid-side quotes. This is a model, not a tradable quote.
"""
from __future__ import annotations
import argparse, bisect, csv, json, math, statistics
from collections import defaultdict
from datetime import date
from pathlib import Path
import pyarrow.parquet as pq
import qqq_spy_put_premium_matched_phase_v1 as eng

POLICY = "HOLD_20_OR_DTE_LE_7"
START, END = "2018-03-01", "2025-12-15"

def read_csv(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def normal_cdf(x):
    return 0.5 * math.erfc(-x / math.sqrt(2.0))

def bs_put(spot, strike, years, sigma, rate=0.0, dividend=0.0):
    if spot <= 0 or strike <= 0:
        raise ValueError("spot and strike must be positive")
    if years <= 0:
        return max(strike - spot, 0.0)
    if sigma is None or not math.isfinite(sigma) or sigma <= 1e-8:
        return max(strike * math.exp(-rate * years) - spot * math.exp(-dividend * years), 0.0)
    root = math.sqrt(years)
    d1 = (math.log(spot / strike) + (rate - dividend + 0.5 * sigma * sigma) * years) / (sigma * root)
    d2 = d1 - sigma * root
    return strike * math.exp(-rate * years) * normal_cdf(-d2) - spot * math.exp(-dividend * years) * normal_cdf(-d1)

def norm_iv(value):
    value = eng.num(value)
    if value is None or value <= 0:
        return None
    if value > 5:
        value /= 100.0
    return value if 0 < value <= 8 else None

def implied_vol_from_ask(ask, spot, strike, years):
    if ask is None or spot is None or strike is None or spot <= 0 or strike <= 0 or years <= 0:
        return None
    if ask < max(strike - spot, 0.0) - 0.10:
        return None
    lo, hi = 1e-5, 8.0
    if bs_put(spot, strike, years, hi) < ask:
        return None
    for _ in range(80):
        mid = (lo + hi) / 2
        if bs_put(spot, strike, years, mid) < ask:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2

def shifted_ask(actual_ask, iv_value, spot_actual, spot_virtual, strike, expiry, day):
    ask = eng.num(actual_ask)
    if ask is None or ask < 0 or spot_actual is None or spot_virtual is None:
        return None, None
    years = max((date.fromisoformat(expiry) - date.fromisoformat(day)).days, 0) / 365.0
    sigma = norm_iv(iv_value)
    if sigma is None:
        sigma = implied_vol_from_ask(ask, spot_actual, strike, years)
    if sigma is None:
        sigma = 0.80
    base = bs_put(spot_actual, strike, years, sigma)
    virtual = bs_put(spot_virtual, strike, years, sigma)
    return max(0.0, ask + virtual - base), sigma

def load_quotes(symbol, cache, required_dates):
    found = {}
    years = sorted({int(d[:4]) for days in required_dates.values() for d in days})
    cols = ["contract_id", "symbol", "type", "date", "bid", "ask", "bid_size", "ask_size", "implied_volatility"]
    for year in years:
        path = cache / symbol.lower() / f"options_{year}.parquet"
        if not path.is_file():
            path, _ = eng.download_verified(symbol, year, cache / symbol.lower())
        parquet = pq.ParquetFile(path)
        missing = sorted(set(cols) - set(parquet.schema_arrow.names))
        if missing:
            raise ValueError(f"{path.name} missing columns: {missing}")
        for batch in parquet.iter_batches(batch_size=65536, columns=cols):
            for row in batch.to_pylist():
                if str(row.get("symbol", "")).upper() != symbol or str(row.get("type", "")).strip().lower() not in ("p", "put"):
                    continue
                ident = eng.normalized_contract_id(row)
                day = eng.as_day(row.get("date"))
                if day in required_dates.get(ident, ()):
                    found[(ident, day)] = row
    return found

def pnl_stats(values, years):
    vals = [float(v) for v in values]
    if not vals:
        return {"n": 0, "cumulative_usd": None, "annual_average_episode_sum_usd": None,
                "mean_per_episode_usd": None, "median_per_episode_usd": None, "win_rate_pct": None,
                "worst_episode_usd": None, "best_episode_usd": None, "profit_factor": None}
    gains = sum(v for v in vals if v > 0)
    losses = -sum(v for v in vals if v < 0)
    return {"n": len(vals), "cumulative_usd": round(sum(vals), 2),
            "annual_average_episode_sum_usd": round(sum(vals) / years, 2),
            "mean_per_episode_usd": round(statistics.mean(vals), 2),
            "median_per_episode_usd": round(statistics.median(vals), 2),
            "win_rate_pct": round(100 * sum(v > 0.005 for v in vals) / len(vals), 2),
            "worst_episode_usd": round(min(vals), 2), "best_episode_usd": round(max(vals), 2),
            "profit_factor": round(gains / losses, 4) if losses else ("INF" if gains else None)}

def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys(k for row in rows for k in row)) if rows else ["status"]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", action="append", required=True,
                        help="Study root containing ratio_1x6; repeat to use one shared quote scan for multiple studies")
    parser.add_argument("--out-name", default="virtual_lock_model_v1")
    parser.add_argument("--qqq-cache", required=True)
    parser.add_argument("--spy-cache", required=True)
    args = parser.parse_args()
    qcache, scache = Path(args.qqq_cache), Path(args.spy_cache)
    qpath, _ = eng.download_verified("QQQ", None, qcache)
    spath, _ = eng.download_verified("SPY", None, scache)
    qspots, sspots = eng.load_spots(qpath, "QQQ"), eng.load_spots(spath, "SPY")
    dates = sorted(d for d in set(qspots) & set(sspots) if START <= d <= END)
    years = (date.fromisoformat(END) - date.fromisoformat(START)).days / 365.2425

    studies, required = [], {"QQQ": defaultdict(set), "SPY": defaultdict(set)}
    for base_arg in args.base:
        base = Path(base_arg)
        arm = base / "ratio_1x6"
        for filename in ("entry_cohort.csv", "trade_episodes.csv", "summary.json"):
            if not (arm / filename).is_file():
                raise FileNotFoundError(f"{arm}/{filename} missing")
        source = json.loads((arm / "summary.json").read_text(encoding="utf-8"))
        entries = {str(r["episode_id"]): r for r in read_csv(arm / "entry_cohort.csv")}
        trades = [r for r in read_csv(arm / "trade_episodes.csv") if r.get("policy") == POLICY]
        records, coverage = [], {"resolved": 0, "unresolved": 0, "entry_missing": 0}
        for trade in trades:
            eid = str(trade.get("episode_id"))
            entry = entries.get(eid)
            if entry is None:
                coverage["entry_missing"] += 1
                continue
            resolved = trade.get("status") == "RESOLVED" and eng.num(trade.get("net_pnl_usd")) is not None and trade.get("exit_date")
            end = str(trade.get("exit_date") if resolved else (trade.get("last_observed_date") or trade.get("exit_signal_date") or entry.get("entry_date") or ""))
            start = str(entry.get("entry_date") or "")
            if resolved: coverage["resolved"] += 1
            else: coverage["unresolved"] += 1
            if not start or not end or start not in sspots:
                continue
            floor = float(sspots[start]) * 0.90
            mark_end = str(trade.get("exit_signal_date") or end)
            left, right = bisect.bisect_right(dates, start), bisect.bisect_right(dates, mark_end)
            mark_dates = dates[left:right]
            need_dates = set(mark_dates)
            if resolved: need_dates.add(str(trade["exit_date"]))
            qid = eng.normalized_contract_id({"contract_id": entry.get("qqq_contract_id")})
            sid = eng.normalized_contract_id({"contract_id": entry.get("spy_contract_id")})
            required["QQQ"][qid].update(need_dates)
            required["SPY"][sid].update(need_dates)
            records.append({"study": base.name, "entry": entry, "trade": trade, "resolved": resolved,
                            "start": start, "end": end, "floor": floor, "mark_dates": mark_dates,
                            "qqq_id": qid, "spy_id": sid})
        studies.append({"base": base, "source": source, "records": records, "coverage": coverage})

    print("Required selected contracts:", {s: len(ids) for s, ids in required.items()})
    qquotes = load_quotes("QQQ", qcache, required["QQQ"])
    squotes = load_quotes("SPY", scache, required["SPY"])
    print("Retained selected-contract/date rows:", {"QQQ": len(qquotes), "SPY": len(squotes)})

    summaries = {}
    for study in studies:
        output_rows, base_pnls, virtual_pnls = [], [], []
        worst_base, worst_virtual = [], []
        path_breaches = exit_breaches = adjusted_n = missing_exit_iv = 0
        total_adjustment = 0.0
        assignment = []
        annual = defaultdict(lambda: {"n": 0, "original_usd": 0.0, "virtual_usd": 0.0, "adjustment_usd": 0.0})
        events = defaultdict(int)
        for rec in study["records"]:
            entry, trade = rec["entry"], rec["trade"]
            lqty = int(float(entry.get("long_qqq_qty") or 1))
            sqty = int(float(entry.get("short_spy_qty") or 6))
            spy_strike, qqq_strike = float(entry["spy_strike"]), float(entry["qqq_strike"])
            s_entry = float(entry["spy_spot_entry"])
            q_entry_ask, s_entry_bid = float(entry["qqq_entry_ask"]), float(entry["spy_entry_bid"])
            slip = float(entry.get("base_slippage_per_share") or 0.05)
            comm = float(entry.get("base_commission_per_contract_per_side") or 0.65)
            cost = 2 * (lqty + sqty) * (slip * 100 + comm)
            expiry = str(entry["expiry"])
            assignment.append(spy_strike * 100 * sqty)
            actual_marks, virtual_marks = [], []
            worst_spot = s_entry
            for day in rec["mark_dates"]:
                s_real = eng.num(sspots.get(day))
                if s_real is None: continue
                worst_spot = min(worst_spot, s_real)
                qrow, srow = qquotes.get((rec["qqq_id"], day)), squotes.get((rec["spy_id"], day))
                if not qrow or not srow or eng.num(qrow.get("bid")) is None or eng.num(srow.get("ask")) is None:
                    continue
                qbid, sask = float(qrow["bid"]), float(srow["ask"])
                vspot = max(s_real, rec["floor"])
                v_ask, _ = shifted_ask(sask, srow.get("implied_volatility"), s_real, vspot, spy_strike, expiry, day)
                if v_ask is None: continue
                actual_marks.append(lqty*100*(qbid-q_entry_ask)+sqty*100*(s_entry_bid-sask)-cost)
                virtual_marks.append(lqty*100*(qbid-q_entry_ask)+sqty*100*(s_entry_bid-v_ask)-cost)
            worst_base.append(min(actual_marks) if actual_marks else eng.num(trade.get("max_adverse_mark_pnl_usd")))
            worst_virtual.append(min(virtual_marks) if virtual_marks else None)
            if worst_spot < rec["floor"] - 1e-8: path_breaches += 1

            original = eng.num(trade.get("net_pnl_usd")) if rec["resolved"] else None
            virtual_pnl = adjustment = exit_spot = v_exit_spot = original_exit_ask = v_exit_ask = None
            if rec["resolved"]:
                day = str(trade["exit_date"])
                exit_spot = eng.num(sspots.get(day))
                original_exit_ask = eng.num(trade.get("exit_spy_ask"))
                row = squotes.get((rec["spy_id"], day))
                if original is not None:
                    base_pnls.append(original)
                if exit_spot is not None and original_exit_ask is not None:
                    v_exit_spot = max(exit_spot, rec["floor"])
                    ivval = row.get("implied_volatility") if row else None
                    v_exit_ask, _ = shifted_ask(original_exit_ask, ivval, exit_spot, v_exit_spot, spy_strike, expiry, day)
                    if norm_iv(ivval) is None: missing_exit_iv += 1
                    adjustment = sqty * 100 * (original_exit_ask - v_exit_ask)
                    virtual_pnl = original + adjustment
                    virtual_pnls.append(virtual_pnl)
                    total_adjustment += adjustment
                    adjusted_n += int(abs(adjustment) > 0.005)
                    exit_breaches += int(exit_spot < rec["floor"] - 1e-8)
                    bucket = annual[day[:4]]
                    bucket["n"] += 1
                    bucket["original_usd"] += original
                    bucket["virtual_usd"] += virtual_pnl
                    bucket["adjustment_usd"] += adjustment

            output_rows.append({
                "study": rec["study"], "episode_id": trade.get("episode_id"), "policy": POLICY,
                "status": trade.get("status"), "entry_date": rec["start"], "exit_signal_date": trade.get("exit_signal_date"),
                "exit_date": trade.get("exit_date"), "expiry": expiry,
                "qqq_contract_id": entry.get("qqq_contract_id"), "spy_contract_id": entry.get("spy_contract_id"),
                "qqq_strike": qqq_strike, "spy_strike": spy_strike,
                "spy_entry_close": round(s_entry, 4), "spy_floor_90pct_entry": round(rec["floor"], 4),
                "spy_worst_close_pct": round((worst_spot/s_entry-1)*100, 4),
                "spy_exit_close": exit_spot, "spy_virtual_exit_close": v_exit_spot,
                "spy_exit_ask_original": original_exit_ask, "spy_exit_ask_virtual_model": v_exit_ask,
                "original_net_pnl_usd": original, "virtual_floor_net_pnl_model_usd": virtual_pnl,
                "terminal_pnl_adjustment_usd": adjustment, "virtual_path_mark_observations": len(virtual_marks),
                "max_adverse_mark_original_usd": min(actual_marks) if actual_marks else eng.num(trade.get("max_adverse_mark_pnl_usd")),
                "max_adverse_mark_virtual_model_usd": min(virtual_marks) if virtual_marks else None,
                "path_breached_spy_floor": worst_spot < rec["floor"] - 1e-8,
            })
            if rec["start"] in dates: events[rec["start"]] += 1
            close_day = str(trade.get("exit_date") or trade.get("last_observed_date") or rec["end"])
            if close_day in dates:
                ix = bisect.bisect_left(dates, close_day)
                if ix + 1 < len(dates): events[dates[ix+1]] -= 1

        base_stats, virt_stats = pnl_stats(base_pnls, years), pnl_stats(virtual_pnls, years)
        concurrent = peak = 0
        for day in dates:
            concurrent += events.get(day, 0)
            peak = max(peak, concurrent)
        outdir = study["base"] / args.out_name
        write_csv(outdir / "episode_reprice.csv", output_rows)
        valid_actual_worst = [v for v in worst_base if v is not None]
        valid_virtual_worst = [v for v in worst_virtual if v is not None]
        result = {
            "schema": "qqq-spy-put-virtual-floor-model-reprice.v1", "status": "COMPLETED",
            "study": study["base"].name, "window": {"start": START, "end": END, "elapsed_years": round(years, 6)},
            "entry_filter": study["source"].get("entry_filter"), "ratio": study["source"].get("ratio"),
            "exit_policy": POLICY, "coverage": {**study["coverage"], "trades_with_marks": sum(v is not None for v in worst_virtual),
                "resolved_repriced_n": len(virtual_pnls), "underlying_path_breach_n": path_breaches,
                "resolved_exit_below_floor_n": exit_breaches, "terminal_pnl_adjusted_n": adjusted_n,
                "exit_iv_missing_or_fallback_n": missing_exit_iv, "peak_concurrent_cohorts_estimate": peak},
            "pnl": {"historical_quote_side": base_stats, "virtual_floor_model": virt_stats,
                "cumulative_terminal_adjustment_usd": round(total_adjustment, 2),
                "mean_assignment_obligation_per_cohort_usd": round(statistics.mean(assignment), 2) if assignment else None,
                "peak_cohort_assignment_notional_proxy_usd": round(peak*statistics.mean(assignment), 2) if assignment else None},
            "mark_path": {
                "worst_single_cohort_original_floating_mark_usd": round(min(valid_actual_worst), 2) if valid_actual_worst else None,
                "worst_single_cohort_virtual_model_floating_mark_usd": round(min(valid_virtual_worst), 2) if valid_virtual_worst else None,
                "mean_per_cohort_worst_mark_original_usd": round(statistics.mean(valid_actual_worst), 2) if valid_actual_worst else None,
                "mean_per_cohort_worst_mark_virtual_model_usd": round(statistics.mean(valid_virtual_worst), 2) if valid_virtual_worst else None,
                "note": "Single-cohort floating marks only; not portfolio NAV drawdown."},
            "annual_exit_pnl": {year: {k: round(v, 2) for k,v in bucket.items()} for year,bucket in sorted(annual.items())},
            "model": {"virtual_path": "max(actual SPY close, 90% of each trade's entry SPY close)",
                "repricing": "Observed SPY put ask plus Black-Scholes price change from actual to virtual spot at same-day IV; observed quote residual is preserved.",
                "parameters": {"risk_free_rate": 0.0, "dividend_yield": 0.0, "daily_historical_iv": True},
                "qqq_leg": "Historical QQQ long-put bid marks unchanged",
                "missing_iv": "Use implied-volatility inversion from actual ask where possible; fallback sigma 0.80 if quote IV and inversion are unavailable."},
            "limitations": [
                "Modelled virtual quote, not an actual tradable quote; Black-Scholes approximation for American-style SPY puts.",
                "Uses zero rates and zero dividend yield; same-day IV may be stale/noisy and quote residual is preserved.",
                "Only common-session closes are used; intraday floor breaches are missed.",
                "Overlapping episode P&L sums do not equal account returns or CAGR.",
                "Peak assignment notional is a contract-notional proxy, not broker margin; no portfolio cash, margin, assignment funding, forced liquidation, financing or compounding.",
                "The model changes SPY option marks but does not model counterfactual liquidity or altered discretionary decisions."
            ]
        }
        (outdir/"summary.json").write_text(json.dumps(result, indent=2, allow_nan=False)+"\n", encoding="utf-8")
        fmt = lambda x: "n/a" if x is None else "USD " + format(x, ",.2f")
        lines = ["# Per-trade virtual SPY -10% floor — model repricing", "",
            f"Study: {study['base'].name}; period {START} to {END} ({years:.3f} years).",
            f"Entry filter: {result['entry_filter'].get('name') if result['entry_filter'] else 'unknown'}; exit policy: {POLICY}.", "",
            "| Metric | Historical quote-side | Virtual-floor model |",
            "|---|---:|---:|",
            f"| Resolved episodes | {base_stats['n']} | {virt_stats['n']} |",
            f"| Cumulative episode P&L | {fmt(base_stats['cumulative_usd'])} | {fmt(virt_stats['cumulative_usd'])} |",
            f"| Annual-average episode P&L sum | {fmt(base_stats['annual_average_episode_sum_usd'])} | {fmt(virt_stats['annual_average_episode_sum_usd'])} |",
            f"| Mean per episode | {fmt(base_stats['mean_per_episode_usd'])} | {fmt(virt_stats['mean_per_episode_usd'])} |",
            f"| Median per episode | {fmt(base_stats['median_per_episode_usd'])} | {fmt(virt_stats['median_per_episode_usd'])} |",
            f"| Win rate | {base_stats['win_rate_pct']:.2f}% | {virt_stats['win_rate_pct']:.2f}% |",
            f"| Worst resolved episode | {fmt(base_stats['worst_episode_usd'])} | {fmt(virt_stats['worst_episode_usd'])} |",
            f"| Profit factor | {base_stats['profit_factor']} | {virt_stats['profit_factor']} |", "",
            "## Path and capital-pressure checks", "",
            f"- Cohort paths breaching -10%: {path_breaches}; resolved exit closes below floor: {exit_breaches}; terminal P&L estimates adjusted: {adjusted_n}.",
            f"- Total terminal P&L adjustment: {fmt(round(total_adjustment,2))}.",
            f"- Peak overlapping cohorts (date-level estimate): {peak}; average assignment obligation per cohort: {fmt(statistics.mean(assignment) if assignment else None)}.",
            f"- Worst single-cohort floating mark: original {fmt(result['mark_path']['worst_single_cohort_original_floating_mark_usd'])}; virtual model {fmt(result['mark_path']['worst_single_cohort_virtual_model_floating_mark_usd'])}.", "",
            "Annual-average episode P&L is the sum of resolved episode P&L divided by elapsed study years, not account annual profit or CAGR. Overlapping daily entries require portfolio capital and margin constraints before account-level returns can be computed.", "",
            "Limitations:"]
        lines.extend("- "+x for x in result["limitations"])
        (outdir/"REF_REPORT.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
        summaries[study["base"].name] = {"out_dir": str(outdir), "pnl": result["pnl"], "coverage": result["coverage"]}
        print(json.dumps({study["base"].name: summaries[study["base"].name]}, indent=2, allow_nan=False))
    print(json.dumps({"status":"COMPLETED","studies":summaries}, indent=2, allow_nan=False))

if __name__ == "__main__":
    assert abs(bs_put(100, 100, 10/365, 0.5) - bs_put(100, 100, 10/365, 0.5)) < 1e-12
    assert bs_put(90, 100, 10/365, 0.5) >= bs_put(100, 100, 10/365, 0.5)
    main()
