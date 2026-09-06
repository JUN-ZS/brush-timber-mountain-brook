import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { Panel, Shell } from "@/components/shell";
import { Badge } from "@/components/ui/badge";
import {
  DEFAULT_POLICY,
  PROXY_STRATEGIES,
  STRATEGIES,
  coverage,
  freezeChampion,
  historicalBenchmark,
  pareto,
  runBacktest,
  sampleWindow,
  searchPolicies,
  targetGate,
  type StrategyId,
} from "@/lib/pulse/backtest";
import { fmtPct } from "@/lib/utils";

export const Route = createFileRoute("/backtest")({ component: Page });

function Page() {
  const [strategy, setStrategy] = useState<StrategyId>("QQQ_VXX");
  const [baseRisk, setBaseRisk] = useState(DEFAULT_POLICY.baseRisk);
  const [unstableRisk, setUnstableRisk] = useState(DEFAULT_POLICY.unstableRisk);
  const [tailRisk, setTailRisk] = useState(DEFAULT_POLICY.tailRisk);
  const [recoveryRisk, setRecoveryRisk] = useState(DEFAULT_POLICY.recoveryRisk);
  const [vxxHedge, setVxxHedge] = useState(DEFAULT_POLICY.vxxHedge);
  const [ddBrake, setDdBrake] = useState(DEFAULT_POLICY.ddBrake);
  const policy = { baseRisk, unstableRisk, tailRisk, recoveryRisk, vxxHedge, ddBrake };
  const w = sampleWindow();
  const cov = coverage();
  const result = useMemo(
    () => runBacktest(strategy, policy),
    [strategy, baseRisk, unstableRisk, tailRisk, recoveryRisk, vxxHedge, ddBrake],
  );
  const grid = useMemo(() => searchPolicies(strategy), [strategy]);
  const frozen = useMemo(() => freezeChampion(grid), [grid]);
  const frontier = useMemo(() => pareto(grid).slice(0, 12), [grid]);
  const bench = historicalBenchmark();
  const oosGate = targetGate(frozen.split.oos);
  const proxy = PROXY_STRATEGIES.includes(strategy);

  return (
    <Shell>
      <div className="grid gap-4">
        <Panel kicker="BACKTEST V2.1 · OOS FROZEN" title="Train → Validation → Frozen → OOS 一次">
          <p className="max-w-4xl text-sm leading-relaxed text-muted">
            12.52% / −23.51% 只是 historical benchmark，不是本引擎結果。Policy 只在 TRAIN+VALIDATION
            上競爭；OOS 不進 ranking。QQQ_VXX = rQQQ − vxxHedge × rVXX，不再寫死 0.10。
          </p>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 md:grid-cols-5">
            <Metric k="Benchmark CAGR" v={fmtPct(bench.cagr, 2)} />
            <Metric k="Benchmark MaxDD" v={fmtPct(bench.maxDd, 2)} />
            <Metric k="Frozen OOS CAGR" v={fmtPct(frozen.split.oos.cagr, 2)} />
            <Metric k="Frozen OOS MaxDD" v={fmtPct(frozen.split.oos.maxDd, 2)} />
            <Metric k="OOS Gate 12%/−5%" v={oosGate.pass ? "PASS" : "FAIL"} />
          </div>
          <p className="mt-3 font-mono text-xs text-subtle">
            {w.trainDate} → train {w.trainEndDate} → val {w.valEndDate} → OOS {w.oosStartDate} → {w.endDate} · {w.nBars}{" "}
            bars
          </p>
          <p className="mt-1 font-mono text-xs text-subtle">
            VXX {cov.vxxStart} → {cov.vxxEnd} · {cov.vxxBars} bars · missing VXX = 0 return · window not shrunk
          </p>
        </Panel>

        <Panel kicker="POLICY" title="Risk budget 由狀態決定，vxxHedge 是真實參數">
          <div className="grid gap-4 md:grid-cols-3">
            <Slider label="CALM risk" value={baseRisk} set={setBaseRisk} max={1} />
            <Slider label="UNSTABLE risk" value={unstableRisk} set={setUnstableRisk} max={1} />
            <Slider label="TAIL risk" value={tailRisk} set={setTailRisk} max={1} />
            <Slider label="RECOVERY risk" value={recoveryRisk} set={setRecoveryRisk} max={1} />
            <Slider label="VXX hedge" value={vxxHedge} set={setVxxHedge} max={0.3} />
            <Slider label="DD brake" value={ddBrake} set={setDdBrake} max={0.08} />
          </div>
        </Panel>

        <Panel kicker="STRATEGY" title="候選結構競爭">
          <div className="flex flex-wrap gap-2">
            {STRATEGIES.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => setStrategy(s)}
                className={`min-h-11 rounded-md border px-3 py-2 text-xs font-mono ${
                  strategy === s ? "border-accent bg-elevated text-fg" : "border-line text-muted"
                }`}
              >
                {s}
                {PROXY_STRATEGIES.includes(s) ? " · PROXY" : ""}
              </button>
            ))}
          </div>
          {proxy ? (
            <p className="mt-3 text-xs text-accent">HYPOTHETICAL OPTION PROXY — 不是歷史期權成交回測。</p>
          ) : null}
          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[920px] text-left text-sm">
              <thead className="text-xs text-subtle">
                <tr>
                  {["split", "CAGR", "MaxDD", "Sharpe", "Sortino", "ES", "Vol"].map((x) => (
                    <th key={x} className="px-3 py-2">
                      {x}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(
                  [
                    ["FULL", result.metrics],
                    ["TRAIN", result.split.train],
                    ["VALIDATION", result.split.validation],
                    ["OOS", result.split.oos],
                  ] as const
                ).map(([n, m]) => (
                  <tr key={n} className="border-t border-line">
                    <td className="px-3 py-2 font-mono">{n}</td>
                    <td className="px-3 py-2 font-mono">{fmtPct(m.cagr, 2)}</td>
                    <td className="px-3 py-2 font-mono">{fmtPct(m.maxDd, 2)}</td>
                    <td className="px-3 py-2 font-mono">{m.sharpe.toFixed(2)}</td>
                    <td className="px-3 py-2 font-mono">{m.sortino.toFixed(2)}</td>
                    <td className="px-3 py-2 font-mono">{fmtPct(m.es, 2)}</td>
                    <td className="px-3 py-2 font-mono">{fmtPct(m.volatility, 2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

        <div className="grid gap-4 md:grid-cols-2">
          <Panel kicker="VALIDATION PARETO" title="只看 VALIDATION，OOS 不排序">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-xs text-subtle">
                  <tr>
                    <th className="py-2">hedge</th>
                    <th className="py-2">unst</th>
                    <th className="py-2">tail</th>
                    <th className="py-2">Val CAGR</th>
                    <th className="py-2">Val DD</th>
                    <th className="py-2">score</th>
                  </tr>
                </thead>
                <tbody>
                  {frontier.map((r, i) => (
                    <tr key={i} className="border-t border-line">
                      <td className="py-2 font-mono">{fmtPct(r.policy.vxxHedge, 0)}</td>
                      <td className="py-2 font-mono">{fmtPct(r.policy.unstableRisk, 0)}</td>
                      <td className="py-2 font-mono">{fmtPct(r.policy.tailRisk, 0)}</td>
                      <td className="py-2 font-mono">{fmtPct(r.split.validation.cagr, 2)}</td>
                      <td className="py-2 font-mono">{fmtPct(r.split.validation.maxDd, 2)}</td>
                      <td className="py-2 font-mono">{r.score.toFixed(1)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Panel>
          <Panel kicker="FROZEN CHAMPION" title="VALIDATION 勝出後才看一次 OOS">
            <div className="space-y-2 font-mono text-sm">
              <div>
                {frozen.strategy}
                {frozen.proxy ? " · HYPOTHETICAL OPTION PROXY" : ""}
              </div>
              <div>
                vxxHedge {fmtPct(frozen.policy.vxxHedge, 0)} · tail {fmtPct(frozen.policy.tailRisk, 0)}
              </div>
              <div>
                TRAIN {fmtPct(frozen.split.train.cagr, 2)} / {fmtPct(frozen.split.train.maxDd, 2)}
              </div>
              <div>
                VAL {fmtPct(frozen.split.validation.cagr, 2)} / {fmtPct(frozen.split.validation.maxDd, 2)}
              </div>
              <div>
                OOS {fmtPct(frozen.split.oos.cagr, 2)} / {fmtPct(frozen.split.oos.maxDd, 2)}
              </div>
              <Badge tone={oosGate.pass ? "pass" : "lock"}>{oosGate.pass ? "OOS GATE PASS" : "OOS GATE FAIL"}</Badge>
            </div>
          </Panel>
        </div>

        <Panel kicker="AUDIT" title="V2.1 刻意不讓 12% / −5% 變成作弊答案">
          <ul className="space-y-2 text-sm text-muted">
            <li>• OOS 不參與 policy generation / ranking / 參數優化。</li>
            <li>• QQQ_VXX 使用 policy.vxxHedge，grid 含 0 / 8% / 12% / 18%。</li>
            <li>• COVERED / PROTECTED / CONVEX 標成 HYPOTHETICAL OPTION PROXY。</li>
            <li>• Target 12% CAGR 且 MaxDD ≥ −5% 只評估 Frozen OOS 一次。</li>
            <li>• oosLeakage = false：selection window 止於 validation 末日。</li>
            <li>• VXX 2018 之前缺值當 0 報酬，樣本沒有偷偷切短。</li>
          </ul>
        </Panel>
      </div>
    </Shell>
  );
}

function Metric({ k, v }: { k: string; v: string }) {
  return (
    <div className="rounded-md border border-line bg-elevated p-3">
      <div className="text-xs text-subtle">{k}</div>
      <div className="mt-1 font-mono text-xl tabular-nums">{v}</div>
    </div>
  );
}

function Slider({
  label,
  value,
  set,
  max,
}: {
  label: string;
  value: number;
  set: (n: number) => void;
  max: number;
}) {
  return (
    <label className="grid gap-2 text-sm">
      <span className="font-mono text-xs text-subtle">
        {label} · {fmtPct(value, 1)}
      </span>
      <input
        type="range"
        min={0}
        max={max}
        step={0.01}
        value={value}
        onChange={(e) => set(Number(e.target.value))}
        className="h-10 accent-accent"
      />
    </label>
  );
}
