#!/usr/bin/env python3
"""Regression checks for Athena token-usage collectors."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CX_COLLECTOR = ROOT / "vibeCoding/codex/9.9.0/.codex/hooks/token-usage-collector.py"
CC_COLLECTOR = ROOT / "vibeCoding/claude/9.9.0/.claude/hooks/token-usage-collector.cjs"


def run(cmd: list[str], *, payload: dict | None = None) -> None:
    stdin = json.dumps(payload) if payload is not None else None
    result = subprocess.run(cmd, input=stdin, text=True, cwd=ROOT, capture_output=True, timeout=20)
    if result.returncode != 0:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise SystemExit(result.returncode)


def scalar(content: str, key: str) -> int:
    match = re.search(rf"^\s*{re.escape(key)}:\s*(\d+)\s*$", content, re.MULTILINE)
    if not match:
        raise AssertionError(f"missing scalar {key}\n{content}")
    return int(match.group(1))


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="athena-token-") as tmp:
        project = Path(tmp)
        ai_state = project / ".ai_state"
        sprint = ai_state / "sprints/test-sprint"
        sprint.mkdir(parents=True)
        index = ai_state / "_index.md"
        index.write_text('---\nstage: "runtime-verify"\ncurrent_sprint_slug: "test-sprint"\n---\n')

        transcript = project / "transcript.jsonl"
        agent_transcript = project / "agent-transcript.jsonl"
        transcript.write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "timestamp": "2026-07-08T00:00:00Z",
                            "type": "event_msg",
                            "payload": {
                                "type": "token_count",
                                "info": {
                                    "last_token_usage": {
                                        "input_tokens": 100,
                                        "cached_input_tokens": 20,
                                        "output_tokens": 30,
                                        "reasoning_output_tokens": 5,
                                        "total_tokens": 130,
                                    }
                                },
                            },
                        }
                    ),
                    json.dumps(
                        {
                            "timestamp": "2026-07-08T00:00:01Z",
                            "message": "<usage>subagent_tokens=77</usage>",
                        }
                    ),
                ]
            )
            + "\n"
        )
        agent_transcript.write_text(
            json.dumps(
                {
                    "timestamp": "2026-07-08T00:00:02Z",
                    "usage": {
                        "input_tokens": 11,
                        "output_tokens": 7,
                        "total_tokens": 18,
                    },
                }
            )
            + "\n"
        )

        payload = {
            "cwd": str(project),
            "transcript_path": str(transcript),
            "hook_event_name": "Stop",
        }
        subagent_payload = {
            "cwd": str(project),
            "agent_transcript_path": str(agent_transcript),
            "hook_event_name": "SubagentStop",
        }

        run(["python3", str(CX_COLLECTOR)], payload=payload)
        index.write_text('---\nstage: "review"\ncurrent_sprint_slug: "test-sprint"\n---\n')
        run(["python3", str(CX_COLLECTOR)], payload=payload)
        run(["node", str(CC_COLLECTOR)], payload=payload)
        run(["python3", str(CX_COLLECTOR)], payload=subagent_payload)
        run(["node", str(CC_COLLECTOR)], payload=subagent_payload)
        run(["python3", str(CX_COLLECTOR)], payload={"cwd": str(project), "hook_event_name": "Stop"})

        usage = (sprint / "token-usage.yaml").read_text()
        if usage.count("fingerprint:") != 6:
            raise AssertionError(usage)
        if 'by_stage:' not in usage or '"runtime-verify":' not in usage or '"review":' not in usage:
            raise AssertionError(usage)
        if 'agent_transcript_path' not in usage:
            raise AssertionError(usage)
        if "<usage>" in usage:
            raise AssertionError("raw usage tag leaked into output")
        if scalar(usage, "input_tokens") != 222:
            raise AssertionError(usage)
        if scalar(usage, "output_tokens") != 74:
            raise AssertionError(usage)
        if scalar(usage, "total_tokens") != 450:
            raise AssertionError(usage)

    with tempfile.TemporaryDirectory(prefix="athena-token-empty-") as tmp:
        project = Path(tmp)
        sprint = project / ".ai_state/sprints/test-sprint"
        sprint.mkdir(parents=True)
        (project / ".ai_state/_index.md").write_text(
            '---\nstage: "review"\ncurrent_sprint_slug: "test-sprint"\n---\n'
        )
        run(["python3", str(CX_COLLECTOR)], payload={"cwd": str(project), "hook_event_name": "Stop"})
        usage = (sprint / "token-usage.yaml").read_text()
        if 'status: "no_usage_found"' not in usage:
            raise AssertionError(usage)
        if not re.search(r"^\s*input_tokens:\s*null\s*$", usage, re.MULTILINE):
            raise AssertionError(usage)

    for config_file in [
        ROOT / "vibeCoding/codex/9.9.0/.codex/hooks.json",
        ROOT / "vibeCoding/claude/9.9.0/.claude/settings.json",
    ]:
        config = json.loads(config_file.read_text())
        subagent_hooks = config["hooks"]["SubagentStop"][0]["hooks"]
        if not any("token-usage-collector" in hook.get("command", "") for hook in subagent_hooks):
            raise AssertionError(f"SubagentStop collector missing in {config_file}")

    print("token usage collector regression ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
