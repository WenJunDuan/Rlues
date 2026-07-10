#!/usr/bin/env python3
"""Runtime behavior contract for the Athena v9.9.1 Codex package.

The suite executes the shipped hook scripts as subprocesses.  It deliberately
uses temporary projects so release validation never mutates package state or
leaves bytecode/cache files in the release tree.
"""

from __future__ import annotations

import copy
import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[2]
HOOKS = ROOT / "vibeCoding/codex/9.9.1/.codex/hooks"
FIXTURES = ROOT / "vibeCoding/scripts/fixtures/athena-9.9.1"
EVIDENCE_COLLECTOR = HOOKS / "evidence-collector.py"
SUBAGENT_TRACKER = HOOKS / "subagent-tracker.py"
DELIVERY_GATE = HOOKS / "delivery-gate.py"
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
        with tempfile.TemporaryDirectory(prefix="athena-991-evidence-") as raw_dir:
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
        with tempfile.TemporaryDirectory(prefix="athena-991-tracker-") as raw_dir:
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
                '    file: ""',
                '    kind: "test"',
                '    command: "python3 -m pytest"',
                '    result: "pass"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    (sprint_dir / "design.md").write_text(
        "# Design\n\n## Round 1 Critic Findings\n\n- Contract accepted.\n",
        encoding="utf-8",
    )
    (sprint_dir / "reviews/pass1.md").write_text(
        "# Review\n\n## Spec Compliance\n\n- PASS\n\nVERDICT: PASS\n",
        encoding="utf-8",
    )
    return sprint_dir


def replace_text(path: Path, old: str, new: str) -> None:
    content = path.read_text(encoding="utf-8")
    if old not in content:
        raise AssertionError(f"mutation source not found in {path}: {old!r}")
    path.write_text(content.replace(old, new, 1), encoding="utf-8")


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
        self.assertEqual(len(NEGATIVE_GATE_CASES), 21)
        with tempfile.TemporaryDirectory(prefix="athena-991-gate-pass-") as raw_dir:
            project = Path(raw_dir)
            sprint_dir = build_complete_feature(project)
            replace_text(sprint_dir / "reviews/pass1.md", "VERDICT: PASS", "VERDICT: REWORK")
            (sprint_dir / "reviews/pass2.md").write_text(
                "# Review Pass 2\n\n## Spec Compliance\n\n- PASS\n\nVERDICT: PASS\n",
                encoding="utf-8",
            )
            result = self.run_gate(project)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertEqual(result.stderr, "")

    def assert_gate_case_blocks(self, case_name: str) -> None:
        with tempfile.TemporaryDirectory(prefix=f"athena-991-gate-{case_name}-") as raw_dir:
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

    def test_non_athena_directory_passes_silently(self) -> None:
        with tempfile.TemporaryDirectory(prefix="athena-991-non-athena-") as raw_dir:
            project = Path(raw_dir)
            result = self.run_gate(project)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertEqual(result.stderr, "")


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
