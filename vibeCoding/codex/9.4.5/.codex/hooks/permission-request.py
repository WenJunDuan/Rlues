#!/usr/bin/env python3
"""
VibeCoding PermissionRequest hook (Codex 端)。
注意: Codex PermissionRequest 协议受限, 只支持 systemMessage,
不能像 CC 那样 allow/deny/ask. 仅做日志和 systemMessage 提示。

安全: cmd 写 hook-trace 前过 redact (v9.4.5-hotfix 修复)
"""
import json
import os
import sys
from pathlib import Path

# redact 工具
sys.path.insert(0, str(Path(__file__).parent))
from _redact import redact


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_name = data.get("tool_name", "unknown")
    tool_input = data.get("tool_input") or {}
    cmd_raw = tool_input.get("command", "") if isinstance(tool_input, dict) else ""
    cmd = redact(cmd_raw)
    short = (cmd[:80] + "...") if len(cmd) > 80 else cmd

    sys.stderr.write(f"[permission-request] {tool_name}: {short}\n")

    # hook-trace (best-effort)
    try:
        sd = Path(os.environ.get("PWD") or os.getcwd()) / ".ai_state"
        if sd.exists():
            line = json.dumps({
                "ts": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
                "hook": "permission-request",
                "tool": tool_name,
                "cmd": short,
            }) + "\n"
            with open(sd / "hook-trace.jsonl", "a") as f:
                f.write(line)
    except Exception:
        pass

    if cmd:
        print(json.dumps({
            "systemMessage": f"VibeCoding: Codex 请求批准 {tool_name} - 审核后再 y/n。"
        }))

    sys.exit(0)


if __name__ == "__main__":
    main()
