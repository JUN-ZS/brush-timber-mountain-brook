import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { Panel, Shell } from "@/components/shell";
import { Badge } from "@/components/ui/badge";
import { DEFAULT_POLICY, historicalBenchmark, pareto, runBacktest, searchPolicies, targetGate, type StrategyId } from "@/lib/pulse/backtest";
import { fmtPct } from "@/lib/utils";

export const Route = createFileRoute("/backtest")({ component: Page });

const strategies: StrategyId[] = ["QQQ", "QQQ_VXX", "COVERED_PROXY", "PROTECTED_PROXY", "CONVEX_PROXY"];

function Page() {
  const [strategy, setStrategy] = useState<StrategyId>("QQQ_VXX");
  const [baseRisk, setBaseRisk] = useState(DEFAULT_POLICY.baseRisk);
  const [unstableRisk, setUnstableRisk] = useState(DEFAULT_POLICY.unstableRisk);
  const [tailRisk, setTailRisk] = useState(DEFAULT_POLICY.tailRisk);
  const [recoveryRisk, setRecoveryRisk] = useState(DEFAULT_POLICY.recoveryRisk);
  const [ddBrake, setDdBrake] = useState(DEFAULT_POLICY.ddBrake);
  const policy = { baseRisk, unstableRisk, tailRisk, recoveryRisk, vxxHedge: 0.10, ddBrake };
  const result = useMemo(() => runBacktest(strategy, policy), [strategy, baseRisk, unstableRisk, tailRisk, recoveryRisk, ddBrake]);
  const grid = useMemo(() => searchPolicies(strategy), [strategy]);
  const frontier = useMemo(() => pareto(grid).slice(0, 18), [grid]);
  const bench = historicalBenchmark();

  return <Shell>
    <div className="grid gap-4">
      <Panel kicker="BACKTEST V2 · STATE CONTROL" title="不是找一組神參數，而是讓風險隨狀態改變">
        <p className="max-w-4xl text-sm leading-relaxed text-muted">12.52% CAGR / −23.51% MaxDD 只作 historical benchmark。這個 App 把「12%+ / MaxDD &lt; 5%」當成可被擊敗的研究假設，而不是答案。所有 regime 判斷只使用前一日資料；最後 20% 固定為 OOS。</p>
        <div className="mt-4 grid gap-3 md:grid-cols-5">
          <Metric k="Historical CAGR" v={fmtPct(bench.cagr, 2)} />
          <Metric k="Historical MaxDD" v={fmtPct(bench.maxDd, 2)} />
          <Metric k="Current CAGR" v={fmtPct(result.metrics.cagr, 2)} />
          <Metric k="Current MaxDD" v={fmtPct(result.metrics.maxDd, 2)} />
          <Metric k="Target Gate" v={targetGate(result) ? "PASS" : "FAIL"} />
        </div>
      </Panel>

      <Panel kicker="POLICY" title="Risk Budget 是控制變數，不是事後統計">
        <div className="grid gap-4 md:grid-cols-3">
          <Slider label="CALM risk" value={baseRisk} set={setBaseRisk} max={1} />
          <Slider label="UNSTABLE risk" value={unstableRisk} set={setUnstableRisk} max={1} />
          <Slider label="TAIL risk" value={tailRisk} set={setTailRisk} max={1} />
          <Slider label="RECOVERY risk" value={recoveryRisk} set={setRecoveryRisk} max={1} />
          <Slider label="DD brake" value={ddBrake} set={setDdBrake} max={0.08} />
        </div>
        <div className="mt-4 flex flex-wrap gap-2"><Badge tone="pass">CALM {fmtPct(baseRisk, 0)}</Badge><Badge tone="fragile">UNSTABLE {fmtPct(unstableRisk, 0)}</Badge><Badge tone="lock">TAIL {fmtPct(tailRisk, 0)}</Badge><Badge tone="mute">RECOVERY {fmtPct(recoveryRisk, 0)}</Badge></div>
      </Panel>

      <Panel kicker="STRATEGY" title="Candidate structures compete">
        <div className="flex flex-wrap gap-2">{strategies.map((s) => <button key={s} onClick={() => setStrategy(s)} className={`rounded-md border px-3 py-2 text-xs font-mono ${strategy === s ? "border-accent bg-elevated text-fg" : "border-line text-muted"}`}>{s}</button>)}</div>
        <div className="mt-4 overflow-x-auto"><table className="w-full min-w-[850px] text-left text-sm"><thead className="text-xs text-subtle"><tr>{["split","CAGR","MaxDD","Sharpe","Sortino","Vol","Calmar"].map(x => <th key={x} className="px-3 py-2">{x}</th>)}</tr></thead><tbody>{([["FULL",result.metrics],["TRAIN",result.split.train],["VALIDATION",result.split.validation],["OOS",result.split.oos]] as const).map(([n,m]) => <tr key={n} className="border-t border-line"><td className="px-3 py-2 font-mono">{n}</td><td className="px-3 py-2 font-mono">{fmtPct(m.cagr,2)}</td><td className="px-3 py-2 font-mono">{fmtPct(m.maxDd,2)}</td><td className="px-3 py-2 font-mono">{m.sharpe.toFixed(2)}</td><td className="px-3 py-2 font-mono">{m.sortino.toFixed(2)}</td><td className="px-3 py-2 font-mono">{fmtPct(m.volatility,2)}</td><td className="px-3 py-2 font-mono">{m.calmar.toFixed(2)}</td></tr>)}</tbody></table></div>
      </Panel>

      <div className="grid gap-4 md:grid-cols-2">
        <Panel kicker="PARETO FRONTIER" title="CAGR ↔ MaxDD">
          <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="text-xs text-subtle"><tr><th className="py-2">unstable</th><th className="py-2">tail</th><th className="py-2">brake</th><th className="py-2">CAGR</th><th className="py-2">MaxDD</th><th className="py-2">OOS CAGR</th><th className="py-2">OOS DD</th></tr></thead><tbody>{frontier.map((r,i)=><tr key={i} className="border-t border-line"><td className="py-2 font-mono">{fmtPct(r.policy.unstableRisk,0)}</td><td className="py-2 font-mono">{fmtPct(r.policy.tailRisk,0)}</td><td className="py-2 font-mono">{fmtPct(r.policy.ddBrake,1)}</td><td className="py-2 font-mono">{fmtPct(r.metrics.cagr,2)}</td><td className="py-2 font-mono">{fmtPct(r.metrics.maxDd,2)}</td><td className="py-2 font-mono">{fmtPct(r.split.oos.cagr,2)}</td><td className="py-2 font-mono">{fmtPct(r.split.oos.maxDd,2)}</td></tr>)}</tbody></table></div>
        </Panel>
        <Panel kicker="REGIME MAP" title="風險預算如何移動">
          <div className="space-y-3 text-sm"><Regime n="CALM" r={baseRisk} d="正常市場：保留主要 drift / carry" /><Regime n="UNSTABLE" r={unstableRisk} d="波動/動能惡化：先縮 risk，不預測方向" /><Regime n="TAIL" r={tailRisk} d="尾部條件：只留下很小 risk budget" /><Regime n="RECOVERY" r={recoveryRisk} d="反彈初期：逐步恢復，不一次滿倉" /><Regime n="DD BRAKE" r={Math.max(0,1 - ddBrake * 10)} d="自身 equity curve 惡化時再二次降槓桿" /></div>
        </Panel>
      </div>

      <Panel kicker="AUDIT" title="這個版本刻意不讓 12% / 5% 變成作弊答案">
        <ul className="space-y-2 text-sm text-muted"><li>• benchmark 與 target 分開：12.52% / −23.51% 是歷史參考；12%+ / −5% 是 gate。</li><li>• state 使用 t−1 資料決定 t 日 risk，避免用當日結果倒推倉位。</li><li>• policy search 只在有限、預先定義的 grid 上掃，不搜尋數千個事後最佳參數。</li><li>• FULL / TRAIN / VALIDATION / OOS 同時顯示；OOS 不參與 policy 排序。</li><li>• options chain 仍然不是實盤 option fill：目前 option structures 是 proxy，不能宣稱真實期權交易結果。</li></ul>
      </Panel>
    </div>
  </Shell>;
}

function Metric({ k, v }: { k: string; v: string }) { return <div className="rounded-md border border-line bg-elevated p-3"><div className="text-xs text-subtle">{k}</div><div className="mt-1 font-mono text-xl tabular-nums">{v}</div></div>; }
function Slider({ label, value, set, max }: { label: string; value: number; set: (n:number)=>void; max:number }) { return <label className="grid gap-2 text-sm"><span className="font-mono text-xs text-subtle">{label} · {fmtPct(value,1)}</span><input type="range" min={0} max={max} step={0.01} value={value} onChange={e=>set(Number(e.target.value))} className="h-10 accent-accent" /></label>; }
function Regime({ n, r, d }: { n:string; r:number; d:string }) { return <div className="rounded-md border border-line p-3"><div className="flex items-center justify-between"><span className="font-mono text-xs">{n}</span><span className="font-mono">{fmtPct(r,0)}</span></div><p className="mt-1 text-xs text-muted">{d}</p></div>; }
