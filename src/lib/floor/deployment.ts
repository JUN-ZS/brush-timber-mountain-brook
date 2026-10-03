export const FLOOR_HORIZON_MONTHS = 120;

export const FRONTLOAD_GRID = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1] as const;

export type DeploymentStatus = "BUY_AVAILABLE" | "ON_TARGET" | "SELL_EXCESS";

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

export function dailyDeploymentRecord(input: {
  recordedAt: string;
  marketDate: string;
  cycleMonth: number;
  capital: number;
  frontload: number;
  nav: number;
  contributed: number;
  qqqPrice: number | null;
  marketState: string | null;
  dayRatio: number | null;
  weekRatio: number | null;
  monthRatio: number | null;
  dayLevel: string;
  weekLevel: string;
  monthLevel: string;
}) {
  const target = frontLoadedTarget(input.capital, input.frontload, input.cycleMonth, input.marketDate);
  const remaining = Math.max(0, input.capital - Math.max(0, input.contributed));
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
    source: "YAHOO_FINANCE_CHART" as const,
  };
}
