import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Panel, Shell } from "@/components/shell";
import {
  actualContributed,
  actualWithdrawn,
  clockTarget,
  createEntry,
  defaultFloorAccount,
  fundingDelta,
  fundingStatus,
  normalizeFloorAccount,
  type FloorAccountState,
  type FloorEntryKind,
} from "@/lib/floor/account";
import { fmtUsd } from "@/lib/utils";

export const Route = createFileRoute("/floor")({ component: Page });

const STORAGE_KEY = "qqq-rolling-floor-product-v1";

function loadState(): FloorAccountState {
  if (typeof window === "undefined") return defaultFloorAccount();
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return raw ? normalizeFloorAccount(JSON.parse(raw)) : defaultFloorAccount();
  } catch {
    return defaultFloorAccount();
  }
}

function saveState(state: FloorAccountState) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function Page() {
  const [state, setState] = useState<FloorAccountState>(() => defaultFloorAccount());
  const [hydrated, setHydrated] = useState(false);
  const [contributionAmount, setContributionAmount] = useState("");
  const [withdrawalAmount, setWithdrawalAmount] = useState("");
  const [navInput, setNavInput] = useState("");
  const [planInput, setPlanInput] = useState("");
  const [monthInput, setMonthInput] = useState("0");
  const [note, setNote] = useState("");
  const [plannedContributionAmount, setPlannedContributionAmount] = useState("");
  const [plannedContributionMonth, setPlannedContributionMonth] = useState("1");
  const [plannedWithdrawalAmount, setPlannedWithdrawalAmount] = useState("");
  const [plannedWithdrawalMonth, setPlannedWithdrawalMonth] = useState("1");

  useEffect(() => {
    const loaded = loadState();
    setState(loaded);
    setPlanInput(String(loaded.plannedPrincipal));
    setMonthInput(String(loaded.cycleMonth));
    setNavInput(String(loaded.nav));
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (hydrated) saveState(state);
  }, [hydrated, state]);

  const contributed = useMemo(() => actualContributed(state.entries), [state.entries]);
  const withdrawn = useMemo(() => actualWithdrawn(state.entries), [state.entries]);
  const clock = clockTarget(state.plannedPrincipal, state.cycleMonth);
  const delta = fundingDelta(state.plannedPrincipal, state.cycleMonth, state.entries);
  const status = fundingStatus(delta);
  const remainingPrincipal = Math.max(0, state.plannedPrincipal - contributed);
  const monthsRemaining = Math.max(0, 120 - state.cycleMonth);
  const averageFutureContribution =
    monthsRemaining > 0 ? remainingPrincipal / monthsRemaining : remainingPrincipal;
  const plannedContribution = Math.max(0, Number(plannedContributionAmount) || 0);
  const plannedMonth = Math.max(
    state.cycleMonth,
    Math.min(120, Math.round(Number(plannedContributionMonth) || state.cycleMonth)),
  );
  const projectedContributed = contributed + plannedContribution;
  const projectedClock = clockTarget(state.plannedPrincipal, plannedMonth);
  const projectedDelta = projectedContributed - projectedClock;
  const projectedRemaining = Math.max(0, state.plannedPrincipal - projectedContributed);
  const projectedMonthsRemaining = Math.max(0, 120 - plannedMonth);
  const projectedAverageFutureContribution =
    projectedMonthsRemaining > 0 ? projectedRemaining / projectedMonthsRemaining : projectedRemaining;

  const plannedWithdrawal = Math.max(0, Number(plannedWithdrawalAmount) || 0);
  const plannedWithdrawalMonthValue = Math.max(
    state.cycleMonth,
    Math.min(120, Math.round(Number(plannedWithdrawalMonth) || state.cycleMonth)),
  );

  function commit(updater: (current: FloorAccountState) => FloorAccountState) {
    setState((current) => updater(current));
  }

  function record(kind: FloorEntryKind) {
    const raw = kind === "CONTRIBUTION" ? contributionAmount : withdrawalAmount;
    const amount = Number(raw);
    if (!(amount > 0) || !Number.isFinite(amount)) return;

    const entry = createEntry(kind, amount, state.cycleMonth, new Date().toISOString(), note);
    commit((current) => ({ ...current, entries: [...current.entries, entry] }));

    if (kind === "CONTRIBUTION") setContributionAmount("");
    else setWithdrawalAmount("");
    setNote("");
  }

  function applyPlan() {
    if (state.entries.length > 0) return;
    const next = Number(planInput);
    if (!(next > 0) || !Number.isFinite(next)) return;
    commit((current) => ({ ...current, plannedPrincipal: next }));
  }

  function applyMonth() {
    const next = Number(monthInput);
    if (!(next >= 0) || !Number.isFinite(next)) return;
    commit((current) => ({
      ...current,
      cycleMonth: Math.max(0, Math.min(120, Math.round(next))),
    }));
  }

  function applyNav() {
    const next = Number(navInput);
    if (!(next >= 0) || !Number.isFinite(next)) return;
    commit((current) => ({ ...current, nav: next }));
  }

  const statusText =
    status === "AHEAD" ? "超前" : status === "BEHIND" ? "落後" : "時鐘內";
  const statusTone = status === "BEHIND" ? "lock" : status === "AHEAD" ? "pass" : "mute";

  return (
    <Shell>
      <div className="grid gap-4">
        <Panel
          kicker="10Y CAPITAL FLOOR · PRODUCT"
          title="只看四個數：時鐘、已掏、帳面、超前 / 落後"
        >
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Metric label="CLOCK TARGET" value={fmtUsd(clock)} note={"Month " + state.cycleMonth + " / 120"} />
            <Metric label="ACTUAL CONTRIBUTED" value={fmtUsd(contributed)} note="只計實際外部供款" />
            <Metric label="ACCOUNT NAV" value={fmtUsd(state.nav)} note="帳面值，獨立記錄" />
            <Metric
              label="ACTUAL − CLOCK"
              value={(delta >= 0 ? "+" : "") + fmtUsd(delta)}
              note={statusText + " · 唔看 NAV"}
              tone={statusTone}
            />
          </div>

          <div className="mt-4 rounded-md border border-line bg-elevated p-3 text-sm text-muted">
            <div className="font-mono text-xs text-subtle">FLOOR FORMULA</div>
            <div className="mt-1 font-mono text-sm text-fg">Cₜ = B × Clockₜ</div>
            <div className="mt-1">
              Funding status = Actual contributed − Cₜ。帳面 NAV 不參與超前 / 落後判定。
            </div>
          </div>
        </Panel>

        <Panel kicker="CAPITAL JOURNEY · DYNAMIC PACE" title="線是參考，路徑可以變">
          <p className="max-w-4xl text-sm leading-relaxed text-muted">
            CLOCK 只畫出「到十年終點時要完成 100% B」的時間骨架；它不是每月固定配額。
            你可以提早掏、延後掏、一次掏多一點或分幾次掏，App 只把實際路徑與 CLOCK 擺在一起。
          </p>

          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <PaceMetric label="CLOCK POSITION" value={fmtUsd(clock)} note={(state.cycleMonth / 120 * 100).toFixed(2) + "% of B"} />
            <PaceMetric label="REMAINING TO 100% B" value={fmtUsd(remainingPrincipal)} note="未掏的正式本金" />
            <PaceMetric label="MONTHS LEFT" value={String(monthsRemaining)} note="到 month 120" />
            <PaceMetric label="AVERAGE FUTURE PACE" value={fmtUsd(averageFutureContribution)} note="只係算術參考，不是指令" />
          </div>

          <div className="mt-4 overflow-x-auto rounded-lg border border-line bg-elevated p-3">
            <CapitalJourneyChart
              plannedPrincipal={state.plannedPrincipal}
              currentMonth={state.cycleMonth}
              entries={state.entries}
              plannedContribution={
                plannedContribution > 0
                  ? { month: plannedMonth, amount: plannedContribution }
                  : null
              }
            />
          </div>

          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            <Panel kicker="NEXT CONTRIBUTION · MANUAL PREVIEW" title="試下一次：幾時加、加幾多">
              <div className="grid gap-3 sm:grid-cols-2">
                <Field label="Planned month" value={plannedContributionMonth} onChange={setPlannedContributionMonth} prefix="M" />
                <Field label="Planned contribution" value={plannedContributionAmount} onChange={setPlannedContributionAmount} prefix="$" />
              </div>
              <div className="mt-3 grid gap-3 sm:grid-cols-3">
                <PaceMetric label="PROJECTED CONTRIBUTED" value={fmtUsd(projectedContributed)} note={"after month " + plannedMonth} />
                <PaceMetric label="PROJECTED Δ vs CLOCK" value={(projectedDelta >= 0 ? "+" : "") + fmtUsd(projectedDelta)} note="仍然只看 funding path" />
                <PaceMetric label="NEW AVG FUTURE PACE" value={fmtUsd(projectedAverageFutureContribution)} note="完成餘下 B 的平均值" />
              </div>
              <p className="mt-3 text-xs text-subtle">
                呢個係預覽，不會寫入 ledger；按正式「記錄供款」先會變成 Actual contributed。
              </p>
            </Panel>

            <Panel kicker="WITHDRAWAL · MANUAL PREVIEW" title="試抽取，但唔碰 Floor">
              <div className="grid gap-3 sm:grid-cols-2">
                <Field label="Planned withdrawal month" value={plannedWithdrawalMonth} onChange={setPlannedWithdrawalMonth} prefix="M" />
                <Field label="Planned withdrawal" value={plannedWithdrawalAmount} onChange={setPlannedWithdrawalAmount} prefix="$" />
              </div>
              <div className="mt-3 grid gap-3 sm:grid-cols-2">
                <PaceMetric label="PLANNED CASH OUT" value={fmtUsd(plannedWithdrawal)} note={"journal month " + plannedWithdrawalMonthValue} />
                <PaceMetric label="CUMULATIVE WITHDRAWN" value={fmtUsd(withdrawn)} note="只計已記錄抽取" />
              </div>
              <p className="mt-3 text-xs text-subtle">
                這只是 cashflow 預覽。它不判斷可否抽、不自動執行、不減 Actual、不加回 Floor NAV。
              </p>
            </Panel>
          </div>
        </Panel>

        <div className="grid gap-4 lg:grid-cols-2">
          <Panel kicker="PLAN CLOCK" title="設定 B 與目前週期月">
            <div className="grid gap-3 sm:grid-cols-2">
              <Field
                label={state.entries.length ? "Planned principal B · LOCKED" : "Planned principal B"}
                value={planInput}
                onChange={setPlanInput}
                prefix="$"
                disabled={state.entries.length > 0}
              />
              <Field label="Cycle month (0–120)" value={monthInput} onChange={setMonthInput} />
            </div>
            <div className="mt-3 flex gap-2">
              <ActionButton onClick={applyPlan} disabled={state.entries.length > 0}>更新 B</ActionButton>
              <ActionButton onClick={applyMonth}>更新月份</ActionButton>
            </div>
            <p className="mt-3 text-xs text-subtle">
              B 是 Planned Principal；第一筆實際供款或抽取記錄後鎖定。時鐘不會自動產生 BUY、SELL、少掏或加掏指令。
            </p>
          </Panel>

          <Panel kicker="ACCOUNT NAV" title="記錄實際帳面值">
            <Field label="Current account NAV" value={navInput} onChange={setNavInput} prefix="$" />
            <div className="mt-3">
              <ActionButton onClick={applyNav}>更新帳面</ActionButton>
            </div>
            <p className="mt-3 text-xs text-subtle">
              NAV 只作帳面記錄；它不會改變已掏本金，也不會改變 CLOCK funding status。
            </p>
          </Panel>
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          <Panel kicker="ACTUAL CONTRIBUTION LEDGER" title="記錄真正掏出的本金">
            <EntryForm
              label="這次實際供款"
              value={contributionAmount}
              onChange={setContributionAmount}
              note={note}
              onNoteChange={setNote}
              onSubmit={() => record("CONTRIBUTION")}
              button="記錄供款"
            />
            <Ledger entries={state.entries.filter((x) => x.kind === "CONTRIBUTION")} />
          </Panel>

          <Panel kicker="WITHDRAWAL LEDGER · OFF" title="抽取只記帳，不回灌 Floor">
            <EntryForm
              label="這次實際抽取"
              value={withdrawalAmount}
              onChange={setWithdrawalAmount}
              note={note}
              onNoteChange={setNote}
              onSubmit={() => record("WITHDRAWAL")}
              button="記錄抽取"
            />
            <div className="mt-3 rounded-md border border-lock/40 bg-elevated p-3 text-sm">
              <div className="flex items-center gap-2">
                <Badge tone="lock">WITHDRAWAL OFF</Badge>
                <span className="text-muted">目前 App 不會自動執行任何抽取規則。</span>
              </div>
              <div className="mt-2 font-mono text-sm">
                Cumulative withdrawn: {fmtUsd(withdrawn)}
              </div>
              <div className="mt-1 text-xs text-subtle">
                抽取不減 Actual contributed，不加回 Floor NAV；它只存在於獨立抽取帳。
              </div>
            </div>
            <Ledger entries={state.entries.filter((x) => x.kind === "WITHDRAWAL")} />
          </Panel>
        </div>

        <Panel kicker="CAPITAL JOURNEY · THESIS ONLY" title="原始思想：賺就放點，跌就溝">
          <div className="grid gap-3 md:grid-cols-3">
            <ThesisBlock
              title="不猜十年終點"
              body="先拉一條 10Y funding line：Cₜ = B × Clockₜ。終點目標仍然是 100% B；App 不預測十年後會賺多少。"
            />
            <ThesisBlock
              title="賺就放點"
              body="盈利抽取只是一個收放研究命題。真正發生的抽取，才進獨立 Withdrawal ledger；抽取規則目前 OFF。"
            />
            <ThesisBlock
              title="跌就溝"
              body="只保留作未驗證的收放命題。App 不會因下跌自動增加部署、加掏本金或產生 BUY 指令。"
            />
          </div>
          <div className="mt-4 rounded-md border border-line bg-elevated p-3">
            <div className="font-mono text-xs text-subtle">RESEARCH OBSERVATION · NO FUNDING / DEPLOYMENT AUTHORITY</div>
            <div className="mt-2 grid gap-3 md:grid-cols-3">
              <ResearchRule title="20Y" body="觀察慢牛 / 慢跌形態；不改 Funding Status。" />
              <ResearchRule title="30Y" body="觀察長週期位置；不改 Actual、NAV 或 Clock。" />
              <ResearchRule title="50Y" body="只作更長尺度研究背景；沒有資金權。" />
            </div>
            <p className="mt-3 text-xs text-subtle">
              「賺就放點、跌就溝」仍是策略原思想，但目前只是 thesis，不是 controller。
            </p>
          </div>
        </Panel>

        <Panel kicker="RESEARCH FIREWALL" title="研究資料永遠不產生資金指令">
          <div className="mb-3">
            <Link
              to="/floor-research"
              className="text-sm text-accent underline decoration-dotted underline-offset-4"
            >
              開啟 Research evidence page →
            </Link>
          </div>
          <div className="grid gap-3 md:grid-cols-3">
            <ResearchRule title="20Y / 30Y / 50Y" body="只放 Research 圖，不擁有 funding 權。" />
            <ResearchRule title="Adaptive" body="歷史對照資料；不會改主畫面的少掏狀態。" />
            <ResearchRule title="α = 0.50" body="固定診斷結果；不重跑、不進正式控制器。" />
          </div>
          <p className="mt-3 text-xs text-subtle">
            歷史 rolling windows 彼此重疊；觀察到的 0% failure 只是診斷，不是保證。
          </p>
        </Panel>
      </div>
    </Shell>
  );
}

function PaceMetric({ label, value, note }: { label: string; value: string; note: string }) {
  return (
    <div className="rounded-md border border-line bg-elevated p-3">
      <div className="text-xs text-subtle">{label}</div>
      <div className="mt-1 font-mono text-lg tabular-nums">{value}</div>
      <div className="mt-1 text-xs text-muted">{note}</div>
    </div>
  );
}

function CapitalJourneyChart({
  plannedPrincipal,
  currentMonth,
  entries,
  plannedContribution,
}: {
  plannedPrincipal: number;
  currentMonth: number;
  entries: FloorAccountState["entries"];
  plannedContribution: { month: number; amount: number } | null;
}) {
  const W = 1040;
  const H = 360;
  const L = 64;
  const R = 28;
  const T = 24;
  const B = 52;
  const plotW = W - L - R;
  const plotH = H - T - B;
  const safePrincipal = Math.max(1, plannedPrincipal);
  const x = (month: number) => L + (Math.max(0, Math.min(120, month)) / 120) * plotW;
  const y = (amount: number) =>
    T + (1 - Math.max(0, Math.min(1, amount / safePrincipal))) * plotH;

  const contributions = entries
    .filter((entry) => entry.kind === "CONTRIBUTION")
    .slice()
    .sort((a, b) => a.cycleMonth - b.cycleMonth || a.recordedAt.localeCompare(b.recordedAt));

  let cumulative = 0;
  const actualPoints = contributions.map((entry) => {
    cumulative += Math.max(0, entry.amount);
    return { month: entry.cycleMonth, amount: cumulative };
  });

  const startActual = actualPoints.length ? [{ month: 0, amount: 0 }, ...actualPoints] : [{ month: 0, amount: 0 }];
  const clockPoints = Array.from({ length: 121 }, (_, month) => ({
    month,
    amount: safePrincipal * (month / 120),
  }));

  const previewPrior = cumulative;
  const previewPoint = plannedContribution
    ? {
        month: Math.max(currentMonth, Math.min(120, plannedContribution.month)),
        amount: previewPrior + plannedContribution.amount,
      }
    : null;

  const maxObserved = Math.max(
    safePrincipal,
    previewPoint?.amount ?? 0,
    cumulative,
    1,
  );
  const previewStatus =
    previewPoint == null
      ? null
      : previewPoint.amount - safePrincipal * (previewPoint.month / 120);

  return (
    <svg viewBox={"0 0 " + W + " " + H} className="min-w-[760px] w-full" role="img" aria-label="Dynamic actual capital path versus 10 year clock reference">
      <rect x={L} y={T} width={plotW} height={plotH} fill="var(--color-surface)" opacity="0.6" rx="8" />
      {[0, 0.25, 0.5, 0.75, 1].map((fraction) => (
        <g key={fraction}>
          <line x1={L} x2={W - R} y1={y(safePrincipal * fraction)} y2={y(safePrincipal * fraction)} stroke="var(--color-line)" />
          <text x={L - 10} y={y(safePrincipal * fraction) + 4} textAnchor="end" fill="var(--color-subtle)" fontSize="11">
            {(fraction * 100).toFixed(0)}%
          </text>
        </g>
      ))}

      <polyline
        points={clockPoints.map((p) => x(p.month) + "," + y(p.amount)).join(" ")}
        fill="none"
        stroke="var(--color-fragile)"
        strokeWidth="3"
        strokeDasharray="6 5"
      />

      {startActual.length > 1 ? (
        <>
          <polyline
            points={startActual.map((p) => x(p.month) + "," + y(Math.min(maxObserved, p.amount))).join(" ")}
            fill="none"
            stroke="var(--color-fg)"
            strokeWidth="3.5"
            strokeLinejoin="round"
            strokeLinecap="round"
          />
          {actualPoints.map((p, index) => (
            <circle key={"actual-" + index} cx={x(p.month)} cy={y(Math.min(maxObserved, p.amount))} r="5" fill="var(--color-fg)" />
          ))}
        </>
      ) : (
        <circle cx={x(0)} cy={y(0)} r="5" fill="var(--color-fg)" />
      )}

      {previewPoint ? (
        <>
          <line x1={x(previewPoint.month)} x2={x(previewPoint.month)} y1={T} y2={T + plotH} stroke="var(--color-accent)" strokeDasharray="3 4" opacity="0.75" />
          <circle cx={x(previewPoint.month)} cy={y(Math.min(maxObserved, previewPoint.amount))} r="7" fill="var(--color-accent)" />
          <text x={Math.min(W - 220, x(previewPoint.month) + 8)} y={Math.max(T + 16, y(Math.min(maxObserved, previewPoint.amount)) - 12)} fill="var(--color-accent)" fontSize="11">
            NEXT · {(previewStatus! >= 0 ? "+" : "") + fmtUsd(previewStatus!)}
          </text>
        </>
      ) : null}

      <line x1={x(currentMonth)} x2={x(currentMonth)} y1={T} y2={T + plotH} stroke="var(--color-fg)" strokeDasharray="2 4" opacity="0.5" />
      <text x={Math.min(W - 120, x(currentMonth) + 7)} y={T + 16} fill="var(--color-fg)" fontSize="11">
        AS-OF M{currentMonth}
      </text>

      {[0, 24, 48, 72, 96, 120].map((month) => (
        <text key={month} x={x(month)} y={H - 24} textAnchor="middle" fill="var(--color-subtle)" fontSize="11">
          M{month}
        </text>
      ))}

      <text x={L} y={H - 5} fill="var(--color-subtle)" fontSize="10">
        - - CLOCK reference · solid ACTUAL contribution path · accent NEXT preview · no market signal authority
      </text>
    </svg>
  );
}

function Metric({
  label,
  value,
  note,
  tone = "mute",
}: {
  label: string;
  value: string;
  note: string;
  tone?: "mute" | "pass" | "lock";
}) {
  return (
    <div className="rounded-lg border border-line bg-elevated p-4">
      <div className="text-xs tracking-wide text-subtle">{label}</div>
      <div className="mt-2 font-mono text-2xl tabular-nums">{value}</div>
      <div className="mt-2">
        <Badge tone={tone}>{note}</Badge>
      </div>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  prefix,
  disabled = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  prefix?: string;
  disabled?: boolean;
}) {
  return (
    <label className="grid gap-1.5 text-sm">
      <span className="text-xs text-subtle">{label}</span>
      <div className="flex items-center rounded-md border border-line bg-elevated px-3 focus-within:border-accent">
        {prefix ? <span className="font-mono text-muted">{prefix}</span> : null}
        <input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          inputMode="decimal"
          disabled={disabled}
          className="min-h-10 w-full bg-transparent px-2 font-mono outline-none disabled:cursor-not-allowed disabled:opacity-50"
        />
      </div>
    </label>
  );
}

function ActionButton({ onClick, children, disabled = false }: { onClick: () => void; children: React.ReactNode; disabled?: boolean }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="min-h-10 rounded-md border border-line bg-elevated px-4 text-sm text-fg transition hover:border-accent hover:bg-surface disabled:cursor-not-allowed disabled:opacity-50"
    >
      {children}
    </button>
  );
}

function EntryForm({
  label,
  value,
  onChange,
  note,
  onNoteChange,
  onSubmit,
  button,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  note: string;
  onNoteChange: (value: string) => void;
  onSubmit: () => void;
  button: string;
}) {
  return (
    <div className="grid gap-3">
      <Field label={label} value={value} onChange={onChange} prefix="$" />
      <Field label="Note（可選）" value={note} onChange={onNoteChange} />
      <ActionButton onClick={onSubmit}>{button}</ActionButton>
    </div>
  );
}

function Ledger({ entries }: { entries: FloorAccountState["entries"] }) {
  if (!entries.length) {
    return <p className="mt-4 text-xs text-subtle">尚未有紀錄。</p>;
  }

  return (
    <div className="mt-4 overflow-x-auto">
      <table className="w-full min-w-[560px] text-left text-xs">
        <thead className="text-subtle">
          <tr>
            <th className="py-2">month</th>
            <th className="py-2">amount</th>
            <th className="py-2">when</th>
            <th className="py-2">note</th>
          </tr>
        </thead>
        <tbody>
          {[...entries].reverse().map((entry) => (
            <tr key={entry.id} className="border-t border-line">
              <td className="py-2 font-mono">{entry.cycleMonth}</td>
              <td className="py-2 font-mono">{fmtUsd(entry.amount)}</td>
              <td className="py-2 font-mono">{new Date(entry.recordedAt).toLocaleString()}</td>
              <td className="py-2 text-muted">{entry.note ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ThesisBlock({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-md border border-line bg-elevated p-3">
      <div className="font-mono text-sm">{title}</div>
      <p className="mt-1 text-xs leading-relaxed text-muted">{body}</p>
    </div>
  );
}

function ResearchRule({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-md border border-line bg-elevated p-3">
      <div className="font-mono text-sm">{title}</div>
      <p className="mt-1 text-xs text-muted">{body}</p>
    </div>
  );
}
