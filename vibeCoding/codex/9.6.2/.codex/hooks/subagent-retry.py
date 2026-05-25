#!/usr/bin/env python3
"""
VibeCoding Athena v9.6.2 · Codex PostToolUse(Bash) hook (subagent-retry)

触发: Bash 命令完成后
职责: 检测 subagent 失败 (spawn_agent / spawn_agents_on_csv 返回非 0), 触发重试建议

非阻塞 (exit 0). 仅记录到 .ai_state/details/runtime-events.md 供主 agent 参考.
"""
import json
import os
import sys
from pathlib import Path

EXIT_SUCCESS = 0


def find_ai_state(cwd: Path) -> Path | None:
    for _ in range(5):
        if (cwd / ".ai_state").is_dir():
            return cwd / ".ai_state"
        if cwd.parent == cwd:
            return None
        cwd = cwd.parent
    return None


def main() -> int:
    try:
        try:
            payload = json.load(sys.stdin) if not sys.stdin.isatty() else {}
        except Exception:
            payload = {}

        tool_input = payload.get("tool_input", {})
        tool_output = payload.get("tool_output", {})
        command = tool_input.get("command", "")
        stdout = tool_output.get("stdout", "")
        stderr = tool_output.get("stderr", "")
        exit_code = tool_output.get("exit_code", 0)

        # 仅关注 spawn_agent / report_agent_job_result 等 subagent 相关失败
        is_subagent_cmd = any(kw in command for kw in [
            "spawn_agent",
            "spawn_agents_on_csv",
            "report_agent_job_result",
        ])

        if not is_subagent_cmd:
            return EXIT_SUCCESS

        if exit_code == 0:
            return EXIT_SUCCESS

        # 失败记录
        cwd = Path.cwd()
        ai_state = find_ai_state(cwd)
        if ai_state is None:
            return EXIT_SUCCESS

        events = ai_state / "details" / "runtime-events.md"
        events.parent.mkdir(parents=True, exist_ok=True)

        import datetime
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = (
            f"\n## {ts} · subagent 失败\n"
            f"- command: `{command[:200]}`\n"
            f"- exit_code: {exit_code}\n"
            f"- stderr (前 500): `{stderr[:500]}`\n"
            f"- 建议: 主 agent 检查 stderr, 修复后重试; 若 3 次失败 → 降级到非 subagent 路径\n"
        )

        with events.open("a", encoding="utf-8") as f:
            f.write(entry)

        return EXIT_SUCCESS
    except Exception as e:
        sys.stderr.write(f"[subagent-retry] warning (non-blocking): {e}\n")
        return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())
