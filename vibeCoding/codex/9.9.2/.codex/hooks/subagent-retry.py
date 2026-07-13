#!/usr/bin/env python3
"""Athena v9.9.2 legacy compatibility shim for PostToolUse.

This file intentionally does not spawn, retry, advance a roadmap, or infer a
subagent result from shell text.  Codex collaboration is driven by native v2
tools and SubagentStart/SubagentStop lifecycle events.  The old filename is
retained only so upgrades can remove a previously wired hook safely.

Wire contract:
https://github.com/openai/codex/blob/rust-v0.144.1/codex-rs/hooks/schema/generated/post-tool-use.command.input.schema.json
"""

from __future__ import annotations

import json
import sys
from typing import Any


def response_exit_code(tool_response: Any) -> int | None:
    if not isinstance(tool_response, dict):
        return None
    value = tool_response.get("exit_code")
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def result_status(tool_response: Any) -> str:
    exit_code = response_exit_code(tool_response)
    if exit_code is None:
        return "unknown"
    return "pass" if exit_code == 0 else "fail"


def main() -> int:
    try:
        payload = json.load(sys.stdin) if not sys.stdin.isatty() else {}
    except (json.JSONDecodeError, OSError):
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    # Evaluate the exact 0.144.1 field so regression tests can import this
    # compatibility shim.  No state transition is performed here.
    result_status(payload.get("tool_response"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
