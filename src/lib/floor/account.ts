export const FLOOR_HORIZON_MONTHS = 120;

export type FloorEntryKind = "CONTRIBUTION" | "WITHDRAWAL";

export type FloorLedgerEntry = {
  id: string;
  recordedAt: string;
  cycleMonth: number;
  kind: FloorEntryKind;
  amount: number;
  note?: string;
  voidedAt?: string | null;
};

export type FloorStatus = "AHEAD" | "ON_CLOCK" | "BEHIND";

export type FloorAccountState = {
  plannedPrincipal: number;
  cycleMonth: number;
  nav: number;
  entries: FloorLedgerEntry[];
};

export function clampCycleMonth(month: number) {
  if (!Number.isFinite(month)) return 0;
  return Math.max(0, Math.min(FLOOR_HORIZON_MONTHS, Math.round(month)));
}

export function clockFraction(cycleMonth: number) {
  return clampCycleMonth(cycleMonth) / FLOOR_HORIZON_MONTHS;
}

export function clockTarget(plannedPrincipal: number, cycleMonth: number) {
  if (!(plannedPrincipal > 0) || !Number.isFinite(plannedPrincipal)) return 0;
  return plannedPrincipal * clockFraction(cycleMonth);
}

export function actualContributed(entries: FloorLedgerEntry[]) {
  return entries
    .filter((entry) => entry.kind === "CONTRIBUTION" && !entry.voidedAt)
    .reduce((sum, entry) => sum + Math.max(0, entry.amount), 0);
}

export function actualWithdrawn(entries: FloorLedgerEntry[]) {
  return entries
    .filter((entry) => entry.kind === "WITHDRAWAL" && !entry.voidedAt)
    .reduce((sum, entry) => sum + Math.max(0, entry.amount), 0);
}

export function fundingDelta(plannedPrincipal: number, cycleMonth: number, entries: FloorLedgerEntry[]) {
  return actualContributed(entries) - clockTarget(plannedPrincipal, cycleMonth);
}

export function fundingStatus(delta: number, epsilon = 0.005): FloorStatus {
  if (delta > epsilon) return "AHEAD";
  if (delta < -epsilon) return "BEHIND";
  return "ON_CLOCK";
}

export function createEntry(
  kind: FloorEntryKind,
  amount: number,
  cycleMonth: number,
  recordedAt = new Date().toISOString(),
  note?: string,
): FloorLedgerEntry {
  if (!(amount > 0) || !Number.isFinite(amount)) {
    throw new Error("Entry amount must be a positive finite number");
  }

  return {
    id:
      typeof crypto !== "undefined" && "randomUUID" in crypto
        ? crypto.randomUUID()
        : recordedAt + "-" + Math.random().toString(36).slice(2),
    recordedAt,
    cycleMonth: clampCycleMonth(cycleMonth),
    kind,
    amount,
    ...(note?.trim() ? { note: note.trim() } : {}),
  };
}

export function defaultFloorAccount(): FloorAccountState {
  return {
    plannedPrincipal: 100_000,
    cycleMonth: 0,
    nav: 0,
    entries: [],
  };
}

export function normalizeFloorAccount(raw: unknown): FloorAccountState {
  if (!raw || typeof raw !== "object") return defaultFloorAccount();

  const value = raw as Record<string, unknown>;
  const plannedPrincipal = Number(value.plannedPrincipal);
  const nav = Number(value.nav);
  const cycleMonth = Number(value.cycleMonth);
  const entriesRaw = Array.isArray(value.entries) ? value.entries : [];

  const entries = entriesRaw.filter((entry): entry is FloorLedgerEntry => {
    if (!entry || typeof entry !== "object") return false;
    const row = entry as Record<string, unknown>;
    return (
      typeof row.id === "string" &&
      typeof row.recordedAt === "string" &&
      Number.isFinite(Number(row.cycleMonth)) &&
      (row.kind === "CONTRIBUTION" || row.kind === "WITHDRAWAL") &&
      Number(row.amount) > 0 &&
      Number.isFinite(Number(row.amount)) &&
      (row.voidedAt == null || typeof row.voidedAt === "string")
    );
  }).map((entry) => ({
    ...entry,
    cycleMonth: clampCycleMonth(Number(entry.cycleMonth)),
    amount: Number(entry.amount),
    voidedAt: entry.voidedAt ?? null,
  }));

  return {
    plannedPrincipal:
      Number.isFinite(plannedPrincipal) && plannedPrincipal > 0
        ? plannedPrincipal
        : 100_000,
    cycleMonth: clampCycleMonth(cycleMonth),
    nav: Number.isFinite(nav) && nav >= 0 ? nav : 0,
    entries,
  };
}
