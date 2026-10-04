import type { DynamicTradeIntent } from "./deployment.ts";
import type { LivePriceLadder, PriceActionLevel, PriceHorizon } from "./yahoo-live.ts";

export const ORDER_RUNG_GRID = [
  { key: "NEAR", horizon: 1 as PriceHorizon, touchProbability: 0.7, weight: 0.5 },
  { key: "MID", horizon: 5 as PriceHorizon, touchProbability: 0.5, weight: 0.3 },
  { key: "DEEP", horizon: 21 as PriceHorizon, touchProbability: 0.3, weight: 0.2 },
] as const;

export type OrderRungKey = (typeof ORDER_RUNG_GRID)[number]["key"];
export type PaperOrderSide = "BUY" | "SELL";
export type PaperOrderStatus = "ARMED" | "STALE" | "TOUCHED" | "FILLED" | "CANCELLED" | "REPLACED" | "SUPERSEDED";

export type PaperOrder = {
  id: string;
  side: PaperOrderSide;
  rung: OrderRungKey;
  horizon: PriceHorizon;
  touchProbability: number;
  limitPrice: number;
  suggestedAmount: number;
  parentIntentId: string;
  parentIntentNotional: number;
  marketDate: string;
  sourcePrice: number;
  createdAt: string;
  status: PaperOrderStatus;
  touchedAt?: string | null;
  filledAt?: string | null;
  filledPrice?: number | null;
  filledAmount?: number | null;
  cancelledAt?: string | null;
};

export type OrderMachineState = {
  schema: "qqq-order-machine.v2";
  seededAt: string;
  updatedAt: string;
  marketDate: string;
  markPrice: number;
  positionNav: number;
  positionShares?: number;
  deploymentReserve: number;
  harvestReserve: number;
  nextBuyRung: number;
  nextSellRung: number;
  orders: PaperOrder[];
};

function safePositive(value: number) {
  return Number.isFinite(value) && value > 0 ? value : 0;
}

function safeNonNegative(value: number) {
  return Number.isFinite(value) && value >= 0 ? value : 0;
}

function rungLevel(ladder: LivePriceLadder, side: PaperOrderSide, index: number): PriceActionLevel | null {
  const rung = ORDER_RUNG_GRID[index];
  if (!rung) return null;
  const rows = side === "BUY" ? ladder.add : ladder.reduce;
  return rows.find(
    (row) =>
      row.horizon === rung.horizon &&
      Math.abs(row.touchProbability - rung.touchProbability) < 1e-9 &&
      row.price != null,
  ) ?? null;
}

function openOrderForSide(state: OrderMachineState, side: PaperOrderSide) {
  return state.orders.find(
    (order) =>
      order.side === side &&
      (order.status === "ARMED" || order.status === "STALE" || order.status === "TOUCHED"),
  ) ?? null;
}

function currentOpenOrders(state: OrderMachineState) {
  return state.orders.filter(
    (order) => order.status === "ARMED" || order.status === "STALE" || order.status === "TOUCHED",
  );
}

function touchPrice(order: PaperOrder, currentPrice: number) {
  return order.side === "BUY"
    ? currentPrice <= order.limitPrice
    : currentPrice >= order.limitPrice;
}

export function seedOrderMachine(input: {
  now: string;
  marketDate: string;
  qqqPrice: number;
  nav: number;
  capital: number;
  contributed: number;
}): OrderMachineState {
  return {
    schema: "qqq-order-machine.v2",
    seededAt: input.now,
    updatedAt: input.now,
    marketDate: input.marketDate,
    markPrice: safePositive(input.qqqPrice),
    positionNav: safeNonNegative(input.nav),
    positionShares:
      input.qqqPrice > 0 ? safeNonNegative(input.nav) / input.qqqPrice : 0,
    deploymentReserve: Math.max(0, safeNonNegative(input.capital) - safeNonNegative(input.contributed)),
    harvestReserve: 0,
    nextBuyRung: 0,
    nextSellRung: 0,
    orders: [],
  };
}

export function markOrderMachineToMarket(
  state: OrderMachineState,
  currentPrice: number,
  now: string,
): OrderMachineState {
  const price = safePositive(currentPrice);
  if (!(price > 0)) return { ...state, updatedAt: now };
  const shares =
    state.positionShares ??
    (state.markPrice > 0 ? state.positionNav / state.markPrice : 0);
  return {
    ...state,
    updatedAt: now,
    markPrice: price,
    positionShares: shares,
    positionNav: shares * price,
  };
}

export function syncOrderMachine(input: {
  state: OrderMachineState;
  now: string;
  marketDate: string;
  currentPrice: number;
  ladder: LivePriceLadder | null;
  intent: DynamicTradeIntent | null;
}): OrderMachineState {
  let state = markOrderMachineToMarket(input.state, input.currentPrice, input.now);
  if (state.marketDate !== input.marketDate) {
    state = {
      ...state,
      updatedAt: input.now,
      marketDate: input.marketDate,
      orders: state.orders.map((order) =>
        order.status === "ARMED" ? { ...order, status: "STALE" as const } : order,
      ),
    };
  }

  state = {
    ...state,
    orders: state.orders.map((order) => {
      if ((order.status !== "ARMED" && order.status !== "STALE") || !touchPrice(order, input.currentPrice)) return order;
      return { ...order, status: "TOUCHED" as const, touchedAt: order.touchedAt ?? input.now };
    }),
  };

  if (!input.ladder || !input.intent || !(input.intent.notional > 0) || currentOpenOrders(state).length > 0) {
    return { ...state, updatedAt: input.now };
  }

  // DEV/Vite dynamic BUY/SELL intent is the parent order. The ladder changes
  // only execution timing/rung and limit placement, never the strategy amount.
  const pointer = input.intent.side === "BUY" ? state.nextBuyRung : state.nextSellRung;
  let index = pointer;
  while (index < ORDER_RUNG_GRID.length && !rungLevel(input.ladder, input.intent.side, index)) {
    index += 1;
  }
  if (index !== pointer) {
    state = {
      ...state,
      ...(input.intent.side === "BUY" ? { nextBuyRung: index } : { nextSellRung: index }),
    };
  }
  if (index >= ORDER_RUNG_GRID.length) return { ...state, updatedAt: input.now };

  const order = makeOrder(state, input.intent, index, input.ladder, input.marketDate, input.now);
  if (!order) return { ...state, updatedAt: input.now };

  const nextOrders = [...state.orders, order].map((candidate) => {
    if (candidate.status !== "ARMED" || !touchPrice(candidate, input.currentPrice)) return candidate;
    return { ...candidate, status: "TOUCHED" as const, touchedAt: input.now };
  });

  return { ...state, updatedAt: input.now, orders: nextOrders };
}

export function canFillOrder(state: OrderMachineState, orderId: string, currentPrice: number) {
  const order = state.orders.find((x) => x.id === orderId);
  if (!order || order.status !== "TOUCHED") return false;
  // TOUCHED is a latched state: once an observed price crossed the limit,
  // the operator can still confirm the paper fill after the market rebounds.
  return currentPrice > 0;
}

export function fillPaperOrder(
  state: OrderMachineState,
  orderId: string,
  currentPrice: number,
  now: string,
): OrderMachineState {
  const order = state.orders.find((x) => x.id === orderId);
  if (!order || order.status !== "TOUCHED" || !canFillOrder(state, orderId, currentPrice)) return state;

  const requestedAmount = Math.max(0, order.suggestedAmount);
  const shares =
    state.positionShares ??
    (state.markPrice > 0 ? state.positionNav / state.markPrice : 0);

  const fillAmount =
    order.side === "BUY"
      ? Math.min(requestedAmount, state.deploymentReserve + state.harvestReserve)
      : Math.min(requestedAmount, shares * order.limitPrice);

  if (!(fillAmount > 0)) return state;

  let next = {
    ...state,
    updatedAt: now,
    orders: state.orders.map((x) =>
      x.id === orderId
        ? {
            ...x,
            status: "FILLED" as const,
            filledAt: now,
            filledPrice: x.limitPrice,
            filledAmount: fillAmount,
          }
        : x,
    ),
  };

  if (order.side === "BUY") {
    const fromHarvest = Math.min(next.harvestReserve, fillAmount);
    const fromDeployment = Math.min(next.deploymentReserve, fillAmount - fromHarvest);
    const funded = fromHarvest + fromDeployment;
    const fillShares = order.limitPrice > 0 ? funded / order.limitPrice : 0;
    next = {
      ...next,
      positionShares: shares + fillShares,
      positionNav: (shares + fillShares) * next.markPrice,
      harvestReserve: next.harvestReserve - fromHarvest,
      deploymentReserve: next.deploymentReserve - fromDeployment,
      nextBuyRung: Math.min(ORDER_RUNG_GRID.length, next.nextBuyRung + 1),
    };
  } else {
    const soldShares = order.limitPrice > 0 ? fillAmount / order.limitPrice : 0;
    next = {
      ...next,
      positionShares: Math.max(0, shares - soldShares),
      positionNav: Math.max(0, shares - soldShares) * next.markPrice,
      harvestReserve: next.harvestReserve + fillAmount,
      nextSellRung: Math.min(ORDER_RUNG_GRID.length, next.nextSellRung + 1),
    };
  }

  return next;
}
export function cancelPaperOrder(
  state: OrderMachineState,
  orderId: string,
  now: string,
): OrderMachineState {
  const order = state.orders.find((x) => x.id === orderId);
  if (!order || (order.status !== "ARMED" && order.status !== "STALE" && order.status !== "TOUCHED")) return state;
  return {
    ...state,
    updatedAt: now,
    orders: state.orders.map((x) =>
      x.id === orderId ? { ...x, status: "CANCELLED" as const, cancelledAt: now } : x,
    ),
    nextBuyRung:
      order.side === "BUY"
        ? Math.min(ORDER_RUNG_GRID.length, state.nextBuyRung + 1)
        : state.nextBuyRung,
    nextSellRung:
      order.side === "SELL"
        ? Math.min(ORDER_RUNG_GRID.length, state.nextSellRung + 1)
        : state.nextSellRung,
  };
}

export function restoreCancelledOrder(
  state: OrderMachineState,
  orderId: string,
  now: string,
): OrderMachineState {
  const order = state.orders.find((x) => x.id === orderId);
  if (!order || order.status !== "CANCELLED") return state;

  const rungIndex = ORDER_RUNG_GRID.findIndex((rung) => rung.key === order.rung);
  if (rungIndex < 0) return state;
  if (openOrderForSide(state, order.side)) return state;

  // Do not rewind into a rung that has already produced a later fill.
  // That would create two incompatible sequential campaign states for one side.
  const laterFillExists = state.orders.some(
    (candidate) =>
      candidate.side === order.side &&
      candidate.status === "FILLED" &&
      ORDER_RUNG_GRID.findIndex((rung) => rung.key === candidate.rung) > rungIndex,
  );
  if (laterFillExists) return state;

  const nextPointer = Math.min(
    state[order.side === "BUY" ? "nextBuyRung" : "nextSellRung"],
    rungIndex,
  );

  const restored = {
    ...state,
    updatedAt: now,
    orders: state.orders.map((candidate) =>
      candidate.id === orderId
        ? {
            ...candidate,
            status: "ARMED" as const,
            touchedAt: null,
            filledAt: null,
            filledPrice: null,
            filledAmount: null,
            cancelledAt: null,
          }
        : candidate,
    ),
  };

  return order.side === "BUY"
    ? { ...restored, nextBuyRung: nextPointer }
    : { ...restored, nextSellRung: nextPointer };
}

export function repricePaperOrder(
  state: OrderMachineState,
  orderId: string,
  now: string,
  marketDate: string,
  ladder: LivePriceLadder | null,
  intent: DynamicTradeIntent | null,
) {
  const old = state.orders.find((x) => x.id === orderId);
  if (!old || (old.status !== "ARMED" && old.status !== "STALE")) return state;
  if (!ladder || !intent || intent.side !== old.side || !(intent.notional > 0)) return state;
  const index = ORDER_RUNG_GRID.findIndex((rung) => rung.key === old.rung);
  if (index < 0) return state;
  const replacement = makeOrder(state, intent, index, ladder, marketDate, now);
  if (!replacement) return state;
  return {
    ...state,
    updatedAt: now,
    marketDate,
    orders: [
      ...state.orders.map((x) => x.id === orderId ? { ...x, status: "REPLACED" as const } : x),
      replacement,
    ],
  };
}

export function resetOrderMachine(input: {
  now: string;
  marketDate: string;
  qqqPrice: number;
  nav: number;
  capital: number;
  contributed: number;
}): OrderMachineState {
  return seedOrderMachine(input);
}

export function activePaperOrders(state: OrderMachineState) {
  return currentOpenOrders(state);
}

export function nextRungLabel(side: PaperOrderSide, index: number) {
  const rung = ORDER_RUNG_GRID[Math.max(0, Math.min(ORDER_RUNG_GRID.length - 1, index))];
  return rung ? side + " " + rung.key : "COMPLETE";
}

export function paperEconomicWealth(state: OrderMachineState) {
  return state.positionNav + state.deploymentReserve + state.harvestReserve;
}function executionSlice(intent: DynamicTradeIntent, index: number) {
  const rung = ORDER_RUNG_GRID[index];
  return rung ? Math.max(0, Number(intent.notional) || 0) * rung.weight : 0;
}

function makeOrder(
  state: OrderMachineState,
  intent: DynamicTradeIntent,
  index: number,
  ladder: LivePriceLadder,
  marketDate: string,
  now: string,
): PaperOrder | null {
  const rung = ORDER_RUNG_GRID[index];
  const level = rungLevel(ladder, intent.side, index);
  if (!rung || !level?.price || !(level.price > 0)) return null;
  const suggestedAmount = executionSlice(intent, index);
  if (!(suggestedAmount > 0)) return null;
  return {
    id:
      typeof crypto !== "undefined" && "randomUUID" in crypto
        ? crypto.randomUUID()
        : intent.side.toLowerCase() + "-" + rung.key + "-" + now,
    side: intent.side,
    rung: rung.key,
    horizon: rung.horizon,
    touchProbability: rung.touchProbability,
    limitPrice: level.price,
    suggestedAmount,
    parentIntentId: intent.id,
    parentIntentNotional: intent.notional,
    marketDate,
    sourcePrice: state.markPrice,
    createdAt: now,
    status: "ARMED",
  };
}

function touchPrice(order: PaperOrder, currentPrice: number) {
  return order.side === "BUY"
    ? currentPrice <= order.limitPrice
    : currentPrice >= order.limitPrice;
}

export function seedOrderMachine(input: {
  now: string;
  marketDate: string;
  qqqPrice: number;
  nav: number;
  capital: number;
  contributed: number;
}): OrderMachineState {
  return {
    schema: "qqq-order-machine.v2",
    seededAt: input.now,
    updatedAt: input.now,
    marketDate: input.marketDate,
    markPrice: safePositive(input.qqqPrice),
    positionNav: safeNonNegative(input.nav),
    positionShares:
      input.qqqPrice > 0 ? safeNonNegative(input.nav) / input.qqqPrice : 0,
    deploymentReserve: Math.max(0, safeNonNegative(input.capital) - safeNonNegative(input.contributed)),
    harvestReserve: 0,
    nextBuyRung: 0,
    nextSellRung: 0,
    orders: [],
  };
}

export function markOrderMachineToMarket(
  state: OrderMachineState,
  currentPrice: number,
  now: string,
): OrderMachineState {
  const price = safePositive(currentPrice);
  if (!(price > 0)) return { ...state, updatedAt: now };
  const shares =
    state.positionShares ??
    (state.markPrice > 0 ? state.positionNav / state.markPrice : 0);
  return {
    ...state,
    updatedAt: now,
    markPrice: price,
    positionShares: shares,
    positionNav: shares * price,
  };
}

export function syncOrderMachine(input: {
  state: OrderMachineState;
  now: string;
  marketDate: string;
  currentPrice: number;
  ladder: LivePriceLadder | null;
  target: number;
}): OrderMachineState {
  let state = markOrderMachineToMarket(input.state, input.currentPrice, input.now);
  if (state.marketDate !== input.marketDate) {
    // A real LIMIT order can remain resting overnight. Mark it STALE so the
    // operator sees that today's ladder changed, but do not silently cancel it.
    state = {
      ...state,
      updatedAt: input.now,
      marketDate: input.marketDate,
      orders: state.orders.map((order) =>
        order.status === "ARMED" ? { ...order, status: "STALE" as const } : order,
      ),
    };
  }

  state = {
    ...state,
    orders: state.orders.map((order) => {
      if ((order.status !== "ARMED" && order.status !== "STALE") || !touchPrice(order, input.currentPrice)) return order;
      return { ...order, status: "TOUCHED" as const, touchedAt: order.touchedAt ?? input.now };
    }),
  };

  if (!input.ladder) return { ...state, updatedAt: input.now };

  for (const side of ["BUY", "SELL"] as const) {
    if (openOrderForSide(state, side)) continue;
    const pointer = side === "BUY" ? state.nextBuyRung : state.nextSellRung;
    let index = pointer;
    while (index < ORDER_RUNG_GRID.length && !rungLevel(input.ladder, side, index)) {
      index += 1;
    }
    if (index !== pointer) {
      state = {
        ...state,
        ...(side === "BUY" ? { nextBuyRung: index } : { nextSellRung: index }),
      };
    }
    if (index >= ORDER_RUNG_GRID.length) continue;
    const order = makeOrder(
      state,
      side,
      index,
      input.ladder,
      input.target,
      input.marketDate,
      input.now,
    );
    if (order) state = { ...state, orders: [...state.orders, order] };
  }

  // A newly armed order can already be through the current observed price
  // (for example after a new market session opens with a gap). Mark it TOUCHED
  // immediately, but never auto-fill it.
  state = {
    ...state,
    orders: state.orders.map((order) => {
      if (order.status !== "ARMED" || !touchPrice(order, input.currentPrice)) return order;
      return { ...order, status: "TOUCHED" as const, touchedAt: input.now };
    }),
  };

  return { ...state, updatedAt: input.now };
}

export function canFillOrder(state: OrderMachineState, orderId: string, currentPrice: number) {
  const order = state.orders.find((x) => x.id === orderId);
  if (!order || order.status !== "TOUCHED") return false;
  // TOUCHED is a latched state: once an observed price crossed the limit,
  // the operator can still confirm the paper fill after the market rebounds.
  return currentPrice > 0;
}

export function fillPaperOrder(
  state: OrderMachineState,
  orderId: string,
  currentPrice: number,
  now: string,
): OrderMachineState {
  const order = state.orders.find((x) => x.id === orderId);
  if (!order || order.status !== "TOUCHED" || !canFillOrder(state, orderId, currentPrice)) return state;

  const requestedAmount = Math.max(0, order.suggestedAmount);
  const shares =
    state.positionShares ??
    (state.markPrice > 0 ? state.positionNav / state.markPrice : 0);

  const fillAmount =
    order.side === "BUY"
      ? Math.min(requestedAmount, state.deploymentReserve + state.harvestReserve)
      : Math.min(requestedAmount, shares * order.limitPrice);

  if (!(fillAmount > 0)) return state;

  let next = {
    ...state,
    updatedAt: now,
    orders: state.orders.map((x) =>
      x.id === orderId
        ? {
            ...x,
            status: "FILLED" as const,
            filledAt: now,
            filledPrice: x.limitPrice,
            filledAmount: fillAmount,
          }
        : x,
    ),
  };

  if (order.side === "BUY") {
    const fromHarvest = Math.min(next.harvestReserve, fillAmount);
    const fromDeployment = Math.min(next.deploymentReserve, fillAmount - fromHarvest);
    const funded = fromHarvest + fromDeployment;
    const fillShares = order.limitPrice > 0 ? funded / order.limitPrice : 0;
    next = {
      ...next,
      positionShares: shares + fillShares,
      positionNav: (shares + fillShares) * next.markPrice,
      harvestReserve: next.harvestReserve - fromHarvest,
      deploymentReserve: next.deploymentReserve - fromDeployment,
      nextBuyRung: Math.min(ORDER_RUNG_GRID.length, next.nextBuyRung + 1),
    };
  } else {
    const soldShares = order.limitPrice > 0 ? fillAmount / order.limitPrice : 0;
    next = {
      ...next,
      positionShares: Math.max(0, shares - soldShares),
      positionNav: Math.max(0, shares - soldShares) * next.markPrice,
      harvestReserve: next.harvestReserve + fillAmount,
      nextSellRung: Math.min(ORDER_RUNG_GRID.length, next.nextSellRung + 1),
    };
  }

  return next;
}
export function cancelPaperOrder(
  state: OrderMachineState,
  orderId: string,
  now: string,
): OrderMachineState {
  const order = state.orders.find((x) => x.id === orderId);
  if (!order || (order.status !== "ARMED" && order.status !== "STALE" && order.status !== "TOUCHED")) return state;
  return {
    ...state,
    updatedAt: now,
    orders: state.orders.map((x) =>
      x.id === orderId ? { ...x, status: "CANCELLED" as const, cancelledAt: now } : x,
    ),
    nextBuyRung:
      order.side === "BUY"
        ? Math.min(ORDER_RUNG_GRID.length, state.nextBuyRung + 1)
        : state.nextBuyRung,
    nextSellRung:
      order.side === "SELL"
        ? Math.min(ORDER_RUNG_GRID.length, state.nextSellRung + 1)
        : state.nextSellRung,
  };
}

export function restoreCancelledOrder(
  state: OrderMachineState,
  orderId: string,
  now: string,
): OrderMachineState {
  const order = state.orders.find((x) => x.id === orderId);
  if (!order || order.status !== "CANCELLED") return state;

  const rungIndex = ORDER_RUNG_GRID.findIndex((rung) => rung.key === order.rung);
  if (rungIndex < 0) return state;
  if (openOrderForSide(state, order.side)) return state;

  // Do not rewind into a rung that has already produced a later fill.
  // That would create two incompatible sequential campaign states for one side.
  const laterFillExists = state.orders.some(
    (candidate) =>
      candidate.side === order.side &&
      candidate.status === "FILLED" &&
      ORDER_RUNG_GRID.findIndex((rung) => rung.key === candidate.rung) > rungIndex,
  );
  if (laterFillExists) return state;

  const nextPointer = Math.min(
    state[order.side === "BUY" ? "nextBuyRung" : "nextSellRung"],
    rungIndex,
  );

  const restored = {
    ...state,
    updatedAt: now,
    orders: state.orders.map((candidate) =>
      candidate.id === orderId
        ? {
            ...candidate,
            status: "ARMED" as const,
            touchedAt: null,
            filledAt: null,
            filledPrice: null,
            filledAmount: null,
            cancelledAt: null,
          }
        : candidate,
    ),
  };

  return order.side === "BUY"
    ? { ...restored, nextBuyRung: nextPointer }
    : { ...restored, nextSellRung: nextPointer };
}

export function repricePaperOrder(
  state: OrderMachineState,
  orderId: string,
  now: string,
  marketDate: string,
  ladder: LivePriceLadder | null,
  target: number,
) {
  const old = state.orders.find((x) => x.id === orderId);
  if (!old || (old.status !== "ARMED" && old.status !== "STALE")) return state;
  if (!ladder) return state;
  const index = old.side === "BUY" ? state.nextBuyRung : state.nextSellRung;
  const level = rungLevel(ladder, old.side, index);
  if (!level?.price) return state;
  const rung = ORDER_RUNG_GRID[index];
  if (!rung) return state;
  const amount = suggestedAmountFor(state, old.side, level, rung.weight, target);
  const replacement = amount > 0
    ? makeOrder(state, old.side, index, ladder, target, marketDate, now)
    : null;
  if (!replacement) return state;
  return {
    ...state,
    updatedAt: now,
    marketDate,
    orders: [
      ...state.orders.map((x) => x.id === orderId ? { ...x, status: "REPLACED" as const } : x),
      replacement,
    ],
  };
}

export function resetOrderMachine(input: {
  now: string;
  marketDate: string;
  qqqPrice: number;
  nav: number;
  capital: number;
  contributed: number;
}): OrderMachineState {
  return seedOrderMachine(input);
}

export function activePaperOrders(state: OrderMachineState) {
  return currentOpenOrders(state);
}

export function nextRungLabel(side: PaperOrderSide, index: number) {
  const rung = ORDER_RUNG_GRID[Math.max(0, Math.min(ORDER_RUNG_GRID.length - 1, index))];
  return rung ? side + " " + rung.key : "COMPLETE";
}

export function paperEconomicWealth(state: OrderMachineState) {
  return state.positionNav + state.deploymentReserve + state.harvestReserve;
}
