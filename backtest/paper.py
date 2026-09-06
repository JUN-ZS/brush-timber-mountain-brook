"""Simulated paper book. Never opens Futu trade context. Never sends orders."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[1]
PAPER_PATH = ROOT / "reports" / "paper_portfolio.json"

START_NAV = 100_000.0


def empty_book(now: Optional[str] = None) -> dict[str, Any]:
    ts = now or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "timestamp": ts,
        "underlying_price": None,
        "option_price": None,
        "position": [],
        "quantity": 0,
        "entry": None,
        "exit": None,
        "premium": 0.0,
        "hedge_value": 0.0,
        "nav": START_NAV,
        "daily_pnl": 0.0,
        "cumulative_pnl": 0.0,
        "drawdown": 0.0,
        "max_dd": 0.0,
        "hedge_pnl": 0.0,
        "premium_drag": 0.0,
        "state": None,
        "risk_budget": None,
        "strategy": "NONE",
        "reason": "initialized empty; no live orders sent",
        "source": "SIMULATED",
        "orders": "NONE",
        "trade_context": "FORBIDDEN",
    }


def load_book() -> dict[str, Any]:
    if not PAPER_PATH.exists():
        return empty_book()
    try:
        return json.loads(PAPER_PATH.read_text(encoding="utf-8"))
    except Exception:
        return empty_book()


def save_book(book: dict[str, Any]) -> None:
    PAPER_PATH.parent.mkdir(parents=True, exist_ok=True)
    PAPER_PATH.write_text(json.dumps(book, indent=2), encoding="utf-8")


def snapshot(
    *,
    qqq: Optional[float],
    state: Optional[str],
    risk_budget: Optional[float],
    mark_option: Optional[float] = None,
) -> dict[str, Any]:
    """Mark-to-market only. Does not open/close anything."""
    book = load_book()
    book["timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    book["underlying_price"] = qqq
    book["option_price"] = mark_option
    book["state"] = state
    book["risk_budget"] = risk_budget
    book["source"] = "SIMULATED"
    book["orders"] = "NONE"
    book["trade_context"] = "FORBIDDEN"
    if not book.get("position"):
        book["reason"] = "paper book empty; diagnostic does not auto-trade"
        book["nav"] = START_NAV
        book["daily_pnl"] = 0.0
    save_book(book)
    return book
