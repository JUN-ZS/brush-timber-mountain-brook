#!/usr/bin/env python3
"""Build a dependency-free SVG chart pack for cash-flow, relative-rotation and floor research."""
from __future__ import annotations
import csv, datetime as dt, html, json, math
from pathlib import Path
from typing import Iterable
from cashflow_aware_qqq_spy import (
    DEFAULT_FLOOR_COST_USD, DEFAULT_FLOOR_FACE_USD, HORIZON_MONTHS,
    INITIAL_CAPITAL_USD, INDICATIVE_TEN_YEAR_PAR_YIELD, MonthlyPrice,
    _quantile, load_flow_schedule, load_monthly_prices, summarize_capital_floor_scenarios,
)

PALETTE = {
    "navy":"#183153","blue":"#3274A1","teal":"#2A9D8F","orange":"#E07A35",
    "red":"#C94C4C","purple":"#7966A8","gray":"#657184","light":"#D7DEE8",
    "grid":"#E8EDF3","paper":"#FFFFFF","ink":"#1E293B","muted":"#64748B",
    "pale_blue":"#EAF2F8","pale_teal":"#E7F5F2","pale_orange":"#FFF1E5",
}
CHARTS = (
    "01_relative_strength_rotation.svg","02_flexible_withdrawals.svg",
    "03_stock_to_bond_floor.svg","04_stock_to_bond_glidepath.svg",
    "05_cashflow_outcomes.svg",
)

def _e(value: object) -> str:
    return html.escape(str(value), quote=True)

def _money(value: float) -> str:
    return "$" + f"{value:,.0f}"

def _money_k(value: float) -> str:
    return "$" + f"{value / 1000:,.0f}" + "k"

def _fmt_pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.2f}%"

def _date_label(value: str) -> str:
    return value[:7]

def _svg_open(title: str, subtitle: str, width: int = 1200, height: int = 680) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-labelledby="title desc" width="{width}" height="{height}">'
        f'<title id="title">{_e(title)}</title><desc id="desc">{_e(subtitle)}</desc>'
        f'<rect width="{width}" height="{height}" rx="20" fill="{PALETTE["paper"]}"/>'
        f'<text x="42" y="48" font-size="27" font-weight="700" fill="{PALETTE["navy"]}">{_e(title)}</text>'
        f'<text x="42" y="78" font-size="14" fill="{PALETTE["muted"]}">{_e(subtitle)}</text>'
    )

def _svg_close(footer: str = "") -> str:
    tail = ""
    if footer:
        tail = f'<text x="42" y="654" font-size="12" fill="{PALETTE["muted"]}">{_e(footer)}</text>'
    return tail + "</svg>"

def _line_path(values: list[float], x0: float, y0: float, w: float, h: float, ymin: float, ymax: float) -> str:
    n = len(values)
    if not n:
        return ""
    span = ymax - ymin or 1.0
    return " ".join(
        ("M" if idx == 0 else "L") +
        f" {x0 + w * idx / max(1, n - 1):.2f} {y0 + h - ((value - ymin) / span * h):.2f}"
        for idx, value in enumerate(values)
    )

def build_relative_rotation(points: list[MonthlyPrice], lookback_months: int = 12) -> dict:
    """For month t-1 -> t, choose the asset using the trailing return known at t-1."""
    if lookback_months < 1 or len(points) <= lookback_months + 1:
        raise ValueError("Not enough observations for the requested relative-strength lookback")
    start_index = lookback_months
    qqq, spy, rotation = [100.0], [100.0], [100.0]
    selected: list[str] = []
    switches, last_selected = 0, None
    for current_index in range(start_index + 1, len(points)):
        signal_end = current_index - 1
        signal_start = signal_end - lookback_months
        signal_qqq = points[signal_end].qqq / points[signal_start].qqq - 1.0
        signal_spy = points[signal_end].spy / points[signal_start].spy - 1.0
        holding = "QQQ" if signal_qqq >= signal_spy else "SPY"
        if last_selected is not None and holding != last_selected:
            switches += 1
        last_selected = holding
        prior, current = points[current_index - 1], points[current_index]
        qqq.append(qqq[-1] * current.qqq / prior.qqq)
        spy.append(spy[-1] * current.spy / prior.spy)
        rotation.append(rotation[-1] * current.price(holding) / prior.price(holding))
        selected.append(holding)
    dates = [point.date.isoformat() for point in points[start_index:]]
    years = (points[-1].date - points[start_index].date).days / 365.25
    def stats(values: list[float]) -> dict:
        peak, maxdd = values[0], 0.0
        for value in values:
            peak = max(peak, value)
            if peak > 0:
                maxdd = min(maxdd, value / peak - 1.0)
        cagr = (values[-1] / values[0]) ** (1 / years) - 1 if years > 0 else None
        return {"terminal_index": values[-1], "cagr": cagr, "max_drawdown": maxdd}
    return {
        "lookback_months": lookback_months, "dates": dates,
        "series": [
            {"label":"QQQ buy & hold","values":qqq,"color":PALETTE["blue"]},
            {"label":"SPY buy & hold","values":spy,"color":PALETTE["teal"]},
            {"label":"12m relative-strength rotation","values":rotation,"color":PALETTE["orange"]},
        ],
        "selected_assets": selected, "switch_count": switches,
        "statistics": {"QQQ buy & hold":stats(qqq),"SPY buy & hold":stats(spy),
                       "12m relative-strength rotation":stats(rotation)},
    }

def render_line_chart(title: str, subtitle: str, dates: list[str], series: list[dict],
                      y_label: str, footer: str, value_format: str = "index") -> str:
    width, height = 1200, 680
    x0, y0, w, h = 92, 125, 1064, 420
    flat = [float(v) for row in series for v in row["values"] if math.isfinite(float(v))]
    if not flat:
        raise ValueError("Cannot chart an empty series")
    ymin, ymax = min(0.0, min(flat)), max(flat) * 1.08
    if ymax <= ymin:
        ymax = ymin + 1.0
    span = ymax - ymin
    svg = [_svg_open(title, subtitle, width, height)]
    svg.append(f'<text x="28" y="340" transform="rotate(-90 28 340)" font-size="13" fill="{PALETTE["muted"]}">{_e(y_label)}</text>')
    for i in range(6):
        value = ymin + span * i / 5
        y = y0 + h - ((value - ymin) / span * h)
        svg.append(f'<line x1="{x0}" y1="{y:.2f}" x2="{x0+w}" y2="{y:.2f}" stroke="{PALETTE["grid"]}"/>')
        label = _money_k(value) if value_format == "usd" else f"{value:,.0f}"
        svg.append(f'<text x="{x0-12}" y="{y+5:.2f}" text-anchor="end" font-size="12" fill="{PALETTE["muted"]}">{_e(label)}</text>')
    for pos in sorted(set((0, len(dates)//3, 2*len(dates)//3, len(dates)-1))):
        if not dates: continue
        x = x0 + w * pos / max(1, len(dates)-1)
        svg.append(f'<line x1="{x:.2f}" y1="{y0}" x2="{x:.2f}" y2="{y0+h}" stroke="{PALETTE["grid"]}"/>')
        svg.append(f'<text x="{x:.2f}" y="{y0+h+26}" text-anchor="middle" font-size="12" fill="{PALETTE["muted"]}">{_e(_date_label(dates[pos]))}</text>')
    for row in series:
        svg.append(f'<path d="{_line_path([float(v) for v in row["values"]],x0,y0,w,h,ymin,ymax)}" fill="none" stroke="{row["color"]}" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>')
    legend_y, legend_x = 600, 95
    for row in series:
        svg.append(f'<line x1="{legend_x}" y1="{legend_y}" x2="{legend_x+28}" y2="{legend_y}" stroke="{row["color"]}" stroke-width="4"/>')
        svg.append(f'<text x="{legend_x+36}" y="{legend_y+5}" font-size="13" fill="{PALETTE["ink"]}">{_e(row["label"])}</text>')
        legend_x += max(255, 17 + len(str(row["label"])) * 7)
    svg.append(_svg_close(footer))
    return "".join(svg)

def render_cashflow_schedule_svg(schedule: dict[int, list]) -> str:
    width, height = 1200, 680
    x0, y0, w, h = 98, 135, 1055, 400
    events = []
    for month, rows in sorted(schedule.items()):
        for event in rows:
            signed = event.amount_usd if event.flow_type == "deposit" else -event.amount_usd
            events.append({"month":month,"type":event.flow_type,"amount":event.amount_usd,
                           "signed":signed,"note":event.note})
    if not events:
        raise ValueError("Schedule chart requires at least one cash-flow event")
    y_min, y_max = min(-1.0, min(e["signed"] for e in events)*1.15), max(1.0,max(e["signed"] for e in events)*1.15)
    total_wd = sum(e["amount"] for e in events if e["type"] == "withdrawal")
    total_dep = sum(e["amount"] for e in events if e["type"] == "deposit")
    svg = [_svg_open("提款／再投入時間表",
        "示例事件日曆；正值＝額外投入，負值＝提款；金額與時間皆可改，不代表預設支出",width,height)]
    def yy(value: float) -> float:
        return y0 + h - ((value-y_min)/(y_max-y_min)*h)
    zero_y = yy(0)
    svg.append(f'<line x1="{x0}" y1="{zero_y:.2f}" x2="{x0+w}" y2="{zero_y:.2f}" stroke="{PALETTE["ink"]}" stroke-width="1.5"/>')
    svg.append(f'<text x="{x0-14}" y="{zero_y+5:.2f}" text-anchor="end" font-size="12" fill="{PALETTE["muted"]}">$0</text>')
    bar_width = min(72,w/max(1,len(events))*0.55)
    for e in events:
        x = x0 + w*e["month"]/HORIZON_MONTHS
        y_val = yy(e["signed"])
        rect_y, rect_h = min(zero_y,y_val), max(2,abs(zero_y-y_val))
        color = PALETTE["blue"] if e["type"] == "deposit" else PALETTE["orange"]
        svg.append(f'<rect x="{x-bar_width/2:.2f}" y="{rect_y:.2f}" width="{bar_width:.2f}" height="{rect_h:.2f}" rx="5" fill="{color}" opacity="0.92"/>')
        label_y = rect_y-8 if e["signed"] >= 0 else rect_y+rect_h+17
        svg.append(f'<text x="{x:.2f}" y="{label_y:.2f}" text-anchor="middle" font-size="12" font-weight="600" fill="{PALETTE["ink"]}">{_e(_money(e["amount"]))}</text>')
        svg.append(f'<text x="{x:.2f}" y="{y0+h+23}" text-anchor="middle" font-size="12" fill="{PALETTE["muted"]}">M{e["month"]}</text>')
    for month in (0,12,24,36,48,60,72,84,96,108,120):
        x = x0+w*month/HORIZON_MONTHS
        svg.append(f'<line x1="{x:.2f}" y1="{y0+h}" x2="{x:.2f}" y2="{y0+h+7}" stroke="{PALETTE["muted"]}"/>')
    svg.append(f'<text x="{x0}" y="108" font-size="14" fill="{PALETTE["ink"]}">提款合計：{_e(_money(total_wd))}　　再投入合計：{_e(_money(total_dep))}</text>')
    svg.append(f'<line x1="830" y1="92" x2="858" y2="92" stroke="{PALETTE["orange"]}" stroke-width="6"/><text x="866" y="97" font-size="13" fill="{PALETTE["ink"]}">提款</text>')
    svg.append(f'<line x1="935" y1="92" x2="963" y2="92" stroke="{PALETTE["blue"]}" stroke-width="6"/><text x="971" y="97" font-size="13" fill="{PALETTE["ink"]}">再投入</text>')
    svg.append(_svg_close("月份是相對於投資開始的月份。首年沒有事件；實際可跳過年份、調低／調高金額或另加投入。"))
    return "".join(svg)

def render_floor_waterfall_svg(noflow_summaries: list[dict], floor_cost: float = DEFAULT_FLOOR_COST_USD,
                               floor_face: float = DEFAULT_FLOOR_FACE_USD) -> str:
    width, height = 1200, 700
    growth = INITIAL_CAPITAL_USD - floor_cost
    svg = [_svg_open("股票資金轉成「到期本金保護」的起始資金圖",
        "把起始本金分成到期債券層與成長層；只保護匹配債券的到期面值，不代表中途組合淨值不跌",width,height)]
    boxes = [
        (45,132,230,110,PALETTE["pale_blue"],"起始資金",_money(INITIAL_CAPITAL_USD),"USD"),
        (367,132,295,110,PALETTE["pale_teal"],"10年期零息債成本*",_money(floor_cost),"示例佔比 "+f"{floor_cost/INITIAL_CAPITAL_USD:.1%}"),
        (367,284,295,110,PALETTE["pale_orange"],"股票／成長層",_money(growth),"示例佔比 "+f"{growth/INITIAL_CAPITAL_USD:.1%}"),
        (780,132,370,110,PALETTE["pale_teal"],"第10年債券到期面值",_money(floor_face),"不拿來付中途支出"),
        (780,284,370,110,PALETTE["pale_orange"],"第10年剩餘成長層","依市場而變","先由成長層支付提款"),
    ]
    for x,y,bw,bh,fill,title,value,detail in boxes:
        svg.append(f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" rx="14" fill="{fill}" stroke="{PALETTE["light"]}"/>')
        svg.append(f'<text x="{x+bw/2}" y="{y+29}" text-anchor="middle" font-size="15" font-weight="600" fill="{PALETTE["navy"]}">{_e(title)}</text>')
        svg.append(f'<text x="{x+bw/2}" y="{y+65}" text-anchor="middle" font-size="24" font-weight="700" fill="{PALETTE["ink"]}">{_e(value)}</text>')
        svg.append(f'<text x="{x+bw/2}" y="{y+89}" text-anchor="middle" font-size="12" fill="{PALETTE["muted"]}">{_e(detail)}</text>')
    svg.extend([
        f'<path d="M 275 187 L 320 187 L 352 187 M 320 187 L 320 339 L 352 339" fill="none" stroke="{PALETTE["gray"]}" stroke-width="2.5"/>',
        f'<path d="M 662 187 L 720 187 L 765 187" fill="none" stroke="{PALETTE["teal"]}" stroke-width="2.5"/>',
        f'<path d="M 662 339 L 720 339 L 765 339" fill="none" stroke="{PALETTE["orange"]}" stroke-width="2.5"/>',
        f'<text x="45" y="438" font-size="16" font-weight="700" fill="{PALETTE["navy"]}">同一批歷史10年窗口的成長層比較（沒有中途提款）</text>',
    ])
    summary = {str(r["scenario"]):r for r in noflow_summaries}
    entries = [
        ("FLOOR_PLUS_QQQ","保本層 + QQQ",PALETTE["blue"]),
        ("FLOOR_PLUS_SPY","保本層 + SPY",PALETTE["teal"]),
        ("FLOOR_PLUS_QQQ_SPY_50_50","保本層 + QQQ/SPY 50:50",PALETTE["purple"]),
        ("FLOOR_PLUS_CASH_0PCT","保本層 + 0%現金",PALETTE["gray"]),
    ]
    for idx,(key,label,color) in enumerate(entries):
        y = 470+idx*43
        row = summary[key]
        svg.extend([
            f'<rect x="47" y="{y-14}" width="9" height="23" rx="3" fill="{color}"/>',
            f'<text x="68" y="{y+3}" font-size="14" fill="{PALETTE["ink"]}">{_e(label)}</text>',
            f'<text x="475" y="{y+3}" font-size="14" fill="{PALETTE["ink"]}">中位數 {_e(_money(float(row["median_terminal_nav_usd"])))}</text>',
            f'<text x="705" y="{y+3}" font-size="14" fill="{PALETTE["ink"]}">5百分位 {_e(_money(float(row["p05_terminal_nav_usd"])))}</text>',
            f'<text x="930" y="{y+3}" font-size="14" fill="{PALETTE["ink"]}">最差 {_e(_money(float(row["worst_terminal_nav_usd"])))}</text>',
        ])
    svg.append(_svg_close("*成本以2026-10-16的10年期公債par yield 5.09%作半年度複利示例；不是可執行STRIPS報價。價格序列不含股息、稅費與現金利息。"))
    return "".join(svg)

def glidepath_data(target_conversion_percentages: Iterable[int] = (30,40,50,60,70,80,90,100)) -> list[dict]:
    """Illustrative ten-year glidepaths; target is total original stock sleeve converted by year 10."""
    colors = [
        "#657184", "#3274A1", "#2A9D8F", "#E07A35",
        "#7966A8", "#C94C4C", "#4C78A8", "#1B7F79",
    ]
    result = []
    seen = set()
    for index, target in enumerate(target_conversion_percentages):
        if not isinstance(target, int) or not 0 <= target <= 100:
            raise ValueError("Each target conversion must be an integer percentage from 0 to 100")
        if target in seen:
            raise ValueError(f"Duplicate glidepath target: {target}")
        seen.add(target)
        bonds = [target * year / 10 for year in range(11)]
        stocks = [100 - value for value in bonds]
        result.append({
            "target_conversion_percent": target,
            "label": f"第10年轉{target}%到債券",
            "stocks": stocks,
            "bonds": bonds,
            "color": colors[index % len(colors)],
        })
    return result

def render_glidepath_svg() -> str:
    width, height = 1200, 690
    x0, y0, w, h = 92, 125, 1064, 370
    rows = glidepath_data()
    svg = [_svg_open(
        "股票逐年轉債券：比較第10年轉換30%–100%",
        "每條線是一個目標：十年內逐年等額轉移初始股票配置；圖只比較配置路徑，不是債券績效回測",
        width, height,
    )]
    for pct in (0,20,40,60,80,100):
        y = y0 + h - pct / 100 * h
        svg.extend([
            f'<line x1="{x0}" y1="{y:.2f}" x2="{x0+w}" y2="{y:.2f}" stroke="{PALETTE["grid"]}"/>',
            f'<text x="{x0-12}" y="{y+5:.2f}" text-anchor="end" font-size="12" fill="{PALETTE["muted"]}">{pct}%</text>',
        ])
    for year in range(11):
        x = x0 + w * year / 10
        svg.extend([
            f'<line x1="{x:.2f}" y1="{y0}" x2="{x:.2f}" y2="{y0+h}" stroke="{PALETTE["grid"]}"/>',
            f'<text x="{x:.2f}" y="{y0+h+23}" text-anchor="middle" font-size="12" fill="{PALETTE["muted"]}">{year}</text>',
        ])
    for row in rows:
        svg.append(
            f'<path d="{_line_path(row["stocks"],x0,y0,w,h,0,100)}" fill="none" '
            f'stroke="{row["color"]}" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>'
        )
    # Two rows of four legend items keeps all eight 30%-100% targets readable.
    for index, row in enumerate(rows):
        legend_row = index // 4
        legend_col = index % 4
        lx = 95 + legend_col * 278
        ly = 545 + legend_row * 29
        svg.extend([
            f'<line x1="{lx}" y1="{ly}" x2="{lx+24}" y2="{ly}" stroke="{row["color"]}" stroke-width="4"/>',
            f'<text x="{lx+32}" y="{ly+5}" font-size="12" fill="{PALETTE["ink"]}">{_e(row["label"])}</text>',
        ])
    svg.extend([
        f'<rect x="90" y="600" width="1070" height="35" rx="7" fill="{PALETTE["pale_blue"]}"/>',
        f'<text x="104" y="622" font-size="12" fill="{PALETTE["navy"]}">例如：第10年轉30% → 股票70%／債券30%；轉60% → 各50%；轉100% → 股票0%／債券100%。按初始股票配置的固定比例逐年轉換。</text>',
        _svg_close("債券回報、久期、價格波動、稅費及提前出售成本尚未加入；比較配置比例不代表選出最高收益方案。"),
    ])
    return "".join(svg)

def _range_rows(noflow_rows: list[dict], cashflow_rows: list[dict], scenario_names: list[str]) -> list[dict]:
    result=[]
    for mode,rows,label in (("no_withdrawals",noflow_rows,"不提款"),("delayed_stepup_demo",cashflow_rows,"遞增提款示例")):
        for scenario in scenario_names:
            group=[r for r in rows if r["scenario"]==scenario]
            terminal=[float(r["terminal_nav_usd"]) for r in group]
            xs=[float(r["investor_xirr"]) for r in group if r.get("investor_xirr") is not None]
            withdrawals=[float(r.get("actual_withdrawals_usd",0.0)) for r in group]
            shortfalls=[float(r.get("withdrawal_shortfall_usd",0.0)) for r in group]
            if not terminal: continue
            result.append({
                "cashflow_mode":mode,"mode_label":label,"scenario":scenario,
                "p05_terminal_nav_usd":round(_quantile(terminal,0.05) or 0.0,2),
                "median_terminal_nav_usd":round(_quantile(terminal,0.50) or 0.0,2),
                "p95_terminal_nav_usd":round(_quantile(terminal,0.95) or 0.0,2),
                "worst_terminal_nav_usd":round(min(terminal),2),
                "median_actual_withdrawals_usd":round(_quantile(withdrawals,0.50) or 0.0,2),
                "p95_withdrawal_shortfall_usd":round(_quantile(shortfalls,0.95) or 0.0,2),
                "median_investor_xirr":_quantile(xs,0.5),"rolling_windows":len(group),
            })
    return result

def render_outcome_range_svg(rows: list[dict]) -> str:
    width,height=1280,780
    x0,y0,w,row_h=395,150,490,57
    minval=min(float(r["p05_terminal_nav_usd"]) for r in rows)
    maxval=max(float(r["p95_terminal_nav_usd"]) for r in rows)
    padding=(maxval-minval)*0.06 or 1000.0
    minval,maxval=max(0.0,minval-padding),maxval+padding
    span=maxval-minval or 1.0
    names={"FLOOR_PLUS_CASH_0PCT":"保本層 + 現金","FLOOR_PLUS_QQQ":"保本層 + QQQ",
           "FLOOR_PLUS_SPY":"保本層 + SPY","FLOOR_PLUS_QQQ_SPY_50_50":"保本層 + QQQ/SPY 50:50"}
    svg=[_svg_open("提款前後：第10年終值分布與提款缺口",
        "同一組211個重疊歷史窗口；線段＝5–95百分位，圓點＝中位數；終值未包含已提取的現金",width,height)]
    for tick in range(6):
        value=minval+span*tick/5
        x=x0+w*tick/5
        svg.extend([f'<line x1="{x:.2f}" y1="{y0-12}" x2="{x:.2f}" y2="{y0+row_h*8}" stroke="{PALETTE["grid"]}"/>',
                    f'<text x="{x:.2f}" y="{y0-22}" text-anchor="middle" font-size="12" fill="{PALETTE["muted"]}">{_e(_money_k(value))}</text>'])
    colors={"FLOOR_PLUS_CASH_0PCT":PALETTE["gray"],"FLOOR_PLUS_QQQ":PALETTE["blue"],
            "FLOOR_PLUS_SPY":PALETTE["teal"],"FLOOR_PLUS_QQQ_SPY_50_50":PALETTE["purple"]}
    for idx,row in enumerate(rows):
        y=y0+idx*row_h+14
        svg.extend([
            f'<text x="42" y="{y+4}" font-size="13" fill="{PALETTE["ink"]}">{_e(names[row["scenario"]])}</text>',
            f'<text x="238" y="{y+4}" font-size="12" fill="{PALETTE["muted"]}">{_e("不提款" if row["cashflow_mode"]=="no_withdrawals" else "提款示例")}</text>',
        ])
        p05,med,p95=(float(row[k]) for k in ("p05_terminal_nav_usd","median_terminal_nav_usd","p95_terminal_nav_usd"))
        xp05,xmed,xp95=(x0+(v-minval)/span*w for v in (p05,med,p95))
        color=colors[row["scenario"]]
        svg.extend([
            f'<line x1="{xp05:.2f}" y1="{y}" x2="{xp95:.2f}" y2="{y}" stroke="{color}" stroke-width="7" stroke-linecap="round" opacity="0.55"/>',
            f'<circle cx="{xmed:.2f}" cy="{y}" r="7" fill="{color}" stroke="#FFFFFF" stroke-width="2"/>',
            f'<text x="905" y="{y+3}" font-size="12" fill="{PALETTE["ink"]}">中位終值 {_e(_money(med))}</text>',
            f'<text x="1080" y="{y+3}" font-size="12" fill="{PALETTE["ink"]}">已取 {_e(_money(float(row["median_actual_withdrawals_usd"])))}</text>',
            f'<text x="1080" y="{y+18}" font-size="11" fill="{PALETTE["muted"]}">P95缺口 {_e(_money(float(row["p95_withdrawal_shortfall_usd"])))}</text>',
        ])
    svg.append(f'<text x="{x0+w/2}" y="{y0+row_h*8+26}" text-anchor="middle" font-size="13" fill="{PALETTE["muted"]}">第10年終值（美元）</text>')
    svg.append(_svg_close("提款金額只用來驗證現金流算術，不是預設。分布來自重疊歷史窗口，不是未來成功機率。"))
    return "".join(svg)

def generate_chart_pack(input_path: Path, flows_path: Path, outdir: Path) -> dict:
    points,digest=load_monthly_prices(input_path)
    schedule=load_flow_schedule(flows_path)
    rotation=build_relative_rotation(points,12)
    no_summaries,no_rows=summarize_capital_floor_scenarios(points)
    flow_summaries,flow_rows=summarize_capital_floor_scenarios(points,custom_schedule=schedule)
    scenario_names=["FLOOR_PLUS_CASH_0PCT","FLOOR_PLUS_QQQ","FLOOR_PLUS_SPY","FLOOR_PLUS_QQQ_SPY_50_50"]
    ranges=_range_rows(no_rows,flow_rows,scenario_names)
    outdir.mkdir(parents=True,exist_ok=True)
    svgs={
        CHARTS[0]:render_line_chart("相對強弱「互追」：QQQ／SPY輪動",
            "每月末用過去12個月已知表現選下一個月持有標的；與同日起算買入持有比較",
            rotation["dates"],rotation["series"],"起始=100的價格指數",
            "僅價格、不含股息再投資、交易成本、稅項；相對強弱不是債券輪動。"),
        CHARTS[1]:render_cashflow_schedule_svg(schedule),
        CHARTS[2]:render_floor_waterfall_svg(no_summaries),
        CHARTS[3]:render_glidepath_svg(),
        CHARTS[4]:render_outcome_range_svg(ranges),
    }
    for name,content in svgs.items():
        (outdir/name).write_text(content,encoding="utf-8")
    with (outdir/"cashflow_outcome_ranges.csv").open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(ranges[0].keys()))
        writer.writeheader(); writer.writerows(ranges)
    report={
        "schema":"cashflow-visual-exploration.v1",
        "input":{"sha256":digest,"monthly_observations":len(points),
                 "first_month":points[0].date.isoformat(),"last_month":points[-1].date.isoformat(),
                 "rolling_ten_year_windows":len(points)-HORIZON_MONTHS},
        "interpretations":{
            "mutual_chase":"QQQ vs SPY monthly relative strength; uses trailing 12-month returns known at the previous month end to select the next month's holding.",
            "withdrawal_chart":"Illustrative schedule only; not a user default or recommendation.",
            "stock_to_bond_floor":"Maturity-matched nominal floor cost derived from a 10-year par yield, not an executable STRIPS quote or historical bond-price replay.",
            "stock_to_bond_glidepath":"Allocation-only rule comparison; not a return backtest.",
            "outcome_distribution":"Same overlapping historical windows; equities are price-only; withdrawals are paid from growth sleeve only; floor never pays spending."},
        "assumptions":{"initial_capital_usd":INITIAL_CAPITAL_USD,"floor_face_usd":DEFAULT_FLOOR_FACE_USD,
            "floor_cost_usd":round(DEFAULT_FLOOR_COST_USD,2),
            "growth_sleeve_usd":round(INITIAL_CAPITAL_USD-DEFAULT_FLOOR_COST_USD,2),
            "par_yield_proxy":INDICATIVE_TEN_YEAR_PAR_YIELD,"par_yield_date":"2026-10-16",
            "withdrawal_events":sum(len(v) for v in schedule.values()),
            "withdrawal_sum_usd":round(sum(e.amount_usd for group in schedule.values() for e in group if e.flow_type=="withdrawal"),2),
            "deposit_sum_usd":round(sum(e.amount_usd for group in schedule.values() for e in group if e.flow_type=="deposit"),2),
            "taxes_fees_and_equity_dividends_included":False,"bond_market_value_and_duration_included":False,
            "rolling_windows_are_independent_trials":False},
        "relative_rotation":{"lookback_months":12,"switch_count":rotation["switch_count"],"statistics":rotation["statistics"]},
        "glidepath_scenarios": glidepath_data(),
        "no_withdrawal_floor_summaries":no_summaries,"sample_schedule_floor_summaries":flow_summaries,
        "outcome_ranges":ranges,"chart_files":list(CHARTS)}
    (outdir/"chart_summary.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    sections=[
        ("相對強弱互追",CHARTS[0],"回看12個月、下一個月執行；這裡是QQQ對SPY，不是債券輪動。"),
        ("提款與再投入",CHARTS[1],"示例先空過首年，之後逐級提款，並包含一次額外投入。"),
        ("起始股票／保本債券分層",CHARTS[2],"以期初成本換取到期名義面值；尚未有真實STRIPS成交報價。"),
        ("逐年股票轉債券規則",CHARTS[3],"只比較配置規則，沒有假裝模擬債券報酬。"),
        ("提款對第10年終值的影響",CHARTS[4],"同時呈現終值、已取現金與缺口，避免只看帳戶餘額。")]
    page=["<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        "<title>Cash-flow / Stock-Bond Chart Lab</title>",
        "<style>body{font-family:system-ui,-apple-system,Segoe UI,sans-serif;max-width:1320px;margin:24px auto;padding:0 18px;color:#1e293b;background:#f7f9fc}h1{color:#183153}section{background:white;border:1px solid #d7dee8;border-radius:16px;padding:18px;margin:20px 0;box-shadow:0 3px 12px #1831530a}section svg{width:100%;height:auto;display:block}p{line-height:1.6;color:#475569}.warn{background:#fff1e5;padding:12px;border-radius:8px}</style></head><body>",
        "<h1>度量衡：互追／提款／股票轉債圖表原型</h1>",
        "<p>來源SHA-256：<code>"+_e(digest)+"</code>；月度資料 "+str(len(points))+" 點；十年窗口 "+str(len(points)-HORIZON_MONTHS)+" 個。</p>",
        "<p class='warn'><b>研究限制：</b>QQQ／SPY是價格序列，不含股息再投資。到期保本層使用10年公債par yield換算成本作占位，並非實際STRIPS報價。逐年股轉債圖只表示配置路徑；本圖包不是交易指示。</p>"]
    for title,filename,description in sections:
        page.extend(["<section><h2>",_e(title),"</h2><p>",_e(description),"</p>",svgs[filename],"</section>"])
    page.append("</body></html>")
    (outdir/"index.html").write_text("".join(page)+"\n",encoding="utf-8")
    return report

def main() -> int:
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,required=True,help="SHA-pinned daily CSV with Date, QQQ and SPY")
    parser.add_argument("--flows-csv",type=Path,required=True,help="Illustrative custom cashflow schedule")
    parser.add_argument("--outdir",type=Path,required=True,help="Destination for SVG/HTML/JSON/CSV chart bundle")
    args=parser.parse_args()
    report=generate_chart_pack(args.input,args.flows_csv,args.outdir)
    print(json.dumps({"schema":report["schema"],"input":report["input"],
        "relative_rotation":report["relative_rotation"],"chart_files":report["chart_files"],
        "output_dir":args.outdir.as_posix()},ensure_ascii=False,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
