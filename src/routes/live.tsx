import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState, type ReactNode } from "react";
import { Panel, Shell } from "@/components/shell";
import { Badge } from "@/components/ui/badge";
import { fmtNum, fmtPct, fmtUsd } from "@/lib/utils";
import {
  derivedState,
  eodSpot,
  emptyQuote,
  emptyPaper,
  nextActionPreview,
  previewConnection,
  runScenarios,
  selectLiveStructure,
  suggestedRisk,
  type ScenarioRow,
} from "@/lib/pulse/live";

export const Route = createFileRoute("/live")({ component: Page });

const STRUCTURES: ScenarioRow["structure"][] = ["QQQ_ONLY", "ATM_PUT", "OTM5_PUT", "PUT_SPREAD"];
const LABELS: Record<ScenarioRow["structure"], string> = {
  QQQ_ONLY: "QQQ only",
  ATM_PUT: "ATM PUT",
  OTM5_PUT: "5% OTM PUT",
  PUT_SPREAD: "Put spread",
};

function Page() {
  const conn = previewConnection();
  const eod = eodSpot();
  const st = derivedState();
  const risk = suggestedRisk(st.regime, st.building);
  const qqq = emptyQuote("US.QQQ", "OpenD not reachable from this preview");
  const vix = emptyQuote("US.VIX", "OpenD not reachable from this preview");
  const selected = selectLiveStructure([], null, st.regime);
  const [shock, setShock] = useState(-0.05);
  const [paper] = useState(emptyPaper);
  const rows = useMemo(() => {
    if (eod.qqq == null || eod.vix == null) return [];
    return runScenarios({
      spot: eod.qqq,
      iv: eod.vix > 3 ? eod.vix / 100 : eod.vix,
      spotSource: "DERIVED",
      ivSource: "DERIVED",
    });
  }, [eod.qqq, eod.vix]);
  const slice = rows.filter((r) => r.shock === shock);
  const steps = nextActionPreview();

  return (
    <Shell>
      <div className="grid gap-4">
        <Panel kicker="V2.3 LIVE REALITY LAYER" title="Futu OpenD · 不下真實單">
          <p className="max-w-4xl text-sm leading-relaxed text-muted">
            V2.2 歷史回測沒有被改寫。這一頁接的是真實行情路徑。預覽環境到不了你 Windows 上的 OpenD，所以連線狀態是
            WAITING_FOR_LOCAL_DIAGNOSTIC，不是策略 FAIL。本機跑診斷、把 TXT 貼回 Grok，才會出現 LIVE QUOTE。
          </p>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 md:grid-cols-4">
            <Metric k="OpenD" v={conn.status} tone="lock" />
            <Metric k="QQQ LIVE" v="UNAVAILABLE" tone="missing" />
            <Metric k="VIX LIVE" v="UNAVAILABLE" tone="missing" />
            <Metric k="Selected hedge" v="NOT_AVAILABLE" tone="fragile" />
          </div>
          <p className="mt-3 font-mono text-xs text-subtle">{conn.reason}</p>
        </Panel>

        <div className="grid gap-4 md:grid-cols-2">
          <Panel kicker="CONNECTION" title="127.0.0.1:11111">
            <dl className="grid grid-cols-2 gap-y-2 text-sm">
              <Dt>status</Dt>
              <Dd>
                <Badge tone="lock">{conn.status}</Badge>
              </Dd>
              <Dt>class</Dt>
              <Dd>{conn.issueClass}</Dd>
              <Dt>login</Dt>
              <Dd>UNAVAILABLE</Dd>
              <Dt>US market</Dt>
              <Dd>UNAVAILABLE</Dd>
              <Dt>live orders</Dt>
              <Dd>FORBIDDEN</Dd>
            </dl>
          </Panel>
          <Panel kicker="LIVE QUOTES" title="沒有 LIVE 就不會填數字">
            <QuoteRow label="QQQ" q={qqq} />
            <QuoteRow label="VIX" q={vix} />
            <p className="mt-3 text-xs text-subtle">
              EOD fallback（DERIVED, {eod.date}）：QQQ {fmtNum(eod.qqq, 2)} · VIX {fmtNum(eod.vix, 2)}. 這不是
              LIVE QUOTE。
            </p>
          </Panel>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <Panel kicker="STATE / RISK" title="V2.2 規則，EOD 先跑一遍">
            <dl className="grid grid-cols-2 gap-y-2 text-sm">
              <Dt>state</Dt>
              <Dd>
                {st.regime}
                {st.building ? " + BUILDING" : ""}
              </Dd>
              <Dt>source</Dt>
              <Dd>DERIVED</Dd>
              <Dt>QQQ exposure</Dt>
              <Dd>{fmtPct(risk.qqqExposure, 0)}</Dd>
              <Dt>put hedge</Dt>
              <Dd>{fmtPct(risk.putHedge, 0)}</Dd>
              <Dt>realized vol</Dt>
              <Dd>{fmtPct(st.vol, 1)}</Dd>
              <Dt>mom 20d / 60d</Dt>
              <Dd>
                {fmtPct(st.dd20, 1)} / {fmtPct(st.mom60, 1)}
              </Dd>
            </dl>
            <p className="mt-3 text-xs text-subtle">{risk.note}</p>
          </Panel>
          <Panel kicker="OPTION SURFACE" title="STRIKE × DTE × IV × GREEKS">
            <p className="text-sm text-muted">
              尚未有 LIVE chain。缺欄位會標 UNAVAILABLE，不會用 0.25 IV 或 Black-Scholes 冒充 LIVE。
            </p>
            <div className="mt-3 grid grid-cols-2 gap-2 font-mono text-xs text-subtle sm:grid-cols-4">
              {["iv", "delta", "bid", "ask", "mid", "spread", "oi", "volume"].map((k) => (
                <div key={k} className="rounded-md border border-line px-2 py-2">
                  {k}: UNAVAILABLE
                </div>
              ))}
            </div>
          </Panel>
        </div>

        <Panel kicker="SELECTED STRUCTURE" title="WHY THIS STRUCTURE?">
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone="fragile">{selected.status}</Badge>
            <Badge tone="missing">{selected.source}</Badge>
          </div>
          <p className="mt-3 text-sm text-muted">{selected.reason}</p>
          <ul className="mt-3 space-y-1 text-sm text-muted">
            {selected.why.map((w) => (
              <li key={w}>• {w}</li>
            ))}
          </ul>
        </Panel>

        <div className="grid gap-4 md:grid-cols-2">
          <Panel kicker="PAPER PORTFOLIO" title="SIMULATED · 沒有 OpenSecTradeContext">
            <dl className="grid grid-cols-2 gap-y-2 text-sm">
              <Dt>NAV</Dt>
              <Dd>{fmtUsd(paper.nav, 0)}</Dd>
              <Dt>daily P&L</Dt>
              <Dd>{fmtUsd(paper.dailyPnl, 0)}</Dd>
              <Dt>max DD</Dt>
              <Dd>{fmtPct(paper.maxDd, 2)}</Dd>
              <Dt>orders</Dt>
              <Dd>{paper.orders}</Dd>
            </dl>
            <p className="mt-3 text-xs text-subtle">診斷通過、有 LIVE 結構之前，不會自動開倉。紙上交易也不是真實委託。</p>
          </Panel>
          <Panel kicker="NEXT ACTION" title="RUN → COPY TXT → PASTE">
            <ol className="space-y-2 text-sm text-muted">
              {steps.map((s) => (
                <li key={s} className="font-mono text-xs leading-relaxed md:text-sm">
                  {s}
                </li>
              ))}
            </ol>
            <p className="mt-3 text-xs text-subtle">結果檔：reports/local_run_result.txt</p>
          </Panel>
        </div>

        <Panel kicker="SCENARIO SIMULATOR · DERIVED" title="QQQ 衝擊 vs 保護結構">
          <p className="text-sm text-muted">
            進場與衝擊後的選擇權價值都是 DERIVED（EOD QQQ + VIX 當 IV 的 Black-Scholes）。有 LIVE 報價時，進場可以標
            LIVE QUOTE，衝擊後重定價仍然是 DERIVED。
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            {([-0.01, -0.03, -0.05, -0.1, -0.2] as const).map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => setShock(s)}
                className={`min-h-11 rounded-sm border px-3 text-sm ${
                  shock === s ? "border-accent bg-elevated text-fg" : "border-line text-muted hover:text-fg"
                }`}
              >
                QQQ {fmtPct(s, 0)}
              </button>
            ))}
          </div>
          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead className="text-xs text-subtle">
                <tr>
                  {["structure", "under P&L", "hedge P&L", "total", "protection", "NAV", "source"].map((h) => (
                    <th key={h} className="px-3 py-2">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {STRUCTURES.map((id) => {
                  const r = slice.find((x) => x.structure === id);
                  if (!r) return null;
                  return (
                    <tr key={id} className="border-t border-line">
                      <td className="px-3 py-2">{LABELS[id]}</td>
                      <td className="px-3 py-2 font-mono">{fmtUsd(r.underlyingPnl, 0)}</td>
                      <td className="px-3 py-2 font-mono">{fmtUsd(r.hedgePnl, 0)}</td>
                      <td className="px-3 py-2 font-mono">{fmtUsd(r.totalPnl, 0)}</td>
                      <td className="px-3 py-2 font-mono">{r.protectionPct == null ? "—" : fmtPct(r.protectionPct, 0)}</td>
                      <td className="px-3 py-2 font-mono">{fmtPct(r.navImpact, 2)}</td>
                      <td className="px-3 py-2 font-mono text-xs text-subtle">{r.shockedOptionSource}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Panel>
      </div>
    </Shell>
  );
}

function Metric({ k, v, tone }: { k: string; v: string; tone?: "lock" | "missing" | "fragile" | "pass" }) {
  return (
    <div className="rounded-md border border-line bg-elevated p-3">
      <div className="text-xs text-subtle">{k}</div>
      <div className="mt-1 font-mono text-lg tabular-nums">{v}</div>
      {tone ? (
        <div className="mt-2">
          <Badge tone={tone}>{tone === "lock" ? "NOT LIVE" : tone.toUpperCase()}</Badge>
        </div>
      ) : null}
    </div>
  );
}

function Dt({ children }: { children: string }) {
  return <dt className="text-subtle">{children}</dt>;
}
function Dd({ children }: { children: ReactNode }) {
  return <dd className="font-mono text-fg">{children}</dd>;
}
function QuoteRow({ label, q }: { label: string; q: { last: number | null; source: string; reason?: string } }) {
  return (
    <div className="flex items-baseline justify-between gap-3 border-b border-line py-2 last:border-0">
      <span className="text-sm text-muted">{label}</span>
      <span className="font-mono text-sm">
        {q.last == null ? "UNAVAILABLE" : fmtNum(q.last, 2)} · {q.source}
      </span>
    </div>
  );
}
