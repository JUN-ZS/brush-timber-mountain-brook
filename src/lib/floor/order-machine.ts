import type { LivePriceLadder, PriceActionLevel, PriceHorizon } from "./yahoo-live.ts";

export const ORDER_RUNG_GRID = [
  { key: "NEAR", horizon: 1 as PriceHorizon, touchProbability: 0.7, weight: 0.5 },
  { key: "MID", horizon: 5 as PriceHorizon, touchProbability: 0.5, weight: 0.3 },
  { key: "DEEP", horizon: 21 as PriceHorizon, touchProbability: 0.3, weight: 0.2 },
] as const;

export type OrderRungKey = (typeof ORDER_RUNG_GRID)[number]["key"];
export type PaperOrderSide = "BUY" | "SELL";
export type PaperOrderStatus = "ARMED" | "TOUCHED" | "FILLED" | "CANCELLED" | "SUPERSEDED";

export type PaperOrder = {
  id: string;
  side: PaperOrderSide;
  rung: OrderRungKey;
  horizon: PriceHorizon;
  touchProbability: number;
  limitPrice: number;
  suggestedAmount: number;
  marketDate: string;
  sourcePrice: number;
  createdAt: string;
  status: PaperOrderStatus;
  touchedAt?: string | null;
  filledAt?: string | null;
  filledPrice?: number | null;
  filledAmount?: number | null;
};

export type OrderMachineState = {
  schema: "qqq-order-machine.v1";
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
      (order.status === "ARMED" || order.status === "TOUCHED"),
  ) ?? null;
}

function currentOpenOrders(state: OrderMachineState) {
  return state.orders.filter(
    (order) => order.status === "ARMED" || order.status === "TOUCHED",
  );
}

function targetAtPrice(positionNav: number, markPrice: number, price: number) {
  if (!(positionNav >= 0) || !(markPrice > 0) || !(price > 0)) return 0;
  return positionNav * (price / markPrice);
}

function suggestedAmountFor(
  state: OrderMachineState,
  side: PaperOrderSide,
  level: PriceActionLevel,
  weight: number,
  target: number,
) {
  const shares =
    state.positionShares ??
    (state.markPrice > 0 ? state.positionNav / state.markPrice : 0);
  const projectedNav = shares * (level.price ?? 0);
  if (side === "BUY") {
    const availableReserve = state.deploymentReserve + state.harvestReserve;
    return Math.max(
      0,
      Math.min(availableReserve * weight, Math.max(0, target - projectedNav)),
    );
  }

  const projectedExcess = Math.max(0, projectedNav - target);
  const maxSell = Math.max(0, state.positionNav * weight);
  return Math.max(0, Math.min(projectedExcess * weight, maxSell));
}

function makeOrder(
  state: OrderMachineState,
  side: PaperOrderSide,
  index: number,
  ladder: LivePriceLadder,
  target: number,
  marketDate: string,
  now: string,
): PaperOrder | null {
  const rung = ORDER_RUNG_GRID[index];
  const level = rungLevel(ladder, side, index);
  if (!rung || !level?.price || !(level.price > 0)) return null;
  const suggestedAmount = suggestedAmountFor(state, side, level, rung.weight, target);
  if (!(suggestedAmount > 0)) return null;
  return {
    id:
      typeof crypto !== "undefined" && "randomUUID" in crypto
        ? crypto.randomUUID()
        : side.toLowerCase() + "-" + rung.key + "-" + now,
    side,
    rung: rung.key,
    horizon: rung.horizon,
    touchProbability: rung.touchProbability,
    limitPrice: level.price,
    suggestedAmount,
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
    schema: "qqq-order-machine.v1",
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

function supersedeOpenOrders(state: OrderMachineState, now: string) {
  return {
    ...state,
    updatedAt: now,
    orders: state.orders.map((order) =>
      order.status === "ARMED" || order.status === "TOUCHED"
        ? { ...order, status: "SUPERSEDED" as const }
        : order,
    ),
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
    state = {
      ...supersedeOpenOrders(state, input.now),
      marketDate: input.marketDate,
    };
  }

  state = {
    ...state,
    orders: state.orders.map((order) => {
      if (order.status !== "ARMED" || !touchPrice(order, input.currentPrice)) return order;
      return { ...order, status: "TOUCHED" as const, touchedAt: input.now };
    }),
  };

  if (!input.ladder) return { ...state, updatedAt: input.now };

  for (const side of ["BUY", "SELL"] as const) {
    if (openOrderForSide(state, side)) continue;
    const index = side === "BUY" ? state.nextBuyRung : state.nextSellRung;
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
  const fillAmount = Math.max(0, order.suggestedAmount);

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
    const shares = next.positionShares ??
      (next.markPrice > 0 ? next.positionNav / next.markPrice : 0);
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
    const shares = next.positionShares ??
      (next.markPrice > 0 ? next.positionNav / next.markPrice : 0);
    const maxSellNotional = shares * order.limitPrice;
    const sold = Math.min(maxSellNotional, fillAmount);
    const soldShares = order.limitPrice > 0 ? sold / order.limitPrice : 0;
    next = {
      ...next,
      positionShares: Math.max(0, shares - soldShares),
      positionNav: Math.max(0, shares - soldShares) * next.markPrice,
      harvestReserve: next.harvestReserve + sold,
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
  if (!order || (order.status !== "ARMED" && order.status !== "TOUCHED")) return state;
  return {
    ...state,
    updatedAt: now,
    orders: state.orders.map((x) =>
      x.id === orderId ? { ...x, status: "CANCELLED" as const } : x,
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
