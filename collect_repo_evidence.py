#!/usr/bin/env python3
"""
collect_repo_evidence.py (Merged v2 — Read-Only Audit & Blind-Safe Collector)

Combines the features of both audit kits while fixing context-bloat and blind-leakage issues:
1. Strictly read-only: uses GIT_OPTIONAL_LOCKS=0, refuses to write inside target repo,
   never modifies working tree, commits, branches, or broker state.
2. Context-window safe: keeps `git/command_results.json` compact (summaries & line counts)
   instead of inlining megabytes of `git rev-list --objects --all` output that would overflow
   an LLM coding agent's context window.
3. Blind-safe `--snapshot`: when `--snapshot` is used for Stage 1, `README*` and narrative
   report files are automatically quarantined into a separate Stage-2-only archive
   (`quarantined_narrative_snapshot_STAGE2_ONLY_HEAD.tar.gz`) so
   `repository_text_snapshot_BLIND_SAFE_HEAD.tar.gz` can be safely handed to the Stage 1
   blind reviewer without leaking prior conclusions.
4. Deep file & data indexing: records per-file SHA-256 hashes, scans code contents for strategy
   keywords, and previews CSV column headers plus first/last rows (date ranges).
5. Fast GitHub metadata: sanitizes remote credentials and fetches recent Actions runs, PRs,
   issues, and artifact metadata in bulk without downloading large artifact payloads.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
from typing import Any, Dict, List, Optional

REPO_DEFAULT = "JUN-ZS/brush-timber-mountain-brook"

SECRET_PATH_PARTS = {
    ".env", ".aws", ".ssh", "credentials", "secrets", "private_keys",
    "private-keys", "id_rsa", "id_ed25519", "keystore", "certs-private"
}

TEXT_SUFFIXES = {
    ".md", ".mdx", ".txt", ".py", ".js", ".mjs", ".cjs", ".ts", ".tsx",
    ".jsx", ".html", ".css", ".scss", ".json", ".yaml", ".yml", ".toml",
    ".ini", ".cfg", ".sh", ".bat", ".cmd", ".ps1", ".sql", ".r", ".jl",
    ".ipynb", ".csv", ".tsv", ".xml", ".svg", ".gitignore", ".dockerignore"
}

CONFIG_NAMES = {
    "package.json", "pyproject.toml", "requirements.txt", "requirements-dev.txt",
    "pytest.ini", "tox.ini", "noxfile.py", "Makefile", "justfile", "Cargo.toml",
    "go.mod", "Gemfile", "Pipfile", "uv.lock", "Dockerfile", "compose.yaml",
    "docker-compose.yml"
}

STRATEGY_KEYWORDS = re.compile(
    r"(qqq|vxx|vix|vx|option|put|call|hybrid|backtest|replay|risk|nav|capital|"
    r"floor|sizing|kelly|portfolio|funding|correlation|strategy|signal|ledger|pnl|"
    r"audit|golden|contract|research|test|workflow|action|assumption|data|"
    r"spread|ratio|cagr|sharpe|drawdown|stress|monte_carlo|bootstrap|resample|"
    r"friction|slippage|commission|tax|bond|treasury|yield|rebalanc|regime|term_structure)",
    re.IGNORECASE,
)

NARRATIVE_PATTERNS = re.compile(
    r"(^readme|report|result|finding|analysis|summary|conclusion|proposal|"
    r"recommendation|review|audit|assumption|validation|release|decision|plan|notes)",
    re.IGNORECASE,
)


def sanitize_remote(s: str) -> str:
    """Remove embedded credentials from remote URLs if any."""
    return re.sub(r"(https?://)[^/@\s]+:[^/@\s]+@", r"\1[REDACTED]@", s)


def sensitive_path(path: str) -> bool:
    parts = [p.lower() for p in Path(path).parts]
    if any(p in SECRET_PATH_PARTS for p in parts):
        return True
    name = Path(path).name.lower()
    return (
        name.startswith(".env")
        or name.endswith((".pem", ".p12", ".pfx", ".key"))
        or "credential" in name
        or "secret" in name
    )


def is_narrative_doc(path: str) -> bool:
    p = Path(path)
    name = p.name.lower()
    suffix = p.suffix.lower()

    # Free-form document formats are quarantined by default. Filename heuristics alone
    # cannot reliably distinguish neutral technical notes from prior AI conclusions.
    # HTML source can contain the application/engine, so only quarantine narrative HTML.
    if (
        name.startswith(("readme", "prompt", "stage2", "stage_2", "stage-2"))
        or "adversarial" in name
    ):
        return True

    if suffix in {".md", ".mdx", ".txt", ".rst", ".pdf", ".docx"}:
        return True
    if suffix == ".html" and NARRATIVE_PATTERNS.search(p.as_posix()):
        return True
    return False

def run(cmd: List[str], cwd: Optional[Path] = None, timeout: int = 60) -> Dict[str, Any]:
    try:
        p = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
            env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
        )
        return {
            "command": cmd,
            "returncode": p.returncode,
            "stdout": p.stdout,
            "stderr": p.stderr,
        }
    except FileNotFoundError as exc:
        return {"command": cmd, "returncode": 127, "stdout": "", "stderr": str(exc)}
    except subprocess.TimeoutExpired as exc:
        return {
            "command": cmd,
            "returncode": 124,
            "stdout": exc.stdout or "",
            "stderr": f"Timed out after {timeout}s",
        }


def write_text(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data, encoding="utf-8", errors="replace")


def write_json(path: Path, data: Any) -> None:
    write_text(path, json.dumps(data, indent=2, ensure_ascii=False, default=str) + "\n")


def sha256_file(path: Path, max_bytes: int = 50 * 1024 * 1024) -> Optional[str]:
    try:
        if not path.is_file() or path.is_symlink():
            return None
        if path.stat().st_size > max_bytes:
            return "SKIPPED_LARGE_FILE"
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def inspect_csv_preview(path: Path) -> Dict[str, Any]:
    """Read header and first/last rows of a CSV file without modifying it."""
    info: Dict[str, Any] = {"columns": [], "row_count_estimate": 0, "first_row": None, "last_row": None}
    try:
        if not path.is_file() or path.stat().st_size > 25 * 1024 * 1024:
            info["note"] = "File > 25MB or not regular file; skipped full line scan."
            if path.is_file():
                with path.open("r", encoding="utf-8", errors="replace") as f:
                    reader = csv.reader(f)
                    header = next(reader, None)
                    first = next(reader, None)
                    info["columns"] = header[:30] if header else []
                    info["first_row"] = first[:10] if first else None
            return info

        with path.open("r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            info["columns"] = header[:30] if header else []
            first = None
            last = None
            count = 0
            for row in reader:
                if not row:
                    continue
                count += 1
                if first is None:
                    first = row[:10]
                last = row[:10]
            info["row_count_estimate"] = count
            info["first_row"] = first
            info["last_row"] = last
    except Exception as exc:
        info["error"] = str(exc)
    return info


def detect_github_slug(remotes_text: str, fallback: str) -> str:
    for line in remotes_text.splitlines():
        m = re.search(r"github\.com[:/]([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?(?:\s|$)", line)
        if m:
            return m.group(1)
    return fallback


def gh_json(args: List[str], cwd: Path, timeout: int = 45) -> Dict[str, Any]:
    r = run(["gh", *args], cwd=cwd, timeout=timeout)
    if r["returncode"] == 0:
        try:
            r["parsed"] = json.loads(r["stdout"])
        except Exception:
            pass
    r["stdout"] = sanitize_remote(r["stdout"])
    r["stderr"] = sanitize_remote(r["stderr"])
    return r


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("repo", nargs="?", default=".", help="Path to an already-cloned git repository")
    ap.add_argument("--out", default="../independent-audit-evidence", help="Evidence output directory (must be outside repo)")
    ap.add_argument("--github-repo", default=None, help="owner/repo for optional GitHub metadata queries (auto-detected if omitted)")
    ap.add_argument("--no-github", "--skip-gh", dest="no_github", action="store_true", help="Only collect local git evidence; do not invoke gh")
    ap.add_argument("--snapshot", action="store_true", help="Create bounded text tar.gz snapshots at HEAD (separating code/data from narrative docs)")
    ap.add_argument("--max-file-bytes", type=int, default=1_000_000, help="Max per-file bytes for optional text snapshot")
    ap.add_argument("--max-snapshot-mb", type=int, default=100, help="Total optional text snapshot size budget in MB")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    out = Path(args.out).resolve()
    if not (repo / ".git").exists() and not (repo / ".git").is_file():
        print(f"ERROR: not a git repository: {repo}", file=sys.stderr)
        return 2
    if out == repo or repo in out.parents:
        print("ERROR: evidence output directory must be outside the target repository.", file=sys.stderr)
        return 2

    # The inventory is anchored to HEAD, while CSV previews and content hashes read
    # working-tree files. Refuse dirty worktrees so those evidence sources cannot disagree.
    status_check = run(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=repo, timeout=60)
    if status_check["returncode"] != 0:
        print("ERROR: could not verify worktree status; refusing to collect ambiguous evidence.", file=sys.stderr)
        return 3
    if status_check["stdout"].strip():
        print(
            "ERROR: worktree is not clean. Commit or discard tracked changes and remove untracked files, "
            "then rerun evidence collection. This collector requires local files to match the pinned HEAD.",
            file=sys.stderr,
        )
        print(status_check["stdout"][:4000], file=sys.stderr)
        return 3

    out.mkdir(parents=True, exist_ok=True)
    generated_at = dt.datetime.now(dt.timezone.utc).isoformat()

    commands = {
        "identity": ["git", "rev-parse", "--show-toplevel", "HEAD"],
        "head_branch": ["git", "branch", "--show-current"],
        "status": ["git", "status", "--porcelain=v1", "--branch"],
        "remotes": ["git", "remote", "-v"],
        "branches": ["git", "branch", "-a", "-vv"],
        "tags": ["git", "tag", "--list", "--sort=-creatordate"],
        "refs": ["git", "show-ref", "--heads", "--tags"],
        "recent_history": [
            "git", "log", "--all", "-n", "500", "--date=iso-strict",
            "--format=%H%x09%ad%x09%an%x09%ae%x09%d%x09%s"
        ],
        "committed_paths_current_head": ["git", "ls-files", "-z"],
        "submodules": ["git", "submodule", "status", "--recursive"],
    }

    local_summary: Dict[str, Any] = {}
    for name, cmd in commands.items():
        r = run(cmd, cwd=repo, timeout=120 if name == "recent_history" else 60)
        stdout_clean = sanitize_remote(r["stdout"])
        stderr_clean = sanitize_remote(r["stderr"])
        if name == "committed_paths_current_head" and r["returncode"] == 0:
            paths = [x for x in r["stdout"].split("\x00") if x]
            write_text(out / "git" / "tracked_paths_HEAD.txt", "\n".join(paths) + "\n")
            local_summary[name] = {
                "command": cmd,
                "returncode": r["returncode"],
                "tracked_file_count": len(paths),
                "output_file": "git/tracked_paths_HEAD.txt",
            }
        else:
            fname = f"{name}.txt"
            write_text(out / "git" / fname, stdout_clean + ("\n[stderr]\n" + stderr_clean if stderr_clean else ""))
            lines = stdout_clean.splitlines()
            local_summary[name] = {
                "command": cmd,
                "returncode": r["returncode"],
                "line_count": len(lines),
                "preview_lines": [] if name == "recent_history" else lines[:20],
                "output_file": f"git/{fname}",
            }

    head_sha = run(["git", "rev-parse", "HEAD"], cwd=repo)["stdout"].strip()
    head_branch = run(["git", "branch", "--show-current"], cwd=repo)["stdout"].strip()
    origin_url = sanitize_remote(run(["git", "remote", "get-url", "origin"], cwd=repo)["stdout"].strip())
    remotes_raw = run(["git", "remote", "-v"], cwd=repo)["stdout"]
    github_slug = args.github_repo or detect_github_slug(remotes_raw, REPO_DEFAULT)

    write_json(out / "git" / "command_results.json", local_summary)

    # Detailed file inventory at HEAD with SHA-256, content keyword scan, and CSV previews
    paths_result = run(["git", "ls-tree", "-r", "-l", "--full-tree", "HEAD"], cwd=repo, timeout=120)
    files: List[Dict[str, Any]] = []
    data_previews: List[Dict[str, Any]] = []

    categories: Dict[str, List[str]] = {
        "configs_and_test_entrypoints": [],
        "github_workflows": [],
        "quarantined_readme_and_narrative_docs": [],
        "strategy_and_backtest_code": [],
        "data_candidates": [],
        "oversized_or_sensitive": [],
    }

    if paths_result["returncode"] == 0:
        for line in paths_result["stdout"].splitlines():
            try:
                left, path = line.split("\t", 1)
                fields = left.split()
                if len(fields) < 4:
                    continue
                git_blob_sha = fields[2]
                size_s = fields[3]
                size = int(size_s) if size_s.isdigit() else 0
                abs_p = repo / path
                suffix = Path(path).suffix.lower()
                name = Path(path).name
                lower = path.lower()

                is_sens = sensitive_path(path)
                is_narr = is_narrative_doc(path)
                file_sha256 = None if is_sens else sha256_file(abs_p)

                matched_keywords: List[str] = []
                if not is_sens and suffix in {".py", ".r", ".jl", ".js", ".mjs", ".ts", ".tsx", ".sh", ".sql", ".ipynb"} and size < 1_000_000 and abs_p.is_file():
                    try:
                        text_sample = abs_p.read_text(encoding="utf-8", errors="ignore")
                        found = set(m.group(0).lower() for m in STRATEGY_KEYWORDS.finditer(text_sample))
                        matched_keywords = sorted(found)[:15]
                    except Exception:
                        pass

                is_rel = bool(STRATEGY_KEYWORDS.search(path)) or bool(matched_keywords)

                entry: Dict[str, Any] = {
                    "path": path,
                    "size_bytes": size,
                    "suffix": suffix,
                    "git_blob_sha": git_blob_sha,
                    "sha256": file_sha256,
                    "sensitive_path_filtered": is_sens,
                    "quarantined_narrative_doc": is_narr,
                    "relevance_candidate": is_rel,
                    "matched_keywords": matched_keywords,
                }
                files.append(entry)

                if name in CONFIG_NAMES or name.lower() in {x.lower() for x in CONFIG_NAMES} or re.search(r"(^tests?/|/tests?/|test_.*\.(py|js|ts|sh)$|.*_test\.(py|js|ts)$)", lower):
                    categories["configs_and_test_entrypoints"].append(path)
                if lower.startswith(".github/workflows/"):
                    categories["github_workflows"].append(path)
                if is_narr:
                    categories["quarantined_readme_and_narrative_docs"].append(path)
                if not is_narr and suffix in {".py", ".js", ".mjs", ".ts", ".tsx", ".sh", ".r", ".jl", ".sql"} and is_rel:
                    categories["strategy_and_backtest_code"].append(path)
                if suffix in {".csv", ".tsv", ".parquet", ".jsonl", ".feather", ".arrow", ".db", ".sqlite"} or re.search(r"(^|/)(data|datasets?|artifacts?)/", lower):
                    categories["data_candidates"].append(path)
                    if suffix == ".csv" and not is_sens and abs_p.is_file():
                        data_previews.append({
                            "path": path,
                            "size_bytes": size,
                            "sha256": file_sha256,
                            "csv_preview": inspect_csv_preview(abs_p),
                        })
                if size > 2_000_000 or is_sens:
                    categories["oversized_or_sensitive"].append(path)
            except Exception:
                continue

    write_json(out / "git" / "file_inventory_HEAD.json", files)
    write_json(out / "git" / "data_files_preview.json", data_previews)
    write_text(
        out / "git" / "relevant_path_candidates.txt",
        "\n".join(
            f"{f['path']}\t{f['size_bytes']}\tquarantined={f['quarantined_narrative_doc']}\tkeywords={','.join(f['matched_keywords'][:6])}"
            for f in files if f["relevance_candidate"]
        ) + "\n",
    )
    write_json(out / "git" / "evidence_path_categories.json", categories)
    write_text(
        out / "git" / "evidence_path_categories.md",
        "# Evidence Path Index\n\n" + "\n".join(
            "## " + k.replace("_", " ").title() + "\n"
            + ("\n".join(f"- `{p}`" for p in v) if v else "- None discovered") + "\n"
            for k, v in categories.items()
        ),
    )

    # Extract workflow definitions and small config files (strictly excluding narrative docs)
    extracts: List[Dict[str, Any]] = []
    for f in files:
        p = f["path"]
        name = Path(p).name
        include = p.startswith(".github/workflows/") or name in CONFIG_NAMES
        if not include or f["sensitive_path_filtered"] or f["quarantined_narrative_doc"] or (f["size_bytes"] or 0) > 250_000:
            continue
        r = run(["git", "show", f"HEAD:{p}"], cwd=repo, timeout=30)
        if r["returncode"] == 0 and "\x00" not in r["stdout"]:
            target = out / "file_extracts" / p
            write_text(target, r["stdout"])
            extracts.append({
                "path": p,
                "output": str(target.relative_to(out)),
                "size_bytes": len(r["stdout"].encode("utf-8", "replace")),
            })
    write_json(out / "file_extracts" / "manifest.json", extracts)

    # Optional bounded snapshots: separate blind-safe code/data snapshot from narrative docs snapshot
    if args.snapshot:
        max_total = max(1, args.max_snapshot_mb) * 1024 * 1024
        blind_snap_path = out / "repository_text_snapshot_BLIND_SAFE_HEAD.tar.gz"
        narr_snap_path = out / "quarantined_narrative_snapshot_STAGE2_ONLY_HEAD.tar.gz"
        total_blind = 0
        total_narr = 0
        chosen_blind = []
        chosen_narr = []

        with tarfile.open(blind_snap_path, "w:gz") as tar_blind, tarfile.open(narr_snap_path, "w:gz") as tar_narr:
            for f in files:
                p = f["path"]
                size = f["size_bytes"] or 0
                if f["sensitive_path_filtered"] or size > args.max_file_bytes or size <= 0:
                    continue
                if Path(p).suffix.lower() not in TEXT_SUFFIXES and Path(p).name.lower() not in {"makefile", "dockerfile", ".gitignore"}:
                    continue
                blob = run(["git", "show", f"HEAD:{p}"], cwd=repo, timeout=30)
                if blob["returncode"] != 0 or "\x00" in blob["stdout"]:
                    continue
                content = blob["stdout"]
                if re.search(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", content):
                    continue
                data = content.encode("utf-8", "replace")
                info = tarfile.TarInfo(name=p)
                info.size = len(data)
                info.mtime = 0

                if f["quarantined_narrative_doc"]:
                    if total_narr + len(data) <= max_total:
                        tar_narr.addfile(info, io.BytesIO(data))
                        total_narr += len(data)
                        chosen_narr.append({"path": p, "size_bytes": len(data)})
                else:
                    if total_blind + len(data) <= max_total:
                        tar_blind.addfile(info, io.BytesIO(data))
                        total_blind += len(data)
                        chosen_blind.append({"path": p, "size_bytes": len(data)})

        write_json(out / "repository_text_snapshot_manifest.json", {
            "blind_safe_archive": blind_snap_path.name,
            "blind_safe_files": len(chosen_blind),
            "blind_safe_bytes": total_blind,
            "stage2_narrative_archive": narr_snap_path.name,
            "stage2_narrative_files": len(chosen_narr),
            "stage2_narrative_bytes": total_narr,
            "excluded_sensitive_path_count": sum(1 for f in files if f["sensitive_path_filtered"]),
            "note": "Stage 1 blind reviewers should only receive blind_safe_archive; stage2_narrative_archive contains quarantined READMEs/reports."
        })

    # Optional GitHub CLI metadata
    github_status: Dict[str, Any] = {"requested": not args.no_github, "repo": github_slug}
    if not args.no_github and shutil.which("gh") is not None:
        auth = run(["gh", "auth", "status"], cwd=repo, timeout=20)
        github_status["gh_auth_status"] = {
            "returncode": auth["returncode"],
            "stderr": sanitize_remote(auth["stderr"]),
            "stdout": sanitize_remote(auth["stdout"]),
        }
        view = gh_json(["repo", "view", github_slug, "--json", "nameWithOwner,url,isPrivate,description,defaultBranchRef"], repo)
        write_json(out / "github" / "repository.json", view.get("parsed", view))
        github_status["repository_query_ok"] = view["returncode"] == 0

        runlist = gh_json([
            "run", "list", "--repo", github_slug, "--limit", "100", "--json",
            "databaseId,name,displayTitle,status,conclusion,createdAt,updatedAt,headSha,url,workflowName,event,headBranch"
        ], repo, timeout=90)
        write_json(out / "github" / "workflow_runs_recent.json", runlist.get("parsed", runlist))
        github_status["workflow_runs_query_ok"] = runlist["returncode"] == 0

        prs = gh_json([
            "pr", "list", "--repo", github_slug, "--state", "all", "--limit", "100", "--json",
            "number,title,state,isDraft,createdAt,updatedAt,mergedAt,closedAt,url,headRefName,headRefOid,baseRefName,mergeStateStatus,reviewDecision"
        ], repo, timeout=90)
        write_json(out / "github" / "pull_requests_recent.json", prs.get("parsed", prs))
        github_status["pull_requests_query_ok"] = prs["returncode"] == 0

        issues = gh_json([
            "issue", "list", "--repo", github_slug, "--state", "all", "--limit", "100", "--json",
            "number,title,state,createdAt,updatedAt,closedAt,url,labels,assignees"
        ], repo, timeout=90)
        write_json(out / "github" / "issues_recent.json", issues.get("parsed", issues))
        github_status["issues_query_ok"] = issues["returncode"] == 0

        # Single bulk API query for recent repo artifacts
        bulk_art = gh_json(["api", f"repos/{github_slug}/actions/artifacts?per_page=100"], repo, timeout=45)
        write_json(out / "github" / "workflow_artifacts_bulk.json", bulk_art.get("parsed", bulk_art))
        github_status["artifacts_bulk_query_ok"] = bulk_art["returncode"] == 0
    elif not args.no_github:
        github_status["note"] = "gh CLI not found in PATH; skipped remote GitHub queries."

    write_json(out / "github" / "collection_status.json", github_status)

    report = {
        "schema": "repo-independent-audit-evidence-v2",
        "generated_at_utc": generated_at,
        "repo_path": str(repo),
        "github_repo": github_slug,
        "head_sha": head_sha,
        "head_branch": head_branch,
        "worktree_clean": True,
        "origin": origin_url,
        "counts": {
            "tracked_files_at_head": len(files),
            "strategy_and_backtest_code": len(categories["strategy_and_backtest_code"]),
            "configs_and_test_entrypoints": len(categories["configs_and_test_entrypoints"]),
            "data_candidates": len(categories["data_candidates"]),
            "quarantined_readme_and_narrative_docs": len(categories["quarantined_readme_and_narrative_docs"]),
            "github_workflows": len(categories["github_workflows"]),
        },
        "collector_version": "2.0.0",
        "scope": "read-only; metadata, hashes, CSV previews, and blind-safe manifests; no strategy conclusion embedded",
    }
    write_json(out / "collection_manifest.json", report)
    write_json(out / "manifest.json", report)

    summary_lines = [
        "# Repository Evidence Collection Summary (`00_README_EVIDENCE_SUMMARY.md`)",
        "",
        f"- **Generated UTC**: `{generated_at}`",
        f"- **Repository**: `{origin_url or github_slug}`",
        f"- **Current Checkout Branch**: `{head_branch or '(detached)'}`",
        f"- **Pinned HEAD Commit SHA**: `{head_sha}`",
        f"- **Tracked Files at HEAD**: {len(files)}",
        f"- **Strategy & Backtest Code Candidates**: {len(categories['strategy_and_backtest_code'])}",
        f"- **Configs & Test Entrypoints**: {len(categories['configs_and_test_entrypoints'])}",
        f"- **Data Path Candidates**: {len(categories['data_candidates'])} (CSV previews in `git/data_files_preview.json`)",
        f"- **Quarantined Narrative / README Docs**: {len(categories['quarantined_readme_and_narrative_docs'])}",
        "",
        "## Stage 1 Isolation Rule (Blind Code-First Review)",
        "1. Give Stage 1 only `repository_text_snapshot_BLIND_SAFE_HEAD.tar.gz`, `collection_manifest.json`, this runbook/prompt, and only the minimum data-preview manifest needed to identify missing inputs.",
        "2. Do NOT give Stage 1 the full evidence folder, Git history, branch/commit messages, `github/` metadata, PR/issue discussions, `git/recent_history.txt`, this generated evidence summary, or `quarantined_narrative_snapshot_STAGE2_ONLY_HEAD.tar.gz`.",
        "3. Do not inspect any file listed under `quarantined_readme_and_narrative_docs` until `STAGE1_INDEPENDENT_FINDINGS.md` has been generated and frozen with `sha256sum`.",
        "4. The blind-safe snapshot represents text files tracked at the pinned HEAD within the configured file/size budget. Record any excluded large, binary, untracked, or branch-only input as `BLOCKED` or `UNVERIFIED`; do not imply those files were inspected.",
        "",
        "## Reading Order for Stage 2 (Adversarial Falsification & Reconciliation)",
        "1. Verify the SHA-256 hash of `STAGE1_INDEPENDENT_FINDINGS.md` and confirm the repository is still at `head_sha`.",
        "2. Inspect `github/workflow_runs_recent.json`, `github/pull_requests_recent.json`, `github/issues_recent.json`, and `github/workflow_artifacts_bulk.json`.",
        "3. Open the quarantined READMEs, prior reports, and PR claims to cross-check written claims against executable code and Stage 1 findings.",
    ]
    summary_text = "\n".join(summary_lines) + "\n"
    write_text(out / "00_README_EVIDENCE_SUMMARY.md", summary_text)
    write_text(out / "EVIDENCE_INDEX.md", summary_text)

    print(f"[OK] Evidence collection complete: {out}")
    print(f"[OK] Pinned HEAD SHA: {head_sha}")
    print(f"[OK] Tracked paths indexed: {len(files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())