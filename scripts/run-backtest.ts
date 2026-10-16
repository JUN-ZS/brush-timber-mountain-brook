import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import {
  BUY_HOLD_QQQ_POLICY,
  buyHoldQQQ,
  coverage,
  historicalBenchmark,
  runBacktest,
  sampleWindow,
  type Metrics,
} from "../src/lib/pulse/backtest.ts";
import {
  INTENDED_PROTECTED_GRID,
  assertPutCushionsDownDay,
  firstWaveGrid,
  freezeProtected,
  paretoProtected,
  searchProtected,
  type ProtectedExtras,
  type ProtectedResult,
  type ProtectedSpec,
} from "../src/lib/pulse/protected.ts";
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
    positiveDays: m.positiveDays,
    negativeDays: m.negativeDays,
    flatDays: m.flatDays,
    positiveDayRatePct: m.positiveDayRatePct,
  };
}

function extraRow(e: ProtectedExtras) {
  return {
    premiumDrag: e.premiumDrag,
    premiumSum: e.premiumSum,
    nRolls: e.nRolls,
    nAddOns: e.nAddOns,
    nOpens: e.nOpens,
    protectionEfficiency: e.protectionEfficiency,
    avgPutSize: e.avgPutSize,
    daysWithPut: e.daysWithPut,
  };
}

function specRow(s: ProtectedSpec) {
  return {
    putDistance: s.putDistance,
    dte: s.dte,
    rollDays: s.rollDays,
    calmPut: s.calmPut,
    unstablePut: s.unstablePut,
    tailPut: s.tailPut,
    recoveryPut: s.recoveryPut,
    buildingPut: s.buildingPut,
    qqq: { calm: s.qqqCalm, unstable: s.qqqUnstable, tail: s.qqqTail, recovery: s.qqqRecovery },
    emergencyDd: s.emergencyDd,
    spread: s.spread,
  };
}

function main() {
  const putGuard = assertPutCushionsDownDay();
  mkdirSync(outDir, { recursive: true });
  mkdirSync(join(root, "src/data"), { recursive: true });
  const w = sampleWindow();
  const cov = coverage();
  const hold = buyHoldQQQ();
  const dailyFloor = runBacktest("PROTECTED_PROXY", BUY_HOLD_QQQ_POLICY, w.start, w.end, false, 1);
  const gridN = firstWaveGrid().length;

  const ranked = searchProtected();
  const champion = freezeProtected(ranked);
  const frontier = paretoProtected(ranked).slice(0, 16);
  const bench = historicalBenchmark();

  const json = {
    version: "2.2",
    executed: true,
    executedAt: new Date().toISOString(),
    oosLeakage: false,
    officialSearch: "PROTECTED put overlay only",
    dataStart: universe.dates[0],
    dataEnd: universe.dates[universe.dates.length - 1],
    nBars: universe.dates.length,
    nObservations: champion.curve.length,
    window: w,
    coverage: cov,
    dataLayer: {
      qqq: "Observed",
      vix: "Observed (used as IV proxy)",
      putPrice: "Derived Black-Scholes",
      iv: "Derived — VIX as IV, flat term structure, not QQQ option IV, not this DTE",
      spread: "Estimated 10% of mid on open and early close",
      fills: "NOT OPRA. Not a historical option-chain fill backtest.",
    },
    intendedGrid: INTENDED_PROTECTED_GRID,
    searchedGrid: {
      n: gridN,
      putDistance: [0.02, 0.03, 0.05],
      dte: [21, 30, 45],
      rollDays: [7, 14],
      calmPut: [0, 0.25],
      unstablePut: [0.25, 0.5, 0.75],
      tailPut: [0.75, 1, 1.5],
      recoveryPut: [0.25, 0.5],
      qqqExposure: "frozen at 100% all states (convexity, not de-risk)",
      emergencyDd: null,
      buildingPut: 0.75,
    },
    putGuard,
    benchmark: bench,
    buyHoldQQQ: {
      layer: "Observed",
      train: row(hold.split.train),
      validation: row(hold.split.validation),
      oos: row(hold.split.oos),
      full: row(hold.metrics),
    },
    dailyFloorProxy: {
      layer: "Hypothetical",
      label: "V2.1 daily -1.5% floor + 2.5bps, no state-risk overlay",
      train: row(dailyFloor.split.train),
      validation: row(dailyFloor.split.validation),
      oos: row(dailyFloor.split.oos),
      full: row(dailyFloor.metrics),
    },
    selectedSpec: specRow(champion.spec),
    layer: "Derived",
    proxyDisclaimer: champion.disclaimer,
    train: row(champion.split.train),
    validation: row(champion.split.validation),
    oos: row(champion.split.oos),
    full: row(champion.metrics),
    extras: {
      train: extraRow(champion.extras.train),
      validation: extraRow(champion.extras.validation),
      oos: extraRow(champion.extras.oos),
      full: extraRow(champion.extras.full),
    },
    score: champion.score,
    oosReturnFrequency: {
      metric: "Positive-return sessions / observed daily sessions; not option trade-level win rate.",
      protectedPutOverlay: { positiveDays: champion.split.oos.positiveDays, negativeDays: champion.split.oos.negativeDays, flatDays: champion.split.oos.flatDays, totalDays: champion.split.oos.nDays, positiveDayRatePct: champion.split.oos.positiveDayRatePct },
      observedQQQ: { positiveDays: hold.split.oos.positiveDays, negativeDays: hold.split.oos.negativeDays, flatDays: hold.split.oos.flatDays, totalDays: hold.split.oos.nDays, positiveDayRatePct: hold.split.oos.positiveDayRatePct },
    },
    selection: {
      score: "protectedScore(validation) including protection efficiency; OOS unused",
      nCandidates: gridN,
      frozenOn: "train+validation window only",
      oosTouchedDuringSelection: false,
    },
    pareto: frontier.map((r) => ({
      spec: specRow(r.spec),
      valCagr: r.split.validation.cagr,
      valMaxDd: r.split.validation.maxDd,
      valEs: r.split.validation.es,
      valPrem: r.extras.validation.premiumDrag,
      valEff: r.extras.validation.protectionEfficiency,
      score: r.score,
    })),
  };

  const slim = { ...json };
  writeFileSync(join(outDir, "backtest-result.json"), JSON.stringify(json, null, 2));
  writeFileSync(join(root, "src/data/backtest-v2-2.json"), JSON.stringify(slim, null, 2));

  const csvLines = [
    "date,equity,drawdown,regime,building,qqqExp,putSize,putMark,premium,strategyReturn,vix",
    ...champion.curve.map(
      (p) =>
        `${p.date},${p.equity.toFixed(8)},${p.drawdown.toFixed(8)},${p.regime},${p.building ? 1 : 0},${p.qqqExp.toFixed(4)},${p.putSize.toFixed(4)},${p.putMark.toFixed(6)},${p.premium.toFixed(6)},${p.strategyReturn.toFixed(8)},${p.vix ?? ""}`,
    ),
  ];
  writeFileSync(join(outDir, "backtest-curve.csv"), csvLines.join("\n"));

  const md = `# BACKTEST V2.2 · PROTECTED PUT OVERLAY

Data: ${json.dataStart} → ${json.dataEnd} (${json.nBars} bars, ${json.nObservations} observations)

VXX coverage (context): ${cov.vxxStart} → ${cov.vxxEnd} (${cov.vxxBars} bars)
Split: TRAIN ${w.trainDate} → ${w.trainEndDate} · VAL → ${w.valEndDate} · OOS ${w.oosStartDate} → ${w.endDate}

Official search: **PROTECTED put overlay only** (${gridN} first-wave specs).
QQQ exposure frozen at 100%. DD brake off. Convexity, not de-risk.

Data layer: QQQ/VIX Observed · put **Derived BS(VIX as IV)** · spread **Estimated 10%** · **NOT OPRA**

Benchmark (historical, not this run): CAGR ${pct(bench.cagr)}  MaxDD ${pct(bench.maxDd)}

## Layers

| Layer | What | FULL CAGR | FULL MaxDD | OOS CAGR | OOS MaxDD | OOS positive days | OOS positive-day rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Observed | QQQ 100% price path | ${pct(hold.metrics.cagr)} | ${pct(hold.metrics.maxDd)} | ${pct(hold.split.oos.cagr)} | ${pct(hold.split.oos.maxDd)} | ${hold.split.oos.positiveDays}/${hold.split.oos.nDays} | ${hold.split.oos.positiveDayRatePct.toFixed(2)}% |
| Hypothetical | Daily −1.5% floor toy | ${pct(dailyFloor.metrics.cagr)} | ${pct(dailyFloor.metrics.maxDd)} | ${pct(dailyFloor.split.oos.cagr)} | ${pct(dailyFloor.split.oos.maxDd)} | ${dailyFloor.split.oos.positiveDays}/${dailyFloor.split.oos.nDays} | ${dailyFloor.split.oos.positiveDayRatePct.toFixed(2)}% |
| Derived | Frozen put overlay | ${pct(champion.metrics.cagr)} | ${pct(champion.metrics.maxDd)} | ${pct(champion.split.oos.cagr)} | ${pct(champion.split.oos.maxDd)} | ${champion.split.oos.positiveDays}/${champion.split.oos.nDays} | ${champion.split.oos.positiveDayRatePct.toFixed(2)}% |

Selected structure:
- distance ${pct(champion.spec.putDistance)} OTM · DTE ${champion.spec.dte}d · roll ${champion.spec.rollDays}d
- PUT CALM ${pct(champion.spec.calmPut)} / UNSTABLE ${pct(champion.spec.unstablePut)} / TAIL ${pct(champion.spec.tailPut)} / RECOVERY ${pct(champion.spec.recoveryPut)} / BUILDING ${pct(champion.spec.buildingPut)}
- QQQ exposure 100% all states
- spread ${pct(champion.spec.spread)} estimated

| Split | CAGR | MaxDD | Positive / observed days | Positive-day rate | Sharpe | Sortino | ES | Prem drag | Prot. eff |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TRAIN | ${pct(champion.split.train.cagr)} | ${pct(champion.split.train.maxDd)} | ${champion.split.train.positiveDays}/${champion.split.train.nDays} | ${champion.split.train.positiveDayRatePct.toFixed(2)}% | ${champion.split.train.sharpe.toFixed(2)} | ${champion.split.train.sortino.toFixed(2)} | ${pct(champion.split.train.es)} | ${pct(champion.extras.train.premiumDrag)} | ${champion.extras.train.protectionEfficiency.toFixed(2)} |
| VALIDATION | ${pct(champion.split.validation.cagr)} | ${pct(champion.split.validation.maxDd)} | ${champion.split.validation.positiveDays}/${champion.split.validation.nDays} | ${champion.split.validation.positiveDayRatePct.toFixed(2)}% | ${champion.split.validation.sharpe.toFixed(2)} | ${champion.split.validation.sortino.toFixed(2)} | ${pct(champion.split.validation.es)} | ${pct(champion.extras.validation.premiumDrag)} | ${champion.extras.validation.protectionEfficiency.toFixed(2)} |
| OOS | ${pct(champion.split.oos.cagr)} | ${pct(champion.split.oos.maxDd)} | ${champion.split.oos.positiveDays}/${champion.split.oos.nDays} | ${champion.split.oos.positiveDayRatePct.toFixed(2)}% | ${champion.split.oos.sharpe.toFixed(2)} | ${champion.split.oos.sortino.toFixed(2)} | ${pct(champion.split.oos.es)} | ${pct(champion.extras.oos.premiumDrag)} | ${champion.extras.oos.protectionEfficiency.toFixed(2)} |
| FULL | ${pct(champion.metrics.cagr)} | ${pct(champion.metrics.maxDd)} | ${champion.metrics.positiveDays}/${champion.metrics.nDays} | ${champion.metrics.positiveDayRatePct.toFixed(2)}% | ${champion.metrics.sharpe.toFixed(2)} | ${champion.metrics.sortino.toFixed(2)} | ${pct(champion.metrics.es)} | ${pct(champion.extras.full.premiumDrag)} | ${champion.extras.full.protectionEfficiency.toFixed(2)} |

## Empirical OOS daily-return frequency — no fixed pass/fail threshold
- Derived put overlay: ${champion.split.oos.positiveDays}/${champion.split.oos.nDays} positive-return sessions (${champion.split.oos.positiveDayRatePct.toFixed(2)}%).
- Observed QQQ buy-and-hold: ${hold.split.oos.positiveDays}/${hold.split.oos.nDays} positive-return sessions (${hold.split.oos.positiveDayRatePct.toFixed(2)}%).
- This is a daily positive-return frequency, not an option trade-level win rate or a claim of executable option fills. See the listed-contract quote-side replay for actual option-episode win rates.

OOS leakage: **false** (selection window ends ${w.valEndDate})
Put cushion guard: **true** (${putGuard.date} qqq=${putGuard.qqq.toFixed(4)} overlay=${putGuard.overlay.toFixed(4)})

Do not treat ${pct(bench.cagr)} / ${pct(bench.maxDd)} as V2.2 output.
`;
  writeFileSync(join(outDir, "backtest-report.md"), md);

  const summary = [
    `## Backtest V2.2 Protected overlay`,
    ``,
    `| Layer | OOS CAGR | OOS MaxDD | OOS positive-day rate |`,
    `| --- | --- | --- | --- |`,
    `| Observed QQQ | ${pct(hold.split.oos.cagr)} | ${pct(hold.split.oos.maxDd)} | ${hold.split.oos.positiveDayRatePct.toFixed(2)}% (${hold.split.oos.positiveDays}/${hold.split.oos.nDays}) |`,
    `| Daily floor toy | ${pct(dailyFloor.split.oos.cagr)} | ${pct(dailyFloor.split.oos.maxDd)} | ${dailyFloor.split.oos.positiveDayRatePct.toFixed(2)}% (${dailyFloor.split.oos.positiveDays}/${dailyFloor.split.oos.nDays}) |`,
    `| **Frozen put overlay** | **${pct(champion.split.oos.cagr)}** | **${pct(champion.split.oos.maxDd)}** | **${champion.split.oos.positiveDayRatePct.toFixed(2)}% (${champion.split.oos.positiveDays}/${champion.split.oos.nDays})** |`,
    ``,
    `Spec: ${pct(champion.spec.putDistance)} OTM · DTE ${champion.spec.dte} · roll ${champion.spec.rollDays} · put C/U/T/R ${pct(champion.spec.calmPut)}/${pct(champion.spec.unstablePut)}/${pct(champion.spec.tailPut)}/${pct(champion.spec.recoveryPut)}`,
    `Val prem drag ${pct(champion.extras.validation.premiumDrag)} · prot.eff ${champion.extras.validation.protectionEfficiency.toFixed(2)}`,
    `OOS leakage: false · candidates ${gridN} · NOT OPRA`,
  ].join("\n");

  if (process.env.GITHUB_STEP_SUMMARY) {
    writeFileSync(process.env.GITHUB_STEP_SUMMARY, summary, { flag: "a" });
  }

  console.log(md);
  console.log(summary);
  console.log("WROTE", join(outDir, "backtest-result.json"));
  console.log("WROTE", join(outDir, "backtest-curve.csv"));
  console.log("WROTE", join(outDir, "backtest-report.md"));
  console.log("OOS_POSITIVE_DAY_RATE_PCT", champion.split.oos.positiveDayRatePct.toFixed(2));
}

main();
