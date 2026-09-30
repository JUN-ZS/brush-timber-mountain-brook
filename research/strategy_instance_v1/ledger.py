from __future__ import annotations
import hashlib, json, os
from pathlib import Path
from typing import Any

SCHEMA = "STRATEGY_INSTANCE.v1"
GENESIS = "0" * 64
EVENT_TYPES = {"INSTANCE_CREATED","INITIAL_STATE_RECORDED","BROKER_CYCLE_OBSERVED",
               "STRATEGY_PLAN_OBSERVED","EXECUTION_DETECTED","MARK_TO_MARKET",
               "DATA_GAP","HUMAN_NOTE"}

def canonical_json(v: Any) -> str:
    return json.dumps(v, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)

def sha256_json(v: Any) -> str:
    return hashlib.sha256(canonical_json(v).encode("utf-8")).hexdigest()

class InstanceLedgerError(RuntimeError): pass

class InstanceLedger:
    def __init__(self, path: str | Path, identity: dict[str, Any] | None = None):
        self.path = Path(path); self.identity = identity or {}
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _rows(self):
        if not self.path.exists(): return []
        out=[]
        for n,line in enumerate(self.path.read_text(encoding="utf-8").splitlines(),1):
            if not line.strip(): continue
            try: out.append(json.loads(line))
            except json.JSONDecodeError as e: raise InstanceLedgerError(f"CORRUPT_JSON:{n}") from e
        return out

    def validate(self):
        prev=GENESIS; rows=self._rows()
        for i,row in enumerate(rows,1):
            if row.get("schema") != SCHEMA: raise InstanceLedgerError(f"BAD_SCHEMA:{i}")
            if int(row.get("event_seq",-1)) != i: raise InstanceLedgerError(f"BAD_SEQUENCE:{i}")
            if row.get("previous_hash") != prev: raise InstanceLedgerError(f"CHAIN_BREAK:{i}")
            rh=row.get("record_hash")
            if not rh: raise InstanceLedgerError(f"MISSING_HASH:{i}")
            body=dict(row); body.pop("record_hash",None)
            if sha256_json(body) != rh: raise InstanceLedgerError(f"HASH_MISMATCH:{i}")
            prev=rh
        return {"valid":True,"records":len(rows),"head_hash":prev,"path":str(self.path)}

    def append(self,event_type: str,*,instance_id: str,cycle_id: str,
               timestamp_utc: str,payload: dict[str,Any],source: str="SYSTEM"):
        if event_type not in EVENT_TYPES: raise InstanceLedgerError(f"UNKNOWN_EVENT:{event_type}")
        v=self.validate(); seq=v["records"]+1
        row={"schema":SCHEMA,"schema_version":1,"event_seq":seq,
             "event_id":f"IE-{timestamp_utc.replace(':','').replace('-','').replace('.','')}-{seq:06d}",
             "instance_id":instance_id,"cycle_id":cycle_id,"timestamp_utc":timestamp_utc,
             "event_type":event_type,"source":source,"identity":self.identity,
             "previous_hash":v["head_hash"],"payload":payload}
        row["record_hash"]=sha256_json(row)
        with self.path.open("a",encoding="utf-8",newline="\n") as f:
            f.write(canonical_json(row)+"\n"); f.flush(); os.fsync(f.fileno())
        return row
