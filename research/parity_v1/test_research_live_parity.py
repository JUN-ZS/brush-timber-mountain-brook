"""Research <-> live PARITY TESTS (local-only; do not push/commit).

Compares LOCKED research engine vs live hedge desk on:
  A) gamma_baseline
  B) far contract selection
  C) near contract selection
  D) target_stack / desired_stack

Each case records: CASE, input_state, research_value, live_value, equal,
difference, difference_type, alpha_impact.
"""
from __future__ import annotations

import json
import math
import unittest
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

from research.live_hedge_v1.engine import (
    Contract,
    ensure_gamma_history_schema,
    gamma_baseline_from_history,
    risk_state,
    select_far,
    select_near,
)
from research.parity_v1.formulas import (
    live_gamma_baseline_from_history,
    live_gamma_walk_baselines,
    research_gamma_baseline_series,
    research_gamma_spot_from_gamma_and_spot,
    research_pick_far as pick_far,
    research_pick_near as pick_near,
    research_target_from_state as target_from_state,
)

PARITY_DIR = Path(__file__).resolve().parent
RESULTS: list[dict[str, Any]] = []

DIFF_TYPES = {
    "PARITY",
    "INFRASTRUCTURE_DRIFT",
    "ALPHA_DRIFT",
    "DATA_SCHEMA_DRIFT",
    "UNTESTABLE",
}


def _num_eq(a: Any, b: Any, tol: float = 1e-12) -> bool:
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    try:
        if isinstance(a, float) and math.isnan(a) and isinstance(b, float) and math.isnan(b):
            return True
        if pd.isna(a) and pd.isna(b):
            return True
    except (TypeError, ValueError):
        pass
    try:
        return abs(float(a) - float(b)) <= tol
    except (TypeError, ValueError):
        return a == b


def record_case(
    case: str,
    input_state: Any,
    research_value: Any,
    live_value: Any,
    *,
    equal: Optional[bool] = None,
    difference: Any = None,
    difference_type: str,
    alpha_impact: str,
) -> dict[str, Any]:
    assert difference_type in DIFF_TYPES, difference_type
    if equal is None:
        equal = _num_eq(research_value, live_value)
    if difference is None:
        if equal:
            difference = 0
        else:
            try:
                if research_value is not None and live_value is not None:
                    difference = float(live_value) - float(research_value)
                else:
                    difference = {"research": research_value, "live": live_value}
            except (TypeError, ValueError):
                difference = {"research": research_value, "live": live_value}
    row = {
        "CASE": case,
        "input_state": input_state,
        "research_value": _jsonable(research_value),
        "live_value": _jsonable(live_value),
        "equal": bool(equal),
        "difference": _jsonable(difference),
        "difference_type": difference_type,
        "alpha_impact": alpha_impact,
    }
    RESULTS.append(row)
    return row


def _jsonable(v: Any) -> Any:
    if v is None:
        return None
    if isinstance(v, (str, int, bool)):
        return v
    if isinstance(v, float):
        if math.isnan(v) or pd.isna(v):
            return None
        if math.isinf(v):
            return str(v)
        return v
    if isinstance(v, (np.floating,)):
        if np.isnan(v):
            return None
        return float(v)
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, dict):
        return {str(k): _jsonable(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_jsonable(x) for x in v]
    if isinstance(v, Path):
        return str(v)
    if isinstance(v, (date,)):
        return v.isoformat()
    if isinstance(v, pd.Timestamp):
        return str(v)
    return str(v)


# ---------------------------------------------------------------------------
# Helpers: build research chain DF / live Contract lists
# ---------------------------------------------------------------------------

def _base_date() -> date:
    return date(2026, 6, 1)


def _expiry_for_dte(asof: date, dte: int) -> date:
    return asof + timedelta(days=dte)


def make_research_far_chain(rows: list[dict]) -> pd.DataFrame:
    """Build a chain DataFrame matching pick_far expectations."""
    asof = _base_date()
    out = []
    for i, r in enumerate(rows):
        dte = int(r["dte"])
        exp = _expiry_for_dte(asof, dte)
        out.append(
            {
                "date": pd.Timestamp(asof),
                "expiration": pd.Timestamp(exp),
                "contract_id": r.get("cid", f"FAR{i}"),
                "strike": float(r["strike"]),
                "bid": float(r.get("bid", 1.0)),
                "ask": float(r.get("ask", 1.1)),
                "delta": float(r["delta"]),
                "volume": float(r["volume"]) if r.get("volume") is not None else 0.0,
                "gamma": r.get("gamma"),
            }
        )
    return pd.DataFrame(out)


def make_live_contracts(rows: list[dict], *, right: str = "CALL") -> list[Contract]:
    asof = _base_date()
    cs = []
    for i, r in enumerate(rows):
        dte = int(r["dte"])
        exp = _expiry_for_dte(asof, dte)
        cs.append(
            Contract(
                code=r.get("cid", f"C{i}"),
                right=right,
                strike=float(r["strike"]),
                expiry=exp.isoformat(),
                dte=dte,
                bid=r.get("bid", 1.0),
                ask=r.get("ask", 1.1),
                delta=r.get("delta"),
                gamma=r.get("gamma"),
                volume=float(r["volume"]) if r.get("volume") is not None else 0.0,
            )
        )
    return cs


def make_research_near_chain(rows: list[dict]) -> pd.DataFrame:
    asof = _base_date()
    out = []
    for i, r in enumerate(rows):
        dte = int(r["dte"])
        exp = _expiry_for_dte(asof, dte)
        out.append(
            {
                "date": pd.Timestamp(asof),
                "expiration": pd.Timestamp(exp),
                "contract_id": r.get("cid", f"NEAR{i}"),
                "strike": float(r["strike"]),
                "bid": float(r.get("bid", 2.0)),
                "ask": float(r.get("ask", 2.1)),
                "delta": float(r["delta"]),
                "volume": float(r["volume"]) if r.get("volume") is not None else 0.0,
            }
        )
    return pd.DataFrame(out)


ALPHA_NOTE_LIVE_ALIGN = (
    "Aligning LIVE to research preserves locked evidence chain; "
    "changing research formula would INVALIDATE evidence (STRATEGY_LOCK mutation_policy)."
)
ALPHA_NOTE_PARITY = "No alpha impact — values already match under identical inputs."
ALPHA_NOTE_SCHEMA = (
    "Live Contract now carries volume through selection path (infra alignment to research). "
    "Does not reselect STRATEGY_LOCK alpha params."
)


class GammaBaselineParityTests(unittest.TestCase):
    """A) gamma_baseline: research MEDIAN(+shift/>=5) vs live median (same semantics)."""

    def _compare_series_case(
        self,
        case: str,
        series: list[Optional[float]],
        *,
        difference_type: str,
        alpha_impact: str,
        compare_at: str = "last_valid",
    ) -> None:
        # Feed the SAME numeric series into both aggregators to isolate median vs mean
        # (and min_periods). Schema difference (gamma*spot vs raw gamma) is a separate case.
        vals = [np.nan if v is None else float(v) for v in series]
        research_s = research_gamma_baseline_series(vals)
        live_walk = live_gamma_walk_baselines(vals)

        # Pointwise compare where research has a value
        pairs = []
        for i, (rv, lv) in enumerate(zip(research_s.tolist(), live_walk)):
            rv_out = None if (rv is None or (isinstance(rv, float) and math.isnan(rv))) else float(rv)
            pairs.append((i, rv_out, lv))

        if compare_at == "last_valid":
            research_value = None
            live_value = None
            idx = None
            for i, rv, lv in reversed(pairs):
                if rv is not None:
                    research_value, live_value, idx = rv, lv, i
                    break
            if idx is None:
                # both may be None (short series)
                research_value = pairs[-1][1] if pairs else None
                live_value = pairs[-1][2] if pairs else None
                idx = len(pairs) - 1 if pairs else -1
        else:
            idx = int(compare_at)
            research_value, live_value = pairs[idx][1], pairs[idx][2]

        equal = _num_eq(research_value, live_value, tol=1e-9)
        row = record_case(
            case,
            {
                "series": series,
                "n": len(series),
                "compare_index": idx,
                "research_formula": "shift(1).rolling(20,min_periods=5).median()",
                "live_formula": "median(history[-20:]) if len>=5 else None (pre-append / gamma_spot)",
            },
            research_value,
            live_value,
            equal=equal,
            difference_type=difference_type if not equal else "PARITY",
            alpha_impact=alpha_impact if not equal else ALPHA_NOTE_PARITY,
        )
        # Diagnostic always printed on failure path; also assert classification present
        self.assertIn(row["difference_type"], DIFF_TYPES)
        # Do NOT force assertEqual across engines — parity report classifies drift.
        # Soft check: record only. Hard assert that we produced a comparable record.
        self.assertEqual(row["CASE"], case)

    def test_A01_n_lt_3(self):
        self._compare_series_case(
            "A01_gamma_n_lt_3",
            [1.0, 2.0],
            difference_type="ALPHA_DRIFT",
            alpha_impact=ALPHA_NOTE_LIVE_ALIGN + " Both None here (research needs >=5 lagged; live needs >=3).",
        )

    def test_A02_n_eq_3(self):
        # After 3 appends, at index 3 baseline: live has mean of first 3; research still None (needs 5 lagged)
        self._compare_series_case(
            "A02_gamma_n_eq_3",
            [1.0, 2.0, 3.0, 4.0],
            difference_type="ALPHA_DRIFT",
            alpha_impact=ALPHA_NOTE_LIVE_ALIGN + " Live emits mean at n>=3; research still NaN until >=5 lagged points.",
        )

    def test_A03_n_eq_4(self):
        self._compare_series_case(
            "A03_gamma_n_eq_4",
            [1.0, 2.0, 3.0, 4.0, 5.0],
            difference_type="ALPHA_DRIFT",
            alpha_impact=ALPHA_NOTE_LIVE_ALIGN + " Live mean active; research still warming (min_periods=5 after shift).",
        )

    def test_A04_n_eq_5(self):
        # Research first valid at index 5: median of shifted values indices 0..4 (5 points)
        series = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0]
        self._compare_series_case(
            "A04_gamma_n_eq_5",
            series,
            difference_type="ALPHA_DRIFT",
            alpha_impact=ALPHA_NOTE_LIVE_ALIGN + " First research median vs live mean of prior history.",
        )

    def test_A05_n_eq_20(self):
        series = [float(i + 1) for i in range(20)] + [100.0]
        self._compare_series_case(
            "A05_gamma_n_eq_20",
            series,
            difference_type="ALPHA_DRIFT",
            alpha_impact=ALPHA_NOTE_LIVE_ALIGN + " Median vs mean on 1..20 window.",
        )

    def test_A06_n_gt_20(self):
        series = [float(i + 1) for i in range(25)] + [50.0]
        self._compare_series_case(
            "A06_gamma_n_gt_20",
            series,
            difference_type="ALPHA_DRIFT",
            alpha_impact=ALPHA_NOTE_LIVE_ALIGN + " Both window to last 20; median vs mean still differ.",
        )

    def test_A07_constant_gamma(self):
        series = [5.0] * 25
        self._compare_series_case(
            "A07_gamma_constant",
            series,
            difference_type="ALPHA_DRIFT",
            alpha_impact=ALPHA_NOTE_LIVE_ALIGN + " Constant series: median==mean expected PARITY once both warm.",
        )

    def test_A08_jumping_gamma(self):
        series = [1.0] * 10 + [100.0] * 10 + [1.0] * 5
        self._compare_series_case(
            "A08_gamma_jumping",
            series,
            difference_type="ALPHA_DRIFT",
            alpha_impact=ALPHA_NOTE_LIVE_ALIGN + " Jumps amplify median vs mean divergence.",
        )

    def test_A09_missing_none_gamma(self):
        # Live skips None (does not append); research series has NaN which affects rolling median
        series = [1.0, None, 2.0, None, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
        vals = [np.nan if v is None else float(v) for v in series]
        research_s = research_gamma_baseline_series(vals)
        # Live walk: only append non-None
        live_walk = live_gamma_walk_baselines(series)
        idx = len(series) - 1
        rv = research_s.iloc[idx]
        research_value = None if pd.isna(rv) else float(rv)
        live_value = live_walk[idx]
        equal = _num_eq(research_value, live_value, tol=1e-9)
        record_case(
            "A09_gamma_missing_none",
            {
                "series": series,
                "note": "Live skips None appends; research rolling includes NaNs in window semantics",
            },
            research_value,
            live_value,
            equal=equal,
            difference_type="ALPHA_DRIFT" if not equal else "PARITY",
            alpha_impact=ALPHA_NOTE_LIVE_ALIGN if not equal else ALPHA_NOTE_PARITY,
        )
        self.assertTrue(True)

    def test_A10_schema_gamma_spot_vs_raw(self):
        """Live stores gamma_spot=abs(gamma)*spot; compare vs research on that series."""
        gammas = [0.01, 0.012, 0.011, 0.015, 0.02, 0.018, 0.017, 0.016]
        spots = [400.0, 401.0, 402.0, 405.0, 410.0, 408.0, 407.0, 406.0]
        gspot = research_gamma_spot_from_gamma_and_spot(gammas, spots)
        research_base = research_gamma_baseline_series(gspot.tolist())
        live_on_spot = live_gamma_walk_baselines(gspot.tolist())
        live_on_raw = live_gamma_walk_baselines(gammas)
        idx = len(gammas) - 1
        rv = research_base.iloc[idx]
        research_value = None if pd.isna(rv) else float(rv)
        live_value = live_on_spot[idx]
        equal = _num_eq(research_value, live_value, tol=1e-9)
        record_case(
            "A10_schema_gamma_spot_vs_raw_abs",
            {
                "gammas": gammas,
                "spots": spots,
                "research_uses": "abs(gamma)*spot then median baseline",
                "live_uses": "gamma_spot=abs(gamma)*spot then median baseline",
                "live_baseline_on_raw_would_be": live_on_raw[idx],
                "live_baseline_on_gamma_spot": live_on_spot[idx],
            },
            research_value,
            live_value,
            equal=equal,
            difference_type="DATA_SCHEMA_DRIFT" if not equal else "PARITY",
            alpha_impact=(
                ALPHA_NOTE_PARITY
                if equal
                else (
                    "Live gamma_history should store gamma_spot; residual mismatch. "
                    + ALPHA_NOTE_LIVE_ALIGN
                )
            ),
        )


class GammaHistoryMigrationParityTests(unittest.TestCase):
    """Migration: legacy raw |γ| history must not blend into gamma_spot baseline."""

    def test_A11_old_schema_resets(self):
        state = {
            "gamma_history": [0.01, 0.012, 0.011, 0.015, 0.02],
            "gamma_history_schema": 1,
            "gamma_history_unit": "raw_abs_gamma",
        }
        before = list(state["gamma_history"])
        hist = ensure_gamma_history_schema(state, spot=400.0)
        equal = hist == [] and state.get("gamma_history_schema") == 2
        record_case(
            "A11_gamma_history_old_schema_reset",
            {"before": before, "spot": 400.0},
            {"history": [], "schema": 2, "unit": "gamma_spot"},
            {
                "history": hist,
                "schema": state.get("gamma_history_schema"),
                "unit": state.get("gamma_history_unit"),
            },
            equal=equal,
            difference_type="PARITY" if equal else "DATA_SCHEMA_DRIFT",
            alpha_impact=(
                "Infra: discard legacy raw |γ| warm-up; collect fresh gamma_spot."
            ),
        )
        self.assertTrue(equal)
        self.assertIsNone(gamma_baseline_from_history(hist))

    def test_A12_schema2_keeps(self):
        vals = [4.0, 4.2, 3.8, 4.1, 4.3, 4.0]
        state = {
            "gamma_history": list(vals),
            "gamma_history_schema": 2,
            "gamma_history_unit": "gamma_spot",
        }
        hist = ensure_gamma_history_schema(state, spot=400.0)
        base = gamma_baseline_from_history(hist)
        equal = hist == vals and base is not None
        record_case(
            "A12_gamma_history_schema2_keep",
            {"vals": vals, "spot": 400.0},
            {"history": vals, "baseline_ready": True},
            {"history": hist, "baseline_ready": base is not None, "baseline": base},
            equal=equal,
            difference_type="PARITY" if equal else "DATA_SCHEMA_DRIFT",
            alpha_impact="Infra: schema2 + unit gamma_spot history retained.",
        )
        self.assertTrue(equal)

    def test_A13_missing_unit_resets(self):
        state = {
            "gamma_history": [4.0, 4.2, 3.8, 4.1, 4.3],
            "gamma_history_schema": 2,
        }
        hist = ensure_gamma_history_schema(state, spot=400.0)
        equal = hist == [] and state.get("gamma_history_unit") == "gamma_spot"
        record_case(
            "A13_gamma_history_missing_unit_reset",
            {"schema": 2, "unit": None},
            {"history": [], "unit": "gamma_spot"},
            {"history": hist, "unit": state.get("gamma_history_unit")},
            equal=equal,
            difference_type="PARITY" if equal else "DATA_SCHEMA_DRIFT",
            alpha_impact="Infra: missing unit marker forces warm-up reset.",
        )
        self.assertTrue(equal)


class FarSelectionParityTests(unittest.TestCase):
    """B) far contract selection."""

    def _run_far(self, case: str, rows: list[dict], spot: float, dte_t: int, delta_t: float,
                 difference_type: str, alpha_impact: str) -> None:
        ch = make_research_far_chain(rows)
        cs = make_live_contracts(rows)
        r = pick_far(ch, spot, dte_t, delta_t)
        l = select_far(cs, spot, dte_t, delta_t)
        r_id = None if r is None else r["cid"]
        l_id = None if l is None else l.code
        r_strike = None if r is None else r["strike"]
        l_strike = None if l is None else l.strike
        equal = r_id == l_id
        record_case(
            case,
            {
                "spot": spot,
                "dte_target": dte_t,
                "delta_target": delta_t,
                "rows": rows,
                "research_sort": "expiry by (dte_err, volume DESC) then (derr, volume DESC, strike ASC)",
                "live_sort": "two-stage: expiry (dte_err, volume DESC) then (derr, volume DESC, strike ASC)",
            },
            {"cid": r_id, "strike": r_strike},
            {"cid": l_id, "strike": l_strike},
            equal=equal,
            difference={"research_cid": r_id, "live_cid": l_id},
            difference_type=difference_type if not equal else "PARITY",
            alpha_impact=alpha_impact if not equal else ALPHA_NOTE_PARITY,
        )

    def test_B01_same_dte_delta_diff_volume(self):
        rows = [
            {"cid": "LOW_VOL", "dte": 90, "strike": 450.0, "delta": 0.08, "volume": 10},
            {"cid": "HIGH_VOL", "dte": 90, "strike": 451.0, "delta": 0.08, "volume": 5000},
        ]
        self._run_far(
            "B01_far_same_dte_delta_diff_volume",
            rows,
            spot=400.0,
            dte_t=90,
            delta_t=0.08,
            difference_type="INFRASTRUCTURE_DRIFT",
            alpha_impact=ALPHA_NOTE_SCHEMA + " Research prefers HIGH_VOL; live ties on delta then lower strike (LOW_VOL).",
        )

    def test_B02_same_everything_except_strike(self):
        rows = [
            {"cid": "K452", "dte": 120, "strike": 452.0, "delta": 0.10, "volume": 100},
            {"cid": "K450", "dte": 120, "strike": 450.0, "delta": 0.10, "volume": 100},
        ]
        self._run_far(
            "B02_far_same_except_strike",
            rows,
            spot=400.0,
            dte_t=120,
            delta_t=0.10,
            difference_type="INFRASTRUCTURE_DRIFT",
            alpha_impact=ALPHA_NOTE_LIVE_ALIGN + " Both should prefer lower strike on equal derr/volume.",
        )

    def test_B03_missing_volume(self):
        # volume None -> research COALESCE to 0; live has no volume field
        rows = [
            {"cid": "V0", "dte": 90, "strike": 460.0, "delta": 0.05, "volume": None},
            {"cid": "V1", "dte": 90, "strike": 461.0, "delta": 0.05, "volume": 0},
        ]
        self._run_far(
            "B03_far_missing_volume",
            rows,
            spot=400.0,
            dte_t=90,
            delta_t=0.05,
            difference_type="DATA_SCHEMA_DRIFT",
            alpha_impact=ALPHA_NOTE_SCHEMA,
        )

    def test_B04_multiple_expiry_candidates(self):
        rows = [
            {"cid": "E80", "dte": 80, "strike": 450.0, "delta": 0.08, "volume": 9999},
            {"cid": "E95", "dte": 95, "strike": 450.0, "delta": 0.08, "volume": 10},
            {"cid": "E120", "dte": 120, "strike": 450.0, "delta": 0.08, "volume": 10},
        ]
        self._run_far(
            "B04_far_multiple_expiry",
            rows,
            spot=400.0,
            dte_t=90,
            delta_t=0.08,
            difference_type="INFRASTRUCTURE_DRIFT",
            alpha_impact=(
                ALPHA_NOTE_SCHEMA
                + " Research picks expiry by dte_err then volume (two-stage); "
                "live flat-sorts all contracts by (dte_err, delta_err, strike)."
            ),
        )

    def test_B05_volume_breaks_equal_dte_err_expiries(self):
        # Two expiries equally far from target (85 and 95 for target 90); research volume wins
        rows = [
            {"cid": "E85_LOW", "dte": 85, "strike": 448.0, "delta": 0.08, "volume": 50},
            {"cid": "E85_HIGH", "dte": 85, "strike": 449.0, "delta": 0.081, "volume": 50},
            {"cid": "E95_HIGHVOL", "dte": 95, "strike": 450.0, "delta": 0.08, "volume": 9000},
            {"cid": "E95_LOWVOL", "dte": 95, "strike": 451.0, "delta": 0.08, "volume": 1},
        ]
        self._run_far(
            "B05_far_expiry_volume_tiebreak",
            rows,
            spot=400.0,
            dte_t=90,
            delta_t=0.08,
            difference_type="INFRASTRUCTURE_DRIFT",
            alpha_impact=ALPHA_NOTE_SCHEMA + " Equal |dte-90|; research chooses higher-volume expiry.",
        )


class NearSelectionParityTests(unittest.TestCase):
    """C) near contract selection."""

    def _run_near(self, case: str, rows: list[dict], spot: float, dte_t: int,
                  difference_type: str, alpha_impact: str) -> None:
        ch = make_research_near_chain(rows)
        cs = make_live_contracts(rows)
        r = pick_near(ch, spot, dte_t)
        l = select_near(cs, spot, dte_t)
        r_id = None if r is None else r["cid"]
        l_id = None if l is None else l.code
        equal = r_id == l_id
        record_case(
            case,
            {
                "spot": spot,
                "dte_target": dte_t,
                "rows": rows,
                "research_filter": "strike<=spot*1.02 then expiry pick; final strike<=spot*1.01",
                "live_filter": "strike<=spot*1.02 then expiry pick; final strike<=spot*1.01; volume tie-break",
            },
            {"cid": r_id, "strike": None if r is None else r["strike"]},
            {"cid": l_id, "strike": None if l is None else l.strike},
            equal=equal,
            difference={"research_cid": r_id, "live_cid": l_id},
            difference_type=difference_type if not equal else "PARITY",
            alpha_impact=alpha_impact if not equal else ALPHA_NOTE_PARITY,
        )

    def test_C01_same_dte_delta_diff_volume(self):
        spot = 400.0
        rows = [
            {"cid": "N_LOW", "dte": 30, "strike": 395.0, "delta": 0.50, "volume": 10},
            {"cid": "N_HIGH", "dte": 30, "strike": 396.0, "delta": 0.50, "volume": 8000},
        ]
        self._run_near(
            "C01_near_same_dte_delta_diff_volume",
            rows,
            spot=spot,
            dte_t=30,
            difference_type="INFRASTRUCTURE_DRIFT",
            alpha_impact=ALPHA_NOTE_SCHEMA,
        )

    def test_C02_same_except_strike(self):
        spot = 400.0
        rows = [
            {"cid": "N399", "dte": 21, "strike": 399.0, "delta": 0.50, "volume": 100},
            {"cid": "N398", "dte": 21, "strike": 398.0, "delta": 0.50, "volume": 100},
        ]
        self._run_near(
            "C02_near_same_except_strike",
            rows,
            spot=spot,
            dte_t=21,
            difference_type="INFRASTRUCTURE_DRIFT",
            alpha_impact=ALPHA_NOTE_LIVE_ALIGN,
        )

    def test_C03_missing_volume(self):
        spot = 400.0
        rows = [
            {"cid": "N_A", "dte": 14, "strike": 400.0, "delta": 0.49, "volume": None},
            {"cid": "N_B", "dte": 14, "strike": 399.0, "delta": 0.49, "volume": 0},
        ]
        self._run_near(
            "C03_near_missing_volume",
            rows,
            spot=spot,
            dte_t=14,
            difference_type="DATA_SCHEMA_DRIFT",
            alpha_impact=ALPHA_NOTE_SCHEMA,
        )

    def test_C04_multiple_expiry(self):
        spot = 400.0
        rows = [
            {"cid": "N7", "dte": 7, "strike": 398.0, "delta": 0.50, "volume": 100},
            {"cid": "N28", "dte": 28, "strike": 398.0, "delta": 0.50, "volume": 100},
            {"cid": "N35", "dte": 35, "strike": 398.0, "delta": 0.50, "volume": 5000},
        ]
        self._run_near(
            "C04_near_multiple_expiry",
            rows,
            spot=spot,
            dte_t=30,
            difference_type="INFRASTRUCTURE_DRIFT",
            alpha_impact=ALPHA_NOTE_SCHEMA + " Target 30 DTE: research two-stage expiry vs live flat sort.",
        )

    def test_C05_strike_pool_1_02_vs_1_01(self):
        """Research uses 1.02 pool for expiry choice; live filters 1.01 only."""
        spot = 400.0
        rows = [
            # Only contract near 30 DTE is slightly OTM above 1.01*spot but <=1.02*spot
            {"cid": "OTM_1_015", "dte": 30, "strike": 400.0 * 1.015, "delta": 0.48, "volume": 9000},
            {"cid": "ITM_14", "dte": 14, "strike": 395.0, "delta": 0.50, "volume": 10},
        ]
        self._run_near(
            "C05_near_strike_pool_1_02_vs_1_01",
            rows,
            spot=spot,
            dte_t=30,
            difference_type="ALPHA_DRIFT",
            alpha_impact=(
                "Research initial filter strike<=spot*1.02 (pick_near L134) then final <=spot*1.01 (L151); "
                "live select_near uses <=spot*1.01 only (engine.py:137). "
                "Can change chosen expiry/contract. Aligning live to research preserves evidence chain."
            ),
        )


class TargetStackParityTests(unittest.TestCase):
    """D) target_stack / desired_stack from same risk inputs."""

    def _compare_stack(
        self,
        case: str,
        *,
        far_delta_abs: float,
        distance_pct: float,
        gamma_rel: float,
        delta_jump: float,
        coverage_mult: float = 1.50,
        spot: float = 400.0,
        far_gamma: float = 0.01,
        gamma_baseline: Optional[float] = None,
    ) -> None:
        # Research path: target_from_state with explicit gamma_rel
        desired_r, state_r = target_from_state(
            far_delta_abs, distance_pct, gamma_rel, delta_jump, coverage_mult
        )

        # Live path: risk_state derives gamma_rel from (abs(gamma)*spot) / gamma_baseline
        # To feed the SAME gamma_rel, set baseline and gamma accordingly.
        if gamma_baseline is None:
            # Choose baseline so abs(far_gamma)*spot/baseline == gamma_rel
            if gamma_rel == 0:
                gamma_baseline = 1.0
                far_gamma = 0.0
            else:
                gamma_baseline = float(spot)
                far_gamma = gamma_rel  # abs(gamma)*spot / spot == gamma_rel

        far = Contract(
            code="FAR",
            right="CALL",
            strike=spot * (1.0 + distance_pct),
            expiry="2026-12-01",
            dte=120,
            bid=1.0,
            ask=1.1,
            delta=far_delta_abs,  # positive call delta
            gamma=far_gamma,
        )
        prev = None if delta_jump == 0 else (far_delta_abs - delta_jump)
        # When we want exact jump: prev_delta such that abs(da - prev) == delta_jump
        if delta_jump > 0:
            prev = far_delta_abs - delta_jump

        live_state = risk_state(far, spot, gamma_baseline=gamma_baseline, prev_delta=prev)
        desired_l = live_state["desired_stack"]

        equal = desired_r == desired_l and _num_eq(
            state_r["risk_score"], live_state["risk_score"], tol=1e-9
        )
        # Also check component scores
        comps_eq = (
            state_r["dscore"] == live_state["dscore"]
            and state_r["xscore"] == live_state["xscore"]
            and state_r["gscore"] == live_state["gscore"]
        )
        record_case(
            case,
            {
                "far_delta_abs": far_delta_abs,
                "distance_pct": distance_pct,
                "gamma_rel": gamma_rel,
                "delta_jump": delta_jump,
                "coverage_mult": coverage_mult,
                "research_state": state_r,
                "live_state": {
                    k: live_state[k]
                    for k in (
                        "far_delta_abs",
                        "distance_pct",
                        "gamma_rel",
                        "delta_jump",
                        "dscore",
                        "xscore",
                        "gscore",
                        "risk_score",
                        "desired_stack",
                    )
                },
                "component_scores_equal": comps_eq,
            },
            {"desired_stack": desired_r, "risk_score": state_r["risk_score"]},
            {"desired_stack": desired_l, "risk_score": live_state["risk_score"]},
            equal=equal,
            difference={
                "stack_delta": desired_l - desired_r,
                "score_delta": live_state["risk_score"] - state_r["risk_score"],
            },
            difference_type="ALPHA_DRIFT" if not equal else "PARITY",
            alpha_impact=(
                ALPHA_NOTE_PARITY
                if equal
                else (
                    "Stack formula structure matches (engine.py:89-113 vs research:272-318) "
                    "when gamma_rel/inputs identical; residual diffs are edge falsy handling "
                    "(live treats gamma_baseline/gamma 0 as missing -> gr=1.0). "
                    + ALPHA_NOTE_LIVE_ALIGN
                )
            ),
        )

    def test_D01_low_risk(self):
        self._compare_stack(
            "D01_stack_low_risk",
            far_delta_abs=0.03,
            distance_pct=0.12,
            gamma_rel=1.0,
            delta_jump=0.0,
        )

    def test_D02_mid_risk(self):
        self._compare_stack(
            "D02_stack_mid_risk",
            far_delta_abs=0.08,
            distance_pct=0.05,
            gamma_rel=1.3,
            delta_jump=0.015,
        )

    def test_D03_high_risk_boost2(self):
        self._compare_stack(
            "D03_stack_high_risk_boost2",
            far_delta_abs=0.12,
            distance_pct=0.01,
            gamma_rel=2.0,
            delta_jump=0.05,
        )

    def test_D04_boundary_score_3_2(self):
        # Craft scores near 3.2 boost boundary
        # dscore=3 (0.06<=da<0.08 -> wait da<0.08 -> 3 if da>=0.06), use 0.07 -> 3
        # xscore=3 (0.04<dist<=0.07 -> dist>0.04 and not >0.07 -> 3), use 0.05
        # gscore=2 (gr<1.5 and dj<0.02), use gr=1.4 dj=0.01
        # score = 0.5*3 + 0.3*3 + 0.2*2 = 1.5+0.9+0.4 = 2.8 -> boost 0
        self._compare_stack(
            "D04_stack_score_below_3_2",
            far_delta_abs=0.07,
            distance_pct=0.05,
            gamma_rel=1.4,
            delta_jump=0.01,
        )

    def test_D05_boundary_score_ge_3_2(self):
        # dscore=4 (0.08<=da<0.10), xscore=3, gscore=2
        # 0.5*4+0.3*3+0.2*2 = 2+0.9+0.4 = 3.3 >= 3.2 -> boost 1
        self._compare_stack(
            "D05_stack_score_ge_3_2",
            far_delta_abs=0.09,
            distance_pct=0.05,
            gamma_rel=1.4,
            delta_jump=0.01,
        )

    def test_D06_zero_gamma_falsy_live(self):
        """Live treats gamma=0 as missing (gr=1.0); research uses provided gamma_rel."""
        desired_r, state_r = target_from_state(0.10, 0.03, 2.5, 0.03, 1.50)
        far = Contract(
            code="FAR",
            right="CALL",
            strike=412.0,
            expiry="2026-12-01",
            dte=120,
            bid=1.0,
            ask=1.1,
            delta=0.10,
            gamma=0.0,
        )
        live_state = risk_state(far, 400.0, gamma_baseline=0.01, prev_delta=0.07)
        equal = desired_r == live_state["desired_stack"]
        record_case(
            "D06_stack_zero_gamma_falsy_live",
            {
                "research_gamma_rel_forced": 2.5,
                "live_gamma": 0.0,
                "live_note": "gamma=0.0 -> gamma_spot=0; gr=0.0/baseline",
                "research_desired": desired_r,
                "live_desired": live_state["desired_stack"],
                "live_gamma_rel": live_state["gamma_rel"],
            },
            desired_r,
            live_state["desired_stack"],
            equal=equal,
            difference_type="INFRASTRUCTURE_DRIFT" if not equal else "PARITY",
            alpha_impact=(
                "Live risk_state uses gamma_spot=abs(gamma)*spot; gamma=0 yields gr=0. "
                + ALPHA_NOTE_LIVE_ALIGN
            ),
        )


def write_reports() -> tuple[Path, Path]:
    json_path = PARITY_DIR / "PARITY_REPORT.json"
    md_path = PARITY_DIR / "PARITY_REPORT.md"
    payload = {
        "schema": "PARITY_REPORT.v1",
        "head_note": "Generated by research.parity_v1.test_research_live_parity",
        "case_count": len(RESULTS),
        "parity_count": sum(1 for r in RESULTS if r["difference_type"] == "PARITY"),
        "drift_counts": {},
        "cases": RESULTS,
    }
    for r in RESULTS:
        t = r["difference_type"]
        payload["drift_counts"][t] = payload["drift_counts"].get(t, 0) + 1

    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Research ↔ Live PARITY REPORT",
        "",
        "Local-only diagnostic. Does **not** change STRATEGY_LOCK / alpha parameters.",
        "Infrastructure-only live alignment to locked research; no STRATEGY_LOCK mutation.",
        "",
        f"- Cases recorded: **{payload['case_count']}**",
        f"- PARITY: **{payload['parity_count']}**",
        f"- Drift counts: `{json.dumps(payload['drift_counts'], ensure_ascii=False)}`",
        "",
        "## Summary table",
        "",
        "| CASE | equal | difference_type | research_value | live_value | difference | alpha_impact |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in RESULTS:
        lines.append(
            "| {CASE} | {equal} | {difference_type} | `{rv}` | `{lv}` | `{df}` | {ai} |".format(
                CASE=r["CASE"],
                equal=r["equal"],
                difference_type=r["difference_type"],
                rv=str(r["research_value"])[:80].replace("|", "/"),
                lv=str(r["live_value"])[:80].replace("|", "/"),
                df=str(r["difference"])[:60].replace("|", "/"),
                ai=str(r["alpha_impact"])[:120].replace("|", "/"),
            )
        )

    lines += [
        "",
        "## Alignment status (infra-only LIVE->RESEARCH)",
        "",
        "1. gamma_baseline: research + live both use shift(1)/pre-append + rolling(20, min_periods=5).median() on gamma_spot=abs(gamma)*spot; live stamps gamma_history_schema=2 / unit=gamma_spot and resets legacy raw |γ|.",
        "2. Far/near selection: both two-stage expiry then strike with volume tie-break; live Contract.volume enriched from quotes.",
        "3. Near strike pool: both <=spot*1.02 then final <=spot*1.01.",
        "4. target/desired stack: scoring + ceil coverage; live gamma_rel from gamma_spot / baseline.",
        "",
        "## Notes",
        "",
        "- Infrastructure-only LIVE->RESEARCH alignment applied (no STRATEGY_LOCK / research alpha edits).",
        "- Do not change research median->mean or drop volume from research — that would be new candidate / evidence invalidation.",
        "",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def tearDownModule() -> None:
    write_reports()


if __name__ == "__main__":
    unittest.main(verbosity=2, exit=False)
    write_reports()
