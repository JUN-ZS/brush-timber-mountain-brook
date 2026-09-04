import { x as require_jsx_runtime } from "../_libs/@tanstack/react-router+[...].mjs";
import { a as Shell, d as fmtNum, f as fmtPct, m as lastBar, o as TRADED, r as Panel, s as calendarIndexOf, t as Badge, u as fmtMul, v as useRadar } from "./shell-BqaE3PNF.mjs";
import { a as ReferenceLine, i as Line, n as YAxis, o as ResponsiveContainer, r as XAxis, s as Tooltip, t as LineChart } from "../_libs/recharts+[...].mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/routes-DbIP5n5X.js
var import_jsx_runtime = require_jsx_runtime();
function Meter({ pct, label }) {
	const w = Math.max(0, Math.min(100, (pct ?? 0) * 100));
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "flex items-baseline justify-between gap-2",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
			className: "font-mono text-xs text-subtle",
			children: label
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
			className: "font-mono text-sm tabular-nums",
			children: fmtPct(pct, 0)
		})]
	}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: "mt-1 h-2 overflow-hidden rounded-sm bg-elevated",
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
			className: "h-full bg-accent",
			style: { width: `${w}%` }
		})
	})] });
}
function WeekTimeline({ rows }) {
	const data = rows.map((r) => ({
		d: r.d.slice(5),
		pct: r.pct == null ? null : Math.round(r.pct * 1e3) / 10
	}));
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: "h-40 w-full",
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ResponsiveContainer, {
			width: "100%",
			height: "100%",
			children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(LineChart, {
				data,
				margin: {
					top: 8,
					right: 8,
					left: 0,
					bottom: 0
				},
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(XAxis, {
						dataKey: "d",
						tick: {
							fill: "var(--color-subtle)",
							fontSize: 10
						},
						axisLine: false,
						tickLine: false
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(YAxis, {
						domain: [40, 100],
						tick: {
							fill: "var(--color-subtle)",
							fontSize: 10
						},
						axisLine: false,
						tickLine: false,
						width: 28
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ReferenceLine, {
						y: 90,
						stroke: "var(--color-lock)",
						strokeDasharray: "3 3"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ReferenceLine, {
						y: 50,
						stroke: "var(--color-subtle)",
						strokeDasharray: "2 2"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Tooltip, {
						contentStyle: {
							background: "var(--color-elevated)",
							border: "1px solid var(--color-line)",
							borderRadius: 8
						},
						labelStyle: { color: "var(--color-muted)" },
						formatter: (v) => [`${v ?? "—"}%`, "WEEK %"]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Line, {
						type: "monotone",
						dataKey: "pct",
						stroke: "var(--color-accent)",
						strokeWidth: 2,
						dot: {
							r: 2.5,
							fill: "var(--color-accent)"
						},
						connectNulls: true
					})
				]
			})
		})
	});
}
function Page() {
	const card = useRadar((s) => s.card);
	const cards = useRadar((s) => s.cards);
	const setSymbol = useRadar((s) => s.setSymbol);
	const setCursor = useRadar((s) => s.setCursor);
	const cursor = useRadar((s) => s.cursor);
	const best = useRadar((s) => s.deploys)[0];
	if (!card) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Shell, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
		className: "text-muted",
		children: "資料不足。"
	}) });
	const arrow = card.volMomentum === "RISING" ? "↑" : card.volMomentum === "FALLING" ? "↓" : "→";
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Shell, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "grid gap-4",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "flex gap-2 overflow-x-auto pb-1",
				children: TRADED.map((sym) => {
					const c = cards.find((x) => x.symbol === sym);
					return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("button", {
						type: "button",
						onClick: () => setSymbol(sym),
						className: `min-h-11 shrink-0 rounded-sm border px-3 py-2 text-sm ${sym === card.symbol ? "border-accent bg-elevated text-fg" : "border-line text-muted"}`,
						children: [sym, c?.week.percentile != null ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
							className: "ml-2 font-mono text-xs tabular-nums text-subtle",
							children: Math.round(c.week.percentile * 100)
						}) : null]
					}, sym);
				})
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Panel, {
				kicker: `${card.symbol} · ${card.cohort} · ${card.nBars} bars · ${card.confidence}`,
				title: `SPOT ${fmtNum(card.spot, 2)}`,
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
					className: "text-sm text-muted",
					children: [
						"相對的是 ",
						card.symbol,
						" 自己的歷史，不是跨股平均。Price ",
						card.priceDir,
						" · Vol ",
						card.volDir,
						" · 慣性 ",
						card.volMomentum,
						" ",
						arrow
					]
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "mt-4 grid gap-4 md:grid-cols-3",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ScaleBlock, {
							title: "DAY",
							s: card.day
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ScaleBlock, {
							title: "WEEK",
							s: card.week
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ScaleBlock, {
							title: "MONTH",
							s: card.month
						})
					]
				})]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "grid gap-4 lg:grid-cols-2",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Panel, {
					kicker: "CONSECUTIVE STATE",
					title: `WEEK 已連續 ${card.week.durationAboveMean} 週高於自身均值`,
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
							className: "font-mono text-sm text-muted",
							children: [
								">",
								"90%：",
								card.week.durationAbove90,
								" 週 · ",
								">",
								"95%：",
								card.week.durationAbove95,
								" 週"
							]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(WeekTimeline, { rows: card.weekTimeline }),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "mt-2 text-sm text-muted",
							children: "同樣的高百分位：從低處爬上來（RISING）與從極端回落（FALLING）不是同一個 State。"
						})
					]
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Panel, {
					kicker: "PREPARATION RADAR",
					title: alertTitle(card.alert),
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("dl", {
							className: "grid grid-cols-2 gap-3 text-sm",
							children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Stat, {
									k: "DAY",
									v: `${fmtPct(card.day.percentile, 0)} ${arrow}`
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Stat, {
									k: "WEEK",
									v: `${fmtPct(card.week.percentile, 0)} ${arrow}`
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Stat, {
									k: "MONTH",
									v: fmtPct(card.month.percentile, 0)
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Stat, {
									k: "WEEK duration",
									v: `${card.week.durationAboveMean} w`
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Stat, {
									k: "Continuation",
									v: fmtPct(card.continuation, 0)
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Stat, {
									k: "Mean reversion",
									v: fmtPct(card.reversion, 0)
								})
							]
						}),
						card.durationCond ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
							className: "mt-3 text-sm text-muted",
							children: [
								"歷史上「已連續 ",
								card.durationCond.duration,
								" 週 ",
								">",
								"90%」：再升 ",
								fmtPct(card.durationCond.pContinue, 0),
								" · 回歸",
								" ",
								fmtPct(card.durationCond.pRevert, 0),
								" · 更極端 ",
								fmtPct(card.durationCond.pExtreme, 0),
								"（n=",
								card.durationCond.n,
								"）"
							]
						}) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "mt-3 text-sm text-muted",
							children: "目前 duration 的條件樣本不足，不硬估。"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
							className: "mt-3",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Badge, {
								tone: card.alert === "READY" ? "fragile" : card.alert === "WAIT" ? "mute" : "pass",
								children: card.alert
							})
						})
					]
				})]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "grid gap-4 lg:grid-cols-2",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Panel, {
					kicker: "WHAT HAPPENS AFTER",
					title: "超越後通常怎樣",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("dl", {
							className: "grid grid-cols-2 gap-3 text-sm",
							children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Stat, {
									k: "Persist 1w",
									v: fmtPct(card.persistence.p1, 0)
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Stat, {
									k: "Persist 3w",
									v: fmtPct(card.persistence.p3, 0)
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Stat, {
									k: "OOS persist",
									v: fmtPct(card.persistence.oosP1, 0)
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Stat, {
									k: "Model 5D",
									v: fmtPct(card.modelWeek, 1)
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Stat, {
									k: "Implied 5D",
									v: fmtPct(card.impliedWeek, 1)
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Stat, {
									k: "VOL EDGE",
									v: fmtPct(card.volEdge, 1)
								})
							]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
							className: "mt-3 text-xs text-subtle",
							children: [
								"頻率來自 TRAIN 相似百分位，時間衰減。Persistence ",
								card.persistence.score,
								"（n=",
								card.persistence.n,
								"）。沒有慣性要扣分。"
							]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
							className: "mt-2",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Badge, {
								tone: card.volEdge != null && card.volEdge > 0 ? "pass" : "fragile",
								children: "選擇權鏈仍 MISSING · IV 用 VIX 或 RV×1.15 代理"
							})
						})
					]
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Panel, {
					kicker: "NEXT THRESHOLD",
					title: "距離下一檔還有多少",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
							className: "font-mono text-sm tabular-nums",
							children: [
								"mean ",
								fmtPct(card.week.mean, 1),
								" · now ",
								fmtPct(card.week.current, 1),
								" · warn ",
								fmtPct(card.week.nextWarn, 1),
								" · extreme ",
								fmtPct(card.week.nextExtreme, 1)
							]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
							className: "mt-3 h-2 overflow-hidden rounded-sm bg-elevated",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
								className: "h-full bg-accent",
								style: { width: `${Math.min(100, (card.week.current || 0) / Math.max(card.week.nextExtreme || .01, .01) * 100)}%` }
							})
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
							className: "mt-2 text-sm text-muted",
							children: [
								"距 warning ",
								fmtPct(card.week.gapToWarn, 1),
								" · 現在 / 自身均值 ",
								fmtMul(card.week.ratio)
							]
						})
					]
				})]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Panel, {
				kicker: "BEST STRUCTURE · HYPOTHETICAL",
				title: best ? `${best.label} · ${best.score.toFixed(0)}/100` : "NO_TRADE",
				children: best ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "text-sm text-muted",
						children: best.legs
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
						className: "mt-2 font-mono text-xs tabular-nums text-subtle",
						children: [
							"EV ",
							fmtPct(best.ev, 2),
							" · POP ",
							fmtPct(best.pop, 0),
							" · breach ",
							fmtPct(best.breach.probability, 0),
							" · ES95",
							" ",
							fmtPct(best.breach.es95, 2),
							" · 連 3 次 ",
							fmtPct(best.breach.consecutive3, 1),
							" · 最長連穿 ",
							best.breach.maxConsecutive
						]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "mt-2 text-xs text-lock",
						children: "不是下單。Council 預設 NO_TRADE。真實 option chain = CAPABILITY_MISSING。"
					})
				] }) : null
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex flex-wrap gap-2",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Jump, {
						label: "最新",
						onClick: () => setCursor(lastBar)
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Jump, {
						label: "2020 壓力",
						onClick: () => setCursor(calendarIndexOf("2020-03-16"))
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Jump, {
						label: "2008",
						onClick: () => setCursor(calendarIndexOf("2008-10-10"))
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Jump, {
						label: "2023 起",
						onClick: () => setCursor(calendarIndexOf("2023-01-03"))
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
						className: "self-center font-mono text-xs tabular-nums text-subtle",
						children: ["bar ", cursor]
					})
				]
			})
		]
	}) });
}
function alertTitle(a) {
	if (a === "READY") return "HIGH STATE / 結構可競爭";
	if (a === "PRE_BREAKOUT") return "尚未破 90，但正在靠近";
	if (a === "EARLY") return "EARLY PREPARATION";
	return "沒有足夠狀態，先 WAIT";
}
function ScaleBlock({ title, s }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "rounded-md border border-line bg-elevated p-3",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "font-mono text-xs text-subtle",
				children: title
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Meter, {
				pct: s.percentile,
				label: s.level
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
				className: "mt-2 font-mono text-xs tabular-nums text-muted",
				children: [
					"now ",
					fmtPct(s.current, 1),
					" / mean ",
					fmtPct(s.mean, 1),
					" = ",
					fmtMul(s.ratio)
				]
			})
		]
	});
}
function Stat({ k, v }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("dt", {
		className: "font-mono text-xs text-subtle",
		children: k
	}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("dd", {
		className: "tabular-nums text-fg",
		children: v
	})] });
}
function Jump({ label, onClick }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
		type: "button",
		onClick,
		className: "min-h-11 rounded-sm border border-line px-3 text-sm text-muted hover:text-fg",
		children: label
	});
}
//#endregion
export { Page as component };
