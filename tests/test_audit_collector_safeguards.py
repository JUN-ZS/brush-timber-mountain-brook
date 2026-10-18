from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "collect_repo_evidence.py"
SPEC = importlib.util.spec_from_file_location("collect_repo_evidence", SCRIPT)
assert SPEC and SPEC.loader
COLLECTOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(COLLECTOR)


def run_git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def make_repo(base: Path) -> Path:
    repo = base / "repo"
    repo.mkdir()
    run_git(repo, "init", "-q")
    run_git(repo, "config", "user.name", "Audit Test")
    run_git(repo, "config", "user.email", "audit-test@example.invalid")
    (repo / "README.md").write_text("Prior narrative recommendation.\n", encoding="utf-8")
    (repo / "prompt_stage2_adversarial.md").write_text("Stage 2 only.\n", encoding="utf-8")
    (repo / "portfolio_memo.md").write_text("Possible prior recommendation must be quarantined.\\n", encoding="utf-8")
    (repo / "strategy.py").write_text("def qqq_strategy():\n    return 'test'\n", encoding="utf-8")
    (repo / "data.csv").write_text("date,close\n2020-01-01,100\n2020-01-02,101\n", encoding="utf-8")
    run_git(repo, "add", "README.md", "prompt_stage2_adversarial.md", "portfolio_memo.md", "strategy.py", "data.csv")
    run_git(repo, "commit", "-qm", "fixture")
    return repo


class CollectorIsolationTests(unittest.TestCase):
    def test_stage_two_prompts_are_quarantined(self) -> None:
        self.assertTrue(COLLECTOR.is_narrative_doc("prompt_stage2_adversarial.md"))
        self.assertTrue(COLLECTOR.is_narrative_doc("research/PROMPT_STAGE2_ADVERSARIAL.md"))
        self.assertTrue(COLLECTOR.is_narrative_doc("stage2_review_notes.md"))
        self.assertTrue(COLLECTOR.is_narrative_doc("portfolio_memo.md"))
        self.assertTrue(COLLECTOR.is_narrative_doc("docs/technical_notes.txt"))

    def test_blind_snapshot_excludes_prompts_and_readmes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo = make_repo(base)
            out = base / "evidence"
            proc = subprocess.run(
                [
                    sys.executable, str(SCRIPT), str(repo), "--out", str(out),
                    "--no-github", "--snapshot", "--max-file-bytes", "25000000",
                    "--max-snapshot-mb", "1",
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr + "\n" + proc.stdout)

            blind = out / "repository_text_snapshot_BLIND_SAFE_HEAD.tar.gz"
            stage2 = out / "quarantined_narrative_snapshot_STAGE2_ONLY_HEAD.tar.gz"
            with tarfile.open(blind, "r:gz") as archive:
                blind_names = set(archive.getnames())
            with tarfile.open(stage2, "r:gz") as archive:
                stage2_names = set(archive.getnames())

            self.assertIn("strategy.py", blind_names)
            self.assertIn("data.csv", blind_names)
            self.assertNotIn("README.md", blind_names)
            self.assertNotIn("prompt_stage2_adversarial.md", blind_names)
            self.assertNotIn("portfolio_memo.md", blind_names)
            self.assertIn("README.md", stage2_names)
            self.assertIn("prompt_stage2_adversarial.md", stage2_names)
            self.assertIn("portfolio_memo.md", stage2_names)

    def test_dirty_worktree_is_rejected_before_output_creation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            repo = make_repo(base)
            (repo / "untracked.txt").write_text("uncommitted evidence\n", encoding="utf-8")
            out = base / "evidence"
            proc = subprocess.run(
                [sys.executable, str(SCRIPT), str(repo), "--out", str(out), "--no-github"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(proc.returncode, 3, proc.stderr + "\n" + proc.stdout)
            self.assertIn("worktree is not clean", proc.stderr.lower())
            self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
