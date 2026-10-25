"""
QQQ Hybrid VXX Call-Spread Contribution V1

Purpose
-------
Reverse-engineer the preserved hybrid replay and isolate the contribution
of the VXX call-credit spread (short VXX call + long wing).

Method
------
Uses the same source functions and data as the verified historical replay:
  - quoteCC(kind='vxx')
  - BASE_RV = 0.02
  - ivVxxCall(vix)
  - universe.json QQQ / VXX / VIX

This is a derived BS / VIX-proxy reconstruction, not historical OPRA fills.
"""

from __future__ import annotations

import argparse
import json
import math
import tempfile
from pathlib import Path

import pandas as pd

from qqq_hybrid_dynamic_deployment_v1_1_replay import (
    BASE_RV,
    CAPITAL,
    bsCall,
    halfSpreadV,
    ivVxxCall,
    portfolio_liq,
    quoteCC,
)
from qqq_hybrid_profit_trend_replay_v1 import prepare_simulator_input


def simulate_with_vxx_cc_attribution(spots_path: str, dynamic: bool = False):
    data = json.loads(Path(spots_path).read_text(encoding="utf-8"))
    df = pd.DataFrame({
        "date": pd.to_datetime(data["dates"]),
        "qqq": data["qqq"],
        "vxx": data["vxx"],
        "vix": data["vix"],
    })
    df["rV"] = df.vxx.pct_change().fillna(0)
    df["rQ"] = df.qqq.pct_change().fillna(0)
    df["vixma"] = df.vix.rolling(20, min_periods=1).mean()
    df["ts"] = (df.vixma - df.vix).apply(lambda x: math.tanh(x / 6) * 0.1)

    cash = [CAPITAL]
    legs = []
    eq = []
    vxx_cc_events = []
    vxx_cc_pnl_realized = 0.0

    for i, row in df.iterrows():
        keep = []
        for p in legs:
            dte = max(p["expiry_i"] - i, 0)
            if p["structure"] == "vxx-cc":
                S = row.vxx
                half = halfSpreadV(row.vix)
                T = max(dte / 365, 1 / 365)
                sigS = ivVxxCall(row.vix)
                sigL = sigS * 0.96
                exitp = (
                    bsCall(S, p["Ks"], T, 0.03, sigS, 0) * (1 + half)
                    - bsCall(S, p["Kl"], T, 0.03, sigL, 0) * (1 - half)
                )
                pnl = (p["premium"] - exitp) * 100 * p["n"]
                liq = -exitp * 100 * p["n"]
                risk = (p["width"] - p["premium"]) * 100 * p["n"]
                fire = dte <= 7 or (risk > 0 and pnl / risk <= -0.55) or (risk > 0 and pnl / risk >= 0.5)
                if fire:
                    cash[0] += liq
                    vxx_cc_pnl_realized += pnl
                    vxx_cc_events.append({
                        "date": str(row.date.date()),
                        "event": "CLOSE_VXX_CC",
                        "n": int(p["n"]),
                        "pnl": float(pnl),
                        "credit": float(p["premium"]),
                        "Ks": float(p["Ks"]),
                        "Kl": float(p["Kl"]),
                    })
                else:
                    keep.append(p)
            else:
                keep.append(p)
        legs = keep

        nav = cash[0] + portfolio_liq(df, i, legs)
        state = "Shock" if (row.rV > 0.06 or row.vix > 35 or row.rQ < -0.03) else "Normal"
        wantV = state != "Shock" and row.ts >= 0
        structs = {p["structure"] for p in legs}

        if wantV and "vxx-cc" not in structs:
            half = halfSpreadV(row.vix)
            q = quoteCC(row.vxx, row.vix, 30 / 365, "vxx", half)
            n = math.floor(nav * BASE_RV / ((q["width"] - q["premium"]) * 100))
            if n > 0:
                cash[0] += q["premium"] * 100 * n
                legs.append({
                    "structure": "vxx-cc",
                    "kind": "vxx",
                    "n": n,
                    "S0": row.vxx,
                    "Ks": q["Ks"],
                    "Kl": q["Kl"],
                    "premium": q["premium"],
                    "width": q["width"],
                    "expiry_i": i + 21,
                })
                vxx_cc_events.append({
                    "date": str(row.date.date()),
                    "event": "OPEN_VXX_CC",
                    "n": int(n),
                    "credit": float(q["premium"]),
                    "Ks": float(q["Ks"]),
                    "Kl": float(q["Kl"]),
                    "width": float(q["width"]),
                })

        nav = cash[0] + portfolio_liq(df, i, legs)
        eq.append((row.date, nav, vxx_cc_pnl_realized))

    e = pd.DataFrame(eq, columns=["date", "nav", "vxx_cc_realized_pnl"])
    return e, vxx_cc_events, vxx_cc_pnl_realized


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spots-path", required=True)
    parser.add_argument("--out", default="artifacts/qqq_hybrid_vxx_call_spread_contribution_v1")
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    spots = prepare_simulator_input(Path(args.spots_path))
    eq, events, realized = simulate_with_vxx_cc_attribution(str(spots), dynamic=False)

    opens = [x for x in events if x["event"] == "OPEN_VXX_CC"]
    closes = [x for x in events if x["event"] == "CLOSE_VXX_CC"]
    win = sum(1 for x in closes if x.get("pnl", 0) > 0)
    loss = sum(1 for x in closes if x.get("pnl", 0) <= 0)

    report = {
        "research_id": "QQQ_HYBRID_VXX_CALL_SPREAD_CONTRIBUTION_V1",
        "status": "DERIVED_REPLAY_ATTRIBUTION",
        "pricing_model": "DERIVED_BS_VIX",
        "not_opra": True,
        "source": "qqq_hybrid_dynamic_deployment_v1_1_replay.py",
        "vxx_call_spread": {
            "risk_budget": BASE_RV,
            "structure": "short VXX call + long wing",
            "delta_targets": {"short": 0.35, "long_wing": 0.16},
            "opens": len(opens),
            "closes": len(closes),
            "wins": win,
            "losses": loss,
            "realized_pnl": float(realized),
        },
        "final_nav": float(eq["nav"].iloc[-1]),
        "caveat": "Derived BS/VIX proxy only. Not historical OPRA fills. Not current sizing.",
    }

    eq.to_csv(out / "vxx_cc_attribution.csv", index=False)
    (out / "vxx_cc_events.json").write_text(json.dumps(events, indent=2), encoding="utf-8")
    (out / "vxx_cc_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
