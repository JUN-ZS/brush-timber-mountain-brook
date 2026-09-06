"""Local diagnostic entry.

python -m backtest.local_diagnostic --diagnostic --futu-test

Never crashes the whole run on a single failed step. Always writes
reports/local_run_result.txt. Exit code 0 so the TXT is the result.
"""

from __future__ import annotations

import argparse
import platform
import subprocess
import sys
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .classify import classify_error, next_action
from .engines import run_state_risk
from .futu_adapter import load_futu, make_adapter, probe_tcp
from .paper import snapshot as paper_snapshot
from .report import write_reports
from .scenario import run_scenarios
from .selector import select_structure
from .surface import merge_quotes, pick_quote_targets, summarize
from .types import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    VIX_CODE,
    Check,
    OptionContract,
    Quote,
    jsonable,
)
from .universe import last_close, load_universe
from .vix_proxy import resolve_vix_input

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "reports" / "local_run_result.txt"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _git() -> tuple[str, str]:
    def one(args: list[str]) -> str:
        try:
            return subprocess.check_output(args, cwd=str(ROOT), timeout=3, text=True, stderr=subprocess.DEVNULL).strip()
        except Exception:
            return "UNAVAILABLE"

    return one(["git", "rev-parse", "--abbrev-ref", "HEAD"]), one(["git", "rev-parse", "--short", "HEAD"])


def _futu_version() -> str:
    futu, err = load_futu()
    if futu is None:
        return f"UNAVAILABLE ({err})"
    return getattr(futu, "__version__", "imported (version unknown)")


def overall_of(tests: dict[str, Check]) -> tuple[str, str, str]:
    """Return (overall, overall_class, bottleneck)."""
    order = [
        "environment",
        "sdk",
        "connection",
        "quote",
        "chain",
        "option_quote",
        "surface",
        "state",
        "risk",
        "paper",
        "scenario",
        "selector",
        "vix",
    ]
    code_fail = [n for n, c in tests.items() if c.status == "FAIL" and c.issue_class == "CODE"]
    if code_fail:
        return "FAIL", "CODE", code_fail[0]
    hard = ["environment", "sdk", "connection"]
    for n in hard:
        c = tests.get(n)
        if c and c.status == "FAIL":
            return "FAIL", c.issue_class or "ENVIRONMENT", n
    live_needed = ("connection", "quote", "chain", "option_quote", "surface")
    if all(n in tests and tests[n].status == "PASS" for n in live_needed):
        return "PASS", "", ""
    for n in ("quote", "chain", "option_quote", "surface"):
        c = tests.get(n)
        if c and c.status in {"FAIL", "PARTIAL", "SKIPPED"}:
            return "PARTIAL", c.issue_class or "DATA", n
    return "PARTIAL", "", "see TESTS"


def run_diagnostic(host: str, port: int, do_futu: bool) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    tests: dict[str, Check] = {}
    branch, sha = _git()
    env = {
        "os": f"{platform.system()} {platform.release()} {platform.machine()}",
        "python": sys.version.replace("\n", " "),
        "project": str(ROOT),
        "git_branch": branch,
        "git_commit": sha,
        "futu_api": _futu_version(),
    }
    tests["environment"] = Check("environment", "PASS", f"python {sys.version.split()[0]} ok", None)

    futu, ferr = load_futu()
    if futu is None:
        tests["sdk"] = Check("sdk", "FAIL", f"futu-api import failed: {ferr}", "ENVIRONMENT")
    else:
        tests["sdk"] = Check("sdk", "PASS", f"futu-api {_futu_version()}", None)

    adapter = make_adapter(host, port)
    opend: dict[str, Any] = {
        "host": host,
        "port": port,
        "connection": "NOT CONNECTED",
        "login_status": "UNAVAILABLE",
        "market_access": "UNAVAILABLE",
        "qot_logined": None,
        "trd_logined": None,
        "market_us": None,
        "reason": "",
        "class": "ENVIRONMENT",
    }
    qqq_q: Optional[Quote] = None
    vix_q: Optional[Quote] = None
    chain: dict[str, Any] = {
        "underlying": "US.QQQ",
        "expiry_count": 0,
        "contract_count": 0,
        "expiries": [],
        "source": "UNAVAILABLE",
    }
    option_quote_info: dict[str, Any] = {
        "contracts_tested": 0,
        "successful": 0,
        "failed": 0,
        "source": "UNAVAILABLE",
    }
    surface_sum: dict[str, Any] = {"available": False}
    quoted: list[OptionContract] = []
    live_qqq_closes = None
    live_vix_closes = None
    live_qqq_source = "UNAVAILABLE"
    live_vix_source = "UNAVAILABLE"
    vix_resolved: dict[str, Any] = {}
    quoted_for_proxy: list[OptionContract] = []

    if not do_futu:
        tests["connection"] = Check("connection", "SKIPPED", "--futu-test not set", None)
        tests["quote"] = Check("quote", "SKIPPED", "futu test skipped", None)
        tests["vix"] = Check("vix", "SKIPPED", "futu test skipped", None)
        tests["chain"] = Check("chain", "SKIPPED", "futu test skipped", None)
        tests["option_quote"] = Check("option_quote", "SKIPPED", "futu test skipped", None)
        tests["surface"] = Check("surface", "SKIPPED", "futu test skipped", None)
    else:
        tcp_ok, tcp_why = probe_tcp(host, port)
        if not tcp_ok:
            warnings.append(f"tcp probe {host}:{port} failed: {tcp_why}")
        try:
            conn = adapter.connect()
            tests["connection"] = conn
            opend["connection"] = "CONNECTED" if conn.status == "PASS" else "NOT CONNECTED"
            opend["reason"] = conn.reason
            opend["class"] = conn.issue_class
            state = adapter.get_market_state()
            opend["qot_logined"] = state.get("qot_logined")
            opend["trd_logined"] = state.get("trd_logined")
            opend["market_us"] = state.get("market_us")
            opend["login_status"] = (
                "LOGGED_IN"
                if state.get("qot_logined")
                else ("NOT LOGGED IN" if conn.status != "FAIL" else "UNAVAILABLE")
            )
            opend["market_access"] = str(state.get("market_us") or "UNAVAILABLE")
        except Exception as e:
            errors.append(f"connect: {type(e).__name__}: {e}")
            tests["connection"] = Check("connection", "FAIL", f"{type(e).__name__}: {e}", "CODE", extra={"trace": traceback.format_exc()[-1200:]})
            opend["reason"] = str(e)
            opend["class"] = "CODE"

        def step(name: str, fn):
            try:
                return fn()
            except Exception as e:
                errors.append(f"{name}: {type(e).__name__}: {e}")
                tests[name] = Check(name, "FAIL", f"{type(e).__name__}: {e}", "CODE", extra={"trace": traceback.format_exc()[-1200:]})
                return None

        qqq_q = step("quote", adapter.get_qqq_quote)
        if qqq_q is not None:
            if qqq_q.source == "LIVE QUOTE" and qqq_q.last is not None:
                tests["quote"] = Check("quote", "PASS", f"US.QQQ last={qqq_q.last}", None)
                live_qqq_source = "LIVE QUOTE"
            else:
                tests["quote"] = Check(
                    "quote",
                    "FAIL",
                    qqq_q.reason or "QQQ quote UNAVAILABLE",
                    classify_error(qqq_q.reason, connected=tests["connection"].status == "PASS"),
                )

        vix_q = step("vix", adapter.get_vix_quote)
        if vix_q is not None:
            if vix_q.source == "LIVE QUOTE" and vix_q.last is not None:
                tests["vix"] = Check("vix", "PASS", f"{VIX_CODE} last={vix_q.last}", None)
                live_vix_source = "LIVE QUOTE"
            else:
                tests["vix"] = Check(
                    "vix",
                    "FAIL",
                    vix_q.reason or "VIX quote UNAVAILABLE",
                    classify_error(vix_q.reason, connected=tests["connection"].status == "PASS"),
                )

        raw_chain = step("chain", lambda: adapter.get_qqq_option_chain("PUT"))
        if raw_chain is not None:
            chain = {k: v for k, v in raw_chain.items() if k != "contracts"}
            metas: list[OptionContract] = list(raw_chain.get("contracts") or [])
            if metas:
                tests["chain"] = Check(
                    "chain",
                    "PASS",
                    f"{len(metas)} contracts across {raw_chain.get('expiry_count')} expiries",
                    None,
                )
            else:
                tests["chain"] = Check(
                    "chain",
                    "FAIL",
                    raw_chain.get("reason") or "0 contracts",
                    raw_chain.get("class") or classify_error(raw_chain.get("reason"), connected=True),
                )
            spot = qqq_q.last if qqq_q and qqq_q.last else None
            targets = pick_quote_targets(metas, spot, limit=12)
            codes = [c.code for c in targets]
            option_quote_info["contracts_tested"] = len(codes)
            if codes:
                sub = adapter.subscribe(codes, ["QUOTE"])
                if sub.status != "PASS":
                    warnings.append(f"subscribe: {sub.reason}")
                quoted = adapter.get_option_quotes(codes)
                quoted = merge_quotes(targets, quoted)
                ok = [c for c in quoted if c.source == "LIVE QUOTE" and (c.bid is not None or c.last is not None)]
                option_quote_info["successful"] = len(ok)
                option_quote_info["failed"] = len(quoted) - len(ok)
                option_quote_info["source"] = "LIVE QUOTE" if ok else "UNAVAILABLE"
                option_quote_info["reason"] = None if ok else "no bid/last on tested contracts"
                if ok:
                    tests["option_quote"] = Check("option_quote", "PASS", f"{len(ok)}/{len(quoted)} contracts had LIVE bid or last", None)
                elif metas:
                    tests["option_quote"] = Check(
                        "option_quote",
                        "FAIL",
                        "chain metadata 可取得，但 dynamic option quote 失败",
                        classify_error(option_quote_info["reason"], connected=True),
                    )
                else:
                    tests["option_quote"] = Check("option_quote", "SKIPPED", "no chain to quote", "DATA")
                try:
                    adapter.unsubscribe(codes, ["QUOTE"])
                except Exception:
                    pass
                surface_sum = summarize(quoted)
                if surface_sum.get("available"):
                    tests["surface"] = Check("surface", "PASS", f"sample {surface_sum.get('sample_code')}", None)
                elif ok:
                    tests["surface"] = Check("surface", "PARTIAL", "quotes without IV/Greeks remain UNAVAILABLE (not estimated)", "DATA")
                    surface_sum["available"] = True
                else:
                    tests["surface"] = Check("surface", "FAIL", "surface unavailable", "DATA")
            else:
                tests["option_quote"] = Check("option_quote", "SKIPPED", "no contracts to quote", "DATA")
                tests["surface"] = Check("surface", "SKIPPED", "no contracts", "DATA")

        kl_q = step("klines_qqq", lambda: adapter.get_daily_closes("US.QQQ", 80))
        if kl_q and kl_q.get("source") == "LIVE QUOTE" and len(kl_q.get("closes") or []) >= 25:
            live_qqq_closes = kl_q["closes"]
            live_qqq_source = "LIVE QUOTE"
        kl_v = step("klines_vix", lambda: adapter.get_daily_closes(VIX_CODE, 80))
        if kl_v and kl_v.get("source") == "LIVE QUOTE" and kl_v.get("closes"):
            live_vix_closes = kl_v["closes"]

        quoted_for_proxy = list(quoted)
        spot_for_proxy = qqq_q.last if qqq_q and qqq_q.source == "LIVE QUOTE" else None
        try:
            vix_resolved = resolve_vix_input(
                live_vix=vix_q.last if vix_q and vix_q.source == "LIVE QUOTE" else None,
                live_vix_source=live_vix_source,
                live_vix_closes=live_vix_closes,
                option_rows=quoted_for_proxy,
                spot=spot_for_proxy,
                live_qqq_closes=live_qqq_closes,
                adapter=adapter,
            )
            if vix_resolved.get("index_quote_ok"):
                tests["vix_proxy"] = Check("vix_proxy", "SKIPPED", "live US..VIX available; proxy unused", None)
            elif vix_resolved.get("value") is not None:
                tests["vix_proxy"] = Check(
                    "vix_proxy",
                    "PASS",
                    f"{vix_resolved.get('method')}={vix_resolved.get('value'):.2f} source={vix_resolved.get('source')}",
                    None,
                    extra={"method": vix_resolved.get("method"), "reason": vix_resolved.get("reason")},
                )
            else:
                tests["vix_proxy"] = Check(
                    "vix_proxy",
                    "FAIL",
                    vix_resolved.get("reason") or "no usable VIX proxy",
                    "DATA",
                )
        except Exception as e:
            errors.append(f"vix_proxy: {type(e).__name__}: {e}")
            tests["vix_proxy"] = Check("vix_proxy", "FAIL", f"{type(e).__name__}: {e}", "CODE")
            vix_resolved = {}

        try:
            adapter.disconnect()
        except Exception:
            pass

    for required in ("quote", "vix", "vix_proxy", "chain", "option_quote", "surface"):
        tests.setdefault(required, Check(required, "SKIPPED", "not reached", "ENVIRONMENT"))

    # Engines always run; they self-label DERIVED vs LIVE.
    try:
        engines = run_state_risk(
            live_qqq_closes=live_qqq_closes,
            live_vix=vix_resolved.get("value") if vix_resolved else (vix_q.last if vix_q else None),
            live_vix_closes=live_vix_closes,
            live_qqq_source=live_qqq_source,
            live_vix_source=(vix_resolved.get("source") if vix_resolved and vix_resolved.get("value") is not None else live_vix_source),
            vix_method=(vix_resolved.get("method") if vix_resolved else None),
            vix_prev5_override=(vix_resolved.get("prev5") if vix_resolved else None),
            vix_reason=(vix_resolved.get("reason") if vix_resolved else None),
        )
        st = engines["state"]
        risk = engines["risk"]
        tests["state"] = Check(
            "state",
            "PASS" if st.get("regime") else "FAIL",
            f"{st.get('regime')} source={st.get('source')}",
            None if st.get("regime") else "CODE",
        )
        tests["risk"] = Check("risk", "PASS", f"put={risk.get('put_hedge')} qqq={risk.get('qqq_exposure')}", None)
    except Exception as e:
        errors.append(f"engines: {e}")
        tests["state"] = Check("state", "FAIL", str(e), "CODE")
        tests["risk"] = Check("risk", "FAIL", str(e), "CODE")
        st, risk = {}, {}

    try:
        u = load_universe()
        derived_spot = last_close("QQQ", u)
        derived_vix = last_close("VIX", u)
    except Exception as e:
        warnings.append(f"universe: {e}")
        derived_spot = derived_vix = None

    spot = qqq_q.last if qqq_q and qqq_q.source == "LIVE QUOTE" else None
    spot_source = "LIVE QUOTE" if spot is not None else "DERIVED"
    if spot is None:
        spot = derived_spot
    iv = None
    iv_source = "UNAVAILABLE"
    if surface_sum.get("iv") is not None and surface_sum.get("iv_source") == "LIVE QUOTE":
        iv = surface_sum["iv"]
        iv_source = "LIVE QUOTE"
    elif vix_q and vix_q.source == "LIVE QUOTE" and vix_q.last is not None:
        iv = (vix_q.last / 100.0) if vix_q.last > 3 else vix_q.last
        iv_source = "DERIVED"
    elif derived_vix is not None:
        iv = derived_vix / 100.0 if derived_vix > 3 else derived_vix
        iv_source = "DERIVED"

    try:
        selector = select_structure(quoted, spot=qqq_q.last if qqq_q and qqq_q.source == "LIVE QUOTE" else None, regime=st.get("regime") or "CALM", building=bool(st.get("building")))
        tests["selector"] = Check(
            "selector",
            "PASS" if selector.get("status") == "AVAILABLE" else "PARTIAL",
            selector.get("reason") or "",
            None if selector.get("status") == "AVAILABLE" else "DATA",
        )
    except Exception as e:
        errors.append(f"selector: {e}")
        selector = {"status": "NOT_AVAILABLE", "reason": str(e)}
        tests["selector"] = Check("selector", "FAIL", str(e), "CODE")

    try:
        paper = paper_snapshot(
            qqq=spot,
            state=st.get("regime"),
            risk_budget=risk.get("risk_budget"),
            mark_option=(selector.get("structure") or {}).get("mid") if isinstance(selector.get("structure"), dict) else None,
        )
        tests["paper"] = Check("paper", "PASS", "simulated book; no live orders", None)
    except Exception as e:
        errors.append(f"paper: {e}")
        paper = {"nav": None, "source": "UNAVAILABLE", "reason": str(e)}
        tests["paper"] = Check("paper", "FAIL", str(e), "CODE")

    try:
        scenario = run_scenarios(
            spot=spot,
            iv=iv,
            iv_source=iv_source,
            spot_source=spot_source,
            live_puts=quoted,
        )
        tests["scenario"] = Check(
            "scenario",
            "PASS" if scenario.get("status") == "PASS" else "PARTIAL",
            scenario.get("note") or scenario.get("reason") or "",
            None if scenario.get("status") == "PASS" else "DATA",
        )
    except Exception as e:
        errors.append(f"scenario: {e}")
        scenario = {"status": "FAIL", "reason": str(e)}
        tests["scenario"] = Check("scenario", "FAIL", str(e), "CODE")

    overall, overall_class, bottleneck = overall_of(tests)
    doc = {
        "run_id": uuid.uuid4().hex[:12],
        "timestamp": _now(),
        "environment": env,
        "opend": opend,
        "qqq": qqq_q.to_dict() if qqq_q else {"code": "US.QQQ", "source": "UNAVAILABLE", "last": None, "bid": None, "ask": None},
        "vix": vix_q.to_dict() if vix_q else {"code": VIX_CODE, "source": "UNAVAILABLE", "last": None},
        "vix_proxy": vix_resolved or {"source": "UNAVAILABLE"},
        "chain": chain,
        "option_quote": option_quote_info,
        "surface": surface_sum,
        "state": st,
        "risk": risk,
        "selector": selector,
        "paper": paper,
        "scenario": {k: v for k, v in scenario.items() if k != "rows"},
        "scenario_rows": scenario.get("rows") or [],
        "tests": {k: v.to_dict() for k, v in tests.items()},
        "errors": errors,
        "warnings": warnings,
        "overall": overall,
        "overall_class": overall_class,
        "bottleneck": bottleneck,
        "next_action": next_action(tests),
        "v22_untouched": True,
        "live_orders": False,
        "credentials_used": False,
    }
    # Keep tests as Check objects for next_action already done; store dicts in doc.
    doc["_tests_obj"] = tests
    return doc


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(description="V2.3 Futu OpenD local diagnostic")
    p.add_argument("--diagnostic", action="store_true", help="write reports/local_run_result.txt")
    p.add_argument("--futu-test", action="store_true", help="probe 127.0.0.1:11111 via futu-api")
    p.add_argument("--host", default=DEFAULT_HOST)
    p.add_argument("--port", type=int, default=DEFAULT_PORT)
    p.add_argument("--out", default=str(DEFAULT_OUT))
    args = p.parse_args(argv)
    if not args.diagnostic and not args.futu_test:
        args.diagnostic = True
        args.futu_test = True
    try:
        doc = run_diagnostic(args.host, args.port, args.futu_test)
    except Exception as e:
        doc = {
            "run_id": uuid.uuid4().hex[:12],
            "timestamp": _now(),
            "environment": {"python": sys.version, "os": platform.platform(), "project": str(ROOT), "git_branch": "UNAVAILABLE", "git_commit": "UNAVAILABLE", "futu_api": "UNAVAILABLE"},
            "opend": {"host": args.host, "port": args.port, "connection": "NOT CONNECTED", "reason": f"{type(e).__name__}: {e}", "class": "CODE"},
            "qqq": {"source": "UNAVAILABLE"},
            "vix": {"source": "UNAVAILABLE"},
            "chain": {},
            "option_quote": {},
            "surface": {},
            "state": {},
            "risk": {},
            "selector": {},
            "paper": {},
            "scenario": {},
            "tests": {"environment": {"name": "environment", "status": "FAIL", "reason": str(e), "class": "CODE"}},
            "errors": [traceback.format_exc()[-2000:]],
            "warnings": [],
            "overall": "FAIL",
            "overall_class": "CODE",
            "bottleneck": "diagnostic runner",
            "next_action": "CODE bug in the diagnostic runner. Paste this TXT back to Grok. Do not send credentials.",
        }
    out = Path(args.out)
    if not out.is_absolute():
        out = ROOT / out
    txt, js = write_reports(doc, out)
    sys.stdout.write(f"WROTE {txt}\nWROTE {js}\nOVERALL {doc.get('overall')} class={doc.get('overall_class')} bottleneck={doc.get('bottleneck')}\n")
    sys.stdout.write(f"NEXT ACTION:\n{doc.get('next_action')}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
