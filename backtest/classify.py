"""First-layer diagnosis: CODE vs ENVIRONMENT vs PERMISSION vs DATA vs API."""

from __future__ import annotations

from typing import Optional


def classify_error(message: str | None, *, connected: bool = False) -> str:
    text = (message or "").lower()
    if any(k in text for k in ("syntaxerror", "attributeerror", "typeerror", "nameerror", "assertionerror")):
        if "futu" not in text:
            return "CODE"
    if any(
        k in text
        for k in (
            "no module named 'futu'",
            "no module named futu",
            "modulenotfounderror",
            "connection refused",
            "connectionreset",
            "timed out",
            "timeout",
            "opend",
            "11111",
            "not connected",
            "connect fail",
            "failed to connect",
            "winerror 10061",
            "errno 111",
            "errno 61",
            "no route to host",
            "network is unreachable",
            "opend is not",
            "socket",
        )
    ):
        return "ENVIRONMENT"
    if any(
        k in text
        for k in (
            "permission",
            "no right",
            "no privilege",
            "not authorized",
            "unauthor",
            "无权限",
            "沒有權限",
            "没有权限",
            "行情权限",
            "option right",
            "no access",
            "not entitled",
            "暂不支持美股指数",
            "暫不支持美股指數",
            "不支持美股指数",
            "不支持美股指數",
            "订阅额度",
            "subscribe limit",
            "quota",
        )
    ):
        return "PERMISSION"
    if connected and any(
        k in text
        for k in (
            "empty",
            "no data",
            "no option",
            "not exist",
            "unknown stock",
            "unknown security",
            "无数据",
            "沒有資料",
            "没有数据",
        )
    ):
        return "DATA"
    if any(
        k in text
        for k in (
            "ret !=",
            "ret_error",
            "proto",
            "protobuf",
            "api error",
            "invalid code",
            "fail",
        )
    ):
        return "API"
    if connected:
        return "API"
    return "ENVIRONMENT"


def next_action(checks: dict) -> str:
    """Smallest next action from the diagnostic checks dict {name: Check-like}."""

    def st(name: str) -> str:
        c = checks.get(name) or {}
        if hasattr(c, "status"):
            return c.status
        return str(c.get("status") or "SKIPPED")

    def reason(name: str) -> str:
        c = checks.get(name) or {}
        if hasattr(c, "reason"):
            return c.reason
        return str(c.get("reason") or "")

    env = st("environment")
    sdk = st("sdk")
    conn = st("connection")
    qqq = st("quote")
    vix = st("vix")
    chain = st("chain")
    oq = st("option_quote")
    surf = st("surface")

    if env != "PASS":
        return (
            "Python environment is incomplete. Install Python 3.10+ from python.org, "
            "re-open the terminal, then re-run: python -m backtest.local_diagnostic --diagnostic --futu-test"
        )
    if sdk != "PASS":
        return (
            "Futu SDK missing. In the same environment that will talk to OpenD run: "
            "pip install futu-api\nThen re-run: python -m backtest.local_diagnostic --diagnostic --futu-test"
        )
    if conn != "PASS":
        return (
            "Futu OpenD = NOT CONNECTED. This is a local environment issue, not a strategy fail.\n"
            "1. Start Futu OpenD on this Windows machine.\n"
            "2. Login inside OpenD (do not send account/password/token to Grok).\n"
            "3. Confirm OpenD listen address is 127.0.0.1 port 11111.\n"
            "4. Re-run: python -m backtest.local_diagnostic --diagnostic --futu-test\n"
            f"Last reason: {reason('connection')}"
        )
    if qqq != "PASS":
        return (
            "OpenD is up, but the QQQ live quote failed. Check US market quote permission "
            "and that code US.QQQ is visible in Futu. This is usually PERMISSION or DATA, not a V2.2 bug.\n"
            f"Reason: {reason('quote')}"
        )
    if chain != "PASS":
        extra = ""
        if qqq == "PASS":
            extra = "QQQ 基础行情正常，但 option chain layer 失败。"
        return (
            f"{extra} Option chain metadata is the bottleneck. Typical cause: US option permission "
            "is not enabled on this Futu account, or US market is closed and the chain API returned empty.\n"
            "Do not rewrite V2.2. Do not invent a chain.\n"
            f"Reason: {reason('chain')}"
        )
    if oq != "PASS":
        return (
            "chain metadata 可取得，但 dynamic option quote / subscription layer 失败。"
            " Snapshot or subscribe on option codes is the bottleneck.\n"
            f"Reason: {reason('option_quote')}"
        )
    if surf != "PASS":
        return (
            "Quotes exist but the option surface is incomplete (IV/Greeks/bid-ask missing). "
            "Keep missing fields as UNAVAILABLE. Do not fill Black-Scholes and call it LIVE.\n"
            f"Reason: {reason('surface')}"
        )
    proxy = st("vix_proxy")
    if vix != "PASS":
        r = reason("vix")
        if proxy == "PASS":
            return (
                "US..VIX index quote is unavailable (OpenAPI does not support US indices / entitlement). "
                "State/risk now uses a DERIVED VIX-units proxy (prefer QQQ ~30D ATM IV*100; "
                "VIXY only for acceleration aid). Do NOT treat the proxy as LIVE Cboe VIX.\n"
                f"Index reason: {r}\n"
                f"Proxy: {reason('vix_proxy')}\n"
                "Next: keep running with proxy, or if Futu ever enables US index quotes, US..VIX will take priority."
            )
        if any(k in r for k in ("暂不支持美股指数", "暫不支持美股指數", "不支持美股指数", "不支持美股指數")):
            return (
                "QQQ live path is up. Correct VIX code is US..VIX, but this OpenD cannot quote US indices "
                "(暂不支持美股指数). OpenAPI currently lists US indices as unsupported.\n"
                "Proxy also failed — check option IV surface / QQQ closes.\n"
                "Do NOT substitute US.VIXY/US.VXX last price as VIX level.\n"
                f"Reason: {r} | proxy: {reason('vix_proxy')}"
            )
        return (
            "QQQ live path is up, VIX quote is not, and VIX proxy is not ready.\n"
            f"Reason: {r}\n"
            f"Proxy: {reason('vix_proxy')}\n"
            "Next: confirm option LIVE IV quotes exist near 30D ATM, then re-run."
        )
    return (
        "FUTU LIVE DATA PATH = READY.\n"
        "Do not rewrite V2.2. Do not search OOS again.\n"
        "Next development stage: compare this LIVE option surface (IV, bid/ask, OI, Greeks) "
        "against the V2.2 Derived BS(VIX) overlay — that is the research question, not a preset answer."
    )
