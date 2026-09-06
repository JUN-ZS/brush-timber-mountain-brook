import type { ReactNode } from "react";
import { Link, useRouterState } from "@tanstack/react-router";
import { Badge } from "@/components/ui/badge";
import { useRadar } from "@/lib/pulse/store";
import { cn } from "@/lib/utils";

const NAV = [
  { to: "/", label: "雷達" },
  { to: "/rank", label: "排行" },
  { to: "/deploy", label: "結構競爭" },
  { to: "/backtest", label: "回測 V2" },
  { to: "/matrix", label: "價×波" },
  { to: "/missing", label: "缺失" },
] as const;

export function Shell({ children }: { children: ReactNode }) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const card = useRadar((s) => s.card);
  return <div className="min-h-svh bg-bg text-fg"><header className="border-b border-line"><div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-4 md:flex-row md:items-end md:justify-between"><div><p className="font-mono text-xs tracking-[0.2em] text-accent uppercase">Relative Vol Timeline</p><h1 className="mt-1 text-2xl font-medium tracking-tight md:text-3xl">相對波動時間線</h1><p className="mt-1 max-w-xl text-sm text-muted">每一隻股票對自己的 DAY / WEEK / MONTH 歷史。結構自己競爭。NO_TRADE 合法。</p></div><div className="flex flex-wrap gap-2"><Badge tone="fragile">{card?.split ?? "—"}</Badge><Badge tone="lock">OPTIONS MISSING</Badge><Badge tone="lock">LIVE LOCKED</Badge><Badge tone="mute">{card?.date ?? "—"}</Badge></div></div><nav className="mx-auto flex max-w-6xl gap-1 overflow-x-auto px-2 pb-2">{NAV.map((item) => { const active = item.to === "/" ? pathname === "/" : pathname.startsWith(item.to); return <Link key={item.to} to={item.to} className={cn("min-h-11 shrink-0 rounded-sm px-3 py-2 text-sm transition-colors duration-200", active ? "bg-elevated text-fg" : "text-muted hover:text-fg")}>{item.label}</Link>; })}</nav></header><main className="mx-auto max-w-6xl px-4 py-6">{children}</main></div>;
}

export function Panel({ title, kicker, children }: { title?: string; kicker?: string; children: ReactNode }) { return <section className="rounded-xl border border-line bg-surface p-4 shadow-panel md:p-5">{kicker ? <p className="font-mono text-xs tracking-[0.16em] text-subtle uppercase">{kicker}</p> : null}{title ? <h2 className="mt-1 text-lg font-medium tracking-tight">{title}</h2> : null}<div className={title || kicker ? "mt-3" : ""}>{children}</div></section>; }
