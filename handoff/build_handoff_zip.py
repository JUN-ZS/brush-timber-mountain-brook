#!/usr/bin/env python3
from pathlib import Path
import zipfile, json, hashlib, os, subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "ULTIMATE_EVOLUTIONARY_TRADING_BRAIN_HANDOFF_V1.zip"

PREFIXES = [
    "handoff/",
    "terminal/qqq_hybrid_deployment_v2/",
    "backtest/",
]
EXACT = [
    "attachments/QQQ-VXX-ChatGPT-完整對話.md",
    "attachments/EVB_EVOLUTIONARY_REPORT.md",
    "attachments/spots_qqq_vxx_vix.1csv",
    "artifacts/backtest-curve.csv",
    "artifacts/backtest-report.md",
    "artifacts/backtest-result.json",
    "research/QQQ_HYBRID_DYNAMIC_DEPLOYMENT_V1_1_README.md",
    "research/QQQ_HYBRID_DOWNSIDE_CONVEXITY_V1_README.md",
    "research/era_dd_return_matrix.md",
    "research/era_dd_return_matrix.json",
    "research/cost_oos_cpcv_survival.md",
    "research/cost_oos_cpcv_survival.json",
    "research/relvol_v22_state_map.md",
    "research/relvol_v22_state_map.json",
    "research/inertia_state_join_contract.md",
    "research/inertia_state_join_contract.json",
    "research/data/vx_m1_m2_external_2016_2022.csv",
    ".github/workflows/qqq-hybrid-terminal-v2.yml",
]

def include(p: Path) -> bool:
    s = p.relative_to(ROOT).as_posix()
    return any(s.startswith(x) for x in PREFIXES) or s in EXACT

files = [p for p in ROOT.rglob("*") if p.is_file() and include(p) and ".git" not in p.parts]
files = sorted(files)

manifest = []
for p in files:
    data = p.read_bytes()
    manifest.append({
        "path": p.relative_to(ROOT).as_posix(),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    })

(OUT.parent).mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for p in files:
        z.write(p, p.relative_to(ROOT).as_posix())
    z.writestr("HANDOFF_MANIFEST.json", json.dumps({
        "package": "ULTIMATE_EVOLUTIONARY_TRADING_BRAIN_HANDOFF_V1",
        "file_count": len(manifest),
        "git_branch": subprocess.run(["git","rev-parse","--abbrev-ref","HEAD"],cwd=ROOT,text=True,capture_output=True).stdout.strip(),
        "git_commit": subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,text=True,capture_output=True).stdout.strip(),
        "files": manifest,
    }, ensure_ascii=False, indent=2))

print(json.dumps({
    "output": str(OUT),
    "file_count": len(files),
    "size_bytes": OUT.stat().st_size
}, ensure_ascii=False))
