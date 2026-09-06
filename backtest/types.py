"""Shared types for the V2.3 live layer.

Price sources are mutually exclusive labels. A number without a source
is a bug — callers must never treat None as 0.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

STATUSES = ("PASS", "FAIL", "PARTIAL", "SKIPPED")
ISSUE_CLASSES = ("CODE", "DATA", "ENVIRONMENT", "PERMISSION", "API")
PRICE_SOURCES = ("LIVE QUOTE", "DERIVED", "ESTIMATED", "SYNTHETIC", "UNAVAILABLE")

QQQ_CODE = "US.QQQ"
VIX_CODE = "US..VIX"  # Futu IDX code for 标普500波动率指数 (not US.VIX)
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 11111


def jsonable(obj: Any) -> Any:
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if dataclass_instance(obj):
        return {k: jsonable(v) for k, v in asdict(obj).items()}
    if isinstance(obj, dict):
        return {str(k): jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [jsonable(x) for x in obj]
    return obj


def dataclass_instance(obj: Any) -> bool:
    return hasattr(obj, "__dataclass_fields__") and not isinstance(obj, type)


def finite(x: Any) -> Optional[float]:
    """Parse a number. NaN / inf / None / 'N/A' → None. Never returns 0 for missing."""
    if x is None:
        return None
    if isinstance(x, bool):
        return None
    if isinstance(x, str):
        s = x.strip()
        if s == "" or s.upper() in {"N/A", "NA", "NONE", "NULL", "UNAVAILABLE", "NAN", "-"}:
            return None
        try:
            x = float(s)
        except ValueError:
            return None
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    if v != v or v in (float("inf"), float("-inf")):
        return None
    return v


@dataclass
class Check:
    name: str
    status: str
    reason: str
    issue_class: Optional[str] = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "name": self.name,
            "status": self.status,
            "reason": self.reason,
            "class": self.issue_class,
        }
        if self.extra:
            d["extra"] = jsonable(self.extra)
        return d


@dataclass
class Quote:
    code: str
    last: Optional[float]
    bid: Optional[float]
    ask: Optional[float]
    timestamp: Optional[str]
    source: str
    volume: Optional[float] = None
    prev_close: Optional[float] = None
    reason: Optional[str] = None
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def mid(self) -> Optional[float]:
        if self.bid is not None and self.ask is not None and self.ask >= self.bid:
            return (self.bid + self.ask) / 2.0
        return self.last

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "last": self.last,
            "bid": self.bid,
            "ask": self.ask,
            "mid": self.mid,
            "timestamp": self.timestamp,
            "source": self.source,
            "volume": self.volume,
            "prev_close": self.prev_close,
            "reason": self.reason,
            "extra": jsonable(self.extra),
        }


@dataclass
class OptionContract:
    code: str
    underlying: str
    right: str
    strike: Optional[float]
    expiry: Optional[str]
    dte: Optional[int]
    lot_size: Optional[int]
    bid: Optional[float]
    ask: Optional[float]
    last: Optional[float]
    iv: Optional[float]
    delta: Optional[float]
    gamma: Optional[float]
    theta: Optional[float]
    vega: Optional[float]
    oi: Optional[float]
    volume: Optional[float]
    source: str
    field_sources: dict[str, str] = field(default_factory=dict)
    reason: Optional[str] = None

    @property
    def mid(self) -> Optional[float]:
        if self.bid is not None and self.ask is not None and self.ask >= self.bid:
            return (self.bid + self.ask) / 2.0
        return self.last

    @property
    def spread_pct(self) -> Optional[float]:
        m = self.mid
        if m is None or m <= 0 or self.bid is None or self.ask is None:
            return None
        return (self.ask - self.bid) / m

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "underlying": self.underlying,
            "right": self.right,
            "strike": self.strike,
            "expiry": self.expiry,
            "dte": self.dte,
            "lot_size": self.lot_size,
            "bid": self.bid,
            "ask": self.ask,
            "last": self.last,
            "mid": self.mid,
            "spread_pct": self.spread_pct,
            "iv": self.iv,
            "delta": self.delta,
            "gamma": self.gamma,
            "theta": self.theta,
            "vega": self.vega,
            "oi": self.oi,
            "volume": self.volume,
            "source": self.source,
            "field_sources": dict(self.field_sources),
            "reason": self.reason,
        }


def unavailable_quote(code: str, reason: str) -> Quote:
    return Quote(
        code=code,
        last=None,
        bid=None,
        ask=None,
        timestamp=None,
        source="UNAVAILABLE",
        reason=reason,
    )


def unavailable_option(code: str, reason: str) -> OptionContract:
    return OptionContract(
        code=code,
        underlying=QQQ_CODE,
        right="PUT",
        strike=None,
        expiry=None,
        dte=None,
        lot_size=None,
        bid=None,
        ask=None,
        last=None,
        iv=None,
        delta=None,
        gamma=None,
        theta=None,
        vega=None,
        oi=None,
        volume=None,
        source="UNAVAILABLE",
        reason=reason,
    )
