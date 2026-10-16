#!/usr/bin/env python3
"""Research-only QQQ put-ratio scale, exit, and volatility/time study."""
from __future__ import annotations
import argparse, csv, json, math, statistics
from datetime import date
from pathlib import Path
from typing import Any

MULT = 100
RATIOS = range(1, 7)
NAVS = (100_000.0, 1_000_000.0)
BUDGET_PCTS = (0.005, 0.01, 0.02)
HORIZONS = (1, 3, 5, 10, 20, 30, 45)
TRIGGER_PCTS = (0.005, 0.01, 0.02)
COSTS = (
    {"name": "ZERO_FRICTION_BOUND", "slippage": 0.0, "commission": 0.0},
    {"name": "BASE_005_065", "slippage": 0.05, "commission": 0.65},
    {"name": "ADVERSE_010_065", "slippage": 0.10, "commission": 0.65},
)
BASE_COST = "BASE_005_065"
SOURCE_END = "2025-12-15"
EVIDENCE = "PUBLIC_EOD_PRESERVATION_MIRROR / CONSERVATIVE_QUOTE_SIDE_REPLAY / NOT_CONFIRMED_FILLS"
SHORT_HEAVY = "SHORT_HEAVY_1_LONG_N_SHORT"
LONG_HEAVY = "LONG_HEAVY_N_LONG_1_SHORT"

def num(value: Any) -> float | None:
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None

def quote_ok(row: Any, side: str, *, executable: bool = False, qty: int = 1, zero_bid_mark: bool = False) -> bool:
    if not isinstance(row, dict):
        return False
    bid, ask = num(row.get("bid")), num(row.get("ask"))
    if bid is None or ask is None or ask <= 0 or bid < 0 or bid > ask:
        return False
    value = bid if side == "bid" else ask
    if value <= 0 and not (side == "bid" and zero_bid_mark and value == 0):
        return False
    if executable:
        size = num(row.get("bid_size" if side == "bid" else "ask_size"))
        if size is None or size < qty:
            return False
    return True

def quantities(direction: str, n: int) -> tuple[int, int]:
    if direction == SHORT_HEAVY:
        return 1, n
    if direction == LONG_HEAVY:
        return n, 1
    raise ValueError(f"Unknown direction: {direction}")

def entry_size_ok(trade: dict[str, Any], direction: str, n: int, units: int = 1) -> bool:
    q = trade.get("entry_quotes") or {}
    nl, ns = quantities(direction, n)
    return quote_ok(q.get("long"), "ask", executable=True, qty=nl*units) and quote_ok(q.get("short"), "bid", executable=True, qty=ns*units)

def entry_cashflow(trade: dict[str, Any], nl: int, ns: int, slip: float, commission: float) -> float:
    q = trade["entry_quotes"]
    return MULT * (ns * (float(q["short"]["bid"]) - slip) - nl * (float(q["long"]["ask"]) + slip)) - (nl + ns) * commission

def terminal_pnl(cash: float, nl: int, ns: int, kl: float, ks: float, spot: float) -> float:
    return cash + MULT * (nl * max(kl - spot, 0.0) - ns * max(ks - spot, 0.0))

def terminal_envelope(trade: dict[str, Any], nl: int, ns: int, slip: float, commission: float) -> dict[str, float]:
    cash = entry_cashflow(trade, nl, ns, slip, commission)
    kl, ks = float(trade["long_strike"]), float(trade["short_strike"])
    spot = num(trade.get("spot_entry"))
    knots = sorted({0.0, ks, kl, max(kl + 1.0, (spot or kl) * 2.0)})
    pnls = [terminal_pnl(cash, nl, ns, kl, ks, x) for x in knots]
    return {"entry_net_cash_usd": cash,
        "terminal_pnl_if_qqq_zero_usd": terminal_pnl(cash, nl, ns, kl, ks, 0.0),
        "max_terminal_loss_usd": max(0.0, -min(pnls)), "max_terminal_profit_usd": max(pnls)}

def whole_units(nav: float, pct: float, loss: float | None) -> int | None:
    if loss is None or not math.isfinite(loss) or loss <= 0: return None
    return max(0, math.floor(nav * pct / loss + 1e-9))

def mark_pnl(state: dict[str, Any], step: dict[str, Any], slip: float, commission: float) -> float | None:
    value = float(state["cash"]); ns, nl = int(state["n_short"]), int(state["n_long"])
    if ns:
        row = step.get("short")
        if not quote_ok(row, "ask"): return None
        value -= ns * (MULT * float(row["ask"]) + MULT * slip + commission)
    if nl:
        row = step.get("long")
        if not quote_ok(row, "bid", zero_bid_mark=True): return None
        bid = float(row["bid"]); value += nl * MULT * bid
        if bid > 0: value -= nl * (MULT * slip + commission)
    return value

def close_shorts(state: dict[str, Any], step: dict[str, Any], qty: int, slip: float, commission: float) -> tuple[bool, str]:
    if qty <= 0 or qty > int(state["n_short"]): return False, "INVALID_SHORT_CLOSE_QUANTITY"
    row = step.get("short")
    if not quote_ok(row, "ask", executable=True, qty=qty): return False, "SHORT_ASK_OR_SIZE_INVALID"
    state["cash"] -= qty * (MULT * (float(row["ask"]) + slip) + commission); state["n_short"] -= qty
    return True, "OK"

def sell_longs(state: dict[str, Any], step: dict[str, Any], qty: int, slip: float, commission: float) -> tuple[bool, str]:
    if qty <= 0 or qty > int(state["n_long"]): return False, "INVALID_LONG_CLOSE_QUANTITY"
    row = step.get("long")
    if not quote_ok(row, "bid", executable=True, qty=qty): return False, "LONG_BID_OR_SIZE_INVALID"
    state["cash"] += qty * (MULT * (float(row["bid"]) - slip) - commission); state["n_long"] -= qty
    return True, "OK"

def act(state: dict[str, Any], step: dict[str, Any], action: str, direction: str, n: int,
        slip: float, commission: float, units: int = 1) -> tuple[bool, str]:
    if action == "FULL_CLOSE":
        if state["n_short"] and not quote_ok(step.get("short"), "ask", executable=True, qty=int(state["n_short"])):
            return False, "SHORT_ASK_OR_SIZE_INVALID"
        if state["n_long"] and not quote_ok(step.get("long"), "bid", executable=True, qty=int(state["n_long"])):
            return False, "LONG_BID_OR_SIZE_INVALID"
        if state["n_short"]:
            ok, why = close_shorts(state, step, int(state["n_short"]), slip, commission)
            if not ok: return False, why
        if state["n_long"]:
            ok, why = sell_longs(state, step, int(state["n_long"]), slip, commission)
            if not ok: raise AssertionError("Atomic preflight/execution mismatch")
        return True, "FULL_CLOSE_OK"
    if action == "CLOSE_SHORT_RISK":
        if state["n_short"] == 0: return True, "NO_SHORT_RISK_REMAINS"
        return close_shorts(state, step, int(state["n_short"]), slip, commission)
    if action == "TRIM_SHORT_RISK":
        current = int(state["n_short"])
        target_short = (units if n > 1 else 0) if direction == SHORT_HEAVY else 0
        qty = max(0, current - target_short)
        if qty == 0: return False, "NO_EXCESS_SHORT_TO_TRIM"
        return close_shorts(state, step, qty, slip, commission)
    return False, "UNKNOWN_ACTION"

def policies() -> list[dict[str, Any]]:
    rows = [{"name": "DTE7_CLOSE_SHORT_RISK", "kind": "DTE7"}]
    for pct in TRIGGER_PCTS:
        label = f"{pct*100:.1f}PCT"
        rows.append({"name": f"TP_{label}_FULL_CLOSE", "kind": "TP", "pct": pct, "action": "FULL_CLOSE"})
    for days in (3, 5):
        for pct in TRIGGER_PCTS:
            label = f"{pct*100:.1f}PCT"
            for action in ("FULL_CLOSE", "TRIM_SHORT_RISK"):
                rows.append({"name": f"FAST{days}_{label}_{action}", "kind": "FAST", "pct": pct, "days": days, "action": action})
    for action in ("FULL_CLOSE", "TRIM_SHORT_RISK"):
        rows.append({"name": f"DAY20_NONPOS_{action}", "kind": "DAY20", "action": action})
    for pct in TRIGGER_PCTS:
        label = f"{pct*100:.1f}PCT"
        rows.append({"name": f"SL_{label}_FULL_CLOSE", "kind": "SL", "pct": pct, "action": "FULL_CLOSE"})
    return rows

def simulate(trade: dict[str, Any], direction: str, n: int, nav: float, policy: dict[str, Any],
             slip: float, commission: float, units: int = 1,
             include_mark_path: bool = False) -> dict[str, Any]:
    nl_unit, ns_unit = quantities(direction, n)
    nl, ns = nl_unit*units, ns_unit*units
    state = {"cash": entry_cashflow(trade, nl, ns, slip, commission), "n_long": nl, "n_short": ns}
    custom_fired = False; trigger_age = None; action_age = None; pending = None
    policy_disabled_by_fallback = False; fallback_count = 0; deferred = missing = required = 0
    marks: list[float] = []; mark_curve: list[dict[str, Any]] = []
    final_pnl = None; final_status = "UNRESOLVED_SOURCE_END"; resolved_age = None
    path = trade.get("path") or []
    for age, step in enumerate(path):
        day = str(step.get("date", ""))[:10]
        try: dte = (date.fromisoformat(str(trade["expiry"])[:10]) - date.fromisoformat(day)).days
        except ValueError: dte = 9999
        if pending is not None and age > pending["signal_age"]:
            ok, _why = act(state, step, pending["action"], direction, n, slip, commission, units=units)
            if ok:
                if action_age is None: action_age = age
                pending = None
                if state["n_short"] == 0 and state["n_long"] == 0:
                    final_pnl, final_status, resolved_age = float(state["cash"]), "CLOSED_AT_OBSERVED_SIDE_QUOTES", age
            else: deferred += 1
        if state["n_short"] == 0 and state["n_long"] == 0:
            if include_mark_path:
                mark_curve.append({"date": day, "holding_age_sessions": age, "pnl_usd": round(float(state["cash"]), 4),
                    "vix": num(step.get("vix")), "dte": dte, "status": "CLOSED_AT_OBSERVED_SIDE_QUOTES",
                    "n_long_remaining": 0, "n_short_remaining": 0})
            break
        mark = mark_pnl(state, step, slip, commission); required += 1
        if mark is None: missing += 1
        else: marks.append(mark)
        if include_mark_path:
            mark_curve.append({"date": day, "holding_age_sessions": age,
                "pnl_usd": round(float(mark), 4) if mark is not None else None,
                "vix": num(step.get("vix")), "dte": dte,
                "status": "OPTION_SIDE_MARK" if mark is not None else "MISSING_OPTION_MARK",
                "n_long_remaining": int(state["n_long"]), "n_short_remaining": int(state["n_short"])})
        if dte <= 0:
            spot = num(step.get("spot"))
            if spot is None: final_status = "UNRESOLVED_MISSING_EXPIRY_UNDERLYING"
            else:
                final_pnl = terminal_pnl(float(state["cash"]), int(state["n_long"]), int(state["n_short"]),
                    float(trade["long_strike"]), float(trade["short_strike"]), spot)
                final_status, resolved_age = "EXPIRY_INTRINSIC_PROXY_NOT_BROKER_SETTLEMENT", age
                if include_mark_path and mark_curve and mark_curve[-1]["date"] == day:
                    mark_curve[-1]["pnl_usd"] = round(float(final_pnl), 4)
                    mark_curve[-1]["status"] = "EXPIRY_INTRINSIC_PROXY_NOT_BROKER_SETTLEMENT"
            break
        if pending is None and state["n_short"] > 0 and dte <= 7:
            pending = {"action": "CLOSE_SHORT_RISK", "signal_age": age}
            policy_disabled_by_fallback = True
            if policy["kind"] == "DTE7": custom_fired, trigger_age = True, age
            else: fallback_count += 1
            continue
        if pending is not None or custom_fired or policy_disabled_by_fallback or mark is None or age == 0: continue
        action = policy.get("action", "FULL_CLOSE"); target = nav * float(policy.get("pct", 0.0))
        fire = False
        if policy["kind"] == "TP": fire = mark >= target
        elif policy["kind"] == "FAST": fire = 1 <= age <= int(policy["days"]) and mark >= target
        elif policy["kind"] == "DAY20": fire = age >= 20 and mark <= 0
        elif policy["kind"] == "SL": fire = mark <= -target
        if fire:
            custom_fired, trigger_age = True, age
            pending = {"action": action, "signal_age": age}
    if final_pnl is None and state["n_short"] == 0 and state["n_long"] == 0:
        final_pnl, final_status = float(state["cash"]), "CLOSED_AT_OBSERVED_SIDE_QUOTES"
        if resolved_age is None: resolved_age = len(path)-1
    return {"trade_id":trade.get("trade_id"),"direction":direction,"ratio_n":n,"n_long":nl,"n_short":ns,
        "nav_usd":nav,"policy":policy["name"],"ratio_units":units,"slippage_per_leg":slip,"commission_per_contract_per_side":commission,
        "entry_date":trade.get("entry_date"),"expiry":trade.get("expiry"),"custom_triggered":trigger_age is not None,
        "custom_trigger_age_sessions":trigger_age,"first_action_age_sessions":action_age,
        "trigger_to_action_delay_sessions":action_age-trigger_age if action_age is not None and trigger_age is not None else None,
        "dte7_fallback_count":fallback_count,"deferred_action_sessions":deferred,"mark_rows_required":required,
        "missing_mark_rows":missing,"mark_coverage_pct":100*(required-missing)/required if required else None,
        "worst_observed_mark_pnl_usd":min(marks) if marks else None,"best_observed_mark_pnl_usd":max(marks) if marks else None,
        "final_pnl_usd":final_pnl,"final_pnl_pct_nav":final_pnl/nav*100 if final_pnl is not None else None,
        "final_status":final_status,"resolved_holding_sessions":resolved_age,"evidence":EVIDENCE,
        "mark_curve":mark_curve if include_mark_path else None}

def distribution(values: list[float]) -> dict[str, Any]:
    xs=sorted(float(x) for x in values if x is not None and math.isfinite(float(x)))
    if not xs: return {"n":0,"mean":None,"median":None,"p05":None,"p95":None}
    def q(p: float) -> float: return xs[min(len(xs)-1,max(0,int(round((len(xs)-1)*p))))]
    return {"n":len(xs),"mean":round(statistics.mean(xs),4),"median":round(statistics.median(xs),4),"p05":round(q(.05),4),"p95":round(q(.95),4)}

def wilson95(k: int, n: int) -> tuple[float | None,float | None]:
    if n<=0: return None,None
    z=1.959963984540054; p=k/n; den=1+z*z/n
    c=(p+z*z/(2*n))/den; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return 100*(c-h),100*(c+h)

def load_prices(path: Path) -> list[dict[str,Any]]:
    rows=[]
    with path.open(newline="",encoding="utf-8") as fh:
        for r in csv.DictReader(fh): rows.append({"date":r.get("date",""),"close":num(r.get("raw_close")),"vix":num(r.get("vix"))})
    return sorted(rows,key=lambda x:x["date"])

def rv_bucket(rv: float | None) -> str | None:
    if rv is None:return None
    if rv<.15:return "RV20_LT15"
    if rv<.25:return "RV20_15_25"
    if rv<.35:return "RV20_25_35"
    return "RV20_GTE35"

def vix_bucket(v: float | None) -> str | None:
    if v is None:return None
    if v<15:return "VIX_LT15"
    if v<25:return "VIX_15_25"
    if v<35:return "VIX_25_35"
    return "VIX_GTE35"

def price_horizon_probabilities(rows: list[dict[str,Any]]) -> list[dict[str,Any]]:
    closes=[x.get("close") for x in rows]; lr=[None]*len(closes)
    for i in range(1,len(closes)):
        if closes[i] is not None and closes[i-1] is not None and closes[i]>0 and closes[i-1]>0:
            lr[i]=math.log(float(closes[i])/float(closes[i-1]))
    rv=[None]*len(closes)
    for i in range(20,len(closes)):
        win=lr[i-19:i+1]
        if len(win)==20 and all(x is not None for x in win): rv[i]=statistics.stdev([float(x) for x in win])*math.sqrt(252)
    result=[]
    for h in HORIZONS:
        groups={"ALL":[]}
        for i in range(len(closes)-h):
            chunk=closes[i:i+h+1]
            if any(x is None for x in chunk) or float(chunk[0])<=0 or float(chunk[-1])<=0:continue
            row={"start_index":i,"ret":float(chunk[-1])/float(chunk[0])-1,"rv":rv[i],"vix":rows[i].get("vix")}
            groups["ALL"].append(row)
            rb=rv_bucket(row["rv"]); vb=vix_bucket(row["vix"])
            if rb:groups.setdefault(rb,[]).append(row)
            if vb:groups.setdefault(vb,[]).append(row)
        for label,items in sorted(groups.items()):
            rs=[float(x["ret"]) for x in items]; n=len(rs)
            if not n:result.append({"horizon_sessions":h,"state":label,"n":0});continue
            q=lambda p: sorted(rs)[min(n-1,max(0,int(round((n-1)*p))))]
            k5=sum(x<=-.05 for x in rs); lo,hi=wilson95(k5,n)
            offsets=[]
            for off in range(max(1,h)):
                sub=[x for x in items if x["start_index"]%h==off]
                if sub:offsets.append(100*sum(x["ret"]<=-.05 for x in sub)/len(sub))
            rvvals=[float(x["rv"]) for x in items if x.get("rv") is not None]
            vol=statistics.stdev([math.log1p(x) for x in rs if x>-1]) if len(rs)>1 else None
            mrv=statistics.median(rvvals) if rvvals else None
            ratio=vol/(mrv*math.sqrt(h/252)) if vol is not None and mrv and mrv>0 else None
            result.append({"horizon_sessions":h,"state":label,"n":n,"p_positive_pct":round(100*sum(x>0 for x in rs)/n,4),
                "p_down_3pct_pct":round(100*sum(x<=-.03 for x in rs)/n,4),"p_down_5pct_pct":round(100*k5/n,4),
                "p_down_5pct_wilson95_nominal_low":round(lo,4) if lo is not None else None,
                "p_down_5pct_wilson95_nominal_high":round(hi,4) if hi is not None else None,
                "p_down_10pct_pct":round(100*sum(x<=-.10 for x in rs)/n,4),"p_up_5pct_pct":round(100*sum(x>=.05 for x in rs)/n,4),
                "p05_return_pct":round(100*q(.05),4),"median_return_pct":round(100*q(.5),4),"p95_return_pct":round(100*q(.95),4),
                "nonoverlap_p_down5_min_pct":round(min(offsets),4) if offsets else None,
                "nonoverlap_p_down5_max_pct":round(max(offsets),4) if offsets else None,
                "median_rv20_pct":round(100*mrv,4) if mrv is not None else None,"rv_sqrt_time_scale_ratio":round(ratio,4) if ratio is not None else None})
    return result

def build_risk_matrix(trades: list[dict[str,Any]], navs: tuple[float,...] = NAVS) -> list[dict[str,Any]]:
    rows=[]
    for direction in (SHORT_HEAVY,LONG_HEAVY):
        for n in RATIOS:
            nl,ns=quantities(direction,n); env=[]
            for t in trades:
                if entry_size_ok(t,direction,n):env.append(terminal_envelope(t,nl,ns,.05,.65))
            losses=[x["max_terminal_loss_usd"] for x in env]; p95=distribution(losses)["p95"] if losses else None
            worst=max(losses) if losses else None; zero=[x["terminal_pnl_if_qqq_zero_usd"] for x in env]
            for nav in navs:
                budgets={}
                for pct in BUDGET_PCTS:
                    budgets[f"budget_{pct*100:g}pct_nav"]={"budget_usd":round(nav*pct,2),
                        "whole_units_using_worst_terminal_loss":whole_units(nav,pct,worst),
                        "whole_units_using_p95_sensitivity":whole_units(nav,pct,p95)}
                rows.append({"direction":direction,"ratio_n":n,"n_long":nl,"n_short":ns,"nav_usd":nav,
                    "cohort_episodes":len(trades),"depth_qualified":len(env),"depth_skipped":len(trades)-len(env),
                    "terminal_loss_median_usd":distribution(losses)["median"] if losses else None,
                    "terminal_loss_p95_usd":p95,"terminal_loss_worst_usd":worst,
                    "terminal_loss_worst_pct_nav":round(100*worst/nav,4) if worst is not None else None,
                    "pnl_if_qqq_zero_median_usd":distribution(zero)["median"] if zero else None,
                    "risk_budgets":budgets,"capacity_status":"TERMINAL_PAYOFF_ONLY_NOT_BROKER_MARGIN"})
    return rows

def summarize_policy(res: list[dict[str,Any]], direction: str, n: int, nav: float, policy: dict[str,Any],
                     cost: dict[str,Any], risk_budget_pct: float, units: int | None, sizing_status: str,
                     qualified: int, skipped: int) -> dict[str,Any]:
    closed=[x for x in res if x["final_pnl_usd"] is not None]; pnls=[float(x["final_pnl_usd"]) for x in closed]
    wins=[x for x in pnls if x>0]; losses=[x for x in pnls if x<0]; grossloss=abs(sum(losses))
    required=sum(x["mark_rows_required"] for x in res); missing=sum(x["missing_mark_rows"] for x in res)
    return {"direction":direction,"ratio_n":n,"n_long":quantities(direction,n)[0],"n_short":quantities(direction,n)[1],
        "nav_usd":nav,"policy":policy["name"],"cost_case":cost["name"],"tail_risk_budget_pct":risk_budget_pct,
        "ratio_units":units,"sizing_status":sizing_status,"slippage_per_leg":cost["slippage"],
        "commission_per_contract_per_side":cost["commission"],"cohort_episodes":len(res)+skipped,
        "depth_qualified_episodes":qualified,"depth_skipped":skipped,"resolved":len(closed),"unresolved":len(res)-len(closed),
        "net_pnl_sum_usd":round(sum(pnls),2) if pnls else None,"net_pnl_sum_pct_nav":round(sum(pnls)/nav*100,6) if pnls else None,
        "expectancy_usd_per_unit":round(statistics.mean(pnls),2) if pnls else None,"median_trade_pnl_usd":round(statistics.median(pnls),2) if pnls else None,
        "win_rate_pct":round(100*len(wins)/len(pnls),4) if pnls else None,"profit_factor":round(sum(wins)/grossloss,6) if grossloss>0 else None,
        "worst_trade_usd":round(min(pnls),2) if pnls else None,"best_trade_usd":round(max(pnls),2) if pnls else None,
        "median_worst_mark_pnl_usd":round(statistics.median([x["worst_observed_mark_pnl_usd"] for x in res if x["worst_observed_mark_pnl_usd"] is not None]),2) if any(x["worst_observed_mark_pnl_usd"] is not None for x in res) else None,
        "custom_trigger_count":sum(bool(x["custom_triggered"]) for x in res),
        "custom_trigger_pct":round(100*sum(bool(x["custom_triggered"]) for x in res)/len(res),4) if res else None,
        "median_trigger_age_sessions":distribution([x["custom_trigger_age_sessions"] for x in res if x["custom_trigger_age_sessions"] is not None])["median"],
        "median_trigger_to_action_delay_sessions":distribution([x["trigger_to_action_delay_sessions"] for x in res if x["trigger_to_action_delay_sessions"] is not None])["median"],
        "dte7_fallback_count":sum(x["dte7_fallback_count"] for x in res),"deferred_action_sessions":sum(x["deferred_action_sessions"] for x in res),
        "mark_coverage_pct":round(100*(required-missing)/required,4) if required else None,
        "median_resolution_age_sessions":distribution([x["resolved_holding_sessions"] for x in closed if x["resolved_holding_sessions"] is not None])["median"],
        "interpretation":"fixed one-unit cohort; EOD quote-side estimates, not fills"}

def build_policy_matrix(trades: list[dict[str,Any]], risk_rows: list[dict[str,Any]], navs: tuple[float,...] = NAVS) -> list[dict[str,Any]]:
    out=[]
    for direction in (SHORT_HEAVY,LONG_HEAVY):
        for n in RATIOS:
            for nav in navs:
                risk=next(x for x in risk_rows if x["direction"]==direction and x["ratio_n"]==n and x["nav_usd"]==nav)
                for risk_pct in BUDGET_PCTS:
                    key=f"budget_{risk_pct*100:g}pct_nav"
                    units=risk["risk_budgets"][key]["whole_units_using_worst_terminal_loss"]
                    if units is None:
                        status="PENDING_NO_TAIL_ESTIMATE"; eligible=[]; skipped=len(trades)
                    elif units==0:
                        status="BLOCKED_ZERO_WHOLE_UNITS"; eligible=[]; skipped=len(trades)
                    else:
                        eligible=[t for t in trades if entry_size_ok(t,direction,n,units)]
                        skipped=len(trades)-len(eligible)
                        status="SIZED_WITH_OBSERVED_DEPTH" if eligible else "BLOCKED_NO_EPISODE_HAS_REQUIRED_DEPTH"
                    for cost in COSTS:
                        for policy in policies():
                            res=[simulate(t,direction,n,nav,policy,cost["slippage"],cost["commission"],units=units)
                                 for t in eligible] if units else []
                            out.append(summarize_policy(res,direction,n,nav,policy,cost,risk_pct,units,status,len(eligible),skipped))
    return out

def write_csv(path: Path, rows: list[dict[str,Any]]) -> None:
    if not rows:path.write_text("",encoding="utf-8");return
    keys=[]
    for row in rows:
        for key in row:
            if key not in keys:keys.append(key)
    with path.open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=keys,extrasaction="ignore");w.writeheader()
        for row in rows:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in row.items()})


def mid_price(row: Any) -> float | None:
    if not isinstance(row, dict):
        return None
    bid, ask = num(row.get("bid")), num(row.get("ask"))
    if bid is None or ask is None or bid < 0 or ask <= 0 or bid > ask:
        return None
    return (bid + ask) / 2.0


def friction_observations(trade: dict[str, Any], nl: int, ns: int,
                          slip: float, commission: float) -> list[dict[str, Any]]:
    """Reconcile midpoint value to conservative quote-side liquidation value at each observed mark."""
    quotes = trade.get("entry_quotes") or {}
    long_mid, short_mid = mid_price(quotes.get("long")), mid_price(quotes.get("short"))
    if long_mid is None or short_mid is None:
        return []
    midpoint_entry_cash = MULT * (ns * short_mid - nl * long_mid)
    execution_state = {
        "cash": entry_cashflow(trade, nl, ns, slip, commission),
        "n_long": nl, "n_short": ns,
    }
    out = []
    expiry = str(trade.get("expiry", ""))[:10]
    for age, step in enumerate(trade.get("path") or []):
        lm, sm = mid_price(step.get("long")), mid_price(step.get("short"))
        if lm is None or sm is None:
            continue
        side_mark = mark_pnl(execution_state, step, slip, commission)
        if side_mark is None:
            continue
        mid_mark = midpoint_entry_cash - ns * MULT * sm + nl * MULT * lm
        friction = mid_mark - side_mark
        try:
            dte = int(num(step.get("dte"))) if num(step.get("dte")) is not None else (
                date.fromisoformat(expiry) - date.fromisoformat(str(step.get("date"))[:10])
            ).days
        except (ValueError, TypeError):
            dte = None
        vix = num(step.get("vix"))
        vb = "VIX_UNKNOWN" if vix is None else (
            "VIX_LT15" if vix < 15 else "VIX_15_25" if vix < 25 else "VIX_25_35" if vix < 35 else "VIX_GTE35"
        )
        db = "DTE_UNKNOWN" if dte is None else (
            "DTE_LE7" if dte <= 7 else "DTE_8_20" if dte <= 20 else "DTE_21_40" if dte <= 40 else "DTE_GT40"
        )
        exit_depth = (
            quote_ok(step.get("short"), "ask", executable=True, qty=ns)
            and quote_ok(step.get("long"), "bid", executable=True, qty=nl)
        )
        out.append({
            "age": age, "date": step.get("date"), "vix": vix, "dte": dte,
            "state_labels": ("OVERALL", vb, db),
            "midpoint_mark_pnl_usd": mid_mark,
            "quoted_side_net_liquidation_pnl_usd": side_mark,
            "friction_drag_usd": friction,
            "exit_depth_qualified": bool(exit_depth),
        })
    return out


def build_friction_bar_matrix(trades: list[dict[str, Any]], risk_rows: list[dict[str, Any]],
                              navs: tuple[float, ...]) -> list[dict[str, Any]]:
    rows = []
    for direction in (SHORT_HEAVY, LONG_HEAVY):
        for n in RATIOS:
            nl_unit, ns_unit = quantities(direction, n)
            for nav in navs:
                risk = next(x for x in risk_rows if x["direction"] == direction and x["ratio_n"] == n and x["nav_usd"] == nav)
                for budget_pct in BUDGET_PCTS:
                    key = f"budget_{budget_pct*100:g}pct_nav"
                    units = risk["risk_budgets"][key]["whole_units_using_worst_terminal_loss"]
                    eligible = [t for t in trades if units and entry_size_ok(t, direction, n, units)]
                    status = ("PENDING_NO_TAIL_ESTIMATE" if units is None else
                              "BLOCKED_ZERO_WHOLE_UNITS" if units == 0 else
                              "SIZED_WITH_OBSERVED_DEPTH" if eligible else "BLOCKED_NO_EPISODE_HAS_REQUIRED_DEPTH")
                    nl, ns = nl_unit * (units or 0), ns_unit * (units or 0)
                    for cost in COSTS:
                        grouped: dict[str, list[dict[str, Any]]] = {}
                        for trade in eligible:
                            obs = friction_observations(trade, nl, ns, cost["slippage"], cost["commission"])
                            by_label: dict[str, list[float]] = {}
                            depth_by_label: dict[str, list[bool]] = {}
                            for item in obs:
                                for label in item["state_labels"]:
                                    by_label.setdefault(label, []).append(item["friction_drag_usd"])
                                    depth_by_label.setdefault(label, []).append(item["exit_depth_qualified"])
                            for label, vals in by_label.items():
                                trade_stats = grouped.setdefault(label, [])
                                trade_stats.append({
                                    "trade_id": trade.get("trade_id"),
                                    "median_drag": statistics.median(vals),
                                    "p95_drag": distribution(vals)["p95"],
                                    "max_drag": max(vals),
                                    "mark_n": len(vals),
                                    "depth_pct": 100 * sum(depth_by_label[label]) / len(depth_by_label[label]),
                                })
                        labels = sorted(set(grouped) | {"OVERALL"})
                        if not eligible:
                            labels = ["OVERALL", "VIX_LT15", "VIX_15_25", "VIX_25_35", "VIX_GTE35",
                                      "DTE_LE7", "DTE_8_20", "DTE_21_40", "DTE_GT40"]
                        for label in labels:
                            stats = grouped.get(label, [])
                            medians = [x["median_drag"] for x in stats]
                            p95s = [x["p95_drag"] for x in stats]
                            bar50 = distribution(medians)["median"] if medians else None
                            bar95 = distribution(medians)["p95"] if medians else None
                            max_trade_p95 = max(p95s) if p95s else None
                            marks_n = sum(x["mark_n"] for x in stats)
                            depth_pct = statistics.mean([x["depth_pct"] for x in stats]) if stats else None
                            for target_pct in TRIGGER_PCTS:
                                target = nav * target_pct
                                rows.append({
                                    "direction": direction, "ratio_n": n, "nav_usd": nav,
                                    "tail_risk_budget_pct": budget_pct, "ratio_units": units,
                                    "sizing_status": status, "cost_case": cost["name"],
                                    "slippage_per_leg_usd": cost["slippage"],
                                    "commission_per_contract_per_side_usd": cost["commission"],
                                    "state": label, "target_pct_nav": target_pct,
                                    "net_profit_target_usd": target, "net_loss_stop_usd": -target,
                                    "episode_count": len(stats), "mark_observations": marks_n,
                                    "friction_bar_p50_episode_median_usd": round(bar50, 2) if bar50 is not None else None,
                                    "friction_bar_p95_episode_median_usd": round(bar95, 2) if bar95 is not None else None,
                                    "worst_episode_p95_friction_usd": round(max_trade_p95, 2) if max_trade_p95 is not None else None,
                                    "friction_p95_pct_of_nav": round(100*bar95/nav, 6) if bar95 is not None and nav else None,
                                    "net_target_to_friction_p95_ratio": round(target/bar95, 4) if bar95 is not None and bar95 > 0 else None,
                                    "midpoint_profit_needed_p50_usd": round(target+bar50, 2) if bar50 is not None else None,
                                    "midpoint_profit_needed_p95_usd": round(target+bar95, 2) if bar95 is not None else None,
                                    "midpoint_stop_line_equivalent_p50_usd": round(-target+bar50, 2) if bar50 is not None else None,
                                    "midpoint_stop_line_equivalent_p95_usd": round(-target+bar95, 2) if bar95 is not None else None,
                                    "exit_depth_qualified_pct": round(depth_pct, 4) if depth_pct is not None else None,
                                    "bar_definition": "p95 of per-episode median midpoint-to-side-mark drag; quote-mark reconciliation, not fills or an optimized trigger",
                                })
    return rows


def create_report(out: Path, prices: list[dict[str,Any]], trades: list[dict[str,Any]], risks: list[dict[str,Any]],
                  matrix: list[dict[str,Any]], probs: list[dict[str,Any]], friction_rows: list[dict[str,Any]],
                  navs: tuple[float,...]) -> dict[str,Any]:
    out.mkdir(parents=True,exist_ok=True)
    write_csv(out/"ratio_risk_capacity.csv",risks);write_csv(out/"ratio_exit_policy_matrix.csv",matrix)
    write_csv(out/"qqq_volatility_horizon_probabilities.csv",probs)
    write_csv(out/"friction_bar_matrix.csv",friction_rows)
    base=[x for x in matrix if x["cost_case"]==BASE_COST]
    policies_shown={"DTE7_CLOSE_SHORT_RISK","TP_1.0PCT_FULL_CLOSE","FAST3_1.0PCT_FULL_CLOSE","FAST3_1.0PCT_TRIM_SHORT_RISK",
        "FAST5_1.0PCT_FULL_CLOSE","FAST5_1.0PCT_TRIM_SHORT_RISK","DAY20_NONPOS_FULL_CLOSE","DAY20_NONPOS_TRIM_SHORT_RISK","SL_1.0PCT_FULL_CLOSE"}
    shown=[x for x in base if x["ratio_n"] in (1,5) and x["policy"] in policies_shown and x["tail_risk_budget_pct"]==0.01]
    meta={"research_id":"QQQ_PUT_RATIO_SCALE_VOLATILITY_V1","status":"RESEARCH_DIAGNOSTIC_ONLY_DEPLOYMENT_BLOCKED",
        "price_start":prices[0]["date"] if prices else None,"price_end":prices[-1]["date"] if prices else None,
        "price_expected_rows":len(prices),"price_valid_closes":sum(x["close"] is not None for x in prices),
        "option_cohort_episodes":len(trades),"option_source_end":SOURCE_END,"expected_option_sessions_missing_after_2025_12_15":11,
        "directions":[SHORT_HEAVY,LONG_HEAVY],"N_values":list(RATIOS),"NAVs":list(navs),
        "policy_summary_rows":len(matrix),"tail_risk_budgets_pct":list(BUDGET_PCTS),"volatility_probability_rows":len(probs),"source_evidence":EVIDENCE,
        "outputs":["ratio_risk_capacity.csv","ratio_exit_policy_matrix.csv","qqq_volatility_horizon_probabilities.csv","friction_bar_matrix.csv","qqq_put_ratio_scale_volatility_summary.md"],
        "blockers":["EOD quote mirror is not confirmed fills","history previously reviewed; not blind final OOS",
            "broker margin/assignment/forced liquidation unavailable","price movement probability is not option win probability"]}
    lines=["# QQQ Put Ratio: scale × exit × volatility/time","",
        "Status: RESEARCH DIAGNOSTIC ONLY; deployment remains BLOCKED.",
        f"Underlying sample: {meta['price_start']} to {meta['price_end']}; valid closes {meta['price_valid_closes']}/{meta['price_expected_rows']}.",
        f"Option cohort: {len(trades)} non-overlapping episodes; latest verified chain date {SOURCE_END}. Eleven expected option sessions through 2025-12-31 remain uncovered.",
        "NAV-relative triggers: $100,000 = $500/$1,000/$2,000; $1,000,000 = $5,000/$10,000/$20,000 for 0.5/1/2%. A fixed $1,000 is not an invariant rule.","",
        "## QQQ price-move frequencies — not option-profit probabilities","","| State | Sessions | N | P(up) | P(drop >=3%) | P(drop >=5%) | Nominal Wilson 95% for drop >=5% | P(drop >=10%) | P(up >=5%) | P05 | Median | P95 | sqrt-time ratio |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for x in probs:
        if x["state"] not in ("ALL","RV20_LT15","RV20_15_25","RV20_25_35","RV20_GTE35"):continue
        lo,hi=x.get("p_down_5pct_wilson95_nominal_low"),x.get("p_down_5pct_wilson95_nominal_high")
        ci="—" if lo is None else f"{lo}%–{hi}%"
        lines.append(f"| {x['state']} | {x['horizon_sessions']} | {x['n']} | {x.get('p_positive_pct')}% | {x.get('p_down_3pct_pct')}% | {x.get('p_down_5pct_pct')}% | {ci} | {x.get('p_down_10pct_pct')}% | {x.get('p_up_5pct_pct')}% | {x.get('p05_return_pct')}% | {x.get('median_return_pct')}% | {x.get('p95_return_pct')}% | {x.get('rv_sqrt_time_scale_ratio')} |")
    lines += ["","Wilson intervals are nominal: overlapping horizon events and serial dependence violate literal independent-trial assumptions. CSV non-overlap-offset ranges show sensitivity, not confidence bounds.",
        "RV20 buckets use trailing information available at the starting close: <15%, 15–25%, 25–35%, >=35%. Any window crossing a missing expected-session close is censored.","",
        "## Terminal-loss budget sizing — payoff envelope, not broker margin","","| Direction | N | Long/Short | NAV | Depth qualified/episodes | Median loss | P95 loss | Worst loss | Worst/NAV | Whole units at 0.5/1/2% budgets |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for x in risks:
        b=x["risk_budgets"]; u="/".join(str(b[f"budget_{p*100:g}pct_nav"]["whole_units_using_worst_terminal_loss"]) for p in BUDGET_PCTS)
        lines.append(f"| {x['direction']} | {x['ratio_n']} | {x['n_long']}/{x['n_short']} | USD {x['nav_usd']:,.0f} | {x['depth_qualified']}/{x['cohort_episodes']} | {x['terminal_loss_median_usd']} | {x['terminal_loss_p95_usd']} | {x['terminal_loss_worst_usd']} | {x['terminal_loss_worst_pct_nav']}% | {u} |")
    lines += ["","Terminal loss is the lowest payoff across the expiry knots, not merely the QQQ=$0 outcome. Whole-unit counts use the worst observed qualifying episode and are terminal payoff arithmetic only. N=1 is mechanically the same 1-long/1-short spread in either label.","",
        "## Cost tug-of-war BAR (base costs, 1% NAV target and 1% terminal-risk budget)",
        "",
        "The NAV target is the NET exit goal. The BAR estimates how far a midpoint-based gross mark would need to move to overcome observed spread crossing plus the selected slippage and commission assumptions. It is the P95 across per-episode median quote-mark drag, not a confirmed fill cost or an optimized trading rule.",
        "",
        "| Direction | N | NAV | Sized units | Sizing status | Cost BAR P50 | Cost BAR P95 | Net target | Midpoint gross needed (P95) | Target / BAR P95 | Exit depth |",
        "|---|---:|---:|---|---|---:|---:|---:|---:|---:|---:|"]
    barshown=[x for x in friction_rows if x["state"]=="OVERALL" and x["cost_case"]==BASE_COST and
        x["tail_risk_budget_pct"]==0.01 and x["target_pct_nav"]==0.01 and x["ratio_n"] in (1,5)]
    for x in barshown:
        fmt=lambda v: "—" if v is None else f"{v:.2f}"
        ratio= "—" if x["net_target_to_friction_p95_ratio"] is None else f"{x['net_target_to_friction_p95_ratio']:.2f}x"
        depth= "—" if x["exit_depth_qualified_pct"] is None else f"{x['exit_depth_qualified_pct']:.1f}%"
        lines.append(f"| {x['direction']} | {x['ratio_n']} | USD {x['nav_usd']:,.0f} | {x['ratio_units']} | {x['sizing_status']} | {fmt(x['friction_bar_p50_episode_median_usd'])} | {fmt(x['friction_bar_p95_episode_median_usd'])} | {fmt(x['net_profit_target_usd'])} | {fmt(x['midpoint_profit_needed_p95_usd'])} | {ratio} | {depth} |")
    lines += ["",
        "The friction_bar_matrix.csv also breaks the cost drag out by VIX and DTE state and shows all 0.5/1/2% targets, both NAV inputs, all N values, and zero/base/adverse cost scenarios. A missing BAR caused by no depth-qualified historical episodes is BLOCK/PENDING, never treated as zero friction.",
        "",
        "## Exit samples at base costs and 1% tail budget (full grid in CSV)","","| Direction | N | NAV | Tail budget | Sized units | Sizing status | Policy | Resolved/eligible | Net P&L | Expectancy | Win% | Worst trade | Trigger% | DTE7 fallback | Deferred | Mark coverage |",
        "|---|---:|---:|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for x in shown:
        lines.append(f"| {x['direction']} | {x['ratio_n']} | USD {x['nav_usd']:,.0f} | {x['tail_risk_budget_pct']*100:g}% | {x['ratio_units']} | {x['sizing_status']} | {x['policy']} | {x['resolved']}/{x['depth_qualified_episodes']} | {x['net_pnl_sum_usd']} | {x['expectancy_usd_per_unit']} | {x['win_rate_pct']}% | {x['worst_trade_usd']} | {x['custom_trigger_pct']}% | {x['dte7_fallback_count']} | {x['deferred_action_sessions']} | {x['mark_coverage_pct']}% |")
    lines += ["","## Self-audit / non-completion gates","",
        "- The option source reports a 16:00 ET preservation snapshot; exact quote timestamps and executable fills are not authenticated.",
        "- 2018–2025 has already been seen in previous repository research: DEVELOPMENT/REVISIT, not blind final OOS.",
        "- P(QQQ moves down 5%) is not P(a given option ratio loses 5% NAV): IV/skew, DTE, strikes, spreads, depth, costs and action lag intervene.",
        "- No app sizing policy, Frozen Original Hybrid, main branch or broker-order permission changed.",
        "- Deployment stays BLOCKED pending unseen OOS, decision-time/fill evidence and broker margin/assignment/forced-liquidation treatment."]
    (out/"qqq_put_ratio_scale_volatility_summary.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    (out/"qqq_put_ratio_scale_volatility_summary.json").write_text(json.dumps(meta,indent=2),encoding="utf-8")
    picked=[x for x in shown if x["ratio_n"] in (1,5)]
    ex=[x for x in probs if x["state"] in ("ALL","RV20_GTE35","VIX_GTE35") and x["horizon_sessions"] in (5,20,45)]
    fb=[x for x in friction_rows if x["state"]=="OVERALL" and x["cost_case"]==BASE_COST and
        x["ratio_n"] in (1,5) and x["tail_risk_budget_pct"]==0.01 and x["target_pct_nav"]==0.01]
    return {**meta,"selected_risk_capacity":[x for x in risks if x["ratio_n"] in (1,5)],
        "selected_policy_examples":picked,"selected_friction_bars":fb,"volatility_examples":ex}

def run(cohort_path: Path, price_path: Path, out: Path, navs: tuple[float,...] = NAVS) -> dict[str,Any]:
    trades=json.loads(cohort_path.read_text(encoding="utf-8")); prices=load_prices(price_path)
    if not trades:raise ValueError("No option episodes; refusing a zero-sample PASS.")
    if not prices:raise ValueError("Underlying price series is empty.")
    if not navs or any((not math.isfinite(float(x))) or float(x) <= 0 for x in navs):
        raise ValueError("NAV inputs must be finite positive USD values.")
    if len(set(float(x) for x in navs)) != len(navs):
        raise ValueError("Duplicate NAV inputs are not allowed.")
    navs=tuple(float(x) for x in navs)
    ds=[x["date"] for x in prices]
    if ds!=sorted(ds) or len(ds)!=len(set(ds)):raise ValueError("Price dates not unique ascending.")
    if prices[-1]["date"]!=SOURCE_END:raise ValueError(f"Expected source end {SOURCE_END}; got {prices[-1]['date']}")
    risks=build_risk_matrix(trades,navs); matrix=build_policy_matrix(trades,risks,navs)
    friction_rows=build_friction_bar_matrix(trades,risks,navs)
    probs=price_horizon_probabilities(prices)
    report=create_report(out,prices,trades,risks,matrix,probs,friction_rows,navs)
    (out/"qqq_put_ratio_scale_volatility_run.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    return report

def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort",type=Path,required=True);parser.add_argument("--prices",type=Path,required=True);parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--nav",type=float,action="append",default=None,help="NAV in USD; repeat to compare multiple capital pools. Defaults to 100000 and 1000000.")
    args=parser.parse_args();navs=tuple(args.nav) if args.nav else NAVS
    report=run(args.cohort,args.prices,args.out,navs=navs)
    print(json.dumps(report,indent=2))
    print((args.out/"qqq_put_ratio_scale_volatility_summary.md").read_text(encoding="utf-8"))

if __name__=="__main__":main()
