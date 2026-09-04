import { i as __toESM } from "../_runtime.mjs";
import { B as require_react, x as require_jsx_runtime, y as useNavigate } from "../_libs/@tanstack/react-router+[...].mjs";
import { a as Shell, f as fmtPct, i as RANK_MODES, l as compete, n as MISSING_UNIVERSE, r as Panel, t as Badge, v as useRadar } from "./shell-BqaE3PNF.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/rank-C259Xrrk.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
function Page() {
	const cards = useRadar((s) => s.cards);
	const cursor = useRadar((s) => s.cursor);
	const setSymbol = useRadar((s) => s.setSymbol);
	const rankMode = useRadar((s) => s.rankMode);
	const setRankMode = useRadar((s) => s.setRankMode);
	const navigate = useNavigate();
	const ranked = [...(0, import_react.useMemo)(() => {
		const need = rankMode === "evrisk" || rankMode === "tail" || rankMode === "deploy" || rankMode === "edge";
		return cards.map((c) => {
			return {
				c,
				dep: need ? compete(c, cursor)[0] : null
			};
		});
	}, [
		cards,
		cursor,
		rankMode
	])].sort((a, b) => scoreOf(b, rankMode) - scoreOf(a, rankMode));
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Shell, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "grid gap-4",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Panel, {
			kicker: "ALL OBSERVED NAMES",
			title: "三個維度都保留，排序只是切換鏡頭",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
				className: "text-sm text-muted",
				children: [
					"日線來自 Yahoo 調整收盤。Mature 歷史長不會自動加分。樣本權重有時間衰減。未納入宇宙的 ",
					MISSING_UNIVERSE.length,
					" 檔仍標缺失。"
				]
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "mt-3 flex flex-wrap gap-2",
				children: RANK_MODES.map((m) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
					type: "button",
					onClick: () => setRankMode(m.id),
					className: `min-h-11 rounded-sm border px-3 text-sm ${rankMode === m.id ? "border-accent bg-elevated text-fg" : "border-line text-muted"}`,
					children: m.label
				}, m.id))
			})]
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
			className: "overflow-x-auto rounded-xl border border-line",
			children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("table", {
				className: "w-full min-w-[920px] text-left text-sm",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("thead", {
					className: "bg-elevated text-xs text-subtle",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("tr", { children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
							className: "px-3 py-2 font-medium",
							children: "sym"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
							className: "px-3 py-2 font-medium",
							children: "DAY"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
							className: "px-3 py-2 font-medium",
							children: "WEEK"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
							className: "px-3 py-2 font-medium",
							children: "MONTH"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
							className: "px-3 py-2 font-medium",
							children: "dur"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
							className: "px-3 py-2 font-medium",
							children: "cont"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
							className: "px-3 py-2 font-medium",
							children: "rev"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
							className: "px-3 py-2 font-medium",
							children: "edge"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
							className: "px-3 py-2 font-medium",
							children: "best"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
							className: "px-3 py-2 font-medium",
							children: "cohort"
						})
					] })
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("tbody", { children: ranked.map(({ c, dep }) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("tr", {
					className: "border-t border-line",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
							className: "px-3 py-3",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
								type: "button",
								className: "min-h-11 text-fg",
								onClick: () => {
									setSymbol(c.symbol);
									navigate({ to: "/" });
								},
								children: c.symbol
							})
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
							className: "px-3 py-3 font-mono tabular-nums",
							children: fmtPct(c.day.percentile, 0)
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
							className: "px-3 py-3 font-mono tabular-nums",
							children: fmtPct(c.week.percentile, 0)
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
							className: "px-3 py-3 font-mono tabular-nums",
							children: fmtPct(c.month.percentile, 0)
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
							className: "px-3 py-3 font-mono tabular-nums",
							children: c.week.durationAboveMean
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
							className: "px-3 py-3 font-mono tabular-nums",
							children: fmtPct(c.continuation, 0)
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
							className: "px-3 py-3 font-mono tabular-nums",
							children: fmtPct(c.reversion, 0)
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
							className: "px-3 py-3 font-mono tabular-nums",
							children: fmtPct(c.volEdge, 1)
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
							className: "px-3 py-3 font-mono text-xs",
							children: dep ? `${dep.label} ${dep.score.toFixed(0)}` : c.alert
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
							className: "px-3 py-3",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Badge, {
								tone: c.cohort === "HOT" ? "fragile" : "mute",
								children: c.cohort
							})
						})
					]
				}, c.symbol)) })]
			})
		})]
	}) });
}
function scoreOf(row, mode) {
	const { c, dep } = row;
	if (mode === "expansion") return (c.week.percentile ?? 0) * .5 + (c.day.percentile ?? 0) * .25 + (c.month.percentile ?? 0) * .25;
	if (mode === "prebreak") {
		const p = c.week.percentile ?? 0;
		return p >= .7 && p < .9 && c.volMomentum === "RISING" ? p + .2 : p * .3;
	}
	if (mode === "persist") return c.persistence.p1 ?? -1;
	if (mode === "edge") return c.volEdge ?? -1;
	if (mode === "evrisk") return dep?.valueRisk ?? -99;
	if (mode === "tail") return dep ? -Math.abs(dep.breach.es95) : -99;
	return dep?.score ?? -1;
}
//#endregion
export { Page as component };
