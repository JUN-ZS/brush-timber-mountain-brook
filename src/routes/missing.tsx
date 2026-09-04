import { createFileRoute } from "@tanstack/react-router";
import { Panel, Shell } from "@/components/shell";
import { Badge } from "@/components/ui/badge";
import { MISSING_UNIVERSE, TRADED } from "@/lib/pulse/universe";
import { universe } from "@/lib/pulse/bars";

export const Route = createFileRoute("/missing")({ component: Page });

function Page() {
  return (
    <Shell>
      <div className="grid gap-4">
        <Panel kicker="CAPABILITY_MISSING" title="有日線的才進宇宙，沒有的不補造">
          <p className="max-w-2xl text-sm text-muted">
            現在用 Yahoo 調整收盤日線（{universe.source}，asof {universe.asof}）。選擇權鏈、IV surface、買賣差仍全部缺失，所以結構競爭是
            HYPOTHETICAL，Council 預設 NO_TRADE。
          </p>
        </Panel>
        <Panel kicker="OBSERVED" title={`${TRADED.length} 檔有自己的 DAY/WEEK/MONTH 時間線`}>
          <div className="flex flex-wrap gap-2">
            {TRADED.map((s) => (
              <Badge key={s} tone="pass">
                {s} {universe.n[s]}
              </Badge>
            ))}
          </div>
        </Panel>
        <Panel kicker="NOT IN PANEL" title={`${MISSING_UNIVERSE.length} 檔未下載`}>
          <div className="flex flex-wrap gap-2">
            {MISSING_UNIVERSE.map((s) => (
              <Badge key={s} tone="missing">
                {s}
              </Badge>
            ))}
          </div>
        </Panel>
      </div>
    </Shell>
  );
}
