#!/usr/bin/env python3
"""
VibeCoding SessionStart hook — 在 Codex 每次 session 启动时注入 VibeCoding 上下文。
等价 CC 端的 post-compact-restore, 因为 Codex 不提供 PreCompact/PostCompact hook。

输出模式:
- stdout 的普通 text → Codex 当作 developer context 追加到 session
- JSON with continue/stopReason/systemMessage → controlled output
"""
import json
import os
import re
import sys
from pathlib import Path


def main():
    # 读入事件, 但我们不依赖事件字段, 只在任何 startup/resume 场景都注入
    try:
        json.load(sys.stdin)
    except Exception:
        pass

    project_dir = Path(os.environ.get("PWD") or os.getcwd())
    state_dir = project_dir / ".ai_state"
    essentials_path = Path.home() / ".codex" / "skills" / "pace" / "context-essentials.md"

    lines = []
    source = "fallback"

    # 1. 注入 context-essentials.md (铁律 + Get-bearings)
    try:
        text = essentials_path.read_text(encoding="utf-8").strip()
        if text:
            lines.append(text)
            source = "context-essentials.md"
    except Exception:
        lines.append(
            "[VibeCoding] TDD · Review · Sisyphus · 设计先行\n"
            "[Get-bearings] 读 project.json → progress.md → lessons.md → git log → tasks.md → init.sh"
        )

    # 2. 注入当前 project 状态 (如果在 VibeCoding 项目里)
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

    # 3. 注入 tasks 概况
    tasks_md = state_dir / "tasks.md"
    if tasks_md.is_file():
        try:
            t = tasks_md.read_text(encoding="utf-8")
            pending = re.findall(r"^- \[ \].*", t, flags=re.MULTILINE)
            done = re.findall(r"^- \[x\].*", t, flags=re.MULTILINE)
            if pending or done:
                lines.append(f"\n[任务] {len(done)}完成 {len(pending)}待办")
                if 0 < len(pending) <= 5:
                    for line in pending:
                        lines.append("  " + line)
        except Exception:
            pass

    if not lines:
        sys.exit(0)

    payload = "\n".join(lines)
    sys.stderr.write(
        f"[session-start] injected {len(payload)} chars ({source})\n"
    )
    # Codex SessionStart: plain stdout → developer context
    print(payload)
    sys.exit(0)


if __name__ == "__main__":
    main()
