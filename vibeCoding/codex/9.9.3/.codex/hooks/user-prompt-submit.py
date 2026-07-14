#!/usr/bin/env python3
"""
VibeCoding Athena v9.9.3 · Codex UserPromptSubmit hook (stage-breadcrumb)

职责: 每轮注入当前 stage 义务面包屑 (≤10 行), 替代 "pace SKILL 每 sprint 必读" 固定税.
设计: parser-only — 文案唯一真相在 skills/pace/references/stages.md 对应 `## {stage}` 段,
      本 hook 只切段不持副本 (借 Trellis workflow-state; 与 CC stage-breadcrumb.cjs 对等).
Fail-open: 任何解析失败 → 零注入零报错 (delivery-gate 另有兜底).
开关: _index.breadcrumb: "off" 关闭 (默认开).

源: https://developers.openai.com/codex/hooks (UserPromptSubmit 事件)
"""
import json
import os
import re
import sys

EXIT_SUCCESS = 0
MAX_LINES = 10
FRAME_LINES = 2
SECTION_LINES = MAX_LINES - FRAME_LINES


def find_ai_state(cwd: str):
    current = cwd
    for _ in range(5):
        candidate = os.path.join(current, ".ai_state")
        if os.path.isdir(candidate):
            return candidate
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent
    return None


def parse_frontmatter(path: str) -> dict:
    if not os.path.isfile(path):
        return {}
    try:
        content = open(path, encoding="utf-8").read()
        if not content.startswith("---"):
            return {}
        parts = content.split("---", 2)
        if len(parts) < 3:
            return {}
        fm = {}
        for line in parts[1].split("\n"):
            t = line.strip()
            if not t or t.startswith("#"):
                continue
            m = re.match(r"^([\w\-_.]+)\s*:\s*(.*)$", t)
            if not m:
                continue
            v = m.group(2).strip()
            q = re.match(r'^"([^"]*)"|^\'([^\']*)\'', v)
            if q:
                v = q.group(1) if q.group(1) is not None else q.group(2)
            else:
                idx = v.find(" #")
                if idx >= 0:
                    v = v[:idx].strip()
            fm[m.group(1)] = v
        return fm
    except Exception:
        return {}


def locate_stages_path():
    candidates = (
        ("~/.agents/skills/pace/references/stages.md", "~/.agents/skills/pace/references/stages.md"),
        ("~/.codex/skills/pace/references/stages.md", "~/.codex/skills/pace/references/stages.md"),
    )
    for raw_path, display_path in candidates:
        expanded = os.path.expanduser(raw_path)
        if os.path.isfile(expanded):
            return expanded, display_path
    return None, None


def extract_stage_section(stage: str):
    stages_path, display_path = locate_stages_path()
    if not stages_path:
        return None, None
    lines = open(stages_path, encoding="utf-8").read().split("\n")
    head = re.compile(r"^## " + re.escape(stage) + r"\b")
    start = -1
    for i, line in enumerate(lines):
        if head.match(line):
            start = i
            break
    if start < 0:
        return None
    picked = []
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        if not line.strip():
            continue
        picked.append(line)
        if len(picked) >= SECTION_LINES:
            break
    return ("\n".join(picked), display_path) if picked else (None, display_path)


def main() -> int:
    try:
        try:
            json.load(sys.stdin) if not sys.stdin.isatty() else {}
        except Exception:
            pass
        ai_state = find_ai_state(os.getcwd())
        if not ai_state:
            return EXIT_SUCCESS
        fm = parse_frontmatter(os.path.join(ai_state, "_index.md"))
        if fm.get("breadcrumb", "on") == "off":
            return EXIT_SUCCESS
        stage = (fm.get("stage") or "").strip()
        if not stage:
            return EXIT_SUCCESS
        section, stages_display_path = extract_stage_section(stage)
        if not section:
            return EXIT_SUCCESS
        head = f"[PACE] stage={stage}"
        if fm.get("path"):
            head += f" · path={fm['path']}"
        if fm.get("current_sprint_slug"):
            head += f" · sprint={fm['current_sprint_slug']}"
        if fm.get("next_action"):
            head += f" · next_action={fm['next_action']}"
        tail = f'(全文/前后 stage: 读 {stages_display_path} · 关闭: _index.breadcrumb: "off")'
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": f"{head}\n{section}\n{tail}",
            }
        }, ensure_ascii=False))
        return EXIT_SUCCESS
    except Exception:
        return EXIT_SUCCESS  # fail-open


if __name__ == "__main__":
    sys.exit(main())
