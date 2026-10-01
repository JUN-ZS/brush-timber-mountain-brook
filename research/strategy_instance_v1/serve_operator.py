from __future__ import annotations

import argparse
import io
import json
import os
import traceback
from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler, SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .run_instance import (
    cycle,
    instance_summary,
    list_instances,
    load_instance,
    dt,
    manual_book_pnl_preview,
    record_manual_trade,
)
from ..evidence_v1.ledger import EvidenceLedger, sha256_json


MUTATION_HEADER = "X-QQQ-Operator"
MUTATION_HEADER_VALUE = "1"
MUTATING_PATHS = {"/api/manual", "/api/refresh"}


def explicit_strategy_context(repo, body):
    """Verify an operator-selected ticket against immutable DECISION_EMITTED evidence.

    Browser-supplied ticket fields are hints only. The authoritative ticket,
    decision timestamp, and pre-decision snapshot hash come from the evidence
    ledger; a forged or altered client snapshot is rejected.
    """
    raw = body.get("strategy_context_snapshot")
    instance_id = str(body.get("instance_id", "")).strip()
    if raw is None:
        return {}
    if not isinstance(raw, dict) or not instance_id:
        raise ValueError("STRATEGY_CONTEXT_NOT_VERIFIABLE")
    if str(raw.get("instance_id", "")).strip() != instance_id:
        raise ValueError("STRATEGY_CONTEXT_INSTANCE_MISMATCH")
    if str(raw.get("context_source") or "") != "OPERATOR_SELECTED_GLOBAL_TICKET_FOR_INSTANCE":
        raise ValueError("STRATEGY_CONTEXT_SOURCE_INVALID")

    ticket_id = str(raw.get("ticket_id") or "").strip()
    leg_raw = raw.get("leg")
    code = str((leg_raw or {}).get("code") or "").upper()
    if not ticket_id or not isinstance(leg_raw, dict) or not code:
        raise ValueError("STRATEGY_CONTEXT_NOT_VERIFIABLE")

    manifest, _, _ = load_instance(Path(repo), instance_id)
    instance_times = [
        z for z in (
            dt(manifest.get("created_at_utc")),
            dt(manifest.get("start_at_utc")),
        ) if z is not None
    ]
    instance_floor_dt = max(instance_times) if instance_times else None
    ledger = EvidenceLedger(Path(repo) / "research/evidence_v1/evidence.jsonl")
    matching = []
    for row in ledger.rows():
        if str(row.get("event_type") or "").upper() != "DECISION_EMITTED":
            continue
        row_instance_id = str(row.get("instance_id") or "").strip()
        if row_instance_id and row_instance_id != instance_id:
            continue
        decision_dt = dt(row.get("timestamp_utc"))
        if instance_floor_dt is not None and (
            decision_dt is None
            or decision_dt < instance_floor_dt
        ):
            continue
        ticket = (row.get("payload") or {}).get("ticket")
        if not isinstance(ticket, dict) or str(ticket.get("ticket_id") or "") != ticket_id:
            continue
        legs = ticket.get("legs") or []
        verified_leg = next(
            (leg for leg in legs if str(leg.get("code") or "").upper() == code),
            None,
        )
        if verified_leg is not None:
            matching.append((row, ticket, verified_leg))

    if not matching:
        raise ValueError("STRATEGY_CONTEXT_TICKET_NOT_VERIFIED")

    source_row, ticket, verified_leg = matching[-1]
    checks = (
        str(raw.get("action") or "") == str(ticket.get("action") or "")
        and str(raw.get("status") or "") == str(ticket.get("status") or "")
        and str(leg_raw.get("side") or "") == str(verified_leg.get("side") or "")
        and str(leg_raw.get("qty") or "") == str(verified_leg.get("qty") or "")
        and str(leg_raw.get("strategy_leg_action") or leg_raw.get("why") or "")
            == str(verified_leg.get("strategy_leg_action") or verified_leg.get("why") or "")
    )
    if not checks:
        raise ValueError("STRATEGY_CONTEXT_TICKET_TAMPERED")

    payload = source_row.get("payload") or {}
    return {
        "ticket_id": ticket.get("ticket_id"),
        "strategy_instance_id": instance_id,
        "action": ticket.get("action"),
        "strategy_leg_action": verified_leg.get("strategy_leg_action") or verified_leg.get("why"),
        "direction": verified_leg.get("direction"),
        "status": ticket.get("status"),
        "code": verified_leg.get("code"),
        "qty": verified_leg.get("qty"),
        "side": verified_leg.get("side"),
        "before_qty": verified_leg.get("before_qty"),
        "target_qty": verified_leg.get("target_qty"),
        "price": verified_leg.get("price"),
        "captured_at_utc": source_row.get("timestamp_utc"),
        "source_evidence_id": source_row.get("evidence_id"),
        "pre_decision_snapshot_sha256": payload.get("snapshot_sha256"),
        "ticket_snapshot_sha256": sha256_json(ticket),
        "ticket_snapshot": json.loads(json.dumps(ticket, ensure_ascii=False)),
        "context_source": "VERIFIED_DECISION_EMITTED_EVIDENCE",
    }


class OperatorHandler(SimpleHTTPRequestHandler):
    server_version = "QQQOperator/1.0"

    def _repo(self) -> Path:
        return self.server.repo_root

    def _json(self, status: int, obj: dict) -> None:
        raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _mutation_allowed(self) -> bool:
        return self.headers.get(MUTATION_HEADER) == MUTATION_HEADER_VALUE

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length", "0") or 0)
        if n <= 0 or n > 1024 * 1024:
            raise ValueError("INVALID_CONTENT_LENGTH")
        obj = json.loads(self.rfile.read(n).decode("utf-8"))
        if not isinstance(obj, dict):
            raise ValueError("JSON_OBJECT_REQUIRED")
        return obj

    def do_GET(self):
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/instances":
                self._json(200, {"status": "OK", "instances": list_instances(self._repo())})
                return

            if parsed.path == "/api/instance":
                q = parse_qs(parsed.query)
                instance_id = str((q.get("instance_id") or [""])[0]).strip()
                if not instance_id:
                    raise ValueError("INSTANCE_ID_REQUIRED")
                self._json(200, {"status": "OK", **instance_summary(self._repo(), instance_id)})
                return

            if parsed.path == "/api/strategy":
                path = self._repo() / "research" / "live_hedge_v1" / "live_state.json"
                if not path.exists():
                    self._json(200, {"status": "MISSING_LIVE_STATE"})
                    return
                self._json(200, {"status": "OK", "live": json.loads(path.read_text(encoding="utf-8"))})
                return

            return super().do_GET()
        except FileNotFoundError:
            self._json(404, {"status": "NOT_FOUND"})
        except Exception as exc:
            self._json(400, {"status": "ERROR", "error": str(exc)})

    def do_POST(self):
        if urlparse(self.path).path in MUTATING_PATHS:
            if not self._mutation_allowed():
                self._json(403, {"status": "FORBIDDEN", "error": "OPERATOR_HEADER_REQUIRED"})
                return
        try:
            body = self._body()

            if self.path == "/api/preview":
                instance_id = str(body.get("instance_id", "")).strip()
                if not instance_id:
                    raise ValueError("INSTANCE_ID_REQUIRED")
                _, state, _ = load_instance(self._repo(), instance_id)
                preview = manual_book_pnl_preview(
                    state.get("manual_lots", []),
                    action=body.get("action"),
                    code=body.get("code"),
                    qty=body.get("qty"),
                    price=body.get("price"),
                    lot_size=body.get("lot_size", 100),
                )
                self._json(200, {"status": "OK", "preview": preview})
                return

            if self.path == "/api/manual":
                strategy_context = explicit_strategy_context(self._repo(), body)
                out = record_manual_trade(
                    self._repo(),
                    instance_id=str(body.get("instance_id", "")).strip(),
                    action=body.get("action"),
                    code=body.get("code"),
                    qty=body.get("qty"),
                    price=body.get("price"),
                    lot_size=body.get("lot_size", 100),
                    timestamp_utc=body.get("timestamp_utc"),
                    trade_id=body.get("trade_id"),
                    note=body.get("note", ""),
                    strategy_context=strategy_context,
                )
                self._json(200, out)
                return

            if self.path == "/api/refresh":
                instance_id = str(body.get("instance_id", "")).strip()
                if not instance_id:
                    raise ValueError("INSTANCE_ID_REQUIRED")

                class Args:
                    pass

                a = Args()
                a.repo_root = self._repo()
                a.instance_id = instance_id
                a.host = str(body.get("host") or "127.0.0.1")
                a.port = int(body.get("port") or 11111)
                a.simulate = bool(body.get("simulate", False))
                a.observe_strategy_plan = True
                a.backfill_after_minutes = 10

                buf = io.StringIO()
                with redirect_stdout(buf):
                    rc = cycle(a)
                lines = [x for x in buf.getvalue().splitlines() if x.strip()]
                payload = json.loads(lines[-1]) if lines else {"status": "REFRESH_RETURNED_EMPTY"}
                payload["returncode"] = rc
                self._json(200 if rc == 0 else 409, payload)
                return

            raise ValueError("UNKNOWN_ENDPOINT")
        except SystemExit as exc:
            self._json(400, {"status": "ERROR", "error": str(exc)})
        except Exception as exc:
            self._json(400, {"status": "ERROR", "error": str(exc), "trace": traceback.format_exc(limit=2)})

    def log_message(self, fmt, *args):
        print("[operator] " + (fmt % args), flush=True)


def main():
    ap = argparse.ArgumentParser(description="Local QQQ Strategy Operator Console")
    ap.add_argument("--port", type=int, default=8766)
    args = ap.parse_args()

    repo = Path(__file__).resolve().parents[2]
    os.chdir(repo)

    httpd = ThreadingHTTPServer(("127.0.0.1", args.port), OperatorHandler)
    httpd.repo_root = repo
    print(
        f"Operator Console: http://127.0.0.1:{args.port}/research/strategy_instance_v1/operator_dashboard.html",
        flush=True,
    )
    print("LOCAL ONLY: this console records USER_MANUAL trades; it never submits broker orders. Remote bind is intentionally disabled.", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
