#!/usr/bin/env python3
"""Athena v9.9.6 · Codex Stop hook — pace-continuator (与 CC 同构)。

1. 在 ``_index.md`` 的 ``## 历史`` 段追加 ``stage=X sprint=N turn-end`` (去重, 保留近 10 条);
2. 通过 ``hookSpecificOutput.additionalContext`` 输出软提醒, 不 block。

恒退出 0。软提醒只在首次自然停止时给一次 —— 每次 Stop 都喂同一段会让会话停不下来。
"""

from __future__ import annotations

import datetime as dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _index_io  # noqa: E402

EXIT_SUCCESS = 0
HIST_MARKER = "## 历史"
HIST_KEEP = 10
CTX_LIMIT = 9000


def find_ai_state(cwd: Path) -> Path | None:
    current = cwd.resolve()
    for _ in range(8):
        if (current / ".ai_state").is_dir():
            return current / ".ai_state"
        if current.parent == current:
            break
        current = current.parent
    return None


def fm_field(fm: str, field: str) -> str:
    match = re.search(rf'{re.escape(field)}:\s*"?([^"\n]*)"?', fm)
    return match.group(1).strip() if match else ""


def main() -> int:
    additional = ""
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
        payload = payload if isinstance(payload, dict) else {}
        stop_hook_active = payload.get("stop_hook_active") is True
        cwd_value = payload.get("cwd")
        cwd = Path(cwd_value).expanduser() if isinstance(cwd_value, str) and cwd_value.strip() else Path.cwd()
        ai_state = find_ai_state(cwd)
        if ai_state is None:
            return EXIT_SUCCESS
        idx = ai_state / "_index.md"
        if not idx.is_file():
            return EXIT_SUCCESS
        _index_io.acquire(idx)   # v9.9.6: Stop 事件与 token-usage-collector 并发
        content = idx.read_text(encoding="utf-8")
        fm_match = re.match(r"^---\n(.*?)\n---", content, re.S)
        if not fm_match:
            return EXIT_SUCCESS
        fm = fm_match.group(1)
        stage = fm_field(fm, "stage")
        sprint = fm_field(fm, "current_sprint_slug")
        next_action = fm_field(fm, "next_action")
        if not stage:
            return EXIT_SUCCESS
        entry_key = f"stage={stage} sprint={sprint or '?'}"

        if not stop_hook_active:
            hist_idx = content.find(HIST_MARKER)
            last_key = ""
            if hist_idx >= 0:
                m = re.search(r"^- `[^`]+`: (stage=\S+ sprint=\S+)", content[hist_idx:], re.M)
                if m:
                    last_key = m.group(1)
            if last_key != entry_key:
                ts = dt.datetime.now().isoformat(sep=" ", timespec="seconds")
                entry = f"- `{ts}`: {entry_key} turn-end\n"
                if hist_idx >= 0:
                    content = re.sub(r"(## 历史[^\n]*\n)", lambda mm: mm.group(1) + entry, content, count=1)
                else:
                    content += f"\n\n{HIST_MARKER}\n{entry}"
                hi = content.find(HIST_MARKER)
                if hi >= 0:
                    head, tail = content[:hi], content[hi:].split("\n")
                    kept, count = [], 0
                    for line in tail:
                        if line.startswith("- `"):
                            if count < HIST_KEEP:
                                kept.append(line)
                                count += 1
                        else:
                            kept.append(line)
                    content = head + "\n".join(kept)
                _index_io.write_atomic(idx, content)

            hints = []
            if next_action:
                hints.append(f'next_action="{next_action}" 未消费 — 下一 turn 按 athena-dev 的 next_action 表处理.')
            if stage == "review":
                hints.append("review stage: reviewer/spec 返回后由主 thread 合并最新 reviews/passN.md, evaluator 后跑; 只有最终 PASS 才推进.")
            if hints:
                additional = f"[pace-continuator] stage={stage}" + (f" sprint={sprint}" if sprint else "") + "\n" + "\n".join(hints)
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"[pace-continuator] non-blocking: {exc}\n")
    if additional:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "Stop",
                                                 "additionalContext": additional[:CTX_LIMIT]}}, ensure_ascii=False))
    return EXIT_SUCCESS


if __name__ == "__main__":
    raise SystemExit(main())
