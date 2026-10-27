#!/usr/bin/env python3
"""Deterministic unit tests for strict PUT/CALL pairing, one-set capacity, and stock sizing."""
from qqq_spy_put_call_stock_overlay_v1 import pair_trade_rows, gate_pairs, calculate_stock_scenarios


def row(signal, expiry="2018-04-13", entry="2018-03-02", pnl="100", exit_index="5", status="RESOLVED",
        signal_index="0", entry_index="1"):
    return {
        "signal_date": signal, "expiry": expiry, "entry_date": entry,
        "signal_index": signal_index, "entry_index": entry_index,
        "status": status, "net_pnl_usd": pnl,
        "exit_date": "2018-03-09" if status == "RESOLVED" else "",
        "exit_index": exit_index if status == "RESOLVED" else "",
        "exit_reason": "HOLD_20_OR_DTE_LE_7",
    }


def test_pair_matching_is_strict():
    puts = [
        row("2018-03-01"),
        row("2018-03-15", expiry="2018-04-27"),
        row("2018-03-29", entry="2018-04-02"),
    ]
    calls = [
        row("2018-03-01", pnl="-50", exit_index="6"),
        row("2018-03-15", expiry="2018-05-04"),
        row("2018-03-29", entry="2018-04-03"),
        row("2018-04-13"),
    ]
    pairs, diag = pair_trade_rows(puts, calls)
    assert len(pairs) == 1, pairs
    assert pairs[0]["signal_date"] == "2018-03-01"
    assert pairs[0]["completed_pair_net_pnl_usd"] == 50.0
    assert diag["common_signal_dates"] == 3
    assert diag["same_expiry_signal_dates"] == 2
    assert diag["same_entry_date_signal_dates"] == 1
    assert diag["call_only_signal_dates"] == 1


def test_single_capacity_waits_for_both_legs():
    pairs = [
        {
            "signal_date": "d1", "signal_index": 0, "entry_index": 1,
            "both_resolved": True, "put_exit_index": "3", "call_exit_index": "5",
        },
        {
            "signal_date": "d2", "signal_index": 4, "entry_index": 5,
            "both_resolved": True, "put_exit_index": "8", "call_exit_index": "9",
        },
        {
            "signal_date": "d3", "signal_index": 6, "entry_index": 7,
            "both_resolved": False, "put_exit_index": "10", "call_exit_index": "",
        },
        {
            "signal_date": "d4", "signal_index": 10, "entry_index": 11,
            "both_resolved": True, "put_exit_index": "12", "call_exit_index": "13",
        },
    ]
    selected, blocked = gate_pairs(pairs, cap=1, source_sessions=20)
    assert [p["signal_date"] for p in selected] == ["d1", "d3"]
    assert [p["signal_date"] for p in blocked] == ["d2", "d4"]


def test_stock_overlay_uses_adjusted_close_ratio():
    universe = {
        "source": "fixture",
        "asof": "2026-09-04",
        "dates": ["2018-03-01", "2025-12-15"],
        "c": {"QQQ": [100.0, 200.0]},
    }
    result = calculate_stock_scenarios(
        universe, raw_start_close=160.0, notional=63694.0,
        current_price=200.0, current_price_date="2026-10-26",
    )
    assert result["qqq_total_return_factor"] == 2.0
    assert round(result["current_position_historical_start_value_usd"], 2) == 50955.2
    assert round(result["current_position_historical_total_return_pnl_usd"], 2) == 50955.2
    assert round(result["historical_initial_investment_total_return_pnl_usd"], 2) == 63694.0


def main():
    test_pair_matching_is_strict()
    test_single_capacity_waits_for_both_legs()
    test_stock_overlay_uses_adjusted_close_ratio()
    print("PUT/CALL STOCK OVERLAY TEST PASS: strict keys, one-set capacity, HUB total-return sizing.")


if __name__ == "__main__":
    main()
