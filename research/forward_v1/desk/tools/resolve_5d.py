#!/usr/bin/env python3
"""Desk resolve_5d — thin entry for MINIMUM RUN V1.2 (horizons=5 only by default).

Delegates to live_forward_resolver with real stock OHLC + QQQ OHLC validation.
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path


def main() -> None:
    here = Path(__file__).resolve().parent
    target = here / "live_forward_resolver.py"
    # Default to 5D-only unless user already passed --horizons
    if "--horizons" not in sys.argv:
        sys.argv.extend(["--horizons", "5"])
    sys.argv[0] = str(target)
    runpy.run_path(str(target), run_name="__main__")


if __name__ == "__main__":
    main()
