#!/usr/bin/env python3
"""athena-metrics — hotfix2 AC9/F2 度量仪器 (git 单源, 离线).

用法: python3 athena-metrics.py <repo_root> <sprint_slug> [base_ref]
输出: 手写md字节 / 代码diff字节 / 状态字节 / commit 数 — 替代已停产的 tool-trace 占比口径。
"""
import subprocess, sys, re
from pathlib import Path

CODE_EXT = re.compile(r"\.(ts|tsx|js|jsx|cjs|mjs|py|rs|go|java|rb|c|cc|cpp|h|sql|sh|toml|json)$")

def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True).stdout

def main():
    root, slug = sys.argv[1], sys.argv[2]
    base = sys.argv[3] if len(sys.argv) > 3 else "HEAD~1"
    stat = git(root, "diff", "--numstat", f"{base}..HEAD")
    code = md = state = 0
    for row in stat.splitlines():
        cols = row.split("\t")
        if len(cols) < 3:
            continue
        add = 0 if cols[0] == "-" else int(cols[0])
        rm = 0 if cols[1] == "-" else int(cols[1])
        f = cols[2]
        lines = add + rm
        if f.startswith(".ai_state/"):
            state += lines
            if f.startswith(f".ai_state/sprints/{slug}/") and f.endswith(".md"):
                md += lines
        elif CODE_EXT.search(f):
            code += lines
    commits = git(root, "rev-list", "--count", f"{base}..HEAD").strip()
    print(f"sprint={slug} base={base}")
    print(f"code_diff_lines={code}")
    print(f"handwritten_sprint_md_lines={md}")
    print(f"state_lines_total={state}")
    print(f"commits={commits}")
    print(f"verdict_ac2={'PASS' if md <= max(code,1) else 'FAIL'} (手写md<=代码diff)")

if __name__ == "__main__":
    main()
