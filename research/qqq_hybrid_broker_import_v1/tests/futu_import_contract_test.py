"""Read-only Futu importer helper contract tests; no broker connection is made."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import futu_import  # noqa: E402


def main() -> None:
    assert list(futu_import.range_chunks(date(2026, 1, 1), date(2026, 3, 31), 90)) == [
        (date(2026, 1, 1), date(2026, 3, 31))
    ]

    chunks = list(futu_import.range_chunks(date(2026, 1, 1), date(2026, 4, 1), 90))
    assert chunks[0] == (date(2026, 1, 1), date(2026, 3, 31))
    assert chunks[1] == (date(2026, 4, 1), date(2026, 4, 1))

    # Explicit IANA timezone conversion keeps DST correct.
    from zoneinfo import ZoneInfo
    before_dst = futu_import.iso_from_futu_time("2026-03-07 10:00:00", ZoneInfo("America/New_York"))
    after_dst = futu_import.iso_from_futu_time("2026-03-09 10:00:00", ZoneInfo("America/New_York"))
    assert before_dst == "2026-03-07T15:00:00Z", before_dst
    assert after_dst == "2026-03-09T14:00:00Z", after_dst

    # The module must expose a dry CLI contract without invoking order APIs.
    parser = futu_import.build_parser()
    args = parser.parse_args([
        "--start", "2026-10-01",
        "--end", "2026-10-02",
        "--market", "US",
        "--timezone", "America/New_York",
        "--acc-id", "123"
    ])
    assert args.market == "US"
    assert args.acc_id == 123
    assert args.with_cashflows is False

    print("FUTU IMPORT CONTRACT TEST: PASS")


if __name__ == "__main__":
    main()
