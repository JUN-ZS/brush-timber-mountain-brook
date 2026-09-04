import { fmtPct } from "@/lib/utils";

export function Meter({ pct, label }: { pct: number | null; label: string }) {
  const w = Math.max(0, Math.min(100, (pct ?? 0) * 100));
  return (
    <div>
      <div className="flex items-baseline justify-between gap-2">
        <span className="font-mono text-xs text-subtle">{label}</span>
        <span className="font-mono text-sm tabular-nums">{fmtPct(pct, 0)}</span>
      </div>
      <div className="mt-1 h-2 overflow-hidden rounded-sm bg-elevated">
        <div className="h-full bg-accent" style={{ width: `${w}%` }} />
      </div>
    </div>
  );
}
