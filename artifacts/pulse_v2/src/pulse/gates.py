from __future__ import annotations


class GateLockedError(RuntimeError):
    def __init__(self, gate: str, detail: str = "") -> None:
        self.gate = gate
        super().__init__(f"GATE_LOCKED:{gate} {detail}".strip())


LOCKS = {
    "Evolution": True,
    "Capital": True,
    "FINAL_OOS": True,
    "LIVE": True,
    "Survival_v1": True,
}


def assert_unlocked(gate: str) -> None:
    if LOCKS.get(gate, True):
        raise GateLockedError(gate, "write this first, do not open with compute")


def deny_fitness_backflow(target: str) -> None:
    raise GateLockedError(
        "FITNESS_BACKFLOW",
        f"shadow/journal must not write {target}",
    )
