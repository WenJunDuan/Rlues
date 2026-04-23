#!/usr/bin/env python3
"""
VibeCoding PreToolUse hook — 拦截危险 Bash 命令。
Codex PreToolUse 当前只对 Bash 事件触发。
输出 systemMessage JSON → Codex 显示为系统消息并阻止执行。
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
            # Codex PreToolUse: systemMessage 会显示给用户
            # 但 block 语义需要通过 exit code (非 0 = 中止该 tool 调用, 但不中止整个 turn)
            # 实际阻断效果靠 sandbox + approval_policy, 这里给出提示供用户拒绝 approval
            print(json.dumps({
                "systemMessage": f"⛔ VibeCoding bash-guard 阻断: {reason}\n命令: {cmd[:120]}"
            }))
            sys.exit(2)  # 非 0 退出, Codex 会把该 tool 调用标记为失败
    sys.exit(0)


if __name__ == "__main__":
    main()
