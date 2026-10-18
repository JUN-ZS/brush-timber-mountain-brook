import type { LivePriceLadder } from "./yahoo-live.ts";

export const FLOOR_HORIZON_MONTHS = 120;

export const FRONTLOAD_GRID = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1] as const;

export type DeploymentStatus = "BUY_AVAILABLE" | "ON_TARGET" | "SELL_EXCESS";

export type DynamicTradeIntent = {
  id: string;
  side: "BUY" | "SELL";
  notional: number;
  target: number;
  signedGap: number;
  cycleMonth: number;
  source: "DEV_VITE_DYNAMIC_DEPLOYMENT_V1";
  createdAt: string;
};


export function clampFrontload(value: number) {
  if (!Number.isFinite(value)) return 0;
  return Math.max(0, Math.min(1, value));
}

export function clampProgress(value: number) {
  if (!Number.isFinite(value)) return 0;
  return Math.max(0, Math.min(1, value));
}

/** F=0 is the original linear 10Y clock; F=1 targets full capital immediately. */
export function frontLoadedFraction(frontload: number, progress: number) {
  const f = clampFrontload(frontload);
  const p = clampProgress(progress);
  return f + (1 - f) * p;
}

export function dailyProgress(cycleMonth: number, isoDate?: string | null, horizonMonths = FLOOR_HORIZON_MONTHS) {
  const month = Math.max(1, Math.min(horizonMonths, Math.round(Number(cycleMonth) || 1)));
  let withinMonth = 0;
  if (isoDate && /^\d{4}-\d{2}-\d{2}$/.test(isoDate)) {
    const parsed = new Date(isoDate + "T00:00:00Z");
    if (!Number.isNaN(parsed.getTime())) {
      const daysInMonth = new Date(Date.UTC(parsed.getUTCFullYear(), parsed.getUTCMonth() + 1, 0)).getUTCDate();
      withinMonth = daysInMonth > 1 ? (parsed.getUTCDate() - 1) / (daysInMonth - 1) : 0;
    }
  }
  return clampProgress(((month - 1) + withinMonth) / horizonMonths);
}

export function frontLoadedTarget(capital: number, frontload: number, cycleMonth: number, isoDate?: string | null) {
  if (!(capital > 0) || !Number.isFinite(capital)) return 0;
  return capital * frontLoadedFraction(frontload, dailyProgress(cycleMonth, isoDate));
}

export function deploymentGap(nav: number, target: number, remainingCapital: number) {
  const safeNav = Number.isFinite(nav) && nav >= 0 ? nav : 0;
  const safeRemaining = Number.isFinite(remainingCapital) && remainingCapital > 0 ? remainingCapital : 0;
  const gap = target - safeNav;
  return {
    buyAvailable: Math.min(safeRemaining, Math.max(0, gap)),
    sellExcess: Math.max(0, -gap),
    signedGap: gap,
    status: gap > 0.005 ? "BUY_AVAILABLE" as const : gap < -0.005 ? "SELL_EXCESS" as const : "ON_TARGET" as const,
  };
}

export function dynamicTradeIntent(input: {
  id: string;
  now: string;
  cycleMonth: number;
  nav: number;
  target: number;
  remainingCapital: number;
}): DynamicTradeIntent | null {
  const gap = deploymentGap(input.nav, input.target, input.remainingCapital);
  if (gap.status === "ON_TARGET") return null;
  return {
    id: input.id,
    side: gap.status === "BUY_AVAILABLE" ? "BUY" : "SELL",
    notional: gap.status === "BUY_AVAILABLE" ? gap.buyAvailable : gap.sellExcess,
    target: input.target,
    signedGap: gap.signedGap,
    cycleMonth: Math.max(1, Math.min(FLOOR_HORIZON_MONTHS, Math.round(Number(input.cycleMonth) || 1))),
    source: "DEV_VITE_DYNAMIC_DEPLOYMENT_V1",
    createdAt: input.now,
  };
}

export function dailyDeploymentRecord(input: {
  recordedAt: string;
  marketDate: string;
  cycleMonth: number;
  capital: number;
  frontload: number;
  nav: number;
  contributed: number;
  startingDeployed: number;
  qqqPrice: number | null;
  marketState: string | null;
  dayRatio: number | null;
  weekRatio: number | null;
  monthRatio: number | null;
  dayLevel: string;
  weekLevel: string;
  monthLevel: string;
  priceLadder?: LivePriceLadder | null;
}) {
  const target = frontLoadedTarget(input.capital, input.frontload, input.cycleMonth, input.marketDate);
  const startingDeployed = Math.max(
    0,
    Math.min(input.capital, Number(input.startingDeployed) || 0),
  );
  const contributed = Math.max(0, Number(input.contributed) || 0);
  const remaining = Math.max(0, input.capital - startingDeployed - contributed);
  const gap = deploymentGap(input.nav, target, remaining);
  return {
    ...input,
    frontload: clampFrontload(input.frontload),
    target,
    remainingCapital: remaining,
    buyAvailable: gap.buyAvailable,
    sellExcess: gap.sellExcess,
    signedGap: gap.signedGap,
    status: gap.status,
    priceLadder: input.priceLadder ?? null,
    source: "YAHOO_FINANCE_CHART" as const,
  };
}


export type DailyDeploymentObservationKey = {
  id: string;
  marketDate: string;
  frontload: number;
  voidedAt?: string | null;
};

export function toggleDailyDeploymentObservation<T extends DailyDeploymentObservationKey>(
  entries: T[],
  entryId: string,
  now: string,
) {
  const target = entries.find((entry) => entry.id === entryId);
  if (!target) return entries;

  if (target.voidedAt) {
    const duplicateActive = entries.some(
      (entry) =>
        entry.id !== entryId &&
        !entry.voidedAt &&
        entry.marketDate === target.marketDate &&
        Math.abs(entry.frontload - target.frontload) < 1e-9,
    );
    if (duplicateActive) return entries;
  }

  return entries.map((entry) =>
    entry.id === entryId
      ? { ...entry, voidedAt: entry.voidedAt ? null : now }
      : entry,
  );
}
