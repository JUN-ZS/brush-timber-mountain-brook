import { createFileRoute } from "@tanstack/react-router";
import { Panel, Shell } from "@/components/shell";
import { stateMatrix } from "@/lib/pulse/relvol";
import { useRadar } from "@/lib/pulse/store";
import { fmtPct } from "@/lib/utils";
import type { PriceDir, VolDir } from "@/lib/pulse/relvol";

export const Route = createFileRoute("/matrix")({ component: Page });

const PRICES: PriceDir[] = ["STRONG_UP", "MOD_UP", "FLAT", "MOD_DOWN", "STRONG_DOWN"];
const VOLS: VolDir[] = ["CONTRACTING", "NORMAL", "EXPANDING", "EXTREME"];

function Page() {
  const card = useRadar((s) => s.card);
  const cursor = useRadar((s) => s.cursor);
  const cells = card ? stateMatrix(card.symbol, cursor) : [];
  const lookup = new Map(cells.map((c) => [`${c.price}|${c.vol}`, c]));

  return (
    <Shell>
      <div className="grid gap-4">
        <Panel kicker="PRICE × VOL" title="方向與波動必須分開">
          <p className="max-w-2xl text-sm text-muted">
            Price ↑ Vol ↑ 不是 Price ↑ Vol ↓。格子裡是 TRAIN、且 k 小於現在 的下一週中位報酬。當格 n 太小就不讀。
          </p>
          {card ? (
            <p className="mt-2 font-mono text-xs text-subtle">
              現在：{card.symbol} · {card.priceDir} × {card.volDir}
            </p>
          ) : null}
        </Panel>
        <div className="overflow-x-auto rounded-xl border border-line">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead className="bg-elevated text-xs text-subtle">
              <tr>
                <th className="px-3 py-2 font-medium">price \ vol</th>
                {VOLS.map((v) => (
                  <th key={v} className="px-3 py-2 font-medium">
                    {v}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {PRICES.map((p) => (
                <tr key={p} className="border-t border-line">
                  <td className="px-3 py-3 font-mono text-xs text-muted">{p}</td>
                  {VOLS.map((v) => {
                    const cell = lookup.get(`${p}|${v}`);
                    const here = card && card.priceDir === p && card.volDir === v;
                    return (
                      <td key={v} className={`px-3 py-3 ${here ? "bg-elevated" : ""}`}>
                        {cell && cell.n >= 8 ? (
                          <div className="font-mono text-xs tabular-nums">
                            <div>{fmtPct(cell.medianNext, 1)}</div>
                            <div className="text-subtle">
                              up {fmtPct(cell.pUp, 0)} · n={cell.n}
                            </div>
                          </div>
                        ) : (
                          <span className="text-subtle">n={cell?.n ?? 0}</span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </Shell>
  );
}
