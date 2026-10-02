import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Panel, Shell } from "@/components/shell";
import { fmtPct, fmtUsd } from "@/lib/utils";
import snapshot from "@/data/rolling_floor_ui_snapshot.json";

export const Route = createFileRoute("/floor")({ component: Page });

type LedgerEntry = {
  id: string;
  recordedAt: string;
  asOf: string;
  month: number;
  amount: number;
  cumulativeAmount: number;
  cumulativeFraction: number;
  clockTarget: number;
  delta: number;
  status: "BELOW_CLOCK" | "ON_CLOCK" | "AHEAD";
};

const LEDGER_KEY = "qqq-rolling-floor-ledger-v1";

function Page() {
  const [capital, setCapital] = useState(100000);
  const [alreadyDeployed, setAlreadyDeployed] = useState(0);
  const [actualNow, setActualNow] = useState(0);
  const [month, setMonth] = useState(0);
  const [ledger, setLedger] = useState<LedgerEntry[]>([]);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(LEDGER_KEY);
      if (raw) setLedger(JSON.parse(raw) as LedgerEntry[]);
    } catch {}
  }, []);

  useEffect(() => {
    try {
      window.localStorage.setItem(LEDGER_KEY, JSON.stringify(ledger));
    } catch {}
  }, [ledger]);

  const suggestedFraction = Math.max(
    snapshot.current.clockFirstMonthTarget,
    snapshot.current.coupledTargetAtPhaseZero,
  );
  const currentAlreadyDeployed = alreadyDeployed / Math.max(capital, 1);
  const requiredExtraFraction = Math.max(0, suggestedFraction - currentAlreadyDeployed);
  const suggestedAmount = requiredExtraFraction * capital;
  const currentClock = clockTarget(month);
  const capitalPath = buildCapitalPath(ledger, capital);
  const responseCurves = snapshot.current.perScale.map((s) => ({
    scale: s.scaleYears,
    xs: s.responseProfile.deploymentFractions,
    ys: s.responseProfile.q05Terminal,
  }));
  const maxResponse = Math.max(...responseCurves.flatMap((c) => c.ys));
  const responseDomain = [1, Math.max(3.5, maxResponse * 1.05)];
  const ndx = snapshot.current.mutualChase.find((x) => x.channel === "NDX");
  const composite = snapshot.current.mutualChase.find((x) => x.channel === "NASDAQCOM");
  const ndxHandoff = ndx ? leaderHandoff(ndx.topology.leaderScaleBySegment) : null;

  const bandText = useMemo(() => {
    const actual = currentAlreadyDeployed;
    if (actual < currentClock - 0.005) return "BELOW CLOCK";
    if (actual > currentClock + 0.005) return "AHEAD";
    return "ON CLOCK";
  }, [currentAlreadyDeployed, currentClock]);

  function recordPoint() {
    if (!Number.isFinite(actualNow) || actualNow < 0) return;
    const cumulativeAmount = ledger.reduce((sum, x) => sum + x.amount, 0) + actualNow;
    if (cumulativeAmount > capital + 1e-8) return;
    const cumulativeFraction = cumulativeAmount / Math.max(capital, 1);
    const ct = currentClock;
    const delta = cumulativeFraction - ct;
    const status = delta < -0.005 ? "BELOW_CLOCK" : delta > 0.005 ? "AHEAD" : "ON_CLOCK";
    setLedger((entries) => [
      ...entries,
      {
        id: globalThis.crypto?.randomUUID?.() ?? String(Date.now()),
        recordedAt: new Date().toISOString(),
        asOf: snapshot.current.asOf,
        month,
        amount: actualNow,
        cumulativeAmount,
        cumulativeFraction,
        clockTarget: ct,
        delta,
        status,
      },
    ]);
    setAlreadyDeployed(cumulativeAmount);
    setActualNow(0);
  }

  function exportLedger() {
    const payload = JSON.stringify(
      {
        version: "rolling-floor-ledger.v1",
        asset: snapshot.asset,
        modelAsOf: snapshot.asOf,
        horizonYears: snapshot.horizonYears,
        entries: ledger,
      },
      null,
      2,
    );
    navigator.clipboard?.writeText(payload).then(
      () => {
        setCopied(true);
        window.setTimeout(() => setCopied(false), 1400);
      },
      () => window.alert(payload),
    );
  }

  return (
    <Shell>
      <div className="grid gap-4">
        <Panel kicker="10Y CAPITAL FLOOR / CONTROL PLANE" title="此刻應投入多少？">
          <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
            <div>
              <div className="flex flex-wrap items-end gap-3">
                <div>
                  <p className="font-mono text-xs text-subtle">今期建議投入</p>
                  <p className="mt-1 text-4xl font-semibold tabular-nums">{fmtUsd(suggestedAmount, 2)}</p>
                  <p className="mt-1 font-mono text-xs text-muted">
                    {fmtPct(requiredExtraFraction, 3)} of total capital · model as-of {snapshot.asOf}
                  </p>
                </div>
                <Badge tone="pass">{fmtPct(suggestedFraction, 3)} cumulative target</Badge>
              </div>
              <p className="mt-4 max-w-2xl text-sm text-muted">
                現行 snapshot 的 95% terminal-principal floor 沒有要求額外 front-load；因此現在首先受 10Y
                deadline clock 限制：第 1 個月 = 1/120 = 0.833%。這是歷史條件下的模型路徑，不是未來打平保證。
              </p>
            </div>
            <div className="grid gap-3">
              <InputRow label="Total capital (USD)" value={capital} onChange={setCapital} />
              <InputRow
                label="Already deployed in this 10Y cycle"
                value={alreadyDeployed}
                onChange={setAlreadyDeployed}
              />
            </div>
          </div>
        </Panel>

        <div className="grid gap-4 lg:grid-cols-3">
          <MetricCard
            kicker="MARKET STATE"
            title={snapshot.current.divergenceStateAtPhaseZero}
            detail={"signal count " + snapshot.current.signalCount + " · agreement " + fmtPct(snapshot.current.agreementAtPhaseZero, 0)}
          />
          <MetricCard
            kicker="MUTUAL CHASE"
            title={ndx?.topology.state ?? "THIN"}
            detail={
              ndxHandoff
                ? "NDX: " + ndxHandoff.from + "Y → " + ndxHandoff.to + "Y at ~" + fmtPct(ndxHandoff.at, 0) + " deployment"
                : "no handoff"
            }
          />
          <MetricCard
            kicker="RULE CHECK"
            title={bandText}
            detail={fmtPct(currentClock, 3) + " minimum cumulative deployment by month " + month}
          />
        </div>

        <Panel kicker="CHASE GEOMETRY / Q05 TERMINAL RESPONSE" title="20Y / 30Y / 50Y 互追">
          <div className="overflow-x-auto">
            <ResponseChart
              curves={responseCurves}
              domain={responseDomain}
              currentX={suggestedFraction}
              handoff={ndxHandoff}
            />
          </div>
          <div className="mt-3 flex flex-wrap gap-3 text-xs text-muted">
            {responseCurves.map((c) => (
              <span key={c.scale} className="font-mono">
                {c.scale}Y · q05 @ 0% = {c.ys[0].toFixed(2)}× · q05 @ 100% = {c.ys.at(-1)?.toFixed(2)}×
              </span>
            ))}
          </div>
          <p className="mt-3 text-xs text-subtle">
            填色帶 = 三尺度 q05 response 的上下包絡；虛線 = 今期投入點；橫向換手標記 = NDX 20Y → 30Y。
            這層只做互追監視，未進入資金控制。
          </p>
        </Panel>

        <Panel kicker="CAPITAL TAPE / 10Y RULE CHECK" title="實際投入點 vs hard deadline rail">
          <div className="grid gap-4 lg:grid-cols-[1fr_300px]">
            <div className="overflow-x-auto">
              <CapitalChart points={capitalPath} suggestedFraction={suggestedFraction} />
            </div>
            <div className="grid gap-3 content-start">
              <InputRow
                label="Month into 10Y (0–119)"
                value={month}
                onChange={(x) => setMonth(Math.max(0, Math.min(119, Math.round(x))))}
              />
              <InputRow label="Actual cash invested now" value={actualNow} onChange={setActualNow} />
              <div className="rounded-lg border border-line bg-elevated p-3">
                <p className="font-mono text-xs text-subtle">CURRENT CLOCK FLOOR</p>
                <p className="mt-1 text-lg tabular-nums">{fmtPct(currentClock, 3)}</p>
                <p className="text-xs text-muted">minimum cumulative deployed at this phase</p>
              </div>
              <button
                type="button"
                onClick={recordPoint}
                className="min-h-11 rounded-md border border-accent/60 bg-accent px-4 text-sm font-medium text-accent-fg"
              >
                記錄今次實際投入
              </button>
              <button
                type="button"
                onClick={exportLedger}
                className="min-h-11 rounded-md border border-line px-4 text-sm text-muted hover:text-fg"
              >
                {copied ? "LEDGER COPIED" : "COPY LEDGER JSON"}
              </button>
            </div>
          </div>
          <LedgerTable entries={ledger} />
        </Panel>

        <div className="grid gap-4 lg:grid-cols-2">
          <Panel kicker="LIVE SNAPSHOT" title="三尺度現在各自說甚麼">
            <div className="grid gap-2">
              {snapshot.current.perScale.map((s) => (
                <div key={s.scaleYears} className="flex items-center justify-between rounded-md border border-line px-3 py-2">
                  <span className="font-mono text-sm">{s.scaleYears}Y</span>
                  <span className="font-mono text-xs tabular-nums text-muted">
                    floor-front-load {fmtPct(s.target, 1)} · q05(0%) {s.responseProfile.q05Terminal[0].toFixed(2)}×
                  </span>
                </div>
              ))}
            </div>
          </Panel>
          <Panel kicker="SEMANTIC LOCK" title="監視可以，偷改規則不可以">
            <div className="grid gap-2 text-sm text-muted">
              <p>LOWER RAIL = hard 10Y deadline；低於它就是偏離。</p>
              <p>CHASE ENVELOPE = 20/30/50Y response geometry；用來看上、下追趕。</p>
              <p>MUTUAL-CHASE = diagnostic only；尚未直接增加或減少投入。</p>
              <p>QQQ = observed outcome；NDX / NASDAQ Composite = state proxies。</p>
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              <Badge tone="pass">RESEARCH-ONLY</Badge>
              <Badge tone="lock">NO GUARANTEED BREAK-EVEN</Badge>
              <Badge tone={composite?.topology.state === "CONVERGENT" ? "pass" : "fragile"}>
                NASDAQCOM {composite?.topology.state ?? "THIN"}
              </Badge>
            </div>
          </Panel>
        </div>
      </div>
    </Shell>
  );
}

function InputRow({ label, value, onChange }: { label: string; value: number; onChange: (value: number) => void }) {
  return (
    <label className="grid gap-1 text-sm">
      <span className="font-mono text-xs text-subtle">{label}</span>
      <input
        type="number"
        min={0}
        step="0.01"
        value={value}
        onChange={(e) => onChange(Number(e.target.value) || 0)}
        className="min-h-11 w-full rounded-md border border-line bg-elevated px-3 font-mono tabular-nums outline-none focus:border-accent"
      />
    </label>
  );
}

function MetricCard({ kicker, title, detail }: { kicker: string; title: string; detail: string }) {
  return (
    <div className="rounded-xl border border-line bg-surface p-4">
      <p className="font-mono text-xs tracking-[0.14em] text-subtle">{kicker}</p>
      <p className="mt-1 text-xl font-medium">{title}</p>
      <p className="mt-1 font-mono text-xs text-muted">{detail}</p>
    </div>
  );
}

function ResponseChart({
  curves,
  domain,
  currentX,
  handoff,
}: {
  curves: Array<{ scale: number; xs: number[]; ys: number[] }>;
  domain: number[];
  currentX: number;
  handoff: { from: number; to: number; at: number } | null;
}) {
  const W = 1000, H = 380, L = 60, R = 24, T = 22, B = 46;
  const plotW = W - L - R, plotH = H - T - B;
  const x = (v: number) => L + v * plotW;
  const y = (v: number) => T + (domain[1] - v) / (domain[1] - domain[0]) * plotH;
  const palette = ["var(--color-accent)", "var(--color-fragile)", "var(--color-muted)"];
  const top = curves[0].ys.map((_, i) => Math.max(...curves.map((c) => c.ys[i])));
  const bottom = curves[0].ys.map((_, i) => Math.min(...curves.map((c) => c.ys[i])));
  const band =
    curves[0].xs.map((v, i) => [x(v), y(top[i])]).concat(
      curves[0].xs.slice().reverse().map((v, i) => [x(v), y(bottom[bottom.length - 1 - i])]),
    ).map((p) => p.join(",")).join(" ");

  return (
    <svg viewBox={"0 0 " + W + " " + H} className="min-w-[760px] w-full" role="img" aria-label="20 30 50 year response curves">
      <rect x={L} y={T} width={plotW} height={plotH} fill="var(--color-elevated)" opacity="0.45" rx="8" />
      {[1, 2, 3].map((v) => (
        <g key={v}>
          <line x1={L} x2={W - R} y1={y(v)} y2={y(v)} stroke="var(--color-line)" />
          <text x={L - 10} y={y(v) + 4} textAnchor="end" fill="var(--color-subtle)" fontSize="11">{v.toFixed(1)}×</text>
        </g>
      ))}
      <polygon points={band} fill="var(--color-accent)" opacity="0.08" />
      <line x1={x(currentX)} x2={x(currentX)} y1={T} y2={T + plotH} stroke="var(--color-fg)" strokeDasharray="4 4" opacity="0.7" />
      <text x={x(currentX) + 6} y={T + 14} fill="var(--color-fg)" fontSize="11">NOW {fmtPct(currentX, 2)}</text>
      {handoff ? (
        <>
          <line x1={x(handoff.at)} x2={x(handoff.at)} y1={T} y2={T + plotH} stroke="var(--color-fragile)" strokeDasharray="2 3" opacity="0.8" />
          <text x={x(handoff.at) + 6} y={H - 14} fill="var(--color-fragile)" fontSize="11">
            {handoff.from}Y → {handoff.to}Y
          </text>
        </>
      ) : null}
      {curves.map((c, idx) => (
        <polyline
          key={c.scale}
          points={c.xs.map((v, i) => x(v) + "," + y(c.ys[i])).join(" ")}
          fill="none"
          stroke={palette[idx] ?? "var(--color-fg)"}
          strokeWidth={idx === 0 ? 3 : 2}
          strokeLinejoin="round"
          strokeLinecap="round"
        />
      ))}
      {[0, 0.25, 0.5, 0.75, 1].map((v) => (
        <text key={v} x={x(v)} y={H - 20} textAnchor="middle" fill="var(--color-subtle)" fontSize="11">{Math.round(v * 100)}%</text>
      ))}
      <text x={L} y={H - 2} fill="var(--color-subtle)" fontSize="11">front-load / cumulative deployment</text>
      <text x={L} y={T - 7} fill="var(--color-subtle)" fontSize="11">historical q05 terminal wealth</text>
    </svg>
  );
}

function CapitalChart({ points, suggestedFraction }: { points: Array<{ month: number; fraction: number }>; suggestedFraction: number }) {
  const W = 1000, H = 330, L = 54, R = 24, T = 20, B = 42;
  const plotW = W - L - R, plotH = H - T - B;
  const x = (m: number) => L + (m / 120) * plotW;
  const y = (v: number) => T + (1 - v) * plotH;
  return (
    <svg viewBox={"0 0 " + W + " " + H} className="min-w-[760px] w-full" role="img" aria-label="capital deployment versus deadline rail">
      <rect x={L} y={T} width={plotW} height={plotH} fill="var(--color-elevated)" opacity="0.45" rx="8" />
      {[0, 0.25, 0.5, 0.75, 1].map((v) => (
        <g key={v}>
          <line x1={L} x2={W - R} y1={y(v)} y2={y(v)} stroke="var(--color-line)" />
          <text x={L - 8} y={y(v) + 4} textAnchor="end" fill="var(--color-subtle)" fontSize="11">{fmtPct(v, 0)}</text>
        </g>
      ))}
      <polyline
        points={Array.from({ length: 121 }, (_, m) => x(m) + "," + y(Math.min(1, (m + 1) / 120))).join(" ")}
        fill="none"
        stroke="var(--color-fragile)"
        strokeWidth="2"
        strokeDasharray="5 5"
      />
      <circle cx={x(0)} cy={y(suggestedFraction)} r="6" fill="var(--color-accent)" />
      <text x={x(0) + 8} y={y(suggestedFraction) - 8} fill="var(--color-accent)" fontSize="11">MODEL NOW</text>
      {points.length > 0 ? (
        <>
          <polyline points={points.map((p) => x(p.month) + "," + y(p.fraction)).join(" ")} fill="none" stroke="var(--color-fg)" strokeWidth="3" strokeLinejoin="round" strokeLinecap="round" />
          {points.map((p) => (
            <circle key={String(p.month) + "-" + String(p.fraction)} cx={x(p.month)} cy={y(p.fraction)} r="5" fill="var(--color-fg)" />
          ))}
        </>
      ) : null}
      {[0, 24, 48, 72, 96, 120].map((m) => (
        <text key={m} x={x(m)} y={H - 18} textAnchor="middle" fill="var(--color-subtle)" fontSize="11">{m}m</text>
      ))}
      <text x={L} y={H - 2} fill="var(--color-subtle)" fontSize="11">lower rail = hard deadline minimum</text>
    </svg>
  );
}

function LedgerTable({ entries }: { entries: LedgerEntry[] }) {
  if (!entries.length) {
    return <p className="mt-4 rounded-md border border-dashed border-line p-4 text-sm text-muted">尚未記錄實際投入點。圖表先顯示模型 NOW 點。</p>;
  }
  return (
    <div className="mt-4 overflow-x-auto">
      <table className="w-full min-w-[760px] text-left text-sm">
        <thead className="text-xs text-subtle">
          <tr>
            <th className="py-2">month</th>
            <th className="py-2">投入</th>
            <th className="py-2">累積</th>
            <th className="py-2">clock</th>
            <th className="py-2">delta</th>
            <th className="py-2">check</th>
          </tr>
        </thead>
        <tbody>
          {[...entries].reverse().map((e) => (
            <tr key={e.id} className="border-t border-line">
              <td className="py-2 font-mono">{e.month}</td>
              <td className="py-2 font-mono tabular-nums">{fmtUsd(e.amount, 2)}</td>
              <td className="py-2 font-mono tabular-nums">{fmtPct(e.cumulativeFraction, 2)}</td>
              <td className="py-2 font-mono tabular-nums">{fmtPct(e.clockTarget, 2)}</td>
              <td className="py-2 font-mono tabular-nums">{fmtPct(e.delta, 2)}</td>
              <td className="py-2"><Badge tone={e.status === "BELOW_CLOCK" ? "lock" : e.status === "AHEAD" ? "fragile" : "pass"}>{e.status}</Badge></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function clockTarget(month: number) {
  return Math.min(1, (month + 1) / 120);
}

function buildCapitalPath(entries: LedgerEntry[], capital: number) {
  return [...entries].sort((a, b) => a.month - b.month).map((e) => ({
    month: e.month,
    fraction: e.cumulativeAmount / Math.max(capital, 1),
  }));
}

function leaderHandoff(leaders: number[]) {
  for (let i = 1; i < leaders.length; i++) {
    if (leaders[i] !== leaders[i - 1] && leaders[i] != null && leaders[i - 1] != null) {
      return { from: leaders[i - 1], to: leaders[i], at: (i + 1) * 0.05 };
    }
  }
  return null;
}
