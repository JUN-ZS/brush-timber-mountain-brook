import { createFileRoute } from "@tanstack/react-router";
import {
  couple,
  monthlyize,
  qqqMonthly,
  recommendForScale,
  TRAP_SCALES_YEARS,
  type ChannelScaleSignal,
  type CoupledSignal,
  type MonthlyPoint,
} from "@/lib/pulse/rolling-floor";
import {
  buildSyntheticLongScale,
  type LongScaleProfile,
} from "@/lib/pulse/long-scale";

const ALLOWED = new Set(["QQQ", "^VIX", "^NDX", "^IXIC"]);

type LiveRollingFloorPayload = {
  asOf: string;
  coupled: CoupledSignal;
  source: "YAHOO_FINANCE_CHART + REPO_QQQ + FRED_PROXY_HISTORY";
};

type LiveLongScalePayload = {
  scale: 50;
  profile: LongScaleProfile;
  authority: "GEOMETRY_ONLY";
};

function appendLivePoint(points: MonthlyPoint[], asOf: string, price: number) {
  const key = asOf.slice(0, 7);
  const out = points.filter((p) => p.date.slice(0, 7) !== key);
  out.push({ date: asOf, value: price });
  return monthlyize(out);
}

async function fetchFredMonthly(id: string, start: string, end: string) {
  const url =
    "https://fred.stlouisfed.org/graph/fredgraph.csv?" +
    new URLSearchParams({ id, cosd: start, coed: end });
  const res = await fetch(url, {
    headers: { "User-Agent": "rolling-floor-live/1.0" },
    cache: "no-store",
  });
  if (!res.ok) throw new Error("FRED " + id + " HTTP " + res.status);
  const raw = await res.text();
  const lines = raw.split(/\r?\n/).filter(Boolean);
  const points: MonthlyPoint[] = [];
  for (let i = 1; i < lines.length; i++) {
    const comma = lines[i].indexOf(",");
    if (comma < 0) continue;
    const date = lines[i].slice(0, comma).trim();
    const value = Number(lines[i].slice(comma + 1).trim());
    if (/^\d{4}-\d{2}-\d{2}$/.test(date) && Number.isFinite(value) && value > 0) {
      points.push({ date, value });
    }
  }
  return monthlyize(points);
}

function latestLiveDate(series: { regularMarketTime?: string | null; bars?: Array<{ date: string }> }) {
  if (series.regularMarketTime) return series.regularMarketTime.slice(0, 10);
  return series.bars?.at(-1)?.date ?? new Date().toISOString().slice(0, 10);
}

type YahooChartResult = {
  chart?: {
    result?: Array<{
      meta?: Record<string, unknown>;
      timestamp?: number[];
      indicators?: {
        quote?: Array<{ close?: Array<number | null> }>;
      };
    } | null>;
    error?: { description?: string | null } | null;
  };
};

export const Route = createFileRoute("/api/yahoo")({
  server: {
    handlers: {
      GET: async () => {
        const symbols = ["QQQ", "^VIX", "^NDX", "^IXIC"];
        const fetchedAt = new Date().toISOString();
        const results = [];
        const warnings: string[] = [];

        for (const symbol of symbols) {
          try {
            const url =
              "https://query1.finance.yahoo.com/v8/finance/chart/" +
              encodeURIComponent(symbol) +
              "?range=5y&interval=1d&includePrePost=false";
            const response = await fetch(url, {
              headers: {
                "User-Agent": "Mozilla/5.0 (compatible; QQQ-Floor/1.0)",
                Accept: "application/json",
              },
              cache: "no-store",
            });
            if (!response.ok) {
              warnings.push(symbol + ": HTTP " + response.status);
              continue;
            }
            const payload = (await response.json()) as YahooChartResult;
            const result = payload.chart?.result?.[0];
            if (!result) {
              warnings.push(symbol + ": no result");
              continue;
            }
            const timestamps = result.timestamp ?? [];
            const closes = result.indicators?.quote?.[0]?.close ?? [];
            const bars = timestamps
              .map((ts, i) => {
                const close = Number(closes[i]);
                if (!Number.isFinite(close) || close <= 0) return null;
                return {
                  date: new Date(ts * 1000).toISOString().slice(0, 10),
                  close,
                };
              })
              .filter((x): x is { date: string; close: number } => x != null);

            const meta = result.meta ?? {};
            const regularMarketPrice = Number(meta.regularMarketPrice);
            const lastClose = bars.at(-1)?.close ?? null;
            results.push({
              symbol,
              price: Number.isFinite(regularMarketPrice) && regularMarketPrice > 0 ? regularMarketPrice : lastClose,
              previousClose: Number.isFinite(Number(meta.previousClose)) ? Number(meta.previousClose) : bars.at(-2)?.close ?? null,
              regularMarketTime:
                Number.isFinite(Number(meta.regularMarketTime))
                  ? new Date(Number(meta.regularMarketTime) * 1000).toISOString()
                  : null,
              marketState: typeof meta.marketState === "string" ? meta.marketState : null,
              currency: typeof meta.currency === "string" ? meta.currency : null,
              bars,
            });
          } catch (error) {
            warnings.push(symbol + ": " + (error instanceof Error ? error.message : "fetch failed"));
          }
        }

        let rollingFloor: LiveRollingFloorPayload | null = null;
        let longScale: LiveLongScalePayload | null = null;
        try {
          const qqqLive = results.find((x) => x.symbol === "QQQ");
          const ndxLive = results.find((x) => x.symbol === "^NDX");
          const compositeLive = results.find((x) => x.symbol === "^IXIC");
          if (qqqLive?.price && ndxLive?.price && compositeLive?.price) {
            const asOf = latestLiveDate(qqqLive);
            const qqqRepo = qqqMonthly();
            const [ndxHistory, compositeHistory] = await Promise.all([
              fetchFredMonthly("NASDAQ100", "1986-01-02", asOf),
              fetchFredMonthly("NASDAQCOM", "1971-02-05", asOf),
            ]);
            const qqq = appendLivePoint(qqqRepo, asOf, qqqLive.price);
            const ndx = appendLivePoint(ndxHistory, asOf, ndxLive.price);
            const nasdaqCom = appendLivePoint(compositeHistory, asOf, compositeLive.price);

            const channels: Array<{
              id: "QQQ" | "NDX" | "NASDAQCOM";
              points: MonthlyPoint[];
              layer: "OBSERVED" | "PROXY_PRICE";
            }> = [
              { id: "QQQ", points: qqq, layer: "OBSERVED" },
              { id: "NDX", points: ndx, layer: "PROXY_PRICE" },
              { id: "NASDAQCOM", points: nasdaqCom, layer: "PROXY_PRICE" },
            ];

            const signals: ChannelScaleSignal[] = [];
            for (const channel of channels) {
              const idx = channel.points.findIndex((p) => p.date === asOf);
              if (idx < 0) continue;
              for (const scaleYears of TRAP_SCALES_YEARS) {
                const signal = recommendForScale( 
                  channel.points,
                  qqqRepo,
                  idx,
                  scaleYears,
                );
                signal.channel = channel.id;
                signal.layer = channel.layer;
                signals.push(signal);
              }
            }

            rollingFloor = {
              asOf,
              coupled: couple(asOf, 0, signals),
              source: "YAHOO_FINANCE_CHART + REPO_QQQ + FRED_PROXY_HISTORY",
            };

            const longProfile = buildSyntheticLongScale(
              qqq,
              ndx,
              nasdaqCom,
              asOf,
              50,
              20,
            );
            if (longProfile) {
              longScale = {
                scale: 50,
                profile: longProfile,
                authority: "GEOMETRY_ONLY",
              };
            } else {
              warnings.push("50Y long-scale reconstruction unavailable");
            }
          } else {
            warnings.push("rolling floor: live QQQ/NDX/NASDAQCOM prices incomplete");
          }
        } catch (error) {
          warnings.push(
            "rolling floor: " + (error instanceof Error ? error.message : "build failed"),
          );
        }

        return Response.json({
          source: "YAHOO_FINANCE_CHART",
          fetchedAt,
          interval: "1d",
          range: "5y",
          symbols: results,
          rollingFloor,
          longScale,
          warnings,
        });
      },
    },
  },
});
