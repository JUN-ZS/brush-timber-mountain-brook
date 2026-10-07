from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import futu  # type: ignore
except Exception:
    futu = None


ROOT = Path(__file__).resolve().parent
TOLERANCE_QTY = 1e-9
TOLERANCE_CASH = 0.01


def _num(value):
    try:
        if value is None or isinstance(value, bool):
            return None
        x = float(str(value).replace(",", ""))
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def _text(value):
    return str(value).strip() if value is not None else ""


def _row_get(row, *names, default=None):
    if isinstance(row, dict):
        for name in names:
            if name in row:
                return row[name]
        return default
    for name in names:
        try:
            return row[name]
        except Exception:
            pass
        try:
            return getattr(row, name)
        except Exception:
            pass
    return default


def _rows_from_frame(data):
    if data is None:
        return []
    if hasattr(data, "iterrows"):
        out = []
        for _, row in data.iterrows():
            out.append(row.to_dict() if hasattr(row, "to_dict") else dict(row))
        return out
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    return []


def canonical_symbol(value):
    raw = _text(value).upper()
    if "." in raw:
        prefix, rest = raw.split(".", 1)
        if prefix in {"US", "HK", "SG", "AU", "CA", "JP"}:
            return rest
    return raw


def position_side(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return {0: "LONG", 1: "SHORT"}.get(int(value))
    s = _text(value).upper()
    if s in {"LONG", "LONG_POSITION", "POSITION_SIDE_LONG", "POSITION_SIDE_LONG()", "0"}:
        return "LONG"
    if s in {"SHORT", "SHORT_POSITION", "POSITION_SIDE_SHORT", "POSITION_SIDE_SHORT()", "1"}:
        return "SHORT"
    return None


def source_trade_side(event):
    provenance = event.get("provenance") if isinstance(event, dict) else {}
    raw = _text((provenance or {}).get("sourceTradeSide"))
    if raw:
        return raw.upper()
    raw = _text(event.get("sourceTradeSide") if isinstance(event, dict) else "")
    return raw.upper()


def reconstruct_positions(normalized):
    events = (normalized or {}).get("events", [])
    books = {}
    unsafe = []

    ordered = sorted(
        [e for e in events if isinstance(e, dict) and str(e.get("type", "")).upper() == "FILL"],
        key=lambda e: (str(e.get("timestamp", "")), str(e.get("id", ""))),
    )

    for event in ordered:
        symbol = canonical_symbol(event.get("symbol"))
        side = source_trade_side(event)
        qty = _num(event.get("quantity"))
        if not symbol or qty is None or qty <= 0:
            unsafe.append({"eventId": event.get("id"), "reason": "FILL_MISSING_SYMBOL_OR_QUANTITY"})
            continue

        if side in {"BUY", "SELL"}:
            bucket = "LONG"
            delta = qty if side == "BUY" else -qty
        elif side == "SELL_SHORT":
            bucket = "SHORT"
            delta = qty
        elif side == "BUY_BACK":
            bucket = "SHORT"
            delta = -qty
        else:
            unsafe.append({
                "eventId": event.get("id"),
                "reason": "SOURCE_TRADE_SIDE_REQUIRED",
                "sourceTradeSide": side or None,
            })
            continue

        key = (symbol, bucket)
        books[key] = books.get(key, 0.0) + delta

    return {
        "positions": [
            {"symbol": symbol, "side": bucket, "quantity": round(qty, 12)}
            for (symbol, bucket), qty in sorted(books.items())
            if abs(qty) > TOLERANCE_QTY
        ],
        "unsafe": unsafe,
    }


def extract_actual_positions(rows):
    out = {}
    invalid = []
    raw_rows = []

    for row in _rows_from_frame(rows):
        code = canonical_symbol(_row_get(row, "code", "symbol"))
        side = position_side(_row_get(row, "position_side", "positionSide"))
        qty = _num(_row_get(row, "qty", "quantity"))
        if not code or not side or qty is None:
            invalid.append({
                "code": _text(_row_get(row, "code", "symbol")),
                "reason": "POSITION_ROW_MISSING_CODE_SIDE_OR_QTY",
            })
            continue
        if qty < 0:
            invalid.append({"code": code, "reason": "POSITION_QTY_NEGATIVE"})
            continue

        key = (code, side)
        out[key] = out.get(key, 0.0) + qty
        raw_rows.append({
            "code": _text(_row_get(row, "code", "symbol")),
            "positionSide": side,
            "qty": qty,
            "canSellQty": _num(_row_get(row, "can_sell_qty", "canSellQty")),
            "averageCost": _num(_row_get(row, "average_cost", "averageCostPrice", "average_cost_price")),
            "dilutedCost": _num(_row_get(row, "diluted_cost", "dilutedCostPrice")),
            "marketValue": _num(_row_get(row, "market_val", "marketValue", "val")),
            "unrealizedPL": _num(_row_get(row, "unrealized_pl", "unrealizedPL")),
            "realizedPL": _num(_row_get(row, "realized_pl", "realizedPL")),
            "currency": _text(_row_get(row, "currency")) or None,
            "positionId": _text(_row_get(row, "position_id", "positionID")) or None,
        })

    return {
        "positions": [
            {"symbol": symbol, "side": side, "quantity": round(qty, 12)}
            for (symbol, side), qty in sorted(out.items())
            if abs(qty) > TOLERANCE_QTY
        ],
        "invalid": invalid,
        "rawRows": raw_rows,
    }


def compare_positions(expected, actual, unsafe=None):
    expected_map = {(p["symbol"], p["side"]): p["quantity"] for p in (expected or {}).get("positions", [])}
    actual_map = {(p["symbol"], p["side"]): p["quantity"] for p in (actual or {}).get("positions", [])}

    rows = []
    matched = under = over = missing = extra = 0

    for symbol, side in sorted(set(expected_map) | set(actual_map)):
        exp = expected_map.get((symbol, side), 0.0)
        got = actual_map.get((symbol, side), 0.0)
        delta = got - exp
        if abs(delta) <= TOLERANCE_QTY:
            status = "MATCH"
            matched += 1
        elif exp > 0 and got == 0:
            status = "MISSING"
            missing += 1
        elif exp == 0 and got > 0:
            status = "EXTRA"
            extra += 1
        elif delta < 0:
            status = "UNDER"
            under += 1
        else:
            status = "OVER"
            over += 1

        rows.append({
            "symbol": symbol,
            "side": side,
            "expectedQty": round(exp, 12),
            "actualQty": round(got, 12),
            "deltaQty": round(delta, 12),
            "status": status,
        })

    if (unsafe or {}).get("unsafe"):
        status = "BLOCKED_UNSAFE_HISTORY"
    elif (actual or {}).get("invalid"):
        status = "BLOCKED_INVALID_BROKER_ROWS"
    elif missing or extra or under or over:
        status = "MISMATCH"
    else:
        status = "MATCH"

    return {
        "status": status,
        "rows": rows,
        "summary": {
            "matched": matched,
            "under": under,
            "over": over,
            "missing": missing,
            "extra": extra,
            "expectedKeys": len(expected_map),
            "actualKeys": len(actual_map),
        },
    }


def fill_cash_delta(event):
    if str(event.get("type", "")).upper() != "FILL":
        return None
    qty = _num(event.get("quantity"))
    price = _num(event.get("price"))
    multiplier = _num(event.get("multiplier")) or 1.0
    fees = _num(event.get("fees")) if event.get("fees") not in (None, "") else 0.0
    if qty is None or price is None or multiplier <= 0 or fees is None or fees < 0:
        return None

    raw_side = source_trade_side(event)
    if raw_side in {"BUY", "BUY_BACK"}:
        gross = -(qty * price * multiplier)
    elif raw_side in {"SELL", "SELL_SHORT"}:
        gross = qty * price * multiplier
    else:
        return None
    return gross - fees


def known_cash_delta(normalized):
    total = 0.0
    applied = []
    blocked = []

    for event in (normalized or {}).get("events", []):
        event_type = str(event.get("type", "")).upper()
        if event_type == "FILL":
            delta = fill_cash_delta(event)
            if delta is None:
                blocked.append({"eventId": event.get("id"), "type": event_type, "reason": "FILL_CASH_EFFECT_NOT_RECONSTRUCTABLE"})
                continue
            total += delta
            applied.append({"eventId": event.get("id"), "type": event_type, "amount": delta})
        elif event_type in {"CASHFLOW", "DIVIDEND", "INTEREST", "BORROW_FEE"}:
            amount = _num(event.get("amount"))
            if amount is None:
                blocked.append({"eventId": event.get("id"), "type": event_type, "reason": "CASH_EVENT_MISSING_AMOUNT"})
                continue
            total += amount
            applied.append({"eventId": event.get("id"), "type": event_type, "amount": amount})

    for event in (normalized or {}).get("quarantine", []):
        amount = _num(event.get("amount"))
        if amount is None or abs(amount) <= 1e-12:
            continue
        blocked.append({
            "eventId": event.get("id"),
            "type": str(event.get("type", "")).upper(),
            "amount": amount,
            "reason": str(event.get("classificationReason", "QUARANTINED_CASH_EFFECT")),
        })

    return {
        "knownCashDelta": total,
        "appliedEvents": applied,
        "blockingQuarantine": blocked,
    }


def reconcile_cash(normalized, actual_usd_cash, opening_cash=None):
    cash = known_cash_delta(normalized)
    if opening_cash is None:
        return {
            "status": "NEEDS_OPENING_CASH",
            "openingCash": None,
            "knownCashDelta": cash["knownCashDelta"],
            "expectedCash": None,
            "actualUsdCash": actual_usd_cash,
            "delta": None,
            "blockingQuarantine": cash["blockingQuarantine"],
            "appliedEvents": cash["appliedEvents"],
            "reason": "Absolute cash parity requires a broker cash anchor at the imported history start.",
        }

    expected = opening_cash + cash["knownCashDelta"]
    delta = None if actual_usd_cash is None else actual_usd_cash - expected

    if cash["blockingQuarantine"]:
        status = "BLOCKED_QUARANTINED_CASH_EVENTS"
    elif actual_usd_cash is None:
        status = "BROKER_CASH_UNAVAILABLE"
    elif abs(delta) <= TOLERANCE_CASH:
        status = "MATCH"
    else:
        status = "MISMATCH"

    return {
        "status": status,
        "openingCash": opening_cash,
        "knownCashDelta": cash["knownCashDelta"],
        "expectedCash": expected,
        "actualUsdCash": actual_usd_cash,
        "delta": delta,
        "blockingQuarantine": cash["blockingQuarantine"],
        "appliedEvents": cash["appliedEvents"],
        "reason": "Exact only when no cash-impacting quarantine remains and broker USD cash matches the anchored event reconstruction.",
    }


def fetch_broker_snapshot(host, port, acc_id, acc_index, refresh_cache=True):
    if futu is None:
        raise RuntimeError("futu-api unavailable")

    env = futu.TrdEnv.REAL
    market = futu.TrdMarket.US
    ctx = futu.OpenSecTradeContext(host=host, port=port, filter_trdmarket=market)

    try:
        position_kwargs = {
            "position_market": market,
            "trd_env": env,
            "acc_id": acc_id,
            "acc_index": acc_index,
            "refresh_cache": bool(refresh_cache),
        }
        ret_pos, positions = ctx.position_list_query(**position_kwargs)
        if ret_pos != getattr(futu, "RET_OK", 0):
            raise RuntimeError("position_list_query: " + str(positions))

        currency = getattr(getattr(futu, "Currency", None), "USD", None)
        funds_kwargs = {
            "trd_env": env,
            "acc_id": acc_id,
            "acc_index": acc_index,
            "refresh_cache": bool(refresh_cache),
        }
        if currency is not None:
            funds_kwargs["currency"] = currency

        ret_funds, funds = ctx.accinfo_query(**funds_kwargs)
        if ret_funds != getattr(futu, "RET_OK", 0):
            raise RuntimeError("accinfo_query: " + str(funds))

        fund_rows = _rows_from_frame(funds)
        fund = fund_rows[0] if fund_rows else {}
        return {
            "capturedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "source": "FUTU_OPEND_REAL_READ_ONLY",
            "account": {
                "accId": acc_id,
                "accIndex": acc_index,
                "market": "US",
                "tradingEnvironment": "REAL",
            },
            "positions": positions if isinstance(positions, list) else _rows_from_frame(positions),
            "funds": fund,
            "usdCash": _num(_row_get(fund, "us_cash", "USD_cash")),
            "usdWithdrawableCash": _num(_row_get(fund, "us_avl_withdrawal_cash", "USD_avl_withdrawal_cash")),
            "totalAssets": _num(_row_get(fund, "total_assets")),
            "marketValue": _num(_row_get(fund, "market_val")),
            "securitiesAssets": _num(_row_get(fund, "securities_assets")),
        }
    finally:
        try:
            ctx.close()
        except Exception:
            pass


def run_reconciliation(import_bundle, broker_snapshot, opening_cash=None):
    normalized = import_bundle.get("normalized") or {}
    expected = reconstruct_positions(normalized)
    actual = extract_actual_positions(broker_snapshot.get("positions", []))
    positions = compare_positions(expected, actual, expected)
    cash = reconcile_cash(normalized, broker_snapshot.get("usdCash"), opening_cash)

    return {
        "schemaVersion": 1,
        "contract": "FUTU_BROKER_RECONCILIATION_V1",
        "capturedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "readOnly": True,
        "ordersPlaced": False,
        "sourceImport": {
            "contract": import_bundle.get("contract"),
            "schemaVersion": import_bundle.get("schemaVersion"),
            "meta": (import_bundle.get("raw") or {}).get("meta", {}),
        },
        "positionReconciliation": positions,
        "cashReconciliation": cash,
        "brokerSnapshot": broker_snapshot,
        "reconstruction": expected,
    }


def build_parser():
    p = argparse.ArgumentParser(description="Compare normalized Futu broker history against current real OpenD positions/cash.")
    p.add_argument("--input", required=True, help="broker_import_*.json from Broker Import V1")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=11111)
    p.add_argument("--acc-id", type=int, default=0)
    p.add_argument("--acc-index", type=int, default=0)
    p.add_argument("--opening-cash", type=float, default=None, help="USD cash anchor at the imported history start; omit to show NEEDS_OPENING_CASH.")
    p.add_argument("--no-refresh-cache", action="store_true", help="Use OpenD cached position/fund data instead of refreshing.")
    p.add_argument("--output", default="")
    return p


def main() -> int:
    args = build_parser().parse_args()
    input_path = Path(args.input)
    if not input_path.exists():
        print("ERROR: input file not found: " + str(input_path), file=sys.stderr)
        return 2

    try:
        bundle = json.loads(input_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print("ERROR: invalid input JSON: " + str(exc), file=sys.stderr)
        return 2

    if not isinstance(bundle, dict) or bundle.get("contract") != "FUTU_BROKER_IMPORT_V1":
        print("ERROR: input is not a FUTU_BROKER_IMPORT_V1 bundle", file=sys.stderr)
        return 2
    if futu is None:
        print("ERROR: futu-api unavailable", file=sys.stderr)
        return 2

    try:
        snapshot = fetch_broker_snapshot(args.host, args.port, args.acc_id, args.acc_index, refresh_cache=not args.no_refresh_cache)
        report = run_reconciliation(bundle, snapshot, args.opening_cash)
    except Exception as exc:
        print("ERROR: " + type(exc).__name__ + ": " + str(exc), file=sys.stderr)
        return 3

    out_path = Path(args.output) if args.output else input_path.with_name(input_path.stem + "_reconcile.json")
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "ok": True,
        "contract": report["contract"],
        "positionStatus": report["positionReconciliation"]["status"],
        "cashStatus": report["cashReconciliation"]["status"],
        "positionRows": len(report["positionReconciliation"]["rows"]),
        "brokerPositions": len(report["brokerSnapshot"]["positions"]),
        "usdCash": report["brokerSnapshot"]["usdCash"],
        "readOnly": True,
        "ordersPlaced": False,
        "output": str(out_path),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
