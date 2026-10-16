import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { Panel, Shell } from "@/components/shell";
import { Badge } from "@/components/ui/badge";
import { frozenV22 as frozen } from "@/lib/pulse/v22-result";
import { buyHoldQQQ, historicalBenchmark, sampleWindow } from "@/lib/pulse/backtest";
import { DEFAULT_PROTECTED, runProtected, type ProtectedSpec } from "@/lib/pulse/protected";
import { fmtPct } from "@/lib/utils";

export const Route = createFileRoute("/backtest")({ component: Page });

type Frozen = typeof frozen & {
  executed?: boolean;
  oos?: { cagr: number; maxDd: number; sharpe: number; sortino: number; es: number; positiveDays?: number; negativeDays?: number; flatDays?: number; positiveDayRatePct?: number; nDays?: number };
  validation?: { cagr: number; maxDd: number };
  train?: { cagr: number; maxDd: number };
  full?: { cagr: number; maxDd: number };
  selectedSpec?: {
    putDistance: number;
    dte: number;
    rollDays: number;
    calmPut: number;
    unstablePut: number;
    tailPut: number;
    recoveryPut: number;
    buildingPut: number;
  };
  extras?: { validation?: { premiumDrag: number; protectionEfficiency: number }; oos?: { premiumDrag: number; protectionEfficiency: number } };
  buyHoldQQQ?: { oos: { cagr: number; maxDd: number }; full: { cagr: number; maxDd: number } };
  dailyFloorProxy?: { oos: { cagr: number; maxDd: number } };
  pareto?: Array<{
    spec: { putDistance: number; dte: number; rollDays: number; tailPut: number };
    valCagr: number;
    valMaxDd: number;
    valPrem: number;
    valEff: number;
    score: number;
  }>;
  dataLayer?: Record<string, string>;
  searchedGrid?: { n: number };
  proxyDisclaimer?: string;
};

const F = frozen as Frozen;

function Page() {
  const seed = F.selectedSpec;
  const [putDistance, setPutDistance] = useState(seed?.putDistance ?? DEFAULT_PROTECTED.putDistance);
  const [dte, setDte] = useState(seed?.dte ?? DEFAULT_PROTECTED.dte);
  const [rollDays, setRollDays] = useState(seed?.rollDays ?? DEFAULT_PROTECTED.rollDays);
  const [calmPut, setCalmPut] = useState(seed?.calmPut ?? DEFAULT_PROTECTED.calmPut);
  const [unstablePut, setUnstablePut] = useState(seed?.unstablePut ?? DEFAULT_PROTECTED.unstablePut);
  const [tailPut, setTailPut] = useState(seed?.tailPut ?? DEFAULT_PROTECTED.tailPut);
  const [recoveryPut, setRecoveryPut] = useState(seed?.recoveryPut ?? DEFAULT_PROTECTED.recoveryPut);
  const spec: ProtectedSpec = {
    ...DEFAULT_PROTECTED,
    putDistance,
    dte,
    rollDays,
    calmPut,
    unstablePut,
    tailPut,
    recoveryPut,
  };
  const w = sampleWindow();
  const live = useMemo(() => runProtected(spec), [putDistance, dte, rollDays, calmPut, unstablePut, tailPut, recoveryPut]);
  const hold = useMemo(() => buyHoldQQQ(), []);
  const bench = historicalBenchmark();

  return (
    <Shell>
      <div className="grid gap-4">
        <Panel kicker="BACKTEST V2.2 · PUT OVERLAY · OOS FROZEN" title="兩個控制器：QQQ 倉位獨立於 Put 倉位">
          <p className="max-w-4xl text-sm leading-relaxed text-muted">
            不再每天把 QQQ 截在 −1.5%。這是持續 put overlay：strike / DTE / roll / 狀態決定 put 規模。QQQ
            第一波鎖 100%——用 convexity 換回撤，不是用降倉換回撤。VIX 當 IV 是 Derived，10% 價差是
            Estimated，<span className="text-fg">不是 OPRA 成交回測</span>。
          </p>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 md:grid-cols-5">
            <Metric k="Observed QQQ OOS" v={`${fmtPct(F.buyHoldQQQ?.oos.cagr ?? hold.split.oos.cagr, 2)} / ${fmtPct(F.buyHoldQQQ?.oos.maxDd ?? hold.split.oos.maxDd, 2)}`} />
            <Metric k="Frozen OOS CAGR" v={fmtPct(F.oos?.cagr ?? live.split.oos.cagr, 2)} />
            <Metric k="Frozen OOS MaxDD" v={fmtPct(F.oos?.maxDd ?? live.split.oos.maxDd, 2)} />
            <Metric k="Val prot. eff" v={(F.extras?.validation?.protectionEfficiency ?? live.extras.validation.protectionEfficiency).toFixed(2)} />
            <Metric k="OOS positive-return days" v={`${F.oos?.positiveDays ?? live.split.oos.positiveDays}/${F.oos?.nDays ?? live.split.oos.nDays} · ${(F.oos?.positiveDayRatePct ?? live.split.oos.positiveDayRatePct).toFixed(2)}%`} />
          </div>
          <p className="mt-3 font-mono text-xs text-subtle">
            {w.trainDate} → train {w.trainEndDate} → val {w.valEndDate} → OOS {w.oosStartDate} → {w.endDate} · {w.nBars}{" "}
            bars · grid {F.searchedGrid?.n ?? "—"}
          </p>
          <p className="mt-1 font-mono text-xs text-subtle">
            {F.proxyDisclaimer ?? live.disclaimer} · leakage false
          </p>
        </Panel>

        <Panel kicker="CONTROLLER B · PUT" title="狀態決定保護，不決定是否還拿著 QQQ">
          <div className="grid gap-4 md:grid-cols-3">
            <Slider label="OTM distance" value={putDistance} set={setPutDistance} max={0.08} />
            <Slider label="DTE days" value={dte} set={setDte} max={90} step={1} asDays />
            <Slider label="Roll remaining" value={rollDays} set={setRollDays} max={30} step={1} asDays />
            <Slider label="CALM put" value={calmPut} set={setCalmPut} max={1.5} />
            <Slider label="UNSTABLE put" value={unstablePut} set={setUnstablePut} max={1.5} />
            <Slider label="TAIL put" value={tailPut} set={setTailPut} max={1.5} />
            <Slider label="RECOVERY put" value={recoveryPut} set={setRecoveryPut} max={1.5} />
          </div>
          <p className="mt-3 text-xs text-subtle">
            BUILDING（vol 加速 / VIX 加速 / 5d 下跌）把 put 至少抬到 75%。Put 只加倉、減倉等到 roll。Controller A
            第一波鎖 QQQ=100%。
          </p>
        </Panel>

        <Panel kicker="LIVE SPEC" title="這一組參數的路徑（不是重新搜 OOS）">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[920px] text-left text-sm">
              <thead className="text-xs text-subtle">
                <tr>
                  {["split", "CAGR", "MaxDD", "Sharpe", "ES", "Prem drag", "Prot. eff"].map((x) => (
                    <th key={x} className="px-3 py-2">
                      {x}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(
                  [
                    ["FULL", live.metrics, live.extras.full],
                    ["TRAIN", live.split.train, live.extras.train],
                    ["VALIDATION", live.split.validation, live.extras.validation],
                    ["OOS", live.split.oos, live.extras.oos],
                  ] as const
                ).map(([n, m, e]) => (
                  <tr key={n} className="border-t border-line">
                    <td className="px-3 py-2 font-mono">{n}</td>
                    <td className="px-3 py-2 font-mono">{fmtPct(m.cagr, 2)}</td>
                    <td className="px-3 py-2 font-mono">{fmtPct(m.maxDd, 2)}</td>
                    <td className="px-3 py-2 font-mono">{m.sharpe.toFixed(2)}</td>
                    <td className="px-3 py-2 font-mono">{fmtPct(m.es, 2)}</td>
                    <td className="px-3 py-2 font-mono">{fmtPct(e.premiumDrag, 2)}</td>
                    <td className="px-3 py-2 font-mono">{e.protectionEfficiency.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-3 text-xs text-subtle">正收益日比例是逐日模型收益的觀察頻率，不是期權逐筆勝率；MaxDD、ES 與 premium drag 保留作風險衡量，不設固定二元門檻。</p>
        </Panel>

        <div className="grid gap-4 md:grid-cols-2">
          <Panel kicker="VALIDATION PARETO" title="CAGR ↑ MaxDD ↓ Prem ↓ · OOS 不排序">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-xs text-subtle">
                  <tr>
                    <th className="py-2">dist</th>
                    <th className="py-2">dte</th>
                    <th className="py-2">tail put</th>
                    <th className="py-2">Val CAGR</th>
                    <th className="py-2">Val DD</th>
                    <th className="py-2">eff</th>
                  </tr>
                </thead>
                <tbody>
                  {(F.pareto ?? []).slice(0, 10).map((r, i) => (
                    <tr key={i} className="border-t border-line">
                      <td className="py-2 font-mono">{fmtPct(r.spec.putDistance, 0)}</td>
                      <td className="py-2 font-mono">{r.spec.dte}</td>
                      <td className="py-2 font-mono">{fmtPct(r.spec.tailPut, 0)}</td>
                      <td className="py-2 font-mono">{fmtPct(r.valCagr, 2)}</td>
                      <td className="py-2 font-mono">{fmtPct(r.valMaxDd, 2)}</td>
                      <td className="py-2 font-mono">{r.valEff.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {!(F.pareto && F.pareto.length) ? (
              <p className="text-xs text-subtle">跑完引擎後這裡會出現 validation Pareto。</p>
            ) : null}
          </Panel>
          <Panel kicker="FROZEN CHAMPION" title="VALIDATION 勝出後才看一次 OOS">
            <div className="space-y-2 font-mono text-sm">
              <div>distance {fmtPct(seed?.putDistance ?? spec.putDistance, 0)} · DTE {seed?.dte ?? spec.dte} · roll {seed?.rollDays ?? spec.rollDays}</div>
              <div>
                put C/U/T/R {fmtPct(seed?.calmPut ?? 0, 0)} / {fmtPct(seed?.unstablePut ?? 0, 0)} / {fmtPct(seed?.tailPut ?? 0, 0)} /{" "}
                {fmtPct(seed?.recoveryPut ?? 0, 0)}
              </div>
              <div>
                TRAIN {fmtPct(F.train?.cagr ?? live.split.train.cagr, 2)} / {fmtPct(F.train?.maxDd ?? live.split.train.maxDd, 2)}
              </div>
              <div>
                VAL {fmtPct(F.validation?.cagr ?? live.split.validation.cagr, 2)} / {fmtPct(F.validation?.maxDd ?? live.split.validation.maxDd, 2)}
              </div>
              <div>
                OOS {fmtPct(F.oos?.cagr ?? live.split.oos.cagr, 2)} / {fmtPct(F.oos?.maxDd ?? live.split.oos.maxDd, 2)}
              </div>
              <div className="text-xs text-subtle">
                Bench {fmtPct(bench.cagr, 2)} / {fmtPct(bench.maxDd, 2)} is not this run
              </div>
              <div className="text-xs text-subtle">OOS 正收益日：{F.oos?.positiveDays ?? live.split.oos.positiveDays}/{F.oos?.nDays ?? live.split.oos.nDays}（{(F.oos?.positiveDayRatePct ?? live.split.oos.positiveDayRatePct).toFixed(2)}%）</div>
            </div>
          </Panel>
        </div>

        <Panel kicker="AUDIT" title="用可觀察頻率、風險與資料品質描述結果">
          <ul className="space-y-2 text-sm text-muted">
            <li>• 只搜 PROTECTED overlay。CONVEX / 每日 −1.5% floor 不進官方 ranking。</li>
            <li>• Controller A（QQQ）第一波鎖 100%。Controller B（Put）跟狀態走，只加不減直到 roll。</li>
            <li>• BUILDING 用 vol/VIX 加速度 + 5d 下跌提前加保護，不必等 VIX≥30。</li>
            <li>• Score 含 Protection Efficiency = DD reduction / premium drag。Pareto 並列 CAGR、MaxDD、premium drag，不轉成固定二元門檻。</li>
            <li>• OOS 不參與 generation / ranking。oosLeakage = false；正收益日率只描述逐日模型路徑，不等於期權逐筆勝率。</li>
            <li>• 沒有歷史 option chain：這是 Derived BS + Estimated spread，不是成交。</li>
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
  step = 0.01,
  asDays = false,
}: {
  label: string;
  value: number;
  set: (n: number) => void;
  max: number;
  step?: number;
  asDays?: boolean;
}) {
  return (
    <label className="grid gap-2 text-sm">
      <span className="font-mono text-xs text-subtle">
        {label} · {asDays ? `${value.toFixed(0)}d` : fmtPct(value, 1)}
      </span>
      <input
        type="range"
        min={0}
        max={max}
        step={step}
        value={value}
        onChange={(e) => set(Number(e.target.value))}
        className="h-10 accent-accent"
      />
    </label>
  );
}
