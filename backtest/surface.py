"""Build a strike × DTE option surface from LIVE quotes only.

Missing IV / Greeks stay UNAVAILABLE. This module does not fill Black-Scholes
into a LIVE field.
"""

from __future__ import annotations

from typing import Any, Optional

from .types import OptionContract, finite


def pick_quote_targets(contracts: list[OptionContract], spot: Optional[float], limit: int = 12) -> list[OptionContract]:
    puts = [c for c in contracts if c.right == "PUT" and c.strike is not None]
    if not puts:
        return contracts[:limit]
    if spot is None or spot <= 0:
        puts.sort(key=lambda c: (c.dte or 999, c.strike or 0))
        return puts[:limit]
    wanted = (0.0, 0.02, 0.05, 0.08)
    dtes = sorted({c.dte for c in puts if c.dte is not None})
    prefer_dte = []
    for t in (30, 21, 45, 14, 60):
        if not dtes:
            break
        dtes.sort(key=lambda d: abs((d or 0) - t))
        if dtes[0] not in prefer_dte:
            prefer_dte.append(dtes[0])
            dtes = dtes[1:]
    out: list[OptionContract] = []
    seen = set()
    for dte in prefer_dte[:3]:
        bucket = [c for c in puts if c.dte == dte]
        for w in wanted:
            target = spot * (1 - w)
            bucket.sort(key=lambda c: abs((c.strike or 0) - target))
            if bucket:
                c = bucket[0]
                if c.code not in seen:
                    seen.add(c.code)
                    out.append(c)
                bucket = [x for x in bucket if x.code != c.code]
        if len(out) >= limit:
            break
    return out[:limit]


def merge_quotes(meta: list[OptionContract], quoted: list[OptionContract]) -> list[OptionContract]:
    by = {q.code: q for q in quoted}
    out = []
    for m in meta:
        q = by.get(m.code)
        if q is None:
            out.append(m)
            continue
        fs = dict(m.field_sources)
        fs.update(q.field_sources)
        out.append(
            OptionContract(
                code=m.code,
                underlying=m.underlying,
                right=m.right or q.right,
                strike=q.strike if q.strike is not None else m.strike,
                expiry=q.expiry or m.expiry,
                dte=q.dte if q.dte is not None else m.dte,
                lot_size=q.lot_size or m.lot_size,
                bid=q.bid,
                ask=q.ask,
                last=q.last,
                iv=q.iv,
                delta=q.delta,
                gamma=q.gamma,
                theta=q.theta,
                vega=q.vega,
                oi=q.oi,
                volume=q.volume,
                source=q.source,
                field_sources=fs,
                reason=q.reason,
            )
        )
    return out


def summarize(rows: list[OptionContract]) -> dict[str, Any]:
    live = [r for r in rows if r.source == "LIVE QUOTE"]
    with_bid = [r for r in live if r.bid is not None and r.bid > 0]
    with_iv = [r for r in live if r.iv is not None]
    with_delta = [r for r in live if r.delta is not None]
    sample = with_bid[0] if with_bid else (live[0] if live else None)
    available = bool(with_bid or with_iv)
    return {
        "available": available,
        "n": len(rows),
        "n_live": len(live),
        "n_bid": len(with_bid),
        "n_iv": len(with_iv),
        "n_delta": len(with_delta),
        "iv": sample.iv if sample else None,
        "delta": sample.delta if sample else None,
        "gamma": sample.gamma if sample else None,
        "theta": sample.theta if sample else None,
        "vega": sample.vega if sample else None,
        "bid": sample.bid if sample else None,
        "ask": sample.ask if sample else None,
        "mid": sample.mid if sample else None,
        "spread_pct": sample.spread_pct if sample else None,
        "sample_code": sample.code if sample else None,
        "iv_source": (sample.field_sources or {}).get("iv", "UNAVAILABLE") if sample else "UNAVAILABLE",
        "bid_source": (sample.field_sources or {}).get("bid", "UNAVAILABLE") if sample else "UNAVAILABLE",
    }


def atm_iv(rows: list[OptionContract], spot: Optional[float]) -> Optional[float]:
    if spot is None or spot <= 0:
        return None
    ranked = [r for r in rows if r.source == "LIVE QUOTE" and r.iv is not None and r.strike is not None]
    if not ranked:
        return None
    ranked.sort(key=lambda r: abs((r.strike or 0) - spot))
    return finite(ranked[0].iv)
