#!/usr/bin/env python3
"""
VibeCoding PostToolUse hook v9.5 (Codex)

监听 spawn_agent / Skill 工具的输出, 检测放弃信号, 注入重试压力。
计数器: per-session, 存 ~/.codex/state/retry-counter.json

v9.5 变更:
  1. 删除"lesson-drafter 已起草"引用 (该 hook 已删除)
  2. 触发消息改引用铁律 6 (完成度证据)
  3. 消息精简 350→200 字符以内

PostToolUse 协议: decision:"block" + reason → stderr 给 agent (但已 ran)
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


ABANDON_KEYWORDS = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"本\s*session\s*没有\s*Bash\s*工具",
        r"Bash\s*工具.*?(不可用|无法使用|无法执行)",
        r"子\s*agent\s*也一样",
        r"无\s*Bash\s*工具权限",
        r"请\s*(您|你)\s*(直接|手动|自己)",
        r"请在(提示框|终端)",
        r"用\s*!\s*前缀",
        r"\bI (cannot|can't|don't have).*Bash\b",
        r"\bplease run (this|the following) (command|manually)\b",
        r"\bpaste (it|this|the command)\b.*\bagain\b",
        r"\bnot listed as available to me\b",
    ]
]


def main():
    try:
        event = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_name = event.get("tool_name", "")
    if not any(t in tool_name.lower() for t in ["spawn", "agent", "skill", "task"]):
        sys.exit(0)

    output = ""
    if event.get("tool_response"):
        output = (
            event["tool_response"]
            if isinstance(event["tool_response"], str)
            else json.dumps(event["tool_response"])
        )
    elif event.get("tool_output"):
        output = (
            event["tool_output"]
            if isinstance(event["tool_output"], str)
            else json.dumps(event["tool_output"])
        )

    if not output:
        sys.exit(0)

    matched = next((p for p in ABANDON_KEYWORDS if p.search(output)), None)
    if not matched:
        sys.exit(0)

    state_dir = Path.home() / ".codex" / "state"
    state_dir.mkdir(exist_ok=True, parents=True)
    counter_file = state_dir / "retry-counter.json"
    try:
        counter = json.loads(counter_file.read_text())
    except Exception:
        counter = {}

    session_id = event.get("session_id", "unknown")
    counter[session_id] = counter.get(session_id, 0) + 1
    try:
        counter_file.write_text(json.dumps(counter))
    except Exception:
        pass

    count = counter[session_id]
    sys.stderr.write(f"[subagent-retry] 放弃信号 ({count}/3): {matched.pattern[:40]}\n")

    # hook-trace
    try:
        sd = Path(os.environ.get("PWD") or os.getcwd()) / ".ai_state"
        if sd.exists():
            line = json.dumps({
                "ts": datetime.now(timezone.utc).isoformat(),
                "hook": "subagent-retry",
                "count": count,
                "tool": tool_name,
                "signal": matched.pattern[:40],
            }) + "\n"
            with open(sd / "hook-trace.jsonl", "a") as f:
                f.write(line)
    except Exception:
        pass

    if count < 3:
        msg = (
            f'⚠ Hermes 铁律 6 (完成度证据): subagent "无能为力" 不算证据 ({count}/3)。\n'
            "重试: ① 主线实测一次命令看真实 stderr ② permission 错就报具体规则 ③ "
            "子 agent 自限就接管，不推回用户"
        )
    else:
        msg = "🛑 已重试 3 次。按铁律 6 接受失败 → 完整命令+stderr+尝试列表写入报告。"

    print(json.dumps({
        "decision": "block",
        "reason": msg,
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
