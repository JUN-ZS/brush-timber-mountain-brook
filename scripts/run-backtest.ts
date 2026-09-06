import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  STRATEGIES,
  assertVxxHedgeIsLive,
  buyHoldQQQ,
  coverage,
  freezeChampion,
  freezeSpotChampion,
  historicalBenchmark,
  pareto,
  sampleWindow,
  searchPolicies,
  targetGate,
  type BacktestResult,
  type Metrics,
} from "../src/lib/pulse/backtest.ts";
import { universe } from "../src/lib/pulse/bars.ts";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const outDir = join(root, "artifacts");

function pct(x: number) {
  return `${(x * 100).toFixed(2)}%`;
}

function row(m: Metrics) {
  return {
    cagr: m.cagr,
    maxDd: m.maxDd,
    sharpe: m.sharpe,
    sortino: m.sortino,
    es: m.es,
    calmar: m.calmar,
    volatility: m.volatility,
    worstDay: m.worstDay,
    turnover: m.turnover,
    nDays: m.nDays,
    totalReturn: m.totalReturn,
  };
}

function main() {
  const hedgeGuard = assertVxxHedgeIsLive();
  mkdirSync(outDir, { recursive: true });
  const w = sampleWindow();
  const cov = coverage();
  const hold = buyHoldQQQ();
  const spotChampion = freezeSpotChampion();
  const spotGate = targetGate(spotChampion.split.oos);

  const frozenByStrategy: Record<string, BacktestResult> = {};
  const leaders: BacktestResult[] = [];
  for (const s of STRATEGIES) {
    const ranked = searchPolicies(s);
    const frozen = freezeChampion(ranked);
    frozenByStrategy[s] = frozen;
    if (ranked[0]) leaders.push(ranked[0]);
  }
  leaders.sort((a, b) => b.score - a.score);
  const champion = freezeChampion(leaders);
  const frontier = pareto(leaders).slice(0, 24);

  const bench = historicalBenchmark();
  const oosGate = targetGate(champion.split.oos);
  const fullGate = targetGate(champion.metrics);

  const json = {
    version: "2.1",
    executed: true,
    executedAt: new Date().toISOString(),
    oosLeakage: false,
    vxxHedgeGuard: hedgeGuard,
    dataStart: universe.dates[0],
    dataEnd: universe.dates[universe.dates.length - 1],
    nBars: universe.dates.length,
    nObservations: champion.curve.length,
    coverage: cov,
    window: w,
    dataBoundary: {
      vxxStart: cov.vxxStart,
      vxxBars: cov.vxxBars,
      vxxFirstClose: cov.vxxFirstClose,
      trainEnd: w.trainEndDate,
      trainContainsVxxStart: cov.vxxStartIndex >= 0 && cov.vxxStartIndex <= w.trainEnd,
      validationContainsVxx: cov.vxxStartIndex >= 0 && cov.vxxStartIndex <= w.valEnd,
      officialWindowNotShrunk: true,
      missingVxxTreatedAsZeroReturn: true,
    },
    benchmark: bench,
    buyHoldQQQ: {
      label: "Observed QQQ 100% price path, no state-risk overlay, no DD brake",
      layer: "Observed",
      train: row(hold.split.train),
      validation: row(hold.split.validation),
      oos: row(hold.split.oos),
      full: row(hold.metrics),
      oosGate: targetGate(hold.split.oos),
    },
    selectedStrategy: champion.strategy,
    selectedPolicy: champion.policy,
    proxy: champion.proxy,
    proxyDisclaimer: champion.proxy
      ? "HYPOTHETICAL OPTION PROXY — not a historical option-chain fill backtest. CONVEX_PROXY debit is a flat 5.5bps/day toy, not OPRA."
      : "spot / ETF overlay",
    layer: champion.proxy ? "Hypothetical" : "Derived",
    train: row(champion.split.train),
    validation: row(champion.split.validation),
    oos: row(champion.split.oos),
    full: row(champion.metrics),
    targetGate: {
      rule: "OOS CAGR >= 12% AND OOS MaxDD >= -5%",
      oos: oosGate,
      full: fullGate,
      final: oosGate.pass ? "PASS" : "FAIL",
      note: champion.proxy
        ? "PASS is on a HYPOTHETICAL OPTION PROXY. It is not a tradable option backtest and not the 12.52% historical book."
        : "Gate evaluated once on frozen OOS.",
    },
    spotChampion: {
      label: "Derived state-risk overlay, QQQ and QQQ_VXX only. Same OOS freeze. Not ranked against proxies.",
      layer: "Derived",
      strategy: spotChampion.strategy,
      policy: spotChampion.policy,
      train: row(spotChampion.split.train),
      validation: row(spotChampion.split.validation),
      oos: row(spotChampion.split.oos),
      full: row(spotChampion.metrics),
      oosGate: spotGate,
    },
    selection: {
      score: "validationScore(validation metrics only)",
      nCandidates: STRATEGIES.length * 108,
      frozenOn: "train+validation window only",
      oosTouchedDuringSelection: false,
    },
    pareto: frontier.map((r) => ({
      strategy: r.strategy,
      policy: r.policy,
      valCagr: r.split.validation.cagr,
      valMaxDd: r.split.validation.maxDd,
      score: r.score,
      proxy: r.proxy,
    })),
    strategyLeaders: Object.fromEntries(
      STRATEGIES.map((s) => {
        const r = frozenByStrategy[s];
        const gate = targetGate(r.split.oos);
        return [
          s,
          {
            policy: r.policy,
            proxy: r.proxy,
            train: row(r.split.train),
            validation: row(r.split.validation),
            oos: row(r.split.oos),
            full: row(r.metrics),
            score: r.score,
            oosGate: gate,
          },
        ];
      }),
    ),
  };

  writeFileSync(join(outDir, "backtest-result.json"), JSON.stringify(json, null, 2));

  const csvLines = [
    "date,equity,drawdown,regime,risk,qqqReturn,vxxReturn,strategyReturn",
    ...champion.curve.map(
      (p) =>
        `${p.date},${p.equity.toFixed(8)},${p.drawdown.toFixed(8)},${p.regime},${p.risk.toFixed(6)},${p.qqq ?? ""},${p.vxx ?? ""},${p.strategyReturn.toFixed(8)}`,
    ),
  ];
  writeFileSync(join(outDir, "backtest-curve.csv"), csvLines.join("\n"));

  const md = `# BACKTEST V2.1

Data: ${json.dataStart} → ${json.dataEnd} (${json.nBars} bars, ${json.nObservations} observations)

VXX coverage: ${cov.vxxStart} → ${cov.vxxEnd} (${cov.vxxBars} bars, first adj close ${cov.vxxFirstClose})
Missing VXX bars = 0 return in QQQ_VXX. Official window was NOT shrunk.

Split: TRAIN ${w.trainDate} → ${w.trainEndDate} · VAL → ${w.valEndDate} · OOS ${w.oosStartDate} → ${w.endDate}

Benchmark (historical, not this run): CAGR ${pct(bench.cagr)}  MaxDD ${pct(bench.maxDd)}

## Layers

| Layer | What | CAGR | MaxDD | OOS CAGR | OOS MaxDD | Gate |
| --- | --- | --- | --- | --- | --- | --- |
| Observed | QQQ 100% price path | ${pct(hold.metrics.cagr)} | ${pct(hold.metrics.maxDd)} | ${pct(hold.split.oos.cagr)} | ${pct(hold.split.oos.maxDd)} | ${targetGate(hold.split.oos).pass ? "PASS" : "FAIL"} |
| Derived | Frozen spot ${spotChampion.strategy} | ${pct(spotChampion.metrics.cagr)} | ${pct(spotChampion.metrics.maxDd)} | ${pct(spotChampion.split.oos.cagr)} | ${pct(spotChampion.split.oos.maxDd)} | ${spotGate.pass ? "PASS" : "FAIL"} |
| Hypothetical | Frozen ${champion.strategy} | ${pct(champion.metrics.cagr)} | ${pct(champion.metrics.maxDd)} | ${pct(champion.split.oos.cagr)} | ${pct(champion.split.oos.maxDd)} | ${oosGate.pass ? "PASS" : "FAIL"} |

Observed QQQ 100% (no overlay):
- TRAIN ${pct(hold.split.train.cagr)} / ${pct(hold.split.train.maxDd)}
- VALIDATION ${pct(hold.split.validation.cagr)} / ${pct(hold.split.validation.maxDd)}
- OOS ${pct(hold.split.oos.cagr)} / ${pct(hold.split.oos.maxDd)}
- FULL ${pct(hold.metrics.cagr)} / ${pct(hold.metrics.maxDd)}

Selected Strategy (all 5 compete on validation only): **${champion.strategy}**
Kind: ${champion.proxy ? "**HYPOTHETICAL OPTION PROXY** — 5.5bps/day debit toy, not OPRA" : "spot / ETF overlay"}

Selected Policy:
- CALM ${pct(champion.policy.baseRisk)}
- UNSTABLE ${pct(champion.policy.unstableRisk)}
- TAIL ${pct(champion.policy.tailRisk)}
- RECOVERY ${pct(champion.policy.recoveryRisk)}
- VXX hedge ${pct(champion.policy.vxxHedge)}
- DD brake ${pct(champion.policy.ddBrake)}

| Split | CAGR | MaxDD | Sharpe | Sortino | ES | nDays |
| --- | --- | --- | --- | --- | --- | --- |
| TRAIN | ${pct(champion.split.train.cagr)} | ${pct(champion.split.train.maxDd)} | ${champion.split.train.sharpe.toFixed(2)} | ${champion.split.train.sortino.toFixed(2)} | ${pct(champion.split.train.es)} | ${champion.split.train.nDays} |
| VALIDATION | ${pct(champion.split.validation.cagr)} | ${pct(champion.split.validation.maxDd)} | ${champion.split.validation.sharpe.toFixed(2)} | ${champion.split.validation.sortino.toFixed(2)} | ${pct(champion.split.validation.es)} | ${champion.split.validation.nDays} |
| OOS | ${pct(champion.split.oos.cagr)} | ${pct(champion.split.oos.maxDd)} | ${champion.split.oos.sharpe.toFixed(2)} | ${champion.split.oos.sortino.toFixed(2)} | ${pct(champion.split.oos.es)} | ${champion.split.oos.nDays} |
| FULL | ${pct(champion.metrics.cagr)} | ${pct(champion.metrics.maxDd)} | ${champion.metrics.sharpe.toFixed(2)} | ${champion.metrics.sortino.toFixed(2)} | ${pct(champion.metrics.es)} | ${champion.metrics.nDays} |

TARGET (OOS only, official champion):
- CAGR >= 12%: ${oosGate.cagrPass ? "PASS" : "FAIL"} (${pct(champion.split.oos.cagr)})
- MaxDD >= -5%: ${oosGate.ddPass ? "PASS" : "FAIL"} (${pct(champion.split.oos.maxDd)})
- FINAL: **${oosGate.pass ? "PASS" : "FAIL"}**${champion.proxy ? " (HYPOTHETICAL PROXY — not a tradable result)" : ""}

Spot-only frozen champion (QQQ / QQQ_VXX, same freeze): **${spotChampion.strategy}**
- VAL ${pct(spotChampion.split.validation.cagr)} / ${pct(spotChampion.split.validation.maxDd)}
- OOS ${pct(spotChampion.split.oos.cagr)} / ${pct(spotChampion.split.oos.maxDd)}
- Gate: **${spotGate.pass ? "PASS" : "FAIL"}**
- Policy: unst ${pct(spotChampion.policy.unstableRisk)} tail ${pct(spotChampion.policy.tailRisk)} hedge ${pct(spotChampion.policy.vxxHedge)} brake ${pct(spotChampion.policy.ddBrake)}

OOS leakage: **false** (selection window ends ${w.valEndDate})
vxxHedge live: **true** (sample ${hedgeGuard.sampleDate}: hedge0=${hedgeGuard.r0.toFixed(6)} hedge18=${hedgeGuard.r18.toFixed(6)})

Do not treat ${pct(bench.cagr)} / ${pct(bench.maxDd)} as V2.1 output.
`;
  writeFileSync(join(outDir, "backtest-report.md"), md);

  const summary = [
    `## Backtest V2.1`,
    ``,
    `| Strategy | Val CAGR | Val MaxDD | Frozen OOS CAGR | Frozen OOS MaxDD | Sharpe | Gate |`,
    `| --- | --- | --- | --- | --- | --- | --- |`,
    ...STRATEGIES.map((s) => {
      const r = frozenByStrategy[s];
      const gate = targetGate(r.split.oos);
      const mark = r.strategy === champion.strategy ? " ← champion" : "";
      return `| ${s}${r.proxy ? " (proxy)" : ""}${mark} | ${pct(r.split.validation.cagr)} | ${pct(r.split.validation.maxDd)} | ${pct(r.split.oos.cagr)} | ${pct(r.split.oos.maxDd)} | ${r.split.oos.sharpe.toFixed(2)} | ${gate.pass ? "PASS" : "FAIL"} |`;
    }),
    ``,
    `**Frozen Champion:** ${champion.strategy}${champion.proxy ? " · HYPOTHETICAL OPTION PROXY" : ""}`,
    ``,
    `| | CAGR | MaxDD | Sharpe | Sortino | ES |`,
    `| --- | --- | --- | --- | --- | --- |`,
    `| TRAIN | ${pct(champion.split.train.cagr)} | ${pct(champion.split.train.maxDd)} | ${champion.split.train.sharpe.toFixed(2)} | ${champion.split.train.sortino.toFixed(2)} | ${pct(champion.split.train.es)} |`,
    `| VALIDATION | ${pct(champion.split.validation.cagr)} | ${pct(champion.split.validation.maxDd)} | ${champion.split.validation.sharpe.toFixed(2)} | ${champion.split.validation.sortino.toFixed(2)} | ${pct(champion.split.validation.es)} |`,
    `| **OOS** | **${pct(champion.split.oos.cagr)}** | **${pct(champion.split.oos.maxDd)}** | ${champion.split.oos.sharpe.toFixed(2)} | ${champion.split.oos.sortino.toFixed(2)} | ${pct(champion.split.oos.es)} |`,
    `| FULL | ${pct(champion.metrics.cagr)} | ${pct(champion.metrics.maxDd)} | ${champion.metrics.sharpe.toFixed(2)} | ${champion.metrics.sortino.toFixed(2)} | ${pct(champion.metrics.es)} |`,
    `| Observed QQQ 100% | ${pct(hold.metrics.cagr)} | ${pct(hold.metrics.maxDd)} | ${hold.metrics.sharpe.toFixed(2)} | ${hold.metrics.sortino.toFixed(2)} | ${pct(hold.metrics.es)} |`,
    `| Derived spot ${spotChampion.strategy} | ${pct(spotChampion.metrics.cagr)} | ${pct(spotChampion.metrics.maxDd)} | ${spotChampion.metrics.sharpe.toFixed(2)} | ${spotChampion.metrics.sortino.toFixed(2)} | ${pct(spotChampion.metrics.es)} |`,
    ``,
    `Official OOS Gate 12% / -5%: **${oosGate.pass ? "PASS" : "FAIL"}**${champion.proxy ? " (HYPOTHETICAL PROXY)" : ""}`,
    `Spot-only OOS Gate: **${spotGate.pass ? "PASS" : "FAIL"}**`,
    `OOS leakage: false`,
    `vxxHedge live: true (${hedgeGuard.sampleDate})`,
    `VXX: ${cov.vxxStart} → ${cov.vxxEnd} (${cov.vxxBars} bars). Pre-VXX missing bars = 0 return. Window not shrunk.`,
  ].join("\n");

  if (process.env.GITHUB_STEP_SUMMARY) {
    writeFileSync(process.env.GITHUB_STEP_SUMMARY, summary, { flag: "a" });
  }

  console.log(md);
  console.log(summary);
  console.log("WROTE", join(outDir, "backtest-result.json"));
  console.log("WROTE", join(outDir, "backtest-curve.csv"));
  console.log("WROTE", join(outDir, "backtest-report.md"));
  console.log("FINAL", oosGate.pass ? "PASS" : "FAIL");
}

main();
