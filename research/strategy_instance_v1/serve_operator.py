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
    manual_book_pnl_preview,
    record_manual_trade,
)


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
                    strategy_id=body.get("strategy_id", "UNALLOCATED"),
                )
                self._json(200, {"status": "OK", "preview": preview})
                return

            if self.path == "/api/manual":
                strategy_context = {}
                live_path = self._repo() / "research" / "live_hedge_v1" / "live_state.json"
                if live_path.exists():
                    try:
                        live = json.loads(live_path.read_text(encoding="utf-8"))
                        card = live.get("action_card") or {}
                        legs = card.get("legs") or []
                        leg = next((x for x in legs if str(x.get("code","")).upper()==str(body.get("code","")).upper()), None)
                        if leg:
                            strategy_context = {
                                "ticket_id":card.get("ticket_id"),
                                "action":card.get("action"),
                                "strategy_leg_action":leg.get("why"),
                                "status":card.get("status"),
                                "code":leg.get("code"),
                                "qty":leg.get("qty"),
                                "side":leg.get("side"),
                                "before_qty":leg.get("before_qty"),
                                "target_qty":leg.get("target_qty"),
                                "price":leg.get("price"),
                                "captured_at_utc":live.get("timestamp"),
                            }
                    except Exception:
                        strategy_context = {}
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
                    strategy_id=body.get("strategy_id"),
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
