#!/usr/bin/env python3
"""
VibeCoding Athena v9.6.2 · Codex index-updater hook

触发: UserPromptSubmit (B3 修复, v9.6.1 用 PostToolUse Bash 永远不触发)

工作流:
1. 找到 .ai_state/_index.md
2. 读 _index.md.fingerprints (上次记录的 details/*.md 的 mtime)
3. 比对 .ai_state/details/ 实际 mtime
4. 不一致 → 重算 counts + features_count + reviews_count, 写回 _index.md.fingerprints

设计原则:
- 单次 IO ≤ 5ms (只读 mtime, 不读内容)
- 退出码: 0 (always 0, 这是非阻塞 hook)
- stdin JSON 不强依赖 (UserPromptSubmit payload 不影响逻辑)
- 失败不阻塞 user prompt 提交 (try/except 兜底)

源: https://developers.openai.com/codex/hooks (UserPromptSubmit 事件)
"""
import json
import os
import re
import sys
from pathlib import Path

# 退出兜底
EXIT_SUCCESS = 0


def find_ai_state(cwd: Path) -> Path | None:
    """从 cwd 向上找 .ai_state 目录, 最多 5 层."""
    for _ in range(5):
        candidate = cwd / ".ai_state"
        if candidate.is_dir():
            return candidate
        if cwd.parent == cwd:
            return None
        cwd = cwd.parent
    return None


def read_index_md(path: Path) -> tuple[dict, str]:
    """读 _index.md, 返回 (frontmatter dict, body str). 没有 frontmatter 则返回 ({}, full_content)."""
    if not path.exists():
        return {}, ""
    content = path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return {}, content
    # 简化 frontmatter parser (不依赖 PyYAML, 避免 stdlib 之外的依赖)
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    fm_raw = parts[1]
    body = parts[2].lstrip("\n")
    fm: dict = {}
    for line in fm_raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([\w\-_.]+)\s*:\s*(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            # 去掉 quote
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            fm[key] = val
    return fm, body


def write_index_md(path: Path, fm: dict, body: str) -> None:
    """写回 _index.md."""
    fm_str = "---\n"
    for k, v in fm.items():
        # 数字不加引号, 字符串加引号
        if isinstance(v, (int, float)):
            fm_str += f"{k}: {v}\n"
        else:
            fm_str += f'{k}: "{v}"\n'
    fm_str += "---\n\n"
    path.write_text(fm_str + body, encoding="utf-8")


def compute_state(ai_state: Path) -> dict:
    """计算当前 .ai_state/details/ 的真实状态."""
    details_dir = ai_state / "details"
    if not details_dir.is_dir():
        return {
            "features_count": 0,
            "reviews_count": 0,
            "cleanup_count": 0,
            "fingerprint": "",
        }

    features_count = 0
    reviews_count = 0
    cleanup_count = 0
    fingerprints = []

    for md_file in sorted(details_dir.rglob("*.md")):
        rel = md_file.relative_to(details_dir)
        mtime = int(md_file.stat().st_mtime)
        fingerprints.append(f"{rel}:{mtime}")

        name = md_file.name
        if name.startswith("feature-") or name == "features.md":
            features_count += 1
        if "review" in name or md_file.parent.name == "reviews":
            reviews_count += 1
        if name.startswith("cleanup-pass-"):
            cleanup_count += 1

    # fingerprint = mtime 集合 hash (用简单字符串拼接代替, 因为只用来 diff 不用密码学强度)
    fp = "|".join(fingerprints)

    return {
        "features_count": features_count,
        "reviews_count": reviews_count,
        "cleanup_count": cleanup_count,
        "fingerprint": fp,
    }


def main() -> int:
    try:
        # 读 stdin (UserPromptSubmit payload, 仅做形式 check, 不阻塞)
        try:
            _payload = json.load(sys.stdin) if not sys.stdin.isatty() else {}
        except Exception:
            _payload = {}

        cwd = Path.cwd()
        ai_state = find_ai_state(cwd)
        if ai_state is None:
            # 没有 .ai_state, 项目未 init, 静默退出
            return EXIT_SUCCESS

        index_path = ai_state / "_index.md"
        fm, body = read_index_md(index_path)

        state = compute_state(ai_state)
        stored_fp = fm.get("fingerprint", "")

        if stored_fp == state["fingerprint"]:
            # mtime 无变化, 跳过更新
            return EXIT_SUCCESS

        # 更新 frontmatter
        fm["features_count"] = state["features_count"]
        fm["reviews_count"] = state["reviews_count"]
        fm["cleanup_count"] = state["cleanup_count"]
        fm["fingerprint"] = state["fingerprint"]

        if index_path.parent.exists():
            write_index_md(index_path, fm, body)

        return EXIT_SUCCESS
    except Exception as e:
        # 严格非阻塞: 任何异常都吞掉, 不影响 UserPromptSubmit
        sys.stderr.write(f"[index-updater] warning (non-blocking): {e}\n")
        return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())
