"""Journal concurrency and duplicate-id integrity regression."""
from __future__ import annotations

import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server  # noqa: E402


def main() -> None:
    server.EVENTS = Path(tempfile.mkdtemp()) / "events.jsonl"
    event = {
        "type": "FILL",
        "id": "RACE-1",
        "timestamp": "2026-10-01T00:00:00Z",
        "symbol": "QQQ",
        "assetType": "EQUITY",
        "side": "BUY",
        "quantity": 1,
        "price": 100,
        "fees": 0,
    }

    def write_once():
        return server.append_events([event])

    with ThreadPoolExecutor(max_workers=16) as pool:
        results = list(pool.map(lambda _: write_once(), range(64)))

    added = sum(x[0] for x in results)
    duplicates = sum(x[1] for x in results)
    assert added == 1, (added, duplicates)
    assert duplicates == 63, (added, duplicates)
    saved = server.read_events()
    assert len(saved) == 1
    assert saved[0]["id"] == "RACE-1"

    identical = server.append_events([event])
    assert identical == (0, 1)

    conflict = dict(event)
    conflict["price"] = 101
    try:
        server.append_events([conflict])
        raise AssertionError("duplicate id with different content must block")
    except server.DuplicateEventIdConflict as exc:
        assert "DUPLICATE_EVENT_ID_CONFLICT" in str(exc)

    assert server.read_events()[0]["price"] == 100
    print("SERVER JOURNAL INTEGRITY TEST: PASS")


if __name__ == "__main__":
    main()
