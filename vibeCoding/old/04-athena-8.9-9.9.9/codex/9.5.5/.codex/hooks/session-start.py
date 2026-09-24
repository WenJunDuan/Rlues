#!/usr/bin/env python3
"""
VibeCoding SessionStart hook v9.5 (Codex)
matcher: startup / resume / clear (Codex 没有 compact)

设计:
  1. 删除全局 lessons INDEX 注入 (Hermes 不再做跨项目知识管理)
  2. just-in-time 检索: 不预加载 tasks 内容, 只注入"任务计数"轻量摘要
  3. 删除 lesson-archiver 调用 (该 hook 已删除)

输出协议: hookSpecificOutput.{hookEventName, additionalContext}
"""
import json
import os
import re
import sys
from pathlib import Path


def main():
    try:
        event = json.load(sys.stdin)
    except Exception:
        event = {}
    source = event.get("source", "unknown")

    project_dir = Path(os.environ.get("PWD") or os.getcwd())
    state_dir = project_dir / ".ai_state"

    home = Path.home()
    project_essentials = project_dir / ".codex" / "skills" / "pace" / "context-essentials.md"
    global_essentials = home / ".codex" / "skills" / "pace" / "context-essentials.md"

    lines = []

    # 1. 注入 context-essentials.md (优先项目级, 回落全局)
    for p in [project_essentials, global_essentials]:
        try:
            text = p.read_text(encoding="utf-8").strip()
            if text:
                lines.append(text)
                break
        except Exception:
            continue

    if not lines:
        lines.append(
            "[VibeCoding v9.5] TDD · Review · Sisyphus · 设计先行 · 完成度证据 · 出处优先\n"
            "[Get-bearings] 读 .ai_state/project.json → 按需 read 其他状态文件"
        )

    # 2. 注入项目状态
    project_json = state_dir / "project.json"
    if project_json.is_file():
        try:
            p = json.loads(project_json.read_text(encoding="utf-8"))
            if p.get("path") and p.get("stage"):
                lines.append(
                    f"\n[PACE] Path:{p['path']} Stage:{p['stage']} Sprint:{p.get('sprint', 0)}"
                )
            gotchas = p.get("gotchas") or []
            if gotchas:
                lines.append("[Gotchas] " + " | ".join(gotchas))
        except Exception:
            pass

    # 3. just-in-time: 只给计数, 不粘 tasks 内容
    tasks_md = state_dir / "tasks.md"
    if tasks_md.is_file():
        try:
            t = tasks_md.read_text(encoding="utf-8")
            pending = re.findall(r"^- \[ \].*", t, flags=re.MULTILINE)
            done = re.findall(r"^- \[x\].*", t, flags=re.MULTILINE)
            if pending or done:
                lines.append(
                    f"[任务] {len(done)}完成 {len(pending)}待办 (详情 read .ai_state/tasks.md)"
                )
        except Exception:
            pass

    if not lines:
        sys.exit(0)

    payload = "\n".join(lines)
    sys.stderr.write(f"[session-start/{source}] injected {len(payload)} chars\n")

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": payload,
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
