#!/usr/bin/env python3
"""
VibeCoding PermissionRequest hook — 当 Codex 请求用户批准某个操作时触发。
用于记录审批 trail 和给出基于上下文的提示 (systemMessage)。
不做自动批准/拒绝, 保留用户最终决定权 (approval_policy = on-request)。
"""
import json
import sys


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    # PermissionRequest 事件包含 tool_name, tool_input 等
    tool_name = data.get("tool_name", "unknown")
    tool_input = data.get("tool_input") or {}
    cmd = tool_input.get("command", "") if isinstance(tool_input, dict) else ""

    # 只做 stderr 日志 + systemMessage 提示, 不阻塞
    short = (cmd[:80] + "...") if len(cmd) > 80 else cmd
    sys.stderr.write(f"[permission-request] {tool_name}: {short}\n")

    # 给用户一个温和的上下文提示
    if cmd:
        print(json.dumps({
            "systemMessage": f"VibeCoding: Codex 请求批准 {tool_name} 操作 — 审核后再 y/n。"
        }))

    sys.exit(0)


if __name__ == "__main__":
    main()
