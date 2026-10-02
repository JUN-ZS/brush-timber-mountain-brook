import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Panel, Shell } from "@/components/shell";
import { fmtPct, fmtUsd } from "@/lib/utils";
import snapshot from "@/data/rolling_floor_ui_snapshot.json";

export const Route = createFileRoute("/floor")({ component: Page });

type EntryStatus = "BELOW_CLOCK" | "ON_CLOCK" | "AHEAD" | "OVER_CAPITAL";

type LedgerEntry = {
  id: string;
  recordedAt: string;
  asOf: string;
  month: number;
  amount: number;
};

const LEDGER_KEY_V2 = "qqq-rolling-floor-ledger-v2";
const FLOOR_STATE_KEY = "qqq-rolling-floor-state-v3";

const DEFAULT_CAPITAL = 100000;
const DEFAULT_STARTING_DEPLOYED = 0;
const DEFAULT_MONTH = 0;

type FloorPersistedState = {
  capital: number;
  startingDeployed: number;
  month: number;
  entries: LedgerEntry[];
};

function defaultFloorState(): FloorPersistedState {
  return {
    capital: DEFAULT_CAPITAL,
    startingDeployed: DEFAULT_STARTING_DEPLOYED,
    month: DEFAULT_MONTH,
    entries: [],
  };
}

function clampMonth(value: unknown): number {
  const n = Number(value);
  if (!Number.isFinite(n)) return DEFAULT_MONTH;
  return Math.max(0, Math.min(119, Math.round(n)));
}

function normalizeFloorState(raw: unknown): FloorPersistedState | null {
  if (raw == null) return null;

  // Legacy v2: array-only ledger
  if (Array.isArray(raw)) {
    return {
      ...defaultFloorState(),
      entries: raw.filter(validLedgerEntry),
    };
  }

  if (typeof raw !== "object") return null;
  const obj = raw as Record<string, unknown>;

  const capitalRaw = Number(obj.capital);
  const capital =
    Number.isFinite(capitalRaw) && capitalRaw >= 1 ? capitalRaw : DEFAULT_CAPITAL;

  const startingRaw = Number(obj.startingDeployed);
  const startingDeployed =
    Number.isFinite(startingRaw) && startingRaw >= 0
      ? startingRaw
      : DEFAULT_STARTING_DEPLOYED;

  const month = clampMonth(obj.month);

  const entriesSource = Array.isArray(obj.entries)
    ? obj.entries
    : Array.isArray(obj.ledger)
      ? obj.ledger
      : [];
  const entries = entriesSource.filter(validLedgerEntry);

  return { capital, startingDeployed, month, entries };
}

function loadFloorState(): FloorPersistedState {
  if (typeof window === "undefined") return defaultFloorState();

  try {
    const v3raw = window.localStorage.getItem(FLOOR_STATE_KEY);
    if (v3raw) {
      const parsed = normalizeFloorState(JSON.parse(v3raw));
      if (parsed) return parsed;
    }

    const v2raw = window.localStorage.getItem(LEDGER_KEY_V2);
    if (v2raw) {
      const parsed = normalizeFloorState(JSON.parse(v2raw));
      if (parsed) return parsed;
    }
  } catch {
    try {
      window.localStorage.removeItem(FLOOR_STATE_KEY);
    } catch {}
  }

  return defaultFloorState();
}

function writeFloorState(state: FloorPersistedState) {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(
      FLOOR_STATE_KEY,
      JSON.stringify({
        capital: state.capital,
        startingDeployed: state.startingDeployed,
        month: state.month,
        entries: state.entries,
      }),
    );
    // Prefer v3 as source of truth after migrate/write.
    window.localStorage.removeItem(LEDGER_KEY_V2);
  } catch {}
}

function Page() {
  const [capital, setCapital] = useState(DEFAULT_CAPITAL);
  const [startingDeployed, setStartingDeployed] = useState(DEFAULT_STARTING_DEPLOYED);
  const [actualNow, setActualNow] = useState(0);
  const [month, setMonth] = useState(DEFAULT_MONTH);
  const [ledger, setLedger] = useState<LedgerEntry[]>([]);
  const [copied, setCopied] = useState(false);
  const [hasHydrated, setHasHydrated] = useState(false);

  // Hydrate from localStorage before any persist write.
  useEffect(() => {
    const loaded = loadFloorState();
    setCapital(loaded.capital);
    setStartingDeployed(loaded.startingDeployed);
    setMonth(loaded.month);
    setLedger(loaded.entries);
    setHasHydrated(true);
  }, []);

  // Persist one blob after hydrate — never write the initial empty defaults.
  useEffect(() => {
    if (!hasHydrated) return;
    writeFloorState({
      capital,
      startingDeployed,
      month,
      entries: ledger,
    });
  }, [hasHydrated, capital, startingDeployed, month, ledger]);

  useEffect(() => {
    const onStorage = (event: StorageEvent) => {
      // writeFloorState removes the v2 ledger key after every v3 write.
      // Another tab must not treat that removal (newValue=null) as a full reset.
      if (event.key !== FLOOR_STATE_KEY) return;
      try {
        if (event.newValue == null) {
          setCapital(DEFAULT_CAPITAL);
          setStartingDeployed(DEFAULT_STARTING_DEPLOYED);
          setMonth(DEFAULT_MONTH);
          setLedger([]);
          return;
        }
        const parsed = normalizeFloorState(JSON.parse(event.newValue));
        if (!parsed) return;
        setCapital(parsed.capital);
        setStartingDeployed(parsed.startingDeployed);
        setMonth(parsed.month);
        setLedger(parsed.entries);
      } catch {}
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const safeCapital = Math.max(1, capital);
  const recordedAmount = ledger.reduce((sum, x) => sum + Math.max(0, x.amount), 0);
  const cumulativeBeforePreview = Math.max(0, startingDeployed) + recordedAmount;
  const cumulativeNowAmount = cumulativeBeforePreview + Math.max(0, actualNow);
  const cumulativeNowFraction = cumulativeNowAmount / safeCapital;

  const currentClock = clockTarget(month);
  const signalFloorAnchor = Math.max(0, Number(snapshot.current.coupledTargetAtPhaseZero) || 0);
  const cumulativeModelTarget = Math.min(1, Math.max(currentClock, signalFloorAnchor));
  const additionalSuggested = Math.max(0, cumulativeModelTarget * safeCapital - cumulativeBeforePreview);
  const remainingCapital = Math.max(0, safeCapital - cumulativeBeforePreview);
  const currentStatus = statusFor(cumulativeNowFraction, currentClock, cumulativeNowAmount, safeCapital);

  const responseCurves = useMemo(
    () =>
      (snapshot.current.perScale ?? [])
        .filter(
          (s) =>
            s.responseProfile?.deploymentFractions?.length &&
            s.responseProfile?.q05Terminal?.length,
        )
        .map((s) => ({
          scale: s.scaleYears,
          xs: s.responseProfile.deploymentFractions,
          ys: s.responseProfile.q05Terminal,
        })),
    [],
  );

  const maxResponse = responseCurves.length
    ? Math.max(...responseCurves.flatMap((c) => c.ys.map((x) => Number(x) || 0)))
    : 1;
  const responseDomain = [1, Math.max(2, maxResponse * 1.05)];

  const ndx = snapshot.current.mutualChase?.find((x) => x.channel === "NDX");
  const composite = snapshot.current.mutualChase?.find((x) => x.channel === "NASDAQCOM");
  const ndxHandoff = ndx ? leaderHandoff(ndx.topology.leaderScaleBySegment) : null;

  const capitalPoints = buildCapitalPoints(
    ledger,
    startingDeployed,
    safeCapital,
    { month, cumulativeAmount: cumulativeNowAmount },
  );

  function recordPoint() {
    if (!Number.isFinite(actualNow) || actualNow <= 0) return;
    if (cumulativeNowAmount > safeCapital + 1e-8) return;

    setLedger((entries) => [
      ...entries,
      {
        id: globalThis.crypto?.randomUUID?.() ?? String(Date.now()),
        recordedAt: new Date().toISOString(),
        asOf: snapshot.current.asOf,
        month,
        amount: actualNow,
      },
    ]);
    setActualNow(0);
  }

  function clearLocal() {
    // Match prior CLEAR UX: wipe ledger + starting + live preview.
    // capital/month reset to defaults; persisted blob rewritten by save effect.
    setLedger([]);
    setStartingDeployed(DEFAULT_STARTING_DEPLOYED);
    setActualNow(0);
    setCapital(DEFAULT_CAPITAL);
    setMonth(DEFAULT_MONTH);
  }

  function copyLedger() {
    const payload = JSON.stringify(
      {
        version: "rolling-floor-ledger.v3",
        asset: snapshot.asset,
        modelAsOf: snapshot.asOf,
        horizonYears: snapshot.horizonYears,
        totalCapital: safeCapital,
        startingDeployed,
        month,
        entries: ledger,
      },
      null,
      2,
    );

    const write = navigator.clipboard?.writeText(payload);
    if (!write) {
      window.alert(payload);
      return;
    }

    write.then(
      () => {
        setCopied(true);
        window.setTimeout(() => setCopied(false), 1200);
      },
      () => window.alert(payload),
    );
  }

  return (
    <Shell>
      <div className="grid gap-4">
        <Panel kicker="10Y CAPITAL FLOOR / CONTROL PLANE" title="第一步：按現況訊號決定今期投入">
          <div className="grid gap-5 lg:grid-cols-[1.15fr_0.85fr]">
            <div>
              <div className="flex flex-wrap items-end gap-3">
                <div>
                  <p className="font-mono text-xs text-subtle">本期需再投入</p>
                  <p className="mt-1 text-4xl font-semibold tabular-nums">{fmtUsd(additionalSuggested, 2)}</p>
                </div>
                <Badge tone={additionalSuggested > 0 ? "pass" : "mute"}>
                  target {fmtPct(cumulativeModelTarget, 3)}
                </Badge>
                <Badge tone={currentStatus === "BELOW_CLOCK" ? "lock" : currentStatus === "AHEAD" ? "fragile" : "pass"}>
                  {currentStatus}
                </Badge>
              </div>

              <div className="mt-4 grid gap-3 sm:grid-cols-3">
                <MetricCard kicker="CURRENT DEPLOYED" title={fmtPct(cumulativeBeforePreview / safeCapital, 3)} detail={fmtUsd(cumulativeBeforePreview, 2)} />
                <MetricCard kicker="CLOCK FLOOR" title={fmtPct(currentClock, 3)} detail={"month " + (month + 1) + " / 120"} />
                <MetricCard kicker="REMAINING" title={fmtUsd(remainingCapital, 2)} detail="available capital" />
              </div>

              <p className="mt-4 max-w-2xl text-sm text-muted">
                目前 verified snapshot = {snapshot.current.asOf}。現時 signal floor anchor =
                {" "}{fmtPct(signalFloorAnchor, 3)}；本 cycle 的硬約束仍然是 10Y deadline clock。
                這是研究模型，不是未來一定打平的保證。
              </p>
            </div>

            <div className="grid gap-3">
              <MoneyField label="Total capital" value={capital} onChange={(x) => setCapital(Math.max(1, x))} />
              <MoneyField
                label="Starting / already deployed"
                value={startingDeployed}
                onChange={(x) => setStartingDeployed(Math.max(0, x))}
              />
            </div>
          </div>
        </Panel>

        <div className="grid gap-4 lg:grid-cols-3">
          <MetricCard
            kicker="MARKET STATE"
            title={snapshot.current.divergenceStateAtPhaseZero}
            detail={"signals " + snapshot.current.signalCount + " · agreement " + fmtPct(snapshot.current.agreementAtPhaseZero, 0)}
          />
          <MetricCard
            kicker="MUTUAL CHASE"
            title={ndx?.topology.state ?? "THIN"}
            detail={
              ndxHandoff
                ? "NDX: " + ndxHandoff.from + "Y → " + ndxHandoff.to + "Y near " + fmtPct(ndxHandoff.at, 0)
                : "no current handoff"
            }
          />
          <MetricCard
            kicker="DATA"
            title={snapshot.current.asOf}
            detail="research snapshot · not live market feed"
          />
        </div>

        <Panel kicker="MUTUAL-CHASE GEOMETRY" title="20Y / 30Y / 50Y：追趕參考線">
          {responseCurves.length ? (
            <>
              <div className="overflow-x-auto">
                <ResponseChart
                  curves={responseCurves}
                  domain={responseDomain}
                  currentX={cumulativeNowFraction}
                  handoff={ndxHandoff}
                />
              </div>
              <div className="mt-3 flex flex-wrap gap-3 text-xs text-muted">
                {responseCurves.map((c) => (
                  <span key={c.scale} className="font-mono">
                    {c.scale}Y · q05@0% {c.ys[0].toFixed(2)}× · q05@100% {(c.ys.at(-1) ?? 0).toFixed(2)}×
                  </span>
                ))}
              </div>
            </>
          ) : (
            <EmptyState text="response curve 不完整；停止畫圖，不猜資料。" />
          )}
          <p className="mt-3 text-xs text-subtle">
            填色 = 三尺度目前 response envelope；白線 = 你目前累積投入位置；黃色虛線 =
            已驗證的 leader handoff。互追目前是監視層，未直接控制資金。
          </p>
        </Panel>

        <Panel kicker="CAPITAL TAPE / RULE CORRIDOR" title="你輸入的數字會立即反映在這條 10Y 路徑">
          <div className="grid gap-5 lg:grid-cols-[1fr_320px]">
            <div className="overflow-x-auto">
              <CapitalChart
                points={capitalPoints}
                currentClock={currentClock}
                currentStatus={currentStatus}
              />
            </div>

            <div className="grid content-start gap-3">
              <NumberField
                label="Current month in this 10Y cycle"
                unit="mo"
                value={month + 1}
                min={1}
                max={120}
                step={1}
                onChange={(x) => setMonth(clampMonth(x - 1))}
              />
              <MoneyField label="Actual cash invested now" value={actualNow} onChange={setActualNow} />

              <div className="rounded-lg border border-line bg-elevated p-3">
                <p className="font-mono text-xs text-subtle">LIVE PREVIEW</p>
                <div className="mt-2 grid grid-cols-2 gap-3">
                  <div>
                    <p className="font-mono text-[11px] text-subtle">after this point</p>
                    <p className="font-mono text-lg tabular-nums">{fmtPct(cumulativeNowFraction, 3)}</p>
                  </div>
                  <div>
                    <p className="font-mono text-[11px] text-subtle">delta vs rail</p>
                    <p className="font-mono text-lg tabular-nums">{fmtPct(cumulativeNowFraction - currentClock, 3)}</p>
                  </div>
                </div>
              </div>

              <button
                type="button"
                disabled={actualNow <= 0 || cumulativeNowAmount > safeCapital + 1e-8}
                onClick={recordPoint}
                className="min-h-11 rounded-md border border-accent/60 bg-accent px-4 text-sm font-medium text-accent-fg disabled:cursor-not-allowed disabled:opacity-40"
              >
                記錄今次實際投入
              </button>

              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={copyLedger}
                  className="min-h-11 rounded-md border border-line px-3 text-xs text-muted hover:text-fg"
                >
                  {copied ? "COPIED" : "COPY LEDGER"}
                </button>
                <button
                  type="button"
                  onClick={clearLocal}
                  className="min-h-11 rounded-md border border-line px-3 text-xs text-subtle hover:text-fg"
                >
                  CLEAR LOCAL
                </button>
              </div>
            </div>
          </div>

          <LedgerTable entries={ledger} capital={safeCapital} startingDeployed={startingDeployed} />
        </Panel>

        <div className="grid gap-4 lg:grid-cols-2">
          <Panel kicker="CURRENT REFERENCE" title="三尺度現在的基準位置">
            <div className="grid gap-2">
              {(snapshot.current.perScale ?? []).map((s) => (
                <div key={s.scaleYears} className="grid grid-cols-[70px_1fr_auto] items-center gap-3 rounded-md border border-line px-3 py-2">
                  <span className="font-mono text-sm">{s.scaleYears}Y</span>
                  <div className="h-1.5 overflow-hidden rounded-full bg-elevated">
                    <div className="h-full bg-accent" style={{ width: pctWidth(s.target) }} />
                  </div>
                  <span className="font-mono text-xs tabular-nums text-muted">{fmtPct(s.target, 2)}</span>
                </div>
              ))}
            </div>
          </Panel>

          <Panel kicker="SEMANTIC LOCK" title="監視層同資金層分開">
            <div className="grid gap-2 text-sm text-muted">
              <p>Hard clock rail = month 0 = 0%；第 n 月（畫面 1..120）最低累積投入 = n / 120。</p>
              <p>Rule corridor = rail 以上至 100%；低於 rail 直接標 BELOW_CLOCK。</p>
              <p>Mutual-chase = 20Y / 30Y / 50Y 的 response geometry，暫時只監視。</p>
              <p>QQQ = observed outcome；NDX / NASDAQ Composite = proxy state channels。</p>
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              <Badge tone="pass">RESEARCH-ONLY</Badge>
              <Badge tone="lock">NO GUARANTEED BREAK-EVEN</Badge>
              <Badge tone={composite?.topology.state === "CONVERGENT" ? "pass" : "fragile"}>
                NASDAQCOM {composite?.topology.state ?? "THIN"}
              </Badge>
            </div>
          </Panel>
        </div>
      </div>
    </Shell>
  );
}

function validLedgerEntry(value: unknown): value is LedgerEntry {
  if (!value || typeof value !== "object") return false;
  const x = value as Partial<LedgerEntry>;
  return (
    typeof x.id === "string" &&
    typeof x.recordedAt === "string" &&
    typeof x.asOf === "string" &&
    Number.isFinite(x.month) &&
    Number.isFinite(x.amount) &&
    x.month >= 0 &&
    x.month <= 119
  );
}

function clockTarget(month: number) {
  return Math.min(1, (month + 1) / 120);
}

function statusFor(fraction: number, clock: number, amount: number, capital: number): EntryStatus {
  if (amount > capital + 1e-8) return "OVER_CAPITAL";
  if (fraction < clock - 0.005) return "BELOW_CLOCK";
  if (fraction > clock + 0.005) return "AHEAD";
  return "ON_CLOCK";
}

function buildCapitalPoints(
  entries: LedgerEntry[],
  startingDeployed: number,
  capital: number,
  preview: { month: number; cumulativeAmount: number },
) {
  const sorted = [...entries].sort(
    (a, b) => a.month - b.month || a.recordedAt.localeCompare(b.recordedAt),
  );
  let cumulative = Math.max(0, startingDeployed);
  const points: Array<{ month: number; fraction: number; preview?: boolean }> = [];

  for (const entry of sorted) {
    cumulative += Math.max(0, entry.amount);
    points.push({
      month: entry.month,
      fraction: cumulative / Math.max(1, capital),
    });
  }

  points.push({
    month: preview.month,
    fraction: preview.cumulativeAmount / Math.max(1, capital),
    preview: true,
  });

  return points.sort(
    (a, b) => a.month - b.month || Number(Boolean(a.preview)) - Number(Boolean(b.preview)),
  );
}

function leaderHandoff(leaders: Array<number | null>) {
  for (let i = 1; i < leaders.length; i++) {
    const prev = leaders[i - 1];
    const next = leaders[i];
    if (prev != null && next != null && prev !== next) {
      return { from: prev, to: next, at: i * 0.05 };
    }
  }
  return null;
}

function pctWidth(value: number | null | undefined) {
  const x = Math.max(0, Math.min(1, Number(value) || 0));
  return x * 100 + "%";
}

function EmptyState({ text }: { text: string }) {
  return <div className="rounded-md border border-dashed border-line p-4 text-sm text-muted">{text}</div>;
}

function MoneyField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
}) {
  return (
    <label className="grid gap-1.5 text-sm">
      <span className="font-mono text-xs text-subtle">{label}</span>
      <span className="flex min-h-11 items-center overflow-hidden rounded-md border border-line bg-elevated focus-within:border-accent">
        <span className="px-3 text-muted">$</span>
        <input
          type="number"
          min={0}
          step="0.01"
          inputMode="decimal"
          value={value}
          onChange={(e) => onChange(Number(e.target.value) || 0)}
          className="min-w-0 flex-1 bg-transparent px-2 pr-3 font-mono tabular-nums outline-none"
        />
      </span>
    </label>
  );
}

function NumberField({
  label,
  unit,
  value,
  onChange,
  min,
  max,
  step,
}: {
  label: string;
  unit: string;
  value: number;
  onChange: (value: number) => void;
  min: number;
  max: number;
  step: number;
}) {
  return (
    <label className="grid gap-1.5 text-sm">
      <span className="font-mono text-xs text-subtle">{label}</span>
      <span className="flex min-h-11 items-center overflow-hidden rounded-md border border-line bg-elevated focus-within:border-accent">
        <input
          type="number"
          min={min}
          max={max}
          step={step}
          inputMode="numeric"
          value={value}
          onChange={(e) => onChange(Number(e.target.value) || 0)}
          className="min-w-0 flex-1 bg-transparent px-3 font-mono tabular-nums outline-none"
        />
        <span className="border-l border-line px-3 text-muted">{unit}</span>
      </span>
    </label>
  );
}

function MetricCard({
  kicker,
  title,
  detail,
}: {
  kicker: string;
  title: string;
  detail: string;
}) {
  return (
    <div className="rounded-xl border border-line bg-surface p-4">
      <p className="font-mono text-xs tracking-[0.14em] text-subtle">{kicker}</p>
      <p className="mt-1 text-xl font-medium">{title}</p>
      <p className="mt-1 font-mono text-xs text-muted">{detail}</p>
    </div>
  );
}

function ResponseChart({
  curves,
  domain,
  currentX,
  handoff,
}: {
  curves: Array<{ scale: number; xs: number[]; ys: number[] }>;
  domain: number[];
  currentX: number;
  handoff: { from: number; to: number; at: number } | null;
}) {
  if (!curves.length) return <EmptyState text="沒有 response curve 資料。" />;

  const W = 1000, H = 380, L = 64, R = 24, T = 24, B = 48;
  const plotW = W - L - R, plotH = H - T - B;
  const x = (v: number) => L + Math.max(0, Math.min(1, v)) * plotW;
  const y = (v: number) =>
    T + (domain[1] - v) / Math.max(0.0001, domain[1] - domain[0]) * plotH;
  const palette = ["var(--color-accent)", "var(--color-fragile)", "var(--color-muted)"];
  const top = curves[0].xs.map((_, i) =>
    Math.max(...curves.map((c) => Number(c.ys[i]) || domain[0])),
  );
  const bottom = curves[0].xs.map((_, i) =>
    Math.min(...curves.map((c) => Number(c.ys[i]) || domain[0])),
  );
  const band = curves[0].xs
    .map((v, i) => [x(v), y(top[i])])
    .concat(
      curves[0].xs
        .slice()
        .reverse()
        .map((v, i) => [x(v), y(bottom[bottom.length - 1 - i])]),
    )
    .map((p) => p.join(","))
    .join(" ");

  return (
    <svg viewBox={"0 0 " + W + " " + H} className="min-w-[760px] w-full" role="img" aria-label="Mutual chase response envelope">
      <rect x={L} y={T} width={plotW} height={plotH} fill="var(--color-elevated)" opacity="0.45" rx="8" />
      {[1, 1.5, 2, 2.5, 3].filter((v) => v <= domain[1] + 0.01).map((v) => (
        <g key={v}>
          <line x1={L} x2={W - R} y1={y(v)} y2={y(v)} stroke="var(--color-line)" />
          <text x={L - 10} y={y(v) + 4} textAnchor="end" fill="var(--color-subtle)" fontSize="11">{v.toFixed(1)}×</text>
        </g>
      ))}
      <polygon points={band} fill="var(--color-accent)" opacity="0.08" />
      <line x1={x(currentX)} x2={x(currentX)} y1={T} y2={T + plotH} stroke="var(--color-fg)" strokeDasharray="4 4" opacity="0.8" />
      <text x={Math.min(W - 120, x(currentX) + 6)} y={T + 14} fill="var(--color-fg)" fontSize="11">NOW {fmtPct(currentX, 2)}</text>
      {handoff ? (
        <>
          <line x1={x(handoff.at)} x2={x(handoff.at)} y1={T} y2={T + plotH} stroke="var(--color-fragile)" strokeDasharray="2 3" opacity="0.9" />
          <text x={Math.min(W - 120, x(handoff.at) + 6)} y={H - 18} fill="var(--color-fragile)" fontSize="11">
            {handoff.from}Y → {handoff.to}Y
          </text>
        </>
      ) : null}
      {curves.map((curve, idx) => (
        <polyline
          key={curve.scale}
          points={curve.xs.map((v, i) => x(v) + "," + y(curve.ys[i])).join(" ")}
          fill="none"
          stroke={palette[idx] ?? "var(--color-fg)"}
          strokeWidth={idx === 0 ? 3 : 2}
          strokeLinejoin="round"
          strokeLinecap="round"
        />
      ))}
      {[0, 0.25, 0.5, 0.75, 1].map((v) => (
        <text key={v} x={x(v)} y={H - 22} textAnchor="middle" fill="var(--color-subtle)" fontSize="11">{Math.round(v * 100)}%</text>
      ))}
      <text x={L} y={H - 4} fill="var(--color-subtle)" fontSize="11">cumulative deployment / response cross-section</text>
    </svg>
  );
}

function CapitalChart({
  points,
  currentClock,
  currentStatus,
}: {
  points: Array<{ month: number; fraction: number; preview?: boolean }>;
  currentClock: number;
  currentStatus: EntryStatus;
}) {
  const W = 1000, H = 340, L = 58, R = 24, T = 20, B = 44;
  const plotW = W - L - R, plotH = H - T - B;
  const x = (month: number) => L + Math.max(0, Math.min(120, month)) / 120 * plotW;
  const y = (fraction: number) => T + (1 - Math.max(0, Math.min(1, fraction))) * plotH;

  // Axis month 0 = 0%, month 120 = 100%. Operator month n (1..120) sits at n/120.
  const rail = Array.from({ length: 121 }, (_, m) => m / 120);
  // Persisted month is a 0-based index; plot it on the operator month (index + 1).
  const xIndex = (monthIndex: number) => x(monthIndex + 1);
  const corridor = [
    [x(0), y(0)],
    ...rail.map((v, m) => [x(m), y(v)]),
    [x(120), y(1)],
    [x(0), y(1)],
  ].map((p) => p.join(",")).join(" ");

  const actual = points.filter((p) => !p.preview);
  const preview = points.find((p) => p.preview);

  return (
    <svg viewBox={"0 0 " + W + " " + H} className="min-w-[760px] w-full" role="img" aria-label="10 year capital rule corridor">
      <rect x={L} y={T} width={plotW} height={plotH} fill="var(--color-elevated)" opacity="0.45" rx="8" />
      <polygon points={corridor} fill="var(--color-pass)" opacity="0.06" />
      {[0, 0.25, 0.5, 0.75, 1].map((v) => (
        <g key={v}>
          <line x1={L} x2={W - R} y1={y(v)} y2={y(v)} stroke="var(--color-line)" />
          <text x={L - 8} y={y(v) + 4} textAnchor="end" fill="var(--color-subtle)" fontSize="11">{fmtPct(v, 0)}</text>
        </g>
      ))}
      <polyline
        points={rail.map((v, m) => x(m) + "," + y(v)).join(" ")}
        fill="none"
        stroke="var(--color-fragile)"
        strokeWidth="3"
        strokeDasharray="5 5"
      />
      {actual.length ? (
        <>
          <polyline
            points={actual.map((p) => xIndex(p.month) + "," + y(p.fraction)).join(" ")}
            fill="none"
            stroke="var(--color-fg)"
            strokeWidth="3"
            strokeLinejoin="round"
            strokeLinecap="round"
          />
          {actual.map((p, index) => (
            <circle key={String(p.month) + "-" + String(index)} cx={xIndex(p.month)} cy={y(p.fraction)} r="5" fill="var(--color-fg)" />
          ))}
        </>
      ) : null}
      {preview ? (
        <>
          <line x1={xIndex(preview.month)} x2={xIndex(preview.month)} y1={T} y2={T + plotH} stroke="var(--color-accent)" strokeDasharray="2 3" opacity="0.7" />
          <circle cx={xIndex(preview.month)} cy={y(preview.fraction)} r="7" fill="var(--color-accent)" />
          <text x={Math.min(W - 150, xIndex(preview.month) + 8)} y={y(preview.fraction) - 10} fill="var(--color-accent)" fontSize="11">
            PREVIEW · {currentStatus}
          </text>
        </>
      ) : null}
      {[0, 24, 48, 72, 96, 120].map((m) => (
        <text key={m} x={x(m)} y={H - 20} textAnchor="middle" fill="var(--color-subtle)" fontSize="11">{m}m</text>
      ))}
      <text x={L} y={H - 4} fill="var(--color-subtle)" fontSize="11">
        shaded corridor = rule-compliant zone above the hard deadline rail
      </text>
    </svg>
  );
}

function LedgerTable({
  entries,
  capital,
  startingDeployed,
}: {
  entries: LedgerEntry[];
  capital: number;
  startingDeployed: number;
}) {
  if (!entries.length) {
    return (
      <p className="mt-4 rounded-md border border-dashed border-line p-4 text-sm text-muted">
        尚未記錄投入點。你在上面的「Actual cash invested now」輸入數字時，圖表會即時預覽。
      </p>
    );
  }

  const rows = entries
    .slice()
    .sort((a, b) => a.month - b.month || a.recordedAt.localeCompare(b.recordedAt))
    .reduce<Array<{
      entry: LedgerEntry;
      fraction: number;
      clock: number;
      status: EntryStatus;
    }>>((rows, entry) => {
      const prior = rows.at(-1)?.fraction ?? startingDeployed / Math.max(1, capital);
      const fraction = prior + entry.amount / Math.max(1, capital);
      rows.push({
        entry,
        fraction,
        clock: clockTarget(entry.month),
        status: statusFor(fraction, clockTarget(entry.month), fraction * capital, capital),
      });
      return rows;
    }, [])
    .reverse();

  return (
    <div className="mt-4 overflow-x-auto">
      <table className="w-full min-w-[800px] text-left text-sm">
        <thead className="text-xs text-subtle">
          <tr>
            <th className="py-2">month</th>
            <th className="py-2">投入</th>
            <th className="py-2">累積</th>
            <th className="py-2">clock</th>
            <th className="py-2">delta</th>
            <th className="py-2">check</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(({ entry, fraction, clock, status }) => (
            <tr key={entry.id} className="border-t border-line">
              <td className="py-2 font-mono tabular-nums">{entry.month + 1}</td>
              <td className="py-2 font-mono tabular-nums">{fmtUsd(entry.amount, 2)}</td>
              <td className="py-2 font-mono tabular-nums">{fmtPct(fraction, 2)}</td>
              <td className="py-2 font-mono tabular-nums">{fmtPct(clock, 2)}</td>
              <td className="py-2 font-mono tabular-nums">{fmtPct(fraction - clock, 2)}</td>
              <td className="py-2">
                <Badge tone={status === "BELOW_CLOCK" || status === "OVER_CAPITAL" ? "lock" : status === "AHEAD" ? "fragile" : "pass"}>
                  {status}
                </Badge>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
