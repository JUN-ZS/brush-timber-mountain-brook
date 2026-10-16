#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

START = date.fromisoformat("2018-03-01")
END = date.fromisoformat("2026-09-04")
POOL = 100_000.0
MONTHLY = POOL / 120.0
INITIAL_NAV = 100_000.0
INITIAL_QQQ_PCT = 0.42

CORE_PCT = 0.42
VIX_HIGH = 28.0
TERM_SAFE = 0.05

MODELS = ("FULL_QQQ", "TARGET_42", "POOL_GATED")
STATES = ("CARRY", "WEAKENING", "PRE-SHOCK", "SHOCK")


def num(v):
    try:
        x = float(str(v).replace(",", "").strip())
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def sha256_file(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_spots(path: Path):
    rows = {}
    for r in read_csv(path):
        d = date.fromisoformat(r["Date"][:10])
        if d < START or d > END:
            continue
        qqq, vix = num(r.get("QQQ")), num(r.get("VIX"))
        if qqq is None or qqq <= 0 or vix is None or vix < 0:
            continue
        rows[d] = {"date": d, "qqq": qqq, "vix": vix}
    return rows


def load_term_from_file(path: Path):
    rows = {}
    for r in read_csv(path):
        d = date.fromisoformat(r["trade_date"][:10])
        if d < START or d > END:
            continue
        if d in rows:
            raise AssertionError("Duplicate Cboe trade date: %s" % d)
        m1, m2 = num(r.get("m1_settlement")), num(r.get("m2_settlement"))
        e1, e2 = date.fromisoformat(r["m1_expiry"][:10]), date.fromisoformat(r["m2_expiry"][:10])
        if m1 is None or m2 is None or m1 <= 0 or m2 <= 0:
            raise AssertionError("Invalid settlement at %s" % d)
        if not (d < e1 < e2):
            raise AssertionError("Expiry contract failed at %s: %s / %s" % (d, e1, e2))
        if not str(r.get("m1_code", "")).startswith("VX_") or not str(r.get("m2_code", "")).startswith("VX_"):
            raise AssertionError("Non-standard VX code at %s" % d)
        rows[d] = {
            "m1": m1, "m2": m2, "s": (m2 - m1) / m1,
            "m1_symbol": r.get("m1_code", ""), "m2_symbol": r.get("m2_code", ""),
            "m1_expiry": r.get("m1_expiry", ""), "m2_expiry": r.get("m2_expiry", ""),
            "source": r.get("source", ""), "source_url": r.get("source_m1_url", "")
        }
    return rows, [path]

def load_term_from_parts(parts_dir: Path):
    rows = {}
    files = sorted(parts_dir.glob("**/part_*.csv"))
    if len(files) < 2:
        raise AssertionError("Expected multiple Cboe collector parts, found %d" % len(files))
    for path in files:
        for r in read_csv(path):
            d = date.fromisoformat(r["trade_date"][:10])
            if d < START or d > END:
                continue
            if d in rows:
                raise AssertionError("Duplicate Cboe trade date: %s" % d)
            m1, m2 = num(r.get("m1_settlement")), num(r.get("m2_settlement"))
            e1 = date.fromisoformat(r["m1_expiry"][:10])
            e2 = date.fromisoformat(r["m2_expiry"][:10])
            if m1 is None or m2 is None or m1 <= 0 or m2 <= 0:
                raise AssertionError("Invalid settlement at %s" % d)
            if not (d < e1 < e2):
                raise AssertionError("Expiry contract failed at %s: %s / %s" % (d, e1, e2))
            if not str(r.get("m1_symbol", "")).startswith("VX/") or not str(r.get("m2_symbol", "")).startswith("VX/"):
                raise AssertionError("Non-standard VX symbol at %s" % d)
            rows[d] = {
                "m1": m1,
                "m2": m2,
                "s": (m2 - m1) / m1,
                "m1_symbol": r.get("m1_symbol", ""),
                "m2_symbol": r.get("m2_symbol", ""),
                "m1_expiry": r.get("m1_expiry", ""),
                "m2_expiry": r.get("m2_expiry", ""),
                "source": r.get("source", ""),
                "source_url": r.get("source_url", ""),
            }
    return rows, files


def regime(s, vix):
    if s is None or vix is None:
        return "BLOCKED"
    if vix >= VIX_HIGH and s <= 0:
        return "SHOCK"
    if s <= 0 or vix >= VIX_HIGH:
        return "PRE-SHOCK"
    if s <= TERM_SAFE:
        return "WEAKENING"
    return "CARRY"


def first_trading_day_by_month(days):
    out = {}
    for d in days:
        out.setdefault((d.year, d.month), d)
    return out


def next_day(days, d):
    i = days.index(d)
    return days[i + 1] if i + 1 < len(days) else None


def route_amount(model, nav_after_contribution, qqq_value, contribution, state):
    target_value = nav_after_contribution * CORE_PCT
    gap = max(target_value - qqq_value, 0.0)
    if model == "FULL_QQQ":
        to_qqq = contribution
    elif model == "TARGET_42":
        to_qqq = min(contribution, gap)
    elif model == "POOL_GATED":
        to_qqq = min(contribution, gap) if state in ("CARRY", "WEAKENING") else 0.0
    else:
        raise ValueError(model)
    return to_qqq, contribution - to_qqq, gap


def xnpv(rate, cashflows):
    if rate <= -0.999999:
        return float("inf")
    t0 = cashflows[0][0]
    return sum(amount / ((1.0 + rate) ** ((d - t0).days / 365.25)) for d, amount in cashflows)


def xirr(cashflows):
    lo, hi = -0.9999, 10.0
    f_lo, f_hi = xnpv(lo, cashflows), xnpv(hi, cashflows)
    while f_lo * f_hi > 0 and hi < 1e6:
        hi *= 2.0
        f_hi = xnpv(hi, cashflows)
    if f_lo * f_hi > 0:
        return None
    for _ in range(200):
        mid = (lo + hi) / 2.0
        f_mid = xnpv(mid, cashflows)
        if abs(f_mid) < 1e-8:
            return mid
        if f_lo * f_mid <= 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    return (lo + hi) / 2.0


def simulate(model, days, market, pool_months):
    initial_price = market[days[0]]["qqq"]
    shares = (INITIAL_NAV * INITIAL_QQQ_PCT) / initial_price
    reserve = INITIAL_NAV * (1.0 - INITIAL_QQQ_PCT)

    pending = defaultdict(float)
    events = []
    daily = []
    route_by_state = Counter()
    contributions = []
    pool_remaining = POOL

    for d in days:
        qqq = market[d]["qqq"]

        # Execute prior close routing decision at next observed session close.
        if pending[d] > 0:
            amount = pending.pop(d)
            bought_shares = amount / qqq
            shares += bought_shares
            reserve -= amount
            events.append({
                "date": d.isoformat(),
                "event": "EXECUTE_QQQ",
                "model": model,
                "amount": amount,
                "price": qqq,
                "shares": bought_shares,
            })

        if d in pool_months:
            contribution = min(MONTHLY, pool_remaining)
            pool_remaining -= contribution
            reserve += contribution
            contributions.append((d, -contribution))

            term = market[d]["term"]
            state = regime(term["s"], market[d]["vix"])
            nav_after = reserve + shares * qqq
            qqq_value = shares * qqq
            to_qqq, to_reserve, gap = route_amount(
                model, nav_after, qqq_value, contribution, state
            )

            ex = next_day(days, d)
            if ex is not None and to_qqq > 0:
                pending[ex] += to_qqq
            elif to_qqq > 0:
                to_reserve += to_qqq
                to_qqq = 0.0

            route_by_state[(state, "QQQ")] += to_qqq
            route_by_state[(state, "RESERVE")] += to_reserve
            events.append({
                "date": d.isoformat(),
                "execution_date": ex.isoformat() if ex else None,
                "event": "ROUTE_NEW_CAPITAL",
                "model": model,
                "state": state,
                "contribution": contribution,
                "to_qqq": to_qqq,
                "to_reserve": to_reserve,
                "qqq_value_before": qqq_value,
                "nav_after_contribution": nav_after,
                "qqq_target_value": nav_after * CORE_PCT,
                "qqq_gap": gap,
            })

        nav = reserve + shares * qqq
        qqq_value = shares * qqq
        daily.append({
            "date": d,
            "nav": nav,
            "qqq_value": qqq_value,
            "qqq_pct": qqq_value / nav if nav > 0 else None,
            "reserve": reserve,
        })

    if pending:
        leftover = sum(pending.values())
        reserve += leftover
        daily[-1]["reserve"] += leftover
        daily[-1]["nav"] += leftover
        daily[-1]["qqq_value"] = shares * market[days[-1]]["qqq"]
        daily[-1]["qqq_pct"] = daily[-1]["qqq_value"] / daily[-1]["nav"]
        events.append({
            "date": days[-1].isoformat(),
            "event": "PENDING_RETURNED_TO_RESERVE",
            "model": model,
            "amount": leftover,
        })
        pending.clear()

    peak = 0.0
    max_dd = 0.0
    for r in daily:
        peak = max(peak, r["nav"])
        r["drawdown"] = r["nav"] / peak - 1.0 if peak > 0 else 0.0
        max_dd = min(max_dd, r["drawdown"])

    cashflows = [(days[0], -INITIAL_NAV)] + contributions + [(days[-1], daily[-1]["nav"])]
    return {
        "model": model,
        "daily": daily,
        "events": events,
        "xirr": xirr(cashflows),
        "max_dd": max_dd,
        "terminal_nav": daily[-1]["nav"],
        "terminal_qqq_pct": daily[-1]["qqq_pct"],
        "terminal_qqq_shares": shares,
        "terminal_qqq_price": market[days[-1]]["qqq"],
        "terminal_reserve": daily[-1]["reserve"],
        "total_contributed": sum(-x[1] for x in contributions),
        "pool_remaining": pool_remaining,
        "qqq_bought": sum(v for (state, kind), v in route_by_state.items() if kind == "QQQ"),
        "reserve_added": sum(v for (state, kind), v in route_by_state.items() if kind == "RESERVE"),
        "route_by_state": route_by_state,
    }


def validate(spots, terms, days, pool_months):
    assert days[0] <= START
    assert days[-1] >= date(2026, 9, 1), "Unexpected terminal date: %s" % days[-1]
    assert len(days) >= 2000, "Too few overlap sessions: %d" % len(days)
    assert len(terms) >= 2000, "Too few Cboe term rows: %d" % len(terms)
    assert len(set(days)) == len(days)

    spot_dates = sorted(spots)
    term_dates = sorted(terms)
    missing_term = sorted(set(spot_dates) - set(term_dates))
    missing_spot = sorted(set(term_dates) - set(spot_dates))
    assert len(missing_term) <= 25, "Too many spot dates without Cboe term: %d" % len(missing_term)
    assert len(missing_spot) <= 25, "Too many Cboe dates without spot: %d" % len(missing_spot)
    assert len(pool_months) == min(120, len(first_trading_day_by_month(days)))

    return {
        "overlap_sessions": len(days),
        "missing_term_dates": [d.isoformat() for d in missing_term[:25]],
        "missing_spot_dates": [d.isoformat() for d in missing_spot[:25]],
        "monthly_tranches": len(pool_months),
    }


def summary(result):
    routes = {
        state: {
            "qqq": result["route_by_state"].get((state, "QQQ"), 0.0),
            "reserve": result["route_by_state"].get((state, "RESERVE"), 0.0),
        }
        for state in STATES
    }
    return {
        "model": result["model"],
        "xirr": result["xirr"],
        "max_drawdown": result["max_dd"],
        "terminal_nav": result["terminal_nav"],
        "terminal_qqq_pct": result["terminal_qqq_pct"],
        "terminal_reserve": result["terminal_reserve"],
        "total_contributed": result["total_contributed"],
        "pool_remaining": result["pool_remaining"],
        "qqq_bought": result["qqq_bought"],
        "reserve_added": result["reserve_added"],
        "routes": routes,
        "events": len(result["events"]),
        "terminal_qqq_shares": result["terminal_qqq_shares"],
        "terminal_qqq_price": result["terminal_qqq_price"],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spots", required=True)
    ap.add_argument("--cboe-parts")
    ap.add_argument("--cboe-file")
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    spots_path = Path(args.spots)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    if bool(args.cboe_parts) == bool(args.cboe_file):
        raise SystemExit("Provide exactly one of --cboe-file or --cboe-parts")

    spots = load_spots(spots_path)
    if args.cboe_file:
        terms, part_files = load_term_from_file(Path(args.cboe_file))
    else:
        terms, part_files = load_term_from_parts(Path(args.cboe_parts))
    overlap = sorted(set(spots) & set(terms))
    market = {
        d: {
            **spots[d],
            "term": terms[d],
            "state": regime(terms[d]["s"], spots[d]["vix"]),
        }
        for d in overlap
    }
    days = sorted(market)

    month_first = first_trading_day_by_month(days)
    pool_months = [month_first[k] for k in sorted(month_first)][:120]
    integrity = validate(spots, terms, days, pool_months)
    state_counts = Counter(market[d]["state"] for d in days)

    # Exact Cell 15 routing invariants.
    cases = []
    for state in STATES:
        to, res, gap = route_amount("POOL_GATED", 105_000.0, 10_000.0, 5_000.0, state)
        cases.append({
            "state": state,
            "to_qqq": to,
            "to_reserve": res,
            "gap": gap,
            "expected": "ALLOW_QQQ" if state in ("CARRY", "WEAKENING") else "RESERVE",
        })
    assert cases[0]["to_qqq"] == 5000.0
    assert cases[1]["to_qqq"] == 5000.0
    assert cases[2]["to_qqq"] == 0.0
    assert cases[3]["to_qqq"] == 0.0

    results = {model: simulate(model, days, market, pool_months) for model in MODELS}
    sums = {model: summary(result) for model, result in results.items()}

    gated = sums["POOL_GATED"]
    t42 = sums["TARGET_42"]
    terminal_delta = gated["terminal_nav"] - t42["terminal_nav"]
    xirr_delta = gated["xirr"] - t42["xirr"] if gated["xirr"] is not None and t42["xirr"] is not None else None
    dd_delta = gated["max_drawdown"] - t42["max_drawdown"]

    if terminal_delta > 1e-8 and dd_delta >= -1e-12:
        verdict = "POOL_GATED_DOMINATES_TARGET42"
    elif terminal_delta < -1e-8 and dd_delta > 1e-6:
        verdict = "RISK_RETURN_TRADEOFF"
    elif terminal_delta < -1e-8:
        verdict = "RETURN_COST"
    else:
        verdict = "NO_CLEAR_INCREMENTAL_VALUE"

    report = {
        "research_id": "QQQ_STRATEGY_POOL_DEPLOYMENT_REPLAY_V1",
        "status": "REPLAY_COMPLETE",
        "base_head": "38e4c93fc81e255f9c461f365b494c9d54a91e05",
        "research_question": "Does current Strategy Pool routing add deployment value without changing frozen strategy policy?",
        "frozen_policy": {
            "engine_version": "V3-FREE-VX-PROVENANCE-2",
            "policy_version": "ORIGINAL_HYBRID_BASELINE_FROZEN",
            "qqq_core_target_pct": 42.0,
            "vix_high": 28.0,
            "term_safe_pct": 5.0,
        },
        "pool_contract": {
            "pool": POOL,
            "months": 120,
            "monthly_tranche": MONTHLY,
            "replayed_months": len(pool_months),
            "remaining_pool_after_window": POOL - len(pool_months) * MONTHLY,
        },
        "causality": {
            "contribution": "first observed trading session of each month at close",
            "routing_decision": "same close",
            "execution": "next observed trading session close",
            "same_close_lookahead": False,
        },
        "data": {
            "start": days[0].isoformat(),
            "end": days[-1].isoformat(),
            "overlap_sessions": len(days),
            "cboe_rows": len(terms),
            "cboe_part_files": [str(p) for p in part_files],
            "spots_sha256": sha256_file(spots_path),
            "term_source": "CBOE_VX_CONTRACT_ARCHIVE_DAILY_SETTLEMENT",
            "cboe_artifact_run_id": 37506316510,
            "cboe_artifact_id": 11431373794,
            "cboe_artifact_digest": "sha256:9df5be92107f4cf03c4ada406b125bbafdd060add3c144db73da452e7aec4337",
            "term_definition": "standard monthly VX only; expiry > trade date; M1/M2 sorted by actual expiry; S=(M2-M1)/M1",
            "integrity": integrity,
        },
        "controls": {
            "FULL_QQQ": "100% of each monthly tranche to QQQ",
            "TARGET_42": "fill 42% QQQ target gap independent of regime",
            "POOL_GATED": "current Cell 15: fill 42% QQQ target gap only in CARRY/WEAKENING; defensive capital remains reserve",
        },
        "cell15_invariants": cases,
        "state_counts": dict(state_counts),
        "results": sums,
        "primary_comparison": {
            "control": "TARGET_42",
            "pool_gated_minus_target42_terminal_nav": terminal_delta,
            "pool_gated_minus_target42_xirr": xirr_delta,
            "pool_gated_minus_target42_maxdd": dd_delta,
            "verdict": verdict,
            "interpretation": "No optimisation. Read terminal NAV, XIRR, MaxDD and reserve together; idle cash is not automatically alpha.",
        },
        "notes": [
            "Deployment-layer replay only; not a full Original Hybrid P&L replay.",
            "No VIX-to-M1/M2 reconstruction.",
            "No options, VXX P&L, fees, slippage, or broker fills.",
            "B/120 is a research interpretation of Strategy Pool and is not yet a targetLedger rule."
        ],
    }

    (out / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    fields = [
        "model","xirr","max_drawdown","terminal_nav","terminal_qqq_pct",
        "terminal_reserve","total_contributed","pool_remaining",
        "qqq_bought","reserve_added","events"
    ]
    with (out / "summary.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for model in MODELS:
            w.writerow({k: sums[model][k] for k in fields})

    for model, result in results.items():
        with (out / (model.lower() + "_daily.csv")).open("w", newline="", encoding="utf-8") as f:
            f2 = ["date","nav","qqq_value","qqq_pct","reserve","drawdown"]
            w = csv.DictWriter(f, fieldnames=f2)
            w.writeheader()
            for row in result["daily"]:
                w.writerow({**row, "date": row["date"].isoformat()})

        with (out / (model.lower() + "_events.csv")).open("w", newline="", encoding="utf-8") as f:
            event_fields = sorted({k for e in result["events"] for k in e})
            w = csv.DictWriter(f, fieldnames=event_fields)
            w.writeheader()
            w.writerows(result["events"])

    md = [
        "# Strategy Pool -> Actual Deployment Replay V1",
        "",
        "Window: %s -> %s (%d overlap sessions)" % (days[0], days[-1], len(days)),
        "Pool: $%0.0f / 120 = $%0.2f monthly tranche; replayed months %d; remaining pool $%0.2f" %
        (POOL, MONTHLY, len(pool_months), POOL - len(pool_months) * MONTHLY),
        "",
        "## Controlled variants",
        "",
        "| Variant | XIRR | MaxDD | Terminal NAV | Terminal QQQ % | Terminal Reserve |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for model in MODELS:
        s = sums[model]
        md.append(
            "| %s | %s | %.2f%% | $%.2f | %.2f%% | $%.2f |" %
            (model,
             "NA" if s["xirr"] is None else "%.4f%%" % (s["xirr"] * 100),
             s["max_drawdown"] * 100,
             s["terminal_nav"],
             s["terminal_qqq_pct"] * 100,
             s["terminal_reserve"])
        )
    md += [
        "",
        "## Primary A/B",
        "",
        "POOL_GATED - TARGET_42 terminal NAV: $%.2f" % terminal_delta,
        "POOL_GATED - TARGET_42 XIRR: %s" % ("NA" if xirr_delta is None else "%.4f%%" % (xirr_delta * 100)),
        "POOL_GATED - TARGET_42 MaxDD: %.2f%%" % (dd_delta * 100),
        "Automatic reading: %s" % verdict,
        "",
        "The gate is not called an improvement merely because it holds reserve. Downside, return and remaining reserve must be read together.",
        "",
        "## Exact Cell 15 routing",
        "- CARRY -> QQQ target-gap fill",
        "- WEAKENING -> QQQ target-gap fill",
        "- PRE-SHOCK -> reserve",
        "- SHOCK -> reserve",
        "",
        "## Data",
        "- Official Cboe daily settlement M1/M2; standard monthly VX only.",
        "- Expiry strictly later than trade date.",
        "- No VIX proxy for term structure.",
        "- Same-close lookahead avoided.",
        "",
        "Source spot SHA256: %s" % sha256_file(spots_path),
    ]
    (out / "report.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print(json.dumps({
        "status": "REPLAY_COMPLETE",
        "research_id": report["research_id"],
        "days": len(days),
        "cboe_rows": len(terms),
        "pool_months": len(pool_months),
        "comparison": report["primary_comparison"],
        "summaries": sums,
        "state_counts": dict(state_counts),
    }, indent=2))


if __name__ == "__main__":
    main()
