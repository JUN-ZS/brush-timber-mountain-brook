import { x as require_jsx_runtime } from "../_libs/@tanstack/react-router+[...].mjs";
import { a as Shell, f as fmtPct, h as stateMatrix, r as Panel, v as useRadar } from "./shell-BqaE3PNF.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/matrix-IqkI622L.js
var import_jsx_runtime = require_jsx_runtime();
var PRICES = [
	"STRONG_UP",
	"MOD_UP",
	"FLAT",
	"MOD_DOWN",
	"STRONG_DOWN"
];
var VOLS = [
	"CONTRACTING",
	"NORMAL",
	"EXPANDING",
	"EXTREME"
];
function Page() {
	const card = useRadar((s) => s.card);
	const cursor = useRadar((s) => s.cursor);
	const cells = card ? stateMatrix(card.symbol, cursor) : [];
	const lookup = new Map(cells.map((c) => [`${c.price}|${c.vol}`, c]));
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Shell, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "grid gap-4",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Panel, {
			kicker: "PRICE × VOL",
			title: "方向與波動必須分開",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "max-w-2xl text-sm text-muted",
				children: "Price ↑ Vol ↑ 不是 Price ↑ Vol ↓。格子裡是 TRAIN、且 k 小於現在 的下一週中位報酬。當格 n 太小就不讀。"
			}), card ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
				className: "mt-2 font-mono text-xs text-subtle",
				children: [
					"現在：",
					card.symbol,
					" · ",
					card.priceDir,
					" × ",
					card.volDir
				]
			}) : null]
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
			className: "overflow-x-auto rounded-xl border border-line",
			children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("table", {
				className: "w-full min-w-[720px] text-left text-sm",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("thead", {
					className: "bg-elevated text-xs text-subtle",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("tr", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
						className: "px-3 py-2 font-medium",
						children: "price \\ vol"
					}), VOLS.map((v) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
						className: "px-3 py-2 font-medium",
						children: v
					}, v))] })
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("tbody", { children: PRICES.map((p) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("tr", {
					className: "border-t border-line",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
						className: "px-3 py-3 font-mono text-xs text-muted",
						children: p
					}), VOLS.map((v) => {
						const cell = lookup.get(`${p}|${v}`);
						const here = card && card.priceDir === p && card.volDir === v;
						return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
							className: `px-3 py-3 ${here ? "bg-elevated" : ""}`,
							children: cell && cell.n >= 8 ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "font-mono text-xs tabular-nums",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { children: fmtPct(cell.medianNext, 1) }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
									className: "text-subtle",
									children: [
										"up ",
										fmtPct(cell.pUp, 0),
										" · n=",
										cell.n
									]
								})]
							}) : /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
								className: "text-subtle",
								children: ["n=", cell?.n ?? 0]
							})
						}, v);
					})]
				}, p)) })]
			})
		})]
	}) });
}
//#endregion
export { Page as component };
