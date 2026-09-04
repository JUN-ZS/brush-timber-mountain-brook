import raw from "../../data/panel.json" with { type: "json" };

export type PanelRow = {
  d: string;
  qo: number | null;
  qh: number | null;
  ql: number | null;
  qc: number;
  qv: number | null;
  spy: number | null;
  tlt: number | null;
  vxx: number | null;
  vix: number | null;
  vix3m: number | null;
};

export const panel = raw as { source: string; fwd_excluded: boolean; n: number; rows: PanelRow[] };

export type SymbolId = "QQQ" | "SPY" | "TLT" | "VXX";

export function closesOf(sym: SymbolId): { d: string; c: number; i: number }[] {
  const out: { d: string; c: number; i: number }[] = [];
  panel.rows.forEach((r, i) => {
    const c = sym === "QQQ" ? r.qc : sym === "SPY" ? r.spy : sym === "TLT" ? r.tlt : r.vxx;
    if (c != null && c > 0) out.push({ d: r.d, c, i });
  });
  return out;
}
