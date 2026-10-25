#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";

const ROOT = path.resolve(import.meta.dirname);
const DEFAULT_V3_ENGINE = path.resolve(
  ROOT, "..", "..", "terminal", "qqq_hybrid_deployment_terminal_v3", "engine.js"
);
const DEFAULT_V3_URL = process.env.QHP_V3_URL || "http://127.0.0.1:8788";

function output(payload) {
  process.stdout.write(JSON.stringify(payload));
}

function loadEngine(enginePath = process.env.QHP_V3_ENGINE || DEFAULT_V3_ENGINE) {
  if (!fs.existsSync(enginePath)) {
    return {
      ok: false,
      connected: false,
      available: false,
      source: "V3_ENGINE_NOT_PRESENT",
      error: "V3 engine not present at expected path: " + enginePath,
      enginePath,
    };
  }

  const source = fs.readFileSync(enginePath, "utf8");
  const sandbox = { window: {} };
  vm.createContext(sandbox);
  vm.runInContext(source, sandbox, { filename: enginePath });

  const engine = sandbox.window.HybridEngineV3;
  if (!engine || typeof engine.derive !== "function") {
    throw new Error("V3 engine did not expose HybridEngineV3.derive");
  }
  return { ok: true, engine, enginePath };
}

function normalizeSnapshot(raw) {
  const m1 = Number(raw.m1);
  const m2 = Number(raw.m2);
  const suppliedSlope = Number(raw.term_slope);
  const slope = Number.isFinite(suppliedSlope)
    ? suppliedSlope
    : (Number.isFinite(m1) && m1 !== 0 && Number.isFinite(m2) ? ((m2 - m1) / m1) * 100 : null);

  return {
    qqq: Number(raw.qqq),
    vxx: Number(raw.vxx),
    vix: Number(raw.vix),
    m1,
    m2,
    s: slope,
    termAsOf: raw.term_asof || null,
    spotAsOf: raw.spot_asof || null,
    today: raw.today || new Date().toISOString().slice(0, 10),
  };
}

async function fetchJson(url) {
  const response = await fetch(url, {
    headers: { "Cache-Control": "no-store" },
    signal: AbortSignal.timeout(5000),
  });
  const body = await response.text();
  if (!response.ok) throw new Error("V3 HTTP " + response.status + ": " + body.slice(0, 300));
  return JSON.parse(body);
}

async function bridge({ v3Url = DEFAULT_V3_URL, fixture = null } = {}) {
  const loaded = loadEngine();
  if (!loaded.ok) {
    return {
      ok: true,
      connected: false,
      available: false,
      policy_owner: "V3",
      source: loaded.source,
      error: loaded.error,
      enginePath: loaded.enginePath,
    };
  }

  let raw;
  try {
    raw = fixture || await fetchJson(v3Url.replace(/\/$/, "") + "/api/snapshot?bridge_ts=" + Date.now());
  } catch (error) {
    return {
      ok: true,
      connected: false,
      available: false,
      policy_owner: "V3",
      source: "V3_SERVER_UNAVAILABLE",
      error: error instanceof Error ? error.message : String(error),
      enginePath: loaded.enginePath,
    };
  }

  const d = normalizeSnapshot(raw);
  const decision = loaded.engine.derive(d);
  return {
    ok: true,
    connected: true,
    available: true,
    policy_owner: "V3",
    engine_version: loaded.engine.POLICY.engineVersion,
    policy_version: loaded.engine.POLICY.policyVersion,
    source: "V3_READ_ONLY_ENGINE",
    snapshot_asof: raw.captured_at || raw.term_asof || null,
    term_source: raw.term_source || null,
    state: decision.state,
    action: decision.action,
    gate: decision.gate,
    reason: decision.reason,
    health: decision.health,
    targets: decision.targets || null,
  };
}

if (process.argv.includes("--json")) {
  try {
    output(await bridge());
  } catch (error) {
    output({
      ok: false,
      connected: false,
      available: false,
      policy_owner: "V3",
      source: "V3_BRIDGE_ERROR",
      error: error instanceof Error ? error.message : String(error),
    });
  }
}

export { bridge, loadEngine, normalizeSnapshot };
