#!/usr/bin/env python3
"""Generate objective-based conclusions and a risk/return frontier from the glidepath replay."""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

from stock_bond_glidepath_backtest import (
    BOND_TICKERS,
    COLORS,
    TIMING_RULES,
    TIMING_LABELS,
    _esc,
    _money,
    _svg_open,
)

FLOW_MODES = (
    "delayed_stepup_example",
    "monthly_withdrawal_500_usd_stress",
    "monthly_withdrawal_1000_usd_stress",
)
FLOW_LABELS = {
    "delayed_stepup_example": "延遲／升降提款示例（提款 $12,800；後續投入 $5,000）",
    "monthly_withdrawal_500_usd_stress": "每月提款 $500（十年要求 $60,000）",
    "monthly_withdrawal_1000_usd_stress": "每月提款 $1,000（十年要求 $120,000）",
}


def pct(value: float | None) -> str:
    return "N/A" if value is None else f"{float(value) * 100:.2f}%"


def _candidate(row: dict) -> dict:
    fields = (
        "bond_proxy", "target_bond_conversion_pct_at_year10", "timing_rule",
        "median_terminal_nav_usd", "p05_terminal_nav_usd", "p95_terminal_nav_usd",
        "worst_terminal_nav_usd", "median_time_weighted_cagr", "p05_time_weighted_cagr",
        "median_daily_max_drawdown", "worst_daily_max_drawdown",
        "windows_below_initial_capital_at_year10", "windows_with_withdrawal_shortfall",
        "p95_withdrawal_shortfall_usd", "rolling_windows",
    )
    result = {key: row.get(key) for key in fields}
    result["scenario_label"] = (
        f'{row["bond_proxy"]}｜第10年目標 {row["target_bond_conversion_pct_at_year10"]}%｜'
        f'{TIMING_LABELS[row["timing_rule"]]}'
    )
    return result


def pareto_frontier(rows: list[dict]) -> list[dict]:
    """Maximise median return while minimising the magnitude of median drawdown."""
    valid = [
        row for row in rows
        if row.get("median_time_weighted_cagr") is not None
        and row.get("median_daily_max_drawdown") is not None
    ]
    frontier, eps = [], 1e-12
    for row in valid:
        ret = float(row["median_time_weighted_cagr"])
        risk = abs(float(row["median_daily_max_drawdown"]))
        is_dominated = any(
            float(other["median_time_weighted_cagr"]) >= ret - eps
            and abs(float(other["median_daily_max_drawdown"])) <= risk + eps
            and (
                float(other["median_time_weighted_cagr"]) > ret + eps
                or abs(float(other["median_daily_max_drawdown"])) < risk - eps
            )
            for other in valid if other is not row
        )
        if not is_dominated:
            frontier.append(row)
    return sorted(frontier, key=lambda row: (
        abs(float(row["median_daily_max_drawdown"])),
        -float(row["median_time_weighted_cagr"]),
    ))


def build_decision_summary(scenarios: list[dict]) -> dict:
    """Summarise separate objectives; intentionally does not manufacture a weighted score."""
    noflow = [row for row in scenarios if row["cashflow_mode"] == "no_withdrawals"]
    if not noflow:
        raise ValueError("Decision summary requires no-withdrawal scenarios")
    growth = max(noflow, key=lambda r: (float(r["median_time_weighted_cagr"]), float(r["median_terminal_nav_usd"])))
    lower_drawdown = max(noflow, key=lambda r: float(r["median_daily_max_drawdown"]))
    terminal = max(noflow, key=lambda r: float(r["median_terminal_nav_usd"]))
    frontier = pareto_frontier(noflow)
    agg_linear = sorted(
        (r for r in noflow if r["bond_proxy"] == "AGG" and r["timing_rule"] == "linear"),
        key=lambda r: int(r["target_bond_conversion_pct_at_year10"]),
    )
    agg_60 = sorted(
        (r for r in noflow if r["bond_proxy"] == "AGG" and int(r["target_bond_conversion_pct_at_year10"]) == 60),
        key=lambda r: TIMING_RULES.index(r["timing_rule"]),
    )
    cashflow = {}
    for mode, label in FLOW_LABELS.items():
        selected = [r for r in scenarios if r["cashflow_mode"] == mode]
        if not selected:
            continue
        counts = [int(r["windows_with_withdrawal_shortfall"]) for r in selected]
        cashflow[mode] = {
            "label": label,
            "configurations": len(selected),
            "configurations_with_any_shortfall": sum(count > 0 for count in counts),
            "min_windows_with_shortfall": min(counts),
            "max_windows_with_shortfall": max(counts),
            "max_p95_shortfall_usd": round(max(float(r["p95_withdrawal_shortfall_usd"]) for r in selected), 2),
        }
    return {
        "selection_note": "Separate historical candidates are selected by their stated metric, not a hidden blended score. The risk/return frontier is descriptive, not a forecast or recommendation.",
        "rolling_windows": int(noflow[0]["rolling_windows"]),
        "no_withdrawal_configurations": len(noflow),
        "growth_oriented": _candidate(growth),
        "lower_median_drawdown": _candidate(lower_drawdown),
        "highest_median_terminal_wealth": _candidate(terminal),
        "pareto_frontier": [_candidate(row) for row in frontier],
        "agg_linear_target_scan": [_candidate(row) for row in agg_linear],
        "agg_60_timing_comparison": [_candidate(row) for row in agg_60],
        "withdrawal_stress": cashflow,
    }


def render_frontier(rows: list[dict]) -> str:
    """Create an SVG scatter plot for all no-flow choices; label non-dominated choices only."""
    width, height = 1360, 760
    x0, y0, plot_w, plot_h = 105, 118, 800, 475
    valid = [r for r in rows if r.get("median_time_weighted_cagr") is not None and r.get("median_daily_max_drawdown") is not None]
    if not valid:
        raise ValueError("No valid scenarios for risk-return frontier")
    frontier = pareto_frontier(valid)
    risks = [abs(float(r["median_daily_max_drawdown"])) for r in valid]
    returns = [float(r["median_time_weighted_cagr"]) for r in valid]
    xmax = max(risks) * 1.10 + 0.01
    ymin = min(returns) - max(0.01, (max(returns) - min(returns)) * 0.10)
    ymax = max(returns) + max(0.01, (max(returns) - min(returns)) * 0.10)

    def xp(value: float) -> float:
        return x0 + value / xmax * plot_w

    def yp(value: float) -> float:
        return y0 + plot_h - (value - ymin) / (ymax - ymin) * plot_h

    svg = [_svg_open("歷史回報／回撤取捨前沿", "每點為一種設定；無提款，使用重疊十年窗口的中位數", width, height)]
    for tick in range(6):
        risk = xmax * tick / 5
        x = xp(risk)
        svg.append(f'<line x1="{x:.2f}" y1="{y0}" x2="{x:.2f}" y2="{y0+plot_h}" stroke="{COLORS["grid"]}"/>')
        svg.append(f'<text x="{x:.2f}" y="{y0+plot_h+23}" text-anchor="middle" font-size="12" fill="{COLORS["muted"]}">{risk*100:.0f}%</text>')
        ret = ymin + (ymax-ymin) * tick / 5
        y = yp(ret)
        svg.append(f'<line x1="{x0}" y1="{y:.2f}" x2="{x0+plot_w}" y2="{y:.2f}" stroke="{COLORS["grid"]}"/>')
        svg.append(f'<text x="{x0-12}" y="{y+4:.2f}" text-anchor="end" font-size="12" fill="{COLORS["muted"]}">{ret*100:.1f}%</text>')
    if frontier:
        path = " ".join(
            ("M" if i == 0 else "L") +
            f' {xp(abs(float(r["median_daily_max_drawdown"]))):.2f} {yp(float(r["median_time_weighted_cagr"])):.2f}'
            for i, r in enumerate(frontier)
        )
        svg.append(f'<path d="{path}" fill="none" stroke="{COLORS["navy"]}" stroke-width="2.8" stroke-dasharray="5 4"/>')

    shapes = {"front_fast":"square","front_loaded":"triangle","linear":"circle","mid_loaded":"diamond","back_loaded":"inverted","back_late":"cross"}
    for r in valid:
        x = xp(abs(float(r["median_daily_max_drawdown"])))
        y = yp(float(r["median_time_weighted_cagr"]))
        color, shape = COLORS[r["bond_proxy"]], shapes[r["timing_rule"]]
        if shape == "circle":
            svg.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4.5" fill="{color}" stroke="#FFFFFF" stroke-width="1" opacity=".86"/>')
        elif shape == "square":
            svg.append(f'<rect x="{x-4:.2f}" y="{y-4:.2f}" width="8" height="8" fill="{color}" stroke="#FFFFFF" stroke-width="1" opacity=".86"/>')
        elif shape == "diamond":
            svg.append(f'<polygon points="{x:.2f},{y-5:.2f} {x-5:.2f},{y:.2f} {x:.2f},{y+5:.2f} {x+5:.2f},{y:.2f}" fill="{color}" stroke="#FFFFFF" stroke-width="1" opacity=".86"/>')
        elif shape == "inverted":
            svg.append(f'<polygon points="{x-4.5:.2f},{y-4:.2f} {x+4.5:.2f},{y-4:.2f} {x:.2f},{y+5:.2f}" fill="{color}" stroke="#FFFFFF" stroke-width="1" opacity=".86"/>')
        elif shape == "cross":
            svg.append(f'<path d="M {x-4:.2f} {y:.2f} H {x+4:.2f} M {x:.2f} {y-4:.2f} V {y+4:.2f}" stroke="{color}" stroke-width="2.5" opacity=".9"/>')
        else:
            svg.append(f'<polygon points="{x:.2f},{y-5:.2f} {x-4.5:.2f},{y+4:.2f} {x+4.5:.2f},{y+4:.2f}" fill="{color}" stroke="#FFFFFF" stroke-width="1" opacity=".86"/>')
    short = {"linear": "線", "front_loaded": "前", "back_loaded": "後"}
    for i, r in enumerate(frontier):
        x = xp(abs(float(r["median_daily_max_drawdown"])))
        y = yp(float(r["median_time_weighted_cagr"]))
        label = f'{r["target_bond_conversion_pct_at_year10"]}% {r["bond_proxy"]} {short[r["timing_rule"]]}'
        right = x > x0 + plot_w * .80
        dx, anchor = (-7, "end") if right else (7, "start")
        dy = -9 if i % 2 == 0 else 14
        label_y = min(y0+plot_h-4, max(y0+13, y+dy))
        svg.append(f'<text x="{x+dx:.2f}" y="{label_y:.2f}" text-anchor="{anchor}" font-size="10.5" font-weight="700" fill="{COLORS["navy"]}">{_esc(label)}</text>')

    svg.append(f'<text x="{x0+plot_w/2:.2f}" y="{y0+plot_h+58}" text-anchor="middle" font-size="13" fill="{COLORS["ink"]}">中位每日最大回撤幅度（越左越小）</text>')
    svg.append(f'<text x="27" y="{y0+plot_h/2:.2f}" transform="rotate(-90 27 {y0+plot_h/2:.2f})" text-anchor="middle" font-size="13" fill="{COLORS["ink"]}">中位年化時間加權回報</text>')
    lx, ly = 975, 145
    svg.append(f'<text x="{lx}" y="{ly}" font-size="15" font-weight="700" fill="{COLORS["navy"]}">顏色：債券代理</text>')
    ly += 29
    for bond in BOND_TICKERS:
        svg.append(f'<circle cx="{lx+6}" cy="{ly-4}" r="5" fill="{COLORS[bond]}"/><text x="{lx+20}" y="{ly}" font-size="13" fill="{COLORS["ink"]}">{bond}</text>')
        ly += 25
    ly += 8
    svg.append(f'<text x="{lx}" y="{ly}" font-size="15" font-weight="700" fill="{COLORS["navy"]}">形狀：轉換時間</text>')
    ly += 28
    for label, shape in (("加速前置","square"),("前置","triangle"),("線性","circle"),("中段S曲線","diamond"),("後置","inverted"),("延後","cross")):
        if shape == "circle":
            marker = f'<circle cx="{lx+6}" cy="{ly-4}" r="4.5" fill="{COLORS["muted"]}"/>'
        elif shape == "square":
            marker = f'<rect x="{lx+2}" y="{ly-8}" width="8" height="8" fill="{COLORS["muted"]}"/>'
        else:
            marker = f'<polygon points="{lx+6},{ly-9} {lx+1},{ly} {lx+11},{ly}" fill="{COLORS["muted"]}"/>'
        svg.append(marker + f'<text x="{lx+20}" y="{ly}" font-size="13" fill="{COLORS["ink"]}">{label}</text>')
        ly += 25
    ly += 14
    svg.append(f'<line x1="{lx}" y1="{ly}" x2="{lx+36}" y2="{ly}" stroke="{COLORS["navy"]}" stroke-width="2.8" stroke-dasharray="5 4"/>')
    svg.append(f'<text x="{lx+45}" y="{ly+4}" font-size="12" fill="{COLORS["ink"]}">非支配前沿</text>')
    svg.append(f'<text x="36" y="{height-26}" font-size="11" fill="{COLORS["muted"]}">前沿只代表本歷史樣本的中位回報／中位回撤取捨；不是未來機率，也不代表本金受保證。</text></svg>')
    return "".join(svg)


def render_summary_html(summary: dict) -> str:
    cards = (
        ("樣本中位年化回報最高", summary["growth_oriented"]),
        ("樣本中位最大回撤較小", summary["lower_median_drawdown"]),
        ("樣本中位期末資產最高", summary["highest_median_terminal_wealth"]),
    )
    out = ["<section id='decision-summary'><h2>先看結論</h2><p>不把不同目標硬合成一個「最佳策略」。分開看增長、較低中位回撤和中位期末資產；候選可能重複。</p><div class='decision-grid'>"]
    for title, row in cards:
        out.append(
            "<article class='decision-card'><h3>" + _esc(title) + "</h3><b>" + _esc(row["scenario_label"]) + "</b><dl>"
            + "<dt>中位第10年資產</dt><dd>" + _money(float(row["median_terminal_nav_usd"])) + "</dd>"
            + "<dt>P05 第10年資產</dt><dd>" + _money(float(row["p05_terminal_nav_usd"])) + "</dd>"
            + "<dt>中位年化回報</dt><dd>" + pct(row["median_time_weighted_cagr"]) + "</dd>"
            + "<dt>中位／最差窗口回撤</dt><dd>" + pct(row["median_daily_max_drawdown"]) + " / " + pct(row["worst_daily_max_drawdown"]) + "</dd></dl></article>"
        )
    out.append("</div><h3>基準掃描：AGG + 線性轉換</h3><div class='table-wrap'><table><thead><tr><th>第10年轉債</th><th>中位終值</th><th>P05終值</th><th>中位年化回報</th><th>中位最大回撤</th><th>低於初始$100,000窗口</th></tr></thead><tbody>")
    for r in summary["agg_linear_target_scan"]:
        out.append(f'<tr><td>{r["target_bond_conversion_pct_at_year10"]}%</td><td>{_money(float(r["median_terminal_nav_usd"]))}</td><td>{_money(float(r["p05_terminal_nav_usd"]))}</td><td>{pct(r["median_time_weighted_cagr"])}</td><td>{pct(r["median_daily_max_drawdown"])}</td><td>{r["windows_below_initial_capital_at_year10"]} / {r["rolling_windows"]}</td></tr>')
    out.append("</tbody></table></div><h3>固定第10年目標60%：AGG轉換時間比較</h3><div class='table-wrap'><table><thead><tr><th>轉換時間</th><th>中位終值</th><th>P05終值</th><th>中位年化回報</th><th>中位／最差窗口回撤</th></tr></thead><tbody>")
    for r in summary["agg_60_timing_comparison"]:
        out.append(f'<tr><td>{_esc(TIMING_LABELS[r["timing_rule"]])}</td><td>{_money(float(r["median_terminal_nav_usd"]))}</td><td>{_money(float(r["p05_terminal_nav_usd"]))}</td><td>{pct(r["median_time_weighted_cagr"])}</td><td>{pct(r["median_daily_max_drawdown"])} / {pct(r["worst_daily_max_drawdown"])}</td></tr>')
    out.append("</tbody></table></div><h3>提款壓力：各情境出現缺口的設定數</h3><div class='table-wrap'><table><thead><tr><th>情境</th><th>有缺口設定</th><th>每設定缺口窗口數範圍</th><th>最大P95缺口</th></tr></thead><tbody>")
    for mode in FLOW_MODES:
        row = summary["withdrawal_stress"].get(mode)
        if row:
            out.append(f'<tr><td>{_esc(row["label"])}</td><td>{row["configurations_with_any_shortfall"]} / {row["configurations"]}</td><td>{row["min_windows_with_shortfall"]}–{row["max_windows_with_shortfall"]} / {summary["rolling_windows"]}</td><td>{_money(float(row["max_p95_shortfall_usd"]))}</td></tr>')
    out.append("</tbody></table></div><p class='note'><b>邊界：</b>窗口彼此重疊，計數不是未來機率。P05 不是保證底線。即使第10年目標為100%債券，也是在第120個月才達成；ETF中途和期末仍可下跌。若需要名義本金下限，須另外核算到期匹配、可成交報價的國債／STRIPS。</p></section>")
    return "".join(out)


def render_summary_markdown(summary: dict) -> str:
    lines = [
        "# 十年股票轉債研究：關鍵結論", "",
        f'- 每個設定使用 **{summary["rolling_windows"]} 個重疊十年窗口**；窗口不是獨立樣本，也不是未來機率。',
        "- 不設隱藏加權分數或單一「最佳策略」；分開看增長、較低回撤和中位期末資產。", "",
        "| 評估目標 | 歷史候選 | 中位終值 | P05終值 | 中位年化回報 | 中位／最差窗口回撤 |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for label, row in (
        ("中位年化回報最高", summary["growth_oriented"]),
        ("中位最大回撤較小", summary["lower_median_drawdown"]),
        ("中位期末資產最高", summary["highest_median_terminal_wealth"]),
    ):
        lines.append(f'| {label} | {row["scenario_label"]} | {_money(float(row["median_terminal_nav_usd"]))} | {_money(float(row["p05_terminal_nav_usd"]))} | {pct(row["median_time_weighted_cagr"])} | {pct(row["median_daily_max_drawdown"])} / {pct(row["worst_daily_max_drawdown"])} |')
    lines.extend(["", "## AGG + 線性轉換（無提款）", "", "| 第10年轉債目標 | 中位終值 | P05終值 | 中位年化回報 | 中位最大回撤 | 期末低於初始$100,000窗口 |", "|---:|---:|---:|---:|---:|---:|"])
    for row in summary["agg_linear_target_scan"]:
        lines.append(f'| {row["target_bond_conversion_pct_at_year10"]}% | {_money(float(row["median_terminal_nav_usd"]))} | {_money(float(row["p05_terminal_nav_usd"]))} | {pct(row["median_time_weighted_cagr"])} | {pct(row["median_daily_max_drawdown"])} | {row["windows_below_initial_capital_at_year10"]} / {row["rolling_windows"]} |')
    lines.extend(["", "## 同一個60%目標：AGG轉換時間比較", "", "| 時間規則 | 中位終值 | P05終值 | 中位年化回報 | 中位／最差窗口回撤 |", "|---|---:|---:|---:|---:|"])
    for row in summary["agg_60_timing_comparison"]:
        lines.append(f'| {TIMING_LABELS[row["timing_rule"]]} | {_money(float(row["median_terminal_nav_usd"]))} | {_money(float(row["p05_terminal_nav_usd"]))} | {pct(row["median_time_weighted_cagr"])} | {pct(row["median_daily_max_drawdown"])} / {pct(row["worst_daily_max_drawdown"])} |')
    lines.extend(["", "## 提款缺口（不是前瞻機率）", "", "| 情境 | 有缺口設定 | 每設定缺口窗口數範圍 | 最大P95缺口 |", "|---|---:|---:|---:|"])
    for mode in FLOW_MODES:
        row = summary["withdrawal_stress"].get(mode)
        if row:
            lines.append(f'| {row["label"]} | {row["configurations_with_any_shortfall"]} / {row["configurations"]} | {row["min_windows_with_shortfall"]}–{row["max_windows_with_shortfall"]} / {summary["rolling_windows"]} | {_money(float(row["max_p95_shortfall_usd"]))} |')
    lines.extend([
        "", f'- 回報／回撤非支配前沿共有 **{len(summary["pareto_frontier"])} 個設定**，代表存在取捨而不是一個通用勝者。',
        "- P05 是歷史樣本第5百分位，不是保證底線；重疊窗口計數不是未來機率。",
        "- 第10年目標100%債券只表示第120個月才達到目標配置，不保證此前不跌，也不等同保本。",
        "", "## 重大限制", "",
        "- 調整收市價近似分配再投資後的總回報；來源可能修訂歷史調整值。逐日價格快照及逐窗口 CSV 與研究 artifact 一併保存。",
        "- 共同樣本始於2003年9月底，未包含2000–2002年科技股崩跌。",
        "- AGG 含機構 MBS 和投資級公司債；SHY／IEF／TLT 是不同久期的國債 ETF，不是個別國債／STRIPS 持有到期回測。",
        "- 稅項、交易成本、買賣差價未另行建模；ETF 不保證名義本金或購買力。",
        "- 若需要第十年名義本金下限，須獨立核算到期匹配、可成交報價的美國國債／STRIPS 本金保護層。", "",
    ])
    return "\n".join(lines)


def enhance_report_dir(outdir: Path) -> dict:
    report_path = outdir / "stock_bond_glidepath_summary.json"
    html_path = outdir / "index.html"
    if not report_path.exists() or not html_path.exists():
        raise FileNotFoundError("Expected stock_bond_glidepath_summary.json and index.html from the backtest")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    summary = build_decision_summary(report["scenarios"])
    report["decision_summary"] = summary
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (outdir / "decision_summary.md").write_text(render_summary_markdown(summary), encoding="utf-8")
    noflow = [row for row in report["scenarios"] if row["cashflow_mode"] == "no_withdrawals"]
    chart = render_frontier(noflow)
    (outdir / "07_risk_return_frontier.svg").write_text(chart, encoding="utf-8")

    page = html_path.read_text(encoding="utf-8")
    if "id='decision-summary'" not in page:
        css = "<style>.decision-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:12px}.decision-card{border:1px solid #d7dee8;border-radius:10px;padding:12px;background:#fbfcfe}.decision-card h3{font-size:16px;margin:0 0 10px}.decision-card dl{display:grid;grid-template-columns:1fr auto;gap:6px 10px;margin:12px 0 0}.decision-card dt{font-size:13px;color:#64748b}.decision-card dd{margin:0;text-align:right;font-weight:650;font-variant-numeric:tabular-nums}.table-wrap{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:13px;font-variant-numeric:tabular-nums}th,td{padding:8px;text-align:right;border-bottom:1px solid #e8edf3;white-space:nowrap}th:first-child,td:first-child{text-align:left}th{background:#f5f7fa;color:#334155}</style>"
        summary_html = render_summary_html(summary)
        if "<p class='note'>" not in page:
            raise ValueError("Dashboard anchor for decision summary changed")
        page = page.replace("<p class='note'>", css + summary_html + "<p class='note'>", 1)
    if "id='risk-return-frontier'" not in page:
        frontier_section = (
            "<section id='risk-return-frontier'><h2>回報與回撤的取捨前沿</h2>"
            "<p>點的顏色代表債券代理、形狀代表轉換時間。前沿上的設定，在中位年化回報與中位最大回撤這兩個指標上沒有同時被其他設定勝過。</p>"
            + chart + "</section>"
        )
        anchor = "<section><h2>第10年終值</h2>"
        if anchor not in page:
            raise ValueError("Dashboard anchor for first chart changed")
        page = page.replace(anchor, frontier_section + anchor, 1)
    page = page.replace("六張 SVG", "七張 SVG")
    html_path.write_text(page, encoding="utf-8")
    return report


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args()
    report = enhance_report_dir(args.outdir)
    print(json.dumps({
        "summary_scenarios": len(report["scenarios"]),
        "no_withdrawal_configurations": report["decision_summary"]["no_withdrawal_configurations"],
        "rolling_windows": report["decision_summary"]["rolling_windows"],
        "pareto_frontier_size": len(report["decision_summary"]["pareto_frontier"]),
        "new_chart": "07_risk_return_frontier.svg",
        "markdown": "decision_summary.md",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
