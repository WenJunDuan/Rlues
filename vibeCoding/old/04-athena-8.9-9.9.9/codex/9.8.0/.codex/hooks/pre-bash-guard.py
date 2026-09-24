#!/usr/bin/env python3
"""
VibeCoding Athena v9.6.4 · Codex PreToolUse(Bash) hook

触发: 任何 Bash 命令前
职责:
  1. 拦截危险命令 (rm -rf / curl|bash / DROP TABLE 等)
  2. v9.6.4 新: spawn_agent 调用在 Refactor/System 路径必须有 --cwd <worktree-path> (铁律 12 CX 等价)
  3. v9.6.4 新: 检测 git worktree add/remove 命令 → 触发 worktrees.yaml 更新 (CX 无原生 WorktreeCreate/Remove hook)

退出码:
- 0: 允许执行
- 2: 阻止执行

源: https://developers.openai.com/codex/hooks
"""
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

EXIT_SUCCESS = 0
EXIT_BLOCK = 2

P0_PATTERNS = [
    r"\brm\s+-rf?\s+/(\s|$)",
    r"\brm\s+-rf?\s+~(\s|$)",
    r"\brm\s+-rf?\s+\$HOME",
    r"\bcurl\b[^|]*\|\s*bash",
    r"\bwget\b[^|]*\|\s*bash",
    r"\bDROP\s+TABLE\b",
    r":\(\)\s*\{",
    r"\bdd\s+.*of=/dev/(sda|nvme|xvd)",
    r">\s*/dev/(sda|nvme|xvd)",
]

P1_PATTERNS = [
    r"\bgit\s+push\s+(--force|-f)\b",
    r"\bgit\s+reset\s+--hard\s+origin",
    r"\bsudo\b",
]


def is_dangerous(command: str):
    for pat in P0_PATTERNS:
        if re.search(pat, command):
            return True, pat
    return False, None


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
    """从 _index.md frontmatter 读字段."""
    try:
        content = idx_path.read_text(encoding="utf-8")
        m = re.search(rf'^{field}:\s*["\']?([^"\n]*)["\']?', content, re.MULTILINE)
        return m.group(1).strip() if m else ""
    except Exception:
        return ""


def check_spawn_agent_worktree(command: str, path_type: str) -> tuple[bool, str | None]:
    """v9.6.4 铁律 12 CX 等价: spawn_agent 在 Refactor/System 必须 --cwd."""
    if "spawn_agent" not in command:
        return False, None
    if path_type not in ("Refactor", "System"):
        return False, None
    # 检查 --cwd 参数
    if "--cwd" not in command:
        msg = (
            "[pre-bash-guard] BLOCKED: 铁律 12 (CX)\n"
            f"path={path_type} 路径要求 spawn_agent 必须先 git worktree add 后用 --cwd 指定 worktree 路径.\n"
            "示例:\n"
            "  git worktree add ../wt-{slug} -b wt-{slug}\n"
            "  spawn_agent --cwd ../wt-{slug} <agent.toml>\n"
        )
        return True, msg
    return False, None


def track_worktree_command(command: str, ai_state: Path) -> None:
    """v9.6.4: 检测 git worktree add/remove, 写 worktrees.yaml + 更新 _index.active_worktrees.

    CX 无原生 WorktreeCreate/Remove hook, 用 PreToolUse(Bash) 监听等价.
    注: 这里在 PreToolUse 写记录, 实际命令还没跑; 用 PostToolUse 更严谨, 但保持简单.
    """
    m_add = re.match(r"git\s+worktree\s+add\s+(?:-b\s+\S+\s+)?(\S+)", command)
    m_remove = re.match(r"git\s+worktree\s+remove\s+(\S+)", command)
    if not (m_add or m_remove):
        return

    sprint_slug = read_field(ai_state / "_index.md", "current_sprint_slug")
    if not sprint_slug:
        return

    sprint_dir = ai_state / "sprints" / sprint_slug
    sprint_dir.mkdir(parents=True, exist_ok=True)
    yaml_path = sprint_dir / "worktrees.yaml"
    ts = datetime.utcnow().isoformat() + "Z"

    if m_add:
        worktree_path = m_add.group(1)
        worktree_name = Path(worktree_path).name
        if not yaml_path.exists():
            yaml_path.write_text(f"sprint_slug: {sprint_slug}\nworktrees:\n", encoding="utf-8")
        with yaml_path.open("a", encoding="utf-8") as f:
            f.write(
                f'  - name: "{worktree_name}"\n'
                f'    path: "{worktree_path}"\n'
                f'    created_at: "{ts}"\n'
                f'    status: active\n'
            )
        # 更新 _index.active_worktrees (简化版)
        update_active_worktrees(ai_state, worktree_name, "add")
    elif m_remove:
        worktree_path = m_remove.group(1)
        worktree_name = Path(worktree_path).name
        if yaml_path.exists():
            content = yaml_path.read_text(encoding="utf-8")
            # 找匹配 name 改 status
            new_content = re.sub(
                rf'(- name: "{re.escape(worktree_name)}"[\s\S]*?status:)\s*active',
                rf'\1 removed',
                content,
            )
            yaml_path.write_text(new_content, encoding="utf-8")
        update_active_worktrees(ai_state, worktree_name, "remove")


def update_active_worktrees(ai_state: Path, worktree_name: str, action: str) -> None:
    """更新 _index.md.active_worktrees 列表."""
    idx_path = ai_state / "_index.md"
    if not idx_path.exists():
        return
    content = idx_path.read_text(encoding="utf-8")
    m = re.search(r"^(active_worktrees:\s*)(\[.*?\])", content, re.MULTILINE)
    current = []
    if m:
        raw = m.group(2)
        if raw != "[]":
            current = [s.strip().strip('"') for s in raw.strip("[]").split(",") if s.strip()]

    if action == "add" and worktree_name not in current:
        current.append(worktree_name)
    if action == "remove":
        current = [w for w in current if w != worktree_name]

    quoted = ", ".join('"%s"' % w for w in current)
    new_line = f"active_worktrees: [{quoted}]"
    if m:
        new_content = re.sub(r"^active_worktrees:.*$", new_line, content, flags=re.MULTILINE)
        idx_path.write_text(new_content, encoding="utf-8")


def main() -> int:
    try:
        try:
            payload = json.load(sys.stdin) if not sys.stdin.isatty() else {}
        except Exception:
            payload = {}

        tool_input = payload.get("tool_input", {})
        command = tool_input.get("command", "")

        if not command:
            return EXIT_SUCCESS

        # 1. 灾难命令拦截
        dangerous, pat = is_dangerous(command)
        if dangerous:
            sys.stderr.write(
                f"[pre-bash-guard] BLOCKED: 检测到灾难命令模式 ({pat})\n"
                f"命令: {command[:200]}\n"
            )
            return EXIT_BLOCK

        # 2. v9.6.4: spawn_agent worktree 检查
        cwd = Path(os.getcwd())
        ai_state = find_ai_state(cwd)
        if ai_state:
            path_type = read_field(ai_state / "_index.md", "path")
            block, msg = check_spawn_agent_worktree(command, path_type)
            if block:
                sys.stderr.write(msg)
                return EXIT_BLOCK

            # 3. v9.6.4: git worktree add/remove → 等价 WorktreeCreate/Remove hook
            track_worktree_command(command, ai_state)

        return EXIT_SUCCESS
    except Exception as e:
        sys.stderr.write(f"[pre-bash-guard] warning (non-blocking): {e}\n")
        return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())
