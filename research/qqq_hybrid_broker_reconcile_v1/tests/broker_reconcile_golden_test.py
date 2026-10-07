from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from broker_reconcile import compare_positions, extract_actual_positions, known_cash_delta, reconcile_cash, reconstruct_positions  # noqa: E402


def main() -> None:
    normalized = {
        "events": [
            {
                "id": "FUTU:FILL:D1",
                "type": "FILL",
                "symbol": "QQQ",
                "quantity": 10,
                "price": 700,
                "multiplier": 1,
                "fees": 1.25,
                "provenance": {"sourceTradeSide": "BUY"},
            },
            {
                "id": "FUTU:FILL:D2",
                "type": "FILL",
                "symbol": "QQQ261218C00750000",
                "quantity": 2,
                "price": 5,
                "multiplier": 100,
                "fees": 3.50,
                "provenance": {"sourceTradeSide": "BUY"},
            },
            {
                "id": "FUTU:FILL:D3",
                "type": "FILL",
                "symbol": "QQQ",
                "quantity": 3,
                "price": 690,
                "multiplier": 1,
                "fees": 0,
                "provenance": {"sourceTradeSide": "SELL_SHORT"},
            },
            {
                "id": "FUTU:FILL:D4",
                "type": "FILL",
                "symbol": "QQQ",
                "quantity": 1,
                "price": 680,
                "multiplier": 1,
                "fees": 0,
                "provenance": {"sourceTradeSide": "BUY_BACK"},
            },
            {"id": "FUTU:DIVIDEND:10", "type": "DIVIDEND", "amount": 12.50},
            {"id": "FUTU:INTEREST:11", "type": "INTEREST", "amount": -2.20},
            {"id": "FUTU:CASHFLOW:12", "type": "CASHFLOW", "amount": 1000},
        ],
        "quarantine": [
            {
                "id": "FUTU:FEE:13",
                "type": "FEE",
                "amount": -1.0,
                "classificationReason": "FEE_DEDUP_LINK_REQUIRED",
            },
            {
                "id": "FUTU:TRADE_SETTLEMENT_AUDIT:14",
                "type": "TRADE_SETTLEMENT_AUDIT",
                "amount": -7000,
            },
        ],
    }

    expected = reconstruct_positions(normalized)
    assert expected["unsafe"] == []
    assert expected["positions"] == [
        {"symbol": "QQQ", "side": "LONG", "quantity": 10},
        {"symbol": "QQQ", "side": "SHORT", "quantity": 2},
        {"symbol": "QQQ261218C00750000", "side": "LONG", "quantity": 2},
    ]

    actual = extract_actual_positions([
        {"code": "US.QQQ", "position_side": "LONG", "qty": 10, "average_cost": 705},
        {"code": "US.QQQ", "position_side": "SHORT", "qty": 2, "average_cost": 690},
        {"code": "US.QQQ261218C00750000", "position_side": "LONG", "qty": 2, "average_cost": 5},
    ])
    report = compare_positions(expected, actual, expected)
    assert report["status"] == "MATCH"
    assert report["summary"]["matched"] == 3

    bad = extract_actual_positions([
        {"code": "US.QQQ", "position_side": "LONG", "qty": 9},
        {"code": "US.QQQ", "position_side": "SHORT", "qty": 2},
    ])
    bad_report = compare_positions(expected, bad, expected)
    assert bad_report["status"] == "MISMATCH"
    assert any(row["status"] == "UNDER" for row in bad_report["rows"])

    unsafe = reconstruct_positions({
        "events": [{
            "id": "BAD",
            "type": "FILL",
            "symbol": "QQQ",
            "quantity": 1,
            "price": 700,
            "provenance": {},
        }]
    })
    blocked = compare_positions(unsafe, actual, unsafe)
    assert blocked["status"] == "BLOCKED_UNSAFE_HISTORY"

    delta = known_cash_delta(normalized)
    expected_cash_delta = (
        -(10 * 700) - 1.25
        - (2 * 5 * 100) - 3.50
        + (3 * 690)
        - (1 * 680)
        + 12.50 - 2.20 + 1000
    )
    assert abs(delta["knownCashDelta"] - expected_cash_delta) < 1e-9
    assert len(delta["blockingQuarantine"]) == 2

    cash_need_anchor = reconcile_cash(normalized, 10000, None)
    assert cash_need_anchor["status"] == "NEEDS_OPENING_CASH"

    cash_blocked = reconcile_cash(normalized, 10000, 1000)
    assert cash_blocked["status"] == "BLOCKED_QUARANTINED_CASH_EVENTS"

    clean = dict(normalized)
    clean["quarantine"] = []
    clean_cash = reconcile_cash(clean, -604.45, 5000)
    assert clean_cash["status"] == "MATCH"

    incomplete = {
        "events": [{
            "id": "FUTU:FILL:INCOMPLETE",
            "type": "FILL",
            "symbol": "QQQ",
            "quantity": 1,
            "price": 700,
            "multiplier": 1,
            "fees": None,
            "provenance": {"sourceTradeSide": "BUY"},
        }]
    }
    incomplete_delta = known_cash_delta(incomplete)
    assert incomplete_delta["blockingQuarantine"]
    assert incomplete_delta["appliedEvents"] == []

    impossible_close = reconstruct_positions({
        "events": [{
            "id": "CLOSE_TOO_MUCH",
            "type": "FILL",
            "symbol": "QQQ",
            "quantity": 2,
            "price": 700,
            "multiplier": 1,
            "fees": 0,
            "provenance": {"sourceTradeSide": "SELL"},
        }]
    })
    assert impossible_close["unsafe"]
    assert impossible_close["positions"] == []

    print("BROKER RECONCILIATION GOLDEN TEST: PASS")


if __name__ == "__main__":
    main()
