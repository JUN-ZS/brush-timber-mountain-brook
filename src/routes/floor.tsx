import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useRef, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Panel, Shell } from "@/components/shell";
import { fmtPct, fmtUsd } from "@/lib/utils";
import {
  actualContributed,
  actualWithdrawn,
  clockFraction,
  clockTarget,
  fundingDelta,
  fundingStatus,
  type FloorEntryKind,
} from "@/lib/floor/account";
import {
  activeTradeNotional,
  createTradeEntry,
  type TradeLedgerEntry,
  type TradeSide,
} from "@/lib/floor/trade-ledger";
import snapshot from "@/data/rolling_floor_ui_snapshot.json";
import { buildLiveHistoryMatch, type LiveHistoryMatch, type YahooSeries } from "@/lib/floor/yahoo-live";
import type { CoupledSignal, ForwardPathProfile } from "@/lib/pulse/rolling-floor";
import type { LongScaleProfile } from "@/lib/pulse/long-scale";
import { DailyDeploymentConsole, type DailyDeploymentEntry } from "@/components/daily-deployment-console";
import { OrderStateMachine } from "@/components/order-state-machine";
import { dailyDeploymentRecord, dynamicTradeIntent, frontLoadedTarget, deploymentGap, toggleDailyDeploymentObservation } from "@/lib/floor/deployment";
import {
  activePaperOrders,
  cancelPaperOrder,
  fillPaperOrder,
  repricePaperOrder,
  restoreCancelledOrder,
  resetOrderMachine,
  seedOrderMachine,
  syncOrderMachine,
  type OrderMachineState,
} from "@/lib/floor/order-machine";

export const Route = createFileRoute("/floor")({ component: Page });

type EntryStatus = "BELOW_CLOCK" | "ON_CLOCK" | "AHEAD" | "OVER_CAPITAL";

type LedgerEntry = {
  id: string;
  recordedAt: string;
  asOf: string;
  month: number;
  amount: number;
  kind?: FloorEntryKind;
  price?: number | null;
  priceObservedAt?: string | null;
  priceSource?: "YAHOO_FINANCE_CHART" | "UNAVAILABLE";
  voidedAt?: string | null;
};

type MarketTapeEntry = {
  observedAt: string;
  marketDate: string;
  month: number;
  price: number;
};

type RiskBaselineProfileView = {
  deploymentFractions: number[];
  garMedian: number[];
  garQ05: number[];
  garQ95: number[];
  maxDdMedian: number[];
  maxDdQ05: number[];
  maxDdQ95: number[];
};

const LEDGER_KEY_V2 = "qqq-rolling-floor-ledger-v2";
const FLOOR_STATE_KEY = "qqq-rolling-floor-state-v4";
const LEGACY_FLOOR_STATE_KEY_V3 = "qqq-rolling-floor-state-v3";

const DEFAULT_CAPITAL = 100000;
const DEFAULT_STARTING_DEPLOYED = 0;
const DEFAULT_MONTH = 0;

type FloorPersistedState = {
  capital: number;
  startingDeployed: number;
  month: number;
  entries: LedgerEntry[];
  marketTape: MarketTapeEntry[];
  dailyDeploymentTape?: DailyDeploymentEntry[];
  frontloadPct?: number;
  orderMachine?: OrderMachineState | null;
  nav: number;
  tradeLedger: TradeLedgerEntry[];
};

type StartDraft = {
  capital: number | null;
  month: number | null;
  startingDeployed: number | null;
  nav: number | null;
  frontloadPct: number | null;
  cashIn: number | null;
};

const EMPTY_START_DRAFT: StartDraft = {
  capital: null,
  month: null,
  startingDeployed: null,
  nav: null,
  frontloadPct: null,
  cashIn: null,
};

const DEFAULT_START_TEMPLATE = {
  schema: "rolling-floor.default-start.v1",
  plannedPrincipalB: null,
  startMonth: null,
  openingDeployed: null,
  accountNav: null,
  frontloadPct: null,
  cashIn: null,
};

function defaultFloorState(): FloorPersistedState {
  return {
    capital: DEFAULT_CAPITAL,
    startingDeployed: DEFAULT_STARTING_DEPLOYED,
    month: DEFAULT_MONTH,
    entries: [],
    marketTape: [],
    dailyDeploymentTape: [],
    nav: 0,
    tradeLedger: [],
  };
}

function clampMonth(value: unknown): number {
  const n = Number(value);
  if (!Number.isFinite(n)) return DEFAULT_MONTH;
  return Math.max(0, Math.min(119, Math.round(n)));
}

function normalizeFloorState(raw: unknown): FloorPersistedState | null {
  if (raw == null) return null;

  // Legacy v2: array-only ledger
  if (Array.isArray(raw)) {
    return {
      ...defaultFloorState(),
      entries: raw
        .filter(validLedgerEntry)
        .map((entry) => ({ ...entry, kind: "CONTRIBUTION" as const })),
    };
  }

  if (typeof raw !== "object") return null;
  const obj = raw as Record<string, unknown>;

  const capitalRaw = Number(obj.capital);
  const capital =
    Number.isFinite(capitalRaw) && capitalRaw >= 1 ? capitalRaw : DEFAULT_CAPITAL;

  const startingRaw = Number(obj.startingDeployed);
  const startingDeployed =
    Number.isFinite(startingRaw) && startingRaw >= 0
      ? startingRaw
      : DEFAULT_STARTING_DEPLOYED;

  const month = clampMonth(obj.month);

  const entriesSource = Array.isArray(obj.entries)
    ? obj.entries
    : Array.isArray(obj.ledger)
      ? obj.ledger
      : [];
  const rawEntries = entriesSource
    .filter(validLedgerEntry)
    .map((entry) => ({
      ...entry,
      kind: entry.kind ?? ("CONTRIBUTION" as const),
    }));

  // PR #68 called this value "starting/already deployed": it is an opening
  // deployment position, not a new external cash-in. Older v4 writes may have
  // materialized it as a synthetic legacy contribution; recover it here but
  // never count it in ACTUAL CONTRIBUTED.
  const legacyOpening = rawEntries.find((entry) => entry.id === "legacy-opening-contribution");
  const recoveredStartingDeployed = Math.max(
    0,
    Math.min(
      capital,
      startingDeployed > 0 ? startingDeployed : Number(legacyOpening?.amount) || 0,
    ),
  );
  const entries = rawEntries.filter((entry) => entry.id !== "legacy-opening-contribution");

  const marketTapeSource = Array.isArray(obj.marketTape) ? obj.marketTape : [];
  const marketTape = marketTapeSource
    .filter(validMarketTapeEntry)
    .map((entry) => ({ ...entry, month: clampMonth(entry.month) }));

  const navRaw = Number(obj.nav);
  const nav = Number.isFinite(navRaw) && navRaw >= 0 ? navRaw : 0;
  const dailyDeploymentTape = Array.isArray(obj.dailyDeploymentTape)
    ? obj.dailyDeploymentTape.filter(validDailyDeploymentEntry)
    : [];
  const frontloadRaw = Number(obj.frontloadPct);
  const frontloadPct = Number.isFinite(frontloadRaw)
    ? Math.max(0, Math.min(1, frontloadRaw))
    : 0.4;

  return {
    capital,
    startingDeployed: recoveredStartingDeployed,
    month,
    entries,
    marketTape,
    dailyDeploymentTape,
    frontloadPct,
    orderMachine: validOrderMachineState(obj.orderMachine) ? obj.orderMachine : null,
    nav,
    tradeLedger: Array.isArray(obj.tradeLedger) ? obj.tradeLedger.filter(validTradeLedgerEntry) : [],
  };
}

function loadFloorState(): FloorPersistedState {
  if (typeof window === "undefined") return null;

  const readStored = (key: string) => {
    const raw = window.localStorage.getItem(key);
    if (!raw) return null;
    try {
      return normalizeFloorState(JSON.parse(raw));
    } catch {
      return null;
    }
  };

  const v4 = readStored(FLOOR_STATE_KEY);
  if (v4) return v4;

  const legacyV3 = readStored(LEGACY_FLOOR_STATE_KEY_V3);
  if (legacyV3) return legacyV3;

  const v2 = readStored(LEDGER_KEY_V2);
  if (v2) return v2;

  try {
    window.localStorage.removeItem(FLOOR_STATE_KEY);
  } catch {
    // Ignore malformed local state; safe defaults remain in memory.
  }

  return defaultFloorState();
}

function writeFloorState(state: FloorPersistedState) {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(
      FLOOR_STATE_KEY,
      JSON.stringify({
        capital: state.capital,
        startingDeployed: state.startingDeployed,
        month: state.month,
        entries: state.entries,
        marketTape: state.marketTape,
        dailyDeploymentTape: state.dailyDeploymentTape,
        frontloadPct: state.frontloadPct,
        orderMachine: state.orderMachine,
        nav: state.nav,
        tradeLedger: state.tradeLedger,
      }),
    );
    // v4 is the source of truth after migration; legacy keys are read-only fallbacks.
    window.localStorage.removeItem(LEDGER_KEY_V2);
  } catch {
      // Ignore malformed local state; safe defaults remain in memory.
    }
}

function Page() {
  const [isStarted, setIsStarted] = useState(false);
  const [startDraft, setStartDraft] = useState<StartDraft>(EMPTY_START_DRAFT);
  const [capital, setCapital] = useState(DEFAULT_CAPITAL);
  const [startingDeployed, setStartingDeployed] = useState(DEFAULT_STARTING_DEPLOYED);
  const [actualNow, setActualNow] = useState(0);
  const [month, setMonth] = useState(DEFAULT_MONTH);
  const [ledger, setLedger] = useState<LedgerEntry[]>([]);
  const [marketTape, setMarketTape] = useState<MarketTapeEntry[]>([]);
  const [dailyDeploymentTape, setDailyDeploymentTape] = useState<DailyDeploymentEntry[]>([]);
  const [frontloadPct, setFrontloadPct] = useState(0.4);
  const [orderMachine, setOrderMachine] = useState<OrderMachineState | null>(null);
  const [nav, setNav] = useState(0);
  const [tradeLedger, setTradeLedger] = useState<TradeLedgerEntry[]>([]);
  const [tradeSide, setTradeSide] = useState<TradeSide>("BUY");
  const [tradeAmountNow, setTradeAmountNow] = useState(0);
  const [tradePriceNow, setTradePriceNow] = useState(0);
  const [tradeNoteNow, setTradeNoteNow] = useState("");
  const [plannedContributionMonth, setPlannedContributionMonth] = useState(DEFAULT_MONTH + 1);
  const [plannedContributionAmount, setPlannedContributionAmount] = useState(0);
  const [plannedWithdrawalMonth, setPlannedWithdrawalMonth] = useState(DEFAULT_MONTH + 1);
  const [plannedWithdrawalAmount, setPlannedWithdrawalAmount] = useState(0);
  const [copied, setCopied] = useState(false);
  const [hasHydrated, setHasHydrated] = useState(false);
  const [liveMatch, setLiveMatch] = useState<LiveHistoryMatch | null>(null);
  const [liveContext, setLiveContext] = useState<YahooSeries[]>([]);
  const [liveFetchedAt, setLiveFetchedAt] = useState<string | null>(null);
  const [liveFloor, setLiveFloor] = useState<CoupledSignal | null>(null);
  const [liveLongScale, setLiveLongScale] = useState<LongScaleProfile | null>(null);
  const [liveLoading, setLiveLoading] = useState(false);
  const [liveError, setLiveError] = useState<string | null>(null);
  const importRef = useRef<HTMLInputElement | null>(null);
  const [transferNotice, setTransferNotice] = useState<string | null>(null);

  async function refreshYahoo() {
    setLiveLoading(true);
    setLiveError(null);
    try {
      const response = await fetch("/api/yahoo?refresh=1", { cache: "no-store" });
      if (!response.ok) throw new Error("Yahoo HTTP " + response.status);
      const payload = (await response.json()) as {
        source?: string;
        fetchedAt?: string;
        symbols?: YahooSeries[];
        rollingFloor?: { asOf: string; coupled: CoupledSignal } | null;
        longScale?: { scale: 50; profile: LongScaleProfile; authority: "GEOMETRY_ONLY" } | null;
        warnings?: string[];
      };
      const symbols = Array.isArray(payload.symbols) ? payload.symbols : [];
      const qqq = symbols.find((x) => x.symbol === "QQQ");
      const match = qqq ? buildLiveHistoryMatch(qqq) : null;
      if (!match) throw new Error("Yahoo QQQ history insufficient");
      setLiveContext(symbols);
      setLiveMatch(match);
      setLiveFloor(payload.rollingFloor?.coupled ?? null);
      setLiveLongScale(payload.longScale?.profile ?? null);
      setLiveFetchedAt(payload.fetchedAt ?? new Date().toISOString());
      if (payload.warnings?.length) setLiveError(payload.warnings.join(" · "));
    } catch (error) {
      setLiveError(error instanceof Error ? error.message : "Yahoo refresh failed");
    } finally {
      setLiveLoading(false);
    }
  }

  useEffect(() => {
    void refreshYahoo();
  }, []);

  // Hydrate from localStorage before any persist write.
  useEffect(() => {
    const loaded = loadFloorState();
    if (!loaded) {
      setIsStarted(false);
      setStartDraft(EMPTY_START_DRAFT);
      setHasHydrated(true);
      return;
    }
    setIsStarted(true);
    setCapital(loaded.capital);
    setStartingDeployed(loaded.startingDeployed);
    setMonth(loaded.month);
    setLedger(loaded.entries);
    setMarketTape(loaded.marketTape);
    setDailyDeploymentTape(loaded.dailyDeploymentTape ?? []);
    setFrontloadPct(loaded.frontloadPct ?? 0.4);
    setOrderMachine(loaded.orderMachine ?? null);
    setNav(loaded.nav);
    setTradeLedger(loaded.tradeLedger ?? []);
    setStartDraft({
      capital: loaded.capital,
      month: loaded.month + 1,
      startingDeployed: loaded.startingDeployed,
      nav: loaded.nav,
      frontloadPct: loaded.frontloadPct ?? 0.4,
      cashIn: actualContributed(loaded.entries),
    });
    setHasHydrated(true);
  }, []);

  // Persist one blob after hydrate — never write the initial empty defaults.
  useEffect(() => {
    if (!hasHydrated || !isStarted) return;
    writeFloorState({
      capital,
      startingDeployed,
      month,
      entries: ledger,
      marketTape,
      dailyDeploymentTape,
      frontloadPct,
      orderMachine,
      nav,
      tradeLedger,
    });
  }, [hasHydrated, isStarted, capital, startingDeployed, month, ledger, marketTape, dailyDeploymentTape, frontloadPct, orderMachine, nav, tradeLedger]);

  // Each successful Yahoo refresh seals one observed QQQ market point at the current cycle month.
  // This tape is the bridge between real-time passage and the forward 10Y simulation.
  useEffect(() => {
    if (!hasHydrated || !liveFetchedAt) return;
    const qqq = liveContext.find((x) => x.symbol === "QQQ");
    if (!qqq?.price) return;
    const marketDate = qqq.regularMarketTime?.slice(0, 10) ?? qqq.bars.at(-1)?.date;
    if (!marketDate) return;

    setMarketTape((current) => {
      const next = current.filter((x) => !(x.marketDate === marketDate && x.month === month));
      next.push({
        observedAt: liveFetchedAt,
        marketDate,
        month,
        price: qqq.price,
      });
      next.sort((a, b) => a.month - b.month || a.marketDate.localeCompare(b.marketDate));
      return next.slice(-240);
    });
  }, [hasHydrated, liveFetchedAt, liveContext, month]);

  useEffect(() => {
    const onStorage = (event: StorageEvent) => {
      // writeFloorState removes the v2 ledger key after every v3 write.
      // Another tab must not treat that removal (newValue=null) as a full reset.
      if (event.key !== FLOOR_STATE_KEY) return;
      try {
        if (event.newValue == null) {
          setIsStarted(false);
          setStartDraft(EMPTY_START_DRAFT);
          setCapital(DEFAULT_CAPITAL);
          setStartingDeployed(DEFAULT_STARTING_DEPLOYED);
          setMonth(DEFAULT_MONTH);
          setLedger([]);
          setMarketTape([]);
          setDailyDeploymentTape([]);
          setFrontloadPct(0.4);
          setOrderMachine(null);
          setNav(0);
          setTradeLedger([]);
          return;
        }
        const parsed = normalizeFloorState(JSON.parse(event.newValue));
        if (!parsed) return;
        setIsStarted(true);
        setStartDraft({
          capital: parsed.capital,
          month: parsed.month + 1,
          startingDeployed: parsed.startingDeployed,
          nav: parsed.nav,
          frontloadPct: parsed.frontloadPct ?? 0.4,
          cashIn: actualContributed(parsed.entries),
        });
        setCapital(parsed.capital);
        setStartingDeployed(parsed.startingDeployed);
        setMonth(parsed.month);
        setLedger(parsed.entries);
        setMarketTape(parsed.marketTape);
        setDailyDeploymentTape(parsed.dailyDeploymentTape ?? []);
        setFrontloadPct(parsed.frontloadPct ?? 0.4);
        setOrderMachine(parsed.orderMachine ?? null);
        setNav(parsed.nav);
        setTradeLedger(parsed.tradeLedger ?? []);
      } catch {
      // Ignore malformed local state; safe defaults remain in memory.
    }
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const safeCapital = Math.max(1, capital);
  const cycleMonth = Math.max(0, Math.min(120, month + 1));
  const contributed = actualContributed(ledger);
  const withdrawn = actualWithdrawn(ledger);
  const actualBuyNotional = activeTradeNotional(tradeLedger, "BUY");
  const actualSellNotional = activeTradeNotional(tradeLedger, "SELL");
  // Funding and deployment are intentionally separate:
  // - fundingNowAmount = external cash-in, used by ACTUAL − CLOCK.
  // - deploymentNowAmount = opening deployed + external cash-in preview,
  //   used only by deployment/research geometry and paper capacity.
  const cumulativeBeforePreview = contributed;
  const cumulativeNowAmount = cumulativeBeforePreview + Math.max(0, actualNow);
  const fundingNowFraction = cumulativeNowAmount / safeCapital;
  const deploymentNowAmount = Math.max(0, startingDeployed) + cumulativeNowAmount;
  const cumulativeNowFraction = deploymentNowAmount / safeCapital;
  const currentClockAmount = clockTarget(safeCapital, cycleMonth);
  const currentClock = currentClockAmount / safeCapital;
  const formalFundingDelta = fundingDelta(safeCapital, cycleMonth, ledger);
  const formalFundingStatus = fundingStatus(formalFundingDelta);
  const remainingFunding = Math.max(0, safeCapital - contributed);
  const remainingDeployment = Math.max(0, safeCapital - Math.max(0, startingDeployed) - contributed);
  const monthsRemaining = Math.max(0, 120 - cycleMonth);
  const averageFutureContribution =
    monthsRemaining > 0 ? remainingFunding / monthsRemaining : remainingFunding;

  const normalizedPlannedContributionMonth = Math.max(1, Math.min(120, Math.round(Number(plannedContributionMonth) || cycleMonth || 1)));
  const normalizedPlannedContributionAmount = Math.max(0, Number(plannedContributionAmount) || 0);
  const projectedContributed = Math.min(safeCapital, contributed + normalizedPlannedContributionAmount);
  const projectedClock = clockTarget(safeCapital, normalizedPlannedContributionMonth);
  const projectedDelta = projectedContributed - projectedClock;
  const projectedMonthsRemaining = Math.max(0, 120 - normalizedPlannedContributionMonth);
  const projectedAverageFutureContribution =
    projectedMonthsRemaining > 0
      ? Math.max(0, safeCapital - projectedContributed) / projectedMonthsRemaining
      : Math.max(0, safeCapital - projectedContributed);
  const activePerScale = (liveFloor?.perScale ?? snapshot.current.perScale) as Array<{
    scaleYears: 20 | 30 | 50;
    target: number | null;
    agreement: number;
    nSignals: number;
    responseProfile?: {
      deploymentFractions: number[];
      q05Terminal: number[];
      pNonLoss: number[];
      meanTerminal: number[];
    } | null;
    riskBaselineProfile?: RiskBaselineProfileView | null;
    forwardPathProfile?: ForwardPathProfile | null;
    nearestAnalogDistance?: number | null;
  }>;
  const activeMutualChase = liveFloor?.mutualChase ?? snapshot.current.mutualChase;
  const activeAsOf = liveFloor?.asof ?? snapshot.current.asOf;
  const signalFloorAnchor = Math.max(
    0,
    Number(liveFloor?.coupledTarget ?? snapshot.current.coupledTargetAtPhaseZero) || 0,
  );
  const modelReferenceX = Math.min(1, Math.max(currentClock, signalFloorAnchor));
  const currentStatus = statusFor(fundingNowFraction, currentClock, cumulativeNowAmount, safeCapital);

  const responseCurves = useMemo(
    () =>
      activePerScale
        .filter(
          (s) =>
            s.responseProfile?.deploymentFractions?.length &&
            s.responseProfile?.q05Terminal?.length,
        )
        .map((s) => ({
          scale: s.scaleYears,
          xs: s.responseProfile!.deploymentFractions,
          ys: s.responseProfile!.q05Terminal,
        })),
    [activePerScale],
  );

  const maxResponse = responseCurves.length
    ? Math.max(...responseCurves.flatMap((c) => c.ys.map((x) => Number(x) || 0)))
    : 1;
  const responseDomain = [1, Math.max(2, maxResponse * 1.05)];

  const riskBaselineCurves = useMemo(
    () =>
      activePerScale
        .map((s) => {
          const profile = s.riskBaselineProfile;
          return profile
            ? {
                scale: s.scaleYears,
                xs: profile.deploymentFractions,
                gar: {
                  median: profile.garMedian,
                  q05: profile.garQ05,
                  q95: profile.garQ95,
                },
                maxDd: {
                  median: profile.maxDdMedian,
                  q05: profile.maxDdQ05,
                  q95: profile.maxDdQ95,
                },
                response: s.responseProfile ?? null,
                forward: s.forwardPathProfile ?? null,
              }
            : null;
        })
        .filter(Boolean) as Array<{
        scale: number;
        xs: number[];
        gar: { median: number[]; q05: number[]; q95: number[] };
        maxDd: { median: number[]; q05: number[]; q95: number[] };
        response: {
          deploymentFractions: number[];
          q05Terminal: number[];
          pNonLoss: number[];
          meanTerminal: number[];
        } | null;
        forward: ForwardPathProfile | null;
      }>,
    [activePerScale],
  );

  const ndx = activeMutualChase?.find((x) => x.channel === "NDX");
  const composite = activeMutualChase?.find((x) => x.channel === "NASDAQCOM");
  const ndxHandoff = ndx ? leaderHandoff(ndx.topology.leaderScaleBySegment) : null;

  const riskCurrentRows = useMemo(
    () =>
      riskBaselineCurves.map((curve) => {
        const gar = interpolateAt(curve.xs, curve.gar.median, cumulativeNowFraction);
        const garLo = interpolateAt(curve.xs, curve.gar.q05, cumulativeNowFraction);
        const garHi = interpolateAt(curve.xs, curve.gar.q95, cumulativeNowFraction);
        const maxDd = interpolateAt(curve.xs, curve.maxDd.median, cumulativeNowFraction);
        const maxDdLo = interpolateAt(curve.xs, curve.maxDd.q05, cumulativeNowFraction);
        const maxDdHi = interpolateAt(curve.xs, curve.maxDd.q95, cumulativeNowFraction);
        return {
          scale: curve.scale,
          gar,
          garLo,
          garHi,
          maxDd,
          maxDdLo,
          maxDdHi,
          garRangePosition: rangePosition(gar, garLo, garHi),
          maxDdRangePosition: rangePosition(maxDd, maxDdLo, maxDdHi),
        };
      }),
    [riskBaselineCurves, cumulativeNowFraction],
  );

  const riskBalance = useMemo(
    () => buildWeightedRiskBalance(riskBaselineCurves, cumulativeNowFraction),
    [riskBaselineCurves, cumulativeNowFraction],
  );

  const livePrice = liveContext.find((x) => x.symbol === "QQQ")?.price ?? null;
  const simulation = useMemo(
    () =>
      livePrice != null
        ? buildStrategySimulation({
            curves: riskBaselineCurves,
            currentMonth: month,
            currentPrice: livePrice,
            cumulativeNowFraction,
            modelTarget: modelReferenceX,
            ledger,
            startingDeployed: startingDeployed / safeCapital,
            marketTape,
            capital: safeCapital,
          })
        : null,
    [
      riskBaselineCurves,
      month,
      livePrice,
      cumulativeNowFraction,
      modelReferenceX,
      ledger,
      safeCapital,
      marketTape,
    ],
  );

  const ndxLeaderAtSim = leaderAtPhase(ndx?.topology.leaderScaleBySegment, cumulativeNowFraction);
  const compositeLeaderAtSim = leaderAtPhase(composite?.topology.leaderScaleBySegment, cumulativeNowFraction);
  const nearestAnalogDistance = medianNumbers(
    activePerScale
      .map((s) => s.nearestAnalogDistance)
      .filter((x): x is number => Number.isFinite(x)),
  );

  const capitalPoints = buildCapitalPoints(
    ledger,
    0,
    safeCapital,
    { month, cumulativeAmount: cumulativeNowAmount },
  );
  const startInputsComplete =
    startDraft.capital != null &&
    startDraft.month != null &&
    startDraft.startingDeployed != null &&
    startDraft.nav != null &&
    startDraft.frontloadPct != null &&
    startDraft.cashIn != null;

  const previewCapital = isStarted ? capital : startDraft.capital;
  const previewMonth = isStarted ? cycleMonth : startDraft.month;
  const previewOpening = isStarted ? startingDeployed : startDraft.startingDeployed;
  const previewNav = isStarted ? nav : startDraft.nav;
  const previewFrontload = isStarted ? frontloadPct : startDraft.frontloadPct;
  const previewCashIn = isStarted ? contributed : startDraft.cashIn;
  const previewClockAmount =
    previewCapital != null && previewMonth != null
      ? clockTarget(previewCapital, previewMonth)
      : null;
  const previewTarget =
    previewCapital != null && previewMonth != null && previewFrontload != null
      ? frontLoadedTarget(previewCapital, previewFrontload, previewMonth, currentMarketDate() ?? undefined)
      : null;
  const previewRemainingDeployment =
    previewCapital != null && previewOpening != null && previewCashIn != null
      ? Math.max(0, previewCapital - Math.max(0, previewOpening) - Math.max(0, previewCashIn))
      : null;
  const previewDeploymentGap =
    previewTarget != null && previewNav != null && previewRemainingDeployment != null
      ? deploymentGap(Math.max(0, previewNav), previewTarget, previewRemainingDeployment)
      : null;


  function currentMarketDate() {
    const qqq = liveContext.find((x) => x.symbol === "QQQ");
    return qqq?.regularMarketTime?.slice(0, 10) ?? qqq?.bars.at(-1)?.date ?? null;
  }

  function currentDynamicTradeIntent(marketDate: string, now = new Date().toISOString()) {
    const target = frontLoadedTarget(safeCapital, frontloadPct, cycleMonth, marketDate);
    return dynamicTradeIntent({
      id: "DEV_VITE_DYNAMIC_" + marketDate + "_M" + String(cycleMonth),
      now,
      cycleMonth,
      nav,
      target,
      remainingCapital: remainingDeployment,
    });
  }

  function corePriceLadder() {
    const ladder = liveMatch?.priceLadder;
    if (!ladder) return null;
    const keep = (rows: typeof ladder.add) =>
      rows.filter(
        (row) =>
          (row.horizon === 1 && Math.abs(row.touchProbability - 0.7) < 1e-9) ||
          (row.horizon === 5 && Math.abs(row.touchProbability - 0.5) < 1e-9) ||
          (row.horizon === 21 && Math.abs(row.touchProbability - 0.3) < 1e-9),
      );
    return {
      add: keep(ladder.add),
      reduce: keep(ladder.reduce),
      samples: ladder.samples,
      quality: ladder.quality,
    };
  }

  function sealDailyDeployment() {
    const marketDate = currentMarketDate();
    if (!marketDate) {
      setTransferNotice("DAILY DEPLOYMENT not recorded · QQQ market date unavailable");
      return;
    }
    const qqq = liveContext.find((x) => x.symbol === "QQQ");
    const row = dailyDeploymentRecord({
      recordedAt: new Date().toISOString(),
      marketDate,
      cycleMonth,
      capital: safeCapital,
      frontload: frontloadPct,
      nav,
      contributed,
      startingDeployed,
      qqqPrice: qqq?.price ?? liveMatch?.currentPrice ?? null,
      marketState: qqq?.marketState ?? null,
      dayRatio: liveMatch?.day.ratio ?? null,
      weekRatio: liveMatch?.week.ratio ?? null,
      monthRatio: liveMatch?.month.ratio ?? null,
      dayLevel: liveMatch?.day.level ?? "UNKNOWN",
      weekLevel: liveMatch?.week.level ?? "UNKNOWN",
      monthLevel: liveMatch?.month.level ?? "UNKNOWN",
      priceLadder: corePriceLadder(),
    });
    const entry: DailyDeploymentEntry = {
      ...row,
      id: globalThis.crypto?.randomUUID?.() ?? ("daily-" + marketDate + "-" + String(frontloadPct)),
    };
    setDailyDeploymentTape((current) => {
      // DAILY DEPLOYMENT TAPE is an audit snapshot series, not an editable ledger.
      // Keep at most one active observation for each marketDate + Frontload F. A
      // different F on the same date is a separate observation. Cancelled rows
      // remain in the audit history and may later be restored.
      if (current.some((x) => !x.voidedAt && x.marketDate === entry.marketDate && Math.abs(x.frontload - entry.frontload) < 1e-9)) {
        return current;
      }
      return [...current, entry]
        .sort((a, b) => a.marketDate.localeCompare(b.marketDate) || a.frontload - b.frontload)
        .slice(-3650);
    });
    setTransferNotice(
      "DAILY DEPLOYMENT sealed · " +
      marketDate +
      " · F " +
      (frontloadPct * 100).toFixed(0) +
      "% · " +
      row.status +
      " · available " +
      fmtUsd(row.buyAvailable, 2),
    );
  }

  useEffect(() => {
    if (!hasHydrated || !liveFetchedAt || !liveMatch) return;
    sealDailyDeployment();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasHydrated, liveFetchedAt]);

  useEffect(() => {
    // A RESET leaves the paper book empty. Live refresh may mark/refresh an
    // existing book, but must never implicitly create a new parent order.
    if (!hasHydrated || !liveFetchedAt || !liveMatch?.priceLadder || !orderMachine) return;
    const qqq = liveContext.find((x) => x.symbol === "QQQ");
    const price = qqq?.price ?? liveMatch.currentPrice;
    const marketDate = qqq?.regularMarketTime?.slice(0, 10) ?? qqq?.bars.at(-1)?.date ?? null;
    if (!(price != null && price > 0) || !marketDate) return;
    const intent = currentDynamicTradeIntent(marketDate);
    setOrderMachine((current) => {
      const seeded =
        current ??
        seedOrderMachine({
          now: new Date().toISOString(),
          marketDate,
          qqqPrice: price,
          nav,
          capital: safeCapital,
          contributed: contributed + Math.max(0, startingDeployed),
        });
      return syncOrderMachine({
        state: seeded,
        now: new Date().toISOString(),
        marketDate,
        currentPrice: price,
        ladder: liveMatch.priceLadder,
        intent,
      });
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasHydrated, liveFetchedAt]);

  function resetPaperBook() {
    // RESET is an operator stop/clear action. Do not seed a new machine here.
    // ARM CURRENT INTENT is the only path that creates a fresh paper book.
    setOrderMachine(null);
    setTransferNotice("PAPER BOOK RESET · all paper orders cleared · no new order armed");
  }

  function armPaperBook() {
    const qqq = liveContext.find((x) => x.symbol === "QQQ");
    const price = qqq?.price ?? liveMatch?.currentPrice ?? null;
    const marketDate = qqq?.regularMarketTime?.slice(0, 10) ?? liveMatch?.marketDate ?? null;
    if (!(price != null && marketDate) || !liveMatch?.priceLadder) return;
    const seeded =
      orderMachine ??
      resetOrderMachine({
        now: new Date().toISOString(),
        marketDate,
        qqqPrice: price,
        nav,
        capital: safeCapital,
        contributed: contributed + Math.max(0, startingDeployed),
      });
    setOrderMachine(
      syncOrderMachine({
        state: seeded,
        now: new Date().toISOString(),
        marketDate,
        currentPrice: price,
        ladder: liveMatch.priceLadder,
        intent: currentDynamicTradeIntent(marketDate),
      }),
    );
  }

  function fillPaperOrderFromDesk(orderId: string) {
    if (!orderMachine || !liveMatch) return;
    const price = liveMatch.currentPrice;
    if (!(price != null && price > 0)) return;
    const now = new Date().toISOString();
    const filled = fillPaperOrder(orderMachine, orderId, price, now);
    const qqq = liveContext.find((x) => x.symbol === "QQQ");
    const marketDate = qqq?.regularMarketTime?.slice(0, 10) ?? qqq?.bars.at(-1)?.date ?? orderMachine.marketDate;
    const next = syncOrderMachine({
      state: filled,
      now: new Date().toISOString(),
      marketDate,
      currentPrice: price,
      ladder: liveMatch.priceLadder,
      intent: currentDynamicTradeIntent(marketDate),
    });
    setOrderMachine(next);
  }

  function cancelPaperOrderFromDesk(orderId: string) {
    if (!orderMachine) return;
    setOrderMachine(cancelPaperOrder(orderMachine, orderId, new Date().toISOString()));
  }

  function restorePaperOrderFromDesk(orderId: string) {
    if (!orderMachine) return;
    setOrderMachine(restoreCancelledOrder(orderMachine, orderId, new Date().toISOString()));
  }

  function repricePaperOrderFromDesk(orderId: string) {
    if (!orderMachine || !liveMatch?.priceLadder) return;
    const qqq = liveContext.find((x) => x.symbol === "QQQ");
    const price = qqq?.price ?? liveMatch.currentPrice;
    const marketDate = qqq?.regularMarketTime?.slice(0, 10) ?? qqq?.bars.at(-1)?.date ?? null;
    if (!(price != null && marketDate)) return;
    const repriced = repricePaperOrder(
      orderMachine,
      orderId,
      new Date().toISOString(),
      marketDate,
      liveMatch.priceLadder,
      currentDynamicTradeIntent(marketDate),
    );
    setOrderMachine(
      syncOrderMachine({
        state: repriced,
        now: new Date().toISOString(),
        marketDate,
        currentPrice: price,
        ladder: liveMatch.priceLadder,
        intent: currentDynamicTradeIntent(marketDate),
      }),
    );
  }

  function recordPoint(kind: FloorEntryKind = "CONTRIBUTION") {
    const amount = kind === "CONTRIBUTION" ? actualNow : plannedWithdrawalAmount;
    if (!Number.isFinite(amount) || amount <= 0) return;
    if (kind === "CONTRIBUTION" && cumulativeNowAmount > safeCapital + 1e-8) return;

    const recordMonth =
      kind === "WITHDRAWAL"
        ? Math.max(0, Math.min(119, Math.round(Number(plannedWithdrawalMonth) || cycleMonth) - 1))
        : month;

    setLedger((entries) => [
      ...entries,
      {
        id: globalThis.crypto?.randomUUID?.() ?? String(Date.now()),
        recordedAt: new Date().toISOString(),
        asOf: activeAsOf,
        month: recordMonth,
        amount,
        kind,
        price: liveContext.find((x) => x.symbol === "QQQ")?.price ?? null,
        priceObservedAt: liveContext.find((x) => x.symbol === "QQQ")?.regularMarketTime ?? null,
        priceSource: liveContext.find((x) => x.symbol === "QQQ")?.price != null ? "YAHOO_FINANCE_CHART" : "UNAVAILABLE",
        voidedAt: null,
      },
    ]);
    setActualNow(0);
    setPlannedWithdrawalAmount(0);
  }

  function toggleDailyDeploymentVoid(entryId: string) {
    const now = new Date().toISOString();
    const next = toggleDailyDeploymentObservation(dailyDeploymentTape, entryId, now);
    const target = dailyDeploymentTape.find((entry) => entry.id === entryId);
    if (target?.voidedAt && next === dailyDeploymentTape) {
      setTransferNotice("DAILY DEPLOYMENT RESTORE blocked · active snapshot already exists for same DATE + F");
      return;
    }
    setDailyDeploymentTape(next);
  }

  function setStartDraftValue<K extends keyof StartDraft>(key: K, value: StartDraft[K]) {
    setStartDraft((current) => ({ ...current, [key]: value }));
  }

  function copyDefaultStart() {
    const payload = JSON.stringify(DEFAULT_START_TEMPLATE, null, 2);
    const write = navigator.clipboard?.writeText(payload);
    if (!write) {
      window.alert(payload);
      return;
    }
    write.then(
      () => setTransferNotice("DEFAULT START copied · blank template ready for manual fill"),
      () => window.alert(payload),
    );
  }

  function applyStartDraft() {
    const d = startDraft;
    if (
      d.capital == null ||
      d.month == null ||
      d.startingDeployed == null ||
      d.nav == null ||
      d.frontloadPct == null ||
      d.cashIn == null
    ) {
      setTransferNotice("START not applied · fill B, start month, OPENING DEPLOYED, NAV, Frontload and CASH IN");
      return;
    }
    const capitalValue = Math.max(1, d.capital);
    const monthValue = Math.max(1, Math.min(120, Math.round(d.month)));
    const openingValue = Math.max(0, Math.min(capitalValue, d.startingDeployed));
    const navValue = Math.max(0, d.nav);
    const frontloadValue = Math.max(0, Math.min(1, d.frontloadPct));
    const cashInValue = Math.max(0, d.cashIn);
    if (openingValue + cashInValue > capitalValue + 1e-8) {
      setTransferNotice("START not applied · OPENING DEPLOYED + CASH IN cannot exceed B");
      return;
    }

    const recordMonth = monthValue - 1;
    const initialEntry = cashInValue > 0
      ? {
          id: globalThis.crypto?.randomUUID?.() ?? ("start-cash-in-" + Date.now()),
          recordedAt: new Date().toISOString(),
          asOf: activeAsOf,
          month: recordMonth,
          amount: cashInValue,
          kind: "CONTRIBUTION" as const,
          price: liveContext.find((x) => x.symbol === "QQQ")?.price ?? null,
          priceObservedAt: liveContext.find((x) => x.symbol === "QQQ")?.regularMarketTime ?? null,
          priceSource: liveContext.find((x) => x.symbol === "QQQ")?.price != null
            ? "YAHOO_FINANCE_CHART" as const
            : "UNAVAILABLE" as const,
          voidedAt: null,
        }
      : null;

    setCapital(capitalValue);
    setStartingDeployed(openingValue);
    setMonth(recordMonth);
    setNav(navValue);
    setFrontloadPct(frontloadValue);
    setActualNow(0);
    setLedger(initialEntry ? [initialEntry] : []);
    setMarketTape([]);
    setDailyDeploymentTape([]);
    setOrderMachine(null);
    setTradeLedger([]);
    setIsStarted(true);
    setStartDraft({
      capital: capitalValue,
      month: monthValue,
      startingDeployed: openingValue,
      nav: navValue,
      frontloadPct: frontloadValue,
      cashIn: cashInValue,
    });
    setTransferNotice(
      "START applied · B " + fmtUsd(capitalValue, 2) +
      " · M" + monthValue +
      " · Opening " + fmtUsd(openingValue, 2) +
      " · CASH IN " + fmtUsd(cashInValue, 2),
    );
  }

  function clearLocal() {
    setIsStarted(false);
    setStartDraft(EMPTY_START_DRAFT);
    // CLEAR creates a genuinely blank new start; no numeric defaults are persisted.
    setLedger([]);
    setMarketTape([]);
    setDailyDeploymentTape([]);
    setFrontloadPct(0.4);
    setOrderMachine(null);
    setStartingDeployed(DEFAULT_STARTING_DEPLOYED);
    setActualNow(0);
    setCapital(DEFAULT_CAPITAL);
    setMonth(DEFAULT_MONTH);
    setNav(0);
    setTradeLedger([]);
    setTradeSide("BUY");
    setTradeAmountNow(0);
    setTradePriceNow(0);
    setTradeNoteNow("");
  }

  function voidLedgerEntry(entryId: string) {
    const now = new Date().toISOString();
    setLedger((entries) =>
      entries.map((entry) =>
        entry.id === entryId ? { ...entry, voidedAt: entry.voidedAt ? null : now } : entry,
      ),
    );
  }

  function recordActualTrade() {
    const amount = Number(tradeAmountNow);
    const price = Number(tradePriceNow);
    if (!(amount > 0) || !(price > 0)) {
      setTransferNotice("TRADE not recorded · amount and execution price are required");
      return;
    }
    const entry = createTradeEntry({
      side: tradeSide,
      amount,
      price,
      cycleMonth: month,
      source: "MANUAL",
      note: tradeNoteNow,
    });
    setTradeLedger((entries) => [...entries, entry]);
    setTradeAmountNow(0);
    setTradeNoteNow("");
    setTransferNotice(
      "ACTUAL " + tradeSide + " recorded · M" + String(month + 1) + " · " +
      fmtUsd(amount, 2) + " @ " + fmtUsd(price, 2),
    );
  }

  function voidTradeEntry(entryId: string) {
    const now = new Date().toISOString();
    setTradeLedger((entries) =>
      entries.map((entry) =>
        entry.id === entryId ? { ...entry, voidedAt: entry.voidedAt ? null : now } : entry,
      ),
    );
  }

  function buildTransferPayload() {
    return {
      schema: "rolling-floor.state.v4",
      exportedAt: new Date().toISOString(),
      asset: snapshot.asset,
      modelSnapshotAsOf: snapshot.asOf,
      horizonYears: snapshot.horizonYears,
      totalCapital: safeCapital,
      startingDeployed,
      month,
      entries: ledger,
      marketTape,
      dailyDeploymentTape,
      frontloadPct,
      orderMachine,
      nav,
      tradeLedger,
    };
  }

  function csvCell(value: unknown) {
    const raw = value == null ? "" : String(value);
    return '"' + raw.replaceAll('"', '""') + '"';
  }

  function downloadText(filename: string, text: string, mime = "application/json") {
    const blob = new Blob([text], { type: mime });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  function pushState() {
    downloadText(
      "rolling-floor-state-" + new Date().toISOString().slice(0, 10) + ".json",
      JSON.stringify(buildTransferPayload(), null, 2),
    );
    setTransferNotice("PUSH complete · full simulator state exported");
  }

  function pushDailyDeploymentCsv() {
    const header = [
      "marketDate","recordedAt","cycleMonth","frontload","capital","contributed","nav","target","signedGap",
      "buyAvailable","sellExcess","remainingCapital","qqqPrice","marketState","dayRatio","weekRatio","monthRatio",
      "dayLevel","weekLevel","monthLevel","status","source","voidedAt","priceLadder",
    ].join(",");
    const rows = dailyDeploymentTape
      .slice()
      .sort((a, b) => a.marketDate.localeCompare(b.marketDate) || a.frontload - b.frontload)
      .map((x) => [
        x.marketDate,x.recordedAt,x.cycleMonth,x.frontload,x.capital,x.contributed,x.nav,x.target,x.signedGap,
        x.buyAvailable,x.sellExcess,x.remainingCapital,x.qqqPrice ?? "",JSON.stringify(x.marketState ?? ""),
        x.dayRatio ?? "",x.weekRatio ?? "",x.monthRatio ?? "",JSON.stringify(x.dayLevel),
        JSON.stringify(x.weekLevel),JSON.stringify(x.monthLevel),JSON.stringify(x.status),JSON.stringify(x.source),
         JSON.stringify(x.voidedAt ?? ""),
        csvCell(JSON.stringify(x.priceLadder ?? null)),
      ].join(","));
    downloadText(
      "qqq-daily-deployment-tape-" + new Date().toISOString().slice(0, 10) + ".csv",
      [header, ...rows].join("\n") + "\n",
      "text/csv;charset=utf-8",
    );
    setTransferNotice("DAILY deployment CSV exported · " + dailyDeploymentTape.length + " observations");
  }

  function pushCsv() {
    const header = [
      "month",
      "kind",
      "recordedAt",
      "asOf",
      "amount",
      "price",
      "priceObservedAt",
      "priceSource",
      "status",
      "cumulativeContributionFraction",
      "clockFraction",
    ].join(",");
    let cumulativeContributionFraction = 0;
    const rows = ledger
      .slice()
      .sort((a, b) => a.month - b.month || a.recordedAt.localeCompare(b.recordedAt))
      .map((entry) => {
        if (!entry.voidedAt && (entry.kind ?? "CONTRIBUTION") === "CONTRIBUTION") {
          cumulativeContributionFraction += entry.amount / Math.max(1, safeCapital);
        }
        return [
          entry.month + 1,
          JSON.stringify(entry.kind ?? "CONTRIBUTION"),
          JSON.stringify(entry.recordedAt),
          JSON.stringify(entry.asOf),
          entry.amount.toFixed(2),
          entry.price == null ? "" : entry.price.toFixed(4),
          JSON.stringify(entry.priceObservedAt ?? ""),
          JSON.stringify(entry.priceSource ?? ""),
          JSON.stringify(entry.voidedAt ? "VOIDED" : "ACTIVE"),
          cumulativeContributionFraction.toFixed(8),
          ((entry.month + 1) / 120).toFixed(8),
        ].join(",");
      });
    downloadText(
      "rolling-floor-ledger-" + new Date().toISOString().slice(0, 10) + ".csv",
      [header, ...rows].join("\n") + "\n",
      "text/csv;charset=utf-8",
    );
    setTransferNotice("PUSH CSV complete · ledger exported");
  }

  function pushTradeCsv() {
    const header = ["month","side","recordedAt","amount","price","shares","source","orderId","status","note"].join(",");
    const rows = tradeLedger
      .slice()
      .sort((a, b) => a.cycleMonth - b.cycleMonth || a.recordedAt.localeCompare(b.recordedAt))
      .map((entry) => [
        entry.cycleMonth + 1,
        JSON.stringify(entry.side),
        JSON.stringify(entry.recordedAt),
        entry.amount.toFixed(2),
        entry.price.toFixed(4),
        entry.shares.toFixed(8),
        JSON.stringify(entry.source),
        JSON.stringify(entry.orderId ?? ""),
        JSON.stringify(entry.voidedAt ? "VOIDED" : "ACTIVE"),
        JSON.stringify(entry.note ?? ""),
      ].join(","));
    downloadText(
      "rolling-floor-trade-ledger-" + new Date().toISOString().slice(0, 10) + ".csv",
      [header, ...rows].join("\n") + "\n",
      "text/csv;charset=utf-8",
    );
    setTransferNotice("TRADE CSV exported · " + tradeLedger.length + " observations");
  }

  function copyLedger() {
    const payload = JSON.stringify(buildTransferPayload(), null, 2);
    const write = navigator.clipboard?.writeText(payload);
    if (!write) {
      window.alert(payload);
      return;
    }
    write.then(
      () => {
        setCopied(true);
        window.setTimeout(() => setCopied(false), 1200);
      },
      () => window.alert(payload),
    );
  }

  function openPull() {
    importRef.current?.click();
  }

  async function pullState(file: File) {
    try {
      const raw = JSON.parse(await file.text());
      if (raw && typeof raw === "object" && (raw as Record<string, unknown>).schema === "rolling-floor.default-start.v1") {
        const template = raw as Record<string, unknown>;
        setIsStarted(false);
        setStartDraft({
          capital: Number.isFinite(Number(template.plannedPrincipalB)) ? Number(template.plannedPrincipalB) : null,
          month: Number.isFinite(Number(template.startMonth)) ? Number(template.startMonth) : null,
          startingDeployed: Number.isFinite(Number(template.openingDeployed)) ? Number(template.openingDeployed) : null,
          nav: Number.isFinite(Number(template.accountNav)) ? Number(template.accountNav) : null,
          frontloadPct: Number.isFinite(Number(template.frontloadPct)) ? Number(template.frontloadPct) : null,
          cashIn: Number.isFinite(Number(template.cashIn)) ? Number(template.cashIn) : null,
        });
        setTransferNotice("DEFAULT START loaded · review inputs, then APPLY START");
        return;
      }
      const parsed = normalizeFloorState(raw);
      if (!parsed) throw new Error("invalid rolling-floor state");
      if (parsed.capital < 1 || parsed.startingDeployed > parsed.capital) {
        throw new Error("capital / startingDeployed invalid");
      }
      setIsStarted(true);
      setStartDraft({
        capital: parsed.capital,
        month: parsed.month + 1,
        startingDeployed: parsed.startingDeployed,
        nav: parsed.nav,
        frontloadPct: parsed.frontloadPct ?? 0.4,
        cashIn: actualContributed(parsed.entries),
      });
      setCapital(parsed.capital);
      setStartingDeployed(parsed.startingDeployed);
      setMonth(parsed.month);
      setLedger(parsed.entries);
      setMarketTape(parsed.marketTape);
      setDailyDeploymentTape(parsed.dailyDeploymentTape ?? []);
      setFrontloadPct(parsed.frontloadPct ?? 0.4);
      setOrderMachine(parsed.orderMachine ?? null);
      setNav(parsed.nav);
      setTradeLedger(parsed.tradeLedger ?? []);
      setTransferNotice(
        "PULL complete · " +
        parsed.entries.length +
        " ledger rows · " +
        parsed.marketTape.length +
        " market observations · NAV " +
        fmtUsd(parsed.nav, 2),
      );
    } catch (error) {
      setTransferNotice(
        "PULL failed · " +
        (error instanceof Error ? error.message : "invalid JSON"),
      );
    }
  }

  return (
    <Shell>
      <div className="grid gap-4">
        <Panel kicker="10Y CAPITAL FLOOR / FORMAL ACCOUNTING" title="本金骨架：Clock 定終點，Actual 記真實掏入，NAV 另記">
          <div className="grid gap-4 lg:grid-cols-4">
            <MetricCard
              kicker="CLOCK TARGET"
              title={fmtUsd(currentClockAmount, 2)}
              detail={"M" + cycleMonth + " / 120 · reference path only"}
            />
            <MetricCard
              kicker="ACTUAL CONTRIBUTED"
              title={fmtUsd(contributed, 2)}
              detail="只計 contribution ledger"
            />
            <MetricCard
              kicker="ACCOUNT NAV"
              title={fmtUsd(nav, 2)}
              detail="帳面值，獨立於 funding"
            />
            <MetricCard
              kicker="ACTUAL − CLOCK"
              title={(formalFundingDelta >= 0 ? "+" : "") + fmtUsd(formalFundingDelta, 2)}
              detail={formalFundingStatus + " · NAV 不參與"}
            />
          </div>

          <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_1fr]">
            <div className="rounded-md border border-line bg-elevated p-4">
              <p className="font-mono text-xs tracking-[0.14em] text-subtle">ACCOUNT INPUTS LIVE ABOVE ↑</p>
              <p className="mt-2 text-sm text-muted">B、CURRENT MONTH、ACCOUNT NAV、下一次入金與抽現，統一在最上面的 Operator Desk 編輯。呢區只顯示正式資金狀態。</p>
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              <MetricCard kicker="PLANNED B" title={fmtUsd(safeCapital, 2)} detail="locked once ledger has entries" />
              <MetricCard kicker="CURRENT MONTH" title={"M" + String(cycleMonth)} detail="formal clock position" />
              <MetricCard kicker="ACCOUNT NAV" title={fmtUsd(nav, 2)} detail="bookkeeping only" />
            </div>
          </div>
        </Panel>

        <Panel kicker="OPERATOR DESK / ONE-GLANCE ACCOUNT" title="所有會改數字的操作，都由這一欄開始">
          <div className="rounded-md border border-accent/40 bg-elevated p-4">
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
              <MoneyField label={ledger.length ? "Planned principal B · LOCKED" : "Planned principal B"} value={capital} onChange={(x) => !ledger.length && setCapital(Math.max(1, x))} />
              <NumberField label="Current cycle month" unit="mo" value={cycleMonth} min={1} max={120} step={1} onChange={(x) => setMonth(clampMonth(x - 1))} />
              <MoneyField label="Account NAV" value={nav} onChange={setNav} />
              <NumberField label="Frontload F · deployment only" unit="%" value={frontloadPct * 100} min={0} max={100} step={10} onChange={(x) => setFrontloadPct(Math.max(0, Math.min(1, x / 100)))} />
              <MetricCard kicker="NET EXTERNAL CASH" title={fmtUsd(contributed - withdrawn, 2)} detail="CASH IN − CASH OUT · BUY/SELL excluded" />
            </div>
            <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-5">
              <MetricCard kicker="OPENING DEPLOYED" title={fmtUsd(startingDeployed, 2)} detail="already deployed · not CASH IN" />
              <MetricCard kicker="DEPLOYED NOW" title={fmtUsd(deploymentNowAmount, 2)} detail="opening + CASH IN preview · not funding status" />
              <MetricCard kicker="FUNDING IN" title={fmtUsd(contributed, 2)} detail="active external contributions" />
              <MetricCard kicker="CASH OUT" title={fmtUsd(withdrawn, 2)} detail="active external withdrawals" />
              <MetricCard kicker="BUY" title={fmtUsd(actualBuyNotional, 2)} detail="internal trade · not funding" />
              <MetricCard kicker="SELL" title={fmtUsd(actualSellNotional, 2)} detail="internal trade · not cash-out" />
              <MetricCard kicker="PAPER" title={orderMachine ? fmtUsd(orderMachine.positionNav + orderMachine.deploymentReserve + orderMachine.harvestReserve, 2) : "—"} detail="paper only · not broker cash" />
            </div>
          </div>

          <div className="mt-4 grid gap-4 lg:grid-cols-3">
            <div className="rounded-md border border-accent/40 bg-elevated p-4">
              <p className="font-mono text-xs tracking-[0.14em] text-subtle">01 · EXTERNAL CASH IN</p>
              <p className="mt-1 text-sm text-muted">真正掏入計劃的本金。</p>
              <div className="mt-3 grid gap-3">
                <MoneyField label="Actual cash invested now" value={actualNow} onChange={setActualNow} />
                <button type="button" disabled={actualNow <= 0 || cumulativeNowAmount > safeCapital + 1e-8} onClick={() => recordPoint("CONTRIBUTION")} className="min-h-11 rounded-md border border-accent/60 bg-accent px-4 text-sm font-medium text-accent-fg disabled:cursor-not-allowed disabled:opacity-40">RECORD CASH IN · M{cycleMonth}</button>
              </div>
            </div>
            <div className="rounded-md border border-accent/40 bg-elevated p-4">
              <p className="font-mono text-xs tracking-[0.14em] text-subtle">02 · INTERNAL QQQ TRADE</p>
              <p className="mt-1 text-sm text-muted">BUY / SELL 只改持倉交易帳，不改 Funding。</p>
              <div className="mt-3 grid gap-3 sm:grid-cols-2">
                <label className="grid gap-1.5 text-sm"><span className="font-mono text-xs text-subtle">SIDE</span><select value={tradeSide} onChange={(e) => setTradeSide(e.target.value as TradeSide)} className="min-h-11 rounded-md border border-line bg-elevated px-3 font-mono text-sm outline-none"><option value="BUY">BUY</option><option value="SELL">SELL</option></select></label>
                <MoneyField label="Executed notional" value={tradeAmountNow} onChange={setTradeAmountNow} />
                <MoneyField label="Execution price" value={tradePriceNow} onChange={setTradePriceNow} />
                <label className="grid gap-1.5 text-sm"><span className="font-mono text-xs text-subtle">NOTE</span><input type="text" value={tradeNoteNow} onChange={(e) => setTradeNoteNow(e.target.value)} placeholder="optional" className="min-h-11 rounded-md border border-line bg-elevated px-3 font-mono text-sm outline-none" /></label>
              </div>
              <div className="mt-3 flex flex-wrap gap-2"><button type="button" onClick={() => setTradePriceNow(livePrice ?? 0)} disabled={livePrice == null} className="min-h-11 rounded-md border border-line px-3 font-mono text-xs text-muted hover:text-fg disabled:opacity-35">USE QQQ NOW</button><button type="button" onClick={recordActualTrade} disabled={tradeAmountNow <= 0 || tradePriceNow <= 0} className="min-h-11 rounded-md border border-accent px-3 font-mono text-xs hover:bg-elevated disabled:opacity-35">RECORD {tradeSide}</button></div>
            </div>
            <div className="rounded-md border border-accent/40 bg-elevated p-4">
              <p className="font-mono text-xs tracking-[0.14em] text-subtle">03 · EXTERNAL CASH OUT</p>
              <p className="mt-1 text-sm text-muted">真正抽離計劃的現金；與 QQQ SELL 完全不同。</p>
              <div className="mt-3 grid gap-3">
                <NumberField label="Cash-out month" unit="mo" value={Math.max(1, Math.min(120, Math.round(Number(plannedWithdrawalMonth) || cycleMonth)))} min={1} max={120} step={1} onChange={setPlannedWithdrawalMonth} />
                <MoneyField label="Cash-out amount" value={Math.max(0, plannedWithdrawalAmount)} onChange={setPlannedWithdrawalAmount} />
                <button type="button" onClick={() => recordPoint("WITHDRAWAL")} disabled={plannedWithdrawalAmount <= 0} className="min-h-11 rounded-md border border-lock/60 bg-elevated px-4 text-sm">RECORD CASH OUT</button>
              </div>
            </div>
          </div>

          <div className="mt-4 rounded-md border border-line bg-elevated p-4">
            <div className="flex flex-wrap items-center justify-between gap-3"><div><p className="font-mono text-xs tracking-[0.14em] text-subtle">04 · NEXT CONTRIBUTION PREVIEW</p><p className="mt-1 text-sm text-muted">只作預覽，不會自動入帳。</p></div>
              <div className="grid gap-3 sm:grid-cols-2"><NumberField label="Next contribution month" unit="mo" value={normalizedPlannedContributionMonth} min={1} max={120} step={1} onChange={setPlannedContributionMonth} /><MoneyField label="Next contribution amount" value={normalizedPlannedContributionAmount} onChange={setPlannedContributionAmount} /></div>
            </div>
            <div className="mt-3 grid gap-3 sm:grid-cols-3"><MetricCard kicker="PROJECTED CONTRIBUTED" title={fmtUsd(projectedContributed, 2)} detail={"after M" + normalizedPlannedContributionMonth} /><MetricCard kicker="PROJECTED Δ VS CLOCK" title={(projectedDelta >= 0 ? "+" : "") + fmtUsd(projectedDelta, 2)} detail="preview only" /><MetricCard kicker="NEW AVG FUTURE PACE" title={fmtUsd(projectedAverageFutureContribution, 2)} detail="to reach B at M120" /></div>
          </div>

          <div className="mt-4 rounded-md border border-line bg-elevated p-4">
            <div className="flex flex-wrap items-center justify-between gap-3"><div><p className="font-mono text-xs tracking-[0.14em] text-subtle">05 · RECENT RECORDS / CANCEL HERE</p><p className="mt-1 text-sm text-muted">CANCEL 不刪原始數字，只排除統計；RESTORE 可恢復。</p></div><Badge tone="mute">AUDIT-PRESERVING</Badge></div>
              <div className="mt-3 grid gap-2">
                {[
                  ...ledger.map((entry) => ({ key: "F-" + entry.id, timestamp: entry.recordedAt, month: entry.month + 1, label: entry.kind ?? "CONTRIBUTION", amount: entry.amount, price: entry.price, cancelled: Boolean(entry.voidedAt), onToggle: () => voidLedgerEntry(entry.id) })),
                  ...tradeLedger.map((entry) => ({ key: "T-" + entry.id, timestamp: entry.recordedAt, month: entry.cycleMonth + 1, label: "TRADE " + entry.side, amount: entry.amount, price: entry.price, cancelled: Boolean(entry.voidedAt), onToggle: () => voidTradeEntry(entry.id) }))
                ].sort((x, y) => y.timestamp.localeCompare(x.timestamp)).slice(0, 8).map((entry) => (
                  <div key={entry.key} className={"grid gap-2 rounded-md border border-line px-3 py-3 sm:grid-cols-[1fr_auto_auto_auto] sm:items-center " + (entry.cancelled ? "opacity-55" : "")}>
                    <div className="min-w-0"><p className="font-mono text-xs">{entry.label} · M{entry.month} · {fmtUsd(entry.amount, 2)}{entry.price != null ? " @ " + fmtUsd(entry.price, 2) : ""}</p><p className="mt-1 truncate text-[11px] text-subtle">{new Date(entry.timestamp).toLocaleString()}</p></div>
                    <Badge tone={entry.cancelled ? "lock" : "pass"}>{entry.cancelled ? "CANCELLED · EXCLUDED" : "ACTIVE"}</Badge>
                    <span className="font-mono text-[11px] text-muted">{entry.cancelled ? "保留原值" : "計入統計"}</span>
                    <button type="button" onClick={entry.onToggle} className={"min-h-9 rounded-md border px-3 font-mono text-[11px] " + (entry.cancelled ? "border-accent text-fg" : "border-line text-muted hover:text-fg")}>{entry.cancelled ? "RESTORE" : "CANCEL ENTRY"}</button>
                  </div>
                ))}
                {ledger.length + tradeLedger.length === 0 ? <p className="rounded-md border border-dashed border-line p-4 text-sm text-muted">尚未有任何 Funding / BUY / SELL 記錄。</p> : null}
              </div>
          </div>
        </Panel>
        <div className="grid gap-4 lg:grid-cols-3">
          <MetricCard
            kicker="MARKET STATE"
            title={liveFloor?.divergenceState ?? snapshot.current.divergenceStateAtPhaseZero}
            detail={
              "signals " +
              (liveFloor?.signals.length ?? snapshot.current.signalCount) +
              " · agreement " +
              fmtPct(liveFloor?.agreement ?? snapshot.current.agreementAtPhaseZero, 0)
            }
          />
          <MetricCard
            kicker="MUTUAL CHASE"
            title={ndx?.topology.state ?? "THIN"}
            detail={
              ndxHandoff
                ? "NDX: " + ndxHandoff.from + "Y → " + ndxHandoff.to + "Y near " + fmtPct(ndxHandoff.at, 0)
                : "no current handoff"
            }
          />
          <MetricCard
            kicker="DATA"
            title={activeAsOf}
            detail={liveFloor ? "LIVE MODEL · Yahoo + FRED + repo QQQ" : "verified snapshot · live model unavailable"}
          />
        </div>

        <Panel kicker="YAHOO DAILY SIGNAL · NOW ↔ HISTORY" title="每日檢查：現在市場狀態對照歷史">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm text-muted">
                Yahoo Finance daily snapshot；打開此頁只抓一次，不做秒級 polling。LIVE 只更新「現在」觀測，
                歷史比較仍以過去樣本計算。
              </p>
              {liveFetchedAt ? (
                <p className="mt-1 font-mono text-xs text-subtle">
                  fetched {new Date(liveFetchedAt).toISOString()} · source YAHOO_FINANCE_CHART
                </p>
              ) : null}
            </div>
            <button
              type="button"
              onClick={() => void refreshYahoo()}
              disabled={liveLoading}
              className="min-h-11 rounded-md border border-line px-3 text-xs text-muted hover:text-fg disabled:opacity-40"
            >
              {liveLoading ? "REFRESHING…" : "REFRESH YAHOO"}
            </button>
          </div>

          {liveError ? (
            <div className="mt-3 rounded-md border border-line bg-elevated p-3 text-xs text-muted">
              Yahoo warning: {liveError}
            </div>
          ) : null}

          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {(["QQQ", "^VIX", "^NDX", "^IXIC"] as const).map((symbol) => {
              const q = liveContext.find((x) => x.symbol === symbol);
              return (
                <div key={symbol} className="rounded-md border border-line bg-elevated p-3">
                  <p className="font-mono text-xs text-subtle">{symbol}</p>
                  <p className="mt-1 font-mono text-xl tabular-nums">
                    {q?.price == null ? "UNAVAILABLE" : q.price.toFixed(2)}
                  </p>
                  <p className="mt-1 text-xs text-subtle">
                    {q?.marketState ?? "UNKNOWN"} · {q?.regularMarketTime ? new Date(q.regularMarketTime).toISOString().slice(0, 10) : "—"}
                  </p>
                </div>
              );
            })}
          </div>

          {liveMatch ? (
            <div className="mt-4 grid gap-4 lg:grid-cols-[1.05fr_0.95fr]">
              <div className="rounded-md border border-line bg-elevated p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="font-mono text-xs tracking-[0.14em] text-subtle">QQQ LIVE STATE · SELF-RELATIVE</p>
                  <div className="flex flex-wrap gap-2">
                    <Badge tone="mute">5D DIR · {liveMatch.priceDir}</Badge>
                    <Badge tone={liveMatch.week.level === "EXTREME" || liveMatch.week.level === "SUPER_EXTREME" ? "lock" : "fragile"}>
                      WEEK RELVOL · {liveMatch.week.level}
                    </Badge>
                  </div>
                </div>
                <p className="mt-3 text-xs leading-relaxed text-muted">
                  DAY / WEEK / MONTH 都只和 QQQ 自己過去同尺度的絕對波動比較。<span className="font-mono">move</span> = 當前該尺度絕對變幅；
                  <span className="font-mono">hist mean</span> = 同尺度歷史平均絕對變幅；
                  <span className="font-mono">ratio</span> = move ÷ hist mean；
                  <span className="font-mono">pctl</span> = 在自己的歷史分布位置。Level 只由 ratio 分段得到，互不混用。
                </p>
                <div className="mt-3 grid gap-2">
                  {[liveMatch.day, liveMatch.week, liveMatch.month].map((scale) => (
                    <div key={scale.scale} className="grid gap-1 rounded-md border border-line/70 px-3 py-2 sm:grid-cols-[78px_1fr_auto] sm:items-center sm:gap-3">
                      <span className="font-mono text-xs text-subtle">{scale.scale}</span>
                      <span className="font-mono text-sm tabular-nums">
                        move {scale.currentMove == null ? "—" : fmtPct(scale.currentMove, 2)}
                        {" · "}hist mean {scale.meanMove == null ? "—" : fmtPct(scale.meanMove, 2)}
                        {" · "}ratio {scale.ratio == null ? "—" : scale.ratio.toFixed(2)}×
                        {" · "}level {scale.level}
                      </span>
                      <span className="font-mono text-xs tabular-nums text-muted">
                        pctl {fmtPct(scale.percentile, 0)}
                      </span>
                    </div>
                  ))}
                </div>
                <p className="mt-3 text-xs text-subtle">
                  5D DIR 是最近約 5 個交易日的方向分箱；WEEK RELVOL 只是週尺度 level 的摘要，不代表整體市場波動。
                </p>
              </div>

              <div className="rounded-md border border-line bg-elevated p-4">
                <p className="font-mono text-xs tracking-[0.14em] text-subtle">HISTORY MATCH · DESCRIPTIVE</p>
                <div className="mt-2 grid grid-cols-2 gap-3">
                  <MetricCard kicker="CURRENT QQQ" title={fmtUsd(liveMatch.currentPrice ?? 0, 2)} detail="Yahoo observation" />
                  <MetricCard kicker="MATCH COUNT" title={String(liveMatch.matches)} detail={liveMatch.matches < 5 ? "THIN sample" : "similar states"} />
                  <MetricCard kicker="MEDIAN 5D" title={fmtPct(liveMatch.median5d, 1)} detail="forward historical analogue" />
                  <MetricCard kicker="P(UP) 5D · DESCRIPTIVE" title={fmtPct(liveMatch.pUp5d, 0)} detail={String(liveMatch.matches) + " matched states"} />
                </div>
                <p className="mt-3 text-xs text-subtle">
                  1D {fmtPct(liveMatch.median1d, 1)} · 5D {fmtPct(liveMatch.median5d, 1)} · 21D {fmtPct(liveMatch.median21d, 1)} ·
                  reference dates {liveMatch.referenceDates.join(", ") || "none"} · n={liveMatch.matches}.
                </p>
              </div>
            </div>
          ) : (
            <div className="mt-4 rounded-md border border-dashed border-line p-4 text-sm text-muted">
              尚未取得 Yahoo QQQ；先不把 LIVE 當成決策輸入。
            </div>
          )}

          <p className="mt-3 text-xs text-subtle">
            LIVE price 是 Yahoo 觀測點；history match 只做描述性相似狀態。n 很小時（例如 n=1），MEDIAN / P(UP) 不應被讀成穩健統計結論，也不直接改寫 hard clock。
          </p>
        </Panel>

        <DailyDeploymentConsole
          capital={safeCapital}
          startingDeployed={startingDeployed}
          contributed={contributed}
          nav={nav}
          cycleMonth={cycleMonth}
          marketDate={
            liveContext.find((x) => x.symbol === "QQQ")?.regularMarketTime?.slice(0, 10) ??
            liveContext.find((x) => x.symbol === "QQQ")?.bars.at(-1)?.date ??
            null
          }
          liveContext={liveContext}
          liveMatch={liveMatch}
          frontload={frontloadPct}
          onFrontloadChange={setFrontloadPct}
          showFrontloadControl={false}
          tape={dailyDeploymentTape}
          onRecord={sealDailyDeployment}
          onExport={pushDailyDeploymentCsv}
           onToggleVoid={toggleDailyDeploymentVoid}
        />

        <OrderStateMachine
          state={orderMachine}
          currentPrice={liveMatch?.currentPrice ?? livePrice}
          target={frontLoadedTarget(safeCapital, frontloadPct, cycleMonth, currentMarketDate() ?? undefined)}
          marketDate={currentMarketDate()}
          canArm={
            liveMatch?.currentPrice != null &&
            currentMarketDate() != null &&
            liveMatch?.priceLadder != null
          }
          onFill={fillPaperOrderFromDesk}
          onCancel={cancelPaperOrderFromDesk}
          onReprice={repricePaperOrderFromDesk}
          onRestore={restorePaperOrderFromDesk}
          onReset={resetPaperBook}
          onArm={armPaperBook}
        />

        <Panel kicker="LIVE RESEARCH CONTEXT / NOW" title="目前市場觀測＋模型幾何（只作研究）">
          <div className="grid gap-4 lg:grid-cols-[1fr_1fr]">
            <div className="rounded-md border border-line bg-elevated p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="font-mono text-xs tracking-[0.14em] text-subtle">RESEARCH STATE</p>
                  <p className="mt-1 text-2xl font-semibold">NO FUNDING COMMAND</p>
                </div>
                <Badge tone="lock">{liveFloor ? "LIVE RESEARCH" : "FALLBACK RESEARCH"}</Badge>
              </div>
              <div className="mt-4 grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
                <MetricCard kicker="CLOCK" title={fmtPct(currentClock, 2)} detail="formal cumulative reference" />
                <MetricCard kicker="ACTUAL" title={fmtPct(cumulativeBeforePreview / safeCapital, 2)} detail="contribution ledger" />
                <MetricCard kicker="MODEL REF" title={fmtPct(modelReferenceX, 2)} detail="research marker only" />
                <MetricCard kicker="MODEL GAP" title={fmtPct(Math.abs(modelReferenceX - cumulativeBeforePreview / safeCapital), 2)} detail="does not authorize funding" />
                <MetricCard kicker="RISK BALANCE" title={riskBalance ? fmtPct(riskBalance.currentValue, 0) : "—"} detail="weighted GAR ↔ MaxDD position" />
                <MetricCard kicker="NOW / HISTORY" title={nearestAnalogDistance == null ? "—" : nearestAnalogDistance.toFixed(2)} detail="nearest state distance · lower = closer" />
              </div>
              <p className="mt-3 text-xs text-subtle">
                RESEARCH REFERENCE COMPOSITION · clock {fmtPct(currentClock, 2)} · signal anchor {fmtPct(signalFloorAnchor, 2)} · effective {fmtPct(modelReferenceX, 2)}.
                Research reference is displayed for context only. It never writes the ledger, changes B, changes NAV,
                changes CLOCK funding status, or emits BUY / SELL / less-fund / more-fund instructions.
              </p>
            </div>
            <div className="rounded-md border border-line bg-elevated p-4">
              <p className="font-mono text-xs tracking-[0.14em] text-subtle">CAPITAL-PHASE RELATIVE BASELINE</p>
              <div className="mt-3 grid gap-2">
                {riskCurrentRows.map((row) => (
                  <div key={row.scale} className="grid grid-cols-[55px_1fr_auto] items-center gap-3">
                    <span className="font-mono text-xs">{row.scale}Y</span>
                    <div className="grid gap-1">
                      <div className="h-1 overflow-hidden rounded bg-line">
                        <div className="h-full bg-accent" style={{ width: pctWidth(row.garRangePosition) }} />
                      </div>
                      <div className="h-1 overflow-hidden rounded bg-line">
                        <div className="h-full bg-fragile" style={{ width: pctWidth(row.maxDdRangePosition) }} />
                      </div>
                    </div>
                    <span className="font-mono text-[11px] tabular-nums">GAR {fmtPct(row.garRangePosition, 0)} · DD {fmtPct(row.maxDdRangePosition, 0)}</span>
                  </div>
                ))}
              </div>
              <p className="mt-3 text-xs text-subtle">呢兩條係「目前資本 deployment phase」在 20Y / 30Y / 50Y 自己歷史 GAR、MaxDD corridor 的位置；唔係 QQQ DAY / WEEK / MONTH Relative Vol，亦唔改 controller。</p>
            </div>
          </div>
        </Panel>

        <Panel kicker="PLANNER / READ ONLY" title="資金計劃摘要（輸入已集中在最上方）">
          <div className="grid gap-4 lg:grid-cols-3">
            <div className="rounded-md border border-line bg-elevated p-4"><p className="font-mono text-xs tracking-[0.14em] text-subtle">NEXT CONTRIBUTION</p><div className="mt-2 grid gap-2 sm:grid-cols-3"><MetricCard kicker="MONTH" title={"M" + String(normalizedPlannedContributionMonth)} detail="preview" /><MetricCard kicker="AMOUNT" title={fmtUsd(normalizedPlannedContributionAmount, 2)} detail="not yet booked" /><MetricCard kicker="PROJECTED Δ" title={(projectedDelta >= 0 ? "+" : "") + fmtUsd(projectedDelta, 2)} detail="vs CLOCK" /></div></div>
            <div className="rounded-md border border-line bg-elevated p-4"><p className="font-mono text-xs tracking-[0.14em] text-subtle">CASH OUT</p><div className="mt-2 grid gap-2 sm:grid-cols-2"><MetricCard kicker="NEXT" title={"M" + String(Math.max(1, Math.min(120, Math.round(Number(plannedWithdrawalMonth) || cycleMonth))))} detail="manual cash-out" /><MetricCard kicker="CUMULATIVE" title={fmtUsd(withdrawn, 2)} detail="active withdrawal ledger" /></div></div>
            <div className="rounded-md border border-line bg-elevated p-4"><p className="font-mono text-xs tracking-[0.14em] text-subtle">ACCOUNTING RULE</p><p className="mt-2 text-sm text-muted">External cash = CASH IN − CASH OUT。BUY/SELL 是內部持倉交換，不進 funding total，也不當成 withdrawal。</p></div>
          </div>
        </Panel>

        <Panel kicker="50Y LONG-SCALE BACKBONE" title="50Y：半真實長尺度骨架（歷史延伸 × QQQ 真實核心 × 未來推演）">
          {liveLongScale ? (
            <>
              <div className="grid gap-3 sm:grid-cols-4">
                <MetricCard kicker="HISTORY" title={liveLongScale.syntheticHistoryStartDate ?? "—"} detail={liveLongScale.syntheticHistoryMonths + " synthetic months before QQQ core"} />
                <MetricCard kicker="REAL QQQ CORE" title={liveLongScale.observedStartDate ?? "—"} detail={liveLongScale.observedEndDate + " observed"} />
                <MetricCard kicker="FUTURE" title={liveLongScale.future ? liveLongScale.future.horizonYears + "Y" : "—"} detail={liveLongScale.syntheticFutureMonths + " synthetic months"} />
                <MetricCard kicker="CALIBRATION" title={liveLongScale.calibration.qqqBeta == null ? "—" : "β " + liveLongScale.calibration.qqqBeta.toFixed(3)} detail={liveLongScale.calibration.qqqOverlapMonths + " QQQ/proxy overlap · proxy β " + (liveLongScale.calibration.proxyBeta == null ? "—" : liveLongScale.calibration.proxyBeta.toFixed(3))} />
              </div>
              <div className="mt-4 overflow-x-auto">
                <LongScaleChart profile={liveLongScale} />
              </div>
              <div className="mt-3 flex flex-wrap gap-3 text-xs text-muted">
                <span className="font-mono">● OBSERVED QQQ</span>
                <span className="font-mono">— SYNTHETIC HISTORY · proxy-calibrated</span>
                <span className="font-mono">- - SYNTHETIC FUTURE · proxy analog</span>
                <span className="font-mono">AUTHORITY · GEOMETRY ONLY</span>
              </div>
              <p className="mt-3 text-xs text-subtle">
                50Y 不冒充「50 年 QQQ 真實資料」：QQQ 可觀測核心保留原值；核心之前由 NASDAQ-100 / NASDAQ Composite
                的重疊校準延伸；核心之後用 proxy 的當前狀態相似歷史路徑形成 q05 / median / q95 未來場。
                這一層提供長記憶幾何，不直接取得 controller 資金權限。
              </p>
            </>
          ) : (
            <EmptyState text="LIVE FRED proxy 尚未取得；不把缺失的 50Y 歷史偽造成真實 QQQ。" />
          )}
        </Panel>

        <Panel kicker="MUTUAL-CHASE GEOMETRY" title="20Y ↔ 30Y ↔ 50Y：追趕場 / leader handoff / crossings">
          {responseCurves.length ? (
            <>
              <div className="overflow-x-auto">
                <ResponseChart
                  curves={responseCurves}
                  domain={responseDomain}
                  currentX={cumulativeNowFraction}
                  handoff={ndxHandoff}
                  mutualChase={activeMutualChase}
                />
              </div>
              <div className="mt-3 flex flex-wrap gap-3 text-xs text-muted">
                {responseCurves.map((c) => (
                  <span key={c.scale} className="font-mono">
                    {c.scale}Y · q05@0% {c.ys[0].toFixed(2)}× · q05@100% {(c.ys.at(-1) ?? 0).toFixed(2)}×
                  </span>
                ))}
              </div>
            </>
          ) : (
            <EmptyState text="response curve 不完整；停止畫圖，不猜資料。" />
          )}
          <p className="mt-3 text-xs text-subtle">
            主圖 = 三尺度 response 曲線；底部兩條 leader lane = NDX / NASDAQCOM 在每個 5% phase
            的相對領跑層；圓點 = pairwise curve crossing；右側讀數 = CURRENT phase 的 response slope
            排名。SIM 只定位你現在的位置，不等於「應投資百分比」。
          </p>
        </Panel>

        <Panel kicker="GAR / MAXDD HISTORICAL BASELINE" title="20Y / 30Y / 50Y：各自基線＋歷史出現區間">
          {riskBaselineCurves.length ? (
            <>
              <div className="overflow-x-auto">
                <RiskBaselineChart
                  curves={riskBaselineCurves}
                  currentX={cumulativeNowFraction}
                  modelX={modelReferenceX}
                />
              </div>
              <div className="mt-3 overflow-x-auto">
                <table className="w-full min-w-[760px] text-left text-xs">
                  <thead className="text-subtle">
                    <tr>
                      <th className="py-2">Y</th>
                      <th className="py-2">GAR @ SIM</th>
                      <th className="py-2">GAR historical range</th>
                      <th className="py-2">MaxDD @ SIM</th>
                      <th className="py-2">MaxDD historical range</th>
                      <th className="py-2">position</th>
                    </tr>
                  </thead>
                  <tbody>
                    {riskCurrentRows.map((row) => (
                      <tr key={row.scale} className="border-t border-line">
                        <td className="py-2 font-mono">{row.scale}Y</td>
                        <td className="py-2 font-mono tabular-nums">{fmtPct(row.gar, 2)}</td>
                        <td className="py-2 font-mono tabular-nums">{fmtPct(row.garLo, 2)} … {fmtPct(row.garHi, 2)}</td>
                        <td className="py-2 font-mono tabular-nums">{fmtPct(row.maxDd, 2)}</td>
                        <td className="py-2 font-mono tabular-nums">{fmtPct(row.maxDdLo, 2)} … {fmtPct(row.maxDdHi, 2)}</td>
                        <td className="py-2 font-mono tabular-nums">
                          GAR {fmtPct(row.garRangePosition, 0)} · DD {fmtPct(row.maxDdRangePosition, 0)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="mt-3 grid gap-2 sm:grid-cols-2">
                <div className="rounded-md border border-line bg-elevated p-3">
                  <p className="font-mono text-[11px] text-subtle">MUTUAL CHASE @ SIM</p>
                  <p className="mt-1 font-mono text-sm tabular-nums">
                    NDX {ndx?.topology.state ?? "THIN"} · leader {ndxLeaderAtSim == null ? "—" : ndxLeaderAtSim + "Y"}
                  </p>
                  <p className="mt-1 font-mono text-xs text-muted">
                    NASDAQCOM {composite?.topology.state ?? "THIN"} · leader {compositeLeaderAtSim == null ? "—" : compositeLeaderAtSim + "Y"}
                  </p>
                </div>
                <div className="rounded-md border border-line bg-elevated p-3">
                  <p className="font-mono text-[11px] text-subtle">VERIFIED BASELINE</p>
                  <p className="mt-1 font-mono text-sm tabular-nums">
                    run #{snapVerifiedRun()} · as-of {snapshot.current.asOf}
                  </p>
                  <p className="mt-1 text-xs text-muted">
                    baseline follows the verified bridge artifact; no live value is mixed into this historical layer.
                  </p>
                </div>
              </div>
              <p className="mt-3 text-xs text-subtle">
                實線 = 每個 Y 層級自己的歷史 GAR / MaxDD 中位基線；淡區 = 同一歷史樣本的 q05–q95
                出現範圍；粗淡區 = 三尺度共同 envelope。SIM 線隨目前實際累積投入移動，MODEL 線是現有
                10Y floor controller 的位置。互追 leader 只描述相對 response 斜率，不控制資金。
              </p>
            </>
          ) : (
            <EmptyState text="目前 snapshot 尚未帶入 GAR / MaxDD baseline；不猜資料，待同一模型重跑後顯示。" />
          )}
        </Panel>

        <Panel kicker="WEIGHTED GAR ↔ MAXDD" title="三尺度合權後：相對風險－回報互追區間（非資金比例）">
          {riskBalance ? (
            <>
              <div className="overflow-x-auto">
                <CombinedRiskChart
                  balance={riskBalance}
                  currentX={cumulativeNowFraction}
                />
              </div>
              <p className="mt-3 text-xs text-subtle">
                X 軸 = cumulative deployment phase（0–100%）；Y 軸 = GAR / MaxDD 在各自歷史 q05–q95
                中的相對位置（0–100%），所以左端出現 30% / 40% 並不代表已投入 30% / 40% 資金。
                灰帶 = 三尺度 envelope；粗線 = response-slope dynamic weight 後的 GAR↔MaxDD 合權線；
                SIM 垂線 = 你目前實際累積投入位置。這張圖不回寫 controller。
              </p>
            </>
          ) : (
            <EmptyState text="GAR / MaxDD combined geometry unavailable。" />
          )}
        </Panel>

        <Panel kicker="10Y PATH SIMULATOR" title="現實紀錄 × NOW analog → 10Y 模擬走勢">
          {simulation ? (
            <>
              <div className="overflow-x-auto">
                <SimulationChart simulation={simulation} currentX={month} />
              </div>
              <div className="mt-3 flex flex-wrap gap-3 text-xs text-muted">
                <span className="font-mono">CURRENT MONTH {month + 1}/120</span>
                <span className="font-mono">QQQ {livePrice == null ? "—" : fmtUsd(livePrice, 2)}</span>
                <span className="font-mono">MARKET TAPE {marketTape.length} obs</span>
                <span className="font-mono">SIM MODEL {liveFloor ? "LIVE" : "FALLBACK UNAVAILABLE"}</span>
              </div>
              <p className="mt-3 text-xs text-subtle">
                已觀測月份使用 market tape；目前月份以 Yahoo 現價錨定；未來段用 NOW 匹配得到的歷史
                10Y analog path 投影。每次 refresh、月份推進、實際投入與實際買入價都會改變這條線。
              </p>
            </>
          ) : (
            <EmptyState text="等待 LIVE rolling-floor model 與 forward analog path；未取得就不猜 10Y 曲線。" />
          )}
        </Panel>

        <Panel kicker="CAPITAL TAPE / RULE CORRIDOR" title="你輸入的數字會立即反映在這條 10Y 路徑">
          <div className="grid gap-5 lg:grid-cols-[1fr_320px]">
            <div className="overflow-x-auto">
              <CapitalChart
                points={capitalPoints}
                currentClock={currentClock}
                currentStatus={currentStatus}
              />
            </div>

            <div className="grid content-start gap-3">
              <div className="rounded-md border border-accent/40 bg-elevated p-3">
                <p className="font-mono text-xs text-subtle">PRIMARY INPUT MOVED ↑</p>
                <p className="mt-1 text-sm text-muted">日常輸入統一放在頁首 Operator Desk。此區只看 10Y 路徑及匯入／匯出，避免同一個數字有兩個輸入入口。</p>
                <div className="mt-3 grid grid-cols-2 gap-3">
                  <MetricCard kicker="CURRENT MONTH" title={"M" + String(cycleMonth)} detail="由 Operator Desk 控制" />
                  <MetricCard kicker="UNRECORDED INPUT" title={actualNow > 0 ? fmtUsd(actualNow, 2) : "—"} detail="按 RECORD 前仍未入帳" />
                </div>
              </div>

              <input
                ref={importRef}
                type="file"
                accept="application/json,.json"
                className="hidden"
                onChange={(event) => {
                  const file = event.target.files?.[0];
                  if (file) void pullState(file);
                  event.currentTarget.value = "";
                }}
              />
              <div className="grid gap-2 sm:grid-cols-4">
                <button
                  type="button"
                  onClick={pushState}
                  className="min-h-11 rounded-md border border-accent/60 bg-accent/10 px-3 text-xs font-medium text-fg hover:bg-accent/20"
                >
                  PUSH JSON
                </button>
                <button
                  type="button"
                  onClick={openPull}
                  className="min-h-11 rounded-md border border-line px-3 text-xs text-muted hover:text-fg"
                >
                  PULL JSON
                </button>
                <button
                  type="button"
                  onClick={pushCsv}
                  className="min-h-11 rounded-md border border-line px-3 text-xs text-muted hover:text-fg"
                >
                  DOWNLOAD CSV
                </button>
                <button
                  type="button"
                  onClick={copyLedger}
                  className="min-h-11 rounded-md border border-line px-3 text-xs text-muted hover:text-fg"
                >
                  {copied ? "COPIED" : "COPY JSON"}
                </button>
              </div>
              {transferNotice ? (
                <p className="font-mono text-[11px] text-subtle">{transferNotice}</p>
              ) : null}
              <button
                type="button"
                onClick={clearLocal}
                className="min-h-11 rounded-md border border-line px-3 text-xs text-subtle hover:text-fg"
              >
                CLEAR LOCAL
              </button>
            </div>
          </div>

          <LedgerTable entries={ledger} capital={safeCapital} onToggleVoid={voidLedgerEntry} />

          <div className="mt-5 rounded-md border border-accent/40 bg-elevated p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="font-mono text-xs tracking-[0.14em] text-subtle">ACTUAL TRADE / EXECUTION JOURNAL</p>
                <p className="mt-1 text-sm text-muted">記真正已成交的 BUY / SELL；呢本帳獨立於 Funding Ledger，唔會改 Actual Contributed。</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Badge tone="pass">BUY {fmtUsd(actualBuyNotional, 2)}</Badge>
                <Badge tone="fragile">SELL {fmtUsd(actualSellNotional, 2)}</Badge>
              </div>
            </div>
            <div className="rounded-md border border-accent/40 bg-elevated p-3">
              <p className="font-mono text-xs text-subtle">PRIMARY INPUT MOVED ↑</p>
              <p className="mt-1 text-sm text-muted">BUY / SELL 輸入已集中到頁首 Operator Desk。下面只保留完整成交歷史、CANCEL / RESTORE 與 CSV。</p>
            </div>
            <TradeLedgerTable entries={tradeLedger} onToggleVoid={voidTradeEntry} />
            <div className="mt-3 flex flex-wrap items-center gap-3">
              <button type="button" onClick={pushTradeCsv} className="min-h-10 rounded-md border border-line px-3 text-xs text-muted hover:text-fg">
                DOWNLOAD TRADE CSV
              </button>
              <span className="text-xs text-subtle">CANCEL ENTRY 只撤銷該筆帳的統計影響；原記錄保留，並標成 CANCELLED · EXCLUDED，之後可 RESTORE。</span>
            </div>
          </div>
        </Panel>

        <div className="grid gap-4 lg:grid-cols-2">
          <Panel kicker="CURRENT REFERENCE" title="三尺度現在的基準位置">
            <div className="grid gap-2">
              {activePerScale.map((s) => (
                <div key={s.scaleYears} className="grid grid-cols-[70px_1fr_auto] items-center gap-3 rounded-md border border-line px-3 py-2">
                  <span className="font-mono text-sm">{s.scaleYears}Y</span>
                  <div className="h-1.5 overflow-hidden rounded-full bg-elevated">
                    <div className="h-full bg-accent" style={{ width: pctWidth(s.target) }} />
                  </div>
                  <span className="font-mono text-xs tabular-nums text-muted">{fmtPct(s.target, 2)}</span>
                </div>
              ))}
            </div>
          </Panel>

          <Panel kicker="SEMANTIC LOCK" title="監視層同資金層分開">
            <div className="mb-3">
              <a href="/floor-research" className="text-sm text-accent underline decoration-dotted underline-offset-4">
                Research evidence → 只讀，不產生資金指令
              </a>
            </div>
            <div className="grid gap-2 text-sm text-muted">
              <p>Hard clock rail = M0 = 0%；第 n 月（畫面 1..120）參考累積位置 = n / 120。</p>
              <p>Funding Status = Actual Contributed − CLOCK；低於 Clock = BEHIND，高於 = AHEAD。這不是每月買入指令。</p>
              <p>Mutual-chase = 20Y / 30Y / 50Y 的 response geometry，暫時只監視。</p>
              <p>QQQ = observed outcome；NDX / NASDAQ Composite = proxy state channels。</p>
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              <Badge tone="pass">RESEARCH-ONLY</Badge>
              <Badge tone="lock">NO GUARANTEED BREAK-EVEN</Badge>
              <Badge tone={composite?.topology.state === "CONVERGENT" ? "pass" : "fragile"}>
                NASDAQCOM {composite?.topology.state ?? "THIN"}
              </Badge>
            </div>
          </Panel>
        </div>
      </div>
    </Shell>
  );
}

function validLedgerEntry(value: unknown): value is LedgerEntry {
  if (!value || typeof value !== "object") return false;
  const x = value as Partial<LedgerEntry>;
  return (
    typeof x.id === "string" &&
    typeof x.recordedAt === "string" &&
    typeof x.asOf === "string" &&
    (x.kind === undefined || x.kind === "CONTRIBUTION" || x.kind === "WITHDRAWAL") &&
    Number.isFinite(x.month) &&
    Number.isFinite(x.amount) &&
    x.amount > 0 &&
    x.month >= 0 &&
    x.month <= 119 &&
    (x.voidedAt == null || typeof x.voidedAt === "string")
  );
}

function validOrderMachineState(value: unknown): value is OrderMachineState {
  if (!value || typeof value !== "object") return false;
  const x = value as Partial<OrderMachineState>;
  if (
    x.schema !== "qqq-order-machine.v2" ||
    typeof x.seededAt !== "string" ||
    typeof x.updatedAt !== "string" ||
    typeof x.marketDate !== "string" ||
    !Number.isFinite(x.markPrice) ||
    !(x.markPrice > 0) ||
    !Number.isFinite(x.positionNav) ||
    x.positionNav < 0 ||
    !Number.isFinite(x.deploymentReserve) ||
    x.deploymentReserve < 0 ||
    !Number.isFinite(x.harvestReserve) ||
    x.harvestReserve < 0 ||
    (x.positionShares !== undefined && (!Number.isFinite(Number(x.positionShares)) || Number(x.positionShares) < 0)) ||
    !Number.isInteger(x.nextBuyRung) ||
    !Number.isInteger(x.nextSellRung) ||
    !Array.isArray(x.orders)
  ) return false;
  return x.orders.every((order) => {
    if (!order || typeof order !== "object") return false;
    const row = order as Record<string, unknown>;
    return (
      typeof row.id === "string" &&
      (row.side === "BUY" || row.side === "SELL") &&
      (row.rung === "NEAR" || row.rung === "MID" || row.rung === "DEEP") &&
      (row.horizon === 1 || row.horizon === 5 || row.horizon === 21) &&
      (row.status === "ARMED" || row.status === "STALE" || row.status === "TOUCHED" || row.status === "FILLED" || row.status === "CANCELLED" || row.status === "REPLACED" || row.status === "SUPERSEDED") &&
      typeof row.parentIntentId === "string" &&
      Number.isFinite(Number(row.parentIntentNotional)) &&
      Number(row.parentIntentNotional) > 0 &&
      Number.isFinite(Number(row.touchProbability)) &&
      Number(row.touchProbability) >= 0 &&
      Number(row.touchProbability) <= 1 &&
      Number.isFinite(Number(row.limitPrice)) &&
      Number(row.limitPrice) > 0 &&
      Number.isFinite(Number(row.suggestedAmount)) &&
      Number(row.suggestedAmount) >= 0 &&
      typeof row.marketDate === "string" &&
      Number.isFinite(Number(row.sourcePrice)) &&
      Number(row.sourcePrice) > 0 &&
      typeof row.createdAt === "string" &&
      (row.touchedAt == null || typeof row.touchedAt === "string") &&
      (row.filledAt == null || typeof row.filledAt === "string") &&
      (row.filledPrice == null || (Number.isFinite(Number(row.filledPrice)) && Number(row.filledPrice) > 0)) &&
      (row.filledAmount == null || (Number.isFinite(Number(row.filledAmount)) && Number(row.filledAmount) >= 0)) &&
      (row.cancelledAt == null || typeof row.cancelledAt === "string")
    );
  });
}

function TradeLedgerTable({
  entries,
  onToggleVoid,
}: {
  entries: TradeLedgerEntry[];
  onToggleVoid: (entryId: string) => void;
}) {
  const rows = entries.slice().sort(
    (a, b) => a.cycleMonth - b.cycleMonth || a.recordedAt.localeCompare(b.recordedAt),
  );
  if (!rows.length) {
    return (
      <p className="mt-4 rounded-md border border-dashed border-line p-4 text-sm text-muted">
        尚未記錄實際 BUY / SELL。呢本帳只記 executed trade，不改 Funding Ledger。
      </p>
    );
  }
  return (
    <div className="mt-4 overflow-x-auto">
      <table className="w-full min-w-[900px] text-left text-xs">
        <thead className="text-[11px] text-subtle">
          <tr>
            <th className="py-2">month</th>
            <th className="py-2">date</th>
            <th className="py-2">side</th>
            <th className="py-2">notional</th>
            <th className="py-2">price</th>
            <th className="py-2">shares</th>
            <th className="py-2">source</th>
            <th className="py-2">status</th>
            <th className="py-2">action</th>
          </tr>
        </thead>
        <tbody>
          {rows.slice().reverse().map((entry) => (
            <tr key={entry.id} className={"border-t border-line " + (entry.voidedAt ? "opacity-50" : "")}>
              <td className="py-2 font-mono">{entry.cycleMonth + 1}</td>
              <td className="py-2 font-mono">{entry.recordedAt}</td>
              <td className="py-2 font-mono">{entry.side}</td>
              <td className="py-2 font-mono tabular-nums">{fmtUsd(entry.amount, 2)}</td>
              <td className="py-2 font-mono tabular-nums">{fmtUsd(entry.price, 2)}</td>
              <td className="py-2 font-mono tabular-nums">{entry.shares.toFixed(6)}</td>
              <td className="py-2 font-mono">{entry.source}</td>
              <td className="py-2">
                <Badge tone={entry.voidedAt ? "lock" : entry.side === "SELL" ? "fragile" : "pass"}>
                  {entry.voidedAt ? "CANCELLED" : "ACTIVE"}
                </Badge>
              </td>
              <td className="py-2">
                <button type="button" onClick={() => onToggleVoid(entry.id)} className="min-h-8 rounded-md border border-line px-2 font-mono text-[11px] text-muted hover:text-fg">
                  {entry.voidedAt ? "RESTORE" : "CANCEL ENTRY"}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function validTradeLedgerEntry(value: unknown): value is TradeLedgerEntry {
  if (!value || typeof value !== "object") return false;
  const x = value as Partial<TradeLedgerEntry>;
  return (
    typeof x.id === "string" &&
    typeof x.recordedAt === "string" &&
    Number.isFinite(x.cycleMonth) &&
    x.cycleMonth >= 0 &&
    x.cycleMonth <= 119 &&
    (x.side === "BUY" || x.side === "SELL") &&
    Number.isFinite(x.amount) && x.amount > 0 &&
    Number.isFinite(x.price) && x.price > 0 &&
    Number.isFinite(x.shares) && x.shares > 0 &&
    (x.source === "MANUAL" || x.source === "PAPER_FILL") &&
    (x.orderId == null || typeof x.orderId === "string") &&
    (x.note == null || typeof x.note === "string") &&
    (x.voidedAt == null || typeof x.voidedAt === "string")
  );
}

function validDailyDeploymentEntry(value: unknown): value is DailyDeploymentEntry {
  if (!value || typeof value !== "object") return false;
  const x = value as Partial<DailyDeploymentEntry>;
  return (
    typeof x.id === "string" &&
    typeof x.recordedAt === "string" &&
    typeof x.marketDate === "string" &&
    Number.isFinite(x.cycleMonth) &&
    Number.isFinite(x.capital) &&
    x.capital > 0 &&
    Number.isFinite(x.frontload) &&
    x.frontload >= 0 &&
    x.frontload <= 1 &&
    Number.isFinite(x.nav) &&
    x.nav >= 0 &&
    Number.isFinite(x.contributed) &&
    x.contributed >= 0 &&
    Number.isFinite(x.target) &&
    Number.isFinite(x.buyAvailable) &&
    x.buyAvailable >= 0 &&
    Number.isFinite(x.sellExcess) &&
    x.sellExcess >= 0 &&
    (x.status === "BUY_AVAILABLE" || x.status === "ON_TARGET" || x.status === "SELL_EXCESS") &&
    (x.priceLadder === undefined || x.priceLadder === null || typeof x.priceLadder === "object") &&
     x.source === "YAHOO_FINANCE_CHART" &&
     (x.voidedAt == null || typeof x.voidedAt === "string")
  );
}

function validMarketTapeEntry(value: unknown): value is MarketTapeEntry {
  if (!value || typeof value !== "object") return false;
  const x = value as Partial<MarketTapeEntry>;
  return (
    typeof x.observedAt === "string" &&
    typeof x.marketDate === "string" &&
    Number.isFinite(x.month) &&
    Number.isFinite(x.price) &&
    x.month >= 0 &&
    x.month <= 119 &&
    x.price > 0
  );
}

function statusFor(fraction: number, clock: number, amount: number, capital: number): EntryStatus {
  if (amount > capital + 1e-8) return "OVER_CAPITAL";
  if (fraction < clock - 0.005) return "BELOW_CLOCK";
  if (fraction > clock + 0.005) return "AHEAD";
  return "ON_CLOCK";
}

function buildCapitalPoints(
  entries: LedgerEntry[],
  startingDeployed: number,
  capital: number,
  preview: { month: number; cumulativeAmount: number },
) {
  const sorted = entries
    .filter((entry) => (entry.kind ?? "CONTRIBUTION") === "CONTRIBUTION" && !entry.voidedAt)
    .sort((a, b) => a.month - b.month || a.recordedAt.localeCompare(b.recordedAt));
  let cumulative = Math.max(0, startingDeployed);
  const points: Array<{ month: number; fraction: number; preview?: boolean }> = [];

  for (const entry of sorted) {
    cumulative += Math.max(0, entry.amount);
    points.push({
      month: entry.month,
      fraction: cumulative / Math.max(1, capital),
    });
  }

  points.push({
    month: preview.month,
    fraction: preview.cumulativeAmount / Math.max(1, capital),
    preview: true,
  });

  return points.sort(
    (a, b) => a.month - b.month || Number(Boolean(a.preview)) - Number(Boolean(b.preview)),
  );
}

function leaderHandoff(leaders: Array<number | null>) {
  for (let i = 1; i < leaders.length; i++) {
    const prev = leaders[i - 1];
    const next = leaders[i];
    if (prev != null && next != null && prev !== next) {
      return { from: prev, to: next, at: i * 0.05 };
    }
  }
  return null;
}

function leaderAtPhase(leaders: Array<number | null> | undefined, phase: number) {
  if (!leaders?.length) return null;
  const index = Math.max(0, Math.min(leaders.length - 1, Math.floor(Math.max(0, Math.min(0.999999, phase)) * leaders.length)));
  return leaders[index] ?? null;
}

function snapVerifiedRun() {
  const run = (snapshot as typeof snapshot & { verifiedSource?: { runNumber?: number } }).verifiedSource?.runNumber;
  return Number.isFinite(run) ? run : "—";
}

function interpolateAt(xs: number[], ys: number[], x: number) {
  if (!xs.length || !ys.length) return 0;
  if (x <= xs[0]) return ys[0] ?? 0;
  const last = xs.length - 1;
  if (x >= xs[last]) return ys[last] ?? 0;

  for (let i = 1; i < xs.length; i++) {
    const x1 = xs[i - 1];
    const x2 = xs[i];
    if (x <= x2) {
      const y1 = ys[i - 1] ?? 0;
      const y2 = ys[i] ?? y1;
      const t = (x - x1) / Math.max(1e-12, x2 - x1);
      return y1 + (y2 - y1) * t;
    }
  }
  return ys[last] ?? 0;
}

function rangePosition(value: number, lo: number, hi: number) {
  if (!Number.isFinite(value) || !Number.isFinite(lo) || !Number.isFinite(hi)) return 0;
  if (Math.abs(hi - lo) < 1e-12) return value >= hi ? 1 : 0;
  return Math.max(0, Math.min(1, (value - lo) / (hi - lo)));
}

function pctWidth(value: number | null | undefined) {
  const x = Math.max(0, Math.min(1, Number(value) || 0));
  return x * 100 + "%";
}

function EmptyState({ text }: { text: string }) {
  return <div className="rounded-md border border-dashed border-line p-4 text-sm text-muted">{text}</div>;
}

function MoneyField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
}) {
  return (
    <label className="grid gap-1.5 text-sm">
      <span className="font-mono text-xs text-subtle">{label}</span>
      <span className="flex min-h-11 items-center overflow-hidden rounded-md border border-line bg-elevated focus-within:border-accent">
        <span className="px-3 text-muted">$</span>
        <input
          type="number"
          min={0}
          step="0.01"
          inputMode="decimal"
          value={value}
          onChange={(e) => onChange(Number(e.target.value) || 0)}
          className="min-w-0 flex-1 bg-transparent px-2 pr-3 font-mono tabular-nums outline-none"
        />
      </span>
    </label>
  );
}

function NumberField({
  label,
  unit,
  value,
  onChange,
  min,
  max,
  step,
}: {
  label: string;
  unit: string;
  value: number;
  onChange: (value: number) => void;
  min: number;
  max: number;
  step: number;
}) {
  return (
    <label className="grid gap-1.5 text-sm">
      <span className="font-mono text-xs text-subtle">{label}</span>
      <span className="flex min-h-11 items-center overflow-hidden rounded-md border border-line bg-elevated focus-within:border-accent">
        <input
          type="number"
          min={min}
          max={max}
          step={step}
          inputMode="numeric"
          value={value}
          onChange={(e) => onChange(Number(e.target.value) || 0)}
          className="min-w-0 flex-1 bg-transparent px-3 font-mono tabular-nums outline-none"
        />
        <span className="border-l border-line px-3 text-muted">{unit}</span>
      </span>
    </label>
  );
}

function MetricCard({
  kicker,
  title,
  detail,
}: {
  kicker: string;
  title: string;
  detail: string;
}) {
  return (
    <div className="rounded-xl border border-line bg-surface p-4">
      <p className="font-mono text-xs tracking-[0.14em] text-subtle">{kicker}</p>
      <p className="mt-1 text-xl font-medium">{title}</p>
      <p className="mt-1 font-mono text-xs text-muted">{detail}</p>
    </div>
  );
}


function responseSlopeAt(profile: { deploymentFractions: number[]; q05Terminal: number[] } | null, phase: number) {
  if (!profile || profile.q05Terminal.length < 2) return 0;
  let i = Math.floor(Math.max(0, Math.min(0.999999, phase)) * (profile.q05Terminal.length - 1));
  i = Math.max(0, Math.min(profile.q05Terminal.length - 2, i));
  const x1 = profile.deploymentFractions[i] ?? 0;
  const x2 = profile.deploymentFractions[i + 1] ?? x1;
  const y1 = profile.q05Terminal[i] ?? 0;
  const y2 = profile.q05Terminal[i + 1] ?? y1;
  return x2 > x1 ? (y2 - y1) / (x2 - x1) : 0;
}

function scaleWeightsAtPhase(
  curves: Array<{
    scale: number;
    xs: number[];
    response: { deploymentFractions: number[]; q05Terminal: number[]; pNonLoss: number[]; meanTerminal: number[] } | null;
  }>,
  phase: number,
) {
  const raw = curves.map((c) => Math.abs(responseSlopeAt(c.response, phase)));
  const sum = raw.reduce((a, b) => a + b, 0);
  if (sum > 1e-12) return raw.map((x) => x / sum);
  return raw.map(() => 1 / Math.max(1, raw.length));
}

type RiskBalanceData = {
  xs: number[];
  scaleLines: Array<{ scale: number; values: number[] }>;
  weighted: number[];
  envelopeLow: number[];
  envelopeHigh: number[];
  currentValue: number;
};

function medianNumbers(xs: number[]) {
  if (!xs.length) return null;
  const sorted = [...xs].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[mid] : ((sorted[mid - 1] ?? 0) + (sorted[mid] ?? 0)) / 2;
}

function normalizedPosition(value: number, lo: number, hi: number) {
  if (!Number.isFinite(value) || !Number.isFinite(lo) || !Number.isFinite(hi)) return 0.5;
  if (Math.abs(hi - lo) < 1e-12) return 0.5;
  return Math.max(0, Math.min(1, (value - lo) / (hi - lo)));
}

function buildWeightedRiskBalance(
  curves: Array<{
    scale: number;
    xs: number[];
    gar: { median: number[]; q05: number[]; q95: number[] };
    maxDd: { median: number[]; q05: number[]; q95: number[] };
    response: { deploymentFractions: number[]; q05Terminal: number[]; pNonLoss: number[]; meanTerminal: number[] } | null;
    forward: ForwardPathProfile | null;
  }>,
  currentX: number,
): RiskBalanceData | null {
  if (!curves.length) return null;
  const xs = curves[0].xs;
  const scaleLines = curves.map((curve) => ({
    scale: curve.scale,
    values: xs.map((_, i) => {
      const gar = normalizedPosition(curve.gar.median[i] ?? 0, curve.gar.q05[i] ?? 0, curve.gar.q95[i] ?? 0);
      const dd = normalizedPosition(curve.maxDd.median[i] ?? 0, curve.maxDd.q05[i] ?? 0, curve.maxDd.q95[i] ?? 0);
      return (gar + dd) / 2;
    }),
  }));
  const weighted = xs.map((_, i) => {
    const phase = xs[i] ?? 0;
    const weights = scaleWeightsAtPhase(curves, phase);
    return scaleLines.reduce((sum, line, j) => sum + (line.values[i] ?? 0) * (weights[j] ?? 0), 0);
  });
  const envelopeLow = xs.map((_, i) => Math.min(...scaleLines.map((line) => line.values[i] ?? 0)));
  const envelopeHigh = xs.map((_, i) => Math.max(...scaleLines.map((line) => line.values[i] ?? 0)));

  return {
    xs,
    scaleLines,
    weighted,
    envelopeLow,
    envelopeHigh,
    currentValue: interpolateAt(xs, weighted, currentX),
  };
}

type StrategySimulation = {
  months: number[];
  projectedMedian: Array<number | null>;
  projectedQ05: Array<number | null>;
  projectedQ95: Array<number | null>;
  observed: Array<{ month: number; equity: number; price: number }>;
  currentMonth: number;
  currentEquity: number;
};

function portfolioEquity(price: number, cash: number, lots: Array<{ amount: number; entry: number }>) {
  return cash + lots.reduce((sum, lot) => sum + lot.amount * (price / Math.max(1e-12, lot.entry)), 0);
}

function baseLotsAtCurrent(
  currentPrice: number,
  startingFraction: number,
  ledger: LedgerEntry[],
  capitalFraction: number,
  currentMonth: number,
) {
  const lots: Array<{ amount: number; entry: number }> = [];
  if (startingFraction > 0) lots.push({ amount: startingFraction, entry: currentPrice });
  for (const entry of ledger) {
    if (
      (entry.kind ?? "CONTRIBUTION") === "CONTRIBUTION" &&
      entry.month <= currentMonth &&
      entry.amount > 0
    ) {
      lots.push({
        amount: entry.amount / Math.max(1, capitalFraction),
        entry: entry.price && entry.price > 0 ? entry.price : currentPrice,
      });
    }
  }
  return lots;
}

function buildProjectedPortfolio(
  path: number[],
  currentPrice: number,
  currentMonth: number,
  currentDeployed: number,
  modelTarget: number,
  startingFraction: number,
  ledger: LedgerEntry[],
  capitalFraction: number,
) {
  const points: Array<{ month: number; equity: number }> = [];
  const lots = baseLotsAtCurrent(currentPrice, startingFraction, ledger, capitalFraction, currentMonth);
  let cash = Math.max(0, 1 - currentDeployed);
  const currentEquity = portfolioEquity(currentPrice, cash, [
    ...lots,
    { amount: Math.max(0, currentDeployed - (startingFraction + ledger.filter((e) => (e.kind ?? "CONTRIBUTION") === "CONTRIBUTION" && e.month <= currentMonth)
        .reduce((s, e) => s + e.amount / Math.max(1, capitalFraction), 0))), entry: currentPrice },
  ].filter((x) => x.amount > 0));
  points.push({ month: currentMonth, equity: currentEquity });

  let deployed = currentDeployed;
  const actualRecordedFraction =
    startingFraction +
    ledger
      .filter((entry) => (entry.kind ?? "CONTRIBUTION") === "CONTRIBUTION" && entry.month <= currentMonth)
      .reduce((sum, entry) => sum + Math.max(0, entry.amount) / Math.max(1, capitalFraction), 0);
  const previewFraction = Math.max(0, currentDeployed - actualRecordedFraction);
  if (previewFraction > 0) lots.push({ amount: previewFraction, entry: currentPrice });

  cash = Math.max(0, 1 - deployed);
  for (let month = currentMonth + 1; month <= 120; month++) {
    const offset = month - currentMonth;
    const price = currentPrice * (path[offset] ?? path.at(-1) ?? 1);
    const clock = month / 120;
    const target = Math.min(1, Math.max(deployed, clock, modelTarget));
    const add = Math.max(0, target - deployed);
    if (add > 0) {
      lots.push({ amount: add, entry: price });
      cash -= add;
      deployed += add;
    }
    points.push({ month, equity: portfolioEquity(price, cash, lots) });
  }
  return points;
}

function buildStrategySimulation({
  curves,
  currentMonth,
  currentPrice,
  cumulativeNowFraction,
  modelTarget,
  ledger,
  startingDeployed,
  marketTape,
  capital,
}: {
  curves: Array<{
    scale: number;
    xs: number[];
    response: { deploymentFractions: number[]; q05Terminal: number[]; pNonLoss: number[]; meanTerminal: number[] } | null;
    forward: ForwardPathProfile | null;
    gar: { median: number[]; q05: number[]; q95: number[] };
    maxDd: { median: number[]; q05: number[]; q95: number[] };
  }>;
  currentMonth: number;
  currentPrice: number;
  cumulativeNowFraction: number;
  modelTarget: number;
  ledger: LedgerEntry[];
  startingDeployed: number;
  marketTape: MarketTapeEntry[];
  capital: number;
}): StrategySimulation | null {
  const forwardCurves = curves.filter((c) => c.forward?.median.length === 121);
  if (!forwardCurves.length) return null;

  const weights = scaleWeightsAtPhase(forwardCurves, cumulativeNowFraction);
  const project = (kind: "median" | "q05" | "q95") =>
    Array.from({ length: 121 }, (_, i) =>
      forwardCurves.reduce(
        (sum, curve, j) => sum + (curve.forward?.[kind][i] ?? 1) * (weights[j] ?? 0),
        0,
      ),
    );

  const medianPath = project("median");
  const q05Path = project("q05");
  const q95Path = project("q95");

  const medianProjected = buildProjectedPortfolio(
    medianPath,
    currentPrice,
    currentMonth,
    cumulativeNowFraction,
    modelTarget,
    startingDeployed,
    ledger,
    capital,
  );
  const lowProjected = buildProjectedPortfolio(
    q05Path,
    currentPrice,
    currentMonth,
    cumulativeNowFraction,
    modelTarget,
    startingDeployed,
    ledger,
    capital,
  );
  const highProjected = buildProjectedPortfolio(
    q95Path,
    currentPrice,
    currentMonth,
    cumulativeNowFraction,
    modelTarget,
    startingDeployed,
    ledger,
    capital,
  );

  const tape = Array.isArray(marketTape) ? marketTape : [];
  const actual = [...tape]
    .filter((x) => x.month <= currentMonth)
    .sort((a, b) => a.month - b.month || a.marketDate.localeCompare(b.marketDate))
    .map((tapePoint, index, all) => {
      const firstPrice = all[0]?.price ?? currentPrice;
      const lots = baseLotsAtCurrent(
        firstPrice,
        startingDeployed,
        ledger,
        capital,
        tapePoint.month,
      );
      const deployed =
        startingDeployed +
        ledger
          .filter((entry) =>
            (entry.kind ?? "CONTRIBUTION") === "CONTRIBUTION" &&
            entry.month <= tapePoint.month,
          )
          .reduce((sum, entry) => sum + Math.max(0, entry.amount) / Math.max(1, capital), 0);
      const cash = Math.max(0, 1 - deployed);
      return {
        month: tapePoint.month,
        equity: portfolioEquity(tapePoint.price, cash, lots),
        price: tapePoint.price,
      };
    });

  return {
    months: Array.from({ length: 121 }, (_, i) => i),
    projectedMedian: medianProjected.map((row) => row.equity),
    projectedQ05: lowProjected.map((row) => row.equity),
    projectedQ95: highProjected.map((row) => row.equity),
    observed: actual,
    currentMonth,
    currentEquity: medianProjected[0]?.equity ?? 1,
  };
}

function CombinedRiskChart({
  balance,
  currentX,
}: {
  balance: RiskBalanceData;
  currentX: number;
}) {
  const W = 1000, H = 360, L = 58, R = 24, T = 22, B = 48;
  const plotW = W - L - R, plotH = H - T - B;
  const x = (v: number) => L + Math.max(0, Math.min(1, v)) * plotW;
  const y = (v: number) => T + (1 - Math.max(0, Math.min(1, v))) * plotH;
  const band = balance.xs
    .map((v, i) => [x(v), y(balance.envelopeHigh[i] ?? 0)])
    .concat(
      balance.xs
        .slice()
        .reverse()
        .map((v, i) => [x(v), y(balance.envelopeLow[balance.envelopeLow.length - 1 - i] ?? 0)]),
    )
    .map((p) => p.join(","))
    .join(" ");
  const palette = ["var(--color-accent)", "var(--color-fragile)", "var(--color-muted)"];

  return (
    <svg viewBox={"0 0 " + W + " " + H} className="min-w-[760px] w-full" role="img" aria-label="Weighted GAR MaxDD relative balance">
      <rect x={L} y={T} width={plotW} height={plotH} fill="var(--color-elevated)" opacity="0.45" rx="8" />
      {[0, 0.25, 0.5, 0.75, 1].map((v) => (
        <g key={v}>
          <line x1={L} x2={W - R} y1={y(v)} y2={y(v)} stroke="var(--color-line)" />
          <text x={L - 8} y={y(v) + 4} textAnchor="end" fill="var(--color-subtle)" fontSize="11">{Math.round(v * 100)}%</text>
        </g>
      ))}
      <polygon points={band} fill="var(--color-accent)" opacity="0.08" />
      {balance.scaleLines.map((line, idx) => (
        <polyline
          key={line.scale}
          points={balance.xs.map((v, i) => x(v) + "," + y(line.values[i] ?? 0)).join(" ")}
          fill="none"
          stroke={palette[idx] ?? "var(--color-fg)"}
          strokeWidth="1.7"
          opacity="0.72"
        />
      ))}
      <polyline
        points={balance.xs.map((v, i) => x(v) + "," + y(balance.weighted[i] ?? 0)).join(" ")}
        fill="none"
        stroke="var(--color-fg)"
        strokeWidth="4"
      />
      <line x1={x(currentX)} x2={x(currentX)} y1={T} y2={T + plotH} stroke="var(--color-fragile)" strokeDasharray="4 4" />
      <circle cx={x(currentX)} cy={y(balance.currentValue)} r="6" fill="var(--color-fg)" />
      <text x={Math.min(W - 170, x(currentX) + 6)} y={T + 16} fill="var(--color-fragile)" fontSize="11">SIM PHASE {fmtPct(currentX, 1)}</text>
      <text x={Math.min(W - 180, x(currentX) + 6)} y={y(balance.currentValue) - 10} fill="var(--color-fg)" fontSize="11">RELATIVE {fmtPct(balance.currentValue, 0)}</text>
      <text x={L} y={H - 22} fill="var(--color-subtle)" fontSize="11">0–100% cumulative deployment phase</text>
      {balance.scaleLines.map((line, idx) => (
        <text key={"legend-" + line.scale} x={W - 220 + idx * 62} y={H - 22} fill={palette[idx] ?? "var(--color-fg)"} fontSize="11">{line.scale}Y</text>
      ))}
      <text x={L} y={H - 5} fill="var(--color-subtle)" fontSize="10">normalized GAR / MaxDD historical position · dynamic mutual-chase weights</text>
    </svg>
  );
}

function SimulationChart({
  simulation,
  currentX,
}: {
  simulation: StrategySimulation;
  currentX: number;
}) {
  const W = 1000, H = 390, L = 64, R = 24, T = 22, B = 48;
  const plotW = W - L - R, plotH = H - T - B;
  const values = [
    ...simulation.projectedQ05,
    ...simulation.projectedQ95,
    ...simulation.projectedMedian,
    ...simulation.observed.map((x) => x.equity),
  ].filter((x): x is number => Number.isFinite(x));
  const lo = Math.min(...values, 0.5);
  const hi = Math.max(...values, 1.1);
  const pad = Math.max(0.05, (hi - lo) * 0.08);
  const domain: [number, number] = [lo - pad, hi + pad];
  const x = (month: number) => L + Math.max(0, Math.min(120, month)) / 120 * plotW;
  const y = (value: number) =>
    T + (domain[1] - value) / Math.max(0.0001, domain[1] - domain[0]) * plotH;

  const projectedBand = simulation.months
    .filter((m) => m >= simulation.currentMonth)
    .map((m) => [x(m), y(simulation.projectedQ95[m] ?? 1)])
    .concat(
      simulation.months
        .filter((m) => m >= simulation.currentMonth)
        .reverse()
        .map((m) => [x(m), y(simulation.projectedQ05[m] ?? 1)]),
    )
    .map((p) => p.join(","))
    .join(" ");

  return (
    <svg viewBox={"0 0 " + W + " " + H} className="min-w-[760px] w-full" role="img" aria-label="10 year hybrid observed and simulated portfolio path">
      <rect x={L} y={T} width={plotW} height={plotH} fill="var(--color-elevated)" opacity="0.45" rx="8" />
      {[0.75, 1, 1.25, 1.5, 2].filter((v) => v >= domain[0] && v <= domain[1]).map((v) => (
        <g key={v}>
          <line x1={L} x2={W - R} y1={y(v)} y2={y(v)} stroke="var(--color-line)" />
          <text x={L - 10} y={y(v) + 4} textAnchor="end" fill="var(--color-subtle)" fontSize="11">{v.toFixed(2)}×</text>
        </g>
      ))}
      <polygon points={projectedBand} fill="var(--color-accent)" opacity="0.1" />
      <polyline
        points={simulation.months.map((m) => x(m) + "," + y(simulation.projectedMedian[m] ?? 1)).join(" ")}
        fill="none"
        stroke="var(--color-accent)"
        strokeWidth="3"
        strokeDasharray="7 4"
      />
      {simulation.observed.length > 0 ? (
        <>
          <polyline
            points={simulation.observed.map((p) => x(p.month) + "," + y(p.equity)).join(" ")}
            fill="none"
            stroke="var(--color-fg)"
            strokeWidth="3"
          />
          {simulation.observed.map((p) => (
            <circle key={String(p.month) + "-" + p.price} cx={x(p.month)} cy={y(p.equity)} r="4" fill="var(--color-fg)" />
          ))}
        </>
      ) : null}
      <line x1={x(currentX)} x2={x(currentX)} y1={T} y2={T + plotH} stroke="var(--color-fragile)" strokeDasharray="4 4" opacity="0.9" />
      <text x={Math.min(W - 150, x(currentX) + 6)} y={T + 16} fill="var(--color-fragile)" fontSize="11">NOW · month {currentX + 1}</text>
      {[0, 24, 48, 72, 96, 120].map((m) => (
        <text key={m} x={x(m)} y={H - 22} textAnchor="middle" fill="var(--color-subtle)" fontSize="11">{m}m</text>
      ))}
      <text x={L} y={H - 5} fill="var(--color-subtle)" fontSize="10">solid = observed tape · dashed = live analog simulation · band = analog q05–q95</text>
    </svg>
  );
}

function RiskBaselineChart({
  curves,
  currentX,
  modelX,
}: {
  curves: Array<{
    scale: number;
    xs: number[];
    gar: { median: number[]; q05: number[]; q95: number[] };
    maxDd: { median: number[]; q05: number[]; q95: number[] };
  }>;
  currentX: number;
  modelX: number;
}) {
  if (!curves.length) return <EmptyState text="GAR / MaxDD baseline 不完整。" />;

  const W = 1000, H = 620, L = 72, R = 24, T = 22, B = 46;
  const plotW = W - L - R;
  const sectionH = 238;
  const gap = 72;
  const garTop = T;
  const ddTop = T + sectionH + gap;
  const x = (v: number) => L + Math.max(0, Math.min(1, v)) * plotW;

  function domainFor(
    metric: "gar" | "maxDd",
  ): [number, number] {
    const values = curves.flatMap((c) =>
      [...c[metric].q05, ...c[metric].q95].filter(Number.isFinite),
    );
    if (!values.length) return [0, 1];
    const lo = Math.min(...values);
    const hi = Math.max(...values);
    const pad = Math.max((hi - lo) * 0.08, metric === "gar" ? 0.005 : 0.01);
    return [lo - pad, hi + pad];
  }

  const garDomain = domainFor("gar");
  const ddDomain = domainFor("maxDd");
  const yFor = (v: number, top: number, domain: [number, number]) =>
    top + (domain[1] - v) / Math.max(0.0001, domain[1] - domain[0]) * sectionH;

  function bandPoints(metric: "gar" | "maxDd", top: number, domain: [number, number]) {
    const xs = curves[0].xs;
    const upper = xs.map((_, i) =>
      Math.max(...curves.map((c) => c[metric].q95[i] ?? domain[0])),
    );
    const lower = xs.map((_, i) =>
      Math.min(...curves.map((c) => c[metric].q05[i] ?? domain[0])),
    );
    return xs
      .map((v, i) => [x(v), yFor(upper[i], top, domain)])
      .concat(
        xs
          .slice()
          .reverse()
          .map((v, i) => {
            const original = lower.length - 1 - i;
            return [x(v), yFor(lower[original], top, domain)];
          }),
      )
      .map((p) => p.join(","))
      .join(" ");
  }

  const palette = ["var(--color-accent)", "var(--color-fragile)", "var(--color-muted)"];

  const renderMetric = (
    metric: "gar" | "maxDd",
    top: number,
    domain: [number, number],
    title: string,
  ) => (
    <g>
      <rect x={L} y={top} width={plotW} height={sectionH} fill="var(--color-elevated)" opacity="0.45" rx="8" />
      <polygon points={bandPoints(metric, top, domain)} fill="var(--color-accent)" opacity="0.09" />
      {[0, 0.25, 0.5, 0.75, 1].map((f) => {
        const value = domain[0] + (domain[1] - domain[0]) * f;
        return (
          <g key={String(metric) + f}>
            <line x1={L} x2={W - R} y1={yFor(value, top, domain)} y2={yFor(value, top, domain)} stroke="var(--color-line)" />
            <text x={L - 10} y={yFor(value, top, domain) + 4} textAnchor="end" fill="var(--color-subtle)" fontSize="11">
              {fmtPct(value, 1)}
            </text>
          </g>
        );
      })}
      <text x={L + 8} y={top + 16} fill="var(--color-fg)" fontSize="12" fontWeight="600">{title}</text>
      {curves.map((curve, idx) => (
        <g key={String(metric) + curve.scale}>
          <polyline
            points={curve.xs.map((v, i) => x(v) + "," + yFor(curve[metric].median[i], top, domain)).join(" ")}
            fill="none"
            stroke={palette[idx] ?? "var(--color-fg)"}
            strokeWidth="3"
            strokeLinejoin="round"
            strokeLinecap="round"
          />
          <circle
            cx={x(currentX)}
            cy={yFor(interpolateAt(curve.xs, curve[metric].median, currentX), top, domain)}
            r="5"
            fill={palette[idx] ?? "var(--color-fg)"}
          />
          <polyline
            points={curve.xs.map((v, i) => x(v) + "," + yFor(curve[metric].q05[i], top, domain)).join(" ")}
            fill="none"
            stroke={palette[idx] ?? "var(--color-fg)"}
            strokeWidth="1"
            opacity="0.24"
          />
          <polyline
            points={curve.xs.map((v, i) => x(v) + "," + yFor(curve[metric].q95[i], top, domain)).join(" ")}
            fill="none"
            stroke={palette[idx] ?? "var(--color-fg)"}
            strokeWidth="1"
            opacity="0.24"
          />
        </g>
      ))}
      <line x1={x(modelX)} x2={x(modelX)} y1={top} y2={top + sectionH} stroke="var(--color-fragile)" strokeDasharray="5 5" opacity="0.85" />
      <line x1={x(currentX)} x2={x(currentX)} y1={top} y2={top + sectionH} stroke="var(--color-fg)" strokeDasharray="3 3" opacity="0.9" />
      <text x={Math.min(W - 140, x(modelX) + 6)} y={top + 32} fill="var(--color-fragile)" fontSize="11">MODEL {fmtPct(modelX, 1)}</text>
      <text x={Math.min(W - 120, x(currentX) + 6)} y={top + 48} fill="var(--color-fg)" fontSize="11">SIM {fmtPct(currentX, 1)}</text>
    </g>
  );

  return (
    <svg viewBox={"0 0 " + W + " " + H} className="min-w-[760px] w-full" role="img" aria-label="Historical GAR and MaxDD baseline corridors by 20Y 30Y 50Y">
      {renderMetric("gar", garTop, garDomain, "GAR · geometric annual rate over fixed 10Y terminal horizon")}
      {renderMetric("maxDd", ddTop, ddDomain, "MaxDD · deployment-path drawdown over fixed 10Y horizon")}
      {[0, 0.25, 0.5, 0.75, 1].map((v) => (
        <text key={v} x={x(v)} y={H - 20} textAnchor="middle" fill="var(--color-subtle)" fontSize="11">
          {Math.round(v * 100)}%
        </text>
      ))}
      <text x={L} y={H - 4} fill="var(--color-subtle)" fontSize="11">
        relative deployment phase · each Y-scale retains its own historical baseline; no GAR/MaxDD weighting is fed back into the controller
      </text>
    </svg>
  );
}

function LongScaleChart({ profile }: { profile: LongScaleProfile }) {
  const W = 1120, H = 500, L = 76, R = 28, T = 24, B = 56;
  const plotW = W - L - R, plotH = H - T - B;
  const currentValue =
    profile.points.filter((p) => p.provenance === "OBSERVED_QQQ").at(-1)?.value ?? 1;
  const normalized = profile.points
    .map((p) => ({
      ...p,
      years: (new Date(p.date).getTime() - new Date(profile.asOf).getTime()) / (365.25 * 24 * 3600 * 1000),
      value: p.value / currentValue,
    }))
    .filter((p) => Number.isFinite(p.years) && Number.isFinite(p.value) && p.value > 0);
  const futureYears = profile.future?.horizonYears ?? 0;
  const historyMin = normalized.length ? Math.min(...normalized.map((p) => p.years)) : -10;
  const xMin = Math.min(-10, Math.floor(historyMin));
  const xMax = Math.max(10, futureYears);
  const futureValues = profile.future
    ? [...profile.future.q05, ...profile.future.q95, ...profile.future.median].filter((x) => Number.isFinite(x) && x > 0)
    : [];
  const allValues = [...normalized.map((p) => p.value), ...futureValues, 1];
  const logMin = Math.floor(Math.log10(Math.max(1e-4, Math.min(...allValues))) * 2) / 2;
  const logMax = Math.ceil(Math.log10(Math.max(1e-4, Math.max(...allValues))) * 2) / 2;
  const x = (years: number) =>
    L + ((years - xMin) / Math.max(1e-9, xMax - xMin)) * plotW;
  const y = (value: number) =>
    T + ((logMax - Math.log10(Math.max(1e-4, value))) / Math.max(1e-9, logMax - logMin)) * plotH;

  const syntheticHistory = normalized.filter((p) => p.provenance === "SYNTHETIC_HISTORY");
  const observed = normalized.filter((p) => p.provenance === "OBSERVED_QQQ");

  const futureBand = profile.future
    ? profile.future.months
        .map((m, i) => [x(m / 12), y(profile.future?.q95[i] ?? 1)])
        .concat(
          profile.future.months
            .slice()
            .reverse()
            .map((m, i) => {
              const original = profile.future!.months.length - 1 - i;
              return [x(m / 12), y(profile.future!.q05[original] ?? 1)];
            }),
        )
        .map((p) => p.join(","))
        .join(" ")
    : "";

  const ticks = [0.1, 0.25, 0.5, 1, 2, 4, 8].filter(
    (v) => Math.log10(v) >= logMin && Math.log10(v) <= logMax,
  );

  return (
    <svg viewBox={"0 0 " + W + " " + H} className="min-w-[900px] w-full" role="img" aria-label="50 year semi-real long scale backbone">
      <rect x={L} y={T} width={plotW} height={plotH} fill="var(--color-elevated)" opacity="0.45" rx="8" />
      {ticks.map((v) => (
        <g key={v}>
          <line x1={L} x2={W - R} y1={y(v)} y2={y(v)} stroke="var(--color-line)" />
          <text x={L - 10} y={y(v) + 4} textAnchor="end" fill="var(--color-subtle)" fontSize="11">{v}×</text>
        </g>
      ))}
      {syntheticHistory.length ? (
        <polyline
          points={syntheticHistory.map((p) => x(p.years) + "," + y(p.value)).join(" ")}
          fill="none"
          stroke="var(--color-muted)"
          strokeWidth="2.5"
          strokeDasharray="6 4"
        />
      ) : null}
      {observed.length ? (
        <polyline
          points={observed.map((p) => x(p.years) + "," + y(p.value)).join(" ")}
          fill="none"
          stroke="var(--color-fg)"
          strokeWidth="3.2"
          strokeLinejoin="round"
          strokeLinecap="round"
        />
      ) : null}
      {futureBand ? <polygon points={futureBand} fill="var(--color-accent)" opacity="0.10" /> : null}
      {profile.future ? (
        <polyline
          points={profile.future.months.map((m, i) => x(m / 12) + "," + y(profile.future?.median[i] ?? 1)).join(" ")}
          fill="none"
          stroke="var(--color-accent)"
          strokeWidth="3"
          strokeDasharray="8 4"
        />
      ) : null}
      <line x1={x(0)} x2={x(0)} y1={T} y2={T + plotH} stroke="var(--color-fragile)" strokeDasharray="4 4" />
      <text x={Math.min(W - 120, x(0) + 7)} y={T + 16} fill="var(--color-fragile)" fontSize="11">NOW</text>
      {profile.observedStartDate ? (
        <text x={x((new Date(profile.observedStartDate).getTime() - new Date(profile.asOf).getTime()) / (365.25 * 24 * 3600 * 1000)) + 6} y={T + 16} fill="var(--color-fg)" fontSize="10">
          QQQ CORE START
        </text>
      ) : null}
      {[-50, -40, -30, -20, -10, 0, 10, 20].filter((v) => v >= xMin && v <= xMax).map((v) => (
        <text key={v} x={x(v)} y={H - 24} textAnchor="middle" fill="var(--color-subtle)" fontSize="11">
          {v > 0 ? "+" : ""}{v}Y
        </text>
      ))}
      <g>
        <text x={W - 270} y={T + 8} fill="var(--color-subtle)" fontSize="10">PROVENANCE</text>
        <text x={W - 270} y={T + 27} fill="var(--color-muted)" fontSize="11">— synthetic history</text>
        <text x={W - 270} y={T + 45} fill="var(--color-fg)" fontSize="11">— observed QQQ core</text>
        <text x={W - 270} y={T + 63} fill="var(--color-accent)" fontSize="11">- - synthetic future q05/median/q95</text>
      </g>
      <text x={L} y={H - 5} fill="var(--color-subtle)" fontSize="10">
        relative value is normalized to current QQQ = 1× · log scale prevents the long-history growth curve from collapsing the early structure
      </text>
    </svg>
  );
}

function ResponseChart({
  curves,
  domain,
  currentX,
  handoff,
  mutualChase,
}: {
  curves: Array<{ scale: number; xs: number[]; ys: number[] }>;
  domain: number[];
  currentX: number;
  handoff: { from: number; to: number; at: number } | null;
  mutualChase?: Array<{
    channel: string;
    topology: {
      state: string;
      leaderScaleBySegment: Array<number | null>;
      leaderChanges: number;
      pairwiseCurveCrossings: number;
    };
  }>;
}) {
  if (!curves.length) return <EmptyState text="沒有 response curve 資料。" />;

  const W = 1180, H = 560, L = 68, R = 280, T = 24, B = 120;
  const plotW = W - L - R, plotH = 320;
  const x = (v: number) => L + Math.max(0, Math.min(1, v)) * plotW;
  const y = (v: number) =>
    T + (domain[1] - v) / Math.max(0.0001, domain[1] - domain[0]) * plotH;
  const curveColor = (scale: number) =>
    scale === 20 ? "var(--color-accent)" : scale === 30 ? "var(--color-fragile)" : "var(--color-muted)";

  const sameCurve = (a: { scale: number; xs: number[]; ys: number[] }, b: { scale: number; xs: number[]; ys: number[] }) =>
    a.xs.length === b.xs.length &&
    a.ys.length === b.ys.length &&
    a.ys.every((value, i) => Math.abs(value - (b.ys[i] ?? value)) < 1e-9);

  const overlap30_50 =
    curves.some((c) => c.scale === 30) &&
    curves.some((c) => c.scale === 50) &&
    sameCurve(
      curves.find((c) => c.scale === 30)!,
      curves.find((c) => c.scale === 50)!,
    );

  const order = [...curves].sort((a, b) => {
    if (a.scale === 30 && b.scale === 50) return 1;
    if (a.scale === 50 && b.scale === 30) return -1;
    return a.scale - b.scale;
  });

  const dynamicTrack = curves[0].xs.map((_, i) => {
    const slopes = curves.map((curve) => {
      const next = Math.min(curve.xs.length - 1, i + 1);
      const prev = Math.max(0, next - 1);
      const dx = (curve.xs[next] ?? 0) - (curve.xs[prev] ?? 0);
      const dy = (curve.ys[next] ?? 0) - (curve.ys[prev] ?? 0);
      return dx > 0 ? Math.abs(dy / dx) : 0;
    });
    const total = slopes.reduce((sum, value) => sum + value, 0);
    return curves.reduce(
      (sum, curve, j) => sum + (curve.ys[i] ?? 0) * ((slopes[j] ?? 0) / (total || Math.max(1, slopes.length))),
      0,
    );
  });

  const currentSlopes = curves
    .map((curve) => {
      const i = Math.max(0, Math.min(curve.xs.length - 2, Math.floor(currentX * (curve.xs.length - 1))));
      const dx = (curve.xs[i + 1] ?? 0) - (curve.xs[i] ?? 0);
      const dy = (curve.ys[i + 1] ?? 0) - (curve.ys[i] ?? 0);
      return { scale: curve.scale, slope: dx > 0 ? dy / dx : 0 };
    })
    .sort((a, b) => Math.abs(b.slope) - Math.abs(a.slope));

  const crossings: Array<{ phase: number; left: number; right: number }> = [];
  for (let a = 0; a < curves.length; a++) {
    for (let b = a + 1; b < curves.length; b++) {
      for (let i = 1; i < curves[a].xs.length; i++) {
        const d1 = (curves[a].ys[i - 1] ?? 0) - (curves[b].ys[i - 1] ?? 0);
        const d2 = (curves[a].ys[i] ?? 0) - (curves[b].ys[i] ?? 0);
        if (d1 === 0 || d1 * d2 < 0) {
          crossings.push({
            phase: curves[a].xs[i - 1] ?? 0,
            left: curves[a].scale,
            right: curves[b].scale,
          });
        }
      }
    }
  }

  const derivedHandoffs = (mutualChase ?? []).flatMap((channel) => {
    const leaders = channel.topology.leaderScaleBySegment;
    const out: Array<{ channel: string; from: number; to: number; at: number }> = [];
    for (let i = 1; i < leaders.length; i++) {
      const from = leaders[i - 1];
      const to = leaders[i];
      if (from != null && to != null && from !== to) out.push({ channel: channel.channel, from, to, at: i * 0.05 });
    }
    return out;
  });
  if (handoff && !derivedHandoffs.some((x) => x.from === handoff.from && x.to === handoff.to && Math.abs(x.at - handoff.at) < 0.051)) {
    derivedHandoffs.unshift({ channel: "NDX", ...handoff });
  }

  const leaderOf = (channel: string) =>
    mutualChase?.find((x) => x.channel === channel)?.topology.leaderScaleBySegment ?? [];
  const leaderRows = [
    { channel: "NDX", leaders: leaderOf("NDX") },
    { channel: "NASDAQCOM", leaders: leaderOf("NASDAQCOM") },
  ];

  const laneY = (row: number) => T + plotH + 34 + row * 29;
  const leaderColor = (scale: number | null) =>
    scale === 20 ? "var(--color-accent)" : scale === 30 ? "var(--color-fragile)" : scale === 50 ? "var(--color-pass)" : "var(--color-muted)";

  return (
    <svg viewBox={"0 0 " + W + " " + H} className="min-w-[1040px] w-full" role="img" aria-label="Mutual chase response field with dynamic simulation track">
      <rect x={L} y={T} width={plotW} height={plotH} fill="var(--color-elevated)" opacity="0.45" rx="8" />
      {[1, 1.5, 2, 2.5, 3].filter((v) => v <= domain[1] + 0.01).map((v) => (
        <g key={v}>
          <line x1={L} x2={L + plotW} y1={y(v)} y2={y(v)} stroke="var(--color-line)" />
          <text x={L - 10} y={y(v) + 4} textAnchor="end" fill="var(--color-subtle)" fontSize="11">{v.toFixed(1)}×</text>
        </g>
      ))}

      {order.map((curve) => (
        <polyline
          key={curve.scale}
          points={curve.xs.map((v, i) => x(v) + "," + y(curve.ys[i])).join(" ")}
          fill="none"
          stroke={curveColor(curve.scale)}
          strokeWidth={curve.scale === 30 && overlap30_50 ? 3.8 : curve.scale === 20 ? 3 : 2.5}
          strokeDasharray={curve.scale === 30 && overlap30_50 ? "5 4" : undefined}
          strokeLinejoin="round"
          strokeLinecap="round"
        />
      ))}

      <polyline
        points={curves[0].xs.map((v, i) => x(v) + "," + y(dynamicTrack[i] ?? domain[0])).join(" ")}
        fill="none"
        stroke="var(--color-fg)"
        strokeWidth="4.5"
        strokeDasharray="11 5"
        opacity="0.9"
      />

      {crossings.map((cross, i) => (
        <circle key={"cross-" + i} cx={x(cross.phase)} cy={T + 14} r="4" fill="var(--color-pass)" />
      ))}

      {derivedHandoffs.map((row, i) => (
        <g key={"handoff-" + row.channel + "-" + i}>
          <line x1={x(row.at)} x2={x(row.at)} y1={T} y2={laneY(1) + 12} stroke="var(--color-fragile)" strokeDasharray="2 3" opacity="0.7" />
          <text x={Math.min(L + plotW - 145, x(row.at) + 6)} y={T + 30 + i * 14} fill="var(--color-fragile)" fontSize="10">
            {row.channel} {row.from}Y → {row.to}Y
          </text>
        </g>
      ))}

      <line x1={x(currentX)} x2={x(currentX)} y1={T} y2={laneY(1) + 12} stroke="var(--color-fg)" strokeDasharray="4 4" opacity="0.95" />
      <circle cx={x(currentX)} cy={y(interpolateAt(curves[0].xs, dynamicTrack, currentX))} r="6" fill="var(--color-fg)" />
      <text x={Math.min(L + plotW - 100, x(currentX) + 6)} y={T + 14} fill="var(--color-fg)" fontSize="11">SIM {fmtPct(currentX, 1)}</text>

      {overlap30_50 ? (
        <g>
          <rect x={L + 12} y={T + 12} width="184" height="30" rx="6" fill="var(--color-surface)" opacity="0.9" />
          <text x={L + 22} y={T + 25} fill="var(--color-fragile)" fontSize="10">30Y</text>
          <text x={L + 51} y={T + 25} fill="var(--color-subtle)" fontSize="10">≡</text>
          <text x={L + 68} y={T + 25} fill="var(--color-muted)" fontSize="10">50Y</text>
          <text x={L + 22} y={T + 37} fill="var(--color-subtle)" fontSize="9">exact sampled response overlap</text>
        </g>
      ) : null}

      {order.map((curve) => {
        const endY = y(curve.ys.at(-1) ?? domain[0]);
        const labelOffset = curve.scale === 30 && overlap30_50 ? -12 : curve.scale === 50 && overlap30_50 ? 12 : 0;
        return (
          <text key={"label-" + curve.scale} x={L + plotW - 2} y={endY + labelOffset + 4} textAnchor="end" fill={curveColor(curve.scale)} fontSize="10" fontWeight="600">
            {curve.scale}Y
          </text>
        );
      })}

      {leaderRows.map((row, rowIndex) => (
        <g key={row.channel}>
          <text x={L - 10} y={laneY(rowIndex) + 14} textAnchor="end" fill="var(--color-subtle)" fontSize="11">{row.channel}</text>
          {Array.from({ length: 20 }, (_, i) => {
            const lead = row.leaders[i] ?? null;
            return (
              <rect
                key={row.channel + "-" + i}
                x={x(i / 20)}
                y={laneY(rowIndex)}
                width={plotW / 20 + 0.5}
                height="18"
                rx="3"
                fill={leaderColor(lead)}
                opacity={lead == null ? 0.08 : 0.55}
              />
            );
          })}
        </g>
      ))}

      <g>
        <text x={W - R + 10} y={T + 4} fill="var(--color-subtle)" fontSize="11">CURRENT SLOPE RANK</text>
        {currentSlopes.map((row, idx) => (
          <g key={row.scale} transform={"translate(" + (W - R + 10) + "," + (T + 20 + idx * 38) + ")"}>
            <text x="0" y="0" fill={curveColor(row.scale)} fontSize="12" fontWeight="600">
              {idx + 1}. {row.scale}Y
            </text>
            <text x="0" y="16" fill="var(--color-muted)" fontSize="11">slope {row.slope.toFixed(3)}</text>
            <rect x="78" y="-10" width="110" height="8" rx="4" fill="var(--color-line)" />
            <rect x="78" y="-10" width={Math.min(110, Math.abs(row.slope) * 24)} height="8" rx="4" fill={curveColor(row.scale)} opacity="0.8" />
          </g>
        ))}
        <text x={W - R + 10} y={T + 145} fill="var(--color-fg)" fontSize="10">— SIM TRACK = phase-by-phase</text>
        <text x={W - R + 10} y={T + 160} fill="var(--color-fg)" fontSize="10">  slope-weighted response path</text>
      </g>

      <g>
        <text x={L} y={H - 34} fill="var(--color-subtle)" fontSize="11">0%</text>
        <text x={x(0.5)} y={H - 34} textAnchor="middle" fill="var(--color-subtle)" fontSize="11">50%</text>
        <text x={x(1)} y={H - 34} textAnchor="end" fill="var(--color-subtle)" fontSize="11">100%</text>
        <text x={L} y={H - 14} fill="var(--color-subtle)" fontSize="10">
          X = deployment phase · solid = scale response · - - = dynamic field track · ● = crossing / current SIM
        </text>
        {[[20,"20Y"],[30,"30Y"],[50,"50Y"]].map(([scale,label],i) => (
          <g key={String(scale)}>
            <rect x={L + i * 82} y={H - 61} width="12" height="12" rx="2" fill={leaderColor(scale as number)} />
            <text x={L + 18 + i * 82} y={H - 51} fill="var(--color-subtle)" fontSize="10">{label}</text>
          </g>
        ))}
      </g>
    </svg>
  );
}

function CapitalChart({
  points,
  currentClock,
  currentStatus,
}: {
  points: Array<{ month: number; fraction: number; preview?: boolean }>;
  currentClock: number;
  currentStatus: EntryStatus;
}) {
  const W = 1000, H = 340, L = 58, R = 24, T = 20, B = 44;
  const plotW = W - L - R, plotH = H - T - B;
  const x = (month: number) => L + Math.max(0, Math.min(120, month)) / 120 * plotW;
  const y = (fraction: number) => T + (1 - Math.max(0, Math.min(1, fraction))) * plotH;

  // Axis month 0 = 0%, month 120 = 100%. Operator month n (1..120) sits at n/120.
  const rail = Array.from({ length: 121 }, (_, m) => m / 120);
  // Persisted month is a 0-based index; plot it on the operator month (index + 1).
  const xIndex = (monthIndex: number) => x(monthIndex + 1);
  const corridor = [
    [x(0), y(0)],
    ...rail.map((v, m) => [x(m), y(v)]),
    [x(120), y(1)],
    [x(0), y(1)],
  ].map((p) => p.join(",")).join(" ");

  const actual = points.filter((p) => !p.preview);
  const preview = points.find((p) => p.preview);

  return (
    <svg viewBox={"0 0 " + W + " " + H} className="min-w-[760px] w-full" role="img" aria-label="10 year capital rule corridor">
      <rect x={L} y={T} width={plotW} height={plotH} fill="var(--color-elevated)" opacity="0.45" rx="8" />
      <polygon points={corridor} fill="var(--color-pass)" opacity="0.06" />
      {[0, 0.25, 0.5, 0.75, 1].map((v) => (
        <g key={v}>
          <line x1={L} x2={W - R} y1={y(v)} y2={y(v)} stroke="var(--color-line)" />
          <text x={L - 8} y={y(v) + 4} textAnchor="end" fill="var(--color-subtle)" fontSize="11">{fmtPct(v, 0)}</text>
        </g>
      ))}
      <polyline
        points={rail.map((v, m) => x(m) + "," + y(v)).join(" ")}
        fill="none"
        stroke="var(--color-fragile)"
        strokeWidth="3"
        strokeDasharray="5 5"
      />
      {actual.length ? (
        <>
          <polyline
            points={actual.map((p) => xIndex(p.month) + "," + y(p.fraction)).join(" ")}
            fill="none"
            stroke="var(--color-fg)"
            strokeWidth="3"
            strokeLinejoin="round"
            strokeLinecap="round"
          />
          {actual.map((p, index) => (
            <circle key={String(p.month) + "-" + String(index)} cx={xIndex(p.month)} cy={y(p.fraction)} r="5" fill="var(--color-fg)" />
          ))}
        </>
      ) : null}
      {preview ? (
        <>
          <line x1={xIndex(preview.month)} x2={xIndex(preview.month)} y1={T} y2={T + plotH} stroke="var(--color-accent)" strokeDasharray="2 3" opacity="0.7" />
          <circle cx={xIndex(preview.month)} cy={y(preview.fraction)} r="7" fill="var(--color-accent)" />
          <text x={Math.min(W - 150, xIndex(preview.month) + 8)} y={y(preview.fraction) - 10} fill="var(--color-accent)" fontSize="11">
            PREVIEW · {currentStatus}
          </text>
        </>
      ) : null}
      {[0, 24, 48, 72, 96, 120].map((m) => (
        <text key={m} x={x(m)} y={H - 20} textAnchor="middle" fill="var(--color-subtle)" fontSize="11">{m}m</text>
      ))}
      <text x={L} y={H - 4} fill="var(--color-subtle)" fontSize="11">
        shaded corridor = rule-compliant zone above the hard deadline rail
      </text>
    </svg>
  );
}

function LedgerTable({
  entries,
  capital,
  startingDeployed,
  onToggleVoid,
}: {
  entries: LedgerEntry[];
  capital: number;
  onToggleVoid: (entryId: string) => void;
}) {
  if (!entries.length) {
    return (
      <p className="mt-4 rounded-md border border-dashed border-line p-4 text-sm text-muted">
        尚未記錄現金流。Contribution 才會改變 Actual Contributed；Withdrawal 只記獨立 cashflow。
      </p>
    );
  }

  const rows = entries
    .slice()
    .sort((a, b) => a.month - b.month || a.recordedAt.localeCompare(b.recordedAt))
    .reduce<Array<{
      entry: LedgerEntry;
      fraction: number;
      clock: number;
      status: EntryStatus | "VOIDED";
    }>>((rows, entry) => {
      const prior = rows.at(-1)?.fraction ?? 0;
      const isContribution = (entry.kind ?? "CONTRIBUTION") === "CONTRIBUTION";
      const fraction = !entry.voidedAt && isContribution
        ? prior + entry.amount / Math.max(1, capital)
        : prior;
      const clock = clockFraction(entry.month + 1);
      rows.push({
        entry,
        fraction,
        clock,
        status: entry.voidedAt ? "VOIDED" : statusFor(fraction, clock, fraction * capital, capital),
      });
      return rows;
    }, [])
    .reverse();

  return (
    <div className="mt-4 overflow-x-auto">
      <table className="w-full min-w-[800px] text-left text-sm">
        <thead className="text-xs text-subtle">
          <tr>
            <th className="py-2">month</th>
            <th className="py-2">type</th>
            <th className="py-2">amount</th>
            <th className="py-2">QQQ price</th>
            <th className="py-2">累積</th>
            <th className="py-2">clock</th>
            <th className="py-2">delta</th>
            <th className="py-2">check</th>
            <th className="py-2">action</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(({ entry, fraction, clock, status }) => (
            <tr key={entry.id} className="border-t border-line">
              <td className="py-2 font-mono tabular-nums">{entry.month + 1}</td>
              <td className="py-2 font-mono text-xs">{entry.kind ?? "CONTRIBUTION"}</td>
              <td className="py-2 font-mono tabular-nums">{fmtUsd(entry.amount, 2)}</td>
              <td className="py-2 font-mono tabular-nums">
                {entry.price == null ? "—" : fmtUsd(entry.price, 2)}
              </td>
              <td className="py-2 font-mono tabular-nums">{fmtPct(fraction, 2)}</td>
              <td className="py-2 font-mono tabular-nums">{fmtPct(clock, 2)}</td>
              <td className="py-2 font-mono tabular-nums">{fmtPct(fraction - clock, 2)}</td>
              <td className="py-2">
                <Badge tone={status === "BELOW_CLOCK" || status === "OVER_CAPITAL" || status === "VOIDED" ? "lock" : status === "AHEAD" ? "fragile" : "pass"}>
                  {status}
                </Badge>
              </td>
              <td className="py-2">
                <button type="button" onClick={() => onToggleVoid(entry.id)} className="min-h-8 rounded-md border border-line px-2 font-mono text-[11px] text-muted hover:text-fg">
                  {entry.voidedAt ? "RESTORE" : "VOID"}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
