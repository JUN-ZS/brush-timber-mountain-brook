from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

try:
    import futu  # type: ignore
except Exception as exc:
    futu = None
    FUTU_IMPORT_ERROR = exc


ROOT = Path(__file__).resolve().parent


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("date must be YYYY-MM-DD") from exc


def rows(data):
    if data is None:
        return []
    if hasattr(data, "to_dict"):
        return data.to_dict("records")
    if isinstance(data, dict):
        return [data]
    return list(data) if isinstance(data, (list, tuple)) else []


def scalar(row, *names, default=None):
    for name in names:
        if isinstance(row, dict) and name in row:
            return row[name]
    return default


def iso_from_futu_time(raw: str, zone: ZoneInfo) -> str:
    text = str(raw).strip()
    dt = datetime.fromisoformat(text.replace(" ", "T"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=zone)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def range_chunks(start: date, end: date, max_days: int = 90):
    cursor = start
    while cursor <= end:
        chunk_end = min(cursor + timedelta(days=max_days - 1), end)
        yield cursor, chunk_end
        cursor = chunk_end + timedelta(days=1)


def call_futu(ctx, method_name, *args, **kwargs):
    method = getattr(ctx, method_name)
    ret, data = method(*args, **kwargs)
    ret_ok = getattr(futu, "RET_OK", 0)
    if ret != ret_ok:
        raise RuntimeError(f"{method_name} failed: {data}")
    return rows(data)


def fetch_deals(ctx, start: date, end: date, acc_id: int, acc_index: int):
    out = []
    for a, b in range_chunks(start, end, 90):
        chunk = call_futu(
            ctx,
            "history_deal_list_query",
            start=f"{a.isoformat()} 00:00:00",
            end=f"{b.isoformat()} 23:59:59",
            trd_env=futu.TrdEnv.REAL,
            acc_id=acc_id,
            acc_index=acc_index,
        )
        out.extend(chunk)
    return out


def fetch_order_fees(ctx, order_ids, acc_id: int, acc_index: int):
    unique = []
    seen = set()
    for oid in order_ids:
        s = str(oid).strip()
        if s and s not in seen:
            unique.append(s)
            seen.add(s)

    out = []
    for i in range(0, len(unique), 400):
        batch = unique[i:i + 400]
        out.extend(call_futu(
            ctx,
            "order_fee_query",
            order_id_list=batch,
            trd_env=futu.TrdEnv.REAL,
            acc_id=acc_id,
            acc_index=acc_index,
        ))
    return out


def fetch_cashflows(ctx, start: date, end: date, throttle_seconds: float, acc_id: int, acc_index: int):
    out = []
    day = start
    requests = 0
    while day <= end:
        if day.weekday() < 5:
            out.extend(
                call_futu(
                    ctx,
                    "get_acc_cash_flow",
                    clearing_date=day.isoformat(),
                    trd_env=futu.TrdEnv.REAL,
                    acc_id=acc_id,
                    acc_index=acc_index,
                )
            )
            requests += 1
            if throttle_seconds > 0:
                time.sleep(throttle_seconds)
        day += timedelta(days=1)
    return out, requests


def build_parser():
    p = argparse.ArgumentParser(description="Read-only Futu OpenD history -> broker normalization bundle")
    p.add_argument("--start", required=True, type=parse_date)
    p.add_argument("--end", required=True, type=parse_date)
    p.add_argument("--market", choices=("US", "HK"), default="US")
    p.add_argument("--timezone", default="America/New_York")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=11111)
    p.add_argument("--acc-id", type=int, default=0)
    p.add_argument("--acc-index", type=int, default=0)
    p.add_argument("--with-cashflows", action="store_true")
    p.add_argument("--cashflow-throttle", type=float, default=1.6)
    p.add_argument("--output", default="")
    return p


def main() -> int:
    args = build_parser().parse_args()
    if args.end < args.start:
        print("ERROR: end date before start date", file=sys.stderr)
        return 2
    if futu is None:
        print("ERROR: futu-api is unavailable: " + str(FUTU_IMPORT_ERROR), file=sys.stderr)
        return 2

    try:
        source_zone = ZoneInfo(args.timezone)
    except Exception as exc:
        print("ERROR: invalid timezone: " + str(exc), file=sys.stderr)
        return 2

    market = futu.TrdMarket.US if args.market == "US" else futu.TrdMarket.HK
    imported_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    ctx = futu.OpenSecTradeContext(
        filter_trdmarket=market,
        host=args.host,
        port=args.port,
    )

    try:
        deals = fetch_deals(ctx, args.start, args.end, args.acc_id, args.acc_index)
        order_ids = [scalar(x, "order_id", "orderID") for x in deals]
        fee_rows = fetch_order_fees(ctx, order_ids, args.acc_id, args.acc_index)
        cashflows = []
        cashflow_requests = 0
        if args.with_cashflows:
            cashflows, cashflow_requests = fetch_cashflows(
                ctx, args.start, args.end, max(0.0, args.cashflow_throttle), args.acc_id, args.acc_index
            )
    finally:
        try:
            ctx.close()
        except Exception:
            pass

    deals_for_normalizer = []
    for deal in deals:
        copied = dict(deal)
        copied["create_time"] = iso_from_futu_time(
            scalar(deal, "create_time", "createTime"),
            source_zone,
        )
        deals_for_normalizer.append(copied)

    raw = {
        "deals": deals,
        "fees": fee_rows,
        "cashflows": cashflows,
        "meta": {
            "broker": "FUTU",
            "market": args.market,
            "start": args.start.isoformat(),
            "end": args.end.isoformat(),
            "timezone": args.timezone,
            "accId": args.acc_id,
            "accIndex": args.acc_index,
            "importedAt": imported_at,
            "cashflowRequests": cashflow_requests,
            "readOnly": True,
            "ordersPlaced": False,
        },
    }

    normalizer = ROOT / "broker_event_normalizer.cjs"
    normalizer_input = {
        "deals": deals_for_normalizer,
        "fees": fee_rows,
        "cashflows": cashflows,
        "meta": raw["meta"],
    }
    proc = subprocess.run(
        ["node", "-e", "const N=require(process.argv[1]); const raw=JSON.parse(require('fs').readFileSync(0,'utf8')); const out=N.normalizeBundle(raw,{sourceTimezone:null,feeRows:raw.fees,importedAt:raw.meta.importedAt}); process.stdout.write(JSON.stringify(out));", str(normalizer)],
        input=json.dumps(normalizer_input, ensure_ascii=False),
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        print(proc.stderr, file=sys.stderr)
        return 3

    normalized = json.loads(proc.stdout)
    normalized["sourceTimezone"] = args.timezone
    for event in normalized["events"]:
        if event.get("type") == "FILL":
            event["provenance"]["sourceTimezone"] = args.timezone

    output = {
        "schemaVersion": 1,
        "contract": "FUTU_BROKER_IMPORT_V1",
        "raw": raw,
        "normalizerInput": normalizer_input,
        "normalized": normalized,
        "readOnly": True,
        "ordersPlaced": False,
    }

    out_path = Path(args.output) if args.output else ROOT / (
        "broker_import_" + args.start.isoformat() + "_" + args.end.isoformat() + ".json"
    )
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "ok": True,
        "output": str(out_path),
        "deals": len(deals),
        "fees": len(fee_rows),
        "cashflows": len(cashflows),
        "cashflowRequests": cashflow_requests,
        "normalizedEvents": len(normalized["events"]),
        "quarantine": len(normalized["quarantine"]),
        "readOnly": True,
        "ordersPlaced": False,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
