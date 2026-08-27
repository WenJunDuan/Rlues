#!/usr/bin/env python3
"""Athena v9.9.6 · Codex PostToolUse hook — design-change-detector.

与 CC ``design-change-detector.cjs`` 语义对等: 检测 ``sprints/{slug}/design.md``
在 impl/review/polish 阶段被修改 → 置 ``design_changed_after_impl=true``,
delivery-gate 在 ship 前据此强制 re-review。

Codex 的 apply_patch payload 结构随版本演进, 因此路径提取是防御式的:
先看常见字段, 再回退到全 payload 文本扫描。任何解析失败一律 fail-open
(退出 0 不写标记) —— 这是流程护栏, 不是安全边界; ship 侧的 fail-closed
判定仍由 delivery-gate 负责。
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _index_io  # noqa: E402
from typing import Any

EXIT_SUCCESS = 0
MARK_STAGES = {"impl", "review", "polish"}
DESIGN_RE = re.compile(r"[\w./-]*/sprints/[^\s\"']+/design\.md")


def find_ai_state(cwd: Path) -> Path | None:
    current = cwd.resolve()
    for _ in range(8):
        if (current / ".ai_state").is_dir():
            return current / ".ai_state"
        if current.parent == current:
            break
        current = current.parent
    return None


def extract_design_path(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        for key in ("file_path", "path", "filename", "target", "file"):
            value = tool_input.get(key)
            if isinstance(value, str) and DESIGN_RE.search(value):
                return value
    blob = json.dumps(payload, ensure_ascii=False)
    match = DESIGN_RE.search(blob)
    return match.group(0) if match else ""


def read_field(idx: Path, field: str) -> str:
    match = re.search(rf'^{re.escape(field)}:\s*["\']?([^"\n]*)["\']?', idx.read_text(encoding="utf-8"), re.M)
    return match.group(1).strip() if match else ""


def set_flag_true(idx: Path, field: str) -> bool:
    pattern = re.compile(rf"^({re.escape(field)}:\s*).*$", re.M)
    # v9.9.6: 读-改-写全程持锁 + 原子替换, 防同事件并发 hook 丢更新
    result = _index_io.update(idx, lambda c: pattern.sub(f"{field}: true", c, count=1) if pattern.search(c) else None)
    return result is not None


def main() -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
        if not isinstance(payload, dict):
            return EXIT_SUCCESS
        if not extract_design_path(payload):
            return EXIT_SUCCESS
        cwd_value = payload.get("cwd")
        cwd = Path(cwd_value).expanduser() if isinstance(cwd_value, str) and cwd_value.strip() else Path.cwd()
        ai_state = find_ai_state(cwd)
        if ai_state is None:
            return EXIT_SUCCESS
        idx = ai_state / "_index.md"
        if not idx.is_file():
            return EXIT_SUCCESS
        stage = read_field(idx, "stage")
        if stage not in MARK_STAGES:
            return EXIT_SUCCESS
        if set_flag_true(idx, "design_changed_after_impl"):
            sys.stderr.write(
                f"[design-change-detector] design.md 在 {stage} stage 被修改; "
                "已置 design_changed_after_impl=true, ship 前需重新 review\n"
            )
    except Exception as exc:  # noqa: BLE001 — 流程护栏 fail-open
        sys.stderr.write(f"[design-change-detector] non-blocking: {exc}\n")
    return EXIT_SUCCESS


if __name__ == "__main__":
    raise SystemExit(main())
