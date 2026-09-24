#!/usr/bin/env python3
"""
VibeCoding Athena v9.6.2 · Codex PreToolUse(Bash) hook

触发: 任何 Bash 命令前
职责: 拦截危险命令 (rm -rf / curl|bash / DROP TABLE 等)

退出码:
- 0: 允许执行
- 2: 阻止执行 (Codex 看到 exit 2 + stderr → block + 反馈给主 agent)

源: https://developers.openai.com/codex/hooks (PreToolUse 事件)
"""
import json
import re
import sys

EXIT_SUCCESS = 0
EXIT_BLOCK = 2

# 灾难命令正则 (按严重度分级)
P0_PATTERNS = [
    r"\brm\s+-rf?\s+/(\s|$)",                # rm -rf /
    r"\brm\s+-rf?\s+~(\s|$)",                # rm -rf ~
    r"\brm\s+-rf?\s+\$HOME",                 # rm -rf $HOME
    r"\bcurl\b[^|]*\|\s*bash",                # curl ... | bash
    r"\bwget\b[^|]*\|\s*bash",                # wget ... | bash
    r"\bDROP\s+TABLE\b",                     # DROP TABLE
    r":\(\)\s*\{",                           # fork bomb
    r"\bdd\s+.*of=/dev/(sda|nvme|xvd)",       # dd of=/dev/sdX
    r">\s*/dev/(sda|nvme|xvd)",              # > /dev/sdX
]

# P1: 高风险但可能合法 (currently 仅 log, 不 block)
P1_PATTERNS = [
    r"\bgit\s+push\s+(--force|-f)\b",
    r"\bgit\s+reset\s+--hard\s+origin",
    r"\bsudo\b",
]


def is_dangerous(command: str) -> tuple[bool, str | None]:
    """返回 (is_dangerous, matched_pattern_description)."""
    for pat in P0_PATTERNS:
        if re.search(pat, command):
            return True, pat
    return False, None


def main() -> int:
    try:
        try:
            payload = json.load(sys.stdin) if not sys.stdin.isatty() else {}
        except Exception:
            payload = {}

        tool_input = payload.get("tool_input", {})
        command = tool_input.get("command", "")

        if not command:
            return EXIT_SUCCESS

        dangerous, pat = is_dangerous(command)
        if dangerous:
            sys.stderr.write(
                f"[pre-bash-guard] BLOCKED: 检测到灾难命令模式 ({pat})\n"
                f"命令: {command[:200]}\n"
                f"如确认无误, 请手工分步执行或修改命令.\n"
            )
            return EXIT_BLOCK

        return EXIT_SUCCESS
    except Exception as e:
        sys.stderr.write(f"[pre-bash-guard] warning (non-blocking): {e}\n")
        return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())
