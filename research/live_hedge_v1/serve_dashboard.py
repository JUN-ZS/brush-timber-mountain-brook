from __future__ import annotations
import argparse,os
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--port",type=int,default=8765)
    args=ap.parse_args()
    repo=Path(__file__).resolve().parents[2]
    os.chdir(repo)
    print("Dashboard: http://127.0.0.1:%d/research/live_hedge_v1/dashboard.html"%args.port,flush=True)
    ThreadingHTTPServer(("127.0.0.1",args.port),SimpleHTTPRequestHandler).serve_forever()

if __name__=="__main__":main()
