import { Badge } from "@/components/ui/badge";
import { Panel } from "@/components/shell";
import { fmtPct, fmtUsd } from "@/lib/utils";
import { FRONTLOAD_GRID, frontLoadedTarget, deploymentGap } from "@/lib/floor/deployment";
import type { LiveHistoryMatch } from "@/lib/floor/yahoo-live";
import type { YahooSeries } from "@/lib/floor/yahoo-live";

export type DailyDeploymentEntry = {
  id: string;
  recordedAt: string;
  marketDate: string;
  cycleMonth: number;
  capital: number;
  frontload: number;
  nav: number;
  contributed: number;
  qqqPrice: number | null;
  marketState: string | null;
  dayRatio: number | null;
  weekRatio: number | null;
  monthRatio: number | null;
  dayLevel: string;
  weekLevel: string;
  monthLevel: string;
  target: number;
  remainingCapital: number;
  buyAvailable: number;
  sellExcess: number;
  signedGap: number;
  status: "BUY_AVAILABLE" | "ON_TARGET" | "SELL_EXCESS";
  source: "YAHOO_FINANCE_CHART";
};

function StatusTone({ status }: { status: DailyDeploymentEntry["status"] | string }) {
  return <Badge tone={status === "BUY_AVAILABLE" ? "pass" : status === "SELL_EXCESS" ? "lock" : "mute"}>{status}</Badge>;
}

function Metric({ k, v, d }: { k: string; v: string; d: string }) {
  return (
    <div className="rounded-md border border-line bg-elevated p-3">
      <p className="font-mono text-[11px] tracking-[0.12em] text-subtle">{k}</p>
      <p className="mt-1 font-mono text-xl tabular-nums">{v}</p>
      <p className="mt-1 text-xs text-muted">{d}</p>
    </div>
  );
}

export function DailyDeploymentConsole({
  capital,
  contributed,
  nav,
  cycleMonth,
  marketDate,
  liveContext,
  liveMatch,
  frontload,
  onFrontloadChange,
  tape,
  onRecord,
  onExport,
}: {
  capital: number;
  contributed: number;
  nav: number;
  cycleMonth: number;
  marketDate: string | null;
  liveContext: YahooSeries[];
  liveMatch: LiveHistoryMatch | null;
  frontload: number;
  onFrontloadChange: (value: number) => void;
  tape: DailyDeploymentEntry[];
  onRecord: () => void;
  onExport: () => void;
}) {
  const qqq = liveContext.find((x) => x.symbol === "QQQ");
  const qqqPrice = qqq?.price ?? liveMatch?.currentPrice ?? null;
  const date = marketDate ?? qqq?.regularMarketTime?.slice(0, 10) ?? qqq?.bars.at(-1)?.date ?? null;
  const safeCapital = Math.max(1, capital);
  const safeNav = Math.max(0, Number(nav) || 0);
  const safeContributed = Math.max(0, Number(contributed) || 0);
  const target = date ? frontLoadedTarget(safeCapital, frontload, cycleMonth, date) : frontLoadedTarget(safeCapital, frontload, cycleMonth);
  const gap = deploymentGap(safeNav, target, Math.max(0, safeCapital - safeContributed));

  const sweep = FRONTLOAD_GRID.map((f) => {
    const t = date ? frontLoadedTarget(safeCapital, f, cycleMonth, date) : frontLoadedTarget(safeCapital, f, cycleMonth);
    const g = deploymentGap(safeNav, t, Math.max(0, safeCapital - safeContributed));
    return { f, t, ...g };
  });

  return (
    <Panel kicker="DAILY DEPLOYMENT / LIVE MARKET TAPE" title="每日市況下：現在可部署幾多？前置比例如何改變互追？">
      <div className="grid gap-4">
        <div className="rounded-md border border-line bg-elevated p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="font-mono text-xs tracking-[0.14em] text-subtle">FRONTLOAD CONTROL · RESEARCH ONLY</p>
              <p className="mt-1 text-sm text-muted">同一個 10Y B，只改 target curve 的前置比例；唔改正式 Funding Status，唔產生 broker order。</p>
            </div>
            <StatusTone status={gap.status} />
          </div>
          <div className="mt-4 grid gap-4 md:grid-cols-[1fr_auto] md:items-end">
            <label className="grid gap-2">
              <span className="font-mono text-xs text-subtle">FRONTLOAD F · {(frontload * 100).toFixed(0)}%</span>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={frontload}
                onChange={(e) => onFrontloadChange(Number(e.target.value))}
                className="w-full accent-[var(--color-accent)]"
              />
            </label>
            <div className="flex flex-wrap gap-2">
              {FRONTLOAD_GRID.map((f) => (
                <button key={f} type="button" onClick={() => onFrontloadChange(f)} className={"rounded border px-2 py-1 font-mono text-xs " + (Math.abs(frontload - f) < 1e-9 ? "border-accent text-fg" : "border-line text-muted hover:text-fg")}>
                  {(f * 100).toFixed(0)}%
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-6">
          <Metric k="QQQ NOW" v={qqqPrice == null ? "—" : fmtUsd(qqqPrice, 2)} d={(date ?? "no date") + " · " + (qqq?.marketState ?? "UNKNOWN")} />
          <Metric k="10Y TARGET" v={fmtUsd(target, 2)} d={"M" + cycleMonth + " · F " + (frontload * 100).toFixed(0) + "%"} />
          <Metric k="ACCOUNT NAV" v={fmtUsd(safeNav, 2)} d="daily marked reference" />
          <Metric k="BUY AVAILABLE" v={fmtUsd(gap.buyAvailable, 2)} d="model shortfall · capped by remaining B" />
          <Metric k="SELL EXCESS" v={fmtUsd(gap.sellExcess, 2)} d="model excess · would become reserve" />
          <Metric k="SIGNED GAP" v={(gap.signedGap >= 0 ? "+" : "") + fmtUsd(gap.signedGap, 2)} d="target − NAV" />
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Metric k="DAY RELVOL" v={liveMatch?.day.ratio == null ? "—" : liveMatch.day.ratio.toFixed(2) + "×"} d={liveMatch?.day.level ?? "UNKNOWN"} />
          <Metric k="WEEK RELVOL" v={liveMatch?.week.ratio == null ? "—" : liveMatch.week.ratio.toFixed(2) + "×"} d={liveMatch?.week.level ?? "UNKNOWN"} />
          <Metric k="MONTH RELVOL" v={liveMatch?.month.ratio == null ? "—" : liveMatch.month.ratio.toFixed(2) + "×"} d={liveMatch?.month.level ?? "UNKNOWN"} />
          <Metric k="5D DIR" v={liveMatch?.priceDir ?? "—"} d="QQQ self-relative daily tape" />
        </div>

        <div className="rounded-md border border-line bg-elevated p-4 overflow-x-auto">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="font-mono text-xs tracking-[0.14em] text-subtle">SAME-DAY FRONTLOAD SWEEP</p>
              <p className="mt-1 text-sm text-muted">同一個 QQQ NAV，逐個 F 重算今天的 target / BUY / SELL；只係顯示，唔選 champion。</p>
            </div>
            <div className="flex gap-2">
              <button type="button" onClick={onRecord} className="min-h-10 rounded-md border border-accent px-3 font-mono text-xs hover:bg-elevated">RECORD TODAY</button>
              <button type="button" onClick={onExport} className="min-h-10 rounded-md border border-line px-3 font-mono text-xs text-muted hover:text-fg">EXPORT DAILY CSV</button>
            </div>
          </div>
          <table className="mt-3 w-full min-w-[760px] border-collapse text-sm">
            <thead><tr className="border-b border-line text-left font-mono text-[11px] text-subtle"><th className="py-2 pr-4">F</th><th className="py-2 pr-4">TARGET</th><th className="py-2 pr-4">BUY AVAILABLE</th><th className="py-2 pr-4">SELL EXCESS</th><th className="py-2 pr-4">GAP</th><th className="py-2 pr-4">STATUS</th></tr></thead>
            <tbody>
              {sweep.map((row) => <tr key={row.f} className={"border-b border-line/50 " + (Math.abs(frontload - row.f) < 1e-9 ? "bg-elevated" : "")}>
                <td className="py-2 pr-4 font-mono">{(row.f * 100).toFixed(0)}%</td>
                <td className="py-2 pr-4 font-mono tabular-nums">{fmtUsd(row.t, 2)}</td>
                <td className="py-2 pr-4 font-mono tabular-nums">{fmtUsd(row.buyAvailable, 2)}</td>
                <td className="py-2 pr-4 font-mono tabular-nums">{fmtUsd(row.sellExcess, 2)}</td>
                <td className="py-2 pr-4 font-mono tabular-nums">{(row.signedGap >= 0 ? "+" : "") + fmtUsd(row.signedGap, 2)}</td>
                <td className="py-2 pr-4"><StatusTone status={row.status} /></td>
              </tr>)}
            </tbody>
          </table>
        </div>

        <div className="rounded-md border border-line bg-elevated p-4 overflow-x-auto">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="font-mono text-xs tracking-[0.14em] text-subtle">DAILY DEPLOYMENT TAPE</p>
              <p className="mt-1 text-sm text-muted">每個 market date 可留一個 snapshot；保留 target、NAV、BUY/SELL、QQQ、DAY/WEEK/MONTH relvol。</p>
            </div>
            <Badge tone="mute">{tape.length} OBSERVATIONS</Badge>
          </div>
          {tape.length ? (
            <table className="mt-3 w-full min-w-[1040px] border-collapse text-xs">
              <thead><tr className="border-b border-line text-left font-mono text-[11px] text-subtle"><th className="py-2 pr-4">DATE</th><th className="py-2 pr-4">QQQ</th><th className="py-2 pr-4">F</th><th className="py-2 pr-4">TARGET</th><th className="py-2 pr-4">NAV</th><th className="py-2 pr-4">BUY</th><th className="py-2 pr-4">SELL</th><th className="py-2 pr-4">DAY</th><th className="py-2 pr-4">WEEK</th><th className="py-2 pr-4">MONTH</th><th className="py-2 pr-4">STATE</th></tr></thead>
              <tbody>{tape.slice().reverse().slice(0, 30).map((row) => <tr key={row.id} className="border-b border-line/50"><td className="py-2 pr-4 font-mono">{row.marketDate}</td><td className="py-2 pr-4 font-mono tabular-nums">{row.qqqPrice == null ? "—" : row.qqqPrice.toFixed(2)}</td><td className="py-2 pr-4 font-mono">{(row.frontload * 100).toFixed(0)}%</td><td className="py-2 pr-4 font-mono tabular-nums">{fmtUsd(row.target, 2)}</td><td className="py-2 pr-4 font-mono tabular-nums">{fmtUsd(row.nav, 2)}</td><td className="py-2 pr-4 font-mono tabular-nums">{fmtUsd(row.buyAvailable, 2)}</td><td className="py-2 pr-4 font-mono tabular-nums">{fmtUsd(row.sellExcess, 2)}</td><td className="py-2 pr-4 font-mono">{row.dayLevel}</td><td className="py-2 pr-4 font-mono">{row.weekLevel}</td><td className="py-2 pr-4 font-mono">{row.monthLevel}</td><td className="py-2 pr-4"><StatusTone status={row.status} /></td></tr>)}</tbody>
            </table>
          ) : <div className="mt-3 rounded-md border border-dashed border-line p-4 text-sm text-muted">尚未有 daily observation；REFRESH YAHOO 後會自動 seal 今日 snapshot。</div>}
        </div>

        <p className="text-xs leading-relaxed text-subtle">DAILY DEPLOYMENT 是研究/帳本層：它把固定 10Y budget 映射成當日 target，再以目前 NAV 算出可用部署或可 harvest 的額度。市場 relvol 只作 context；唔會偷偷改 target，亦唔會變成 BUY/SELL broker command。</p>
      </div>
    </Panel>
  );
}
