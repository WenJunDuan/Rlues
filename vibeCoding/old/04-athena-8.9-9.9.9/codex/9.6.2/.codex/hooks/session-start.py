#!/usr/bin/env python3
"""
VibeCoding Athena v9.6.2 · Codex SessionStart hook

触发: session 启动 / resume
职责:
1. 注入 .ai_state/_index.md (若存在) 摘要进 system prompt
2. 注入 ~/.agents/standards/_index.md 摘要 (Sprint B 接入)
3. 检查 .ai_state 是否需要恢复 (PreCompact 类替代)

源: https://developers.openai.com/codex/hooks (SessionStart 事件)
"""
import json
import os
import re
import sys
from pathlib import Path

EXIT_SUCCESS = 0


def find_ai_state(cwd: Path) -> Path | None:
    for _ in range(5):
        if (cwd / ".ai_state").is_dir():
            return cwd / ".ai_state"
        if cwd.parent == cwd:
            return None
        cwd = cwd.parent
    return None


def read_index_summary(ai_state: Path) -> str:
    """读 _index.md frontmatter, 返回简短摘要."""
    idx = ai_state / "_index.md"
    if not idx.exists():
        return ""
    content = idx.read_text(encoding="utf-8")
    # 提取 frontmatter
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm = parts[1]
            return fm.strip()
    return ""


def read_standards_summary() -> str:
    """读 ~/.agents/standards/_index.md, 返回规范摘要 (≤ 600 字符)."""
    home = Path.home()
    standards_idx = home / ".agents" / "standards" / "_index.md"
    if not standards_idx.exists():
        return ""
    content = standards_idx.read_text(encoding="utf-8")
    # 只截取前 600 字符 (避免 system prompt 膨胀)
    if len(content) > 600:
        content = content[:600] + "\n... (see ~/.agents/standards/ for full)"
    return content


def main() -> int:
    try:
        try:
            payload = json.load(sys.stdin) if not sys.stdin.isatty() else {}
        except Exception:
            payload = {}

        cwd = Path.cwd()
        ai_state = find_ai_state(cwd)

        context_parts = []

        if ai_state:
            idx_summary = read_index_summary(ai_state)
            if idx_summary:
                context_parts.append(f"## Athena 项目状态 (.ai_state/_index.md frontmatter)\n\n{idx_summary}")

        std_summary = read_standards_summary()
        if std_summary:
            context_parts.append(f"## 项目规范摘要 (~/.agents/standards/_index.md)\n\n{std_summary}\n\n详细规则按 stage 触发自动加载.")

        if context_parts:
            additional_context = "\n\n---\n\n".join(context_parts)
            # Codex SessionStart hook 通过 stdout JSON 注入 context
            # 源: https://developers.openai.com/codex/hooks SessionStart 输出协议
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": additional_context,
                }
            }
            print(json.dumps(output))

        return EXIT_SUCCESS
    except Exception as e:
        sys.stderr.write(f"[session-start] warning (non-blocking): {e}\n")
        return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())
