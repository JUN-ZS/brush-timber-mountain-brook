(function (root) {
  "use strict";
  function validPositive(value) { return typeof value === "number" && Number.isFinite(value) && value > 0; }
  function parseDate(value) {
    if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
    const [year, month, day] = value.split("-").map(Number);
    const ms = Date.UTC(year, month - 1, day), d = new Date(ms);
    if (d.getUTCFullYear() !== year || d.getUTCMonth() !== month - 1 || d.getUTCDate() !== day) return null;
    return { year, month, day, ms };
  }
  function wholeMonthsBetween(startDate, today) {
    const start = parseDate(startDate), end = parseDate(today);
    if (!start || !end || start.ms > end.ms) return null;
    let months = (end.year - start.year) * 12 + end.month - start.month;
    if (end.day < start.day) months -= 1;
    return Math.max(0, months);
  }
  function evaluate(input) {
    const i = input && typeof input === "object" ? input : {};
    const base=i.baseCapitalUsd, nav=i.currentNavUsd, cash=i.currentCashUsd, horizon=i.horizonMonths, monthly=i.monthlyContributionUsd;
    const start=parseDate(i.startDate), today=parseDate(i.today), pending=[];
    if (!validPositive(base)) pending.push("starting capital B");
    if (!start) pending.push("valid plan start date");
    if (!(Number.isInteger(horizon)&&horizon>=1&&horizon<=600)) pending.push("horizon from 1 to 600 months");
    if (monthly!==null&&monthly!==undefined&&!(Number.isFinite(monthly)&&monthly>=0)) pending.push("monthly contribution >= 0");
    if (!today) pending.push("valid current date");
    if (start&&today&&start.ms>today.ms) pending.push("start date must not be in the future");
    const horizonOk=Number.isInteger(horizon)&&horizon>=1&&horizon<=600;
    const elapsedRaw=start&&today&&start.ms<=today.ms&&horizonOk?wholeMonthsBetween(i.startDate,i.today):null;
    const elapsed=elapsedRaw===null?null:Math.min(elapsedRaw,horizon);
    const remaining=elapsed===null||!horizonOk?null:Math.max(0,horizon-elapsed);
    const completion=elapsed===null||!horizonOk?null:elapsed/horizon*100;
    const floor=validPositive(base)&&elapsed!==null&&horizonOk?base*Math.min(elapsed/horizon,1):null;
    const gap=floor!==null&&validPositive(nav)?nav-floor:null;
    const plannedFuture=monthly!==null&&monthly!==undefined&&Number.isFinite(monthly)&&monthly>=0&&remaining!==null?monthly*remaining:null;
    const market=i.market&&typeof i.market==="object"?i.market:null;
    let status,nextAction;
    if(pending.some(x=>["starting capital B","valid plan start date","horizon from 1 to 600 months","valid current date","start date must not be in the future"].includes(x))){
      status="BASELINE_PENDING";nextAction="開局先確認起始基準 B、起始日與期限。APP 中原有的 NAV 預設值只是情境輸入；不要把示例數字當成已核實本金。";
    } else if(!validPositive(nav)){
      status="NAV_PENDING";nextAction="請輸入已核實的目前帳戶 NAV。未有現值時不評估底線距離，且不得把未入帳供款當作資金。";
    } else if(gap!==null&&gap< -0.005){
      status="FLOOR_BREACH";nextAction="目前 NAV 低於 CLOCK Floor。暫停新增風險，先對帳 NAV／入出金／已持倉與未成交單，再人工覆核；此狀態不會自動 SELL。";
    } else if(!market||market.blocked===true){
      status="WAIT_FOR_DATA";nextAction="暫停新部署：先刷新或核實 QQQ、VXX、VIX、VX M1/M2 的數值、來源、時區與日期；資料 BLOCKED 時不採用容量數字。";
    } else if(market.action==="REDUCE"||market.riskOff===true||market.high===true||market.backwardation===true){
      status="DEFENSIVE_REVIEW";nextAction="市場進入風險防守覆核：不加新 volatility-seller 風險，按原有閘檢視 VXX／賣方腿；QQQ Core 不因這條件自動清倉。";
    } else if(market.allowNew!==true){
      status="HOLD_NEW_CARRY";nextAction="目前市場閘不允許新增 Carry。保留現金與風險預算，下一個覆核週期再重算，不以價格猜測繞過狀態閘。";
    } else {
      status="CARRY_HUMAN_REVIEW";nextAction="市場閘只允許進入人工審查：按 CURRENT → TARGET、最大容量、真實可用現金、預留與共享風險池計算缺口；所有資料／合約／策略證據硬閘仍須通過，絕不自動下單。";
    }
    if(pending.length&&status!=="BASELINE_PENDING")nextAction+=" 另有待補資料："+pending.join("、")+"。";
    const labels={BASELINE_PENDING:"先鎖定基準",NAV_PENDING:"NAV 待確認",FLOOR_BREACH:"低於 CLOCK Floor · 暫停新增風險",WAIT_FOR_DATA:"市場資料封鎖 · 等資料",DEFENSIVE_REVIEW:"防守狀態 · 人工覆核",HOLD_NEW_CARRY:"HOLD · 暫停新增 Carry",CARRY_HUMAN_REVIEW:"CARRY · 只供人工審查"};
    return {
      status,statusLabel:labels[status]||"PENDING",nextAction,pending,
      baseCapitalUsd:validPositive(base)?base:null,startDate:start?i.startDate:null,horizonMonths:horizonOk?horizon:null,
      currentNavUsd:validPositive(nav)?nav:null,currentCashUsd:Number.isFinite(cash)&&cash>=0?cash:null,
      monthlyContributionUsd:Number.isFinite(monthly)&&monthly>=0?monthly:null,
      elapsedMonths:elapsed,remainingMonths:remaining,completionPct:completion,floorUsd:floor,floorGapUsd:gap,
      plannedFutureContributionsUsd:plannedFuture,
      marketGate:market?{state:market.state||null,blocked:market.blocked===true,allowNew:market.allowNew===true,action:market.action||null}:null,
      floorRule:"C_t = B * min(elapsedWholeMonths / horizonMonths, 1)",floorIsGuarantee:false,
      contributionsCountedInCurrentCash:false,forecastedCagr:null,forecastedMaxDrawdown:null,brokerOrders:false
    };
  }
  const api={evaluate,wholeMonthsBetween};
  if(typeof module!=="undefined"&&module.exports)module.exports=api;
  if(root)root.DeploymentRoadmapV1=api;
})(typeof window!=="undefined"?window:(typeof globalThis!=="undefined"?globalThis:this));
