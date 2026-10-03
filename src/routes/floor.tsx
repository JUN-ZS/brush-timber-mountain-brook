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
    if (!(next >= 1) || !Number.isFinite(next)) return;
    commit((current) => ({
      ...current,
      cycleMonth: Math.max(1, Math.min(120, Math.round(next))),
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
              <Field label="Cycle month (1–120)" value={monthInput} onChange={setMonthInput} />
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

function ResearchRule({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-md border border-line bg-elevated p-3">
      <div className="font-mono text-sm">{title}</div>
      <p className="mt-1 text-xs text-muted">{body}</p>
    </div>
  );
}
