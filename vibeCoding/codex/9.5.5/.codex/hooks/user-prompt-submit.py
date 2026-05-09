#!/usr/bin/env python3
"""
VibeCoding UserPromptSubmit hook v9.5 (Codex)

策略 (关键词智能触发):
- "继续/接着/重新" → 注入 R₀ 强制提醒 (just-in-time, 不预加载内容)
- "调用/调度/spawn" → 注入 spawn_agent 真实性提醒
- "失败/不行/错误" → 注入铁律 6 (完成度证据) 重试提醒

v9.5 变更:
  1. 删除 ~/.codex/lessons/ 引用 (全局 lessons 系统已删除)
  2. R₀ 改为 just-in-time, 不预加载 lessons.md 内容
  3. 铁律编号统一改为 6 (完成度证据), 而非旧的 8 (不懒惰)

输出协议: hookSpecificOutput.{hookEventName, additionalContext}
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


TRIGGERS = [
    {
        "name": "continuation",
        "patterns": [
            re.compile(r"继续(做|开发|工作|实现)?", re.IGNORECASE),
            re.compile(r"接着(做|来|搞)", re.IGNORECASE),
            re.compile(r"重新(做|来|开始)", re.IGNORECASE),
            re.compile(r"\bcontinue\b", re.IGNORECASE),
            re.compile(r"\bresume\b", re.IGNORECASE),
        ],
        "message": (
            "[Hermes R₀ Get-bearings] just-in-time:\n"
            "  1. read .ai_state/project.json → Path/Stage/Sprint\n"
            "  2. read .ai_state/progress.md → 上次做到哪\n"
            "  3. 命中 lessons 主题再 read .ai_state/lessons.md\n"
            "  4. git log --oneline -10\n"
            "  跳过 R₀ 直接动手 = 违反 PACE 流程。"
        ),
    },
    {
        "name": "spawn-truth",
        "patterns": [
            re.compile(r"调用|调度", re.IGNORECASE),
            re.compile(r"spawn[_\s]?agent", re.IGNORECASE),
            re.compile(r"reviewer|evaluator|generator", re.IGNORECASE),
        ],
        "message": (
            "[Hermes 调度真实性] spawn_agent 必须产生真实 tool_use:\n"
            "  - 不允许伪造完成 (subagent 失败但报告 done)\n"
            "  - 不允许降级伪装 (调用失败后用本地分析冒充 subagent 输出)\n"
            "  - 报告完成必须附 tool_use ID 或命令输出 (铁律 6)"
        ),
    },
    {
        "name": "failure-handling",
        "patterns": [
            re.compile(r"(失败|不行|挂了|错误|出错|报错|没成功)", re.IGNORECASE),
            re.compile(r"\b(fail|failed|error|broken|crash)\b", re.IGNORECASE),
            re.compile(r"permission denied", re.IGNORECASE),
        ],
        "message": (
            "[Hermes 铁律 6 完成度证据] 工具失败按顺序:\n"
            "  1. 读 stderr/exit code 分类 (permission/not-found/子任务自限)\n"
            "  2. 改参数/换路径/换工具/拆到主线 至少试 3 次\n"
            "  3. 第 3 次仍败 → 完整命令+stderr+尝试列表写入报告\n"
            "  禁止: 第一次响应就让用户手动执行"
        ),
    },
]


def main():
    try:
        event = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    prompt = event.get("prompt", "") or event.get("user_prompt", "") or ""
    if not prompt:
        sys.exit(0)

    matched_messages = []
    matched_names = []
    for trigger in TRIGGERS:
        for pat in trigger["patterns"]:
            if pat.search(prompt):
                matched_messages.append(trigger["message"])
                matched_names.append(trigger["name"])
                break

    if not matched_messages:
        sys.exit(0)

    # hook-trace
    try:
        sd = Path(os.environ.get("PWD") or os.getcwd()) / ".ai_state"
        if sd.exists():
            line = json.dumps({
                "ts": datetime.now(timezone.utc).isoformat(),
                "hook": "user-prompt-submit",
                "triggers": matched_names,
                "prompt_preview": prompt[:50],
            }) + "\n"
            with open(sd / "hook-trace.jsonl", "a") as f:
                f.write(line)
    except Exception:
        pass

    additional = "\n\n".join(matched_messages)
    sys.stderr.write(
        f"[user-prompt-submit] 触发: {','.join(matched_names)} ({len(additional)} chars)\n"
    )

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": additional,
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
