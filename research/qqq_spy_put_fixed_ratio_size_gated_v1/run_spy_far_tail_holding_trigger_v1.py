#!/usr/bin/env python3
"""Source-pinned holding-period SPY PUT hedge triggers with chronological holdout."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import qqq_spy_put_fixed_phase_v1 as base_engine
import spy_far_tail_hedge_v1 as hedge_engine
import run_spy_far_tail_conditional_v1 as prior_conditional

ROOT = Path(__file__).resolve().parent
POLICY = "HOLD_20_OR_DTE_LE_7"
RULES = (
    "SHORT_PUT_ABS_DELTA_GE_0.35",
    "SPY_ENTRY_DRAWDOWN_GE_5PCT",
    "PACKAGE_MTM_LOSS_GE_50PCT_SPY_SHORT_CREDIT",
    "ANY_OF_THREE_PREDECLARED",
)
RULE_LABELS = {
    "SHORT_PUT_ABS_DELTA_GE_0.35": "Short SPY PUT |Delta| >= 0.35",
    "SPY_ENTRY_DRAWDOWN_GE_5PCT": "SPY down >= 5% from entry",
    "PACKAGE_MTM_LOSS_GE_50PCT_SPY_SHORT_CREDIT": "Package MTM loss >= 50% of initial SPY short credit",
    "ANY_OF_THREE_PREDECLARED": "OR: any of the three rules",
}
DELTA_THRESHOLD = 0.35
SPY_DRAWDOWN_THRESHOLD_PCT = 5.0
PACKAGE_LOSS_CREDIT_MULTIPLE = 0.50
TRAIN_END_YEAR = 2022
HOLDOUT_START_YEAR = 2023
HOLDOUT_END_YEAR = 2025
EXPECTED_START_YEAR = 2018
EXPECTED_END_YEAR = 2025
MULTIPLIER = 100
OUT_DIR = ROOT / "results" / "spy_far_tail_holding_trigger_v2"


def fnum(value: Any) -> float | None:
    try:
        out = float(value)
        return out if math.isfinite(out) else None
    except (TypeError, ValueError):
        return None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return value


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"Refusing to write empty output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for field in row:
            if field not in seen:
                fields.append(field)
                seen.add(field)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def sample_period(entry_date: str) -> str:
    year = int(str(entry_date)[:4])
    if EXPECTED_START_YEAR <= year <= TRAIN_END_YEAR:
        return "TRAIN_2018_2022"
    if HOLDOUT_START_YEAR <= year <= HOLDOUT_END_YEAR:
        return "LOCKED_HOLDOUT_2023_2025"
    raise ValueError(f"Entry year outside the declared data window: {entry_date}")


def trigger_conditions(
    short_put_delta: float | None,
    entry_spy_spot: float | None,
    current_spy_spot: float | None,
    package_mtm_pnl_usd: float | None,
    initial_spy_short_credit_usd: float | None,
) -> dict[str, Any]:
    """Evaluate only observable current-state features; never inspect future rows."""
    delta_abs = abs(short_put_delta) if short_put_delta is not None else None
    drawdown_pct = None
    if (
        entry_spy_spot is not None and current_spy_spot is not None
        and entry_spy_spot > 0 and current_spy_spot > 0
    ):
        drawdown_pct = (entry_spy_spot - current_spy_spot) / entry_spy_spot * 100.0
    loss_limit = (
        -PACKAGE_LOSS_CREDIT_MULTIPLE * initial_spy_short_credit_usd
        if initial_spy_short_credit_usd is not None and initial_spy_short_credit_usd > 0
        else None
    )
    component_hits = {
        RULES[0]: delta_abs is not None and delta_abs >= DELTA_THRESHOLD,
        RULES[1]: drawdown_pct is not None and drawdown_pct >= SPY_DRAWDOWN_THRESHOLD_PCT,
        RULES[2]: (
            package_mtm_pnl_usd is not None and loss_limit is not None
            and package_mtm_pnl_usd <= loss_limit
        ),
    }
    hits = dict(component_hits)
    hits[RULES[3]] = any(component_hits.values())
    availability = {
        RULES[0]: delta_abs is not None,
        RULES[1]: drawdown_pct is not None,
        RULES[2]: package_mtm_pnl_usd is not None and loss_limit is not None,
        RULES[3]: any((
            delta_abs is not None,
            drawdown_pct is not None,
            package_mtm_pnl_usd is not None and loss_limit is not None,
        )),
    }
    return {
        "hits": hits,
        "availability": availability,
        "delta_abs": delta_abs,
        "drawdown_pct": drawdown_pct,
        "package_mtm_pnl_usd": package_mtm_pnl_usd,
        "package_loss_limit_usd": loss_limit,
        "trigger_reasons": [key for key, value in component_hits.items() if value],
    }


def first_trigger_date(observations: list[tuple[str, dict[str, Any]]], rule: str) -> str | None:
    """Deterministic chronological helper; later observations cannot alter an earlier signal."""
    for day, features in sorted(observations, key=lambda item: item[0]):
        evaluated = trigger_conditions(
            features.get("delta"), features.get("entry_spot"), features.get("spot"),
            features.get("mtm"), features.get("credit"),
        )
        if evaluated["hits"][rule]:
            return day
    return None


def outcome_for_hedge(
    triggered: bool,
    entry_executable: bool,
    base_realized_pnl_usd: float | None,
    exit_executable: bool,
    tail_realized_pnl_usd: float | None,
) -> tuple[float | None, str]:
    """Preserve unknown realized outcomes when an entered hedge lacks a valid exit."""
    if base_realized_pnl_usd is None:
        return None, "BASE_UNRESOLVED_MARK_ONLY"
    if not triggered:
        return base_realized_pnl_usd, "NO_TRIGGER_NO_HEDGE"
    if not entry_executable:
        return base_realized_pnl_usd, "TRIGGERED_BUT_TAIL_ENTRY_UNAVAILABLE"
    if exit_executable and tail_realized_pnl_usd is not None:
        return base_realized_pnl_usd + tail_realized_pnl_usd, "HEDGE_PAIRED_REALIZED"
    return None, "HEDGE_ENTERED_EXIT_UNAVAILABLE"


def package_mark_pnl_from_rows(trade: dict[str, Any], qrow: dict[str, Any], srow: dict[str, Any]) -> float | None:
    """Build an explicitly numeric close-mark ledger from CSV rows and current exact-contract quotes."""
    required_numbers = (
        "long_qqq_qty", "short_spy_qty", "qqq_entry_ask", "spy_entry_bid",
        "base_slippage_per_share", "base_commission_per_contract_per_side",
    )
    episode = dict(trade)
    for field in required_numbers:
        value = fnum(trade.get(field))
        if value is None:
            raise ValueError(f"Missing or invalid numeric field for package MTM: {field}")
        episode[field] = value
    episode["long_qqq_qty"] = int(episode["long_qqq_qty"])
    episode["short_spy_qty"] = int(episode["short_spy_qty"])
    if episode["long_qqq_qty"] < 1 or episode["short_spy_qty"] < 1:
        raise ValueError("Package MTM requires positive leg quantities")
    return base_engine.mark_pnl(episode, qrow, srow)


def next_session_entry_observation(
    candidate: dict[str, Any] | None,
    quote: dict[str, Any] | None,
    observed_day: str,
    expected_day: str | None,
    base_exit_day: str,
    current_spot: float | None,
) -> dict[str, Any]:
    """Validate an exact-contract quote observed on the predeclared next trading session."""
    out = {
        "tail_entry_date": expected_day,
        "tail_entry_quote_valid": False,
        "tail_entry_ask": None,
        "tail_entry_ask_size": 0,
        "tail_entry_abs_delta": None,
        "tail_entry_spot": current_spot,
        "tail_entry_status": None,
    }
    if not expected_day or expected_day >= base_exit_day:
        out.update({"tail_entry_date": None, "tail_entry_status": "NO_NEXT_SESSION_BEFORE_BASE_EXIT"})
        return out
    if observed_day != expected_day:
        out["tail_entry_status"] = "NEXT_SESSION_DATE_MISMATCH"
        return out
    if not candidate:
        out["tail_entry_status"] = "NO_ELIGIBLE_TRIGGER_DATE_CANDIDATE"
        return out
    exact_id = str(candidate.get("contract_id") or "")
    valid_identity = (
        isinstance(quote, dict)
        and base_engine.normalized_contract_id(quote) == exact_id
        and base_engine.standard_put_identity(quote, "SPY")
        and base_engine.as_day(quote.get("date")) == observed_day
        and base_engine.as_day(quote.get("expiration")) == base_engine.as_day(candidate.get("selection_expiry"))
    )
    if not valid_identity or not base_engine.valid_quote(quote):
        out["tail_entry_status"] = "NEXT_SESSION_EXACT_CONTRACT_QUOTE_MISSING_OR_INVALID"
        return out
    delta = fnum(quote.get("delta"))
    out.update({
        "tail_entry_quote_valid": True,
        "tail_entry_ask": float(quote["ask"]),
        "tail_entry_ask_size": base_engine.displayed_size(quote, "ask"),
        "tail_entry_abs_delta": abs(delta) if delta is not None else None,
        "tail_entry_status": "NEXT_SESSION_EXACT_CONTRACT_QUOTE_VALID",
    })
    return out


def next_or_none(iterator):
    try:
        return next(iterator)
    except StopIteration:
        return None


def tracked_symbol_days(
    paths: list[Path], symbol: str, start_day: str, end_day: str, stats: dict[str, Any]
):
    """Track exact option snapshot coverage while retaining the engine's pinned streaming reader."""
    stats.setdefault("first_chain_date", None)
    for day, rows in base_engine.iter_symbol_days(paths, symbol, start_day, end_day, stats):
        if stats["first_chain_date"] is None:
            stats["first_chain_date"] = day
        yield day, rows


def iter_merged_symbol_days(
    qqq_paths: list[Path],
    spy_paths: list[Path],
    start_day: str,
    end_day: str,
    stats: dict[str, Any],
    underlying_days: list[str],
):
    """Merge QQQ/SPY option snapshots with every observed SPY-close day.

    This deliberately emits an empty option-row list on an underlying-only day, so
    the SPY drawdown trigger still observes that close while Delta and package-MTM
    triggers remain unavailable without the required current-day option quotes.
    """
    q_iter = iter(tracked_symbol_days(qqq_paths, "QQQ", start_day, end_day, stats["qqq"]))
    s_iter = iter(tracked_symbol_days(spy_paths, "SPY", start_day, end_day, stats["spy"]))
    u_iter = iter(day for day in underlying_days if start_day <= day <= end_day)
    q_item, s_item, u_day = next_or_none(q_iter), next_or_none(s_iter), next_or_none(u_iter)
    while q_item is not None or s_item is not None or u_day is not None:
        candidates = [item[0] for item in (q_item, s_item) if item is not None]
        if u_day is not None:
            candidates.append(u_day)
        day = min(candidates)
        q_rows, s_rows = [], []
        if q_item is not None and q_item[0] == day:
            q_rows = q_item[1]
            q_item = next_or_none(q_iter)
        if s_item is not None and s_item[0] == day:
            s_rows = s_item[1]
            s_item = next_or_none(s_iter)
        if u_day == day:
            u_day = next_or_none(u_iter)
        yield day, q_rows, s_rows


def initialize_event(trade: dict[str, Any], rule: str) -> dict[str, Any]:
    return {
        "trade_key": trade["trade_key"], "arm": trade["arm"], "phase": trade["phase"],
        "episode_id": trade.get("episode_id"), "policy": trade.get("policy"),
        "entry_date": trade.get("entry_date"), "observation_end_date": trade.get("_end_date"),
        "entry_year": int(str(trade.get("entry_date"))[:4]),
        "sample_period": sample_period(str(trade.get("entry_date"))),
        "trigger_rule": rule, "trigger_rule_label": RULE_LABELS[rule],
        "triggered": False, "trigger_date": None, "trigger_reason": "NO_TRIGGER",
        "expected_hedge_entry_date": None, "hedge_entry_schedule_status": "NOT_TRIGGERED",
        "holding_observation_days": 0, "feature_observation_days": 0,
        "delta_observation_days": 0, "drawdown_observation_days": 0, "mtm_observation_days": 0,
        "feature_coverage_pct": None,
        "delta_abs_at_trigger": None, "spy_entry_drawdown_pct_at_trigger": None,
        "package_mtm_pnl_usd_at_trigger": None, "package_loss_limit_usd_at_trigger": None,
        "selected_tail_contracts_json": "{}",
    }


def load_replay_inputs(base_results_root: Path, overlay_results: Path):
    cohorts, trades, input_hashes = hedge_engine.load_base_ledgers(base_results_root)
    overlay_manifest_path = overlay_results / "manifest.json"
    overlay_manifest = read_json(overlay_manifest_path)
    if overlay_manifest.get("status") != "COMPLETED":
        raise ValueError("Pinned unconditional tail overlay manifest is not COMPLETED")
    prior_conditional.validate_baseline_hashes(input_hashes, overlay_manifest.get("input_ledger_sha256"))
    if not cohorts or not trades:
        raise ValueError("No source-pinned baseline trades found")
    chosen = []
    for raw in trades.values():
        if str(raw.get("policy")) != POLICY:
            continue
        trade = dict(raw)
        end_date, end_kind = hedge_engine.requested_observation_date(trade)
        trade["_end_date"] = end_date or ""
        trade["_end_kind"] = end_kind
        base_resolved = hedge_engine.is_resolved(trade)
        base_pnl = fnum(trade.get("net_pnl_usd")) if base_resolved else None
        trade["_base_resolved"] = base_pnl is not None
        trade["_base_realized_pnl"] = base_pnl
        trade["_sample_period"] = sample_period(str(trade["entry_date"]))
        trade["_entry_year"] = int(str(trade["entry_date"])[:4])
        if trade.get("entry_date"):
            chosen.append(trade)
    if not chosen:
        raise ValueError(f"No rows found for primary exit policy {POLICY}")
    return cohorts, chosen, input_hashes, overlay_manifest, sha256_file(overlay_manifest_path)


def build_events_and_observations(trades: list[dict[str, Any]], cache: Path):
    dated = [t for t in trades if t.get("entry_date") and t.get("_end_date")]
    if not dated:
        raise ValueError("No trades have both entry and observed end dates")
    start_day = min(str(t["entry_date"]) for t in dated)
    end_day = max(str(t["_end_date"]) for t in dated)
    if int(start_day[:4]) < EXPECTED_START_YEAR or int(end_day[:4]) > EXPECTED_END_YEAR:
        raise ValueError(f"Replay dates outside source-pinned window: {start_day} through {end_day}")

    years = range(int(start_day[:4]), int(end_day[:4]) + 1)
    source_pins: list[dict[str, Any]] = []
    symbol_paths: dict[str, list[Path]] = {"QQQ": [], "SPY": []}
    for symbol in ("QQQ", "SPY"):
        for year in years:
            path, pin = base_engine.download_verified(symbol, year, cache / symbol.lower())
            symbol_paths[symbol].append(path)
            source_pins.append(pin)
    spot_maps = {}
    for symbol in ("QQQ", "SPY"):
        path, pin = base_engine.download_verified(symbol, None, cache / f"{symbol.lower()}-underlying")
        source_pins.append(pin)
        spot_maps[symbol] = base_engine.load_spots(path, symbol)

    events: dict[tuple[str, str], dict[str, Any]] = {}
    picks: dict[tuple[str, str, str], dict[str, Any] | None] = {}
    entry_observations: dict[tuple[str, str, str], dict[str, Any]] = {}
    exit_observations: dict[tuple[str, str, str], dict[str, Any]] = {}
    for trade in trades:
        for rule in RULES:
            events[(trade["trade_key"], rule)] = initialize_event(trade, rule)

    entries_by_date: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for trade in dated:
        entries_by_date[str(trade["entry_date"])].append(trade)
    entry_dates = sorted(entries_by_date)
    entry_cursor = 0
    active: list[dict[str, Any]] = []
    exit_requests: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    pending_entries: dict[str, list[tuple[str, str, str, str, str]]] = defaultdict(list)
    stream_stats = {
        "qqq": {"chain_dates": 0, "put_rows": 0, "first_chain_date": None, "last_chain_date": None},
        "spy": {"chain_dates": 0, "put_rows": 0, "first_chain_date": None, "last_chain_date": None},
        "merged_dates": 0, "entry_day_missing_from_option_stream_n": 0,
        "underlying_only_observation_days": 0,
    }
    observed_entry_dates: set[str] = set()
    observed_option_dates: set[str] = set()
    underlying_observation_days = sorted(
        day for day in spot_maps["SPY"].keys() if start_day <= day <= end_day
    )
    next_session_by_day = {
        day: underlying_observation_days[i + 1]
        for i, day in enumerate(underlying_observation_days[:-1])
    }

    for day, qqq_rows, spy_rows in iter_merged_symbol_days(
        symbol_paths["QQQ"], symbol_paths["SPY"], start_day, end_day,
        stream_stats, underlying_observation_days
    ):
        stream_stats["merged_dates"] += 1
        if qqq_rows or spy_rows:
            observed_option_dates.add(day)
        else:
            stream_stats["underlying_only_observation_days"] += 1
        observed_entry_dates.update([day] if qqq_rows or spy_rows else [])
        q_by_id = base_engine.rows_by_id(qqq_rows)
        s_by_id = base_engine.rows_by_id(spy_rows)
        spot_spy = fnum(spot_maps["SPY"].get(day))

        # Trigger features are observed on day T; hedge entry is attempted only on
        # the next SPY underlying session using that session's exact-contract quote.
        # No same-day EOD fill assumption, fallback quote, forward-fill, or later retry.
        for trade_key, rule, tail_label, expected_entry_day, base_exit_day in pending_entries.pop(day, []):
            key = (trade_key, rule, tail_label)
            candidate = picks.get(key)
            quote = s_by_id.get(str(candidate.get("contract_id"))) if candidate else None
            entry_observation = next_session_entry_observation(
                candidate, quote, day, expected_entry_day, base_exit_day, spot_spy
            )
            entry_observations[key] = entry_observation
            if (
                entry_observation.get("tail_entry_quote_valid")
                and int(entry_observation.get("tail_entry_ask_size") or 0) >= 1
                and base_exit_day > day
            ):
                exit_requests[base_exit_day].append((trade_key, rule, tail_label))

        # Exact-date exit observations only: never carry a prior quote forward.
        for trade_key, rule, tail_label in exit_requests.pop(day, []):
            pick = picks.get((trade_key, rule, tail_label))
            if not pick:
                continue
            quote = s_by_id.get(str(pick["contract_id"]))
            valid = (
                isinstance(quote, dict)
                and base_engine.standard_put_identity(quote, "SPY")
                and base_engine.as_day(quote.get("date")) == day
                and base_engine.valid_quote(quote)
            )
            exit_observations[(trade_key, rule, tail_label)] = {
                "tail_exit_date": day, "tail_exit_quote_valid": bool(valid),
                "tail_exit_bid": float(quote["bid"]) if valid else None,
                "tail_exit_bid_size": base_engine.displayed_size(quote, "bid") if valid else 0,
            }

        # A missing option snapshot on the literal entry date is not replaced. The
        # position may be evaluated on the first later date with an actual snapshot.
        while entry_cursor < len(entry_dates) and entry_dates[entry_cursor] < day:
            active.extend(entries_by_date[entry_dates[entry_cursor]])
            entry_cursor += 1
        active = [t for t in active if str(t.get("_end_date") or "") > day]

        spot_spy = fnum(spot_maps["SPY"].get(day))
        for trade in active:
            if not (str(trade["entry_date"]) < day < str(trade["_end_date"])):
                continue
            trade_key = trade["trade_key"]
            qrow = q_by_id.get(str(trade.get("qqq_contract_id") or ""))
            srow = s_by_id.get(str(trade.get("spy_contract_id") or ""))
            q_quote_valid = (
                isinstance(qrow, dict) and base_engine.standard_put_identity(qrow, "QQQ")
                and base_engine.as_day(qrow.get("date")) == day and base_engine.valid_quote(qrow)
            )
            s_quote_valid = (
                isinstance(srow, dict) and base_engine.standard_put_identity(srow, "SPY")
                and base_engine.as_day(srow.get("date")) == day and base_engine.valid_quote(srow)
            )
            delta = fnum(srow.get("delta")) if s_quote_valid else None
            if delta is not None:
                delta = abs(delta)

            q_close_executable = (
                q_quote_valid
                and base_engine.displayed_size(qrow, "bid") >= int(fnum(trade.get("long_qqq_qty")) or 0)
            )
            s_close_executable = (
                s_quote_valid
                and base_engine.displayed_size(srow, "ask") >= int(fnum(trade.get("short_spy_qty")) or 0)
            )
            mark_pnl = None
            if q_close_executable and s_close_executable:
                mark_pnl = package_mark_pnl_from_rows(trade, qrow, srow)

            entry_spot = fnum(trade.get("spy_spot_entry"))
            short_qty = fnum(trade.get("short_spy_qty"))
            short_entry_bid = fnum(trade.get("spy_entry_bid"))
            short_credit = (
                short_qty * short_entry_bid * MULTIPLIER
                if short_qty is not None and short_entry_bid is not None
                and short_qty > 0 and short_entry_bid > 0 else None
            )
            features = trigger_conditions(delta, entry_spot, spot_spy, mark_pnl, short_credit)

            for rule in RULES:
                event = events[(trade_key, rule)]
                event["holding_observation_days"] += 1
                if delta is not None:
                    event["delta_observation_days"] += 1
                if features["drawdown_pct"] is not None:
                    event["drawdown_observation_days"] += 1
                if mark_pnl is not None:
                    event["mtm_observation_days"] += 1
                if features["availability"][rule]:
                    event["feature_observation_days"] += 1

                if event["triggered"] or not features["hits"][rule]:
                    continue
                event["triggered"] = True
                event["trigger_date"] = day
                reasons = features["trigger_reasons"]
                event["trigger_reason"] = "|".join(reasons) if reasons else rule
                event["delta_abs_at_trigger"] = features["delta_abs"]
                event["spy_entry_drawdown_pct_at_trigger"] = (
                    round(features["drawdown_pct"], 6) if features["drawdown_pct"] is not None else None
                )
                event["package_mtm_pnl_usd_at_trigger"] = (
                    round(mark_pnl, 2) if mark_pnl is not None else None
                )
                event["package_loss_limit_usd_at_trigger"] = (
                    round(features["package_loss_limit_usd"], 2)
                    if features["package_loss_limit_usd"] is not None else None
                )

                selected_ids = {}
                scheduled_entry_day = next_session_by_day.get(day)
                can_enter_before_exit = bool(
                    scheduled_entry_day and scheduled_entry_day < str(trade["_end_date"])
                )
                event["expected_hedge_entry_date"] = scheduled_entry_day if can_enter_before_exit else None
                event["hedge_entry_schedule_status"] = (
                    "SCHEDULED_NEXT_SESSION_ATTEMPT"
                    if can_enter_before_exit else "NO_NEXT_SESSION_BEFORE_BASE_EXIT"
                )
                for tail in hedge_engine.TAILS:
                    label = str(tail["label"])
                    key = (trade_key, rule, label)
                    pick = None
                    if spot_spy is not None:
                        pick = hedge_engine.select_far_tail(
                            spy_rows, day, str(trade.get("expiry")), spot_spy,
                            float(tail["target_delta"]), float(tail["delta_min"]), float(tail["delta_max"])
                        )
                    if pick is not None:
                        pick = dict(pick)
                        pick["selection_date"] = day
                    picks[key] = pick
                    selected_ids[label] = ({
                        "contract_id": pick.get("contract_id"),
                        "strike": pick.get("strike"),
                        "abs_delta_at_selection": pick.get("abs_delta"),
                        "selection_date": day,
                        "selection_ask_diagnostic_only": pick.get("entry_ask"),
                        "selection_ask_size_diagnostic_only": pick.get("ask_size"),
                    } if pick else None)
                    if can_enter_before_exit:
                        pending_entries[scheduled_entry_day].append(
                            (trade_key, rule, label, scheduled_entry_day, str(trade["_end_date"]))
                        )
                    else:
                        entry_observations[key] = next_session_entry_observation(
                            pick, None, day, None, str(trade["_end_date"]), spot_spy
                        )
                event["selected_tail_contracts_json"] = json.dumps(selected_ids, sort_keys=True)

        # Entry-day quotes cannot trigger a position that was just opened at that day's close.
        while entry_cursor < len(entry_dates) and entry_dates[entry_cursor] == day:
            active.extend(entries_by_date[entry_dates[entry_cursor]])
            entry_cursor += 1

    for trade in dated:
        if str(trade["entry_date"]) not in observed_entry_dates:
            stream_stats["entry_day_missing_from_option_stream_n"] += 1

    for event in events.values():
        n = int(event["holding_observation_days"])
        available = int(event["feature_observation_days"])
        event["feature_coverage_pct"] = round(100.0 * available / n, 4) if n else None
        if not event["triggered"]:
            event["trigger_reason"] = "NO_TRIGGER_WITHIN_OBSERVED_HOLD"
    return events, picks, entry_observations, exit_observations, source_pins, stream_stats, spot_maps


def build_trade_rows(
    trades: list[dict[str, Any]],
    events: dict[tuple[str, str], dict[str, Any]],
    picks: dict[tuple[str, str, str], dict[str, Any] | None],
    entry_observations: dict[tuple[str, str, str], dict[str, Any]],
    exit_observations: dict[tuple[str, str, str], dict[str, Any]],
    slippage_per_share: float,
    commission_per_contract: float,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for trade in trades:
        base_pnl = trade.get("_base_realized_pnl")
        base_resolved = base_pnl is not None
        for rule in RULES:
            event = events[(trade["trade_key"], rule)]
            for tail in hedge_engine.TAILS:
                label = str(tail["label"])
                key = (trade["trade_key"], rule, label)
                pick = picks.get(key)
                entry_obs = entry_observations.get(key, {})
                entry_ask = fnum(entry_obs.get("tail_entry_ask"))
                entry_ask_size = int(fnum(entry_obs.get("tail_entry_ask_size")) or 0)
                entry_quote_valid = bool(entry_obs.get("tail_entry_quote_valid"))
                for qty in hedge_engine.TAIL_QUANTITIES:
                    entry_ok = bool(event["triggered"] and entry_quote_valid and entry_ask is not None
                                     and entry_ask_size >= int(qty))
                    exit_obs = exit_observations.get(key, {})
                    exit_bid = fnum(exit_obs.get("tail_exit_bid"))
                    exit_quote_valid = bool(exit_obs.get("tail_exit_quote_valid"))
                    exit_ok = bool(
                        entry_ok and exit_quote_valid and exit_bid is not None
                        and int(fnum(exit_obs.get("tail_exit_bid_size")) or 0) >= int(qty)
                    )
                    tail_pnl = None
                    if entry_ok and exit_ok and base_resolved and entry_ask is not None:
                        tail_pnl = hedge_engine.tail_net_pnl(
                            entry_ask, exit_bid, int(qty), slippage_per_share, commission_per_contract
                        )
                    conditional_pnl, action = outcome_for_hedge(
                        bool(event["triggered"]), entry_ok, base_pnl, exit_ok, tail_pnl
                    )
                    entry_debit = None
                    if entry_ok and entry_ask is not None:
                        entry_debit = int(qty) * (
                            MULTIPLIER * entry_ask + MULTIPLIER * slippage_per_share + commission_per_contract
                        )
                    output.append({
                        "trade_key": trade["trade_key"], "arm": trade["arm"], "phase": trade["phase"],
                        "episode_id": trade.get("episode_id"), "policy": trade.get("policy"),
                        "entry_date": trade.get("entry_date"), "entry_year": trade.get("_entry_year"),
                        "sample_period": trade.get("_sample_period"), "exit_date": trade.get("exit_date"),
                        "base_status": trade.get("status"), "base_resolved": base_resolved,
                        "base_realized_net_pnl_usd": round(base_pnl, 2) if base_pnl is not None else None,
                        "base_max_adverse_mark_pnl_usd": fnum(trade.get("max_adverse_mark_pnl_usd")),
                        "trigger_rule": rule, "trigger_rule_label": RULE_LABELS[rule],
                        "triggered": bool(event["triggered"]), "trigger_date": event.get("trigger_date"),
                        "trigger_reason": event.get("trigger_reason"),
                        "trigger_data_coverage_pct": event.get("feature_coverage_pct"),
                        "delta_abs_at_trigger": event.get("delta_abs_at_trigger"),
                        "spy_entry_drawdown_pct_at_trigger": event.get("spy_entry_drawdown_pct_at_trigger"),
                        "package_mtm_pnl_usd_at_trigger": event.get("package_mtm_pnl_usd_at_trigger"),
                        "tail_label": label, "tail_target_abs_delta": tail.get("target_delta"),
                        "tail_quantity": int(qty),
                        "tail_contract_id": pick.get("contract_id") if pick else None,
                        "tail_strike": fnum(pick.get("strike")) if pick else None,
                        "tail_selection_date": pick.get("selection_date") if pick else None,
                        "tail_abs_delta_at_selection": fnum(pick.get("abs_delta")) if pick else None,
                        "tail_entry_date": entry_obs.get("tail_entry_date"),
                        "tail_entry_status": entry_obs.get("tail_entry_status"),
                        "tail_entry_quote_valid": entry_quote_valid,
                        "tail_abs_delta_at_entry": fnum(entry_obs.get("tail_entry_abs_delta")),
                        "tail_entry_ask": entry_ask,
                        "tail_entry_ask_size": entry_ask_size,
                        "tail_entry_executable": entry_ok,
                        "tail_exit_date": exit_obs.get("tail_exit_date"),
                        "tail_exit_quote_valid": exit_quote_valid,
                        "tail_exit_bid": exit_bid,
                        "tail_exit_bid_size": int(fnum(exit_obs.get("tail_exit_bid_size")) or 0),
                        "tail_exit_executable": exit_ok,
                        "tail_realized_net_pnl_usd": round(tail_pnl, 2) if tail_pnl is not None else None,
                        "conditional_action": action,
                        "conditional_realized_net_pnl_usd": (
                            round(conditional_pnl, 2) if conditional_pnl is not None else None
                        ),
                        "conditional_outcome_known": conditional_pnl is not None,
                        "modeled_tail_entry_debit_usd": round(entry_debit, 2) if entry_debit is not None else None,
                    })
    return output


def avg(values: Iterable[float | int | None]) -> float | None:
    clean = [float(x) for x in values if x is not None and math.isfinite(float(x))]
    return round(statistics.mean(clean), 2) if clean else None


def quantile(values: Iterable[float | int | None], probability: float) -> float | None:
    """Deterministic linearly interpolated quantile; ignores missing/non-finite values."""
    clean = sorted(float(x) for x in values if x is not None and math.isfinite(float(x)))
    if not clean:
        return None
    p = min(1.0, max(0.0, float(probability)))
    rank = (len(clean) - 1) * p
    lower = int(math.floor(rank))
    upper = int(math.ceil(rank))
    value = clean[lower] + (clean[upper] - clean[lower]) * (rank - lower)
    return round(value, 2)


def bottom_tail_mean(values: Iterable[float | int | None], fraction: float = 0.05) -> float | None:
    """Mean of the worst ceil(fraction * N) realized outcomes; not a portfolio drawdown."""
    clean = sorted(float(x) for x in values if x is not None and math.isfinite(float(x)))
    if not clean:
        return None
    k = max(1, int(math.ceil(len(clean) * min(1.0, max(0.0, fraction)))))
    return round(statistics.mean(clean[:k]), 2)


def med(values: Iterable[float | int | None]) -> float | None:
    clean = [float(x) for x in values if x is not None and math.isfinite(float(x))]
    return round(statistics.median(clean), 2) if clean else None


def bounds(values: Iterable[float | int | None]) -> tuple[float | None, float | None]:
    clean = [float(x) for x in values if x is not None and math.isfinite(float(x))]
    return (round(min(clean), 2), round(max(clean), 2)) if clean else (None, None)


def summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    base_resolved = [r for r in rows if r.get("base_realized_net_pnl_usd") is not None]
    matched = [r for r in base_resolved if r.get("conditional_realized_net_pnl_usd") is not None]
    base_all = [float(r["base_realized_net_pnl_usd"]) for r in base_resolved]
    base_matched = [float(r["base_realized_net_pnl_usd"]) for r in matched]
    conditional = [float(r["conditional_realized_net_pnl_usd"]) for r in matched]
    increments = [c - b for b, c in zip(base_matched, conditional)]
    entered_matched = [
        (r, b, c) for r, b, c in zip(matched, base_matched, conditional)
        if bool(r.get("tail_entry_executable"))
    ]
    entered_increments = [c - b for _, b, c in entered_matched]
    base_loss_flags = [b < -0.005 for b in base_matched]
    conditional_loss_flags = [c < -0.005 for c in conditional]
    loss_rate_change_pp = (
        100.0 * statistics.mean(conditional_loss_flags) - 100.0 * statistics.mean(base_loss_flags)
        if matched else None
    )
    base_bottom5 = bottom_tail_mean(base_matched, 0.05)
    conditional_bottom5 = bottom_tail_mean(conditional, 0.05)
    losing_pairs = [(b, c) for b, c in zip(base_matched, conditional) if b < -0.005]
    triggered = [r for r in rows if bool(r.get("triggered"))]
    entry_rows = [r for r in rows if bool(r.get("tail_entry_executable"))]
    resolved_entry = [r for r in base_resolved if bool(r.get("tail_entry_executable"))]
    exit_pairs = [
        r for r in resolved_entry
        if bool(r.get("tail_exit_executable")) and r.get("tail_realized_net_pnl_usd") is not None
    ]
    missing_exit = [
        r for r in resolved_entry
        if not (bool(r.get("tail_exit_executable")) and r.get("tail_realized_net_pnl_usd") is not None)
    ]
    opened_n = len(rows)
    resolved_n = len(base_resolved)
    data_coverages = [fnum(r.get("trigger_data_coverage_pct")) for r in rows]
    worst_base_row = min(matched, key=lambda r: float(r["base_realized_net_pnl_usd"])) if matched else None
    worst_cond_row = min(matched, key=lambda r: float(r["conditional_realized_net_pnl_usd"])) if matched else None
    worst_base_all_row = min(base_resolved, key=lambda r: float(r["base_realized_net_pnl_usd"])) if base_resolved else None
    worst_base_all_conditional = (
        fnum(worst_base_all_row.get("conditional_realized_net_pnl_usd"))
        if worst_base_all_row else None
    )
    worst_base_all_paired_change = (
        worst_base_all_conditional - float(worst_base_all_row["base_realized_net_pnl_usd"])
        if worst_base_all_row and worst_base_all_conditional is not None else None
    )
    worst_base = float(worst_base_row["base_realized_net_pnl_usd"]) if worst_base_row else None
    worst_cond = float(worst_cond_row["conditional_realized_net_pnl_usd"]) if worst_cond_row else None
    worst_base_paired_change = (
        float(worst_base_row["conditional_realized_net_pnl_usd"])
        - float(worst_base_row["base_realized_net_pnl_usd"])
        if worst_base_row else None
    )
    worst_cond_paired_change = (
        float(worst_cond_row["conditional_realized_net_pnl_usd"])
        - float(worst_cond_row["base_realized_net_pnl_usd"])
        if worst_cond_row else None
    )
    return {
        "opened_n": opened_n,
        "base_resolved_n": resolved_n,
        "base_unresolved_n": opened_n - resolved_n,
        "triggered_n": len(triggered),
        "trigger_rate_pct": round(100.0 * len(triggered) / opened_n, 2) if opened_n else None,
        "trigger_data_coverage_pct_mean": avg(data_coverages),
        "hedge_entry_executable_n": len(entry_rows),
        "hedge_entry_coverage_pct_of_triggered": (
            round(100.0 * len(entry_rows) / len(triggered), 2) if triggered else None
        ),
        "resolved_triggered_entry_n": len(resolved_entry),
        "hedge_exit_paired_realized_n": len(exit_pairs),
        "hedge_exit_coverage_pct_of_resolved_entry": (
            round(100.0 * len(exit_pairs) / len(resolved_entry), 2) if resolved_entry else None
        ),
        "hedge_missing_exit_outcome_n": len(missing_exit),
        "conditional_outcome_known_n": len(matched),
        "conditional_outcome_coverage_pct_of_base_resolved": (
            round(100.0 * len(matched) / resolved_n, 2) if resolved_n else None
        ),
        "no_hedge_mean_all_resolved_usd": avg(base_all),
        "no_hedge_mean_matched_usd": avg(base_matched),
        "conditional_mean_matched_usd": avg(conditional),
        "conditional_mean_increment_vs_no_hedge_usd": avg(increments),
        "conditional_total_increment_vs_no_hedge_usd": round(sum(increments), 2) if increments else None,
        "conditional_mean_increment_on_executed_entries_usd": avg(entered_increments),
        "executed_entry_paired_outcome_n": len(entered_matched),
        "baseline_loss_rate_matched_pct": (
            round(100.0 * statistics.mean(base_loss_flags), 2) if matched else None
        ),
        "conditional_loss_rate_matched_pct": (
            round(100.0 * statistics.mean(conditional_loss_flags), 2) if matched else None
        ),
        "conditional_loss_rate_change_pp": (
            round(loss_rate_change_pp, 2) if loss_rate_change_pp is not None else None
        ),
        "baseline_p05_matched_usd": quantile(base_matched, 0.05),
        "conditional_p05_matched_usd": quantile(conditional, 0.05),
        "baseline_bottom5_mean_matched_usd": base_bottom5,
        "conditional_bottom5_mean_matched_usd": conditional_bottom5,
        "bottom5_mean_change_usd": (
            round(conditional_bottom5 - base_bottom5, 2)
            if base_bottom5 is not None and conditional_bottom5 is not None else None
        ),
        "paired_delta_p05_usd": quantile(increments, 0.05),
        "paired_delta_bottom5_mean_usd": bottom_tail_mean(increments, 0.05),
        "modeled_tail_entry_debit_per_successful_entry_usd": (
            round(sum(float(r["modeled_tail_entry_debit_usd"]) for r in entry_rows
                      if r.get("modeled_tail_entry_debit_usd") is not None) / len(entry_rows), 2)
            if entry_rows else None
        ),
        "modeled_tail_entry_debit_per_opened_position_usd": (
            round(sum(float(r["modeled_tail_entry_debit_usd"]) for r in entry_rows
                      if r.get("modeled_tail_entry_debit_usd") is not None) / opened_n, 2)
            if opened_n else None
        ),
        "baseline_worst_resolved_trade_key": worst_base_all_row.get("trade_key") if worst_base_all_row else None,
        "baseline_worst_resolved_trade_entry_date": worst_base_all_row.get("entry_date") if worst_base_all_row else None,
        "baseline_worst_resolved_trade_pnl_usd": (
            round(float(worst_base_all_row["base_realized_net_pnl_usd"]), 2) if worst_base_all_row else None
        ),
        "baseline_worst_resolved_trade_conditional_pnl_usd": (
            round(worst_base_all_conditional, 2) if worst_base_all_conditional is not None else None
        ),
        "baseline_worst_resolved_trade_paired_change_usd": (
            round(worst_base_all_paired_change, 2) if worst_base_all_paired_change is not None else None
        ),
        "baseline_worst_resolved_trade_outcome_known_pct": (
            100.0 if worst_base_all_conditional is not None else 0.0
        ) if worst_base_all_row else None,
        "no_hedge_win_rate_matched_pct": (
            round(100.0 * sum(x > 0.005 for x in base_matched) / len(base_matched), 2) if base_matched else None
        ),
        "conditional_win_rate_matched_pct": (
            round(100.0 * sum(x > 0.005 for x in conditional) / len(conditional), 2) if conditional else None
        ),
        "no_hedge_worst_matched_usd": round(worst_base, 2) if worst_base is not None else None,
        "conditional_worst_matched_usd": round(worst_cond, 2) if worst_cond is not None else None,
        # Paired change on the exact baseline worst-loss trade within this matched sample.
        "worst_trade_improvement_usd": (
            round(worst_base_paired_change, 2) if worst_base_paired_change is not None else None
        ),
        "baseline_worst_trade_paired_change_usd": (
            round(worst_base_paired_change, 2) if worst_base_paired_change is not None else None
        ),
        # This compares minima that may belong to different trades; it is not a paired improvement.
        "difference_between_worst_observed_pnls_usd": (
            round(worst_cond - worst_base, 2)
            if worst_base is not None and worst_cond is not None else None
        ),
        "baseline_worst_trade_key": worst_base_row.get("trade_key") if worst_base_row else None,
        "baseline_worst_trade_entry_date": worst_base_row.get("entry_date") if worst_base_row else None,
        "baseline_worst_trade_pnl_usd": round(worst_base, 2) if worst_base is not None else None,
        "baseline_worst_trade_conditional_pnl_usd": (
            round(float(worst_base_row["conditional_realized_net_pnl_usd"]), 2) if worst_base_row else None
        ),
        "conditional_worst_trade_key": worst_cond_row.get("trade_key") if worst_cond_row else None,
        "conditional_worst_trade_entry_date": worst_cond_row.get("entry_date") if worst_cond_row else None,
        "conditional_worst_trade_pnl_usd": round(worst_cond, 2) if worst_cond is not None else None,
        "conditional_worst_trade_paired_change_usd": (
            round(worst_cond_paired_change, 2) if worst_cond_paired_change is not None else None
        ),
        "losing_base_trades_improved_n": sum(c > b + 0.005 for b, c in losing_pairs),
        "losing_base_trades_turned_positive_n": sum(
            b < -0.005 and c > 0.005 for b, c in zip(base_matched, conditional)
        ),
        "modeled_tail_entry_debit_total_usd": round(sum(
            float(r["modeled_tail_entry_debit_usd"]) for r in entry_rows
            if r.get("modeled_tail_entry_debit_usd") is not None
        ), 2),
    }


def group_rows(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row.get(k) for k in keys)].append(row)
    output = []
    for key, items in sorted(grouped.items(), key=lambda kv: tuple(str(v) for v in kv[0])):
        out = dict(zip(keys, key))
        out.update(summarize_rows(items))
        output.append(out)
    return output


SUMMARY_KEYS = ("sample_period", "arm", "phase", "trigger_rule", "tail_label", "tail_quantity")


def build_robustness(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keys = ("sample_period", "arm", "trigger_rule", "tail_label", "tail_quantity")
    numeric_fields = (
        "trigger_rate_pct", "trigger_data_coverage_pct_mean", "hedge_entry_coverage_pct_of_triggered",
        "hedge_exit_coverage_pct_of_resolved_entry", "conditional_outcome_coverage_pct_of_base_resolved",
        "no_hedge_mean_matched_usd", "conditional_mean_matched_usd",
        "conditional_mean_increment_vs_no_hedge_usd", "worst_trade_improvement_usd",
        "baseline_worst_trade_paired_change_usd", "difference_between_worst_observed_pnls_usd",
        "baseline_worst_resolved_trade_paired_change_usd", "baseline_worst_resolved_trade_outcome_known_pct",
        "conditional_mean_increment_on_executed_entries_usd", "conditional_loss_rate_change_pp",
        "baseline_p05_matched_usd", "conditional_p05_matched_usd",
        "baseline_bottom5_mean_matched_usd", "conditional_bottom5_mean_matched_usd",
        "bottom5_mean_change_usd", "paired_delta_p05_usd", "paired_delta_bottom5_mean_usd",
        "modeled_tail_entry_debit_total_usd", "modeled_tail_entry_debit_per_successful_entry_usd",
        "modeled_tail_entry_debit_per_opened_position_usd",
    )
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row.get(k) for k in keys)].append(row)
    output = []
    for key, phases in sorted(grouped.items(), key=lambda kv: tuple(str(v) for v in kv[0])):
        out = dict(zip(keys, key))
        out["phase_count"] = len(phases)
        for field in numeric_fields:
            vals = [fnum(p.get(field)) for p in phases]
            out[field + "_phase_median"] = med(vals)
            lo, hi = bounds(vals)
            out[field + "_phase_min"] = lo
            out[field + "_phase_max"] = hi
        out["opened_n_phase_min"] = min(int(p["opened_n"]) for p in phases)
        out["opened_n_phase_max"] = max(int(p["opened_n"]) for p in phases)
        out["conditional_outcome_known_n_phase_min"] = min(int(p["conditional_outcome_known_n"]) for p in phases)
        out["conditional_outcome_known_n_phase_max"] = max(int(p["conditional_outcome_known_n"]) for p in phases)
        output.append(out)
    return output


def build_annual_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return group_rows(rows, ("entry_year", "arm", "trigger_rule", "tail_label", "tail_quantity"))


def fmt_money(value: Any) -> str:
    number = fnum(value)
    if number is None:
        return "—"
    return ("−$" if number < 0 else "$") + f"{abs(number):,.2f}"


def fmt_pct(value: Any) -> str:
    number = fnum(value)
    return "—" if number is None else f"{number:.2f}%"


def fmt_count(value: Any) -> str:
    number = fnum(value)
    if number is None:
        return "—"
    return f"{number:,.0f}" if abs(number - round(number)) < 1e-9 else f"{number:,.1f}"


def fmt_pp(value: Any) -> str:
    number = fnum(value)
    return "—" if number is None else f"{number:.2f} pp"


def build_report(manifest: dict[str, Any], robustness: list[dict[str, Any]]) -> str:
    lines = [
        "# SPY Far-Tail In-Holding Risk Trigger — Research V2", "",
        "> Source-pinned historical replay with next-session entry attempts; daily quotes remain execution proxies, not verified fills. No broker connection or live orders.", "",
        "## 1. Decision question and frozen baseline", "",
        f"- Primary baseline: QQQ LONG PUT 1 : SPY SHORT PUT 3, {POLICY}; existing DTE14/DTE45 arms and five fixed phases retained.",
        "- No hedge is the control. Each hedge arm adds 1 or 3 same-expiry SPY far-OTM PUT contracts only after its first holding-period trigger; the exact selected contract is held to the original base exit date.",
        "- Original positions, entries, exit dates, cadence, and base trade P&L are read-only; the overlay does not delay or alter the base exit.",
        "- Day T uses observed data to evaluate the trigger and select a candidate. Entry is attempted only on the next SPY underlying trading session using that session's exact-contract Ask; same-day EOD fills, fallback quotes and retries are prohibited. Exit uses the original base exit date's exact-contract Bid. Costs are $0.05 per option-share per side plus $0.65 per contract per side; displayed size is not proof of a fill.",
        "",
        "## 2. Pre-declared trigger rules", "",
        "| Rule | Frozen condition | Required current observations |",
        "|---|---|---|",
        "| Short-put Delta | Exact selected SPY short PUT absolute Delta >= 0.35 | Current exact-contract option row, valid bid/ask and Delta |",
        "| SPY drawdown | SPY close >= 5% below actual entry SPY spot | Current-day SPY underlying close; no price forward-fill |",
        "| Package MTM loss | Full-package executable mark-to-close P&L <= -50% of initial gross SPY short-put credit | Same-day QQQ long PUT bid and SPY short PUT ask, valid contracts and sufficient displayed sizes |",
        "| OR composite | First date any of the three rules fires | At least one rule feature available that day |",
        "",
        "All rules fire at most once per position, on the first observed qualifying date strictly after entry and strictly before the frozen base exit date. The composite records which component(s) fired. Thresholds were fixed before this run and are not selected by comparing results.",
        "No missing price, Delta, or quote is forward-filled. The package-MTM rule is unavailable when either leg lacks an executable current mark.",
        "",
        "## 3. Chronological validation design", "",
        "- Descriptive / development segment by entry date: 2018-01-01 through 2022-12-31.",
        "- Locked chronological holdout by entry date: 2023-01-01 through 2025-12-31.",
        "- The holdout outcomes must not be used to revise thresholds. Because this repository has analyzed the same broad years for other strategy questions, this is a locked holdout for this trigger family, not a globally virgin data set. Truly untouched forward validation requires later dated option-chain data; the pinned chain ends at the date recorded below.",
        "- Five phase schedules overlap. Cross-phase medians/ranges are robustness summaries, not independent samples or confidence intervals.",
        "",
        "## 4. Historical holdout results — mean paired net P&L delta and worst trade", "",
        "The table below reports medians across five overlapping phases. Mean Δ uses exactly the same rows where conditional realized outcomes are known. 'Worst matched-baseline pair Δ' is the paired change on the worst baseline trade within that matched sample. 'Global worst-baseline pair Δ' uses the worst trade across all base-resolved rows, and is blank when that exact trade's conditional outcome is unknown; coverage shows whether the latter could be paired. A failed entry means no hedge was bought and the base result remains; an entered hedge with missing/undersized exit data makes the conditional realized outcome missing, not zero.",
        "",
        "| Arm | Rule | Tail target | Qty | Trigger rate | Outcome coverage | Mean Δ / position | Worst matched-baseline pair Δ | Difference between minima (unpaired) | Global worst-baseline pair Δ | Global worst outcome coverage | Losses improved / flipped positive | Total entry debit, phase median |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    holdout = [r for r in robustness if r["sample_period"] == "LOCKED_HOLDOUT_2023_2025"]
    for row in sorted(holdout, key=lambda r: (
        str(r["arm"]), str(r["trigger_rule"]), str(r["tail_label"]), int(r["tail_quantity"])
    )):
        lines.append(
            f"| {row['arm']} | {row['trigger_rule']} | {row['tail_label']} | {row['tail_quantity']} "
            f"| {fmt_pct(row.get('trigger_rate_pct_phase_median'))} "
            f"| {fmt_pct(row.get('conditional_outcome_coverage_pct_of_base_resolved_phase_median'))} "
            f"| {fmt_money(row.get('conditional_mean_increment_vs_no_hedge_usd_phase_median'))} "
            f"| {fmt_money(row.get('baseline_worst_trade_paired_change_usd_phase_median'))} "
            f"| {fmt_money(row.get('difference_between_worst_observed_pnls_usd_phase_median'))} "
            f"| {fmt_money(row.get('baseline_worst_resolved_trade_paired_change_usd_phase_median'))} "
            f"| {fmt_pct(row.get('baseline_worst_resolved_trade_outcome_known_pct_phase_median'))} "
            f"| {fmt_count(row.get('losing_base_trades_improved_n_phase_median'))} / {fmt_count(row.get('losing_base_trades_turned_positive_n_phase_median'))} "
            f"| {fmt_money(row.get('modeled_tail_entry_debit_total_usd_phase_median'))} |"
        )
    lines += [
        "",
        "- The exact original worst-trade paired change is computed on the same trade row. The separate difference between minimum outcomes may compare different trades and must not be interpreted as paired improvement.", "",
        "Do not select a winner solely from the holdout values. These are predeclared comparisons; a later untouched forward sample is required before a strategy-selection claim.", "",
        "## 5. Additional tail-risk and per-entry cost checks", "",
        "The lower-tail statistics are computed across realized position outcomes within each phase and matched set, not as account equity drawdown or portfolio CVaR. `bottom-5% mean change` compares the worst 5% of each strategy's outcome distribution; those rows can differ. The paired delta on executed entries only includes positions where a hedge was actually entered and both base/conditional realized outcomes are known. Per-entry debit is modeled opening debit, not net cost after exit proceeds.", "",
        "| Arm | Rule | Tail | Qty | Paired Δ / executed entry | Base → hedged bottom-5% mean | Bottom-5% change | Loss-rate change (pp) | Modeled debit / entry |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
        *[
            f"| {row['arm']} | {row['trigger_rule']} | {row['tail_label']} | {row['tail_quantity']} "
            f"| {fmt_money(row.get('conditional_mean_increment_on_executed_entries_usd_phase_median'))} "
            f"| {fmt_money(row.get('baseline_bottom5_mean_matched_usd_phase_median'))} → "
            f"{fmt_money(row.get('conditional_bottom5_mean_matched_usd_phase_median'))} "
            f"| {fmt_money(row.get('bottom5_mean_change_usd_phase_median'))} "
            f"| {fmt_pp(row.get('conditional_loss_rate_change_pp_phase_median'))} "
            f"| {fmt_money(row.get('modeled_tail_entry_debit_per_successful_entry_usd_phase_median'))} |"
            for row in sorted(
                [r for r in holdout if r.get("trigger_rule") == "ANY_OF_THREE_PREDECLARED"],
                key=lambda row: (str(row["arm"]), str(row["tail_label"]), int(row["tail_quantity"])),
            )
        ],
        "",
        "A robust insurance choice should not be declared from one minimum alone. Review the paired change of the baseline worst trade, the lower-tail distribution, the loss-rate change, entry cost and coverage together. None of these per-trade metrics implies a portfolio-level MaxDD or margin result.", "",
        "## 6. Annual outcomes by entry year", "",
        "Full annual-by-entry-year results are in holding_annual_by_entry_year.csv. Entry-year grouping keeps the chronology split fixed to the date when the rule had to act, rather than assigning an earlier entry to a later holdout because it exited later.",
        "",
        "## 7. Completeness and limitations", "",
        f"- Replay status: **{manifest['status']}**; selected baseline trades: {manifest['selected_baseline_trade_rows']}; trigger rows: {manifest['trigger_event_rows']}; trade/configuration rows: {manifest['holding_trade_level_rows']}.",
        f"- Source chain window: {manifest['chain_first_date']} to {manifest['chain_last_date']}; option-chain source: {manifest['option_chain_source']} at pin {manifest['option_chain_source_commit']}.",
        f"- Source files downloaded and hash/byte verified: {manifest['verified_source_file_count']}; baseline ledger hashes matched the original overlay manifest: {manifest['baseline_input_hashes_match_overlay_manifest']}.",
        "- The next-session daily Ask is still an execution-timing proxy rather than a timestamped verified fill. Displayed size is not guaranteed liquidity; costs are modeled, not broker statements.",
        "- Unresolved base positions remain mark-only; their outcomes are not counted as realized P&L.",
        "- Results are not account-level NAV, portfolio MaxDD, broker margin, assignment/early exercise, forced-liquidation, or cross-position capital simulations.",
        "- No threshold tuning, live trading, main-branch merge, or broker order is performed by this research.",
        "",
        "## 8. Reproducible outputs", "",
        "- holding_trigger_events.csv: first trigger date and feature availability per position/rule.",
        "- holding_trade_level.csv: each baseline position × rule × tail target × quantity, paired outcomes and missing-exit handling.",
        "- holding_summary_by_period_phase.csv: train/holdout/full results per phase.",
        "- holding_robustness_by_period.csv: medians and ranges across overlapping phases.",
        "- holding_annual_by_entry_year.csv: outcomes grouped by entry cohort year.",
        "- holding_manifest.json: pinned baseline hashes, source file pins, rule thresholds, output counts and warnings.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-results-root", type=Path, default=ROOT / "results")
    parser.add_argument("--overlay-results", type=Path, default=ROOT / "results" / "spy_far_tail_hedge_v1")
    parser.add_argument("--cache", type=Path, default=Path.home() / ".cache" / "spy-options-holding-trigger-v1")
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    args = parser.parse_args()

    cohorts, trades, input_hashes, overlay_manifest, overlay_manifest_sha = load_replay_inputs(
        args.base_results_root, args.overlay_results
    )
    events, picks, entry_observations, exits, pins, stream_stats, spot_maps = build_events_and_observations(trades, args.cache)
    slippage = float(overlay_manifest["costs"]["slippage_per_option_share_per_side_usd"])
    commission = float(overlay_manifest["costs"]["commission_per_contract_per_side_usd"])
    trade_rows = build_trade_rows(trades, events, picks, entry_observations, exits, slippage, commission)
    event_rows = [dict(events[key]) for key in sorted(events)]
    period_phase = group_rows(trade_rows, SUMMARY_KEYS)
    robustness = build_robustness(period_phase)
    annual = build_annual_rows(trade_rows)

    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(args.out / "holding_trigger_events.csv", event_rows)
    write_csv(args.out / "holding_trade_level.csv", trade_rows)
    write_csv(args.out / "holding_summary_by_period_phase.csv", period_phase)
    write_csv(args.out / "holding_robustness_by_period.csv", robustness)
    write_csv(args.out / "holding_annual_by_entry_year.csv", annual)

    underlying_dates = [
        day for symbol in ("QQQ", "SPY") for day in spot_maps[symbol].keys()
        if EXPECTED_START_YEAR <= int(day[:4]) <= EXPECTED_END_YEAR
    ]
    qqq_first = stream_stats["qqq"].get("first_chain_date")
    spy_first = stream_stats["spy"].get("first_chain_date")
    qqq_last = stream_stats["qqq"].get("last_chain_date")
    spy_last = stream_stats["spy"].get("last_chain_date")
    common_chain_starts = [d for d in (qqq_first, spy_first) if d]
    common_chain_ends = [d for d in (qqq_last, spy_last) if d]
    baseline_hash_match = input_hashes == overlay_manifest.get("input_ledger_sha256")
    manifest = {
        "schema": "spy-far-tail-in-holding-risk-trigger.v2",
        "status": "COMPLETED" if events and trade_rows and period_phase and robustness and annual else "FAILED_EMPTY_OUTPUT",
        "baseline_policy": POLICY,
        "baseline_anchor_commit": overlay_manifest.get("base_anchor_commit"),
        "conditional_overlay_source_commit": overlay_manifest.get("current_git_sha"),
        "option_chain_source": base_engine.SOURCE_REPO,
        "option_chain_source_commit": base_engine.SOURCE_COMMIT,
        "chain_first_date": max(common_chain_starts) if len(common_chain_starts) == 2 else None,
        "chain_last_date": min(common_chain_ends) if len(common_chain_ends) == 2 else None,
        "option_chain_coverage_by_symbol": {
            "QQQ": {"first": qqq_first, "last": qqq_last, "snapshot_dates": stream_stats["qqq"]["chain_dates"]},
            "SPY": {"first": spy_first, "last": spy_last, "snapshot_dates": stream_stats["spy"]["chain_dates"]},
        },
        "underlying_price_window": {
            "first": min(underlying_dates) if underlying_dates else None,
            "last": max(underlying_dates) if underlying_dates else None,
        },
        "selected_baseline_trade_rows": len(trades),
        "unique_base_position_cohorts": len({(t["arm"], t["phase"], t.get("episode_id")) for t in trades}),
        "trigger_event_rows": len(event_rows),
        "holding_trade_level_rows": len(trade_rows),
        "summary_by_period_phase_rows": len(period_phase),
        "robustness_by_period_rows": len(robustness),
        "annual_by_entry_year_rows": len(annual),
        "baseline_input_hashes_match_overlay_manifest": bool(baseline_hash_match),
        "baseline_input_sha256": input_hashes,
        "overlay_manifest_sha256": overlay_manifest_sha,
        "verified_source_file_count": len(pins),
        "verified_source_pins": pins,
        "stream_stats": stream_stats,
        "primary_holdout": {
            "split_key": "entry_date",
            "training": "2018-01-01 through 2022-12-31",
            "locked_holdout": "2023-01-01 through 2025-12-31",
            "globally_virgin": False,
            "reason": "The repository previously analyzed overlapping historical years for other strategies; post-2025 source-pinned option chains are required for a globally virgin forward holdout."
        },
        "trigger_rules": {
            "delta": {"rule": RULES[0], "abs_delta_gte": DELTA_THRESHOLD, "source": "current exact selected SPY short PUT row"},
            "spy_drawdown": {"rule": RULES[1], "entry_to_current_close_drop_pct_gte": SPY_DRAWDOWN_THRESHOLD_PCT},
            "package_mtm_loss": {"rule": RULES[2], "loss_multiple_of_initial_gross_spy_short_credit": PACKAGE_LOSS_CREDIT_MULTIPLE},
            "composite": {"rule": RULES[3], "combine": "OR", "fire": "first observed day any component fires"},
        },
        "tail_targets": [
            {"label": tail["label"], "target_abs_delta": tail["target_delta"], "delta_min": tail["delta_min"], "delta_max": tail["delta_max"]}
            for tail in hedge_engine.TAILS
        ],
        "quantities": list(hedge_engine.TAIL_QUANTITIES),
        "costs": overlay_manifest.get("costs"),
        "price_and_time_rules": {
            "trigger_window": "strictly after base entry_date and strictly before the original base exit_date or unresolved last-observed date",
            "signal_and_candidate_selection": "trigger features and candidate contract are selected from day-T observations only",
            "entry_time": "only the next SPY underlying trading session after trigger day, exact selected contract quote; no same-day fill assumption and no retry if quote is missing",
            "exit_quote": "exact same tail contract on original base exit date only; no forward-fill",
            "missing_quote": "no trigger, no candidate, or failed next-session entry keeps base outcome; entered hedge without valid original-exit quote leaves conditional realized outcome missing",
            "worst_trade_metric": "worst_trade_improvement_usd is paired P&L change on the exact baseline worst-loss trade; difference_between_worst_observed_pnls_usd compares minima that may belong to different trades",
        },
        "analysis_script_sha256": sha256_file(Path(__file__)),
        "warnings": [
            "EOD quotes and displayed sizes are not verified fills.",
            "Five phase schedules overlap and are not independent samples.",
            "The 2023-2025 holdout is chronological for this trigger family but not globally virgin within this repository.",
            "The source data ends in 2025; post-2025 untouched forward validation is not possible from the pinned source.",
            "No account NAV, broker margin, assignment/early exercise, financing, or forced liquidation is modeled.",
            "Unresolved base trades are not assigned zero and are excluded from realized-P&L comparisons.",
        ],
    }
    if not baseline_hash_match:
        raise ValueError("Baseline input SHA-256 no longer matches the original overlay manifest")
    if manifest["status"] != "COMPLETED":
        raise RuntimeError("Holding-period trigger experiment produced incomplete outputs")
    (args.out / "holding_manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False), encoding="utf-8")
    report = build_report(manifest, robustness)
    (args.out / "SPY_FAR_TAIL_HOLDING_TRIGGER_REPORT.md").write_text(report, encoding="utf-8")
    required_report_sections = (
        "## 1. Decision question and frozen baseline",
        "## 2. Pre-declared trigger rules",
        "## 3. Chronological validation design",
        "## 4. Historical holdout results",
        "## 6. Completeness and limitations",
        "## 7. Reproducible outputs",
    )
    missing_sections = [section for section in required_report_sections if section not in report]
    if len(report) < 6000 or missing_sections:
        raise RuntimeError(
            f"Holding-period report failed completeness check: bytes={len(report.encode('utf-8'))}; "
            f"missing_sections={missing_sections}"
        )
    print(json.dumps({
        "status": manifest["status"],
        "selected_baseline_trade_rows": len(trades),
        "trigger_event_rows": len(event_rows),
        "holding_trade_level_rows": len(trade_rows),
        "summary_by_period_phase_rows": len(period_phase),
        "robustness_by_period_rows": len(robustness),
        "annual_by_entry_year_rows": len(annual),
        "verified_source_file_count": len(pins),
        "report_bytes": len(report.encode("utf-8")),
        "output_dir": str(args.out),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
