import { createFileRoute } from "@tanstack/react-router";
import { Meter } from "@/components/meter";
import { Panel, Shell } from "@/components/shell";
import { WeekTimeline } from "@/components/timeline";
import { Badge } from "@/components/ui/badge";
import { calendarIndexOf, lastBar } from "@/lib/pulse/bars";
import { useRadar } from "@/lib/pulse/store";
import { TRADED } from "@/lib/pulse/universe";
import { fmtMul, fmtNum, fmtPct } from "@/lib/utils";
import type { ScaleState } from "@/lib/pulse/relvol";

export const Route = createFileRoute("/")({ component: Page });

function Page() {
  const card = useRadar((s) => s.card);
  const cards = useRadar((s) => s.cards);
  const setSymbol = useRadar((s) => s.setSymbol);
  const setCursor = useRadar((s) => s.setCursor);
  const cursor = useRadar((s) => s.cursor);
  const deploys = useRadar((s) => s.deploys);
  const best = deploys[0];

  if (!card) {
    return (
      <Shell>
        <p className="text-muted">資料不足。</p>
      </Shell>
    );
  }

  const arrow = card.volMomentum === "RISING" ? "↑" : card.volMomentum === "FALLING" ? "↓" : "→";

  return (
    <Shell>
      <div className="grid gap-4">
        <div className="flex gap-2 overflow-x-auto pb-1">
          {TRADED.map((sym) => {
            const c = cards.find((x) => x.symbol === sym);
            return (
              <button
                key={sym}
                type="button"
                onClick={() => setSymbol(sym)}
                className={`min-h-11 shrink-0 rounded-sm border px-3 py-2 text-sm ${
                  sym === card.symbol ? "border-accent bg-elevated text-fg" : "border-line text-muted"
                }`}
              >
                {sym}
                {c?.week.percentile != null ? (
                  <span className="ml-2 font-mono text-xs tabular-nums text-subtle">
                    {Math.round(c.week.percentile * 100)}
                  </span>
                ) : null}
              </button>
            );
          })}
        </div>

        <Panel kicker={`${card.symbol} · ${card.cohort} · ${card.nBars} bars · ${card.confidence}`} title={`SPOT ${fmtNum(card.spot, 2)}`}>
          <p className="text-sm text-muted">
            相對的是 {card.symbol} 自己的歷史，不是跨股平均。Price {card.priceDir} · Vol {card.volDir} · 慣性 {card.volMomentum}{" "}
            {arrow}
          </p>
          <div className="mt-4 grid gap-4 md:grid-cols-3">
            <ScaleBlock title="DAY" s={card.day} />
            <ScaleBlock title="WEEK" s={card.week} />
            <ScaleBlock title="MONTH" s={card.month} />
          </div>
        </Panel>

        <div className="grid gap-4 lg:grid-cols-2">
          <Panel kicker="CONSECUTIVE STATE" title={`WEEK 已連續 ${card.week.durationAboveMean} 週高於自身均值`}>
            <p className="font-mono text-sm text-muted">
              {">"}90%：{card.week.durationAbove90} 週 · {">"}95%：{card.week.durationAbove95} 週
            </p>
            <WeekTimeline rows={card.weekTimeline} />
            <p className="mt-2 text-sm text-muted">
              同樣的高百分位：從低處爬上來（RISING）與從極端回落（FALLING）不是同一個 State。
            </p>
          </Panel>
          <Panel kicker="PREPARATION RADAR" title={alertTitle(card.alert)}>
            <dl className="grid grid-cols-2 gap-3 text-sm">
              <Stat k="DAY" v={`${fmtPct(card.day.percentile, 0)} ${arrow}`} />
              <Stat k="WEEK" v={`${fmtPct(card.week.percentile, 0)} ${arrow}`} />
              <Stat k="MONTH" v={fmtPct(card.month.percentile, 0)} />
              <Stat k="WEEK duration" v={`${card.week.durationAboveMean} w`} />
              <Stat k="Continuation" v={fmtPct(card.continuation, 0)} />
              <Stat k="Mean reversion" v={fmtPct(card.reversion, 0)} />
            </dl>
            {card.durationCond ? (
              <p className="mt-3 text-sm text-muted">
                歷史上「已連續 {card.durationCond.duration} 週 {'>'}90%」：再升 {fmtPct(card.durationCond.pContinue, 0)} · 回歸{" "}
                {fmtPct(card.durationCond.pRevert, 0)} · 更極端 {fmtPct(card.durationCond.pExtreme, 0)}（n=
                {card.durationCond.n}）
              </p>
            ) : (
              <p className="mt-3 text-sm text-muted">目前 duration 的條件樣本不足，不硬估。</p>
            )}
            <div className="mt-3">
              <Badge tone={card.alert === "READY" ? "fragile" : card.alert === "WAIT" ? "mute" : "pass"}>
                {card.alert}
              </Badge>
            </div>
          </Panel>
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          <Panel kicker="WHAT HAPPENS AFTER" title="超越後通常怎樣">
            <dl className="grid grid-cols-2 gap-3 text-sm">
              <Stat k="Persist 1w" v={fmtPct(card.persistence.p1, 0)} />
              <Stat k="Persist 3w" v={fmtPct(card.persistence.p3, 0)} />
              <Stat k="OOS persist" v={fmtPct(card.persistence.oosP1, 0)} />
              <Stat k="Model 5D" v={fmtPct(card.modelWeek, 1)} />
              <Stat k="Implied 5D" v={fmtPct(card.impliedWeek, 1)} />
              <Stat k="VOL EDGE" v={fmtPct(card.volEdge, 1)} />
            </dl>
            <p className="mt-3 text-xs text-subtle">
              頻率來自 TRAIN 相似百分位，時間衰減。Persistence {card.persistence.score}（n={card.persistence.n}）。沒有慣性要扣分。
            </p>
            <div className="mt-2">
              <Badge tone={card.volEdge != null && card.volEdge > 0 ? "pass" : "fragile"}>
                選擇權鏈仍 MISSING · IV 用 VIX 或 RV×1.15 代理
              </Badge>
            </div>
          </Panel>
          <Panel kicker="NEXT THRESHOLD" title="距離下一檔還有多少">
            <p className="font-mono text-sm tabular-nums">
              mean {fmtPct(card.week.mean, 1)} · now {fmtPct(card.week.current, 1)} · warn {fmtPct(card.week.nextWarn, 1)} ·
              extreme {fmtPct(card.week.nextExtreme, 1)}
            </p>
            <div className="mt-3 h-2 overflow-hidden rounded-sm bg-elevated">
              <div
                className="h-full bg-accent"
                style={{
                  width: `${Math.min(100, ((card.week.current || 0) / Math.max(card.week.nextExtreme || 0.01, 0.01)) * 100)}%`,
                }}
              />
            </div>
            <p className="mt-2 text-sm text-muted">
              距 warning {fmtPct(card.week.gapToWarn, 1)} · 現在 / 自身均值 {fmtMul(card.week.ratio)}
            </p>
          </Panel>
        </div>

        <Panel kicker="BEST STRUCTURE · HYPOTHETICAL" title={best ? `${best.label} · ${best.score.toFixed(0)}/100` : "NO_TRADE"}>
          {best ? (
            <>
              <p className="text-sm text-muted">{best.legs}</p>
              <p className="mt-2 font-mono text-xs tabular-nums text-subtle">
                EV {fmtPct(best.ev, 2)} · POP {fmtPct(best.pop, 0)} · breach {fmtPct(best.breach.probability, 0)} · ES95{" "}
                {fmtPct(best.breach.es95, 2)} · 連 3 次 {fmtPct(best.breach.consecutive3, 1)} · 最長連穿 {best.breach.maxConsecutive}
              </p>
              <p className="mt-2 text-xs text-lock">不是下單。Council 預設 NO_TRADE。真實 option chain = CAPABILITY_MISSING。</p>
            </>
          ) : null}
        </Panel>

        <div className="flex flex-wrap gap-2">
          <Jump label="最新" onClick={() => setCursor(lastBar)} />
          <Jump label="2020 壓力" onClick={() => setCursor(calendarIndexOf("2020-03-16"))} />
          <Jump label="2008" onClick={() => setCursor(calendarIndexOf("2008-10-10"))} />
          <Jump label="2023 起" onClick={() => setCursor(calendarIndexOf("2023-01-03"))} />
          <span className="self-center font-mono text-xs tabular-nums text-subtle">bar {cursor}</span>
        </div>
      </div>
    </Shell>
  );
}

function alertTitle(a: string) {
  if (a === "READY") return "HIGH STATE / 結構可競爭";
  if (a === "PRE_BREAKOUT") return "尚未破 90，但正在靠近";
  if (a === "EARLY") return "EARLY PREPARATION";
  return "沒有足夠狀態，先 WAIT";
}

function ScaleBlock({ title, s }: { title: string; s: ScaleState }) {
  return (
    <div className="rounded-md border border-line bg-elevated p-3">
      <p className="font-mono text-xs text-subtle">{title}</p>
      <Meter pct={s.percentile} label={s.level} />
      <p className="mt-2 font-mono text-xs tabular-nums text-muted">
        now {fmtPct(s.current, 1)} / mean {fmtPct(s.mean, 1)} = {fmtMul(s.ratio)}
      </p>
    </div>
  );
}

function Stat({ k, v }: { k: string; v: string }) {
  return (
    <div>
      <dt className="font-mono text-xs text-subtle">{k}</dt>
      <dd className="tabular-nums text-fg">{v}</dd>
    </div>
  );
}

function Jump({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button type="button" onClick={onClick} className="min-h-11 rounded-sm border border-line px-3 text-sm text-muted hover:text-fg">
      {label}
    </button>
  );
}
