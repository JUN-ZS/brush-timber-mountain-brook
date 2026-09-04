import { Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export function WeekTimeline({
  rows,
}: {
  rows: { d: string; pct: number | null }[];
}) {
  const data = rows.map((r) => ({
    d: r.d.slice(5),
    pct: r.pct == null ? null : Math.round(r.pct * 1000) / 10,
  }));
  return (
    <div className="h-40 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <XAxis dataKey="d" tick={{ fill: "var(--color-subtle)", fontSize: 10 }} axisLine={false} tickLine={false} />
          <YAxis domain={[40, 100]} tick={{ fill: "var(--color-subtle)", fontSize: 10 }} axisLine={false} tickLine={false} width={28} />
          <ReferenceLine y={90} stroke="var(--color-lock)" strokeDasharray="3 3" />
          <ReferenceLine y={50} stroke="var(--color-subtle)" strokeDasharray="2 2" />
          <Tooltip
            contentStyle={{ background: "var(--color-elevated)", border: "1px solid var(--color-line)", borderRadius: 8 }}
            labelStyle={{ color: "var(--color-muted)" }}
            formatter={(v) => [`${v ?? "—"}%`, "WEEK %"]}
          />
          <Line type="monotone" dataKey="pct" stroke="var(--color-accent)" strokeWidth={2} dot={{ r: 2.5, fill: "var(--color-accent)" }} connectNulls />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
