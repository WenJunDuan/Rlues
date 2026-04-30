#!/usr/bin/env python3
"""
VibeCoding PostToolUse hook (Codex)

监听 spawn_agent / Skill / 其他工具的输出, 检测放弃信号 (关键词驱动),
注入重试压力。
计数器: per-session, 存 ~/.codex/state/retry-counter.json

PostToolUse 协议:
- decision:"block" + reason → stderr 给 agent (但已 ran)
- 或 hookSpecificOutput.additionalContext (4 月 stable 后支持)
"""
import json
import os
import sys
from pathlib import Path


# 放弃信号关键词 (Q1 决策: 关键词驱动)
ABANDON_KEYWORDS = [
    __import__("re").compile(p, __import__("re").IGNORECASE)
    for p in [
        r"本\s*session\s*没有\s*Bash\s*工具",
        r"子\s*agent\s*也一样",
        r"无\s*Bash\s*工具权限",
        r"请\s*(您|你)\s*(直接|手动|自己)",
        r"请在(提示框|终端)",
        r"用\s*!\s*前缀",
        r"\bI cannot execute\b",
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
    # 只看 spawn_agent 类工具的输出 (Codex)
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

    matched = next((re for re in ABANDON_KEYWORDS if re.search(output)), None)
    if not matched:
        sys.exit(0)

    # 计数器
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
    sys.stderr.write(
        f"[subagent-retry] 检测到放弃信号 ({count}/3): {matched.pattern[:40]}\n"
    )

    # hook-trace
    try:
        sd = Path(os.environ.get("PWD") or os.getcwd()) / ".ai_state"
        if sd.exists():
            line = json.dumps({
                "ts": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
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
            f"⚠ Hermes 铁律 8: subagent 报告无能为力是不接受的 (第 {count}/3 次)。\n"
            "重试要求:\n"
            "  1. 实测一次失败的命令, 看真实 stderr 和 exit code\n"
            "  2. permission denied → 报具体阻断原因, 切到主线做\n"
            "  3. subagent 自我设限 → 主线接管, 不要把任务推回用户\n"
            '  4. 完全禁止 "请你用 ! 前缀手动执行" 作为响应'
        )
    else:
        msg = (
            f"🛑 已重试 3 次仍报无能为力, 按铁律 8 接受失败。\n"
            "lesson-drafter 应已在 ~/.codex/lessons/draft-*.md 起草此问题。"
        )

    # PostToolUse decision:block + reason → 注入给 agent
    # 注: Codex PostToolUse 的 block 不能 undo 已运行的工具, 但 reason 会作为 stderr 给 agent
    print(json.dumps({
        "decision": "block",
        "reason": msg,
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
