export type TradeSide = "BUY" | "SELL";
export type TradeSource = "MANUAL" | "PAPER_FILL";

export type TradeLedgerEntry = {
  id: string;
  recordedAt: string;
  cycleMonth: number;
  side: TradeSide;
  amount: number;
  price: number;
  shares: number;
  source: TradeSource;
  orderId?: string | null;
  note?: string;
  voidedAt?: string | null;
};

function clampCycleMonth(month: number) {
  if (!Number.isFinite(month)) return 0;
  return Math.max(0, Math.min(119, Math.round(month)));
}

export function createTradeEntry(input: {
  side: TradeSide;
  amount: number;
  price: number;
  cycleMonth: number;
  recordedAt?: string;
  source?: TradeSource;
  orderId?: string | null;
  note?: string;
}): TradeLedgerEntry {
  if (!(input.amount > 0) || !Number.isFinite(input.amount)) {
    throw new Error("Trade amount must be a positive finite number");
  }
  if (!(input.price > 0) || !Number.isFinite(input.price)) {
    throw new Error("Trade price must be a positive finite number");
  }
  const recordedAt = input.recordedAt ?? new Date().toISOString();
  return {
    id:
      typeof crypto !== "undefined" && "randomUUID" in crypto
        ? crypto.randomUUID()
        : recordedAt + "-" + Math.random().toString(36).slice(2),
    recordedAt,
    cycleMonth: clampCycleMonth(input.cycleMonth),
    side: input.side,
    amount: input.amount,
    price: input.price,
    shares: input.amount / input.price,
    source: input.source ?? "MANUAL",
    ...(input.orderId ? { orderId: input.orderId } : {}),
    ...(input.note?.trim() ? { note: input.note.trim() } : {}),
    voidedAt: null,
  };
}

export function activeTradeNotional(entries: TradeLedgerEntry[], side: TradeSide) {
  return entries
    .filter((entry) => entry.side === side && !entry.voidedAt)
    .reduce((sum, entry) => sum + Math.max(0, entry.amount), 0);
}
