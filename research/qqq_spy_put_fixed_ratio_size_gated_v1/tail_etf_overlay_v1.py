#!/usr/bin/env python3
"""Paired per-cohort overlay for Cambria TAIL ETF on the DTE14 QQQ/SPY put ratios."""
from __future__ import annotations
import argparse, csv, hashlib, json, math, statistics, urllib.parse, urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

BASE = Path("research/qqq_spy_put_fixed_ratio_size_gated_v1/results/premium_matched_dte14_q60_70_v1")
OUT_DEFAULT = BASE / "tail_overlay_v1"
POLICY = "HOLD_20_OR_DTE_LE_7"
BUDGETS = (250.0, 500.0, 1000.0, 2500.0)
FRICTION_BPS = (0.0, 10.0, 25.0, 50.0)

def as_num(value):
    try:
        x = float(value)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None

def epoch(day):
    return int(datetime(day.year, day.month, day.day, tzinfo=timezone.utc).timestamp())

def fetch_tail_prices(start, end):
    start_day, end_day = date.fromisoformat(start), date.fromisoformat(end)
    query = urllib.parse.urlencode({
        "period1": epoch(start_day - timedelta(days=5)),
        "period2": epoch(end_day + timedelta(days=5)),
        "interval": "1d", "events": "div,splits",
    })
    url = "https://query1.finance.yahoo.com/v8/finance/chart/TAIL?" + query
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 tail-overlay-research/1.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as response:
        raw = response.read()
    payload = json.loads(raw)
    result = payload.get("chart", {}).get("result")
    if payload.get("chart", {}).get("error") or not result:
        raise RuntimeError("TAIL history request failed: " + str(payload.get("chart", {}).get("error")))
    item = result[0]
    times = item.get("timestamp") or []
    adjusted = (item.get("indicators") or {}).get("adjclose") or []
    if not adjusted or not adjusted[0].get("adjclose"):
        raise RuntimeError("No adjusted-close field; refusing to silently substitute unadjusted close")
    closes = adjusted[0]["adjclose"]
    rows = []
    for ts, value in zip(times, closes):
        price = as_num(value)
        if price is None or price <= 0:
            continue
        day = datetime.fromtimestamp(int(ts), timezone.utc).date().isoformat()
        if start <= day <= end:
            rows.append({"date": day, "adj_close": round(price, 8)})
    if len(rows) < 100:
        raise RuntimeError("Insufficient TAIL observations: " + str(len(rows)))
    source = {
        "ticker": "TAIL",
        "provider": "Yahoo Finance chart endpoint",
        "url": url,
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "raw_response_sha256": hashlib.sha256(raw).hexdigest(),
        "rows": len(rows),
        "first_date": rows[0]["date"],
        "last_date": rows[-1]["date"],
        "price_field": "adjusted close; dividend-adjusted return proxy",
    }
    return rows, source

def read_episodes(path):
    if not path.is_file():
        raise FileNotFoundError("Missing baseline trade file: " + str(path))
    with path.open(encoding="utf-8-sig", newline="") as handle:
        all_rows = list(csv.DictReader(handle))
    if not all_rows:
        raise ValueError("Empty trade file: " + str(path))
    needed = {"episode_id", "policy", "status", "entry_date", "exit_date", "net_pnl_usd"}
    missing = needed - set(all_rows[0])
    if missing:
        raise ValueError(str(path) + " missing columns: " + repr(sorted(missing)))
    rows = []
    for row in all_rows:
        if row["policy"] != POLICY or row["status"] != "RESOLVED" or not row["exit_date"]:
            continue
        pnl = as_num(row["net_pnl_usd"])
        if pnl is None:
            continue
        rows.append({
            "episode_id": str(row["episode_id"]),
            "entry_date": row["entry_date"][:10],
            "exit_date": row["exit_date"][:10],
            "base_net_pnl_usd": round(pnl, 6),
        })
    ids = [r["episode_id"] for r in rows]
    if not rows or len(ids) != len(set(ids)):
        raise ValueError("No resolved episodes or duplicate episode IDs in " + str(path))
    return rows

def calculate_tail_pnl(budget, entry_price, exit_price, friction_bps):
    if budget < 0 or entry_price <= 0 or exit_price <= 0 or friction_bps < 0:
        raise ValueError("Invalid overlay inputs")
    raw = budget * (exit_price / entry_price - 1.0)
    friction = budget * friction_bps / 10000.0
    return raw, friction, raw - friction

def pair_rows(episodes, price_map, budget, friction_bps):
    result, missing = [], []
    for ep in episodes:
        p0, p1 = price_map.get(ep["entry_date"]), price_map.get(ep["exit_date"])
        if p0 is None or p1 is None:
            missing.append(ep["episode_id"])
            continue
        raw, friction, hedge = calculate_tail_pnl(budget, p0, p1, friction_bps)
        result.append({
            **ep, "tail_budget_usd_per_cohort": budget, "tail_friction_bps_round_trip": friction_bps,
            "tail_entry_adj_close": p0, "tail_exit_adj_close": p1,
            "tail_raw_pnl_usd": round(raw, 6), "tail_friction_usd": round(friction, 6),
            "tail_net_pnl_usd": round(hedge, 6),
            "combined_net_pnl_usd": round(ep["base_net_pnl_usd"] + hedge, 6),
            "holding_calendar_days": (date.fromisoformat(ep["exit_date"]) - date.fromisoformat(ep["entry_date"])).days,
        })
    return result, missing

def pct(a, b):
    return 100.0 * a / b if b else None

def summarize(ratio, all_eps, rows, missing, budget, friction_bps, years):
    base = [r["base_net_pnl_usd"] for r in rows]
    tail = [r["tail_net_pnl_usd"] for r in rows]
    combined = [r["combined_net_pnl_usd"] for r in rows]
    losers = [r for r in rows if r["base_net_pnl_usd"] < 0]
    original_worst = min(rows, key=lambda r: r["base_net_pnl_usd"])
    combined_worst = min(rows, key=lambda r: r["combined_net_pnl_usd"])
    pos_tail_losers = [r for r in losers if r["tail_net_pnl_usd"] > 0]
    offset25 = [r for r in losers if r["tail_net_pnl_usd"] >= 0.25 * abs(r["base_net_pnl_usd"])]
    loss_dollars = sum(abs(r["base_net_pnl_usd"]) for r in losers)
    offset_dollars = sum(max(r["tail_net_pnl_usd"], 0) for r in losers)
    return {
        "ratio": ratio, "tail_budget_usd_per_cohort": budget, "tail_friction_bps_round_trip": friction_bps,
        "core_resolved_episodes": len(all_eps), "paired_count": len(rows),
        "paired_price_coverage_pct": pct(len(rows), len(all_eps)), "missing_tail_price_episode_ids": missing,
        "base_total_episode_pnl_usd": round(sum(base), 2),
        "tail_total_episode_pnl_usd": round(sum(tail), 2),
        "combined_total_episode_pnl_usd": round(sum(combined), 2),
        "base_annual_average_episode_pnl_usd": round(sum(base) / years, 2),
        "tail_annual_average_episode_pnl_usd": round(sum(tail) / years, 2),
        "combined_annual_average_episode_pnl_usd": round(sum(combined) / years, 2),
        "base_mean_net_pnl_usd": round(statistics.mean(base), 2),
        "combined_mean_net_pnl_usd": round(statistics.mean(combined), 2),
        "base_median_net_pnl_usd": round(statistics.median(base), 2),
        "combined_median_net_pnl_usd": round(statistics.median(combined), 2),
        "base_win_rate_pct": pct(sum(x > 0.005 for x in base), len(base)),
        "combined_win_rate_pct": pct(sum(x > 0.005 for x in combined), len(combined)),
        "base_worst_episode": {
            "episode_id": original_worst["episode_id"], "entry_date": original_worst["entry_date"],
            "exit_date": original_worst["exit_date"], "base_net_pnl_usd": round(original_worst["base_net_pnl_usd"], 2),
            "tail_net_pnl_usd": round(original_worst["tail_net_pnl_usd"], 2),
            "combined_net_pnl_usd": round(original_worst["combined_net_pnl_usd"], 2),
            "same_episode_improvement_usd": round(original_worst["combined_net_pnl_usd"] - original_worst["base_net_pnl_usd"], 2),
        },
        "combined_worst_episode": {
            "episode_id": combined_worst["episode_id"], "entry_date": combined_worst["entry_date"],
            "exit_date": combined_worst["exit_date"], "base_net_pnl_usd": round(combined_worst["base_net_pnl_usd"], 2),
            "tail_net_pnl_usd": round(combined_worst["tail_net_pnl_usd"], 2),
            "combined_net_pnl_usd": round(combined_worst["combined_net_pnl_usd"], 2),
        },
        "base_losing_episodes": len(losers),
        "losses_with_positive_tail_pnl": len(pos_tail_losers),
        "positive_tail_coverage_of_core_losses_pct": pct(len(pos_tail_losers), len(losers)),
        "losses_offset_by_at_least_25pct_count": len(offset25),
        "losses_offset_by_at_least_25pct_pct": pct(len(offset25), len(losers)),
        "positive_tail_pnl_on_base_losers_usd": round(offset_dollars, 2),
        "total_base_loss_dollars_usd": round(loss_dollars, 2),
        "positive_tail_pnl_as_pct_of_base_loss_dollars": pct(offset_dollars, loss_dollars),
        "mean_tail_return_per_episode_pct": round(statistics.mean([x / budget * 100 for x in tail]), 4) if budget and rows else 0.0,
    }

def usd(value):
    return "n/a" if value is None else "USD " + format(value, ",.2f")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2018-03-01")
    parser.add_argument("--end", default="2025-12-15")
    parser.add_argument("--out", default=str(OUT_DEFAULT))
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    prices, source = fetch_tail_prices(args.start, args.end)
    price_map = {r["date"]: r["adj_close"] for r in prices}
    with (out / "TAIL_adjusted_close.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["date", "adj_close"])
        writer.writeheader()
        writer.writerows(prices)
    years = max((date.fromisoformat(args.end) - date.fromisoformat(args.start)).days / 365.2425, 0.01)
    base_summaries, scenarios, paired_output = {}, [], []
    for ratio in ("1x3", "1x6"):
        episodes = read_episodes(BASE / ("ratio_" + ratio) / "trade_episodes.csv")
        check, missing0 = pair_rows(episodes, price_map, 0, 0)
        coverage = len(check) / max(len(episodes), 1)
        if coverage < 0.98:
            raise RuntimeError(f"TAIL date pairing below 98% for {ratio}: {coverage:.2%}; missing IDs {missing0[:10]}")
        base_pnl = [r["base_net_pnl_usd"] for r in check]
        base_summaries[ratio] = {
            "measured_episodes": len(check), "base_total_episode_pnl_usd": round(sum(base_pnl), 2),
            "base_annual_average_episode_pnl_usd": round(sum(base_pnl) / years, 2),
            "base_mean_net_pnl_usd": round(statistics.mean(base_pnl), 2),
            "base_median_net_pnl_usd": round(statistics.median(base_pnl), 2),
            "base_win_rate_pct": pct(sum(x > 0.005 for x in base_pnl), len(base_pnl)),
            "worst_base_net_pnl_usd": round(min(base_pnl), 2),
        }
        for budget in BUDGETS:
            for bps in FRICTION_BPS:
                paired, missing = pair_rows(episodes, price_map, budget, bps)
                if len(paired) != len(episodes):
                    raise RuntimeError(f"Pair count mismatch for {ratio}: {len(paired)}/{len(episodes)}")
                scenarios.append(summarize(ratio, episodes, paired, missing, budget, bps, years))
                paired_output.extend({"ratio": ratio, **r} for r in paired)
    report = {
        "schema": "tail-etf-overlay-paired-episodes.v1", "status": "COMPLETED",
        "window": {"start": args.start, "end": args.end, "elapsed_years": round(years, 6)},
        "policy": POLICY, "budget_grid_usd_per_cohort": list(BUDGETS),
        "friction_grid_bps_round_trip": list(FRICTION_BPS), "source": source,
        "baseline": base_summaries, "scenarios": scenarios,
        "limitations": [
            "Paired per-cohort overlay, not an account-level capital-constrained NAV replay.",
            "Overlapping cohorts produce overlapping ETF positions; total episode P&L is an episode sum, not CAGR.",
            "TAIL adjusted close is a return proxy, not an executable fill. The 10 bps haircut is a sensitivity assumption.",
            "TAIL allocation is capital deployed, not an option premium; the ETF can lose value.",
            "Unresolved option cohorts are excluded, matching resolved-trade metrics in the core report.",
        ],
    }
    (out / "source_manifest.json").write_text(json.dumps(source, indent=2) + "\n", encoding="utf-8")
    (out / "summary.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    fields = ["ratio", "episode_id", "entry_date", "exit_date", "holding_calendar_days", "base_net_pnl_usd",
              "tail_budget_usd_per_cohort", "tail_friction_bps_round_trip", "tail_entry_adj_close", "tail_exit_adj_close",
              "tail_raw_pnl_usd", "tail_friction_usd", "tail_net_pnl_usd", "combined_net_pnl_usd"]
    with (out / "episode_paired.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(paired_output)
    lines = [
        "# TAIL ETF paired overlay: QQQ LONG PUT / SPY SHORT PUT",
        "",
        f"Window {args.start} to {args.end}; elapsed {years:.3f} years; policy {POLICY}.",
        "",
        "For each resolved strategy cohort, invest USD 250, 500, 1,000, or 2,500 in TAIL at the cohort entry-date adjusted close and close it on that cohort exit date. TAIL uses dividend-adjusted daily prices. Friction sensitivity is 0, 10, 25, and 50 bps round-trip. These budgets are ETF capital deployed, not option premiums.",
        "",
        "## No-TAIL baseline",
        "",
        "| Ratio | Resolved | Total episode P&L | Average / cohort | Median / cohort | Win rate | Worst cohort | Annual average episode P&L |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for ratio, s in base_summaries.items():
        lines.append(f"| {ratio.replace('x', ':')} | {s['measured_episodes']} | {usd(s['base_total_episode_pnl_usd'])} | {usd(s['base_mean_net_pnl_usd'])} | {usd(s['base_median_net_pnl_usd'])} | {s['base_win_rate_pct']:.2f}% | {usd(s['worst_base_net_pnl_usd'])} | {usd(s['base_annual_average_episode_pnl_usd'])} |")
    lines += [
        "",
        "## TAIL overlay sensitivity",
        "",
        "| Ratio | TAIL capital / cohort | Friction bps | TAIL total episode P&L | Combined total episode P&L | Mean combined / cohort | Median combined / cohort | Combined win rate | Worst combined cohort | Improvement on original worst cohort | Core losses with positive TAIL | Core losses offset >=25% | Positive TAIL P&L on losers / core loss dollars | Price pairing coverage |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for s in scenarios:
        lines.append(
            f"| {s['ratio'].replace('x', ':')} | {usd(s['tail_budget_usd_per_cohort'])} | {s['tail_friction_bps_round_trip']:.0f} | "
            f"{usd(s['tail_total_episode_pnl_usd'])} | {usd(s['combined_total_episode_pnl_usd'])} | "
            f"{usd(s['combined_mean_net_pnl_usd'])} | {usd(s['combined_median_net_pnl_usd'])} | "
            f"{s['combined_win_rate_pct']:.2f}% | {usd(s['combined_worst_episode']['combined_net_pnl_usd'])} | "
            f"{usd(s['base_worst_episode']['same_episode_improvement_usd'])} | "
            f"{s['losses_with_positive_tail_pnl']}/{s['base_losing_episodes']} ({s['positive_tail_coverage_of_core_losses_pct']:.1f}%) | "
            f"{s['losses_offset_by_at_least_25pct_count']}/{s['base_losing_episodes']} ({s['losses_offset_by_at_least_25pct_pct']:.1f}%) | "
            f"{usd(s['positive_tail_pnl_on_base_losers_usd'])} / {usd(s['total_base_loss_dollars_usd'])} ({s['positive_tail_pnl_as_pct_of_base_loss_dollars']:.2f}%) | "
            f"{s['paired_price_coverage_pct']:.2f}% |"
        )
    lines += [
        "",
        "## Caveats",
        "",
        "- Episode totals include overlapping trades and overlapping TAIL stakes; they are not portfolio returns or account CAGR.",
        "- The overlay holds TAIL for the exact matched option-cohort interval. It is not a VIX/volatility-triggered hedge.",
        "- Daily adjusted closes are not guaranteed executable fills. The 0–50 bps friction grid is a scenario sensitivity, not a reconstruction of historical bid/ask spreads.",
        "- TAIL can decline during a losing option cohort. All resolved episode pairs are reported; unresolved core episodes are excluded.",
        "- The source hash, query URL, and retrieval time are in source_manifest.json; the daily prices used are stored in TAIL_adjusted_close.csv.",
        "",
    ]
    (out / "TAIL_OVERLAY_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": "COMPLETED", "baseline": base_summaries, "scenario_count": len(scenarios),
                      "tail_source": source, "output_dir": str(out)}, indent=2, allow_nan=False))

if __name__ == "__main__":
    main()
