#!/usr/bin/env python3
"""Deterministic tests for DTE20/DTE<=4 daily valuation and option-leg accounting."""
from qqq_spy_put_call_daily_nav_v1 import (
    pair_entries, drawdown_metrics, mark_open_leg, position_value_for_day, intrinsic_value,
)


def trade(signal, expiry="2018-04-13", entry="2018-03-02", signal_index="0",
          entry_index="1", contract="QQQ180413P00155000", status="RESOLVED", pnl="100"):
    return {
        "signal_date": signal, "expiry": expiry, "entry_date": entry,
        "signal_index": signal_index, "entry_index": entry_index,
        "qqq_contract_id": contract, "spy_contract_id": "SPY180413P00255000",
        "status": status, "net_pnl_usd": pnl,
    }


def test_pairing_requires_same_signal_expiry_entry():
    puts = [
        trade("d1"),
        trade("d2", expiry="2018-04-27"),
        trade("d3", entry="2018-04-02"),
    ]
    calls = [
        trade("d1", contract="QQQ180413C00180000", pnl="-50"),
        trade("d2", expiry="2018-05-04", contract="QQQ180427C00180000"),
        trade("d3", entry="2018-04-03", contract="QQQ180511C00180000"),
        trade("d4", contract="QQQ180413C00180000"),
    ]
    pairs, diag = pair_entries(puts, calls)
    assert len(pairs) == 1
    assert pairs[0]["signal_date"] == "d1"
    assert diag["common_signal_dates"] == 3
    assert diag["same_expiry_signal_dates"] == 2
    assert diag["same_entry_date_signal_dates"] == 1
    assert diag["call_only_signal_dates"] == 1


def test_daily_drawdown_from_nav():
    rows = [
        {"date": "d1", "portfolio_nav_usd": 100.0},
        {"date": "d2", "portfolio_nav_usd": 110.0},
        {"date": "d3", "portfolio_nav_usd": 88.0},
        {"date": "d4", "portfolio_nav_usd": 99.0},
    ]
    dd = drawdown_metrics(rows)
    assert dd["max_drawdown_usd"] == -22.0
    assert dd["max_drawdown_pct"] == -20.0
    assert dd["max_drawdown_peak_date"] == "d2"
    assert dd["max_drawdown_trough_date"] == "d3"


def test_open_leg_marks_at_liquidation_side_and_stale_quote_is_explicit():
    pos = {
        "symbol": "QQQ", "contract_id": "QQQ180413P00155000",
        "position_side": "LONG", "qty": 1, "entry_price": 4.0,
        "last_quote_date": "", "last_bid": None, "last_ask": None,
        "_last_quote_index": None,
    }
    live = mark_open_leg(pos, "d1", 0, {"bid": 5.0, "ask": 5.2})
    assert live["mark_price"] == 5.0
    assert live["signed_open_market_value_usd"] == 500.0
    assert round(live["unrealized_pnl_usd"], 2) == 88.70
    stale = mark_open_leg(pos, "d3", 2, None)
    assert stale["valuation_method"] == "STALE_LAST_VALID_QUOTE"
    assert stale["quote_age_sessions"] == 2
    assert stale["mark_price"] == 5.0


def test_resolved_leg_pnl_persists_after_exit_date():
    pos = {
        "entry_date": "d1", "terminal_kind": "RESOLVED", "terminal_date": "d2",
        "exit_date": "d2", "exit_price": 3.0, "final_pnl_usd": 123.45,
        "is_resolved": True, "symbol": "QQQ", "position_side": "LONG", "qty": 1,
    }
    dates = ["d1", "d2", "d3"]
    idx = {d: i for i, d in enumerate(dates)}
    at_exit = position_value_for_day(pos, "d2", 1, {}, {}, {}, dates, idx)
    after_exit = position_value_for_day(pos, "d3", 2, {}, {}, {}, dates, idx)
    assert at_exit["realized_pnl_usd"] == 123.45
    assert after_exit["realized_pnl_usd"] == 123.45
    assert after_exit["unrealized_pnl_usd"] == 0.0
    assert not after_exit["is_open_eod"]


def test_call_and_put_intrinsic_values():
    assert intrinsic_value("P", 90, 100) == 10
    assert intrinsic_value("C", 110, 100) == 10
    assert intrinsic_value("P", 110, 100) == 0
    assert intrinsic_value("C", 90, 100) == 0


def main():
    test_pairing_requires_same_signal_expiry_entry()
    test_daily_drawdown_from_nav()
    test_open_leg_marks_at_liquidation_side_and_stale_quote_is_explicit()
    test_resolved_leg_pnl_persists_after_exit_date()
    test_call_and_put_intrinsic_values()
    print("DAILY NAV TEST PASS: strict pairing, NAV drawdown, live/stale marks, closed-leg persistence, intrinsic payoff.")


if __name__ == "__main__":
    main()
