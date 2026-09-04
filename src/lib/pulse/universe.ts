export const TRADED = [
  "QQQ",
  "SPY",
  "IWM",
  "DIA",
  "NVDA",
  "TSLA",
  "PLTR",
  "HOOD",
  "AMD",
  "SMCI",
  "MU",
  "AVGO",
  "META",
  "NFLX",
  "AMZN",
  "GOOGL",
  "AAPL",
  "MSFT",
  "TSM",
  "BABA",
  "GLD",
  "TLT",
  "VXX",
] as const;

export type SymbolId = (typeof TRADED)[number];

export const INDEX = new Set<SymbolId>(["QQQ", "SPY", "IWM", "DIA"]);
export const RATES = new Set<SymbolId>(["TLT", "GLD"]);

export type Cohort = "HOT" | "MATURE" | "UNKNOWN";

/** History length is a feature, not a weight. Mature does not score higher. */
export function cohortOf(nBars: number, weekMean: number | null): Cohort {
  if (nBars < 1600) return "HOT";
  if (weekMean != null && weekMean >= 0.07) return "HOT";
  if (nBars >= 2500 && (weekMean == null || weekMean < 0.05)) return "MATURE";
  return "UNKNOWN";
}

export const MISSING_UNIVERSE = [
  "TQQQ",
  "SLV",
  "USO",
  "IBIT",
  "COIN",
  "MSTR",
  "ARM",
  "SNOW",
  "CRWD",
  "APP",
] as const;

export const RANK_MODES = [
  { id: "expansion", label: "Highest relative vol" },
  { id: "prebreak", label: "Pre-breakout" },
  { id: "persist", label: "Highest persistence" },
  { id: "edge", label: "Highest IV/RV edge" },
  { id: "evrisk", label: "Best EV / risk" },
  { id: "tail", label: "Lowest tail risk" },
  { id: "deploy", label: "Best option deployment" },
] as const;

export type RankMode = (typeof RANK_MODES)[number]["id"];
