#!/usr/bin/env python3
"""Runtime behavior contract for the Athena v9.9.2 Codex package.

The suite executes the shipped hook scripts as subprocesses.  It deliberately
uses temporary projects so release validation never mutates package state or
leaves bytecode/cache files in the release tree.
"""

from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[2]
HOOKS = ROOT / "vibeCoding/codex/9.9.2/.codex/hooks"
FIXTURES = ROOT / "vibeCoding/scripts/fixtures/athena-9.9.2"
EVIDENCE_COLLECTOR = HOOKS / "evidence-collector.py"
SUBAGENT_TRACKER = HOOKS / "subagent-tracker.py"
DELIVERY_GATE = HOOKS / "delivery-gate.py"
SESSION_START = HOOKS / "session-start.py"
SPRINT_SLUG = "runtime-contract"
ROADMAP_SLUG = "runtime-roadmap"


def run_hook(script: Path, payload: dict[str, Any], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, str(script)],
        cwd=cwd,
        input=json.dumps(payload, ensure_ascii=False),
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
        env=env,
    )


def write_index(project: Path, *, stage: str = "ship", roadmap_slug: str = "") -> Path:
    ai_state = project / ".ai_state"
    ai_state.mkdir(parents=True, exist_ok=True)
    index = ai_state / "_index.md"
    index.write_text(
        "\n".join(
            [
                "---",
                "path: Feature",
                f"stage: {stage}",
                f'current_sprint_slug: "{SPRINT_SLUG}"',
                f'current_roadmap_slug: "{roadmap_slug}"',
                "plan_critique_disabled: false",
                "plan_critique_min_rounds: 1",
                "design_changed_after_impl: false",
                "skip_runtime_verify: false",
                "skip_architecture_check: false",
                'next_action: "must-not-change"',
                "---",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return index


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected JSON object in {path}")
    return value


def evidence_payload(response: Any, tool_use_id: str) -> dict[str, Any]:
    return {
        "hook_event_name": "PostToolUse",
        "tool_name": "Bash",
        "tool_use_id": tool_use_id,
        "tool_input": {"command": "python3 -m pytest"},
        "tool_response": response,
    }


EVIDENCE_CASES: tuple[tuple[str, str | None, dict[str, Any] | None, str, int | None], ...] = (
    ("integer_zero", "posttool-exit-zero.json", None, "pass", 0),
    ("integer_seven", "posttool-exit-seven.json", None, "fail", 7),
    ("string_response", "posttool-string.json", None, "unknown", None),
    ("string_exit_code", "posttool-string-exit-code.json", None, "unknown", None),
    (
        "boolean_exit_code",
        None,
        evidence_payload({"exit_code": True, "stdout": "looks successful"}, "fixture-bool"),
        "unknown",
        None,
    ),
    (
        "nested_exit_code",
        None,
        evidence_payload({"result": {"exit_code": 0}}, "fixture-nested"),
        "unknown",
        None,
    ),
)


class EvidenceCollectorTests(unittest.TestCase):
    maxDiff = None

    def assert_evidence_case(
        self,
        fixture_name: str | None,
        inline_payload: dict[str, Any] | None,
        expected_status: str,
        expected_exit_code: int | None,
    ) -> None:
        with tempfile.TemporaryDirectory(prefix="athena-992-evidence-") as raw_dir:
            project = Path(raw_dir)
            write_index(project, stage="impl")
            payload = load_json(FIXTURES / fixture_name) if fixture_name else copy.deepcopy(inline_payload)
            self.assertIsInstance(payload, dict)
            payload["cwd"] = str(project)

            result = run_hook(EVIDENCE_COLLECTOR, payload, project)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, "")

            sprint_dir = project / ".ai_state/sprints" / SPRINT_SLUG
            trace_rows = [
                json.loads(line)
                for line in (sprint_dir / "tool-trace.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(trace_rows), 1)
            self.assertEqual(trace_rows[0]["status"], expected_status)
            self.assertEqual(trace_rows[0]["exit_code"], expected_exit_code)

            evidence = (sprint_dir / "evidence.yaml").read_text(encoding="utf-8")
            matches = re.findall(r'(?m)^\s+result:\s+"([^"]+)"\s*$', evidence)
            self.assertEqual(len(matches), 1, evidence)
            actual = matches[0]
            if expected_status == "fail":
                self.assertTrue(actual.startswith("fail"), actual)
            else:
                self.assertEqual(actual, expected_status)
            if expected_status == "unknown":
                self.assertNotEqual(actual, "pass", "unknown evidence must never be upgraded to pass")


def make_evidence_test(
    fixture_name: str | None,
    inline_payload: dict[str, Any] | None,
    expected_status: str,
    expected_exit_code: int | None,
) -> Callable[[EvidenceCollectorTests], None]:
    def test(self: EvidenceCollectorTests) -> None:
        self.assert_evidence_case(
            fixture_name,
            inline_payload,
            expected_status,
            expected_exit_code,
        )

    return test


for _case_name, _fixture, _payload, _status, _exit_code in EVIDENCE_CASES:
    setattr(
        EvidenceCollectorTests,
        f"test_{_case_name}",
        make_evidence_test(_fixture, _payload, _status, _exit_code),
    )


class SubagentTrackerTests(unittest.TestCase):
    def test_start_stop_records_raw_schema_without_state_mutation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="athena-992-tracker-") as raw_dir:
            project = Path(raw_dir)
            index = write_index(project, stage="impl")
            index_before = index.read_bytes()

            base_payload: dict[str, Any] = {
                "cwd": str(project),
                "agent_id": "agent-runtime-1",
                "agent_type": "default",
                # These fields are intentionally hostile extras.  The raw event
                # ledger must neither persist them nor use them to update state.
                "task_name": "invented task",
                "role": "generator",
                "exit_code": 0,
                "exit": "success",
                "next_action": "invented next action",
            }
            for event in ("SubagentStart", "SubagentStop"):
                payload = {**base_payload, "hook_event_name": event}
                result = run_hook(SUBAGENT_TRACKER, payload, project)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertEqual(result.stderr, "")

            sprint_dir = project / ".ai_state/sprints" / SPRINT_SLUG
            rows = [
                json.loads(line)
                for line in (sprint_dir / "subagent-events.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            expected_fields = {
                "schema_version",
                "event",
                "agent_id",
                "agent_type",
                "sprint_slug",
                "timestamp",
            }
            self.assertEqual(len(rows), 2)
            self.assertEqual([row["event"] for row in rows], ["SubagentStart", "SubagentStop"])
            for row in rows:
                self.assertEqual(set(row), expected_fields)
                self.assertEqual(row["schema_version"], 1)
                self.assertEqual(row["agent_id"], "agent-runtime-1")
                self.assertEqual(row["agent_type"], "default")
                self.assertEqual(row["sprint_slug"], SPRINT_SLUG)
                parsed = dt.datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
                self.assertIsNotNone(parsed.tzinfo)

            self.assertFalse((sprint_dir / "subagent-assignments.jsonl").exists())
            self.assertEqual(index.read_bytes(), index_before)


def assignment_row(*, timestamp: str = "2026-07-10T00:00:01Z") -> dict[str, Any]:
    return {
        "schema_version": 1,
        "agent_id": "agent-g1",
        "task_name": "runtime generator",
        "role": "generator",
        "sprint_slug": SPRINT_SLUG,
        "timestamp": timestamp,
    }


def event_row(event: str, *, agent_id: str = "agent-g1", timestamp: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "event": event,
        "agent_id": agent_id,
        "agent_type": "default",
        "sprint_slug": SPRINT_SLUG,
        "timestamp": timestamp,
    }


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def git(project: Path, *args: str) -> str:
    run = subprocess.run(
        ["git", *args],
        cwd=project,
        check=False,
        capture_output=True,
        text=True,
    )
    if run.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {run.stderr or run.stdout}")
    return run.stdout.strip()


def bind_review(project: Path, sprint_dir: Path, review_path: Path) -> None:
    design_hash = hashlib.sha256((sprint_dir / "design.md").read_bytes()).hexdigest()
    commit = git(project, "rev-parse", "HEAD")
    manifest_paths = {
        "design.md": sprint_dir / "design.md",
        "checklist.yaml": sprint_dir / "checklist.yaml",
        "evidence.yaml": sprint_dir / "evidence.yaml",
        "runtime-verify.md": sprint_dir / "runtime-verify.md",
        "rework-notes.md": sprint_dir / "rework-notes.md",
        "cleanup-pass.md": sprint_dir / "cleanup-pass.md",
        "tdd-evidence.yaml": sprint_dir / "tdd-evidence.yaml",
        "architecture/ARCHITECTURE.md": project / ".ai_state/architecture/ARCHITECTURE.md",
        "architecture/athena-9.9.2.md": project / ".ai_state/architecture/athena-9.9.2.md",
    }
    manifest_lines = [
        "schema_version: 1",
        f'implementation_commit: "{commit}"',
        "files:",
    ]
    for label, file_path in manifest_paths.items():
        digest = hashlib.sha256(file_path.read_bytes()).hexdigest()
        manifest_lines.append(f'  "{label}": "{digest}"')
    manifest = sprint_dir / "review-manifest.yaml"
    manifest.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    manifest_hash = hashlib.sha256(manifest.read_bytes()).hexdigest()
    body = review_path.read_text(encoding="utf-8")
    body = re.sub(r"(?m)^Reviewed design sha256:.*\n?", "", body)
    body = re.sub(r"(?m)^Reviewed implementation commit:.*\n?", "", body).rstrip()
    body = re.sub(r"(?m)^Reviewed state manifest sha256:.*\n?", "", body).rstrip()
    review_path.write_text(
        body
        + f"\n\nReviewed design sha256: {design_hash}\n"
        + f"Reviewed implementation commit: {commit}\n"
        + f"Reviewed state manifest sha256: {manifest_hash}\n",
        encoding="utf-8",
    )


def build_complete_feature(project: Path) -> Path:
    write_index(project, roadmap_slug=ROADMAP_SLUG)
    sprint_dir = project / ".ai_state/sprints" / SPRINT_SLUG
    (sprint_dir / "reviews").mkdir(parents=True, exist_ok=True)
    roadmap_dir = project / ".ai_state/roadmap" / ROADMAP_SLUG
    roadmap_dir.mkdir(parents=True, exist_ok=True)
    (roadmap_dir / "items.yaml").write_text(
        "\n".join(
            [
                f'roadmap_slug: "{ROADMAP_SLUG}"',
                "total_items: 2",
                "items:",
                '  - slug: "runtime-one"',
                "    status: completed",
                '  - slug: "runtime-two"',
                "    status: completed",
                "",
            ]
        ),
        encoding="utf-8",
    )

    write_jsonl(sprint_dir / "subagent-assignments.jsonl", [assignment_row()])
    write_jsonl(
        sprint_dir / "subagent-events.jsonl",
        [
            event_row("SubagentStart", timestamp="2026-07-10T00:00:02Z"),
            event_row("SubagentStop", timestamp="2026-07-10T00:00:03Z"),
        ],
    )
    (sprint_dir / "checklist.yaml").write_text(
        "tasks:\n  - id: T1\n    status: completed\n",
        encoding="utf-8",
    )
    (sprint_dir / "evidence.yaml").write_text(
        "\n".join(
            [
                f'sprint_slug: "{SPRINT_SLUG}"',
                "collected_evidence:",
                '  - tool_use_id: "tool-pass-1"',
                '    tool: "Bash"',
                '    ac_id: AC1',
                '    file: ""',
                '    kind: "test"',
                '    command: "python3 -m pytest"',
                '    result: "pass"',
                '    source: command',
                '    command_or_artifact: "python3 -m pytest"',
                '    observed_at: "2026-07-13T08:00:00Z"',
                '    summary: "pytest completed with exit 0"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    (sprint_dir / "design.md").write_text(
        "# Design\n\n## Acceptance Criteria\n\n- [ ] AC1: observable outcome X\n\n## Round 1 Critic Findings\n\n- Contract accepted.\n",
        encoding="utf-8",
    )
    (sprint_dir / "reviews/pass1.md").write_text(
        "# Review\n\n## Spec Compliance\n\n- PASS\n\n"
        "## Evidence Cross-Check\n\n- PASS\n\nVERDICT: PASS\n",
        encoding="utf-8",
    )
    (sprint_dir / "runtime-verify.md").write_text("## Test Scenarios\n\nPASS\n", encoding="utf-8")
    (sprint_dir / "rework-notes.md").write_text("# Rework\n\nPASS\n", encoding="utf-8")
    (sprint_dir / "cleanup-pass.md").write_text("# Cleanup\n\nPASS\n", encoding="utf-8")
    architecture = project / ".ai_state/architecture"
    architecture.mkdir(parents=True, exist_ok=True)
    (architecture / "ARCHITECTURE.md").write_text("# Architecture\n", encoding="utf-8")
    (architecture / "athena-9.9.2.md").write_text("# Athena 9.9.2\n", encoding="utf-8")
    (project / "implementation.txt").write_text("reviewed implementation\n", encoding="utf-8")
    git(project, "init", "-q")
    git(project, "config", "user.email", "athena@example.invalid")
    git(project, "config", "user.name", "Athena Runtime Contract")
    git(project, "add", ".")
    git(project, "commit", "-qm", "reviewed implementation")
    implementation_commit = git(project, "rev-parse", "HEAD")
    output_artifact = sprint_dir / "evidence/pytest.txt"
    output_artifact.parent.mkdir(parents=True, exist_ok=True)
    output_artifact.write_text(
        "command: python3 -m pytest\nexit_code: 0\nsummary: pytest completed with exit 0\n",
        encoding="utf-8",
    )
    output_hash = hashlib.sha256(output_artifact.read_bytes()).hexdigest()
    (sprint_dir / "evidence.yaml").write_text(
        "\n".join(
            [
                f'sprint_slug: "{SPRINT_SLUG}"',
                "collected_evidence:",
                '  - tool_use_id: "tool-pass-1"',
                '    ac_id: AC1',
                '    result: "pass"',
                '    source: command',
                '    command_or_artifact: "python3 -m pytest"',
                '    observed_at: "2026-07-13T08:00:00Z"',
                '    summary: "pytest completed with exit 0"',
                '    exit_code: 0',
                '    output_artifact: "evidence/pytest.txt"',
                f'    artifact_sha256: "{output_hash}"',
                f'    implementation_commit: "{implementation_commit}"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    (sprint_dir / "tdd-evidence.yaml").write_text(
        "schema_version: 1\nrecords:\n"
        "  - test_file: vibeCoding/scripts/test-athena-9.9.2-runtime.py\n"
        "    red_command: python3 vibeCoding/scripts/test-athena-9.9.2-runtime.py\n"
        "    red_summary: fail-open negative cases failed before implementation\n"
        "    red_observed_at: 2026-07-13T07:00:00Z\n"
        "    implementation_files: [delivery-gate.py]\n"
        "    green_command: python3 vibeCoding/scripts/test-athena-9.9.2-runtime.py\n"
        "    green_summary: runtime contract passed\n"
        "    green_observed_at: 2026-07-13T08:00:00Z\n",
        encoding="utf-8",
    )
    bind_review(project, sprint_dir, sprint_dir / "reviews/pass1.md")
    return sprint_dir


def replace_text(path: Path, old: str, new: str) -> None:
    content = path.read_text(encoding="utf-8")
    if old not in content:
        raise AssertionError(f"mutation source not found in {path}: {old!r}")
    path.write_text(content.replace(old, new, 1), encoding="utf-8")


def write_user_authorization(
    sprint_dir: Path,
    *,
    reason: str = "user-approved temporary impl entry",
    authorized_by: str = "user:release-owner",
    expiry: str = "2099-01-01T00:00:00Z",
) -> None:
    target = sprint_dir / "user-authorizations/release-owner.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "schema_version: 1\n"
        "kind: spec_gate_exception_authorization\n"
        f'sprint_slug: "{SPRINT_SLUG}"\n'
        'path: "Feature"\n'
        f'reason: "{reason}"\n'
        "decision: approve\n"
        "authorization_source: user_prompt\n"
        f'authorized_by: "{authorized_by}"\n'
        'authorized_at: "2026-07-13T08:00:00Z"\n'
        f'expiry: "{expiry}"\n'
        'removal_condition: "acceptance criteria restored"\n',
        encoding="utf-8",
    )


def mutate_gate_case(case_name: str, project: Path, sprint_dir: Path) -> None:
    assignments = sprint_dir / "subagent-assignments.jsonl"
    events = sprint_dir / "subagent-events.jsonl"
    checklist = sprint_dir / "checklist.yaml"
    evidence = sprint_dir / "evidence.yaml"
    review = sprint_dir / "reviews/pass1.md"
    index = project / ".ai_state/_index.md"
    roadmap_items = project / ".ai_state/roadmap" / ROADMAP_SLUG / "items.yaml"

    if case_name == "missing-assignment":
        assignments.unlink()
    elif case_name == "missing-generator-stop":
        write_jsonl(events, [event_row("SubagentStart", timestamp="2026-07-10T00:00:02Z")])
    elif case_name == "agent-id-mismatch":
        write_jsonl(
            events,
            [
                event_row("SubagentStart", agent_id="agent-other", timestamp="2026-07-10T00:00:02Z"),
                event_row("SubagentStop", agent_id="agent-other", timestamp="2026-07-10T00:00:03Z"),
            ],
        )
    elif case_name == "checklist-incomplete":
        replace_text(checklist, "status: completed", "status: pending")
    elif case_name == "evidence-empty":
        evidence.write_text(f'sprint_slug: "{SPRINT_SLUG}"\ncollected_evidence:\n', encoding="utf-8")
    elif case_name == "evidence-unknown-only":
        replace_text(evidence, 'result: "pass"', 'result: "unknown"')
    elif case_name == "evidence-fail":
        replace_text(evidence, 'result: "pass"', 'result: "fail (exit 7)"')
    elif case_name == "review-without-final-pass":
        replace_text(review, "VERDICT: PASS", "VERDICT: REWORK")
    elif case_name == "latest-review-rework":
        (sprint_dir / "reviews/pass2.md").write_text(
            "# Review Pass 2\n\n## Spec Compliance\n\n- REWORK\n\nVERDICT: REWORK\n",
            encoding="utf-8",
        )
    elif case_name == "malformed-jsonl":
        assignments.write_text('{"schema_version":1,not-json}\n', encoding="utf-8")
    elif case_name == "ambiguous-start":
        write_jsonl(
            events,
            [
                event_row("SubagentStart", timestamp="2026-07-10T00:00:02Z"),
                event_row("SubagentStart", timestamp="2026-07-10T00:00:02.500000Z"),
                event_row("SubagentStop", timestamp="2026-07-10T00:00:03Z"),
            ],
        )
    elif case_name == "unbound-start":
        rows = [json.loads(line) for line in events.read_text(encoding="utf-8").splitlines()]
        rows.append(event_row("SubagentStart", agent_id="agent-unbound", timestamp="2026-07-10T00:00:04Z"))
        write_jsonl(events, rows)
    elif case_name == "isolated-stop":
        write_jsonl(events, [event_row("SubagentStop", timestamp="2026-07-10T00:00:03Z")])
    elif case_name == "orphan-stop":
        rows = [json.loads(line) for line in events.read_text(encoding="utf-8").splitlines()]
        rows.append(event_row("SubagentStop", agent_id="agent-orphan", timestamp="2026-07-10T00:00:04Z"))
        write_jsonl(events, rows)
    elif case_name == "stop-before-assignment":
        write_jsonl(assignments, [assignment_row(timestamp="2026-07-10T00:00:04Z")])
    elif case_name == "roadmap-pending":
        replace_text(roadmap_items, "status: completed", "status: pending")
    elif case_name == "roadmap-in-progress":
        replace_text(roadmap_items, "status: completed", "status: in_progress")
    elif case_name == "roadmap-malformed":
        roadmap_items.write_text(
            f'roadmap_slug: "{ROADMAP_SLUG}"\ntotal_items: 2\nitems:\n  - slug: "broken"\n',
            encoding="utf-8",
        )
    elif case_name == "missing-index":
        index.unlink()
    elif case_name == "malformed-index":
        index.write_text("---\npath Feature\nstage: ship\n---\n", encoding="utf-8")
    elif case_name == "unknown-stage":
        replace_text(index, "stage: ship", "stage: unknowable")
    elif case_name == "spec-missing-criteria":
        (sprint_dir / "design.md").write_text(
            "# Design\n\n## Round 1 Critic Findings\n\n- Contract accepted.\n",
            encoding="utf-8",
        )
    elif case_name == "spec-placeholder-criteria":
        # design §4.3: semantic placeholder rejection (prefix/substring).
        (sprint_dir / "design.md").write_text(
            "# Design\n\n## Acceptance Criteria\n\n- [ ] TODO: define later\n"
            "- [ ] login works correctly.\n- [ ] 待定\n\n"
            "## Round 1 Critic Findings\n\n- Contract accepted.\n",
            encoding="utf-8",
        )
    elif case_name == "spec-unmapped-ac-label":
        # design §4.4(2): AC2 has no checklist/evidence mapping.
        (sprint_dir / "design.md").write_text(
            "# Design\n\n## Acceptance Criteria\n\n- [ ] AC1: observable outcome X\n"
            "- [ ] AC2: observable outcome Y\n\n"
            "## Round 1 Critic Findings\n\n- Contract accepted.\n",
            encoding="utf-8",
        )
    elif case_name == "spec-ac-unknown-evidence":
        # AC1 is present but its own evidence is unknown. An unrelated global
        # PASS must not make the per-criterion mapping pass.
        evidence.write_text(
            "\n".join(
                [
                    f'sprint_slug: "{SPRINT_SLUG}"',
                    "collected_evidence:",
                    '  - tool_use_id: "tool-unknown-ac1"',
                    '    result: "unknown"',
                    '    criteria: [AC1]',
                    '  - tool_use_id: "tool-unrelated-pass"',
                    '    result: "pass"',
                    '    criteria: []',
                    "",
                ]
            ),
            encoding="utf-8",
        )
    elif case_name == "spec-ac-checklist-only":
        # A checklist mention is implementation planning, not acceptance
        # evidence. AC2 has no passing evidence or accepted review result.
        (sprint_dir / "design.md").write_text(
            "# Design\n\n## Acceptance Criteria\n\n- [ ] AC1: observable outcome X\n"
            "- [ ] AC2: observable outcome Y\n\n"
            "## Round 1 Critic Findings\n\n- Contract accepted.\n",
            encoding="utf-8",
        )
        checklist.write_text(
            "tasks:\n  - id: T1\n    title: implement AC1 and AC2\n    status: completed\n",
            encoding="utf-8",
        )
    elif case_name == "spec-ac-missing-artifact":
        evidence.write_text(
            "collected_evidence:\n"
            "  - tool_use_id: ac1-missing-artifact\n"
            "    ac_id: AC1\n"
            "    result: pass\n"
            "    source: artifact\n"
            "    command_or_artifact: missing/runtime-report.md\n"
            "    observed_at: 2026-07-13T08:00:00Z\n"
            "    summary: claimed artifact coverage\n",
            encoding="utf-8",
        )
    elif case_name == "spec-ac-stale-review":
        pass2 = sprint_dir / "reviews/pass2.md"
        pass2.write_text(
            "# Review Pass 2\n\n## Spec Compliance\n\n"
            "| AC | Result |\n|---|---|\n| AC1 | SATISFIED |\n\n"
            "## Evidence Cross-Check\n\nPASS\n\nVERDICT: PASS\n",
            encoding="utf-8",
        )
        bind_review(project, sprint_dir, pass2)
        evidence.write_text(
            "collected_evidence:\n"
            "  - tool_use_id: ac1-stale-review\n"
            "    ac_id: AC1\n"
            "    result: pass\n"
            "    source: review\n"
            "    command_or_artifact: reviews/pass1.md\n"
            "    observed_at: 2026-07-13T08:00:00Z\n"
            "    summary: stale review reference\n",
            encoding="utf-8",
        )
    elif case_name == "spec-exception-unauthorized":
        # design §4.5: an exception naming the sprint without reason/authorizer/
        # expiry must fail closed.
        replace_text(
            index,
            "design_changed_after_impl: false",
            f'design_changed_after_impl: false\nspec_gate_exception: "{SPRINT_SLUG}"',
        )
        (sprint_dir / "design.md").write_text(
            "# Design\n\n## Round 1 Critic Findings\n\n- Contract accepted.\n",
            encoding="utf-8",
        )
    elif case_name == "spec-exception-unstructured-authorizer":
        replace_text(index, "stage: ship", "stage: impl")
        replace_text(
            index,
            "design_changed_after_impl: false",
            "design_changed_after_impl: false\n"
            f'spec_gate_exception: "{SPRINT_SLUG}"\n'
            'spec_gate_exception_reason: "dogfood exception"\n'
            'spec_gate_exception_path: "Feature"\n'
            'spec_gate_exception_authorized_by: "someone said yes"\n'
            'spec_gate_exception_authorized_at: "2026-07-13T08:00:00Z"\n'
            'spec_gate_exception_expiry: "2099-01-01T00:00:00Z"\n'
            'spec_gate_exception_removal_condition: "acceptance criteria restored"\n'
            'spec_gate_exception_emergency_hotfix: false\n'
            'spec_gate_exception_authorization_ref: "user-authorizations/release-owner.yaml"',
        )
        (sprint_dir / "design.md").write_text(
            "# Design\n\n## Round 1 Critic Findings\n\n- Contract accepted.\n",
            encoding="utf-8",
        )
    elif case_name == "spec-exception-at-ship":
        replace_text(
            index,
            "design_changed_after_impl: false",
            "design_changed_after_impl: false\n"
            f'spec_gate_exception: "{SPRINT_SLUG}"\n'
            'spec_gate_exception_path: "Feature"\n'
            'spec_gate_exception_reason: "user-approved temporary impl entry"\n'
            'spec_gate_exception_authorized_by: "user:release-owner"\n'
            'spec_gate_exception_authorized_at: "2026-07-13T08:00:00Z"\n'
            'spec_gate_exception_expiry: "2099-01-01T00:00:00Z"\n'
            'spec_gate_exception_removal_condition: "acceptance criteria restored"\n'
            'spec_gate_exception_emergency_hotfix: false\n'
            'spec_gate_exception_authorization_ref: "user-authorizations/release-owner.yaml"',
        )
        write_user_authorization(sprint_dir)
        (sprint_dir / "design.md").write_text(
            "# Design\n\n## Round 1 Critic Findings\n\n- Contract accepted.\n",
            encoding="utf-8",
        )
    else:
        raise AssertionError(f"no mutation defined for gate case {case_name!r}")


GATE_MANIFEST = load_json(FIXTURES / "gate-cases.json")
NEGATIVE_GATE_CASES = tuple(GATE_MANIFEST.get("negative", []))
EXPECTED_NEGATIVE_GATE_CASES = {
    "missing-assignment",
    "missing-generator-stop",
    "agent-id-mismatch",
    "checklist-incomplete",
    "evidence-empty",
    "evidence-unknown-only",
    "evidence-fail",
    "review-without-final-pass",
    "latest-review-rework",
    "malformed-jsonl",
    "ambiguous-start",
    "unbound-start",
    "isolated-stop",
    "orphan-stop",
    "stop-before-assignment",
    "roadmap-pending",
    "roadmap-in-progress",
    "roadmap-malformed",
    "missing-index",
    "malformed-index",
    "unknown-stage",
    "spec-missing-criteria",
    "spec-placeholder-criteria",
    "spec-unmapped-ac-label",
    "spec-ac-unknown-evidence",
    "spec-ac-checklist-only",
    "spec-ac-missing-artifact",
    "spec-ac-stale-review",
    "spec-exception-unauthorized",
    "spec-exception-unstructured-authorizer",
    "spec-exception-at-ship",
}


class DeliveryGateTests(unittest.TestCase):
    maxDiff = None

    def run_gate(self, project: Path) -> subprocess.CompletedProcess[str]:
        return run_hook(
            DELIVERY_GATE,
            {"hook_event_name": "Stop", "cwd": str(project)},
            project,
        )

    def test_complete_chain_passes(self) -> None:
        self.assertEqual(GATE_MANIFEST.get("schema_version"), 1)
        self.assertEqual(GATE_MANIFEST.get("positive"), "complete-chain")
        self.assertEqual(set(NEGATIVE_GATE_CASES), EXPECTED_NEGATIVE_GATE_CASES)
        self.assertEqual(len(NEGATIVE_GATE_CASES), 31)
        with tempfile.TemporaryDirectory(prefix="athena-992-gate-pass-") as raw_dir:
            project = Path(raw_dir)
            sprint_dir = build_complete_feature(project)
            replace_text(sprint_dir / "reviews/pass1.md", "VERDICT: PASS", "VERDICT: REWORK")
            (sprint_dir / "reviews/pass2.md").write_text(
                "# Review Pass 2\n\n## Spec Compliance\n\n- PASS\n\n"
                "## Evidence Cross-Check\n\n- PASS\n\nVERDICT: PASS\n",
                encoding="utf-8",
            )
            bind_review(project, sprint_dir, sprint_dir / "reviews/pass2.md")
            result = self.run_gate(project)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertEqual(result.stderr, "")

    def assert_gate_case_blocks(self, case_name: str) -> None:
        with tempfile.TemporaryDirectory(prefix=f"athena-992-gate-{case_name}-") as raw_dir:
            project = Path(raw_dir)
            sprint_dir = build_complete_feature(project)
            mutate_gate_case(case_name, project, sprint_dir)
            result = self.run_gate(project)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("[delivery-gate]", result.stderr)
            try:
                response = json.loads(result.stdout)
            except json.JSONDecodeError as exc:
                self.fail(f"{case_name} did not return a block decision: {exc}: {result.stdout!r}")
            self.assertEqual(response.get("decision"), "block", response)
            self.assertIsInstance(response.get("reason"), str)
            self.assertTrue(response["reason"].strip())

    def test_evaluator_bold_chinese_verdict_template_passes(self) -> None:
        # Regression: evaluator.toml emits "**判定**: PASS"; the gate must parse it.
        # Before the fix, strip("*") left "判定**:" and the VERDICT-only regex missed
        # it, so a legitimate PASS was blocked as "no explicit VERDICT line".
        with tempfile.TemporaryDirectory(prefix="athena-992-gate-bold-") as raw_dir:
            project = Path(raw_dir)
            sprint_dir = build_complete_feature(project)
            (sprint_dir / "reviews/pass1.md").write_text(
                "# Review\n\n## Spec Compliance\n\n- PASS\n\n"
                "## Evidence Cross-Check\n\n- PASS\n\n"
                "## VERDICT (evaluator, sprint)\n\n**判定**: PASS\n",
                encoding="utf-8",
            )
            bind_review(project, sprint_dir, sprint_dir / "reviews/pass1.md")
            result = self.run_gate(project)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertEqual(result.stderr, "")

    def test_evaluator_bold_verdict_rework_blocks(self) -> None:
        with tempfile.TemporaryDirectory(prefix="athena-992-gate-bold-rw-") as raw_dir:
            project = Path(raw_dir)
            sprint_dir = build_complete_feature(project)
            (sprint_dir / "reviews/pass1.md").write_text(
                "# Review\n\n## Spec Compliance\n\n- REWORK\n\n**判定**: REWORK\n",
                encoding="utf-8",
            )
            result = self.run_gate(project)
            response = json.loads(result.stdout)
            self.assertEqual(response.get("decision"), "block", response)

    def test_refactor_blocks_when_git_change_probes_are_unavailable(self) -> None:
        # Review freshness is fail-closed when Git provenance is unavailable.
        with tempfile.TemporaryDirectory(prefix="athena-992-gate-git-fail-") as raw_dir:
            project = Path(raw_dir)
            sprint_dir = build_complete_feature(project)
            replace_text(project / ".ai_state/_index.md", "path: Feature", "path: Refactor")
            replace_text(
                sprint_dir / "design.md",
                "- Contract accepted.",
                "- Contract accepted.\n\n## Round 2 Critic Findings\n\n- Contract rechecked.",
            )
            replace_text(
                sprint_dir / "reviews/pass1.md",
                "VERDICT: PASS",
                "## Evidence Cross-Check\n\n- PASS\n\nVERDICT: PASS",
            )
            (sprint_dir / "runtime-verify.md").write_text("## 测试场景\n\n- PASS\n", encoding="utf-8")
            (sprint_dir / "cleanup-pass.md").write_text("# Cleanup\n\nPASS\n", encoding="utf-8")
            bind_review(project, sprint_dir, sprint_dir / "reviews/pass1.md")
            shutil.rmtree(project / ".git")
            result = self.run_gate(project)
            response = json.loads(result.stdout)
            self.assertEqual(response.get("decision"), "block", response)
            self.assertRegex(response.get("reason", ""), r"review freshness|Git|git")

    def test_spec_gate_accepts_packaged_chinese_heading(self) -> None:
        # P0-3 regression: the packaged design template emits "## 验收标准
        # (acceptance criteria)"; the gate must accept it (no \b after CJK).
        with tempfile.TemporaryDirectory(prefix="athena-992-gate-zh-") as raw_dir:
            project = Path(raw_dir)
            sprint_dir = build_complete_feature(project)
            (sprint_dir / "design.md").write_text(
                "# Design\n\n## 验收标准 (acceptance criteria)\n\n"
                "- [ ] AC1: 用户以输入 X 得到可观测输出 Y\n\n"
                "## Round 1 Critic Findings\n\n- Contract accepted.\n",
                encoding="utf-8",
            )
            bind_review(project, sprint_dir, sprint_dir / "reviews/pass1.md")
            result = self.run_gate(project)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "", result.stdout)

    def test_impl_entry_blocks_feature_without_criteria(self) -> None:
        # design §4.2 primary gate: Feature+ cannot sit in impl without
        # machine-recognizable acceptance criteria.
        with tempfile.TemporaryDirectory(prefix="athena-992-impl-entry-") as raw_dir:
            project = Path(raw_dir)
            sprint_dir = build_complete_feature(project)
            replace_text(project / ".ai_state/_index.md", "stage: ship", "stage: impl")
            (sprint_dir / "design.md").write_text(
                "# Design\n\n## Round 1 Critic Findings\n\n- Contract accepted.\n",
                encoding="utf-8",
            )
            result = self.run_gate(project)
            self.assertEqual(result.returncode, 0, result.stderr)
            response = json.loads(result.stdout)
            self.assertEqual(response.get("decision"), "block", response)
            self.assertIn("spec-gate", response.get("reason", ""))

    def test_impl_entry_passes_with_criteria(self) -> None:
        with tempfile.TemporaryDirectory(prefix="athena-992-impl-ok-") as raw_dir:
            project = Path(raw_dir)
            build_complete_feature(project)
            replace_text(project / ".ai_state/_index.md", "stage: ship", "stage: impl")
            result = self.run_gate(project)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "", result.stdout)

    def test_authorized_unexpired_exception_allows_impl_entry_only(self) -> None:
        # design §4.5: a structured, user-authorized exception may unblock the
        # temporary impl entry, but it must be cleared before ship.
        with tempfile.TemporaryDirectory(prefix="athena-992-exception-") as raw_dir:
            project = Path(raw_dir)
            sprint_dir = build_complete_feature(project)
            replace_text(project / ".ai_state/_index.md", "stage: ship", "stage: impl")
            replace_text(
                project / ".ai_state/_index.md",
                "design_changed_after_impl: false",
                "design_changed_after_impl: false\n"
                f'spec_gate_exception: "{SPRINT_SLUG}"\n'
                'spec_gate_exception_path: "Feature"\n'
                'spec_gate_exception_reason: "user-approved dogfood exception"\n'
                'spec_gate_exception_authorized_by: "user:release-owner"\n'
                'spec_gate_exception_authorized_at: "2026-07-13T08:00:00Z"\n'
                'spec_gate_exception_expiry: "2099-01-01T00:00:00Z"\n'
                'spec_gate_exception_removal_condition: "acceptance criteria restored"\n'
                'spec_gate_exception_emergency_hotfix: false\n'
                'spec_gate_exception_authorization_ref: "user-authorizations/release-owner.yaml"',
            )
            write_user_authorization(
                sprint_dir,
                reason="user-approved dogfood exception",
                authorized_by="user:release-owner",
                expiry="2099-01-01T00:00:00Z",
            )
            (sprint_dir / "design.md").write_text(
                "# Design\n\n## Round 1 Critic Findings\n\n- Contract accepted.\n",
                encoding="utf-8",
            )
            result = self.run_gate(project)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "", result.stdout)

    def test_explicit_review_acceptance_can_cover_an_ac(self) -> None:
        # Per-AC coverage may come from explicit passing evidence OR an
        # accepted final review result. The generic final PASS alone is not
        # enough; the review must name AC1 and mark it SATISFIED.
        with tempfile.TemporaryDirectory(prefix="athena-992-review-ac-") as raw_dir:
            project = Path(raw_dir)
            sprint_dir = build_complete_feature(project)
            (sprint_dir / "evidence.yaml").write_text(
                "collected_evidence:\n"
                "  - tool_use_id: ac1-review\n"
                "    ac_id: AC1\n"
                "    result: pass\n"
                "    source: review\n"
                "    command_or_artifact: reviews/pass1.md\n"
                "    observed_at: 2026-07-13T08:00:00Z\n"
                "    summary: final review explicitly accepted AC1\n",
                encoding="utf-8",
            )
            (sprint_dir / "reviews/pass1.md").write_text(
                "# Review\n\n## Spec Compliance\n\n"
                "| AC | Result |\n|---|---|\n| AC1 | SATISFIED |\n\n"
                "## Evidence Cross-Check\n\nPASS\n\n"
                "VERDICT: PASS\n",
                encoding="utf-8",
            )
            bind_review(project, sprint_dir, sprint_dir / "reviews/pass1.md")
            result = self.run_gate(project)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "", result.stdout)

    def test_review_binding_allows_state_only_post_review_change(self) -> None:
        with tempfile.TemporaryDirectory(prefix="athena-992-state-only-") as raw_dir:
            project = Path(raw_dir)
            sprint_dir = build_complete_feature(project)
            (sprint_dir / "session-log.md").write_text("# Session\n", encoding="utf-8")
            result = self.run_gate(project)
            self.assertEqual(result.stdout, "", result.stdout)

    def test_review_binding_blocks_unstaged_implementation_drift(self) -> None:
        with tempfile.TemporaryDirectory(prefix="athena-992-unstaged-") as raw_dir:
            project = Path(raw_dir)
            build_complete_feature(project)
            (project / "implementation.txt").write_text("changed after review\n", encoding="utf-8")
            self.assertIn("unreviewed implementation drift", self.run_gate(project).stdout)

    def test_review_binding_blocks_staged_implementation_drift(self) -> None:
        with tempfile.TemporaryDirectory(prefix="athena-992-staged-") as raw_dir:
            project = Path(raw_dir)
            build_complete_feature(project)
            (project / "staged.txt").write_text("staged after review\n", encoding="utf-8")
            git(project, "add", "staged.txt")
            self.assertIn("unreviewed implementation drift", self.run_gate(project).stdout)

    def test_review_binding_blocks_untracked_implementation_drift(self) -> None:
        with tempfile.TemporaryDirectory(prefix="athena-992-untracked-") as raw_dir:
            project = Path(raw_dir)
            build_complete_feature(project)
            (project / "untracked.txt").write_text("untracked after review\n", encoding="utf-8")
            self.assertIn("unreviewed implementation drift", self.run_gate(project).stdout)

    def test_review_binding_blocks_committed_implementation_drift(self) -> None:
        with tempfile.TemporaryDirectory(prefix="athena-992-committed-") as raw_dir:
            project = Path(raw_dir)
            build_complete_feature(project)
            (project / "committed.txt").write_text("committed after review\n", encoding="utf-8")
            git(project, "add", "committed.txt")
            git(project, "commit", "-qm", "post-review implementation drift")
            self.assertIn("unreviewed implementation drift", self.run_gate(project).stdout)

    def test_non_athena_directory_passes_silently(self) -> None:
        with tempfile.TemporaryDirectory(prefix="athena-992-non-athena-") as raw_dir:
            project = Path(raw_dir)
            result = self.run_gate(project)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertEqual(result.stderr, "")


class SessionStartMemoryTests(unittest.TestCase):
    def run_session_start(self, project: Path) -> subprocess.CompletedProcess[str]:
        return run_hook(
            SESSION_START,
            {"hook_event_name": "SessionStart", "cwd": str(project)},
            project,
        )

    def write_memory_index(self, project: Path, latest_review: str, latest_design: str) -> None:
        ai = project / ".ai_state"
        ai.mkdir(parents=True, exist_ok=True)
        (ai / "_index.md").write_text(
            "---\n"
            'version: "9.9.2"\n'
            'path: "System"\n'
            'stage: "review"\n'
            f'current_sprint_slug: "{SPRINT_SLUG}"\n'
            'next_action: "review"\n'
            "pointers:\n"
            f'  latest_design: "{latest_design}"\n'
            f'  latest_review: "{latest_review}"\n'
            '  latest_cleanup: ""\n'
            '  latest_requirement: ""\n'
            "route_history: []\n"
            "---\n",
            encoding="utf-8",
        )

    def test_routes_existing_authoritative_pointers(self) -> None:
        with tempfile.TemporaryDirectory(prefix="athena-992-session-memory-") as raw_dir:
            project = Path(raw_dir)
            design = project / ".ai_state/sprints" / SPRINT_SLUG / "design.md"
            review = project / ".ai_state/sprints" / SPRINT_SLUG / "reviews/pass2.md"
            design.parent.mkdir(parents=True, exist_ok=True)
            review.parent.mkdir(parents=True, exist_ok=True)
            design.write_text("# Design\n", encoding="utf-8")
            review.write_text("## Spec Compliance\n\nVERDICT: PASS\n", encoding="utf-8")
            self.write_memory_index(
                project,
                f"sprints/{SPRINT_SLUG}/reviews/pass2.md",
                f"sprints/{SPRINT_SLUG}/design.md",
            )
            result = self.run_session_start(project)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Tier1 working memory", result.stdout)
            self.assertIn("Tier2 persistent memory", result.stdout)
            self.assertIn("_index.md retrieval router", result.stdout)
            self.assertIn(f"sprints/{SPRINT_SLUG}/design.md", result.stdout)
            self.assertNotIn("missing authoritative pointer", result.stdout)

    def test_warns_on_missing_authoritative_pointer(self) -> None:
        with tempfile.TemporaryDirectory(prefix="athena-992-session-missing-") as raw_dir:
            project = Path(raw_dir)
            self.write_memory_index(
                project,
                f"sprints/{SPRINT_SLUG}/reviews/pass2.md",
                f"sprints/{SPRINT_SLUG}/missing-design.md",
            )
            result = self.run_session_start(project)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("missing authoritative pointer", result.stdout)

    def test_warns_on_stale_latest_review_pointer(self) -> None:
        with tempfile.TemporaryDirectory(prefix="athena-992-session-stale-") as raw_dir:
            project = Path(raw_dir)
            reviews = project / ".ai_state/sprints" / SPRINT_SLUG / "reviews"
            reviews.mkdir(parents=True, exist_ok=True)
            (reviews / "pass1.md").write_text("VERDICT: PASS\n", encoding="utf-8")
            (reviews / "pass2.md").write_text("VERDICT: PASS\n", encoding="utf-8")
            design = project / ".ai_state/sprints" / SPRINT_SLUG / "design.md"
            design.write_text("# Design\n", encoding="utf-8")
            self.write_memory_index(
                project,
                f"sprints/{SPRINT_SLUG}/reviews/pass1.md",
                f"sprints/{SPRINT_SLUG}/design.md",
            )
            result = self.run_session_start(project)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("stale authoritative pointer", result.stdout)

    def test_warns_on_escaping_pointer_and_history_overflow(self) -> None:
        with tempfile.TemporaryDirectory(prefix="athena-992-session-bounds-") as raw_dir:
            project = Path(raw_dir)
            self.write_memory_index(project, "../../outside.md", "")
            replace_text(
                project / ".ai_state/_index.md",
                "route_history: []",
                "route_history: [1,2,3,4,5,6,7,8,9,10,11]",
            )
            result = self.run_session_start(project)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("escaping authoritative pointer", result.stdout)
            self.assertIn("route_history overflow", result.stdout)


def make_gate_test(case_name: str) -> Callable[[DeliveryGateTests], None]:
    def test(self: DeliveryGateTests) -> None:
        self.assert_gate_case_blocks(case_name)

    return test


for _gate_case in NEGATIVE_GATE_CASES:
    setattr(
        DeliveryGateTests,
        f"test_negative_{_gate_case.replace('-', '_')}",
        make_gate_test(_gate_case),
    )


if __name__ == "__main__":
    unittest.main(verbosity=2)
