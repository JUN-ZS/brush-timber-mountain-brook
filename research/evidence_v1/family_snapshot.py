from __future__ import annotations

from dataclasses import asdict
from typing import Any, Iterable

from ..live_hedge_v1.engine import Contract, select_far


FAR_DTE = (90, 120, 180)
FAR_DELTA = (0.05, 0.08, 0.10)
NEAR_DTE = 30
COVERAGE = 1.50
LONG_DELTA = 0.50
POLICIES = (
    "TP50_IMMEDIATE",
    "TP75_IMMEDIATE",
    "TP100_IMMEDIATE",
    "TRAIL20_IMMEDIATE",
    "TP50_ON_RISK",
    "TP75_ON_RISK",
    "TRAIL20_ON_RISK",
    "TP75_COOLDOWN3",
)


def _pct(v: float | None) -> float | None:
    return None if v is None else round(float(v) * 100.0, 6)


def build_family_snapshot(
    contracts: Iterable[Contract],
    *,
    spot: float,
    signal_active: bool,
    campaign_active: bool,
    active_far_code: str | None = None,
) -> dict[str, Any]:
    """Observe all 72 locked family members without selecting a winner.

    This is an observation vector, not an execution recommendation. Policies
    are deliberately retained even when their entry action is identical so
    the future record can resolve them independently.
    """
    contracts = list(contracts)
    rows: list[dict[str, Any]] = []

    for dte_target in FAR_DTE:
        for delta_target in FAR_DELTA:
            far = select_far(contracts, spot, dte_target, delta_target)
            for policy in POLICIES:
                family_id = f"FAR{dte_target}_D{delta_target:.2f}_NEAR30_C1.50_{policy}"
                if far is None:
                    rows.append({
                        "family_id": family_id,
                        "far_dte_target": dte_target,
                        "far_delta_target": delta_target,
                        "near_dte": NEAR_DTE,
                        "coverage": COVERAGE,
                        "policy": policy,
                        "status": "UNAVAILABLE",
                        "signal_active": signal_active,
                        "campaign_active": campaign_active,
                        "live_far_reference_match": False,
                        "live_policy_mapping": "UNMAPPED",
                        "far_code": None,
                        "far_dte": None,
                        "far_delta": None,
                        "far_strike": None,
                        "far_bid": None,
                        "far_ask": None,
                        "far_source": "LIVE_QUOTE_CHAIN" if contracts else "MISSING",
                    })
                    continue

                rows.append({
                    "family_id": family_id,
                    "far_dte_target": dte_target,
                    "far_delta_target": delta_target,
                    "near_dte": NEAR_DTE,
                    "coverage": COVERAGE,
                    "policy": policy,
                    "status": "AVAILABLE",
                    "signal_active": signal_active,
                    "campaign_active": campaign_active,
                    "active_family": active_far_code == far.code,
                    "far_code": far.code,
                    "far_dte": far.dte,
                    "far_delta": None if far.delta is None else abs(float(far.delta)),
                    "far_strike": far.strike,
                    "far_bid": far.bid,
                    "far_ask": far.ask,
                    "far_spread_pct": (
                        None
                        if far.bid is None or far.ask is None or far.bid <= 0
                        else _pct((far.ask - far.bid) / ((far.ask + far.bid) / 2))
                    ),
                    "far_source": "LIVE_QUOTE_CHAIN",
                })

    return {
        "schema": "V22_FAMILY_OBSERVATION.v1",
        "config_count": len(rows),
        "family_count_expected": 72,
        "signal_active": signal_active,
        "campaign_active": campaign_active,
        "live_policy_mapping": "UNMAPPED",
        "near_dte": NEAR_DTE,
        "coverage": COVERAGE,
        "rows": rows,
    }
