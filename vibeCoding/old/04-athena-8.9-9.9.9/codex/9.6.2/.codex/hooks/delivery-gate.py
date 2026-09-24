#!/usr/bin/env python3
"""
VibeCoding Athena v9.6.2 · Codex Stop hook (delivery-gate)

触发: 主 agent stop (即将 turn 结束)
职责:
1. 读 .ai_state/_index.md frontmatter
2. 判断当前 stage 是否符合 ship 条件
3. v9.6.2 新增 (Sprint D): Refactor/System 路径 + stage=ship 时, 强制检查 cleanup-pass-{N}.md 存在

退出码:
- 0: 允许结束
- 2: 阻止结束 (用 top-level decision:"block" + stderr 反馈)

源:
- https://developers.openai.com/codex/hooks (Stop 事件输出协议)
- v9.6.1 hotfix: Stop hook 必须用 top-level decision:"block", 不是 hookSpecificOutput.stopDecision
"""
import json
import re
import sys
from pathlib import Path

EXIT_SUCCESS = 0
EXIT_BLOCK = 2

REFACTOR_SYSTEM = {"Refactor", "System"}


def find_ai_state(cwd: Path) -> Path | None:
    for _ in range(5):
        if (cwd / ".ai_state").is_dir():
            return cwd / ".ai_state"
        if cwd.parent == cwd:
            return None
        cwd = cwd.parent
    return None


def parse_frontmatter(content: str) -> dict:
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    fm: dict = {}
    for line in parts[1].splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([\w\-_.]+)\s*:\s*(.*)$", line)
        if m:
            k, v = m.group(1), m.group(2).strip()
            if v.startswith('"') and v.endswith('"'):
                v = v[1:-1]
            fm[k] = v
    return fm


def block(reason: str) -> int:
    """统一的 block 响应 (Codex Stop hook 协议)."""
    output = {
        "decision": "block",
        "reason": reason,
    }
    sys.stderr.write(reason + "\n")
    print(json.dumps(output))
    return EXIT_BLOCK


def main() -> int:
    try:
        try:
            payload = json.load(sys.stdin) if not sys.stdin.isatty() else {}
        except Exception:
            payload = {}

        cwd = Path.cwd()
        ai_state = find_ai_state(cwd)
        if ai_state is None:
            # 项目未 init, 不干预
            return EXIT_SUCCESS

        idx = ai_state / "_index.md"
        if not idx.exists():
            return EXIT_SUCCESS

        content = idx.read_text(encoding="utf-8")
        fm = parse_frontmatter(content)

        path = fm.get("path", "")
        stage = fm.get("stage", "")
        sprint = fm.get("current_sprint", "1")

        # ============ v9.6.2 新增: polish 强制检查 (Sprint D) ============
        if path in REFACTOR_SYSTEM and stage == "ship":
            cleanup_file = ai_state / "details" / f"cleanup-pass-{sprint}.md"
            if not cleanup_file.exists():
                return block(
                    f"[delivery-gate] Refactor/System 路径必须先完成 polish stage.\n"
                    f"运行 /polish (或主 agent 进入 polish stage) 生成 "
                    f"{cleanup_file.relative_to(cwd) if cleanup_file.is_relative_to(cwd) else cleanup_file}\n"
                    f"然后再 ship.\n"
                )

        # ============ 原有: pace 状态机基本合规检查 ============
        # 若 stage 缺失或异常, 提示但不阻塞 (容错)
        valid_stages = {"plan", "design", "impl", "review", "polish", "ship"}
        if stage and stage not in valid_stages:
            sys.stderr.write(
                f"[delivery-gate] warning: 未知 stage 值 '{stage}', "
                f"期望 {valid_stages}\n"
            )

        return EXIT_SUCCESS
    except Exception as e:
        sys.stderr.write(f"[delivery-gate] warning (non-blocking): {e}\n")
        return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())
