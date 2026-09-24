#!/usr/bin/env python3
"""
VibeCoding PreToolUse hook — 拦截灾难级 Bash 命令。
v9.5: 只拦截"会让机器进医院"的命令。其他靠 sandbox + approval_policy + 流程约束。
"""
import json
import re
import sys


# 灾难级 (3 条):
DANGEROUS_PATTERNS = [
    (re.compile(r"rm\s+-[rR]f\s+(/\*?|~/?)(\s|;|&|\||$)"), "禁止删除系统/用户根目录"),
    (re.compile(r"(curl|wget)\s+.*\|\s*(bash|sh|zsh)"), "禁止管道执行远程脚本"),
    (re.compile(r"mkfs\.|dd\s+if=.*of=/dev/sd|>\s*/dev/sd[a-z]"), "禁止格式化磁盘/写设备"),
]


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_input = data.get("tool_input") or {}
    cmd = tool_input.get("command", "") or ""
    if not cmd:
        sys.exit(0)

    for pattern, reason in DANGEROUS_PATTERNS:
        if pattern.search(cmd):
            sys.stderr.write(f"[bash-guard] deny: {reason} ({cmd[:60]})\n")
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"VibeCoding bash-guard 阻断: {reason}",
                }
            }))
            sys.exit(0)
    sys.exit(0)


if __name__ == "__main__":
    main()
