"""2026-09-22 gate fixes: post-review roadmap ledger, ship writes outside the repo, binding-gap names.

CC and CX share one fixture. Run: python3 vibeCoding/scripts/tests/athena999/test_gate_fixes_20260922.py
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[3]
CX = ROOT / "codex/9.9.9/.codex/hooks"
CC = ROOT / "claude/9.9.9/.claude/hooks"
CC_GATE = CC / "delivery-gate.cjs"
CX_GATE = CX / "delivery-gate.py"


def load_cx_gate():
    sys.path.insert(0, str(CX))
    spec = importlib.util.spec_from_file_location("delivery_gate_fixes", CX_GATE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(root, *args):
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True)


class RoadmapAllowlist(unittest.TestCase):
    """ship 后 roadmap/<slug>/items.yaml 与 vm-pending 同属过程台账, 不进 post-review drift。"""

    def test_roadmap_items_are_allowed_and_other_state_still_blocks(self):
        gate = load_cx_gate()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            git(root, "init", "-q")
            sprint = root / ".ai_state/sprints/test"
            sprint.mkdir(parents=True)
            design = sprint / "design.md"
            design.write_text("## Done Contract\n- AC1: ships\n", encoding="utf-8")
            git(root, "add", ".")
            git(root, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "reviewed")
            commit = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"], check=True, text=True, capture_output=True
            ).stdout.strip()
            fm = {key: "" for key in gate.INDEX_GOVERNANCE_FIELDS}
            fm.update(version="9.9.9", path="Feature", current_sprint_slug="test")
            manifest = sprint / "review-manifest.yaml"
            manifest.write_text(
                "schema_version: 1\nimplementation_commit: " + commit
                + "\nindex_governance_sha256: " + gate.index_governance_sha256(fm)
                + '\nfiles:\n  design.md: "' + hashlib.sha256(design.read_bytes()).hexdigest() + '"\n',
                encoding="utf-8",
            )
            review = (
                "Reviewed design sha256: " + hashlib.sha256(design.read_bytes()).hexdigest() + "\n"
                "Reviewed implementation commit: " + commit + "\n"
                "Reviewed state manifest sha256: " + hashlib.sha256(manifest.read_bytes()).hexdigest() + "\n"
            )
            items = root / ".ai_state/roadmap/demo/items.yaml"
            items.parent.mkdir(parents=True)
            items.write_text("slug: demo\nitems: []\n", encoding="utf-8")
            gate.validate_review_binding(
                review, sprint / "reviews/implementation-review.md", sprint, root / ".ai_state", root, fm
            )
            code = (
                "const m=require(process.argv[1]);"
                "m.validateReviewBinding(process.argv[2],'review',process.argv[3],process.argv[4],process.argv[5],JSON.parse(process.argv[6]));"
            )
            args = [
                "node", "-e", code, str(CC_GATE), review, str(sprint), str(root / ".ai_state"), str(root), json.dumps(fm)
            ]
            run = subprocess.run(args, text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            outside = root / ".ai_state/roadmap-evil.md"
            outside.write_text("must block\n", encoding="utf-8")
            with self.assertRaisesRegex(gate.GateError, "unreviewed .ai_state drift"):
                gate.validate_review_binding(
                    review, sprint / "reviews/implementation-review.md", sprint, root / ".ai_state", root, fm
                )
            run = subprocess.run(args, text=True, capture_output=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn("unreviewed .ai_state drift", run.stderr)
            self.assertIn(".ai_state/roadmap-evil.md", run.stderr)


if __name__ == "__main__":
    unittest.main()
