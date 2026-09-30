#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, math
from dataclasses import dataclass
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

START = pd.Timestamp("2011-01-01")
END = pd.Timestamp("2025-12-31")

N_SHORT = 10
SIGNAL_PCT_52W = 0.98
SIGNAL_EXT200 = 0.08
COOLDOWN_DAYS = 10

FAR_DTES = (90, 120, 180)
FAR_DELTAS = (0.05, 0.08, 0.10)

NEAR_DTES = (7, 14, 21, 30)
LONG_DELTA = 0.50
MAX_STACK = 5

# Three aggressiveness levels for the dynamic near-long inventory.
# The actual stack is then adjusted by delta/distance/gamma state.
COVERAGE_MULTS = (0.75, 1.00, 1.50)

# Paired harvest/reload policies. Each policy is evaluated for every
# near DTE and far DTE/delta combination.
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

REFERENCE_CAPITAL_USD = 500000.0 / 7.8


@dataclass
class Pos:
    entry: pd.Timestamp
    expiry: pd.Timestamp
    cid: str
    strike: float
    delta: float
    cost: float
    target_dte: int
    peak_bid: float = 0.0
    closed: bool = False
    exit: pd.Timestamp | None = None
    exit_price: float | None = None
    pnl: float | None = None


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_underlying(path: Path) -> pd.DataFrame:
    x = pd.read_parquet(path)
    x.columns = [c.lower() for c in x.columns]
    x["date"] = pd.to_datetime(x["date"]).dt.tz_localize(None).dt.normalize()
    x = x.sort_values("date").drop_duplicates("date")
    x = x[(x.date >= START) & (x.date <= END)].copy()
    x["dma200"] = x.close.rolling(200, min_periods=200).mean()
    x["high52w"] = x.close.rolling(252, min_periods=252).max()
    x["ext200"] = x.close / x.dma200 - 1.0
    x["ratio52"] = x.close / x.high52w
    x["signal"] = (x.ratio52 >= SIGNAL_PCT_52W) & (x.ext200 >= SIGNAL_EXT200)
    x["ret1d"] = x.close.pct_change()
    return x.reset_index(drop=True)


def read_options(con, path, sql, params):
    return con.execute(sql, [str(path), *params]).df()


def option_columns(con, path: Path) -> set[str]:
    z = con.execute("DESCRIBE SELECT * FROM read_parquet(?)", [str(path)]).df()
    return {str(x).lower() for x in z["column_name"]}


def pick_far(ch: pd.DataFrame, spot: float, dte_target: int, delta_target: float):
    if ch is None or ch.empty:
        return None
    g = ch[
        (ch.strike > float(spot))
        & ch.bid.notna() & ch.ask.notna() & ch.delta.notna()
        & (ch.ask >= ch.bid) & (ch.bid >= 0)
    ].copy()
    if g.empty:
        return None
    g["dte"] = (g.expiration - g.date).dt.days
    g = g[(g.dte >= 60) & (g.dte <= 210)]
    if g.empty:
        return None
    exp_score = g.groupby("expiration", as_index=False).agg(
        dte=("dte", "first"), volume=("volume", "sum")
    )
    exp_score["err"] = (exp_score.dte - dte_target).abs()
    ex = exp_score.sort_values(["err", "volume"], ascending=[True, False]).iloc[0].expiration
    z = g[g.expiration == ex].copy()
    z["derr"] = (z.delta.abs() - delta_target).abs()
    z = z.sort_values(["derr", "volume", "strike"], ascending=[True, False, True])
    r = z.iloc[0]
    out = {
        "cid": str(r.contract_id),
        "strike": float(r.strike),
        "delta": float(r.delta),
        "expiry": pd.Timestamp(r.expiration),
        "entry_bid": float(r.bid),
        "entry_ask": float(r.ask),
    }
    if "gamma" in r.index and pd.notna(r["gamma"]):
        out["gamma"] = float(r["gamma"])
    return out


def pick_near(ch: pd.DataFrame, spot: float, target_dte: int):
    if ch is None or ch.empty:
        return None
    g = ch[
        (ch.strike <= float(spot) * 1.02)
        & ch.bid.notna() & ch.ask.notna() & ch.delta.notna()
        & (ch.ask >= ch.bid) & (ch.bid >= 0)
    ].copy()
    if g.empty:
        return None
    g["dte"] = (g.expiration - g.date).dt.days
    g = g[(g.dte >= 7) & (g.dte <= 35)]
    if g.empty:
        return None

    exp_score = g.groupby("expiration", as_index=False).agg(
        dte=("dte", "first"), volume=("volume", "sum")
    )
    exp_score["err"] = (exp_score.dte - target_dte).abs()
    ex = exp_score.sort_values(["err", "volume"], ascending=[True, False]).iloc[0].expiration

    z = g[(g.expiration == ex) & (g.strike <= float(spot) * 1.01)].copy()
    if z.empty:
        return None
    z["derr"] = (z.delta.abs() - LONG_DELTA).abs()
    z = z.sort_values(["derr", "volume", "strike"], ascending=[True, False, True])
    r = z.iloc[0]
    return {
        "cid": str(r.contract_id),
        "strike": float(r.strike),
        "delta": float(r.delta),
        "expiry": pd.Timestamp(r.expiration),
        "entry_ask": float(r.ask),
    }


def build_far_candidates(u: pd.DataFrame, con, opt_path: Path):
    sigdates = [pd.Timestamp(d) for d in u.loc[u.signal & u.dma200.notna(), "date"]]
    if not sigdates:
        return {}

    has_gamma = "gamma" in option_columns(con, opt_path)
    gamma_select = ', CAST("gamma" AS DOUBLE) AS gamma' if has_gamma else ""
    ch = read_options(
        con, opt_path,
        f"""
        SELECT CAST(date AS DATE) AS date,
               CAST(expiration AS DATE) AS expiration,
               CAST(contract_id AS VARCHAR) AS contract_id,
               CAST(strike AS DOUBLE) AS strike,
               CAST(bid AS DOUBLE) AS bid,
               CAST(ask AS DOUBLE) AS ask,
               COALESCE(CAST(volume AS DOUBLE),0) AS volume,
               CAST(delta AS DOUBLE) AS delta
               {gamma_select}
        FROM read_parquet(?)
        WHERE CAST(date AS DATE) IN (SELECT * FROM UNNEST(?))
          AND UPPER("type")='CALL'
          AND delta IS NOT NULL
          AND bid IS NOT NULL AND ask IS NOT NULL
          AND ask >= bid AND bid >= 0
          AND CAST(expiration AS DATE) BETWEEN CAST(date AS DATE)+INTERVAL 60 DAY
                                            AND CAST(date AS DATE)+INTERVAL 210 DAY
        """,
        [[d.date() for d in sigdates]],
    )
    if ch.empty:
        return {}

    ch["date"] = pd.to_datetime(ch.date)
    ch["expiration"] = pd.to_datetime(ch.expiration)

    out = {}
    for d, g in ch.groupby("date", sort=False):
        out[d] = {}
        spot = float(u.loc[u.date == d, "close"].iloc[0])
        for fd in FAR_DTES:
            for delta in FAR_DELTAS:
                out[d][(fd, delta)] = pick_far(g, spot, fd, delta)
    return out, has_gamma


def get_quotes(con, opt_path: Path, ids, with_delta=False, with_gamma=False):
    if not ids:
        return pd.DataFrame()

    cols = "CAST(bid AS DOUBLE) AS bid, CAST(ask AS DOUBLE) AS ask"
    if with_delta:
        cols += ", CAST(delta AS DOUBLE) AS delta"
    if with_gamma:
        cols += ', CAST("gamma" AS DOUBLE) AS gamma'

    q = read_options(
        con, opt_path,
        f"""
        SELECT CAST(date AS DATE) AS date,
               CAST(contract_id AS VARCHAR) AS cid,
               {cols}
        FROM read_parquet(?)
        WHERE CAST(contract_id AS VARCHAR) IN (SELECT * FROM UNNEST(?))
          AND bid IS NOT NULL AND ask IS NOT NULL
          AND ask >= bid AND bid >= 0
        """,
        [list(map(str, ids))],
    )
    if q.empty:
        return q
    q["date"] = pd.to_datetime(q.date)
    q["cid"] = q.cid.astype(str)
    return q.sort_values(["cid", "date"]).drop_duplicates(["cid", "date"])


def quote_maps(q: pd.DataFrame):
    out = {}
    if q.empty:
        return out
    for cid, g in q.groupby("cid", sort=False):
        out[cid] = g.set_index("date").sort_index()
    return out


def campaign_rows(u, far_candidates, far_dte, far_delta):
    sigs = u[u.signal & u.dma200.notna()]
    rows = []
    next_allowed = None

    for _, sr in sigs.iterrows():
        d0 = pd.Timestamp(sr.date)
        if next_allowed is not None and d0 <= next_allowed:
            continue
        far = far_candidates.get(d0, {}).get((far_dte, far_delta))
        if not far:
            continue
        rows.append({"entry": d0, "far": far, "start_spot": float(sr.close)})

        fq = None
        # Actual far exit is determined later from the quote map.
        if far.get("expiry") is not None:
            next_allowed = d0 + pd.Timedelta(days=365)
    return rows


def target_from_state(
    far_delta_abs: float,
    distance_pct: float,
    gamma_rel: float,
    delta_jump: float,
    coverage_mult: float,
):
    # Each component is causal and bounded. Higher score means greater short-call risk.
    if far_delta_abs < 0.04:
        dscore = 1
    elif far_delta_abs < 0.06:
        dscore = 2
    elif far_delta_abs < 0.08:
        dscore = 3
    elif far_delta_abs < 0.10:
        dscore = 4
    else:
        dscore = 5

    if distance_pct > 0.10:
        xscore = 1
    elif distance_pct > 0.07:
        xscore = 2
    elif distance_pct > 0.04:
        xscore = 3
    elif distance_pct > 0.02:
        xscore = 4
    else:
        xscore = 5

    if gamma_rel < 1.20 and delta_jump < 0.01:
        gscore = 1
    elif gamma_rel < 1.50 and delta_jump < 0.02:
        gscore = 2
    else:
        gscore = 3

    base = int(math.ceil((coverage_mult * N_SHORT * far_delta_abs) / LONG_DELTA))
    composite = 0.50 * dscore + 0.30 * xscore + 0.20 * gscore
    boost = 2 if composite >= 4.2 else 1 if composite >= 3.2 else 0

    return max(1, min(MAX_STACK, base + boost)), {
        "dscore": dscore,
        "xscore": xscore,
        "gscore": gscore,
        "risk_score": composite,
    }


def should_harvest(policy: str, pos: Pos, dt: pd.Timestamp, bid: float, risk_score: float):
    dte = max(0, (pos.expiry - dt).days)
    ret = bid / pos.cost - 1.0 if pos.cost > 0 else -1.0
    pos.peak_bid = max(pos.peak_bid, bid)

    if dte <= 2 or dt >= pos.expiry:
        return True

    if policy.startswith("TP50") and ret >= 0.50:
        return True
    if policy.startswith("TP75") and ret >= 0.75:
        return True
    if policy.startswith("TP100") and ret >= 1.00:
        return True

    if policy.startswith("TRAIL20"):
        peak_ret = pos.peak_bid / pos.cost - 1.0 if pos.cost > 0 else -1.0
        if peak_ret >= 0.25 and bid <= pos.peak_bid * 0.80:
            return True

    # Risk policies also harvest a profitable leg when the state score falls.
    if "ON_RISK" in policy and ret > 0 and risk_score <= 2.2:
        return True

    if "COOLDOWN3" in policy and ret >= 0.75:
        return True

    return False


def reload_gate(policy: str, dt: pd.Timestamp, last_harvest, state, prev_state, desired, active_count):
    if desired <= active_count:
        return False

    # Avoid mechanically selling at the bid and rebuying the same chain on the same day.
    harvested_today = last_harvest is not None and dt == last_harvest
    if policy.endswith("IMMEDIATE"):
        return not harvested_today or (desired - active_count >= 2)

    if "COOLDOWN3" in policy:
        if last_harvest is not None and (dt - last_harvest).days < 3:
            return False
        return True

    if "ON_RISK" in policy:
        if prev_state is None:
            return True
        return (
            state["risk_score"] > prev_state["risk_score"] + 0.25
            or state["dscore"] > prev_state["dscore"]
            or state["xscore"] > prev_state["xscore"]
            or state["gscore"] > prev_state["gscore"]
        )

    return True


def close_excess(positions, target, dt, quote_maps_by_cid, cash_ref):
    active = [p for p in positions if not p.closed]
    excess = len(active) - target
    if excess <= 0:
        return cash_ref

    # Prefer profitable short-term winners first; otherwise use the oldest expiring layer.
    candidates = []
    for p in active:
        q = quote_maps_by_cid.get(p.cid)
        if q is None or dt not in q.index:
            continue
        bid = float(q.loc[dt, "bid"])
        ret = bid / p.cost - 1.0 if p.cost > 0 else -1.0
        dte = max(0, (p.expiry - dt).days)
        candidates.append((ret, -dte, p.entry, p))

    candidates.sort(key=lambda x: (x[0] > 0, x[0], x[1], x[2]), reverse=True)
    closed = 0
    cash = cash_ref
    for _, _, _, p in candidates:
        if closed >= excess:
            break
        q = quote_maps_by_cid[p.cid]
        bid = float(q.loc[dt, "bid"])
        p.closed = True
        p.exit = dt
        p.exit_price = bid
        p.pnl = (bid - p.cost) * 100.0
        cash += bid * 100.0
        closed += 1
    return cash


def simulate(
    u,
    far_candidates,
    near_chains,
    far_quotes_by_cid,
    near_quotes_by_cid,
    far_dte,
    far_delta,
    near_dte,
    coverage_mult,
    policy,
    has_gamma,
):
    sigs = u[u.signal & u.dma200.notna()]
    results = []
    next_allowed = None

    for _, sr in sigs.iterrows():
        d0 = pd.Timestamp(sr.date)
        if next_allowed is not None and d0 <= next_allowed:
            continue

        far = far_candidates.get(d0, {}).get((far_dte, far_delta))
        if not far:
            continue

        far_cid = far["cid"]
        far_strike = float(far["strike"])
        far_exp = pd.Timestamp(far["expiry"])
        fq = far_quotes_by_cid.get(far_cid)
        if fq is None or fq.empty:
            continue

        # First underlying high touching the far short strike, otherwise expiry.
        end = far_exp
        subu = u[(u.date > d0) & (u.date <= end)]
        touch = subu[subu.high >= far_strike]
        far_reason = "SHORT_TOUCH" if not touch.empty else "EXPIRY"
        if not touch.empty:
            end = pd.Timestamp(touch.iloc[0].date)

        fq_after = fq.loc[fq.index >= end]
        if fq_after.empty:
            continue
        far_exit_date = pd.Timestamp(fq_after.index[0])
        if (far_exit_date - end).days > 5:
            continue

        far_entry_bid = float(far["entry_bid"])
        far_exit_ask = float(fq_after.iloc[0].ask)
        far_pnl = (far_entry_bid - N_SHORT * far_exit_ask) * 100.0

        # Reindex the far chain to underlying observation dates, carrying forward only known data.
        sub_dates = u[(u.date >= d0) & (u.date <= end)]["date"]
        fqd = fq.reindex(sub_dates, method="ffill").copy()
        if fqd.empty:
            continue

        # Causal gamma: use actual gamma when present; otherwise derive a same-contract
        # daily gamma proxy = |dDelta/dSpot| * Spot.
        spots = u.set_index("date").reindex(fqd.index)["close"]
        fqd["spot"] = spots
        fqd["delta_abs"] = fqd["delta"].abs()

        if has_gamma and "gamma" in fqd.columns:
            fqd["gamma_spot"] = fqd["gamma"].abs() * fqd["spot"]
        else:
            dspot = fqd["spot"].diff()
            ddelta = fqd["delta_abs"].diff()
            fqd["gamma_spot"] = (ddelta.abs() / dspot.abs().replace(0, np.nan)) * fqd["spot"]
        fqd["gamma_baseline"] = fqd["gamma_spot"].shift(1).rolling(20, min_periods=5).median()
        fqd["gamma_rel"] = fqd["gamma_spot"] / fqd["gamma_baseline"].replace(0, np.nan)
        fqd["gamma_rel"] = fqd["gamma_rel"].replace([np.inf, -np.inf], np.nan).fillna(1.0)
        fqd["delta_jump"] = fqd["delta_abs"].diff().abs().fillna(0.0)
        fqd["distance_pct"] = (far_strike - fqd["spot"]) / fqd["spot"]

        days = list(fqd.index)
        positions = []
        trades = []
        cash = far_entry_bid * N_SHORT * 100.0
        peak_equity = cash
        eq_rows = []
        prev_state = None
        last_harvest = None
        state_increases = 0
        state_decreases = 0
        opens = 0

        for dt in days:
            row = fqd.loc[dt]
            far_delta_now = abs(float(row["delta_abs"])) if pd.notna(row["delta_abs"]) else 0.0
            dist_now = float(row["distance_pct"])
            gamma_rel_now = float(row["gamma_rel"]) if pd.notna(row["gamma_rel"]) else 1.0
            delta_jump_now = float(row["delta_jump"]) if pd.notna(row["delta_jump"]) else 0.0

            desired, state = target_from_state(
                far_delta_now,
                dist_now,
                gamma_rel_now,
                delta_jump_now,
                coverage_mult,
            )

            if prev_state is not None:
                if state["risk_score"] > prev_state["risk_score"] + 0.25:
                    state_increases += 1
                elif state["risk_score"] < prev_state["risk_score"] - 0.25:
                    state_decreases += 1

            active = [p for p in positions if not p.closed]

            # First mark peak and harvest existing near-long inventory.
            for p in active:
                q = near_quotes_by_cid.get(p.cid)
                if q is None or dt not in q.index:
                    continue
                bid = float(q.loc[dt, "bid"])
                if should_harvest(policy, p, dt, bid, state["risk_score"]):
                    p.closed = True
                    p.exit = dt
                    p.exit_price = bid
                    p.pnl = (bid - p.cost) * 100.0
                    cash += bid * 100.0
                    trades.append(p)
                    last_harvest = dt

            active = [p for p in positions if not p.closed]

            # If state risk falls, actively shrink inventory; prefer profitable layers.
            if len(active) > desired:
                before = len(active)
                cash = close_excess(positions, desired, dt, near_quotes_by_cid, cash)
                after = len([p for p in positions if not p.closed])
                if after < before:
                    last_harvest = dt

            active = [p for p in positions if not p.closed]

            # Reload according to the policy-specific gate.
            if reload_gate(policy, dt, last_harvest, state, prev_state, desired, len(active)):
                add_count = max(0, desired - len(active))
                for _ in range(add_count):
                    chain = near_chains.get(dt)
                    leg = pick_near(chain, float(row["spot"]), near_dte) if chain is not None else None
                    if not leg:
                        continue
                    q = near_quotes_by_cid.get(leg["cid"])
                    if q is None or dt not in q.index:
                        continue
                    ask = float(q.loc[dt, "ask"])
                    if ask <= 0:
                        continue
                    p = Pos(
                        entry=dt,
                        expiry=leg["expiry"],
                        cid=leg["cid"],
                        strike=leg["strike"],
                        delta=leg["delta"],
                        cost=ask,
                        target_dte=near_dte,
                        peak_bid=ask,
                    )
                    positions.append(p)
                    cash -= ask * 100.0
                    opens += 1

            # Daily mark-to-market.
            liq = cash
            for p in positions:
                if p.closed:
                    continue
                q = near_quotes_by_cid.get(p.cid)
                if q is not None and dt in q.index:
                    liq += float(q.loc[dt, "bid"]) * 100.0

            # Far short is a liability marked at ask.
            liq -= N_SHORT * float(row["ask"]) * 100.0
            eq_rows.append((dt, liq))
            peak_equity = max(peak_equity, liq)
            prev_state = state

        # Force-close any remaining near long at far exit.
        for p in [x for x in positions if not x.closed]:
            q = near_quotes_by_cid.get(p.cid)
            if q is None or q.empty:
                continue
            avail = q.loc[q.index >= far_exit_date]
            if avail.empty:
                avail = q.loc[q.index <= far_exit_date]
            if avail.empty:
                continue
            if avail.index[0] >= far_exit_date:
                dt2 = pd.Timestamp(avail.index[0])
                bid = float(avail.iloc[0]["bid"])
            else:
                dt2 = pd.Timestamp(avail.index[-1])
                bid = float(avail.iloc[-1]["bid"])
            p.closed = True
            p.exit = dt2
            p.exit_price = bid
            p.pnl = (bid - p.cost) * 100.0
            cash += bid * 100.0
            trades.append(p)

        near_pnl = float(sum(t.pnl or 0.0 for t in trades))
        total_pnl = float(far_pnl + near_pnl)

        eq = pd.DataFrame(eq_rows, columns=["date", "equity"])
        if not eq.empty:
            nav = REFERENCE_CAPITAL_USD + eq["equity"]
            dd = nav / nav.cummax() - 1.0
            maxdd = float(dd.min())
            worst_nav = float(nav.min())
        else:
            maxdd = float("nan")
            worst_nav = float("nan")

        results.append(
            {
                "campaign_entry": d0,
                "campaign_far_expiry": far_exp,
                "far_exit": far_exit_date,
                "far_reason": far_reason,
                "far_dte_target": far_dte,
                "far_delta_target": far_delta,
                "near_dte": near_dte,
                "coverage_mult": coverage_mult,
                "policy": policy,
                "far_strike": far_strike,
                "far_entry_premium_usd": far_entry_bid * N_SHORT * 100.0,
                "far_pnl_usd": far_pnl,
                "near_trades": len(trades),
                "near_open_count": opens,
                "near_realized_pnl_usd": near_pnl,
                "total_pnl_usd": total_pnl,
                "maxdd": maxdd,
                "worst_nav": worst_nav,
                "long_wins": int(sum(1 for t in trades if (t.pnl or 0.0) > 0)),
                "long_losses": int(sum(1 for t in trades if (t.pnl or 0.0) <= 0)),
                "long_win_rate": (
                    float(sum(1 for t in trades if (t.pnl or 0.0) > 0) / len(trades))
                    if trades else np.nan
                ),
                "state_increases": state_increases,
                "state_decreases": state_decreases,
                "final_stack": len([p for p in positions if not p.closed]),
            }
        )

        next_allowed = far_exit_date + pd.Timedelta(days=COOLDOWN_DAYS)

    return pd.DataFrame(results)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--out", default="artifacts")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    od = Path(args.data_dir) / "QQQ_options.parquet"
    ud = Path(args.data_dir) / "QQQ_underlying.parquet"

    u = load_underlying(ud)
    con = duckdb.connect()

    far_build = build_far_candidates(u, con, od)
    if not far_build:
        raise RuntimeError("No far candidates")
    far_candidates, has_gamma = far_build

    # Build the full set of daily dates that may be needed by stateful near-long
    # decisions. No future chain rows are introduced into a decision date.
    event_dates = set(pd.Timestamp(d) for d in u.loc[u.signal & u.dma200.notna(), "date"])
    for legs in far_candidates.values():
        for leg in legs.values():
            if not leg:
                continue
            d = next(k for k, v in far_candidates.items() if leg in v.values())
            end = min(pd.Timestamp(leg["expiry"]), d + pd.Timedelta(days=365))
            active = u[(u.date >= d) & (u.date <= end)]
            event_dates.update(pd.Timestamp(x) for x in active.date)

    event_dates = sorted(event_dates)

    near = read_options(
        con, od,
        """
        SELECT CAST(date AS DATE) AS date,
               CAST(expiration AS DATE) AS expiration,
               CAST(contract_id AS VARCHAR) AS contract_id,
               CAST(strike AS DOUBLE) AS strike,
               CAST(bid AS DOUBLE) AS bid,
               CAST(ask AS DOUBLE) AS ask,
               COALESCE(CAST(volume AS DOUBLE),0) AS volume,
               CAST(delta AS DOUBLE) AS delta
        FROM read_parquet(?)
        WHERE CAST(date AS DATE) IN (SELECT * FROM UNNEST(?))
          AND UPPER("type")='CALL'
          AND delta IS NOT NULL
          AND bid IS NOT NULL AND ask IS NOT NULL
          AND ask >= bid AND bid >= 0
          AND CAST(expiration AS DATE) BETWEEN CAST(date AS DATE)+INTERVAL 7 DAY
                                            AND CAST(date AS DATE)+INTERVAL 35 DAY
        """,
        [[d.date() for d in event_dates]],
    )
    near["date"] = pd.to_datetime(near.date)
    near["expiration"] = pd.to_datetime(near.expiration)
    near_chains = {d: g for d, g in near.groupby("date", sort=False)}

    near_ids = set()
    for d, ch in near_chains.items():
        spot_row = u.loc[u.date == d, "close"]
        if spot_row.empty:
            continue
        spot = float(spot_row.iloc[0])
        for td in NEAR_DTES:
            leg = pick_near(ch, spot, td)
            if leg:
                near_ids.add(leg["cid"])

    far_ids = set()
    for legs in far_candidates.values():
        for leg in legs.values():
            if leg:
                far_ids.add(leg["cid"])

    fq = get_quotes(con, od, far_ids, with_delta=True, with_gamma=has_gamma)
    far_quotes_by_cid = quote_maps(fq)

    nq = get_quotes(con, od, near_ids)
    near_quotes_by_cid = quote_maps(nq)

    all_rows = []
    summary_rows = []

    # 9 far configurations x 4 near DTE x 3 dynamic coverage levels x 8 policies = 864.
    for fd in FAR_DTES:
        for fdel in FAR_DELTAS:
            for ndte in NEAR_DTES:
                for cov in COVERAGE_MULTS:
                    for policy in POLICIES:
                        df = simulate(
                            u=u,
                            far_candidates=far_candidates,
                            near_chains=near_chains,
                            far_quotes_by_cid=far_quotes_by_cid,
                            near_quotes_by_cid=near_quotes_by_cid,
                            far_dte=fd,
                            far_delta=fdel,
                            near_dte=ndte,
                            coverage_mult=cov,
                            policy=policy,
                            has_gamma=has_gamma,
                        )
                        if df.empty:
                            continue
                        df["data_gamma_mode"] = "OBSERVED_GAMMA" if has_gamma else "DERIVED_DDELTA_DSPOT"
                        all_rows.append(df)

                        ntrades = int(df.near_trades.sum())
                        summary_rows.append(
                            {
                                "far_dte_target": fd,
                                "far_delta_target": fdel,
                                "near_dte": ndte,
                                "coverage_mult": cov,
                                "policy": policy,
                                "campaigns": int(len(df)),
                                "total_pnl_usd": float(df.total_pnl_usd.sum()),
                                "avg_campaign_pnl_usd": float(df.total_pnl_usd.mean()),
                                "median_campaign_pnl_usd": float(df.total_pnl_usd.median()),
                                "far_pnl_usd": float(df.far_pnl_usd.sum()),
                                "near_realized_pnl_usd": float(df.near_realized_pnl_usd.sum()),
                                "near_trade_count": ntrades,
                                "near_win_rate": float(df.long_wins.sum() / max(1, df.long_wins.sum() + df.long_losses.sum())),
                                "worst_campaign_pnl_usd": float(df.total_pnl_usd.min()),
                                "mean_campaign_maxdd": float(df.maxdd.mean()),
                                "worst_campaign_maxdd": float(df.maxdd.min()),
                                "avg_near_opens": float(df.near_open_count.mean()),
                                "avg_final_stack": float(df.final_stack.mean()),
                                "state_increases": int(df.state_increases.sum()),
                                "state_decreases": int(df.state_decreases.sum()),
                            }
                        )

    if not all_rows:
        raise RuntimeError("No strategy results")

    detail = pd.concat(all_rows, ignore_index=True)
    summary = pd.DataFrame(summary_rows)
    summary = summary.sort_values(
        ["total_pnl_usd", "near_win_rate"],
        ascending=[False, False]
    ).reset_index(drop=True)

    detail.to_csv(out / "v22_dynamic_state_detail.csv", index=False)
    summary.to_csv(out / "v22_dynamic_state_summary.csv", index=False)

    days = max(1, (u.date.max() - u.date.min()).days)
    top = summary.head(20).to_dict("records")
    report = {
        "status": "REAL_QQQ_CHAIN_DYNAMIC_STATE_ENGINE",
        "data": {
            "options_sha256": sha256_file(od),
            "underlying_sha256": sha256_file(ud),
            "underlying_range": [str(u.date.min().date()), str(u.date.max().date())],
            "signal_count": int(u.signal.sum()),
            "near_event_date_count": len(event_dates),
            "gamma_mode": "OBSERVED_GAMMA" if has_gamma else "DERIVED_DDELTA_DSPOT",
            "matrix_configs": 4 * 3 * 3 * 4 * 8,
            "calendar_years": days / 365.25,
        },
        "engine": {
            "far_position": "10 x fixed short CALL, selected at the extreme-high signal and held until first High touch of strike or far expiry",
            "near_position": "dynamic stack of near CALLs, nearest 50-delta contract at the requested 7/14/21/30 DTE",
            "state_inputs": [
                "absolute far-short delta",
                "distance from spot to far short strike",
                "far gamma or causal same-contract dDelta/dSpot gamma proxy",
                "daily far-delta jump",
            ],
            "stack_rule": "coverage base from 10*far_delta, multiplied by coverage_mult, then boosted by the composite delta/distance/gamma state",
            "execution": "buy near at Ask, sell near at Bid; short far opened at Bid and closed at Ask",
            "no_lookahead": "all management state and reload decisions use only data available on or before the management date",
        },
        "matrix": {
            "far_dtes": list(FAR_DTES),
            "far_delta_targets": list(FAR_DELTAS),
            "near_dtes": list(NEAR_DTES),
            "coverage_mults": list(COVERAGE_MULTS),
            "policies": list(POLICIES),
            "configs": 864,
        },
        "top20": top,
    }

    (out / "v22_dynamic_state_result.json").write_text(
        json.dumps(report, indent=2, default=str),
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, default=str), flush=True)


if __name__ == "__main__":
    main()
