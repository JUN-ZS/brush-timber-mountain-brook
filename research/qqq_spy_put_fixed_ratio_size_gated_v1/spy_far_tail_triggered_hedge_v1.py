#!/usr/bin/env python3
"""Replay predeclared SPY price-triggered long-PUT hedges against a frozen base ledger."""
from __future__ import annotations
import argparse, csv, hashlib, json, math, statistics
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any, Iterable

import qqq_spy_put_fixed_phase_v1 as engine
import spy_far_tail_hedge_v1 as overlay

ROOT = Path(__file__).resolve().parent
SCHEMA = "spy-far-tail-triggered-hedge.v1"
TRIGGERS = (
    {"label": "ENTRY_SPOT_DRAWDOWN_3PCT", "drop": 0.03},
    {"label": "ENTRY_SPOT_DRAWDOWN_5PCT", "drop": 0.05},
)
TAILS = (
    {"label": "TAIL_025_DELTA", "target": 0.025, "minimum": 0.01, "maximum": 0.08},
    {"label": "TAIL_05_DELTA", "target": 0.05, "minimum": 0.01, "maximum": 0.08},
)
TAIL = {
    "TAIL_025_DELTA": {"label": "2.5-delta (~−0.025)"},
    "TAIL_05_DELTA": {"label": "5-delta (~−0.05)"},
}
POLICY = {"HOLD_10_OR_DTE_LE_7": "Hold 10 / DTE≤7", "HOLD_20_OR_DTE_LE_7": "Hold 20 / DTE≤7"}
QUANTITIES = (1, 3)
SHOCKS = (-0.05, -0.10, -0.20, -0.30, -0.50)
SLIPPAGE_DEFAULT = 0.05
COMMISSION_DEFAULT = 0.65


def num(value: Any) -> float | None:
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (TypeError, ValueError):
        return None


def textval(value: Any) -> str:
    return "" if value is None else str(value).strip()


def as_day(value: Any) -> str:
    if value is None:
        return ""
    return value.isoformat()[:10] if hasattr(value, "isoformat") else str(value)[:10]


def trigger_condition_met(close: float | None, entry_spot: float, drop: float) -> bool:
    """SPY daily close at/below a fixed fraction of original entry spot."""
    return close is not None and entry_spot > 0 and 0 < drop < 1 and close <= entry_spot * (1.0 - drop)


def trigger_tail_expiry_pnl(entry_ask: float, strike: float, entry_spot: float, shock: float,
                            quantity: int, slippage: float = SLIPPAGE_DEFAULT,
                            commission: float = COMMISSION_DEFAULT) -> float:
    """Tail-leg-only hypothetical expiry P&L after shock from actual hedge entry spot."""
    if entry_spot <= 0 or strike <= 0 or quantity < 1 or entry_ask < 0 or shock > 0:
        raise ValueError("invalid stress inputs")
    shocked_spot = max(0.0, entry_spot * (1.0 + shock))
    intrinsic = max(0.0, strike - shocked_spot)
    return overlay.tail_net_pnl(entry_ask, intrinsic, quantity, slippage, commission)


def median(values: Iterable[float | int | None]) -> float | None:
    cleaned = [float(v) for v in values if v is not None]
    return statistics.median(cleaned) if cleaned else None


def bounds(values: Iterable[float | int | None]) -> tuple[float | None, float | None]:
    cleaned = [float(v) for v in values if v is not None]
    return (min(cleaned), max(cleaned)) if cleaned else (None, None)


def money(value: float | int | None) -> str:
    if value is None:
        return "—"
    value = float(value)
    prefix = "−$" if value < 0 else "$"
    return prefix + f"{abs(value):,.2f}"


def span(lo: float | int | None, hi: float | int | None) -> str:
    return "—" if lo is None or hi is None else f"{lo:g}–{hi:g}"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"required CSV is missing or empty: {path}")
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"refusing to write empty output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    seen = set()
    for row in rows:
        for key in row:
            if key not in seen:
                fields.append(key)
                seen.add(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def prepare_trade_metadata(cohorts, trades):
    meta = {}
    watcher_by_entry: dict[str, list[tuple[str, str]]] = defaultdict(list)
    watchers = {}
    details = {}
    for trade_key, base in trades.items():
        cohort_key = (base["arm"], base["phase"], textval(base.get("episode_id")))
        cohort = cohorts[cohort_key]
        target_day, target_kind = overlay.requested_observation_date(base)
        target_day = as_day(target_day)
        resolved = overlay.is_resolved(base)
        base_pnl = num(base.get("net_pnl_usd")) if resolved else None
        meta[trade_key] = {
            "trade_key": trade_key, "arm": base["arm"], "phase": int(base["phase"]),
            "episode_id": textval(base.get("episode_id")), "policy": textval(base.get("policy")),
            "entry_date": as_day(base.get("entry_date")), "exit_date": as_day(base.get("exit_date")) or None,
            "target_date": target_day or None, "target_kind": target_kind, "resolved": resolved,
            "base_pnl": base_pnl, "cohort": cohort, "base": base,
        }
        for trigger in TRIGGERS:
            watch_key = (trade_key, trigger["label"])
            watchers[watch_key] = {
                "trade_key": trade_key, "trigger_label": trigger["label"], "drop": trigger["drop"],
                "signal_date": None, "signal_spot": None, "status": "WAITING",
                "entry_reference_spot": cohort["spy_spot_entry"], "entry_date": meta[trade_key]["entry_date"],
                "target_date": target_day,
            }
            watcher_by_entry[meta[trade_key]["entry_date"]].append(watch_key)
            for tail in TAILS:
                detail_key = (trade_key, trigger["label"], tail["label"])
                details[detail_key] = {
                    "trade_key": trade_key, "trigger_label": trigger["label"], "tail_label": tail["label"],
                    "target_delta": tail["target"], "delta_min": tail["minimum"], "delta_max": tail["maximum"],
                    "signal_date": None, "signal_spot": None, "selection_status": "NOT_TRIGGERED",
                    "entry_date": None, "entry_spot": None, "contract_id": None, "strike": None,
                    "abs_delta": None, "entry_bid": None, "entry_ask": None, "entry_ask_size": 0,
                    "exit_quote_valid": False, "exit_bid": None, "exit_bid_size": 0, "exit_observed_date": None,
                }
    return meta, watcher_by_entry, watchers, details


def replay(base_results_root: Path, cache: Path, out: Path, slippage: float, commission: float):
    cohorts, trades, input_hashes = overlay.load_base_ledgers(base_results_root)
    if not trades or not cohorts:
        raise ValueError("frozen base ledger input is empty")
    meta, watcher_by_entry, watchers, details = prepare_trade_metadata(cohorts, trades)

    target_days = [m["target_date"] for m in meta.values() if m["target_date"]]
    entry_days = [m["entry_date"] for m in meta.values() if m["entry_date"]]
    start_day, end_day = min(entry_days), max(target_days)
    first_year, last_year = int(start_day[:4]), int(end_day[:4])
    underlying_path, underlying_pin = engine.download_verified("SPY", None, cache)
    spots = engine.load_spots(underlying_path, "SPY")
    option_paths, option_pins = [], []
    for year in range(first_year, last_year + 1):
        path, pin = engine.download_verified("SPY", year, cache)
        option_paths.append(path)
        option_pins.append(pin)

    active_watchers = set()
    pending = []
    exit_requests: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    source_stats = {"chain_dates": 0, "put_rows": 0, "last_chain_date": None}
    tail_lookup = {t["label"]: t for t in TAILS}

    for day, day_rows in engine.iter_symbol_days(option_paths, "SPY", start_day, end_day, source_stats):
        quotes_by_id = {engine.normalized_contract_id(row): row for row in day_rows if engine.normalized_contract_id(row)}
        spot_today = spots.get(day)

        # A close-confirmed trigger enters no earlier than the next available chain session.
        old_pending, pending = pending, []
        for detail_key in old_pending:
            trade_key, trigger_label, tail_label = detail_key
            detail = details[detail_key]
            m = meta[trade_key]
            if not m["target_date"] or day >= m["target_date"]:
                detail["selection_status"] = "TRIGGER_TOO_LATE_TO_ENTER"
                watchers[(trade_key, trigger_label)]["status"] = "TRIGGERED_BUT_TOO_LATE"
                continue
            if spot_today is None:
                detail["selection_status"] = "NO_UNDERLYING_CLOSE_ON_ENTRY_SESSION"
                watchers[(trade_key, trigger_label)]["status"] = "TRIGGERED_BUT_NO_ENTRY_PRICE"
                continue
            tail = tail_lookup[tail_label]
            pick = overlay.select_far_tail(day_rows, day, m["cohort"]["expiry"], float(spot_today),
                                           tail["target"], tail["minimum"], tail["maximum"])
            detail["entry_date"] = day
            detail["entry_spot"] = float(spot_today)
            if pick is None:
                detail["selection_status"] = "NO_ELIGIBLE_CONTRACT_ON_NEXT_SESSION"
                watchers[(trade_key, trigger_label)]["status"] = "TRIGGERED_BUT_NO_CONTRACT"
                continue
            detail.update({
                "selection_status": "SELECTED", "contract_id": pick["contract_id"],
                "strike": pick["strike"], "abs_delta": pick["abs_delta"],
                "entry_bid": pick["entry_bid"], "entry_ask": pick["entry_ask"],
                "entry_ask_size": pick["ask_size"], "entry_bid_size": pick["bid_size"],
                "otm_pct_entry": pick["otm_pct_entry"], "relative_spread": pick["relative_spread"],
                "open_interest": pick["open_interest"], "expiry": pick["selection_expiry"],
            })
            exit_requests[m["target_date"]].append(detail_key)

        # Mark the same exact contract on the base exit / last-observed date.
        for detail_key in exit_requests.pop(day, []):
            detail = details[detail_key]
            quote = quotes_by_id.get(detail["contract_id"])
            detail["exit_observed_date"] = day
            if not engine.valid_quote(quote):
                detail["exit_quote_valid"] = False
                detail["exit_bid"] = None
                detail["exit_bid_size"] = 0
                continue
            detail["exit_quote_valid"] = True
            detail["exit_bid"] = float(quote["bid"])
            detail["exit_bid_size"] = engine.displayed_size(quote, "bid")

        # Evaluate rules from information available by this close only.
        for watch_key in list(active_watchers):
            watcher = watchers[watch_key]
            if not watcher["target_date"] or day >= watcher["target_date"]:
                active_watchers.discard(watch_key)
                if watcher["status"] == "WAITING":
                    watcher["status"] = "EXITED_WITHOUT_TRIGGER"
                continue
            if watcher["status"] != "WAITING" or day <= watcher["entry_date"] or spot_today is None:
                continue
            if trigger_condition_met(float(spot_today), float(watcher["entry_reference_spot"]), float(watcher["drop"])):
                watcher["signal_date"] = day
                watcher["signal_spot"] = float(spot_today)
                watcher["status"] = "TRIGGERED"
                active_watchers.discard(watch_key)
                trade_key, trigger_label = watch_key
                for tail in TAILS:
                    detail_key = (trade_key, trigger_label, tail["label"])
                    details[detail_key]["signal_date"] = day
                    details[detail_key]["signal_spot"] = float(spot_today)
                    details[detail_key]["selection_status"] = "PENDING_NEXT_SESSION"
                    pending.append(detail_key)

        # Do not evaluate the entry-date close as a risk trigger.
        for watch_key in watcher_by_entry.get(day, []):
            watcher = watchers[watch_key]
            if watcher["target_date"] and watcher["target_date"] > day and watcher["status"] == "WAITING":
                active_watchers.add(watch_key)

    for detail_key in pending:
        details[detail_key]["selection_status"] = "NO_NEXT_CHAIN_SESSION"

    selection_rows = []
    for detail_key, d in sorted(details.items()):
        trade_key, trigger_label, tail_label = detail_key
        m = meta[trade_key]
        watcher = watchers[(trade_key, trigger_label)]
        selection_rows.append({
            "arm": m["arm"], "phase": m["phase"], "episode_id": m["episode_id"], "policy": m["policy"],
            "base_entry_date": m["entry_date"], "base_exit_date": m["exit_date"], "target_observation_date": m["target_date"],
            "trigger_label": trigger_label, "trigger_drop_pct": watcher["drop"] * 100.0,
            "entry_reference_spot": watcher["entry_reference_spot"], "trigger_date": d["signal_date"],
            "trigger_spot_close": d["signal_spot"], "tail_label": tail_label, "target_abs_delta": d["target_delta"],
            "selection_status": d["selection_status"], "tail_entry_date": d["entry_date"],
            "tail_entry_spot_close": d["entry_spot"], "tail_expiry": d.get("expiry"),
            "tail_contract_id": d["contract_id"], "tail_strike": d["strike"], "tail_abs_delta": d["abs_delta"],
            "tail_otm_pct_entry": d.get("otm_pct_entry"), "tail_entry_bid": d["entry_bid"],
            "tail_entry_ask": d["entry_ask"], "tail_entry_ask_size": d["entry_ask_size"],
            "tail_entry_bid_size": d.get("entry_bid_size"), "tail_exit_quote_valid": d["exit_quote_valid"],
            "tail_exit_bid": d["exit_bid"], "tail_exit_bid_size": d["exit_bid_size"],
            "tail_exit_observed_date": d["exit_observed_date"],
            "signal_to_entry_calendar_days": (
                (date.fromisoformat(d["entry_date"]) - date.fromisoformat(d["signal_date"])).days
                if d["entry_date"] and d["signal_date"] else None
            ),
        })

    trade_rows = []
    for trade_key, m in sorted(meta.items()):
        base = m["base"]
        for trigger in TRIGGERS:
            watcher = watchers[(trade_key, trigger["label"])]
            for tail in TAILS:
                detail = details[(trade_key, trigger["label"], tail["label"])]
                selected = detail["selection_status"] == "SELECTED"
                for qty in QUANTITIES:
                    entry_ok = selected and int(detail["entry_ask_size"] or 0) >= qty
                    exit_gate = bool(detail["exit_quote_valid"]) and int(detail["exit_bid_size"] or 0) >= qty
                    exit_bid = num(detail["exit_bid"]) if detail["exit_quote_valid"] else None
                    entry_ask = num(detail["entry_ask"]) if selected else None
                    tail_mtm = tail_realized = None
                    if entry_ok and entry_ask is not None and exit_bid is not None:
                        tail_mtm = overlay.tail_net_pnl(entry_ask, exit_bid, qty, slippage, commission)
                        if m["resolved"] and exit_gate:
                            tail_realized = tail_mtm
                    hedged = m["base_pnl"] + tail_realized if m["base_pnl"] is not None and tail_realized is not None else None
                    trade_rows.append({
                        "trade_key": trade_key, "arm": m["arm"], "phase": m["phase"], "episode_id": m["episode_id"],
                        "policy": m["policy"], "base_status": base.get("status"), "base_resolved": m["resolved"],
                        "entry_date": m["entry_date"], "exit_date": m["exit_date"], "target_observation_date": m["target_date"],
                        "base_net_pnl_usd": m["base_pnl"], "base_worst_mark_usd": num(base.get("max_adverse_mark_pnl_usd")),
                        "base_spy_short_contract_id": m["cohort"]["spy_contract_id"],
                        "base_spy_short_strike": m["cohort"]["spy_strike"], "base_spy_short_qty": m["cohort"]["short_spy_qty"],
                        "trigger_label": trigger["label"], "trigger_drop_pct": trigger["drop"] * 100.0,
                        "trigger_signal_date": watcher["signal_date"], "trigger_signal_spot_close": watcher["signal_spot"],
                        "trigger_status": watcher["status"], "trigger_fired": watcher["signal_date"] is not None,
                        "tail_label": tail["label"], "tail_target_abs_delta": tail["target"],
                        "tail_quantity": qty, "tail_selection_status": detail["selection_status"],
                        "tail_contract_id": detail["contract_id"], "tail_strike": detail["strike"],
                        "tail_abs_delta": detail["abs_delta"], "tail_entry_date": detail["entry_date"],
                        "tail_entry_spot_close": detail["entry_spot"], "tail_entry_bid": detail["entry_bid"],
                        "tail_entry_ask": entry_ask, "tail_entry_ask_size": detail["entry_ask_size"],
                        "tail_entry_executable": bool(entry_ok),
                        "tail_entry_gross_premium_usd": (round(entry_ask * 100.0 * qty, 2) if entry_ok and entry_ask is not None else None),
                        "tail_exit_target_date": m["target_date"], "tail_exit_observed_date": detail["exit_observed_date"],
                        "tail_exit_quote_valid": bool(detail["exit_quote_valid"]), "tail_exit_bid": exit_bid,
                        "tail_exit_bid_size": int(detail["exit_bid_size"] or 0), "tail_exit_executable_size_gate": bool(exit_gate),
                        "tail_net_pnl_usd": round(tail_realized, 2) if tail_realized is not None else None,
                        "tail_mtm_net_est_usd": round(tail_mtm, 2) if tail_mtm is not None else None,
                        "hedged_net_pnl_usd": round(hedged, 2) if hedged is not None else None,
                        "paired_realized_comparison": bool(m["base_pnl"] is not None and tail_realized is not None),
                        "unresolved_base_trade": not m["resolved"],
                    })

    summary_rows = build_summary(trade_rows)
    annual_rows = build_annual(trade_rows)
    stress_rows = build_tail_stress(trade_rows, details, meta, slippage, commission)
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "triggered_selection.csv", selection_rows)
    write_csv(out / "triggered_trade_level.csv", trade_rows)
    write_csv(out / "triggered_summary.csv", summary_rows)
    write_csv(out / "triggered_annual.csv", annual_rows)
    write_csv(out / "triggered_tail_stress.csv", stress_rows)
    manifest = {
        "schema": SCHEMA, "status": "COMPLETED" if all([selection_rows, trade_rows, summary_rows, annual_rows, stress_rows]) else "FAILED_EMPTY_OUTPUT",
        "base_anchor_commit": overlay.BASE_ANCHOR_COMMIT, "source_repository": engine.SOURCE_REPO,
        "source_tree_commit": engine.SOURCE_COMMIT, "base_trade_ledger_count": len(trades),
        "unique_base_cohort_count": len(cohorts), "trigger_trade_config_rows": len(trade_rows),
        "selection_state_rows": len(selection_rows), "trigger_summary_rows": len(summary_rows),
        "trigger_annual_rows": len(annual_rows), "trigger_tail_stress_rows": len(stress_rows),
        "trigger_policy": {
            "thresholds": list(TRIGGERS),
            "signal_definition": "SPY underlying daily close <= frozen base trade entry spot * (1 - threshold); dates strictly after base entry and strictly before base exit/last-observed date.",
            "execution_timing": "Buy on the next available SPY option-chain session after a close-confirmed trigger; no same-close fill and no retry after blocked entry.",
            "exit_rule": "Close the exact selected tail contract on the frozen base trade exit date; unresolved base trades remain MTM only.",
            "targets": list(TAILS), "quantities": list(QUANTITIES),
        },
        "costs": {"slippage_per_option_share_per_side_usd": slippage, "commission_per_contract_per_side_usd": commission},
        "input_ledger_sha256": input_hashes, "underlying_spot_source_pin": underlying_pin,
        "verified_spy_option_source_pins": option_pins, "spot_rows": len(spots), "chain_stats": source_stats,
        "warnings": [
            "Public EOD option quotes and displayed sizes are not verified fills.",
            "Source pinning confirms byte identity against the configured public Git mirror, not OPRA provenance.",
            "Five shifted base phases overlap and are not independent samples.",
            "Triggered comparisons require valid entry and exit displayed-size gates; quote availability can create selection bias.",
            "Tail stress estimates tail-leg expiry intrinsic economics only, not whole-book loss or probability.",
            "No NAV, margin, forced liquidation, assignment costs, or broker orders are modeled.",
        ],
    }
    (out / "triggered_manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False), encoding="utf-8")
    unconditional_summary = read_csv(out.parent / "spy_far_tail_hedge_v1" / "summary.csv")
    report = make_report(summary_rows, annual_rows, stress_rows, unconditional_summary, out)
    (out / "SPY_FAR_TAIL_TRIGGERED_HEDGE_REPORT.md").write_text(report, encoding="utf-8")
    if manifest["status"] != "COMPLETED" or len(report) < 10000:
        raise RuntimeError("triggered replay or report failed completeness checks")
    print(json.dumps({"status": manifest["status"], "base_rows": len(trades), "selection_rows": len(selection_rows),
                      "trade_rows": len(trade_rows), "summary_rows": len(summary_rows),
                      "annual_rows": len(annual_rows), "tail_stress_rows": len(stress_rows),
                      "underlying_spot_rows": len(spots), "report_bytes": len(report.encode("utf-8")),
                      "out": str(out)}, indent=2))
    return 0


def _trade_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    base_resolved = [r for r in rows if r["base_net_pnl_usd"] is not None]
    signals = [r for r in base_resolved if r["trigger_fired"]]
    entered = [r for r in base_resolved if r["tail_entry_executable"]]
    paired = [r for r in rows if r["paired_realized_comparison"]]
    base_values = [float(r["base_net_pnl_usd"]) for r in paired]
    hedge_values = [float(r["hedged_net_pnl_usd"]) for r in paired]
    tail_values = [float(r["tail_net_pnl_usd"]) for r in paired]
    if paired:
        worst_base_row = min(paired, key=lambda r: float(r["base_net_pnl_usd"]))
        matched_worst_improvement = float(worst_base_row["hedged_net_pnl_usd"]) - float(worst_base_row["base_net_pnl_usd"])
    else:
        matched_worst_improvement = None
    base_losses = [r for r in paired if float(r["base_net_pnl_usd"]) < -0.005]
    resolved_n, signal_n, paired_n = len(base_resolved), len(signals), len(paired)
    premiums_all = [float(r["tail_entry_gross_premium_usd"]) for r in rows if r["tail_entry_gross_premium_usd"] is not None]
    premiums_paired = [float(r["tail_entry_gross_premium_usd"]) for r in paired if r["tail_entry_gross_premium_usd"] is not None]
    return {
        "opened_base_trades": len(rows),
        "base_resolved_n": resolved_n, "base_unresolved_n": len(rows) - resolved_n,
        "trigger_signal_n_resolved": signal_n,
        "trigger_rate_pct_of_base_resolved": round(100.0 * signal_n / resolved_n, 2) if resolved_n else None,
        "triggered_entry_executable_n_resolved": len(entered),
        "entry_coverage_pct_of_triggered_resolved": round(100.0 * len(entered) / signal_n, 2) if signal_n else None,
        "paired_n": paired_n,
        "paired_coverage_pct_of_base_resolved": round(100.0 * paired_n / resolved_n, 2) if resolved_n else None,
        "paired_coverage_pct_of_triggered_resolved": round(100.0 * paired_n / signal_n, 2) if signal_n else None,
        "triggered_but_unpriced_open_n": sum(1 for r in base_resolved if r["tail_entry_executable"] and not r["paired_realized_comparison"]),
        "no_hedge_mean_paired_usd": round(statistics.mean(base_values), 2) if paired else None,
        "hedged_mean_paired_usd": round(statistics.mean(hedge_values), 2) if paired else None,
        "incremental_mean_paired_usd": round(statistics.mean([h-b for h, b in zip(hedge_values, base_values)]), 2) if paired else None,
        "incremental_sum_paired_usd": round(sum(tail_values), 2) if paired else None,
        "known_increment_per_all_resolved_trade_usd": round(sum(tail_values) / resolved_n, 2) if resolved_n else None,
        "paired_no_hedge_win_rate_pct": round(100.0 * sum(v > 0.005 for v in base_values) / paired_n, 2) if paired else None,
        "paired_hedged_win_rate_pct": round(100.0 * sum(v > 0.005 for v in hedge_values) / paired_n, 2) if paired else None,
        "paired_no_hedge_worst_trade_usd": round(min(base_values), 2) if paired else None,
        "paired_hedged_worst_trade_usd": round(min(hedge_values), 2) if paired else None,
        "hedged_pnl_on_worst_base_trade_usd": round(float(worst_base_row["hedged_net_pnl_usd"]), 2) if paired else None,
        "worst_base_trade_improvement_usd": round(matched_worst_improvement, 2) if paired else None,
        "baseline_losing_trades_n": len(base_losses),
        "baseline_losses_improved_n": sum(float(r["hedged_net_pnl_usd"]) > float(r["base_net_pnl_usd"]) for r in base_losses),
        "baseline_losses_turned_positive_n": sum(float(r["hedged_net_pnl_usd"]) > 0.005 for r in base_losses),
        "gross_premium_spend_total_usd": round(sum(premiums_all), 2),
        "gross_premium_spend_on_paired_usd": round(sum(premiums_paired), 2),
        "mean_gross_premium_on_paired_usd": round(statistics.mean(premiums_paired), 2) if premiums_paired else None,
    }


def build_summary(trade_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in trade_rows:
        key = (row["arm"], int(row["phase"]), row["policy"], row["trigger_label"], row["tail_label"], int(row["tail_quantity"]))
        grouped[key].append(row)
    result = []
    result_lookup = {}
    for key, rows in sorted(grouped.items()):
        arm, phase, policy, trigger, tail, qty = key
        metrics = _trade_summary(rows)
        obj = {"arm": arm, "phase": phase, "policy": policy, "trigger_label": trigger,
               "trigger_drop_pct": float(rows[0]["trigger_drop_pct"]), "tail_label": tail,
               "tail_target_abs_delta": float(rows[0]["tail_target_abs_delta"]), "tail_quantity": qty, **metrics}
        result.append(obj)
        result_lookup[key] = obj

    # Compare one-vs-three only where BOTH quantities were paired for the exact same triggered contract/trade.
    pair_maps = {}
    for key, rows in grouped.items():
        pair_maps[key] = {r["trade_key"]: r for r in rows if r["paired_realized_comparison"]}
    for key, three_obj in result_lookup.items():
        arm, phase, policy, trigger, tail, qty = key
        if qty != 3:
            continue
        key1 = (arm, phase, policy, trigger, tail, 1)
        one_obj = result_lookup.get(key1)
        if not one_obj:
            continue
        m1, m3 = pair_maps[key1], pair_maps[key]
        common_keys = sorted(set(m1) & set(m3))
        common1 = [m1[k] for k in common_keys]
        common3 = [m3[k] for k in common_keys]
        def mean_field(rows, field):
            return round(statistics.mean(float(r[field]) for r in rows), 2) if rows else None
        common_metrics = {
            "common_paired_1x3_n": len(common_keys),
            "common_1x_mean_net_usd": mean_field(common1, "hedged_net_pnl_usd"),
            "common_3x_mean_net_usd": mean_field(common3, "hedged_net_pnl_usd"),
            "common_1x_mean_tail_net_usd": mean_field(common1, "tail_net_pnl_usd"),
            "common_3x_mean_tail_net_usd": mean_field(common3, "tail_net_pnl_usd"),
            "common_3x_extra_drag_per_paired_usd": (
                round(statistics.mean(float(b["tail_net_pnl_usd"]) - float(a["tail_net_pnl_usd"]) for a, b in zip(common1, common3)), 2)
                if common_keys else None
            ),
            "common_1x_worst_hedged_usd": round(min(float(r["hedged_net_pnl_usd"]) for r in common1), 2) if common1 else None,
            "common_3x_worst_hedged_usd": round(min(float(r["hedged_net_pnl_usd"]) for r in common3), 2) if common3 else None,
        }
        three_obj.update(common_metrics)
        one_obj.update(common_metrics)
    return result


def build_annual(trade_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in trade_rows:
        exit_date = row.get("exit_date") or row.get("target_observation_date")
        if not exit_date:
            continue
        key = (row["arm"], int(row["phase"]), row["policy"], int(str(exit_date)[:4]),
               row["trigger_label"], row["tail_label"], int(row["tail_quantity"]))
        grouped[key].append(row)
    result = []
    for key, rows in sorted(grouped.items()):
        arm, phase, policy, year, trigger, tail, qty = key
        result.append({
            "arm": arm, "phase": phase, "policy": policy, "exit_year": year,
            "trigger_label": trigger, "trigger_drop_pct": float(rows[0]["trigger_drop_pct"]),
            "tail_label": tail, "tail_target_abs_delta": float(rows[0]["tail_target_abs_delta"]),
            "tail_quantity": qty, **_trade_summary(rows),
        })
    return result


def build_tail_stress(details, meta, slippage, commission):
    buckets: dict[tuple[Any, ...], list[float]] = defaultdict(list)
    for (trade_key, trigger_label, tail_label), detail in details.items():
        if detail["selection_status"] != "SELECTED" or detail["entry_ask"] is None or detail["strike"] is None:
            continue
        m = meta[trade_key]
        for qty in QUANTITIES:
            if int(detail["entry_ask_size"] or 0) < qty:
                continue
            for shock in SHOCKS:
                pnl = trigger_tail_expiry_pnl(float(detail["entry_ask"]), float(detail["strike"]),
                    float(detail["entry_spot"]), shock, qty, slippage, commission)
                key = (m["arm"], int(m["phase"]), m["policy"], trigger_label, tail_label, qty, shock)
                buckets[key].append(pnl)
    rows = []
    for key, values in sorted(buckets.items()):
        arm, phase, policy, trigger, tail, qty, shock = key
        rows.append({
            "arm": arm, "phase": phase, "policy": policy, "trigger_label": trigger, "tail_label": tail,
            "tail_quantity": qty, "spot_shock_after_hedge_entry_pct": round(shock * 100, 2),
            "entered_hedge_n": len(values), "mean_tail_expiry_net_pnl_usd": round(statistics.mean(values), 2),
            "median_tail_expiry_net_pnl_usd": round(statistics.median(values), 2),
            "worst_tail_expiry_net_pnl_usd": round(min(values), 2),
            "fraction_tail_leg_positive_pct": round(100.0 * sum(v > 0.005 for v in values) / len(values), 2),
        })
    if not rows:
        raise ValueError("no triggered hedge entries available for stress grid")
    return rows


def make_report(summary_rows, annual_rows, stress_rows, unconditional_summary, out_dir: Path) -> str:
    s_groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in summary_rows:
        s_groups[(row["arm"], row["policy"], row["trigger_label"], row["tail_label"], int(row["tail_quantity"]))].append(row)
    u_groups: dict[tuple[Any, ...], list[dict[str, str]]] = defaultdict(list)
    for row in unconditional_summary:
        u_groups[(row["arm"], row["policy"], row["tail_label"], int(float(row["tail_quantity"])))].append(row)
    primary_keys = [(trigger["label"], tail["label"], qty) for trigger in TRIGGERS for tail in TAILS for qty in QUANTITIES]
    lines = [
        "# SPY Far-Tail Triggered Hedge — Full Research Report V1", "",
        "> Research-only historical replay. Trigger rules, next-session entry lag and transaction costs were fixed before this run. No live orders were placed.", "",
        "## 1. Executive conclusion", "",
        "**Keep the no-hedge strategy as the control. Do not buy an unconditional tail hedge by default.** This experiment tests whether a fixed price-risk trigger can reduce premium spending without hiding missing quotes or treating unpriced exits as realized P&L. A trigger should only advance if it improves loss severity on matched trades enough to justify its premium budget. No single win-rate or worst-trade statistic is a deployment approval.", "",
        "### Predeclared rule", "",
        "- Trigger on a daily SPY close at least 3% or 5% below each base trade's fixed SPY entry spot. This is entry-price drawdown, not rolling-high drawdown and not a VIX/VX trigger.",
        "- The signal is known after the close. Buy no earlier than the next available SPY option-chain session using the same expiry as the base SPY short PUT.",
        "- Compare 2.5-delta and 5-delta; both use the same 0.01–0.08 eligible absolute-Delta band. Each is tested at one and three contracts.",
        "- No same-close execution, no repeat/retry after blocked next-session entry, and exit only on the frozen base exit date. Untriggered trades remain unhedged.",
        "- Preserve DTE14/DTE45, both original exit policies, all no-hedge base results and unconditional-hedge results as controls.",
        "",
        "## 2. Triggered hedge: no-hedge paired baseline and protection results", "",
        "Base and hedged P&L in each row use the exact same paired trades. Coverage is against all resolved base trades. The phase-level numbers are summarized by their median/range; the five entry phases overlap and are not independent samples.",
        "",
        "| Arm | Exit | Trigger | Tail | Qty | Trigger rate | Entry coverage among signals | Paired coverage of all resolved | Paired N range | Base mean | Hedged mean | Incremental mean | Worst loss base→hedged | Same worst-base trade improvement | Gross premium spend / phase median | Unpriced entered positions |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for arm in ("DTE14", "DTE45"):
        for policy in ("HOLD_10_OR_DTE_LE_7", "HOLD_20_OR_DTE_LE_7"):
            for trigger, tail, qty in primary_keys:
                rows = s_groups[(arm, policy, trigger, tail, qty)]
                def medf(field):
                    return median([num(r.get(field)) for r in rows])
                nlo, nhi = bounds([num(r.get("paired_n")) for r in rows])
                bmin, _ = bounds([num(r.get("paired_no_hedge_worst_trade_usd")) for r in rows])
                hmin, _ = bounds([num(r.get("paired_hedged_worst_trade_usd")) for r in rows])
                premium = medf("gross_premium_spend_total_usd")
                unpriced = medf("triggered_but_unpriced_open_n")
                lines.append(
                    f"| {arm} | {POLICY[policy]} | {trigger.replace('ENTRY_SPOT_DRAWDOWN_','')} | {TAIL[tail]['label']} | {qty} "
                    f"| {medf('trigger_rate_pct_of_base_resolved'):.2f}% "
                    f"| {medf('entry_coverage_pct_of_triggered_resolved') if medf('entry_coverage_pct_of_triggered_resolved') is not None else 0:.2f}% "
                    f"| {medf('paired_coverage_pct_of_base_resolved'):.2f}% "
                    f"| {span(nlo,nhi)} | {money(medf('no_hedge_mean_paired_usd'))} "
                    f"| {money(medf('hedged_mean_paired_usd'))} | {money(medf('incremental_mean_paired_usd'))} "
                    f"| {money(bmin)}→{money(hmin)} | {money(medf('worst_base_trade_improvement_usd'))} "
                    f"| {money(premium)} | {unpriced:.0f} |"
                )
    lines += [
        "",
        "### Definitions and accounting", "",
        "- Trigger rate = resolved trades with a confirmed trigger / all resolved base trades.",
        "- Entry coverage among signals = number of resolved trades with a selected contract and sufficient ask size / resolved triggered trades.",
        "- Paired coverage = triggered, entered, resolved tail trades with valid exact-contract exit quotes and sufficient displayed bid size / all resolved base trades.",
        "- Incremental mean = hedged minus base mean on the same paired sample, net of modeled option costs. Negative means carry cost exceeded the recorded hedge offset in that sample.",
        "- Worst loss shows each phase's worst paired base and hedged outcome. Same worst-base trade improvement identifies the most negative base trade in the paired set and compares that exact trade after hedging.",
        "- Gross premium spend is entry ask × 100 × contracts for trades with an executable displayed ask size. It is gross cash outlay, not net insurance cost.",
        "- Unpriced entered positions are disclosed and excluded from realized paired P&L; they are never assigned zero profit.",
        "",
        "## 3. Direct comparison with unconditional insurance — DTE45 / Hold-20", "",
        "For each candidate, conditional rows show the triggered paired subset; unconditional rows use the previous source-pinned replay. Each has its own paired coverage, so the matched base mean is the appropriate within-row baseline—not an all-trades mean taken from another sample.",
        "",
        "| Rule | Tail | Qty | Trigger rate | Coverage median | Paired N range | Base mean | Hedge mean | Mean change | Worst paired loss base→hedged |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for trigger, tail, qty in primary_keys:
        rows = s_groups[("DTE45", "HOLD_20_OR_DTE_LE_7", trigger, tail, qty)]
        def cm(field):
            return median([num(r.get(field)) for r in rows])
        nlo, nhi = bounds([num(r.get("paired_n")) for r in rows])
        bw = median([num(r.get("paired_no_hedge_worst_trade_usd")) for r in rows])
        hw = median([num(r.get("paired_hedged_worst_trade_usd")) for r in rows])
        lines.append(
            f"| Trigger {trigger.replace('ENTRY_SPOT_DRAWDOWN_','')} | {TAIL[tail]['label']} | {qty} "
            f"| {cm('trigger_rate_pct_of_base_resolved'):.2f}% | {cm('paired_coverage_pct_of_base_resolved'):.2f}% "
            f"| {span(nlo,nhi)} | {money(cm('no_hedge_mean_paired_usd'))} | {money(cm('hedged_mean_paired_usd'))} "
            f"| {money(cm('incremental_mean_paired_usd'))} | {money(bw)}→{money(hw)} |"
        )
        uncond = u_groups.get(("DTE45", "HOLD_20_OR_DTE_LE_7", tail, qty), [])
        if uncond:
            ulo, uhi = bounds([num(r.get("joint_resolved_paired_n")) for r in uncond])
            ubase = median([num(r.get("paired_baseline_mean_net_usd")) for r in uncond])
            uhedge = median([num(r.get("paired_hedged_mean_net_usd")) for r in uncond])
            uinc = median([num(r.get("paired_mean_incremental_hedge_usd")) for r in uncond])
            ucov = median([num(r.get("paired_coverage_pct_of_base_resolved")) for r in uncond])
            ubw = median([num(r.get("paired_baseline_worst_trade_usd")) for r in uncond])
            uhw = median([num(r.get("paired_hedged_worst_trade_usd")) for r in uncond])
            lines.append(
                f"| Unconditional | {TAIL[tail]['label']} | {qty} | Every entry scheduled | {ucov:.2f}% "
                f"| {span(ulo,uhi)} | {money(ubase)} | {money(uhedge)} | {money(uinc)} | {money(ubw)}→{money(uhw)} |"
            )

    lines += [
        "",
        "## 4. Annual behavior — DTE45 / Hold-20", "",
        "Per-trade mean P&L by frozen base exit year. The phase medians are shown, not pooled as independent observations. Different Delta/quantity arms may have different paired N and quote coverage.",
        "",
        "| Exit year | Trigger | Tail | Qty | Trigger rate | Paired coverage | Paired N range | Base mean | Hedged mean | Mean change | Same worst-base trade improvement |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    annual_groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in annual_rows:
        if row["arm"] == "DTE45" and row["policy"] == "HOLD_20_OR_DTE_LE_7":
            annual_groups[(int(row["exit_year"]), row["trigger_label"], row["tail_label"], int(row["tail_quantity"]))].append(row)
    for year in sorted({key[0] for key in annual_groups}):
        for trigger, tail, qty in primary_keys:
            rows = annual_groups.get((year, trigger, tail, qty), [])
            if not rows:
                continue
            def am(field):
                return median([num(r.get(field)) for r in rows])
            nlo, nhi = bounds([num(r.get("paired_n")) for r in rows])
            lines.append(
                f"| {year} | {trigger.replace('ENTRY_SPOT_DRAWDOWN_','')} | {TAIL[tail]['label']} | {qty} "
                f"| {am('trigger_rate_pct_of_base_resolved'):.2f}% | {am('paired_coverage_pct_of_base_resolved'):.2f}% "
                f"| {span(nlo,nhi)} | {money(am('no_hedge_mean_paired_usd'))} | {money(am('hedged_mean_paired_usd'))} "
                f"| {money(am('incremental_mean_paired_usd'))} | {money(am('worst_base_trade_improvement_usd'))} |"
            )

    lines += [
        "",
        "## 5. One vs three contracts on the exact same paired trades", "",
        "The 3x-valid sample is the matched comparison set for both quantities. Because the same selected contract is used, any 3x-valid entry and exit size also passes the 1x gates. This prevents a more favorable 1x sample from being compared to a different 3x sample.",
        "",
        "| Arm | Exit | Trigger | Tail | Common N range | 1x hedge mean | 3x hedge mean | 1x tail net mean | 3x tail net mean | Extra 3x tail drag per trade | Worst hedged trade 1x→3x |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for arm in ("DTE14", "DTE45"):
        for policy in ("HOLD_10_OR_DTE_LE_7", "HOLD_20_OR_DTE_LE_7"):
            for trigger, tail, qty in primary_keys:
                if qty != 3:
                    continue
                rows = s_groups[(arm, policy, trigger, tail, qty)]
                def qm(field):
                    return median([num(r.get(field)) for r in rows])
                nlo, nhi = bounds([num(r.get("common_paired_1x3_n")) for r in rows])
                lines.append(
                    f"| {arm} | {POLICY[policy]} | {trigger.replace('ENTRY_SPOT_DRAWDOWN_','')} | {TAIL[tail]['label']} "
                    f"| {span(nlo,nhi)} | {money(qm('common_1x_mean_net_usd'))} | {money(qm('common_3x_mean_net_usd'))} "
                    f"| {money(qm('common_1x_mean_tail_net_usd'))} | {money(qm('common_3x_mean_tail_net_usd'))} "
                    f"| {money(qm('common_3x_extra_drag_per_paired_usd'))} "
                    f"| {money(qm('common_1x_worst_hedged_usd'))}→{money(qm('common_3x_worst_hedged_usd'))} |"
                )

    lines += [
        "",
        "## 6. Tail-leg expiry stress after the delayed hedge entry", "",
        "Hypothetical intrinsic payoff of the selected long PUT from the actual hedge-entry spot. It includes modeled round-trip costs, but is not a whole-book stress result, historical path replay or probability forecast. It excludes the base SPY short PUT's updated market value at the later trigger date and the QQQ long PUT.",
        "",
        "| Arm | Exit | Trigger | Tail | Qty | SPY shock after hedge entry | Entered N range | Mean tail P&L range | Worst tail P&L range | Positive tail payoff rate median |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    stress_groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in stress_rows:
        key = (row["arm"], row["policy"], row["trigger_label"], row["tail_label"], int(row["tail_quantity"]),
               float(row["spot_shock_after_hedge_entry_pct"]))
        stress_groups[key].append(row)
    for key, rows in sorted(stress_groups.items()):
        arm, policy, trigger, tail, qty, shock = key
        nlo, nhi = bounds([num(r.get("entered_hedge_n")) for r in rows])
        meanlo, meanhi = bounds([num(r.get("mean_tail_expiry_net_pnl_usd")) for r in rows])
        worstlo, worsthi = bounds([num(r.get("worst_tail_expiry_net_pnl_usd")) for r in rows])
        positive = median([num(r.get("fraction_tail_leg_positive_pct")) for r in rows])
        lines.append(
            f"| {arm} | {POLICY[policy]} | {trigger.replace('ENTRY_SPOT_DRAWDOWN_','')} | {TAIL[tail]['label']} | {qty} "
            f"| {shock:g}% | {span(nlo,nhi)} | {money(meanlo)} to {money(meanhi)} "
            f"| {money(worstlo)} to {money(worsthi)} | {positive:.2f}% |"
        )

    lines += [
        "",
        "## 7. Decision framework — is the insurance worth paying for?", "",
        "A risk-triggered candidate should advance only when all of the following are acceptable together:",
        "",
        "1. **Loss-tail improvement:** better same-worst-base-trade outcome and paired worst loss, not just a theoretical payoff under a -50% shock.",
        "2. **Quote coverage:** enough trigger-day and exit-day option quote/size coverage; report unpriced entries rather than assuming zero P&L.",
        "3. **Premium budget:** compare gross premium outlay and realized incremental P&L against downside reduction. Annual figures here are per-trade averages, not account income.",
        "4. **Quantity scaling:** judge 1x and 3x on the same common paired set. More contracts should be treated as higher-budget disaster insurance unless results show otherwise.",
        "5. **Independent validation:** the rule is fixed before testing, but the result still uses the same historical period for exploration. Before deployment, validate it on a separate holdout or forward sample.",
        "6. **Whole-book risk:** replay full QQQ+SPY NAV, concurrent positions, margin, early assignment/exercise, forced liquidation and realistic fill uncertainty. The current tail-leg stress cannot certify portfolio MaxDD.",
        "",
        "### Interpretation cautions", "",
        "- A 3% trigger can occur more often and buy earlier; a 5% trigger can spend less but may enter too late. The results table should determine whether that trade-off is worthwhile.",
        "- If 3x improves severe downside but materially reduces average P&L, it is insurance—not a demonstrated return enhancer.",
        "- The no-hedge strategy is the mandatory control. Do not choose a trigger on these years and then call those same years independent validation.",
        "",
        "## 8. Data lineage and limitations", "",
        "- The original base ledgers and unconditional replay results are read-only reference inputs.",
        "- Daily spot data and SPY options are source-pinned to anahatsingh-ui/options-dataset-hist commit 37f6c456fe1a4775c875673fb8ef907d5cd2fd66. Hash pinning proves byte identity against the Git mirror, not OPRA authenticity.",
        "- End-of-day quotes and displayed sizes are not verified fills; the size check is only an eligibility gate.",
        "- The five shifted base phases overlap and are not independent samples.",
        "- The trigger is based on fixed entry-price drawdown, not high-water drawdown, VIX/VX structure, or option delta deterioration.",
        "- Triggered paired samples exclude entered positions with insufficient exit quotes/sizes; those unknowns are counted separately, so quote-availability selection bias remains.",
        "- Tail stress is expiry intrinsic P&L of the tail option alone. It excludes the base SPY short PUT's updated market value at the trigger date, QQQ long PUT, margin, forced liquidation, assignment/exercise costs and financing.",
        "- No broker orders or live execution were performed.",
        "",
        "## 9. Reproducible artifacts", "",
        "- [Triggered contract selection and trigger dates](triggered_selection.csv)",
        "- [Full base-vs-triggered trade ledger](triggered_trade_level.csv)",
        "- [Phase/config trigger summary](triggered_summary.csv)",
        "- [Annual results](triggered_annual.csv)",
        "- [Tail-leg expiry stress grid](triggered_tail_stress.csv)",
        "- [Full unconditional SPY tail decision report](../spy_far_tail_hedge_v1/SPY_FAR_TAIL_DECISION_REPORT.md)",
        "- [Research PR #147](https://github.com/JUN-ZS/brush-timber-mountain-brook/pull/147)",
        "",
    ]
    report = "\n".join(lines)
    if len(report) < 10000:
        raise ValueError("trigger report unexpectedly short")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-results-root", type=Path, default=ROOT / "results")
    parser.add_argument("--cache", type=Path, default=Path.home() / ".cache" / "spy-far-tail-triggered-v1")
    parser.add_argument("--out", type=Path, default=ROOT / "results" / "spy_far_tail_triggered_v1")
    parser.add_argument("--slippage-per-share", type=float, default=SLIPPAGE_DEFAULT)
    parser.add_argument("--commission-per-contract-per-side", type=float, default=COMMISSION_DEFAULT)
    args = parser.parse_args()
    if args.slippage_per_share < 0 or args.commission_per_contract_per_side < 0:
        raise ValueError("transaction costs must be non-negative")

    cohorts, trades, input_hashes = overlay.load_base_ledgers(args.base_results_root)
    if not trades or not cohorts:
        raise ValueError("frozen base ledger input is empty")
    # Replay owns output generation so it can preserve pinned source identity and counts in the manifest.
    manifest = _run_replay(cohorts, trades, input_hashes, args.cache, args.out,
                           args.slippage_per_share, args.commission_per_contract_per_side)
    print(json.dumps(manifest, indent=2))
    return 0


def _run_replay(cohorts, trades, input_hashes, cache: Path, out: Path, slippage: float, commission: float):
    meta, watcher_by_entry, watchers, details = prepare_trade_metadata(cohorts, trades)
    target_days = [m["target_date"] for m in meta.values() if m["target_date"]]
    entry_days = [m["entry_date"] for m in meta.values() if m["entry_date"]]
    start_day, end_day = min(entry_days), max(target_days)
    first_year, last_year = int(start_day[:4]), int(end_day[:4])
    underlying_path, underlying_pin = engine.download_verified("SPY", None, cache)
    spots = engine.load_spots(underlying_path, "SPY")
    option_paths, option_pins = [], []
    for year in range(first_year, last_year + 1):
        path, pin = engine.download_verified("SPY", year, cache)
        option_paths.append(path)
        option_pins.append(pin)

    active_watchers = set()
    pending = []
    exit_requests: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    source_stats = {"chain_dates": 0, "put_rows": 0, "last_chain_date": None}
    tail_lookup = {t["label"]: t for t in TAILS}
    for day, day_rows in engine.iter_symbol_days(option_paths, "SPY", start_day, end_day, source_stats):
        quotes_by_id = {engine.normalized_contract_id(row): row for row in day_rows if engine.normalized_contract_id(row)}
        spot_today = spots.get(day)

        old_pending, pending = pending, []
        for detail_key in old_pending:
            trade_key, trigger_label, tail_label = detail_key
            detail = details[detail_key]
            m = meta[trade_key]
            if not m["target_date"] or day >= m["target_date"]:
                detail["selection_status"] = "TRIGGER_TOO_LATE_TO_ENTER"
                watchers[(trade_key, trigger_label)]["status"] = "TRIGGERED_BUT_TOO_LATE"
                continue
            if spot_today is None:
                detail["selection_status"] = "NO_UNDERLYING_CLOSE_ON_ENTRY_SESSION"
                watchers[(trade_key, trigger_label)]["status"] = "TRIGGERED_BUT_NO_ENTRY_PRICE"
                continue
            tail = tail_lookup[tail_label]
            pick = overlay.select_far_tail(day_rows, day, m["cohort"]["expiry"], float(spot_today),
                                           tail["target"], tail["minimum"], tail["maximum"])
            detail["entry_date"], detail["entry_spot"] = day, float(spot_today)
            if pick is None:
                detail["selection_status"] = "NO_ELIGIBLE_CONTRACT_ON_NEXT_SESSION"
                watchers[(trade_key, trigger_label)]["status"] = "TRIGGERED_BUT_NO_CONTRACT"
                continue
            detail.update({
                "selection_status": "SELECTED", "contract_id": pick["contract_id"],
                "strike": pick["strike"], "abs_delta": pick["abs_delta"],
                "entry_bid": pick["entry_bid"], "entry_ask": pick["entry_ask"],
                "entry_ask_size": pick["ask_size"], "entry_bid_size": pick["bid_size"],
                "otm_pct_entry": pick["otm_pct_entry"], "relative_spread": pick["relative_spread"],
                "open_interest": pick["open_interest"], "expiry": pick["selection_expiry"],
            })
            exit_requests[m["target_date"]].append(detail_key)

        for detail_key in exit_requests.pop(day, []):
            detail = details[detail_key]
            quote = quotes_by_id.get(detail["contract_id"])
            detail["exit_observed_date"] = day
            if not engine.valid_quote(quote):
                detail["exit_quote_valid"], detail["exit_bid"], detail["exit_bid_size"] = False, None, 0
                continue
            detail["exit_quote_valid"] = True
            detail["exit_bid"] = float(quote["bid"])
            detail["exit_bid_size"] = engine.displayed_size(quote, "bid")

        for watch_key in list(active_watchers):
            watcher = watchers[watch_key]
            if not watcher["target_date"] or day >= watcher["target_date"]:
                active_watchers.discard(watch_key)
                if watcher["status"] == "WAITING":
                    watcher["status"] = "EXITED_WITHOUT_TRIGGER"
                continue
            if watcher["status"] != "WAITING" or day <= watcher["entry_date"] or spot_today is None:
                continue
            if trigger_condition_met(float(spot_today), float(watcher["entry_reference_spot"]), float(watcher["drop"])):
                watcher["signal_date"], watcher["signal_spot"], watcher["status"] = day, float(spot_today), "TRIGGERED"
                active_watchers.discard(watch_key)
                trade_key, trigger_label = watch_key
                for tail in TAILS:
                    detail_key = (trade_key, trigger_label, tail["label"])
                    details[detail_key]["signal_date"] = day
                    details[detail_key]["signal_spot"] = float(spot_today)
                    details[detail_key]["selection_status"] = "PENDING_NEXT_SESSION"
                    pending.append(detail_key)

        for watch_key in watcher_by_entry.get(day, []):
            watcher = watchers[watch_key]
            if watcher["target_date"] and watcher["target_date"] > day and watcher["status"] == "WAITING":
                active_watchers.add(watch_key)

    for detail_key in pending:
        details[detail_key]["selection_status"] = "NO_NEXT_CHAIN_SESSION"

    selection_rows = []
    for detail_key, d in sorted(details.items()):
        trade_key, trigger_label, tail_label = detail_key
        m, watcher = meta[trade_key], watchers[(trade_key, trigger_label)]
        selection_rows.append({
            "arm": m["arm"], "phase": m["phase"], "episode_id": m["episode_id"], "policy": m["policy"],
            "base_entry_date": m["entry_date"], "base_exit_date": m["exit_date"], "target_observation_date": m["target_date"],
            "trigger_label": trigger_label, "trigger_drop_pct": watcher["drop"] * 100.0,
            "entry_reference_spot": watcher["entry_reference_spot"], "trigger_date": d["signal_date"],
            "trigger_spot_close": d["signal_spot"], "tail_label": tail_label, "target_abs_delta": d["target_delta"],
            "selection_status": d["selection_status"], "tail_entry_date": d["entry_date"],
            "tail_entry_spot_close": d["entry_spot"], "tail_expiry": d.get("expiry"),
            "tail_contract_id": d["contract_id"], "tail_strike": d["strike"], "tail_abs_delta": d["abs_delta"],
            "tail_otm_pct_entry": d.get("otm_pct_entry"), "tail_entry_bid": d["entry_bid"],
            "tail_entry_ask": d["entry_ask"], "tail_entry_ask_size": d["entry_ask_size"],
            "tail_entry_bid_size": d.get("entry_bid_size"), "tail_exit_quote_valid": d["exit_quote_valid"],
            "tail_exit_bid": d["exit_bid"], "tail_exit_bid_size": d["exit_bid_size"],
            "tail_exit_observed_date": d["exit_observed_date"],
            "signal_to_entry_calendar_days": (
                (date.fromisoformat(d["entry_date"]) - date.fromisoformat(d["signal_date"])).days
                if d["entry_date"] and d["signal_date"] else None
            ),
        })

    trade_rows = []
    for trade_key, m in sorted(meta.items()):
        base = m["base"]
        for trigger in TRIGGERS:
            watcher = watchers[(trade_key, trigger["label"])]
            for tail in TAILS:
                detail = details[(trade_key, trigger["label"], tail["label"])]
                selected = detail["selection_status"] == "SELECTED"
                for qty in QUANTITIES:
                    entry_ok = selected and int(detail["entry_ask_size"] or 0) >= qty
                    exit_gate = bool(detail["exit_quote_valid"]) and int(detail["exit_bid_size"] or 0) >= qty
                    exit_bid = num(detail["exit_bid"]) if detail["exit_quote_valid"] else None
                    entry_ask = num(detail["entry_ask"]) if selected else None
                    tail_mtm = tail_realized = None
                    if entry_ok and entry_ask is not None and exit_bid is not None:
                        tail_mtm = overlay.tail_net_pnl(entry_ask, exit_bid, qty, slippage, commission)
                        if m["resolved"] and exit_gate:
                            tail_realized = tail_mtm
                    hedged = m["base_pnl"] + tail_realized if m["base_pnl"] is not None and tail_realized is not None else None
                    trade_rows.append({
                        "trade_key": trade_key, "arm": m["arm"], "phase": m["phase"], "episode_id": m["episode_id"],
                        "policy": m["policy"], "base_status": base.get("status"), "base_resolved": m["resolved"],
                        "entry_date": m["entry_date"], "exit_date": m["exit_date"], "target_observation_date": m["target_date"],
                        "base_net_pnl_usd": m["base_pnl"], "base_worst_mark_usd": num(base.get("max_adverse_mark_pnl_usd")),
                        "base_spy_short_contract_id": m["cohort"]["spy_contract_id"],
                        "base_spy_short_strike": m["cohort"]["spy_strike"], "base_spy_short_qty": m["cohort"]["short_spy_qty"],
                        "trigger_label": trigger["label"], "trigger_drop_pct": trigger["drop"] * 100.0,
                        "trigger_signal_date": watcher["signal_date"], "trigger_signal_spot_close": watcher["signal_spot"],
                        "trigger_status": watcher["status"], "trigger_fired": watcher["signal_date"] is not None,
                        "tail_label": tail["label"], "tail_target_abs_delta": tail["target"],
                        "tail_quantity": qty, "tail_selection_status": detail["selection_status"],
                        "tail_contract_id": detail["contract_id"], "tail_strike": detail["strike"],
                        "tail_abs_delta": detail["abs_delta"], "tail_entry_date": detail["entry_date"],
                        "tail_entry_spot_close": detail["entry_spot"], "tail_entry_bid": detail["entry_bid"],
                        "tail_entry_ask": entry_ask, "tail_entry_ask_size": detail["entry_ask_size"],
                        "tail_entry_executable": bool(entry_ok),
                        "tail_entry_gross_premium_usd": (round(entry_ask * 100.0 * qty, 2) if entry_ok and entry_ask is not None else None),
                        "tail_exit_target_date": m["target_date"], "tail_exit_observed_date": detail["exit_observed_date"],
                        "tail_exit_quote_valid": bool(detail["exit_quote_valid"]), "tail_exit_bid": exit_bid,
                        "tail_exit_bid_size": int(detail["exit_bid_size"] or 0), "tail_exit_executable_size_gate": bool(exit_gate),
                        "tail_net_pnl_usd": round(tail_realized, 2) if tail_realized is not None else None,
                        "tail_mtm_net_est_usd": round(tail_mtm, 2) if tail_mtm is not None else None,
                        "hedged_net_pnl_usd": round(hedged, 2) if hedged is not None else None,
                        "paired_realized_comparison": bool(m["base_pnl"] is not None and tail_realized is not None),
                        "unresolved_base_trade": not m["resolved"],
                    })

    summary_rows = build_summary(trade_rows)
    annual_rows = build_annual(trade_rows)
    stress_rows = build_tail_stress(details, meta, slippage, commission)
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "triggered_selection.csv", selection_rows)
    write_csv(out / "triggered_trade_level.csv", trade_rows)
    write_csv(out / "triggered_summary.csv", summary_rows)
    write_csv(out / "triggered_annual.csv", annual_rows)
    write_csv(out / "triggered_tail_stress.csv", stress_rows)
    manifest = {
        "schema": SCHEMA, "status": "COMPLETED" if all([selection_rows, trade_rows, summary_rows, annual_rows, stress_rows]) else "FAILED_EMPTY_OUTPUT",
        "base_anchor_commit": overlay.BASE_ANCHOR_COMMIT, "source_repository": engine.SOURCE_REPO,
        "source_tree_commit": engine.SOURCE_COMMIT, "base_trade_ledger_count": len(trades),
        "unique_base_cohort_count": len(cohorts), "trigger_trade_config_rows": len(trade_rows),
        "selection_state_rows": len(selection_rows), "trigger_summary_rows": len(summary_rows),
        "trigger_annual_rows": len(annual_rows), "trigger_tail_stress_rows": len(stress_rows),
        "trigger_policy": {
            "thresholds": list(TRIGGERS),
            "signal_definition": "SPY underlying daily close <= frozen base trade entry spot * (1 - threshold); dates strictly after base entry and strictly before base exit/last-observed date.",
            "execution_timing": "Buy on the next available SPY option-chain session after a close-confirmed trigger; no same-close fill and no retry after blocked entry.",
            "exit_rule": "Close the exact selected tail contract on the frozen base trade exit date; unresolved base trades remain MTM only.",
            "targets": list(TAILS), "quantities": list(QUANTITIES),
        },
        "costs": {"slippage_per_option_share_per_side_usd": slippage, "commission_per_contract_per_side_usd": commission},
        "input_ledger_sha256": input_hashes, "underlying_spot_source_pin": underlying_pin,
        "verified_spy_option_source_pins": option_pins, "spot_rows": len(spots), "chain_stats": source_stats,
        "warnings": [
            "Public EOD option quotes and displayed sizes are not verified fills.",
            "Source pinning confirms byte identity against the configured public Git mirror, not OPRA provenance.",
            "Five shifted base phases overlap and are not independent samples.",
            "Triggered comparisons require valid entry and exit displayed-size gates; quote availability can create selection bias.",
            "Tail stress estimates tail-leg expiry intrinsic economics only, not whole-book loss or probability.",
            "No NAV, margin, forced liquidation, assignment costs, or broker orders are modeled.",
        ],
    }
    (out / "triggered_manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False), encoding="utf-8")
    unconditional_summary = read_csv(out.parent / "spy_far_tail_hedge_v1" / "summary.csv")
    report = make_report(summary_rows, annual_rows, stress_rows, unconditional_summary, out)
    (out / "SPY_FAR_TAIL_TRIGGERED_HEDGE_REPORT.md").write_text(report, encoding="utf-8")
    if manifest["status"] != "COMPLETED" or len(report) < 10000:
        raise RuntimeError("triggered replay or report failed completeness checks")
    manifest["report_bytes"] = len(report.encode("utf-8"))
    (out / "triggered_manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False), encoding="utf-8")
    return {"status": manifest["status"], "base_rows": len(trades), "selection_rows": len(selection_rows),
            "trade_rows": len(trade_rows), "summary_rows": len(summary_rows), "annual_rows": len(annual_rows),
            "tail_stress_rows": len(stress_rows), "underlying_spot_rows": len(spots),
            "report_bytes": len(report.encode("utf-8")), "out": str(out)}


def _trade_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    base_resolved = [r for r in rows if r["base_net_pnl_usd"] is not None]
    signals = [r for r in base_resolved if r["trigger_fired"]]
    entered = [r for r in base_resolved if r["tail_entry_executable"]]
    paired = [r for r in rows if r["paired_realized_comparison"]]
    base_values = [float(r["base_net_pnl_usd"]) for r in paired]
    hedge_values = [float(r["hedged_net_pnl_usd"]) for r in paired]
    tail_values = [float(r["tail_net_pnl_usd"]) for r in paired]
    if paired:
        worst_base_row = min(paired, key=lambda r: float(r["base_net_pnl_usd"]))
        worst_improvement = float(worst_base_row["hedged_net_pnl_usd"]) - float(worst_base_row["base_net_pnl_usd"])
    else:
        worst_improvement = None
    base_losses = [r for r in paired if float(r["base_net_pnl_usd"]) < -0.005]
    resolved_n, signal_n, paired_n = len(base_resolved), len(signals), len(paired)
    premiums_all = [float(r["tail_entry_gross_premium_usd"]) for r in rows if r["tail_entry_gross_premium_usd"] is not None]
    premiums_paired = [float(r["tail_entry_gross_premium_usd"]) for r in paired if r["tail_entry_gross_premium_usd"] is not None]
    return {
        "opened_base_trades": len(rows), "base_resolved_n": resolved_n, "base_unresolved_n": len(rows) - resolved_n,
        "trigger_signal_n_resolved": signal_n,
        "trigger_rate_pct_of_base_resolved": round(100.0 * signal_n / resolved_n, 2) if resolved_n else None,
        "triggered_entry_executable_n_resolved": len(entered),
        "entry_coverage_pct_of_triggered_resolved": round(100.0 * len(entered) / signal_n, 2) if signal_n else None,
        "paired_n": paired_n,
        "paired_coverage_pct_of_base_resolved": round(100.0 * paired_n / resolved_n, 2) if resolved_n else None,
        "paired_coverage_pct_of_triggered_resolved": round(100.0 * paired_n / signal_n, 2) if signal_n else None,
        "triggered_but_unpriced_open_n": sum(1 for r in base_resolved if r["tail_entry_executable"] and not r["paired_realized_comparison"]),
        "no_hedge_mean_paired_usd": round(statistics.mean(base_values), 2) if paired else None,
        "hedged_mean_paired_usd": round(statistics.mean(hedge_values), 2) if paired else None,
        "incremental_mean_paired_usd": round(statistics.mean([h-b for h, b in zip(hedge_values, base_values)]), 2) if paired else None,
        "incremental_sum_paired_usd": round(sum(tail_values), 2) if paired else None,
        "known_increment_per_all_resolved_trade_usd": round(sum(tail_values) / resolved_n, 2) if resolved_n else None,
        "paired_no_hedge_win_rate_pct": round(100.0 * sum(v > 0.005 for v in base_values) / paired_n, 2) if paired else None,
        "paired_hedged_win_rate_pct": round(100.0 * sum(v > 0.005 for v in hedge_values) / paired_n, 2) if paired else None,
        "paired_no_hedge_worst_trade_usd": round(min(base_values), 2) if paired else None,
        "paired_hedged_worst_trade_usd": round(min(hedge_values), 2) if paired else None,
        "hedged_pnl_on_worst_base_trade_usd": round(float(worst_base_row["hedged_net_pnl_usd"]), 2) if paired else None,
        "worst_base_trade_improvement_usd": round(worst_improvement, 2) if paired else None,
        "baseline_losing_trades_n": len(base_losses),
        "baseline_losses_improved_n": sum(float(r["hedged_net_pnl_usd"]) > float(r["base_net_pnl_usd"]) for r in base_losses),
        "baseline_losses_turned_positive_n": sum(float(r["hedged_net_pnl_usd"]) > 0.005 for r in base_losses),
        "gross_premium_spend_total_usd": round(sum(premiums_all), 2),
        "gross_premium_spend_on_paired_usd": round(sum(premiums_paired), 2),
        "mean_gross_premium_on_paired_usd": round(statistics.mean(premiums_paired), 2) if premiums_paired else None,
    }


def build_summary(trade_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in trade_rows:
        key = (row["arm"], int(row["phase"]), row["policy"], row["trigger_label"], row["tail_label"], int(row["tail_quantity"]))
        grouped[key].append(row)
    result, lookup = [], {}
    for key, rows in sorted(grouped.items()):
        arm, phase, policy, trigger, tail, qty = key
        obj = {
            "arm": arm, "phase": phase, "policy": policy, "trigger_label": trigger,
            "trigger_drop_pct": float(rows[0]["trigger_drop_pct"]), "tail_label": tail,
            "tail_target_abs_delta": float(rows[0]["tail_target_abs_delta"]), "tail_quantity": qty,
            **_trade_summary(rows),
        }
        result.append(obj)
        lookup[key] = obj

    # One-vs-three comparison restricted to the exact trades where both quantities were paired.
    paired_maps = {key: {r["trade_key"]: r for r in rows if r["paired_realized_comparison"]} for key, rows in grouped.items()}
    for key, obj3 in lookup.items():
        arm, phase, policy, trigger, tail, qty = key
        if qty != 3:
            continue
        key1 = (arm, phase, policy, trigger, tail, 1)
        obj1 = lookup.get(key1)
        if obj1 is None:
            continue
        map1, map3 = paired_maps[key1], paired_maps[key]
        common_keys = sorted(set(map1) & set(map3))
        common1, common3 = [map1[k] for k in common_keys], [map3[k] for k in common_keys]
        def meanfield(rows, field):
            return round(statistics.mean(float(r[field]) for r in rows), 2) if rows else None
        common_metrics = {
            "common_paired_1x3_n": len(common_keys),
            "common_1x_mean_net_usd": meanfield(common1, "hedged_net_pnl_usd"),
            "common_3x_mean_net_usd": meanfield(common3, "hedged_net_pnl_usd"),
            "common_1x_mean_tail_net_usd": meanfield(common1, "tail_net_pnl_usd"),
            "common_3x_mean_tail_net_usd": meanfield(common3, "tail_net_pnl_usd"),
            "common_3x_extra_drag_per_paired_usd": (
                round(statistics.mean(float(b["tail_net_pnl_usd"]) - float(a["tail_net_pnl_usd"]) for a, b in zip(common1, common3)), 2)
                if common_keys else None
            ),
            "common_1x_worst_hedged_usd": round(min(float(r["hedged_net_pnl_usd"]) for r in common1), 2) if common1 else None,
            "common_3x_worst_hedged_usd": round(min(float(r["hedged_net_pnl_usd"]) for r in common3), 2) if common3 else None,
        }
        obj3.update(common_metrics)
        obj1.update(common_metrics)
    return result


def build_annual(trade_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in trade_rows:
        exit_day = row.get("exit_date") or row.get("target_observation_date")
        if not exit_day:
            continue
        key = (row["arm"], int(row["phase"]), row["policy"], int(str(exit_day)[:4]),
               row["trigger_label"], row["tail_label"], int(row["tail_quantity"]))
        grouped[key].append(row)
    result = []
    for key, rows in sorted(grouped.items()):
        arm, phase, policy, year, trigger, tail, qty = key
        result.append({
            "arm": arm, "phase": phase, "policy": policy, "exit_year": year,
            "trigger_label": trigger, "trigger_drop_pct": float(rows[0]["trigger_drop_pct"]),
            "tail_label": tail, "tail_target_abs_delta": float(rows[0]["tail_target_abs_delta"]),
            "tail_quantity": qty, **_trade_summary(rows),
        })
    return result


def build_tail_stress(details, meta, slippage, commission):
    buckets: dict[tuple[Any, ...], list[float]] = defaultdict(list)
    for (trade_key, trigger_label, tail_label), detail in details.items():
        if detail["selection_status"] != "SELECTED" or detail["entry_ask"] is None or detail["strike"] is None:
            continue
        m = meta[trade_key]
        for qty in QUANTITIES:
            if int(detail["entry_ask_size"] or 0) < qty:
                continue
            for shock in SHOCKS:
                pnl = trigger_tail_expiry_pnl(float(detail["entry_ask"]), float(detail["strike"]),
                    float(detail["entry_spot"]), shock, qty, slippage, commission)
                key = (m["arm"], int(m["phase"]), m["policy"], trigger_label, tail_label, qty, shock)
                buckets[key].append(pnl)
    result = []
    for key, values in sorted(buckets.items()):
        arm, phase, policy, trigger, tail, qty, shock = key
        result.append({
            "arm": arm, "phase": phase, "policy": policy, "trigger_label": trigger, "tail_label": tail,
            "tail_quantity": qty, "spot_shock_after_hedge_entry_pct": round(shock * 100, 2),
            "entered_hedge_n": len(values), "mean_tail_expiry_net_pnl_usd": round(statistics.mean(values), 2),
            "median_tail_expiry_net_pnl_usd": round(statistics.median(values), 2),
            "worst_tail_expiry_net_pnl_usd": round(min(values), 2),
            "fraction_tail_leg_positive_pct": round(100.0 * sum(v > 0.005 for v in values) / len(values), 2),
        })
    if not result:
        raise ValueError("no triggered hedge entries available for stress grid")
    return result


def make_report(summary_rows, annual_rows, stress_rows, unconditional_summary, out_dir: Path) -> str:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in summary_rows:
        groups[(row["arm"], row["policy"], row["trigger_label"], row["tail_label"], int(row["tail_quantity"]))].append(row)
    uncond: dict[tuple[Any, ...], list[dict[str, str]]] = defaultdict(list)
    for row in unconditional_summary:
        uncond[(row["arm"], row["policy"], row["tail_label"], int(float(row["tail_quantity"])))].append(row)
    candidates = [(tr["label"], ta["label"], q) for tr in TRIGGERS for ta in TAILS for q in QUANTITIES]
    lines = [
        "# SPY Far-Tail Triggered Hedge — Full Research Report V1", "",
        "> Research-only historical replay. Trigger rules, next-session entry lag and costs were fixed before this run. No live orders were placed.", "",
        "## 1. Executive conclusion", "",
        "**Keep the no-hedge strategy as the control. Do not buy an unconditional tail hedge by default.** This experiment tests whether a fixed price-risk trigger can reduce premium spending without hiding missing quotes or treating unpriced exits as realized P&L. A trigger should only advance if it improves loss severity on matched trades enough to justify premium cost. No single win-rate or worst-trade statistic is a deployment approval.", "",
        "### Predeclared rule", "",
        "- Trigger on a daily SPY close at least 3% or 5% below each base trade's fixed SPY entry spot. This is entry-price drawdown, not rolling-high drawdown and not a VIX/VX trigger.",
        "- The signal is known after the close. Buy no earlier than the next available SPY option-chain session using the same expiry as the base SPY short PUT.",
        "- Compare 2.5-delta and 5-delta; both use the same 0.01–0.08 eligible absolute-Delta band. Each is tested at one and three contracts.",
        "- No same-close execution, no repeat/retry after blocked next-session entry, and exit only on the frozen base exit date. Untriggered trades remain unhedged.",
        "- Preserve DTE14/DTE45, both original exit policies, all no-hedge base results and unconditional-hedge results as controls.",
        "",
        "## 2. Triggered hedge: no-hedge paired baseline and protection results", "",
        "Base and hedged P&L in each row use the exact same paired trades. Coverage is against all resolved base trades. The phase-level numbers are summarized by their median/range; the five entry phases overlap and are not independent samples.",
        "",
        "| Arm | Exit | Trigger | Tail | Qty | Trigger rate | Entry coverage among signals | Paired coverage of all resolved | Paired N range | Base mean | Hedged mean | Incremental mean | Worst loss base→hedged | Same worst-base trade improvement | Gross premium spend / phase median | Unpriced entered positions |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for arm in ("DTE14", "DTE45"):
        for policy in ("HOLD_10_OR_DTE_LE_7", "HOLD_20_OR_DTE_LE_7"):
            for trigger, tail, qty in candidates:
                rows = groups[(arm, policy, trigger, tail, qty)]
                def medf(field):
                    return median([num(r.get(field)) for r in rows])
                nlo, nhi = bounds([num(r.get("paired_n")) for r in rows])
                bw, _ = bounds([num(r.get("paired_no_hedge_worst_trade_usd")) for r in rows])
                hw, _ = bounds([num(r.get("paired_hedged_worst_trade_usd")) for r in rows])
                prem = medf("gross_premium_spend_total_usd")
                unpriced_n = medf("triggered_but_unpriced_open_n")
                entry_cov = medf("entry_coverage_pct_of_triggered_resolved")
                lines.append(
                    f"| {arm} | {POLICY[policy]} | {trigger.replace('ENTRY_SPOT_DRAWDOWN_','')} | {TAIL[tail]['label']} | {qty} "
                    f"| {medf('trigger_rate_pct_of_base_resolved'):.2f}% "
                    f"| {(entry_cov if entry_cov is not None else 0):.2f}% "
                    f"| {medf('paired_coverage_pct_of_base_resolved'):.2f}% | {span(nlo,nhi)} "
                    f"| {money(medf('no_hedge_mean_paired_usd'))} | {money(medf('hedged_mean_paired_usd'))} "
                    f"| {money(medf('incremental_mean_paired_usd'))} | {money(bw)}→{money(hw)} "
                    f"| {money(medf('worst_base_trade_improvement_usd'))} | {money(prem)} | {(unpriced_n if unpriced_n is not None else 0):.0f} |"
                )
    lines += [
        "",
        "### Definitions and accounting", "",
        "- Trigger rate = resolved trades with a close-confirmed trigger / all resolved base trades.",
        "- Entry coverage among signals = resolved trades with a selected contract and sufficient ask size / resolved triggered trades.",
        "- Paired coverage = triggered, entered, resolved tail trades with valid exact-contract exit quotes and sufficient displayed bid size / all resolved base trades.",
        "- Incremental mean = hedged minus base mean on the same paired sample, net of modeled option costs. Negative means carry cost exceeded the recorded hedge offset in that sample.",
        "- Worst loss shows the median across phases of each phase's worst paired base and hedged outcome. Same worst-base trade improvement identifies the most negative base trade in the paired set and compares that exact trade after hedging.",
        "- Gross premium spend is entry ask × 100 × contracts for trades with an executable displayed ask size. It is cash outlay, not net insurance cost.",
        "- Unpriced entered positions are disclosed and excluded from realized paired P&L; they are never assigned zero profit.",
        "",
        "## 3. Direct comparison with unconditional insurance — DTE45 / Hold-20", "",
        "For each candidate, conditional rows show the triggered paired subset; unconditional rows use the previous source-pinned replay. Each has its own paired coverage, so the matched base mean is the appropriate within-row baseline—not an all-trades mean taken from another sample.",
        "",
        "| Rule | Tail | Qty | Trigger rate | Coverage median | Paired N range | Base mean | Hedge mean | Mean change | Worst paired loss base→hedged |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for trigger, tail, qty in candidates:
        rows = groups[("DTE45", "HOLD_20_OR_DTE_LE_7", trigger, tail, qty)]
        def cm(field):
            return median([num(r.get(field)) for r in rows])
        nlo, nhi = bounds([num(r.get("paired_n")) for r in rows])
        bw = median([num(r.get("paired_no_hedge_worst_trade_usd")) for r in rows])
        hw = median([num(r.get("paired_hedged_worst_trade_usd")) for r in rows])
        lines.append(
            f"| Trigger {trigger.replace('ENTRY_SPOT_DRAWDOWN_','')} | {TAIL[tail]['label']} | {qty} "
            f"| {cm('trigger_rate_pct_of_base_resolved'):.2f}% | {cm('paired_coverage_pct_of_base_resolved'):.2f}% "
            f"| {span(nlo,nhi)} | {money(cm('no_hedge_mean_paired_usd'))} | {money(cm('hedged_mean_paired_usd'))} "
            f"| {money(cm('incremental_mean_paired_usd'))} | {money(bw)}→{money(hw)} |"
        )
        ur = uncond.get(("DTE45", "HOLD_20_OR_DTE_LE_7", tail, qty), [])
        if ur:
            ulo, uhi = bounds([num(r.get("joint_resolved_paired_n")) for r in ur])
            ucov = median([num(r.get("paired_coverage_pct_of_base_resolved")) for r in ur])
            ub = median([num(r.get("paired_baseline_mean_net_usd")) for r in ur])
            uh = median([num(r.get("paired_hedged_mean_net_usd")) for r in ur])
            ui = median([num(r.get("paired_mean_incremental_hedge_usd")) for r in ur])
            ubw = median([num(r.get("paired_baseline_worst_trade_usd")) for r in ur])
            uhw = median([num(r.get("paired_hedged_worst_trade_usd")) for r in ur])
            lines.append(
                f"| Unconditional | {TAIL[tail]['label']} | {qty} | Every entry scheduled | {ucov:.2f}% "
                f"| {span(ulo,uhi)} | {money(ub)} | {money(uh)} | {money(ui)} | {money(ubw)}→{money(uhw)} |"
            )

    lines += [
        "",
        "## 4. Annual behavior — DTE45 / Hold-20", "",
        "Per-trade mean P&L by frozen base exit year. Phase medians are shown, not pooled as independent observations. Delta/quantity arms can have different paired N and quote coverage.",
        "",
        "| Exit year | Trigger | Tail | Qty | Trigger rate | Paired coverage | Paired N range | Base mean | Hedged mean | Mean change | Same worst-base trade improvement |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    agroups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in annual_rows:
        if row["arm"] == "DTE45" and row["policy"] == "HOLD_20_OR_DTE_LE_7":
            agroups[(int(row["exit_year"]), row["trigger_label"], row["tail_label"], int(row["tail_quantity"]))].append(row)
    for year in sorted({key[0] for key in agroups}):
        for trigger, tail, qty in candidates:
            rows = agroups.get((year, trigger, tail, qty), [])
            if not rows:
                continue
            def am(field):
                return median([num(r.get(field)) for r in rows])
            nlo, nhi = bounds([num(r.get("paired_n")) for r in rows])
            lines.append(
                f"| {year} | {trigger.replace('ENTRY_SPOT_DRAWDOWN_','')} | {TAIL[tail]['label']} | {qty} "
                f"| {am('trigger_rate_pct_of_base_resolved'):.2f}% | {am('paired_coverage_pct_of_base_resolved'):.2f}% "
                f"| {span(nlo,nhi)} | {money(am('no_hedge_mean_paired_usd'))} | {money(am('hedged_mean_paired_usd'))} "
                f"| {money(am('incremental_mean_paired_usd'))} | {money(am('worst_base_trade_improvement_usd'))} |"
            )
    lines += [
        "",
        "## 5. One vs three contracts on a common paired set", "",
        "The 3x-valid sample is the matched comparison set for both quantities. Because the same selected contract is used, a 3x-valid entry/exit also passes the 1x gates; this avoids comparing different samples.",
        "",
        "| Arm | Exit | Trigger | Tail | Common N range | 1x hedge mean | 3x hedge mean | 1x tail net mean | 3x tail net mean | Extra 3x tail drag per trade | Worst hedged trade 1x→3x |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for arm in ("DTE14", "DTE45"):
        for policy in ("HOLD_10_OR_DTE_LE_7", "HOLD_20_OR_DTE_LE_7"):
            for trigger, tail, qty in candidates:
                if qty != 3:
                    continue
                rows = groups[(arm, policy, trigger, tail, qty)]
                def qm(field):
                    return median([num(r.get(field)) for r in rows])
                nlo, nhi = bounds([num(r.get("common_paired_1x3_n")) for r in rows])
                lines.append(
                    f"| {arm} | {POLICY[policy]} | {trigger.replace('ENTRY_SPOT_DRAWDOWN_','')} | {TAIL[tail]['label']} "
                    f"| {span(nlo,nhi)} | {money(qm('common_1x_mean_net_usd'))} | {money(qm('common_3x_mean_net_usd'))} "
                    f"| {money(qm('common_1x_mean_tail_net_usd'))} | {money(qm('common_3x_mean_tail_net_usd'))} "
                    f"| {money(qm('common_3x_extra_drag_per_paired_usd'))} "
                    f"| {money(qm('common_1x_worst_hedged_usd'))}→{money(qm('common_3x_worst_hedged_usd'))} |"
                )

    lines += [
        "",
        "## 6. Tail-leg expiry stress after delayed hedge entry", "",
        "Hypothetical intrinsic payoff of the selected long PUT from the actual hedge-entry spot, including modeled round-trip costs. This is not a whole-book stress, historical path replay or probability forecast; it excludes the base SPY short PUT's updated value at trigger and the QQQ long PUT.",
        "",
        "| Arm | Exit | Trigger | Tail | Qty | SPY shock after hedge entry | Entered N range | Mean tail P&L range | Worst tail P&L range | Positive tail payoff rate median |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    stress_groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in stress_rows:
        key = (row["arm"], row["policy"], row["trigger_label"], row["tail_label"], int(row["tail_quantity"]),
               float(row["spot_shock_after_hedge_entry_pct"]))
        stress_groups[key].append(row)
    for key, rows in sorted(stress_groups.items()):
        arm, policy, trigger, tail, qty, shock = key
        nlo, nhi = bounds([num(r.get("entered_hedge_n")) for r in rows])
        meanlo, meanhi = bounds([num(r.get("mean_tail_expiry_net_pnl_usd")) for r in rows])
        worstlo, worsthi = bounds([num(r.get("worst_tail_expiry_net_pnl_usd")) for r in rows])
        positive = median([num(r.get("fraction_tail_leg_positive_pct")) for r in rows])
        lines.append(
            f"| {arm} | {POLICY[policy]} | {trigger.replace('ENTRY_SPOT_DRAWDOWN_','')} | {TAIL[tail]['label']} | {qty} "
            f"| {shock:g}% | {span(nlo,nhi)} | {money(meanlo)} to {money(meanhi)} "
            f"| {money(worstlo)} to {money(worsthi)} | {positive:.2f}% |"
        )

    lines += [
        "",
        "## 7. Decision framework — is this insurance worth paying for?", "",
        "Advance a trigger only if all criteria are acceptable together:",
        "",
        "1. **Loss-tail improvement:** better same-worst-base-trade outcome and paired worst loss, not only a theoretical -50% shock payoff.",
        "2. **Quote coverage:** enough entry and exit quote/size coverage; disclose unpriced entries and do not assume zero P&L.",
        "3. **Premium budget:** compare gross entry outlay and realized incremental P&L with downside reduction. Annual means here are per-trade amounts, not account income.",
        "4. **Quantity scaling:** compare 1x and 3x on the same common paired set. More contracts should be treated as higher-budget insurance unless results show otherwise.",
        "5. **Independent validation:** this historical period was used for research. A chosen rule requires a separate holdout or forward sample.",
        "6. **Whole-book risk:** before deployment, model QQQ+SPY NAV, concurrent trades, margin, assignment/exercise, forced liquidation and fill uncertainty. This tail-leg-only replay cannot certify portfolio MaxDD.",
        "",
        "### Interpretation cautions", "",
        "- The 3% trigger may enter earlier and more often; the 5% trigger may reduce spend but can enter later. Use the measured results rather than presuming either wins.",
        "- If 3x reduces severe loss but materially cuts average P&L, it is insurance, not a demonstrated return enhancer.",
        "- No hedge remains the mandatory control. Do not treat the same sample used for choosing a trigger as independent validation.",
        "",
        "## 8. Data lineage and limitations", "",
        "- Original base ledgers and unconditional replay results are read-only reference inputs.",
        "- Daily SPY close and option chains are pinned to anahatsingh-ui/options-dataset-hist commit 37f6c456fe1a4775c875673fb8ef907d5cd2fd66. Hash pinning proves byte identity against the Git mirror, not OPRA authenticity.",
        "- EOD quotes and displayed sizes are not verified fills; size gates are only eligibility checks.",
        "- Five shifted base phases overlap and are not independent samples.",
        "- The rule uses fixed entry-price drawdown, not rolling-high drawdown, VIX/VX structure, or option delta deterioration.",
        "- Triggered paired samples omit entered positions with insufficient exit quote/size; these are counted separately, so quote-availability selection bias remains.",
        "- The tail stress grid estimates the option leg only. It excludes the base SPY short PUT's updated market value at trigger, QQQ long PUT, margin, forced liquidation, assignment/exercise and financing.",
        "- No live broker orders were placed.",
        "",
        "## 9. Reproducible artifacts", "",
        "- [Triggered contract selection and dates](triggered_selection.csv)",
        "- [Full no-hedge vs triggered trade ledger](triggered_trade_level.csv)",
        "- [Phase/config trigger summary](triggered_summary.csv)",
        "- [Annual results](triggered_annual.csv)",
        "- [Tail-leg expiry stress grid](triggered_tail_stress.csv)",
        "- [Unconditional SPY tail decision report](../spy_far_tail_hedge_v1/SPY_FAR_TAIL_DECISION_REPORT.md)",
        "- [Research PR #147](https://github.com/JUN-ZS/brush-timber-mountain-brook/pull/147)", "",
    ]
    report = "\n".join(lines)
    if len(report) < 10000:
        raise ValueError("trigger report unexpectedly short")
    return report


if __name__ == "__main__":
    raise SystemExit(main() and 0)
