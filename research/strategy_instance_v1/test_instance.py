import json
import unittest
import tempfile, threading, time
from pathlib import Path
from datetime import datetime, timezone
from .ledger import InstanceLedger, InstanceLedgerError, sha256_json
from .run_instance import (
    apply_deal,
    load_instance,
    manual_apply_trade,
    manual_position_snapshot,
    manual_book_pnl_preview,
    save,
    init_lots,
)
from .run_instance import instance_mutation_lock, mhash, mpath, spath, lpath
from .performance_tape import build_performance_tape, classify_relationship

def test_operator_ticket_context_is_verified_from_evidence():
    import json
    from .serve_operator import explicit_strategy_context
    from ..evidence_v1.ledger import EvidenceLedger
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        ticket={
            "ticket_id":"TICKET-1","action":"ADD_NEAR","status":"OPEN",
            "legs":[{
                "code":"US.QQQ.TEST","side":"BUY","qty":2,
                "strategy_leg_action":"ADD_NEAR","before_qty":0,"target_qty":2,
                "price":8.5,
            }],
        }
        ledger=EvidenceLedger(root/"research/evidence_v1/evidence.jsonl",{})
        ledger.append("CYCLE_STARTED",instance_id="I",cycle_id="C1",
                      timestamp_utc="2026-10-01T00:00:00+00:00",payload={})
        decision=ledger.append(
            "DECISION_EMITTED",instance_id="I",cycle_id="C1",
            timestamp_utc="2026-10-01T00:00:05+00:00",
            payload={"ticket":ticket,"snapshot_sha256":"SNAP-1"},
        )
        body={"instance_id":"I","strategy_context_snapshot":{
            "instance_id":"I",
            "ticket_id":"TICKET-1",
            "context_source":"OPERATOR_SELECTED_GLOBAL_TICKET_FOR_INSTANCE",
            "action":"ADD_NEAR","status":"OPEN",
            "leg":dict(ticket["legs"][0]),
        }}
        ctx=explicit_strategy_context(root,body)
        assert ctx["source_evidence_id"]==decision["evidence_id"]
        assert ctx["pre_decision_snapshot_sha256"]=="SNAP-1"
        assert ctx["ticket_snapshot"]==ticket
        assert ctx["ticket_snapshot_sha256"]==sha256_json(ticket)


def test_operator_ticket_context_rejects_browser_tampering():
    import tempfile
    from .serve_operator import explicit_strategy_context
    from ..evidence_v1.ledger import EvidenceLedger
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        ticket={"ticket_id":"TICKET-2","action":"ADD_NEAR","status":"OPEN",
                "legs":[{"code":"US.QQQ.TEST","side":"BUY","qty":2,
                         "strategy_leg_action":"ADD_NEAR"}]}
        ledger=EvidenceLedger(root/"research/evidence_v1/evidence.jsonl",{})
        ledger.append("DECISION_EMITTED",instance_id="I",cycle_id="C1",
                      timestamp_utc="2026-10-01T00:00:00+00:00",
                      payload={"ticket":ticket})
        body={"instance_id":"I","strategy_context_snapshot":{
            "instance_id":"I","ticket_id":"TICKET-2",
            "context_source":"OPERATOR_SELECTED_GLOBAL_TICKET_FOR_INSTANCE",
            "action":"ADD_NEAR","status":"OPEN",
            "leg":{"code":"US.QQQ.TEST","side":"BUY","qty":99,
                   "strategy_leg_action":"ADD_NEAR"},
        }}
        try:
            explicit_strategy_context(root,body)
        except ValueError as exc:
            assert str(exc)=="STRATEGY_CONTEXT_TICKET_TAMPERED"
        else:
            raise AssertionError("browser-supplied ticket mutation must be rejected")


def test_pending_strategy_executions_is_read_only_and_deals_are_explicit():
    from .run_instance import pending_strategy_executions, save
    with tempfile.TemporaryDirectory() as td:
        repo=Path(td); iid="I-PENDING"
        manifest={"schema":"STRATEGY_INSTANCE_MANIFEST.v1","schema_version":1,
                  "instance_id":iid,"created_at_utc":"2026-10-01T00:00:00+00:00",
                  "start_at_utc":"2026-10-01T00:00:00+00:00","strategy_id":"TEST",
                  "strategy_version":"V1","initial_positions":[]}
        manifest["manifest_hash"]=mhash(manifest); save(mpath(repo,iid),manifest)
        l=InstanceLedger(lpath(repo,iid),{"instance_id":iid,
            "manifest_hash":manifest["manifest_hash"],"strategy_id":"TEST","strategy_version":"V1"})
        deal={"deal_id":"D-P","code":"US.QQQ.TEST","side":"BUY","qty":3,
              "price":5.0,"created_at":"2026-10-01T00:01:00+00:00"}
        l.append("BROKER_EXECUTION_UNATTRIBUTED",instance_id=iid,cycle_id="C1",
                 timestamp_utc="2026-10-01T00:01:01+00:00",
                 payload={"deal":deal,"attribution":None},source="BROKER_OBSERVED")
        out=pending_strategy_executions(repo,iid)
        assert out["count"]==1
        row=out["pending"][0]
        assert row["deal_id"]=="D-P"
        assert row["remaining_qty"]==3
        assert out["attribution_policy"]=="EXPLICIT_USER_CONFIRMATION_ONLY"

def test_operator_mutation_endpoint_requires_header():
    from .serve_operator import MUTATION_HEADER, MUTATION_HEADER_VALUE, MUTATING_PATHS
    assert "/api/manual" in MUTATING_PATHS
    assert "/api/refresh" in MUTATING_PATHS
    assert MUTATION_HEADER == "X-QQQ-Operator"
    assert MUTATION_HEADER_VALUE == "1"


def test_operator_ticket_context_rejects_structural_leg_tampering():
    import tempfile
    from .serve_operator import explicit_strategy_context
    from ..evidence_v1.ledger import EvidenceLedger
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        ticket={"ticket_id":"T-STRUCT","action":"ADD_NEAR","status":"OPEN",
                "legs":[{"code":"US.QQQ.TEST","qty":2,"side":"BUY",
                         "strategy_leg_action":"ADD_NEAR",
                         "before_qty":1,"target_qty":3,"price":8.5}]}
        ledger=EvidenceLedger(root/"research/evidence_v1/evidence.jsonl",{})
        ledger.append("DECISION_EMITTED",instance_id="I",cycle_id="C1",
                      timestamp_utc="2026-10-01T00:00:00+00:00",
                      payload={"ticket":ticket})
        forged=json.loads(json.dumps(ticket["legs"][0]))
        forged["before_qty"]=0
        try:
            explicit_strategy_context(root,{"instance_id":"I",
                "strategy_context_snapshot":{
                    "instance_id":"I","ticket_id":"T-STRUCT",
                    "context_source":"OPERATOR_SELECTED_GLOBAL_TICKET_FOR_INSTANCE",
                    "action":"ADD_NEAR","status":"OPEN","leg":forged}})
        except ValueError as exc:
            assert str(exc)=="STRATEGY_CONTEXT_TICKET_TAMPERED"
        else:
            raise AssertionError("structural ticket mutation must be rejected")

def test_operator_strategy_context_must_be_instance_scoped():
    import tempfile
    from .serve_operator import explicit_strategy_context
    from ..evidence_v1.ledger import EvidenceLedger
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        ticket={"ticket_id":"T1","action":"ADD_NEAR","status":"OPEN",
                "legs":[{"code":"US.QQQ.TEST","qty":1,"side":"BUY",
                         "strategy_leg_action":"ADD_NEAR"}]}
        ledger=EvidenceLedger(root/"research/evidence_v1/evidence.jsonl",{})
        ledger.append("DECISION_EMITTED",instance_id="I2",cycle_id="C1",
                      timestamp_utc="2026-10-01T00:00:00+00:00",
                      payload={"ticket":ticket,"snapshot_sha256":"S1"})
        raw={"instance_id":"I1","ticket_id":"T1",
             "context_source":"OPERATOR_SELECTED_GLOBAL_TICKET_FOR_INSTANCE",
             "action":"ADD_NEAR","status":"OPEN",
             "leg":dict(ticket["legs"][0])}
        try:
            explicit_strategy_context(root,{"instance_id":"I2",
                "strategy_context_snapshot":raw})
        except ValueError as exc:
            assert str(exc)=="STRATEGY_CONTEXT_INSTANCE_MISMATCH"
        else:
            raise AssertionError("context from another instance must be rejected")

def test_runtime_lock_rejects_tampered_strategy_identity():
    from . import run_instance
    from ..evidence_v1 import lock_guard
    old=lock_guard.load_lock
    lock_guard.load_lock=lambda _repo: {
        "strategy_id":"TAMPERED",
        "strategy_version":"V22-family-30D-1.5x",
        "selection_cutoff":"2025-12-15",
        "selection_status":"LOCKED_FROM_PRIOR_FULL_SAMPLE_V22_AUDIT",
        "research_engine_commit":"930c949ec5260865f2bf3ee1c6e030dab7b8e4c4",
        "candidate_family":{"near_dte":30,"coverage":1.5,"far_dte":[90,120,180],"far_abs_delta":[0.05,0.08,0.10],"long_delta":0.50,
                           "policies":sorted(lock_guard.LOCKED_POLICIES)},
        "signal":{"ratio52_gte":0.98,"ext200_gte":0.08},
    }
    try:
        try:
            lock_guard.assert_runtime_lock(Path("."),far_dte=120,far_delta=0.08,near_dte=30)
        except lock_guard.StrategyLockViolation as exc:
            assert str(exc)=="LOCK_VIOLATION:STRATEGY_ID"
        else:
            raise AssertionError("tampered strategy identity accepted")
    finally:
        lock_guard.load_lock=old


def test_instance_init_does_not_silence_corrupt_runtime_identity():
    from . import run_instance
    with tempfile.TemporaryDirectory() as td:
        repo=Path(td)
        old=run_instance.runtime_identity
        run_instance.runtime_identity=lambda _repo: (_ for _ in ()).throw(ValueError("bad lock"))
        try:
            class A:
                repo_root=repo; strategy_id=None; strategy_version=None
                research_engine_commit=None; strategy_lock_hash=None
                start_at_utc=None; instance_id="I"; position=[]; note=""; initial_cash=None
                far_code=None
            try:
                run_instance._init_cmd_unlocked(A())
            except SystemExit as exc:
                assert str(exc)=="INSTANCE_RUNTIME_IDENTITY_INVALID:ValueError"
            else:
                raise AssertionError("corrupt runtime identity was silently accepted")
        finally:
            run_instance.runtime_identity=old


def test_instance_init_rejects_lineage_override_against_locked_runtime():
    import tempfile
    from pathlib import Path
    from . import run_instance
    with tempfile.TemporaryDirectory() as td:
        repo=Path(td)
        old=run_instance.runtime_identity
        run_instance.runtime_identity=lambda _repo: {
            "strategy_id":"LOCKED","strategy_version":"V1",
            "research_engine_commit":"ENG1","strategy_lock_hash":"HASH1",
        }
        try:
            class A:
                strategy_id="OTHER"; strategy_version=None; research_engine_commit=None
                strategy_lock_hash=None; start_at_utc=None; instance_id="I"; repo_root=repo
                position=[]; note=""; initial_cash=None
                far_code=None
            try:
                run_instance._init_cmd_unlocked(A())
            except SystemExit as exc:
                assert str(exc)=="INSTANCE_LINEAGE_MISMATCH:strategy_id"
            else:
                raise AssertionError("lineage override was accepted")
        finally:
            run_instance.runtime_identity=old


def test_pnl_observation_status_requires_position_reconciliation():
    from .run_instance import derive_pnl_observation_status
    assert derive_pnl_observation_status([], "OK") == "OBSERVED_MATCHED"
    assert derive_pnl_observation_status([], "EMPTY") == "OBSERVED_MATCHED_CLOSED"
    assert derive_pnl_observation_status([{"code":"US.QQQ.TEST","side":"LONG","lot_qty":1,"broker_qty":0}], "OK") == "DATA_GAP"
    assert derive_pnl_observation_status([], "PARTIAL") == "DATA_GAP"


def test_instance_input_rejects_non_qqq_option_codes():
    from .run_instance import pos_spec
    try:
        pos_spec("US.QQQ,LONG,1,5.0")
    except SystemExit as exc:
        assert str(exc)=="POSITION_CODE_MUST_BE_QQQ_OPTION"
    else:
        raise AssertionError("QQQ underlying must not enter option instance")
    try:
        pos_spec("US.QCOM261030C00500000,LONG,1,5.0")
    except SystemExit as exc:
        assert str(exc)=="POSITION_CODE_MUST_BE_QQQ_OPTION"
    else:
        raise AssertionError("non-QQQ option must not enter instance")


def test_unverified_strategy_pnl_is_not_presented_as_observed():
    from .run_instance import derive_pnl_observation_status
    assert derive_pnl_observation_status(
        [{"code":"US.QQQ.TEST","side":"LONG","lot_qty":1,"broker_qty":0}],
        "OK",
    ) == "DATA_GAP"
    assert derive_pnl_observation_status([], "OK") == "OBSERVED_MATCHED"
    assert derive_pnl_observation_status([], "EMPTY") == "OBSERVED_MATCHED_CLOSED"


def test_instance_strategy_lineage_rejects_engine_or_lock_drift():
    import tempfile
    import research.strategy_instance_v1.run_instance as ri
    from .run_instance import assert_instance_strategy_lineage

    manifest={"strategy_id":"S1","strategy_version":"V1",
              "research_engine_commit":"ENG1","strategy_lock_hash":"LOCK1"}
    with tempfile.TemporaryDirectory() as td:
        original=ri.runtime_identity
        try:
            ri.runtime_identity=lambda repo: {
                "strategy_id":"S1","strategy_version":"V1",
                "research_engine_commit":"ENG2","strategy_lock_hash":"LOCK1",
            }
            try:
                assert_instance_strategy_lineage(Path(td),manifest)
            except SystemExit as exc:
                assert "research_engine_commit" in str(exc)
            else:
                raise AssertionError("engine lineage drift must block the cycle")
        finally:
            ri.runtime_identity=original


def test_unmanaged_broker_qqq_short_is_reconciliation_gap():
    from .run_instance import reconcile
    lots=[{"lot_id":"T0","code":"US.QQQ261230C00600000","side":"LONG","qty":1,"avg_price":5.0,"status":"OPEN","lot_size":100}]
    positions=[
        {"code":"US.QQQ261230C00600000","side":"LONG","qty":1,"avg_cost":5.0},
        {"code":"US.QQQ261230C00610000","side":"SHORT","qty":3,"avg_cost":1.0},
    ]
    gaps=reconcile(lots,positions)
    assert any(
        x["reason"]=="UNMANAGED_QQQ_SHORT"
        and x["code"]=="US.QQQ261230C00610000"
        and x["broker_qty"]==3
        for x in gaps
    )


def test_unrelated_broker_qqq_execution_is_not_strategy_attributed():
    from .run_instance import attribute_broker_deal, managed_position_view, reconcile

    deal = {
        "deal_id":"UNRELATED-1",
        "code":"US.QQQ261230C00600000",
        "side":"BUY",
        "qty":5,
        "price":2.0,
        "created_at":"2026-10-01T21:01:00+00:00",
    }
    assert attribute_broker_deal([], deal)["status"] == "UNATTRIBUTED"

    lots=[{"lot_id":"T0","code":"US.QQQ261030C00500000","side":"LONG","qty":1,"avg_price":5.0,"status":"OPEN","lot_size":100}]
    positions=[
        {"code":"US.QQQ261030C00500000","side":"LONG","qty":1,"avg_cost":5.0},
        {"code":"US.QQQ261230C00600000","side":"LONG","qty":5,"avg_cost":2.0},
    ]
    assert reconcile(lots, positions) == []
    owned=managed_position_view(positions,lots)
    assert [(x["code"],x["qty"]) for x in owned] == [("US.QQQ261030C00500000",1)]


def test_strategy_mark_uses_owned_lot_cost_not_account_aggregate_cost():
    from .run_instance import mark_lots

    lots=[{
        "lot_id":"T0","code":"US.QQQ.TEST","side":"LONG",
        "qty":1,"avg_price":5.0,"lot_size":100,"status":"OPEN",
    }]
    cmap={"US.QQQ.TEST": type("C",(),{"lot_size":100})()}
    quotes={"US.QQQ.TEST":{"mid":6.0,"bid":5.9,"ask":6.1}}
    marked=mark_lots(lots,cmap,quotes)
    assert marked["unrealized_pnl"]==100.0


def test_strategy_attributed_buy_can_close_short_without_creating_long():
    from .run_instance import apply_strategy_attributed_deal

    lots=[{"lot_id":"T0","code":"US.QQQ.TEST","side":"SHORT","qty":2,"avg_price":7.0,"lot_size":100,"status":"OPEN"}]
    match={
        "action":"CLOSE_CAMPAIGN_EMERGENCY",
        "candidate":{"code":"US.QQQ.TEST","side":"BUY","qty":1},
    }
    deal={"deal_id":"D-COVER","code":"US.QQQ.TEST","side":"BUY","qty":1,"price":4.0,"lot_size":100}
    consumed,pnl,application=apply_strategy_attributed_deal(lots,deal,match)
    assert consumed==1
    assert pnl==300.0
    assert application=="CLOSE_SHORT"
    assert sum(x["qty"] for x in lots if x["side"]=="SHORT" and x["status"]=="OPEN")==1
    assert not any(x["side"]=="LONG" and x["status"]=="OPEN" for x in lots)


def test_legacy_execution_without_attribution_is_not_replayed_into_strategy_book():
    with tempfile.TemporaryDirectory() as td:
        repo=Path(td)
        instance_id="I-LEGACY"
        manifest={
            "schema":"STRATEGY_INSTANCE_MANIFEST.v1","schema_version":1,
            "instance_id":instance_id,
            "created_at_utc":"2026-10-01T00:00:00+00:00",
            "start_at_utc":"2026-10-01T00:00:00+00:00",
            "strategy_id":"TEST","strategy_version":"V1",
            "initial_positions":[],
        }
        manifest["manifest_hash"]=mhash(manifest)
        save(mpath(repo,instance_id),manifest)
        stale={
            "schema":"STRATEGY_INSTANCE_STATE.v1","schema_version":1,
            "instance_id":instance_id,"processed_deal_ids":[],
            "lots":[],"realized_pnl":0.0,"last_cycle_at":None,
            "last_history_backfill_at":None,"last_snapshot_hash":None,
            "last_reconcile":None,"cycle_count":0,"data_gaps":0,
            "manual_lots":[],"manual_realized_pnl":0.0,
            "manual_trade_count":0,"manual_last_mark":None,
        }
        save(spath(repo,instance_id),stale)
        ledger=InstanceLedger(
            repo/"research/strategy_instance_v1/instances"/instance_id/"ledger.jsonl",
            {"instance_id":instance_id,"manifest_hash":manifest["manifest_hash"],
             "strategy_id":"TEST","strategy_version":"V1"},
        )
        ledger.append(
            "EXECUTION_DETECTED",instance_id=instance_id,cycle_id="C1",
            timestamp_utc="2026-10-01T00:01:00+00:00",
            payload={"deal":{
                "deal_id":"OLD","code":"US.QQQ.TEST","side":"BUY",
                "qty":1,"price":2.0,"lot_size":100,
                "created_at":"2026-10-01T00:01:00+00:00",
            }},
        )
        _,state,_=load_instance(repo,instance_id)
        assert state["realized_pnl"]==0.0
        assert state["lots"]==[]
        assert state["unattributed_deal_ids"]==["OLD"]
        assert state["strategy_deal_ids"]==[]


def test_strategy_attribution_never_promotes_plan_timing_to_execution():
    from .run_instance import attribute_broker_deal
    rows=[{
        "event_seq":1,
        "event_type":"STRATEGY_PLAN_OBSERVED",
        "timestamp_utc":"2026-10-01T21:00:00+00:00",
        "payload":{"plan":{"primary_candidate":{
            "action":"ADD_NEAR","code":"US.QQQ.TEST","qty":2
        }}},
    }]
    deal={"deal_id":"D-TIMING","code":"US.QQQ.TEST","side":"BUY","qty":2,
          "price":5.0,"created_at":"2026-10-01T21:01:00+00:00"}
    out=attribute_broker_deal(rows,deal,{})
    assert out["status"]=="POTENTIAL_PREDECISION_MATCH"
    assert out["basis"]=="recent_strategy_plan_observation_without_intent_proof"

def test_strategy_plan_attribution_is_bounded_and_cannot_reuse_quantity():
    from .run_instance import attribute_broker_deal

    rows=[{
        "event_seq":7,
        "event_type":"STRATEGY_PLAN_OBSERVED",
        "timestamp_utc":"2026-10-01T21:00:00+00:00",
        "payload":{"plan":{
            "candidate_actions":[{
                "action":"ADD_NEAR",
                "code":"US.QQQ261030C00500000",
                "qty":2,
            }],
            "primary_candidate":{
                "action":"ADD_NEAR",
                "code":"US.QQQ261030C00500000",
                "qty":2,
            },
        }},
    }]
    used={}
    d={"deal_id":"D1","code":"US.QQQ261030C00500000","side":"BUY","qty":3,"price":8.0,"created_at":"2026-10-01T21:01:00+00:00"}
    first=attribute_broker_deal(rows,d,used)
    assert first["status"]=="POTENTIAL_PREDECISION_MATCH"
    assert first["qty"]==2
    used[first["plan_key"]]=first["qty"]
    second=attribute_broker_deal(rows,d,used)
    assert second["status"]=="UNATTRIBUTED"
    assert second["reason"]=="strategy_plan_quantity_already_consumed"


def test_confirm_rejects_already_detected_execution():
    import tempfile
    from .run_instance import confirm_strategy_execution, save
    with tempfile.TemporaryDirectory() as td:
        repo=Path(td); iid="I-CONF-BLOCK"
        manifest={"schema":"STRATEGY_INSTANCE_MANIFEST.v1","schema_version":1,
                  "instance_id":iid,"created_at_utc":"2026-10-01T00:00:00+00:00",
                  "start_at_utc":"2026-10-01T00:00:00+00:00","strategy_id":"TEST",
                  "strategy_version":"V1","initial_positions":[]}
        manifest["manifest_hash"]=mhash(manifest); save(mpath(repo,iid),manifest)
        save(spath(repo,iid),{"schema":"STRATEGY_INSTANCE_STATE.v1","schema_version":1,
            "instance_id":iid,"processed_deal_ids":[],"strategy_deal_ids":[],"unattributed_deal_ids":[],
            "lots":[],"realized_pnl":0.0,"last_cycle_at":None,"last_history_backfill_at":None,
            "last_snapshot_hash":None,"last_reconcile":None,"cycle_count":1,"data_gaps":0,
            "gamma_history":[],"gamma_history_schema":2,"gamma_history_unit":"gamma_spot","far_delta_abs":None,
            "manual_lots":[],"manual_realized_pnl":0.0,"manual_trade_count":0,"manual_last_mark":None})
        l=InstanceLedger(lpath(repo,iid),{"instance_id":iid,"manifest_hash":manifest["manifest_hash"],
            "strategy_id":"TEST","strategy_version":"V1"})
        l.append("EXECUTION_DETECTED",instance_id=iid,cycle_id="C1",
                 timestamp_utc="2026-10-01T00:01:00+00:00",
                 payload={"deal":{"deal_id":"D-EX","code":"US.QQQ.TEST","side":"BUY",
                                  "qty":1,"price":5.0,"lot_size":100,
                                  "created_at":"2026-10-01T00:01:00+00:00"}})
        try:
            confirm_strategy_execution(repo,instance_id=iid,deal_id="D-EX",
                                       expected_strategy_side="LONG",qty=1)
        except SystemExit as exc:
            assert str(exc)=="STRATEGY_DEAL_ALREADY_FULLY_CONFIRMED:D-EX"
        else:
            raise AssertionError("already attributed execution was confirmable")


def test_confirmation_persists_source_plan_lineage_without_inference():
    import tempfile
    from .run_instance import confirm_strategy_execution, save
    with tempfile.TemporaryDirectory() as td:
        repo=Path(td); iid="I-LINEAGE"
        manifest={"schema":"STRATEGY_INSTANCE_MANIFEST.v1","schema_version":1,
                  "instance_id":iid,"created_at_utc":"2026-10-01T00:00:00+00:00",
                  "start_at_utc":"2026-10-01T00:00:00+00:00","strategy_id":"TEST",
                  "strategy_version":"V1","initial_positions":[]}
        manifest["manifest_hash"]=mhash(manifest); save(mpath(repo,iid),manifest)
        save(spath(repo,iid),{"schema":"STRATEGY_INSTANCE_STATE.v1","schema_version":1,
            "instance_id":iid,"processed_deal_ids":["D-L"],"strategy_deal_ids":[],
            "unattributed_deal_ids":["D-L"],"lots":[],"realized_pnl":0.0,
            "last_cycle_at":None,"last_history_backfill_at":None,
            "last_snapshot_hash":None,"last_reconcile":None,"cycle_count":1,"data_gaps":1,
            "gamma_history":[],"gamma_history_schema":2,"gamma_history_unit":"gamma_spot",
            "far_delta_abs":None,"manual_lots":[],"manual_realized_pnl":0.0,
            "manual_trade_count":0,"manual_last_mark":None})
        l=InstanceLedger(lpath(repo,iid),{"instance_id":iid,
            "manifest_hash":manifest["manifest_hash"],"strategy_id":"TEST","strategy_version":"V1"})
        primary={"action":"ADD_NEAR","code":"US.QQQ.TEST","qty":1,
                 "side":"BUY","strategy_leg_action":"ADD_NEAR"}
        l.append("STRATEGY_PLAN_OBSERVED",instance_id=iid,cycle_id="C1",
                 timestamp_utc="2026-10-01T00:01:00+00:00",
                 payload={"plan":{"primary_candidate":primary},
                          "primary_candidate":primary,"strategy_observation_accepted":True},
                 source="SYSTEM")
        deal={"deal_id":"D-L","code":"US.QQQ.TEST","side":"BUY","qty":1,
              "price":5.0,"lot_size":100,"created_at":"2026-10-01T00:02:00+00:00"}
        l.append("BROKER_EXECUTION_UNATTRIBUTED",instance_id=iid,cycle_id="C2",
                 timestamp_utc="2026-10-01T00:02:01+00:00",
                 payload={"deal":deal,"attribution":{
                     "status":"POTENTIAL_PREDECISION_MATCH",
                     "qty":1,
                     "match":{"event_seq":1,"event_id":"E1","candidate_sha256":"x"*64}
                 }},source="BROKER_OBSERVED")
        out=confirm_strategy_execution(repo,instance_id=iid,deal_id="D-L",
                expected_strategy_side="LONG",qty=1,note="explicit")
        assert out["confirmed_qty"]==1
        _,_,ledger=load_instance(repo,iid)
        row=[r for r in ledger.rows() if r["event_type"]=="STRATEGY_EXECUTION_CONFIRMED"][0]
        src=row["payload"]["source_strategy_observation"]
        assert src["event_seq"]==1
        assert len(src["candidate_sha256"])==64
        assert src["match_basis"]=="PRIMARY_CANDIDATE_ONLY"

def test_confirmed_strategy_execution_is_explicit_and_replayable():
    import tempfile
    from .run_instance import confirm_strategy_execution, init_lots, save
    with tempfile.TemporaryDirectory() as td:
        repo=Path(td); iid="I-CONF"
        manifest={"schema":"STRATEGY_INSTANCE_MANIFEST.v1","schema_version":1,
                  "instance_id":iid,"created_at_utc":"2026-10-01T00:00:00+00:00",
                  "start_at_utc":"2026-10-01T00:00:00+00:00","strategy_id":"TEST",
                  "strategy_version":"V1","initial_positions":[]}
        manifest["manifest_hash"]=mhash(manifest)
        save(mpath(repo,iid),manifest)
        st={"schema":"STRATEGY_INSTANCE_STATE.v1","schema_version":1,"instance_id":iid,
            "processed_deal_ids":["D1"],"strategy_deal_ids":[],"unattributed_deal_ids":["D1"],
            "lots":[],"realized_pnl":0.0,"last_cycle_at":None,"last_history_backfill_at":None,
            "last_snapshot_hash":None,"last_reconcile":None,"cycle_count":1,"data_gaps":1,
            "gamma_history":[],"gamma_history_schema":2,"gamma_history_unit":"gamma_spot","far_delta_abs":None,
            "manual_lots":[],"manual_realized_pnl":0.0,"manual_trade_count":0,"manual_last_mark":None}
        save(spath(repo,iid),st)
        l=InstanceLedger(lpath(repo,iid),{"instance_id":iid,"manifest_hash":manifest["manifest_hash"],"strategy_id":"TEST","strategy_version":"V1"})
        l.append("BROKER_EXECUTION_UNATTRIBUTED",instance_id=iid,cycle_id="C1",
                 timestamp_utc="2026-10-01T00:01:00+00:00",
                 payload={"deal":{"deal_id":"D1","code":"US.QQQ.TEST","side":"BUY","qty":2,"price":5.0,"lot_size":100,"created_at":"2026-10-01T00:01:00+00:00"},
                          "reason":"strategy_execution_requires_explicit_user_confirmation"})
        out=confirm_strategy_execution(repo,instance_id=iid,deal_id="D1",expected_strategy_side="LONG",qty=1,note="verified")
        assert out["confirmed_qty"]==1
        assert out["strategy_application"]=="CONFIRMED_OPEN_LONG"
        _,state,ledger=load_instance(repo,iid)
        assert state["strategy_deal_ids"]==["D1"]
        assert state["unattributed_deal_ids"]==["D1"]
        assert state["lots"][0]["qty"]==1
        assert state["lots"][0]["source"]=="BROKER_DEAL_CONFIRMED"
        assert ledger.validate()["records"]==2


def test_confirm_rejects_already_attributed_execution():
    import tempfile
    from .run_instance import confirm_strategy_execution, save
    with tempfile.TemporaryDirectory() as td:
        repo=Path(td); iid="I-CONF-BLOCK"
        manifest={"schema":"STRATEGY_INSTANCE_MANIFEST.v1","schema_version":1,
                  "instance_id":iid,"created_at_utc":"2026-10-01T00:00:00+00:00",
                  "start_at_utc":"2026-10-01T00:00:00+00:00","strategy_id":"TEST",
                  "strategy_version":"V1","initial_positions":[]}
        manifest["manifest_hash"]=mhash(manifest)
        save(mpath(repo,iid),manifest)
        st={"schema":"STRATEGY_INSTANCE_STATE.v1","schema_version":1,"instance_id":iid,
            "processed_deal_ids":[],"strategy_deal_ids":["D-EX"],"unattributed_deal_ids":[],
            "lots":[],"realized_pnl":0.0,"last_cycle_at":None,"last_history_backfill_at":None,
            "last_snapshot_hash":None,"last_reconcile":None,"cycle_count":1,"data_gaps":0,
            "gamma_history":[],"gamma_history_schema":2,"gamma_history_unit":"gamma_spot","far_delta_abs":None,
            "manual_lots":[],"manual_realized_pnl":0.0,"manual_trade_count":0,"manual_last_mark":None}
        save(spath(repo,iid),st)
        ledger=InstanceLedger(lpath(repo,iid),{"instance_id":iid,"manifest_hash":manifest["manifest_hash"],"strategy_id":"TEST","strategy_version":"V1"})
        ledger.append("EXECUTION_DETECTED",instance_id=iid,cycle_id="C1",
                      timestamp_utc="2026-10-01T00:01:00+00:00",
                      payload={"deal":{"deal_id":"D-EX","code":"US.QQQ.TEST","side":"BUY","qty":1,"price":5.0,"lot_size":100,"created_at":"2026-10-01T00:01:00+00:00"}})
        try:
            confirm_strategy_execution(repo,instance_id=iid,deal_id="D-EX",expected_strategy_side="LONG",qty=1,note="double")
        except SystemExit as exc:
            assert str(exc)=="STRATEGY_DEAL_ALREADY_FULLY_CONFIRMED:D-EX"
        else:
            raise AssertionError("already attributed execution was confirmable")


def test_confirmed_strategy_execution_supports_partial_qty_without_losing_remainder():
    import tempfile
    from .run_instance import confirm_strategy_execution, save
    with tempfile.TemporaryDirectory() as td:
        repo=Path(td); iid="I-CONF-PART"
        manifest={"schema":"STRATEGY_INSTANCE_MANIFEST.v1","schema_version":1,
                  "instance_id":iid,"created_at_utc":"2026-10-01T00:00:00+00:00",
                  "start_at_utc":"2026-10-01T00:00:00+00:00","strategy_id":"TEST",
                  "strategy_version":"V1","initial_positions":[]}
        manifest["manifest_hash"]=mhash(manifest)
        save(mpath(repo,iid),manifest)
        st={"schema":"STRATEGY_INSTANCE_STATE.v1","schema_version":1,"instance_id":iid,
            "processed_deal_ids":["D2"],"strategy_deal_ids":[],"unattributed_deal_ids":["D2"],
            "lots":[],"realized_pnl":0.0,"last_cycle_at":None,"last_history_backfill_at":None,
            "last_snapshot_hash":None,"last_reconcile":None,"cycle_count":1,"data_gaps":1,
            "gamma_history":[],"gamma_history_schema":2,"gamma_history_unit":"gamma_spot","far_delta_abs":None,
            "manual_lots":[],"manual_realized_pnl":0.0,"manual_trade_count":0,"manual_last_mark":None}
        save(spath(repo,iid),st)
        ledger=InstanceLedger(lpath(repo,iid),{"instance_id":iid,"manifest_hash":manifest["manifest_hash"],"strategy_id":"TEST","strategy_version":"V1"})
        ledger.append("BROKER_EXECUTION_UNATTRIBUTED",instance_id=iid,cycle_id="C1",
                      timestamp_utc="2026-10-01T00:01:00+00:00",
                      payload={"deal":{"deal_id":"D2","code":"US.QQQ.TEST","side":"BUY","qty":5,"price":4.0,"lot_size":100,"created_at":"2026-10-01T00:01:00+00:00"},
                               "reason":"strategy_execution_requires_explicit_user_confirmation"})
        out=confirm_strategy_execution(repo,instance_id=iid,deal_id="D2",expected_strategy_side="LONG",qty=2,note="first confirmed slice")
        assert out["confirmed_qty"]==2
        assert out["strategy_application"]=="CONFIRMED_OPEN_LONG"
        _,state,_=load_instance(repo,iid)
        assert state["strategy_deal_ids"]==["D2"]
        assert state["unattributed_deal_ids"]==["D2"]
        assert state["lots"][0]["qty"]==2
        assert state["lots"][0]["source"]=="BROKER_DEAL_CONFIRMED"


def test_potential_plan_match_consumption_counts_prior_unattributed_events():
    from .run_instance import attribute_broker_deal
    plan_key=("7",0,"ADD_NEAR","US.QQQ261030C00500000","BUY")
    rows=[
        {
            "event_seq":7,"event_id":"E7",
            "event_type":"STRATEGY_PLAN_OBSERVED",
            "timestamp_utc":"2026-10-01T21:00:00+00:00",
            "payload":{
                "plan":{
                    "primary_candidate":{
                        "action":"ADD_NEAR",
                        "code":"US.QQQ261030C00500000",
                        "qty":2,
                    }
                }
            },
        },
        {
            "event_seq":8,
            "event_type":"BROKER_EXECUTION_UNATTRIBUTED",
            "timestamp_utc":"2026-10-01T21:01:00+00:00",
            "payload":{
                "deal":{"deal_id":"D0","code":"US.QQQ261030C00500000",
                        "side":"BUY","qty":2,"price":8.0,
                        "created_at":"2026-10-01T21:01:00+00:00"},
                "attribution":{
                    "plan_key":plan_key,
                    "qty":2,
                },
            },
        },
    ]
    d={"deal_id":"D1","code":"US.QQQ261030C00500000","side":"BUY","qty":1,
       "price":8.1,"created_at":"2026-10-01T21:02:00+00:00"}
    out=attribute_broker_deal(rows,d,{})
    assert out["status"]=="UNATTRIBUTED"
    assert out["reason"]=="strategy_plan_quantity_already_consumed"

def test_strategy_plan_quantity_cannot_be_reused_across_cycles():
    from .run_instance import attribute_broker_deal
    plan_key=("7",0,"ADD_NEAR","US.QQQ261030C00500000","BUY")
    rows=[
        {
            "event_seq":7,
            "event_type":"STRATEGY_PLAN_OBSERVED",
            "timestamp_utc":"2026-10-01T21:00:00+00:00",
            "payload":{"plan":{
                "candidate_actions":[{"action":"ADD_NEAR","code":"US.QQQ261030C00500000","qty":2}],
                "primary_candidate":{"action":"ADD_NEAR","code":"US.QQQ261030C00500000","qty":2},
            }},
        },
        {
            "event_seq":8,
            "event_type":"EXECUTION_DETECTED",
            "timestamp_utc":"2026-10-01T21:01:00+00:00",
            "payload":{
                "deal":{"deal_id":"D1","code":"US.QQQ261030C00500000","side":"BUY","qty":2,"price":8.0},
                "attribution":{"plan_key":plan_key,"qty":2},
            },
        },
    ]
    d={"deal_id":"D2","code":"US.QQQ261030C00500000","side":"BUY","qty":1,"price":8.0,"created_at":"2026-10-01T21:05:00+00:00"}
    out=attribute_broker_deal(rows,d)
    assert out["status"]=="UNATTRIBUTED"
    assert out["reason"]=="strategy_plan_quantity_already_consumed"


def test_non_primary_candidate_is_not_auto_attributed():
    from .run_instance import attribute_broker_deal
    rows=[{
        "event_seq":8,
        "event_type":"STRATEGY_PLAN_OBSERVED",
        "timestamp_utc":"2026-10-01T21:00:00+00:00",
        "payload":{"plan":{
            "candidate_actions":[
                {"action":"HARVEST_NEAR","code":"US.QQQ261030C00500000","qty":1},
                {"action":"ADD_NEAR","code":"US.QQQ261030C00500000","qty":2},
            ],
            "primary_candidate":{
                "action":"HARVEST_NEAR","code":"US.QQQ261030C00500000","qty":1,
            },
        }},
    }]
    deal={"deal_id":"D2","code":"US.QQQ261030C00500000","side":"BUY","qty":2,"price":8.0,"created_at":"2026-10-01T21:01:00+00:00"}
    out=attribute_broker_deal(rows,deal)
    assert out["status"]=="UNATTRIBUTED"
    assert out["reason"]=="no_recent_matching_strategy_plan"


def test_instance_mutation_lock_serializes_threads():
    with tempfile.TemporaryDirectory() as td:
        events = []
        active = [0]
        peak = [0]
        guard = threading.Lock()

        def worker(name):
            with instance_mutation_lock(Path(td), "I-LOCK"):
                with guard:
                    active[0] += 1
                    peak[0] = max(peak[0], active[0])
                    events.append(name + "-start")
                time.sleep(0.02)
                with guard:
                    events.append(name + "-end")
                    active[0] -= 1

        a = threading.Thread(target=worker, args=("A",))
        b = threading.Thread(target=worker, args=("B",))
        a.start(); b.start(); a.join(); b.join()
        assert peak[0] == 1
        assert events[0].endswith("-start")
        assert events[1].endswith("-end")
        assert events[2].endswith("-start")
        assert events[3].endswith("-end")


def test_instance_contract_map_merges_live_quote_timestamp():
    from .run_instance import contracts_map
    cmap = contracts_map({
        "contracts": [{
            "code": "US.QQQ.TEST", "right": "CALL", "strike": 500.0,
            "expiry": "2026-10-30", "dte": 30,
            "bid": None, "ask": None, "delta": None, "gamma": None, "iv": None,
            "lot_size": 100, "volume": None,
        }],
        "quotes": {
            "US.QQQ.TEST": {
                "bid": 8.0, "ask": 8.5, "delta": 0.50, "gamma": 0.03,
                "iv": 0.25, "volume": 1234,
                "timestamp": "2026-10-01T21:00:00+00:00",
            }
        },
    })
    assert cmap["US.QQQ.TEST"].quote_timestamp == "2026-10-01T21:00:00+00:00"


def test_instance_contract_map_merges_live_quote_fields():
    from .run_instance import contracts_map
    cmap = contracts_map({
        "contracts": [{
            "code": "US.QQQ.TEST", "right": "CALL", "strike": 500.0,
            "expiry": "2026-10-30", "dte": 30,
            "bid": None, "ask": None, "delta": None, "gamma": None, "iv": None,
            "lot_size": 100, "volume": None,
        }],
        "quotes": {
            "US.QQQ.TEST": {
                "bid": 8.0, "ask": 8.5, "delta": 0.50, "gamma": 0.03,
                "iv": 0.25, "volume": 1234,
            }
        },
    })
    assert cmap["US.QQQ.TEST"].bid == 8.0
    assert cmap["US.QQQ.TEST"].delta == 0.50
    assert cmap["US.QQQ.TEST"].gamma == 0.03
    assert cmap["US.QQQ.TEST"].iv == 0.25
    assert cmap["US.QQQ.TEST"].volume == 1234




def test_strategy_plan_receives_persisted_dynamic_state_inputs():
    from .run_instance import gamma_state_for_instance
    state = {"gamma_history": [10.0, 11.0, 12.0, 13.0, 14.0], "gamma_history_schema": 2, "gamma_history_unit": "gamma_spot", "far_delta_abs": 0.08}
    hist, baseline, prev = gamma_state_for_instance(state, None, 500.0)
    assert hist == [10.0, 11.0, 12.0, 13.0, 14.0]
    assert baseline == 12.0
    assert prev == 0.08



def test_futu_naive_us_timestamp_is_converted_to_utc_for_deal_order_filtering():
    from .run_instance import dt
    z = dt("2026-10-01 17:00:00")
    assert z is not None
    assert z.hour == 21
    assert z.utcoffset().total_seconds() == 0

def test_gamma_state_resets_unmarked_legacy_history():
    from .run_instance import gamma_state_for_instance
    state = {"gamma_history": [0.01, 0.012, 0.011, 0.015, 0.02], "far_delta_abs": 0.08}
    hist, baseline, prev = gamma_state_for_instance(state, None, 500.0)
    assert hist == []
    assert baseline is None
    assert prev == 0.08
    assert state["gamma_history_schema"] == 2
    assert state["gamma_history_unit"] == "gamma_spot"

def test_state_cache_recovery_rebuilds_only_accepted_dynamic_observations():
    with tempfile.TemporaryDirectory() as td:
        repo=Path(td); instance_id="I-DYNAMIC"
        manifest={
            "schema":"STRATEGY_INSTANCE_MANIFEST.v1","schema_version":1,
            "instance_id":instance_id,
            "created_at_utc":"2026-10-01T00:00:00+00:00",
            "start_at_utc":"2026-10-01T00:00:00+00:00",
            "strategy_id":"TEST","strategy_version":"V1",
            "initial_positions":[],
        }
        manifest["manifest_hash"]=mhash(manifest)
        save(mpath(repo,instance_id),manifest)
        l=InstanceLedger(lpath(repo,instance_id),{
            "instance_id":instance_id,
            "manifest_hash":manifest["manifest_hash"],
            "strategy_id":"TEST",
            "strategy_version":"V1",
        })
        l.append("INSTANCE_CREATED",instance_id=instance_id,cycle_id="C0",
                 timestamp_utc="2026-10-01T00:00:00+00:00",payload={})
        l.append("STRATEGY_PLAN_OBSERVED",instance_id=instance_id,cycle_id="C1",
                 timestamp_utc="2026-10-01T00:01:00+00:00",
                 payload={
                     "strategy_observation_accepted":False,
                     "gamma_spot_observed":99.0,
                     "far_delta_abs_observed":0.50,
                 },source="SYSTEM")
        l.append("STRATEGY_PLAN_OBSERVED",instance_id=instance_id,cycle_id="C2",
                 timestamp_utc="2026-10-01T00:02:00+00:00",
                 payload={
                     "strategy_observation_accepted":True,
                     "gamma_spot_observed":10.0,
                     "far_delta_abs_observed":0.08,
                 },source="SYSTEM")
        l.append("STRATEGY_PLAN_OBSERVED",instance_id=instance_id,cycle_id="C3",
                 timestamp_utc="2026-10-01T00:03:00+00:00",
                 payload={
                     "strategy_observation_accepted":True,
                     "gamma_spot_observed":12.0,
                     "far_delta_abs_observed":0.10,
                 },source="SYSTEM")
        Path(spath(repo,instance_id)).write_text("{broken",encoding="utf-8")
        _,state,_=load_instance(repo,instance_id)
        assert state["gamma_history"]==[10.0,12.0]
        assert state["far_delta_abs"]==0.10
        assert state["gamma_history_schema"]==2
        assert state["gamma_history_unit"]=="gamma_spot"

def test_economic_t0_is_strict_broker_attribution_boundary():
    # The cycle partition must treat executions at/before economic T0 as
    # outside the strategy instance, even when the instance file was created earlier.
    src = Path(__file__).resolve().parents[2] / "research" / "strategy_instance_v1" / "run_instance.py"
    text = src.read_text(encoding="utf-8")
    assert 'if deal_time <= economic_t0:' in text
    assert 'pre_instance.append(d)' in text

def test_manual_trade_timestamp_cannot_precede_t0_or_jump_future():
    with tempfile.TemporaryDirectory() as td:
        repo=Path(td); instance_id="I-TIME"
        manifest={
            "schema":"STRATEGY_INSTANCE_MANIFEST.v1","schema_version":1,
            "instance_id":instance_id,
            "created_at_utc":"2026-10-01T00:00:00+00:00",
            "start_at_utc":"2026-10-01T01:00:00+00:00",
            "strategy_id":"TEST","strategy_version":"V1","initial_positions":[],
        }
        manifest["manifest_hash"]=mhash(manifest)
        save(mpath(repo,instance_id),manifest)
        l=InstanceLedger(lpath(repo,instance_id),{
            "instance_id":instance_id,"manifest_hash":manifest["manifest_hash"],
            "strategy_id":"TEST","strategy_version":"V1"})
        l.append("INSTANCE_CREATED",instance_id=instance_id,cycle_id="C0",
                 timestamp_utc="2026-10-01T01:00:00+00:00",payload={})
        try:
            from .run_instance import record_manual_trade
            record_manual_trade(repo,instance_id=instance_id,action="ADD",
                code="US.QQQ.TEST",qty=1,price=5.0,
                timestamp_utc="2026-10-01T00:30:00+00:00")
        except SystemExit as exc:
            assert str(exc)=="MANUAL_TRADE_BEFORE_ECONOMIC_T0"
        else:
            raise AssertionError("pre-T0 manual trade must be blocked")

        future=(datetime.now(timezone.utc)+__import__("datetime").timedelta(minutes=10)).isoformat()
        try:
            record_manual_trade(repo,instance_id=instance_id,action="ADD",
                code="US.QQQ.TEST",qty=1,price=5.0,timestamp_utc=future)
        except SystemExit as exc:
            assert str(exc)=="MANUAL_TRADE_FUTURE"
        else:
            raise AssertionError("future manual trade must be blocked")


def test_partial_strategy_confirmations_merge_into_one_lot():
    from .run_instance import apply_confirmed_strategy_deal
    lots=[]
    deal={"deal_id":"D-PART","code":"US.QQQ.TEST","side":"BUY","qty":1,
          "price":5.0,"lot_size":100,"created_at":"2026-10-01T00:00:10+00:00"}
    used1,_,_=apply_confirmed_strategy_deal(lots,deal,"LONG")
    used2,_,_=apply_confirmed_strategy_deal(lots,deal,"LONG")
    assert used1==1 and used2==1
    assert len(lots)==1
    assert lots[0]["lot_id"]=="D-D-PART-L"
    assert lots[0]["qty"]==2
    assert lots[0]["avg_price"]==5.0


def test_strategy_confirmation_rejects_side_conflict():
    with tempfile.TemporaryDirectory() as td:
        repo=Path(td); instance_id="I-CONFLICT"
        manifest={
            "schema":"STRATEGY_INSTANCE_MANIFEST.v1","schema_version":1,
            "instance_id":instance_id,
            "created_at_utc":"2026-10-01T00:00:00+00:00",
            "start_at_utc":"2026-10-01T00:00:00+00:00",
            "strategy_id":"TEST","strategy_version":"V1","initial_positions":[],
        }
        manifest["manifest_hash"]=mhash(manifest)
        save(mpath(repo,instance_id),manifest)
        l=InstanceLedger(lpath(repo,instance_id),{
            "instance_id":instance_id,"manifest_hash":manifest["manifest_hash"],
            "strategy_id":"TEST","strategy_version":"V1"})
        l.append("INSTANCE_CREATED",instance_id=instance_id,cycle_id="C0",
                 timestamp_utc="2026-10-01T00:00:00+00:00",payload={})
        deal={"deal_id":"D1","code":"US.QQQ.TEST","side":"BUY","qty":2,
              "price":5.0,"lot_size":100,"created_at":"2026-10-01T00:00:10+00:00"}
        l.append("BROKER_EXECUTION_UNATTRIBUTED",instance_id=instance_id,cycle_id="C1",
                 timestamp_utc="2026-10-01T00:00:11+00:00",
                 payload={"deal":deal,"attribution":None},source="BROKER_OBSERVED")
        l.append("STRATEGY_EXECUTION_CONFIRMED",instance_id=instance_id,cycle_id="C2",
                 timestamp_utc="2026-10-01T00:00:12+00:00",
                 payload={"deal":deal,"confirmed_qty":1,
                          "expected_strategy_side":"LONG","unattributed_remaining_qty":1},
                 source="USER_MANUAL")
        try:
            from .run_instance import confirm_strategy_execution
            confirm_strategy_execution(repo,instance_id=instance_id,deal_id="D1",
                expected_strategy_side="SHORT",qty=1)
        except SystemExit as exc:
            assert str(exc).startswith("STRATEGY_CONFIRMATION_SIDE_CONFLICT:D1:")
        else:
            raise AssertionError("conflicting strategy side confirmation must be blocked")

def test_corrupt_instance_state_cache_recovers_from_ledger():
    with tempfile.TemporaryDirectory() as td:
        repo=Path(td); instance_id="I-CACHE"
        manifest={
            "schema":"STRATEGY_INSTANCE_MANIFEST.v1","schema_version":1,
            "instance_id":instance_id,
            "created_at_utc":"2026-10-01T00:00:00+00:00",
            "start_at_utc":"2026-10-01T00:00:00+00:00",
            "strategy_id":"TEST","strategy_version":"V1",
            "initial_positions":[],
        }
        manifest["manifest_hash"]=mhash(manifest)
        save(mpath(repo,instance_id),manifest)
        l=InstanceLedger(lpath(repo,instance_id),{
            "instance_id":instance_id,"manifest_hash":manifest["manifest_hash"],
            "strategy_id":"TEST","strategy_version":"V1"})
        l.append("INSTANCE_CREATED",instance_id=instance_id,cycle_id="C0",
                 timestamp_utc="2026-10-01T00:00:00+00:00",payload={})
        save(spath(repo,instance_id),{"schema":"BROKEN"})
        Path(spath(repo,instance_id)).write_text("{broken",encoding="utf-8")
        m,state,_=load_instance(repo,instance_id)
        assert m["instance_id"]==instance_id
        assert state["state_cache_integrity"]=="CORRUPT_RECOVERED_FROM_LEDGER"
        assert state["instance_id"]==instance_id

def test_load_recovers_broker_state_from_immutable_execution_ledger():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        instance_id = "I-RECOVER"
        manifest = {
            "schema": "STRATEGY_INSTANCE_MANIFEST.v1",
            "schema_version": 1,
            "instance_id": instance_id,
            "created_at_utc": "2026-10-01T00:00:00+00:00",
            "start_at_utc": "2026-10-01T00:00:00+00:00",
            "strategy_id": "TEST",
            "strategy_version": "V1",
            "initial_positions": [{
                "code": "US.QQQ261030C00500000",
                "side": "LONG",
                "qty": 1,
                "avg_cost": 5.0,
                "lot_size": 100,
            }],
        }
        manifest["manifest_hash"] = mhash(manifest)
        save(mpath(repo, instance_id), manifest)
        stale = {
            "schema": "STRATEGY_INSTANCE_STATE.v1",
            "schema_version": 1,
            "instance_id": instance_id,
            "processed_deal_ids": [],
            "lots": init_lots(manifest),
            "realized_pnl": 0.0,
            "last_cycle_at": None,
            "last_snapshot_hash": None,
            "last_reconcile": None,
            "cycle_count": 0,
            "data_gaps": 0,
            "manual_lots": init_lots(manifest),
            "manual_realized_pnl": 0.0,
            "manual_trade_count": 0,
            "manual_last_mark": None,
        }
        save(spath(repo, instance_id), stale)
        from .ledger import InstanceLedger
        ledger = InstanceLedger(
            repo / "research/strategy_instance_v1/instances" / instance_id / "ledger.jsonl",
            {
                "instance_id": instance_id,
                "manifest_hash": manifest["manifest_hash"],
                "strategy_id": "TEST",
                "strategy_version": "V1",
            },
        )
        ledger.append(
            "EXECUTION_DETECTED",
            instance_id=instance_id,
            cycle_id="C1",
            timestamp_utc="2026-10-01T00:01:00+00:00",
            payload={
                "deal": {
                    "deal_id": "D1",
                    "code": "US.QQQ261030C00500000",
                    "side": "SELL",
                    "qty": 1,
                    "price": 7.0,
                    "lot_size": 100,
                    "created_at": "2026-10-01T00:01:00+00:00",
                    "attribution_status": "MATCHED_PREDECISION_PLAN",
                },
                "attribution": {
                    "status": "MATCHED_PREDECISION_PLAN",
                    "match": {
                        "event_seq": 3,
                        "candidate_index": 0,
                        "observed_at_utc": "2026-10-01T00:00:30+00:00",
                        "action": "REDUCE_NEAR",
                        "candidate": {
                            "action": "REDUCE_NEAR",
                            "code": "US.QQQ261030C00500000",
                            "qty": 1,
                        },
                        "age_minutes": 0.5,
                    },
                },
                "realized_pnl_delta": 200.0,
            },
            source="BROKER_OBSERVED",
        )
        _, state, _ = load_instance(repo, instance_id)
        assert state["realized_pnl"] == 0.0
        assert state["processed_deal_ids"] == ["D1"]
        assert state["strategy_deal_ids"] == []
        assert state["unattributed_deal_ids"] == ["D1"]
        assert all(x["qty"] == 1 for x in state["lots"] if x["code"] == "US.QQQ261030C00500000")

def test_instance_ledger_concurrent_append_preserves_chain():
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "ledger.jsonl"
        ledger = InstanceLedger(path, {"instance_id": "I-CONC"})
        errors = []

        def worker(i):
            try:
                ledger.append(
                    "HUMAN_NOTE",
                    instance_id="I-CONC",
                    cycle_id=f"C{i}",
                    timestamp_utc=f"2026-10-01T00:00:{i:02d}+00:00",
                    payload={"i": i},
                    source="USER_MANUAL",
                )
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(12)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert not errors
        result = ledger.validate()
        assert result["records"] == 12


def test_hash_chain():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/"ledger.jsonl"; l=InstanceLedger(p,{"instance_id":"I"})
        l.append("INSTANCE_CREATED",instance_id="I",cycle_id="C1",timestamp_utc="2026-10-01T00:00:00+00:00",payload={"x":1})
        l.append("MARK_TO_MARKET",instance_id="I",cycle_id="C1",timestamp_utc="2026-10-01T00:00:01+00:00",payload={"pnl":12.5})
        assert l.validate()["records"]==2
        p.write_text(p.read_text().replace('"pnl":12.5','"pnl":13.5'),encoding="utf-8")
        try: l.validate()
        except InstanceLedgerError as e: assert "HASH_MISMATCH" in str(e)
        else: raise AssertionError("tamper not detected")

def test_fifo_long_close():
    lots=[{"lot_id":"T0","code":"US.QQQ.TEST","side":"LONG","qty":2,"avg_price":5.0,"lot_size":100,"status":"OPEN"}]
    r=apply_deal(lots,{"deal_id":"D1","code":"US.QQQ.TEST","side":"SELL","qty":3,"price":6.0,"lot_size":100})
    assert r==200.0
    assert sum(x["qty"] for x in lots if x.get("status","OPEN")=="OPEN" and x["side"]=="SHORT")==1

def test_fifo_short_cover():
    lots=[{"lot_id":"T0","code":"US.QQQ.TEST","side":"SHORT","qty":2,"avg_price":7.0,"lot_size":100,"status":"OPEN"}]
    r=apply_deal(lots,{"deal_id":"D2","code":"US.QQQ.TEST","side":"BUY_BACK","qty":1,"price":4.0,"lot_size":100})
    assert r==300.0
    assert sum(x["qty"] for x in lots if x.get("status","OPEN")=="OPEN" and x["side"]=="SHORT")==1

def test_canonical_hash_order():
    assert sha256_json({"a":1,"b":2})==sha256_json({"b":2,"a":1})

def test_manual_adjustable_book_tracks_realized_pnl_without_touching_broker_book():
    lots=[]
    pnl,_=manual_apply_trade(lots,action="ADD",code="US.QQQ.TEST",qty=2,price=5.0,lot_size=100,trade_id="M1",timestamp="2026-10-01T00:00:00+00:00")
    assert pnl==0.0
    pnl,_=manual_apply_trade(lots,action="REDUCE",code="US.QQQ.TEST",qty=1,price=7.0,lot_size=100,trade_id="M2",timestamp="2026-10-01T00:01:00+00:00")
    assert pnl==200.0
    pos=manual_position_snapshot(lots)
    assert pos[0]["qty"]==1
    assert pos[0]["avg_cost"]==5.0


def test_manual_far_short_book_tracks_cover_pnl():
    lots=[]
    manual_apply_trade(lots,action="SELL_FAR",code="US.QQQ.TEST",qty=10,price=2.0,lot_size=100,trade_id="M3",timestamp="2026-10-01T00:02:00+00:00")
    pnl,_=manual_apply_trade(lots,action="BUY_BACK_FAR",code="US.QQQ.TEST",qty=4,price=1.25,lot_size=100,trade_id="M4",timestamp="2026-10-01T00:03:00+00:00")
    assert pnl==300.0
    pos=manual_position_snapshot(lots)
    assert pos[0]["side"]=="SHORT"
    assert pos[0]["qty"]==6

def test_manual_pnl_preview_does_not_mutate_book():
    lots=[{"lot_id":"T0","code":"US.QQQ.TEST","side":"LONG","qty":2,"avg_price":5.0,"lot_size":100,"status":"OPEN"}]
    p=manual_book_pnl_preview(lots,action="REDUCE",code="US.QQQ.TEST",qty=1,price=7.0,lot_size=100)
    assert p["realized_pnl_preview"]==200.0
    assert p["matched_qty"]==1
    assert lots[0]["qty"]==2


def test_manual_pnl_preview_blocks_over_reduce():
    lots=[{"lot_id":"T0","code":"US.QQQ.TEST","side":"LONG","qty":1,"avg_price":5.0,"lot_size":100,"status":"OPEN"}]
    p=manual_book_pnl_preview(lots,action="REDUCE",code="US.QQQ.TEST",qty=2,price=7.0,lot_size=100)
    assert p["remaining_unmatched"]==1



def test_strategy_plan_fails_closed_on_unknown_qqq_position_side():
    from .run_instance import strategy_plan
    from research.live_hedge_v1.engine import Contract
    c=Contract("US.QQQ261230C00600000","CALL",600.0,"2026-12-30",90,2.0,2.5,0.08,0.01,0.2,100,100)
    out=strategy_plan(
        {"market":{"spot":500.0,"timestamp":"2026-10-01T21:00:00+00:00","signal_active":True}},
        [{"code":c.code,"side":"UNKNOWN","qty":10,"avg_cost":2.0}],
        [], {c.code:c}, {c.code:{"bid":2.0,"ask":2.5,"delta":0.08,"gamma":0.01}},
        {"far_dte":90,"far_delta":0.08,"near_dte":30,"far_code_hint":c.code},
    )
    assert out["status"]=="BLOCKED_UNKNOWN_POSITION_SIDE"


def test_strategy_cycle_far_observation_does_not_pick_first_ambiguous_short():
    from .run_instance import instance_far_position
    positions = [
        {"code": "US.QQQ261230C00600000", "side": "SHORT", "qty": 10},
        {"code": "US.QQQ261230C00610000", "side": "SHORT", "qty": 5},
    ]
    assert instance_far_position({}, positions) is None
    assert instance_far_position({"far_code_hint": positions[1]["code"]}, positions)["code"] == positions[1]["code"]

def test_explicit_far_code_hint_is_allowed_only_for_single_broker_row():
    from .run_instance import instance_far_position
    p={"code":"US.QQQ261230C00600000","side":"SHORT","qty":10}
    out=instance_far_position({"far_code_hint":p["code"]},[p],[])
    assert out["qty"]==10
    assert out["ownership_source"]=="EXPLICIT_FAR_CODE_HINT_SINGLE_BROKER_ROW"


def test_strategy_plan_blocks_extra_same_code_far_quantity():
    from .run_instance import strategy_plan
    from research.live_hedge_v1.engine import Contract
    code="US.QQQ261230C00600000"
    contract=Contract(code,"CALL",600.0,"2026-12-30",90,2.0,2.5,0.08,0.01,0.2,100,100)
    cmap={code:contract}; quotes={code:{"bid":2.0,"ask":2.5,"delta":0.08,"gamma":0.01}}
    out=strategy_plan(
        {"market":{"spot":500.0,"timestamp":datetime.now(timezone.utc).isoformat(),"source":"LIVE QUOTE","signal_active":False}},
        [{"code":code,"side":"SHORT","qty":12,"avg_cost":2.0}],
        [],cmap,quotes,
        {"far_dte":90,"far_delta":0.08,"near_dte":30,"far_code_hint":code},
        near_lots=[{"lot_id":"F1","code":code,"side":"SHORT","qty":10,"avg_price":2.0,"status":"OPEN"}],
    )
    assert out["status"]=="DATA_GAP"
    assert "quantity differs" in out["reason"]


def test_strategy_plan_refuses_single_unowned_far_short():
    from .run_instance import strategy_plan
    from research.live_hedge_v1.engine import Contract
    contract=Contract(
        "US.QQQ261230C00600000","CALL",600.0,"2026-12-30",90,
        2.0,2.5,0.08,0.01,0.2,100,100,
    )
    cmap={contract.code:contract}
    quotes={contract.code:{"bid":2.0,"ask":2.5,"delta":0.08,"gamma":0.01}}
    out=strategy_plan(
        {"market":{"spot":500.0,"timestamp":datetime.now(timezone.utc).isoformat(),"source":"LIVE QUOTE","signal_active":False}},
        [{"code":contract.code,"side":"SHORT","qty":10,"avg_cost":2.0}],
        [],cmap,quotes,
        {"far_dte":90,"far_delta":0.08,"near_dte":30},
        near_lots=[],
    )
    assert out["status"]=="DATA_GAP"
    assert "unscoped QQQ SHORT" in out["reason"]


def test_strategy_plan_refuses_ambiguous_far_short_ownership():
    from .run_instance import strategy_plan
    from research.live_hedge_v1.engine import Contract
    snap = {
        "market": {"spot": 500.0, "timestamp": "2026-10-01T21:00:00+00:00", "signal_active": False},
    }
    contracts = [
        Contract("US.QQQ261230C00600000","CALL",600.0,"2026-12-30",90,2.0,2.5,0.08,0.01,0.2,100,100),
        Contract("US.QQQ261230C00610000","CALL",610.0,"2026-12-30",90,1.5,2.0,0.05,0.01,0.2,100,100),
    ]
    cmap = {c.code: c for c in contracts}
    quotes = {c.code: {"bid": c.bid, "ask": c.ask, "delta": c.delta, "gamma": c.gamma} for c in contracts}
    ps = [
        {"code": contracts[0].code, "side": "SHORT", "qty": 10, "avg_cost": 2.0},
        {"code": contracts[1].code, "side": "SHORT", "qty": 5, "avg_cost": 1.8},
    ]
    out = strategy_plan(snap, ps, [], cmap, quotes, {"far_dte": 90, "far_delta": 0.08, "near_dte": 30})
    assert out["status"] == "DATA_GAP"
    assert "unscoped QQQ SHORT" in out["reason"]


def test_strategy_mark_cost_basis_ignores_unmanaged_same_code_lots():
    from .run_instance import managed_position_view
    ps=[
        {"code":"US.QQQ.TEST","side":"LONG","qty":11,"avg_cost":9.0,"lot_size":100},
    ]
    lots=[
        {"lot_id":"S1","code":"US.QQQ.TEST","side":"LONG","qty":1,"avg_price":5.0,"lot_size":100,"status":"OPEN"},
    ]
    view=managed_position_view(ps,lots)
    assert view==[{
        "code":"US.QQQ.TEST","side":"LONG","qty":1,"avg_cost":5.0,
        "lot_size":100,"source":"BROKER_OBSERVED_STRATEGY_OWNED",
        "cost_basis_source":"STRATEGY_LOTS",
    }]


def test_strategy_plan_ignores_unmanaged_qqq_long_from_target_stack():
    from .run_instance import strategy_plan
    from research.live_hedge_v1.engine import Contract

    near_code="US.QQQ261130C00500000"
    other_code="US.QQQ261130C00510000"
    far_code="US.QQQ261230C00600000"
    contracts=[
        Contract(near_code,"CALL",500.0,"2026-11-30",30,8.0,8.5,0.50,0.01,0.2,100,100),
        Contract(other_code,"CALL",510.0,"2026-11-30",30,7.0,7.5,0.45,0.01,0.2,100,100),
        Contract(far_code,"CALL",600.0,"2026-12-30",90,2.0,2.5,0.08,0.01,0.2,100,100),
    ]
    cmap={c.code:c for c in contracts}
    quotes={c.code:{"bid":c.bid,"ask":c.ask,"delta":c.delta,"gamma":c.gamma} for c in contracts}
    ps=[
        {"code":near_code,"side":"LONG","qty":1,"avg_cost":8.0},
        {"code":other_code,"side":"LONG","qty":20,"avg_cost":7.0},
        {"code":far_code,"side":"SHORT","qty":10,"avg_cost":2.0},
    ]
    managed_lots=[{"lot_id":"T1","code":near_code,"side":"LONG","qty":1,"avg_cost":8.0,"status":"OPEN"}]
    out=strategy_plan(
        {"market":{"spot":500.0,"timestamp":datetime.now(timezone.utc).isoformat(),"source":"LIVE QUOTE","signal_active":False}},
        ps,[],cmap,quotes,
        {"far_dte":90,"far_delta":0.08,"near_dte":30,"far_code_hint":far_code},
        near_lots=managed_lots,
    )
    assert out["status"] in {"ACTIONABLE","HOLD"}
    assert "ACTIVE_NEAR=1" in out.get("reasons",[])
    assert all(x.get("code")!=other_code for x in out.get("candidate_actions",[]))



def test_strategy_plan_explicit_far_hint_accepts_single_dict_position():
    from .run_instance import strategy_plan
    from research.live_hedge_v1.engine import Contract
    contract=Contract(
        "US.QQQ261230C00600000","CALL",600.0,"2026-12-30",90,
        2.0,2.5,0.08,0.01,0.2,100,100,
    )
    cmap={contract.code:contract}
    quotes={contract.code:{"bid":2.0,"ask":2.5,"delta":0.08,"gamma":0.01}}
    out=strategy_plan(
        {"market":{"spot":500.0,"timestamp":datetime.now(timezone.utc).isoformat(),"source":"LIVE QUOTE","signal_active":False}},
        [{"code":contract.code,"side":"SHORT","qty":10,"avg_cost":2.0}],
        [],
        cmap,
        quotes,
        {"far_dte":90,"far_delta":0.08,"near_dte":30,"far_code_hint":contract.code},
    )
    assert out["far"]["code"]==contract.code


def test_strategy_plan_uses_explicit_far_code_hint():
    from .run_instance import strategy_plan
    from research.live_hedge_v1.engine import Contract
    snap = {
        "market": {"spot": 500.0, "timestamp": datetime.now(timezone.utc).isoformat(), "source": "LIVE QUOTE", "signal_active": False},
    }
    contracts = [
        Contract("US.QQQ261230C00600000","CALL",600.0,"2026-12-30",90,2.0,2.5,0.08,0.01,0.2,100,100),
        Contract("US.QQQ261230C00610000","CALL",610.0,"2026-12-30",90,1.5,2.0,0.05,0.01,0.2,100,100),
    ]
    cmap = {c.code: c for c in contracts}
    quotes = {c.code: {"bid": c.bid, "ask": c.ask, "delta": c.delta, "gamma": c.gamma} for c in contracts}
    ps = [
        {"code": contracts[0].code, "side": "SHORT", "qty": 10, "avg_cost": 2.0},
        {"code": contracts[1].code, "side": "SHORT", "qty": 5, "avg_cost": 1.8},
    ]
    out = strategy_plan(
        snap, ps, [], cmap, quotes,
        {"far_dte": 90, "far_delta": 0.08, "near_dte": 30},
    )
    assert out["status"] == "DATA_GAP"
    out = strategy_plan(
        snap, ps, [], cmap, quotes,
        {"far_dte": 90, "far_delta": 0.08, "near_dte": 30, "far_code_hint": contracts[0].code},
    )
    assert out["status"] == "DATA_GAP"
    assert "extra broker QQQ SHORT" in out["reason"]

    # A single explicitly hinted far position is admissible.
    out = strategy_plan(
        snap, [ps[0]], [], cmap, quotes,
        {"far_dte": 90, "far_delta": 0.08, "near_dte": 30, "far_code_hint": contracts[0].code},
    )
    assert out["far"]["code"] == contracts[0].code

def test_strategy_relationship_requires_semantic_action_match():
    ref = {"ticket_id":"T1","code":"US.QQQ.TEST","action":"SELL_FAR","qty":10}
    assert classify_relationship("SELL_FAR","US.QQQ.TEST",10,ref) == "FOLLOW_STRATEGY"
    assert classify_relationship("SELL_FAR","US.QQQ.TEST",7,ref) == "ADJUST_SIZE"
    assert classify_relationship("BUY_BACK_FAR","US.QQQ.TEST",10,ref) == "OPERATOR_ONLY"
    assert classify_relationship("ADD","US.QQQ.OTHER",10,ref) == "OPERATOR_ONLY"


def test_emergency_leg_maps_to_manual_action():
    ref = {
        "ticket_id":"T2","code":"US.QQQ.FAR","action":"CLOSE_CAMPAIGN_EMERGENCY",
        "strategy_leg_action":"CLOSE_FAR_EMERGENCY","side":"BUY","qty":2
    }
    assert classify_relationship("BUY_BACK_FAR","US.QQQ.FAR",2,ref) == "FOLLOW_STRATEGY"
    assert classify_relationship("BUY_BACK_FAR","US.QQQ.FAR",1,ref) == "ADJUST_SIZE"


def test_performance_tape_recomputes_old_broad_follow_label():
    trades = [{
        "timestamp_utc":"2026-10-01T00:00:00+00:00","event_seq":1,"trade_id":"M1",
        "action":"BUY_BACK_FAR","code":"US.QQQ.TEST","qty":2,"price":1.0,"lot_size":100,
        "relationship_to_strategy":"FOLLOW_STRATEGY",
        "strategy_reference":{"ticket_id":"T1","code":"US.QQQ.TEST","action":"SELL_FAR","qty":2,"price":2.0},
        "realized_pnl_delta":0.0
    }]
    tape = build_performance_tape(trades)
    assert tape["counts"]["OPERATOR_ONLY"] == 1
    assert tape["counts"]["FOLLOW_STRATEGY"] == 0
    assert tape["rows"][0]["relationship"] == "OPERATOR_ONLY"
    assert tape["rows"][0]["qty_delta"] is None
    assert tape["size_gap_contracts"] == 0
    assert tape["rows"][0]["execution_slippage_estimate"] is None


def test_performance_tape_fifo_attributes_close_to_opening_decisions():
    trades = [
        {
            "timestamp_utc":"2026-10-01T00:00:00+00:00","event_seq":1,"trade_id":"M1",
            "action":"ADD","code":"US.QQQ.TEST","qty":2,"price":5.0,"lot_size":100,
            "strategy_reference":{"ticket_id":"T1","code":"US.QQQ.TEST","action":"ADD_NEAR","qty":2,"price":5.0},
            "realized_pnl_delta":0.0,
        },
        {
            "timestamp_utc":"2026-10-01T00:01:00+00:00","event_seq":2,"trade_id":"M2",
            "action":"ADD","code":"US.QQQ.TEST","qty":3,"price":6.0,"lot_size":100,
            "strategy_reference":{"ticket_id":"T2","code":"US.QQQ.TEST","action":"ADD_NEAR","qty":5,"price":6.0},
            "realized_pnl_delta":0.0,
        },
        {
            "timestamp_utc":"2026-10-01T00:02:00+00:00","event_seq":3,"trade_id":"M3",
            "action":"REDUCE","code":"US.QQQ.TEST","qty":4,"price":8.0,"lot_size":100,
            "strategy_reference":{},
            "realized_pnl_delta":1000.0,
        },
    ]
    tape = build_performance_tape(trades)
    assert tape["opening_counts"]["FOLLOW_STRATEGY"] == 1
    assert tape["opening_counts"]["ADJUST_SIZE"] == 1
    assert tape["closing_counts"]["OPERATOR_ONLY"] == 1
    assert tape["attributed_realized"]["FOLLOW_STRATEGY"] == 600.0
    assert tape["attributed_realized"]["ADJUST_SIZE"] == 400.0
    assert tape["observed_realized"] == 1000.0
    assert tape["attribution_delta"] == 0.0
    assert tape["unmatched_close_qty"] == 0
    assert tape["attribution_status"] == "CONSISTENT"
    rows = {x["trade_id"]: x for x in tape["rows"]}
    assert rows["M1"]["attributed_close_pnl"] == 600.0
    assert rows["M2"]["attributed_close_pnl"] == 400.0


def test_performance_tape_t0_close_is_baseline_not_mismatch():
    trades = [{
        "timestamp_utc":"2026-10-01T00:01:00+00:00","event_seq":2,"trade_id":"M1",
        "action":"REDUCE","code":"US.QQQ.TEST","qty":1,"price":8.0,"lot_size":100,
        "strategy_reference":{},
        "realized_pnl_delta":300.0,
    }]
    baseline = [{
        "lot_id":"T0-0001","code":"US.QQQ.TEST","side":"LONG",
        "qty":1,"avg_price":5.0,"lot_size":100
    }]
    tape = build_performance_tape(trades, baseline_lots=baseline)
    assert tape["baseline_t0_realized"] == 300.0
    assert tape["baseline_t0_close_qty"] == 1
    assert tape["observed_realized"] == 300.0
    assert tape["attribution_delta"] == 0.0
    assert tape["unmatched_close_qty"] == 0
    assert tape["attribution_status"] == "CONSISTENT"


def test_repair_far_direction_maps_to_correct_manual_action():
    assert classify_relationship(
        "SELL_FAR","US.QQQ.TEST",10,
        {"ticket_id":"T3","code":"US.QQQ.TEST","action":"REPAIR_FAR","direction":"ADD","qty":10}
    ) == "FOLLOW_STRATEGY"
    assert classify_relationship(
        "BUY_BACK_FAR","US.QQQ.TEST",2,
        {"ticket_id":"T4","code":"US.QQQ.TEST","action":"REPAIR_FAR","direction":"REDUCE","qty":2}
    ) == "FOLLOW_STRATEGY"



def test_roll_ticket_legs_carry_semantic_actions():
    before = {
        "LONG:US.QQQ.OLD": {"code": "US.QQQ.OLD", "side": "LONG", "qty": 2, "avg_cost": 5.0},
    }
    from ..live_hedge_v1.campaign import build_ticket
    ticket = build_ticket(
        action={
            "action": "ROLL_NEAR",
            "code": "US.QQQ.OLD",
            "qty": 2,
            "price": 6.0,
            "new_code": "US.QQQ.NEW",
            "new_price": 7.0,
        },
        campaign_id="C-ROLL",
        before_positions=before,
        now="2026-10-01T00:00:00+00:00",
        sequence=1,
    )
    assert ticket["legs"][0]["strategy_leg_action"] == "REDUCE_NEAR"
    assert ticket["legs"][1]["strategy_leg_action"] == "ADD_NEAR"


def test_roll_manual_legs_are_classified_by_leg_semantics():
    old_ref = {
        "ticket_id": "T-ROLL",
        "action": "ROLL_NEAR",
        "strategy_leg_action": "REDUCE_NEAR",
        "code": "US.QQQ.OLD",
        "qty": 2,
    }
    new_ref = {
        "ticket_id": "T-ROLL",
        "action": "ROLL_NEAR",
        "strategy_leg_action": "ADD_NEAR",
        "code": "US.QQQ.NEW",
        "qty": 2,
    }
    assert classify_relationship("REDUCE", "US.QQQ.OLD", 2, old_ref) == "FOLLOW_STRATEGY"
    assert classify_relationship("ADD", "US.QQQ.NEW", 2, new_ref) == "FOLLOW_STRATEGY"



def load_tests(loader, tests, pattern):
    """Allow unittest CI to execute this module's top-level test functions."""
    suite = unittest.TestSuite(tests)
    for name, obj in sorted(globals().items()):
        if name.startswith("test_") and callable(obj):
            suite.addTest(unittest.FunctionTestCase(obj, description=name))
    return suite
