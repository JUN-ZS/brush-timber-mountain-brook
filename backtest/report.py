"""Machine-readable + human-readable diagnostic TXT."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from .types import jsonable

SEP = "=" * 60
SUB = "=" * 26


def _s(v: Any) -> str:
    if v is None:
        return "UNAVAILABLE"
    if isinstance(v, float):
        if abs(v) >= 1:
            return f"{v:.4f}".rstrip("0").rstrip(".")
        return f"{v:.6f}".rstrip("0").rstrip(".")
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)


def _check_block(name: str, check: Any) -> list[str]:
    if check is None:
        return [f"{name}: SKIPPED", f"{name}.reason: not run", f"{name}.class: "]
    if hasattr(check, "to_dict"):
        d = check.to_dict()
    elif isinstance(check, dict):
        d = check
    else:
        d = {"status": str(check), "reason": "", "class": None}
    lines = [
        f"{name}: {d.get('status')}",
        f"{name}.reason: {d.get('reason') or ''}",
        f"{name}.class: {d.get('class') or d.get('issue_class') or ''}",
    ]
    extra = d.get("extra") or {}
    if isinstance(extra, dict):
        for k, v in extra.items():
            if k == "trace":
                continue
            lines.append(f"{name}.{k}: {_s(v)}")
    return lines


def render_txt(doc: dict[str, Any]) -> str:
    env = doc.get("environment") or {}
    opend = doc.get("opend") or {}
    qqq = doc.get("qqq") or {}
    vix = doc.get("vix") or {}
    chain = doc.get("chain") or {}
    oq = doc.get("option_quote") or {}
    surface = doc.get("surface") or {}
    state = doc.get("state") or {}
    risk = doc.get("risk") or {}
    paper = doc.get("paper") or {}
    tests = doc.get("tests") or {}
    errors = doc.get("errors") or []
    warnings = doc.get("warnings") or []
    lines = [
        SEP,
        "FUTU V2.3 LOCAL RUN RESULT",
        SUB,
        "",
        f"RUN_ID: {doc.get('run_id')}",
        f"timestamp: {doc.get('timestamp')}",
        f"host: {opend.get('host')}",
        f"port: {opend.get('port')}",
        "",
        "## ENVIRONMENT",
        "",
        f"OS: {env.get('os')}",
        f"Python: {env.get('python')}",
        f"Project: {env.get('project')}",
        f"Git branch: {env.get('git_branch')}",
        f"Git commit: {env.get('git_commit')}",
        f"futu-api: {env.get('futu_api')}",
        "",
        "## FUTU OPEND",
        "",
        f"host: {opend.get('host')}",
        f"port: {opend.get('port')}",
        f"connection: {opend.get('connection')}",
        f"login_status: {opend.get('login_status')}",
        f"market_access: {opend.get('market_access')}",
        f"qot_logined: {_s(opend.get('qot_logined'))}",
        f"trd_logined: {_s(opend.get('trd_logined'))}",
        f"market_us: {_s(opend.get('market_us'))}",
        f"reason: {opend.get('reason') or ''}",
        f"class: {opend.get('class') or ''}",
        "",
        "## QUOTE TEST",
        "",
        f"QQQ: {qqq.get('code') or 'US.QQQ'}",
        f"last: {_s(qqq.get('last'))}",
        f"bid: {_s(qqq.get('bid'))}",
        f"ask: {_s(qqq.get('ask'))}",
        f"timestamp: {_s(qqq.get('timestamp'))}",
        f"source: {qqq.get('source') or 'UNAVAILABLE'}",
        f"reason: {qqq.get('reason') or ''}",
        "",
        f"VIX: {vix.get('code') or 'US.VIX'}",
        f"VIX.last: {_s(vix.get('last'))}",
        f"VIX.source: {vix.get('source') or 'UNAVAILABLE'}",
        f"VIX.reason: {vix.get('reason') or ''}",
        "",
        "## OPTION CHAIN",
        "",
        f"underlying: {chain.get('underlying') or 'US.QQQ'}",
        f"expiry_count: {_s(chain.get('expiry_count'))}",
        f"contract_count: {_s(chain.get('contract_count'))}",
        f"expiries: {', '.join(chain.get('expiries') or []) or 'UNAVAILABLE'}",
        f"source: {chain.get('source') or 'UNAVAILABLE'}",
        f"reason: {chain.get('reason') or ''}",
        f"class: {chain.get('class') or ''}",
        "",
        "## OPTION QUOTE",
        "",
        f"contracts_tested: {_s(oq.get('contracts_tested'))}",
        f"successful: {_s(oq.get('successful'))}",
        f"failed: {_s(oq.get('failed'))}",
        f"source: {oq.get('source') or 'UNAVAILABLE'}",
        f"reason: {oq.get('reason') or ''}",
        "",
        "## OPTION SURFACE",
        "",
        f"available: {_s(surface.get('available'))}",
        f"iv: {_s(surface.get('iv'))}",
        f"delta: {_s(surface.get('delta'))}",
        f"gamma: {_s(surface.get('gamma'))}",
        f"theta: {_s(surface.get('theta'))}",
        f"vega: {_s(surface.get('vega'))}",
        f"bid: {_s(surface.get('bid'))}",
        f"ask: {_s(surface.get('ask'))}",
        f"mid: {_s(surface.get('mid'))}",
        f"spread_pct: {_s(surface.get('spread_pct'))}",
        f"iv_source: {surface.get('iv_source') or 'UNAVAILABLE'}",
        f"bid_source: {surface.get('bid_source') or 'UNAVAILABLE'}",
        f"sample_code: {surface.get('sample_code') or 'UNAVAILABLE'}",
        "",
        "## STATE ENGINE",
        "",
        f"state: {state.get('regime') or 'UNAVAILABLE'}",
        f"building: {_s(state.get('building'))}",
        f"VIX: {_s(state.get('vix'))}",
        f"QQQ return: {_s(state.get('qqq_return'))}",
        f"realized_vol: {_s(state.get('realized_vol'))}",
        f"momentum_20d: {_s(state.get('momentum_20d'))}",
        f"momentum_60d: {_s(state.get('momentum_60d'))}",
        f"source: {state.get('source') or 'UNAVAILABLE'}",
        f"reason: {state.get('reason') or ''}",
        "",
        "## RISK ENGINE",
        "",
        f"QQQ exposure: {_s(risk.get('qqq_exposure'))}",
        f"put hedge: {_s(risk.get('put_hedge'))}",
        f"target hedge: {_s(risk.get('target_hedge'))}",
        f"risk budget: {_s(risk.get('risk_budget'))}",
        f"DD brake: {_s(risk.get('dd_brake'))}",
        f"convexity mode: {risk.get('convexity_mode') or 'UNAVAILABLE'}",
        f"source: {risk.get('source') or 'DERIVED'}",
        "",
        "## SELECTED STRUCTURE",
        "",
        f"status: {(doc.get('selector') or {}).get('status') or 'NOT_AVAILABLE'}",
        f"kind: {_s((doc.get('selector') or {}).get('structure', {}) and (doc.get('selector') or {}).get('structure', {}).get('kind'))}",
        f"code: {_s(((doc.get('selector') or {}).get('structure') or {}).get('code'))}",
        f"reason: {(doc.get('selector') or {}).get('reason') or ''}",
        "",
        "## PAPER PORTFOLIO",
        "",
        f"NAV: {_s(paper.get('nav'))}",
        f"daily_pnl: {_s(paper.get('daily_pnl'))}",
        f"cumulative_pnl: {_s(paper.get('cumulative_pnl'))}",
        f"max_dd: {_s(paper.get('max_dd'))}",
        f"hedge_pnl: {_s(paper.get('hedge_pnl'))}",
        f"premium_drag: {_s(paper.get('premium_drag'))}",
        f"source: {paper.get('source') or 'SIMULATED'}",
        f"orders: {paper.get('orders') or 'NONE'}",
        f"reason: {paper.get('reason') or ''}",
        "",
        "## SCENARIO SIMULATOR",
        "",
        f"status: {(doc.get('scenario') or {}).get('status')}",
        f"spot: {_s((doc.get('scenario') or {}).get('spot'))}",
        f"spot_source: {(doc.get('scenario') or {}).get('spot_source') or 'UNAVAILABLE'}",
        f"iv_source: {(doc.get('scenario') or {}).get('iv_source') or 'UNAVAILABLE'}",
        f"note: {(doc.get('scenario') or {}).get('note') or ''}",
        "",
        "## ERRORS",
        "",
    ]
    if errors:
        for e in errors:
            lines.append(f"[ERROR] {e}")
    else:
        lines.append("[ERROR] none")
    lines += ["", "## WARNINGS", ""]
    if warnings:
        for w in warnings:
            lines.append(f"[WARNING] {w}")
    else:
        lines.append("[WARNING] none")
    lines += ["", "## TESTS", ""]
    order = [
        "environment",
        "sdk",
        "connection",
        "quote",
        "vix",
        "chain",
        "option_quote",
        "surface",
        "state",
        "risk",
        "paper",
        "scenario",
        "selector",
    ]
    alias = {
        "connection": "connection_test",
        "quote": "quote_test",
        "chain": "chain_test",
        "option_quote": "option_quote_test",
        "surface": "surface_test",
        "state": "state_test",
        "paper": "paper_portfolio_test",
        "sdk": "sdk_test",
        "environment": "environment_test",
        "vix": "vix_test",
        "risk": "risk_test",
        "scenario": "scenario_test",
        "selector": "selector_test",
    }
    for key in order:
        lines.extend(_check_block(alias.get(key, key), tests.get(key)))
    lines += [
        "",
        "## OVERALL STATUS",
        "",
        f"{doc.get('overall')}",
        f"overall.class: {doc.get('overall_class') or ''}",
        f"bottleneck: {doc.get('bottleneck') or ''}",
        "",
        "## NEXT ACTION",
        "",
        str(doc.get("next_action") or ""),
        "",
        SEP,
        "END RESULT",
        SUB,
        "",
        "Paste this entire file back to Grok. Do not send Futu passwords, tokens, or 2FA.",
        "Grok Build cannot reach your Windows 127.0.0.1 — this TXT is the API.",
        "",
    ]
    return "\n".join(lines) + "\n"


def write_reports(doc: dict[str, Any], txt_path: Path) -> tuple[Path, Path]:
    txt_path.parent.mkdir(parents=True, exist_ok=True)
    txt = render_txt(doc)
    txt_path.write_text(txt, encoding="utf-8")
    js = txt_path.with_suffix(".json")
    js.write_text(json.dumps(jsonable(doc), indent=2, default=str), encoding="utf-8")
    return txt_path, js
