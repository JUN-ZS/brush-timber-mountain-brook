"""Intentional destruction tests. Passing the happy path is not enough."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pulse.cost import true_cost_frac
from pulse.event import PulseEvent
from pulse.gates import GateLockedError
from pulse.kill import open_survival
from pulse.radar import LOOKAHEAD, assert_no_lookahead
from pulse.splits import FROZEN_OOS, assign_split, assert_not_frozen
from pulse.engine import PulseV2Engine


def test_2023_is_not_frozen_oos():
    s = assign_split("2024-06-01")
    assert s.name == "UNPROVEN_OOS"
    assert s.may_claim_oos is False


def test_cannot_mint_frozen_oos():
    raised = False
    try:
        assert_not_frozen(FROZEN_OOS)
    except AssertionError:
        raised = True
    assert raised, "FROZEN_OOS must be rejected until lock proof"


def test_lookahead_blocked():
    try:
        assert_no_lookahead(["QQQ", "fwd5"])
        assert False, "lookahead must throw"
    except ValueError as e:
        assert "LOOKAHEAD_FORBIDDEN" in str(e)


def test_survival_locked():
    try:
        open_survival()
        assert False
    except GateLockedError as e:
        assert e.gate == "Survival_v1"


def test_evolution_locked():
    try:
        PulseV2Engine().unlock_evolution()
        assert False
    except GateLockedError as e:
        assert e.gate == "Evolution"


def test_no_fitness_backflow():
    try:
        PulseV2Engine().write_fitness_to_gene()
        assert False
    except GateLockedError as e:
        assert e.gate == "FITNESS_BACKFLOW"


def test_unanswered_event_cannot_enter():
    ev = PulseEvent(
        event_id="X",
        bar_date="2024-01-02",
        split="UNPROVEN_OOS",
        search_level="SINGLE",
        direction="UP",
        skeleton="TEST",
        regime="RISK_ON",
        family_id="TEST|UP|RISK_ON",
        what_changed="price",
        why_unusual="x",
        transition_strength=1.0,
        states={},
        observed_fields=["QQQ"],
        missing_fields=[],
    )
    ok, reason = ev.may_enter()
    assert ok is False
    assert "UNANSWERED" in reason


def test_false_pulse_not_only_mfe_zero():
    from pulse.kill import attack_event

    att = attack_event(0.03, -0.01, "TRAIN", "RISK_ON", 20, end_ret=-0.01, decayed=True, time_to_mfe=1)
    assert att["verdict"] == "FALSE_PULSE"


def test_cost_not_soft_5bps():
    c1 = true_cost_frac(mult=1)
    c3 = true_cost_frac(mult=3)
    c5 = true_cost_frac(mult=5)
    assert c1 > 0.0005
    assert c3 > c1
    assert c5 > c3


def test_protocol_hash_stable():
    a = PulseV2Engine().protocol_hash
    b = PulseV2Engine().protocol_hash
    assert a == b and len(a) == 64


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in tests:
        try:
            fn()
            print("PASS", fn.__name__)
        except Exception as e:
            failed += 1
            print("FAIL", fn.__name__, type(e).__name__, e)
    print(f"{len(tests)-failed}/{len(tests)} ENFORCED")
    raise SystemExit(failed)
