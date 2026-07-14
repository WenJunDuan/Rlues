#!/usr/bin/env python3
"""Athena v9.9.3 Codex PreToolUse(Bash) guardrail.

Blocks a small set of catastrophic shell patterns and prevents an Athena
project from pushing before ``stage: ship``.  Native Codex collaboration tools
are not shell commands, and worktree isolation is established by the main
thread before delegation, so this hook performs no fake subagent/worktree
enforcement.  Hooks are defense-in-depth guardrails, not a security boundary.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

EXIT_SUCCESS = 0
EXIT_BLOCK = 2

CATASTROPHIC_PATTERNS = [
    r"\brm\s+-rf?\s+/(?:\s|$)",
    r"\brm\s+-rf?\s+~(?:\s|$)",
    r"\brm\s+-rf?\s+\$HOME(?:\s|$)",
    r"\bcurl\b[^|]*\|\s*(?:ba|z|fi)?sh\b",
    r"\bwget\b[^|]*\|\s*(?:ba|z|fi)?sh\b",
    r"\bDROP\s+TABLE\b",
    r":\(\)\s*\{",
    r"\bdd\s+.*\bof=/dev/(?:sda|nvme\w*|xvd\w*)\b",
    r">\s*/dev/(?:sda|nvme\w*|xvd\w*)\b",
]


def find_ai_state(cwd: Path) -> Path | None:
    current = cwd.resolve()
    for _ in range(8):
        candidate = current / ".ai_state"
        if candidate.is_dir():
            return candidate
        if current.parent == current:
            break
        current = current.parent
    return None


def payload_cwd(payload: dict[str, Any]) -> Path:
    value = payload.get("cwd")
    if isinstance(value, str) and value.strip():
        return Path(value).expanduser()
    return Path.cwd()


def read_field(idx_path: Path, field: str) -> str:
    try:
        content = idx_path.read_text(encoding="utf-8")
        match = re.search(rf'^{re.escape(field)}:\s*["\']?([^"\n]*)["\']?', content, re.MULTILINE)
        return match.group(1).strip() if match else ""
    except OSError:
        return ""


def main() -> int:
    try:
        try:
            payload = json.load(sys.stdin) if not sys.stdin.isatty() else {}
        except (json.JSONDecodeError, OSError):
            payload = {}
        if not isinstance(payload, dict):
            payload = {}
        tool_input = payload.get("tool_input")
        if not isinstance(tool_input, dict):
            return EXIT_SUCCESS
        command = tool_input.get("command")
        if not isinstance(command, str) or not command.strip():
            return EXIT_SUCCESS

        for pattern in CATASTROPHIC_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                sys.stderr.write(
                    f"[pre-bash-guard] BLOCKED catastrophic command pattern: {pattern}\n"
                )
                return EXIT_BLOCK

        ai_state = find_ai_state(payload_cwd(payload))
        # Include ordinary ``git push`` and forms such as ``git -C <repo> push``.
        if ai_state and re.search(r"\bgit\b[^;\n|&]*\bpush\b", command):
            if "ATHENA_ALLOW_PUSH=1" not in command:
                stage = read_field(ai_state / "_index.md", "stage")
                if stage and stage != "ship":
                    sys.stderr.write(
                        f"[pre-bash-guard] BLOCKED git push at stage={stage}; advance through review to ship. "
                        "Emergency override: ATHENA_ALLOW_PUSH=1 (owner accepts risk).\n"
                    )
                    return EXIT_BLOCK
        return EXIT_SUCCESS
    except Exception as exc:
        sys.stderr.write(f"[pre-bash-guard] non-blocking error: {exc}\n")
        return EXIT_SUCCESS


if __name__ == "__main__":
    raise SystemExit(main())
