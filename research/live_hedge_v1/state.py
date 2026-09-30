from __future__ import annotations
import json
from pathlib import Path

class StateStore:
    def __init__(self,path="research/live_hedge_v1/state.json"):
        self.path=Path(path)
    def load(self):
        return json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {"far_code":None,"far_delta":None,"gamma_history":[]}
    def save(self,s):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.path.write_text(json.dumps(s,indent=2,ensure_ascii=False),encoding="utf-8")
    def update_far(self,code,delta,gamma,previous_delta):
        s=self.load(); hist=s.setdefault("gamma_history",[])
        baseline=(sum(hist[-20:])/len(hist[-20:])) if len(hist)>=3 else None
        if delta is not None:s["far_delta"]=abs(float(delta))
        if gamma is not None:hist.append(abs(float(gamma)))
        s["gamma_history"]=hist[-20:];s["far_code"]=code
        self.save(s)
        return {"previous_far_delta_abs":previous_delta,"gamma_baseline":baseline}
