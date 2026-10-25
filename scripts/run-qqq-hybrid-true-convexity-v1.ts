import { mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { bsPrice } from "../src/lib/pulse/black-scholes.ts";
import { buyHoldQQQ } from "../src/lib/pulse/backtest.ts";
import { DEFAULT_PROTECTED, runProtected } from "../src/lib/pulse/protected.ts";

const ROOT = resolve(fileURLToPath(new URL("..", import.meta.url)));
const OUT_DIR = resolve(ROOT, process.env.OUT_DIR ?? "research/qqq_hybrid_downside_convexity_v1");

const SPEC = {
  ...DEFAULT_PROTECTED,
  putDistance: 0.05,
  dte: 45,
  rollDays: 7,
  calmPut: 0.50,
  unstablePut: 0.50,
  tailPut: 0.50,
  recoveryPut: 0.50,
  buildingPut: 0.50,
  qqqCalm: 1,
  qqqUnstable: 1,
  qqqTail: 1,
  qqqRecovery: 1,
  emergencyDd: null,
  spread: 0.10,
};

function pct(x: number) { return (x * 100).toFixed(3) + "%"; }
function finite(x: number | null | undefined) { return typeof x === "number" && Number.isFinite(x) ? x : null; }

function stressCurve() {
  const spot = 100;
  const strike = 95;
  const iv = 0.20;
  const tYears = 45 / 365;
  const unitNotional = 0.50;
  const entryMid = bsPrice({ spot, strike, tYears, iv, right: "PUT" });
  const entryPay = entryMid * (1 + SPEC.spread);
  const contracts = unitNotional * spot / spot;
  const shocks = [0, -0.05, -0.10, -0.20, -0.30];
  const rows = shocks.map((shock) => {
    const terminalSpot = spot * (1 + shock);
    const putPayoff = Math.max(strike - terminalSpot, 0) * contracts;
    const overlayReturn = shock + putPayoff / spot - entryPay / spot;
    return { shock, nakedReturn: shock, overlayReturn, incremental: overlayReturn - shock };
  });
  const by = new Map(rows.map((r) => [r.shock, r.overlayReturn]));
  const curvature = (by.get(-0.20) ?? 0) - 2 * (by.get(-0.10) ?? 0) + (by.get(0) ?? 0);
  return { entryMid, entryPay, contracts, rows, curvature };
}

function main() {
  const naked = buyHoldQQQ();
  const fixed = runProtected(SPEC, 60, undefined, true);
  const stress = stressCurve();

  const result = {
    researchId: "QQQ_HYBRID_TRUE_CONVEXITY_V1",
    status: "RESEARCH_ONLY",
    data: {
      source: "src/data/universe.json",
      sourceAsOf: "2026-09-04",
      optionModel: "DERIVED_BLACK_SCHOLES_WITH_VIX_IV_IN_EXISTING_PROTECTED_ENGINE",
      historicalOptionFills: "NOT_OPRA",
    },
    preregisteredHypothesis: "100% QQQ exposure plus constant 0.5x 5% OTM 45D protective put, rolled 7 calendar days before expiry, 10% spread haircut; no regime sizing and no parameter search.",
    benchmark: {
      full: { cagr: naked.metrics.cagr, maxDd: naked.metrics.maxDd, es: naked.metrics.es },
      validation: { cagr: naked.split.validation.cagr, maxDd: naked.split.validation.maxDd, es: naked.split.validation.es },
      oos: { cagr: naked.split.oos.cagr, maxDd: naked.split.oos.maxDd, es: naked.split.oos.es },
    },
    overlay: {
      spec: SPEC,
      full: {
        cagr: fixed.metrics.cagr,
        maxDd: fixed.metrics.maxDd,
        es: fixed.metrics.es,
        premiumDrag: fixed.extras.full.premiumDrag,
        protectionEfficiency: fixed.extras.full.protectionEfficiency,
        avgPutSize: fixed.extras.full.avgPutSize,
        rolls: fixed.extras.full.nRolls,
        opens: fixed.extras.full.nOpens,
      },
      validation: {
        cagr: fixed.split.validation.cagr,
        maxDd: fixed.split.validation.maxDd,
        es: fixed.split.validation.es,
        premiumDrag: fixed.extras.validation.premiumDrag,
        protectionEfficiency: fixed.extras.validation.protectionEfficiency,
      },
      oos: {
        cagr: fixed.split.oos.cagr,
        maxDd: fixed.split.oos.maxDd,
        es: fixed.split.oos.es,
        premiumDrag: fixed.extras.oos.premiumDrag,
        protectionEfficiency: fixed.extras.oos.protectionEfficiency,
      },
    },
    deltasVsNaked: {
      full: {
        cagr: fixed.metrics.cagr - naked.metrics.cagr,
        maxDd: fixed.metrics.maxDd - naked.metrics.maxDd,
        es: fixed.metrics.es - naked.metrics.es,
      },
      validation: {
        cagr: fixed.split.validation.cagr - naked.split.validation.cagr,
        maxDd: fixed.split.validation.maxDd - naked.split.validation.maxDd,
        es: fixed.split.validation.es - naked.split.validation.es,
      },
      oos: {
        cagr: fixed.split.oos.cagr - naked.split.oos.cagr,
        maxDd: fixed.split.oos.maxDd - naked.split.oos.maxDd,
        es: fixed.split.oos.es - naked.split.oos.es,
      },
    },
    mechanicalConvexity: {
      stress: stress.rows,
      frozenPayoffCurvature_0_10_20: stress.curvature,
      definition: "W(-20%) - 2*W(-10%) + W(0%) on a fixed 0.5x 5% OTM 45D put overlay.",
      note: "This is an isolated payoff stress, not a historical fill result.",
    },
    disclaimer: "Historical overlay is the repository's derived BS/VIX engine, not OPRA. Mechanical stress only demonstrates non-linear payoff shape; it does not establish live profitability.",
  };

  mkdirSync(OUT_DIR, { recursive: true });
  writeFileSync(resolve(OUT_DIR, "qqq_hybrid_true_convexity_v1.json"), JSON.stringify(result, null, 2));

  const md = [
    "# QQQ_HYBRID_TRUE_CONVEXITY_V1",
    "",
    "> RESEARCH_ONLY. Fixed hypothesis. No ranking. No product authority.",
    "",
    "## Fixed hypothesis",
    "100% QQQ exposure + constant 0.5x 5% OTM 45D protective put, rolled 7 calendar days before expiry, estimated 10% spread haircut. No regime sizing and no parameter search.",
    "",
    "## Historical result",
    "| Split | Naked CAGR | Overlay CAGR | ΔCAGR | Naked MaxDD | Overlay MaxDD | ΔMaxDD | Overlay premium drag |",
    "| --- | --- | --- | --- | --- | --- | --- | --- |",
    "| Validation | " + pct(naked.split.validation.cagr) + " | " + pct(fixed.split.validation.cagr) + " | " + pct(fixed.split.validation.cagr - naked.split.validation.cagr) + " | " + pct(naked.split.validation.maxDd) + " | " + pct(fixed.split.validation.maxDd) + " | " + pct(fixed.split.validation.maxDd - naked.split.validation.maxDd) + " | " + pct(fixed.extras.validation.premiumDrag) + " |",
    "| OOS | " + pct(naked.split.oos.cagr) + " | " + pct(fixed.split.oos.cagr) + " | " + pct(fixed.split.oos.cagr - naked.split.oos.cagr) + " | " + pct(naked.split.oos.maxDd) + " | " + pct(fixed.split.oos.maxDd) + " | " + pct(fixed.split.oos.maxDd - naked.split.oos.maxDd) + " | " + pct(fixed.extras.oos.premiumDrag) + " |",
    "",
    "## Mechanical convexity",
    "Fixed payoff stress curvature = " + stress.curvature.toFixed(6),
    "",
    ...stress.rows.map((r) => "shock " + pct(r.shock) + " · naked " + pct(r.nakedReturn) + " · overlay " + pct(r.overlayReturn) + " · incremental " + pct(r.incremental)),
    "",
    "A positive frozen-payoff curvature is mechanical convexity. Historical improvement still has to be judged after premium drag and the model's non-OPRA limitations.",
    "",
  ].join("\n");
  writeFileSync(resolve(OUT_DIR, "qqq_hybrid_true_convexity_v1.md"), md);
  console.log(md);
}

main();
