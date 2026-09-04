import raw from "../../data/universe.json" with { type: "json" };

export type UniverseFile = {
  source: string;
  asof: string;
  dates: string[];
  c: Record<string, (number | null)[]>;
  n: Record<string, number>;
};

export const universe = raw as UniverseFile;
export const calendar = universe.dates;
export const lastBar = calendar.length - 1;

export type ClosePt = { d: string; c: number; cal: number };

export function vixAt(cal: number): number | null {
  const v = universe.c.VIX?.[cal];
  return v != null && v > 0 ? v : null;
}

export function denseCloses(sym: string): ClosePt[] {
  const arr = universe.c[sym];
  if (!arr) return [];
  const out: ClosePt[] = [];
  for (let i = 0; i < arr.length; i++) {
    const c = arr[i];
    if (c != null && c > 0) out.push({ d: calendar[i], c, cal: i });
  }
  return out;
}

export function calendarIndexOf(date: string): number {
  let lo = 0;
  let hi = calendar.length - 1;
  if (date <= calendar[0]) return 0;
  if (date >= calendar[hi]) return hi;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (calendar[mid] < date) lo = mid + 1;
    else hi = mid;
  }
  return lo;
}
