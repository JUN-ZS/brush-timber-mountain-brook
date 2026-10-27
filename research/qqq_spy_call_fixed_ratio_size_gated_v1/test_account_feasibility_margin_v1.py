#!/usr/bin/env python3
"""Deterministic tests for account cash ledger and the stated margin proxy."""
from account_feasibility_margin_v1 import (
    UNIT_COST_PER_CONTRACT_PER_SIDE,
    entry_cash_delta,
    exit_cash_delta,
    naked_stock_option_margin_per_contract,
    option_intrinsic,
    stress_option_mark,
)


def main():
    # IBKR-published naked stock-option formula examples, one standard 100-share contract.
    assert abs(naked_stock_option_margin_per_contract("C", 100, 110, 2, 1) - 1200.0) < 1e-9
    assert abs(naked_stock_option_margin_per_contract("P", 100, 90, 2, 1) - 1200.0) < 1e-9
    assert abs(naked_stock_option_margin_per_contract("P", 100, 110, 12, 1) - 3200.0) < 1e-9
    assert abs(naked_stock_option_margin_per_contract("C", 100, 90, 15, 2) - 7000.0) < 1e-9

    assert option_intrinsic("P", 90, 100) == 10
    assert option_intrinsic("C", 110, 100) == 10
    assert option_intrinsic("C", 90, 100) == 0

    long_pos = {"position_side": "LONG", "entry_price": 4.0, "qty": 1}
    short_pos = {"position_side": "SHORT", "entry_price": 2.0, "qty": 6}
    assert abs(entry_cash_delta(long_pos) - (-400.0 - UNIT_COST_PER_CONTRACT_PER_SIDE)) < 1e-9
    assert abs(entry_cash_delta(short_pos) - (1200.0 - 6 * UNIT_COST_PER_CONTRACT_PER_SIDE)) < 1e-9

    long_exit = {**long_pos, "exit_price": 3.0, "position_id": "long"}
    short_exit = {**short_pos, "exit_price": 2.5, "position_id": "short"}
    assert abs(exit_cash_delta(long_exit) - (300.0 - UNIT_COST_PER_CONTRACT_PER_SIDE)) < 1e-9
    assert abs(exit_cash_delta(short_exit) - (-1500.0 - 6 * UNIT_COST_PER_CONTRACT_PER_SIDE)) < 1e-9

    scenario = {"qqq_return": -0.20, "spy_return": -0.20, "extrinsic_multiplier": 2.0}
    put_pos = {"symbol": "SPY", "right": "P", "strike": 100}
    shocked_spot, shocked_mark = stress_option_mark(put_pos, 3.0, 100.0, scenario)
    assert shocked_spot == 80.0
    assert shocked_mark == 26.0  # intrinsic 20 + current extrinsic 3 * 2

    # A finite +100% shock is not a bound on naked-call losses.
    call_pos = {"symbol": "SPY", "right": "C", "strike": 100}
    up = {"qqq_return": 1.0, "spy_return": 1.0, "extrinsic_multiplier": 0.5}
    _, call_mark = stress_option_mark(call_pos, 2.0, 100.0, up)
    assert call_mark == 101.0

    print("ACCOUNT FEASIBILITY TEST PASS: naked-option margin, cash flows, intrinsic payoff, and stress repricing.")


if __name__ == "__main__":
    main()
