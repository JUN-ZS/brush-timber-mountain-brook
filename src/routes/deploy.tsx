import { createFileRoute } from "@tanstack/react-router";
import { Panel, Shell } from "@/components/shell";
import { Badge } from "@/components/ui/badge";
import { capacityPlan } from "@/lib/pulse/structures";
import { thresholdProbe } from "@/lib/pulse/relvol";
import { useRadar } from "@/lib/pulse/store";
import { fmtPct, fmtUsd } from "@/lib/utils";

export const Route = createFileRoute("/deploy")({ component: Page });

function Page() {
  const card = useRadar((s) => s.card);
  const deploys = useRadar((s) => s.deploys);
  const cursor = useRadar((s) => s.cursor);
  const maxConsec = useRadar((s) => s.maxConsec);
  const maxDd = useRadar((s) => s.maxDd);
  const setBudget = useRadar((s) => s.setBudget);
  const probe = card ? thresholdProbe(card.symbol, cursor) : [];
  const best = deploys.find((d) => d.id !== "NO_TRADE") ?? deploys[0];
  const plan = card && best ? capacityPlan(best, card.spot, { maxConsec, maxDd }) : null;

  return (
    <Shell>
      <div className="grid gap-4">
        <Panel kicker="STRUCTURES COMPETE" title="鐵蝶只是候選人">
          <p className="max-w-2xl text-sm text-muted">
            Short ratio = f(VolState, Continuation, Reversion)，不是寫死 5×。評估用 TRAIN 相似狀態的下一週報酬分布，權重隨時間衰減。真實
            option chain 不存在，全部 HYPOTHETICAL。NO_TRADE 合法。
          </p>
          {card ? (
            <p className="mt-2 font-mono text-xs tabular-nums text-subtle">
              {card.symbol} WEEK {fmtPct(card.week.percentile, 0)} · persist {card.persistence.score} · ratio hint{" "}
              {deploys.find((d) => d.id === "CALL_RATIO")?.shortRatio ?? "—"} · alert {card.alert}
            </p>
          ) : null}
        </Panel>

        <Panel kicker="BREACH CAPACITY" title="我可以承受多少次穿破">
          <div className="grid gap-4 md:grid-cols-2">
            <label className="grid gap-2 text-sm">
              <span className="font-mono text-xs text-subtle">Max consecutive losses · {maxConsec}</span>
              <input
                type="range"
                min={1}
                max={8}
                value={maxConsec}
                onChange={(e) => setBudget({ maxConsec: Number(e.target.value) })}
                className="h-11 accent-accent"
              />
            </label>
            <label className="grid gap-2 text-sm">
              <span className="font-mono text-xs text-subtle">Max drawdown · {fmtUsd(maxDd)}</span>
              <input
                type="range"
                min={500}
                max={20000}
                step={500}
                value={maxDd}
                onChange={(e) => setBudget({ maxDd: Number(e.target.value) })}
                className="h-11 accent-accent"
              />
            </label>
          </div>
          {plan && best ? (
            <p className="mt-3 text-sm text-muted">
              對 {best.label}：建議 {plan.lots} lot · notional {fmtUsd(plan.notional)} · ES95 {fmtUsd(plan.es95Dollar)} ·{" "}
              {plan.rejected ? plan.reason : plan.reason}
            </p>
          ) : null}
        </Panel>

        <div className="overflow-x-auto rounded-xl border border-line">
          <table className="w-full min-w-[980px] text-left text-sm">
            <thead className="bg-elevated text-xs text-subtle">
              <tr>
                <th className="px-3 py-2 font-medium">structure</th>
                <th className="px-3 py-2 font-medium">score</th>
                <th className="px-3 py-2 font-medium">EV</th>
                <th className="px-3 py-2 font-medium">POP</th>
                <th className="px-3 py-2 font-medium">breach</th>
                <th className="px-3 py-2 font-medium">ES95</th>
                <th className="px-3 py-2 font-medium">3-streak</th>
                <th className="px-3 py-2 font-medium">max run</th>
              </tr>
            </thead>
            <tbody>
              {deploys.map((d) => (
                <tr key={d.variant} className="border-t border-line">
                  <td className="px-3 py-3">
                    <div className="font-medium">{d.label}</div>
                    <div className="font-mono text-xs text-subtle">{d.legs}</div>
                  </td>
                  <td className="px-3 py-3 font-mono tabular-nums">{d.score.toFixed(0)}</td>
                  <td className="px-3 py-3 font-mono tabular-nums">{fmtPct(d.ev, 2)}</td>
                  <td className="px-3 py-3 font-mono tabular-nums">{fmtPct(d.pop, 0)}</td>
                  <td className="px-3 py-3 font-mono tabular-nums">{fmtPct(d.breach.probability, 0)}</td>
                  <td className="px-3 py-3 font-mono tabular-nums">{fmtPct(d.breach.es95, 2)}</td>
                  <td className="px-3 py-3 font-mono tabular-nums">{fmtPct(d.breach.consecutive3, 1)}</td>
                  <td className="px-3 py-3 font-mono tabular-nums">{d.breach.maxConsecutive}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <Panel kicker="THRESHOLD PROBE" title="門檻自己競爭，不把 1.25× 當成真理">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[520px] text-left text-sm">
              <thead className="text-xs text-subtle">
                <tr>
                  <th className="py-2 font-medium">ratio ≥</th>
                  <th className="py-2 font-medium">n</th>
                  <th className="py-2 font-medium">P(stays next week)</th>
                </tr>
              </thead>
              <tbody>
                {probe.map((r) => (
                  <tr key={r.thr} className="border-t border-line">
                    <td className="py-2 font-mono tabular-nums">{r.thr.toFixed(2)}×</td>
                    <td className="py-2 font-mono tabular-nums">{r.n}</td>
                    <td className="py-2 font-mono tabular-nums">{fmtPct(r.p1, 0)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
        <Badge tone="lock">Council NO_TRADE · 這頁不是券商下單</Badge>
      </div>
    </Shell>
  );
}
