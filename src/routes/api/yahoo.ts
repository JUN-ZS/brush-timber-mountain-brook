import { createFileRoute } from "@tanstack/react-router";

const ALLOWED = new Set(["QQQ", "^VIX", "^NDX", "^IXIC"]);

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

        return Response.json({
          source: "YAHOO_FINANCE_CHART",
          fetchedAt,
          interval: "1d",
          range: "5y",
          symbols: results,
          warnings,
        });
      },
    },
  },
});
