#!/usr/bin/env python3
"""Athena v9.9.6 Codex PostToolUse evidence collector.

Codex 0.144.1 exposes ``tool_response`` as arbitrary JSON.  Only a top-level
object whose ``exit_code`` is a JSON integer is treated as authoritative;
strings, booleans, nested values, and missing fields remain ``unknown``.

The hook records only recognized validation commands as redacted evidence;
ordinary Bash, apply_patch, and MCP calls do not create raw telemetry by
default.  A hook is a best-effort guardrail, not a security or completeness
boundary; ship-time file evidence is still derived from Git.

Wire contract:
https://github.com/openai/codex/blob/rust-v0.144.1/codex-rs/hooks/schema/generated/post-tool-use.command.input.schema.json
"""

from __future__ import annotations

import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any

EXIT_SUCCESS = 0

EVIDENCE_PATTERNS = [
    (r"\b(npm|pnpm|yarn|bun)\s+(test|run\s+test)\b", "test"),
    (r"\bpytest\b", "test"),
    (r"\bcargo\s+test\b", "test"),
    (r"\bgo\s+test\b", "test"),
    (r"\b(\./gradlew|mvn)\s+test\b", "test"),
    (r"\beslint\b", "lint"),
    (r"\bprettier\s+--check\b", "lint"),
    (r"\bruff\b", "lint"),
    (r"\btsc\s+--noEmit\b", "typecheck"),
    (r"\b(npm|pnpm|yarn|bun)\s+run\s+build\b", "build"),
    (r"\bcargo\s+build\b", "build"),
    (r"\bgo\s+build\b", "build"),
    (r"\bcmake\s+--build\b", "build"),
]



def redact(value: str) -> str:
    """F3 (2026-07-29, W35): redact credentials before evidence is versioned."""
    v = re.sub(r"\b(sk-[A-Za-z0-9_-]{8,}|gh[pousr]_[A-Za-z0-9_]{8,})\b", "[REDACTED]", value or "")
    v = re.sub(r"(authorization\s*:\s*bearer\s+)[^\s,;]+", r"\1[REDACTED]", v, flags=re.I)
    v = re.sub(
        r"((?:api[_-]?key|token|password|secret|private[_-]?key|client[_-]?secret|"
        r"aws[_-](?:secret[_-]?access[_-]?key|access[_-]?key[_-]?id)|database[_-]?url)\s*[=:]\s*)[^\s,;]+",
        r"\1[REDACTED]",
        v,
        flags=re.I,
    )
    v = re.sub(r"(--(?:password|token|api[-_]?key|secret)(?:=|\s+))[^\s,;]+", r"\1[REDACTED]", v, flags=re.I)
    v = re.sub(r"(\b(?:https?|postgres(?:ql)?|mysql)://)[^\s/@:]+:[^\s/@]+@", r"\1[REDACTED]@", v, flags=re.I)
    return v[:500]


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


def response_exit_code(tool_response: Any) -> int | None:
    """Return a trustworthy exit code, or ``None`` for unknown.

    ``bool`` is explicitly rejected because Python treats it as an ``int``.
    """

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


def classify_evidence(command: str) -> str | None:
    for pattern, kind in EVIDENCE_PATTERNS:
        if re.search(pattern, command):
            return kind
    return None


def scalar(value: Any, limit: int) -> str:
    if not isinstance(value, str):
        return ""
    return value[:limit]


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
            tool_input = {}
        tool_response = payload.get("tool_response")
        tool_name = scalar(payload.get("tool_name"), 100) or "unknown"
        command = scalar(tool_input.get("command"), 4000) or scalar(tool_input.get("cmd"), 4000)

        ai_state = find_ai_state(payload_cwd(payload))
        if ai_state is None:
            return EXIT_SUCCESS
        sprint_slug = read_field(ai_state / "_index.md", "current_sprint_slug")
        if not sprint_slug:
            return EXIT_SUCCESS

        exit_code = response_exit_code(tool_response)
        status = result_status(tool_response)
        timestamp = dt.datetime.now(dt.UTC).isoformat().replace("+00:00", "Z")
        sprint_dir = ai_state / "sprints" / sprint_slug
        sprint_dir.mkdir(parents=True, exist_ok=True)

        # hotfix2 (2026-07-29, W35/AC3): tool-trace.jsonl 默认零遥测。
        kind = classify_evidence(command)
        if kind is None:
            return EXIT_SUCCESS

        evidence_path = sprint_dir / "evidence.yaml"
        if not evidence_path.exists():
            evidence_path.write_text(
                f"sprint_slug: {json.dumps(sprint_slug, ensure_ascii=False)}\ncollected_evidence:\n",
                encoding="utf-8",
            )
        # F8 (2026-07-29, W35): result 只允许 pass/fail/unknown — "fail (exit N)" 会让
        # 双端 validateEvidence 抛 unsupported result, 一条失败验证永久卡死 evidence 解析。
        result = status
        entry = (
            f"  - tool_use_id: {json.dumps(scalar(payload.get('tool_use_id'), 200), ensure_ascii=False)}\n"
            f"    tool: {json.dumps(tool_name, ensure_ascii=False)}\n"
            '    file: ""\n'
            f"    kind: {json.dumps(kind, ensure_ascii=False)}\n"
            f"    command: {json.dumps(redact(command)[:120], ensure_ascii=False)}\n"
            f"    result: {json.dumps(result, ensure_ascii=False)}\n"
            f"    timestamp: {json.dumps(timestamp)}\n"
        )
        with evidence_path.open("a", encoding="utf-8") as handle:
            handle.write(entry)
        return EXIT_SUCCESS
    except Exception as exc:  # best-effort collector; never claim success on error
        sys.stderr.write(f"[evidence-collector] non-blocking error: {exc}\n")
        return EXIT_SUCCESS


if __name__ == "__main__":
    raise SystemExit(main())
