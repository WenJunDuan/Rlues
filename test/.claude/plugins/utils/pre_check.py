"""PreToolUse hook checks for Bash plugin calls."""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Any


ALLOWED_PATTERN = re.compile(
    r"^\s*python3\s+\.claude/plugins/(?:[A-Za-z0-9_.-]+/main\.py|utils/[A-Za-z0-9_.-]+\.py)(?:\s+[^;\n\r]*)?\s*$"
)
FORBIDDEN_TOKENS = ("&&", "||", "|", ";", "`", "$(", "\n", "\r")


def _load_payload(raw: str) -> Any:
    text = raw.strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _extract_command(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for key in ("command", "cmd"):
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
        for key in ("input", "tool_input", "arguments", "args"):
            if key in value:
                nested = _extract_command(value[key])
                if nested:
                    return nested
        return ""
    if isinstance(value, list):
        for item in value:
            nested = _extract_command(item)
            if nested:
                return nested
    return ""


def _deny(message: str, command: str) -> int:
    print(json.dumps({"block": True, "message": message, "command": command}, ensure_ascii=False), file=sys.stderr)
    return 2


def main() -> int:
    raw = sys.argv[1] if len(sys.argv) > 1 else os.getenv("TOOL_INPUT", "")
    payload = _load_payload(raw if isinstance(raw, str) else "")
    command = _extract_command(payload)
    if not command:
        return _deny("unable to extract bash command from TOOL_INPUT", "")

    if any(token in command for token in FORBIDDEN_TOKENS):
        return _deny("shell chaining and redirection are not allowed", command)
    if not ALLOWED_PATTERN.match(command):
        return _deny("only python3 .claude/plugins/<plugin>/main.py or utils/*.py invocations are allowed", command)
    if ".." in command:
        return _deny("relative parent path is not allowed", command)

    print(json.dumps({"block": False, "message": "pre-check passed", "command": command}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
