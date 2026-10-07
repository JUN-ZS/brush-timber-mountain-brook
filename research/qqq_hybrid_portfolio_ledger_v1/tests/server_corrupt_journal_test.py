"""Fail-closed corrupt journal: one bad JSONL line blocks the ledger."""
from __future__ import annotations

import json
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server  # noqa: E402


def main() -> None:
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = "http://127.0.0.1:" + str(httpd.server_port)
    server.EVENTS = Path(tempfile.mkdtemp()) / "events.jsonl"

    server.EVENTS.write_text(
        json.dumps({"type": "CASHFLOW", "id": "ok1", "timestamp": "2026-10-01T00:00:00Z", "amount": 1})
        + "\n{not-valid-json\n"
        + json.dumps({"type": "CASHFLOW", "id": "ok2", "timestamp": "2026-10-02T00:00:00Z", "amount": 1})
        + "\n",
        encoding="utf-8",
    )

    try:
        server.read_events()
        raise AssertionError("read_events should raise CorruptJournalError")
    except server.CorruptJournalError as exc:
        assert "CORRUPT_JOURNAL" in str(exc)

    try:
        urllib.request.urlopen(base + "/api/events", timeout=5)
        raise AssertionError("/api/events should return 409")
    except urllib.error.HTTPError as exc:
        assert exc.code == 409
        body = json.load(exc)
        assert body["ok"] is False
        assert body["blocked"] is True
        assert body["status"] == "CORRUPT_JOURNAL"
        assert body["events"] == []





    # Boundary validation must reject unstable identifiers and silent multiplier fallback.
    for bad_event, expected in [
        (
            {"type": "CASHFLOW", "timestamp": "2026-10-01T00:00:00Z", "amount": 1},
            "event id is required",
        ),
        (
            {"type": "FILL", "id": "bad-mult", "timestamp": "2026-10-01T00:00:00Z",
             "symbol": "QQQ-OPT", "assetType": "OPTION", "side": "BUY",
             "quantity": 1, "price": 2, "multiplier": 0},
            "multiplier must be > 0",
        ),
    ]:
        try:
            server.validate_event(bad_event)
            raise AssertionError("invalid event should be rejected")
        except ValueError as exc:
            assert expected in str(exc)

    # Valid JSON but invalid event semantics must also block.
    server.EVENTS.write_text(
        json.dumps({"type": "FILL", "id": "bad-semantic", "timestamp": "2026-10-01T00:00:00",
                    "symbol": "QQQ", "assetType": "EQUITY", "side": "BUY",
                    "quantity": 1, "price": 100, "fees": 0}) + "\n",
        encoding="utf-8",
    )
    try:
        server.read_events()
        raise AssertionError("semantically invalid journal event should block")
    except server.CorruptJournalError as exc:
        assert "CORRUPT_JOURNAL" in str(exc)
        assert "timezone" in str(exc)

    httpd.shutdown()
    print("SERVER CORRUPT JOURNAL TEST: PASS")


if __name__ == "__main__":
    main()
