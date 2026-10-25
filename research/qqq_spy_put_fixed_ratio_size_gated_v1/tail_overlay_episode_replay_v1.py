#!/usr/bin/env python3
"""Pair historical TAIL ETF total returns with resolved QQQ/SPY put-ratio episodes.

TAIL is bought for each option cohort at entry and sold at that cohort's exit.
This is an episode-level hedge test, not a capital-constrained account backtest.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, statistics, urllib.parse, urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

POLICY = "HOLD_20_OR_DTE_LE_7"
ALLOCATIONS_USD = (250.0, 500.0, 1000.0, 2500.0)
ROUND_TRIP_COST_RATES = (0.001, 0.0025, 0.005)
START_DATE, END_DATE = "2017-04-06", "2025-12-15"
YAHOO_ENDPOINT = "https://query1.finance.yahoo.com/v8/finance/chart/TAIL"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def finite(value: Any) -> float | None:
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def download_tail_history(out_dir: Path, refresh: bool = False) -> tuple[Path, dict[str, Any]]:
    """Freeze the first successful Yahoo chart snapshot; verify hashes on reuse."""
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "tail_adjusted_history.csv"
    manifest_path = out_dir / "tail_source_manifest.json"
    if csv_path.exists() and manifest_path.exists() and not refresh:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        actual = sha256_file(csv_path)
        if actual != manifest.get("csv_sha256"):
            raise ValueError(f"Frozen TAIL CSV hash mismatch: {actual} != {manifest.get('csv_sha256')}")
        return csv_path, manifest
    if csv_path.exists() != manifest_path.exists() and not refresh:
        raise ValueError("Only one TAIL source file exists; refusing to silently replace partial provenance")

    period1 = int(datetime(2017, 4, 5, tzinfo=timezone.utc).timestamp())
    period2 = int(datetime(2025, 12, 17, tzinfo=timezone.utc).timestamp())
    query = urllib.parse.urlencode({"period1": period1, "period2": period2,
                                    "interval": "1d", "events": "div,splits"})
    url = f"{YAHOO_ENDPOINT}?{query}"
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (tail-overlay-research/1.0)"})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()
    payload_sha = hashlib.sha256(payload).hexdigest()
    raw = json.loads(payload.decode("utf-8"))
    if raw.get("chart", {}).get("error"):
        raise RuntimeError(f"Yahoo chart API error: {raw['chart']['error']}")
    result_rows = raw.get("chart", {}).get("result") or []
    if not result_rows:
        raise RuntimeError("Yahoo chart API returned no TAIL history")
    result = result_rows[0]
    timestamps = result.get("timestamp") or []
    indicators = result.get("indicators") or {}
    quote = (indicators.get("quote") or [{}])[0]
    closes = quote.get("close") or []
    adjusted = ((indicators.get("adjclose") or [{}])[0]).get("adjclose") or []
    if not timestamps or len(timestamps) != len(closes) or len(timestamps) != len(adjusted):
        raise RuntimeError("TAIL source has missing or unaligned timestamp/close/adjusted-close arrays")

    dividends, splits = {}, {}
    events = result.get("events") or {}
    for ev in (events.get("dividends") or {}).values():
        if ev.get("date") is not None:
            d = datetime.fromtimestamp(int(ev["date"]), timezone.utc).date().isoformat()
            dividends[d] = float(ev.get("amount") or 0.0)
    for ev in (events.get("splits") or {}).values():
        if ev.get("date") is not None:
            d = datetime.fromtimestamp(int(ev["date"]), timezone.utc).date().isoformat()
            splits[d] = f"{ev.get('numerator', 0)}:{ev.get('denominator', 0)}"

    records = {}
    for ts, close, adj in zip(timestamps, closes, adjusted):
        day = datetime.fromtimestamp(int(ts), timezone.utc).date().isoformat()
        c, a = finite(close), finite(adj)
        if START_DATE <= day <= END_DATE and c is not None and a is not None and c > 0 and a > 0:
            records[day] = {"date": day, "close": c, "adj_close": a,
                            "dividend_per_share": dividends.get(day, 0.0),
                            "split_ratio": splits.get(day, "")}
    if len(records) < 1500:
        raise RuntimeError(f"Too few daily TAIL observations: {len(records)}")
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "close", "adj_close", "dividend_per_share", "split_ratio"])
        writer.writeheader()
        for day in sorted(records):
            writer.writerow(records[day])
    manifest = {
        "symbol": "TAIL", "name": "Cambria Tail Risk ETF", "provider": "Yahoo Finance chart API",
        "source_url": url, "price_measure": "adjusted close total-return proxy including distributions",
        "requested_start": START_DATE, "requested_end": END_DATE,
        "first_observation": min(records), "last_observation": max(records),
        "observation_count": len(records), "raw_payload_sha256": payload_sha,
        "csv_sha256": sha256_file(csv_path), "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "refresh_policy": "first successful response is frozen; later runs validate its SHA-256 and do not silently refresh",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return csv_path, manifest


def load_tail_prices(path: Path) -> dict[str, float]:
    prices = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            day, adj = str(row.get("date", ""))[:10], finite(row.get("adj_close"))
            if day and adj is not None and adj > 0:
                prices[day] = adj
    if not prices:
        raise ValueError("TAIL adjusted-close file contains no valid prices")
    return prices


def read_policy_trades(path: Path, ratio: str) -> tuple[list[dict[str, Any]], dict[str, int]]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    selected = [r for r in rows if r.get("policy") == POLICY]
    resolved = [r for r in selected if r.get("status") == "RESOLVED"]
    trades, missing_fields = [], 0
    for row in resolved:
        entry_day, exit_day = str(row.get("entry_date", ""))[:10], str(row.get("exit_date", ""))[:10]
        pnl = finite(row.get("net_pnl_usd"))
        if not entry_day or not exit_day or pnl is None:
            missing_fields += 1
            continue
        trades.append({"ratio": ratio, "episode_id": row.get("episode_id", ""),
                       "entry_date": entry_day, "exit_date": exit_day,
                       "hold_calendar_days": (date.fromisoformat(exit_day) - date.fromisoformat(entry_day)).days,
                       "base_net_pnl_usd": pnl})
    return trades, {"opened": len(selected), "resolved_options": len(resolved),
                    "unresolved_options": len(selected) - len(resolved), "missing_option_fields": missing_fields}


def pair_tail_returns(trades: list[dict[str, Any]], prices: dict[str, float]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    paired, missing_entry, missing_exit = [], 0, 0
    for row in trades:
        start, end = row["entry_date"], row["exit_date"]
        if start not in prices:
            missing_entry += 1
            continue
        if end not in prices:
            missing_exit += 1
            continue
        p0, p1 = prices[start], prices[end]
        ret = p1 / p0 - 1.0
        paired.append({**row, "tail_adj_close_entry": p0, "tail_adj_close_exit": p1,
                       "tail_total_return": ret, "tail_total_return_pct": 100 * ret})
    return paired, {"options_resolved_with_exact_tail_prices": len(paired),
                    "missing_tail_entry_price": missing_entry, "missing_tail_exit_price": missing_exit}


def profit_factor(values: list[float]) -> float | str | None:
    gains, losses = sum(v for v in values if v > 0), -sum(v for v in values if v < 0)
    if losses <= 1e-12:
        return "INF" if gains > 0 else None
    return gains / losses


def summarize(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"n": 0, "wins": 0, "losses": 0, "win_rate_pct": None,
                "mean_net_pnl_usd": None, "median_net_pnl_usd": None, "total_net_pnl_usd": None,
                "worst_trade_usd": None, "best_trade_usd": None, "profit_factor": None}
    wins, losses = sum(v > 0.005 for v in values), sum(v < -0.005 for v in values)
    return {"n": len(values), "wins": wins, "losses": losses, "win_rate_pct": 100 * wins / len(values),
            "mean_net_pnl_usd": statistics.mean(values), "median_net_pnl_usd": statistics.median(values),
            "total_net_pnl_usd": sum(values), "worst_trade_usd": min(values), "best_trade_usd": max(values),
            "profit_factor": profit_factor(values)}


def make_scenario(paired: list[dict[str, Any]], allocation: float, cost_rate: float) -> dict[str, Any]:
    base = [float(r["base_net_pnl_usd"]) for r in paired]
    tail_gross = [allocation * float(r["tail_total_return"]) for r in paired]
    tail_cost = [allocation * cost_rate for _ in paired]
    tail_net = [g - c for g, c in zip(tail_gross, tail_cost)]
    combined = [b + t for b, t in zip(base, tail_net)]
    loss_ids = [i for i, value in enumerate(base) if value < -0.005]
    offset_wins = sum(tail_net[i] > 0.005 for i in loss_ids)
    tail_losers = sum(tail_net[i] < -0.005 for i in loss_ids)
    base_s, tail_s, combined_s = summarize(base), summarize(tail_net), summarize(combined)
    return {
        "allocation_per_entry_cohort_usd": allocation, "round_trip_cost_rate": cost_rate, "paired_n": len(paired),
        "base_on_paired_sample": base_s,
        "tail_overlay": {**tail_s, "gross_total_pnl_usd": sum(tail_gross),
                         "assumed_round_trip_cost_usd": sum(tail_cost),
                         "average_holding_calendar_days": statistics.mean([r["hold_calendar_days"] for r in paired]) if paired else None,
                         "median_return_pct_per_holding_period": statistics.median([r["tail_total_return_pct"] for r in paired]) if paired else None},
        "combined": combined_s,
        "worst_trade_loss_reduction_usd": combined_s["worst_trade_usd"] - base_s["worst_trade_usd"] if paired else None,
        "base_loss_cohorts": len(loss_ids),
        "base_loss_cohorts_with_positive_tail_net_pnl": offset_wins,
        "base_loss_cohort_tail_offset_coverage_pct": 100 * offset_wins / len(loss_ids) if loss_ids else None,
        "base_loss_cohorts_where_tail_lost_money": tail_losers,
        "base_loss_cohort_tail_loss_pct": 100 * tail_losers / len(loss_ids) if loss_ids else None,
        "tail_net_pnl_on_base_loss_cohorts_usd": sum(tail_net[i] for i in loss_ids),
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"Refusing to create a CSV without rows: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--refresh-tail-data", action="store_true")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    data_path, manifest = download_tail_history(args.out, refresh=args.refresh_tail_data)
    prices = load_tail_prices(data_path)
    output: dict[str, Any] = {
        "schema": "tail-overlay-per-episode.v1", "status": "COMPLETED_WITH_UNRESOLVEDS",
        "policy": POLICY, "source": {"symbol": "TAIL", "price_measure": "Yahoo adjusted close total-return proxy",
        "csv_sha256": manifest["csv_sha256"], "raw_payload_sha256": manifest["raw_payload_sha256"]},
        "window": {"start": "2018-03-01", "end": "2025-12-15"},
        "method": {"holding_rule": "Buy TAIL on each option episode entry date; sell on that episode exit date.",
        "allocations_usd_per_entry_cohort": list(ALLOCATIONS_USD), "round_trip_cost_rates": list(ROUND_TRIP_COST_RATES),
        "overlapping_option_cohorts": True, "compounding_account_nav": False, "max_drawdown_or_cagr_computed": False},
        "ratios": {}
    }
    paired_export, sensitivity_export = [], []
    for qty in (3, 6):
        ratio = f"1:{qty}"
        trade_path = args.input_root / f"ratio_1x{qty}" / "trade_episodes.csv"
        if not trade_path.is_file():
            raise FileNotFoundError(f"Missing required option replay output: {trade_path}")
        trades, coverage = read_policy_trades(trade_path, ratio)
        paired, price_coverage = pair_tail_returns(trades, prices)
        if len(paired) < 0.98 * max(1, len(trades)):
            raise RuntimeError(f"TAIL exact-date pairing coverage too low for {ratio}: {len(paired)}/{len(trades)}")
        ratio_result = {"input": {**coverage, **price_coverage,
                         "tail_price_pair_coverage_pct_of_resolved": 100 * len(paired) / len(trades) if trades else None},
                        "scenarios": []}
        paired_export.extend({**r, "allocation_semantics": "fixed dollars per cohort; concurrent cohorts stack"} for r in paired)
        for allocation in (0.0, *ALLOCATIONS_USD):
            costs = (0.0,) if allocation == 0 else ROUND_TRIP_COST_RATES
            for cost_rate in costs:
                scenario = make_scenario(paired, allocation, cost_rate)
                scenario["ratio"] = ratio
                ratio_result["scenarios"].append(scenario)
                sensitivity_export.append({
                    "ratio": ratio, "allocation_per_entry_cohort_usd": allocation,
                    "round_trip_cost_rate_pct": 100 * cost_rate, "paired_n": scenario["paired_n"],
                    "base_total_net_pnl_usd": scenario["base_on_paired_sample"]["total_net_pnl_usd"],
                    "tail_gross_total_pnl_usd": scenario["tail_overlay"]["gross_total_pnl_usd"],
                    "tail_cost_usd": scenario["tail_overlay"]["assumed_round_trip_cost_usd"],
                    "tail_net_total_pnl_usd": scenario["tail_overlay"]["total_net_pnl_usd"],
                    "combined_total_net_pnl_usd": scenario["combined"]["total_net_pnl_usd"],
                    "combined_mean_net_pnl_usd": scenario["combined"]["mean_net_pnl_usd"],
                    "combined_median_net_pnl_usd": scenario["combined"]["median_net_pnl_usd"],
                    "combined_win_rate_pct": scenario["combined"]["win_rate_pct"],
                    "combined_worst_trade_usd": scenario["combined"]["worst_trade_usd"],
                    "combined_profit_factor": scenario["combined"]["profit_factor"],
                    "worst_trade_loss_reduction_usd": scenario["worst_trade_loss_reduction_usd"],
                    "base_loss_cohorts": scenario["base_loss_cohorts"],
                    "base_loss_cohorts_with_positive_tail_net_pnl": scenario["base_loss_cohorts_with_positive_tail_net_pnl"],
                    "base_loss_cohort_tail_offset_coverage_pct": scenario["base_loss_cohort_tail_offset_coverage_pct"],
                    "base_loss_cohorts_where_tail_lost_money": scenario["base_loss_cohorts_where_tail_lost_money"],
                    "base_loss_cohort_tail_loss_pct": scenario["base_loss_cohort_tail_loss_pct"],
                })
        output["ratios"][ratio] = ratio_result

    for ratio, info in output["ratios"].items():
        rows = [r for r in paired_export if r["ratio"] == ratio]
        returns = [float(r["tail_total_return_pct"]) for r in rows]
        losing = [r for r in rows if float(r["base_net_pnl_usd"]) < -0.005]
        info["paired_period_diagnostics"] = {
            "tail_positive_periods_n": sum(v > 0.005 for v in returns),
            "tail_negative_periods_n": sum(v < -0.005 for v in returns),
            "tail_positive_periods_pct": 100 * sum(v > 0.005 for v in returns) / len(returns) if returns else None,
            "mean_tail_return_pct_per_episode": statistics.mean(returns) if returns else None,
            "median_tail_return_pct_per_episode": statistics.median(returns) if returns else None,
            "base_loss_count": len(losing),
            "base_loss_periods_with_positive_tail_return_n": sum(float(r["tail_total_return_pct"]) > 0.005 for r in losing),
        }
    output["notes"] = [
        "TAIL is an ETF hedge proxy, not guaranteed insurance and not a direct payoff against each QQQ/SPY option loss.",
        "TAIL is paired on exact option entry/exit dates; no missing market-date prices are forward-filled.",
        "The TAIL allocation is bought per option entry cohort and sold at that cohort's exit. Overlapping cohorts cause overlapping TAIL holdings; $1,000 means $1,000 for every cohort, not a one-time 1% NAV allocation.",
        "Episode P&L sums overlapping trade groups and is not an account NAV series. This report does not calculate account CAGR or portfolio maximum drawdown.",
        "The adjusted-close price snapshot is saved with source hashes. Fund expenses are already reflected in market returns; taxes and historical live bid/ask fills are not modeled.",
        "Round-trip transaction-cost assumptions are 0.10%, 0.25%, and 0.50% of the TAIL allocation; 0.10% is only a reference case, not a claim about all historical spreads.",
        "This is an in-sample, fixed-entry-schedule comparison; underlying option quotes are EOD observations, not verified fills."
    ]
    (args.out / "tail_overlay_summary.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(args.out / "paired_episode_returns.csv", paired_export)
    write_csv(args.out / "tail_overlay_sensitivity.csv", sensitivity_export)

    lines = [
        "# TAIL ETF overlay — paired episode replay", "",
        "Research only. This episode-level hedge comparison is not a compounded USD 100,000 account backtest.", "",
        "## Method", "",
        "- Base positions: existing resolved HOLD_20_OR_DTE_LE_7 episodes from the frozen DTE14 QQQ |Delta| 0.60–0.70 setup.",
        "- TAIL is bought at each option cohort entry and sold at that cohort exit using adjusted closes; exact dates only, no forward fill.",
        "- Allocation per entry cohort: USD 250, 500, 1,000, or 2,500. Overlapping cohorts stack.",
        "- TAIL round-trip cost stress: 0.10%, 0.25%, and 0.50% of allocation. Option P&L already includes its base costs.",
        "- Base control is recalculated on the same exact-date paired sample for fair comparison.", "",
        "## Main comparison (TAIL 0.10% round-trip cost; matched sample)", "",
        "| Ratio | TAIL per cohort | Paired N | Base total | TAIL net total | Combined total | Combined mean | Combined win rate | Base worst | Combined worst | Worst-loss improvement | Losing base trades with positive TAIL net |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
    ]
    for ratio in ("1:3", "1:6"):
        for allocation in (0.0, *ALLOCATIONS_USD):
            cost_rate = 0 if allocation == 0 else 0.001
            s = next(s for s in output["ratios"][ratio]["scenarios"]
                     if s["allocation_per_entry_cohort_usd"] == allocation and abs(s["round_trip_cost_rate"] - cost_rate) < 1e-12)
            b, t, c = s["base_on_paired_sample"], s["tail_overlay"], s["combined"]
            values = [
                ratio, f"USD {allocation:,.0f}", str(s["paired_n"]),
                f"USD {b['total_net_pnl_usd']:,.2f}", f"USD {t['total_net_pnl_usd']:,.2f}",
                f"USD {c['total_net_pnl_usd']:,.2f}", f"USD {c['mean_net_pnl_usd']:,.2f}",
                f"{c['win_rate_pct']:.2f}%", f"USD {b['worst_trade_usd']:,.2f}",
                f"USD {c['worst_trade_usd']:,.2f}", f"USD {s['worst_trade_loss_reduction_usd']:,.2f}",
                f"{s['base_loss_cohorts_with_positive_tail_net_pnl']}/{s['base_loss_cohorts']}"
            ]
            lines.append("| " + " | ".join(values) + " |")
    lines += ["", "## Pairing coverage and TAIL return behaviour", "",
              "| Ratio | Options resolved | Exact-date TAIL pairs | Coverage | TAIL-positive periods | Median TAIL return / hold period |",
              "|---|---:|---:|---:|---:|---:|"]
    for ratio in ("1:3", "1:6"):
        info, diag = output["ratios"][ratio], output["ratios"][ratio]["paired_period_diagnostics"]
        inp = info["input"]
        lines.append("| " + " | ".join([
            ratio, str(inp["resolved_options"]), str(inp["options_resolved_with_exact_tail_prices"]),
            f"{inp['tail_price_pair_coverage_pct_of_resolved']:.2f}%",
            f"{diag['tail_positive_periods_n']}/{inp['options_resolved_with_exact_tail_prices']}",
            f"{diag['median_tail_return_pct_per_episode']:.2f}%"
        ]) + " |")
    lines += ["", "## Cost sensitivity", "",
              "See tail_overlay_sensitivity.csv for all sizes at the 0.10%, 0.25%, and 0.50% cost assumptions.", "",
              "## Interpretation limits", "",
              "- TAIL can lose money during calm or rising markets and does not guarantee an offset for every option loss.",
              "- USD 1,000 is opened for each new cohort, not a single continuously rebalanced 1% portfolio allocation. Concurrent cohorts multiply capital committed to TAIL.",
              "- Option episode P&L does not constrain SPY assignment cash or broker margin. Results are not account CAGR, NAV drawdown, or capital feasibility.",
              "- Yahoo adjusted close is frozen with SHA-256 provenance; it is a total-return proxy, not historical executable bid/ask. Taxes and additional market impact are not modeled.", "",
              "## Output files", "",
              "- tail_source_manifest.json — source provenance and SHA-256",
              "- tail_adjusted_history.csv — frozen daily TAIL price snapshot",
              "- paired_episode_returns.csv — exact-date paired option episodes and TAIL returns",
              "- tail_overlay_sensitivity.csv — all hedge sizes and costs",
              "- tail_overlay_summary.json — machine-readable summary", ""]
    (args.out / "TAIL_OVERLAY_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    required = ("TAIL_OVERLAY_REPORT.md", "tail_overlay_summary.json", "paired_episode_returns.csv",
                "tail_overlay_sensitivity.csv", "tail_adjusted_history.csv", "tail_source_manifest.json")
    for filename in required:
        p = args.out / filename
        if not p.is_file() or p.stat().st_size == 0:
            raise RuntimeError(f"Missing or empty required output: {p}")
    print(json.dumps({"report": str(args.out / "TAIL_OVERLAY_REPORT.md"),
        "summary": str(args.out / "tail_overlay_summary.json"), "history_rows": len(prices),
        "ratio_pairing": {k: v["input"] for k, v in output["ratios"].items()},
        "scenario_count": len(sensitivity_export)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
