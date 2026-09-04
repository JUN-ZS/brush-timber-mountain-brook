from __future__ import annotations


def true_cost_frac(*, spread=0.0003, slip=0.0004, liq_penalty=0.0002, impact=0.0001, mult=1.0) -> float:
    """Model + spread + slippage + liquidity + impact.

    Soft 5bps-only cost is forbidden. mult in {1,2,3,5}.
    Scaled components: slip and impact grow with mult; spread less so.
    """
    if mult not in {1, 2, 3, 5}:
        raise ValueError("cost mult must be 1/2/3/5")
    slip_s = slip * (0.7 + 0.3 * mult)
    impact_s = impact * mult
    liq_s = liq_penalty * (1.0 if mult == 1 else 1.0 + 0.25 * (mult - 1))
    spread_s = spread * (1.0 + 0.1 * (mult - 1))
    return float(spread_s + slip_s + liq_s + impact_s)


def death_point(path_mfe: float, costs: dict[int, float]) -> int | None:
    """Smallest mult where mfe cannot cover 2-way cost."""
    for m in (1, 2, 3, 5):
        if path_mfe <= 2.0 * costs[m]:
            return m
    return None
