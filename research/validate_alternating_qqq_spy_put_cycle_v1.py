#!/usr/bin/env python3
"""Acceptance validator for exact-DTE20 alternating QQQ/SPY PUT replay."""
import argparse, csv, json
from datetime import date
from pathlib import Path

ARM = "alternate_dte20_every10"
OFFSET = 0

def rows(path):
    with Path(path).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def require(ok, message):
    if not ok:
        raise SystemExit("VALIDATION_FAIL: " + message)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    p.add_argument("--initial-nav", type=float, default=100000.0)
    a = p.parse_args()
    out = Path(a.out)
    m = json.loads((out / "run_manifest.json").read_text(encoding="utf-8"))
    require(m.get("study_id") == "ALTERNATING_SPY_QQQ_PUT_DTE20_EVERY10_V1", "study id")
    c = m["contract_setup"]
    require(c.get("dte_band") == [14, 28] and c.get("dte_target") == 20, "DTE20 target/window mismatch")
    require(c.get("long_delta_rule", "").startswith("UNCONSTRAINED"), "LONG PUT Delta must not be restricted")
    cadence = m["cadence"]
    require(cadence.get("new_signal_every_common_sessions") == 10, "not 10-session cadence")
    cfg = cadence["arms"][ARM]
    require(cadence.get("signal_anchor_common_session_offset") == OFFSET, "wrong anchor offset")
    require(cfg.get("schedule_offset") == OFFSET, "arm schedule offset")
    require(cfg.get("max_hold_sessions") == 20 and cfg.get("exit_remaining_dte") == 7, "exit rules")
    daily = rows(out / (ARM + "_daily_nav.csv"))
    entries = rows(out / (ARM + "_entries.csv"))
    trades = rows(out / (ARM + "_trades.csv"))
    skips = rows(out / (ARM + "_skips.csv"))
    summary = rows(out / "portfolio_arm_summary.csv")
    require(len(summary) == 1 and summary[0]["arm"] == ARM, "summary arm scope")
    require(len(daily) == m["common_sessions"] and len(daily) > 0, "daily NAV row count")
    require(abs(float(daily[0]["nav_usd"]) - a.initial_nav) < .01, "starting NAV")
    by_date = {r["date"]: i for i, r in enumerate(daily)}
    entry_map = {r["episode_id"]: r for r in entries}
    trade_map = {r["episode_id"]: r for r in trades}
    require(len(entry_map) == len(entries) and len(trade_map) == len(trades), "duplicate episode id")
    require(set(entry_map) == set(trade_map), "entries/trades ledger mismatch")
    attempts = {}
    for r in entries:
        i = int(r["signal_index"])
        require(i >= OFFSET and (i - OFFSET) % 10 == 0 and r["schedule_signal_date"] == daily[i]["date"], "entry cadence/index")
        require(int(r["entry_index"]) == i + 1, "entry not next common session")
        actual_dte = (date.fromisoformat(r["expiry"]) - date.fromisoformat(r["entry_date"])).days
        require(14 <= actual_dte <= 28, "entry DTE outside execution window")
        require(abs(actual_dte - 20) <= 8, "entry DTE too far from DTE20 target")
        target_ask = 6 * float(r["short_signal_bid"])
        require(abs(float(r["long_target_ask_signal"]) - target_ask) < .0001, "long target Ask not 6x short Bid")
        expected_error = abs(float(r["long_signal_ask"]) - target_ask)
        require(abs(float(r["long_premium_error_signal"]) - expected_error) < .0001, "long premium match error mismatch")
        require(r["signal_date"] == r["entry_date"], "option quote date does not match entry")
        expected_dir = "A" if ((i - OFFSET) // 10) % 2 == 0 else "B"
        require(r["direction"] == expected_dir, "A/B entry alternation")
        require(i not in attempts, "duplicate schedule slot")
        attempts[i] = r["direction"]
        opening = round(100 * (6 * float(r["short_entry_bid"]) - float(r["long_entry_ask"])), 2)
        require(round(float(r["net_opening_cashflow_usd"]), 2) == opening, "1:6 opening cashflow")
        require(round(float(r["long_premium_paid_usd"]), 2) == round(100 * float(r["long_entry_ask"]), 2), "long premium")
        require(round(float(r["short_premium_received_usd"]), 2) == round(600 * float(r["short_entry_bid"]), 2), "short premium")
    for r in skips:
        i = by_date.get(r.get("signal_date"))
        require(i is not None and i >= OFFSET and (i - OFFSET) % 10 == 0, "skip off cadence")
        expected_dir = "A" if ((i - OFFSET) // 10) % 2 == 0 else "B"
        require(r["direction"] == expected_dir and i not in attempts, "skip direction/duplicate")
        attempts[i] = r["direction"]
    scheduled = set(range(OFFSET, len(daily), 10))
    require(set(attempts) == scheduled, "scheduled signals not reconciled")
    require(len(entries) + len(skips) == len(scheduled), "entry/skip count")
    require(len(skips) == 0, "user rule requires an entry on every scheduled 10-session cycle")
    for episode, t in trade_map.items():
        if t.get("exit_date"):
            held = int(float(t.get("hold_sessions") or 0))
            if held > 20:
                require(int(float(t.get("exit_deferred_sessions") or 0)) > 0,
                    episode + " held over 20 sessions without a documented unavailable exit quote")
            remaining = (date.fromisoformat(t["expiry"]) - date.fromisoformat(t["exit_date"])).days
            require(t.get("exit_source") != "OBSERVED_BID_ASK" or remaining <= 7 or held >= 20, episode + " exited before trigger")
    peak = None
    max_dd_usd = 0.0
    max_dd_pct = 0.0
    for r in daily:
        nav = float(r["nav_usd"])
        peak = nav if peak is None else max(peak, nav)
        max_dd_usd = min(max_dd_usd, nav - peak)
        max_dd_pct = min(max_dd_pct, (nav / peak - 1) * 100 if peak > 0 else 0)
    s = summary[0]
    end_nav = float(daily[-1]["nav_usd"])
    require(abs(max_dd_usd - float(s["max_drawdown_usd"])) <= .02, "MaxDD USD mismatch")
    require(abs(max_dd_pct - float(s["max_drawdown_pct"])) <= .0001, "MaxDD percent mismatch")
    require(abs(end_nav - float(s["ending_nav_usd"])) <= .02, "ending NAV mismatch")
    require(abs(end_nav - a.initial_nav - float(s["total_portfolio_pnl_usd"])) <= .02, "net P&L mismatch")
    print(json.dumps({
        "status": "PASS", "study_id": m["study_id"],
        "start": daily[0]["date"], "end": daily[-1]["date"],
        "common_sessions": len(daily), "scheduled_opportunities": len(scheduled),
        "entered_cohorts": len(entries), "skipped": len(skips),
        "ending_nav_usd": round(end_nav, 2),
        "net_pnl_usd": round(end_nav - a.initial_nav, 2),
        "max_drawdown_usd": round(max_dd_usd, 2),
        "max_drawdown_pct": round(max_dd_pct, 6)
    }, indent=2))

if __name__ == "__main__":
    main()
