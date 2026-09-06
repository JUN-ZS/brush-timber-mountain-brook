/**
 * V2.3 live reality layer (browser).
 *
 * The Grok preview / Vercel deploy cannot open the user's Windows
 * Futu OpenD at 127.0.0.1:11111. This module therefore defaults to
 * UNAVAILABLE / WAITING_FOR_LOCAL_DIAGNOSTIC and never invents LIVE quotes.
 *
 * Scenario marks use Observed QQQ/VIX EOD + Black-Scholes and are labelled
 * DERIVED. Paper is SIMULATED. No broker orders.
 */
import { bsPrice, ivShockForMove, normIv } from "./black-scholes.ts";
import { lastBar, universe } from "./bars.ts";
import { state } from "./backtest.ts";

export type PriceSource = "LIVE QUOTE" | "DERIVED" | "ESTIMATED" | "SYNTHETIC" | "UNAVAILABLE";
export type CheckStatus = "PASS" | "FAIL" | "PARTIAL" | "SKIPPED";
export type LiveStatus = "WAITING_FOR_LOCAL_DIAGNOSTIC" | "NOT CONNECTED" | "LIVE" | "UNAVAILABLE";

export type LiveQuote = {
  code: string;
  last: number | null;
  bid: number | null;
  ask: number | null;
  source: PriceSource;
  timestamp: string | null;
  reason?: string;
};

export type LiveContract = {
  code: string;
  strike: number | null;
  dte: number | null;
  right: "PUT" | "CALL";
  bid: number | null;
  ask: number | null;
  last: number | null;
  mid: number | null;
  iv: number | null;
  delta: number | null;
  gamma: number | null;
  theta: number | null;
  vega: number | null;
  oi: number | null;
  spreadPct: number | null;
  source: PriceSource;
};

export type SelectedStructure = {
  status: "AVAILABLE" | "NOT_AVAILABLE";
  kind: string | null;
  code: string | null;
  strike: number | null;
  dte: number | null;
  delta: number | null;
  iv: number | null;
  bid: number | null;
  ask: number | null;
  mid: number | null;
  spreadPct: number | null;
  source: PriceSource;
  reason: string;
  why: string[];
};

export type ScenarioRow = {
  shock: number;
  structure: "QQQ_ONLY" | "ATM_PUT" | "OTM5_PUT" | "PUT_SPREAD";
  underlyingPnl: number;
  hedgePnl: number;
  totalPnl: number;
  protectionPct: number | null;
  navImpact: number;
  entrySource: PriceSource | "N/A";
  shockedOptionSource: PriceSource | "N/A";
};

export type PaperBook = {
  nav: number;
  dailyPnl: number;
  cumulativePnl: number;
  maxDd: number;
  hedgePnl: number;
  premiumDrag: number;
  positions: Array<{ code: string; qty: number; entry: number; reason: string }>;
  source: "SIMULATED";
  orders: "NONE";
};

export const PAPER_KEY = "pulse-v23-paper";
export const START_NAV = 100_000;
export const SHOCKS = [-0.01, -0.03, -0.05, -0.1, -0.2] as const;

export function eodSpot(): { qqq: number | null; vix: number | null; date: string; source: PriceSource } {
  const q = universe.c.QQQ?.[lastBar];
  const v = universe.c.VIX?.[lastBar];
  return {
    qqq: q != null && q > 0 ? q : null,
    vix: v != null && v > 0 ? v : null,
    date: universe.dates[lastBar] ?? "UNAVAILABLE",
    source: "DERIVED",
  };
}

export function derivedState() {
  const s = state(lastBar);
  return { ...s, source: "DERIVED" as const, asof: universe.dates[lastBar] };
}

export function suggestedRisk(regime: string, building: boolean) {
  const table: Record<string, number> = { CALM: 0.25, UNSTABLE: 0.5, TAIL: 0.75, RECOVERY: 0.25 };
  let put = table[regime] ?? 0.25;
  if (building) put = Math.max(put, 0.75);
  return {
    qqqExposure: 1,
    putHedge: put,
    targetHedge: put,
    riskBudget: 1,
    ddBrake: null as number | null,
    convexityMode: "PUT_OVERLAY",
    source: "DERIVED" as const,
    note: "Suggested overlay, not a frozen V2.2 spec and not an order.",
  };
}

export function emptyQuote(code: string, reason: string): LiveQuote {
  return { code, last: null, bid: null, ask: null, source: "UNAVAILABLE", timestamp: null, reason };
}

export function previewConnection(): {
  status: LiveStatus;
  reason: string;
  issueClass: "ENVIRONMENT";
} {
  return {
    status: "WAITING_FOR_LOCAL_DIAGNOSTIC",
    reason:
      "This preview cannot reach your Windows Futu OpenD. Run python -m backtest.local_diagnostic --diagnostic --futu-test and paste reports/local_run_result.txt back to Grok.",
    issueClass: "ENVIRONMENT",
  };
}

export function selectLiveStructure(contracts: LiveContract[], spot: number | null, regime: string): SelectedStructure {
  if (spot == null || spot <= 0) {
    return {
      status: "NOT_AVAILABLE",
      kind: null,
      code: null,
      strike: null,
      dte: null,
      delta: null,
      iv: null,
      bid: null,
      ask: null,
      mid: null,
      spreadPct: null,
      source: "UNAVAILABLE",
      reason: "no LIVE underlying spot",
      why: ["spot UNAVAILABLE — selector will not guess"],
    };
  }
  const live = contracts.filter((c) => c.source === "LIVE QUOTE" && c.right === "PUT" && c.bid != null && c.bid > 0);
  if (!live.length) {
    return {
      status: "NOT_AVAILABLE",
      kind: null,
      code: null,
      strike: null,
      dte: null,
      delta: null,
      iv: null,
      bid: null,
      ask: null,
      mid: null,
      spreadPct: null,
      source: "UNAVAILABLE",
      reason: "no LIVE option quotes. DERIVED / SYNTHETIC contracts are not allowed to win.",
      why: [
        `STATE = ${regime}`,
        "Need LIVE PUT with DTE 14–60, OTM 2–8%, bid > 0",
        "Paste local_run_result.txt after a Windows OpenD run to fill this panel",
      ],
    };
  }
  const otmTarget = regime === "TAIL" ? 0.02 : regime === "UNSTABLE" ? 0.03 : 0.05;
  live.sort((a, b) => {
    const sa = score(a, spot, otmTarget);
    const sb = score(b, spot, otmTarget);
    return sb - sa;
  });
  const best = live[0];
  const otm = best.strike != null ? 1 - best.strike / spot : null;
  return {
    status: "AVAILABLE",
    kind: "OTM_PUT",
    code: best.code,
    strike: best.strike,
    dte: best.dte,
    delta: best.delta,
    iv: best.iv,
    bid: best.bid,
    ask: best.ask,
    mid: best.mid,
    spreadPct: best.spreadPct,
    source: "LIVE QUOTE",
    reason: "best LIVE put under the first-stage filter (not an order)",
    why: [
      `STATE = ${regime}`,
      `DTE = ${best.dte}`,
      `OTM = ${otm == null ? "—" : (otm * 100).toFixed(2) + "%"}`,
      `bid ${best.bid} / ask ${best.ask}`,
      "Compared only among LIVE puts",
    ],
  };
}

function score(c: LiveContract, spot: number, otmTarget: number) {
  if (c.strike == null || c.dte == null) return -99;
  const otm = 1 - c.strike / spot;
  const spread = c.spreadPct ?? 0.25;
  return -(spread * 4 + Math.abs(c.dte - 30) / 30 + Math.abs(otm - otmTarget) / 0.05);
}

function putMark(spot: number, strike: number, dte: number, iv: number) {
  return bsPrice({ spot, strike, tYears: Math.max(dte, 1) / 365, iv, right: "PUT" });
}

export function runScenarios(args: {
  spot: number;
  iv: number;
  spotSource: PriceSource;
  ivSource: PriceSource;
  nav?: number;
  dte?: number;
}): ScenarioRow[] {
  const nav = args.nav ?? START_NAV;
  const dte = args.dte ?? 30;
  const shares = nav / args.spot;
  const contracts = shares / 100;
  const sig = normIv(args.iv, 0.2);
  const rows: ScenarioRow[] = [];
  for (const shock of SHOCKS) {
    const newSpot = args.spot * (1 + shock);
    const qqqPnl = shares * (newSpot - args.spot);
    const iv2 = sig * ivShockForMove(shock);
    const kinds: ScenarioRow["structure"][] = ["QQQ_ONLY", "ATM_PUT", "OTM5_PUT", "PUT_SPREAD"];
    for (const kind of kinds) {
      let hedge = 0;
      if (kind === "ATM_PUT") {
        const k = Math.round(args.spot);
        hedge = contracts * 100 * (putMark(newSpot, k, Math.max(dte - 1, 1), iv2) - putMark(args.spot, k, dte, sig));
      } else if (kind === "OTM5_PUT") {
        const k = Math.round(args.spot * 0.95);
        hedge = contracts * 100 * (putMark(newSpot, k, Math.max(dte - 1, 1), iv2) - putMark(args.spot, k, dte, sig));
      } else if (kind === "PUT_SPREAD") {
        const kl = Math.round(args.spot * 0.95);
        const ks = Math.round(args.spot * 0.9);
        const entry = putMark(args.spot, kl, dte, sig) - putMark(args.spot, ks, dte, sig);
        const exitp = putMark(newSpot, kl, Math.max(dte - 1, 1), iv2) - putMark(newSpot, ks, Math.max(dte - 1, 1), iv2);
        hedge = contracts * 100 * (exitp - entry);
      }
      const total = qqqPnl + hedge;
      rows.push({
        shock,
        structure: kind,
        underlyingPnl: qqqPnl,
        hedgePnl: hedge,
        totalPnl: total,
        protectionPct: qqqPnl < 0 ? Math.max(0, Math.min(1, 1 - total / qqqPnl)) : null,
        navImpact: total / nav,
        entrySource: kind === "QQQ_ONLY" ? args.spotSource : "DERIVED",
        shockedOptionSource: kind === "QQQ_ONLY" ? "N/A" : "DERIVED",
      });
    }
  }
  return rows;
}

export function emptyPaper(): PaperBook {
  return {
    nav: START_NAV,
    dailyPnl: 0,
    cumulativePnl: 0,
    maxDd: 0,
    hedgePnl: 0,
    premiumDrag: 0,
    positions: [],
    source: "SIMULATED",
    orders: "NONE",
  };
}

export function loadPaper(): PaperBook {
  if (typeof localStorage === "undefined") return emptyPaper();
  try {
    const raw = localStorage.getItem(PAPER_KEY);
    if (!raw) return emptyPaper();
    const p = JSON.parse(raw) as PaperBook;
    return { ...emptyPaper(), ...p, source: "SIMULATED", orders: "NONE" };
  } catch {
    return emptyPaper();
  }
}

export function savePaper(book: PaperBook) {
  if (typeof localStorage === "undefined") return;
  localStorage.setItem(PAPER_KEY, JSON.stringify({ ...book, source: "SIMULATED", orders: "NONE" }));
}

export function nextActionPreview() {
  return [
    "STEP 1  啟動 Futu OpenD，確認已登入。不要把帳戶/密碼/Token 貼給 Grok。",
    "STEP 2  在 repo 根目錄執行：",
    "        python -m backtest.local_diagnostic --diagnostic --futu-test",
    "STEP 3  打開 reports/local_run_result.txt，全部 COPY。",
    "STEP 4  貼回 Grok。Grok 會判斷 CODE / ENVIRONMENT / PERMISSION / DATA / API，再給下一個最小修正。",
  ];
}
