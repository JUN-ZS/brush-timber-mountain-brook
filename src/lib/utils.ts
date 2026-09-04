import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function fmtPct(x: number | null | undefined, d = 0) {
  if (x == null || Number.isNaN(x)) return "—";
  return `${(x * 100).toFixed(d)}%`;
}

export function fmtNum(x: number | null | undefined, d = 2) {
  if (x == null || Number.isNaN(x)) return "—";
  return x.toFixed(d);
}

export function fmtMul(x: number | null | undefined) {
  if (x == null || Number.isNaN(x)) return "—";
  return `${x.toFixed(2)}×`;
}

export function fmtUsd(x: number | null | undefined, d = 0) {
  if (x == null || Number.isNaN(x)) return "—";
  const sign = x < 0 ? "-" : "";
  return `${sign}$${Math.abs(x).toFixed(d)}`;
}
