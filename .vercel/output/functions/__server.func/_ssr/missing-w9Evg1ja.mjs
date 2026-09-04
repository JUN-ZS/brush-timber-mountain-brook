import { x as require_jsx_runtime } from "../_libs/@tanstack/react-router+[...].mjs";
import { _ as universe, a as Shell, n as MISSING_UNIVERSE, o as TRADED, r as Panel, t as Badge } from "./shell-BqaE3PNF.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/missing-w9Evg1ja.js
var import_jsx_runtime = require_jsx_runtime();
function Page() {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Shell, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "grid gap-4",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Panel, {
				kicker: "CAPABILITY_MISSING",
				title: "有日線的才進宇宙，沒有的不補造",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
					className: "max-w-2xl text-sm text-muted",
					children: [
						"現在用 Yahoo 調整收盤日線（",
						universe.source,
						"，asof ",
						universe.asof,
						"）。選擇權鏈、IV surface、買賣差仍全部缺失，所以結構競爭是 HYPOTHETICAL，Council 預設 NO_TRADE。"
					]
				})
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Panel, {
				kicker: "OBSERVED",
				title: `${TRADED.length} 檔有自己的 DAY/WEEK/MONTH 時間線`,
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "flex flex-wrap gap-2",
					children: TRADED.map((s) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Badge, {
						tone: "pass",
						children: [
							s,
							" ",
							universe.n[s]
						]
					}, s))
				})
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Panel, {
				kicker: "NOT IN PANEL",
				title: `${MISSING_UNIVERSE.length} 檔未下載`,
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "flex flex-wrap gap-2",
					children: MISSING_UNIVERSE.map((s) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Badge, {
						tone: "missing",
						children: s
					}, s))
				})
			})
		]
	}) });
}
//#endregion
export { Page as component };
