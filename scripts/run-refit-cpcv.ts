
/**
 * Re-fit CPCV / walk-forward for V2.2 PROTECTED overlay.
 * Selection uses TRAIN/VAL only (searchProtectedWindow). Test scored once after freeze.
 * Not frozen-curve sensitivity.
 */
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { sampleWindow, targetGate, type Metrics } from "../src/lib/pulse/backtest.ts";
import {
  evaluateProtectedWindow,
  firstWaveGrid,
  searchProtectedWindow,
  type ProtectedSpec,
  type ProtectedWindow,
  type ProtectedWindowResult,
} from "../src/lib/pulse/protected.ts";
import { universe } from "../src/lib/pulse/bars.ts";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const EMBARGO = 21;

function pct(x: number | null | undefined) {
  if (x == null || Number.isNaN(x)) return null;
  return Math.round(x * 10000) / 10000;
}

function row(m: Metrics | null) {
  if (!m) return null;
  return {
    cagr: pct(m.cagr),
    maxDd: pct(m.maxDd),
    sharpe: pct(m.sharpe),
    nDays: m.nDays,
    totalReturn: pct(m.totalReturn),
  };
}

function specKey(s: ProtectedSpec) {
  return `d${s.putDistance}_dte${s.dte}_roll${s.rollDays}_c${s.calmPut}_u${s.unstablePut}_t${s.tailPut}_r${s.recoveryPut}`;
}

function stretch(m: Metrics | null) {
  return !!m && m.cagr >= 0.12 && m.maxDd >= -0.05;
}
function cagrBand(m: Metrics | null) {
  return !!m && m.cagr >= 0.1 && m.cagr <= 0.15;
}
function jointBand(m: Metrics | null) {
  return !!m && m.cagr >= 0.1 && m.cagr <= 0.15 && m.maxDd >= -0.1;
}

function makeBlocks(nBlocks: number) {
  const w = sampleWindow();
  const start = w.start;
  const end = w.end;
  const n = end - start + 1;
  const blocks: { id: number; from: number; to: number; fromDate: string; toDate: string }[] = [];
  for (let b = 0; b < nBlocks; b++) {
    const from = start + Math.floor((b * n) / nBlocks);
    const to = start + Math.floor(((b + 1) * n) / nBlocks) - 1;
    blocks.push({
      id: b,
      from,
      to,
      fromDate: universe.dates[from],
      toDate: universe.dates[to],
    });
  }
  return { w, blocks };
}

function windowForPrefixTest(
  trainFrom: number,
  testFrom: number,
  testTo: number,
): ProtectedWindow {
  const embargoedTestFrom = testFrom;
  const valTo = Math.max(trainFrom + 50, embargoedTestFrom - 1 - EMBARGO);
  const span = valTo - trainFrom + 1;
  const trainTo = trainFrom + Math.floor(span * 0.75) - 1;
  const valFrom = trainTo + 1;
  return {
    simStart: trainFrom,
    simEnd: testTo,
    trainFrom,
    trainTo,
    valFrom,
    valTo,
    testFrom,
    testTo,
  };
}

function runFold(label: string, win: ProtectedWindow) {
  const t0 = Date.now();
  const ranked = searchProtectedWindow(win);
  const best = ranked[0];
  if (!best) throw new Error(`no candidates for ${label}`);
  const evaled = evaluateProtectedWindow(best.spec, win);
  const ms = Date.now() - t0;
  return {
    label,
    ms,
    window: {
      train: `${universe.dates[win.trainFrom]}→${universe.dates[win.trainTo]}`,
      val: `${universe.dates[win.valFrom]}→${universe.dates[win.valTo]}`,
      test:
        win.testFrom != null && win.testTo != null
          ? `${universe.dates[win.testFrom]}→${universe.dates[win.testTo]}`
          : null,
      embargoDays: EMBARGO,
    },
    selected: specKey(best.spec),
    selectedSpec: best.spec,
    selectScore: best.score,
    train: row(evaled.train),
    validation: row(evaled.validation),
    test: row(evaled.test),
    test_stretch: stretch(evaled.test),
    test_cagr_in_10_15: cagrBand(evaled.test),
    test_joint_band_10_15_dd10: jointBand(evaled.test),
    test_gate_official_12_dd5: evaled.test ? targetGate(evaled.test) : null,
    nGrid: firstWaveGrid().length,
  };
}

function combinations<T>(arr: T[], k: number): T[][] {
  const out: T[][] = [];
  const rec = (start: number, path: T[]) => {
    if (path.length === k) {
      out.push(path.slice());
      return;
    }
    for (let i = start; i < arr.length; i++) {
      path.push(arr[i]);
      rec(i + 1, path);
      path.pop();
    }
  };
  rec(0, []);
  return out;
}

function main() {
  const { w, blocks } = makeBlocks(6);
  console.log(
    `REFIT CPCV start bars=${w.start}..${w.end} (${universe.dates[w.start]}→${universe.dates[w.end]}) grid=${firstWaveGrid().length} blocks=${blocks.length}`,
  );

  const walkForward = [];
  for (let i = 1; i < blocks.length; i++) {
    const trainFrom = blocks[0].from;
    const test = blocks[i];
    // Need enough train before test
    if (test.from - trainFrom < 200) continue;
    const win = windowForPrefixTest(trainFrom, test.from, test.to);
    console.log(`WF fold test block ${test.id} ${test.fromDate}→${test.toDate}`);
    const fold = runFold(`walk_forward_test_block_${test.id}`, win);
    walkForward.push(fold);
    console.log(
      `  selected=${fold.selected} testCAGR=${fold.test?.cagr} testMaxDD=${fold.test?.maxDd} stretch=${fold.test_stretch} (${fold.ms}ms)`,
    );
  }

  // Purged combinatorial: test = pair of blocks; train = prefix before earliest test block only
  const purged = [];
  for (const pair of combinations(blocks, 2)) {
    const earliest = pair.reduce((a, b) => (a.from < b.from ? a : b));
    // Only use contiguous prefix train before earliest test — later non-test blocks after a hole are excluded (anti-leak)
    if (earliest.id === 0) continue; // no prefix train
    const later = pair.find((b) => b !== earliest)!;
    // Require test blocks to be a contiguous suffix starting at earliest (purge gaps): only accept adjacent pairs
    if (later.id !== earliest.id + 1) continue;
    const trainFrom = blocks[0].from;
    const testFrom = earliest.from;
    const testTo = later.to;
    if (testFrom - trainFrom < 200) continue;
    const win = windowForPrefixTest(trainFrom, testFrom, testTo);
    const label = `purged_adjacent_blocks_${earliest.id}_${later.id}`;
    console.log(`CPCV ${label} test ${universe.dates[testFrom]}→${universe.dates[testTo]}`);
    const fold = runFold(label, win);
    purged.push(fold);
    console.log(
      `  selected=${fold.selected} testCAGR=${fold.test?.cagr} testMaxDD=${fold.test?.maxDd} stretch=${fold.test_stretch} (${fold.ms}ms)`,
    );
  }

  const allTest = [...walkForward, ...purged];
  const cagrs = allTest.map((f) => f.test?.cagr).filter((x): x is number => x != null);
  const dds = allTest.map((f) => f.test?.maxDd).filter((x): x is number => x != null);

  const summary = {
    method:
      "Re-fit: firstWaveGrid search with protectedScore(validation) on train-prefix windows only; test evaluated once. Walk-forward over 6 blocks + purged adjacent-block pairs. Embargo=21d before test. Non-contiguous post-hole train excluded to prevent path leak.",
    evidence_class: "REFIT_CPCV_TRAIN_ONLY_SELECTION",
    not: "frozen_curve_sensitivity",
    labels: {
      THEORETICAL_TARGET_BAND: "CAGR 10-15% and MaxDD >= -10%",
      STRETCH_HYPOTHESIS: "CAGR >= 12% and MaxDD >= -5%",
    },
    grid_n: firstWaveGrid().length,
    embargo_days: EMBARGO,
    n_walk_forward: walkForward.length,
    n_purged_adjacent: purged.length,
    test_cagr_mean: cagrs.length ? pct(cagrs.reduce((a, b) => a + b, 0) / cagrs.length) : null,
    test_cagr_min: cagrs.length ? pct(Math.min(...cagrs)) : null,
    test_cagr_max: cagrs.length ? pct(Math.max(...cagrs)) : null,
    test_maxdd_mean: dds.length ? pct(dds.reduce((a, b) => a + b, 0) / dds.length) : null,
    test_maxdd_worst: dds.length ? pct(Math.min(...dds)) : null,
    folds_stretch_pass: allTest.filter((f) => f.test_stretch).length,
    folds_cagr_in_10_15: allTest.filter((f) => f.test_cagr_in_10_15).length,
    folds_joint_band: allTest.filter((f) => f.test_joint_band_10_15_dd10).length,
    verdict: {
      STRETCH_HYPOTHESIS:
        allTest.every((f) => !f.test_stretch) ? "REJECTED_ON_REFIT_TEST_FOLDS" : "SOME_FOLDS_HIT_STRETCH_INSPECT",
      THEORETICAL_JOINT_BAND:
        allTest.filter((f) => f.test_joint_band_10_15_dd10).length === 0
          ? "NOT_SURVIVED_ON_REFIT_TEST_FOLDS"
          : "PARTIAL_HIT_INSPECT",
    },
  };

  const payload = {
    module: "refit_cpcv",
    asof: new Date().toISOString().slice(0, 10),
    sample: {
      start: universe.dates[w.start],
      end: universe.dates[w.end],
      blocks,
    },
    summary,
    walk_forward: walkForward,
    purged_adjacent: purged,
  };

  const research = join(root, "research");
  mkdirSync(research, { recursive: true });
  writeFileSync(join(research, "refit_cpcv.json"), JSON.stringify(payload, null, 2));

  const lines = [
    "# Re-fit CPCV (train-only selection)",
    "",
    "> True re-search on train/val windows. **Not** frozen-curve sensitivity.",
    "",
    `Grid: **${summary.grid_n}** specs (first wave). Embargo: **${EMBARGO}** days.`,
    "",
    "## Summary",
    "",
    `- folds: walk-forward **${summary.n_walk_forward}** + purged-adjacent **${summary.n_purged_adjacent}**`,
    `- test CAGR mean/min/max: **${summary.test_cagr_mean}** / ${summary.test_cagr_min} / ${summary.test_cagr_max}`,
    `- test MaxDD mean/worst: **${summary.test_maxdd_mean}** / ${summary.test_maxdd_worst}`,
    `- Stretch passes: **${summary.folds_stretch_pass}**`,
    `- CAGR in 10–15%: **${summary.folds_cagr_in_10_15}**`,
    `- Joint band (10–15% & DD≥-10%): **${summary.folds_joint_band}**`,
    "",
    `### Verdict`,
    "",
    `- STRETCH: **${summary.verdict.STRETCH_HYPOTHESIS}**`,
    `- THEORETICAL joint: **${summary.verdict.THEORETICAL_JOINT_BAND}**`,
    "",
    "## Walk-forward folds",
    "",
    "| Fold | Selected | Test CAGR | Test MaxDD | Stretch |",
    "| --- | --- | --- | --- | --- |",
  ];
  for (const f of walkForward) {
    lines.push(
      `| ${f.label} | \`${f.selected}\` | ${f.test?.cagr} | ${f.test?.maxDd} | ${f.test_stretch} |`,
    );
  }
  lines.push("", "## Purged adjacent-block folds", "", "| Fold | Selected | Test CAGR | Test MaxDD | Stretch |", "| --- | --- | --- | --- | --- |");
  for (const f of purged) {
    lines.push(
      `| ${f.label} | \`${f.selected}\` | ${f.test?.cagr} | ${f.test?.maxDd} | ${f.test_stretch} |`,
    );
  }
  lines.push(
    "",
    "## Method note",
    "",
    summary.method,
    "",
  );
  writeFileSync(join(research, "refit_cpcv.md"), lines.join("\n"));
  console.log("WROTE research/refit_cpcv.json");
  console.log("WROTE research/refit_cpcv.md");
  console.log(JSON.stringify(summary, null, 2));
}

main();
