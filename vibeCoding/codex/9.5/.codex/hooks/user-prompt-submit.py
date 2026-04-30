#!/usr/bin/env python3
"""
VibeCoding UserPromptSubmit hook (Codex 独有, v0.116+)

策略 (Q4 决策: 关键词智能触发):
- 用户 prompt 含 "继续/继续做/接着/再/重新" → 注入 R₀ 强制提醒
- 含 "调用/调度/spawn" → 注入 spawn_agent 真实性提醒 (反伪造)
- 含 "失败/不行/错误/挂了" → 注入铁律 8 重试提醒
- 都不含 → 不注入 (避免污染常规对话)

输出协议: hookSpecificOutput.{hookEventName, additionalContext}
"""
import json
import os
import re
import sys
from pathlib import Path


# 关键词触发器
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
            "[Hermes R₀ 强制] 你需要先做 Get-bearings 再继续:\n"
            "  1. 扫 ~/.codex/lessons/INDEX.md (主题命中再读)\n"
            "  2. 读 .ai_state/project.json → Path/Stage/Sprint\n"
            "  3. 读 .ai_state/progress.md → 上次做了什么\n"
            "  4. 读 .ai_state/lessons.md 最近 10 条\n"
            "  5. git log --oneline -10\n"
            "  跳过 R₀ 直接动手 = 违反铁律。"
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
            "[Hermes 完成度证据] 跨 worker 调用前后, 检查 AGENTS.md 的 '完成度证据要求' 表:\n"
            "  spawn_agent worker 已执行 → 必须给出 child agent thread ID + report_agent_job_result 输出\n"
            "  /review 或 reviewer 已跑 → 必须给出 reviewer 输出片段, 不可用时明示 'unavailable, 已记 lesson'\n"
            "  不能给证据的 '已完成' 视同未完成\n"
            "[Hermes 阶段一致性] 若当前 stage=plan, 不要立即 spawn_agent generator 写代码; 先确认 design.md/tasks.md。\n"
            "  若 stage=review, 不要 spawn_agent generator 改代码; review 阶段只评审, 改代码回 impl。"
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
            "[Hermes 铁律 8] 工具失败按顺序处理:\n"
            "  1. 读 stderr/exit code 分类 (permission/not-found/子任务自限)\n"
            "  2. 改参数/换路径/换工具/拆到主线 至少试 3 次\n"
            "  3. 第 3 次仍败才报告每次具体失败\n"
            "  绝对禁止: 让用户用 ! 前缀手动执行作为第一次响应"
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

    # 命中检测
    matched_messages = []
    matched_names = []
    for trigger in TRIGGERS:
        for pat in trigger["patterns"]:
            if pat.search(prompt):
                matched_messages.append(trigger["message"])
                matched_names.append(trigger["name"])
                break  # 每个 trigger 只触发一次

    if not matched_messages:
        sys.exit(0)

    # hook-trace
    try:
        sd = Path(os.environ.get("PWD") or os.getcwd()) / ".ai_state"
        if sd.exists():
            line = json.dumps({
                "ts": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
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

    # UserPromptSubmit 官方协议: hookSpecificOutput.additionalContext (4 月 stable 后支持)
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": additional,
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
