import { createFileRoute } from "@tanstack/react-router";
import { Panel, Shell } from "@/components/shell";
import { Badge } from "@/components/ui/badge";

export const Route = createFileRoute("/strategy")({ component: Page });

const CONSOLE_URL = "http://127.0.0.1:8766/research/strategy_instance_v1/operator_dashboard.html";

function Page() {
  return (
    <Shell>
      <div className="grid gap-4">
        <Panel kicker="LOCKED V22 · OPERATOR BOUNDARY" title="策略器">
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone="pass">STRATEGY ENGINE</Badge>
            <Badge tone="lock">NO BROKER ORDER SUBMISSION</Badge>
            <Badge tone="fragile">LOCAL ONLY</Badge>
          </div>
          <p className="mt-3 max-w-4xl text-sm leading-relaxed text-muted">
            這一頁只把現有的 QQQ Strategy Operator Console 拉回主 App 的可見入口。
            V22 策略仍由原本的 Python runtime 產生 ticket；這裡不複製、不改寫 alpha。
            Operator Console 仍在本機 127.0.0.1:8766，由它讀取 live strategy state、instance state、manual book 與 performance tape。
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <a
              href={CONSOLE_URL}
              target="_blank"
              rel="noreferrer"
              className="min-h-11 rounded-sm border border-accent bg-elevated px-3 py-2 text-sm text-fg"
            >
              開啟獨立策略器 ↗
            </a>
            <span className="self-center font-mono text-xs text-subtle">{CONSOLE_URL}</span>
          </div>
        </Panel>

        <Panel kicker="LIVE OPERATOR CONSOLE" title="策略器畫面">
          <div className="overflow-hidden rounded-lg border border-line bg-black">
            <iframe
              title="QQQ Strategy Operator Console"
              src={CONSOLE_URL}
              className="h-[1100px] w-full"
            />
          </div>
          <p className="mt-3 text-xs text-subtle">
            需要先在同一部 Windows PC 執行 <code>run_strategy_operator.cmd</code>。
            Console 沒有啟動時，這個框架會顯示本機連線失敗；不會把它誤報成策略失效。
          </p>
        </Panel>
      </div>
    </Shell>
  );
}
