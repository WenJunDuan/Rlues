#!/usr/bin/env python3
"""
VibeCoding Athena v9.9.6 · Codex index updater (UserPromptSubmit/PostToolUse, 见 hooks.json)

职责: 扫描 .ai_state/, 更新 _index.md frontmatter counts + pointers.

v9.6.4 改动 (vs v9.6.2):
- sprints/ 替代 details/ → 按 path 字段分类计数
- compound/ 替代 lessons.md → 按 doc_type 分类计数 + 按 git 提交时间取 latest 5
- 维护 latest_architecture_update（ARCHITECTURE.md 最后提交时间）

v9.9.0 新: re-route 机械触发 — sprint 改动文件数超路径上限 (Quick>3 / Bugfix>3 / Feature>10)
  且 stage ∈ {impl, runtime-verify} 且 next_action 为空 → 写 next_action="re-route" (只升不降的地板检测)

非阻塞.
"""
import datetime
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys_path_parent = Path(__file__).resolve().parent
if str(sys_path_parent) not in sys.path:
    sys.path.insert(0, str(sys_path_parent))
import _index_io  # noqa: E402
from _index_bounds import enforce_index_bounds  # noqa: E402

EXIT_SUCCESS = 0

# v9.9.0: re-route 机械触发的路径文件数上限 (铁律[分诊] 地板检测)
PATH_FILE_CAPS = {"Quick": 3, "Bugfix": 3, "Feature": 10}


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


def read_sprint_path(sprint_dir: Path) -> str:
    """读 sprint 目录里第一个含 path: 字段的文件."""
    for candidate in ["design.md", "brainstorm.md", "checklist.yaml"]:
        fp = sprint_dir / candidate
        if fp.exists():
            try:
                content = fp.read_text(encoding="utf-8")
                m = re.search(r'^path:\s*["\']?(\w+)["\']?', content, re.MULTILINE)
                if m:
                    return m.group(1)
            except Exception:
                pass
    return ""


def parse_doc_type(filename: str) -> str | None:
    m = re.match(r"^\d{4}-\d{2}-\d{2}-(\w+)-.*\.md$", filename)
    return m.group(1) if m else None


def scan_sprints(ai_state: Path):
    sprints_dir = ai_state / "sprints"
    counts = {"features": 0, "issues": 0, "refactors": 0, "systems": 0, "reviews": 0, "cleanup": 0}
    if not sprints_dir.exists():
        return counts
    for sprint_dir in sprints_dir.iterdir():
        if not sprint_dir.is_dir():
            continue
        path_type = read_sprint_path(sprint_dir)
        if path_type in ("Feature", "Quick", "Hotfix"):
            counts["features"] += 1
        elif path_type == "Bugfix":
            counts["issues"] += 1
        elif path_type == "Refactor":
            counts["refactors"] += 1
        elif path_type == "System":
            counts["systems"] += 1
        reviews_dir = sprint_dir / "reviews"
        if reviews_dir.exists():
            counts["reviews"] += sum(1 for f in reviews_dir.iterdir() if f.is_file() and f.suffix == ".md")
        if (sprint_dir / "cleanup-pass.md").exists():
            counts["cleanup"] += 1
    return counts


def git_commit_times(ai_state: Path, files: list[Path], scopes: list[Path]) -> dict[str, str] | None:
    """Return each tracked file's latest commit time from one batched git log."""
    if not files or not scopes:
        return None
    try:
        repo_root = Path(subprocess.run(
            ["git", "-C", str(ai_state), "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip())
        relative_to_absolute = {
            os.path.relpath(file.resolve(), repo_root).replace(os.sep, "/"): str(file.resolve())
            for file in files
        }
        scope_paths = list(dict.fromkeys(
            os.path.relpath(scope.resolve(), repo_root).replace(os.sep, "/") for scope in scopes
        ))
        output = subprocess.run(
            ["git", "-C", str(repo_root), "log", "--format=%cI%x00", "--name-only", "-z", "--", *scope_paths],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        times: dict[str, str] = {}
        current_time = ""
        timestamp = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$")
        for raw_token in output.split("\0"):
            token = raw_token.lstrip("\n")
            if timestamp.fullmatch(token):
                current_time = token
            elif token in relative_to_absolute and current_time:
                times.setdefault(relative_to_absolute[token], current_time)
        return times
    except (OSError, subprocess.SubprocessError) as exc:
        sys.stderr.write(f"[index-updater] git metadata unavailable; falling back to mtime: {exc}\n")
        return None


def scan_compound(ai_state: Path, git_times: dict[str, str] | None):
    compound_dir = ai_state / "compound"
    counts = {"learning": 0, "trick": 0, "decision": 0, "explore": 0}
    by_type = {"learning": [], "trick": [], "decision": [], "explore": []}
    if not compound_dir.exists():
        return counts, by_type
    for f in compound_dir.iterdir():
        if not f.is_file():
            continue
        dt = parse_doc_type(f.name)
        if dt in counts:
            counts[dt] += 1
            commit_time = git_times.get(str(f.resolve())) if git_times else None
            sort_time = datetime.datetime.fromisoformat(commit_time).timestamp() if commit_time else f.stat().st_mtime
            by_type[dt].append((f.name, sort_time))
    for t in by_type:
        by_type[t].sort(key=lambda x: x[1], reverse=True)
        by_type[t] = [f"compound/{name}" for name, _ in by_type[t][:5]]
    return counts, by_type


def scan_architecture(ai_state: Path, git_times: dict[str, str] | None):
    arch = ai_state / "architecture" / "ARCHITECTURE.md"
    if not arch.exists():
        return ""
    commit_time = git_times.get(str(arch.resolve())) if git_times else None
    if commit_time:
        return commit_time
    return datetime.datetime.utcfromtimestamp(arch.stat().st_mtime).isoformat() + "Z"


def scan_requirements(ai_state: Path):
    # v9.8.0: requirements/{slug}.md 长效需求档计数 + 最新指针
    req_dir = ai_state / "requirements"
    if not req_dir.exists():
        return 0, ""
    files = [f for f in req_dir.iterdir() if f.is_file() and f.suffix == ".md"]
    latest = ""
    latest_mtime = 0.0
    for f in files:
        m = f.stat().st_mtime
        if m > latest_mtime:
            latest_mtime = m
            latest = f"requirements/{f.name}"
    return len(files), latest


def update_field(content: str, field: str, value) -> str:
    if isinstance(value, list):
        val_str = "[" + ", ".join(f'"{v}"' for v in value) + "]"
    elif isinstance(value, int):
        val_str = str(value)
    else:
        val_str = f'"{value}"'
    re_obj = re.compile(rf"^(\s*{field}:\s*).*$", re.MULTILINE)
    if re_obj.search(content):
        return re_obj.sub(rf"\g<1>{val_str}", content)
    return content


def read_fm_field(content: str, field: str) -> str:
    """从 _index.md frontmatter 读字段 (风格同 pre-bash-guard.read_field)."""
    m = re.search(rf'^{field}:\s*["\']?([^"\n]*)["\']?', content, re.MULTILINE)
    return m.group(1).strip() if m else ""


def check_reroute(content: str, ai_state: Path) -> str:
    """v9.9.0: re-route 机械触发 (铁律[分诊] 地板检测, 只升不降).

    stage ∈ {impl, runtime-verify} 且 next_action 为空时, 统计 git 现场变更集中的
    非 .ai_state 改动文件数; 超路径上限 → 写 next_action="re-route" + stderr 提示。
    W36: 与 ship 共享 git 单一真相, 不依赖普通工具 raw trace 或停产账本。
    """
    fm_path = read_fm_field(content, "path")
    fm_stage = read_fm_field(content, "stage")
    fm_sprint = read_fm_field(content, "current_sprint_slug")
    fm_next_action = read_fm_field(content, "next_action")
    # hotfix2 AC6/W37: next_action 枚举告警
    if not re.fullmatch(r"(|re-route|runtime-verify|review|polish|ship|rework_impl|await-review-result|next_roadmap_item:[A-Za-z0-9._-]+|roadmap_complete)", fm_next_action or ""):
        sys.stderr.write(f"[index-updater] next_action 非枚举值 — 进度散文请写 route_history/design\n")
    if fm_path not in PATH_FILE_CAPS or fm_stage not in ("impl", "runtime-verify"):
        return content
    if not fm_sprint or fm_next_action:
        return content
    # F1/W36 (2026-07-29): re-route 改用 git 现场变更集 (tool-trace 已停产, W35)。
    import subprocess
    seen = set()
    for args in (["diff","--name-only"],["diff","--name-only","--cached"],["ls-files","--others","--exclude-standard"]):
        try:
            out = subprocess.run(["git",*args], cwd=str(ai_state.parent), capture_output=True, text=True, timeout=10).stdout
            for f in out.splitlines():
                fp = f.strip()
                if fp and ".ai_state/" not in fp.replace("\\","/"):
                    seen.add(fp)
        except Exception:
            pass  # 非 git 环境: 不触发
    if len(seen) > PATH_FILE_CAPS[fm_path]:
        content = update_field(content, "next_action", "re-route")
        sys.stderr.write(
            f"[index-updater] re-route: path={fm_path} 改动 {len(seen)} 文件 > 上限 {PATH_FILE_CAPS[fm_path]} — "
            "重走路由审议 (只升不降), _index.route_history 记一条\n"
        )
    return content


def main() -> int:
    try:
        # A3 (2026-07-28, 台账 W22): 按写入面分流 — 写 .ai_state 才重扫 counts/pointers;
        # 写实现文件才查 re-route。payload 缺失/无路径 → 旧全量行为 (fail-open)。
        try:
            payload = json.load(sys.stdin) if not sys.stdin.isatty() else {}
        except Exception:
            payload = {}
        if not isinstance(payload, dict):
            payload = {}
        tool_input = payload.get("tool_input") if isinstance(payload.get("tool_input"), dict) else {}
        written = str(tool_input.get("file_path") or tool_input.get("path") or "").replace("\\", "/")
        # K2 (2026-07-28, 台账 W32): CX 布线在 UserPromptSubmit + PostToolUse(Bash|MCP) 也跑本
        # hook, 这些事件 payload 无写入路径 → 旧逻辑 fail-open 全量扫 = 每条消息/每次 Bash 都
        # 交全扫税 (实测 327 Bash/sprint)。无写入路径直接 no-op: counts/pointers 只在 .ai_state
        # 写入时刷新, re-route 只在实现写入 (含 apply_patch 路径) 时检查。
        if not written and isinstance(tool_input, dict):
            cmd = tool_input.get("command")
            if isinstance(cmd, str) and "File:" in cmd:
                import re as _re2
                mm = _re2.search(r"(?:Update|Add) File: (\S+)", cmd)
                if mm:
                    written = mm.group(1)
        if not written:
            return EXIT_SUCCESS
        is_state_write = ".ai_state/" in written
        do_scan = is_state_write
        do_reroute = not is_state_write

        cwd = Path(payload.get("cwd")) if isinstance(payload.get("cwd"), str) and payload.get("cwd") else Path.cwd()
        ai_state = find_ai_state(cwd)
        if ai_state is None:
            return EXIT_SUCCESS

        idx_path = ai_state / "_index.md"
        if not idx_path.exists():
            return EXIT_SUCCESS

        if not _index_io.acquire(idx_path):
            return EXIT_SUCCESS

        content = idx_path.read_text(encoding="utf-8")
        content_before = content
        if do_scan:

            sprint_counts = scan_sprints(ai_state)
            content = update_field(content, "features_count", sprint_counts["features"])
            content = update_field(content, "issues_count", sprint_counts["issues"])
            content = update_field(content, "refactors_count", sprint_counts["refactors"])
            content = update_field(content, "systems_count", sprint_counts["systems"])
            content = update_field(content, "reviews_count", sprint_counts["reviews"])
            content = update_field(content, "cleanup_count", sprint_counts["cleanup"])

            compound_dir = ai_state / "compound"
            compound_files = [f for f in compound_dir.iterdir() if f.is_file()] if compound_dir.exists() else []
            arch = ai_state / "architecture" / "ARCHITECTURE.md"
            git_times = git_commit_times(
                ai_state,
                [*compound_files, *([arch] if arch.exists() else [])],
                [*([compound_dir] if compound_dir.exists() else []), *([arch] if arch.exists() else [])],
            )
            cmp_counts, by_type = scan_compound(ai_state, git_times)
            # compound nested counts (in counts.compound)
            # v9.9.0 修: 限定 compound: 块内替换 (旧实现撞任意同名缩进键)
            # Keep the trailing newline inside the nested block.  The previous
            # optional-newline pattern could leave the next heading adjacent to the
            # final item after replacement (`explore: 0# === Pointers ===`).
            cmp_block = re.search(r"^(\s*)compound:\s*\n((?:\1\s+\S.*(?:\n|$))*)", content, re.MULTILINE)
            if cmp_block:
                block = cmp_block.group(2)
                new_block = block
                for k, v in cmp_counts.items():
                    new_block = re.sub(rf"^(\s+{k}:\s*)\d+\s*$", rf"\g<1>{v}", new_block, count=1, flags=re.MULTILINE)
                if new_block and not new_block.endswith("\n"):
                    new_block += "\n"
                content = content.replace(cmp_block.group(0), cmp_block.group(0).replace(block, new_block), 1)
            content = re.sub(
                r"^(\s+explore:\s*\d+)#\s*(=== Pointers ===)",
                r"\1\n# \2",
                content,
                flags=re.MULTILINE,
            )

            content = update_field(content, "latest_decisions", by_type["decision"])
            content = update_field(content, "latest_lessons", by_type["learning"])

            arch_mtime = scan_architecture(ai_state, git_times)
            if arch_mtime:
                content = update_field(content, "latest_architecture_update", arch_mtime)

            # v9.8.0: requirements/ count + latest pointer
            req_count, req_latest = scan_requirements(ai_state)
            content = update_field(content, "requirements_count", req_count)
            if req_latest:
                content = update_field(content, "latest_requirement", req_latest)

        # v9.9.0: re-route 机械触发 (铁律[分诊] 地板检测, 只升不降)
        if do_reroute:
            content = check_reroute(content, ai_state)

        content = enforce_index_bounds(content, ai_state)

        if content != content_before:
            _index_io.write_atomic(idx_path, content)   # A3: 无变化不写
        return EXIT_SUCCESS
    except Exception as e:
        sys.stderr.write(f"[index-updater] non-blocking: {e}\n")
        return EXIT_SUCCESS
    finally:
        if "idx_path" in locals():
            _index_io.release(idx_path)


if __name__ == "__main__":
    sys.exit(main())
