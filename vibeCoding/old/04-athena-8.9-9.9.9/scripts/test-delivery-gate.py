#!/usr/bin/env python3
"""Regression checks for Athena delivery gates."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CX_GATE = ROOT / "vibeCoding/codex/9.9.0/.codex/hooks/delivery-gate.py"
CC_GATE = ROOT / "vibeCoding/claude/9.9.0/.claude/hooks/delivery-gate.cjs"


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        input=json.dumps({"hook_event_name": "Stop"}),
        text=True,
        cwd=cwd,
        capture_output=True,
        timeout=20,
    )


def assert_arch_block(result: subprocess.CompletedProcess[str], label: str) -> None:
    if result.returncode != 0:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise AssertionError(f"{label} returned {result.returncode}")
    text = result.stdout + result.stderr
    if '"decision": "block"' not in text and '"decision":"block"' not in text:
        raise AssertionError(f"{label} did not block\n{text}")
    if "architecture" not in text:
        raise AssertionError(f"{label} did not block on architecture\n{text}")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="athena-delivery-gate-") as tmp:
        project = Path(tmp)
        subprocess.run(["git", "init"], cwd=project, check=True, capture_output=True)
        ai_state = project / ".ai_state"
        sprint = ai_state / "sprints/test-sprint"
        reviews = sprint / "reviews"
        reviews.mkdir(parents=True)
        (ai_state / "_index.md").write_text(
            "---\n"
            'path: "System"  # inline comment must be ignored\n'
            'stage: "ship"  # inline comment must be ignored\n'
            'current_sprint_slug: "test-sprint"\n'
            "skip_runtime_verify: true\n"
            "---\n",
            encoding="utf-8",
        )
        (sprint / "cleanup-pass.md").write_text("# cleanup\n", encoding="utf-8")
        (sprint / "subagent-log.md").write_text("generator\n", encoding="utf-8")
        (sprint / "design.md").write_text(
            "# design\n\n## Critic Findings\n\n## Critic Findings\n",
            encoding="utf-8",
        )
        time.sleep(0.01)
        (reviews / "pass1.md").write_text(
            "## Spec Compliance\n\nPASS\n\n## Evidence Cross-Check\n\nPASS\n",
            encoding="utf-8",
        )
        for i in range(5):
            (project / f"changed-{i}.txt").write_text(str(i), encoding="utf-8")

        assert_arch_block(run(["python3", str(CX_GATE)], project), "cx delivery gate")
        assert_arch_block(run(["node", str(CC_GATE)], project), "cc delivery gate")

    print("delivery gate regression ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
