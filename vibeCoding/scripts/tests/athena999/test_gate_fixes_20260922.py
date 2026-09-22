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


CC_AC_HARNESS = r'''
const fs = require("fs"), path = require("path"), Module = require("module");
const gate = process.argv[1], evidence = process.argv[2], sprint = process.argv[3];
const mod = new Module(gate, null);
mod.filename = gate;
mod.paths = Module._nodeModulePaths(path.dirname(gate));
mod._compile(fs.readFileSync(gate, "utf8") + "\nmodule.exports.__t={validateEvidence,validateAcMapping};\n", gate);
const records = mod.exports.__t.validateEvidence(evidence);
try {
  mod.exports.__t.validateAcMapping(sprint, ["AC1: kept", "AC2: dropped"], records, path.join(sprint, "reviews/implementation-review.md"), "VERDICT: PASS\n", "a".repeat(40));
  process.stdout.write("PASS");
} catch (error) {
  process.stderr.write(String((error && error.message) || error));
  process.exit(2);
}
'''
GAP_FIELDS = (
    "source_sha256", "design_sha256", "environment_sha256",
    "binding_status", "output_artifact", "artifact_sha256", "缺字段",
)


class EvidenceFilterNames(unittest.TestCase):
    """缺绑定字段仍整条过滤; block 文案点名 AC 与缺字段。齐套 current 记录仍通过。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        git(self.root, "init", "-q")
        self.sprint = self.root / ".ai_state/sprints/test"
        self.sprint.mkdir(parents=True)
        (self.root / ".ai_state/_index.md").write_text(
            '---\nversion: "9.9.9"\npath: Feature\nstage: ship\n'
            'current_sprint_slug: "test"\nskip_impl_subagent_check: "true"\n---\n',
            encoding="utf-8",
        )
        (self.sprint / "design.md").write_text("## Done Contract\n- AC1: kept\n- AC2: dropped\n", encoding="utf-8")
        (self.root / "app.py").write_text("print(1)\n", encoding="utf-8")
        git(self.root, "add", "app.py")
        git(self.root, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "base")
        self.gate = load_cx_gate()
        spec = importlib.util.spec_from_file_location("input_binding_gatefix", CX / "_input_binding.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.live = module.snapshot(self.root, self.sprint)
        probe = (
            "const m=require(process.argv[1]);"
            "process.stdout.write(JSON.stringify(m.snapshot(process.argv[2],process.argv[3])));"
        )
        run = subprocess.run(
            ["node", "-e", probe, str(CC / "_input-binding.cjs"), str(self.root), str(self.sprint)],
            text=True, capture_output=True,
        )
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout), self.live)

    def write_evidence(self, body):
        (self.sprint / "evidence.yaml").write_text(body, encoding="utf-8")

    def current_block(self, tool_id="current-ac1", ac="AC1", source=None):
        out = self.sprint / "evidence" / "out.txt"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("ok\n", encoding="utf-8")
        digest = hashlib.sha256(out.read_bytes()).hexdigest()
        source = self.live["source_sha256"] if source is None else source
        return (
            f"  - tool_use_id: {tool_id}\n    ac_id: {ac}\n    result: pass\n"
            "    command: npm test\n    timestamp: 2026-09-22T00:00:00Z\n"
            "    binding_status: current\n"
            f"    source_sha256: {source}\n"
            f"    design_sha256: {self.live['design_sha256']}\n"
            f"    environment_sha256: {self.live['environment_sha256']}\n"
            "    output_artifact: evidence/out.txt\n"
            f"    artifact_sha256: {digest}\n"
        )

    def cc_validate(self):
        code = (
            "try{require(process.argv[1]).validateEvidence(process.argv[2]);process.exit(0)}"
            "catch(e){process.stderr.write(String(e.message||e));process.exit(2)}"
        )
        return subprocess.run(
            ["node", "-e", code, str(CC_GATE), str(self.sprint / "evidence.yaml")],
            text=True, capture_output=True,
        )

    def assert_names(self, text, tool_id):
        for field in GAP_FIELDS:
            self.assertIn(field, text)
        self.assertIn(tool_id, text)
        self.assertIn("AC1", text)

    def test_incomplete_stop_names_the_missing_fields(self):
        self.write_evidence(
            "collected_evidence:\n"
            "  - tool_use_id: hand-ac1\n    ac_id: AC1\n    result: pass\n"
            "    command: node test.js\n    timestamp: 2026-09-22T00:00:00Z\n"
        )
        with self.assertRaises(self.gate.GateError) as caught:
            self.gate.validate_evidence(self.sprint / "evidence.yaml")
        self.assert_names(str(caught.exception), "hand-ac1")
        cc = self.cc_validate()
        self.assertEqual(cc.returncode, 2, cc.stderr)
        self.assert_names(cc.stderr, "hand-ac1")
        payload = json.dumps({"hook_event_name": "Stop", "cwd": str(self.root), "session_id": "s", "tool_name": ""})
        for runner, script, label in (("node", CC_GATE, "cc"), (sys.executable, CX_GATE, "cx")):
            run = subprocess.run([runner, str(script)], input=payload, text=True, capture_output=True)
            self.assertEqual(run.returncode, 0, label + "\n" + run.stderr)
            self.assertIn("decision", run.stdout, label)
            self.assert_names(run.stdout, "hand-ac1")

    def test_current_record_stays_and_filtered_ac_is_named(self):
        self.write_evidence(
            "collected_evidence:\n" + self.current_block()
            + "  - tool_use_id: hand-ac2\n    ac_id: AC2\n    result: pass\n"
            "    command: node test.js\n    timestamp: 2026-09-22T00:00:00Z\n"
        )
        records = self.gate.validate_evidence(self.sprint / "evidence.yaml")
        self.assertEqual([row["tool_use_id"] for row in records], ["current-ac1"])
        with self.assertRaises(self.gate.GateError) as caught:
            self.gate.validate_ac_mapping(
                self.sprint, ["AC1: kept", "AC2: dropped"], records,
                self.sprint / "reviews/implementation-review.md", "VERDICT: PASS\n", "a" * 40,
            )
        self.assertIn("hand-ac2", str(caught.exception))
        self.assertIn("AC2", str(caught.exception))
        self.assertIn("缺字段", str(caught.exception))
        self.assertNotIn("current-ac1", str(caught.exception))
        cc = subprocess.run(
            ["node", "-e", CC_AC_HARNESS, str(CC_GATE), str(self.sprint / "evidence.yaml"), str(self.sprint)],
            text=True, capture_output=True,
        )
        self.assertEqual(cc.returncode, 2, cc.stderr)
        self.assertIn("hand-ac2", cc.stderr)
        self.assertIn("缺字段", cc.stderr)
        self.assertNotIn("current-ac1", cc.stderr)
        self.write_evidence("collected_evidence:\n" + self.current_block(source="0" * 64, tool_id="stale-ac1"))
        with self.assertRaises(self.gate.GateError) as stale:
            self.gate.validate_evidence(self.sprint / "evidence.yaml")
        self.assertIn("过滤原因", str(stale.exception))
        self.assertIn("source_sha256", str(stale.exception))
        cc = self.cc_validate()
        self.assertEqual(cc.returncode, 2, cc.stderr)
        self.assertIn("过滤原因", cc.stderr)
        self.assertIn("source_sha256", cc.stderr)


if __name__ == "__main__":
    unittest.main()
