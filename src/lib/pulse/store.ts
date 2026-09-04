import { create } from "zustand";
import { lastBar } from "./bars.ts";
import { cardAt, ranking, type RelCard } from "./relvol.ts";
import { compete, type Deployment } from "./structures.ts";
import { TRADED, type RankMode, type SymbolId } from "./universe.ts";

const seedCards = ranking(lastBar);
const seed = seedCards.find((c) => c.symbol === "QQQ") ?? seedCards[0];

type Store = {
  cursor: number;
  symbol: SymbolId;
  card: RelCard | null;
  cards: RelCard[];
  deploys: Deployment[];
  rankMode: RankMode;
  maxConsec: number;
  maxDd: number;
  setSymbol: (s: SymbolId) => void;
  setCursor: (i: number) => void;
  setRankMode: (m: RankMode) => void;
  setBudget: (p: { maxConsec?: number; maxDd?: number }) => void;
};

function pack(sym: SymbolId, cursor: number) {
  const cards = ranking(cursor);
  const card = cards.find((c) => c.symbol === sym) ?? cards[0] ?? null;
  const deploys = card ? compete(card, cursor) : [];
  return { cards, card, deploys };
}

export const useRadar = create<Store>((set, get) => ({
  cursor: lastBar,
  symbol: (seed?.symbol as SymbolId) ?? "QQQ",
  card: seed ?? null,
  cards: seedCards,
  deploys: seed ? compete(seed, lastBar) : [],
  rankMode: "expansion",
  maxConsec: 3,
  maxDd: 2000,
  setSymbol: (s) => set({ symbol: s, ...pack(s, get().cursor) }),
  setCursor: (i) => {
    const n = Math.max(120, Math.min(i, lastBar));
    set({ cursor: n, ...pack(get().symbol, n) });
  },
  setRankMode: (m) => set({ rankMode: m }),
  setBudget: (p) => set({ maxConsec: p.maxConsec ?? get().maxConsec, maxDd: p.maxDd ?? get().maxDd }),
}));

export { lastBar, TRADED };
