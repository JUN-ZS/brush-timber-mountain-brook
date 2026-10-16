import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";

const root = process.cwd();
const logicPath = path.join(root, "research", "qqq_put_ratio_lab_v1", "logic.js");
const dataPath = path.join(root, "research", "qqq_put_ratio_lab_v1", "data.json");
const moduleBox = { exports: {} };
vm.runInNewContext(fs.readFileSync(logicPath, "utf8"), { module: moduleBox, console });
const L = moduleBox.exports;
const data = JSON.parse(fs.readFileSync(dataPath, "utf8"));

const cap = L.ratioInfo(80000, "SHORT_HEAVY", 5, 1, data);
assert.equal(cap.unitsByTerminalTail, 0, "$80k NAV at 1% terminal budget must block a 1x5 whole unit");
assert.ok(cap.lossPctOfNav > 268 && cap.lossPctOfNav < 269, "1x5 tail-loss arithmetic must be ~268% of $80k NAV");
assert.equal(L.matchedHistory("SHORT_HEAVY", 5, data).n, 62);
assert.equal(L.matchedHistory("SHORT_HEAVY", 4, data), null, "do not copy 1x5 win rate to other N");
assert.equal(L.volState(""), "ALL");
assert.equal(L.volState(14.9), "RV20_LT15");
assert.equal(L.volState(20), "RV20_15_25");
assert.equal(L.volState(30), "RV20_25_35");
assert.equal(L.volState(35), "RV20_GTE35");
const high = L.volRow(data, 40, 5);
const all = L.volRow(data, "", 5);
assert.ok(high.selected.down5Pct > all.all.down5Pct * 2, "high RV20 sample should show at least 2x the ALL 5-day >=5% down rate");
const alerts = L.alerts({nav:80000,direction:"SHORT_HEAVY",n:5,riskPct:1,profitPct:1,currentPnl:900,age:3,dte:25,rv20:40,horizon:5}, data);
assert.ok(alerts.some(a => a.title.includes("獲利 BAR 已達")));
assert.ok(alerts.some(a => a.title.includes("早段獲利")));
assert.ok(alerts.some(a => a.title.includes("尾部風險")));
assert.equal(data.metadata.priceRows, 1960);
assert.equal(data.metadata.optionEpisodes, 62);
assert.equal(data.events.plus1000Within5Sessions, 0);
const levels = data.drawdown.levels;
assert.deepEqual(levels.map(x => x.levelPct), [3,5,10,15,20,25,30]);
for (let i=1; i<levels.length; i++) {
  assert.ok(levels[i].episodes <= levels[i-1].episodes, "deeper drawdown counts cannot increase");
}

const tp800 = data.policies.find(x => x.id === "TP_USD_800_CLOSE_SHORT_RISK");
if (tp800) {
  assert.equal(tp800.n, 62, "$800 policy must use the same 62 episodes");
  assert.ok(Number.isFinite(tp800.netPnlUsd), "$800 net P&L must come from a direct replay");
}
if (data.events.profitThresholds) {
  assert.ok(data.events.profitThresholds["800"], "must expose direct $800 threshold event study");
  assert.ok(data.events.profitThresholds["1000"], "must retain direct $1,000 comparison");
  assert.ok(data.events.profitThresholds["800"].actualPolicyTriggerCount <= 62);
}

console.log("QQQ Put Ratio Lab contract PASS — NAV tail budget, matched history, time/vol alerts, drawdown tiers");
