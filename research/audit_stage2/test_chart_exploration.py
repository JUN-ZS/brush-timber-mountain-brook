import datetime as dt
import unittest

from cashflow_aware_qqq_spy import FlowEvent, MonthlyPrice
from chart_exploration import (
    build_relative_rotation,
    glidepath_data,
    render_cashflow_schedule_svg,
    render_glidepath_svg,
    render_line_chart,
)


def monthly_points(count=48):
    rows = []
    year, month = 2000, 1
    qqq, spy = 100.0, 100.0
    for i in range(count):
        if i:
            qqq *= 1.025 if (i // 6) % 2 == 0 else 0.985
            spy *= 1.012 if (i // 9) % 2 == 0 else 1.005
            month += 1
            if month == 13:
                month, year = 1, year + 1
        rows.append(MonthlyPrice(dt.date(year, month, 28), qqq, spy))
    return rows


class ChartExplorationTests(unittest.TestCase):
    def test_relative_rotation_uses_lookback_and_equal_length_curves(self):
        points = monthly_points(48)
        result = build_relative_rotation(points, lookback_months=12)
        expected = len(points) - 12
        self.assertEqual(len(result["dates"]), expected)
        self.assertEqual(len(result["series"]), 3)
        for row in result["series"]:
            self.assertEqual(len(row["values"]), expected)
            self.assertTrue(all(v > 0 for v in row["values"]))
        self.assertGreaterEqual(result["switch_count"], 0)
        self.assertEqual(set(result["statistics"]), {
            "QQQ buy & hold", "SPY buy & hold", "12m relative-strength rotation"
        })

    def test_glidepath_rules_are_bounded_and_have_expected_endpoints(self):
        rows = glidepath_data((0, 5, 10, 15, 20))
        by_label = {row["label"]: row for row in rows}
        self.assertEqual(by_label["每年轉0個百分點"]["stocks"][10], 100)
        self.assertEqual(by_label["每年轉10個百分點"]["stocks"][5], 50)
        self.assertEqual(by_label["每年轉10個百分點"]["bonds"][10], 100)
        for row in rows:
            self.assertEqual(len(row["stocks"]), 11)
            self.assertEqual(len(row["bonds"]), 11)
            for stock, bond in zip(row["stocks"], row["bonds"]):
                self.assertGreaterEqual(stock, 0)
                self.assertLessEqual(stock, 100)
                self.assertEqual(stock + bond, 100)

    def test_svg_charts_are_documents_with_labels(self):
        points = monthly_points(30)
        rotation = build_relative_rotation(points, 12)
        svg = render_line_chart(
            "Rotation test", "Subtitle", rotation["dates"], rotation["series"],
            "Indexed value", "Source note"
        )
        self.assertTrue(svg.startswith("<svg "))
        self.assertIn("QQQ buy &amp; hold", svg)
        self.assertIn("Source note", svg)
        glidepath = render_glidepath_svg()
        self.assertIn("每年轉10個百分點", glidepath)
        self.assertIn("不是報酬回測", glidepath)

    def test_cashflow_chart_displays_withdrawals_and_reinvestment(self):
        schedule = {
            13: [FlowEvent(13, "withdrawal", 1000.0, "after first year")],
            25: [FlowEvent(25, "deposit", 5000.0, "top-up")],
        }
        svg = render_cashflow_schedule_svg(schedule)
        self.assertIn("提款合計：$1,000", svg)
        self.assertIn("再投入合計：$5,000", svg)
        with self.assertRaises(ValueError):
            render_cashflow_schedule_svg({})


if __name__ == "__main__":
    unittest.main()
