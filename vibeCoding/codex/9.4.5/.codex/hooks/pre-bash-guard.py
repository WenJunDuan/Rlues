#!/usr/bin/env python3
"""
VibeCoding PreToolUse hook — 拦截危险 Bash 命令。
Codex PreToolUse Bash 事件协议:
  - hookSpecificOutput.permissionDecision: "deny" / "allow" / "ask"
  - 或 exit 2 + stderr 阻断
"""
import json
import re
import sys


DANGEROUS_PATTERNS = [
    (re.compile(r"rm\s+-[rR]f\s+(/\*?|~/?)(\s|;|&|\||$)"), "禁止删除系统/用户根目录"),
    (re.compile(r"curl\s+.*\|\s*(bash|sh|zsh)"), "禁止管道执行远程脚本"),
    (re.compile(r"wget\s+.*\|\s*(bash|sh|zsh)"), "禁止管道执行远程脚本"),
    (re.compile(r"git\s+push\s+.*--force"), "禁止 force push"),
    (re.compile(r"git\s+push\s+origin\s+(main|master)\b"), "禁止直接 push main/master"),
    (re.compile(r">\s*/dev/sd[a-z]"), "禁止写入磁盘设备"),
    (re.compile(r"mkfs\."), "禁止格式化文件系统"),
    (re.compile(r"dd\s+if="), "禁止 dd 操作"),
    (re.compile(r"chmod\s+-R\s+777\s+/"), "禁止全局 777 权限"),
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
            sys.stderr.write(
                f"[bash-guard] deny: {reason} ({cmd[:60]})\n"
            )
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
