import { Badge } from "@/components/ui/badge";
import { Panel } from "@/components/shell";
import { fmtPct, fmtUsd } from "@/lib/utils";
import { FRONTLOAD_GRID, frontLoadedTarget, deploymentGap } from "@/lib/floor/deployment";
import type { LiveHistoryMatch, LivePriceLadder, PriceHorizon } from "@/lib/floor/yahoo-live";
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
  priceLadder: LivePriceLadder | null;
  source: "YAHOO_FINANCE_CHART";
  voidedAt?: string | null;
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
function horizonLabel(horizon: PriceHorizon) {
  return horizon === 1 ? "1D" : horizon === 5 ? "5D" : "21D";
}

function mediumTouchPrice(ladder: LivePriceLadder | null, side: "ADD" | "REDUCE") {
  const rows = side === "ADD" ? ladder?.add ?? [] : ladder?.reduce ?? [];
  return rows.find((row) => row.horizon === 5 && Math.abs(row.touchProbability - 0.5) < 1e-9)?.price ?? null;
}

function PriceLadderSide({
  title,
  side,
  levels,
  quality,
}: {
  title: string;
  side: "ADD" | "REDUCE";
  levels: LivePriceLadder["add"];
  quality: string;
}) {
  const grouped = [1, 5, 21] as const;
  return (
    <div className="rounded-md border border-line bg-elevated p-4 overflow-x-auto">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="font-mono text-xs tracking-[0.14em] text-subtle">{title}</p>
          <p className="mt-1 text-sm text-muted">{side === "ADD" ? "價格向下到位 → 候選限價加倉" : "價格向上到位 → 候選限價減倉"}</p>
        </div>
        <Badge tone={quality === "THIN" ? "fragile" : "mute"}>{quality}</Badge>
      </div>
      <table className="mt-3 w-full min-w-[640px] border-collapse text-xs">
        <thead>
          <tr className="border-b border-line text-left font-mono text-[11px] text-subtle">
            <th className="py-2 pr-4">HORIZON</th>
            <th className="py-2 pr-4">TOUCH≈</th>
            <th className="py-2 pr-4">LIMIT PRICE</th>
            <th className="py-2 pr-4">DISTANCE</th>
            <th className="py-2 pr-4">SAMPLE</th>
          </tr>
        </thead>
        <tbody>
          {grouped.flatMap((horizon) =>
            levels
              .filter((row) => row.horizon === horizon)
              .map((row) => (
                <tr key={side + "-" + horizon + "-" + row.touchProbability} className="border-b border-line/50">
                  <td className="py-2 pr-4 font-mono">{horizonLabel(horizon)}</td>
                  <td className="py-2 pr-4 font-mono tabular-nums">{fmtPct(row.touchProbability, 0)}</td>
                  <td className="py-2 pr-4 font-mono text-base font-semibold tabular-nums">
                    {row.price == null ? "UNAVAILABLE" : fmtUsd(row.price, 2)}
                  </td>
                  <td className="py-2 pr-4 font-mono tabular-nums">
                    {row.distancePct == null ? "—" : fmtPct(row.distancePct, 2)}
                  </td>
                  <td className="py-2 pr-4 font-mono">{row.samples}</td>
                </tr>
              )),
          )}
        </tbody>
      </table>
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
  showFrontloadControl = true,
  startingDeployed,
  tape,
  onRecord,
  onExport,
  onToggleVoid,
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
  showFrontloadControl?: boolean;
  startingDeployed: number;
  tape: DailyDeploymentEntry[];
  onRecord: () => void;
  onExport: () => void;
  onToggleVoid: (entryId: string) => void;
}) {
  const qqq = liveContext.find((x) => x.symbol === "QQQ");
  const qqqPrice = qqq?.price ?? liveMatch?.currentPrice ?? null;
  const date = marketDate ?? qqq?.regularMarketTime?.slice(0, 10) ?? qqq?.bars.at(-1)?.date ?? null;
  const safeCapital = Math.max(1, capital);
  const safeNav = Math.max(0, Number(nav) || 0);
  const safeContributed = Math.max(0, Number(contributed) || 0);
  const safeStartingDeployed = Math.max(0, Math.min(safeCapital, Number(startingDeployed) || 0));
  const remainingDeployment = Math.max(0, safeCapital - safeStartingDeployed - safeContributed);
  const target = date ? frontLoadedTarget(safeCapital, frontload, cycleMonth, date) : frontLoadedTarget(safeCapital, frontload, cycleMonth);
  const gap = deploymentGap(safeNav, target, remainingDeployment);

  const sweep = FRONTLOAD_GRID.map((f) => {
    const t = date ? frontLoadedTarget(safeCapital, f, cycleMonth, date) : frontLoadedTarget(safeCapital, f, cycleMonth);
    const g = deploymentGap(safeNav, t, remainingDeployment);
    return { f, t, ...g };
  });

  return (
    <Panel kicker="DAILY DEPLOYMENT / LIVE MARKET TAPE" title="每日市況下：10Y target 同 NAV 有幾多 deployment gap？">
      <div className="grid gap-4">
        <div className="rounded-md border border-line bg-elevated p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="font-mono text-xs tracking-[0.14em] text-subtle">FRONTLOAD · DEPLOYMENT TARGET ONLY</p>
              <p className="mt-1 text-sm text-muted">F 只改 deployment target curve；唔會增加 ACTUAL CONTRIBUTED，亦唔會變成 CASH IN。輸入統一放頁首 Operator Desk。</p>
            </div>
            <StatusTone status={gap.status} />
          </div>
          {showFrontloadControl ? (
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
          ) : (
            <p className="mt-3 font-mono text-xs text-subtle">CONTROLLED AT OPERATOR DESK ↑ · current F {(frontload * 100).toFixed(0)}%</p>
          )}
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-6">
          <Metric k="QQQ NOW" v={qqqPrice == null ? "—" : fmtUsd(qqqPrice, 2)} d={(date ?? "no date") + " · " + (qqq?.marketState ?? "UNKNOWN")} />
          <Metric k="10Y TARGET" v={fmtUsd(target, 2)} d={"M" + cycleMonth + " · F " + (frontload * 100).toFixed(0) + "%"} />
          <Metric k="ACCOUNT NAV" v={fmtUsd(safeNav, 2)} d="daily marked reference" />
          <Metric k="DEPLOYMENT BUY GAP" v={fmtUsd(gap.buyAvailable, 2)} d="target shortfall · paper planning only · not CASH IN" />
          <Metric k="DEPLOYMENT SELL EXCESS" v={fmtUsd(gap.sellExcess, 2)} d="target excess · paper planning only · not CASH OUT" />
          <Metric k="SIGNED GAP" v={(gap.signedGap >= 0 ? "+" : "") + fmtUsd(gap.signedGap, 2)} d="target − NAV" />
        </div>

        {liveMatch?.priceLadder ? (
          <div className="grid gap-3">
            <div className="rounded-md border border-accent/40 bg-elevated p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="font-mono text-xs tracking-[0.14em] text-subtle">CONDITIONAL PRICE LADDER · MANUAL LIMIT MAP</p>
                  <p className="mt-1 text-sm text-muted">
                    目前 QQQ state 對照歷史相似狀態，把未來 1D / 5D / 21D 的 forward low / high 分布投影到今日價格。
                    不是單點預言；TOUCH≈ 只代表 matched states 的描述性歷史頻率。
                  </p>
                </div>
                <Badge tone="lock">NO BROKER ORDER</Badge>
              </div>
              <div className="mt-3 grid gap-3 sm:grid-cols-3">
                <Metric k="CURRENT QQQ" v={liveMatch.currentPrice == null ? "—" : fmtUsd(liveMatch.currentPrice, 2)} d="Yahoo observation" />
                <Metric k="MATCHES" v={String(liveMatch.priceLadder.samples)} d="same-state historical analogues" />
                <Metric k="LADDER QUALITY" v={liveMatch.priceLadder.quality} d="descriptive only · no confidence interval" />
              </div>
            </div>
            <div className="grid gap-3 lg:grid-cols-2">
              <PriceLadderSide title="ADD / BUY LIMITS" side="ADD" levels={liveMatch.priceLadder.add} quality={liveMatch.priceLadder.quality} />
              <PriceLadderSide title="REDUCE / SELL LIMITS" side="REDUCE" levels={liveMatch.priceLadder.reduce} quality={liveMatch.priceLadder.quality} />
            </div>
            <p className="text-xs leading-relaxed text-subtle">
              LIMIT PRICE 是用日線收市資料的歷史 matched-state forward low/high 分布換算，唔等於日內 bid/ask 觸價機率。
              每次 REFRESH YAHOO 都會重新計；實際掛單由你在交易平台手動落，系統不傳單。
            </p>
          </div>
        ) : null}

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
              <p className="mt-1 text-sm text-muted">同一個 QQQ NAV，逐個 F 重算今天的 target / deployment gap；只係顯示，唔選 champion，亦唔會改 funding ledger。</p>
            </div>
            <div className="flex gap-2">
              <button type="button" onClick={onRecord} className="min-h-10 rounded-md border border-accent px-3 font-mono text-xs hover:bg-elevated">RECORD TODAY</button>
              <button type="button" onClick={onExport} className="min-h-10 rounded-md border border-line px-3 font-mono text-xs text-muted hover:text-fg">EXPORT DAILY CSV</button>
            </div>
          </div>
          <table className="mt-3 w-full min-w-[760px] border-collapse text-sm">
            <thead><tr className="border-b border-line text-left font-mono text-[11px] text-subtle"><th className="py-2 pr-4">F</th><th className="py-2 pr-4">TARGET</th><th className="py-2 pr-4">BUY GAP</th><th className="py-2 pr-4">SELL EXCESS</th><th className="py-2 pr-4">GAP</th><th className="py-2 pr-4">STATUS</th></tr></thead>
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
              <p className="mt-1 text-sm text-muted">每個 market date + Frontload F 可留一個 observation。CANCEL 只撤銷該筆觀測的有效性，原記錄保留；之後可 RESTORE。</p>
            </div>
            <Badge tone="mute">{tape.length} OBSERVATIONS · {tape.filter((x) => !x.voidedAt).length} ACTIVE</Badge>
          </div>
          {tape.length ? (
            <table className="mt-3 w-full min-w-[1040px] border-collapse text-xs">
              <thead><tr className="border-b border-line text-left font-mono text-[11px] text-subtle"><th className="py-2 pr-4">DATE</th><th className="py-2 pr-4">QQQ</th><th className="py-2 pr-4">F</th><th className="py-2 pr-4">TARGET</th><th className="py-2 pr-4">NAV</th><th className="py-2 pr-4">BUY</th><th className="py-2 pr-4">SELL</th><th className="py-2 pr-4">DAY</th><th className="py-2 pr-4">WEEK</th><th className="py-2 pr-4">MONTH</th><th className="py-2 pr-4">ADD 5D</th><th className="py-2 pr-4">REDUCE 5D</th><th className="py-2 pr-4">STATE</th><th className="py-2 pr-4">ACTION</th></tr></thead>
              <tbody>{tape.slice().reverse().slice(0, 30).map((row) => <tr key={row.id} className={"border-b border-line/50 " + (row.voidedAt ? "opacity-50" : "")}><td className="py-2 pr-4 font-mono">{row.marketDate}</td><td className="py-2 pr-4 font-mono tabular-nums">{row.qqqPrice == null ? "—" : row.qqqPrice.toFixed(2)}</td><td className="py-2 pr-4 font-mono">{(row.frontload * 100).toFixed(0)}%</td><td className="py-2 pr-4 font-mono tabular-nums">{fmtUsd(row.target, 2)}</td><td className="py-2 pr-4 font-mono tabular-nums">{fmtUsd(row.nav, 2)}</td><td className="py-2 pr-4 font-mono tabular-nums">{fmtUsd(row.buyAvailable, 2)}</td><td className="py-2 pr-4 font-mono tabular-nums">{fmtUsd(row.sellExcess, 2)}</td><td className="py-2 pr-4 font-mono">{row.dayLevel}</td><td className="py-2 pr-4 font-mono">{row.weekLevel}</td><td className="py-2 pr-4 font-mono">{row.monthLevel}</td><td className="py-2 pr-4 font-mono tabular-nums">{mediumTouchPrice(row.priceLadder, "ADD") == null ? "—" : fmtUsd(mediumTouchPrice(row.priceLadder, "ADD")!, 2)}</td><td className="py-2 pr-4 font-mono tabular-nums">{mediumTouchPrice(row.priceLadder, "REDUCE") == null ? "—" : fmtUsd(mediumTouchPrice(row.priceLadder, "REDUCE")!, 2)}</td><td className="py-2 pr-4"><Badge tone={row.voidedAt ? "lock" : row.status === "SELL_EXCESS" ? "fragile" : row.status === "BUY_AVAILABLE" ? "pass" : "mute"}>{row.voidedAt ? "CANCELLED · EXCLUDED" : row.status}</Badge></td><td className="py-2 pr-4"><button type="button" onClick={() => onToggleVoid(row.id)} className={"min-h-8 rounded-md border px-2 font-mono text-[11px] " + (row.voidedAt ? "border-accent text-fg" : "border-line text-muted hover:text-fg")}>{row.voidedAt ? "RESTORE" : "CANCEL"}</button></td></tr>)}</tbody>
            </table>
          ) : <div className="mt-3 rounded-md border border-dashed border-line p-4 text-sm text-muted">尚未有 daily observation；REFRESH YAHOO 後會自動 seal 今日 snapshot。</div>}
        </div>

        <p className="text-xs leading-relaxed text-subtle">DAILY DEPLOYMENT 是研究/規劃層：它把固定 10Y budget 映射成當日 target，再以目前 NAV 算 deployment gap。呢個 gap 只係規劃額度，唔係 CASH IN / CASH OUT，亦唔會直接變成 broker command。CANCEL / RESTORE 只控制 observation 是否有效，不改 Funding / Trade ledger。</p>
      </div>
    </Panel>
  );
}
