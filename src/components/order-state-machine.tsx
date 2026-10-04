import { Badge } from "@/components/ui/badge";
import { Panel } from "@/components/shell";
import { fmtPct, fmtUsd } from "@/lib/utils";
import {
  activePaperOrders,
  canFillOrder,
  nextRungLabel,
  paperEconomicWealth,
  type OrderMachineState,
  type PaperOrder,
} from "@/lib/floor/order-machine";

function statusTone(status: PaperOrder["status"]) {
  if (status === "TOUCHED") return "fragile" as const;
  if (status === "FILLED") return "pass" as const;
  if (status === "ARMED") return "mute" as const;
  return "lock" as const;
}

function orderActionLabel(order: PaperOrder) {
  if (order.status === "TOUCHED") return "MARK FILLED @ LIMIT";
  if (order.status === "ARMED") return "WAIT PRICE";
  return order.status;
}

function Metric({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="rounded-md border border-line bg-elevated p-3">
      <p className="font-mono text-[11px] tracking-[0.12em] text-subtle">{label}</p>
      <p className="mt-1 font-mono text-xl tabular-nums">{value}</p>
      <p className="mt-1 text-xs text-muted">{detail}</p>
    </div>
  );
}

export function OrderStateMachine({
  state,
  currentPrice,
  target,
  marketDate,
  onFill,
  onCancel,
  onReset,
}: {
  state: OrderMachineState | null;
  currentPrice: number | null;
  target: number;
  marketDate: string | null;
  onFill: (orderId: string) => void;
  onCancel: (orderId: string) => void;
  onReset: () => void;
}) {
  if (!state) {
    return (
      <Panel kicker="ORDER STATE MACHINE / MANUAL LIMIT DESK" title="掛單狀態機：等待建立 Paper Book">
        <div className="rounded-md border border-dashed border-line p-4">
          <p className="text-sm text-muted">
            會以目前 ACCOUNT NAV、10Y target、未投入 B reserve 與今日 QQQ 價格建立獨立 paper book。
            呢層只產生「手動掛單計劃」，唔會連 Futu 或其他券商。
          </p>
          <button
            type="button"
            onClick={onReset}
            disabled={currentPrice == null}
            className="mt-3 min-h-11 rounded-md border border-accent px-4 font-mono text-xs disabled:opacity-40"
          >
            INITIALIZE PAPER BOOK
          </button>
        </div>
      </Panel>
    );
  }

  const active = activePaperOrders(state);
  const buy = active.find((order) => order.side === "BUY") ?? null;
  const sell = active.find((order) => order.side === "SELL") ?? null;
  const buyHistory = state.orders
    .filter((order) => order.side === "BUY" && order.status === "FILLED")
    .slice(-3)
    .reverse();
  const sellHistory = state.orders
    .filter((order) => order.side === "SELL" && order.status === "FILLED")
    .slice(-3)
    .reverse();

  return (
    <Panel kicker="ORDER STATE MACHINE / MANUAL LIMIT DESK" title="掛單狀態機：Price → Touch → Fill → Reserve → Next Level">
      <div className="grid gap-4">
        <div className="rounded-md border border-accent/40 bg-elevated p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="font-mono text-xs tracking-[0.14em] text-subtle">SESSION-LOCKED PAPER BOOK</p>
              <p className="mt-1 text-sm text-muted">
                Session = {marketDate ?? state.marketDate}. ARMED / TOUCHED 掛單唔會因日內 refresh 自動改價；新 market date 先會 SUPERSEDE，再生成同一 rung 的新價格。
              </p>
            </div>
            <Badge tone="lock">NO BROKER TRANSMISSION</Badge>
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <Metric label="QQQ NOW" value={currentPrice == null ? "—" : fmtUsd(currentPrice, 2)} detail="observed price" />
          <Metric label="TARGET" value={fmtUsd(target, 2)} detail="front-loaded 10Y target" />
          <Metric label="SHADOW QQQ NAV" value={fmtUsd(state.positionNav, 2)} detail="paper marked position" />
          <Metric label="DEPLOYMENT RESERVE" value={fmtUsd(state.deploymentReserve, 2)} detail="uncontributed B budget" />
          <Metric label="HARVEST RESERVE" value={fmtUsd(state.harvestReserve, 2)} detail="filled SELL proceeds · paper only" />
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Metric label="ECONOMIC WEALTH" value={fmtUsd(paperEconomicWealth(state), 2)} detail="shadow NAV + both reserves" />
          <Metric label="NEXT BUY" value={nextRungLabel("BUY", state.nextBuyRung)} detail="deepens after BUY fill/cancel" />
          <Metric label="NEXT SELL" value={nextRungLabel("SELL", state.nextSellRung)} detail="rises after SELL fill/cancel" />
          <Metric label="ACTIVE ORDERS" value={String(active.length)} detail="max 1 BUY + 1 SELL" />
        </div>

        <div className="grid gap-3 lg:grid-cols-2">
          {[{ side: "BUY" as const, order: buy }, { side: "SELL" as const, order: sell }].map(({ side, order }) => (
            <div key={side} className="rounded-md border border-line bg-elevated p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <p className="font-mono text-xs tracking-[0.14em] text-subtle">{side} CHASE LANE</p>
                  <p className="mt-1 text-sm text-muted">
                    {side === "BUY" ? "到低位 → 加倉；成交後消耗 Harvest → Deployment reserve" : "到高位 → 減倉；成交後把 proceeds 放入 Harvest reserve"}
                  </p>
                </div>
                <Badge tone={order ? statusTone(order.status) : "mute"}>{order?.status ?? "WAITING"}</Badge>
              </div>

              {order ? (
                <div className="mt-4 grid gap-3">
                  <div className="grid grid-cols-2 gap-3">
                    <Metric label="RUNG" value={order.rung} detail={String(order.horizon) + "D · touch≈ " + fmtPct(order.touchProbability, 0)} />
                    <Metric label="LIMIT" value={fmtUsd(order.limitPrice, 2)} detail={(currentPrice == null ? "—" : fmtPct(order.limitPrice / currentPrice - 1, 2)) + " vs NOW"} />
                    <Metric label="AMOUNT" value={fmtUsd(order.suggestedAmount, 2)} detail="paper suggested notional" />
                    <Metric label="SOURCE QQQ" value={fmtUsd(order.sourcePrice, 2)} detail="price when armed" />
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <button
                      type="button"
                      disabled={order.status !== "TOUCHED" || currentPrice == null || !canFillOrder(state, order.id, currentPrice)}
                      onClick={() => onFill(order.id)}
                      className="min-h-10 rounded-md border border-accent px-3 font-mono text-xs disabled:cursor-not-allowed disabled:opacity-35"
                    >
                      {orderActionLabel(order)}
                    </button>
                    <button
                      type="button"
                      disabled={order.status !== "ARMED" && order.status !== "TOUCHED"}
                      onClick={() => onCancel(order.id)}
                      className="min-h-10 rounded-md border border-line px-3 font-mono text-xs text-muted hover:text-fg disabled:cursor-not-allowed disabled:opacity-35"
                    >
                      SKIP / CANCEL RUNG
                    </button>
                    {order.status === "TOUCHED" ? (
                      <Badge tone="fragile">PRICE TOUCHED · CONFIRM MANUALLY</Badge>
                    ) : (
                      <span className="text-xs text-subtle">等待 QQQ observed price 到 limit。</span>
                    )}
                  </div>
                </div>
              ) : (
                <div className="mt-4 rounded-md border border-dashed border-line p-4 text-sm text-muted">
                  此方向暫無 active order。完成上一級、skip，或 reserve 不足會停在 WAITING。
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="rounded-md border border-line bg-elevated p-4 overflow-x-auto">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <p className="font-mono text-xs tracking-[0.14em] text-subtle">STATE TRANSITION LOG</p>
              <p className="mt-1 text-sm text-muted">ARMED → TOUCHED → FILLED；CANCEL 會跳過當前 rung；新交易日未成交掛單會 SUPERSEDE。</p>
            </div>
            <button type="button" onClick={onReset} className="min-h-10 rounded-md border border-line px-3 font-mono text-xs text-muted hover:text-fg">
              REBASE PAPER BOOK
            </button>
          </div>
          <table className="mt-3 w-full min-w-[920px] border-collapse text-xs">
            <thead>
              <tr className="border-b border-line text-left font-mono text-[11px] text-subtle">
                <th className="py-2 pr-4">TIME</th>
                <th className="py-2 pr-4">SIDE</th>
                <th className="py-2 pr-4">RUNG</th>
                <th className="py-2 pr-4">LIMIT</th>
                <th className="py-2 pr-4">AMOUNT</th>
                <th className="py-2 pr-4">STATUS</th>
              </tr>
            </thead>
            <tbody>
              {state.orders.slice().reverse().slice(0, 12).map((order) => (
                <tr key={order.id} className="border-b border-line/50">
                  <td className="py-2 pr-4 font-mono">{order.filledAt ?? order.touchedAt ?? order.createdAt}</td>
                  <td className="py-2 pr-4 font-mono">{order.side}</td>
                  <td className="py-2 pr-4 font-mono">{order.rung}</td>
                  <td className="py-2 pr-4 font-mono tabular-nums">{fmtUsd(order.limitPrice, 2)}</td>
                  <td className="py-2 pr-4 font-mono tabular-nums">{fmtUsd(order.filledAmount ?? order.suggestedAmount, 2)}</td>
                  <td className="py-2 pr-4"><Badge tone={statusTone(order.status)}>{order.status}</Badge></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <div className="rounded-md border border-line bg-elevated p-4">
            <p className="font-mono text-xs tracking-[0.14em] text-subtle">RECENT BUY FILLS</p>
            {buyHistory.length ? buyHistory.map((order) => (
              <div key={order.id} className="mt-2 flex justify-between gap-4 text-xs">
                <span className="font-mono">{order.rung} · {fmtUsd(order.filledPrice ?? order.limitPrice, 2)}</span>
                <span className="font-mono tabular-nums">{fmtUsd(order.filledAmount ?? 0, 2)}</span>
              </div>
            )) : <p className="mt-2 text-xs text-muted">none</p>}
          </div>
          <div className="rounded-md border border-line bg-elevated p-4">
            <p className="font-mono text-xs tracking-[0.14em] text-subtle">RECENT SELL FILLS</p>
            {sellHistory.length ? sellHistory.map((order) => (
              <div key={order.id} className="mt-2 flex justify-between gap-4 text-xs">
                <span className="font-mono">{order.rung} · {fmtUsd(order.filledPrice ?? order.limitPrice, 2)}</span>
                <span className="font-mono tabular-nums">{fmtUsd(order.filledAmount ?? 0, 2)}</span>
              </div>
            )) : <p className="mt-2 text-xs text-muted">none</p>}
          </div>
        </div>

        <p className="text-xs leading-relaxed text-subtle">
          呢個 Paper Book 同正式 Actual Contributed / Account NAV 分開。BUY/SELL fill 只改 paper position/reserve；
          真正券商成交仍要你自己在交易平台完成，再另外記錄真實現金流。Economic Wealth 亦係研究帳，不應當成券商實際現金餘額。
        </p>
      </div>
    </Panel>
  );
}
