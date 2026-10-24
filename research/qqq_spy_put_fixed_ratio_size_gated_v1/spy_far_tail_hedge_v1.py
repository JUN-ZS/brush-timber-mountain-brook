#!/usr/bin/env python3
"""Replay SPY far-tail long-put overlays against frozen QQQ1:SPY3 trade ledgers."""
from __future__ import annotations
import argparse, csv, hashlib, json, math, statistics
from collections import defaultdict
from pathlib import Path
from typing import Any
import qqq_spy_put_fixed_phase_v1 as engine

ROOT = Path(__file__).resolve().parent
BASE_ANCHOR_COMMIT = "c0cc1de3f196a312c00582d9ee9600c689c388d9"
ARMS = {"DTE45": "expiry_guarded_dte45", "DTE14": "expiry_guarded_dte14"}
PHASES = range(5)
POLICIES = ("HOLD_10_OR_DTE_LE_7", "HOLD_20_OR_DTE_LE_7")
TAILS = (
    {"label": "TAIL_05_DELTA", "target_delta": 0.05, "delta_min": 0.01, "delta_max": 0.08},
    {"label": "TAIL_10_DELTA", "target_delta": 0.10, "delta_min": 0.05, "delta_max": 0.15},
)
TAIL_QUANTITIES = (1, 3)
SHOCKS = (0.0, -0.10, -0.20, -0.30, -0.40, -0.50, -1.0)
MULTIPLIER = 100


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def as_float(value: Any) -> float | None:
    try:
        n = float(value)
        return n if math.isfinite(n) else None
    except (TypeError, ValueError):
        return None


def as_int(value: Any, default: int = 0) -> int:
    n = as_float(value)
    return int(n) if n is not None else default


def as_text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def is_resolved(row: dict[str, Any]) -> bool:
    return as_text(row.get("status")).upper() == "RESOLVED" and as_float(row.get("net_pnl_usd")) is not None


def unit_side_cost(slippage_per_share: float, commission_per_contract_per_side: float) -> float:
    return slippage_per_share * MULTIPLIER + commission_per_contract_per_side


def select_far_tail(rows: list[dict[str, Any]], day: str, expiry: str, spot: float,
                    target_delta: float, delta_min: float, delta_max: float) -> dict[str, Any] | None:
    """Select same-expiry listed SPY put: strict OTM, valid positive bid and delta band."""
    candidates = []
    if spot <= 0:
        return None
    for row in rows:
        if not engine.standard_put_identity(row, "SPY"):
            continue
        if engine.as_day(row.get("date")) != day or engine.as_day(row.get("expiration")) != expiry:
            continue
        if not engine.valid_quote(row, require_positive_bid=True):
            continue
        strike, delta = as_float(row.get("strike")), as_float(row.get("delta"))
        if strike is None or delta is None or strike >= spot:
            continue
        ad = abs(delta)
        if not delta_min <= ad <= delta_max:
            continue
        ask_size = engine.displayed_size(row, "ask")
        if ask_size < 1:
            continue
        bid, ask = float(row["bid"]), float(row["ask"])
        oi = as_float(row.get("open_interest")) or 0.0
        candidates.append({
            "contract_id": engine.normalized_contract_id(row), "strike": strike, "abs_delta": ad,
            "entry_bid": bid, "entry_ask": ask, "bid_size": engine.displayed_size(row, "bid"),
            "ask_size": ask_size, "open_interest": oi,
            "relative_spread": (ask - bid) / max((ask + bid) / 2.0, 1e-9),
            "otm_pct_entry": (spot - strike) / spot * 100.0, "selection_expiry": expiry,
        })
    if not candidates:
        return None
    return min(candidates, key=lambda x: (
        abs(x["abs_delta"] - target_delta), -x["ask_size"], -x["open_interest"],
        x["relative_spread"], x["contract_id"],
    ))


def entry_size_ok(selection: dict[str, Any] | None, quantity: int) -> bool:
    return bool(selection) and quantity >= 1 and as_int(selection.get("ask_size")) >= quantity


def exit_size_ok(row: dict[str, Any] | None, quantity: int) -> bool:
    return isinstance(row, dict) and engine.valid_quote(row) and quantity >= 1 and engine.displayed_size(row, "bid") >= quantity


def tail_net_pnl(entry_ask: float, exit_bid: float, quantity: int, slippage_per_share: float = 0.05,
                 commission_per_contract_per_side: float = 0.65) -> float:
    unit = unit_side_cost(slippage_per_share, commission_per_contract_per_side)
    return quantity * MULTIPLIER * (exit_bid - entry_ask) - quantity * 2.0 * unit


def expiry_spy_sleeve_pnl(spot: float, short_strike: float, short_quantity: int, short_entry_bid: float,
                          tail_strike: float, tail_quantity: int, tail_entry_ask: float, shock: float,
                          slippage_per_share: float = 0.05,
                          commission_per_contract_per_side: float = 0.65) -> dict[str, float]:
    """Expiry intrinsic stress for SPY short-put sleeve only, with opening costs."""
    stressed_spot = max(0.0, spot * (1.0 + shock))
    unit = unit_side_cost(slippage_per_share, commission_per_contract_per_side)
    short_intrinsic = max(0.0, short_strike - stressed_spot)
    tail_intrinsic = max(0.0, tail_strike - stressed_spot)
    short_net = short_quantity * MULTIPLIER * (short_entry_bid - short_intrinsic) - short_quantity * unit
    tail_net = tail_quantity * MULTIPLIER * (tail_intrinsic - tail_entry_ask) - tail_quantity * unit
    return {"stressed_spy_spot": stressed_spot, "short_put_sleeve_net_usd": short_net,
            "tail_put_net_usd": tail_net, "hedged_spy_sleeve_net_usd": short_net + tail_net}


def load_base_ledgers(base_results_root: Path):
    cohorts, trades, input_hashes = {}, {}, {}
    for arm, dirname in ARMS.items():
        for phase in PHASES:
            path = base_results_root / dirname / "fixed_phase_sensitivity" / f"phase_{phase}" / "trade_episodes.csv"
            if not path.is_file():
                raise FileNotFoundError(f"required base replay ledger missing: {path}")
            input_hashes[f"{arm}/phase_{phase}/trade_episodes.csv"] = sha256_file(path)
            with path.open("r", encoding="utf-8", newline="") as handle:
                for raw in csv.DictReader(handle):
                    episode_id, policy = as_text(raw.get("episode_id")), as_text(raw.get("policy"))
                    if not episode_id or policy not in POLICIES:
                        raise ValueError(f"invalid ledger identity in {path}: {episode_id}/{policy}")
                    trade_key = f"{arm}|{phase}|{episode_id}|{policy}"
                    if trade_key in trades:
                        raise ValueError(f"duplicate base trade key: {trade_key}")
                    row = dict(raw)
                    row.update({"arm": arm, "phase": phase, "trade_key": trade_key})
                    trades[trade_key] = row
                    cohort_key = (arm, phase, episode_id)
                    if cohort_key not in cohorts:
                        required = ("entry_date", "expiry", "spy_contract_id", "spy_strike", "spy_spot_entry",
                                    "spy_entry_bid", "short_spy_qty", "base_slippage_per_share",
                                    "base_commission_per_contract_per_side")
                        missing = [f for f in required if raw.get(f) in (None, "")]
                        if missing:
                            raise ValueError(f"base cohort missing {missing}: {trade_key}")
                        cohorts[cohort_key] = {
                            "arm": arm, "phase": phase, "episode_id": episode_id, "entry_date": as_text(raw["entry_date"]),
                            "expiry": as_text(raw["expiry"]), "spy_contract_id": as_text(raw["spy_contract_id"]),
                            "spy_strike": float(raw["spy_strike"]), "spy_spot_entry": float(raw["spy_spot_entry"]),
                            "spy_entry_bid": float(raw["spy_entry_bid"]), "short_spy_qty": as_int(raw["short_spy_qty"]),
                            "base_slippage_per_share": float(raw["base_slippage_per_share"]),
                            "base_commission_per_contract_per_side": float(raw["base_commission_per_contract_per_side"]),
                            "trade_keys": [],
                        }
                    cohorts[cohort_key]["trade_keys"].append(trade_key)
    for key, cohort in cohorts.items():
        got = {as_text(trades[k].get("policy")) for k in cohort["trade_keys"]}
        if got != set(POLICIES):
            raise ValueError(f"base cohort missing exit policies: {key}: {sorted(got)}")
    return cohorts, trades, input_hashes


def requested_observation_date(row: dict[str, Any]) -> tuple[str, str]:
    return (as_text(row.get("exit_date")), "RESOLVED_EXIT") if is_resolved(row) else (
        as_text(row.get("last_observed_date")), "UNRESOLVED_MARK_ONLY")


def stream_and_select(cohorts, trades, spy_cache: Path):
    """One pinned source pass selects each entry tail then observes exact exit-date quotes."""
    years = {int(c["entry_date"][:4]) for c in cohorts.values()}
    for trade in trades.values():
        day, _ = requested_observation_date(trade)
        if day:
            years.add(int(day[:4]))
    years = list(range(min(years), max(years) + 1))
    paths, source_pins = [], []
    for year in years:
        path, pin = engine.download_verified("SPY", year, spy_cache)
        paths.append(path)
        source_pins.append(pin)
    entry_dates: dict[str, list[tuple[str, int, str]]] = defaultdict(list)
    for key, cohort in cohorts.items():
        entry_dates[cohort["entry_date"]].append(key)
    selected, observations = {}, {}
    exit_requests_by_date: dict[str, list[tuple[str, tuple[str, str, str, int]]]] = defaultdict(list)
    stats = {"chain_dates": 0, "put_rows": 0, "last_chain_date": None}
    start_day = min(c["entry_date"] for c in cohorts.values())
    end_day = max(max(as_text(t.get("exit_date")) or as_text(t.get("last_observed_date")) for t in trades.values()),
                  max(c["entry_date"] for c in cohorts.values()))
    for day, day_rows in engine.iter_symbol_days(paths, "SPY", start_day, end_day, stats):
        by_id = {engine.normalized_contract_id(r): r for r in day_rows if engine.normalized_contract_id(r)}
        for cohort_key in entry_dates.get(day, []):
            cohort = cohorts[cohort_key]
            for tail in TAILS:
                tail_key = (cohort_key, tail["label"])
                pick = select_far_tail(day_rows, day, cohort["expiry"], cohort["spy_spot_entry"],
                                       tail["target_delta"], tail["delta_min"], tail["delta_max"])
                selected[tail_key] = pick
                if pick is None:
                    continue
                for trade_key in cohort["trade_keys"]:
                    target_day, target_kind = requested_observation_date(trades[trade_key])
                    if not target_day:
                        continue
                    for qty in TAIL_QUANTITIES:
                        if entry_size_ok(pick, qty):
                            request_key = (trade_key, tail["label"], target_kind, qty)
                            exit_requests_by_date[target_day].append((pick["contract_id"], request_key))
        for contract_id, request_key in exit_requests_by_date.get(day, []):
            if request_key in observations:
                continue
            quote = by_id.get(contract_id)
            if not isinstance(quote, dict) or not engine.valid_quote(quote):
                observations[request_key] = {"tail_exit_quote_valid": False, "tail_exit_bid": None,
                    "tail_exit_bid_size": 0, "tail_exit_executable_size_gate": False, "tail_exit_date": day}
                continue
            bid, size = float(quote["bid"]), engine.displayed_size(quote, "bid")
            observations[request_key] = {"tail_exit_quote_valid": True, "tail_exit_bid": bid,
                "tail_exit_bid_size": size, "tail_exit_executable_size_gate": size >= request_key[3],
                "tail_exit_date": day}
    return selected, observations, source_pins, stats


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"refusing to emit empty output: {path}")
    fields, seen = [], set()
    for row in rows:
        for name in row:
            if name not in seen:
                seen.add(name)
                fields.append(name)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build_outputs(cohorts, trades, selected, observations, slippage: float, commission: float):
    entry_rows, trade_level, summary_rows = [], [], []
    stress_buckets: dict[tuple[str, int, str, int, float], list[dict[str, float]]] = defaultdict(list)
    unit = unit_side_cost(slippage, commission)
    for cohort_key, cohort in sorted(cohorts.items()):
        for tail in TAILS:
            pick = selected.get((cohort_key, tail["label"]))
            for qty in TAIL_QUANTITIES:
                gate = entry_size_ok(pick, qty)
                entry_rows.append({
                    "arm": cohort["arm"], "phase": cohort["phase"], "episode_id": cohort["episode_id"],
                    "entry_date": cohort["entry_date"], "expiry": cohort["expiry"],
                    "base_spy_short_contract_id": cohort["spy_contract_id"], "base_spy_short_strike": cohort["spy_strike"],
                    "base_spy_short_qty": cohort["short_spy_qty"], "tail_label": tail["label"],
                    "tail_target_abs_delta": tail["target_delta"], "tail_quantity": qty,
                    "tail_contract_id": pick["contract_id"] if pick else None, "tail_strike": pick["strike"] if pick else None,
                    "tail_abs_delta": pick["abs_delta"] if pick else None, "tail_otm_pct_entry": pick["otm_pct_entry"] if pick else None,
                    "tail_entry_bid": pick["entry_bid"] if pick else None, "tail_entry_ask": pick["entry_ask"] if pick else None,
                    "tail_entry_ask_size": pick["ask_size"] if pick else 0, "tail_entry_executable_size_gate": gate,
                    "tail_entry_cost_usd": qty * unit if gate else None,
                    "selection_status": "SELECTED" if pick else "NO_ELIGIBLE_TAIL_CONTRACT",
                })
                if gate and pick:
                    for shock in SHOCKS:
                        stress_buckets[(cohort["arm"], cohort["phase"], tail["label"], qty, shock)].append(
                            expiry_spy_sleeve_pnl(cohort["spy_spot_entry"], cohort["spy_strike"], cohort["short_spy_qty"],
                                cohort["spy_entry_bid"], pick["strike"], qty, pick["entry_ask"], shock, slippage, commission))
    for trade_key, base in sorted(trades.items()):
        cohort_key = (base["arm"], base["phase"], as_text(base["episode_id"]))
        cohort = cohorts[cohort_key]
        resolved = is_resolved(base)
        base_pnl = as_float(base.get("net_pnl_usd")) if resolved else None
        target_day, target_kind = requested_observation_date(base)
        for tail in TAILS:
            pick = selected.get((cohort_key, tail["label"]))
            for qty in TAIL_QUANTITIES:
                entry_ok = entry_size_ok(pick, qty)
                obs = observations.get((trade_key, tail["label"], target_kind, qty), {})
                quote_valid = bool(obs.get("tail_exit_quote_valid"))
                exit_gate = bool(obs.get("tail_exit_executable_size_gate"))
                exit_bid = as_float(obs.get("tail_exit_bid")) if quote_valid else None
                entry_ask = as_float(pick.get("entry_ask")) if pick else None
                tail_net = tail_mtm = None
                if entry_ok and entry_ask is not None and exit_bid is not None:
                    tail_mtm = tail_net_pnl(entry_ask, exit_bid, qty, slippage, commission)
                    if resolved and exit_gate:
                        tail_net = tail_mtm
                hedged = base_pnl + tail_net if base_pnl is not None and tail_net is not None else None
                trade_level.append({
                    "arm": base["arm"], "phase": base["phase"], "episode_id": base["episode_id"],
                    "policy": base["policy"], "base_status": base.get("status"), "entry_date": base.get("entry_date"),
                    "exit_date": base.get("exit_date"), "base_net_pnl_usd": base_pnl,
                    "base_worst_mark_usd": as_float(base.get("max_adverse_mark_pnl_usd")),
                    "base_spy_short_contract_id": cohort["spy_contract_id"], "base_spy_short_strike": cohort["spy_strike"],
                    "base_spy_short_qty": cohort["short_spy_qty"], "tail_label": tail["label"],
                    "tail_target_abs_delta": tail["target_delta"], "tail_quantity": qty,
                    "tail_contract_id": pick["contract_id"] if pick else None, "tail_strike": pick["strike"] if pick else None,
                    "tail_abs_delta": pick["abs_delta"] if pick else None, "tail_otm_pct_entry": pick["otm_pct_entry"] if pick else None,
                    "tail_entry_bid": pick["entry_bid"] if pick else None, "tail_entry_ask": entry_ask,
                    "tail_entry_ask_size": pick["ask_size"] if pick else 0, "tail_entry_executable": entry_ok,
                    "tail_exit_target_date": target_day or None, "tail_observation_kind": target_kind,
                    "tail_exit_quote_valid": quote_valid, "tail_exit_bid": exit_bid,
                    "tail_exit_bid_size": as_int(obs.get("tail_exit_bid_size")),
                    "tail_exit_executable_size_gate": exit_gate, "tail_exit_observed_date": obs.get("tail_exit_date"),
                    "tail_net_pnl_usd": tail_net, "tail_mtm_net_est_usd": tail_mtm,
                    "hedged_net_pnl_usd": hedged, "paired_realized_comparison": base_pnl is not None and tail_net is not None,
                    "unresolved_base_trade": not resolved,
                })
    grouped: dict[tuple[str, int, str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in trade_level:
        grouped[(row["arm"], row["phase"], row["policy"], row["tail_label"], row["tail_quantity"])].append(row)
    for (arm, phase, policy, label, qty), rows in sorted(grouped.items()):
        opened = len(rows)
        selected_n = sum(bool(r["tail_contract_id"]) for r in rows)
        entries_ok = [r for r in rows if r["tail_entry_executable"]]
        base_resolved = [r for r in rows if r["base_net_pnl_usd"] is not None]
        paired = [r for r in rows if r["paired_realized_comparison"]]
        bp = [float(r["base_net_pnl_usd"]) for r in paired]
        hp = [float(r["hedged_net_pnl_usd"]) for r in paired]
        tp = [float(r["tail_net_pnl_usd"]) for r in paired]
        losses = [r for r in paired if float(r["base_net_pnl_usd"]) < -0.005]
        summary_rows.append({
            "arm": arm, "phase": phase, "policy": policy, "tail_label": label, "tail_quantity": qty,
            "opened_base_trades": opened, "selected_tail_contract_n": selected_n, "tail_entry_executable_n": len(entries_ok),
            "entry_coverage_pct_of_opened": round(100 * len(entries_ok) / opened, 2) if opened else None,
            "base_resolved_n": len(base_resolved), "base_unresolved_n": opened - len(base_resolved),
            "base_resolved_with_tail_entry_n": sum(r["tail_entry_executable"] for r in base_resolved),
            "joint_resolved_paired_n": len(paired),
            "paired_coverage_pct_of_base_resolved": round(100 * len(paired) / len(base_resolved), 2) if base_resolved else None,
            "valid_exit_quote_n_in_entry_sample": sum(r["tail_entry_executable"] and r["tail_exit_quote_valid"] for r in rows),
            "exit_size_gate_pass_n_in_entry_sample": sum(r["tail_entry_executable"] and r["tail_exit_executable_size_gate"] for r in rows),
            "missing_exit_quote_n_in_entry_sample": sum(r["tail_entry_executable"] and not r["tail_exit_quote_valid"] for r in rows),
            "entry_size_gate_fail_n": sum(bool(r["tail_contract_id"]) and not r["tail_entry_executable"] for r in rows),
            "paired_baseline_mean_net_usd": round(statistics.mean(bp), 2) if bp else None,
            "paired_baseline_win_rate_pct": round(100 * sum(v > 0.005 for v in bp) / len(bp), 2) if bp else None,
            "paired_baseline_worst_trade_usd": round(min(bp), 2) if bp else None,
            "paired_hedged_mean_net_usd": round(statistics.mean(hp), 2) if hp else None,
            "paired_hedged_win_rate_pct": round(100 * sum(v > 0.005 for v in hp) / len(hp), 2) if hp else None,
            "paired_hedged_worst_trade_usd": round(min(hp), 2) if hp else None,
            "paired_mean_tail_net_pnl_usd": round(statistics.mean(tp), 2) if tp else None,
            "paired_mean_incremental_hedge_usd": round(statistics.mean([h-b for h,b in zip(hp,bp)]), 2) if paired else None,
            "paired_baseline_losing_trades_n": len(losses),
            "baseline_losses_improved_n": sum(float(r["hedged_net_pnl_usd"]) > float(r["base_net_pnl_usd"]) for r in losses),
            "baseline_losses_turned_positive_n": sum(float(r["hedged_net_pnl_usd"]) > 0.005 for r in losses),
        })
    stress_rows = []
    for (arm, phase, label, qty, shock), rows in sorted(stress_buckets.items()):
        bp = [r["short_put_sleeve_net_usd"] for r in rows]
        hp = [r["hedged_spy_sleeve_net_usd"] for r in rows]
        tp = [r["tail_put_net_usd"] for r in rows]
        stress_rows.append({
            "arm": arm, "phase": phase, "tail_label": label, "tail_quantity": qty,
            "spy_shock_pct": shock * 100, "eligible_entry_cohorts": len(rows),
            "mean_short_spy_sleeve_net_usd": round(statistics.mean(bp), 2),
            "mean_hedged_spy_sleeve_net_usd": round(statistics.mean(hp), 2),
            "mean_tail_increment_usd": round(statistics.mean(tp), 2),
            "worst_short_spy_sleeve_net_usd": round(min(bp), 2),
            "worst_hedged_spy_sleeve_net_usd": round(min(hp), 2),
            "fraction_hedge_improves_short_sleeve_pct": round(100 * sum(h > b for h,b in zip(hp,bp)) / len(rows), 2),
        })
    return entry_rows, trade_level, summary_rows, stress_rows


def make_report(summary_rows, stress_rows):
    lines = [
        "# SPY Far-Tail Long-PUT Protection Overlay — V1", "",
        "## Frozen baseline and overlay", "",
        "- Base ledgers are read-only: QQQ LONG PUT 1 : SPY SHORT PUT 3, no entry filter, five-session cadence, five overlapping anchor phases.",
        "- Overlay buys a listed SPY far-OTM PUT on the actual base entry date at the exact short-put expiry; strike must be below SPY entry spot.",
        "- TAIL_05_DELTA targets absolute Delta 0.05 within 0.01–0.08; TAIL_10_DELTA targets absolute Delta 0.10 within 0.05–0.15. Each is tested at 1 and 3 contracts.",
        "- Selection is nearest Delta to target, then larger displayed ask size, open interest, tighter relative spread and stable contract ID. Positive bid and valid quote required. Same contract is tested at 1x and 3x; 3x entry fails if displayed ask size is below three.",
        "- Long PUT enters at ask and exits at bid. Costs: USD 0.05 per option share per side plus USD 0.65 per contract per side.",
        "- Paired realized comparison uses only base-resolved trades with valid tail entry and exact tail-contract exit quote with sufficient bid size. EOD quotes are estimates, not verified fills. Base-unresolved trades stay unresolved; their hedge observations are MTM only.", "",
        "## Five-phase summary (ranges across phases; not pooled independent samples)", "",
        "The five fixed-anchor schedules overlap and are not independent observations. The table shows phase ranges; summary.csv contains every phase separately.", "",
        "| Arm | Exit policy | Tail | Qty | Entry coverage range | Paired N range | Mean baseline P&L range | Mean hedged P&L range | Incremental hedge range | Worst hedged trade range |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    combos = sorted({(r["arm"], r["policy"], r["tail_label"], r["tail_quantity"]) for r in summary_rows})
    def fmt_range(values, suffix=""):
        clean = [float(v) for v in values if v is not None and math.isfinite(float(v))]
        return "—" if not clean else f"{min(clean):,.2f} to {max(clean):,.2f}{suffix}"
    for arm, policy, label, qty in combos:
        rs = [r for r in summary_rows if (r["arm"],r["policy"],r["tail_label"],r["tail_quantity"]) == (arm,policy,label,qty)]
        lines.append(
            f"| {arm} | {policy} | {label} | {qty} | {fmt_range([r['entry_coverage_pct_of_opened'] for r in rs], '%')} | "
            f"{fmt_range([r['joint_resolved_paired_n'] for r in rs])} | "
            f"{fmt_range([r['paired_baseline_mean_net_usd'] for r in rs], ' USD')} | "
            f"{fmt_range([r['paired_hedged_mean_net_usd'] for r in rs], ' USD')} | "
            f"{fmt_range([r['paired_mean_incremental_hedge_usd'] for r in rs], ' USD')} | "
            f"{fmt_range([r['paired_hedged_worst_trade_usd'] for r in rs], ' USD')} |"
        )
    lines += ["", "## Expiry stress grid — SPY put sleeve only", "",
        "Intrinsic-payoff stress check using actual entry spot, short-put credit/strike and tail-put ask/strike; not a historical path replay or prediction. It excludes the QQQ long-put leg, time value at exit, assignment/exercise fees, financing, margin and forced liquidation. Opening costs are included.", "",
        "| Arm | Phase | Tail | Qty | SPY shock | N | Mean short sleeve | Mean hedged sleeve | Mean hedge increment | Worst short sleeve | Worst hedged sleeve |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for r in stress_rows:
        lines.append(
            f"| {r['arm']} | {r['phase']} | {r['tail_label']} | {r['tail_quantity']} | {r['spy_shock_pct']:.0f}% | {r['eligible_entry_cohorts']} | "
            f"USD {r['mean_short_spy_sleeve_net_usd']:,.2f} | USD {r['mean_hedged_spy_sleeve_net_usd']:,.2f} | USD {r['mean_tail_increment_usd']:,.2f} | "
            f"USD {r['worst_short_spy_sleeve_net_usd']:,.2f} | USD {r['worst_hedged_spy_sleeve_net_usd']:,.2f} |")
    lines += ["", "## Critical limitations", "",
        "- Far-tail insurance is not free; compare recurring premium and round-trip costs with left-tail loss reduction.",
        "- Coverage is among opened cohorts; original missed/entry-skipped opportunities remain documented in base replay reports.",
        "- Paired P&L is restricted to resolved base trades with valid tail entry and exit size. Paired samples may be selected by quote availability; read paired N and coverage next to P&L.",
        "- Displayed EOD size is a screening gate, not a guaranteed fill. A valid bid with insufficient size is MTM only, not realized hedge P&L.",
        "- Same-expiry SPY tail PUTs offset the SPY short-put sleeve below the tail strike only for matched quantities; one long tail does not cover all three short puts. They do not hedge every cross-underlying loss mode.",
        "- Source is a public EOD preservation mirror verified against pinned Git blob sizes/hashes; this proves byte identity, not OPRA authenticity. No broker orders are placed.", "",
        "## Output files", "", "trade_level.csv: policy-specific paired accounting and MTM values.",
        "entry_selection.csv: exact selected tail contracts and size gates.", "summary.csv: all phase/policy/Delta/quantity combinations.",
        "stress_grid.csv: per-phase SPY expiry shock grid.", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-results-root", type=Path, default=ROOT / "results")
    parser.add_argument("--spy-cache", type=Path, default=Path.home() / ".cache" / "spy-options-expiry-guard-v1")
    parser.add_argument("--out", type=Path, default=ROOT / "results" / "spy_far_tail_hedge_v1")
    parser.add_argument("--slippage-per-share", type=float, default=0.05)
    parser.add_argument("--commission-per-contract-per-side", type=float, default=0.65)
    args = parser.parse_args()
    if args.slippage_per_share < 0 or args.commission_per_contract_per_side < 0:
        raise ValueError("transaction costs must be non-negative")
    cohorts, trades, input_hashes = load_base_ledgers(args.base_results_root)
    selected, observations, source_pins, source_stats = stream_and_select(cohorts, trades, args.spy_cache)
    entry_rows, trade_rows, summary_rows, stress_rows = build_outputs(
        cohorts, trades, selected, observations, args.slippage_per_share, args.commission_per_contract_per_side)
    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(args.out / "entry_selection.csv", entry_rows)
    write_csv(args.out / "trade_level.csv", trade_rows)
    write_csv(args.out / "summary.csv", summary_rows)
    write_csv(args.out / "stress_grid.csv", stress_rows)
    (args.out / "report.md").write_text(make_report(summary_rows, stress_rows), encoding="utf-8")
    manifest = {
        "schema": "spy-far-tail-hedge-overlay.v1",
        "status": "COMPLETED" if cohorts and summary_rows and stress_rows else "FAILED_EMPTY_OUTPUT",
        "base_anchor_commit": BASE_ANCHOR_COMMIT, "current_git_sha": __import__("os").environ.get("GITHUB_SHA"),
        "source_repository": engine.SOURCE_REPO, "source_tree_commit": engine.SOURCE_COMMIT,
        "base_trade_ledger_count": len(trades), "unique_base_cohort_count": len(cohorts),
        "summary_rows": len(summary_rows), "entry_selection_rows": len(entry_rows),
        "trade_level_rows": len(trade_rows), "stress_grid_rows": len(stress_rows), "stream_stats": source_stats,
        "tail_configurations": list(TAILS), "tail_quantities": list(TAIL_QUANTITIES), "expiry_shocks": list(SHOCKS),
        "costs": {"slippage_per_option_share_per_side_usd": args.slippage_per_share,
                  "commission_per_contract_per_side_usd": args.commission_per_contract_per_side},
        "input_ledger_sha256": input_hashes, "verified_spy_source_pins": source_pins,
        "code_sha256": {"overlay": sha256_file(Path(__file__)), "base_engine": sha256_file(ROOT / "qqq_spy_put_fixed_phase_v1.py")},
        "unresolved_handling": "Base unresolved trades remain unresolved; quote at last observed date is MTM only, never realized P&L.",
        "paired_comparison_rule": "Only base-resolved trades with exact tail contract and sufficient entry ask-side and exit bid-side displayed sizes enter paired realized P&L.",
        "warnings": ["EOD quotes are not verified fills.", "The five anchor phases overlap and are not independent samples.",
                     "Stress grid is expiry intrinsic payoff only; excludes QQQ leg, margin, assignment fees and forced liquidation."],
    }
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False), encoding="utf-8")
    if manifest["status"] != "COMPLETED":
        raise RuntimeError("overlay did not complete all required output families")
    print(json.dumps({"status": manifest["status"], "base_trade_ledger_count": len(trades),
        "unique_base_cohort_count": len(cohorts), "summary_rows": len(summary_rows),
        "entry_selection_rows": len(entry_rows), "trade_level_rows": len(trade_rows),
        "stress_grid_rows": len(stress_rows), "output_dir": str(args.out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
