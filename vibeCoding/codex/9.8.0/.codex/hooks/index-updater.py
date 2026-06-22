#!/usr/bin/env python3
"""
VibeCoding Athena v9.6.4 · Codex PostToolUse(Edit|Write) hook (index-updater)

职责: 扫描 .ai_state/, 更新 _index.md frontmatter counts + pointers.

v9.6.4 改动 (vs v9.6.2):
- sprints/ 替代 details/ → 按 path 字段分类计数
- compound/ 替代 lessons.md → 按 doc_type 分类计数 + latest 5 列表
- 维护 latest_architecture_update

非阻塞.
"""
import datetime
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


def scan_compound(ai_state: Path):
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
            by_type[dt].append((f.name, f.stat().st_mtime))
    for t in by_type:
        by_type[t].sort(key=lambda x: x[1], reverse=True)
        by_type[t] = [f"compound/{name}" for name, _ in by_type[t][:5]]
    return counts, by_type


def scan_architecture(ai_state: Path):
    arch = ai_state / "architecture" / "ARCHITECTURE.md"
    if not arch.exists():
        return ""
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


def main() -> int:
    try:
        cwd = Path.cwd()
        ai_state = find_ai_state(cwd)
        if ai_state is None:
            return EXIT_SUCCESS

        idx_path = ai_state / "_index.md"
        if not idx_path.exists():
            return EXIT_SUCCESS

        content = idx_path.read_text(encoding="utf-8")

        sprint_counts = scan_sprints(ai_state)
        content = update_field(content, "features_count", sprint_counts["features"])
        content = update_field(content, "issues_count", sprint_counts["issues"])
        content = update_field(content, "refactors_count", sprint_counts["refactors"])
        content = update_field(content, "systems_count", sprint_counts["systems"])
        content = update_field(content, "reviews_count", sprint_counts["reviews"])
        content = update_field(content, "cleanup_count", sprint_counts["cleanup"])

        cmp_counts, by_type = scan_compound(ai_state)
        # compound nested counts (in counts.compound)
        # 简化: 直接匹配 learning/trick/decision/explore 行
        for k, v in cmp_counts.items():
            re_nested = re.compile(rf"^(\s+{k}:\s*)\d+\s*$", re.MULTILINE)
            if re_nested.search(content):
                content = re_nested.sub(rf"\g<1>{v}", content)

        content = update_field(content, "latest_decisions", by_type["decision"])
        content = update_field(content, "latest_lessons", by_type["learning"])

        arch_mtime = scan_architecture(ai_state)
        if arch_mtime:
            content = update_field(content, "latest_architecture_update", arch_mtime)

        # v9.8.0: requirements/ count + latest pointer
        req_count, req_latest = scan_requirements(ai_state)
        content = update_field(content, "requirements_count", req_count)
        if req_latest:
            content = update_field(content, "latest_requirement", req_latest)

        idx_path.write_text(content, encoding="utf-8")
        return EXIT_SUCCESS
    except Exception as e:
        sys.stderr.write(f"[index-updater] non-blocking: {e}\n")
        return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())
