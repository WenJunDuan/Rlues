#!/usr/bin/env python3
"""Athena v9.9.6 · Codex 铁律[零写入] 红区 worktree 护栏。

**双事件设计 — PreToolUse 阻断 (已按官方核实) + SubagentStart 纵深审计**

| 事件 | 能力 | 效力 |
|---|---|---|
| ``PreToolUse`` matcher ``spawn_agent|Agent`` | spawn 前阻断 | Codex 0.145 function-tool hook 路径；红区写 agent 没有声明真实的隔离 worktree 时 exit 2 阻断 |
| ``SubagentStart`` | 起来之后检测 | 纵深防御；把已经启动的违规写进 ``sprints/{slug}/worktree-violations.jsonl`` 并由 ship gate 消费 |

``PreToolUse`` 是唯一能在 spawn 前阻断的原生路径 (官方: exit 2 + 阻断原因写 stderr)。
``SubagentStart`` 没有阻断语义 —— ``continue: false`` 仅为兼容解析, 不会阻止 subagent
启动; 它只负责留下可复核的纵深证据, 不宣称能撤销已发生的 spawn。
"""

from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

EXIT_SUCCESS = 0
RED_PATHS = {"Refactor", "System"}
AGENT_KEYS = ("agent_type", "subagent_type", "agent", "name", "role")
TASK_KEYS = ("task", "prompt", "instructions", "input", "message")
WORKTREE_DECLARATION = re.compile(r"(?im)\bworktree\s*[:=]\s*['\"]?(/[^\s'\"]+)")


def find_ai_state(cwd: Path) -> Path | None:
    current = cwd.resolve()
    for _ in range(8):
        if (current / ".ai_state").is_dir():
            return current / ".ai_state"
        if current.parent == current:
            break
        current = current.parent
    return None


def strip_inline_comment(value: str) -> str:
    value = value.strip()
    q = re.match(r'^"([^"]*)"|^\'([^\']*)\'', value)
    if q:
        return q.group(1) if q.group(1) is not None else q.group(2)
    idx = value.find(" #")
    return value[:idx].strip() if idx >= 0 else value


def index_field(idx: Path, field: str) -> str:
    try:
        m = re.search(rf"^{re.escape(field)}\s*:\s*(.*)$", idx.read_text(encoding="utf-8"), re.M)
    except OSError:
        return ""
    return strip_inline_comment(m.group(1)) if m else ""


def pick(container: Any, keys: tuple[str, ...]) -> str:
    if not isinstance(container, dict):
        return ""
    for key in keys:
        v = container.get(key)
        if isinstance(v, str) and v.strip():
            return v
    return ""


READONLY_ROLES = {
    # P0-1 (2026-07-29, W35): 打包的只读角色显式豁免 — 旧逻辑 unknown profile 默认
    # writable, 只读 explorer 被记违规账并在 ship 被 gate 阻断 (hotfix2 实测)。
    "architect", "critic", "reviewer", "spec-compliance", "spec_compliance",
    "evaluator", "explorer", "pr_explorer", "docs_researcher",
}


def agent_writes_files(agent_name: str) -> bool:
    """read-only 角色/沙箱不写文件; 真正未知的 profile 仍保守当作会写 (fail-closed)。"""
    if agent_name in READONLY_ROLES:
        return False
    toml = Path.home() / ".codex" / "agents" / f"{agent_name}.toml"
    if not toml.is_file():
        return True
    m = re.search(r'^\s*sandbox_mode\s*=\s*"([^"]+)"', toml.read_text(encoding="utf-8", errors="ignore"), re.M)
    return not (m and m.group(1) == "read-only")


def worktree_roots(cwd: Path) -> list[Path]:
    try:
        out = subprocess.run(["git", "worktree", "list", "--porcelain"], cwd=str(cwd),
                             capture_output=True, text=True, timeout=5, check=False).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    return [Path(value).resolve() for value in re.findall(r"(?m)^worktree (.+)$", out)]


def declared_is_isolated_worktree(task: str, cwd: Path) -> bool:
    match = WORKTREE_DECLARATION.search(task)
    if not match:
        return False
    declared = Path(match.group(1)).expanduser().resolve()
    roots = worktree_roots(cwd)
    return len(roots) > 1 and declared in roots[1:]


def record_violation(
    ai_state: Path, payload: dict, agent: str, reason: str, *, blocked_before_start: bool
) -> None:
    slug = index_field(ai_state / "_index.md", "current_sprint_slug")
    if not slug or "/" in slug or slug.startswith("."):
        sys.stderr.write("[subagent-worktree-audit] 无安全 sprint slug, 违规未落盘\n")
        return
    d = ai_state / "sprints" / slug
    if not d.is_dir():
        return
    row = {"schema_version": 1,
           "ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "event": str(payload.get("hook_event_name", "")),
           "blocked_before_start": blocked_before_start,
           "resolved": False,
           "agent": agent, "reason": reason,
           "agent_id": pick(payload, ("agent_id", "id")) or None}
    with (d / "worktree-violations.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    event = ""
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
        if not isinstance(payload, dict):
            return EXIT_SUCCESS
        event = str(payload.get("hook_event_name", ""))
        if event not in {"PreToolUse", "SubagentStart"}:
            return EXIT_SUCCESS
        tool_input = payload.get("tool_input") if isinstance(payload.get("tool_input"), dict) else {}
        cwd_v = payload.get("cwd")
        cwd = Path(cwd_v).expanduser() if isinstance(cwd_v, str) and cwd_v.strip() else Path.cwd()
        ai_state = find_ai_state(cwd)
        if ai_state is None or not (ai_state / "_index.md").is_file():
            return EXIT_SUCCESS
        agent = pick(tool_input, AGENT_KEYS) or pick(payload, AGENT_KEYS) or "unknown"
        if agent != "unknown" and not agent_writes_files(agent):
            return EXIT_SUCCESS

        # P9 fix (2026-07-28, .ai_state/proposals.md P9, 两次实测死锁): 改动对象在项目
        # repo 之外时 (安装态 ~/.claude / ~/.codex harness), worktree 对 repo 外路径零隔离
        # 效果, 却无条件阻断唯一合法执行路径。显式出口: _index.harness_target_outside_repo:
        # true (可审计; ship 后应移除)。豁免时提示备份纪律, 不静默。
        if index_field(ai_state / "_index.md", "harness_target_outside_repo").strip().lower() == "true":
            sys.stderr.write(
                "[subagent-worktree-audit] EXEMPT: _index.harness_target_outside_repo=true — "
                "repo 外改动, worktree 无隔离效果, 跳过强制。纪律: 改前逐文件备份 + 单写者串行; ship 后移除该字段。\n"
            )
            return EXIT_SUCCESS

        path_type = index_field(ai_state / "_index.md", "path")
        task = pick(tool_input, TASK_KEYS) or pick(payload, TASK_KEYS)
        in_worktree = declared_is_isolated_worktree(task, cwd)
        parallel = len(worktree_roots(cwd)) > 1

        reason = ""
        if path_type in RED_PATHS and not in_worktree:
            reason = (f"铁律[零写入] 红区: path={path_type}, 写文件的 agent \"{agent}\" "
                      "的任务里没有 worktree 绝对路径。主 thread 应先建 worktree 再把路径写进任务。")
        elif parallel and not in_worktree:
            reason = (f"铁律[零写入] 并行场景: 存在多个 checkout, 写文件的 agent \"{agent}\" "
                      "必须落在自己的 worktree 内。")
        if not reason:
            return EXIT_SUCCESS

        blocked = event == "PreToolUse"
        record_violation(ai_state, payload, agent, reason, blocked_before_start=blocked)
        if blocked:
            sys.stderr.write(f"[subagent-worktree-audit] BLOCKED before spawn: {reason}\n")
            return 2
        sys.stderr.write(f"[subagent-worktree-audit] VIOLATION after agent start: {reason}\n")
        return EXIT_SUCCESS
    except Exception as exc:  # noqa: BLE001 — hook payload 是跨进程信任边界
        # 只有 PreToolUse 有 exit 2 阻断语义; 在 SubagentStart 上返回 2 拦不住任何东西,
        # 只会产生 hook 失败噪声并让日志说谎。事件不可知时保守 fail-closed。
        if event == "SubagentStart":
            sys.stderr.write(f"[subagent-worktree-audit] audit skipped on invalid hook input: {exc}\n")
            return EXIT_SUCCESS
        sys.stderr.write(f"[subagent-worktree-audit] BLOCKED on invalid hook input: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
