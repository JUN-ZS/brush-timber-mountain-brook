from __future__ import annotations

from collections import defaultdict


def family_id(skeleton: str, direction: str, regime: str) -> str:
    return f"{skeleton}|{direction}|{regime}"


def collapse(events: list[dict]) -> dict:
    """Same skeleton + direction + regime = one vote."""
    buckets: dict[str, list[dict]] = defaultdict(list)
    for e in events:
        buckets[e["family_id"]].append(e)
    return {
        "n_events": len(events),
        "n_families": len(buckets),
        "families": {
            k: {"n": len(v), "vote": 1, "members": [x["event_id"] for x in v]}
            for k, v in buckets.items()
        },
    }
