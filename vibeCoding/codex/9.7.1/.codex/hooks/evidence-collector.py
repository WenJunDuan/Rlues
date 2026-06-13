#!/usr/bin/env python3
"""
VibeCoding Athena v9.7.0 · Codex PostToolUse(Bash) hook (evidence-collector)

职责 (铁律[证据] CX 实现, 修复 v9.6.4 CX 端 evidence 链断裂):
  1. 每个 Bash tool call 追加一行 tool-trace.jsonl
  2. 识别过程证据命令 (test / lint / build / typecheck) → 写 evidence.yaml

平台边界 [官方 developers.openai.com/codex/hooks]:
  CX 的 PostToolUse 实质只覆盖 shell 工具; apply_patch / 文件写 / MCP 工具
  不触发 hook ("doesn't intercept non-shell, non-MCP tool calls").
  → 本 hook 只收**过程证据**; **文件证据**由 delivery-gate.py 门禁时
    用 git diff --stat 现场计算. 对等的是门禁强度, 不是逐字段照抄 CC.

evidence.yaml schema 与 CC 端一致 (file 字段在 CX 过程证据中留空合法).
非阻塞: 任何异常 exit 0.
"""
import datetime
import json
import re
import sys
from pathlib import Path

EXIT_SUCCESS = 0

# 过程证据命令模式 (test / lint / build / typecheck)
EVIDENCE_PATTERNS = [
    (r"\b(npm|pnpm|yarn|bun)\s+(test|run\s+test)", "test"),
    (r"\bpytest\b", "test"),
    (r"\bcargo\s+test\b", "test"),
    (r"\bgo\s+test\b", "test"),
    (r"\b(\./gradlew|mvn)\s+test\b", "test"),
    (r"\beslint\b", "lint"),
    (r"\bprettier\s+--check", "lint"),
    (r"\bruff\b", "lint"),
    (r"\btsc\s+--noEmit", "typecheck"),
    (r"\b(npm|pnpm|yarn|bun)\s+run\s+build", "build"),
    (r"\bcargo\s+build\b", "build"),
    (r"\bgo\s+build\b", "build"),
    (r"\bcmake\s+--build", "build"),
]


def find_ai_state(cwd: Path):
    current = cwd
    for _ in range(5):
        candidate = current / ".ai_state"
        if candidate.is_dir():
            return candidate
        if current.parent == current:
            return None
        current = current.parent
    return None


def read_field(idx_path: Path, field: str) -> str:
    try:
        content = idx_path.read_text(encoding="utf-8")
        m = re.search(rf'^{field}:\s*["\']?([^"\n]*)["\']?', content, re.MULTILINE)
        return m.group(1).strip() if m else ""
    except Exception:
        return ""


def classify_evidence(command: str):
    for pat, kind in EVIDENCE_PATTERNS:
        if re.search(pat, command):
            return kind
    return None


def main() -> int:
    try:
        try:
            payload = json.load(sys.stdin) if not sys.stdin.isatty() else {}
        except Exception:
            payload = {}

        tool_input = payload.get("tool_input", {}) or {}
        tool_output = payload.get("tool_output", {}) or {}
        command = tool_input.get("command", "") or ""
        if not command:
            return EXIT_SUCCESS

        ai_state = find_ai_state(Path.cwd())
        if ai_state is None:
            return EXIT_SUCCESS

        sprint_slug = read_field(ai_state / "_index.md", "current_sprint_slug")
        if not sprint_slug:
            return EXIT_SUCCESS

        exit_code = tool_output.get("exit_code", 0)
        if exit_code is None:
            exit_code = 0
        ts = datetime.datetime.utcnow().isoformat() + "Z"
        sprint_dir = ai_state / "sprints" / sprint_slug
        sprint_dir.mkdir(parents=True, exist_ok=True)

        # 1. tool-trace.jsonl (每个 Bash call 一行; schema 对齐 CC: ts/tool/exit/command)
        trace = {
            "ts": ts,
            "tool": "Bash",
            "tool_use_id": payload.get("tool_use_id", "") or "",
            "exit": exit_code,
            "command": command[:200],
        }
        with (sprint_dir / "tool-trace.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(trace, ensure_ascii=False) + "\n")

        # 2. 过程证据 → evidence.yaml (schema 与 CC 一致; file 留空合法)
        kind = classify_evidence(command)
        if kind:
            ev_path = sprint_dir / "evidence.yaml"
            if not ev_path.exists():
                ev_path.write_text(
                    f"sprint_slug: {sprint_slug}\ncollected_evidence:\n",
                    encoding="utf-8",
                )
            status = "pass" if exit_code == 0 else f"fail (exit {exit_code})"
            entry = (
                f'  - tool_use_id: "{trace["tool_use_id"]}"\n'
                f'    tool: "Bash"\n'
                f'    file: ""\n'
                f'    kind: "{kind}"\n'
                f'    command: "{command[:120]}"\n'
                f'    result: "{status}"\n'
                f'    timestamp: "{ts}"\n'
            )
            with ev_path.open("a", encoding="utf-8") as f:
                f.write(entry)

        return EXIT_SUCCESS
    except Exception as e:
        sys.stderr.write(f"[evidence-collector] non-blocking: {e}\n")
        return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())
