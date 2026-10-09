"""Research-only VXX short call/put verticals inside the historical QQQ/VXX hybrid.

This is a new model variant, not a live policy change.
- Historical option prices remain DERIVED_BS_VIX, not OPRA.
- Legacy call-only control must reconcile to the preserved simulator.
- Dual-sided variant reallocates the historical 2% VXX option max-loss budget as
  1% VXX call vertical + 1% VXX put vertical.
- No naked VXX options: each short option is paired with a protective wing.
- Current sizing must never be copied from historical research parameters.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pandas as pd

from qqq_hybrid_dynamic_deployment_v1_1_replay import (
    CAPITAL, BASE_QCC_RISK, bsCall, halfSpreadQ, halfSpreadV, ivQqq,
    ivVxxCall, quoteCC, simulate as legacy_simulate, strikeFromCallDelta,
)
from qqq_hybrid_profit_trend_replay_v1 import prepare_simulator_input

RESEARCH_ID = "QQQ_HYBRID_VXX_SHORT_CALL_PUT_V1"
SOURCE_REPLAY_SHA = "ac74b3812c826ad491fb829108f26397322e45eb"

LEG_CONFIGS = {
    # Exact historical source parity control.
    "LEGACY_CALL_ONLY": {"vxx_call_risk_pct": 2.0, "vxx_put_risk_pct": 0.0, "rsi_filter": "NONE", "legacy_quote": True},
    # Controlled comparisons isolate whether adding puts helps at the same call budget.
    "CALL_ONLY_1PCT": {"vxx_call_risk_pct": 1.0, "vxx_put_risk_pct": 0.0, "rsi_filter": "NONE"},
    "DUAL_CALL_PUT": {"vxx_call_risk_pct": 1.0, "vxx_put_risk_pct": 1.0, "rsi_filter": "NONE"},
    "CALL_ONLY_2PCT_NEW_QUOTE": {"vxx_call_risk_pct": 2.0, "vxx_put_risk_pct": 0.0, "rsi_filter": "NONE"},
    "CALL_PUT_ADDON": {"vxx_call_risk_pct": 2.0, "vxx_put_risk_pct": 1.0, "rsi_filter": "NONE"},
    "PUT_ONLY_1PCT": {"vxx_call_risk_pct": 0.0, "vxx_put_risk_pct": 1.0, "rsi_filter": "NONE"},
    # Online VXX short-call research explores RSI regimes; filter only the option leg,
    # not the separate VXX short-stock layer.
    "CALL_RSI_LT50": {"vxx_call_risk_pct": 2.0, "vxx_put_risk_pct": 0.0, "rsi_filter": "LT50"},
    "CALL_RSI_GE50": {"vxx_call_risk_pct": 2.0, "vxx_put_risk_pct": 0.0, "rsi_filter": "GE50"},
    "NO_VXX_OPTIONS": {"vxx_call_risk_pct": 0.0, "vxx_put_risk_pct": 0.0, "rsi_filter": "NONE"},
}
LEG_KEYS = ("qqq_core", "qqq_call", "vxx_short", "vxx_call", "vxx_put")


def bs_put(S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0) -> float:
    if T <= 1.0 / 365.0 or sigma < 1e-8:
        return max(K - S, 0.0)
    call = bsCall(S, K, T, r, sigma, q)
    return call - S * math.exp(-q * T) + K * math.exp(-r * T)


def quote_vxx_call_spread(S: float, vix: float, T: float, *, require_positive_credit: bool) -> dict | None:
    """VXX short call plus higher-strike long-call wing using the repo BS/VIX proxy."""
    half = halfSpreadV(vix)
    sig_short = ivVxxCall(vix)
    sig_long = sig_short * 0.96
    short_k = strikeFromCallDelta(S, T, 0.03, 0.0, sig_short, 0.35)
    long_k = strikeFromCallDelta(S, T, 0.03, 0.0, sig_long, 0.16)
    if long_k <= short_k:
        long_k = short_k * 1.14
    short_mid = bsCall(S, short_k, T, 0.03, sig_short, 0.0)
    long_mid = bsCall(S, long_k, T, 0.03, sig_long, 0.0)
    credit = short_mid * (1.0 - half) - long_mid * (1.0 + half)
    width = long_k - short_k
    if width <= 0 or credit >= width or (require_positive_credit and credit <= 0):
        return None
    # The historical control retains the preserved quoteCC minimum-credit behavior;
    # the new dual-sided candidate finder never manufactures positive credit.
    if not require_positive_credit:
        credit = max(credit, 1e-4)
    return {"short_k": short_k, "long_k": long_k, "credit": credit, "width": width, "side": "call"}


def quote_vxx_put_spread(S: float, vix: float, T: float) -> dict | None:
    """VXX short put plus lower-strike long-put wing; absolute put delta targets .35/.16."""
    half = halfSpreadV(vix)
    sig_short = ivVxxCall(vix)
    sig_long = sig_short * 0.96
    # |put delta|=.35 implies call delta=.65 at the same strike; .16 -> .84.
    short_k = strikeFromCallDelta(S, T, 0.03, 0.0, sig_short, 0.65)
    long_k = strikeFromCallDelta(S, T, 0.03, 0.0, sig_long, 0.84)
    if long_k >= short_k:
        long_k = short_k * 0.86
    short_mid = bs_put(S, short_k, T, 0.03, sig_short, 0.0)
    long_mid = bs_put(S, long_k, T, 0.03, sig_long, 0.0)
    credit = short_mid * (1.0 - half) - long_mid * (1.0 + half)
    width = short_k - long_k
    # Invalid/non-positive credit remains pending; never add a synthetic credit floor.
    if width <= 0 or credit <= 0 or credit >= width:
        return None
    return {"short_k": short_k, "long_k": long_k, "credit": credit, "width": width, "side": "put"}


def spread_mark(S: float, vix: float, p: dict, dte: int) -> float:
    """Conservative cost to close one vertical, per underlying share."""
    T = max(dte / 365.0, 1.0 / 365.0)
    half = halfSpreadV(vix) if p["kind"] == "vxx" else halfSpreadQ(vix)
    if p["kind"] == "vxx":
        sig_short = ivVxxCall(vix)
        sig_long = sig_short * 0.96
        q = 0.0
    else:
        sig_short = ivQqq(vix) * 0.95
        sig_long = ivQqq(vix) * 0.90
        q = 0.004
    pricer = bsCall if p["side"] == "call" else bs_put
    short_ask = pricer(S, p["short_k"], T, 0.03, sig_short, q) * (1.0 + half)
    long_bid = pricer(S, p["long_k"], T, 0.03, sig_long, q) * (1.0 - half)
    return max(short_ask - long_bid, 0.0)


def position_liquidation_value(row, p: dict, i: int) -> float:
    dte = max(int(p["expiry_i"] - i), 0)
    if p["structure"] == "qqq-long":
        return float(row.qqq) * p["n"]
    if p["structure"] == "vxx-short":
        return -float(row.vxx) * p["n"]
    S = float(row.vxx if p["kind"] == "vxx" else row.qqq)
    return -spread_mark(S, float(row.vix), p, dte) * 100.0 * p["n"]


def leg_key(p: dict) -> str:
    return {
        "qqq-long": "qqq_core", "qqq-cc": "qqq_call",
        "vxx-short": "vxx_short", "vxx-cc": "vxx_call", "vxx-pc": "vxx_put",
    }[p["structure"]]


def open_credit_vertical(legs: list, events: list, cash: float, nav: float, row, i: int,
                         structure: str, risk_pct: float, quote: dict | None) -> tuple[list, list, float]:
    if risk_pct <= 0 or quote is None:
        return legs, events, cash
    max_loss_per_contract = (float(quote["width"]) - float(quote["credit"])) * 100.0
    if max_loss_per_contract <= 0:
        return legs, events, cash
    risk_budget = nav * risk_pct / 100.0
    n = int(math.floor(risk_budget / max_loss_per_contract))
    if n <= 0:
        return legs, events, cash
    p = {
        "structure": structure, "kind": "vxx", "side": quote["side"], "n": n,
        "short_k": float(quote["short_k"]), "long_k": float(quote["long_k"]),
        "credit": float(quote["credit"]), "width": float(quote["width"]),
        "expiry_i": i + 21, "risk_budget_pct": risk_pct,
        "max_loss_at_open": max_loss_per_contract * n,
    }
    cash += p["credit"] * 100.0 * n
    legs.append(p)
    events.append({
        "date": str(row.date.date()), "event": "OPEN_" + structure.upper().replace("-", "_"),
        "contracts": n, "side": p["side"], "short_strike": p["short_k"],
        "long_strike": p["long_k"], "expiry_index": p["expiry_i"],
        "credit_per_share": p["credit"], "width": p["width"],
        "max_loss_per_contract": max_loss_per_contract,
        "max_loss_total_at_open": p["max_loss_at_open"],
        "risk_budget_usd": risk_budget, "risk_budget_pct_nav": risk_pct,
        "risk_budget_check": p["max_loss_at_open"] <= risk_budget + 1e-7,
    })
    return legs, events, cash


def component_pnls(row, i: int, legs: list, realized: dict) -> dict:
    out = {k: float(realized.get(k, 0.0)) for k in LEG_KEYS}
    for p in legs:
        if p["structure"] == "qqq-long":
            out["qqq_core"] += (float(row.qqq) - p["S0"]) * p["n"]
        elif p["structure"] == "vxx-short":
            out["vxx_short"] += (p["S0"] - float(row.vxx)) * p["n"]
        else:
            S = float(row.vxx if p["kind"] == "vxx" else row.qqq)
            dte = max(int(p["expiry_i"] - i), 0)
            liability = spread_mark(S, float(row.vix), p, dte)
            out[leg_key(p)] += (p["credit"] - liability) * 100.0 * p["n"]
    out["vxx_options"] = out["vxx_call"] + out["vxx_put"]
    return out


def simulate_variant(spots_path: str, variant: str) -> tuple[pd.DataFrame, list[dict], dict]:
    if variant not in LEG_CONFIGS:
        raise ValueError(f"Unknown variant: {variant}")
    cfg = LEG_CONFIGS[variant]
    data = json.loads(Path(spots_path).read_text(encoding="utf-8"))
    required = {"dates", "qqq", "vxx", "vix"}
    if not required.issubset(data):
        raise ValueError("Simulator input must contain dates/qqq/vxx/vix arrays")
    if len({len(data[k]) for k in required}) != 1:
        raise ValueError("Input series length mismatch")
    df = pd.DataFrame({
        "date": pd.to_datetime(data["dates"]),
        "qqq": pd.to_numeric(data["qqq"], errors="coerce"),
        "vxx": pd.to_numeric(data["vxx"], errors="coerce"),
        "vix": pd.to_numeric(data["vix"], errors="coerce"),
    })
    df = df.dropna(subset=["date", "qqq", "vxx", "vix"]).sort_values("date").reset_index(drop=True)
    df["rQ"] = df.qqq.pct_change().fillna(0.0)
    df["rV"] = df.vxx.pct_change().fillna(0.0)
    df["vixma"] = df.vix.rolling(20, min_periods=1).mean()
    df["ts"] = (df.vixma - df.vix).apply(lambda x: math.tanh(float(x) / 6.0) * 0.1)
    # Wilder-style 14-session RSI on VXX, inspired by public VXX short-call
    # backtest exploration that compares RSI<50 versus RSI>=50.
    changes = df["vxx"].diff()
    gains = changes.clip(lower=0.0)
    losses = -changes.clip(upper=0.0)
    avg_gain = gains.ewm(alpha=1.0 / 14.0, min_periods=14, adjust=False).mean()
    avg_loss = losses.ewm(alpha=1.0 / 14.0, min_periods=14, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    df["vxx_rsi14"] = 100.0 - (100.0 / (1.0 + rs))
    no_loss = avg_loss.eq(0.0) & avg_loss.notna() & avg_gain.notna()
    df.loc[no_loss & avg_gain.gt(0.0), "vxx_rsi14"] = 100.0
    df.loc[no_loss & avg_gain.eq(0.0), "vxx_rsi14"] = 50.0
    # Use yesterday's closed-bar RSI for today's modeled entry to avoid look-ahead.
    df["vxx_rsi14_entry"] = df["vxx_rsi14"].shift(1)

    cash = float(CAPITAL)
    legs: list[dict] = []
    events: list[dict] = []
    realized = {k: 0.0 for k in LEG_KEYS}
    rows = []
    for i, row in df.iterrows():
        keep = []
        for p in legs:
            dte = max(int(p["expiry_i"] - i), 0)
            if p["structure"] == "qqq-long":
                keep.append(p)
                continue
            if p["structure"] == "vxx-short":
                pnl = (p["S0"] - float(row.vxx)) * p["n"]
                denom = p["S0"] * p["n"]
                reasons = []
                if row.rV > 0.06: reasons.append("VXX_DAILY_SPIKE")
                if row.vix > 35: reasons.append("VIX_SHOCK")
                if row.ts < 0: reasons.append("TERM_SLOPE_PROXY_NEGATIVE")
                if dte <= 7: reasons.append("DTE_EXIT")
                if denom > 0 and pnl / denom <= -0.5: reasons.append("LOSS_50PCT")
                if reasons:
                    cash -= float(row.vxx) * p["n"]
                    realized["vxx_short"] += pnl
                    events.append({"date": str(row.date.date()), "event": "CLOSE_VXX_SHORT",
                                   "contracts_or_shares": p["n"], "realized_pnl": pnl, "reasons": reasons})
                else:
                    keep.append(p)
                continue

            S = float(row.vxx if p["kind"] == "vxx" else row.qqq)
            liability = spread_mark(S, float(row.vix), p, dte)
            pnl = (p["credit"] - liability) * 100.0 * p["n"]
            risk = (p["width"] - p["credit"]) * 100.0 * p["n"]
            reasons = []
            if dte <= 7: reasons.append("DTE_EXIT")
            if risk > 0 and pnl / risk <= -0.55: reasons.append("LOSS_55PCT_MAX_RISK")
            if risk > 0 and pnl / risk >= 0.50: reasons.append("PROFIT_50PCT_MAX_RISK")
            if reasons:
                cash -= liability * 100.0 * p["n"]
                realized[leg_key(p)] += pnl
                events.append({"date": str(row.date.date()), "event": "CLOSE_" + p["structure"].upper().replace("-", "_"),
                               "contracts": p["n"], "side": p.get("side", "call"),
                               "realized_pnl": pnl, "reasons": reasons})
            else:
                keep.append(p)
        legs = keep

        nav_before_open = cash + sum(position_liquidation_value(row, p, i) for p in legs)
        existing = {p["structure"] for p in legs}

        if "qqq-long" not in existing and float(row.qqq) > 0:
            n = int(math.floor(nav_before_open * 0.42 / float(row.qqq)))
            if n > 0:
                cash -= float(row.qqq) * n
                legs.append({"structure": "qqq-long", "n": n, "S0": float(row.qqq), "expiry_i": i + 100000})
                events.append({"date": str(row.date.date()), "event": "OPEN_QQQ_CORE", "shares": n})

        if "qqq-cc" not in existing and float(row.qqq) > 0:
            half = halfSpreadQ(float(row.vix))
            q = quoteCC(float(row.qqq), float(row.vix), 30.0 / 365.0, "qqq", half)
            risk_per_share = float(q["width"]) - float(q["premium"])
            if risk_per_share > 0:
                n = int(math.floor(nav_before_open * BASE_QCC_RISK / (risk_per_share * 100.0)))
                if n > 0:
                    p = {"structure": "qqq-cc", "kind": "qqq", "side": "call", "n": n,
                         "short_k": float(q["Ks"]), "long_k": float(q["Kl"]),
                         "credit": float(q["premium"]), "width": float(q["width"]), "expiry_i": i + 21}
                    cash += p["credit"] * 100.0 * n
                    legs.append(p)
                    events.append({"date": str(row.date.date()), "event": "OPEN_QQQ_CC", "contracts": n,
                                   "short_strike": p["short_k"], "long_strike": p["long_k"],
                                   "credit_per_share": p["credit"],
                                   "max_loss_total_at_open": risk_per_share * 100.0 * n,
                                   "risk_budget_usd": nav_before_open * BASE_QCC_RISK})

        want_vxx_stock = not (row.rV > 0.06 or row.vix > 35 or row.rQ < -0.03) and row.ts >= 0
        # Keep the existing stock-seller gate unchanged. RSI experiments affect only
        # the option legs, which avoids confounding short-stock exposure with options.
        want_vxx_options = want_vxx_stock
        if cfg.get("rsi_filter") == "LT50":
            want_vxx_options = want_vxx_options and pd.notna(row.vxx_rsi14_entry) and float(row.vxx_rsi14_entry) < 50.0
        elif cfg.get("rsi_filter") == "GE50":
            want_vxx_options = want_vxx_options and pd.notna(row.vxx_rsi14_entry) and float(row.vxx_rsi14_entry) >= 50.0

        if want_vxx_stock and "vxx-short" not in existing and float(row.vxx) > 0:
            n = int(math.floor(nav_before_open * 0.18 / float(row.vxx)))
            if n > 0:
                cash += float(row.vxx) * n
                legs.append({"structure": "vxx-short", "n": n, "S0": float(row.vxx), "expiry_i": i + 21})
                events.append({"date": str(row.date.date()), "event": "OPEN_VXX_SHORT", "shares": n})

        if want_vxx_options:
            if "vxx-cc" not in existing and cfg["vxx_call_risk_pct"] > 0:
                if cfg.get("legacy_quote", False):
                    half = halfSpreadV(float(row.vix))
                    q0 = quoteCC(float(row.vxx), float(row.vix), 30.0 / 365.0, "vxx", half)
                    q = {"short_k": q0["Ks"], "long_k": q0["Kl"], "credit": q0["premium"],
                         "width": q0["width"], "side": "call"}
                else:
                    q = quote_vxx_call_spread(float(row.vxx), float(row.vix), 30.0 / 365.0,
                                              require_positive_credit=True)
                legs, events, cash = open_credit_vertical(
                    legs, events, cash, nav_before_open, row, i, "vxx-cc",
                    cfg["vxx_call_risk_pct"], q)
            if "vxx-pc" not in existing and cfg["vxx_put_risk_pct"] > 0:
                q = quote_vxx_put_spread(float(row.vxx), float(row.vix), 30.0 / 365.0)
                legs, events, cash = open_credit_vertical(
                    legs, events, cash, nav_before_open, row, i, "vxx-pc",
                    cfg["vxx_put_risk_pct"], q)

        nav = cash + sum(position_liquidation_value(row, p, i) for p in legs)
        attrib = component_pnls(row, i, legs, realized)
        component_sum = sum(attrib[k] for k in LEG_KEYS)
        rows.append({
            "date": row.date, "nav": nav, "total_profit": nav - CAPITAL,
            "qqq_core_pnl": attrib["qqq_core"], "qqq_call_pnl": attrib["qqq_call"],
            "vxx_short_pnl": attrib["vxx_short"], "vxx_call_pnl": attrib["vxx_call"],
            "vxx_put_pnl": attrib["vxx_put"], "vxx_options_pnl": attrib["vxx_options"],
            "component_sum_error": nav - CAPITAL - component_sum,
            "vix": float(row.vix), "vxx_term_slope_proxy": float(row.ts),
        })
    eq = pd.DataFrame(rows)
    eq["peak_nav"] = eq["nav"].cummax()
    eq["drawdown"] = eq["nav"] / eq["peak_nav"] - 1.0
    eq["daily_profit"] = eq["nav"].diff().fillna(0.0)
    for sessions, label in ((21, "1m"), (63, "3m"), (126, "6m"), (252, "12m")):
        eq[f"return_{label}"] = eq["nav"].pct_change(sessions)
    component_final = {k: float(eq[f"{k}_pnl"].iloc[-1]) for k in LEG_KEYS}
    final_nav = float(eq["nav"].iloc[-1])
    days = max((eq["date"].iloc[-1] - eq["date"].iloc[0]).days, 1)
    return eq, events, {
        "variant": variant,
        "vxx_call_risk_pct": cfg["vxx_call_risk_pct"],
        "vxx_put_risk_pct": cfg["vxx_put_risk_pct"],
        "vxx_options_rsi_filter": cfg.get("rsi_filter", "NONE"),
        "vxx_total_option_risk_budget_pct": cfg["vxx_call_risk_pct"] + cfg["vxx_put_risk_pct"],
        "option_contract_counts": {
            "vxx_call_open_events": sum(e["event"] == "OPEN_VXX_CC" for e in events),
            "vxx_call_close_events": sum(e["event"] == "CLOSE_VXX_CC" for e in events),
            "vxx_put_open_events": sum(e["event"] == "OPEN_VXX_PC" for e in events),
            "vxx_put_close_events": sum(e["event"] == "CLOSE_VXX_PC" for e in events),
        },
        "component_final_pnl": component_final,
        "vxx_options_component_final_pnl": float(eq["vxx_options_pnl"].iloc[-1]),
        "component_sum_error_max_abs": float(eq["component_sum_error"].abs().max()),
        "final_nav": final_nav,
        "final_profit": float(eq["total_profit"].iloc[-1]),
        "total_return": final_nav / CAPITAL - 1.0,
        "cagr": (final_nav / CAPITAL) ** (365.25 / days) - 1.0 if final_nav > 0 else -1.0,
        "maxdd_daily_mtm": float(eq["drawdown"].min()),
        "rows": int(len(eq)),
        "window": {"start": str(eq["date"].iloc[0].date()), "end": str(eq["date"].iloc[-1].date())},
    }


def run_research(spots_path: Path, out_dir: Path) -> dict:
    spots = prepare_simulator_input(spots_path)
    summaries, curves, events_by_variant = {}, {}, {}
    for variant in LEG_CONFIGS:
        eq, events, summary = simulate_variant(str(spots), variant)
        summaries[variant], curves[variant], events_by_variant[variant] = summary, eq, events
        eq.to_csv(out_dir / f"{variant.lower()}_equity_attribution.csv", index=False)
        (out_dir / f"{variant.lower()}_events.json").write_text(json.dumps(events, indent=2), encoding="utf-8")

    original = legacy_simulate(str(spots), False)
    original_eq = original[6].copy()
    control_eq = curves["LEGACY_CALL_ONLY"]
    same_rows = len(original_eq) == len(control_eq)
    max_diff = float((original_eq["nav"].to_numpy() - control_eq["nav"].to_numpy()).__abs__().max()) if same_rows else None
    if not same_rows or max_diff is None or max_diff > 0.01:
        raise AssertionError(f"Legacy parity failed: rows_match={same_rows}, max_abs_nav_diff={max_diff}")

    dual, no_opts, legacy = summaries["DUAL_CALL_PUT"], summaries["NO_VXX_OPTIONS"], summaries["LEGACY_CALL_ONLY"]
    controlled_comparisons = {
        "DUAL_CALL_PUT_vs_CALL_ONLY_1PCT": {
            "final_nav_delta_usd": float(summaries["DUAL_CALL_PUT"]["final_nav"] - summaries["CALL_ONLY_1PCT"]["final_nav"]),
            "cagr_delta": float(summaries["DUAL_CALL_PUT"]["cagr"] - summaries["CALL_ONLY_1PCT"]["cagr"]),
            "maxdd_delta": float(summaries["DUAL_CALL_PUT"]["maxdd_daily_mtm"] - summaries["CALL_ONLY_1PCT"]["maxdd_daily_mtm"]),
            "purpose": "Tests adding 1% put-risk budget while holding the call-risk budget at 1%.",
        },
        "CALL_PUT_ADDON_vs_CALL_ONLY_2PCT_NEW_QUOTE": {
            "final_nav_delta_usd": float(summaries["CALL_PUT_ADDON"]["final_nav"] - summaries["CALL_ONLY_2PCT_NEW_QUOTE"]["final_nav"]),
            "cagr_delta": float(summaries["CALL_PUT_ADDON"]["cagr"] - summaries["CALL_ONLY_2PCT_NEW_QUOTE"]["cagr"]),
            "maxdd_delta": float(summaries["CALL_PUT_ADDON"]["maxdd_daily_mtm"] - summaries["CALL_ONLY_2PCT_NEW_QUOTE"]["maxdd_daily_mtm"]),
            "purpose": "Tests adding 1% put-risk budget while retaining 2% call-risk budget; total option risk budget becomes 3%.",
        },
        "PUT_ONLY_1PCT_vs_NO_VXX_OPTIONS": {
            "final_nav_delta_usd": float(summaries["PUT_ONLY_1PCT"]["final_nav"] - summaries["NO_VXX_OPTIONS"]["final_nav"]),
            "cagr_delta": float(summaries["PUT_ONLY_1PCT"]["cagr"] - summaries["NO_VXX_OPTIONS"]["cagr"]),
            "maxdd_delta": float(summaries["PUT_ONLY_1PCT"]["maxdd_daily_mtm"] - summaries["NO_VXX_OPTIONS"]["maxdd_daily_mtm"]),
            "purpose": "Tests the VXX put vertical by itself inside the rest of the Hybrid.",
        },
        "CALL_RSI_LT50_vs_CALL_RSI_GE50": {
            "final_nav_delta_usd": float(summaries["CALL_RSI_LT50"]["final_nav"] - summaries["CALL_RSI_GE50"]["final_nav"]),
            "cagr_delta": float(summaries["CALL_RSI_LT50"]["cagr"] - summaries["CALL_RSI_GE50"]["cagr"]),
            "maxdd_delta": float(summaries["CALL_RSI_LT50"]["maxdd_daily_mtm"] - summaries["CALL_RSI_GE50"]["maxdd_daily_mtm"]),
            "purpose": "Compares public-source RSI regime split for VXX short calls; VXX stock gate is unchanged.",
        },
    }
    report = {
        "research_id": RESEARCH_ID, "status": "DERIVED_BS_VIX_RESEARCH_NOT_LIVE",
        "pricing_model": "DERIVED_BS_VIX", "not_opra": True,
        "source_replay": "qqq_hybrid_dynamic_deployment_v1_1_replay.py",
        "source_replay_sha": SOURCE_REPLAY_SHA, "data_path": str(spots_path),
        "historical_sizing_only": {
            "qqq_core_pct_nav": 42.0, "qqq_call_risk_pct_nav": 0.8,
            "vxx_short_notional_pct_nav": 18.0, "legacy_vxx_call_max_loss_budget_pct_nav": 2.0,
            "meaning": "Historical replay parameters only; NOT current frozen sizing.",
        },
        "new_dual_sided_hypothesis": {
            "vxx_short_call_vertical": "short call + higher-strike long call wing",
            "vxx_short_put_vertical": "short put + lower-strike long put wing",
            "short_delta_abs_targets": {"call": 0.35, "put": 0.35},
            "long_wing_delta_abs_targets": {"call": 0.16, "put": 0.16},
            "total_vxx_option_max_loss_budget_pct_nav": 2.0,
            "allocation": "1% max-loss budget to calls + 1% to puts",
            "entry_gate": "same historical safe-state gate: no Shock and term-slope proxy >= 0",
            "exit_gate": "DTE <= 7 sessions, PnL/max-risk <= -55%, or PnL/max-risk >= +50%",
        },
        "legacy_parity": {
            "status": "PASS", "rows_match": same_rows,
            "max_abs_daily_nav_difference_usd": max_diff,
            "preserved_source_final_nav": float(original[2]),
            "replayed_control_final_nav": float(legacy["final_nav"]),
        },
        "variants": summaries,
        "counterfactual_portfolio_delta_vs_no_vxx_options": {
            "legacy_call_only_final_nav_difference_usd": float(legacy["final_nav"] - no_opts["final_nav"]),
            "dual_call_put_final_nav_difference_usd": float(dual["final_nav"] - no_opts["final_nav"]),
            "interpretation": (
                "Same starting capital/data and same non-VXX-option rules; portfolio-level counterfactual includes "
                "NAV-based sizing feedback and is not a standalone option-only PnL attribution."
            ),
        },
        "controlled_comparisons": controlled_comparisons,
        "caveats": [
            "VXX options use derived BS/VIX proxies, not historical OPRA quotes or fills.",
            "The dual-sided setup is a research hypothesis; every VXX short option is part of a defined-risk vertical.",
            "Cboe M1/M2 is not substituted into this exact-replay family; using it would be a separate model.",
            "No live order, current capacity, broker action, or current frozen sizing is generated.",
        ],
        "artifact_files": [
            "legacy_call_only_equity_attribution.csv", "dual_call_put_equity_attribution.csv",
            "no_vxx_options_equity_attribution.csv", "legacy_call_only_events.json",
            "dual_call_put_events.json", "no_vxx_options_events.json", "strategy_report.json",
        ],
    }
    for variant, eq in curves.items():
        eq.to_csv(out_dir / f"{variant.lower()}_equity_attribution.csv", index=False)
    (out_dir / "strategy_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spots-path", required=True)
    parser.add_argument("--out", default="artifacts/qqq_hybrid_vxx_short_call_put_v1")
    args = parser.parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    report = run_research(Path(args.spots_path), out_dir)
    print(json.dumps({
        "research_id": report["research_id"], "legacy_parity": report["legacy_parity"],
        "variants": report["variants"], "controlled_comparisons": report["controlled_comparisons"],
        "counterfactual_portfolio_delta_vs_no_vxx_options": report["counterfactual_portfolio_delta_vs_no_vxx_options"],
        "report": str(out_dir / "strategy_report.json"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
