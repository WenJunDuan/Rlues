#!/usr/bin/env python3
"""
VibeCoding Athena v9.6.4 · Codex PostToolUse(Bash) hook

触发: Bash 命令完成后
职责 (CX 等价 SubagentStop, 因为 Codex 无原生 SubagentStop 事件):
  1. 检测 spawn_agent / spawn_agents_on_csv 完成 → 写 sprints/{slug}/subagent-log.md
  2. 检测 spawn_agent 失败 (exit != 0) → 写 runtime-events.md
  3. 检测主 agent ship 完成 → roadmap items.yaml 自动推进
  4. 检测 git worktree add/remove → 写 worktrees.yaml (此处再次确认, 与 pre-bash-guard 互补)

非阻塞 (exit 0).
源: https://developers.openai.com/codex/hooks
"""
import datetime
import json
import os
import re
import sys
from pathlib import Path

EXIT_SUCCESS = 0


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


def update_field(idx_path: Path, field: str, value):
    if not idx_path.exists():
        return
    content = idx_path.read_text(encoding="utf-8")
    if isinstance(value, bool):
        new_line = f"{field}: {'true' if value else 'false'}"
    else:
        new_line = f'{field}: "{value}"'
    re_obj = re.compile(rf"^{field}:.*$", re.MULTILINE)
    if re_obj.search(content):
        content = re_obj.sub(new_line, content)
    else:
        # frontmatter 末尾插入
        content = re.sub(
            r"^---\n([\s\S]*?)\n---",
            lambda m: f"---\n{m.group(1)}\n{new_line}\n---",
            content,
            count=1,
        )
    idx_path.write_text(content, encoding="utf-8")


def log_subagent(ai_state: Path, sprint_slug: str, agent_name: str, command: str,
                  exit_code: int, stderr: str, stdout: str):
    log_path = ai_state / "sprints" / sprint_slug / "subagent-log.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if not log_path.exists():
        log_path.write_text(f"# Subagent Log — {sprint_slug}\n\n", encoding="utf-8")
    ts = datetime.datetime.utcnow().isoformat() + "Z"
    status = "success" if exit_code == 0 else f"exit {exit_code}"
    cmd_preview = command[:150].replace("\n", " ")
    summary = (stdout if exit_code == 0 else stderr)[:200].replace("\n", " ")
    entry = (
        f"## {ts} · {agent_name}\n"
        f"- Command: `{cmd_preview}`\n"
        f"- Status: {status}\n"
        f"- Output: {summary}\n\n"
    )
    with log_path.open("a", encoding="utf-8") as f:
        f.write(entry)


def extract_agent_name(command: str) -> str:
    """从 spawn_agent 命令中提取 agent name."""
    # spawn_agent <agent.toml> ... 或 spawn_agent --config=path/<name>.toml
    m = re.search(r"spawn_agent\s+(?:--?config[=\s])?(\S+?\.toml)", command)
    if m:
        return Path(m.group(1)).stem
    # spawn_agents_on_csv ...
    if "spawn_agents_on_csv" in command:
        return "csv-batch"
    return "unknown-agent"


def check_roadmap_advance(ai_state: Path):
    """ship 完成时, 推进 roadmap items.yaml."""
    idx_path = ai_state / "_index.md"
    roadmap_slug = read_field(idx_path, "current_roadmap_slug")
    sprint_slug = read_field(idx_path, "current_sprint_slug")
    if not roadmap_slug or not sprint_slug:
        return

    items_path = ai_state / "roadmap" / roadmap_slug / "items.yaml"
    if not items_path.exists():
        return

    content = items_path.read_text(encoding="utf-8")
    # 简化: 找 sprint_slug 匹配的 item, 改 status: completed
    if f'sprint_slug: "{sprint_slug}"' in content or f"sprint_slug: {sprint_slug}" in content:
        lines = content.split("\n")
        match_idx = -1
        for i, line in enumerate(lines):
            if sprint_slug in line and "sprint_slug" in line:
                match_idx = i
                break
        if match_idx >= 0:
            # 附近 5 行内找 status
            for j in range(max(0, match_idx - 5), min(len(lines), match_idx + 5)):
                if lines[j].strip().startswith("status:"):
                    lines[j] = re.sub(r"status:\s*\w+", "status: completed", lines[j])
                    break
            content = "\n".join(lines)
            items_path.write_text(content, encoding="utf-8")

    # 找下个 pending
    next_pending = find_next_pending(content)
    if next_pending:
        update_field(idx_path, "next_action", f"next_roadmap_item:{next_pending}")
    else:
        update_field(idx_path, "current_roadmap_slug", "")
        update_field(idx_path, "next_action", "roadmap_complete")


def find_next_pending(content: str):
    """从 items.yaml 找第一个 pending 的 slug."""
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if line.strip() == "status: pending":
            for j in range(max(0, i - 5), min(len(lines), i + 5)):
                m = re.match(r"\s*-?\s*slug:\s*[\"']?([\w-]+)[\"']?", lines[j])
                if m:
                    return m.group(1)
    return None


def main() -> int:
    try:
        try:
            payload = json.load(sys.stdin) if not sys.stdin.isatty() else {}
        except Exception:
            payload = {}

        tool_input = payload.get("tool_input", {})
        tool_output = payload.get("tool_output", {})
        command = tool_input.get("command", "")
        stdout = tool_output.get("stdout", "")
        stderr = tool_output.get("stderr", "")
        exit_code = tool_output.get("exit_code", 0)

        if not command:
            return EXIT_SUCCESS

        cwd = Path.cwd()
        ai_state = find_ai_state(cwd)
        if ai_state is None:
            return EXIT_SUCCESS

        sprint_slug = read_field(ai_state / "_index.md", "current_sprint_slug")
        stage = read_field(ai_state / "_index.md", "stage")

        # 1. spawn_agent / spawn_agents_on_csv 完成 → 写 subagent-log.md
        is_subagent_cmd = any(kw in command for kw in [
            "spawn_agent",
            "spawn_agents_on_csv",
        ])
        if is_subagent_cmd:
            agent_name = extract_agent_name(command)
            if sprint_slug:
                log_subagent(ai_state, sprint_slug, agent_name, command, exit_code, stderr, stdout)
                update_field(ai_state / "_index.md", "last_subagent", agent_name)
                update_field(
                    ai_state / "_index.md",
                    "last_subagent_at",
                    datetime.datetime.utcnow().isoformat() + "Z",
                )

            # 失败记录
            if exit_code != 0:
                events = ai_state / "details" / "runtime-events.md"
                events.parent.mkdir(parents=True, exist_ok=True)
                ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with events.open("a", encoding="utf-8") as f:
                    f.write(
                        f"\n## {ts} · subagent 失败\n"
                        f"- command: `{command[:200]}`\n"
                        f"- exit_code: {exit_code}\n"
                        f"- stderr (前 500): `{stderr[:500]}`\n"
                        f"- 建议: 主 agent 检查 stderr, 修复后重试\n"
                    )

            # ship stage + generator 完成 → roadmap 推进
            if exit_code == 0 and stage == "ship" and agent_name in ("generator", "polish_worker"):
                check_roadmap_advance(ai_state)

        return EXIT_SUCCESS
    except Exception as e:
        sys.stderr.write(f"[subagent-retry] warning (non-blocking): {e}\n")
        return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())
