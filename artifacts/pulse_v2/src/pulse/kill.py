from __future__ import annotations

"""Event kill chain. Survival v1 is LOCKED — this module scores attacks
but must not emit ROBUST or PASS.
"""

from collections import Counter

from .cost import death_point, true_cost_frac
from .gates import GateLockedError


def attack_event(
    path_mfe: float,
    path_mae: float,
    split: str,
    regime: str,
    n_paths: int,
    *,
    end_ret: float = 0.0,
    decayed: bool = False,
    time_to_mfe: int | None = None,
) -> dict:
    """MFE<=0 is almost never true on a 10-bar high-water mark.

    FALSE_PULSE = no continuation after cost, or immediate decay.
    HARD_FAIL outranks FALSE_PULSE. Graduation remains locked.
    """
    costs = {m: true_cost_frac(mult=m) for m in (1, 2, 3, 5)}
    dp = death_point(path_mfe, costs)
    reasons: list[str] = []
    verdict = "UNTESTED"

    if dp is not None and dp <= 3:
        verdict = "HARD_FAIL"
        reasons.append(f"cost_death_at_x{dp}")
    if regime == "CRISIS_VOL" and path_mfe < abs(path_mae):
        verdict = "HARD_FAIL"
        reasons.append("crisis_not_asymmetric")

    if verdict != "HARD_FAIL":
        two_way = 2.0 * costs[1]
        false = (
            path_mfe <= two_way
            or end_ret <= 0
            or decayed
            or (time_to_mfe is not None and time_to_mfe <= 1 and end_ret < path_mfe * 0.3)
        )
        if false:
            verdict = "FALSE_PULSE"
            reasons.append("no_continuation_after_cost_or_decay")

    if verdict == "UNTESTED":
        if n_paths < 10:
            verdict = "INSUFFICIENT_SAMPLE"
            reasons.append(f"n_paths={n_paths}<10")
        elif split == "UNPROVEN_OOS":
            verdict = "FRAGILE"
            reasons.append("unproven_window_cannot_graduate")
        else:
            verdict = "FRAGILE"
            reasons.append("survival_locked_no_pass")

    return {
        "verdict": verdict,
        "reasons": reasons,
        "cost_death_point": dp,
        "costs": costs,
        "robust_candidate": 0,
    }


def summarize(attacks: list[dict]) -> dict:
    c = Counter(a["verdict"] for a in attacks)
    return {
        "FALSE_PULSE": c.get("FALSE_PULSE", 0),
        "FRAGILE": c.get("FRAGILE", 0),
        "INSUFFICIENT_SAMPLE": c.get("INSUFFICIENT_SAMPLE", 0),
        "HARD_FAIL": c.get("HARD_FAIL", 0),
        "SURVIVING_EVENT": c.get("SURVIVING_EVENT", 0),
        "ROBUST_EVENT": 0,
        "PASS": 0,
    }


def open_survival() -> None:
    raise GateLockedError("Survival_v1", "no CPCV>=10 + frozen hash + true cost matrix")
