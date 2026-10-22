from __future__ import annotations

import unittest
import json
import tempfile
from pathlib import Path

from .ledger import InstanceLedger
from .run_instance import (
    STATE_SCHEMA,
    instance_summary,
    manual_apply_trade,
    manual_position_snapshot,
    mhash,
    record_manual_trade,
    summarize_strategy_pnl,
)


class SingleStrategyPnlTests(unittest.TestCase):
    def test_same_code_isolated_by_strategy_id(self):
        lots = []
        manual_apply_trade(lots, action="ADD", code="US.QQQ.CALL_A", qty=2, price=5.0,
                           lot_size=100, trade_id="A1", timestamp="2026-10-01T00:00:00Z",
                           strategy_id="STRAT_A")
        manual_apply_trade(lots, action="ADD", code="US.QQQ.CALL_A", qty=3, price=7.0,
                           lot_size=100, trade_id="B1", timestamp="2026-10-01T00:01:00Z",
                           strategy_id="STRAT_B")
        pnl, _ = manual_apply_trade(lots, action="REDUCE", code="US.QQQ.CALL_A", qty=1, price=8.0,
                                    lot_size=100, trade_id="A2", timestamp="2026-10-01T00:02:00Z",
                                    strategy_id="STRAT_A")
        self.assertEqual(pnl, 300.0)
        positions = {p["strategy_id"]: p for p in manual_position_snapshot(lots)}
        self.assertEqual(positions["STRAT_A"]["qty"], 1)
        self.assertEqual(positions["STRAT_B"]["qty"], 3)
        self.assertEqual(positions["STRAT_A"]["avg_cost"], 5.0)
        self.assertEqual(positions["STRAT_B"]["avg_cost"], 7.0)

    def test_cannot_close_another_strategy_lots_by_shared_option_code(self):
        lots = []
        manual_apply_trade(lots, action="ADD", code="US.QQQ.CALL_A", qty=2, price=5.0,
                           lot_size=100, trade_id="B1", timestamp="2026-10-01T00:00:00Z",
                           strategy_id="STRAT_B")
        with self.assertRaisesRegex(SystemExit, "MANUAL_REDUCE_EXCEEDS_POSITION"):
            manual_apply_trade(lots, action="REDUCE", code="US.QQQ.CALL_A", qty=1, price=8.0,
                               lot_size=100, trade_id="A1", timestamp="2026-10-01T00:01:00Z",
                               strategy_id="STRAT_A")

    def test_missing_mark_is_pending_not_zero(self):
        lots = [
            {"lot_id":"A1", "strategy_id":"STRAT_A", "code":"US.QQQ.CALL_A", "side":"LONG",
             "qty":1, "avg_price":5.0, "lot_size":100, "status":"OPEN"},
            {"lot_id":"B1", "strategy_id":"STRAT_B", "code":"US.QQQ.PUT_B", "side":"SHORT",
             "qty":1, "avg_price":2.0, "lot_size":100, "status":"OPEN"},
        ]
        mark = {"status":"PARTIAL", "unrealized_pnl":50.0, "rows":[
            {"lot_id":"A1", "strategy_id":"STRAT_A", "status":"MARKED", "unrealized_pnl":50.0},
            {"lot_id":"B1", "strategy_id":"STRAT_B", "status":"NO_MARK"},
        ]}
        out = summarize_strategy_pnl(lots, mark, [
            {"strategy_id":"STRAT_A","realized_pnl_delta":150.0},
            {"strategy_id":"STRAT_B","realized_pnl_delta":-25.0},
        ], expected_realized_pnl=125.0)
        self.assertEqual(out["by_strategy"]["STRAT_A"]["total_pnl"], 200.0)
        self.assertIsNone(out["by_strategy"]["STRAT_B"]["unrealized_pnl"])
        self.assertEqual(out["by_strategy"]["STRAT_B"]["mark_status"], "PENDING")
        self.assertEqual(out["reconciliation"]["status"], "PENDING_MARKS")
        self.assertIsNone(out["reconciliation"]["total_delta"])

    def test_total_strategy_pnl_reconciles_to_manual_book_when_all_marks_exist(self):
        lots = [
            {"lot_id":"A1", "strategy_id":"STRAT_A", "code":"US.QQQ.CALL_A", "side":"LONG",
             "qty":1, "avg_price":5.0, "lot_size":100, "status":"OPEN"},
            {"lot_id":"B1", "strategy_id":"STRAT_B", "code":"US.QQQ.PUT_B", "side":"SHORT",
             "qty":2, "avg_price":3.0, "lot_size":100, "status":"OPEN"},
        ]
        mark = {"status":"OK", "unrealized_pnl":30.0, "rows":[
            {"lot_id":"A1", "strategy_id":"STRAT_A", "status":"MARKED", "unrealized_pnl":50.0},
            {"lot_id":"B1", "strategy_id":"STRAT_B", "status":"MARKED", "unrealized_pnl":-20.0},
        ]}
        trades = [
            {"strategy_id":"STRAT_A","realized_pnl_delta":200.0},
            {"strategy_id":"STRAT_B","realized_pnl_delta":-50.0},
        ]
        out = summarize_strategy_pnl(lots, mark, trades, expected_realized_pnl=150.0)
        self.assertEqual(out["reconciliation"]["status"], "RECONCILED")
        self.assertAlmostEqual(out["reconciliation"]["realized_delta"], 0.0)
        self.assertAlmostEqual(out["reconciliation"]["unrealized_delta"], 0.0)
        self.assertAlmostEqual(out["reconciliation"]["total_delta"], 0.0)
        self.assertEqual(sum(x["total_pnl"] for x in out["by_strategy"].values()), 180.0)

    def test_ledger_realized_mismatch_is_not_passed(self):
        out = summarize_strategy_pnl([], {"status":"EMPTY", "rows":[]}, [
            {"strategy_id":"STRAT_A","realized_pnl_delta":100.0}
        ], expected_realized_pnl=99.0)
        self.assertEqual(out["reconciliation"]["status"], "CHECK_REQUIRED")
        self.assertAlmostEqual(out["reconciliation"]["realized_delta"], 1.0)




    def test_real_manual_ledger_keeps_same_contract_strategies_separate(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            instance_id = "TEST_SINGLE_STRATEGY"
            folder = repo / "research" / "strategy_instance_v1" / "instances" / instance_id
            folder.mkdir(parents=True)
            manifest = {
                "schema": "STRATEGY_INSTANCE_MANIFEST.v1",
                "schema_version": 1,
                "instance_id": instance_id,
                "created_at_utc": "2026-10-01T00:00:00+00:00",
                "start_at_utc": "2026-10-01T00:00:00+00:00",
                "strategy_id": "DEFAULT_STRATEGY",
                "strategy_version": "TEST",
                "research_engine_commit": None,
                "strategy_lock_hash": None,
                "far_dte": 120,
                "far_delta": 0.08,
                "near_dte": 30,
                "coverage_mult": 1.5,
                "initial_cash": 100000.0,
                "far_code_hint": None,
                "initial_positions": [],
                "notes": "isolated fixture",
                "mutation_rule": "immutable test T0",
            }
            manifest["manifest_hash"] = mhash(manifest)
            (folder / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            state = {
                "schema": STATE_SCHEMA, "schema_version": 1, "instance_id": instance_id,
                "processed_deal_ids": [], "lots": [], "realized_pnl": 0.0,
                "last_cycle_at": None, "last_history_backfill_at": None,
                "last_snapshot_hash": None, "last_reconcile": None,
                "cycle_count": 0, "data_gaps": 0, "manual_lots": [],
                "manual_realized_pnl": 0.0, "manual_trade_count": 0, "manual_last_mark": None,
            }
            (folder / "state.json").write_text(json.dumps(state), encoding="utf-8")
            ledger = InstanceLedger(
                folder / "ledger.jsonl",
                {
                    "instance_id": instance_id,
                    "manifest_hash": manifest["manifest_hash"],
                    "strategy_id": manifest["strategy_id"],
                    "strategy_version": manifest["strategy_version"],
                    "research_engine_commit": None,
                },
            )
            ledger.append(
                "INSTANCE_CREATED", instance_id=instance_id, cycle_id="INIT",
                timestamp_utc="2026-10-01T00:00:00+00:00", payload={"fixture": True},
                source="USER_INITIAL",
            )

            common = {
                "repo": repo, "instance_id": instance_id, "action": "ADD",
                "code": "US.QQQ.SAME_CONTRACT", "qty": 2, "lot_size": 100,
                "timestamp_utc": "2026-10-01T00:01:00+00:00",
            }
            record_manual_trade(
                common["repo"], instance_id=common["instance_id"], action="ADD",
                code=common["code"], qty=2, price=5.0, lot_size=100,
                timestamp_utc="2026-10-01T00:01:00+00:00", trade_id="OPEN_A",
                strategy_id="STRAT_A",
            )
            record_manual_trade(
                common["repo"], instance_id=common["instance_id"], action="ADD",
                code=common["code"], qty=2, price=7.0, lot_size=100,
                timestamp_utc="2026-10-01T00:02:00+00:00", trade_id="OPEN_B",
                strategy_id="STRAT_B",
            )
            record_manual_trade(
                common["repo"], instance_id=common["instance_id"], action="REDUCE",
                code=common["code"], qty=1, price=8.0, lot_size=100,
                timestamp_utc="2026-10-01T00:03:00+00:00", trade_id="CLOSE_A",
                strategy_id="STRAT_A",
            )

            report = instance_summary(repo, instance_id)
            pnl = report["strategy_pnl"]["by_strategy"]
            positions = {x["strategy_id"]: x for x in report["manual_book"]["positions"]}
            self.assertEqual(pnl["STRAT_A"]["realized_pnl"], 300.0)
            self.assertEqual(pnl["STRAT_B"]["realized_pnl"], 0.0)
            self.assertEqual(positions["STRAT_A"]["qty"], 1)
            self.assertEqual(positions["STRAT_B"]["qty"], 2)
            self.assertEqual(positions["STRAT_A"]["avg_cost"], 5.0)
            self.assertEqual(positions["STRAT_B"]["avg_cost"], 7.0)
            self.assertEqual(report["strategy_pnl"]["reconciliation"]["status"], "PENDING_MARKS")

            with self.assertRaisesRegex(SystemExit, "MANUAL_REDUCE_EXCEEDS_POSITION"):
                record_manual_trade(
                    repo, instance_id=instance_id, action="REDUCE",
                    code="US.QQQ.SAME_CONTRACT", qty=2, price=9.0, lot_size=100,
                    timestamp_utc="2026-10-01T00:04:00+00:00", trade_id="BAD_CLOSE_A",
                    strategy_id="STRAT_A",
                )
            report_after = instance_summary(repo, instance_id)
            positions_after = {x["strategy_id"]: x for x in report_after["manual_book"]["positions"]}
            self.assertEqual(positions_after["STRAT_A"]["qty"], 1)
            self.assertEqual(positions_after["STRAT_B"]["qty"], 2)


if __name__ == "__main__":
    unittest.main()
