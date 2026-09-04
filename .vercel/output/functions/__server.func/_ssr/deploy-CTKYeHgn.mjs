import { x as require_jsx_runtime } from "../_libs/@tanstack/react-router+[...].mjs";
import { a as Shell, c as capacityPlan, f as fmtPct, g as thresholdProbe, p as fmtUsd, r as Panel, t as Badge, v as useRadar } from "./shell-BqaE3PNF.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/deploy-CTKYeHgn.js
var import_jsx_runtime = require_jsx_runtime();
function Page() {
	const card = useRadar((s) => s.card);
	const deploys = useRadar((s) => s.deploys);
	const cursor = useRadar((s) => s.cursor);
	const maxConsec = useRadar((s) => s.maxConsec);
	const maxDd = useRadar((s) => s.maxDd);
	const setBudget = useRadar((s) => s.setBudget);
	const probe = card ? thresholdProbe(card.symbol, cursor) : [];
	const best = deploys.find((d) => d.id !== "NO_TRADE") ?? deploys[0];
	const plan = card && best ? capacityPlan(best, card.spot, {
		maxConsec,
		maxDd
	}) : null;
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Shell, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "grid gap-4",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Panel, {
				kicker: "STRUCTURES COMPETE",
				title: "鐵蝶只是候選人",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "max-w-2xl text-sm text-muted",
					children: "Short ratio = f(VolState, Continuation, Reversion)，不是寫死 5×。評估用 TRAIN 相似狀態的下一週報酬分布，權重隨時間衰減。真實 option chain 不存在，全部 HYPOTHETICAL。NO_TRADE 合法。"
				}), card ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
					className: "mt-2 font-mono text-xs tabular-nums text-subtle",
					children: [
						card.symbol,
						" WEEK ",
						fmtPct(card.week.percentile, 0),
						" · persist ",
						card.persistence.score,
						" · ratio hint",
						" ",
						deploys.find((d) => d.id === "CALL_RATIO")?.shortRatio ?? "—",
						" · alert ",
						card.alert
					]
				}) : null]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Panel, {
				kicker: "BREACH CAPACITY",
				title: "我可以承受多少次穿破",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "grid gap-4 md:grid-cols-2",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("label", {
						className: "grid gap-2 text-sm",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
							className: "font-mono text-xs text-subtle",
							children: ["Max consecutive losses · ", maxConsec]
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
							type: "range",
							min: 1,
							max: 8,
							value: maxConsec,
							onChange: (e) => setBudget({ maxConsec: Number(e.target.value) }),
							className: "h-11 accent-accent"
						})]
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("label", {
						className: "grid gap-2 text-sm",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
							className: "font-mono text-xs text-subtle",
							children: ["Max drawdown · ", fmtUsd(maxDd)]
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
							type: "range",
							min: 500,
							max: 2e4,
							step: 500,
							value: maxDd,
							onChange: (e) => setBudget({ maxDd: Number(e.target.value) }),
							className: "h-11 accent-accent"
						})]
					})]
				}), plan && best ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
					className: "mt-3 text-sm text-muted",
					children: [
						"對 ",
						best.label,
						"：建議 ",
						plan.lots,
						" lot · notional ",
						fmtUsd(plan.notional),
						" · ES95 ",
						fmtUsd(plan.es95Dollar),
						" ·",
						" ",
						plan.rejected ? plan.reason : plan.reason
					]
				}) : null]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "overflow-x-auto rounded-xl border border-line",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("table", {
					className: "w-full min-w-[980px] text-left text-sm",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("thead", {
						className: "bg-elevated text-xs text-subtle",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("tr", { children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
								className: "px-3 py-2 font-medium",
								children: "structure"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
								className: "px-3 py-2 font-medium",
								children: "score"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
								className: "px-3 py-2 font-medium",
								children: "EV"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
								className: "px-3 py-2 font-medium",
								children: "POP"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
								className: "px-3 py-2 font-medium",
								children: "breach"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
								className: "px-3 py-2 font-medium",
								children: "ES95"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
								className: "px-3 py-2 font-medium",
								children: "3-streak"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
								className: "px-3 py-2 font-medium",
								children: "max run"
							})
						] })
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("tbody", { children: deploys.map((d) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("tr", {
						className: "border-t border-line",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("td", {
								className: "px-3 py-3",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
									className: "font-medium",
									children: d.label
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
									className: "font-mono text-xs text-subtle",
									children: d.legs
								})]
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
								className: "px-3 py-3 font-mono tabular-nums",
								children: d.score.toFixed(0)
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
								className: "px-3 py-3 font-mono tabular-nums",
								children: fmtPct(d.ev, 2)
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
								className: "px-3 py-3 font-mono tabular-nums",
								children: fmtPct(d.pop, 0)
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
								className: "px-3 py-3 font-mono tabular-nums",
								children: fmtPct(d.breach.probability, 0)
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
								className: "px-3 py-3 font-mono tabular-nums",
								children: fmtPct(d.breach.es95, 2)
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
								className: "px-3 py-3 font-mono tabular-nums",
								children: fmtPct(d.breach.consecutive3, 1)
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
								className: "px-3 py-3 font-mono tabular-nums",
								children: d.breach.maxConsecutive
							})
						]
					}, d.variant)) })]
				})
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Panel, {
				kicker: "THRESHOLD PROBE",
				title: "門檻自己競爭，不把 1.25× 當成真理",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "overflow-x-auto",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("table", {
						className: "w-full min-w-[520px] text-left text-sm",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("thead", {
							className: "text-xs text-subtle",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("tr", { children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
									className: "py-2 font-medium",
									children: "ratio ≥"
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
									className: "py-2 font-medium",
									children: "n"
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
									className: "py-2 font-medium",
									children: "P(stays next week)"
								})
							] })
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("tbody", { children: probe.map((r) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("tr", {
							className: "border-t border-line",
							children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("td", {
									className: "py-2 font-mono tabular-nums",
									children: [r.thr.toFixed(2), "×"]
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
									className: "py-2 font-mono tabular-nums",
									children: r.n
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
									className: "py-2 font-mono tabular-nums",
									children: fmtPct(r.p1, 0)
								})
							]
						}, r.thr)) })]
					})
				})
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Badge, {
				tone: "lock",
				children: "Council NO_TRADE · 這頁不是券商下單"
			})
		]
	}) });
}
//#endregion
export { Page as component };
