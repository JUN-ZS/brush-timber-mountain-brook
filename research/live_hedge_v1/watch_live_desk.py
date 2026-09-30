from __future__ import annotations
import argparse,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--interval",type=int,default=15)
    ap.add_argument("--far-dte",type=int,default=120)
    ap.add_argument("--far-delta",type=float,default=.08)
    ap.add_argument("--near-dte",type=int,default=30)
    ap.add_argument("--host",default="127.0.0.1")
    ap.add_argument("--port",type=int,default=11111)
    args=ap.parse_args()
    if args.interval<5:raise ValueError("interval must be >=5 seconds")
    while True:
        started=datetime.now(timezone.utc).isoformat()
        cmd=[sys.executable,"-m","research.live_hedge_v1.run_live_desk",
             "--far-dte",str(args.far_dte),"--far-delta",str(args.far_delta),
             "--near-dte",str(args.near_dte),"--host",args.host,"--port",str(args.port)]
        p=subprocess.run(cmd,text=True,capture_output=True)
        log=Path("research/live_hedge_v1/live_cycles.jsonl")
        log.parent.mkdir(parents=True,exist_ok=True)
        with log.open("a",encoding="utf-8") as f:
            f.write('{"started_at":"'+started.replace('"','')+'","returncode":'+str(p.returncode)+',"stdout":'+__import__("json").dumps((p.stdout or "")[-10000:],ensure_ascii=False)+',"stderr":'+__import__("json").dumps((p.stderr or "")[-4000:],ensure_ascii=False)+'}\n')
        if p.stdout: print("\n"+p.stdout,flush=True)
        if p.returncode!=0 and p.stderr: print(p.stderr,flush=True)
        time.sleep(args.interval)

if __name__=="__main__":main()
