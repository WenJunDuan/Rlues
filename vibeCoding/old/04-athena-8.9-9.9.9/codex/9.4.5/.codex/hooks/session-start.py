#!/usr/bin/env python3
"""
VibeCoding SessionStart hook (Codex)
matcher: startup / resume / clear (Codex 没有 compact)

输出协议: hookSpecificOutput.{hookEventName, additionalContext}
   或 plain stdout (兼容)

顺手跑一次 lesson-archiver (7 天 draft 自动归档)
"""
import json
import os
import re
import sys
from pathlib import Path


def run_archiver():
    """轻量调用 lesson-archiver."""
    try:
        archiver = Path.home() / ".codex" / "hooks" / "lesson-archiver.py"
        if archiver.is_file():
            import subprocess
            r = subprocess.run(
                ["python3", str(archiver)],
                capture_output=True, text=True, timeout=5
            )
            if r.stderr:
                sys.stderr.write(r.stderr)
    except Exception:
        pass


def main():
    run_archiver()

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
    src = "fallback"

    # 1. 注入 context-essentials.md (优先项目级, 回落全局)
    for p in [project_essentials, global_essentials]:
        try:
            text = p.read_text(encoding="utf-8").strip()
            if text:
                lines.append(text)
                src = str(p)
                break
        except Exception:
            continue

    if not lines:
        lines.append(
            "[VibeCoding] TDD · Review · Sisyphus · 设计先行 · 不懒惰 · 穷尽调研\n"
            "[Get-bearings] 扫 ~/.codex/lessons/INDEX.md → 项目 .ai_state/"
        )

    # 2. 注入全局 lessons INDEX 摘要
    index_path = home / ".codex" / "lessons" / "INDEX.md"
    try:
        idx = index_path.read_text(encoding="utf-8")
        if idx and len(idx) < 3000:
            lines.append("\n--- ~/.codex/lessons/INDEX.md ---")
            lines.append(idx)
        elif len(idx) >= 3000:
            lines.append(
                f"\n[Global Lessons] INDEX.md 过长 ({len(idx)} chars), 主动 cat 查看"
            )
    except Exception:
        pass

    # 3. 注入项目状态
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

    # 4. 注入 tasks 概况
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
        f"[session-start/{source}] injected {len(payload)} chars (essentials: {src})\n"
    )

    # SessionStart 官方协议: hookSpecificOutput.additionalContext
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": payload,
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
