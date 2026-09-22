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


class ShipWriteOutsideRepo(unittest.TestCase):
    """Q12 批二③: stage=ship 的 Write/Edit 只拦仓库内路径。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        git(self.root, "init", "-q")
        sprint = self.root / ".ai_state/sprints/gatefix"
        sprint.mkdir(parents=True)
        (self.root / ".ai_state/_index.md").write_text(
            '---\nversion: "9.9.9"\npath: Feature\nstage: ship\n'
            'current_sprint_slug: gatefix\nskip_impl_subagent_check: "true"\n---\n',
            encoding="utf-8",
        )
        (sprint / "design.md").write_text("## Done Contract\n- AC1: ships\n", encoding="utf-8")

    def hook(self, runner, script, tool_input, tool="Write", event="PreToolUse", env=None):
        payload = {
            "hook_event_name": event,
            "cwd": str(self.root),
            "tool_name": tool,
            "tool_input": tool_input,
        }
        return subprocess.run(
            [runner, str(script)], input=json.dumps(payload), text=True, capture_output=True, env=env
        )

    def assert_allowed(self, run, label):
        self.assertEqual(run.returncode, 0, label + "\n" + run.stderr)
        self.assertNotIn("decision", run.stdout, label + "\n" + run.stdout)

    def assert_blocked(self, run, label):
        self.assertEqual(run.returncode, 0, label + "\n" + run.stderr)
        self.assertIn("block", run.stdout, label + "\n" + run.stdout + run.stderr)
        self.assertIn("decision", run.stdout, label + "\n" + run.stdout)

    def test_outside_write_allowed_inside_still_blocks(self):
        env = os.environ.copy()
        env["TMPDIR"] = env.get("TMPDIR") or "/tmp"
        for runner, script, label in (("node", CC_GATE, "cc"), (sys.executable, CX_GATE, "cx")):
            self.assert_blocked(self.hook(runner, script, {"file_path": str(self.root / "inside.js")}), label + " inside")
            self.assert_blocked(self.hook(runner, script, {"file_path": "inside.js"}, tool="Edit"), label + " relative")
            self.assert_allowed(self.hook(runner, script, {"file_path": "/tmp/athena-gatefix-msg.txt"}, tool="Edit"), label + " /tmp")
            self.assert_allowed(
                self.hook(runner, script, {"file_path": "$TMPDIR/athena-gatefix-msg.txt"}, env=env), label + " TMPDIR"
            )
            self.assert_allowed(
                self.hook(runner, script, {"file_path": str(self.root) + "-out/file.txt"}), label + " sibling prefix"
            )
            self.assert_allowed(self.hook(runner, script, {"file_path": "../athena-gatefix-outside.txt"}), label + " parent")
            patch_out = self.hook(runner, script, {"patch": "*** Add File: /tmp/athena-gatefix-patch.txt\n+hello\n"}, tool="apply_patch")
            self.assert_allowed(patch_out, label + " patch /tmp")
            patch_in = self.hook(runner, script, {"patch": "*** Add File: inside.js\n+hello\n"}, tool="apply_patch")
            self.assert_blocked(patch_in, label + " patch inside")
            stopped = self.hook(runner, script, {}, tool="", event="Stop")
            self.assert_blocked(stopped, label + " stop")


if __name__ == "__main__":
    unittest.main()
