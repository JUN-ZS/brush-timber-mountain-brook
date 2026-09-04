const SQRT_2PI = Math.sqrt(2 * Math.PI);

function nPdf(x: number) {
  return Math.exp(-0.5 * x * x) / SQRT_2PI;
}

function nCdf(x: number) {
  const a1 = 0.254829592;
  const a2 = -0.284496736;
  const a3 = 1.421413741;
  const a4 = -1.453152027;
  const a5 = 1.061405429;
  const p = 0.3275911;
  const sign = x < 0 ? -1 : 1;
  const abs = Math.abs(x) / Math.SQRT2;
  const t = 1 / (1 + p * abs);
  const y = 1 - ((((a5 * t + a4) * t + a3) * t + a2) * t + a1) * t * Math.exp(-abs * abs);
  return 0.5 * (1 + sign * y);
}

export type OptionRight = "CALL" | "PUT";

export function normIv(iv: number | null | undefined, fallback = 0.25) {
  if (iv == null || !Number.isFinite(iv) || iv <= 0) return fallback;
  let v = iv;
  if (v > 3) v = v / 100;
  return Math.min(Math.max(v, 0.03), 3.5);
}

export function intrinsicPrice(spot: number, strike: number, right: OptionRight) {
  return right === "CALL" ? Math.max(spot - strike, 0) : Math.max(strike - spot, 0);
}

export function bsPrice(params: {
  spot: number;
  strike: number;
  tYears: number;
  iv: number;
  rate?: number;
  right: OptionRight;
}) {
  const { spot: S, strike: K, right } = params;
  const r = params.rate ?? 0.04;
  const sig = normIv(params.iv, 0.25);
  const T = params.tYears;
  if (S <= 0 || K <= 0 || T <= 1 / 365 / 24) return intrinsicPrice(S, K, right);
  const sqrtT = Math.sqrt(T);
  const d1 = (Math.log(S / K) + (r + 0.5 * sig * sig) * T) / (sig * sqrtT);
  const d2 = d1 - sig * sqrtT;
  if (right === "CALL") return S * nCdf(d1) - K * Math.exp(-r * T) * nCdf(d2);
  return K * Math.exp(-r * T) * nCdf(-d2) - S * nCdf(-d1);
}

export function bsGreeks(params: {
  spot: number;
  strike: number;
  tYears: number;
  iv: number;
  rate?: number;
  right: OptionRight;
}) {
  const { spot: S, strike: K, right } = params;
  const r = params.rate ?? 0.04;
  const sig = normIv(params.iv, 0.25);
  const T = Math.max(params.tYears, 1 / 365 / 8);
  if (params.tYears <= 1 / 365 / 24 || S <= 0 || K <= 0) {
    const price = intrinsicPrice(S, K, right);
    const itm = right === "CALL" ? (S > K ? 1 : S === K ? 0.5 : 0) : S < K ? -1 : S === K ? -0.5 : 0;
    return { price, delta: itm, gamma: 0, theta: 0, vega: 0 };
  }
  const sqrtT = Math.sqrt(T);
  const d1 = (Math.log(S / K) + (r + 0.5 * sig * sig) * T) / (sig * sqrtT);
  const d2 = d1 - sig * sqrtT;
  const gamma = nPdf(d1) / (S * sig * sqrtT);
  const vega = (S * nPdf(d1) * sqrtT) / 100;
  const thetaCall = (-(S * nPdf(d1) * sig) / (2 * sqrtT) - r * K * Math.exp(-r * T) * nCdf(d2)) / 365;
  const thetaPut = (-(S * nPdf(d1) * sig) / (2 * sqrtT) + r * K * Math.exp(-r * T) * nCdf(-d2)) / 365;
  const delta = right === "CALL" ? nCdf(d1) : nCdf(d1) - 1;
  const price =
    right === "CALL"
      ? S * nCdf(d1) - K * Math.exp(-r * T) * nCdf(d2)
      : K * Math.exp(-r * T) * nCdf(-d2) - S * nCdf(-d1);
  return { price, delta, gamma, theta: right === "CALL" ? thetaCall : thetaPut, vega };
}

export function roundStrike(k: number, spot: number) {
  const step = spot >= 300 ? 5 : spot >= 80 ? 1 : 0.5;
  return Math.round(k / step) * step;
}

export function strikeForDelta(params: {
  spot: number;
  tYears: number;
  iv: number;
  targetAbsDelta: number;
  right: OptionRight;
}) {
  const { spot, tYears, iv, targetAbsDelta, right } = params;
  const T = Math.max(tYears, 1 / 365);
  const z =
    targetAbsDelta >= 0.4 ? 0.25 : targetAbsDelta >= 0.25 ? 0.67 : targetAbsDelta >= 0.15 ? 1.04 : targetAbsDelta >= 0.1 ? 1.28 : 1.65;
  const m = iv * Math.sqrt(T) * z;
  return roundStrike(right === "PUT" ? spot * Math.exp(-m) : spot * Math.exp(m), spot);
}

export function ivShockForMove(spotShock: number) {
  if (spotShock >= 0) return Math.max(0.62, 1 - Math.abs(spotShock) * 1.5);
  const mag = Math.abs(spotShock);
  if (mag < 0.04) return 1 + mag * 1.2;
  if (mag < 0.1) return 1.05 + (mag - 0.04) * 2.2;
  return Math.min(2.05, 1.18 + (mag - 0.1) * 3.4);
}
