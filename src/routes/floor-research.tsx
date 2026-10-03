import { createFileRoute } from "@tanstack/react-router";
import { Badge } from "@/components/ui/badge";
import { Panel, Shell } from "@/components/shell";
import research from "@/data/rolling_floor_research_snapshot.json";

export const Route = createFileRoute("/floor-research")({ component: Page });

const x = research;

function Page() {
  return (
    <Shell>
      <div className="grid gap-4">
        <Panel kicker="RESEARCH ONLY · NO FUNDING AUTHORITY" title="10Y Floor 研究證據">
          <div className="flex flex-wrap gap-2">
            <Badge tone="lock">NOT A CONTROLLER</Badge>
            <Badge tone="mute">153 OVERLAPPING WINDOWS</Badge>
            <Badge tone="mute">α FIXED 0.50</Badge>
          </div>
          <p className="mt-3 max-w-4xl text-sm leading-relaxed text-muted">
            呢頁只保存已跑過的研究診斷。任何一項結果都不會改變主畫面的 CLOCK、Actual、NAV 或 Funding Status。
          </p>
        </Panel>

        <Panel kicker="ORIGINAL THESIS · NOT A RULE" title="為甚麼有這條線：賺就放點，跌就溝">
          <p className="max-w-4xl text-sm leading-relaxed text-muted">
            原思想不是猜十年終點，而是用中間的 10Y CLOCK 當本金骨架：Cₜ = B × t/120，終點仍然是 100% B。
            「賺就放點、跌就溝」只描述一個尚未驗證的收放問題；研究未通過之前，App 不會把它變成部署、少掏、加掏或 BUY/SELL 指令。
          </p>
          <div className="mt-4 grid gap-3 md:grid-cols-3">
            <Rule title="20Y / 30Y / 50Y" body="研究觀察層；無 funding authority，亦不改 Floor。" />
            <Rule title="67.40%" body="歷史 Adaptive 診斷平均，不是本版 10Y 計畫需要投入的百分比。" />
            <Rule title="α = 0.50" body="已做 isolated diagnostic；有 withdrawal 不代表抽完後 Floor 仍在。" />
          </div>
        </Panel>

        <Panel kicker="FORMAL FLOOR BASELINE" title="CLOCK 不抽取">
          <div className="grid gap-3 md:grid-cols-2">
            <Stat label="CLOCK Q05 terminal / B" value={x.floor.clockQ05Terminal.toFixed(4) + "×"} />
            <Stat label="CLOCK principal failure" value={(x.floor.clockPrincipalFailureRate * 100).toFixed(1) + "%"} />
          </div>
          <p className="mt-3 text-xs text-subtle">
            這個 0% 只代表本次 153 個重疊 rolling windows 的歷史診斷；不是未來保證。
          </p>
        </Panel>

        <Panel kicker="ADAPTIVE SECONDARY · FAILED COMPOUND" title="Adaptive funding 對照">
          <div className="grid gap-3 md:grid-cols-3">
            <Stat label="Q05 terminal / B" value={x.adaptiveFunding.q05Terminal.toFixed(4) + "×"} />
            <Stat label="Principal failure" value={(x.adaptiveFunding.principalFailureRate * 100).toFixed(1) + "%"} />
            <Stat label="Mean contributed / B" value={(x.adaptiveFunding.meanTotalContributedRatio * 100).toFixed(2) + "%"} />
          </div>
          <p className="mt-3 text-xs text-subtle">
            研究結論：少掏外部本金的 Adaptive 只作失敗對照；App 不會因此建議少掏。
          </p>
        </Panel>

        <Panel kicker="ISOLATED WITHDRAWAL · FIXED BEFORE REPLAY" title="CLOCK + α=0.50 withdrawal">
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
            <Stat label="Mean Δ NAV / B" value={x.isolatedAlpha050.deltaNavTerminal.toFixed(4) + "×"} />
            <Stat label="Mean Δ net wealth / B" value={x.isolatedAlpha050.deltaNetEconomicWealth.toFixed(4) + "×"} />
            <Stat label="Principal failure" value={(x.isolatedAlpha050.principalFailureRate * 100).toFixed(2) + "%"} />
            <Stat label="Q05 terminal / B" value={x.isolatedAlpha050.q05Terminal.toFixed(4) + "×"} />
          </div>
          <div className="mt-4 rounded-md border border-lock/40 bg-elevated p-3 text-sm">
            <div className="font-mono">Wₜ = 0.50 × max(0, NAVₜ − B)</div>
            <div className="mt-1 text-muted">
              Mean cumulative withdrawal = {(x.isolatedAlpha050.meanTotalWithdrawnRatio * 100).toFixed(2)}% of B.
              Same-start CLOCK Q05 = {x.isolatedAlpha050.baselineQ05Terminal.toFixed(4)}× B.
            </div>
            <div className="mt-2">
              <Badge tone="lock">DIAGNOSTIC FAILED</Badge>
            </div>
          </div>
        </Panel>

        <Panel kicker="LEGACY COUNTEREXAMPLE" title="完整抽光（早期 Cₜ-relative sweep）">
          <div className="grid gap-3 md:grid-cols-3">
            <Stat label="Principal failure" value={(x.legacyFullSweep.principalFailureRate * 100).toFixed(2) + "%"} />
            <Stat label="Q05 terminal / B" value={x.legacyFullSweep.q05Terminal.toFixed(4) + "×"} />
            <Stat label="Mean net economic wealth / B" value={x.legacyFullSweep.meanNetEconomicWealth.toFixed(4) + "×"} />
          </div>
          <p className="mt-3 text-xs text-subtle">
            只保存作歷史 counterexample；唔係產品規則，亦唔係 withdrawal alpha 的參數搜尋。
          </p>
        </Panel>

        <Panel kicker="FIREWALL" title="研究層不會生成任何操作建議">
          <div className="grid gap-3 md:grid-cols-3">
            <Rule title="No BUY / HOLD" body="Research 不會寫入主畫面的操作狀態。" />
            <Rule title="No SELL" body="Withdrawal ledger 與 Funding status 完全分開。" />
            <Rule title="No alpha rerun" body="App 不會重跑 α；新 alpha 必須先註冊，再另做研究。" />
          </div>
        </Panel>
      </div>
    </Shell>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-line bg-elevated p-3">
      <div className="text-xs text-subtle">{label}</div>
      <div className="mt-1 font-mono text-lg tabular-nums">{value}</div>
    </div>
  );
}

function Rule({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-md border border-line bg-elevated p-3">
      <div className="font-mono text-sm">{title}</div>
      <div className="mt-1 text-xs text-muted">{body}</div>
    </div>
  );
}
