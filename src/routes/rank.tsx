import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useMemo } from "react";
import { Panel, Shell } from "@/components/shell";
import { Badge } from "@/components/ui/badge";
import { compete } from "@/lib/pulse/structures";
import { RANK_MODES, MISSING_UNIVERSE, type RankMode, type SymbolId } from "@/lib/pulse/universe";
import { useRadar } from "@/lib/pulse/store";
import { fmtPct } from "@/lib/utils";
import type { RelCard } from "@/lib/pulse/relvol";

export const Route = createFileRoute("/rank")({ component: Page });

function Page() {
  const cards = useRadar((s) => s.cards);
  const cursor = useRadar((s) => s.cursor);
  const setSymbol = useRadar((s) => s.setSymbol);
  const rankMode = useRadar((s) => s.rankMode);
  const setRankMode = useRadar((s) => s.setRankMode);
  const navigate = useNavigate();

  const scored = useMemo(() => {
    const need = rankMode === "evrisk" || rankMode === "tail" || rankMode === "deploy" || rankMode === "edge";
    return cards.map((c) => {
      const dep = need ? compete(c, cursor)[0] : null;
      return { c, dep };
    });
  }, [cards, cursor, rankMode]);

  const ranked = [...scored].sort((a, b) => scoreOf(b, rankMode) - scoreOf(a, rankMode));

  return (
    <Shell>
      <div className="grid gap-4">
        <Panel kicker="ALL OBSERVED NAMES" title="三個維度都保留，排序只是切換鏡頭">
          <p className="text-sm text-muted">
            日線來自 Yahoo 調整收盤。Mature 歷史長不會自動加分。樣本權重有時間衰減。未納入宇宙的 {MISSING_UNIVERSE.length} 檔仍標缺失。
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            {RANK_MODES.map((m) => (
              <button
                key={m.id}
                type="button"
                onClick={() => setRankMode(m.id)}
                className={`min-h-11 rounded-sm border px-3 text-sm ${
                  rankMode === m.id ? "border-accent bg-elevated text-fg" : "border-line text-muted"
                }`}
              >
                {m.label}
              </button>
            ))}
          </div>
        </Panel>
        <div className="overflow-x-auto rounded-xl border border-line">
          <table className="w-full min-w-[920px] text-left text-sm">
            <thead className="bg-elevated text-xs text-subtle">
              <tr>
                <th className="px-3 py-2 font-medium">sym</th>
                <th className="px-3 py-2 font-medium">DAY</th>
                <th className="px-3 py-2 font-medium">WEEK</th>
                <th className="px-3 py-2 font-medium">MONTH</th>
                <th className="px-3 py-2 font-medium">dur</th>
                <th className="px-3 py-2 font-medium">cont</th>
                <th className="px-3 py-2 font-medium">rev</th>
                <th className="px-3 py-2 font-medium">edge</th>
                <th className="px-3 py-2 font-medium">best</th>
                <th className="px-3 py-2 font-medium">cohort</th>
              </tr>
            </thead>
            <tbody>
              {ranked.map(({ c, dep }) => (
                <tr key={c.symbol} className="border-t border-line">
                  <td className="px-3 py-3">
                    <button
                      type="button"
                      className="min-h-11 text-fg"
                      onClick={() => {
                        setSymbol(c.symbol as SymbolId);
                        void navigate({ to: "/" });
                      }}
                    >
                      {c.symbol}
                    </button>
                  </td>
                  <td className="px-3 py-3 font-mono tabular-nums">{fmtPct(c.day.percentile, 0)}</td>
                  <td className="px-3 py-3 font-mono tabular-nums">{fmtPct(c.week.percentile, 0)}</td>
                  <td className="px-3 py-3 font-mono tabular-nums">{fmtPct(c.month.percentile, 0)}</td>
                  <td className="px-3 py-3 font-mono tabular-nums">{c.week.durationAboveMean}</td>
                  <td className="px-3 py-3 font-mono tabular-nums">{fmtPct(c.continuation, 0)}</td>
                  <td className="px-3 py-3 font-mono tabular-nums">{fmtPct(c.reversion, 0)}</td>
                  <td className="px-3 py-3 font-mono tabular-nums">{fmtPct(c.volEdge, 1)}</td>
                  <td className="px-3 py-3 font-mono text-xs">
                    {dep ? `${dep.label} ${dep.score.toFixed(0)}` : c.alert}
                  </td>
                  <td className="px-3 py-3">
                    <Badge tone={c.cohort === "HOT" ? "fragile" : "mute"}>{c.cohort}</Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </Shell>
  );
}

function scoreOf(row: { c: RelCard; dep: ReturnType<typeof compete>[number] | null }, mode: RankMode) {
  const { c, dep } = row;
  if (mode === "expansion") return (c.week.percentile ?? 0) * 0.5 + (c.day.percentile ?? 0) * 0.25 + (c.month.percentile ?? 0) * 0.25;
  if (mode === "prebreak") {
    const p = c.week.percentile ?? 0;
    return p >= 0.7 && p < 0.9 && c.volMomentum === "RISING" ? p + 0.2 : p * 0.3;
  }
  if (mode === "persist") return c.persistence.p1 ?? -1;
  if (mode === "edge") return c.volEdge ?? -1;
  if (mode === "evrisk") return dep?.valueRisk ?? -99;
  if (mode === "tail") return dep ? -Math.abs(dep.breach.es95) : -99;
  return dep?.score ?? -1;
}
