export function mean(xs: number[]) {
  if (!xs.length) return null;
  let s = 0;
  for (const x of xs) s += x;
  return s / xs.length;
}

export function wmean(xs: number[], ws: number[]) {
  let s = 0;
  let w = 0;
  for (let i = 0; i < xs.length; i++) {
    s += xs[i] * ws[i];
    w += ws[i];
  }
  return w > 0 ? s / w : null;
}

export function median(xs: number[]) {
  if (!xs.length) return null;
  const a = [...xs].sort((x, y) => x - y);
  const m = Math.floor(a.length / 2);
  return a.length % 2 ? a[m] : (a[m - 1] + a[m]) / 2;
}

export function stdev(xs: number[]) {
  if (xs.length < 8) return null;
  const m = mean(xs)!;
  let v = 0;
  for (const x of xs) v += (x - m) * (x - m);
  return Math.sqrt(v / (xs.length - 1));
}

export function percentileRank(hist: number[], x: number) {
  if (hist.length < 40) return null;
  let n = 0;
  for (const v of hist) if (v <= x) n += 1;
  return n / hist.length;
}

export function quantile(xs: number[], q: number) {
  if (!xs.length) return 0;
  const a = [...xs].sort((x, y) => x - y);
  const i = Math.min(a.length - 1, Math.max(0, Math.floor(q * (a.length - 1))));
  return a[i];
}

export function expectedShortfall(xs: number[], q: number) {
  if (!xs.length) return 0;
  const a = [...xs].sort((x, y) => x - y);
  const cut = Math.max(1, Math.floor(a.length * q));
  const tail = a.slice(0, cut);
  return tail.reduce((s, x) => s + x, 0) / tail.length;
}

export function timeDecay(barsAgo: number, halfLifeYears = 6) {
  return Math.exp(-barsAgo / (252 * halfLifeYears));
}
