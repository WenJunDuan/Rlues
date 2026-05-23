#!/usr/bin/env python3
"""VibeCoding Athena Codex PreToolUse Bash guard v9.6.1.

设计:
- 3 条灾难命令 (与 CC 等价, 跨平台正则 parity — 铁律 6)
- Codex hook 输出协议: permissionDecision = "deny" 阻断
- Codex 文档: hooks 当前实验性, Windows 不支持

参考: https://developers.openai.com/codex/hooks

v9.6.1 修复: rm 正则去掉多余的 ; & | 分支, 与 CC 端 pre-bash-guard.cjs 对齐
(原 cx 版有这些分支但 cc 版没有, 违反跨平台 parity 铁律 6).
"""
import json
import re
import sys
import datetime
import os

DANGER_PATTERNS = [
    # 1. rm -rf 系统/用户根 (与 CC 正则等价, 用 | 合并两个分支保持数量一致)
    (re.compile(r"rm\s+-[rRf]+\s+(/\s|/\*|~/?\s|~\s|/$|~$)|rm\s+-[rRf]+\s+/\s*[;&|]"), "禁止删除系统/用户根目录"),
    # 2. 管道远程脚本
    (re.compile(r"(curl|wget)\s+[^|]*\|\s*(bash|sh|zsh|fish|ksh)"), "禁止管道执行远程脚本"),
    # 3. 格式化磁盘 / 写设备
    (re.compile(r"\bmkfs\.|dd\s+if=.*of=/dev/sd|>\s*/dev/sd[a-z]"), "禁止格式化磁盘/写设备"),
]


def main():
    raw = sys.stdin.read()
    try:
        event = json.loads(raw)
    except Exception:
        sys.exit(0)
        return

    cmd = (event.get("tool_input") or {}).get("command", "")
    if not cmd:
        sys.exit(0)
        return

    for pat, reason in DANGER_PATTERNS:
        if pat.search(cmd):
            sys.stderr.write(f"[bash-guard] deny: {reason} ({cmd[:60]})\n")
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Athena bash-guard 阻断: {reason}"
                }
            }))
            try:
                project_dir = os.environ.get("CODEX_PROJECT_DIR") or os.getcwd()
                state_dir = os.path.join(project_dir, ".ai_state")
                with open(os.path.join(state_dir, "hook-trace.jsonl"), "a") as f:
                    f.write(json.dumps({
                        "ts": datetime.datetime.utcnow().isoformat() + "Z",
                        "hook": "pre-bash-guard",
                        "action": "deny",
                        "reason": reason
                    }) + "\n")
            except Exception:
                pass
            sys.exit(0)
            return

    sys.exit(0)


if __name__ == "__main__":
    main()
