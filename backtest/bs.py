"""Black-Scholes used only for DERIVED scenario marks. Never labelled LIVE."""

from __future__ import annotations

import math
from typing import Optional

SQRT_2PI = math.sqrt(2.0 * math.pi)


def n_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / SQRT_2PI


def n_cdf(x: float) -> float:
    a1, a2, a3, a4, a5, p = 0.254829592, -0.284496736, 1.421413741, -1.453152027, 1.061405429, 0.3275911
    sign = -1.0 if x < 0 else 1.0
    absv = abs(x) / math.sqrt(2.0)
    t = 1.0 / (1.0 + p * absv)
    y = 1.0 - ((((a5 * t + a4) * t + a3) * t + a2) * t + a1) * t * math.exp(-absv * absv)
    return 0.5 * (1.0 + sign * y)


def norm_iv(iv: Optional[float], fallback: Optional[float] = None) -> Optional[float]:
    if iv is None or not math.isfinite(iv) or iv <= 0:
        return fallback
    v = iv / 100.0 if iv > 3 else iv
    return min(max(v, 0.03), 3.5)


def intrinsic(spot: float, strike: float, right: str) -> float:
    if right == "CALL":
        return max(spot - strike, 0.0)
    return max(strike - spot, 0.0)


def bs_price(spot: float, strike: float, t_years: float, iv: float, right: str = "PUT", rate: float = 0.04) -> float:
    sig = norm_iv(iv, 0.25)
    if sig is None or spot <= 0 or strike <= 0 or t_years <= 1 / 365 / 24:
        return intrinsic(spot, strike, right)
    sqrt_t = math.sqrt(t_years)
    d1 = (math.log(spot / strike) + (rate + 0.5 * sig * sig) * t_years) / (sig * sqrt_t)
    d2 = d1 - sig * sqrt_t
    if right == "CALL":
        return spot * n_cdf(d1) - strike * math.exp(-rate * t_years) * n_cdf(d2)
    return strike * math.exp(-rate * t_years) * n_cdf(-d2) - spot * n_cdf(-d1)


def iv_shock_for_move(spot_shock: float) -> float:
    if spot_shock >= 0:
        return max(0.62, 1 - abs(spot_shock) * 1.5)
    mag = abs(spot_shock)
    if mag < 0.04:
        return 1 + mag * 1.2
    if mag < 0.1:
        return 1.05 + (mag - 0.04) * 2.2
    return min(2.05, 1.18 + (mag - 0.1) * 3.4)
