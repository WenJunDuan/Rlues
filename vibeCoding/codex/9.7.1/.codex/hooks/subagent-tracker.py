#!/usr/bin/env python3
"""
VibeCoding Athena v9.7.0 · Codex SubagentStop hook (新)

职责:
  1. SubagentStop 触发时写 sprints/{slug}/subagent-log.md
  2. 更新 _index.md last_subagent + last_subagent_at

⚠️ 铁律[不臆造] 声明: SubagentStop 是 CX 原生事件 [官方
developers.openai.com/codex/hooks 共享 JSON 字段列表], 但 payload 中
subagent 标识字段的确切名称未在官方 Schemas 页核验到. 本 hook 防御式
读取候选字段 (subagent_name / agent_name / subagent_type / name),
全部缺失时记 "unknown". 待 dogfood 确认后收敛为单一字段.

roadmap 自动推进逻辑保留在 subagent-retry.py (PostToolUse Bash, 已验证可用),
本 hook 不重复 (零减负 + 不重叠).
非阻塞: 任何异常 exit 0.
"""
import datetime
import json
import re
import sys
from pathlib import Path

FIELD_CANDIDATES = ("subagent_name", "agent_name", "subagent_type", "name")


def find_ai_state(cwd: Path):
    current = cwd
    for _ in range(5):
        candidate = current / ".ai_state"
        if candidate.is_dir():
            return candidate
        if current.parent == current:
            return None
        current = current.parent
    return None


def read_field(idx_path: Path, field: str) -> str:
    try:
        content = idx_path.read_text(encoding="utf-8")
        m = re.search(rf'^{field}:\s*["\']?([^"\n]*)["\']?', content, re.MULTILINE)
        return m.group(1).strip() if m else ""
    except Exception:
        return ""


def update_field(idx_path: Path, field: str, value: str) -> None:
    if not idx_path.exists():
        return
    content = idx_path.read_text(encoding="utf-8")
    new_line = f'{field}: "{value}"'
    re_obj = re.compile(rf"^{field}:.*$", re.MULTILINE)
    if re_obj.search(content):
        content = re_obj.sub(new_line, content)
        idx_path.write_text(content, encoding="utf-8")
    # 字段不存在则不强行插入 (模板已含该字段; 缺失说明非 Athena 项目, 跳过)


def main() -> int:
    try:
        try:
            payload = json.load(sys.stdin) if not sys.stdin.isatty() else {}
        except Exception:
            payload = {}

        agent_name = "unknown"
        for k in FIELD_CANDIDATES:
            v = payload.get(k)
            if isinstance(v, str) and v.strip():
                agent_name = v.strip()
                break

        ai_state = find_ai_state(Path.cwd())
        if ai_state is None:
            return 0
        idx_path = ai_state / "_index.md"
        if not idx_path.exists():
            return 0

        ts = datetime.datetime.utcnow().isoformat() + "Z"
        update_field(idx_path, "last_subagent", agent_name)
        update_field(idx_path, "last_subagent_at", ts)

        sprint_slug = read_field(idx_path, "current_sprint_slug")
        if sprint_slug:
            log_path = ai_state / "sprints" / sprint_slug / "subagent-log.md"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            if not log_path.exists():
                log_path.write_text(f"# Subagent Log — {sprint_slug}\n\n", encoding="utf-8")
            with log_path.open("a", encoding="utf-8") as f:
                f.write(f"## {ts} · {agent_name} (SubagentStop)\n\n")

        return 0
    except Exception as e:
        sys.stderr.write(f"[subagent-tracker] non-blocking: {e}\n")
        return 0


if __name__ == "__main__":
    sys.exit(main())
